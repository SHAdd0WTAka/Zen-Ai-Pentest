"""
Caching Strategy - Redis/Memory/SQLite backends
"""

import asyncio
import hashlib
import json
import logging
import pickle
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Union

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

import aiosqlite

logger = logging.getLogger(__name__)


class CacheBackend:
    """Abstract cache backend interface"""

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

    async def close(self):
        pass


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support"""

    def __init__(self, max_size: int = 1000):
        self._cache: dict = {}
        self._expiry: dict = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            # Check expiry
            if key in self._expiry:
                if datetime.utcnow() > self._expiry[key]:
                    del self._cache[key]
                    del self._expiry[key]
                    return None

            return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()

            self._cache[key] = value

            if ttl:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)

            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            return True

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
            return True

    def _evict_oldest(self):
        """Remove oldest entries"""
        if not self._cache:
            return

        # Remove expired entries first
        now = datetime.utcnow()
        expired = [k for k, exp in self._expiry.items() if exp and now > exp]
        for k in expired:
            del self._cache[k]
            del self._expiry[k]

        # If still at capacity, remove oldest
        if len(self._cache) >= self._max_size:
            oldest = min(self._expiry.keys(), key=lambda k: self._expiry[k])
            del self._cache[oldest]
            del self._expiry[oldest]


class SQLiteCache(CacheBackend):
    """SQLite-based persistent cache"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path.home() / ".cache" / "zen-ai-pentest" / "cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires TIMESTAMP
                )
            """)
            await self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires)
            """)
            await self._db.commit()
        return self._db

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            db = await self._get_db()

            cursor = await db.execute("SELECT value, expires FROM cache WHERE key = ?", (key,))
            row = await cursor.fetchone()

            if row is None:
                return None

            value, expires = row

            # Check expiry
            if expires and datetime.utcnow() > datetime.fromisoformat(expires):
                await self.delete(key)
                return None

            return pickle.loads(value)  # nosec B301

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            db = await self._get_db()

            expires = None
            if ttl:
                expires = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

            serialized = pickle.dumps(value)

            await db.execute(
                """INSERT OR REPLACE INTO cache (key, value, expires)
                   VALUES (?, ?, ?)""",
                (key, serialized, expires),
            )
            await db.commit()
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            db = await self._get_db()
            await db.execute("DELETE FROM cache WHERE key = ?", (key,))
            await db.commit()
            return True

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> bool:
        async with self._lock:
            db = await self._get_db()
            await db.execute("DELETE FROM cache")
            await db.commit()
            return True

    async def cleanup_expired(self):
        """Remove expired entries"""
        async with self._lock:
            db = await self._get_db()
            await db.execute("DELETE FROM cache WHERE expires < ?", (datetime.utcnow().isoformat(),))
            await db.commit()

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None


class RedisCache(CacheBackend):
    """Redis cache backend"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis not installed: pip install redis")

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,
            )
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                return pickle.loads(value)  # nosec B301
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            client = await self._get_client()
            serialized = pickle.dumps(value)
            await client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def clear(self) -> bool:
        try:
            client = await self._get_client()
            await client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


class MultiTierCache:
    """
    Multi-tier caching (L1: Memory, L2: SQLite, L3: Redis)
    """

    def __init__(
        self,
        memory_size: int = 100,
        sqlite_path: Optional[Path] = None,
        redis_config: Optional[dict] = None,
    ):
        self.l1 = MemoryCache(max_size=memory_size)
        self.l2 = SQLiteCache(sqlite_path) if sqlite_path else None
        self.l3 = None

        if redis_config and REDIS_AVAILABLE:
            try:
                self.l3 = RedisCache(**redis_config)
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (L1 -> L2 -> L3)"""
        # Try L1
        value = await self.l1.get(key)
        if value is not None:
            return value

        # Try L2
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                # Promote to L1
                await self.l1.set(key, value)
                return value

        # Try L3
        if self.l3:
            value = await self.l3.get(key)
            if value is not None:
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


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(
    backend: Union[CacheBackend, str] = "memory",
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
):
    """
    Decorator for caching function results

    Args:
        backend: Cache backend or "memory"/"sqlite"/"redis"
        ttl: Time to live in seconds
        key_func: Custom key generation function
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
