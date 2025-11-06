"""Application configuration"""
import os
from datetime import timedelta
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Invoice & Receipt Processor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    TESTING: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    WORKERS: int = 4

    # Database
    DATABASE_URL: str = "sqlite:///./invoices.db"
    DATABASE_ECHO: bool = False

    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-this-in-production"
    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)
    ALGORITHM: str = "HS256"

    # Rate limiting
    RATELIMIT_ENABLED: bool = True
    RATELIMIT_DEFAULT: str = "100/hour"
    RATELIMIT_STORAGE_URL: str = "redis://localhost:6379/1"

    # File uploads
    UPLOAD_FOLDER: str = "uploads"
    PROCESSED_FOLDER: str = "processed"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg", "pdf", "gif", "bmp", "tiff"}

    # OCR
    TESSERACT_CMD: Optional[str] = None  # Auto-detect
    OCR_TIMEOUT: int = 30  # seconds
    DEFAULT_OCR_LANGUAGE: str = "eng"

    # Currency
    BASE_CURRENCY: str = "USD"
    EXCHANGE_RATE_API_KEY: Optional[str] = None

    # Email processing
    EMAIL_ENABLED: bool = False
    EMAIL_SERVER: str = ""
    EMAIL_PORT: int = 993
    EMAIL_USE_SSL: bool = True
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    # Cloud OCR (optional)
    GOOGLE_CLOUD_VISION_ENABLED: bool = False
    GOOGLE_CLOUD_CREDENTIALS: Optional[str] = None
    AZURE_FORM_RECOGNIZER_ENABLED: bool = False
    AZURE_FORM_RECOGNIZER_ENDPOINT: Optional[str] = None
    AZURE_FORM_RECOGNIZER_KEY: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted"""
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @validator("SECRET_KEY", "JWT_SECRET_KEY")
    def validate_secret_keys(cls, v, field):
        """Warn if using default secret keys in production"""
        if v == "change-this-in-production" and os.getenv("ENVIRONMENT") == "production":
            raise ValueError(f"{field.name} must be changed in production")
        return v


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings
