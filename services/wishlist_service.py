"""
ShopEase — Wishlist Service
Module 6: Wishlist System
"""

from typing import Optional, Tuple, Dict, Any, List
from models import db, Wishlist, Product, User
from services.cart_service import CartService


class WishlistService:
    """Business logic service for customer wishlist operations."""

    @classmethod
    def get_user_wishlist(cls, user_id: int) -> Dict[str, Any]:
        """Fetch all wishlist items for an authenticated user with full product metadata."""
        items = (
            Wishlist.query.filter_by(user_id=user_id)
            .order_by(Wishlist.created_at.desc())
            .all()
        )

        items_list = []
        for itm in items:
            prod = itm.product
            if prod:
                items_list.append({
                    "id": itm.id,
                    "product_id": prod.id,
                    "name": prod.name,
                    "description": prod.description,
                    "price": round(float(prod.price), 2),
                    "image": prod.image,
                    "category_id": prod.category_id,
                    "category_name": prod.category.name if prod.category else "General",
                    "stock": prod.stock,
                    "stock_status": prod.stock_status,
                    "is_in_stock": prod.stock > 0,
                    "rating": round(float(prod.rating), 1),
                    "is_active": prod.is_active,
                    "added_at": itm.created_at.isoformat() if itm.created_at else None,
                })

        return {
            "items_count": len(items_list),
            "items": items_list,
        }

    @classmethod
    def get_guest_wishlist(cls, product_ids: List[int]) -> Dict[str, Any]:
        """Hydrate product metadata for guest wishlist product IDs."""
        if not product_ids:
            return {"items_count": 0, "items": []}

        # Deduplicate while preserving order
        unique_ids = []
        for pid in product_ids:
            try:
                val = int(pid)
                if val not in unique_ids:
                    unique_ids.append(val)
            except (ValueError, TypeError):
                continue

        products = Product.query.filter(Product.id.in_(unique_ids), Product.is_active.is_(True)).all()
        prod_map = {p.id: p for p in products}

        items_list = []
        for pid in unique_ids:
            if pid in prod_map:
                prod = prod_map[pid]
                items_list.append({
                    "id": pid,
                    "product_id": prod.id,
                    "name": prod.name,
                    "description": prod.description,
                    "price": round(float(prod.price), 2),
                    "image": prod.image,
                    "category_id": prod.category_id,
                    "category_name": prod.category.name if prod.category else "General",
                    "stock": prod.stock,
                    "stock_status": prod.stock_status,
                    "is_in_stock": prod.stock > 0,
                    "rating": round(float(prod.rating), 1),
                    "is_active": prod.is_active,
                    "added_at": None,
                })

        return {
            "items_count": len(items_list),
            "items": items_list,
        }

    @classmethod
    def add_to_wishlist(cls, user_id: int, product_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add a product to user's saved wishlist."""
        product = Product.query.filter_by(id=product_id).first()
        if not product or not product.is_active:
            return False, "Product is not available or inactive.", None

        existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            return True, f"'{product.name}' is already in your wishlist.", existing.to_dict()

        wishlist_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()

        return True, f"Added '{product.name}' to your wishlist!", wishlist_item.to_dict()

    @classmethod
    def remove_from_wishlist(cls, user_id: int, product_id: int) -> Tuple[bool, str]:
        """Remove a product from user's wishlist."""
        item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if not item:
            return False, "Item was not found in your wishlist."

        prod_name = item.product.name if item.product else "Item"
        db.session.delete(item)
        db.session.commit()

        return True, f"Removed '{prod_name}' from your wishlist."

    @classmethod
    def toggle_wishlist(cls, user_id: int, product_id: int) -> Tuple[bool, str, bool, Optional[Dict[str, Any]]]:
        """
        Toggle product in/out of wishlist.
        Returns (success, message, is_in_wishlist, data)
        """
        product = Product.query.filter_by(id=product_id).first()
        if not product or not product.is_active:
            return False, "Product is not available or inactive.", False, None

        existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return True, f"Removed '{product.name}' from your wishlist.", False, None
        else:
            new_item = Wishlist(user_id=user_id, product_id=product_id)
            db.session.add(new_item)
            db.session.commit()
            return True, f"Added '{product.name}' to your wishlist!", True, new_item.to_dict()

    @classmethod
    def clear_wishlist(cls, user_id: int) -> Tuple[bool, str]:
        """Empty all items from user's wishlist."""
        Wishlist.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return True, "Your wishlist has been cleared."

    @classmethod
    def move_to_cart(cls, user_id: int, product_id: int, quantity: int = 1) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Move a specific product from wishlist to shopping cart."""
        product = Product.query.filter_by(id=product_id).first()
        if not product or not product.is_active:
            return False, "Product is no longer available.", None

        if product.stock <= 0:
            return False, f"Sorry, '{product.name}' is currently out of stock.", None

        # Add to cart
        success, message, cart_item = CartService.add_to_cart(user_id, product_id, quantity)
        if not success:
            return False, message, None

        # Remove from wishlist once added to cart
        wishlist_item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if wishlist_item:
            db.session.delete(wishlist_item)
            db.session.commit()

        return True, f"Moved '{product.name}' to your shopping cart!", cart_item

    @classmethod
    def move_all_to_cart(cls, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Transfer all in-stock wishlist items to shopping cart."""
        items = Wishlist.query.filter_by(user_id=user_id).all()
        if not items:
            return False, "Your wishlist is empty.", {"moved_count": 0, "skipped_count": 0}

        moved_count = 0
        skipped_count = 0

        for itm in list(items):
            prod = itm.product
            if prod and prod.is_active and prod.stock > 0:
                success, _, _ = CartService.add_to_cart(user_id, prod.id, 1)
                if success:
                    db.session.delete(itm)
                    moved_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1

        db.session.commit()

        msg = f"Moved {moved_count} item(s) to your shopping cart."
        if skipped_count > 0:
            msg += f" ({skipped_count} item(s) were out of stock or unavailable)."

        return True, msg, {"moved_count": moved_count, "skipped_count": skipped_count}

    @classmethod
    def sync_guest_wishlist(cls, user_id: int, guest_product_ids: List[int]) -> Tuple[bool, str, Dict[str, Any]]:
        """Merge guest localStorage product IDs into database wishlist upon authentication."""
        if not guest_product_ids:
            summary = cls.get_user_wishlist(user_id)
            return True, "Wishlist is already synchronized.", summary

        added_count = 0
        for pid in guest_product_ids:
            try:
                product_id = int(pid)
            except (ValueError, TypeError):
                continue

            product = Product.query.filter_by(id=product_id, is_active=True).first()
            if not product:
                continue

            existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not existing:
                new_item = Wishlist(user_id=user_id, product_id=product_id)
                db.session.add(new_item)
                added_count += 1

        db.session.commit()
        summary = cls.get_user_wishlist(user_id)

        msg = f"Synchronized wishlist ({added_count} new item(s) added)." if added_count > 0 else "Wishlist synchronized."
        return True, msg, summary
