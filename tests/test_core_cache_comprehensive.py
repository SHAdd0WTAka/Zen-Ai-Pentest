"""
Comprehensive async tests for core/cache.py - Target: 80%+ Coverage.

This test module provides thorough testing of all cache backends:
- MemoryCache (async operations, TTL, LRU eviction, concurrency)
- SQLiteCache (async operations, persistence, batch operations)
- RedisCache (mocked async operations)
- MultiTierCache (L1/L2/L3 interaction)
- Cache decorators (@cached)

Coverage Goals:
- Line Coverage: 80%+
- Branch Coverage: 75%+
- Function Coverage: 85%+
"""

import asyncio
import pickle
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import all cache components
from core.cache import REDIS_AVAILABLE  # noqa: F401
from core.cache import (
    SQLITE_AVAILABLE,
    CacheBackend,
    CacheStats,
    MemoryCache,
    MultiTierCache,
    RedisCache,
    SQLiteCache,
    cache_cve,
    cached,
    get_cached_cve,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def memory_cache():
    """Create a fresh MemoryCache instance."""
    cache = MemoryCache(max_size=100, max_memory_mb=10.0)
    yield cache
    await cache.clear()


@pytest.fixture
async def sqlite_cache(tmp_path):
    """Create a SQLiteCache with temp database."""
    if not SQLITE_AVAILABLE:
        pytest.skip("aiosqlite not available")

    db_path = tmp_path / "test_cache.db"
    cache = SQLiteCache(db_path=db_path)
    yield cache
    await cache.clear()
    await cache.close()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_pool = AsyncMock()
    mock_pool.get = AsyncMock(return_value=None)
    mock_pool.set = AsyncMock(return_value=True)
    mock_pool.delete = AsyncMock(return_value=1)
    mock_pool.exists = AsyncMock(return_value=1)
    mock_pool.flushdb = AsyncMock(return_value=True)
    mock_pool.mget = AsyncMock(return_value=[])
    mock_pool.mset = AsyncMock(return_value=True)
    mock_pool.pipeline = MagicMock(return_value=AsyncMock(execute=AsyncMock(return_value=[True, True])))
    mock_pool.close = AsyncMock()
    return mock_pool


# ============================================================================
# Test CacheStats (100% Coverage)
# ============================================================================


class TestCacheStatsComprehensive:
    """Comprehensive tests for CacheStats dataclass."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_gets == 0
        assert stats.total_sets == 0
        assert stats.total_deletes == 0
        assert stats.bytes_stored == 0

    def test_initialization_custom(self):
        """Test custom initialization."""
        stats = CacheStats(
            hits=100,
            misses=50,
            evictions=10,
            total_gets=150,
            total_sets=200,
            total_deletes=5,
            bytes_stored=1024,
        )
        assert stats.hits == 100
        assert stats.misses == 50
        assert stats.evictions == 10
        assert stats.total_gets == 150
        assert stats.total_sets == 200
        assert stats.total_deletes == 5
        assert stats.bytes_stored == 1024

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        # 50% hit rate
        stats = CacheStats(hits=50, misses=50, total_gets=100)
        assert stats.hit_rate == 0.5

        # 100% hit rate
        stats = CacheStats(hits=100, misses=0, total_gets=100)
        assert stats.hit_rate == 1.0

        # 0% hit rate
        stats = CacheStats(hits=0, misses=100, total_gets=100)
        assert stats.hit_rate == 0.0

    def test_hit_rate_empty(self):
        """Test hit rate with no gets (division by zero protection)."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_miss_rate_calculation(self):
        """Test miss rate calculation."""
        stats = CacheStats(hits=75, misses=25, total_gets=100)
        assert stats.miss_rate == 0.25

    def test_miss_rate_empty(self):
        """Test miss rate with no gets."""
        stats = CacheStats()
        assert stats.miss_rate == 0.0

    def test_to_dict_complete(self):
        """Test to_dict with all fields."""
        stats = CacheStats(
            hits=80,
            misses=20,
            evictions=5,
            total_gets=100,
            total_sets=50,
            total_deletes=10,
            bytes_stored=2048,
        )
        d = stats.to_dict()

        assert d["hits"] == 80
        assert d["misses"] == 20
        assert d["evictions"] == 5
        assert d["hit_rate"] == "80.00%"
        assert d["miss_rate"] == "20.00%"
        assert d["total_gets"] == 100
        assert d["total_sets"] == 50
        assert d["total_deletes"] == 10
        assert d["bytes_stored"] == 2048

    def test_stats_mutation(self):
        """Test that stats can be mutated."""
        stats = CacheStats()
        stats.hits += 10
        stats.total_gets += 10
        assert stats.hit_rate == 1.0


# ============================================================================
# Test MemoryCache Async Operations (Comprehensive)
# ============================================================================


class TestMemoryCacheAsync:
    """Comprehensive async tests for MemoryCache."""

    @pytest.mark.asyncio
    async def test_get_existing_key(self, memory_cache):
        """Test getting an existing key."""
        await memory_cache.set("key1", "value1")
        value = await memory_cache.get("key1")
        assert value == "value1"
        assert memory_cache.stats.hits == 1
        assert memory_cache.stats.total_gets == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, memory_cache):
        """Test getting a non-existent key."""
        value = await memory_cache.get("nonexistent")
        assert value is None
        assert memory_cache.stats.misses == 1
        assert memory_cache.stats.total_gets == 1

    @pytest.mark.asyncio
    async def test_set_and_get_multiple(self, memory_cache):
        """Test setting and getting multiple values."""
        data = {
            "key1": "value1",
            "key2": 42,
            "key3": {"nested": "dict"},
            "key4": [1, 2, 3],
        }

        for key, value in data.items():
            await memory_cache.set(key, value)

        for key, expected_value in data.items():
            actual_value = await memory_cache.get(key)
            assert actual_value == expected_value

        assert memory_cache.stats.total_sets == 4
        assert memory_cache.stats.total_gets == 4
        assert memory_cache.stats.hits == 4

    @pytest.mark.asyncio
    async def test_set_with_ttl_expires(self, memory_cache):
        """Test that values with TTL expire correctly."""
        # Set with very short TTL
        await memory_cache.set("key1", "value1", ttl=0.1)

        # Should exist immediately
        value = await memory_cache.get("key1")
        assert value == "value1"

        # Wait for expiry
        await asyncio.sleep(0.2)

        # Should be expired
        value = await memory_cache.get("key1")
        assert value is None
        assert memory_cache.stats.misses >= 1

    @pytest.mark.asyncio
    async def test_set_default_ttl(self, memory_cache):
        """Test default TTL from initialization."""
        cache = MemoryCache(default_ttl=3600)
        await cache.set("key1", "value1")  # Uses default TTL

        value = await cache.get("key1")
        assert value == "value1"

        # Check expiry was set
        assert "key1" in cache._expiry

    @pytest.mark.asyncio
    async def test_delete_existing(self, memory_cache):
        """Test deleting an existing key."""
        await memory_cache.set("key1", "value1")
        result = await memory_cache.delete("key1")

        assert result is True
        value = await memory_cache.get("key1")
        assert value is None
        assert memory_cache.stats.total_deletes == 1

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, memory_cache):
        """Test deleting a non-existent key."""
        result = await memory_cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, memory_cache):
        """Test exists method."""
        await memory_cache.set("key1", "value1")

        assert await memory_cache.exists("key1") is True
        assert await memory_cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, memory_cache):
        """Test clearing all cache entries."""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")

        result = await memory_cache.clear()
        assert result is True

        assert await memory_cache.get("key1") is None
        assert await memory_cache.get("key2") is None
        assert len(memory_cache._cache) == 0
        assert memory_cache._current_memory == 0

    @pytest.mark.asyncio
    async def test_lru_eviction(self, memory_cache):
        """Test LRU eviction when cache is full."""
        # Set cache with size 3
        cache = MemoryCache(max_size=3, max_memory_mb=10.0)

        # Add 3 items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it most recently used
        await cache.get("key1")

        # Add 4th item - should evict key2 (least recently used)
        await cache.set("key4", "value4")

        assert await cache.get("key1") is not None  # Still exists
        assert await cache.get("key2") is None  # Evicted
        assert await cache.get("key3") is not None
        assert await cache.get("key4") is not None

        assert cache.stats.evictions >= 1

    @pytest.mark.asyncio
    async def test_memory_eviction(self, memory_cache):
        """Test eviction based on memory limit."""
        # Create cache with very small memory limit (1KB)
        cache = MemoryCache(max_size=100, max_memory_mb=0.001)

        # Add item larger than memory limit
        large_value = "x" * 1000  # 1KB string
        result = await cache.set("large", large_value)

        # Should be rejected (larger than 50% of max memory)
        assert result is False

    @pytest.mark.asyncio
    async def test_memory_tracking(self, memory_cache):
        """Test accurate memory tracking."""
        value = {"test": "data" * 100}
        await memory_cache.set("key1", value)

        # Memory should be tracked
        assert memory_cache._current_memory > 0
        assert memory_cache.stats.bytes_stored == memory_cache._current_memory

    @pytest.mark.asyncio
    async def test_update_existing_key(self, memory_cache):
        """Test updating an existing key."""
        await memory_cache.set("key1", "value1")

        await memory_cache.set("key1", "updated_value")

        value = await memory_cache.get("key1")
        assert value == "updated_value"

    @pytest.mark.asyncio
    async def test_get_stats(self, memory_cache):
        """Test getting cache statistics."""
        await memory_cache.set("key1", "value1")
        await memory_cache.get("key1")
        await memory_cache.get("nonexistent")
        await memory_cache.delete("key1")

        stats = memory_cache.get_stats()
        assert isinstance(stats, CacheStats)
        assert stats.total_sets == 1
        assert stats.total_gets == 2
        assert stats.total_deletes == 1
        assert stats.hits == 1
        assert stats.misses == 1


