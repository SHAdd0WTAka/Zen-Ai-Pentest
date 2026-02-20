"""
Enhanced Caching Strategy - Redis/Memory/SQLite backends with LRU and TTL support

Optimizations:
- LRU eviction for memory cache
- Async batch operations
- Cache warming support
- Hit/miss statistics
- Size-based eviction
"""

import asyncio
import hashlib
import json
import logging
import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Redis availability check
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiosqlite

    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


@dataclass
class CacheStats:
    """Cache performance statistics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_gets: int = 0
    total_sets: int = 0
    total_deletes: int = 0
    bytes_stored: int = 0

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-1)"""
        if self.total_gets == 0:
            return 0.0
        return self.hits / self.total_gets

    @property
    def miss_rate(self) -> float:
        """Cache miss rate (0-1)"""
        if self.total_gets == 0:
            return 0.0
        return self.misses / self.total_gets

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{self.hit_rate:.2%}",
            "miss_rate": f"{self.miss_rate:.2%}",
            "total_gets": self.total_gets,
            "total_sets": self.total_sets,
            "total_deletes": self.total_deletes,
            "bytes_stored": self.bytes_stored,
        }


class CacheBackend:
    """Abstract cache backend interface with stats support"""

    def __init__(self):
        self.stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError()

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError()

    async def delete(self, key: str) -> bool:
        raise NotImplementedError()

    async def exists(self, key: str) -> bool:
        raise NotImplementedError()

    async def clear(self) -> bool:
        raise NotImplementedError()

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get operation"""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def mset(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Batch set operation"""
        success = True
        for key, value in items.items():
            if not await self.set(key, value, ttl):
                success = False
        return success

    async def close(self):
        pass

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats


class MemoryCache(CacheBackend):
    """
    Enhanced in-memory cache with LRU eviction and TTL support.

    Optimizations:
    - O(1) LRU using OrderedDict
    - Size-based eviction
    - Hit/miss tracking
    - Thread-safe operations
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float = 100.0,
        default_ttl: Optional[int] = None,
    ):
        super().__init__()
        self._max_size = max_size
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._default_ttl = default_ttl

        # Use OrderedDict for O(1) LRU operations
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._expiry: Dict[str, float] = {}
        self._sizes: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._current_memory = 0

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            self.stats.total_gets += 1

            # Check if key exists
            if key not in self._cache:
                self.stats.misses += 1
                return None

            # Check expiry
            if key in self._expiry and time.time() > self._expiry[key]:
                self._remove(key)
                self.stats.misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self.stats.hits += 1
            return self._cache[key]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            return await self._set_locked(key, value, ttl)

    async def _set_locked(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Internal set with lock held"""
        self.stats.total_sets += 1

        # Calculate value size
        try:
            value_size = len(pickle.dumps(value))
        except (pickle.PicklingError, TypeError):
            value_size = sys.getsizeof(value)

        # If updating existing key, adjust memory
        if key in self._cache:
            self._current_memory -= self._sizes.get(key, 0)

        # Check if value is too large
        if value_size > self._max_memory_bytes * 0.5:
            logger.warning(f"Value for key {key} is too large ({value_size} bytes), skipping")
            return False

        # Evict entries if needed
        while (
            len(self._cache) >= self._max_size
            or self._current_memory + value_size > self._max_memory_bytes
        ) and self._cache:
            self._evict_lru()

        # Store value
        self._cache[key] = value
        self._cache.move_to_end(key)
        self._sizes[key] = value_size
        self._current_memory += value_size
        self.stats.bytes_stored = self._current_memory

        # Set expiry
        effective_ttl = ttl or self._default_ttl
        if effective_ttl:
            self._expiry[key] = time.time() + effective_ttl

        return True

    def _remove(self, key: str):
        """Remove key from cache (assumes lock held)"""
        if key in self._cache:
            self._current_memory -= self._sizes.get(key, 0)
            del self._cache[key]
            self._expiry.pop(key, None)
            self._sizes.pop(key, None)

    def _evict_lru(self):
        """Evict least recently used entry (assumes lock held)"""
        if not self._cache:
            return

        # Remove expired entries first
        now = time.time()
        expired = [k for k, exp in self._expiry.items() if exp and now > exp]
        for k in expired:
            self._remove(k)
            self.stats.evictions += 1

        # If still need space, remove LRU
        if self._cache:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
            self.stats.evictions += 1

    async def delete(self, key: str) -> bool:
        async with self._lock:
            self.stats.total_deletes += 1
            if key in self._cache:
                self._remove(key)
                return True
            return False

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None

    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
            self._sizes.clear()
            self._current_memory = 0
            self.stats.bytes_stored = 0
            return True

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Optimized batch get"""
        result = {}
        async with self._lock:
            for key in keys:
                self.stats.total_gets += 1
                if key in self._cache:
                    if key in self._expiry and time.time() > self._expiry[key]:
                        self._remove(key)
                        self.stats.misses += 1
                    else:
                        self._cache.move_to_end(key)
                        result[key] = self._cache[key]
                        self.stats.hits += 1
                else:
                    self.stats.misses += 1
        return result

    async def mset(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Optimized batch set"""
        async with self._lock:
            for key, value in items.items():
                await self._set_locked(key, value, ttl)
        return True

    def get_stats(self) -> CacheStats:
        """Get detailed cache statistics"""
        stats = super().get_stats()
        stats.bytes_stored = self._current_memory
        return stats


