from datetime import datetime
from . import db


class Review(db.Model):
    """Customer product review and rating entity."""
    __tablename__ = "reviews"
    __table_args__ = (
        db.CheckConstraint("rating >= 1.0 AND rating <= 5.0", name="check_review_rating_range"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Float, default=5.0, nullable=False)
    title = db.Column(db.String(150), nullable=True)
    comment = db.Column(db.Text, nullable=False)
    is_verified_purchase = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Anonymous",
            "product_id": self.product_id,
            "rating": round(float(self.rating), 1),
            "title": self.title or "",
            "comment": self.comment,
            "is_verified_purchase": self.is_verified_purchase,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Review {self.id}: Product {self.product_id} - {self.rating}★>"
