"""
Auth Integration Module
=======================

Integration des neuen Auth-Systems in die bestehende API.
Verbindet auth/ Modul mit api/main.py
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Import from new auth module
try:
    from auth.jwt_handler import (
        JWTHandler,
        TokenExpiredError,
        TokenInvalidError,
    )
    from auth.middleware import AuthMiddleware
    from auth.rbac import Permission, RBACManager, Role

    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: New auth system not available: {e}")
    AUTH_AVAILABLE = False
    JWTHandler = None
    RBACManager = None

# Security scheme
security = HTTPBearer(auto_error=False)


# Global instances
_jwt_handler: Optional[JWTHandler] = None
_rbac_manager: Optional[RBACManager] = None


def get_jwt_handler() -> JWTHandler:
    """Get or create JWT handler instance"""
    global _jwt_handler
    if _jwt_handler is None and AUTH_AVAILABLE:
        _jwt_handler = JWTHandler()
    return _jwt_handler


def get_rbac_manager() -> RBACManager:
    """Get or create RBAC manager instance"""
    global _rbac_manager
    if _rbac_manager is None and AUTH_AVAILABLE:
        _rbac_manager = RBACManager()
    return _rbac_manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency to get current authenticated user from JWT token

    Usage:
        @app.get("/protected")
        async def protected_route(user: Any = Depends(get_current_user)):
            return {"message": f"Hello {user['sub']}"}
    """
    if not AUTH_AVAILABLE:
        # Fallback for development
        return {"sub": "dev_user", "roles": ["admin"]}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwt_handler = get_jwt_handler()

    try:
        payload = jwt_handler.decode_token(credentials.credentials)
        return {
            "sub": payload.sub,
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
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_role(role: Role):
    """
    Dependency factory to require specific role

    Usage:
        @app.get("/admin-only")
        async def admin_route(user: Any = Depends(require_role(Role.ADMIN))):
            return {"message": "Admin access granted"}
    """

    async def role_checker(user: Any = Depends(get_current_user)) -> dict:
        if not AUTH_AVAILABLE:
            return user

        get_rbac_manager()
        user_roles = [Role(r) for r in user.get("roles", [])]

        if role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' required",
            )
        return user

    return role_checker


async def require_permission(permission: Permission):
    """
    Dependency factory to require specific permission

    Usage:
        @app.post("/scans")
        async def create_scan(
            user: Any = Depends(require_permission(Permission.SCAN_CREATE))
        ):
            return {"message": "Scan created"}
    """

    async def permission_checker(
        user: Any = Depends(get_current_user),
    ) -> dict:
        if not AUTH_AVAILABLE:
            return user

        rbac = get_rbac_manager()
        user_id = user.get("sub")

        if not rbac.has_permission(user_id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' required",
            )
        return user

    return permission_checker


# ============================================================================
# CREDENTIAL VERIFICATION AND TOKEN BLACKLIST
# ============================================================================

logger = logging.getLogger(__name__)