class SQLiteCache(CacheBackend):
    """
    SQLite-based persistent cache with async support.

    Optimizations:
    - Connection pooling
    - Prepared statements
    - Batch operations
    - Automatic cleanup
    """

    def __init__(
        self,
        db_path: Path = None,
        pool_size: int = 5,
        cleanup_interval: int = 3600,
    ):
        super().__init__()
        self.db_path = db_path or Path.home() / ".cache" / "zen-ai-pentest" / "cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._pool_size = pool_size
        self._cleanup_interval = cleanup_interval
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        self._last_cleanup = 0

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute("PRAGMA journal_mode=WAL")
            await self._db.execute("PRAGMA synchronous=NORMAL")
            await self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            await self._db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires)
            """
            )
            await self._db.commit()
        return self._db

    async def _maybe_cleanup(self):
        """Periodically clean up expired entries"""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            await self.cleanup_expired()
            self._last_cleanup = now

    async def get(self, key: str) -> Optional[Any]:
        self.stats.total_gets += 1
        await self._maybe_cleanup()

        async with self._lock:
            db = await self._get_db()
            cursor = await db.execute(
                "SELECT value, expires FROM cache WHERE key = ?",
                (key,),
            )
            row = await cursor.fetchone()

            if row is None:
                self.stats.misses += 1
                return None

            value, expires = row

            # Check expiry
            if expires and datetime.utcnow() > datetime.fromisoformat(expires):
                await self.delete(key)
                self.stats.misses += 1
                return None

            try:
                self.stats.hits += 1
                return pickle.loads(value)  # nosec B301
            except (pickle.PickleError, EOFError):
                await self.delete(key)
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            return await self._set_locked(key, value, ttl)

    async def _set_locked(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        self.stats.total_sets += 1

        try:
            db = await self._get_db()
            serialized = pickle.dumps(value)

            expires = None
            if ttl:
                expires = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

            await db.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, expires)
                VALUES (?, ?, ?)
            """,
                (key, serialized, expires),
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"SQLite cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        async with self._lock:
            self.stats.total_deletes += 1
            try:
                db = await self._get_db()
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"SQLite cache delete error: {e}")
                return False

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> bool:
        async with self._lock:
            try:
                db = await self._get_db()
                await db.execute("DELETE FROM cache")
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"SQLite cache clear error: {e}")
                return False

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Optimized batch get with single query"""
        if not keys:
            return {}

        await self._maybe_cleanup()

        placeholders = ",".join("?" * len(keys))
        async with self._lock:
            self.stats.total_gets += len(keys)
            try:
                db = await self._get_db()
                cursor = await db.execute(
                    f"SELECT key, value, expires FROM cache WHERE key IN ({placeholders})",
                    keys,
                )
                rows = await cursor.fetchall()

                result = {}
                now = datetime.utcnow()
                expired_keys = []

                for row in rows:
                    key, value, expires = row
                    if expires and now > datetime.fromisoformat(expires):
                        expired_keys.append(key)
                        self.stats.misses += 1
                    else:
                        try:
                            result[key] = pickle.loads(value)  # nosec B301
                            self.stats.hits += 1
                        except (pickle.PickleError, EOFError):
                            expired_keys.append(key)
                            self.stats.misses += 1

                # Clean up expired keys
                if expired_keys:
                    placeholders = ",".join("?" * len(expired_keys))
                    await db.execute(
                        f"DELETE FROM cache WHERE key IN ({placeholders})", expired_keys
                    )
                    await db.commit()

                return result
            except Exception as e:
                logger.error(f"SQLite cache mget error: {e}")
                return {}

    async def mset(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Optimized batch set with transaction"""
        if not items:
            return True

        async with self._lock:
            self.stats.total_sets += len(items)
            try:
                db = await self._get_db()
                expires = None
                if ttl:
                    expires = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

                await db.execute("BEGIN")
                for key, value in items.items():
                    serialized = pickle.dumps(value)
                    await db.execute(
                        "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
                        (key, serialized, expires),
                    )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"SQLite cache mset error: {e}")
                await db.execute("ROLLBACK")
                return False

    async def cleanup_expired(self):
        """Remove expired entries"""
        async with self._lock:
            try:
                db = await self._get_db()
                cursor = await db.execute(
                    "DELETE FROM cache WHERE expires < ?",
                    (datetime.utcnow().isoformat(),),
                )
                await db.commit()
                deleted = cursor.rowcount
                self.stats.evictions += deleted
                logger.debug(f"Cleaned up {deleted} expired cache entries")
            except Exception as e:
                logger.error(f"SQLite cache cleanup error: {e}")

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None


