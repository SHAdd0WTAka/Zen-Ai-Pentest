"""Additional cache tests for SQLite, Redis, and complex scenarios"""

import asyncio
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
class TestCacheHelpers:
    """Test cache helper functions"""

    def test_sharded_lock_import(self):
        from core.cache import ShardedLock

        assert ShardedLock is not None

    def test_cache_stats_hit_rate(self):
        from core.cache import CacheStats

        stats = CacheStats()
        stats.hits = 7
        stats.misses = 3
        stats.total_gets = 10
        assert stats.hit_rate == 0.7

    def test_cache_stats_empty(self):
        from core.cache import CacheStats

        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_multi_tier_cache_import(self):
        from core.cache import MultiTierCache

        assert MultiTierCache is not None

    def test_cache_alias(self):
        from core.cache import Cache, MultiTierCache

        assert Cache is MultiTierCache


@pytest.mark.asyncio
class TestMemoryCacheEdgeCases:
    """Edge case tests for MemoryCache"""

    async def test_set_overwrite(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key", "old")
        await cache.set("key", "new")
        assert await cache.get("key") == "new"

    async def test_get_none_value(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key", None)
        # None is treated as not cached
        assert await cache.get("key") is None

    async def test_large_value(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        large_data = "x" * 100000
        await cache.set("large", large_data)
        assert await cache.get("large") == large_data

    async def test_unicode_key(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("🔑", "value")
        assert await cache.get("🔑") == "value"

    async def test_concurrent_set_get(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        async def writer():
            for i in range(100):
                await cache.set(f"key_{i}", f"val_{i}")

        async def reader():
            for i in range(100):
                await cache.get(f"key_{i}")

        await asyncio.gather(writer(), reader())

    async def test_concurrent_delete(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        for i in range(10):
            await cache.set(f"key_{i}", f"val_{i}")

        async def deleter():
            for i in range(10):
                await cache.delete(f"key_{i}")

        await asyncio.gather(deleter(), deleter())

    async def test_clear_empty_cache(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.clear()
        assert await cache.get("any") is None

    async def test_mset_empty(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.mset({})
        stats = cache.get_stats()
        assert stats is not None


@pytest.mark.asyncio
class TestCacheStats:
    """Test cache statistics"""

    async def test_stats_tracks_hits(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key", "val")
        await cache.get("key")
        stats = cache.get_stats()
        assert stats.hits >= 1

    async def test_stats_tracks_misses(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.get("nonexistent")
        stats = cache.get_stats()
        assert stats.misses >= 1

    async def test_stats_tracks_evictions(self):
        from core.cache import MemoryCache

        cache = MemoryCache(max_size=1)
        await cache.set("k1", "v1")
        await cache.set("k2", "v2")
        stats = cache.get_stats()
        assert stats.evictions >= 1
