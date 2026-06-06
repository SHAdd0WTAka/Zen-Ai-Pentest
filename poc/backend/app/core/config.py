"""
Application configuration using Pydantic Settings.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Zen-AI-Pentest"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 4

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 50

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Hosts
    ALLOWED_HOSTS: List[str] = ["*"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"

    # Scanning
    SCAN_TIMEOUT: int = 3600  # 1 hour
    MAX_PARALLEL_SCANS: int = 5
    SCAN_OUTPUT_DIR: str = "scan_outputs"

    # Tools
    NMAP_PATH: str = "/usr/bin/nmap"
    NUCLEI_PATH: str = "/usr/local/bin/nuclei"
    SQLMAP_PATH: str = "/usr/local/bin/sqlmap"
    FFUF_PATH: str = "/usr/local/bin/ffuf"
    WHATWEB_PATH: str = "/usr/local/bin/whatweb"
    WAFW00F_PATH: str = "/usr/local/bin/wafw00f"
    SUBFINDER_PATH: str = "/usr/local/bin/subfinder"
    HTTPX_PATH: str = "/usr/local/bin/httpx"

    # Notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_FROM: Optional[str] = None

    SLACK_WEBHOOK_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Feature Flags
    FEATURE_AI_ANALYSIS: bool = True
    FEATURE_COMPLIANCE_REPORTS: bool = True
    FEATURE_WEBHOOKS: bool = True

    @property
    def DATABASE_ASYNC_URL(self) -> str:
        """Get async database URL."""
        return str(self.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
