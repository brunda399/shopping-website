from datetime import datetime
from . import db


class Order(db.Model):
    """Customer order entity."""
    __tablename__ = "orders"

    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"
    ALL_STATUSES = [
        STATUS_PENDING,
        STATUS_CONFIRMED,
        STATUS_SHIPPED,
        STATUS_DELIVERED,
        STATUS_CANCELLED,
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    payment_method = db.Column(db.String(50), default="COD", nullable=False)
    status = db.Column(db.String(30), default=STATUS_PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_amount": round(float(self.total_amount), 2),
            "address": self.address,
            "city": self.city,
            "pincode": self.pincode,
            "phone": self.phone,
            "payment_method": self.payment_method,
            "status": self.status,
            "items_count": self.items.count(),
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Order {self.id}: User {self.user_id} - ${self.total_amount} ({self.status})>"


class OrderItem(db.Model):
    """Line item in a customer order capturing product price at time of purchase."""
    __tablename__ = "order_items"
    __table_args__ = (
        db.CheckConstraint("quantity >= 1", name="check_order_item_quantity_positive"),
        db.CheckConstraint("price >= 0", name="check_order_item_price_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "quantity": self.quantity,
            "price": round(float(self.price), 2),
            "subtotal": round(float(self.price * self.quantity), 2),
        }

    def __repr__(self):
        return f"<OrderItem {self.id}: Order {self.order_id} - Product {self.product_id} x {self.quantity}>"
