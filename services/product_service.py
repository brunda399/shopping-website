import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from werkzeug.datastructures import FileStorage
from models import db, Product, Category
from utils.validators import (
    validate_non_empty_string,
    validate_positive_number,
    validate_integer,
    validate_image_file,
    generate_secure_image_filename,
)


class ProductService:
    """Service handling product catalog and category operations."""

    @staticmethod
    def get_all_products(
        category_id: Optional[int] = None,
        category_name: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: Optional[bool] = None,
        min_rating: Optional[float] = None,
        sort_by: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve products with advanced filtering, search, sorting, and pagination."""
        query = Product.query

        # Status filter (default to active for storefront if is_active is True)
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)

        # Category ID filter
        if category_id:
            query = query.filter(Product.category_id == category_id)

        # Category Name filter (case-insensitive with Shoes / Footwear synonym support)
        if category_name and category_name.strip():
            cat_query = category_name.strip()
            if cat_query.lower() in ("shoes", "footwear"):
                query = query.join(Product.category).filter(
                    (Category.name.ilike("footwear")) | (Category.name.ilike("shoes"))
                )
            else:
                query = query.join(Product.category).filter(Category.name.ilike(cat_query))

        # Price range filter
        if min_price is not None:
            query = query.filter(Product.price >= float(min_price))
        if max_price is not None:
            query = query.filter(Product.price <= float(max_price))

        # In-stock only filter
        if in_stock_only:
            query = query.filter(Product.stock > 0)

        # Minimum rating filter
        if min_rating is not None:
            query = query.filter(Product.rating >= float(min_rating))

        # Keyword search across name and description
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                (Product.name.ilike(term)) | (Product.description.ilike(term))
            )

        # Sorting logic
        if sort_by in ("price_asc", "price-low"):
            query = query.order_by(Product.price.asc())
        elif sort_by in ("price_desc", "price-high"):
            query = query.order_by(Product.price.desc())
        elif sort_by in ("rating", "rating_desc"):
            query = query.order_by(Product.rating.desc())
        elif sort_by == "stock_asc":
            query = query.order_by(Product.stock.asc())
        elif sort_by in ("name_asc", "alpha"):
            query = query.order_by(Product.name.asc())
        elif sort_by == "name_desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.created_at.desc())

        # Pagination
        if page and per_page:
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            return [p.to_dict() for p in pagination.items]

        products = query.all()
        return [p.to_dict() for p in products]

    @staticmethod
    def get_related_products(product_id: int, category_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """Retrieve active related products from the same category."""
        related = Product.query.filter(
            Product.id != product_id,
            Product.category_id == category_id,
            Product.is_active == True
        ).order_by(Product.rating.desc()).limit(limit).all()

        # If category has fewer products, fill with other active products
        if len(related) < limit:
            remaining = limit - len(related)
            existing_ids = [p.id for p in related] + [product_id]
            backfill = Product.query.filter(
                ~Product.id.in_(existing_ids),
                Product.is_active == True
            ).order_by(Product.rating.desc()).limit(remaining).all()
            related.extend(backfill)

        return [p.to_dict() for p in related]

    @staticmethod
    def get_product_by_id(product_id: int, only_active: bool = False) -> Optional[Dict[str, Any]]:
        """Fetch product dictionary by primary key ID."""
        if not product_id:
            return None
        product = db.session.get(Product, product_id)
        if not product:
            return None
        if only_active and not product.is_active:
            return None
        return product.to_dict()

    @staticmethod
    def get_product_model(product_id: int) -> Optional[Product]:
        """Fetch raw SQLAlchemy Product instance."""
        if not product_id:
            return None
        return db.session.get(Product, product_id)

    @staticmethod
    def create_product(
        name: str,
        category_id: int,
        price: Any,
        stock: Any,
        description: Optional[str] = None,
        image: Optional[str] = None,
        rating: float = 0.0,
        is_active: bool = True,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate and create a new product."""
        # 1. Validate Name
        valid_name, err = validate_non_empty_string(name, "Product name", max_length=150)
        if not valid_name:
            return False, err, None

        # 2. Validate Price
        valid_price, err = validate_positive_number(price, "Price", allow_zero=True)
        if not valid_price:
            return False, err, None

        # 3. Validate Stock
        valid_stock, err = validate_integer(stock, "Stock quantity", allow_zero=True)
        if not valid_stock:
            return False, err, None

        # 4. Validate Category
        if not category_id:
            return False, "Category is required.", None
        category = db.session.get(Category, int(category_id))
        if not category:
            return False, "Selected category does not exist.", None

        # 5. Clean / Default Values
        clean_desc = description.strip() if description else ""
        clean_image = image.strip() if image and image.strip() else "default-product.png"
        clean_price = round(float(price), 2)
        clean_stock = int(stock)
        clean_rating = max(0.0, min(5.0, float(rating))) if rating else 0.0

        try:
            product = Product(
                name=name.strip(),
                category_id=category.id,
                price=clean_price,
                stock=clean_stock,
                description=clean_desc,
                image=clean_image,
                rating=clean_rating,
                is_active=bool(is_active),
            )
            db.session.add(product)
            db.session.commit()
            return True, "Product created successfully.", product.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to create product: {str(e)}", None

    @staticmethod
    def update_product(
        product_id: int,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        price: Optional[Any] = None,
        stock: Optional[Any] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        rating: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update an existing product's fields with strict validation."""
        product = db.session.get(Product, product_id)
        if not product:
            return False, "Product not found.", None

        if name is not None:
            valid_name, err = validate_non_empty_string(name, "Product name", max_length=150)
            if not valid_name:
                return False, err, None
            product.name = name.strip()

        if price is not None:
            valid_price, err = validate_positive_number(price, "Price", allow_zero=True)
            if not valid_price:
                return False, err, None
            product.price = round(float(price), 2)

        if stock is not None:
            valid_stock, err = validate_integer(stock, "Stock quantity", allow_zero=True)
            if not valid_stock:
                return False, err, None
            product.stock = int(stock)

        if category_id is not None:
            category = db.session.get(Category, int(category_id))
            if not category:
                return False, "Selected category does not exist.", None
            product.category_id = category.id

        if description is not None:
            product.description = description.strip()

        if image is not None and image.strip():
            product.image = image.strip()

        if rating is not None:
            product.rating = max(0.0, min(5.0, float(rating)))

        if is_active is not None:
            product.is_active = bool(is_active)

        try:
            db.session.commit()
            return True, "Product updated successfully.", product.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update product: {str(e)}", None

    @staticmethod
    def delete_product(product_id: int) -> Tuple[bool, str]:
        """Safely delete a product or deactivate it if order history exists."""
        product = db.session.get(Product, product_id)
        if not product:
            return False, "Product not found."

        try:
            # Check if product is referenced in historical orders
            if hasattr(product, "order_items") and product.order_items.count() > 0:
                # Soft delete to preserve historical order invoice integrity
                product.is_active = False
                db.session.commit()
                return True, "Product has prior order history and was deactivated instead of deleted."

            db.session.delete(product)
            db.session.commit()
            return True, "Product deleted successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete product: {str(e)}"

    @staticmethod
    def toggle_product_status(product_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Toggle product between Active and Inactive."""
        product = db.session.get(Product, product_id)
        if not product:
            return False, "Product not found.", None

        try:
            product.is_active = not product.is_active
            db.session.commit()
            status_text = "activated" if product.is_active else "deactivated"
            return True, f"Product successfully {status_text}.", product.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to change product status: {str(e)}", None

    @staticmethod
    def update_stock(product_id: int, new_stock: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update available inventory count for a product."""
        valid_stock, err = validate_integer(new_stock, "Stock quantity", allow_zero=True)
        if not valid_stock:
            return False, err, None

        product = db.session.get(Product, product_id)
        if not product:
            return False, "Product not found.", None

        try:
            product.stock = int(new_stock)
            db.session.commit()
            return True, "Stock updated successfully.", product.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update stock: {str(e)}", None

    # --------------------------------------------------------------------------
    # Category Management
    # --------------------------------------------------------------------------

    @staticmethod
    def get_all_categories() -> List[Dict[str, Any]]:
        """Retrieve all categories with their product counts."""
        categories = Category.query.order_by(Category.name.asc()).all()
        return [c.to_dict() for c in categories]

    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Dict[str, Any]]:
        """Fetch category details by ID."""
        if not category_id:
            return None
        cat = db.session.get(Category, category_id)
        return cat.to_dict() if cat else None

    @staticmethod
    def create_category(name: str, description: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add a new product category."""
        valid_name, err = validate_non_empty_string(name, "Category name", max_length=80)
        if not valid_name:
            return False, err, None

        clean_name = name.strip()
        if Category.query.filter_by(name=clean_name).first():
            return False, f"Category '{clean_name}' already exists.", None

        try:
            category = Category(name=clean_name, description=description.strip() if description else None)
            db.session.add(category)
            db.session.commit()
            return True, "Category created successfully.", category.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to create category: {str(e)}", None

    @staticmethod
    def update_category(category_id: int, name: str, description: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update category name and description."""
        cat = db.session.get(Category, category_id)
        if not cat:
            return False, "Category not found.", None

        valid_name, err = validate_non_empty_string(name, "Category name", max_length=80)
        if not valid_name:
            return False, err, None

        clean_name = name.strip()
        existing = Category.query.filter_by(name=clean_name).first()
        if existing and existing.id != cat.id:
            return False, f"Another category named '{clean_name}' already exists.", None

        try:
            cat.name = clean_name
            cat.description = description.strip() if description else None
            db.session.commit()
            return True, "Category updated successfully.", cat.to_dict()
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update category: {str(e)}", None

    @staticmethod
    def delete_category(category_id: int) -> Tuple[bool, str]:
        """Delete a category if it contains no associated products."""
        cat = db.session.get(Category, category_id)
        if not cat:
            return False, "Category not found."

        if cat.products.count() > 0:
            return False, f"Cannot delete category '{cat.name}' because it contains {cat.products.count()} product(s)."

        try:
            db.session.delete(cat)
            db.session.commit()
            return True, f"Category '{cat.name}' deleted successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete category: {str(e)}"

    # --------------------------------------------------------------------------
    # Product Image Upload & Handling
    # --------------------------------------------------------------------------

    @staticmethod
    def save_product_image(file_storage: FileStorage, upload_folder: str) -> Tuple[bool, str]:
        """Sanitize, validate, and save an uploaded product image file."""
        if not file_storage or not file_storage.filename:
            return False, "No file was selected for upload."

        valid_ext, err = validate_image_file(file_storage.filename)
        if not valid_ext:
            return False, err

        # Generate secure filename to avoid collision and prevent path traversal
        filename = generate_secure_image_filename(file_storage.filename)
        os.makedirs(upload_folder, exist_ok=True)
        dest_path = Path(upload_folder) / filename

        try:
            file_storage.save(str(dest_path))
            # Store relative web path
            web_path = f"/static/images/products/{filename}"
            return True, web_path
        except Exception as e:
            return False, f"Failed to save image file: {str(e)}"

    # --------------------------------------------------------------------------
    # Initial Data Seeding
    # --------------------------------------------------------------------------

    @staticmethod
    def seed_initial_data() -> None:
        """Seed default categories and featured products if database is empty."""
        try:
            if Category.query.count() > 0:
                return

            categories_data = [
                ("Electronics", "Audio, smartphones & computing gadgets", "🎧"),
                ("Fashion", "Men & Women trendy apparel & clothing", "🧥"),
                ("Footwear", "Athletic sneakers, running & casual shoes", "👟"),
                ("Watches", "Smartwatches & luxury analog timepieces", "⌚"),
                ("Home & Living", "Modern home decor & smart living essentials", "🏠"),
                ("Accessories", "Travel backpacks, wallets & sunglasses", "🎒"),
            ]

            created_cats = {}
            for name, desc, icon in categories_data:
                cat = Category(name=name, description=desc)
                db.session.add(cat)
                db.session.flush()
                created_cats[name] = cat.id

            products_data = [
                {
                    "name": "Noise-Cancelling Wireless Headphones Pro",
                    "description": "Premium wireless over-ear headphones with active noise cancellation, 40-hour battery life, and crystal-clear acoustic fidelity.",
                    "price": 129.99,
                    "category_id": created_cats["Electronics"],
                    "image": "🎧",
                    "stock": 28,
                    "rating": 4.9,
                    "is_active": True,
                },
                {
                    "name": "Classic Mechanical Chronograph Watch",
                    "description": "Sapphire crystal glass with genuine leather strap, water-resistant to 50 meters with precision automatic movement.",
                    "price": 189.50,
                    "category_id": created_cats["Watches"],
                    "image": "⌚",
                    "stock": 14,
                    "rating": 4.8,
                    "is_active": True,
                },
                {
                    "name": "Ultra-Lightweight Performance Sneakers",
                    "description": "Ergonomic responsive cushioning engineered for everyday runs, gym sessions, and maximum all-day comfort.",
                    "price": 79.99,
                    "category_id": created_cats["Footwear"],
                    "image": "👟",
                    "stock": 45,
                    "rating": 4.7,
                    "is_active": True,
                },
                {
                    "name": "Waterproof Urban Commuter Backpack",
                    "description": "Weather-resistant Oxford fabric with padded 15.6-inch laptop compartment and hidden anti-theft zipper pockets.",
                    "price": 54.00,
                    "category_id": created_cats["Accessories"],
                    "image": "🎒",
                    "stock": 32,
                    "rating": 4.8,
                    "is_active": True,
                },
                {
                    "name": "Smart Fitness Tracker Band 5",
                    "description": "Always-on AMOLED display with heart rate monitoring, sleep analysis, SpO2 sensor, and 14-day battery life.",
                    "price": 49.99,
                    "category_id": created_cats["Electronics"],
                    "image": "📱",
                    "stock": 60,
                    "rating": 4.6,
                    "is_active": True,
                },
                {
                    "name": "Minimalist Polarized Sunglasses",
                    "description": "UV400 protection polarized lenses with lightweight titanium-alloy frames for crisp glare-free vision.",
                    "price": 34.50,
                    "category_id": created_cats["Accessories"],
                    "image": "🕶️",
                    "stock": 25,
                    "rating": 4.7,
                    "is_active": True,
                },
                {
                    "name": "Ceramic Pour-Over Coffee Maker Set",
                    "description": "Artisan handmade matte ceramic dripper with heat-resistant borosilicate glass server and reusable mesh filter.",
                    "price": 42.00,
                    "category_id": created_cats["Home & Living"],
                    "image": "☕",
                    "stock": 19,
                    "rating": 4.9,
                    "is_active": True,
                },
                {
                    "name": "Premium Cotton Relaxed Hoodie",
                    "description": "Crafted from 100% heavyweight French terry cotton with ribbed cuffs and fleece-lined double-layer hood.",
                    "price": 59.00,
                    "category_id": created_cats["Fashion"],
                    "image": "🧥",
                    "stock": 38,
                    "rating": 4.8,
                    "is_active": True,
                },
            ]

            for item in products_data:
                prod = Product(**item)
                db.session.add(prod)

            db.session.commit()
        except Exception:
            db.session.rollback()
