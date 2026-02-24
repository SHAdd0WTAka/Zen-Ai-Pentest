"""
Authentication Configuration
============================

Centralized configuration for the authentication system.
All security-sensitive settings should be loaded from environment variables.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class JWTConfig:
    """JWT Configuration Settings"""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # Short-lived access tokens
    refresh_token_expire_days: int = 7  # Longer-lived refresh tokens
    issuer: str = "zen-ai-pentest"
    audience: str = "zen-ai-pentest-api"
    token_type_header: str = "Bearer"

    @classmethod
    def from_env(cls) -> "JWTConfig":
        return cls(
            secret_key=os.getenv("JWT_SECRET_KEY", ""),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
            ),
            refresh_token_expire_days=int(
                os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
            ),
            issuer=os.getenv("JWT_ISSUER", "zen-ai-pentest"),
            audience=os.getenv("JWT_AUDIENCE", "zen-ai-pentest-api"),
        )


@dataclass
class BcryptConfig:
    """Bcrypt Password Hashing Configuration"""

    rounds: int = 12  # Work factor (2^12 iterations)

    @classmethod
    def from_env(cls) -> "BcryptConfig":
        return cls(
            rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
        )


@dataclass
class MFAConfig:
    """Multi-Factor Authentication Configuration"""

    issuer_name: str = "Zen-AI-Pentest"
    digits: int = 6
    interval: int = 30  # TOTP time window in seconds
    window: int = 1  # Allowed time drift windows
    backup_codes_count: int = 10

    @classmethod
    def from_env(cls) -> "MFAConfig":
        return cls(
            issuer_name=os.getenv("MFA_ISSUER_NAME", "Zen-AI-Pentest"),
            digits=int(os.getenv("MFA_DIGITS", "6")),
            interval=int(os.getenv("MFA_INTERVAL", "30")),
            window=int(os.getenv("MFA_WINDOW", "1")),
            backup_codes_count=int(os.getenv("MFA_BACKUP_CODES_COUNT", "10")),
        )


@dataclass
class RateLimitConfig:
    """Rate Limiting Configuration"""

    login_attempts: int = 5
    login_window_seconds: int = 300  # 5 minutes
    api_key_requests: int = 100
    api_key_window_seconds: int = 60  # 1 minute
    mfa_attempts: int = 3
    mfa_window_seconds: int = 300

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        return cls(
            login_attempts=int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5")),
            login_window_seconds=int(
                os.getenv("RATE_LIMIT_LOGIN_WINDOW", "300")
            ),
            api_key_requests=int(
                os.getenv("RATE_LIMIT_API_KEY_REQUESTS", "100")
            ),
            api_key_window_seconds=int(
                os.getenv("RATE_LIMIT_API_KEY_WINDOW", "60")
            ),
            mfa_attempts=int(os.getenv("RATE_LIMIT_MFA_ATTEMPTS", "3")),
            mfa_window_seconds=int(os.getenv("RATE_LIMIT_MFA_WINDOW", "300")),
        )


@dataclass
class SessionConfig:
    """Session Management Configuration"""

    max_sessions_per_user: int = 5
    session_timeout_minutes: int = 30
    absolute_timeout_hours: int = 8
    cleanup_interval_minutes: int = 60

    @classmethod
    def from_env(cls) -> "SessionConfig":
        return cls(
            max_sessions_per_user=int(os.getenv("SESSION_MAX_PER_USER", "5")),
            session_timeout_minutes=int(
                os.getenv("SESSION_TIMEOUT_MINUTES", "30")
            ),
            absolute_timeout_hours=int(
                os.getenv("SESSION_ABSOLUTE_TIMEOUT_HOURS", "8")
            ),
            cleanup_interval_minutes=int(
                os.getenv("SESSION_CLEANUP_INTERVAL", "60")
            ),
        )


@dataclass
class APIKeyConfig:
    """API Key Management Configuration"""

    key_prefix: str = "zap_"
    key_length: int = 32
    max_keys_per_user: int = 5
    default_expiry_days: int = 90

    @classmethod
    def from_env(cls) -> "APIKeyConfig":
        return cls(
            key_prefix=os.getenv("API_KEY_PREFIX", "zap_"),
            key_length=int(os.getenv("API_KEY_LENGTH", "32")),
            max_keys_per_user=int(os.getenv("API_KEY_MAX_PER_USER", "5")),
            default_expiry_days=int(
                os.getenv("API_KEY_DEFAULT_EXPIRY_DAYS", "90")
            ),
        )


@dataclass
class AuditConfig:
    """Audit Logging Configuration"""

    log_file_path: str = "/var/log/zen-ai-pentest/auth.log"
    max_file_size_mb: int = 100
    backup_count: int = 10
    log_to_console: bool = True
    sensitive_fields: List[str] = None

    def __post_init__(self):
        if self.sensitive_fields is None:
            self.sensitive_fields = [
                "password",
                "token",
                "secret",
                "api_key",
                "mfa_code",
            ]

    @classmethod
    def from_env(cls) -> "AuditConfig":
        config = cls(
            log_file_path=os.getenv(
                "AUDIT_LOG_FILE", "/var/log/zen-ai-pentest/auth.log"
            ),
            max_file_size_mb=int(os.getenv("AUDIT_MAX_FILE_SIZE_MB", "100")),
            backup_count=int(os.getenv("AUDIT_BACKUP_COUNT", "10")),
            log_to_console=os.getenv("AUDIT_LOG_TO_CONSOLE", "true").lower()
            == "true",
        )
        return config


@dataclass
class AuthConfig:
    """Main Authentication Configuration"""

    environment: Environment
    jwt: JWTConfig
    bcrypt: BcryptConfig
    mfa: MFAConfig
    rate_limit: RateLimitConfig
    session: SessionConfig
    api_key: APIKeyConfig
    audit: AuditConfig

    # Security settings
    require_mfa: bool = False
    allow_registration: bool = True
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    max_failed_logins: int = 5
    lockout_duration_minutes: int = 30

    @classmethod
    def from_env(cls) -> "AuthConfig":
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        environment = (
            Environment(env_str)
            if env_str in [e.value for e in Environment]
            else Environment.DEVELOPMENT
        )

        return cls(
            environment=environment,
            jwt=JWTConfig.from_env(),
            bcrypt=BcryptConfig.from_env(),
            mfa=MFAConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
            session=SessionConfig.from_env(),
            api_key=APIKeyConfig.from_env(),
            audit=AuditConfig.from_env(),
            require_mfa=os.getenv("AUTH_REQUIRE_MFA", "false").lower()
            == "true",
            allow_registration=os.getenv(
                "AUTH_ALLOW_REGISTRATION", "true"
            ).lower()
            == "true",
            password_min_length=int(
                os.getenv("AUTH_PASSWORD_MIN_LENGTH", "12")
            ),
            password_require_uppercase=os.getenv(
                "AUTH_PASSWORD_REQUIRE_UPPERCASE", "true"
            ).lower()
            == "true",
            password_require_lowercase=os.getenv(
                "AUTH_PASSWORD_REQUIRE_LOWERCASE", "true"
            ).lower()
            == "true",
            password_require_digits=os.getenv(
                "AUTH_PASSWORD_REQUIRE_DIGITS", "true"
            ).lower()
            == "true",
            password_require_special=os.getenv(
                "AUTH_PASSWORD_REQUIRE_SPECIAL", "true"
            ).lower()
            == "true",
            max_failed_logins=int(os.getenv("AUTH_MAX_FAILED_LOGINS", "5")),
            lockout_duration_minutes=int(
                os.getenv("AUTH_LOCKOUT_DURATION_MINUTES", "30")
            ),
        )


# Global configuration instance
_config: Optional[AuthConfig] = None


def get_config() -> AuthConfig:
    """Get or create global configuration instance"""
    global _config
    if _config is None:
        _config = AuthConfig.from_env()
    return _config


def set_config(config: AuthConfig) -> None:
    """Set global configuration instance"""
    global _config
    _config = config
