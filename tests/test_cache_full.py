"""
Comprehensive tests for core/cache.py - Complete coverage for all cache backends.

Targets 90-100% coverage for:
- CacheStats
- CacheBackend
- MemoryCache
- SQLiteCache
- RedisCache
- MultiTierCache
- Cache decorators and utilities
"""

import asyncio
import pickle
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest
import pytest_asyncio

# Import all cache components
from core.cache import (
    REDIS_AVAILABLE,
    SQLITE_AVAILABLE,
    Cache,
    CacheBackend,
    CacheStats,
    MemoryCache,
    MultiTierCache,
    RedisCache,
    SQLiteCache,
    _get_cache_backend,
    cache_cve,
    cached,
    generate_cache_key,
    get_cached_cve,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    _tmpf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmpf.close()
    tmp = Path(_tmpf.name)
    yield tmp
    # Cleanup
    if tmp.exists():
        tmp.unlink(missing_ok=True)


@pytest_asyncio.fixture
async def memory_cache():
    """Create a MemoryCache instance."""
    cache = MemoryCache(max_size=100, max_memory_mb=10)
    yield cache
    await cache.clear()


@pytest_asyncio.fixture
async def sqlite_cache(temp_db_path):
    """Create a SQLiteCache instance."""
    if not SQLITE_AVAILABLE:
        pytest.skip("aiosqlite not available")
    cache = SQLiteCache(db_path=temp_db_path)
    yield cache
    await cache.close()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(return_value=None)
    mock_pool.set = AsyncMock(return_value=True)
    mock_pool.setex = AsyncMock(return_value=True)
    mock_pool.delete = AsyncMock(return_value=1)
    mock_pool.exists = AsyncMock(return_value=0)
    mock_pool.flushdb = AsyncMock(return_value=True)
    mock_pool.mget = AsyncMock(return_value=[])
    mock_pool.mset = AsyncMock(return_value=True)
    mock_pool.pipeline = MagicMock(return_value=AsyncMock())
    mock_pool.close = AsyncMock()
    return mock_pool


@pytest_asyncio.fixture
async def redis_cache(mock_redis):
    """Create a RedisCache instance with mocked Redis."""
    if not REDIS_AVAILABLE:
        pytest.skip("redis not available")

    cache = RedisCache(host="localhost", port=6379)
    cache._pool = mock_redis
    yield cache
    await cache.close()


@pytest_asyncio.fixture
async def multi_tier_cache(temp_db_path):
    """Create a MultiTierCache instance."""
    cache = MultiTierCache(memory_size=50, sqlite_path=temp_db_path)
    yield cache
    await cache.close()


# ============================================================================
# CacheStats Tests
# ============================================================================


class TestCacheStats:
    """Test CacheStats dataclass."""

    def test_default_values(self):
        """Test default values of CacheStats."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_gets == 0
        assert stats.total_sets == 0
        assert stats.total_deletes == 0
        assert stats.bytes_stored == 0

    def test_hit_rate_zero_when_no_gets(self):
        """Test hit_rate returns 0 when no gets."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit_rate calculation."""
        stats = CacheStats()
        stats.total_gets = 10
        stats.hits = 7
        assert stats.hit_rate == 0.7

    def test_miss_rate_zero_when_no_gets(self):
        """Test miss_rate returns 0 when no gets."""
        stats = CacheStats()
        assert stats.miss_rate == 0.0

    def test_miss_rate_calculation(self):
        """Test miss_rate calculation."""
        stats = CacheStats()
        stats.total_gets = 10
        stats.misses = 3
        assert stats.miss_rate == 0.3

    def test_to_dict(self):
        """Test to_dict serialization."""
        stats = CacheStats(
            hits=100,
            misses=20,
            evictions=5,
            total_gets=120,
            total_sets=50,
            total_deletes=10,
            bytes_stored=1024,
        )
        d = stats.to_dict()
        assert d["hits"] == 100
        assert d["misses"] == 20
        assert d["evictions"] == 5
        assert d["total_gets"] == 120
        assert d["total_sets"] == 50
        assert d["total_deletes"] == 10
        assert d["bytes_stored"] == 1024
        assert d["hit_rate"] == "83.33%"
        assert d["miss_rate"] == "16.67%"

    def test_to_dict_with_zero_gets(self):
        """Test to_dict with zero total_gets."""
        stats = CacheStats()
        d = stats.to_dict()
        assert d["hit_rate"] == "0.00%"
        assert d["miss_rate"] == "0.00%"


# ============================================================================
# CacheBackend Abstract Class Tests
# ============================================================================


class TestCacheBackend:
    """Test CacheBackend abstract class."""

    @pytest.mark.asyncio
    async def test_get_raises_not_implemented(self):
        """Test get raises NotImplementedError."""
        backend = CacheBackend()
        with pytest.raises(NotImplementedError):
            await backend.get("key")

    @pytest.mark.asyncio
    async def test_set_raises_not_implemented(self):
        """Test set raises NotImplementedError."""
        backend = CacheBackend()
        with pytest.raises(NotImplementedError):
            await backend.set("key", "value")

    @pytest.mark.asyncio
    async def test_delete_raises_not_implemented(self):
        """Test delete raises NotImplementedError."""
        backend = CacheBackend()
        with pytest.raises(NotImplementedError):
            await backend.delete("key")

    @pytest.mark.asyncio
    async def test_exists_raises_not_implemented(self):
        """Test exists raises NotImplementedError."""
        backend = CacheBackend()
        with pytest.raises(NotImplementedError):
            await backend.exists("key")

    @pytest.mark.asyncio
    async def test_clear_raises_not_implemented(self):
        """Test clear raises NotImplementedError."""
        backend = CacheBackend()
        with pytest.raises(NotImplementedError):
            await backend.clear()

    @pytest.mark.asyncio
    async def test_mget_base_implementation(self):
        """Test mget base implementation iterates over keys."""

        class TestBackend(CacheBackend):
            async def get(self, key):
                if key == "key1":
                    return "value1"
                if key == "key3":
                    return "value3"
                return None

            async def set(self, key, value, ttl=None):
                return True

            async def delete(self, key):
                return True

            async def exists(self, key):
                return True

            async def clear(self):
                return True

        backend = TestBackend()
        result = await backend.mget(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key3": "value3"}

    @pytest.mark.asyncio
    async def test_mset_base_implementation(self):
        """Test mset base implementation iterates over items."""

        class TestBackend(CacheBackend):
            def __init__(self):
                super().__init__()
                self.data = {}

            async def get(self, key):
                return self.data.get(key)

            async def set(self, key, value, ttl=None):
                self.data[key] = value
                return True

            async def delete(self, key):
                return True

            async def exists(self, key):
                return True

            async def clear(self):
                return True

        backend = TestBackend()
        result = await backend.mset({"key1": "value1", "key2": "value2"})
        assert result is True
        assert backend.data == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_mset_partial_failure(self):
        """Test mset when some sets fail."""

        class TestBackend(CacheBackend):
            async def get(self, key):
                return None

            async def set(self, key, value, ttl=None):
                return key != "key2"  # Fail on key2

            async def delete(self, key):
                return True

            async def exists(self, key):
                return True

            async def clear(self):
                return True

        backend = TestBackend()
        result = await backend.mset({"key1": "value1", "key2": "value2"})
        assert result is False

    @pytest.mark.asyncio
    async def test_close_base_implementation(self):
        """Test close base implementation does nothing."""
        backend = CacheBackend()
        result = await backend.close()
        assert result is None

    def test_get_stats(self):
        """Test get_stats returns stats object."""
        backend = CacheBackend()
        stats = backend.get_stats()
        assert isinstance(stats, CacheStats)
        assert stats is backend.stats


# ============================================================================
# MemoryCache Tests
# ============================================================================


class TestMemoryCache:
    """Test MemoryCache implementation."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test basic set and get."""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self):
        """Test get returns None for missing key."""
        cache = MemoryCache()
        result = await cache.get("nonexistent")
        assert result is None
        assert cache.stats.misses == 1
        assert cache.stats.total_gets == 1

    @pytest.mark.asyncio
    async def test_get_existing_updates_stats(self):
        """Test get updates hit stats."""
        cache = MemoryCache()
        await cache.set("key", "value")
        result = await cache.get("key")
        assert result == "value"
        assert cache.stats.hits == 1
        assert cache.stats.total_gets == 1

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test set with TTL."""
        cache = MemoryCache()
        await cache.set("key", "value", ttl=3600)
        result = await cache.get("key")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_set_updates_stats(self):
        """Test set updates stats."""
        cache = MemoryCache()
        await cache.set("key", "value")
        assert cache.stats.total_sets == 1

    @pytest.mark.asyncio
    async def test_set_default_ttl(self):
        """Test set uses default TTL."""
        cache = MemoryCache(default_ttl=3600)
        await cache.set("key", "value")
        assert "key" in cache._expiry

    @pytest.mark.asyncio
    async def test_get_expired_key(self):
        """Test get returns None for expired key."""
        cache = MemoryCache()
        # Manually set an expired entry
        cache._cache["key"] = "value"
        cache._expiry["key"] = time.time() - 1  # Expired 1 second ago
        result = await cache.get("key")
        assert result is None
        assert cache.stats.misses == 1

    @pytest.mark.asyncio
    async def test_get_expired_key_removed(self):
        """Test expired key is removed from cache."""
        cache = MemoryCache()
        await cache.set("key", "value", ttl=-1)  # Negative TTL for immediate expiration
        result = await cache.get("key")
        assert result is None
        assert "key" not in cache._cache
        assert "key" not in cache._expiry

    @pytest.mark.asyncio
    async def test_delete_existing_key(self):
        """Test delete removes existing key."""
        cache = MemoryCache()
        await cache.set("key", "value")
        result = await cache.delete("key")
        assert result is True
        assert await cache.get("key") is None
        assert cache.stats.total_deletes == 1

    @pytest.mark.asyncio
    async def test_delete_missing_key(self):
        """Test delete returns False for missing key."""
        cache = MemoryCache()
        result = await cache.delete("nonexistent")
        assert result is False
        assert cache.stats.total_deletes == 1

    @pytest.mark.asyncio
    async def test_exists_true(self):
        """Test exists returns True for existing key."""
        cache = MemoryCache()
        await cache.set("key", "value")
        result = await cache.exists("key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        """Test exists returns False for missing key."""
        cache = MemoryCache()
        result = await cache.exists("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_expired(self):
        """Test exists returns False for expired key."""
        cache = MemoryCache()
        await cache.set("key", "value", ttl=-1)  # Negative TTL for immediate expiration
        result = await cache.exists("key")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear removes all data."""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        result = await cache.clear()
        assert result is True
        assert len(cache._cache) == 0
        assert len(cache._expiry) == 0
        assert len(cache._sizes) == 0
        assert cache._current_memory == 0
        assert cache.stats.bytes_stored == 0

    @pytest.mark.asyncio
    async def test_mget(self):
        """Test batch get."""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        result = await cache.mget(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}
        assert cache.stats.hits == 2
        assert cache.stats.misses == 1

    @pytest.mark.asyncio
    async def test_mget_expired(self):
        """Test mget skips expired keys."""
        cache = MemoryCache()
        await cache.set("key1", "value1", ttl=-1)  # Negative TTL for immediate expiration
        await cache.set("key2", "value2")
        result = await cache.mget(["key1", "key2"])
        assert result == {"key2": "value2"}

    @pytest.mark.asyncio
    async def test_mset(self):
        """Test batch set."""
        cache = MemoryCache()
        result = await cache.mset({"key1": "value1", "key2": "value2"})
        assert result is True
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_mget_moves_to_end(self):
        """Test mget updates LRU order."""
        cache = MemoryCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        # Access key1 to make it more recent
        await cache.mget(["key1"])
        # Add key3 to evict key2 (LRU)
        await cache.set("key3", "value3")
        assert await cache.get("key1") is not None
        assert await cache.get("key2") is None  # Evicted

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when max_size reached."""
        cache = MemoryCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Should evict key1
        assert await cache.get("key1") is None
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert cache.stats.evictions >= 1

    @pytest.mark.asyncio
    async def test_lru_access_order(self):
        """Test LRU updates on access."""
        cache = MemoryCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        # Access key1 to make it more recent
        await cache.get("key1")
        # Add key3 to evict key2 (now LRU)
        await cache.set("key3", "value3")
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") is None  # Evicted
        assert await cache.get("key3") == "value3"

    @pytest.mark.asyncio
    async def test_memory_based_eviction(self):
        """Test eviction based on memory limit."""
        cache = MemoryCache(max_size=1000, max_memory_mb=0.001)  # Very small
        await cache.set("key1", "x" * 100)
        await cache.set("key2", "x" * 100)
        # Should evict to stay under memory limit
        assert cache._current_memory <= cache._max_memory_bytes

    @pytest.mark.asyncio
    async def test_value_too_large(self):
        """Test set returns False for value too large."""
        cache = MemoryCache(max_memory_mb=0.001)
        # Value > 50% of max memory
        large_value = "x" * 1000
        result = await cache.set("key", large_value)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_existing_key_adjusts_memory(self):
        """Test updating key adjusts memory accounting."""
        cache = MemoryCache()
        await cache.set("key", "small")
        initial_memory = cache._current_memory
        await cache.set("key", "much larger value here")
        # Memory should be updated
        assert cache._current_memory != initial_memory

    @pytest.mark.asyncio
    async def test_evict_lru_empty_cache(self):
        """Test _evict_lru on empty cache."""
        cache = MemoryCache()
        cache._evict_lru()  # Should not raise
        assert cache.stats.evictions == 0

    @pytest.mark.asyncio
    async def test_evict_expired_entries(self):
        """Test eviction removes expired entries first."""
        cache = MemoryCache(max_size=3)
        await cache.set("expired", "value", ttl=-1)  # Negative TTL for immediate expiration
        await cache.set("valid1", "value1")
        await cache.set("valid2", "value2")
        # Trigger eviction
        await cache.set("new", "value")
        # Expired should be removed
        assert "expired" not in cache._cache

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close does nothing for MemoryCache."""
        cache = MemoryCache()
        result = await cache.close()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_stats_with_memory(self):
        """Test get_stats returns updated bytes_stored."""
        cache = MemoryCache()
        await cache.set("key", "value")
        stats = cache.get_stats()
        assert stats.bytes_stored == cache._current_memory

    @pytest.mark.asyncio
    async def test_set_with_unpicklable_value(self):
        """Test set handles unpicklable values."""
        cache = MemoryCache()

        class Unpicklable:
            def __reduce__(self):
                raise pickle.PicklingError("Cannot pickle")

        obj = Unpicklable()
        # Should fall back to sys.getsizeof
        result = await cache.set("key", obj)
        # Result depends on size check
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self):
        """Test overwriting existing key."""
        cache = MemoryCache()
        await cache.set("key", "old_value")
        await cache.set("key", "new_value")
        result = await cache.get("key")
        assert result == "new_value"


