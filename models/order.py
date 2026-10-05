import json
from datetime import datetime, timedelta
from . import db


class Order(db.Model):
    """Customer order entity with full lifecycle tracking, address snapshot, and calculation breakdown."""
    __tablename__ = "orders"

    STATUS_PLACED = "PLACED"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_PACKED = "PACKED"
    STATUS_SHIPPED = "SHIPPED"
    STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"

    ALL_STATUSES = [
        STATUS_PLACED,
        STATUS_CONFIRMED,
        STATUS_PACKED,
        STATUS_SHIPPED,
        STATUS_OUT_FOR_DELIVERY,
        STATUS_DELIVERED,
        STATUS_CANCELLED,
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Financial breakdown (calculated on server)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    shipping = db.Column(db.Float, nullable=False, default=0.0)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)

    # Address snapshot
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True, default="India")
    pincode = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    shipping_address_json = db.Column(db.Text, nullable=True)

    # Payment & Fulfillment
    payment_method = db.Column(db.String(50), default="COD", nullable=False)
    payment_status = db.Column(db.String(30), default="PENDING", nullable=False)
    status = db.Column(db.String(30), default=STATUS_PLACED, nullable=False)
    estimated_delivery = db.Column(db.String(50), nullable=True)
    tracking_history_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def tracking_history(self) -> list:
        if self.tracking_history_json:
            try:
                return json.loads(self.tracking_history_json)
            except Exception:
                pass
        # Default tracking timeline based on current status
        now_str = self.created_at.strftime("%b %d, %Y, %I:%M %p") if self.created_at else ""
        return [
            {"status": self.STATUS_PLACED, "label": "Order Placed", "timestamp": now_str, "done": True, "current": self.status == self.STATUS_PLACED},
            {"status": self.STATUS_CONFIRMED, "label": "Order Confirmed", "timestamp": "Processing", "done": self.status in [self.STATUS_CONFIRMED, self.STATUS_PACKED, self.STATUS_SHIPPED, self.STATUS_OUT_FOR_DELIVERY, self.STATUS_DELIVERED], "current": self.status == self.STATUS_CONFIRMED},
            {"status": self.STATUS_PACKED, "label": "Packed", "timestamp": "Warehouse", "done": self.status in [self.STATUS_PACKED, self.STATUS_SHIPPED, self.STATUS_OUT_FOR_DELIVERY, self.STATUS_DELIVERED], "current": self.status == self.STATUS_PACKED},
            {"status": self.STATUS_SHIPPED, "label": "Shipped", "timestamp": "In transit", "done": self.status in [self.STATUS_SHIPPED, self.STATUS_OUT_FOR_DELIVERY, self.STATUS_DELIVERED], "current": self.status == self.STATUS_SHIPPED},
            {"status": self.STATUS_OUT_FOR_DELIVERY, "label": "Out for Delivery", "timestamp": "Courier agent", "done": self.status in [self.STATUS_OUT_FOR_DELIVERY, self.STATUS_DELIVERED], "current": self.status == self.STATUS_OUT_FOR_DELIVERY},
            {"status": self.STATUS_DELIVERED, "label": "Delivered", "timestamp": self.estimated_delivery or "Upcoming", "done": self.status == self.STATUS_DELIVERED, "current": self.status == self.STATUS_DELIVERED},
        ]

    @property
    def shipping_address(self) -> dict:
        if self.shipping_address_json:
            try:
                return json.loads(self.shipping_address_json)
            except Exception:
                pass
        return {
            "fullName": self.full_name or "Valued Customer",
            "full_name": self.full_name or "Valued Customer",
            "phone": self.phone,
            "addressLine1": self.address,
            "address_line1": self.address,
            "city": self.city,
            "state": self.state or "",
            "postalCode": self.pincode,
            "postal_code": self.pincode,
            "country": "India",
        }

    def to_dict(self) -> dict:
        item_list = [item.to_dict() for item in self.items]
        addr = self.shipping_address
        return {
            "id": self.id,
            "userId": self.user_id,
            "user_id": self.user_id,
            "orderNumber": self.order_number,
            "order_number": self.order_number,
            "subtotal": round(float(self.subtotal), 2),
            "discount": round(float(self.discount), 2),
            "shipping": round(float(self.shipping), 2),
            "tax": round(float(self.tax), 2),
            "total": round(float(self.total_amount), 2),
            "total_amount": round(float(self.total_amount), 2),
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "phone": self.phone,
            "fullName": self.full_name,
            "full_name": self.full_name,
            "shippingAddress": addr,
            "shipping_address": addr,
            "paymentMethod": self.payment_method,
            "payment_method": self.payment_method,
            "paymentStatus": self.payment_status,
            "payment_status": self.payment_status,
            "orderStatus": self.status,
            "status": self.status,
            "estimatedDelivery": self.estimated_delivery,
            "estimated_delivery": self.estimated_delivery,
            "trackingHistory": self.tracking_history,
            "tracking_history": self.tracking_history,
            "items_count": len(item_list),
            "items": item_list,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Order {self.id}: {self.order_number} (Rs.{self.total_amount}) [{self.status}]>"


class OrderItem(db.Model):
    """Line item capturing product price, name, image, and variant selection at time of purchase."""
    __tablename__ = "order_items"
    __table_args__ = (
        db.CheckConstraint("quantity >= 1", name="check_order_item_quantity_positive"),
        db.CheckConstraint("price >= 0", name="check_order_item_price_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    product_name = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=True)

    def to_dict(self) -> dict:
        subtot = round(float(self.subtotal or (self.price * self.quantity)), 2)
        p_name = self.product_name or (self.product.name if self.product else "Product")
        img = self.image or (self.product.image if self.product else "📦")
        return {
            "id": self.id,
            "orderId": self.order_id,
            "order_id": self.order_id,
            "productId": self.product_id,
            "product_id": self.product_id,
            "productName": p_name,
            "product_name": p_name,
            "name": p_name,
            "image": img,
            "thumbnail": img,
            "size": self.size,
            "color": self.color,
            "quantity": self.quantity,
            "price": round(float(self.price), 2),
            "subtotal": subtot,
        }

    def __repr__(self):
        return f"<OrderItem {self.id}: Order {self.order_id} - Product {self.product_id} ({self.size}/{self.color}) x {self.quantity}>"

