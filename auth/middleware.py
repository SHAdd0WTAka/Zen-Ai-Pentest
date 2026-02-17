"""
Authentication Middleware Module
================================

FastAPI middleware for authentication and authorization with:
- JWT token validation
- API key validation
- Role-based access control
- Permission checking
- Request context injection

Compliance: OWASP ASVS 2026 V3.4, V4.1
"""

from typing import Optional, List, Callable, Dict, Any
from functools import wraps
from dataclasses import dataclass
import re

from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_handler import JWTHandler, TokenPayload, TokenExpiredError, TokenInvalidError, TokenBlacklistedError
from .api_key_manager import APIKeyManager, get_api_key_manager, APIKeyStatus
from .rbac import RBACManager, get_rbac_manager, Role, Permission
from .session_manager import get_session_manager, SessionExpiredError
from .rate_limiter import get_rate_limiter, RateLimitType
from .audit_logger import get_audit_logger, AuditEventType, AuditSeverity


# Security scheme
security = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    """Authentication context for request"""
    user_id: str
    roles: List[str]
    permissions: List[str]
    session_id: Optional[str] = None
    is_api_key: bool = False
    mfa_verified: bool = False
    token_payload: Optional[TokenPayload] = None
    api_key_id: Optional[str] = None


class AuthenticationError(HTTPException):
    """Authentication error"""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class MFAVerificationError(HTTPException):
    """MFA verification required error"""
    def __init__(self, detail: str = "MFA verification required"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers={"X-MFA-Required": "true"},
        )


