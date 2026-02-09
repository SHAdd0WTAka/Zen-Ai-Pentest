"""
Caching Strategy - Redis/Memory/SQLite backends
Performance Optimizations:
- Multi-tier caching (L1: Memory, L2: SQLite, L3: Redis)
- Compression for large data (zlib)
- Cache warming support
- Cache statistics/metrics
- Optimized key generation
"""

import asyncio
import hashlib
import json
import logging
import pickle
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Union, Dict, List, Set

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiosqlite
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_bytes_stored: int = 0
    total_bytes_compressed: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def compression_ratio(self) -> float:
        if self.total_bytes_stored == 0:
            return 1.0
        return self.total_bytes_compressed / self.total_bytes_stored
    
    def to_dict(self) -> Dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 4),
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "compression_ratio": round(self.compression_ratio, 4),
            "total_bytes_stored": self.total_bytes_stored,
            "total_bytes_compressed": self.total_bytes_compressed,
        }


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

    async def get_stats(self) -> CacheStats:
        """Get cache statistics (optional implementation)."""
        return CacheStats()


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support and compression for large values."""

    def __init__(self, max_size: int = 1000, compression_threshold: int = 1024):
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}
        self._compressed: Set[str] = set()
        self._max_size = max_size
        self._compression_threshold = compression_threshold
        self._lock = asyncio.Lock()
        self._stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            # Check expiry
            if key in self._expiry:
                if datetime.now(timezone.utc) > self._expiry[key]:
                    await self._delete_internal(key)
                    self._stats.misses += 1
                    return None

            value = self._cache.get(key)
            if value is not None:
                # Decompress and deserialize
                try:
                    if key in self._compressed:
                        value = pickle.loads(zlib.decompress(value))
                    else:
                        value = pickle.loads(value)
                except Exception as e:
                    logger.error(f"Deserialization error for key {key}: {e}")
                    await self._delete_internal(key)
                    self._stats.misses += 1
                    return None
                self._stats.hits += 1
                return value
            
            self._stats.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()

            # Compress large values
            serialized = pickle.dumps(value)
            self._stats.total_bytes_stored += len(serialized)
            
            if len(serialized) > self._compression_threshold:
                try:
                    compressed = zlib.compress(serialized, level=6)
                    if len(compressed) < len(serialized):
                        value = compressed
                        self._compressed.add(key)
                        self._stats.total_bytes_compressed += len(compressed)
                    else:
                        value = serialized
                except Exception as e:
                    logger.warning(f"Compression failed for key {key}: {e}")
                    value = serialized
            else:
                value = serialized

            self._cache[key] = value

            if ttl:
                self._expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl)

            self._stats.sets += 1
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            return await self._delete_internal(key)

    async def _delete_internal(self, key: str) -> bool:
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        self._compressed.discard(key)
        self._stats.deletes += 1
        return True

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
            self._compressed.clear()
            return True

    def _evict_oldest(self):
        """Remove oldest entries"""
        if not self._cache:
            return

        # Remove expired entries first
        now = datetime.now(timezone.utc)
        expired = [k for k, exp in self._expiry.items() if exp and now > exp]
        for k in expired:
            self._cache.pop(k, None)
            self._expiry.pop(k, None)
            self._compressed.discard(k)
            self._stats.evictions += 1

        # If still at capacity, remove oldest
        if len(self._cache) >= self._max_size:
            oldest = min(self._expiry.keys(), key=lambda k: self._expiry[k])
            self._cache.pop(oldest, None)
            self._expiry.pop(oldest, None)
            self._compressed.discard(oldest)
            self._stats.evictions += 1

    async def get_stats(self) -> CacheStats:
        async with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
                evictions=self._stats.evictions,
                total_bytes_stored=self._stats.total_bytes_stored,
                total_bytes_compressed=self._stats.total_bytes_compressed,
            )


class SQLiteCache(CacheBackend):
    """SQLite-based persistent cache with compression."""

    def __init__(self, db_path: Path = None, compression: bool = True):
        if not AIOSQLITE_AVAILABLE:
            raise ImportError("aiosqlite not installed: pip install aiosqlite")
            
        self.db_path = db_path or Path.home() / ".cache" / "zen-ai-pentest" / "cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        self._compression = compression
        self._stats = CacheStats()

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires TIMESTAMP,
                    compressed INTEGER DEFAULT 0
                )
            """)
            await self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires)
            """)
            await self._db.execute("""
                CREATE INDEX IF NOT EXISTS idx_key ON cache(key)
            """)
            await self._db.commit()
        return self._db

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            db = await self._get_db()

            cursor = await db.execute(
                "SELECT value, expires, compressed FROM cache WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()

            if row is None:
                self._stats.misses += 1
                return None

            value, expires, compressed = row

            # Check expiry
            if expires and datetime.now(timezone.utc) > datetime.fromisoformat(expires):
                await self.delete(key)
                self._stats.misses += 1
                return None

            try:
                if compressed:
                    value = zlib.decompress(value)
                result = pickle.loads(value)
                self._stats.hits += 1
                return result
            except Exception as e:
                logger.error(f"Deserialization error for key {key}: {e}")
                await self.delete(key)
                self._stats.misses += 1
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            db = await self._get_db()

            expires = None
            if ttl:
                expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()

            serialized = pickle.dumps(value)
            compressed = 0
            
            self._stats.total_bytes_stored += len(serialized)

            if self._compression and len(serialized) > 1024:
                try:
                    compressed_data = zlib.compress(serialized, level=6)
                    if len(compressed_data) < len(serialized):
                        serialized = compressed_data
                        compressed = 1
                        self._stats.total_bytes_compressed += len(compressed_data)
                except Exception as e:
                    logger.warning(f"Compression failed for key {key}: {e}")

            await db.execute(
                """INSERT OR REPLACE INTO cache (key, value, expires, compressed)
                   VALUES (?, ?, ?, ?)""",
                (key, serialized, expires, compressed),
            )
            await db.commit()
            self._stats.sets += 1
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            db = await self._get_db()
            await db.execute("DELETE FROM cache WHERE key = ?", (key,))
            await db.commit()
            self._stats.deletes += 1
            return True

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> bool:
        async with self._lock:
            db = await self._get_db()
            await db.execute("DELETE FROM cache")
            await db.commit()
            return True

    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count."""
        async with self._lock:
            db = await self._get_db()
            cursor = await db.execute(
                "DELETE FROM cache WHERE expires < ?",
                (datetime.now(timezone.utc).isoformat(),)
            )
            await db.commit()
            self._stats.evictions += cursor.rowcount
            return cursor.rowcount

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None

    async def get_stats(self) -> CacheStats:
        async with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
                evictions=self._stats.evictions,
                total_bytes_stored=self._stats.total_bytes_stored,
                total_bytes_compressed=self._stats.total_bytes_compressed,
            )


