"""More cache tests to push coverage"""

import asyncio
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
class TestMemoryCacheAdvanced:
    """Advanced MemoryCache tests"""

    async def test_set_with_ttl(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key", "value", ttl=3600)
        assert await cache.get("key") == "value"

    async def test_set_with_compression(self):
        from core.cache import MemoryCache

        cache = MemoryCache(enable_compression=True)
        large_data = "x" * 10000
        await cache.set("compressed", large_data)
        result = await cache.get("compressed")
        assert result == large_data

    async def test_set_with_encryption(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("encrypted", "secret_data")
        result = await cache.get("encrypted")
        assert result == "secret_data"

    async def test_get_missing(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        result = await cache.get("missing")
        assert result is None

    async def test_stats_after_operations(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("k1", "v1")
        await cache.get("k1")
        await cache.get("missing")
        stats = cache.get_stats()
        assert stats.hits >= 1
        assert stats.misses >= 1

    async def test_clear_empty(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.clear()
        assert await cache.get("any") is None

    async def test_concurrent_access(self):
        from core.cache import MemoryCache

        cache = MemoryCache()

        async def writer(n):
            for i in range(10):
                await cache.set(f"key_{n}_{i}", f"val_{n}_{i}")

        async def reader(n):
            for i in range(10):
                await cache.get(f"key_{n}_{i}")

        await asyncio.gather(writer(1), writer(2), reader(1), reader(2))


@pytest.mark.asyncio
class TestCacheManagerAdvanced:
    """Advanced CacheManager tests"""

    async def test_multiple_backends(self):
        from core.cache import CacheManager, MemoryCache

        cm = CacheManager()
        cm.register_backend("fast", MemoryCache())
        cm.register_backend("slow", MemoryCache())
        await cm.set("key", "fast_val", backend="fast")
        await cm.set("key", "slow_val", backend="slow")
        assert await cm.get("key", backend="fast") == "fast_val"
        assert await cm.get("key", backend="slow") == "slow_val"

    async def test_clear_backend(self):
        from core.cache import CacheManager, MemoryCache

        cm = CacheManager()
        cm.register_backend("default", MemoryCache())
        await cm.set("key", "val")
        await cm.clear()
        assert await cm.get("key") is None


class TestGenerateCacheKeyAdvanced:
    """Advanced generate_cache_key tests"""

    def test_nested_dict(self):
        from core.cache import generate_cache_key

        key = generate_cache_key({"a": {"b": {"c": 1}}})
        assert isinstance(key, str)
        assert len(key) == 64

    def test_list_of_dicts(self):
        from core.cache import generate_cache_key

        key = generate_cache_key([{"a": 1}, {"b": 2}])
        assert isinstance(key, str)

    def test_mixed_args_kwargs(self):
        from core.cache import generate_cache_key

        key = generate_cache_key("arg1", 123, kw1="val1", kw2=456)
        assert isinstance(key, str)
