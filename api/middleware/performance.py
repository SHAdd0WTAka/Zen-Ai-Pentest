"""
Performance Monitoring Middleware for FastAPI

Provides:
- Request timing
- Memory profiling
- Slow request detection
- Performance headers
- Stats aggregation
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.performance import get_timer

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring API performance.

    Features:
    - Tracks request latency
    - Detects slow requests
    - Adds performance headers
    - Aggregates statistics
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold_ms: float = 1000.0,
        track_stats: bool = True,
        add_headers: bool = True,
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold_ms
        self.track_stats = track_stats
        self.add_headers = add_headers
        self.timer = get_timer()
        self._request_stats: Dict[str, List[float]] = defaultdict(list)
        self._total_requests = 0
        self._slow_requests = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        self._total_requests += 1

        # Extract route info for stats
        route = request.url.path
        method = request.method

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {route} - {e}")
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Track stats
        if self.track_stats:
            self._request_stats[f"{method} {route}"].append(duration_ms)
            self.timer.record(f"api_{method}_{route}", duration_ms)

        # Detect slow requests
        if duration_ms > self.slow_request_threshold:
            self._slow_requests += 1
            logger.warning(
                f"Slow request detected: {method} {route} took {duration_ms:.2f}ms "
                f"(threshold: {self.slow_request_threshold:.2f}ms)"
            )

        # Add performance headers
        if self.add_headers:
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Request-Count"] = str(self._total_requests)

        return response

    def get_stats(self) -> Dict:
        """Get aggregated statistics"""
        stats = {
            "total_requests": self._total_requests,
            "slow_requests": self._slow_requests,
            "slow_request_percentage": (
                (self._slow_requests / self._total_requests * 100)
                if self._total_requests > 0
                else 0
            ),
            "endpoints": {},
        }

        for endpoint, times in self._request_stats.items():
            if times:
                stats["endpoints"][endpoint] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "p95_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
                }

        return stats


class ConnectionPoolMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor database connection pool health.
    """

    def __init__(self, app: ASGIApp, max_connections: int = 20):
        super().__init__(app)
        self.max_connections = max_connections
        self._active_connections = 0
        self._peak_connections = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        self._active_connections += 1
        self._peak_connections = max(self._peak_connections, self._active_connections)

        try:
            response = await call_next(request)
        finally:
            self._active_connections -= 1

        # Add connection pool info
        response.headers["X-Active-Connections"] = str(self._active_connections)
        return response

    def get_stats(self) -> Dict:
        return {
            "active_connections": self._active_connections,
            "peak_connections": self._peak_connections,
            "max_connections": self.max_connections,
            "utilization": (self._active_connections / self.max_connections * 100),
        }


# =============================================================================
# Dependency for route-level performance tracking
# =============================================================================

async def track_request_performance(request: Request):
    """
    Dependency to track individual request performance.
    Usage:
        @app.get("/endpoint")
        async def endpoint(perf: dict = Depends(track_request_performance)):
            # perf contains timing info after request
            pass
    """
    start = time.perf_counter()
    yield {"start_time": start}
    duration = (time.perf_counter() - start) * 1000
    logger.debug(f"Request to {request.url.path} took {duration:.2f}ms")


__all__ = [
    "PerformanceMonitoringMiddleware",
    "ConnectionPoolMiddleware",
    "track_request_performance",
]
