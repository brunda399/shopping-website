"""Service handling customer address book operations and validation."""
from typing import List, Dict, Any, Tuple, Optional
from models import db, Address
from utils.logger import log_info, log_error


class AddressService:
    """Service handling multi-address storage, default selection, and validation."""

    @staticmethod
    def get_user_addresses(user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all saved addresses for a user, default address first."""
        addresses = Address.query.filter_by(user_id=user_id).order_by(
            Address.is_default.desc(), Address.created_at.desc()
        ).all()
        return [addr.to_dict() for addr in addresses]

    @staticmethod
    def get_address_by_id(address_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific address belonging to the user."""
        addr = Address.query.filter_by(id=address_id, user_id=user_id).first()
        return addr.to_dict() if addr else None

    @classmethod
    def create_address(cls, user_id: int, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate and create a new delivery address."""
        full_name = (data.get("fullName") or data.get("full_name") or "").strip()
        phone = (data.get("phone") or "").strip()
        address_line1 = (data.get("addressLine1") or data.get("address_line1") or "").strip()
        address_line2 = (data.get("addressLine2") or data.get("address_line2") or "").strip()
        city = (data.get("city") or "").strip()
        state = (data.get("state") or "").strip()
        postal_code = (data.get("postalCode") or data.get("postal_code") or data.get("pincode") or "").strip()
        country = (data.get("country") or "India").strip()
        landmark = (data.get("landmark") or "").strip()
        address_type = (data.get("addressType") or data.get("address_type") or "HOME").strip().upper()
        is_default = bool(data.get("isDefault") or data.get("is_default") or False)

        # Validation
        if not full_name:
            return False, "Full Name is required.", None
        if not phone or len(phone) < 7:
            return False, "A valid contact phone number is required.", None
        if not address_line1:
            return False, "Address Line 1 is required.", None
        if not city:
            return False, "City is required.", None
        if not state:
            return False, "State is required.", None
        if not postal_code or len(postal_code) < 3:
            return False, "A valid Postal / PIN Code is required.", None

        existing_count = Address.query.filter_by(user_id=user_id).count()
        # If it's user's first address, automatically make it default
        if existing_count == 0:
            is_default = True

        if is_default:
            Address.query.filter_by(user_id=user_id).update({"is_default": False})

        new_addr = Address(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            address_line1=address_line1,
            address_line2=address_line2 if address_line2 else None,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            landmark=landmark if landmark else None,
            address_type=address_type if address_type in ["HOME", "WORK", "OTHER"] else "HOME",
            is_default=is_default,
        )

        db.session.add(new_addr)
        db.session.commit()
        log_info(f"Created address #{new_addr.id} for user #{user_id}")
        return True, "Address saved successfully.", new_addr.to_dict()

    @classmethod
    def update_address(cls, address_id: int, user_id: int, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update an existing delivery address."""
        addr = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not addr:
            return False, "Address not found.", None

        full_name = (data.get("fullName") or data.get("full_name") or addr.full_name).strip()
        phone = (data.get("phone") or addr.phone).strip()
        address_line1 = (data.get("addressLine1") or data.get("address_line1") or addr.address_line1).strip()
        city = (data.get("city") or addr.city).strip()
        state = (data.get("state") or addr.state).strip()
        postal_code = (data.get("postalCode") or data.get("postal_code") or data.get("pincode") or addr.postal_code).strip()

        if not full_name or not phone or not address_line1 or not city or not state or not postal_code:
            return False, "Please fill in all required address fields.", None

        is_default = data.get("isDefault") if "isDefault" in data else data.get("is_default")
        if is_default is not None and bool(is_default):
            Address.query.filter_by(user_id=user_id).update({"is_default": False})
            addr.is_default = True

        addr.full_name = full_name
        addr.phone = phone
        addr.address_line1 = address_line1
        if "addressLine2" in data or "address_line2" in data:
            addr.address_line2 = data.get("addressLine2") or data.get("address_line2")
        addr.city = city
        addr.state = state
        addr.postal_code = postal_code
        if "country" in data:
            addr.country = data["country"].strip()
        if "landmark" in data:
            addr.landmark = data["landmark"].strip()
        if "addressType" in data or "address_type" in data:
            addr.address_type = (data.get("addressType") or data.get("address_type") or "HOME").upper()

        db.session.commit()
        return True, "Address updated successfully.", addr.to_dict()

    @classmethod
    def delete_address(cls, address_id: int, user_id: int) -> Tuple[bool, str]:
        """Delete an address and ensure a default address remains if others exist."""
        addr = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not addr:
            return False, "Address not found."

        was_default = addr.is_default
        db.session.delete(addr)
        db.session.commit()

        # If deleted was default, promote another address to default
        if was_default:
            next_addr = Address.query.filter_by(user_id=user_id).first()
            if next_addr:
                next_addr.is_default = True
                db.session.commit()

        return True, "Address deleted successfully."

    @classmethod
    def set_default(cls, address_id: int, user_id: int) -> Tuple[bool, str]:
        """Set specified address as default."""
        addr = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not addr:
            return False, "Address not found."

        Address.query.filter_by(user_id=user_id).update({"is_default": False})
        addr.is_default = True
        db.session.commit()
        return True, "Default delivery address updated."
