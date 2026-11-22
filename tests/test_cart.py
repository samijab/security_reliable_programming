"""Unit tests for ShoppingCart Fixes 1-5."""
import pytest

from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart


@pytest.fixture
def repo(tmp_path):
    """A fresh test database for every test, so tests don't affect each other."""
    db = tmp_path / 'test.db'
    initialize(str(db))
    return StoreRepository(str(db))


@pytest.fixture
def cart(repo):
    return ShoppingCart('student', repo)


# Fix 1
def test_invalid_quantities_are_rejected(cart):
    assert cart.add_item('USB-01', 0) is False
    assert cart.add_item('USB-01', -3) is False
    assert cart.add_item('USB-01', 1.5) is False
    assert cart.lines == []

    cart.add_item('USB-01', 2)
    assert cart.remove_item('USB-01', -5) is False
    assert cart.lines[0].quantity == 2


# Fix 2
def test_duplicate_adds_cannot_exceed_stock(cart):
    assert cart.add_item('USB-01', 30) is True
    assert cart.add_item('USB-01', 30) is False   # 60 > 50 in stock
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 30


# Fix 3
def test_total_updates_when_cart_changes_after_discount(cart):
    cart.add_item('MOU-01', 2)                    # 59.90
    cart.apply_discount('WELCOME10')
    assert cart.total() == 53.91
    cart.add_item('USB-01', 1)                    # 69.89
    assert cart.total() == 62.9
    cart.remove_item('MOU-01')                    # 9.99
    assert cart.total() == 8.99


# Fix 3
def test_discount_does_not_stack(cart):
    cart.add_item('MOU-01', 2)
    cart.apply_discount('WELCOME10')
    cart.apply_discount('WELCOME10')
    assert cart.total() == 53.91                  # 10% off once


# Fix 4
def test_save15_never_makes_total_negative(cart):
    cart.add_item('USB-01', 1)                    # 9.99
    cart.apply_discount('SAVE15')
    assert cart.total() == 0


# Fix 5
def test_loading_saved_cart_twice_does_not_duplicate(repo):
    cart = ShoppingCart('student', repo)
    cart.add_item('USB-01', 2)
    cart.save()

    new_cart = ShoppingCart('student', repo)
    new_cart.load()
    new_cart.load()
    assert new_cart.lines[0].quantity == 2