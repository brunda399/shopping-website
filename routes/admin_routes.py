from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from services.admin_service import AdminService
from services.product_service import ProductService
from utils.auth_decorators import admin_required

# API Blueprint for administrative statistics and programmatic endpoints
admin_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")

# Web Blueprint for administrative management dashboard UI
admin_web_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ------------------------------------------------------------------------------
# Admin API Endpoints
# ------------------------------------------------------------------------------

@admin_bp.route("/stats", methods=["GET"])
@admin_required
def get_stats():
    """Foundation endpoint for admin dashboard summary statistics."""
    stats = AdminService.get_dashboard_stats()
    # Enrich with catalog metrics
    products = ProductService.get_all_products(is_active=None)
    categories = ProductService.get_all_categories()
    
    total_products = len(products)
    active_products = sum(1 for p in products if p.get("is_active"))
    low_stock = sum(1 for p in products if 0 < p.get("stock", 0) <= 5)
    out_of_stock = sum(1 for p in products if p.get("stock", 0) <= 0)

    stats.update({
        "total_products": total_products,
        "active_products": active_products,
        "low_stock_products": low_stock,
        "out_of_stock_products": out_of_stock,
        "total_categories": len(categories),
    })

    return jsonify({
        "success": True,
        "data": stats,
    }), 200


# ------------------------------------------------------------------------------
# Admin Web UI Controllers (Module 3 Product Management)
# ------------------------------------------------------------------------------

@admin_web_bp.route("", methods=["GET"])
@admin_web_bp.route("/products", methods=["GET"])
@admin_required
def products_dashboard():
    """Render the Product & Category Management dashboard."""
    # Retrieve all products (active and inactive) for admin management
    products = ProductService.get_all_products(is_active=None)
    categories = ProductService.get_all_categories()

    # Calculate live inventory counters
    total_products = len(products)
    active_count = sum(1 for p in products if p.get("is_active"))
    inactive_count = total_products - active_count
    low_stock_count = sum(1 for p in products if 0 < p.get("stock", 0) <= 5)
    out_of_stock_count = sum(1 for p in products if p.get("stock", 0) <= 0)

    stats = {
        "total_products": total_products,
        "active_products": active_count,
        "inactive_products": inactive_count,
        "low_stock": low_stock_count,
        "out_of_stock": out_of_stock_count,
        "total_categories": len(categories),
    }

    return render_template(
        "admin/products.html",
        products=products,
        categories=categories,
        stats=stats,
    )


@admin_web_bp.route("/products/create", methods=["POST"])
@admin_required
def create_product_form():
    """Handle product creation from web form submission."""
    name = request.form.get("name", "").strip()
    category_id = request.form.get("category_id")
    price = request.form.get("price")
    stock = request.form.get("stock")
    description = request.form.get("description", "").strip()
    rating = request.form.get("rating", 0.0)
    is_active = bool(request.form.get("is_active"))

    # Image handling: file upload takes precedence over text/emoji input
    image = request.form.get("image_url", "").strip()
    if "image_file" in request.files:
        file = request.files["image_file"]
        if file and file.filename:
            upload_dir = current_app.config.get("UPLOAD_FOLDER")
            save_success, path_or_err = ProductService.save_product_image(file, upload_dir)
            if not save_success:
                flash(f"Image upload error: {path_or_err}", "error")
                return redirect(url_for("admin.products_dashboard"))
            image = path_or_err

    success, message, _ = ProductService.create_product(
        name=name,
        category_id=category_id,
        price=price,
        stock=stock,
        description=description,
        image=image,
        rating=rating,
        is_active=is_active,
    )

    if success:
        flash(f"Product '{name}' was created successfully.", "success")
    else:
        flash(message, "error")

    return redirect(url_for("admin.products_dashboard"))


@admin_web_bp.route("/products/<int:product_id>/edit", methods=["POST"])
@admin_required
def edit_product_form(product_id: int):
    """Handle product edit form submission."""
    name = request.form.get("name", "").strip()
    category_id = request.form.get("category_id")
    price = request.form.get("price")
    stock = request.form.get("stock")
    description = request.form.get("description", "").strip()
    rating = request.form.get("rating")
    is_active = bool(request.form.get("is_active"))

    image = request.form.get("image_url", "").strip() or None
    if "image_file" in request.files:
        file = request.files["image_file"]
        if file and file.filename:
            upload_dir = current_app.config.get("UPLOAD_FOLDER")
            save_success, path_or_err = ProductService.save_product_image(file, upload_dir)
            if not save_success:
                flash(f"Image upload error: {path_or_err}", "error")
                return redirect(url_for("admin.products_dashboard"))
            image = path_or_err

    success, message, _ = ProductService.update_product(
        product_id=product_id,
        name=name,
        category_id=category_id,
        price=price,
        stock=stock,
        description=description,
        image=image,
        rating=rating,
        is_active=is_active,
    )

    if success:
        flash(f"Product #{product_id} updated successfully.", "success")
    else:
        flash(message, "error")

    return redirect(url_for("admin.products_dashboard"))


@admin_web_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product_form(product_id: int):
    """Handle product deletion from admin dashboard."""
    success, message = ProductService.delete_product(product_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    return redirect(url_for("admin.products_dashboard"))


@admin_web_bp.route("/products/<int:product_id>/toggle", methods=["POST"])
@admin_required
def toggle_product_form(product_id: int):
    """Quick toggle product active status from table action."""
    success, message, product = ProductService.toggle_product_status(product_id)
    if success:
        status_word = "Active" if product.get("is_active") else "Inactive"
        flash(f"Product #{product_id} is now {status_word}.", "info")
    else:
        flash(message, "error")
    return redirect(url_for("admin.products_dashboard"))


@admin_web_bp.route("/categories/create", methods=["POST"])
@admin_required
def create_category_form():
    """Handle category creation from admin dashboard."""
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    success, message, _ = ProductService.create_category(name, description)
    if success:
        flash(f"Category '{name}' created successfully.", "success")
    else:
        flash(message, "error")

    return redirect(url_for("admin.products_dashboard"))


@admin_web_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def delete_category_form(category_id: int):
    """Handle category deletion from admin dashboard."""
    success, message = ProductService.delete_category(category_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")

    return redirect(url_for("admin.products_dashboard"))
