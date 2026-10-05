import re
from typing import Tuple, Optional, Any, Dict


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: Optional[str]) -> Tuple[bool, str]:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False, "Email address is required."
    clean_email = email.strip()
    if len(clean_email) > 120:
        return False, "Email address must not exceed 120 characters."
    if not EMAIL_REGEX.match(clean_email):
        return False, "Invalid email address format."
    return True, ""


def validate_password(password: Optional[str]) -> Tuple[bool, str]:
    """Validate password length and basic complexity."""
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if len(password) > 128:
        return False, "Password must not exceed 128 characters."
    return True, ""


def validate_positive_number(
    val: Any, 
    field_name: str = "Value", 
    allow_zero: bool = True
) -> Tuple[bool, str]:
    """Validate that a numeric value is non-negative."""
    try:
        num = float(val)
        if allow_zero and num < 0:
            return False, f"{field_name} cannot be negative."
        if not allow_zero and num <= 0:
            return False, f"{field_name} must be greater than zero."
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number."


def validate_non_empty_string(
    val: Optional[str], 
    field_name: str = "Field", 
    max_length: int = 255
) -> Tuple[bool, str]:
    """Validate non-empty string."""
    if not val or not isinstance(val, str) or not val.strip():
        return False, f"{field_name} is required."
    if len(val.strip()) > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters."
    return True, ""


def validate_phone(phone: Optional[str]) -> Tuple[bool, str]:
    """Validate optional phone number format."""
    if not phone or not phone.strip():
        return True, ""  # Phone is optional
    clean_phone = phone.strip()
    # Accept numbers, spaces, plus, hyphens, parentheses (7 to 20 chars)
    phone_pattern = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")
    if not phone_pattern.match(clean_phone):
        return False, "Please enter a valid phone number (7-20 digits)."
    return True, ""


def validate_password_match(password: Optional[str], confirm_password: Optional[str]) -> Tuple[bool, str]:
    """Verify that password and confirm password match."""
    if not password or not confirm_password:
        return False, "Both password and confirmation are required."
    if password != confirm_password:
        return False, "Passwords do not match."
    return True, ""


def validate_integer(
    val: Any, 
    field_name: str = "Stock", 
    allow_zero: bool = True
) -> Tuple[bool, str]:
    """Validate that a value is a valid whole integer (rejects floats, strings, and negatives)."""
    if val is None or val == "":
        return False, f"{field_name} is required."
    try:
        # Rejection of decimal strings like "10.5"
        if isinstance(val, str) and "." in val.strip():
            return False, f"{field_name} must be a whole integer without decimals."
        if isinstance(val, float) and not val.is_integer():
            return False, f"{field_name} must be a whole integer without decimals."
        num = int(val)
        if allow_zero and num < 0:
            return False, f"{field_name} cannot be negative."
        if not allow_zero and num <= 0:
            return False, f"{field_name} must be greater than zero."
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid whole integer."


DEFAULT_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def validate_image_file(filename: Optional[str], allowed_extensions: Optional[set] = None) -> Tuple[bool, str]:
    """Validate image file extension and security against malicious uploads."""
    if not filename or not isinstance(filename, str):
        return False, "Filename is required."
    allowed = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
    if "." not in filename:
        return False, "Image file must have an extension."
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in allowed:
        return False, f"Invalid image format '.{ext}'. Allowed formats: {', '.join(sorted(allowed))}."
    return True, ""


def generate_secure_image_filename(original_filename: str) -> str:
    """Generate a sanitized, unique filename to prevent collision and directory traversal."""
    import uuid
    from werkzeug.utils import secure_filename
    cleaned = secure_filename(original_filename)
    ext = cleaned.rsplit(".", 1)[1].lower() if "." in cleaned else "jpg"
    unique_token = uuid.uuid4().hex[:12]
    return f"prod_{unique_token}.{ext}"


