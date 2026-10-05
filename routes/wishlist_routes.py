from flask import Blueprint, jsonify

wishlist_bp = Blueprint("wishlist_api", __name__, url_prefix="/api/wishlist")


@wishlist_bp.route("/status", methods=["GET"])
def wishlist_status():
    """Foundation endpoint for wishlist status check."""
    return jsonify({
        "success": True,
        "message": "Wishlist API route is ready (Module 6 implementation pending)",
    }), 200
