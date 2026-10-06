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




@main_bp.route("/checkout", methods=["GET"])
def checkout_page():
    """Customer checkout view with address selection, order review, and payment."""
    from flask import request, redirect, url_for, flash, session
    from services.cart_service import CartService
    from services.address_service import AddressService
    from services.product_service import ProductService

    user_id = session.get("user_id")
    if not user_id:
        flash("Please sign in or create an account to proceed to checkout.", "warning")
        return redirect(url_for("main.login", next=request.full_path if request.query_string else request.path))

    is_buy_now = request.args.get("buy_now") == "1"
    buy_now_item = session.get("buy_now_context") if is_buy_now else None

    if is_buy_now and buy_now_item:
        prod = ProductService.get_product_by_id(buy_now_item["product_id"])
        if not prod:
            flash("The requested Buy Now item is no longer available.", "error")
            return redirect(url_for("main.products"))

        qty = int(buy_now_item.get("quantity", 1))
        unit_p = prod["sale_price"] or prod["price"]
        item_subtotal = round(unit_p * qty, 2)
        shipping = 0.0 if item_subtotal >= 50.0 else 5.0
        tax = 0.0
        total = round(item_subtotal + shipping + tax, 2)

        order_summary = {
            "items": [{
                "product_id": prod["id"],
                "product": prod,
                "name": prod["name"],
                "image": prod["image"],
                "quantity": qty,
                "selected_size": buy_now_item.get("size"),
                "selected_color": buy_now_item.get("color"),
                "size": buy_now_item.get("size"),
                "color": buy_now_item.get("color"),
                "price": unit_p,
                "unit_price": unit_p,
                "subtotal": item_subtotal,
            }],
            "items_count": 1,
            "total_quantity": qty,
            "subtotal": item_subtotal,
            "discount": 0.0,
            "shipping": shipping,
            "tax": tax,
            "total": total,
            "grand_total": total,
            "is_buy_now": True,
        }
    else:
        coupon_code = session.get("applied_coupon", "")
        order_summary = CartService.get_cart_summary(user_id=user_id, coupon_code=coupon_code)
        if order_summary["items_count"] == 0:
            flash("Your shopping cart is currently empty. Add items before checking out.", "info")
            return redirect(url_for("main.cart_page"))

    addresses = AddressService.get_user_addresses(user_id)
    return render_template(
        "checkout/index.html",
        cart=order_summary,
        items=order_summary["items"],
        addresses=addresses,
        is_buy_now=bool(is_buy_now and buy_now_item),
    )


@main_bp.route("/buy-now", methods=["POST"])
def buy_now():
    """Initialize Buy Now temporary checkout context and route directly to checkout."""
    from flask import request, redirect, url_for, session

    prod_id = request.form.get("product_id") or request.form.get("id")
    qty = request.form.get("quantity", 1)
    size = request.form.get("selected_size") or request.form.get("size")
    color = request.form.get("selected_color") or request.form.get("color")

    if not prod_id:
        return redirect(url_for("main.products"))

    session["buy_now_context"] = {
        "product_id": int(prod_id),
        "quantity": int(qty),
        "size": size,
        "color": color,
    }

    if not session.get("user_id"):
        return redirect(url_for("main.login", next="/checkout?buy_now=1"))
    return redirect(url_for("main.checkout_page", buy_now=1))


@main_bp.route("/order-confirmation/<order_number>", methods=["GET"])
def order_confirmation(order_number: str):
    """Customer order receipt and confirmation showcase view."""
    from flask import abort
    from services.order_service import OrderService

    order = OrderService.get_order_by_number(order_number)
    if not order:
        abort(404)

    return render_template("orders/confirmation.html", order=order)


@main_bp.route("/orders", methods=["GET"])
def orders_page():
    """Customer order history overview."""
    from flask import redirect, url_for, flash, session
    from services.order_service import OrderService

    user_id = session.get("user_id")
    if not user_id:
        flash("Please sign in to view your orders.", "warning")
        return redirect(url_for("main.login", next="/orders"))

    orders = OrderService.get_user_orders(user_id)
    return render_template("orders/index.html", orders=orders)


@main_bp.route("/orders/<identifier>", methods=["GET"])
def order_detail_page(identifier: str):
    """Detailed view for a specific order with visual tracking timeline."""
    from flask import redirect, url_for, flash, abort, session
    from services.order_service import OrderService

    user_id = session.get("user_id")
    if not user_id:
        flash("Please sign in to view this order.", "warning")
        return redirect(url_for("main.login", next=f"/orders/{identifier}"))

    order = OrderService.get_order_by_number(identifier, user_id=user_id)
    if not order and identifier.isdigit():
        order = OrderService.get_order_by_id(int(identifier), user_id=user_id)

    if not order:
        abort(404)

    return render_template("orders/detail.html", order=order)


def register_routes(app):
    """Register all modular route blueprints with the Flask application."""
    from .auth_routes import auth_bp
    from .product_routes import product_bp
    from .cart_routes import cart_bp
    from .wishlist_routes import wishlist_bp
    from .order_routes import order_bp
    from .address_routes import address_bp
    from .admin_routes import admin_bp, admin_web_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(address_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_web_bp)

