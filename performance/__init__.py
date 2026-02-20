"""
Performance Optimization Module

Provides caching, connection pooling, and async optimizations.

Usage:
    from performance import CacheManager, ConnectionPool

    cache = CacheManager()
    await cache.set("key", value, ttl=300)
    value = await cache.get("key")
"""

from .async_optimizer import AsyncOptimizer
from .cache import CacheConfig, CacheManager
from .metrics import PerformanceMetrics
from .pool import ConnectionPool, PoolConfig

__all__ = [
    "CacheManager",
    "CacheConfig",
    "ConnectionPool",
    "PoolConfig",
    "AsyncOptimizer",
    "PerformanceMetrics",
]
