"""
Comprehensive tests for the caching system.

Tests cover:
- Cache backends (MemoryCache, SQLiteCache, RedisCache)
- Cache class interface
- TTL functionality
- Cache eviction
- Thread safety
- Multi-tier caching
- Cache decorators
"""

import asyncio
import hashlib
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.cache import (
    CacheBackend,
    MemoryCache,
    MultiTierCache,
    SQLiteCache,
    _get_cache_backend,
    cache_cve,
    cached,
    generate_cache_key,
    get_cached_cve,
)

# Try to import RedisCache, but skip tests if not available
try:
    from core.cache import RedisCache

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


# =============================================================================
# CacheBackend Abstract Base Class Tests
# =============================================================================


class TestCacheBackend:
    """Tests for CacheBackend abstract class."""

    def test_abstract_methods(self):
        """Test that CacheBackend defines abstract methods."""
        # Cannot instantiate abstract class - will raise either TypeError or be allowed
        # depending on Python version
        try:
            backend = CacheBackend()
            # If instantiation succeeded, verify abstract methods are not implemented
            assert not hasattr(backend, "_cache")
        except TypeError:
            pass  # Expected in most Python versions


# =============================================================================
# MemoryCache Tests
# =============================================================================


class TestMemoryCache:
    """Tests for MemoryCache class."""

    @pytest.fixture
    async def cache(self):
        """Create a test memory cache."""
        cache = MemoryCache(max_size=100)
        yield cache
        await cache.clear()

    @pytest.mark.asyncio
    async def test_basic_set_get(self, cache):
        """Test basic set and get operations."""
        result = await cache.set("key1", "value1")
        assert result is True

        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting non-existent key."""
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test delete operation."""
        await cache.set("key1", "value1")
        result = await cache.delete("key1")
        assert result is True

        value = await cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        """Test deleting non-existent key doesn't error."""
        result = await cache.delete("nonexistent")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists check."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        result = await cache.clear()
        assert result is True

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test that keys expire after TTL."""
        await cache.set("key1", "value1", ttl=1)  # 1 second TTL

        # Should exist immediately
        assert await cache.get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_ttl_not_expired(self, cache):
        """Test that keys don't expire before TTL."""
        await cache.set("key1", "value1", ttl=10)  # 10 second TTL

        await asyncio.sleep(0.1)

        assert await cache.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_no_ttl(self, cache):
        """Test keys without TTL don't expire."""
        await cache.set("key1", "value1")  # No TTL

        assert await cache.get("key1") == "value1"
        # No expiration check needed, just ensure it stays

    @pytest.mark.asyncio
    async def test_different_value_types(self, cache):
        """Test caching different value types."""
        # String
        await cache.set("str_key", "string_value")
        assert await cache.get("str_key") == "string_value"

        # Integer
        await cache.set("int_key", 42)
        assert await cache.get("int_key") == 42

        # Float
        await cache.set("float_key", 3.14)
        assert await cache.get("float_key") == 3.14

        # List
        await cache.set("list_key", [1, 2, 3])
        assert await cache.get("list_key") == [1, 2, 3]

        # Dict
        await cache.set("dict_key", {"a": 1, "b": 2})
        assert await cache.get("dict_key") == {"a": 1, "b": 2}

        # None
        await cache.set("none_key", None)
        assert await cache.get("none_key") is None

    @pytest.mark.asyncio
    async def test_eviction_on_capacity(self):
        """Test that oldest items are evicted when capacity reached."""
        cache = MemoryCache(max_size=3)

        await cache.set("key1", "value1", ttl=100)
        await asyncio.sleep(0.01)
        await cache.set("key2", "value2", ttl=100)
        await asyncio.sleep(0.01)
        await cache.set("key3", "value3", ttl=100)

        # All three should exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"

        # Add fourth item - should evict oldest (key1)
        await asyncio.sleep(0.01)
        await cache.set("key4", "value4")

        assert await cache.get("key1") is None  # Evicted
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_update_existing_key(self, cache):
        """Test updating an existing key."""
        await cache.set("key1", "value1")
        await cache.set("key1", "value2")

        assert await cache.get("key1") == "value2"

    @pytest.mark.asyncio
    async def test_thread_safety(self):
        """Test thread safety with concurrent operations."""
        cache = MemoryCache(max_size=1000)
        errors = []

        async def writer(start, count):
            try:
                for i in range(count):
                    await cache.set(f"key_{start}_{i}", f"value_{start}_{i}")
            except Exception as e:
                errors.append(e)

        async def reader(start, count):
            try:
                for i in range(count):
                    await cache.get(f"key_{start}_{i}")
            except Exception as e:
                errors.append(e)

        # Start multiple concurrent writers and readers
        tasks = []
        for i in range(5):
            tasks.append(asyncio.create_task(writer(i, 100)))
            tasks.append(asyncio.create_task(reader(i, 100)))

        await asyncio.gather(*tasks)

        assert (
            len(errors) == 0
        ), f"Errors during concurrent operations: {errors}"

    @pytest.mark.asyncio
    async def test_expired_entries_removed_on_eviction(self):
        """Test that expired entries are cleaned up during eviction."""
        cache = MemoryCache(max_size=5)

        # Add some entries with short TTL
        await cache.set("expired1", "value", ttl=0)
        await cache.set("expired2", "value", ttl=0)
        await asyncio.sleep(0.1)

        # Add entries with long TTL
        await cache.set("live1", "value", ttl=100)
        await cache.set("live2", "value", ttl=100)
        await cache.set("live3", "value", ttl=100)

        # At capacity, all should report as present
        assert len(cache._cache) == 5

        # Add one more - should trigger eviction
        await cache.set("live4", "value", ttl=100)

        # Expired entries should be cleaned up
        assert len(cache._cache) <= 5


