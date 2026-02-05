"""
Custom Middleware for FastAPI

- Rate limiting
- Security headers
- Request logging
"""

import logging
import time
from typing import Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api.core.config import settings

logger = logging.getLogger("ZenAI.API.Middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.requests: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit (simplified - use Redis in production)
        current_time = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove old requests (older than 1 minute)
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if current_time - t < 60
        ]

        # Check limit
        limit = settings.RATE_LIMIT_ANONYMOUS
        if len(self.requests[client_ip]) >= limit:
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"},
            )

        # Record request
        self.requests[client_ip].append(current_time)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {response.status_code} | "
            f"Duration: {duration:.3f}s | "
            f"Path: {request.url.path}"
        )

        # Add duration header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response
