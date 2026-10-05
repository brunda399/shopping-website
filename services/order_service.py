"""Service handling order creation, server-side financial calculations, stock decrement, and tracking."""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from models import db, Order, OrderItem, Product, Cart, CartItem, Address, User
from services.cart_service import CartService
from services.address_service import AddressService
from utils.logger import log_info, log_error


class OrderService:
    """Service orchestrating checkout verification, order creation, and fulfillment tracking."""

    @staticmethod
    def generate_order_number() -> str:
        """Generate human-readable, unique e-commerce order identifier."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_suffix = uuid.uuid4().hex[:6].upper()
        return f"ORD-{date_str}-{rand_suffix}"

    @classmethod
    def calculate_order_financials(
        cls,
        items_data: List[Dict[str, Any]],
        coupon_code: Optional[str] = None
    ) -> Tuple[float, float, float, float, float, Optional[Dict[str, Any]]]:
        """Strict server-side calculation of Subtotal, Discount, Shipping, Tax, and Grand Total."""
        subtotal = 0.0
        for itm in items_data:
            p = itm["product"]
            qty = itm["quantity"]
            unit_price = p.effective_price
            subtotal += unit_price * qty

        subtotal = round(subtotal, 2)

        # Shipping: Free shipping over 50.0, else 5.0
        shipping = 0.0
        if subtotal > 0:
            shipping = 0.0 if subtotal >= 50.0 else 5.0

        # Coupon Discount
        discount = 0.0
        coupon_details = None
        if coupon_code and subtotal > 0:
            valid, msg, disc, details = CartService.validate_coupon(coupon_code, subtotal)
            if valid:
                discount = disc
                coupon_details = details

        # Tax: included in item prices
        tax = 0.0

        # Grand Total
        grand_total = max(0.0, round(subtotal - discount + shipping + tax, 2))

        return subtotal, discount, shipping, tax, grand_total, coupon_details

    @classmethod
    def create_order(
        cls,
        user_id: int,
        address_id: Optional[int] = None,
        address_payload: Optional[Dict[str, Any]] = None,
        payment_method: str = "COD",
        coupon_code: Optional[str] = None,
        buy_now_item: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Execute full checkout transaction:
        1. Validate authentication & user
        2. Validate items & stock
        3. Recalculate financials strictly on server
        4. Validate & snapshot delivery address
        5. Create Order & OrderItem records
        6. Decrement product stock
        7. Clear shopping cart
        8. Return order confirmation
        """
        user = User.query.get(user_id)
        if not user:
            return False, "User account not found.", None

        # 1. Resolve Items to Purchase
        checkout_items = []

        if buy_now_item:
            # Direct Buy-Now flow: single product variant
            prod_id = buy_now_item.get("product_id") or buy_now_item.get("id")
            qty = int(buy_now_item.get("quantity", 1))
            size = buy_now_item.get("size") or buy_now_item.get("selected_size")
            color = buy_now_item.get("color") or buy_now_item.get("selected_color")

            if not prod_id or qty <= 0:
                return False, "Invalid Buy Now product parameters.", None

            product = Product.query.get(prod_id)
            if not product or not product.is_active:
                return False, "The requested product is currently unavailable.", None

            if product.stock < qty:
                return False, f"Insufficient stock for '{product.name}'. Available: {product.stock}.", None

            checkout_items.append({
                "product": product,
                "quantity": qty,
                "size": size,
                "color": color,
            })
        else:
            # Standard Cart Checkout flow
            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart:
                return False, "Your shopping cart is empty.", None

            cart_db_items = CartItem.query.filter_by(cart_id=cart.id).all()
            if not cart_db_items:
                return False, "Your shopping cart is empty.", None

            for ci in cart_db_items:
                prod = ci.product
                if not prod or not prod.is_active:
                    return False, f"A product in your cart is no longer active.", None

                if prod.stock < ci.quantity:
                    return False, f"Cannot proceed. '{prod.name}' only has {prod.stock} unit(s) available, but {ci.quantity} requested.", None

                checkout_items.append({
                    "product": prod,
                    "quantity": ci.quantity,
                    "size": ci.selected_size,
                    "color": ci.selected_color,
                })

        if not checkout_items:
            return False, "No valid items to place an order.", None

        # 2. Strict Server Financial Calculations
        subtotal, discount, shipping, tax, grand_total, coupon_info = cls.calculate_order_financials(
            checkout_items, coupon_code=coupon_code
        )

        # 3. Resolve Delivery Address & Snapshot
        selected_address = None
        if address_id:
            selected_address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        elif address_payload:
            # Quick address creation or pass-through
            succ, msg, new_addr = AddressService.create_address(user_id, address_payload)
            if succ and new_addr:
                selected_address = Address.query.get(new_addr["id"])

        if not selected_address:
            # Fallback to user's default address
            selected_address = Address.query.filter_by(user_id=user_id, is_default=True).first()

        if not selected_address:
            # Fallback to any user address
            selected_address = Address.query.filter_by(user_id=user_id).first()

        if not selected_address:
            return False, "Please select or provide a valid delivery address.", None

        # Prepare Address Snapshot
        addr_dict = {
            "fullName": selected_address.full_name,
            "full_name": selected_address.full_name,
            "phone": selected_address.phone,
            "addressLine1": selected_address.address_line1,
            "address_line1": selected_address.address_line1,
            "addressLine2": selected_address.address_line2 or "",
            "city": selected_address.city,
            "state": selected_address.state,
            "postalCode": selected_address.postal_code,
            "postal_code": selected_address.postal_code,
            "country": selected_address.country,
            "landmark": selected_address.landmark or "",
        }

        # 4. Resolve Payment Method & Status
        normalized_payment = payment_method.strip().upper()
        if normalized_payment in ["ONLINE", "CARD", "UPI", "NETBANKING"]:
            payment_status = "PAID"
        else:
            normalized_payment = "COD"
            payment_status = "COD_PENDING"

        # 5. Estimated Delivery calculation (4 business days)
        est_date = datetime.utcnow() + timedelta(days=4)
        estimated_delivery_str = est_date.strftime("%A, %b %d, %Y")

        # 6. Database Transaction
        try:
            order_number = cls.generate_order_number()

            # Tracking timeline initialized
            now_iso = datetime.utcnow().strftime("%b %d, %Y, %I:%M %p")
            tracking_timeline = [
                {"status": Order.STATUS_PLACED, "label": "Order Placed", "timestamp": now_iso, "done": True, "current": True},
                {"status": Order.STATUS_CONFIRMED, "label": "Order Confirmed", "timestamp": "Pending dispatch", "done": False, "current": False},
                {"status": Order.STATUS_PACKED, "label": "Packed", "timestamp": "Warehouse", "done": False, "current": False},
                {"status": Order.STATUS_SHIPPED, "label": "Shipped", "timestamp": "In transit", "done": False, "current": False},
                {"status": Order.STATUS_OUT_FOR_DELIVERY, "label": "Out for Delivery", "timestamp": "Courier partner", "done": False, "current": False},
                {"status": Order.STATUS_DELIVERED, "label": "Delivered", "timestamp": estimated_delivery_str, "done": False, "current": False},
            ]

            order = Order(
                user_id=user_id,
                order_number=order_number,
                subtotal=subtotal,
                discount=discount,
                shipping=shipping,
                tax=tax,
                total_amount=grand_total,
                address=selected_address.address_line1,
                city=selected_address.city,
                state=selected_address.state,
                pincode=selected_address.postal_code,
                phone=selected_address.phone,
                full_name=selected_address.full_name,
                shipping_address_json=json.dumps(addr_dict),
                payment_method=normalized_payment,
                payment_status=payment_status,
                status=Order.STATUS_PLACED,
                estimated_delivery=estimated_delivery_str,
                tracking_history_json=json.dumps(tracking_timeline),
            )
            db.session.add(order)
            db.session.flush()

            # 7. Create OrderItems & Decrement Inventory
            for itm in checkout_items:
                prod = itm["product"]
                qty = itm["quantity"]
                size = itm["size"]
                color = itm["color"]
                purchase_price = prod.effective_price
                line_subtotal = round(purchase_price * qty, 2)

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    image=prod.image,
                    size=size,
                    color=color,
                    quantity=qty,
                    price=purchase_price,
                    subtotal=line_subtotal,
                )
                db.session.add(order_item)

                # Stock Management: Decrement inventory safely
                prod.stock = max(0, prod.stock - qty)

            # 8. Clear Cart if this was a normal cart checkout
            if not buy_now_item:
                cart = Cart.query.filter_by(user_id=user_id).first()
                if cart:
                    CartItem.query.filter_by(cart_id=cart.id).delete()

            db.session.commit()
            log_info(f"Order #{order.order_number} successfully placed for User #{user_id}. Grand Total: Rs. {grand_total}")
            return True, "Order placed successfully!", order.to_dict()

        except Exception as e:
            db.session.rollback()
            log_error(f"Failed to place order: {e}")
            return False, f"Failed to place order due to a system error. Please try again.", None

    @staticmethod
    def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all customer orders sorted newest first."""
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return [order.to_dict() for order in orders]

    @staticmethod
    def get_order_by_number(order_number: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch order by its human-readable order number with authorization check."""
        query = Order.query.filter_by(order_number=order_number)
        if user_id:
            query = query.filter_by(user_id=user_id)
        order = query.first()
        return order.to_dict() if order else None

    @staticmethod
    def get_order_by_id(order_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch order details by ID with optional authorization check."""
        query = Order.query.filter_by(id=order_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        order = query.first()
        return order.to_dict() if order else None

    @classmethod
    def cancel_order(cls, order_id: int, user_id: int) -> Tuple[bool, str]:
        """Cancel order and restore product inventory if eligible."""
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return False, "Order not found."

        if order.status in [Order.STATUS_DELIVERED, Order.STATUS_CANCELLED]:
            return False, f"Order cannot be cancelled in its current state ({order.status})."

        # Restore inventory
        for item in order.items:
            prod = Product.query.get(item.product_id)
            if prod:
                prod.stock += item.quantity

        order.status = Order.STATUS_CANCELLED
        order.payment_status = "REFUNDED" if order.payment_status == "PAID" else "CANCELLED"
        db.session.commit()
        return True, "Order has been cancelled and inventory restored."

    @classmethod
    def update_order_status(cls, order_id: int, new_status: str) -> Tuple[bool, str]:
        """Update order lifecycle status (Admin / System fulfillment)."""
        if new_status not in Order.ALL_STATUSES:
            return False, f"Invalid status: {new_status}"

        order = Order.query.get(order_id)
        if not order:
            return False, "Order not found."

        order.status = new_status
        db.session.commit()
        return True, f"Order status updated to {new_status}."
