"""
Auth Middleware
===============

FastAPI middleware for authentication and authorization.
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .jwt_handler import JWTHandler, TokenExpiredError, TokenInvalidError


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication.
    
    Validates JWT tokens on protected routes.
    Skips validation for public routes.
    """
    
    # Routes that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/health/",
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/csrf-token",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    ]
    
    # Path prefixes that are public
    PUBLIC_PREFIXES = [
        "/static/",
        "/assets/",
    ]
    
    def __init__(self, app, jwt_handler: Optional[JWTHandler] = None):
        super().__init__(app)
        self.jwt_handler = jwt_handler or JWTHandler()
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)"""
        # Check exact matches
        if path in self.PUBLIC_PATHS:
            return True
        
        # Check prefixes
        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process each request"""
        path = request.url.path
        
        # Skip auth for public paths
        if self._is_public_path(path):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # If no auth header and not public path, reject
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract and validate token
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            payload = self.jwt_handler.decode_token(token)
            # Store user info in request state for later use
            request.state.user = {
                "sub": payload.sub,
                "roles": payload.roles,
                "permissions": payload.permissions,
                "session_id": payload.session_id,
            }
            
        except TokenExpiredError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except TokenInvalidError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid token: {str(e)}"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Continue with request
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    
    Limits requests per IP address.
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # IP -> [(timestamp, count)]
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit"""
        import time
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if current_time - ts < self.window_seconds
            ]
        else:
            self.requests[client_ip] = []
        
        # Count recent requests
        total_requests = sum(count for ts, count in self.requests[client_ip])
        
        if total_requests >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(self.window_seconds)},
            )
        
        # Record this request
        self.requests[client_ip].append((current_time, 1))
        
        # Continue
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.max_requests - total_requests - 1)
        )
        
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging.
    
    Logs all requests with user information.
    """
    
    def __init__(self, app, audit_logger=None):
        super().__init__(app)
        self.audit_logger = audit_logger
    
    async def dispatch(self, request: Request, call_next):
        """Log request"""
        import time
        import logging
        
        start_time = time.time()
        
        # Get user info if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("sub")
        
        # Process request
        response = await call_next(request)
        
        # Log
        duration = time.time() - start_time
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "user_id": user_id,
            "client_ip": request.client.host if request.client else None,
            "duration_ms": round(duration * 1000, 2),
        }
        
        if self.audit_logger:
            self.audit_logger.log_action("request", user_id, log_data)
        else:
            logger = logging.getLogger(__name__)
            logger.info(f"Request: {log_data}")
        
        return response
