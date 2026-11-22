"""Unit test for StoreRepository (Fix 6)."""
from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart


def test_sql_injection_input_does_not_return_data(tmp_path):
    db = tmp_path / 'test.db'
    initialize(str(db))
    repo = StoreRepository(str(db))

    cart = ShoppingCart('alice', repo)
    cart.add_item('USB-01', 1)
    cart.save()

    attack = "x' OR '1'='1"
    assert repo.get_product(attack) is None
    assert repo.get_saved_cart(attack) == []
    assert repo.get_product('USB-01').name == 'USB cable'
    assert repo.get_saved_cart('alice') == [('USB-01', 1)]