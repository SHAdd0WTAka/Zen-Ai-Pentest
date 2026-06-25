"""Cache Redis tests"""

import pytest


class TestCacheRedis:
    """Test cache Redis"""

    def test_redis_cache_import(self):
        from core.cache import RedisCache

        assert RedisCache is not None

    def test_redis_cache_creation(self):
        from core.cache import RedisCache

        cache = RedisCache()
        assert cache is not None