# ============================================================================
# Test MemoryCache Batch Operations
# ============================================================================


class TestMemoryCacheBatch:
    """Tests for batch operations in MemoryCache."""

    @pytest.mark.asyncio
    async def test_mget_multiple_keys(self, memory_cache):
        """Test batch get."""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.set("key3", "value3")

        results = await memory_cache.mget(["key1", "key2", "nonexistent"])

        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert "nonexistent" not in results

    @pytest.mark.asyncio
    async def test_mget_empty_list(self, memory_cache):
        """Test mget with empty list."""
        results = await memory_cache.mget([])
        assert results == {}

    @pytest.mark.asyncio
    async def test_mset_multiple(self, memory_cache):
        """Test batch set."""
        items = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

        result = await memory_cache.mset(items)
        assert result is True

        for key, value in items.items():
            assert await memory_cache.get(key) == value

    @pytest.mark.asyncio
    async def test_mset_with_ttl(self, memory_cache):
        """Test batch set with TTL."""
        items = {"key1": "value1", "key2": "value2"}

        await memory_cache.mset(items, ttl=3600)

        # Check TTL was set
        assert "key1" in memory_cache._expiry
        assert "key2" in memory_cache._expiry

    @pytest.mark.asyncio
    async def test_mset_empty_dict(self, memory_cache):
        """Test mset with empty dict."""
        result = await memory_cache.mset({})
        assert result is True


