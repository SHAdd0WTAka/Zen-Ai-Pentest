"""Async cache tests"""

import pytest


class TestAsyncCache:
    """Test async cache"""

    def test_cache_backend_has_get(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "get")

    def test_cache_backend_has_set(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "set")

    def test_cache_backend_has_delete(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "delete")

    def test_cache_backend_has_exists(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "exists")

    def test_cache_backend_has_clear(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "clear")

    def test_cache_backend_has_get_stats(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "get_stats")

    def test_cache_backend_has_close(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "close")

    def test_cache_backend_has_mget(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "mget")

    def test_cache_backend_has_mset(self):
        from core.cache import CacheBackend

        assert hasattr(CacheBackend, "mset")
