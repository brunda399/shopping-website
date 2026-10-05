from flask import Blueprint, request, jsonify, session
from services.cart_service import CartService
from models import Product

cart_bp = Blueprint("cart_api", __name__, url_prefix="/api/cart")


@cart_bp.route("/status", methods=["GET"])
def cart_status():
    """Foundation health check endpoint for Cart API."""
    return jsonify({
        "success": True,
        "message": "Cart API is operational (Module 5 Active)",
    }), 200


@cart_bp.route("", methods=["GET"])
def get_cart():
    """Retrieve full cart summary, items list, subtotal, shipping, and discounts."""
    user_id = session.get("user_id")
    coupon_code = request.args.get("coupon", session.get("applied_coupon", "")).strip()

    summary = CartService.get_cart_summary(user_id=user_id, coupon_code=coupon_code)
    return jsonify({
        "success": True,
        "data": summary
    }), 200


@cart_bp.route("/items", methods=["POST"])
def add_to_cart():
    """Add a product to the shopping cart with quantity and inventory validation."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Product ID is required."}
        }), 400

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Product ID and Quantity must be valid integers."}
        }), 400

    user_id = session.get("user_id")

    if user_id:
        success, message, item = CartService.add_to_cart(user_id, product_id, quantity)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": message}
            }), 400

        coupon_code = session.get("applied_coupon", "")
        summary = CartService.get_cart_summary(user_id=user_id, coupon_code=coupon_code)
        return jsonify({
            "success": True,
            "message": message,
            "data": item,
            "cart": summary
        }), 200
    else:
        # Guest user: validate product availability before client-side storage
        product = Product.query.filter_by(id=product_id).first()
        if not product or not product.is_active:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": "Product is not available or inactive."}
            }), 404

        if product.stock <= 0:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": f"Sorry, '{product.name}' is currently out of stock."}
            }), 400

        if quantity > product.stock:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": f"Cannot add {quantity} units. Only {product.stock} units in stock."}
            }), 400

        guest_item = {
            "product_id": product.id,
            "name": product.name,
            "price": round(float(product.price), 2),
            "image": product.image,
            "category_name": product.category.name if product.category else "General",
            "quantity": quantity,
            "stock": product.stock,
            "subtotal": round(float(product.price * quantity), 2),
        }

        return jsonify({
            "success": True,
            "message": f"Added {product.name} to bag.",
            "data": guest_item
        }), 200


@cart_bp.route("/items/<int:product_id>", methods=["PUT", "PATCH"])
def update_cart_item(product_id: int):
    """Update item quantity or remove item if quantity is set to 0."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    
    if "quantity" not in data:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Quantity field is required."}
        }), 400

    try:
        quantity = int(data["quantity"])
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Quantity must be an integer."}
        }), 400

    user_id = session.get("user_id")

    if user_id:
        success, message, item = CartService.update_cart_item(user_id, product_id, quantity)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": message}
            }), 400

        coupon_code = session.get("applied_coupon", "")
        summary = CartService.get_cart_summary(user_id=user_id, coupon_code=coupon_code)
        return jsonify({
            "success": True,
            "message": message,
            "data": item,
            "cart": summary
        }), 200
    else:
        # Guest user validation
        product = Product.query.filter_by(id=product_id).first()
        if not product or not product.is_active:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": "Product not found or inactive."}
            }), 404

        if quantity > product.stock:
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": f"Cannot set quantity to {quantity}. Only {product.stock} units available."}
            }), 400

        return jsonify({
            "success": True,
            "message": f"Updated quantity to {quantity}.",
            "data": {"product_id": product_id, "quantity": quantity}
        }), 200


@cart_bp.route("/items/<int:product_id>", methods=["DELETE"])
def remove_from_cart(product_id: int):
    """Remove a specific item from the cart."""
    user_id = session.get("user_id")

    if user_id:
        success, message = CartService.remove_from_cart(user_id, product_id)
        if not success:
            return jsonify({
                "success": False,
                "error": {"code": 404, "message": message}
            }), 404

        coupon_code = session.get("applied_coupon", "")
        summary = CartService.get_cart_summary(user_id=user_id, coupon_code=coupon_code)
        return jsonify({
            "success": True,
            "message": message,
            "cart": summary
        }), 200
    else:
        return jsonify({
            "success": True,
            "message": "Item removed from cart."
        }), 200


@cart_bp.route("", methods=["DELETE"])
def clear_cart():
    """Clear all items from the shopping cart."""
    user_id = session.get("user_id")
    session.pop("applied_coupon", None)

    if user_id:
        success, message = CartService.clear_cart(user_id)
        summary = CartService.get_cart_summary(user_id=user_id)
        return jsonify({
            "success": True,
            "message": message,
            "cart": summary
        }), 200
    else:
        return jsonify({
            "success": True,
            "message": "Cart cleared.",
            "cart": {
                "items": [],
                "items_count": 0,
                "total_quantity": 0,
                "subtotal": 0.0,
                "shipping": 0.0,
                "discount": 0.0,
                "total": 0.0,
            }
        }), 200


@cart_bp.route("/coupon", methods=["POST"])
def apply_coupon():
    """Validate and apply a promotional coupon code."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    coupon_code = data.get("coupon_code", "").strip()
    provided_subtotal = data.get("subtotal")

    user_id = session.get("user_id")
    if user_id and provided_subtotal is None:
        summary = CartService.get_cart_summary(user_id=user_id)
        subtotal = summary["subtotal"]
    else:
        try:
            subtotal = float(provided_subtotal or 0.0)
        except (ValueError, TypeError):
            subtotal = 0.0

    valid, message, discount, details = CartService.validate_coupon(coupon_code, subtotal)
    if not valid:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": message}
        }), 400

    session["applied_coupon"] = details["code"]

    return jsonify({
        "success": True,
        "message": message,
        "data": details
    }), 200


@cart_bp.route("/coupon", methods=["DELETE"])
def remove_coupon():
    """Remove the currently applied coupon code."""
    session.pop("applied_coupon", None)
    return jsonify({
        "success": True,
        "message": "Coupon code removed."
    }), 200


@cart_bp.route("/sync", methods=["POST"])
def sync_cart():
    """Synchronize client/guest localStorage items into the database cart upon user authentication."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "error": {"code": 401, "message": "Authentication required to sync cart."}
        }), 401

    data = request.get_json(silent=True) or {}
    guest_items = data.get("items", [])

    success, message, summary = CartService.sync_guest_cart(user_id, guest_items)
    return jsonify({
        "success": True,
        "message": message,
        "data": summary
    }), 200