# ============================================================================
# SQLiteCache Tests
# ============================================================================


@pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not available")
class TestSQLiteCache:
    """Test SQLiteCache implementation."""

    @pytest.mark.asyncio
    async def test_set_and_get(self, temp_db_path):
        """Test basic set and get."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self, temp_db_path):
        """Test get returns None for missing key."""
        cache = SQLiteCache(db_path=temp_db_path)
        result = await cache.get("nonexistent")
        assert result is None
        assert cache.stats.misses == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, temp_db_path):
        """Test set with TTL."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key", "value", ttl=3600)
        result = await cache.get("key")
        assert result == "value"
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_expired_key(self, temp_db_path):
        """Test get returns None for expired key."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Use negative TTL for immediate expiration
        await cache.set("key", "value", ttl=-1)
        result = await cache.get("key")
        assert result is None
        assert cache.stats.misses == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_delete_existing(self, temp_db_path):
        """Test delete removes existing key."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key", "value")
        result = await cache.delete("key")
        assert result is True
        assert await cache.get("key") is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_exists(self, temp_db_path):
        """Test exists method."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key", "value")
        assert await cache.exists("key") is True
        assert await cache.exists("nonexistent") is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_clear(self, temp_db_path):
        """Test clear removes all data."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        result = await cache.clear()
        assert result is True
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget(self, temp_db_path):
        """Test batch get."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        result = await cache.mget(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_empty_keys(self, temp_db_path):
        """Test mget with empty keys list."""
        cache = SQLiteCache(db_path=temp_db_path)
        result = await cache.mget([])
        assert result == {}
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset(self, temp_db_path):
        """Test batch set."""
        cache = SQLiteCache(db_path=temp_db_path)
        result = await cache.mset({"key1": "value1", "key2": "value2"})
        assert result is True
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset_empty(self, temp_db_path):
        """Test mset with empty dict."""
        cache = SQLiteCache(db_path=temp_db_path)
        result = await cache.mset({})
        assert result is True
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset_with_ttl(self, temp_db_path):
        """Test batch set with TTL."""
        cache = SQLiteCache(db_path=temp_db_path)
        result = await cache.mset({"key1": "value1", "key2": "value2"}, ttl=3600)
        assert result is True
        await cache.close()

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, temp_db_path):
        """Test cleanup of expired entries."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("key", "value", ttl=-1)
        await cache.cleanup_expired()
        # Expired entry should be removed
        result = await cache.get("key")
        assert result is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_cleanup_expired_no_entries(self, temp_db_path):
        """Test cleanup when no expired entries."""
        cache = SQLiteCache(db_path=temp_db_path)
        result = await cache.cleanup_expired()
        assert result is None  # Method doesn't return anything
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_removes_expired(self, temp_db_path):
        """Test mget removes expired entries."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache.set("expired", "value", ttl=-1)
        await cache.set("valid", "value", ttl=3600)
        result = await cache.mget(["expired", "valid"])
        assert "expired" not in result
        assert result["valid"] == "value"
        await cache.close()

    @pytest.mark.asyncio
    async def test_pickle_error_on_get(self, temp_db_path):
        """Test handling pickle error on get."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Manually insert corrupted data
        db = await cache._get_db()
        await db.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
            ("corrupted", b"not valid pickle", None),
        )
        await db.commit()
        # Should handle error gracefully
        result = await cache.get("corrupted")
        assert result is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_pickle_error_on_mget(self, temp_db_path):
        """Test handling pickle error on mget."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Manually insert corrupted data
        db = await cache._get_db()
        await db.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
            ("corrupted", b"not valid pickle", None),
        )
        await db.commit()
        # Should handle error gracefully
        result = await cache.mget(["corrupted"])
        assert result == {}
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_error_handling(self, temp_db_path):
        """Test set handles database errors."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Mock _get_db to raise exception
        with patch.object(cache, "_get_db", side_effect=Exception("DB Error")):
            result = await cache.set("key", "value")
            assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_delete_error_handling(self, temp_db_path):
        """Test delete handles database errors."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Mock _get_db to raise exception
        with patch.object(cache, "_get_db", side_effect=Exception("DB Error")):
            result = await cache.delete("key")
            assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_clear_error_handling(self, temp_db_path):
        """Test clear handles database errors."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Mock _get_db to raise exception
        with patch.object(cache, "_get_db", side_effect=Exception("DB Error")):
            result = await cache.clear()
            assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_error_handling(self, temp_db_path):
        """Test mget handles database errors."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Mock _get_db to raise exception
        with patch.object(cache, "_get_db", side_effect=Exception("DB Error")):
            result = await cache.mget(["key1", "key2"])
            assert result == {}
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset_error_handling(self, temp_db_path):
        """Test mset handles database errors."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Mock _get_db to raise exception
        with patch.object(cache, "_get_db", side_effect=Exception("DB Error")):
            result = await cache.mset({"key1": "value1"})
            assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self, temp_db_path):
        """Test cleanup_expired handles database errors."""
        cache = SQLiteCache(db_path=temp_db_path)
        # Mock _get_db to raise exception
        with patch.object(cache, "_get_db", side_effect=Exception("DB Error")):
            result = await cache.cleanup_expired()
            assert result is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_maybe_cleanup(self, temp_db_path):
        """Test periodic cleanup is triggered."""
        cache = SQLiteCache(db_path=temp_db_path, cleanup_interval=0)
        await cache.set("key", "value", ttl=-1)
        # Force cleanup by setting last_cleanup to 0
        cache._last_cleanup = 0
        await cache._maybe_cleanup()
        # Should have cleaned up
        await cache.close()

    @pytest.mark.asyncio
    async def test_db_initialization(self, temp_db_path):
        """Test database initialization creates tables."""
        cache = SQLiteCache(db_path=temp_db_path)
        db = await cache._get_db()
        # Check table exists
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache'")
        row = await cursor.fetchone()
        assert row is not None
        await cache.close()

    @pytest.mark.asyncio
    async def test_close(self, temp_db_path):
        """Test close closes database connection."""
        cache = SQLiteCache(db_path=temp_db_path)
        await cache._get_db()  # Ensure connection is created
        await cache.close()
        assert cache._db is None


