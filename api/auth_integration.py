"""
Auth Integration Module
=======================

Integration des neuen Auth-Systems in die bestehende API.
Verbindet auth/ Modul mit api/main.py
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Import from new auth module
try:
    from auth.config import AuthConfig
    from auth.jwt_handler import JWTHandler, TokenExpiredError, TokenInvalidError
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


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current authenticated user from JWT token

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
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
        async def admin_route(user: dict = Depends(require_role(Role.ADMIN))):
            return {"message": "Admin access granted"}
    """

    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
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
            user: dict = Depends(require_permission(Permission.SCAN_CREATE))
        ):
            return {"message": "Scan created"}
    """

    async def permission_checker(user: dict = Depends(get_current_user)) -> dict:
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
        async def login(credentials: dict):
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

            # TODO: Implement actual credential verification
            if credentials.get("username") == "admin" and credentials.get("password") == "admin":
                access_token = jwt_handler.create_access_token(user_id="admin", roles=["admin"], permissions=["*"])
                refresh_token = jwt_handler.create_refresh_token(user_id="admin", session_id="session_1")

                return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        @app.post("/auth/refresh", tags=["Authentication"])
        async def refresh_token(refresh_token: str):
            """Refresh access token"""
            jwt_handler = get_jwt_handler()

            try:
                payload = jwt_handler.decode_token(refresh_token)

                # Create new access token
                new_access_token = jwt_handler.create_access_token(
                    user_id=payload.sub, roles=payload.roles, permissions=payload.permissions
                )

                return {"access_token": new_access_token, "token_type": "bearer"}
            except (TokenExpiredError, TokenInvalidError):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

        @app.post("/auth/logout", tags=["Authentication"])
        async def logout(user: dict = Depends(get_current_user)):
            """Logout endpoint - blacklist token"""
            get_jwt_handler()

            # TODO: Get JTI from current token and blacklist it
            # jwt_handler.blacklist_token(jti)

            return {"message": "Logged out successfully"}


# Convenience exports
__all__ = [
    "get_current_user",
    "require_role",
    "require_permission",
    "AuthIntegration",
    "AUTH_AVAILABLE",
]
