from flask import Blueprint, jsonify

order_bp = Blueprint("order_api", __name__, url_prefix="/api/orders")


@order_bp.route("/status", methods=["GET"])
def order_status():
    """Foundation endpoint for order status check."""
    return jsonify({
        "success": True,
        "message": "Orders API route is ready (Module 7 implementation pending)",
    }), 200
