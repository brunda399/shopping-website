import json
from datetime import datetime
from . import db


class Product(db.Model):
    """Product entity with pricing, variants, stock, category relation, specs, and ratings."""
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("price >= 0", name="check_product_price_non_negative"),
        db.CheckConstraint("stock >= 0", name="check_product_stock_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(255), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    sale_price = db.Column(db.Float, nullable=True)
    discount_percentage = db.Column(db.Integer, nullable=True, default=0)
    currency = db.Column(db.String(10), default="INR", nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    subcategory = db.Column(db.String(100), nullable=True, index=True)
    brand = db.Column(db.String(100), nullable=True, index=True)
    image = db.Column(db.String(255), default="default-product.png", nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)
    images_json = db.Column(db.Text, nullable=True)
    stock = db.Column(db.Integer, default=0, nullable=False)
    rating = db.Column(db.Float, default=0.0, nullable=False)
    review_count = db.Column(db.Integer, default=0, nullable=False)
    sku = db.Column(db.String(80), nullable=True, index=True)
    sizes_json = db.Column(db.Text, nullable=True)
    colors_json = db.Column(db.Text, nullable=True)
    variants_json = db.Column(db.Text, nullable=True)
    specifications_json = db.Column(db.Text, nullable=True)
    tags_json = db.Column(db.Text, nullable=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_new = db.Column(db.Boolean, default=False, nullable=False)
    is_best_seller = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cart_items = db.relationship("CartItem", backref="product", cascade="all, delete-orphan", lazy="dynamic")
    wishlist_items = db.relationship("Wishlist", backref="product", cascade="all, delete-orphan", lazy="dynamic")
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")
    reviews = db.relationship("Review", backref="product", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def sizes(self) -> list:
        if not self.sizes_json:
            return []
        try:
            return json.loads(self.sizes_json)
        except Exception:
            return [s.strip() for s in self.sizes_json.split(",") if s.strip()]

    @property
    def colors(self) -> list:
        if not self.colors_json:
            return []
        try:
            return json.loads(self.colors_json)
        except Exception:
            return [c.strip() for c in self.colors_json.split(",") if c.strip()]

    @property
    def images(self) -> list:
        if self.images_json:
            try:
                imgs = json.loads(self.images_json)
                if isinstance(imgs, list) and imgs:
                    return imgs
            except Exception:
                pass
        return [self.image] if self.image else []

    @property
    def specifications(self) -> dict:
        if not self.specifications_json:
            return {}
        try:
            return json.loads(self.specifications_json)
        except Exception:
            return {}

    @property
    def tags(self) -> list:
        if not self.tags_json:
            return []
        try:
            return json.loads(self.tags_json)
        except Exception:
            return [t.strip() for t in self.tags_json.split(",") if t.strip()]

    @property
    def variants(self) -> list:
        if not self.variants_json:
            return []
        try:
            return json.loads(self.variants_json)
        except Exception:
            return []

    @property
    def effective_price(self) -> float:
        """Returns sale_price if valid and lower than regular price, else price."""
        if self.sale_price is not None and 0 < self.sale_price < self.price:
            return round(float(self.sale_price), 2)
        return round(float(self.price), 2)

    @property
    def calculated_discount(self) -> int:
        """Calculates discount percentage dynamically or returns stored percentage."""
        if self.discount_percentage and self.discount_percentage > 0:
            return int(self.discount_percentage)
        if self.sale_price and self.price > self.sale_price > 0:
            return int(round(((self.price - self.sale_price) / self.price) * 100))
        return 0

    @property
    def stock_status(self) -> str:
        """Categorize inventory levels for UI badges."""
        if self.stock <= 0:
            return "out_of_stock"
        elif self.stock <= 5:
            return "low_stock"
        return "in_stock"

    def to_dict(self) -> dict:
        eff_price = self.effective_price
        disc_pct = self.calculated_discount
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug or f"product-{self.id}",
            "description": self.description,
            "price": round(float(self.price), 2),
            "salePrice": eff_price,
            "sale_price": eff_price,
            "effective_price": eff_price,
            "discountPercentage": disc_pct,
            "discount_percentage": disc_pct,
            "currency": self.currency or "INR",
            "category": self.category.name if self.category else "",
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "subcategory": self.subcategory,
            "brand": self.brand,
            "image": self.image,
            "thumbnail": self.thumbnail or self.image,
            "images": self.images,
            "stock": self.stock,
            "rating": round(float(self.rating), 1),
            "reviewCount": self.review_count,
            "review_count": self.review_count,
            "sku": self.sku or f"SKU-{self.id:05d}",
            "sizes": self.sizes,
            "colors": self.colors,
            "variants": self.variants,
            "specifications": self.specifications,
            "tags": self.tags,
            "isFeatured": self.is_featured,
            "is_featured": self.is_featured,
            "isNew": self.is_new,
            "is_new": self.is_new,
            "isBestSeller": self.is_best_seller,
            "is_best_seller": self.is_best_seller,
            "is_active": self.is_active,
            "isActive": self.is_active,
            "is_in_stock": self.stock > 0,
            "stock_status": self.stock_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Product {self.id}: {self.name} (Rs.{self.price})>"