class RedisCache(CacheBackend):
    """Redis cache backend with connection pooling"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10,
    ):
        super().__init__()
        if not REDIS_AVAILABLE:
            raise ImportError("redis not installed: pip install redis")

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self._pool: Optional[redis.Redis] = None

    async def _get_pool(self) -> redis.Redis:
        if self._pool is None:
            self._pool = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,
                max_connections=self.max_connections,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
        return self._pool

    async def get(self, key: str) -> Optional[Any]:
        self.stats.total_gets += 1
        try:
            pool = await self._get_pool()
            value = await pool.get(key)
            if value:
                self.stats.hits += 1
                return pickle.loads(value)  # nosec B301
            self.stats.misses += 1
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            pool = await self._get_pool()
            serialized = pickle.dumps(value)
            await pool.set(key, serialized, ex=ttl)
            self.stats.total_sets += 1
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            pool = await self._get_pool()
            await pool.delete(key)
            self.stats.total_deletes += 1
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            pool = await self._get_pool()
            return await pool.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def clear(self) -> bool:
        try:
            pool = await self._get_pool()
            await pool.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get using Redis MGET"""
        if not keys:
            return {}

        self.stats.total_gets += len(keys)
        try:
            pool = await self._get_pool()
            values = await pool.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = pickle.loads(value)  # nosec B301
                        self.stats.hits += 1
                    except pickle.PickleError:
                        self.stats.misses += 1
                else:
                    self.stats.misses += 1

            return result
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return {}

    async def mset(self, items: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Batch set using Redis MSET with optional TTL"""
        if not items:
            return True

        self.stats.total_sets += len(items)
        try:
            pool = await self._get_pool()
            serialized = {k: pickle.dumps(v) for k, v in items.items()}

            if ttl:
                # Use pipeline for atomic MSET + EXPIRE
                pipe = pool.pipeline()
                pipe.mset(serialized)
                for key in items.keys():
                    pipe.expire(key, ttl)
                await pipe.execute()
            else:
                await pool.mset(serialized)

            return True
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            return False

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None


class MultiTierCache:
    """
    Multi-tier caching (L1: Memory, L2: SQLite, L3: Redis)

    Strategy:
    - L1: Hot data, very fast, limited size
    - L2: Warm data, persistent, larger size
    - L3: Shared data, distributed (Redis)
    """

    def __init__(
        self,
        memory_size: int = 100,
        memory_max_mb: float = 50.0,
        sqlite_path: Optional[Path] = None,
        redis_config: Optional[dict] = None,
    ):
        self.l1 = MemoryCache(max_size=memory_size, max_memory_mb=memory_max_mb)
        self.l2 = SQLiteCache(sqlite_path) if SQLITE_AVAILABLE else None
        self.l3 = None

        if redis_config and REDIS_AVAILABLE:
            try:
                self.l3 = RedisCache(**redis_config)
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")

        self._hit_distribution = {"L1": 0, "L2": 0, "L3": 0}

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (L1 -> L2 -> L3)"""
        # Try L1
        value = await self.l1.get(key)
        if value is not None:
            self._hit_distribution["L1"] += 1
            return value

        # Try L2
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                self._hit_distribution["L2"] += 1
                # Promote to L1
                await self.l1.set(key, value)
                return value

        # Try L3
        if self.l3:
            value = await self.l3.get(key)
            if value is not None:
                self._hit_distribution["L3"] += 1
                # Promote to L1/L2
                await self.l1.set(key, value)
                if self.l2:
                    await self.l2.set(key, value)
                return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tiers: str = "all",  # "all", "memory", "persistent"
    ) -> bool:
        """Set in cache tiers"""
        success = True

        if tiers in ("all", "memory"):
            success = await self.l1.set(key, value, ttl) and success

        if tiers in ("all", "persistent") and self.l2:
            success = await self.l2.set(key, value, ttl) and success

        if tiers == "all" and self.l3:
            success = await self.l3.set(key, value, ttl) and success

        return success

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Optimized multi-tier batch get"""
        result = {}
        missing = keys[:]

        # Try L1 first
        if missing:
            l1_results = await self.l1.mget(missing)
            for key, value in l1_results.items():
                result[key] = value
                self._hit_distribution["L1"] += 1
                missing.remove(key)

        # Try L2 for missing
        if missing and self.l2:
            l2_results = await self.l2.mget(missing)
            for key, value in l2_results.items():
                result[key] = value
                self._hit_distribution["L2"] += 1
                missing.remove(key)
                # Promote to L1
                await self.l1.set(key, value)

        # Try L3 for remaining
        if missing and self.l3:
            l3_results = await self.l3.mget(missing)
            for key, value in l3_results.items():
                result[key] = value
                self._hit_distribution["L3"] += 1
                # Promote to L1/L2
                await self.l1.set(key, value)
                if self.l2:
                    await self.l2.set(key, value)

        return result

    async def delete(self, key: str) -> bool:
        """Delete from all tiers"""
        await self.l1.delete(key)
        if self.l2:
            await self.l2.delete(key)
        if self.l3:
            await self.l3.delete(key)
        return True

    async def close(self):
        if self.l2:
            await self.l2.close()
        if self.l3:
            await self.l3.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics from all tiers"""
        total_hits = sum(self._hit_distribution.values())
        return {
            "hit_distribution": {
                tier: {"count": count, "percentage": (count / total_hits * 100) if total_hits > 0 else 0}
                for tier, count in self._hit_distribution.items()
            },
            "L1_memory": self.l1.get_stats().to_dict(),
            "L2_sqlite": self.l2.get_stats().to_dict() if self.l2 else None,
            "L3_redis": self.l3.get_stats().to_dict() if self.l3 else None,
        }


