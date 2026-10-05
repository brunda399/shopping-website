import os
from flask import Flask
from config import config_by_name
from models import db
from utils.logger import setup_logger, log_info
from utils.error_handlers import register_error_handlers
from routes import register_routes


def create_app(config_name: str = None) -> Flask:
    """Application factory for the E-Commerce platform."""
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # Load configuration
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize Logger
    setup_logger(app)
    log_info(f"Initializing E-Commerce App in '{config_name}' environment")

    # Initialize Database
    db.init_app(app)
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        log_info("Database tables verified/created successfully")

        # Run comprehensive SQLite schema migrations to support all Module 7 columns
        from utils.db_migration import run_schema_migrations
        run_schema_migrations(app)


        # Ensure upload folder exists
        upload_folder = app.config.get("UPLOAD_FOLDER")
        if upload_folder:
            os.makedirs(upload_folder, exist_ok=True)

        if not app.config.get("TESTING"):
            from services.product_service import ProductService
            from services.auth_service import AuthService
            ProductService.seed_initial_data()
            AuthService.seed_default_users()
            log_info("Initial catalog and demo accounts seed check completed")

    # Inject current_user into all Jinja2 templates
    @app.context_processor
    def inject_current_user():
        from flask import session
        from services.auth_service import AuthService
        user_id = session.get("user_id")
        user = AuthService.get_user_by_id(user_id) if user_id else None
        return dict(current_user=user)

    # Register Error Handlers
    register_error_handlers(app)

    # Register Blueprints / Routes
    register_routes(app)
    log_info("All application routes and blueprints registered")

    return app


app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    debug = app.config.get("DEBUG", True)
    
    print(f"\n==========================================")
    print(f"  ShopEase Online E-Commerce — Module 3")
    print(f"  Running on http://{host}:{port}")
    print(f"  Admin Hub:  http://{host}:{port}/admin/products")
    print(f"  Products:   http://{host}:{port}/api/products")
    print(f"  Login:      http://{host}:{port}/login")
    print(f"  API Health: http://{host}:{port}/api/health")
    print(f"==========================================\n")



    
    app.run(host=host, port=port, debug=debug)
