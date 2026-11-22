"""Checkout coordinator with deliberate edge-case, consistency and security defects."""
from models import OrderResult


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        if len(cart.lines) == 0:
            return OrderResult(None, 'empty', 0)
        
        if not request_id:
            return OrderResult(None, 'missing_request_id', 0)

        # Same request sent again: return the first result / don't charge again.
        existing = self.repository.find_order_by_request_id(request_id)
        if existing:
            order_id, status, amount = existing
            return OrderResult(order_id, status, amount)

        amount = cart.total()
        # Make sure everything is still in stock before charging.
        for line in cart.lines:
            product = self.repository.get_product(line.sku)
            if product is None or product.stock < line.quantity:
                return OrderResult(None, 'out_of_stock', amount)
        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = 'paid' if response['approved'] else 'declined'
        except Exception:
            status = 'payment_error'
        order_id = self.repository.save_order(cart.user_id, amount, status, request_id)
        # Only take stock and empty the cart if the payment went through.
        if status == 'paid':
            for line in cart.lines:
                self.repository.update_stock(line.sku, line.quantity)
            cart.lines.clear()
            cart.discount_code = None
            cart.save()
        return OrderResult(order_id, status, amount)