"""
ShopEase — Wishlist REST API Blueprint
Module 6: Wishlist System
"""

from flask import Blueprint, request, jsonify, session
from services.wishlist_service import WishlistService
from services.cart_service import CartService
from models import Product

wishlist_bp = Blueprint("wishlist_api", __name__, url_prefix="/api/wishlist")


@wishlist_bp.route("/status", methods=["GET"])
def wishlist_status():
    """Foundation health check endpoint for Wishlist API."""
    return jsonify({
        "success": True,
        "message": "Wishlist API is operational (Module 6 Active)",
    }), 200


@wishlist_bp.route("", methods=["GET"])
def get_wishlist():
    """Retrieve full wishlist items list for authenticated user or hydrated guest items."""
    user_id = session.get("user_id")

    if user_id:
        data = WishlistService.get_user_wishlist(user_id)
        return jsonify({
            "success": True,
            "data": data
        }), 200
    else:
        # Support guest wishlist hydration via ?product_ids=1,2,3 or JSON
        ids_param = request.args.get("product_ids", "")
        if ids_param:
            try:
                product_ids = [int(i.strip()) for i in ids_param.split(",") if i.strip()]
            except ValueError:
                product_ids = []
        else:
            product_ids = []

        data = WishlistService.get_guest_wishlist(product_ids)
        return jsonify({
            "success": True,
            "data": data
        }), 200


@wishlist_bp.route("/items", methods=["POST"])
def add_to_wishlist():
    """Add a product to the user's wishlist."""
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    product_id = payload.get("product_id")

    if not product_id:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Product ID is required."}
        }), 400

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Product ID must be an integer."}
        }), 400

    user_id = session.get("user_id")

    if user_id:
        success, message, item = WishlistService.add_to_wishlist(user_id, product_id)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": message}
            }), 404

        summary = WishlistService.get_user_wishlist(user_id)
        return jsonify({
            "success": True,
            "message": message,
            "data": item,
            "wishlist": summary
        }), 200
    else:
        # Guest user: validate product exists and is active
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": "Product is not available or inactive."}
            }), 404

        return jsonify({
            "success": True,
            "message": f"Added '{product.name}' to wishlist.",
            "data": {
                "product_id": product.id,
                "name": product.name,
                "price": round(float(product.price), 2),
                "image": product.image,
                "category_name": product.category.name if product.category else "General",
                "stock": product.stock,
                "stock_status": product.stock_status,
                "is_in_stock": product.stock > 0,
            }
        }), 200


@wishlist_bp.route("/toggle", methods=["POST"])
def toggle_wishlist():
    """Toggle a product in or out of the user's wishlist."""
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    product_id = payload.get("product_id")

    if not product_id:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Product ID is required."}
        }), 400

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Product ID must be an integer."}
        }), 400

    user_id = session.get("user_id")

    if user_id:
        success, message, is_in_wishlist, item = WishlistService.toggle_wishlist(user_id, product_id)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": message}
            }), 404

        summary = WishlistService.get_user_wishlist(user_id)
        return jsonify({
            "success": True,
            "message": message,
            "is_in_wishlist": is_in_wishlist,
            "data": item,
            "wishlist": summary
        }), 200
    else:
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": "Product is not available or inactive."}
            }), 404

        return jsonify({
            "success": True,
            "message": f"Toggled '{product.name}' in wishlist.",
            "data": {
                "product_id": product.id,
                "name": product.name,
                "price": round(float(product.price), 2),
                "image": product.image,
            }
        }), 200


@wishlist_bp.route("/items/<int:product_id>", methods=["DELETE"])
def remove_from_wishlist(product_id: int):
    """Remove a product from the user's wishlist."""
    user_id = session.get("user_id")

    if user_id:
        success, message = WishlistService.remove_from_wishlist(user_id, product_id)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": message}
            }), 404

        summary = WishlistService.get_user_wishlist(user_id)
        return jsonify({
            "success": True,
            "message": message,
            "wishlist": summary
        }), 200
    else:
        return jsonify({
            "success": True,
            "message": "Item removed from wishlist."
        }), 200


@wishlist_bp.route("", methods=["DELETE"])
def clear_wishlist():
    """Clear all items from the user's wishlist."""
    user_id = session.get("user_id")

    if user_id:
        success, message = WishlistService.clear_wishlist(user_id)
        return jsonify({
            "success": True,
            "message": message,
            "wishlist": {"items_count": 0, "items": []}
        }), 200
    else:
        return jsonify({
            "success": True,
            "message": "Wishlist cleared.",
            "wishlist": {"items_count": 0, "items": []}
        }), 200


@wishlist_bp.route("/items/<int:product_id>/move-to-cart", methods=["POST"])
def move_to_cart(product_id: int):
    """Move an item from wishlist to the shopping cart."""
    user_id = session.get("user_id")
    payload = request.get_json(silent=True) or {}
    quantity = payload.get("quantity", 1)

    try:
        quantity = int(quantity)
        if quantity <= 0:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1

    if user_id:
        success, message, cart_item = WishlistService.move_to_cart(user_id, product_id, quantity)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": message}
            }), 400

        wishlist_summary = WishlistService.get_user_wishlist(user_id)
        cart_summary = CartService.get_cart_summary(user_id=user_id)

        return jsonify({
            "success": True,
            "message": message,
            "data": cart_item,
            "wishlist": wishlist_summary,
            "cart": cart_summary
        }), 200
    else:
        product = Product.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": "Product not found or inactive."}
            }), 404

        if product.stock <= 0:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": f"Sorry, '{product.name}' is currently out of stock."}
            }), 400

        return jsonify({
            "success": True,
            "message": f"Added '{product.name}' to shopping bag.",
            "data": {
                "product_id": product.id,
                "name": product.name,
                "price": round(float(product.price), 2),
                "image": product.image,
                "quantity": quantity
            }
        }), 200


@wishlist_bp.route("/move-all-to-cart", methods=["POST"])
def move_all_to_cart():
    """Bulk move all in-stock wishlist items to shopping cart."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "error": {"code": 401, "message": "Authentication required to bulk transfer wishlist items."}
        }), 401

    success, message, stats = WishlistService.move_all_to_cart(user_id)
    wishlist_summary = WishlistService.get_user_wishlist(user_id)
    cart_summary = CartService.get_cart_summary(user_id=user_id)

    return jsonify({
        "success": success,
        "message": message,
        "data": stats,
        "wishlist": wishlist_summary,
        "cart": cart_summary
    }), 200


@wishlist_bp.route("/sync", methods=["POST"])
def sync_wishlist():
    """Synchronize client/guest localStorage wishlist items into database upon user login."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "error": {"code": 401, "message": "Authentication required to sync wishlist."}
        }), 401

    payload = request.get_json(silent=True) or {}
    product_ids = payload.get("product_ids", [])

    success, message, summary = WishlistService.sync_guest_wishlist(user_id, product_ids)
    return jsonify({
        "success": True,
        "message": message,
        "data": summary
    }), 200
