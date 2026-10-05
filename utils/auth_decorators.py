import functools
from flask import session, request, redirect, url_for, flash, jsonify
from .error_handlers import is_api_request


def login_required(f):
    """Decorator ensuring that a route can only be accessed by authenticated users."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if is_api_request():
                return jsonify({
                    "success": False,
                    "error": {
                        "code": 401,
                        "message": "Authentication required. Please log in."
                    }
                }), 401
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("main.login", next=request.full_path if request.query_string else request.path))
        return f(*args, **kwargs)
    return decorated_function


# API alias for explicit API route readability
login_required_api = login_required


def admin_required(f):
    """Decorator ensuring that a route can only be accessed by an administrator."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if is_api_request():
                return jsonify({
                    "success": False,
                    "error": {
                        "code": 401,
                        "message": "Authentication required. Please log in."
                    }
                }), 401
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("main.login", next=request.path))

        if session.get("user_role") != "ADMIN":
            if is_api_request():
                return jsonify({
                    "success": False,
                    "error": {
                        "code": 403,
                        "message": "Forbidden. Administrator privileges required."
                    }
                }), 403
            flash("Access denied. Administrator privileges required.", "error")
            return redirect(url_for("main.index"))

        return f(*args, **kwargs)
    return decorated_function
