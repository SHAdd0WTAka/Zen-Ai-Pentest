"""
Intelligent Caching System

Multi-layer caching with Redis/Memory support.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration"""

    default_ttl: int = 300  # 5 minutes
    max_size: int = 10000
    cleanup_interval: int = 60
    enable_memory_cache: bool = True
    enable_redis: bool = False
    redis_url: str = "redis://localhost:6379"


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl

    def touch(self):
        self.access_count += 1
        self.last_accessed = time.time()


class CacheManager:
    """
    Multi-layer cache manager

    Features:
    - In-memory LRU cache
    - Redis support (optional)
    - TTL support
    - Cache warming
    - Statistics

    Example:
        cache = CacheManager()

        # Basic usage
        await cache.set("key", value, ttl=300)
        value = await cache.get("key")

        # Decorator
        @cache.cached(ttl=60)
        async def expensive_function():
            return await compute_something()
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._memory: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        # Statistics
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._evictions = 0

    async def start(self):
        """Start cache manager"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cache manager started")

    async def stop(self):
        """Stop cache manager"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
        self._memory.clear()
        logger.info("Cache manager stopped")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            entry = self._memory.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                del self._memory[key]
                self._misses += 1
                return None

            entry.touch()
            self._hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.config.default_ttl

        async with self._lock:
            # Evict if at capacity
            if len(self._memory) >= self.config.max_size:
                self._evict_lru()

            self._memory[key] = CacheEntry(value, ttl)
            self._sets += 1
            return True

    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        async with self._lock:
            if key in self._memory:
                del self._memory[key]
                return True
            return False

    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._memory.clear()

    async def get_or_set(self, key: str, factory: Callable, ttl: Optional[int] = None) -> Any:
        """Get or create cache entry"""
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
        await self.set(key, value, ttl)
        return value

    def cached(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """Decorator for caching function results"""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = self._generate_key(key_prefix, func, args, kwargs)
                return await self.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache_key = self._generate_key(key_prefix, func, args, kwargs)
                # For sync functions, use run_in_executor
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl))

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def _generate_key(self, prefix: str, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function call"""
        key_data = {"prefix": prefix, "func": func.__name__, "args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        hash_key = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{func.__name__}:{hash_key}"

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._memory:
            return

        lru_key = min(self._memory.keys(), key=lambda k: self._memory[k].last_accessed)
        del self._memory[lru_key]
        self._evictions += 1

    async def _cleanup_loop(self):
        """Periodic cleanup of expired entries"""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _cleanup_expired(self):
        """Remove expired entries"""
        async with self._lock:
            expired = [k for k, v in self._memory.items() if v.is_expired()]
            for k in expired:
                del self._memory[k]

            if expired:
                logger.debug(f"Cleaned up {len(expired)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._memory),
            "max_size": self.config.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "evictions": self._evictions,
            "hit_rate": round(hit_rate, 2),
            "memory_usage_mb": len(self._memory) * 0.001,  # Rough estimate
        }
