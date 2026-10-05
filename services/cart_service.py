from typing import Optional, Tuple, Dict, Any, List
from models import db, Cart, CartItem, Product


class CartService:
    """Service handling business logic for shopping cart operations, calculations, and stock validation."""

    VALID_COUPONS = {
        "EASE50": {
            "description": "50% off select orders up to $50 max discount",
            "percent": 50,
            "min_subtotal": 20.0,
            "max_discount": 50.0,
        },
        "SAVE10": {
            "description": "10% off entire order",
            "percent": 10,
            "min_subtotal": 0.0,
            "max_discount": 100.0,
        },
        "WELCOME15": {
            "description": "15% off first order",
            "percent": 15,
            "min_subtotal": 30.0,
            "max_discount": 75.0,
        },
    }

    @staticmethod
    def get_or_create_cart(user_id: int) -> Cart:
        """Fetch user cart or create a new one if not existing."""
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    @classmethod
    def get_cart_summary(
        cls,
        user_id: Optional[int] = None,
        guest_items: Optional[List[Dict[str, Any]]] = None,
        coupon_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate complete cart totals, item details, shipping, discounts, and item counts."""
        items_list = []
        subtotal = 0.0
        total_quantity = 0

        if user_id:
            cart = cls.get_or_create_cart(user_id)
            db_items = CartItem.query.filter_by(cart_id=cart.id).all()
            for itm in db_items:
                if itm.product and itm.product.is_active:
                    item_dict = itm.to_dict()
                    subtotal += item_dict["subtotal"]
                    total_quantity += itm.quantity
                    items_list.append(item_dict)
                elif itm.product and not itm.product.is_active:
                    # Inactive item: mark notice or auto-remove
                    db.session.delete(itm)
            db.session.commit()
        elif guest_items:
            for g_item in guest_items:
                p_id = g_item.get("product_id") or g_item.get("id")
                qty = int(g_item.get("quantity", 1))
                if p_id and qty > 0:
                    prod = Product.query.get(p_id)
                    if prod and prod.is_active:
                        item_subtotal = round(float(prod.price * qty), 2)
                        subtotal += item_subtotal
                        total_quantity += qty
                        items_list.append({
                            "id": None,
                            "product_id": prod.id,
                            "product": prod.to_dict(),
                            "quantity": qty,
                            "subtotal": item_subtotal,
                        })

        subtotal = round(subtotal, 2)

        # Shipping logic: Free shipping over $50, else $5.00 flat (0 if cart empty)
        shipping = 0.0
        if subtotal > 0:
            shipping = 0.0 if subtotal >= 50.0 else 5.00

        # Coupon Discount calculation
        discount_amount = 0.0
        coupon_details = None
        if coupon_code and subtotal > 0:
            valid, msg, disc, details = cls.validate_coupon(coupon_code, subtotal)
            if valid:
                discount_amount = disc
                coupon_details = details

        total_amount = max(0.0, round(subtotal - discount_amount + shipping, 2))

        return {
            "items": items_list,
            "items_count": len(items_list),
            "total_quantity": total_quantity,
            "subtotal": subtotal,
            "shipping": shipping,
            "free_shipping_eligible": subtotal >= 50.0,
            "free_shipping_threshold": 50.0,
            "amount_needed_for_free_shipping": max(0.0, round(50.0 - subtotal, 2)) if subtotal < 50.0 else 0.0,
            "discount": discount_amount,
            "coupon": coupon_details,
            "total": total_amount,
        }

    @classmethod
    def add_to_cart(
        cls,
        user_id: int,
        product_id: int,
        quantity: int = 1
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add product to user's cart with inventory and status validation."""
        if quantity <= 0:
            return False, "Quantity must be at least 1.", None

        product = Product.query.filter_by(id=product_id).first()
        if not product or not product.is_active:
            return False, "Product is not available or inactive.", None

        if product.stock <= 0:
            return False, f"Sorry, '{product.name}' is currently out of stock.", None

        cart = cls.get_or_create_cart(user_id)
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()

        current_qty = cart_item.quantity if cart_item else 0
        new_qty = current_qty + quantity

        if new_qty > product.stock:
            available_to_add = product.stock - current_qty
            if available_to_add <= 0:
                return False, f"Cannot add more. You already have the maximum available stock ({product.stock}) in your cart.", None
            return False, f"Cannot add {quantity} units. Only {available_to_add} more unit(s) available in stock.", None

        if cart_item:
            cart_item.quantity = new_qty
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=new_qty)
            db.session.add(cart_item)

        db.session.commit()
        return True, f"Added {product.name} to cart.", cart_item.to_dict()

    @classmethod
    def update_cart_item(
        cls,
        user_id: int,
        product_id: int,
        quantity: int
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update quantity of an existing item in the user's cart."""
        cart = cls.get_or_create_cart(user_id)
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

        if not cart_item:
            return False, "Item not found in cart.", None

        # Setting quantity to 0 removes the item
        if quantity <= 0:
            prod_name = cart_item.product.name if cart_item.product else "Item"
            db.session.delete(cart_item)
            db.session.commit()
            return True, f"Removed {prod_name} from cart.", None

        product = cart_item.product
        if not product or not product.is_active:
            db.session.delete(cart_item)
            db.session.commit()
            return False, "Product is no longer available and was removed from cart.", None

        if quantity > product.stock:
            return False, f"Cannot set quantity to {quantity}. Only {product.stock} units available in stock.", None

        cart_item.quantity = quantity
        db.session.commit()
        return True, f"Updated quantity to {quantity}.", cart_item.to_dict()

    @classmethod
    def remove_from_cart(cls, user_id: int, product_id: int) -> Tuple[bool, str]:
        """Remove a product from the user's cart."""
        cart = cls.get_or_create_cart(user_id)
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

        if not cart_item:
            return False, "Item not found in cart."

        prod_name = cart_item.product.name if cart_item.product else "Item"
        db.session.delete(cart_item)
        db.session.commit()
        return True, f"Removed {prod_name} from cart."

    @classmethod
    def clear_cart(cls, user_id: int) -> Tuple[bool, str]:
        """Clear all items from user's shopping cart."""
        cart = cls.get_or_create_cart(user_id)
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()
        return True, "Cart has been cleared."

    @classmethod
    def validate_coupon(
        cls,
        code: str,
        subtotal: float
    ) -> Tuple[bool, str, float, Optional[Dict[str, Any]]]:
        """Validate coupon code and return discount amount and details."""
        if not code or not code.strip():
            return False, "Please provide a coupon code.", 0.0, None

        normalized_code = code.strip().upper()
        coupon_data = cls.VALID_COUPONS.get(normalized_code)

        if not coupon_data:
            return False, f"Coupon code '{normalized_code}' is invalid or expired.", 0.0, None

        if subtotal < coupon_data["min_subtotal"]:
            return (
                False,
                f"Coupon '{normalized_code}' requires a minimum subtotal of ${coupon_data['min_subtotal']:.2f}.",
                0.0,
                None,
            )

        # Calculate percentage discount
        calculated_discount = (subtotal * coupon_data["percent"]) / 100.0
        final_discount = min(calculated_discount, coupon_data["max_discount"])
        final_discount = round(final_discount, 2)

        details = {
            "code": normalized_code,
            "description": coupon_data["description"],
            "percent": coupon_data["percent"],
            "discount_amount": final_discount,
        }

        return True, f"Coupon '{normalized_code}' applied successfully!", final_discount, details

    @classmethod
    def sync_guest_cart(
        cls,
        user_id: int,
        guest_items: List[Dict[str, Any]]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Merge guest localStorage items into authenticated user database cart upon login."""
        if not guest_items:
            return True, "No items to sync.", cls.get_cart_summary(user_id)

        merged_count = 0
        for item in guest_items:
            product_id = item.get("product_id") or item.get("id")
            quantity = int(item.get("quantity", 1))
            if product_id and quantity > 0:
                success, _, _ = cls.add_to_cart(user_id, int(product_id), quantity)
                if success:
                    merged_count += 1

        summary = cls.get_cart_summary(user_id)
        return True, f"Merged {merged_count} item(s) into your cart.", summary
