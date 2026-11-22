"""Unit tests for CheckoutService Fixes 7 and 8) ."""
import pytest

from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart
from payments import FakePaymentGateway
from checkout import CheckoutService


class BrokenGateway:
    def charge(self, amount, payment_token):
        raise ConnectionError('gateway down')


@pytest.fixture
def repo(tmp_path):
    db = tmp_path / 'test.db'
    initialize(str(db))
    return StoreRepository(str(db))


@pytest.fixture
def cart(repo):
    c = ShoppingCart('student', repo)
    c.add_item('MOU-01', 2)
    return c


def test_empty_cart_is_not_charged(repo):
    gateway = FakePaymentGateway()
    result = CheckoutService(repo, gateway).checkout(ShoppingCart('student', repo), 'TOKEN', 'req-1')
    assert result.status == 'empty'
    assert gateway.calls == []


# Fix 7
def test_declined_payment_keeps_stock_and_cart(repo, cart):
    gateway = FakePaymentGateway(should_approve=False)
    result = CheckoutService(repo, gateway).checkout(cart, 'TOKEN', 'req-1')
    assert result.status == 'declined'
    assert repo.get_product('MOU-01').stock == 20   # stock not lost
    assert len(cart.lines) == 1                     # cart not emptied


# Fix 7
def test_payment_error_keeps_stock_and_cart(repo, cart):
    result = CheckoutService(repo, BrokenGateway()).checkout(cart, 'TOKEN', 'req-1')
    assert result.status == 'payment_error'
    assert repo.get_product('MOU-01').stock == 20
    assert len(cart.lines) == 1


# Fix 7
def test_out_of_stock_at_checkout_is_not_charged(repo):
    cart = ShoppingCart('student', repo)
    cart.add_item('LAP-01', 3)
    repo.update_stock('LAP-01', 4)                  # someone else bought 4, only 1 left
    gateway = FakePaymentGateway()
    result = CheckoutService(repo, gateway).checkout(cart, 'TOKEN', 'req-1')
    assert result.status == 'out_of_stock'
    assert gateway.calls == []                      # card never charged
    assert repo.get_product('LAP-01').stock == 1


# Fix 8
def test_repeated_checkout_only_charges_once(repo, cart):
    gateway = FakePaymentGateway()
    service = CheckoutService(repo, gateway)
    first = service.checkout(cart, 'TOKEN', 'req-1')
    cart.add_item('MOU-01', 2)                      # user clicks checkout again
    second = service.checkout(cart, 'TOKEN', 'req-1')
    assert first.status == 'paid'
    assert second.order_id == first.order_id
    assert len(gateway.calls) == 1                  # charged once only
    assert repo.get_product('MOU-01').stock == 18