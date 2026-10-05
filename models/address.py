from datetime import datetime
from . import db


class Address(db.Model):
    """Customer delivery address entity."""
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), default="India", nullable=False)
    landmark = db.Column(db.String(150), nullable=True)
    address_type = db.Column(db.String(30), default="HOME", nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def formatted_address(self) -> str:
        """Formatted multi-line address string for labels & invoices."""
        parts = [self.full_name, f"Ph: {self.phone}", self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.landmark:
            parts.append(f"Near: {self.landmark}")
        parts.append(f"{self.city}, {self.state} - {self.postal_code}")
        parts.append(self.country)
        return ", ".join(parts)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "landmark": self.landmark,
            "address_type": self.address_type,
            "is_default": self.is_default,
            "formatted_address": self.formatted_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Address {self.id}: {self.full_name} ({self.city})>"
