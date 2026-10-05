from flask import Blueprint, jsonify, request, current_app, session
from services.product_service import ProductService
from utils.auth_decorators import admin_required

product_bp = Blueprint("product_api", __name__, url_prefix="/api/products")


# ------------------------------------------------------------------------------
# Public & Filterable Product Endpoints
# ------------------------------------------------------------------------------

@product_bp.route("", methods=["GET"])
def get_products():
    """Fetch product catalog with optional query, category filter, price, stock, rating, sorting, and pagination."""
    category_id = request.args.get("category_id", type=int)
    category_name = request.args.get("category") or request.args.get("category_name")
    subcategory = request.args.get("subcategory")
    brand = request.args.get("brand")
    color = request.args.get("color")
    size = request.args.get("size")
    search = request.args.get("q") or request.args.get("search")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    in_stock = request.args.get("in_stock", "").lower() in ("true", "1") or request.args.get("in_stock_only", "").lower() in ("true", "1")
    min_rating = request.args.get("min_rating", type=float)
    sort_by = request.args.get("sort_by")
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)

    # Allow administrators to view inactive products if explicitly requested
    include_inactive = request.args.get("include_inactive", "").lower() in ("true", "1")
    is_admin = session.get("user_role") == "ADMIN"
    
    is_active_filter = None if (include_inactive and is_admin) else True

    products = ProductService.get_all_products(
        category_id=category_id,
        category_name=category_name,
        subcategory=subcategory,
        brand=brand,
        color=color,
        size=size,
        search=search,
        is_active=is_active_filter,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock if in_stock else None,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )

    response_payload = {
        "success": True,
        "count": len(products),
        "data": products,
    }
    if page is not None:
        response_payload["pagination"] = {
            "page": page,
            "per_page": per_page or 12,
            "total_items": len(products)
        }

    return jsonify(response_payload), 200


@product_bp.route("/suggestions", methods=["GET"])
def get_suggestions():
    """Retrieve auto-complete search suggestions."""
    q = request.args.get("q", "")
    limit = request.args.get("limit", 8, type=int)
    suggestions = ProductService.get_search_suggestions(q, limit=limit)
    return jsonify({
        "success": True,
        "query": q,
        "data": suggestions,
    }), 200



@product_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """Retrieve full details of a specific product."""
    is_admin = session.get("user_role") == "ADMIN"
    product = ProductService.get_product_by_id(product_id, only_active=not is_admin)
    if not product:
        return jsonify({
            "success": False,
            "error": {
                "code": 404,
                "message": f"Product #{product_id} not found or inactive."
            }
        }), 404

    return jsonify({
        "success": True,
        "data": product
    }), 200


@product_bp.route("/<int:product_id>/related", methods=["GET"])
def get_related_products_endpoint(product_id: int):
    """Retrieve related recommendations for a product."""
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": f"Product #{product_id} not found."}
        }), 404

    limit = request.args.get("limit", default=4, type=int)
    category_id = product.get("category_id")
    related = ProductService.get_related_products(product_id, category_id, limit=limit)
    return jsonify({
        "success": True,
        "data": related,
        "count": len(related)
    }), 200


@product_bp.route("/<int:product_id>/reviews", methods=["GET"])
def get_product_reviews(product_id: int):
    """Retrieve all verified reviews and star rating distribution for a product."""
    from models import Review
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": "Product not found."}
        }), 404

    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    review_list = [r.to_dict() for r in reviews]

    distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        star = int(round(r.rating))
        if 1 <= star <= 5:
            distribution[star] += 1

    return jsonify({
        "success": True,
        "product_id": product_id,
        "count": len(review_list),
        "rating": product["rating"],
        "distribution": distribution,
        "data": review_list,
    }), 200


@product_bp.route("/<int:product_id>/reviews", methods=["POST"])
def submit_product_review(product_id: int):
    """Submit a customer rating and review for a product with verification."""
    from flask import session
    from models import db, Review, OrderItem, Order, Product
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "error": {"code": 401, "message": "Please sign in to submit a review."}
        }), 401

    product = Product.query.get(product_id)
    if not product:
        return jsonify({
            "success": False,
            "error": {"code": 404, "message": "Product not found."}
        }), 404

    data = request.get_json(silent=True) or request.form.to_dict() or {}
    rating = data.get("rating", 5)
    title = (data.get("title") or "").strip()
    comment = (data.get("comment") or "").strip()

    try:
        rating = float(rating)
        if not (1.0 <= rating <= 5.0):
            return jsonify({
                "success": False,
                "error": {"code": 400, "message": "Rating must be between 1 and 5 stars."}
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Rating must be a numeric value between 1 and 5."}
        }), 400

    if not comment:
        return jsonify({
            "success": False,
            "error": {"code": 400, "message": "Please write a comment for your review."}
        }), 400

    # Verify purchase
    has_purchased = OrderItem.query.join(Order).filter(
        Order.user_id == user_id,
        OrderItem.product_id == product_id
    ).count() > 0

    rev = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        title=title if title else None,
        comment=comment,
        is_verified_purchase=has_purchased,
    )
    db.session.add(rev)
    db.session.flush()

    # Recalculate average product rating
    all_revs = Review.query.filter_by(product_id=product_id).all()
    avg_r = sum(r.rating for r in all_revs) / len(all_revs)
    product.rating = round(avg_r, 1)
    product.review_count = len(all_revs)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Review submitted successfully!",
        "data": rev.to_dict(),
    }), 201



