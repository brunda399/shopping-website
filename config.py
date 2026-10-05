import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration class with default settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    
    # Ensure instance directory exists
    INSTANCE_DIR = BASE_DIR / "instance"
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    # Product image upload configuration
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "images" / "products")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request payload
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    
    # Database URI with robust cross-platform path resolution
    _raw_db_url = os.getenv("DATABASE_URL")
    if _raw_db_url and _raw_db_url.startswith("sqlite:///") and not _raw_db_url.startswith("sqlite:///:memory:"):
        _rel_path = _raw_db_url.replace("sqlite:///", "")
        _db_path = Path(_rel_path)
        if not _db_path.is_absolute():
            _db_path = BASE_DIR / _db_path
        _db_path.parent.mkdir(parents=True, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path.as_posix()}"
    elif _raw_db_url:
        SQLALCHEMY_DATABASE_URI = _raw_db_url
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(INSTANCE_DIR / 'ecommerce.db').as_posix()}"



class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    TESTING = True
    DEBUG = True
    ENV = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    ENV = "production"
    # Ensure SECRET_KEY is set in production
    SECRET_KEY = os.getenv("SECRET_KEY")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