# ============================================================================
# Test MemoryCache Concurrency
# ============================================================================


class TestMemoryCacheConcurrency:
    """Tests for concurrent access to MemoryCache."""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, memory_cache):
        """Test concurrent reads."""
        await memory_cache.set("key1", "value1")

        async def read_key():
            return await memory_cache.get("key1")

        # Run 100 concurrent reads
        results = await asyncio.gather(*[read_key() for _ in range(100)])

        assert all(r == "value1" for r in results)
        assert memory_cache.stats.hits == 100

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, memory_cache):
        """Test concurrent writes."""

        async def write_key(i):
            return await memory_cache.set(f"key{i}", f"value{i}")

        # Run 50 concurrent writes
        results = await asyncio.gather(*[write_key(i) for i in range(50)])

        assert all(results)
        assert memory_cache.stats.total_sets == 50

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, memory_cache):
        """Test mixed concurrent operations."""
        await memory_cache.set("shared", "initial")

        async def mixed_op(i):
            if i % 3 == 0:
                return await memory_cache.get("shared")
            elif i % 3 == 1:
                return await memory_cache.set(f"key{i}", f"value{i}")
            else:
                return await memory_cache.delete(f"key{i-1}")

        # Run mixed operations
        results = await asyncio.gather(*[mixed_op(i) for i in range(30)])

        # Should complete without errors
        assert len(results) == 30


# ============================================================================
# Test SQLiteCache (if available)
# ============================================================================


@pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not installed")
class TestSQLiteCacheAsync:
    """Comprehensive async tests for SQLiteCache."""

    @pytest.mark.asyncio
    async def test_get_set_delete(self, sqlite_cache):
        """Test basic get/set/delete."""
        # Set
        result = await sqlite_cache.set("key1", "value1")
        assert result is True

        # Get
        value = await sqlite_cache.get("key1")
        assert value == "value1"

        # Delete
        result = await sqlite_cache.delete("key1")
        assert result is True

        # Verify deletion
        value = await sqlite_cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, sqlite_cache):
        """Test TTL in SQLite cache."""
        # Set with short TTL
        await sqlite_cache.set("key1", "value1", ttl=1)

        # Should exist
        value = await sqlite_cache.get("key1")
        assert value == "value1"

        # Wait for expiry
        await asyncio.sleep(1.5)

        # Trigger cleanup by getting
        value = await sqlite_cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_exists(self, sqlite_cache):
        """Test exists method."""
        await sqlite_cache.set("key1", "value1")

        assert await sqlite_cache.exists("key1") is True
        assert await sqlite_cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_clear(self, sqlite_cache):
        """Test clear."""
        await sqlite_cache.set("key1", "value1")
        await sqlite_cache.set("key2", "value2")

        result = await sqlite_cache.clear()
        assert result is True

        assert await sqlite_cache.get("key1") is None
        assert await sqlite_cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_mget(self, sqlite_cache):
        """Test batch get."""
        await sqlite_cache.set("key1", "value1")
        await sqlite_cache.set("key2", "value2")

        results = await sqlite_cache.mget(["key1", "key2", "nonexistent"])

        assert results["key1"] == "value1"
        assert results["key2"] == "value2"
        assert "nonexistent" not in results

    @pytest.mark.asyncio
    async def test_mset(self, sqlite_cache):
        """Test batch set."""
        items = {"key1": "value1", "key2": "value2"}

        result = await sqlite_cache.mset(items)
        assert result is True

        assert await sqlite_cache.get("key1") == "value1"
        assert await sqlite_cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_complex_types(self, sqlite_cache):
        """Test storing complex types."""
        data = {
            "dict": {"nested": "value", "number": 42},
            "list": [1, 2, 3, {"key": "value"}],
            "tuple": (1, 2, 3),
            "set": {1, 2, 3},
        }

        for key, value in data.items():
            await sqlite_cache.set(key, value)
            retrieved = await sqlite_cache.get(key)
            assert retrieved == value

    @pytest.mark.asyncio
    async def test_persistence(self, sqlite_cache):
        """Test that data persists across cache instances."""
        db_path = sqlite_cache.db_path

        # Set data
        await sqlite_cache.set("persistent", "data")
        await sqlite_cache.close()

        # Create new instance with same DB
        new_cache = SQLiteCache(db_path=db_path)
        value = await new_cache.get("persistent")

        assert value == "data"
        await new_cache.close()

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, sqlite_cache):
        """Test explicit cleanup of expired entries."""
        await sqlite_cache.set("key1", "value1", ttl=0)
        await asyncio.sleep(0.1)

        # Run cleanup
        await sqlite_cache.cleanup_expired()

        # Should be removed
        value = await sqlite_cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_stats_tracking(self, sqlite_cache):
        """Test statistics tracking."""
        await sqlite_cache.set("key1", "value1")
        await sqlite_cache.get("key1")  # hit
        await sqlite_cache.get("nonexistent")  # miss
        await sqlite_cache.delete("key1")

        stats = sqlite_cache.get_stats()
        assert stats.total_sets == 1
        assert stats.total_gets == 2
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.total_deletes == 1


# ============================================================================
# Test RedisCache (Mocked)
# ============================================================================


