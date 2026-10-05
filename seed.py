"""
Repeatable CLI Seed Script for ShopEase E-Commerce Platform.
Run `python seed.py` to populate or refresh the catalog with realistic products,
categories, Kurti collections, and default accounts without duplicate entries.
"""
import sys
from app import create_app
from data.seed_catalog import seed_large_catalog
from models import db, Product, Category, User
from utils.logger import log_info

def run_seed():
    app = create_app()
    with app.app_context():
        print("-> Running database schema verification...")
        from utils.db_migration import run_schema_migrations
        run_schema_migrations(app)

        print("-> Seeding multi-category catalog and Kurti collection...")
        seed_large_catalog()

        total_prods = Product.query.count()
        total_cats = Category.query.count()
        total_users = User.query.count()
        print(f"-> Seed completed successfully! Verified {total_prods} products across {total_cats} categories ({total_users} user accounts).")

if __name__ == "__main__":
    run_seed()
