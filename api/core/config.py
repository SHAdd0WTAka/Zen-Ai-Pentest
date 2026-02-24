"""Configuration settings stub for CI/CD compatibility."""

import os
from typing import Optional


class Settings:
    """Application settings."""

    # JWT Settings
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "dev-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # App
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    APP_NAME: str = "ZEN-AI Pentest"
    VERSION: str = "1.0.0"


settings = Settings()
