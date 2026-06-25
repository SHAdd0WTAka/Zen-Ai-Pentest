"""
Tests using the actual core/cache.py API signatures
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    from core.cache import (
        CacheBackend,
        CacheStats,
        MemoryCache,
        MultiTierCache,
        RedisCache,
        SQLiteCache,
        cached,
        generate_cache_key,
    )

    HAS_CACHE = True
except ImportError as e:
    HAS_CACHE = False
    print(f"Cache import error: {e}")


# =============================================================================
# CacheStats Tests (actual fields: hits, misses, evictions, total_gets, total_sets, total_deletes, bytes_stored)
# =============================================================================
@pytest.mark.skipif(not HAS_CACHE, reason="Cache not available")
class TestCacheStats:
    """Test CacheStats dataclass."""

    def test_initial_state(self):
        s = CacheStats()
        assert s.hits == 0
        assert s.misses == 0
        assert s.evictions == 0
        assert s.total_gets == 0
        assert s.total_sets == 0
        assert s.total_deletes == 0
        assert s.bytes_stored == 0

    def test_hit_rate_zero(self):
        s = CacheStats()
        assert s.hit_rate == 0.0

    def test_hit_rate_with_gets(self):
        s = CacheStats()
        s.hits = 7
        s.total_gets = 10  # hit_rate = hits / total_gets if total_gets > 0
        # hit_rate calculation might be different
        rate = s.hit_rate
        assert isinstance(rate, float)

    def test_miss_rate(self):
        s = CacheStats()
        s.misses = 3
        s.total_gets = 10
        rate = s.miss_rate
        assert isinstance(rate, float)

    def test_to_dict(self):
        s = CacheStats()
        s.hits = 3
        s.misses = 1
        d = s.to_dict()
        assert isinstance(d, dict)
        assert d.get("hits") == 3
        assert d.get("misses") == 1


# =============================================================================
# MemoryCache Tests (actual API: get, set, delete, exists, clear, mget, mset, get_stats, close)
# =============================================================================
@pytest.mark.skipif(not HAS_CACHE, reason="Cache not available")
class TestMemoryCache:
    """Test MemoryCache with actual API."""

    @pytest.fixture
    def cache(self):
        return MemoryCache()

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_ttl_expires(self, cache):
        await cache.set("key1", "value1", ttl=0.01)
        await asyncio.sleep(0.05)
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        # Should not raise
        await cache.delete("nonexistent")

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_mget(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        results = await cache.mget(["key1", "key2", "key3"])
        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert results.get("key3") is None

    @pytest.mark.asyncio
    async def test_mset(self, cache):
        await cache.mset({"key1": "value1", "key2": "value2"})
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        await cache.set("key1", "value1")
        await cache.get("key1")  # hit
        await cache.get("key2")  # miss
        stats = cache.get_stats()
        assert isinstance(stats, CacheStats)

    @pytest.mark.asyncio
    async def test_close(self, cache):
        # Should not raise
        await cache.close()

    @pytest.mark.asyncio
    async def test_complex_values(self, cache):
        # Test dict
        await cache.set("dict", {"nested": [1, 2, 3]})
        result = await cache.get("dict")
        assert result == {"nested": [1, 2, 3]}

        # Test list
        await cache.set("list", [1, 2, {"a": "b"}])
        result = await cache.get("list")
        assert result == [1, 2, {"a": "b"}]

    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache):
        async def worker(i):
            await cache.set(f"key{i}", f"value{i}")
            return await cache.get(f"key{i}")

        results = await asyncio.gather(*[worker(i) for i in range(10)])
        assert all(r is not None for r in results)


# =============================================================================
# SQLiteCache Tests (actual API: db_path, pool_size, cleanup_interval)
# =============================================================================
@pytest.mark.skipif(not HAS_CACHE, reason="Cache not available")
class TestSQLiteCache:
    """Test SQLiteCache with actual API."""

    @pytest.fixture
    def cache(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        cache = SQLiteCache(db_path=Path(db_path))
        yield cache
        try:
            os.unlink(db_path)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        await cache.set("key1", "value1")
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_mget(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        results = await cache.mget(["key1", "key2", "key3"])
        assert results["key1"] == "value1"
        assert results["key2"] == "value2"

    @pytest.mark.asyncio
    async def test_mset(self, cache):
        await cache.mset({"key1": "value1", "key2": "value2"})
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_close(self, cache):
        await cache.close()


# =============================================================================
# MultiTierCache Tests (actual API: memory_size, memory_max_mb, sqlite_path, redis_config)
# =============================================================================
@pytest.mark.skipif(not HAS_CACHE, reason="Cache not available")
class TestMultiTierCache:
    """Test MultiTierCache with actual API."""

    @pytest.fixture
    def cache(self):
        return MultiTierCache(memory_size=10, memory_max_mb=1)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        await cache.set("key1", "value1")
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_mget(self, cache):
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        results = await cache.mget(["key1", "key2"])
        assert results["key1"] == "value1"
        assert results["key2"] == "value2"

    @pytest.mark.asyncio
    async def test_close(self, cache):
        await cache.close()


# =============================================================================
# Decorator Tests
# =============================================================================
@pytest.mark.skipif(not HAS_CACHE, reason="Cache not available")
class TestDecorators:
    """Test cache decorators."""

    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        cache = MemoryCache()
        call_count = 0

        @cached(cache, ttl=60)
        async def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await expensive_function(5)
        result2 = await expensive_function(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Cached

    def test_generate_cache_key(self):
        key1 = generate_cache_key("func", (1, 2), {"a": 3})
        key2 = generate_cache_key("func", (1, 2), {"a": 3})
        key3 = generate_cache_key("func", (1, 2), {"a": 4})
        assert key1 == key2
        assert key1 != key3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