# ============================================================================
# RedisCache Tests
# ============================================================================


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="redis not available")
class TestRedisCache:
    """Test RedisCache implementation."""

    @pytest.mark.asyncio
    async def test_get(self, mock_redis):
        """Test basic get."""
        mock_redis.get = AsyncMock(return_value=pickle.dumps("value"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.get("key")
        assert result == "value"
        assert cache.stats.hits == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_missing(self, mock_redis):
        """Test get returns None for missing key."""
        mock_redis.get = AsyncMock(return_value=None)
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.get("key")
        assert result is None
        assert cache.stats.misses == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_error(self, mock_redis):
        """Test get handles errors."""
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.get("key")
        assert result is None
        assert cache.stats.misses == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_set(self, mock_redis):
        """Test basic set."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.set("key", "value")
        assert result is True
        mock_redis.set.assert_called_once()
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, mock_redis):
        """Test set with TTL."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.set("key", "value", ttl=3600)
        assert result is True
        mock_redis.set.assert_called_once_with("key", pickle.dumps("value"), ex=3600)
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_error(self, mock_redis):
        """Test set handles errors."""
        mock_redis.set = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.set("key", "value")
        assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_delete(self, mock_redis):
        """Test delete."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.delete("key")
        assert result is True
        mock_redis.delete.assert_called_once_with("key")
        await cache.close()

    @pytest.mark.asyncio
    async def test_delete_error(self, mock_redis):
        """Test delete handles errors."""
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.delete("key")
        assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_exists_true(self, mock_redis):
        """Test exists returns True."""
        mock_redis.exists = AsyncMock(return_value=1)
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.exists("key")
        assert result is True
        await cache.close()

    @pytest.mark.asyncio
    async def test_exists_false(self, mock_redis):
        """Test exists returns False."""
        mock_redis.exists = AsyncMock(return_value=0)
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.exists("key")
        assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_exists_error(self, mock_redis):
        """Test exists handles errors."""
        mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.exists("key")
        assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_clear(self, mock_redis):
        """Test clear."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.clear()
        assert result is True
        mock_redis.flushdb.assert_called_once()
        await cache.close()

    @pytest.mark.asyncio
    async def test_clear_error(self, mock_redis):
        """Test clear handles errors."""
        mock_redis.flushdb = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.clear()
        assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget(self, mock_redis):
        """Test batch get."""
        mock_redis.mget = AsyncMock(return_value=[pickle.dumps("value1"), None, pickle.dumps("value3")])
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mget(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key3": "value3"}
        assert cache.stats.hits == 2
        assert cache.stats.misses == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_empty(self, mock_redis):
        """Test mget with empty keys."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mget([])
        assert result == {}
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_error(self, mock_redis):
        """Test mget handles errors."""
        mock_redis.mget = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mget(["key1", "key2"])
        assert result == {}
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_pickle_error(self, mock_redis):
        """Test mget handles pickle errors."""
        mock_redis.mget = AsyncMock(return_value=[b"invalid pickle"])
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mget(["key1"])
        assert result == {}
        assert cache.stats.misses == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset(self, mock_redis):
        """Test batch set."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mset({"key1": "value1", "key2": "value2"})
        assert result is True
        mock_redis.mset.assert_called_once()
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset_empty(self, mock_redis):
        """Test mget with empty dict."""
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mset({})
        assert result is True
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset_with_ttl(self, mock_redis):
        """Test mset with TTL."""
        mock_pipe = AsyncMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mset({"key1": "value1", "key2": "value2"}, ttl=3600)
        assert result is True
        mock_redis.pipeline.assert_called_once()
        await cache.close()

    @pytest.mark.asyncio
    async def test_mset_error(self, mock_redis):
        """Test mset handles errors."""
        mock_redis.mset = AsyncMock(side_effect=Exception("Redis error"))
        cache = RedisCache()
        cache._pool = mock_redis
        result = await cache.mset({"key1": "value1"})
        assert result is False
        await cache.close()

    @pytest.mark.asyncio
    async def test_close(self, mock_redis):
        """Test close closes connection."""
        cache = RedisCache()
        cache._pool = mock_redis
        await cache.close()
        mock_redis.close.assert_called_once()
        assert cache._pool is None

    @pytest.mark.asyncio
    async def test_get_pool_creates_connection(self):
        """Test _get_pool creates connection on first call."""
        with patch("core.cache.redis") as mock_redis_module:
            mock_pool = AsyncMock()
            mock_redis_module.Redis.return_value = mock_pool
            cache = RedisCache()
            pool = await cache._get_pool()
            assert pool is mock_pool
            mock_redis_module.Redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pool_returns_existing(self, mock_redis):
        """Test _get_pool returns existing connection."""
        cache = RedisCache()
        cache._pool = mock_redis
        pool = await cache._get_pool()
        assert pool is mock_redis


def test_redis_import_error():
    """Test RedisCache raises ImportError when redis not available."""
    with patch("core.cache.REDIS_AVAILABLE", False):
        with pytest.raises(ImportError, match="redis not installed"):
            RedisCache()


# ============================================================================
# MultiTierCache Tests
# ============================================================================


class TestMultiTierCache:
    """Test MultiTierCache implementation."""

    @pytest.mark.asyncio
    async def test_get_from_l1(self, temp_db_path):
        """Test get from L1 cache."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        await cache.set("key", "value")
        result = await cache.get("key")
        assert result == "value"
        assert cache._hit_distribution["L1"] == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_from_l2_promotes_to_l1(self, temp_db_path):
        """Test get from L2 promotes to L1."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        # Set only in L2
        await cache.set("key", "value", tiers="persistent")
        # Clear L1
        await cache.l1.clear()
        # Get should fetch from L2 and promote to L1
        result = await cache.get("key")
        assert result == "value"
        assert cache._hit_distribution["L2"] == 1
        # Verify promoted to L1
        assert await cache.l1.get("key") == "value"
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self, temp_db_path):
        """Test get returns None for missing key."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        result = await cache.get("nonexistent")
        assert result is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_all_tiers(self, temp_db_path):
        """Test set in all tiers."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        result = await cache.set("key", "value", tiers="all")
        assert result is True
        assert await cache.l1.get("key") == "value"
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_memory_tier(self, temp_db_path):
        """Test set in memory tier only."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        result = await cache.set("key", "value", tiers="memory")
        assert result is True
        assert await cache.l1.get("key") == "value"
        await cache.close()

    @pytest.mark.asyncio
    async def test_set_persistent_tier(self, temp_db_path):
        """Test set in persistent tier only."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        result = await cache.set("key", "value", tiers="persistent")
        assert result is True
        # Should not be in L1
        assert await cache.l1.get("key") is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget(self, temp_db_path):
        """Test batch get across tiers."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        result = await cache.mget(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}
        await cache.close()

    @pytest.mark.asyncio
    async def test_mget_promotes_from_l2(self, temp_db_path):
        """Test mget promotes from L2 to L1."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        # Set in L2 only
        await cache.set("key", "value", tiers="persistent")
        # Clear L1
        await cache.l1.clear()
        # mget should promote to L1
        result = await cache.mget(["key"])
        assert result == {"key": "value"}
        assert cache._hit_distribution["L2"] == 1
        await cache.close()

    @pytest.mark.asyncio
    async def test_delete(self, temp_db_path):
        """Test delete from all tiers."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        await cache.set("key", "value", tiers="all")
        result = await cache.delete("key")
        assert result is True
        assert await cache.l1.get("key") is None
        await cache.close()

    @pytest.mark.asyncio
    async def test_delete_without_l2(self, temp_db_path):
        """Test delete when L2 is None."""
        cache = MultiTierCache(memory_size=10)
        cache.l2 = None
        await cache.set("key", "value")
        result = await cache.delete("key")
        assert result is True
        await cache.close()

    @pytest.mark.asyncio
    async def test_close(self, temp_db_path):
        """Test close closes all tiers."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        await cache.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_close_without_l2_l3(self):
        """Test close when L2 and L3 are None."""
        cache = MultiTierCache(memory_size=10)
        cache.l2 = None
        cache.l3 = None
        await cache.close()
        # Should not raise

    def test_get_stats(self, temp_db_path):
        """Test get_stats returns combined stats."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        stats = cache.get_stats()
        assert "hit_distribution" in stats
        assert "L1_memory" in stats
        assert "L2_sqlite" in stats
        assert "L3_redis" in stats
        # Check structure of hit_distribution
        for tier in ["L1", "L2", "L3"]:
            assert tier in stats["hit_distribution"]
            assert "count" in stats["hit_distribution"][tier]
            assert "percentage" in stats["hit_distribution"][tier]

    def test_get_stats_with_hits(self, temp_db_path):
        """Test get_stats with actual hits."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        cache._hit_distribution = {"L1": 80, "L2": 15, "L3": 5}
        stats = cache.get_stats()
        assert stats["hit_distribution"]["L1"]["count"] == 80
        assert stats["hit_distribution"]["L1"]["percentage"] == 80.0
        assert stats["hit_distribution"]["L2"]["percentage"] == 15.0
        assert stats["hit_distribution"]["L3"]["percentage"] == 5.0

    def test_get_stats_no_hits(self, temp_db_path):
        """Test get_stats with no hits."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)
        stats = cache.get_stats()
        for tier in ["L1", "L2", "L3"]:
            assert stats["hit_distribution"][tier]["percentage"] == 0

    @pytest.mark.asyncio
    async def test_redis_unavailable_warning(self, temp_db_path):
        """Test warning when Redis is unavailable."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            with patch("core.cache.RedisCache", side_effect=Exception("Redis down")):
                with patch("core.cache.logger") as mock_logger:
                    cache = MultiTierCache(
                        memory_size=10,
                        sqlite_path=temp_db_path,
                        redis_config={"host": "localhost"},
                    )
                    assert cache.l3 is None
                    mock_logger.warning.assert_called_once()
                    await cache.close()


# ============================================================================
# Decorator and Utility Tests
# ============================================================================


class TestCachedDecorator:
    """Test @cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator_async(self):
        """Test @cached decorator with async function."""
        call_count = [0]

        @cached(backend="memory", ttl=3600)
        async def test_func(x):
            call_count[0] += 1
            return x * 2

        # First call - cache miss
        result1 = await test_func(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call - cache hit
        result2 = await test_func(5)
        assert result2 == 10
        assert call_count[0] == 1  # Should not increment

    @pytest.mark.asyncio
    async def test_cached_decorator_with_condition(self):
        """Test @cached with condition function."""
        call_count = [0]

        @cached(backend="memory", ttl=3600, condition=lambda x: x > 0)
        async def test_func(x):
            call_count[0] += 1
            return x * 2

        # Positive result should be cached
        result1 = await test_func(5)
        assert result1 == 10
        assert call_count[0] == 1

        result2 = await test_func(5)
        assert result2 == 10
        assert call_count[0] == 1  # From cache

        # Zero result should not be cached
        await test_func(0)
        await test_func(0)
        assert call_count[0] == 3  # Called each time

    @pytest.mark.asyncio
    async def test_cached_decorator_with_custom_key_func(self):
        """Test @cached with custom key function."""
        call_count = [0]

        def custom_key(x, y):
            return f"custom:{x}:{y}"

        @cached(backend="memory", ttl=3600, key_func=custom_key)
        async def test_func(x, y):
            call_count[0] += 1
            return x + y

        result1 = await test_func(1, 2)
        assert result1 == 3
        assert call_count[0] == 1

        result2 = await test_func(1, 2)
        assert result2 == 3
        assert call_count[0] == 1  # From cache

    @pytest.mark.asyncio
    async def test_cached_decorator_cache_hit_logging(self):
        """Test cache hit is logged."""
        with patch("core.cache.logger") as mock_logger:
            call_count = [0]

            @cached(backend="memory", ttl=3600)
            async def test_func(x):
                call_count[0] += 1
                return x * 2

            await test_func(5)
            await test_func(5)  # Cache hit

            mock_logger.debug.assert_called()


class TestGenerateCacheKey:
    """Test generate_cache_key function."""

    def test_generate_cache_key_basic(self):
        """Test basic key generation."""
        key = generate_cache_key("arg1", "arg2", kwarg1="value1")
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length

    def test_generate_cache_key_deterministic(self):
        """Test key generation is deterministic."""
        key1 = generate_cache_key("arg1", kwarg1="value1")
        key2 = generate_cache_key("arg1", kwarg1="value1")
        assert key1 == key2

    def test_generate_cache_key_different_args(self):
        """Test different args produce different keys."""
        key1 = generate_cache_key("arg1")
        key2 = generate_cache_key("arg2")
        assert key1 != key2

    def test_generate_cache_key_with_complex_types(self):
        """Test key generation with complex types."""
        key = generate_cache_key([1, 2, 3], {"key": "value"})
        assert isinstance(key, str)


class TestGetCacheBackend:
    """Test _get_cache_backend function."""

    def test_get_memory_backend(self):
        """Test getting memory backend."""
        backend = _get_cache_backend("memory")
        assert isinstance(backend, MemoryCache)

    def test_get_memory_backend_cached(self):
        """Test memory backend is cached."""
        backend1 = _get_cache_backend("memory")
        backend2 = _get_cache_backend("memory")
        assert backend1 is backend2

    @pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not available")
    def test_get_sqlite_backend(self):
        """Test getting sqlite backend."""
        # Reset global cache to get fresh instance
        import core.cache as cache_module

        cache_module._sqlite_cache = None
        backend = _get_cache_backend("sqlite")
        assert isinstance(backend, SQLiteCache)

    def test_get_backend_instance(self):
        """Test passing backend instance returns same."""
        custom_backend = MemoryCache()
        result = _get_cache_backend(custom_backend)
        assert result is custom_backend

    def test_get_unknown_backend(self):
        """Test unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown cache backend"):
            _get_cache_backend("unknown")


@pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not available")
class TestCveCacheUtilities:
    """Test CVE cache utilities."""

    @pytest.mark.asyncio
    async def test_cache_cve_and_get_cached_cve(self, temp_db_path):
        """Test caching and retrieving CVE data."""
        # Reset global instance
        import core.cache as cache_module

        cache_module._sqlite_cache = None

        cve_data = {"id": "CVE-2021-1234", "severity": "high"}
        await cache_cve("CVE-2021-1234", cve_data, ttl=3600)
        result = await get_cached_cve("CVE-2021-1234")
        assert result == cve_data

    @pytest.mark.asyncio
    async def test_get_cached_cve_missing(self, temp_db_path):
        """Test getting non-existent CVE."""
        # Reset global instance
        import core.cache as cache_module

        cache_module._sqlite_cache = None

        result = await get_cached_cve("CVE-NOT-EXIST")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_cve_uppercase(self, temp_db_path):
        """Test CVE ID is normalized to uppercase."""
        # Reset global instance
        import core.cache as cache_module

        cache_module._sqlite_cache = None

        cve_data = {"id": "CVE-2021-1234"}
        await cache_cve("cve-2021-1234", cve_data)  # lowercase
        result = await get_cached_cve("CVE-2021-1234")  # uppercase
        assert result == cve_data


# ============================================================================
# Cache Compatibility Alias
# ============================================================================


class TestCacheAlias:
    """Test Cache alias for MultiTierCache."""

    def test_cache_is_multi_tier(self):
        """Test Cache is alias for MultiTierCache."""
        assert Cache is MultiTierCache


# ============================================================================
# Integration Tests
# ============================================================================


class TestCacheIntegration:
    """Integration tests for cache system."""

    @pytest.mark.asyncio
    async def test_memory_cache_full_workflow(self):
        """Test complete MemoryCache workflow."""
        cache = MemoryCache(max_size=5, default_ttl=1)

        # Set multiple values
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Batch get
        results = await cache.mget(["key1", "key2", "missing"])
        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert "missing" not in results

        # Batch set
        await cache.mset({"key4": "value4", "key5": "value5"})

        # Check exists
        assert await cache.exists("key1") is True
        assert await cache.exists("missing") is False

        # Delete
        await cache.delete("key1")
        assert await cache.get("key1") is None

        # Clear
        await cache.clear()
        assert len(cache._cache) == 0

        # Close
        await cache.close()

    @pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not available")
    @pytest.mark.asyncio
    async def test_sqlite_cache_full_workflow(self, temp_db_path):
        """Test complete SQLiteCache workflow."""
        cache = SQLiteCache(db_path=temp_db_path)

        # Set and get
        await cache.set("key1", "value1", ttl=3600)
        result = await cache.get("key1")
        assert result == "value1"

        # Batch operations
        await cache.mset({"key2": "value2", "key3": "value3"})
        results = await cache.mget(["key2", "key3"])
        assert results["key2"] == "value2"
        assert results["key3"] == "value3"

        # Expired entry
        await cache.set("expired", "value", ttl=-1)
        assert await cache.get("expired") is None

        # Cleanup
        await cache.cleanup_expired()

        await cache.close()

    @pytest.mark.asyncio
    async def test_multi_tier_cache_workflow(self, temp_db_path):
        """Test complete MultiTierCache workflow."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)

        # Set in all tiers
        await cache.set("key1", "value1", tiers="all")

        # Get should populate from L1
        result = await cache.get("key1")
        assert result == "value1"

        # Batch get
        await cache.set("key2", "value2")
        results = await cache.mget(["key1", "key2"])
        assert "key1" in results
        assert "key2" in results

        # Delete
        await cache.delete("key1")
        assert await cache.get("key1") is None

        # Stats
        stats = cache.get_stats()
        assert "hit_distribution" in stats
        assert "L1_memory" in stats

        await cache.close()

    @pytest.mark.asyncio
    async def test_multi_tier_promotion(self, temp_db_path):
        """Test data promotion across tiers."""
        cache = MultiTierCache(memory_size=10, sqlite_path=temp_db_path)

        # Set in L2 only
        await cache.set("key", "value", tiers="persistent")

        # Clear L1 to simulate cache miss
        await cache.l1.clear()

        # Get should fetch from L2 and promote to L1
        result = await cache.get("key")
        assert result == "value"
        assert await cache.l1.get("key") == "value"

        await cache.close()


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_memory_cache_empty_batch_operations(self):
        """Test batch operations with empty input."""
        cache = MemoryCache()
        result = await cache.mget([])
        assert result == {}
        result = await cache.mset({})
        assert result is True

    @pytest.mark.asyncio
    async def test_memory_cache_complex_values(self):
        """Test caching complex values."""
        cache = MemoryCache()
        complex_value = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "tuple": (4, 5, 6),
            "none": None,
            "bool": True,
        }
        await cache.set("complex", complex_value)
        result = await cache.get("complex")
        assert result == complex_value

    @pytest.mark.asyncio
    async def test_memory_cache_unicode_keys(self):
        """Test caching with unicode keys."""
        cache = MemoryCache()
        await cache.set("ключ", "value")
        result = await cache.get("ключ")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_memory_cache_empty_values(self):
        """Test caching empty values."""
        cache = MemoryCache()
        await cache.set("empty_str", "")
        await cache.set("empty_list", [])
        await cache.set("empty_dict", {})
        await cache.set("zero", 0)
        await cache.set("false", False)

        assert await cache.get("empty_str") == ""
        assert await cache.get("empty_list") == []
        assert await cache.get("empty_dict") == {}
        assert await cache.get("zero") == 0
        assert await cache.get("false") is False

    @pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not available")
    @pytest.mark.asyncio
    async def test_sqlite_cache_complex_values(self, temp_db_path):
        """Test SQLite caching complex values."""
        cache = SQLiteCache(db_path=temp_db_path)
        complex_value = {"nested": [1, 2, {"deep": "value"}]}
        await cache.set("complex", complex_value)
        result = await cache.get("complex")
        assert result == complex_value
        await cache.close()

    @pytest.mark.asyncio
    async def test_memory_cache_concurrent_access(self):
        """Test concurrent cache access."""
        cache = MemoryCache()

        async def writer(n):
            for i in range(n):
                await cache.set(f"key_{i}", f"value_{i}")

        async def reader(n):
            for i in range(n):
                await cache.get(f"key_{i}")

        # Run concurrent operations
        await asyncio.gather(writer(50), reader(50))

        # Verify some data
        assert await cache.get("key_0") == "value_0"


# ============================================================================
# Module Import Tests
# ============================================================================


class TestModuleImports:
    """Test module-level imports and availability flags."""

    def test_redis_available_flag(self):
        """Test REDIS_AVAILABLE flag is boolean."""
        assert isinstance(REDIS_AVAILABLE, bool)

    def test_sqlite_available_flag(self):
        """Test SQLITE_AVAILABLE flag is boolean."""
        assert isinstance(SQLITE_AVAILABLE, bool)

    def test_all_exports(self):
        """Test __all__ exports."""
        from core import cache as cache_module

        assert hasattr(cache_module, "__all__")
        exports = cache_module.__all__
        assert "CacheBackend" in exports
        assert "MemoryCache" in exports
        assert "SQLiteCache" in exports
        assert "RedisCache" in exports
        assert "MultiTierCache" in exports
        assert "CacheStats" in exports
        assert "cached" in exports
        assert "generate_cache_key" in exports
        assert "get_cached_cve" in exports
        assert "cache_cve" in exports
        assert "Cache" in exports