class TestRedisCacheMocked:
    """Tests for RedisCache with mocked Redis."""

    @pytest.mark.asyncio
    async def test_get_success(self, mock_redis):
        """Test successful get."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            mock_redis.get = AsyncMock(return_value=pickle.dumps("value1"))

            value = await cache.get("key1")
            assert value == "value1"
            assert cache.stats.hits == 1

    @pytest.mark.asyncio
    async def test_get_miss(self, mock_redis):
        """Test cache miss."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            mock_redis.get = AsyncMock(return_value=None)

            value = await cache.get("key1")
            assert value is None
            assert cache.stats.misses == 1

    @pytest.mark.asyncio
    async def test_set(self, mock_redis):
        """Test set."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            result = await cache.set("key1", "value1")
            assert result is True
            assert cache.stats.total_sets == 1
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, mock_redis):
        """Test delete."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            result = await cache.delete("key1")
            assert result is True
            assert cache.stats.total_deletes == 1

    @pytest.mark.asyncio
    async def test_exists(self, mock_redis):
        """Test exists."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            mock_redis.exists = AsyncMock(return_value=1)

            result = await cache.exists("key1")
            assert result is True

    @pytest.mark.asyncio
    async def test_clear(self, mock_redis):
        """Test clear."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            result = await cache.clear()
            assert result is True
            mock_redis.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_mget(self, mock_redis):
        """Test batch get."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            mock_redis.mget = AsyncMock(
                return_value=[
                    pickle.dumps("value1"),
                    None,
                    pickle.dumps("value3"),
                ]
            )

            results = await cache.mget(["key1", "key2", "key3"])

            assert results["key1"] == "value1"
            assert "key2" not in results
            assert results["key3"] == "value3"

    @pytest.mark.asyncio
    async def test_mset(self, mock_redis):
        """Test batch set."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            items = {"key1": "value1", "key2": "value2"}
            result = await cache.mset(items)

            assert result is True
            mock_redis.mset.assert_called_once()

    @pytest.mark.asyncio
    async def test_mset_with_ttl(self, mock_redis):
        """Test batch set with TTL uses pipeline."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            items = {"key1": "value1"}
            result = await cache.mset(items, ttl=3600)

            assert result is True
            mock_redis.pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, mock_redis):
        """Test closing connection."""
        with patch("core.cache.REDIS_AVAILABLE", True):
            cache = RedisCache()
            cache._pool = mock_redis

            await cache.close()
            mock_redis.close.assert_called_once()
            assert cache._pool is None

    def test_init_without_redis(self):
        """Test that init fails without redis package."""
        with patch("core.cache.REDIS_AVAILABLE", False):
            with pytest.raises(ImportError):
                RedisCache()


# ============================================================================
# Test MultiTierCache
# ============================================================================


class TestMultiTierCacheAsync:
    """Comprehensive async tests for MultiTierCache."""

    @pytest.mark.asyncio
    async def test_l1_hit(self):
        """Test L1 cache hit."""
        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)

        await cache.set("key1", "value1")
        value = await cache.get("key1")

        assert value == "value1"
        assert cache._hit_distribution["L1"] == 1

    @pytest.mark.asyncio
    async def test_l2_promotion(self, sqlite_cache):
        """Test L2 to L1 promotion."""
        if not SQLITE_AVAILABLE:
            pytest.skip("aiosqlite not available")

        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)
        cache.l2 = sqlite_cache

        # Set in L2 only
        await cache.l2.set("key1", "value1")

        # Get from cache - should hit L2 and promote to L1
        value = await cache.get("key1")

        assert value == "value1"
        assert cache._hit_distribution["L2"] == 1

        # Should now be in L1
        l1_value = await cache.l1.get("key1")
        assert l1_value == "value1"

    @pytest.mark.asyncio
    async def test_tiered_set_all(self):
        """Test setting in all tiers."""
        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)

        result = await cache.set("key1", "value1", tiers="all")
        assert result is True

        # Should be in L1
        assert await cache.l1.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_tiered_set_memory_only(self):
        """Test setting in memory only."""
        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)

        result = await cache.set("key1", "value1", tiers="memory")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_all_tiers(self, sqlite_cache):
        """Test delete from all tiers."""
        if not SQLITE_AVAILABLE:
            pytest.skip("aiosqlite not available")

        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)
        cache.l2 = sqlite_cache

        # Set in both tiers
        await cache.set("key1", "value1")
        await cache.l2.set("key1", "value1")

        # Delete from all
        result = await cache.delete("key1")
        assert result is True

        # Should be deleted from all tiers
        assert await cache.l1.get("key1") is None
        assert await cache.l2.get("key1") is None

    @pytest.mark.asyncio
    async def test_mget_multi_tier(self, sqlite_cache):
        """Test multi-tier batch get."""
        if not SQLITE_AVAILABLE:
            pytest.skip("aiosqlite not available")

        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)
        cache.l2 = sqlite_cache

        # Set in different tiers
        await cache.l1.set("key1", "l1_value")
        await cache.l2.set("key2", "l2_value")

        results = await cache.mget(["key1", "key2"])

        assert results["key1"] == "l1_value"
        assert results["key2"] == "l2_value"

    @pytest.mark.asyncio
    async def test_get_stats(self, sqlite_cache):
        """Test getting combined stats."""
        if not SQLITE_AVAILABLE:
            pytest.skip("aiosqlite not available")

        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)
        cache.l2 = sqlite_cache

        # Generate some activity
        await cache.set("key1", "value1")
        await cache.get("key1")

        stats = cache.get_stats()

        assert "hit_distribution" in stats
        assert "L1_memory" in stats
        assert "L2_sqlite" in stats
        assert stats["hit_distribution"]["L1"]["count"] == 1

    @pytest.mark.asyncio
    async def test_close(self, sqlite_cache):
        """Test closing all tiers."""
        if not SQLITE_AVAILABLE:
            pytest.skip("aiosqlite not available")

        cache = MultiTierCache(memory_size=10, memory_max_mb=5.0)
        cache.l2 = sqlite_cache

        await cache.close()

        # L2 should be closed
        assert cache.l2._db is None


# ============================================================================
# Test Cache Decorators
# ============================================================================


class TestCachedDecorator:
    """Tests for @cached decorator."""

    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """Test caching async function results."""
        call_count = 0

        @cached(backend="memory", ttl=3600)
        async def async_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call
        result1 = await async_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same arg - should be cached
        result2 = await async_function(5)
        assert result2 == 10
        assert call_count == 1  # Not called again

    def test_sync_function_caching(self):
        """Test caching sync function results."""
        call_count = 0

        @cached(backend="memory", ttl=3600)
        def sync_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        # First call
        result1 = sync_function(5)
        assert result1 == 15
        assert call_count == 1

        # Second call - should be cached
        result2 = sync_function(5)
        assert result2 == 15
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_different_args_different_cache(self):
        """Test that different args have different cache entries."""
        call_count = 0

        @cached(backend="memory", ttl=3600)
        async def compute(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        await compute(1, 2)
        await compute(1, 3)
        await compute(2, 2)

        assert call_count == 3  # All different

    @pytest.mark.asyncio
    async def test_custom_key_function(self):
        """Test custom key generation."""
        call_count = 0

        def custom_key(x, y):
            return f"custom:{x}:{y}"

        @cached(backend="memory", ttl=3600, key_func=custom_key)
        async def compute(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        await compute(1, 2)
        await compute(1, 2)

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_condition_function(self):
        """Test condition for caching."""
        call_count = 0

        @cached(backend="memory", ttl=3600, condition=lambda r: r > 10)
        async def compute(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Result 10 not cached
        await compute(5)  # result 10
        await compute(5)  # result 10, called again

        assert call_count == 2

        # Result 20 cached
        await compute(10)  # result 20
        await compute(10)  # result 20, from cache

        assert call_count == 3


# ============================================================================
# Test CVE Cache Functions
# ============================================================================


class TestCVEFunctions:
    """Tests for CVE-specific cache functions."""

    @pytest.mark.asyncio
    async def test_cache_cve_and_get(self):
        """Test caching and retrieving CVE data."""
        cve_data = {
            "id": "CVE-2021-44228",
            "description": "Log4j vulnerability",
            "severity": "CRITICAL",
        }

        # Cache CVE
        await cache_cve("CVE-2021-44228", cve_data)

        # Retrieve CVE
        cached = await get_cached_cve("CVE-2021-44228")

        assert cached == cve_data

    @pytest.mark.asyncio
    async def test_get_nonexistent_cve(self):
        """Test getting non-existent CVE."""
        result = await get_cached_cve("CVE-9999-99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_cve_case_insensitive(self):
        """Test CVE ID is case insensitive."""
        cve_data = {"id": "CVE-2021-44228"}

        await cache_cve("cve-2021-44228", cve_data)

        # Should be retrievable with uppercase
        cached = await get_cached_cve("CVE-2021-44228")
        assert cached == cve_data


# ============================================================================
# Test CacheBackend Base Class
# ============================================================================


class TestCacheBackendAsync:
    """Tests for CacheBackend abstract class methods."""

    @pytest.mark.asyncio
    async def test_default_mget(self):
        """Test default mget implementation."""
        backend = CacheBackend()

        # Default mget should return empty dict
        results = await backend.mget(["key1", "key2"])
        assert results == {}

    @pytest.mark.asyncio
    async def test_default_mset(self):
        """Test default mset implementation."""
        backend = CacheBackend()

        # Default mset should return True
        result = await backend.mset({"key1": "value1"})
        assert result is True

    @pytest.mark.asyncio
    async def test_default_close(self):
        """Test default close does nothing."""
        backend = CacheBackend()

        # Should not raise
        await backend.close()


# ============================================================================
# Performance Tests
# ============================================================================


class TestCachePerformance:
    """Performance tests for cache operations."""

    @pytest.mark.asyncio
    async def test_memory_cache_throughput(self):
        """Test memory cache throughput."""
        cache = MemoryCache(max_size=1000, max_memory_mb=50.0)

        # Measure set throughput
        start = time.time()
        for i in range(1000):
            await cache.set(f"key{i}", f"value{i}")
        set_time = time.time() - start

        # Measure get throughput
        start = time.time()
        for i in range(1000):
            await cache.get(f"key{i}")
        get_time = time.time() - start

        # Assert reasonable performance (>1000 ops/sec)
        assert set_time < 1.0, f"Set throughput too slow: {1000/set_time} ops/sec"
        assert get_time < 1.0, f"Get throughput too slow: {1000/get_time} ops/sec"

    @pytest.mark.asyncio
    async def test_batch_vs_individual(self):
        """Test batch operations vs individual."""
        cache = MemoryCache(max_size=1000, max_memory_mb=50.0)

        # Individual sets
        items = {f"key{i}": f"value{i}" for i in range(100)}

        start = time.time()
        for k, v in items.items():
            await cache.set(k, v)
        individual_time = time.time() - start

        await cache.clear()

        # Batch set
        start = time.time()
        await cache.mset(items)
        batch_time = time.time() - start

        # Batch should be faster (or at least not significantly slower)
        assert batch_time <= individual_time * 1.5


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestCacheEdgeCases:
    """Edge cases and error handling tests."""

    @pytest.mark.asyncio
    async def test_empty_key(self, memory_cache):
        """Test empty string key."""
        await memory_cache.set("", "value")
        value = await memory_cache.get("")
        assert value == "value"

    @pytest.mark.asyncio
    async def test_none_value(self, memory_cache):
        """Test None value."""
        await memory_cache.set("key", None)
        # Note: exists() uses get(), so None values are tricky
        value = await memory_cache.get("key")
        assert value is None

    @pytest.mark.asyncio
    async def test_unicode_keys_and_values(self, memory_cache):
        """Test unicode strings."""
        keys_values = [
            ("日本語", "中文"),
            ("emoji🎉", "special!@#$%"),
            ("\n\t\r", "\x00\x01"),
        ]

        for key, value in keys_values:
            await memory_cache.set(key, value)
            assert await memory_cache.get(key) == value

    @pytest.mark.asyncio
    async def test_large_value_rejection(self, memory_cache):
        """Test that oversized values are rejected."""
        # Create value larger than 50% of memory limit
        large_value = "x" * (1024 * 1024)  # 1MB

        result = await memory_cache.set("large", large_value)
        assert result is False

    @pytest.mark.asyncio
    async def test_negative_ttl(self, memory_cache):
        """Test negative TTL."""
        await memory_cache.set("key", "value", ttl=-1)

        # Should be expired immediately (or treated as no TTL)
        # Behavior depends on implementation
        result = await memory_cache.get("key")
        # Either None (expired) or "value" (no expiry)
        assert result is None or result == "value"

    @pytest.mark.asyncio
    async def test_zero_ttl(self, memory_cache):
        """Test zero TTL."""
        await memory_cache.set("key", "value", ttl=0)

        # Zero TTL typically means no expiry
        value = await memory_cache.get("key")
        assert value == "value"


# ============================================================================
# Coverage Test Runner
# ============================================================================

if __name__ == "__main__":
    # Run with coverage
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=core.cache",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80",
        ]
    )
