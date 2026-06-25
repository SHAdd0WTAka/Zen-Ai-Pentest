"""
Shared authentication dependencies for the API.

Extracted from api/main.py to support modular route files.
"""

import logging
import os
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.csrf_protection import csrf_protection, require_csrf

# Import new auth system
try:
    from auth import JWTHandler, PasswordHasher, RBACManager, UserManager
    from database.auth_models import init_auth_db

    NEW_AUTH_AVAILABLE = True
except ImportError as e:
    print(f"Auth import error: {e}")
    NEW_AUTH_AVAILABLE = False

# Legacy auth as fallback
from api.auth_simple import authenticate_user as legacy_authenticate_user
from api.auth_simple import create_access_token as legacy_create_access_token
from api.auth_simple import verify_token as legacy_verify_token

logger = logging.getLogger(__name__)

# Initialize new auth components (after logger is defined)
_jwt_handler = None
_rbac_manager = None
_password_hasher = None
_user_manager = None

if NEW_AUTH_AVAILABLE:
    try:
        _jwt_handler = JWTHandler()
        _rbac_manager = RBACManager()
        _password_hasher = PasswordHasher()
        _user_manager = UserManager(_jwt_handler, _password_hasher)
        logger.info("New auth system initialized with database support")
    except Exception as e:
        logger.warning(f"Failed to initialize new auth components: {e}")
        import api.auth_deps as _self

        _self.NEW_AUTH_AVAILABLE = False

# Security
security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify JWT token - uses new auth system if available, falls back to legacy
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try new auth system first
    if NEW_AUTH_AVAILABLE and _jwt_handler:
        try:
            from auth.jwt_handler import TokenExpiredError, TokenInvalidError

            payload = _jwt_handler.decode_token(credentials.credentials)
            return {
                "sub": payload.sub,
                "username": payload.sub,
                "role": payload.roles[0] if payload.roles else "user",
                "roles": payload.roles,
                "permissions": payload.permissions,
                "session_id": payload.session_id,
            }
        except TokenExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except TokenInvalidError:
            # Legacy token - fall through to legacy verification
            pass

    # Fallback to legacy
    return legacy_verify_token(credentials)


async def optional_auth(
    request: Request,
) -> Optional[dict]:
    """
    Optional authentication - returns user if token valid, None otherwise
    Used for public read-only endpoints
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    # Create credentials object manually
    try:
        scheme, token = auth_header.split(" ", 1)
        if scheme.lower() != "bearer":
            return None

        from fastapi.security.http import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
        return await verify_token(credentials)
    except (ValueError, HTTPException):
        return None


# =============================================================================
# Secure Credential Store (In production: use database!)
# =============================================================================
# Load admin credentials from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    import warnings

    warnings.warn(
        "ADMIN_PASSWORD not set! Authentication will fail. Set ADMIN_PASSWORD environment variable!",
        RuntimeWarning,
    )
    # SECURITY: No fallback password. Authentication will reject all attempts.


def verify_admin_credentials(username: str, password: str) -> bool:
    """Securely verify admin credentials using constant-time comparison"""
    import hmac

    if not ADMIN_PASSWORD:
        return False
    return hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)
