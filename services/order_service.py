from typing import List, Dict, Any
from models import Order


class OrderService:
    """Service handling order retrieval and order lifecycle operations."""

    @staticmethod
    def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all orders placed by a specific user."""
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return [order.to_dict() for order in orders]

    @staticmethod
    def get_order_by_id(order_id: int, user_id: int = None) -> Dict[str, Any]:
        """Fetch order details with authorization check."""
        query = Order.query.filter_by(id=order_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        order = query.first()
        return order.to_dict() if order else None
