"""REST API endpoints for order checkout, history, cancellation, and tracking."""
from flask import Blueprint, request, jsonify, session
from services.order_service import OrderService
from utils.auth_decorators import login_required_api

order_bp = Blueprint("order_api", __name__, url_prefix="/api/orders")


@order_bp.route("/status", methods=["GET"])
def order_status():
    """Health check for Order API."""
    return jsonify({
        "success": True,
        "message": "Order API is active and functional (Module 7 Complete)",
    }), 200


@order_bp.route("", methods=["POST"])
@login_required_api
def place_order():
    """
    Execute order placement:
    Validates cart, stock, addresses, recalculates prices, creates Order and OrderItems,
    decrements stock, and clears the cart.
    """
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    address_id = data.get("address_id") or data.get("addressId")
    if address_id:
        try:
            address_id = int(address_id)
        except (ValueError, TypeError):
            address_id = None

    address_payload = data.get("address") or data.get("shippingAddress") or data.get("address_payload")
    payment_method = data.get("payment_method") or data.get("paymentMethod") or "COD"
    coupon_code = data.get("coupon_code") or data.get("coupon") or session.get("applied_coupon", "")
    buy_now_item = data.get("buy_now_item") or data.get("buyNowItem")

    # If buy_now flag is set without explicit item, check session buy_now
    if not buy_now_item and session.get("buy_now_context"):
        buy_now_item = session.get("buy_now_context")

    success, message, order = OrderService.create_order(
        user_id=user_id,
        address_id=address_id,
        address_payload=address_payload,
        payment_method=payment_method,
        coupon_code=coupon_code,
        buy_now_item=buy_now_item,
    )

    if not success:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": message}
        }), 400

    # Clear applied coupon and buy now context from session on successful order
    session.pop("applied_coupon", None)
    session.pop("buy_now_context", None)

    return jsonify({
        "success": True,
        "message": message,
        "data": order,
        "orderNumber": order["orderNumber"],
        "redirect_url": f"/order-confirmation/{order['orderNumber']}",
    }), 201


@order_bp.route("", methods=["GET"])
@login_required_api
def get_user_orders():
    """Retrieve all orders placed by the current user."""
    user_id = session.get("user_id")
    orders = OrderService.get_user_orders(user_id)
    return jsonify({
        "success": True,
        "data": orders,
        "count": len(orders),
    }), 200


@order_bp.route("/<identifier>", methods=["GET"])
@login_required_api
def get_order_detail(identifier: str):
    """Retrieve detailed order information by Order ID or Order Number."""
    user_id = session.get("user_id")

    # Try resolving by order_number first, then by integer ID
    order = OrderService.get_order_by_number(identifier, user_id=user_id)
    if not order and identifier.isdigit():
        order = OrderService.get_order_by_id(int(identifier), user_id=user_id)

    if not order:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": f"Order '{identifier}' not found."}
        }), 404

    return jsonify({
        "success": True,
        "data": order,
    }), 200


@order_bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required_api
def cancel_order(order_id: int):
    """Cancel customer order and restore stock."""
    user_id = session.get("user_id")
    success, message = OrderService.cancel_order(order_id, user_id)
    if not success:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": message}
        }), 400

    return jsonify({
        "success": True,
        "message": message,
    }), 200


@order_bp.route("/track/<order_number>", methods=["GET"])
def track_order(order_number: str):
    """Public or customer tracking timeline status for an order."""
    order = OrderService.get_order_by_number(order_number)
    if not order:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": "Order tracking record not found."}
        }), 404

    return jsonify({
        "success": True,
        "data": {
            "orderNumber": order["orderNumber"],
            "orderStatus": order["orderStatus"],
            "estimatedDelivery": order["estimatedDelivery"],
            "trackingHistory": order["trackingHistory"],
        }
    }), 200
