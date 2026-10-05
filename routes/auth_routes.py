from flask import Blueprint, jsonify, request, session
from services.auth_service import AuthService
from utils.auth_decorators import login_required

auth_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_bp.route("/status", methods=["GET"])
def auth_status():
    """Endpoint for auth status check."""
    user_id = session.get("user_id")
    is_authenticated = bool(user_id)
    return jsonify({
        "success": True,
        "is_authenticated": is_authenticated,
        "user_id": user_id,
        "user_name": session.get("user_name"),
        "user_role": session.get("user_role"),
    }), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    """API endpoint to register a new user account."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")
    confirm_password = data.get("confirm_password")
    phone = data.get("phone", "")

    success, message, user = AuthService.register_user(
        name=name,
        email=email,
        password=password,
        confirm_password=confirm_password,
        phone=phone,
    )

    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 400,
                "message": message
            }
        }), 400

    # Auto-login after successful registration
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_role"] = user["role"]
    session["user_email"] = user["email"]

    return jsonify({
        "success": True,
        "message": message,
        "data": user
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """API endpoint to authenticate user credentials."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    email = data.get("email", "")
    password = data.get("password", "")
    remember = data.get("remember", False)

    success, message, user = AuthService.authenticate_user(email, password)

    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 401,
                "message": message
            }
        }), 401

    # Store user in session
    session.permanent = bool(remember)
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role
    session["user_email"] = user.email

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "data": user.to_dict()
    }), 200


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """API endpoint to clear session and log out."""
    session.clear()
    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """API endpoint to retrieve active user profile."""
    user = AuthService.get_user_by_id(session.get("user_id"))
    if not user:
        session.clear()
        return jsonify({
            "success": False,
            "error": {
                "code": 404,
                "message": "User not found."
            }
        }), 404

    return jsonify({
        "success": True,
        "data": user.to_dict()
    }), 200


@auth_bp.route("/profile", methods=["PUT", "POST"])
@login_required
def update_profile():
    """API endpoint to update user name and phone."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    user_id = session.get("user_id")

    name = data.get("name", "")
    phone = data.get("phone", "")

    success, message, user = AuthService.update_profile(user_id=user_id, name=name, phone=phone)
    if not success:
        return jsonify({
            "success": False,
            "error": {
                "code": 400,
                "message": message
            }
        }), 400

    # Update session name
    session["user_name"] = user["name"]

    return jsonify({
        "success": True,
        "message": message,
        "data": user
    }), 200


@auth_bp.route("/change-password", methods=["PUT", "POST"])
@login_required
def change_password():
    """API endpoint to change user account password."""
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    user_id = session.get("user_id")

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password")

    success, message = AuthService.change_password(
        user_id=user_id,
        current_password=current_password,
        new_password=new_password,
        confirm_password=confirm_password,
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
        "message": message
    }), 200
