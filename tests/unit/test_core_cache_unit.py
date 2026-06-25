"""
Unit Tests for Cache Module - Week 1 Goal
cache.py: 20% → 75% coverage
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestCacheStats:
    """Test CacheStats dataclass"""

    def test_stats_creation(self):
        from core.cache import CacheStats

        stats = CacheStats(hits=10, misses=5, evictions=2)
        assert stats.hits == 10
        assert stats.misses == 5
        assert stats.evictions == 2

    def test_hit_rate(self):
        from core.cache import CacheStats

        stats = CacheStats(hits=90, misses=10, total_gets=100)
        assert stats.hit_rate == 0.9  # 90% (property, not method)

    def test_hit_rate_no_requests(self):
        from core.cache import CacheStats

        stats = CacheStats(hits=0, misses=0, total_gets=0)
        assert stats.hit_rate == 0.0

    def test_miss_rate(self):
        from core.cache import CacheStats

        stats = CacheStats(hits=80, misses=20, total_gets=100)
        assert stats.miss_rate == 0.2  # 20% (property, not method)

    def test_to_dict(self):
        from core.cache import CacheStats

        stats = CacheStats(hits=50, misses=10, evictions=2)
        data = stats.to_dict()
        assert data["hits"] == 50
        assert data["misses"] == 10
        assert data["evictions"] == 2


class TestMemoryCache:
    """Test MemoryCache class"""

    @pytest.mark.asyncio
    async def test_memory_cache_creation(self):
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=100, default_ttl=60)
        assert cache._max_size == 100
        assert cache._default_ttl == 60

    @pytest.mark.asyncio
    async def test_cache_get_set(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        # Set value
        await cache.set("key1", "value1")

        # Get value
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_cache_get_missing(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")

        assert deleted is True
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_exists(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        await cache.set("key1", "value1")

        assert await cache.exists("key1") is True
        assert await cache.exists("key2") is False

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        cleared = await cache.clear()

        assert cleared is True
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=100)

        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1


class TestSQLiteCache:
    """Test SQLiteCache class"""

    @pytest.mark.asyncio
    async def test_sqlite_cache_creation(self):
        import tempfile

        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            assert cache.db_path == db_path
            await cache.close()

    @pytest.mark.asyncio
    async def test_sqlite_get_set(self):
        import tempfile

        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("key1", "value1")
            result = await cache.get("key1")

            assert result == "value1"
            await cache.close()

    @pytest.mark.asyncio
    async def test_sqlite_delete(self):
        import tempfile

        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("key1", "value1")
            deleted = await cache.delete("key1")

            assert deleted is True
            assert await cache.get("key1") is None
            await cache.close()

    @pytest.mark.asyncio
    async def test_sqlite_clear(self):
        import tempfile

        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("key1", "value1")
            await cache.clear()

            assert await cache.get("key1") is None
            await cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