class RedisCache(CacheBackend):
    """Redis cache backend with compression support."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        compression: bool = True,
        compression_threshold: int = 1024,
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis not installed: pip install redis")

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client: Optional[Any] = None
        self._compression = compression
        self._compression_threshold = compression_threshold
        self._stats = CacheStats()

    async def _get_client(self) -> Any:
        if self._client is None:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                try:
                    # Check if compressed (first byte indicates compression)
                    if value.startswith(b'\x01'):
                        value = zlib.decompress(value[1:])
                    result = pickle.loads(value)
                    self._stats.hits += 1
                    return result
                except Exception as e:
                    logger.error(f"Redis deserialization error: {e}")
                    await self.delete(key)
                    self._stats.misses += 1
                    return None
            self._stats.misses += 1
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._stats.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            client = await self._get_client()
            serialized = pickle.dumps(value)
            self._stats.total_bytes_stored += len(serialized)

            if self._compression and len(serialized) > self._compression_threshold:
                try:
                    compressed = zlib.compress(serialized, level=6)
                    # Prefix with \x01 to indicate compression
                    serialized = b'\x01' + compressed
                    self._stats.total_bytes_compressed += len(serialized)
                except Exception as e:
                    logger.warning(f"Redis compression failed: {e}")

            await client.set(key, serialized, ex=ttl)
            self._stats.sets += 1
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = await self._get_client()
            await client.delete(key)
            self._stats.deletes += 1
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

    async def get_stats(self) -> CacheStats:
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            sets=self._stats.sets,
            deletes=self._stats.deletes,
            evictions=self._stats.evictions,
            total_bytes_stored=self._stats.total_bytes_stored,
            total_bytes_compressed=self._stats.total_bytes_compressed,
        )


class MultiTierCache:
    """
    Multi-tier caching (L1: Memory, L2: SQLite, L3: Redis)
    with cache warming and statistics.
    """

    def __init__(
        self,
        memory_size: int = 100,
        sqlite_path: Optional[Path] = None,
        redis_config: Optional[dict] = None,
        compression: bool = True,
    ):
        self.l1 = MemoryCache(max_size=memory_size)
        self.l2 = SQLiteCache(sqlite_path, compression=compression) if sqlite_path is not None else None
        self.l3 = None

        if redis_config and REDIS_AVAILABLE:
            try:
                self.l3 = RedisCache(**redis_config, compression=compression)
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")

        self._stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (L1 -> L2 -> L3)"""
        # Try L1
        value = await self.l1.get(key)
        if value is not None:
            self._stats.hits += 1
            return value

        # Try L2
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                # Promote to L1
                await self.l1.set(key, value)
                self._stats.hits += 1
                return value

        # Try L3
        if self.l3:
            value = await self.l3.get(key)
            if value is not None:
                # Promote to L1/L2
                await self.l1.set(key, value)
                if self.l2:
                    await self.l2.set(key, value)
                self._stats.hits += 1
                return value

        self._stats.misses += 1
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

        if success:
            self._stats.sets += 1
        return success

    async def delete(self, key: str) -> bool:
        """Delete from all tiers"""
        await self.l1.delete(key)
        if self.l2:
            await self.l2.delete(key)
        if self.l3:
            await self.l3.delete(key)
        self._stats.deletes += 1
        return True

    async def warm_cache(self, entries: Dict[str, Any], ttl: Optional[int] = None):
        """
        Warm the cache with a batch of entries.
        
        Args:
            entries: Dictionary of key -> value pairs
            ttl: Time to live for all entries
        """
        tasks = []
        for key, value in entries.items():
            tasks.append(self.set(key, value, ttl))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Cache warmed with {len(entries)} entries")

    async def warm_cache_async(
        self, 
        key_generator: Callable[[], List[str]],
        value_fetcher: Callable[[str], Any],
        ttl: Optional[int] = None,
        max_concurrent: int = 10
    ):
        """
        Async cache warming with parallel fetching.
        
        Args:
            key_generator: Function that returns list of keys to warm
            value_fetcher: Async function to fetch value for a key
            ttl: Time to live for warmed entries
            max_concurrent: Max concurrent fetches
        """
        keys = key_generator()
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_and_cache(key: str):
            async with semaphore:
                try:
                    value = await value_fetcher(key)
                    if value is not None:
                        await self.set(key, value, ttl)
                except Exception as e:
                    logger.warning(f"Failed to warm cache for key {key}: {e}")
        
        tasks = [fetch_and_cache(key) for key in keys]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Async cache warming completed for {len(keys)} keys")

    async def get_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all tiers."""
        stats = {
            "combined": CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                sets=self._stats.sets,
                deletes=self._stats.deletes,
            ),
            "l1_memory": await self.l1.get_stats(),
        }
        
        if self.l2:
            stats["l2_sqlite"] = await self.l2.get_stats()
        if self.l3:
            stats["l3_redis"] = await self.l3.get_stats()
        
        return stats

    async def close(self):
        if self.l2:
            await self.l2.close()
        if self.l3:
            await self.l3.close()


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments (optimized)."""
    # Use faster hash for simple keys
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(key_data.encode()).hexdigest()[:32]