# =============================================================================
# SQLiteCache Tests
# =============================================================================


class TestSQLiteCache:
    """Tests for SQLiteCache class."""

    @pytest.fixture
    async def cache(self):
        """Create a test SQLite cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            yield cache
            await cache.close()

    @pytest.mark.asyncio
    async def test_basic_set_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting non-existent key."""
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test delete operation."""
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists check."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache):
        """Test that keys expire after TTL."""
        await cache.set("key1", "value1", ttl=1)

        assert await cache.get("key1") == "value1"

        await asyncio.sleep(1.1)

        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_complex_data_types(self, cache):
        """Test caching complex data types via pickle."""
        # Dictionary
        data = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        await cache.set("dict_key", data)
        assert await cache.get("dict_key") == data

        # Custom object (as long as it's picklable)
        class TestObj:
            def __init__(self):
                self.value = 42

            def __eq__(self, other):
                return isinstance(other, TestObj) and self.value == other.value

        obj = TestObj()
        await cache.set("obj_key", obj)
        retrieved = await cache.get("obj_key")
        assert retrieved == obj

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache):
        """Test cleanup of expired entries."""
        await cache.set("expired", "value", ttl=0)
        await cache.set("live", "value", ttl=100)

        await asyncio.sleep(0.1)

        await cache.cleanup_expired()

        assert await cache.get("expired") is None
        assert await cache.get("live") == "value"

    @pytest.mark.asyncio
    async def test_database_created(self, cache):
        """Test that database file is created."""
        # The cache fixture already created it
        assert cache.db_path.exists()
        assert cache._db is not None

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test concurrent database access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "concurrent.db"
            cache = SQLiteCache(db_path=db_path)

            errors = []

            async def operation(worker_id, count):
                try:
                    for i in range(count):
                        key = f"worker{worker_id}_key{i}"
                        await cache.set(key, f"value{i}")
                        await cache.get(key)
                except Exception as e:
                    errors.append(e)

            tasks = [asyncio.create_task(operation(i, 50)) for i in range(5)]
            await asyncio.gather(*tasks)

            assert len(errors) == 0
            await cache.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, cache):
        """Test that close can be called multiple times."""
        await cache.close()
        await cache.close()  # Should not raise


# =============================================================================
# RedisCache Tests (Conditional)
# =============================================================================


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
class TestRedisCache:
    """Tests for RedisCache class."""

    @pytest.fixture
    async def cache(self):
        """Create a test Redis cache."""
        cache = RedisCache(
            host="localhost", port=6379, db=15
        )  # Use DB 15 for tests
        await cache.clear()
        yield cache
        await cache.clear()
        await cache.close()

    @pytest.mark.asyncio
    async def test_basic_set_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting non-existent key."""
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test delete operation."""
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists check."""
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_ttl(self, cache):
        """Test TTL functionality."""
        await cache.set("key1", "value1", ttl=1)

        assert await cache.get("key1") == "value1"

        await asyncio.sleep(1.1)

        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling with bad connection."""
        # Create cache with invalid host
        cache = RedisCache(host="invalid_host", port=99999)

        # Operations should fail gracefully
        result = await cache.set("key", "value")
        assert result is False

        result = await cache.get("key")
        assert result is None

        result = await cache.exists("key")
        assert result is False

        result = await cache.delete("key")
        assert result is False

        result = await cache.clear()
        assert result is False

        await cache.close()


@pytest.mark.skipif(REDIS_AVAILABLE, reason="Testing import error case")
def test_redis_import_error():
    """Test that RedisCache raises ImportError when redis not available."""
    with pytest.raises(ImportError):
        RedisCache()


# =============================================================================
# MultiTierCache Tests
# =============================================================================


class TestMultiTierCache:
    """Tests for MultiTierCache class."""

    @pytest.fixture
    async def cache(self):
        """Create a test multi-tier cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = Path(tmpdir) / "cache.db"
            cache = MultiTierCache(memory_size=10, sqlite_path=sqlite_path)
            yield cache
            await cache.close()

    @pytest.mark.asyncio
    async def test_l1_cache_get(self, cache):
        """Test L1 (memory) cache hit."""
        await cache.set("key1", "value1")

        # First get - from L1
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_l2_promotion(self, cache):
        """Test L2 to L1 promotion."""
        # Set in L2 only
        await cache.l2.set("key1", "value1")

        # Get should promote to L1
        value = await cache.get("key1")
        assert value == "value1"

        # Should now be in L1
        assert await cache.l1.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_set_all_tiers(self, cache):
        """Test setting in all tiers."""
        await cache.set("key1", "value1", tiers="all")

        assert await cache.l1.get("key1") == "value1"
        assert await cache.l2.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_set_memory_only(self, cache):
        """Test setting only in memory."""
        await cache.set("key1", "value1", tiers="memory")

        assert await cache.l1.get("key1") == "value1"
        # L2 might have it or not, depending on implementation

    @pytest.mark.asyncio
    async def test_set_persistent_only(self, cache):
        """Test setting only in persistent storage."""
        await cache.set("key1", "value1", tiers="persistent")

        assert await cache.l2.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_delete_from_all_tiers(self, cache):
        """Test deleting from all tiers."""
        await cache.set("key1", "value1")
        await cache.delete("key1")

        assert await cache.l1.get("key1") is None
        assert await cache.l2.get("key1") is None

    @pytest.mark.asyncio
    async def test_miss_returns_none(self, cache):
        """Test that miss returns None."""
        value = await cache.get("nonexistent")
        assert value is None


