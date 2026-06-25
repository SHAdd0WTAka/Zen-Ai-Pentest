"""Cache manager async tests"""

import pytest


class TestCacheManagerAsync:
    """Test cache manager async"""

    def test_cache_manager_has_set(self):
        from core.cache import CacheManager

        assert hasattr(CacheManager, "set")

    def test_cache_manager_has_get(self):
        from core.cache import CacheManager

        assert hasattr(CacheManager, "get")

    def test_cache_manager_has_delete(self):
        from core.cache import CacheManager

        assert hasattr(CacheManager, "delete")

    def test_cache_manager_has_exists(self):
        from core.cache import CacheManager

        assert hasattr(CacheManager, "exists")

    def test_cache_manager_has_clear(self):
        from core.cache import CacheManager

        assert hasattr(CacheManager, "clear")

    def test_cache_manager_has_register(self):
        from core.cache import CacheManager

        assert hasattr(CacheManager, "register_backend")
