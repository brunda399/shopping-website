from typing import Optional, Tuple, Dict, Any
from models import db, Cart, CartItem, Product


class CartService:
    """Service handling cart and cart item operations."""

    @staticmethod
    def get_or_create_cart(user_id: int) -> Cart:
        """Fetch user cart or create a new one if not existing."""
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    @staticmethod
    def get_cart_summary(user_id: int) -> Dict[str, Any]:
        """Calculate cart totals, items, and details."""
        cart = CartService.get_or_create_cart(user_id)
        items = CartItem.query.filter_by(cart_id=cart.id).all()
        
        total_amount = 0.0
        item_list = []
        for item in items:
            item_data = item.to_dict()
            total_amount += item_data["subtotal"]
            item_list.append(item_data)

        return {
            "cart_id": cart.id,
            "user_id": user_id,
            "items": item_list,
            "items_count": len(item_list),
            "total_amount": round(total_amount, 2),
        }