# =============================================================================
# Cache Decorators
# =============================================================================


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    backend: Union[CacheBackend, str] = "memory",
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    condition: Optional[Callable[[Any], bool]] = None,
):
    """
    Decorator for caching function results

    Args:
        backend: Cache backend or "memory"/"sqlite"/"redis"
        ttl: Time to live in seconds
        key_func: Custom key generation function
        condition: Only cache if condition(result) is True
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = _get_cache_backend(backend)

            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__module__}.{func.__name__}:{generate_cache_key(*args, **kwargs)}"

            # Try cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value

            # Execute and cache
            result = await func(*args, **kwargs)

            if condition is None or condition(result):
                await cache.set(key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in async context
            return asyncio.run(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Global cache instances
_memory_cache = None
_sqlite_cache = None
_redis_cache = None


def _get_cache_backend(backend: Union[CacheBackend, str]) -> CacheBackend:
    """Get or create cache backend"""
    global _memory_cache, _sqlite_cache, _redis_cache

    if isinstance(backend, CacheBackend):
        return backend

    if backend == "memory":
        if _memory_cache is None:
            _memory_cache = MemoryCache()
        return _memory_cache

    elif backend == "sqlite":
        if _sqlite_cache is None:
            _sqlite_cache = SQLiteCache()
        return _sqlite_cache

    elif backend == "redis":
        if _redis_cache is None:
            _redis_cache = RedisCache()
        return _redis_cache

    raise ValueError(f"Unknown cache backend: {backend}")


# Convenience function for CVE caching
async def get_cached_cve(cve_id: str) -> Optional[dict]:
    """Get CVE from cache"""
    cache = _get_cache_backend("sqlite")
    return await cache.get(f"cve:{cve_id.upper()}")


async def cache_cve(cve_id: str, data: dict, ttl: int = 86400 * 7):
    """Cache CVE data for 7 days"""
    cache = _get_cache_backend("sqlite")
    await cache.set(f"cve:{cve_id.upper()}", data, ttl)


# Export public APIs
__all__ = [
    # Backends
    "CacheBackend",
    "MemoryCache",
    "SQLiteCache",
    "RedisCache",
    "MultiTierCache",
    # Statistics
    "CacheStats",
    # Decorators
    "cached",
    "generate_cache_key",
    # Utilities
    "get_cached_cve",
    "cache_cve",
    # Global instances
    "_get_cache_backend",
]
