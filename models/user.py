from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(db.Model):
    """User entity supporting both Customers and Admins."""
    __tablename__ = "users"

    ROLE_USER = "USER"
    ROLE_ADMIN = "ADMIN"
    ROLES = [ROLE_USER, ROLE_ADMIN]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default=ROLE_USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cart = db.relationship("Cart", backref="user", uselist=False, cascade="all, delete-orphan")
    wishlist_items = db.relationship("Wishlist", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    addresses = db.relationship("Address", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="user", lazy="dynamic", cascade="all, delete-orphan")


    def set_password(self, password: str) -> None:
        """Hash and store user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify entered password against stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role == self.ROLE_ADMIN

    def to_dict(self) -> dict:
        """Safe dictionary representation (excluding password hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"
