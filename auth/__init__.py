"""
Zen-AI-Pentest Authentication Module
=====================================

A secure authentication system implementing:
- JWT Authentication with Access & Refresh Tokens
- OAuth2 Password Flow
- Role-Based Access Control (RBAC)
- Multi-Factor Authentication (TOTP)
- API Key Management
- Session Management
- Bcrypt Password Hashing
- Token Blacklisting
- Rate Limiting
- Audit Logging

Compliance: ISO 27001, OWASP ASVS 2026, Zero-Trust Architecture
"""

from .jwt_handler import JWTHandler, TokenType, TokenPayload
from .password_hasher import PasswordHasher, PasswordStrengthError
from .rbac import RBACManager, Role, Permission
from .mfa import MFAHandler, MFAError
from .config import AuthConfig, JWTConfig, BcryptConfig, MFAConfig
from .middleware import AuthMiddleware, RateLimitMiddleware, AuditLogMiddleware
from .user_manager import UserManager, get_user_manager

__version__ = "1.1.0"  # Added database layer
__author__ = "Zen-AI-Pentest Team"

__all__ = [
    "JWTHandler",
    "TokenType",
    "TokenPayload",
    "PasswordHasher",
    "PasswordStrengthError",
    "RBACManager",
    "Role",
    "Permission",
    "MFAHandler",
    "MFAError",
    "AuthConfig",
    "JWTConfig",
    "BcryptConfig",
    "MFAConfig",
    "AuthMiddleware",
    "RateLimitMiddleware",
    "AuditLogMiddleware",
    "UserManager",
    "get_user_manager",
]