# ------------------------------------------------------------------------------
# Admin Product Management Endpoints (CRUD)
# ------------------------------------------------------------------------------

@product_bp.route("", methods=["POST"])
@admin_required
def create_product():
    """Admin endpoint to create a new product."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    name = data.get("name", "")
    category_id = data.get("category_id")
    price = data.get("price")
    stock = data.get("stock", 0)
    description = data.get("description", "")
    image = data.get("image", "")
    rating = data.get("rating", 0.0)
    is_active = data.get("is_active", True)
    if isinstance(is_active, str):
        is_active = is_active.lower() in ("true", "1", "on")

    # Handle image upload if provided in multipart form
    if "image_file" in request.files:
        file = request.files["image_file"]
        if file and file.filename:
            upload_dir = current_app.config.get("UPLOAD_FOLDER")
            save_success, path_or_err = ProductService.save_product_image(file, upload_dir)
            if not save_success:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": 400,
                        "message": path_or_err
                    }
                }), 400
            image = path_or_err

    success, message, product = ProductService.create_product(
        name=name,
        category_id=category_id,
        price=price,
        stock=stock,
        description=description,
        image=image,
        rating=rating,
        is_active=is_active,
    )

    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 400,
                "message": message
            }
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "data": product
    }), 201


@product_bp.route("/<int:product_id>", methods=["PUT", "POST"])
@admin_required
def update_product(product_id: int):
    """Admin endpoint to update product details."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    name = data.get("name")
    category_id = data.get("category_id")
    price = data.get("price")
    stock = data.get("stock")
    description = data.get("description")
    image = data.get("image")
    rating = data.get("rating")
    is_active = data.get("is_active")
    if isinstance(is_active, str):
        is_active = is_active.lower() in ("true", "1", "on")

    # Handle replacement image upload if provided
    if "image_file" in request.files:
        file = request.files["image_file"]
        if file and file.filename:
            upload_dir = current_app.config.get("UPLOAD_FOLDER")
            save_success, path_or_err = ProductService.save_product_image(file, upload_dir)
            if not save_success:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": 400,
                        "message": path_or_err
                    }
                }), 400
            image = path_or_err

    success, message, product = ProductService.update_product(
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

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({
            "success": False,
            "error": {
                "code": status_code,
                "message": message
            }
        }), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": product
    }), 200


@product_bp.route("/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id: int):
    """Admin endpoint to delete a product or deactivate if historical orders exist."""
    success, message = ProductService.delete_product(product_id)
    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 404 if "not found" in message.lower() else 400,
                "message": message
            }
        }), 404 if "not found" in message.lower() else 400

    return jsonify({
        "success": True,
        "message": message
    }), 200


@product_bp.route("/<int:product_id>/status", methods=["PATCH", "POST"])
@admin_required
def toggle_product_status(product_id: int):
    """Admin endpoint to toggle active / inactive visibility."""
    success, message, product = ProductService.toggle_product_status(product_id)
    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 404,
                "message": message
            }
        }), 404

    return jsonify({
        "success": True,
        "message": message,
        "data": product
    }), 200


@product_bp.route("/<int:product_id>/stock", methods=["PATCH", "POST"])
@admin_required
def update_product_stock(product_id: int):
    """Admin endpoint to update stock inventory."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    stock = data.get("stock")

    success, message, product = ProductService.update_stock(product_id, stock)
    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({
            "success": False,
            "error": {
                "code": status_code,
                "message": message
            }
        }), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": product
    }), 200


# ------------------------------------------------------------------------------
# Category Management Endpoints
# ------------------------------------------------------------------------------

@product_bp.route("/categories", methods=["GET"])
def get_categories():
    """Public endpoint to fetch all categories with product counts."""
    categories = ProductService.get_all_categories()
    return jsonify({
        "success": True,
        "count": len(categories),
        "data": categories,
    }), 200


@product_bp.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id: int):
    """Fetch details of a single category."""
    category = ProductService.get_category_by_id(category_id)
    if not category:
        return jsonify({
            "success": False,
            "error": {
                "code": 404,
                "message": f"Category #{category_id} not found."
            }
        }), 404

    return jsonify({
        "success": True,
        "data": category
    }), 200


@product_bp.route("/categories", methods=["POST"])
@admin_required
def create_category():
    """Admin endpoint to create a new category."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    name = data.get("name", "")
    description = data.get("description", "")

    success, message, category = ProductService.create_category(name, description)
    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 400,
                "message": message
            }
        }), 400

    return jsonify({
        "success": True,
        "message": message,
        "data": category
    }), 201


@product_bp.route("/categories/<int:category_id>", methods=["PUT", "POST"])
@admin_required
def update_category(category_id: int):
    """Admin endpoint to update a category."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    name = data.get("name", "")
    description = data.get("description", "")

    success, message, category = ProductService.update_category(category_id, name, description)
    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({
            "success": False,
            "error": {
                "code": status_code,
                "message": message
            }
        }), status_code

    return jsonify({
        "success": True,
        "message": message,
        "data": category
    }), 200


@product_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@admin_required
def delete_category(category_id: int):
    """Admin endpoint to delete a category."""
    success, message = ProductService.delete_category(category_id)
    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        return jsonify({
            "success": False,
            "error": {
                "code": status_code,
                "message": message
            }
        }), status_code

    return jsonify({
        "success": True,
        "message": message
    }), 200
