"""
Performance Optimization Module

Provides caching, connection pooling, and async optimizations.

Usage:
    from performance import CacheManager, ConnectionPool
    
    cache = CacheManager()
    await cache.set("key", value, ttl=300)
    value = await cache.get("key")
"""

from .cache import CacheManager, CacheConfig
from .pool import ConnectionPool, PoolConfig
from .async_optimizer import AsyncOptimizer
from .metrics import PerformanceMetrics

__all__ = [
    "CacheManager",
    "CacheConfig",
    "ConnectionPool",
    "PoolConfig",
    "AsyncOptimizer",
    "PerformanceMetrics",
]
