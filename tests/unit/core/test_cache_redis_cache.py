"""Cache Redis cache tests"""

import pytest


class TestRedisCache:
    """Test Redis cache"""

    def test_redis_cache_import(self):
        from core.cache import RedisCache

        assert RedisCache is not None

    def test_redis_cache_has_set(self):
        from core.cache import RedisCache

        assert hasattr(RedisCache, "set")

    def test_redis_cache_has_get(self):
        from core.cache import RedisCache

        assert hasattr(RedisCache, "get")

    def test_redis_cache_has_delete(self):
        from core.cache import RedisCache

        assert hasattr(RedisCache, "delete")
