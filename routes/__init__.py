from flask import Blueprint, jsonify, render_template

# API base blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Main web blueprint for HTML pages
main_bp = Blueprint("main", __name__)


@api_bp.route("/health", methods=["GET"])
def health_check():
    """System health check endpoint required by Module 0."""
    return jsonify({
        "success": True,
        "message": "E-Commerce API is running"
    }), 200


@main_bp.route("/", methods=["GET"])
def index():
    """Render home page with categories and featured products."""
    from services.product_service import ProductService
    categories = ProductService.get_all_categories()
    products = ProductService.get_all_products(is_active=True)
    return render_template("index.html", categories=categories, products=products)


@main_bp.route("/products", methods=["GET"])
def products():
    """Customer product discovery, filtering, and catalog browsing view."""
    from flask import request
    from services.product_service import ProductService
    categories = ProductService.get_all_categories()
    
    selected_category = request.args.get("category", "")
    search_query = request.args.get("q", "")
    sort_by = request.args.get("sort_by", "newest")
    
    return render_template(
        "products/index.html",
        categories=categories,
        initial_category=selected_category,
        initial_search=search_query,
        initial_sort=sort_by,
    )


@main_bp.route("/products/<int:product_id>", methods=["GET"])
def product_detail(product_id: int):
    """Customer product details page with specifications and related items."""
    from flask import abort, session
    from services.product_service import ProductService
    is_admin = session.get("user_role") == "ADMIN"
    product = ProductService.get_product_by_id(product_id, only_active=not is_admin)
    if not product:
        abort(404)
        
    related_products = ProductService.get_related_products(product_id, product["category_id"], limit=4)
    return render_template(
        "products/detail.html",
        product=product,
        related_products=related_products,
    )


@main_bp.route("/cart", methods=["GET"])
def cart_page():
    """Customer shopping cart page."""
    from flask import session
    from services.cart_service import CartService
    user_id = session.get("user_id")
    coupon_code = session.get("applied_coupon", "")
    summary = CartService.get_cart_summary(user_id=user_id, coupon_code=coupon_code)
    return render_template("cart/index.html", cart=summary, cart_items=summary["items"])


@main_bp.route("/wishlist", methods=["GET"])
def wishlist_page():
    """Customer wishlist / saved favorites page."""
    from flask import session
    from services.wishlist_service import WishlistService
    user_id = session.get("user_id")
    if user_id:
        wishlist_data = WishlistService.get_user_wishlist(user_id)
    else:
        wishlist_data = {"items_count": 0, "items": []}
    return render_template("wishlist/index.html", wishlist=wishlist_data, wishlist_items=wishlist_data["items"])


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    """Render and handle customer account registration."""
    from flask import request, redirect, url_for, flash, session
    from services.auth_service import AuthService

    # Redirect if already logged in
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = request.form.get("phone", "").strip()

        success, message, user = AuthService.register_user(
            name=name,
            email=email,
            password=password,
            confirm_password=confirm_password,
            phone=phone,
        )

        if not success:
            flash(message, "error")
            return render_template("auth/register.html", name=name, email=email, phone=phone)

        # Set session on successful registration
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]
        session["user_email"] = user["email"]

        flash(f"Welcome to ShopEase, {user['name']}! Your account has been created.", "success")
        next_page = request.args.get("next")
        return redirect(next_page if next_page and next_page.startswith("/") else url_for("main.index"))

    return render_template("auth/register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render and handle customer login."""
    from flask import request, redirect, url_for, flash, session
    from services.auth_service import AuthService

    # Redirect if already logged in
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    next_page = request.args.get("next") or ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        success, message, user = AuthService.authenticate_user(email, password)

        if not success:
            flash(message, "error")
            return render_template("auth/login.html", email=email, next=next_page)

        # Set authenticated session
        session.permanent = remember
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_role"] = user.role
        session["user_email"] = user.email

        flash(f"Welcome back, {user.name}!", "success")
        return redirect(next_page if next_page and next_page.startswith("/") else url_for("main.index"))

    return render_template("auth/login.html", next=next_page)


@main_bp.route("/logout", methods=["GET"])
def logout():
    """Sign out the current user and redirect home."""
    from flask import redirect, url_for, flash, session
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("main.index"))


@main_bp.route("/profile", methods=["GET", "POST"])
def profile():
    """User profile management view."""
    from flask import request, redirect, url_for, flash, session
    from services.auth_service import AuthService
    from utils.auth_decorators import login_required

    user_id = session.get("user_id")
    if not user_id:
        flash("Please sign in to access your account profile.", "warning")
        return redirect(url_for("main.login", next=request.path))

    user = AuthService.get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("Account not found. Please sign in again.", "error")
        return redirect(url_for("main.login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()

            success, message, updated_user = AuthService.update_profile(user_id, name, phone)
            if success:
                session["user_name"] = updated_user["name"]
                flash("Profile details updated successfully.", "success")
            else:
                flash(message, "error")

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            success, message = AuthService.change_password(
                user_id, current_password, new_password, confirm_password
            )
            if success:
                flash("Password updated successfully.", "success")
            else:
                flash(message, "error")

        return redirect(url_for("main.profile"))

    return render_template("auth/profile.html", user=user)




def register_routes(app):
    """Register all modular route blueprints with the Flask application."""
    from .auth_routes import auth_bp
    from .product_routes import product_bp
    from .cart_routes import cart_bp
    from .wishlist_routes import wishlist_bp
    from .order_routes import order_bp
    from .admin_routes import admin_bp, admin_web_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_web_bp)
