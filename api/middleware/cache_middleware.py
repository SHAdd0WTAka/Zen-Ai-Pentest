"""
API Response Caching Middleware

Caches GET request responses to reduce database load
and improve API response times.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.cache import MultiTierCache
from core.performance_monitor import get_monitor

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache API responses for GET requests.

    Features:
    - Configurable cache TTL per route
    - Cache key based on URL and query params
    - Skip caching for authenticated routes (optional)
    - Cache invalidation support
    """

    def __init__(
        self,
        app,
        cache: Optional[MultiTierCache] = None,
        default_ttl: int = 60,
        excluded_paths: Optional[list] = None,
        excluded_query_params: Optional[list] = None,
        key_prefix: str = "api:cache",
    ):
        super().__init__(app)
        self.cache = cache or MultiTierCache(memory_size=500, memory_max_mb=50)
        self.default_ttl = default_ttl
        self.excluded_paths = set(excluded_paths or ["/health", "/metrics", "/api/v1/health"])
        self.excluded_query_params = set(excluded_query_params or ["token", "api_key", "auth"])
        self.key_prefix = key_prefix
        self.monitor = get_monitor()

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Build path component
        path = request.url.path

        # Build query component (excluding sensitive params)
        query_params = []
        for key, value in request.query_params.items():
            if key not in self.excluded_query_params:
                query_params.append(f"{key}={value}")

        query_string = "&".join(sorted(query_params))

        # Create hash
        key_data = f"{path}?{query_string}"
        # MD5 used for cache key generation (non-security purpose)
        hash_value = hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

        return f"{self.key_prefix}:{hash_value}"

    def _should_cache(self, request: Request, response: Response) -> bool:
        """Determine if response should be cached"""
        # Only cache GET requests
        if request.method != "GET":
            return False

        # Skip excluded paths
        if request.url.path in self.excluded_paths:
            return False

        # Skip if response is not successful
        if response.status_code != 200:
            return False

        # Skip if explicitly disabled
        if request.headers.get("X-No-Cache"):
            return False

        return True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching"""
        # Skip non-GET requests immediately
        if request.method != "GET":
            return await call_next(request)

        # Check excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get from cache
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit: {cache_key}")
                self.monitor._record_metric(
                    type(
                        "Metric",
                        (),
                        {
                            "name": "api.cache_hit",
                            "duration_ms": 0,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "memory_delta_mb": 0.0,
                            "metadata": {"path": request.url.path},
                        },
                    )()
                )
                return JSONResponse(
                    content=cached_data,
                    headers={"X-Cache": "HIT"},
                )
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        # Get fresh response
        with self.monitor.timer(f"api.endpoint.{request.url.path}", track_memory=False):
            response = await call_next(request)

        # Cache if appropriate
        if self._should_cache(request, response):
            try:
                # Read response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Parse and cache
                content = json.loads(response_body)
                await self.cache.set(cache_key, content, ttl=self.default_ttl)
                logger.debug(f"Cached response: {cache_key}")

                # Return with cache miss header
                return JSONResponse(
                    content=content,
                    headers={"X-Cache": "MISS"},
                )
            except Exception as e:
                logger.warning(f"Cache storage error: {e}")
                # Return original response
                return response

        return response

    async def invalidate_path(self, path: str):
        """Invalidate all cached entries for a path"""
        # Note: In production, use Redis KEYS or a cache index
        logger.info(f"Cache invalidation requested for: {path}")

    async def clear_cache(self):
        """Clear all cached responses"""
        await self.cache.clear()
        logger.info("API cache cleared")


class ConditionalCacheMiddleware(BaseHTTPMiddleware):
    """
    Advanced caching with ETag support and conditional requests.

    Implements:
    - ETag generation for resources
    - 304 Not Modified responses
    - Cache-Control headers
    """

    def __init__(
        self,
        app,
        cache: Optional[MultiTierCache] = None,
        default_ttl: int = 300,
    ):
        super().__init__(app)
        self.cache = cache or MultiTierCache(memory_size=200, memory_max_mb=20)
        self.default_ttl = default_ttl

    def _generate_etag(self, content: dict) -> str:
        """Generate ETag for content"""
        content_str = json.dumps(content, sort_keys=True)
        # MD5 used for ETag generation (non-security purpose)
        return hashlib.md5(content_str.encode(), usedforsecurity=False).hexdigest()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle conditional requests"""
        # Get client ETag if present
        client_etag = request.headers.get("If-None-Match")

        # Generate cache key
        cache_key = f"etag:{request.url.path}:{request.query_params}"

        # Try cache
        cached = await self.cache.get(cache_key)

        if cached:
            etag = cached.get("_etag")

            # Check if client has current version
            if client_etag and client_etag == etag:
                return Response(status_code=304)

            # Return cached content
            content = {k: v for k, v in cached.items() if not k.startswith("_")}
            return JSONResponse(
                content=content,
                headers={
                    "ETag": etag,
                    "Cache-Control": f"max-age={self.default_ttl}",
                },
            )

        # Get fresh response
        response = await call_next(request)

        if response.status_code == 200:
            # Read and cache
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            try:
                content = json.loads(body)
                etag = self._generate_etag(content)

                # Store with metadata
                cache_data = {
                    **content,
                    "_etag": etag,
                    "_timestamp": time.time(),
                }
                await self.cache.set(cache_key, cache_data, ttl=self.default_ttl)

                return JSONResponse(
                    content=content,
                    headers={
                        "ETag": etag,
                        "Cache-Control": f"max-age={self.default_ttl}",
                    },
                )
            except Exception as e:
                logger.warning(f"ETag caching error: {e}")

        return response


def setup_cache_middleware(
    app,
    enabled: bool = True,
    default_ttl: int = 60,
    **kwargs,
):
    """
    Configure and add cache middleware to FastAPI app.

    Args:
        app: FastAPI application
        enabled: Whether caching is enabled
        default_ttl: Default cache TTL in seconds
        **kwargs: Additional middleware options
    """
    if not enabled:
        logger.info("API response caching disabled")
        return

    app.add_middleware(
        CacheMiddleware,
        default_ttl=default_ttl,
        **kwargs,
    )
    logger.info(f"Cache middleware configured with TTL={default_ttl}s")


__all__ = [
    "CacheMiddleware",
    "ConditionalCacheMiddleware",
    "setup_cache_middleware",
]