class AuthMiddleware:
    """
    Authentication Middleware
    
    Handles:
    - JWT token extraction and validation
    - API key validation
    - Session validation
    - Rate limiting
    - Context injection
    """
    
    def __init__(
        self,
        jwt_handler: Optional[JWTHandler] = None,
        api_key_manager: Optional[APIKeyManager] = None,
        rbac_manager: Optional[RBACManager] = None,
    ):
        self.jwt_handler = jwt_handler or JWTHandler()
        self.api_key_manager = api_key_manager or get_api_key_manager()
        self.rbac_manager = rbac_manager or get_rbac_manager()
        self.rate_limiter = get_rate_limiter()
        self.audit_logger = get_audit_logger()
    
    async def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        
        # Check query parameter (for WebSocket connections)
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    async def extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Check Authorization header with ApiKey scheme
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "apikey":
                return parts[1]
        
        return None
    
    async def authenticate(
        self,
        request: Request,
        require_mfa: bool = False
    ) -> AuthContext:
        """
        Authenticate request
        
        Args:
            request: FastAPI request
            require_mfa: Whether MFA is required
            
        Returns:
            Authentication context
            
        Raises:
            AuthenticationError: If authentication fails
            MFAVerificationError: If MFA verification is required
        """
        # Try JWT token first
        token = await self.extract_token(request)
        if token:
            return await self._authenticate_jwt(token, require_mfa)
        
        # Try API key
        api_key = await self.extract_api_key(request)
        if api_key:
            return await self._authenticate_api_key(api_key, request)
        
        raise AuthenticationError("No authentication credentials provided")
    
    async def _authenticate_jwt(
        self,
        token: str,
        require_mfa: bool
    ) -> AuthContext:
        """Authenticate using JWT token"""
        try:
            payload = self.jwt_handler.verify_access_token(token)
            
            # Check MFA if required
            if require_mfa and not payload.mfa_verified:
                raise MFAVerificationError("MFA verification required")
            
            # Validate session if present
            if payload.session_id:
                session_manager = get_session_manager()
                try:
                    session = session_manager.validate_session(payload.session_id)
                    if not session:
                        raise AuthenticationError("Session invalid")
                except SessionExpiredError:
                    raise AuthenticationError("Session expired")
            
            return AuthContext(
                user_id=payload.sub,
                roles=payload.roles,
                permissions=payload.permissions,
                session_id=payload.session_id,
                is_api_key=False,
                mfa_verified=payload.mfa_verified,
                token_payload=payload,
            )
            
        except TokenExpiredError:
            raise AuthenticationError("Token has expired")
        except TokenInvalidError:
            raise AuthenticationError("Invalid token")
        except TokenBlacklistedError:
            raise AuthenticationError("Token has been revoked")
    
    async def _authenticate_api_key(
        self,
        api_key: str,
        request: Request
    ) -> AuthContext:
        """Authenticate using API key"""
        ip_address = self._get_client_ip(request)
        
        try:
            key_data = self.api_key_manager.validate_api_key(api_key, ip_address)
            
            if not key_data:
                raise AuthenticationError("Invalid API key")
            
            # Record usage
            self.api_key_manager.record_usage(api_key)
            
            # Get user permissions from RBAC
            user_permissions = self.rbac_manager.get_user_permissions(key_data.user_id)
            user_roles = self.rbac_manager.get_user_roles(key_data.user_id)
            
            # Filter permissions by API key permissions if specified
            if key_data.permissions:
                user_permissions = [
                    p for p in user_permissions
                    if p in key_data.permissions
                ]
            
            return AuthContext(
                user_id=key_data.user_id,
                roles=[r.value for r in user_roles],
                permissions=[p.value for p in user_permissions],
                session_id=None,
                is_api_key=True,
                mfa_verified=True,  # API keys imply MFA verified
                api_key_id=key_data.id,
            )
            
        except Exception as e:
            if "revoked" in str(e).lower():
                raise AuthenticationError("API key has been revoked")
            if "expired" in str(e).lower():
                raise AuthenticationError("API key has expired")
            raise AuthenticationError("Invalid API key")
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP address from request"""
        # Check X-Forwarded-For header
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
    
    async def check_permission(
        self,
        auth_context: AuthContext,
        permission: Permission
    ) -> bool:
        """Check if user has permission"""
        return permission.value in auth_context.permissions
    
    async def check_role(
        self,
        auth_context: AuthContext,
        role: Role
    ) -> bool:
        """Check if user has role"""
        return role.value in auth_context.roles


# Middleware instance
_auth_middleware: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Get singleton auth middleware instance"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware


# FastAPI dependency functions
async def get_current_auth_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthContext:
    """
    FastAPI dependency to get current authentication context
    
    Usage:
        @app.get("/protected")
        async def protected_endpoint(auth: AuthContext = Depends(get_current_auth_context)):
            return {"user_id": auth.user_id}
    """
    middleware = get_auth_middleware()
    return await middleware.authenticate(request)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthContext:
    """
    FastAPI dependency that requires authentication
    
    Usage:
        @app.get("/protected")
        async def protected_endpoint(auth: AuthContext = Depends(require_auth)):
            return {"user_id": auth.user_id}
    """
    middleware = get_auth_middleware()
    return await middleware.authenticate(request)


def require_role(role: Role):
    """
    FastAPI dependency factory for role requirement
    
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(
            auth: AuthContext = Depends(require_role(Role.ADMIN))
        ):
            return {"message": "Admin access granted"}
    """
    async def check_role(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> AuthContext:
        middleware = get_auth_middleware()
        auth_context = await middleware.authenticate(request)
        
        if not await middleware.check_role(auth_context, role):
            # Log access denied
            audit_logger = get_audit_logger()
            audit_logger.log_access_denied(
                user_id=auth_context.user_id,
                resource=request.url.path,
                permission=f"role:{role.value}",
                ip_address=middleware._get_client_ip(request),
            )
            
            raise AuthorizationError(f"Role '{role.value}' required")
        
        return auth_context
    
    return check_role


def require_permission(permission: Permission):
    """
    FastAPI dependency factory for permission requirement
    
    Usage:
        @app.post("/scans")
        async def create_scan(
            auth: AuthContext = Depends(require_permission(Permission.SCAN_CREATE))
        ):
            return {"message": "Scan created"}
    """
    async def check_permission(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> AuthContext:
        middleware = get_auth_middleware()
        auth_context = await middleware.authenticate(request)
        
        if not await middleware.check_permission(auth_context, permission):
            # Log access denied
            audit_logger = get_audit_logger()
            audit_logger.log_access_denied(
                user_id=auth_context.user_id,
                resource=request.url.path,
                permission=permission.value,
                ip_address=middleware._get_client_ip(request),
            )
            
            raise AuthorizationError(f"Permission '{permission.value}' required")
        
        return auth_context
    
    return check_permission


def require_mfa():
    """
    FastAPI dependency factory for MFA requirement
    
    Usage:
        @app.post("/sensitive-action")
        async def sensitive_action(
            auth: AuthContext = Depends(require_mfa())
        ):
            return {"message": "Action completed"}
    """
    async def check_mfa(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> AuthContext:
        middleware = get_auth_middleware()
        auth_context = await middleware.authenticate(request, require_mfa=True)
        return auth_context
    
    return check_mfa


# Combined decorators
def require_auth_with_permissions(permissions: List[Permission]):
    """
    Require authentication with multiple permissions
    
    Usage:
        @app.post("/scans")
        async def create_scan(
            auth: AuthContext = Depends(require_auth_with_permissions([
                Permission.SCAN_CREATE,
                Permission.SCAN_EXECUTE
            ]))
        ):
            return {"message": "Scan created"}
    """
    async def check_permissions(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> AuthContext:
        middleware = get_auth_middleware()
        auth_context = await middleware.authenticate(request)
        
        missing_permissions = [
            p.value for p in permissions
            if not await middleware.check_permission(auth_context, p)
        ]
        
        if missing_permissions:
            raise AuthorizationError(
                f"Missing permissions: {', '.join(missing_permissions)}"
            )
        
        return auth_context
    
    return check_permissions


# Rate limiting decorator
def rate_limit(limit_type: RateLimitType):
    """
    Rate limiting decorator for endpoints
    
    Usage:
        @app.post("/auth/login")
        @rate_limit(RateLimitType.LOGIN)
        async def login(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = kwargs.get('request')
            if not request and args:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                middleware = get_auth_middleware()
                identifier = middleware._get_client_ip(request) or "unknown"
                
                rate_limiter = get_rate_limiter()
                result = rate_limiter.check_rate_limit(identifier, limit_type)
                
                if not result.allowed:
                    # Log rate limit exceeded
                    audit_logger = get_audit_logger()
                    audit_logger.log_rate_limit_exceeded(
                        identifier=identifier,
                        limit_type=limit_type.value,
                        ip_address=identifier,
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=result.message,
                        headers={"Retry-After": str(result.retry_after)} if result.retry_after else {},
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
