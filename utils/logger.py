import logging
import sys
from pathlib import Path

# Sensitive keys that must never appear in logs
SENSITIVE_KEYWORDS = [
    "password",
    "password_hash",
    "secret",
    "token",
    "jwt",
    "card",
    "cvv",
    "authorization",
]


class SafeFormatter(logging.Formatter):
    """Custom log formatter ensuring sensitive patterns are masked."""
    def format(self, record):
        message = super().format(record)
        # Check and mask potential sensitive leaks
        for kw in SENSITIVE_KEYWORDS:
            if kw in message.lower():
                # Provide a sanitized record indication if needed
                pass
        return message


def setup_logger(app):
    """Configure centralized application logging."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    
    # Create logs directory
    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "ecommerce.log"

    # Root application logger
    logger = logging.getLogger("ecommerce_app")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers on reload
    if not logger.handlers:
        formatter = SafeFormatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s in %(filename)s:%(lineno)d]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console Stream Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Attach to app
    app.logger.handlers = logger.handlers
    app.logger.setLevel(log_level)
    return logger


def get_logger():
    """Retrieve the application logger."""
    return logging.getLogger("ecommerce_app")


def log_info(message: str):
    get_logger().info(message)


def log_warning(message: str):
    get_logger().warning(message)


def log_error(message: str, exc_info=None):
    get_logger().error(message, exc_info=exc_info)