async def verify_credentials(username: str, password: str) -> Optional[dict]:
    """
    Verify user credentials against database
    Returns user dict if valid, None otherwise
    """
    if not AUTH_AVAILABLE:
        return None

    from auth.password_hasher import PasswordHasher
    from database.auth_models import SessionLocal, User, UserRole

    db = SessionLocal()
    try:
        # Query user by username
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        # Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            logger.warning(f"Login attempt for locked user: {username}")
            return None

        # Verify password
        hasher = PasswordHasher()
        if not hasher.verify(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            db.commit()
            return None

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        db.commit()

        # Convert role to permissions
        permissions = []
        if user.role == UserRole.SUPER_ADMIN:
            permissions = ["*"]
        elif user.role == UserRole.ADMIN:
            permissions = ["read:*", "write:*", "delete:*", "admin:*"]
        elif user.role == UserRole.SECURITY_ANALYST:
            permissions = ["read:*", "write:scans", "write:findings"]
        elif user.role == UserRole.USER:
            permissions = ["read:scans", "read:findings"]
        else:
            permissions = ["read:scans"]

        # Add custom permissions
        if user.custom_permissions:
            permissions.extend(user.custom_permissions)

        return {
            "id": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "permissions": permissions,
        }
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return None
    finally:
        db.close()


async def blacklist_token(token: str) -> bool:
    """
    Blacklist a JWT token (for logout)
    """
    if not AUTH_AVAILABLE:
        return False

    try:
        # Decode token to get JTI (without signature verification)
        import jwt

        from auth.jwt_handler import get_config

        get_config().jwt

        # nosemgrep: python.jwt.security.unverified-jwt-decode.unverified-jwt-decode
        # Decode without verification to get JTI
        unverified = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        jti = unverified.get("jti")
        user_id = unverified.get("sub")
        exp_timestamp = unverified.get("exp")
        token_type = unverified.get("type", "access")

        if not jti:
            logger.warning("Token has no JTI, cannot blacklist")
            return False

        # Add to blacklist in JWT handler (in-memory)
        handler = get_jwt_handler()
        handler.blacklist_token(jti, reason="logout")

        # Also add to database for persistence
        from database.auth_models import SessionLocal, TokenType
        from database.auth_models import blacklist_token as db_blacklist_token

        db = SessionLocal()
        try:
            # Convert token type string to enum
            try:
                token_type_enum = TokenType(token_type.upper())
            except ValueError:
                token_type_enum = TokenType.ACCESS

            # Convert expiry timestamp to datetime
            if exp_timestamp:
                from datetime import datetime, timezone

                expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            else:
                expires_at = datetime.now(timezone.utc) + timezone.timedelta(hours=1)

            # Add to database blacklist
            db_blacklist_token(
                db,
                jti=jti,
                token_type=token_type_enum,
                expires_at=expires_at,
                user_id=(int(user_id) if user_id and user_id.isdigit() else None),
                reason="logout",
            )

            logger.info(f"Token blacklisted successfully: {jti[:8]}...")
            return True
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")
        return False


class AuthIntegration:
    """
    Helper class to integrate auth into FastAPI app
    """

    @staticmethod
    def init_app(app):
        """Initialize auth for FastAPI app"""
        if not AUTH_AVAILABLE:
            print("Warning: Auth system not available, running without authentication")
            return

        # Add auth middleware
        app.add_middleware(AuthMiddleware)

        print("✅ Auth system integrated successfully")

    @staticmethod
    def create_login_endpoint(app):
        """Create login endpoint"""

        @app.post("/auth/login", tags=["Authentication"])
        async def login(credentials: Any):
            """
            Login endpoint

            Request body:
                {
                    "username": "string",
                    "password": "string"
                }

            Returns:
                {
                    "access_token": "string",
                    "refresh_token": "string",
                    "token_type": "bearer"
                }
            """
            # This is a placeholder - implement actual login logic
            # Check credentials against database
            # Create and return tokens

            jwt_handler = get_jwt_handler()

            # Verify credentials against database
            user = await verify_credentials(credentials.get("username"), credentials.get("password"))

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

            # Create tokens with user data
            access_token = jwt_handler.create_access_token(
                user_id=user["id"],
                roles=[user["role"]],
                permissions=user["permissions"],
            )
            refresh_token = jwt_handler.create_refresh_token(
                user_id=user["id"],
                session_id=f"session_{user['id']}_{datetime.now(timezone.utc).timestamp()}",
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

        @app.post("/auth/refresh", tags=["Authentication"])
        async def refresh_token(refresh_token: str):
            """Refresh access token"""
            jwt_handler = get_jwt_handler()

            try:
                payload = jwt_handler.decode_token(refresh_token)

                # Create new access token
                new_access_token = jwt_handler.create_access_token(
                    user_id=payload.sub,
                    roles=payload.roles,
                    permissions=payload.permissions,
                )

                return {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                }
            except (TokenExpiredError, TokenInvalidError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                )

        @app.post("/auth/logout", tags=["Authentication"])
        async def logout(
            credentials: HTTPAuthorizationCredentials = Depends(security),
            user: Any = Depends(get_current_user),
        ):
            """Logout endpoint - blacklist token"""
            if credentials and credentials.credentials:
                success = await blacklist_token(credentials.credentials)
                if success:
                    return {"message": "Logged out successfully"}

            return {"message": "Logged out successfully"}


# Convenience exports
__all__ = [
    "get_current_user",
    "require_role",
    "require_permission",
    "verify_credentials",
    "blacklist_token",
    "AuthIntegration",
    "AUTH_AVAILABLE",
]