def cached(
    backend: Union[CacheBackend, str] = "memory",
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    cache_none: bool = False,
):
    """
    Decorator for caching function results

    Args:
        backend: Cache backend or "memory"/"sqlite"/"redis"
        ttl: Time to live in seconds
        key_func: Custom key generation function
        cache_none: Whether to cache None results
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
            if cached_value is not None or (cache_none and cached_value is None):
                logger.debug(f"Cache hit: {key}")
                return cached_value

            # Execute and cache
            result = await func(*args, **kwargs)
            if result is not None or cache_none:
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
_multi_tier_cache = None


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


def get_multi_tier_cache(
    memory_size: int = 100,
    sqlite_path: Optional[Path] = None,
    redis_config: Optional[dict] = None,
) -> MultiTierCache:
    """Get or create multi-tier cache instance."""
    global _multi_tier_cache
    if _multi_tier_cache is None:
        _multi_tier_cache = MultiTierCache(
            memory_size=memory_size,
            sqlite_path=sqlite_path,
            redis_config=redis_config,
        )
    return _multi_tier_cache


# Convenience function for CVE caching
async def get_cached_cve(cve_id: str) -> Optional[dict]:
    """Get CVE from cache"""
    cache = _get_cache_backend("sqlite")
    return await cache.get(f"cve:{cve_id.upper()}")


async def cache_cve(cve_id: str, data: dict, ttl: int = 86400 * 7):
    """Cache CVE data for 7 days"""
    cache = _get_cache_backend("sqlite")
    await cache.set(f"cve:{cve_id.upper()}", data, ttl)


# Batch CVE caching
async def cache_cves_batch(cve_data: Dict[str, dict], ttl: int = 86400 * 7):
    """Cache multiple CVEs at once."""
    cache = _get_cache_backend("sqlite")
    tasks = [
        cache.set(f"cve:{cve_id.upper()}", data, ttl)
        for cve_id, data in cve_data.items()
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
