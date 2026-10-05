"""REST API endpoints for delivery address management."""
from flask import Blueprint, request, jsonify, session
from services.address_service import AddressService
from utils.auth_decorators import login_required_api

address_bp = Blueprint("address_api", __name__, url_prefix="/api/addresses")


@address_bp.route("", methods=["GET"])
@login_required_api
def get_addresses():
    """Retrieve all saved addresses for current user."""
    user_id = session.get("user_id")
    addresses = AddressService.get_user_addresses(user_id)
    return jsonify({
        "success": True,
        "data": addresses,
        "count": len(addresses),
    }), 200


@address_bp.route("", methods=["POST"])
@login_required_api
def create_address():
    """Create a new delivery address."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    
    success, message, addr = AddressService.create_address(user_id, data)
    if not success:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": message}
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "data": addr,
    }), 201


@address_bp.route("/<int:address_id>", methods=["PUT", "PATCH"])
@login_required_api
def update_address(address_id: int):
    """Update an existing delivery address."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    success, message, addr = AddressService.update_address(address_id, user_id, data)
    if not success:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": message}
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "data": addr,
    }), 200


@address_bp.route("/<int:address_id>", methods=["DELETE"])
@login_required_api
def delete_address(address_id: int):
    """Delete a delivery address."""
    user_id = session.get("user_id")
    success, message = AddressService.delete_address(address_id, user_id)
    if not success:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": message}
        }), 404

    return jsonify({
        "success": True,
        "message": message,
    }), 200


@address_bp.route("/<int:address_id>/default", methods=["PUT", "POST"])
@login_required_api
def set_default_address(address_id: int):
    """Set an address as default."""
    user_id = session.get("user_id")
    success, message = AddressService.set_default(address_id, user_id)
    if not success:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": message}
        }), 404

    return jsonify({
        "success": True,
        "message": message,
    }), 200
