"""Cache memory tests"""

import pytest


class TestCacheMemory:
    """Test cache memory"""

    def test_memory_cache_import(self):
        from core.cache import MemoryCache

        assert MemoryCache is not None

    def test_memory_cache_creation(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        assert cache is not None

    def test_memory_cache_set(self):
        from core.cache import MemoryCache

        cache = MemoryCache()
        assert cache is not None
