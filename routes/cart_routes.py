from flask import Blueprint, jsonify

cart_bp = Blueprint("cart_api", __name__, url_prefix="/api/cart")


@cart_bp.route("/status", methods=["GET"])
def cart_status():
    """Foundation endpoint for cart status check."""
    return jsonify({
        "success": True,
        "message": "Cart API route is ready (Module 5 implementation pending)",
    }), 200
