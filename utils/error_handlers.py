from flask import jsonify, render_template, request
from .logger import log_error


def is_api_request() -> bool:
    """Determine if current request targets an API endpoint or expects JSON."""
    return (
        request.path.startswith("/api/")
        or request.is_json
        or request.headers.get("Accept", "").lower().startswith("application/json")
    )


def register_error_handlers(app):
    """Register centralized error handlers for the application."""

    @app.errorhandler(400)
    def bad_request(error):
        message = getattr(error, "description", "Bad Request")
        if is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "code": 400,
                    "message": message
                }
            }), 400
        return render_template("errors/404.html", error_code=400, message=message), 400

    @app.errorhandler(401)
    def unauthorized(error):
        message = getattr(error, "description", "Unauthorized access")
        if is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "code": 401,
                    "message": message
                }
            }), 401
        return render_template("errors/404.html", error_code=401, message=message), 401

    @app.errorhandler(403)
    def forbidden(error):
        message = getattr(error, "description", "Forbidden - You do not have permission")
        if is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "code": 403,
                    "message": message
                }
            }), 403
        return render_template("errors/404.html", error_code=403, message=message), 403

    @app.errorhandler(404)
    def not_found(error):
        message = getattr(error, "description", "The requested resource was not found")
        if is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "code": 404,
                    "message": message
                }
            }), 404
        return render_template("errors/404.html", error_code=404, message=message), 404

    @app.errorhandler(409)
    def conflict(error):
        message = getattr(error, "description", "Conflict with current state of resource")
        if is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "code": 409,
                    "message": message
                }
            }), 409
        return render_template("errors/404.html", error_code=409, message=message), 409

    @app.errorhandler(500)
    def internal_server_error(error):
        # Log server error safely without exposing stack traces to end users
        log_error(f"Internal Server Error on {request.path}: {str(error)}", exc_info=True)
        message = "An unexpected error occurred. Please try again later."
        if is_api_request():
            return jsonify({
                "success": False,
                "error": {
                    "code": 500,
                    "message": message
                }
            }), 500
        return render_template("errors/500.html", error_code=500, message=message), 500
