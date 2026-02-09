"""
API Configuration Settings
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Zen AI Pentest API"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    VERSION: str = "1.0.0"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))

    # Security - MUST be set via environment variable
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "FATAL SECURITY ERROR: SECRET_KEY environment variable is not set. "
            "The application cannot start without a properly configured secret key. "
            "Please set SECRET_KEY to a secure random string (min 32 characters)."
        )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://zenuser:password@localhost:5432/zenpentest")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Rate Limiting
    RATE_LIMIT_ANONYMOUS: int = 10  # requests per minute
    RATE_LIMIT_AUTHENTICATED: int = 100
    RATE_LIMIT_PREMIUM: int = 1000

    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
