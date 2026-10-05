"""Database schema migration utility for dynamic column addition in SQLite."""
from models import db
from utils.logger import log_info, log_error


def run_schema_migrations(app):
    """Ensure all required columns and tables exist in SQLite without data loss."""
    with app.app_context():
        try:
            # 1. Create any missing tables (addresses, reviews, etc.)
            db.create_all()

            with db.engine.connect() as conn:
                # Helper to get existing column names for a table
                def get_columns(table_name):
                    res = conn.execute(db.text(f"PRAGMA table_info({table_name})")).fetchall()
                    return [row[1] for row in res]

                # Migrations for 'products'
                prod_cols = get_columns("products")
                prod_migrations = [
                    ("slug", "VARCHAR(255)"),
                    ("sale_price", "FLOAT"),
                    ("discount_percentage", "INTEGER DEFAULT 0"),
                    ("currency", "VARCHAR(10) DEFAULT 'INR'"),
                    ("subcategory", "VARCHAR(100)"),
                    ("brand", "VARCHAR(100)"),
                    ("thumbnail", "VARCHAR(255)"),
                    ("images_json", "TEXT"),
                    ("review_count", "INTEGER DEFAULT 0"),
                    ("sku", "VARCHAR(80)"),
                    ("sizes_json", "TEXT"),
                    ("colors_json", "TEXT"),
                    ("variants_json", "TEXT"),
                    ("specifications_json", "TEXT"),
                    ("tags_json", "TEXT"),
                    ("is_featured", "BOOLEAN DEFAULT 0"),
                    ("is_new", "BOOLEAN DEFAULT 0"),
                    ("is_best_seller", "BOOLEAN DEFAULT 0"),
                    ("is_active", "BOOLEAN DEFAULT 1"),
                ]
                for col_name, col_type in prod_migrations:
                    if col_name not in prod_cols:
                        conn.execute(db.text(f"ALTER TABLE products ADD COLUMN {col_name} {col_type}"))

                # Migrations for 'categories'
                cat_cols = get_columns("categories")
                if "updated_at" not in cat_cols:
                    conn.execute(db.text("ALTER TABLE categories ADD COLUMN updated_at DATETIME"))

                # Migrations for 'cart_items'
                cart_cols = get_columns("cart_items")
                cart_migrations = [
                    ("selected_size", "VARCHAR(50)"),
                    ("selected_color", "VARCHAR(50)"),
                    ("variant_id", "VARCHAR(100)"),
                ]
                for col_name, col_type in cart_migrations:
                    if col_name not in cart_cols:
                        conn.execute(db.text(f"ALTER TABLE cart_items ADD COLUMN {col_name} {col_type}"))

                # Migrations for 'orders'
                order_cols = get_columns("orders")
                order_migrations = [
                    ("order_number", "VARCHAR(50)"),
                    ("subtotal", "FLOAT DEFAULT 0.0"),
                    ("discount", "FLOAT DEFAULT 0.0"),
                    ("shipping", "FLOAT DEFAULT 0.0"),
                    ("tax", "FLOAT DEFAULT 0.0"),
                    ("state", "VARCHAR(100) DEFAULT 'India'"),
                    ("full_name", "VARCHAR(100)"),
                    ("shipping_address_json", "TEXT"),
                    ("payment_status", "VARCHAR(30) DEFAULT 'PENDING'"),
                    ("estimated_delivery", "VARCHAR(50)"),
                    ("tracking_history_json", "TEXT"),
                ]
                for col_name, col_type in order_migrations:
                    if col_name not in order_cols:
                        conn.execute(db.text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"))

                # Migrations for 'order_items'
                order_item_cols = get_columns("order_items")
                order_item_migrations = [
                    ("product_name", "VARCHAR(255)"),
                    ("image", "VARCHAR(255)"),
                    ("size", "VARCHAR(50)"),
                    ("color", "VARCHAR(50)"),
                    ("subtotal", "FLOAT"),
                ]
                for col_name, col_type in order_item_migrations:
                    if col_name not in order_item_cols:
                        conn.execute(db.text(f"ALTER TABLE order_items ADD COLUMN {col_name} {col_type}"))

                conn.commit()
                log_info("Database schema migration verification completed successfully")
        except Exception as e:
            log_error(f"Schema migration error: {e}")