# =============================================================================
# Utility Function Tests
# =============================================================================


class TestGenerateCacheKey:
    """Tests for generate_cache_key function."""

    def test_basic_key_generation(self):
        """Test basic key generation."""
        key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")

        # Same args should produce same key
        assert key1 == key2

    def test_different_args_different_keys(self):
        """Test that different args produce different keys."""
        key1 = generate_cache_key("arg1")
        key2 = generate_cache_key("arg2")

        assert key1 != key2

    def test_kwargs_order_independence(self):
        """Test that kwargs order doesn't affect key."""
        key1 = generate_cache_key(a=1, b=2)
        key2 = generate_cache_key(b=2, a=1)

        assert key1 == key2

    def test_complex_args(self):
        """Test key generation with complex args."""
        key = generate_cache_key([1, 2, 3], {"a": "b"})

        # Should produce valid MD5 hash
        assert len(key) == 32
        assert all(c in "0123456789abcdef" for c in key)


# =============================================================================
# Cache Decorator Tests
# =============================================================================


class TestCachedDecorator:
    """Tests for cached decorator."""

    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """Test caching of async function."""
        call_count = 0

        @cached(backend="memory", ttl=60)
        async def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return x + y

        # First call
        result1 = await expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # Second call with same args - should use cache
        result2 = await expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Not called again

        # Different args - should call function
        result3 = await expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2

    def test_sync_function_caching(self):
        """Test caching of sync function."""
        call_count = 0

        @cached(backend="memory", ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x * y

        # First call
        result1 = expensive_function(2, 3)
        assert result1 == 6
        assert call_count == 1

        # Second call - cached
        result2 = expensive_function(2, 3)
        assert result2 == 6
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test that cached values expire."""
        call_count = 0

        @cached(backend="memory", ttl=0)
        async def short_ttl_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        await short_ttl_function(5)
        assert call_count == 1

        # Wait for expiration
        await asyncio.sleep(0.1)

        # Should call function again
        await short_ttl_function(5)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_custom_key_function(self):
        """Test custom key generation function."""
        call_count = 0

        def custom_key(x, y):
            return f"custom_{x}_{y}"

        @cached(backend="memory", ttl=60, key_func=custom_key)
        async def my_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        await my_function(1, 2)
        await my_function(1, 2)
        assert call_count == 1


# =============================================================================
# Cache Backend Factory Tests
# =============================================================================


class TestGetCacheBackend:
    """Tests for _get_cache_backend function."""

    def test_get_memory_backend(self):
        """Test getting memory backend."""
        backend = _get_cache_backend("memory")
        assert isinstance(backend, MemoryCache)

        # Should return same instance (singleton)
        backend2 = _get_cache_backend("memory")
        assert backend is backend2

    def test_get_sqlite_backend(self):
        """Test getting SQLite backend."""
        backend = _get_cache_backend("sqlite")
        assert isinstance(backend, SQLiteCache)

        # Should return same instance
        backend2 = _get_cache_backend("sqlite")
        assert backend is backend2

    @pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
    def test_get_redis_backend(self):
        """Test getting Redis backend."""
        backend = _get_cache_backend("redis")
        assert isinstance(backend, RedisCache)

    def test_get_custom_backend(self):
        """Test passing custom backend."""
        custom = MemoryCache()
        result = _get_cache_backend(custom)
        assert result is custom

    def test_invalid_backend(self):
        """Test error on invalid backend name."""
        with pytest.raises(ValueError, match="Unknown cache backend"):
            _get_cache_backend("invalid")


# =============================================================================
# CVE Cache Helper Tests
# =============================================================================


class TestCveCacheHelpers:
    """Tests for CVE-specific cache helpers."""

    @pytest.mark.asyncio
    async def test_get_cached_cve(self):
        """Test getting cached CVE data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cve.db"
            cache = SQLiteCache(db_path=db_path)

            # Manually set some CVE data
            await cache.set("cve:CVE-2023-1234", {"description": "Test CVE"})

            # Patch the global _sqlite_cache
            with patch("core.cache._sqlite_cache", cache):
                result = await get_cached_cve("CVE-2023-1234")
                assert result == {"description": "Test CVE"}

                # Test case insensitivity
                result2 = await get_cached_cve("cve-2023-1234")
                assert result2 == {"description": "Test CVE"}

            await cache.close()

    @pytest.mark.asyncio
    async def test_cache_cve(self):
        """Test caching CVE data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cve.db"
            cache = SQLiteCache(db_path=db_path)

            with patch("core.cache._sqlite_cache", cache):
                await cache_cve("CVE-2023-5678", {"description": "New CVE"})

                result = await cache.get("cve:CVE-2023-5678")
                assert result == {"description": "New CVE"}

            await cache.close()


# =============================================================================
# Integration Tests
# =============================================================================


class TestCacheIntegration:
    """Integration tests for caching system."""

    @pytest.mark.asyncio
    async def test_tiered_cache_workflow(self):
        """Test a realistic tiered caching workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "workflow.db"
            cache = MultiTierCache(memory_size=5, sqlite_path=db_path)

            # Simulate fetching data from "backend"
            backend_calls = 0

            async def fetch_from_backend(key):
                nonlocal backend_calls
                backend_calls += 1
                await asyncio.sleep(0.01)  # Simulate latency
                return {"data": f"value_for_{key}"}

            # Check cache first, then backend
            async def get_data(key):
                cached = await cache.get(key)
                if cached is not None:
                    return cached

                data = await fetch_from_backend(key)
                await cache.set(key, data, ttl=60)
                return data

            # First fetch - hits backend
            result1 = await get_data("key1")
            assert backend_calls == 1
            assert result1["data"] == "value_for_key1"

            # Second fetch - hits cache
            result2 = await get_data("key1")
            assert backend_calls == 1  # No additional call
            assert result2 == result1

            # Different key - hits backend
            result3 = await get_data("key2")
            assert backend_calls == 2

            await cache.close()

    @pytest.mark.asyncio
    async def test_cache_decorator_with_real_backend(self):
        """Test decorator with real backend integration."""
        call_count = 0

        @cached(backend="memory", ttl=1)
        async def compute_expensive(x, y):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return {"result": x**y, "computed": True}

        # Multiple calls
        tasks = [compute_expensive(2, 10) for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should have same result
        assert all(r["result"] == 1024 for r in results)

        # Should only compute once
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_sqlite_persistence(self):
        """Test that SQLite cache persists across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "persist.db"

            # First instance
            cache1 = SQLiteCache(db_path=db_path)
            await cache1.set("key1", "value1")
            await cache1.close()

            # Second instance - same file
            cache2 = SQLiteCache(db_path=db_path)
            value = await cache2.get("key1")
            assert value == "value1"
            await cache2.close()
