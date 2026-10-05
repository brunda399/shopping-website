from flask_sqlalchemy import SQLAlchemy

# Central SQLAlchemy instance
db = SQLAlchemy()

# Import models for easy access and table metadata discovery
from .user import User
from .category import Category
from .product import Product
from .cart import Cart, CartItem
from .wishlist import Wishlist
from .order import Order, OrderItem
from .address import Address
from .review import Review

__all__ = [
    "db",
    "User",
    "Category",
    "Product",
    "Cart",
    "CartItem",
    "Wishlist",
    "Order",
    "OrderItem",
    "Address",
    "Review",
]

