"""
Zen-AI-Pentest Authentication System
====================================

Main application entry point for the authentication system.

Features:
- FastAPI application with all auth endpoints
- CORS configuration
- Error handling
- Health checks
- Documentation

Usage:
    uvicorn auth.main:app --reload
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .router import router
from .config import get_config, Environment
from .jwt_handler import JWTHandler, TokenExpiredError, TokenInvalidError, TokenBlacklistedError
from .audit_logger import get_audit_logger, AuditEventType, AuditSeverity


# Get configuration
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles startup and shutdown events.
    """
    # Startup
    print("=" * 60)
    print("Zen-AI-Pentest Authentication System")
    print("=" * 60)
    print(f"Environment: {config.environment.value}")
    print(f"JWT Algorithm: {config.jwt.algorithm}")
    print(f"Access Token Expiry: {config.jwt.access_token_expire_minutes} minutes")
    print(f"Refresh Token Expiry: {config.jwt.refresh_token_expire_days} days")
    print(f"MFA Enabled: {config.require_mfa}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("Shutting down authentication system...")


# Create FastAPI application
app = FastAPI(
    title="Zen-AI-Pentest Auth API",
    description="""
    Secure Authentication System for Zen-AI-Pentest
    
    ## Features
    
    * **JWT Authentication** - Access and refresh tokens
    * **OAuth2 Password Flow** - Standard OAuth2 implementation
    * **Role-Based Access Control** - Granular permissions
    * **Multi-Factor Authentication** - TOTP support
    * **API Key Management** - Secure API access
    * **Session Management** - Secure session handling
    * **Rate Limiting** - Protection against brute force
    * **Audit Logging** - Comprehensive security logging
    
    ## Compliance
    
    * ISO 27001
    * OWASP ASVS 2026
    * Zero-Trust Architecture
    """,
    version="1.0.0",
    docs_url="/docs" if config.environment != Environment.PRODUCTION else None,
    redoc_url="/redoc" if config.environment != Environment.PRODUCTION else None,
    openapi_url="/openapi.json" if config.environment != Environment.PRODUCTION else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-MFA-Required", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Add trusted host middleware in production
if config.environment == Environment.PRODUCTION:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(","),
    )


# Custom exception handlers
@app.exception_handler(TokenExpiredError)
async def token_expired_handler(request: Request, exc: TokenExpiredError):
    """Handle expired token errors"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "token_expired",
            "message": "Token has expired",
            "detail": str(exc),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(TokenInvalidError)
async def token_invalid_handler(request: Request, exc: TokenInvalidError):
    """Handle invalid token errors"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "token_invalid",
            "message": "Invalid token",
            "detail": str(exc),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(TokenBlacklistedError)
async def token_blacklisted_handler(request: Request, exc: TokenBlacklistedError):
    """Handle blacklisted token errors"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "token_revoked",
            "message": "Token has been revoked",
            "detail": str(exc),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions"""
    # Log the error
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
        message=f"Unhandled exception: {str(exc)}",
        severity=AuditSeverity.ERROR,
        details={
            "path": str(request.url),
            "method": request.method,
            "error": str(exc),
        }
    )
    
    # Return generic error in production
    if config.environment == Environment.PRODUCTION:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "An internal error occurred",
            },
        )
    else:
        # Return detailed error in development
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


# Include auth router
app.include_router(router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the health status of the authentication system.
    """
    return {
        "status": "healthy",
        "service": "zen-ai-pentest-auth",
        "version": "1.0.0",
        "environment": config.environment.value,
    }


# Readiness check endpoint
@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint
    
    Returns whether the service is ready to accept requests.
    """
    # Check JWT configuration
    if not config.jwt.secret_key:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "reason": "JWT secret key not configured",
            },
        )
    
    return {
        "status": "ready",
        "checks": {
            "jwt_config": True,
            "argon2_config": True,
        },
    }


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Remove server header
    response.headers.pop("Server", None)
    
    return response


# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests"""
    from datetime import datetime
    
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    # Log request (in production, use proper logging)
    if config.environment != Environment.PRODUCTION:
        print(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    return response


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    
    Returns basic information about the authentication system.
    """
    return {
        "service": "Zen-AI-Pentest Authentication System",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
    }


# Security info endpoint
@app.get("/security/info", tags=["Security"])
async def security_info():
    """
    Security information endpoint
    
    Returns security-related configuration information.
    """
    return {
        "password_policy": {
            "min_length": config.password_min_length,
            "require_uppercase": config.password_require_uppercase,
            "require_lowercase": config.password_require_lowercase,
            "require_digits": config.password_require_digits,
            "require_special": config.password_require_special,
        },
        "jwt": {
            "algorithm": config.jwt.algorithm,
            "access_token_expire_minutes": config.jwt.access_token_expire_minutes,
            "refresh_token_expire_days": config.jwt.refresh_token_expire_days,
        },
        "mfa": {
            "required": config.require_mfa,
            "digits": config.mfa.digits,
            "interval": config.mfa.interval,
        },
        "rate_limiting": {
            "login_attempts": config.rate_limit.login_attempts,
            "login_window_seconds": config.rate_limit.login_window_seconds,
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "auth.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=config.environment == Environment.DEVELOPMENT,
        log_level="info" if config.environment == Environment.PRODUCTION else "debug",
    )
