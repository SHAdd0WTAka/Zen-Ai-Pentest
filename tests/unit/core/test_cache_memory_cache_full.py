"""Memory cache full tests"""

import pytest


class TestMemoryCacheFull:
    """Test memory cache full"""

    def test_memory_cache_creation(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        assert cache is not None

    def test_memory_cache_has_set(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "set")

    def test_memory_cache_has_get(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "get")

    def test_memory_cache_has_delete(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "delete")

    def test_memory_cache_has_exists(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "exists")

    def test_memory_cache_has_clear(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "clear")

    def test_memory_cache_has_get_stats(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "get_stats")

    def test_memory_cache_has_close(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "close")

    def test_memory_cache_has_mget(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "mget")

    def test_memory_cache_has_mset(self):
        from core.cache import MemoryCache

        assert hasattr(MemoryCache, "mset")
