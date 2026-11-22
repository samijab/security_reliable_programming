# Defects and Fixes

## 1. No quantity Validation 
**Where:** `cart.py`, `add_item()` and `remove_item()`
**Problem:** Quantities never checked so zero negative or non int amounts were accepted. When I called `remove _item` with a negative number it actually added items to the cart.
**Fix:** Both methods now reject any quantities that are not a positive whole number and return `False`

## 2. Stock check ignored items already in cart 
**Where:** `cart.py`and `add_item()`
**Problem:** Stock was only compared to the quantity being added, not the
total in the cart. Adding the same product several times could put more in
the cart than was in stock
**Fix:** The check now uses the quantity already in the cart plus the new
quantity.

## 3. Discount total not updated after cart changes, and coupons stacked
**Where:** `cart.py`, `apply_discount()` and `total()`
**Problem:** `apply_discount` saved a fixed discounted total so adding or
removing items afterwards did not change the price. It also calculated from
the already-discounted total, so applying a coupon twice gave a bigger
discount.
**Fix:** Only the coupon code is stored. `total()` recalculates the discount
from the current subtotal every time, and a new coupon replaces the old one
instead of stacking.

## 4. SAVE15 could make the total negative
**Where:** `cart.py`, `total()`
**Problem:** SAVE15 subtracted $15 regardless of the cart value, so a cart
under $15 ended up with a negative total.
**Fix:** The total is limited to a minimum of $0.00.

## 5. Repeated loads duplicated the saved cart
**Where:** `cart.py`, `load()`
**Problem:** `load()` added saved items on top of whatever was already in the
cart. Calling it twice doubled every quantity.
**Fix:** The cart is cleared before the saved items are loaded, loading is
safe to repeat.

## 6. SQL injection in product and saved-cart lookups
**Where:** `repository.py`, `get_product()` and `get_saved_cart()`
**Problem:** The SQL was built with f-strings, input was inserted directly
into the query. Input like `x' OR '1'='1` changes the query.
**Fix:** Both queries now use parameterised placeholders (`?`), like the rest
of the repository.

## 7. Declined payments lost stock and emptied the cart
**Where:** `checkout.py`, `checkout()`
**Problem:** Stock was decreased before the payment was attempted and never
restored, a declined or failed payment permanently removed stock. The cart
was also cleared even when payment failed. Stock was never re-checked at
checkout so items bought by someone else in the meantime could still be sold.
**Fix:** Stock is checked before charging returns `out_of_stock` if not
enough. Stock is only decreased and the cart cleared after the payment
is approved.

## 8. Repeated checkout charged the customer twice
**Where:** `checkout.py`, `checkout()` plus new `find_order_by_request_id()` in `repository.py`
**Problem:** The request id was saved but never checked. Sending the same
checkout again double click and retry created a second order and a second
charge. A missing request id was only printed, and only for orders over $1000.
The payment token was also printed to the console.
**Fix:** A request id is now required. If an order with the same request id
already exists, that original result is returned and the card is not charged
again. The token is no longer printed.

## Assumptions
- A request id represents one checkout attempt. Reusing it returns the
  original result even if it was declined; to retry, a new request id is used.
- If the payment gateway raises an error, we assume no money was taken.
- FREESHIP is accepted but changes nothing because the app has no shipping cost.
- Totals are rounded to 2 decimal places.