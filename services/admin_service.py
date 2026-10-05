from typing import Dict, Any
from models import User, Product, Order, Category


class AdminService:
    """Service handling administration analytics and administrative actions."""

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Aggregate summary metrics for the admin dashboard."""
        total_users = User.query.filter_by(role=User.ROLE_USER).count()
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_categories = Category.query.count()

        return {
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_categories": total_categories,
        }
