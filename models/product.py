from datetime import datetime
from . import db


class Product(db.Model):
    """Product entity with pricing, stock, category relation, and rating."""
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("price >= 0", name="check_product_price_non_negative"),
        db.CheckConstraint("stock >= 0", name="check_product_stock_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    image = db.Column(db.String(255), default="default-product.png", nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    rating = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cart_items = db.relationship("CartItem", backref="product", cascade="all, delete-orphan", lazy="dynamic")
    wishlist_items = db.relationship("Wishlist", backref="product", cascade="all, delete-orphan", lazy="dynamic")
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")

    @property
    def stock_status(self) -> str:
        """Categorize inventory levels for UI badges."""
        if self.stock <= 0:
            return "out_of_stock"
        elif self.stock <= 5:
            return "low_stock"
        return "in_stock"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": round(float(self.price), 2),
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "image": self.image,
            "stock": self.stock,
            "rating": round(float(self.rating), 1),
            "is_active": self.is_active,
            "is_in_stock": self.stock > 0,
            "stock_status": self.stock_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Product {self.id}: {self.name} (${self.price})>"
