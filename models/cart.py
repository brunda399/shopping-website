from datetime import datetime
from . import db


class Cart(db.Model):
    """Shopping cart entity associated with a user."""
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    items = db.relationship("CartItem", backref="cart", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "items_count": self.items.count(),
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Cart {self.id} (User {self.user_id})>"


class CartItem(db.Model):
    """Single item in a user's shopping cart with variant selection (size, color)."""
    __tablename__ = "cart_items"
    __table_args__ = (
        db.CheckConstraint("quantity >= 1", name="check_cart_item_quantity_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    selected_size = db.Column(db.String(50), nullable=True)
    selected_color = db.Column(db.String(50), nullable=True)
    variant_id = db.Column(db.String(100), nullable=True)

    # Relationship product is automatically populated by Product.cart_items backref

    @property
    def unit_price(self) -> float:
        """Effective unit price at checkout/cart time."""
        if not self.product:
            return 0.0
        return self.product.effective_price

    @property
    def subtotal_price(self) -> float:
        """Line subtotal based on effective unit price."""
        return round(float(self.unit_price * self.quantity), 2)

    def to_dict(self) -> dict:
        unit_p = self.unit_price
        subtot = self.subtotal_price
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "product": self.product.to_dict() if self.product else None,
            "quantity": self.quantity,
            "selected_size": self.selected_size,
            "selected_color": self.selected_color,
            "size": self.selected_size,
            "color": self.selected_color,
            "variant_id": self.variant_id,
            "price": unit_p,
            "unit_price": unit_p,
            "subtotal": subtot,
        }

    def __repr__(self):
        return f"<CartItem {self.id}: Product {self.product_id} ({self.selected_size}/{self.selected_color}) x {self.quantity}>"

