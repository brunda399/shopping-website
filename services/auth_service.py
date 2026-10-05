from typing import Optional, Tuple, Dict, Any
from models import db, User, Cart
from utils.validators import (
    validate_email,
    validate_password,
    validate_non_empty_string,
    validate_phone,
    validate_password_match,
)


class AuthService:
    """Service handling user registration, authentication, sessions, and profile management."""

    @staticmethod
    def register_user(
        name: str, 
        email: str, 
        password: str, 
        confirm_password: Optional[str] = None,
        phone: Optional[str] = None, 
        role: str = User.ROLE_USER
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate input and register a new user account with initialized shopping cart."""
        # 1. Name validation
        valid_name, err = validate_non_empty_string(name, "Full Name", max_length=100)
        if not valid_name:
            return False, err, None

        if len(name.strip()) < 2:
            return False, "Full Name must be at least 2 characters long.", None

        # 2. Email validation
        valid_email, err = validate_email(email)
        if not valid_email:
            return False, err, None

        normalized_email = email.strip().lower()
        if User.query.filter_by(email=normalized_email).first():
            return False, "An account with this email address already exists.", None

        # 3. Phone validation (optional)
        if phone:
            valid_phone, err = validate_phone(phone)
            if not valid_phone:
                return False, err, None

        # 4. Password validation
        valid_pwd, err = validate_password(password)
        if not valid_pwd:
            return False, err, None

        # 5. Confirm password check (if provided)
        if confirm_password is not None:
            valid_match, err = validate_password_match(password, confirm_password)
            if not valid_match:
                return False, err, None

        # 6. Role check
        if role not in User.ROLES:
            role = User.ROLE_USER

        try:
            user = User(
                name=name.strip(),
                email=normalized_email,
                phone=phone.strip() if phone else None,
                role=role,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Ensure new user has an initialized cart
            cart = Cart(user_id=user.id)
            db.session.add(cart)
            db.session.commit()

            return True, "Account registered successfully!", user.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}", None

    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Verify user credentials and return User model instance."""
        if not email or not password:
            return False, "Email and password are required.", None

        normalized_email = email.strip().lower()
        user = User.query.filter_by(email=normalized_email).first()

        if not user or not user.check_password(password):
            return False, "Invalid email or password.", None

        return True, "Login successful.", user

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Fetch user by primary key ID."""
        if not user_id:
            return None
        return db.session.get(User, user_id)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Fetch user by email."""
        if not email:
            return None
        return User.query.filter_by(email=email.strip().lower()).first()

    @staticmethod
    def update_profile(user_id: int, name: str, phone: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update user profile personal details."""
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return False, "User account not found.", None

        valid_name, err = validate_non_empty_string(name, "Full Name", max_length=100)
        if not valid_name:
            return False, err, None

        if len(name.strip()) < 2:
            return False, "Full Name must be at least 2 characters long.", None

        if phone:
            valid_phone, err = validate_phone(phone)
            if not valid_phone:
                return False, err, None

        try:
            user.name = name.strip()
            user.phone = phone.strip() if phone else None
            db.session.commit()
            return True, "Profile updated successfully.", user.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update profile: {str(e)}", None

    @staticmethod
    def change_password(
        user_id: int, 
        current_password: str, 
        new_password: str, 
        confirm_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Change user password after verifying the existing password."""
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return False, "User account not found."

        if not current_password:
            return False, "Current password is required."

        if not user.check_password(current_password):
            return False, "Current password is incorrect."

        valid_pwd, err = validate_password(new_password)
        if not valid_pwd:
            return False, err

        if current_password == new_password:
            return False, "New password cannot be identical to current password."

        if confirm_password is not None:
            valid_match, err = validate_password_match(new_password, confirm_password)
            if not valid_match:
                return False, err

        try:
            user.set_password(new_password)
            db.session.commit()
            return True, "Password changed successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to change password: {str(e)}"

    @staticmethod
    def seed_default_users() -> list:
        """Seed default demo customer and admin accounts if database has no users."""
        seeded = []
        try:
            if User.query.count() > 0:
                return User.query.all()

            # Demo Customer
            _, _, cust = AuthService.register_user(
                name="Alex Customer",
                email="customer@shopease.local",
                password="Customer123!",
                phone="+1-555-0199",
                role=User.ROLE_USER,
            )
            if cust:
                seeded.append(cust)

            # Demo Admin
            _, _, admin = AuthService.register_user(
                name="Admin Manager",
                email="admin@shopease.local",
                password="Admin123!",
                phone="+1-555-0100",
                role=User.ROLE_ADMIN,
            )
            if admin:
                seeded.append(admin)

            return seeded
        except Exception:
            db.session.rollback()
            return seeded
