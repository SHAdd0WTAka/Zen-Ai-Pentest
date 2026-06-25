"""Cache cache result decorator tests"""

import pytest


class TestCacheResultDecorator:
    """Test cache result decorator"""

    def test_cache_result_import(self):
        from core.cache import cache_result

        assert cache_result is not None

    def test_cache_result_is_callable(self):
        from core.cache import cache_result

        assert callable(cache_result)

    def test_cache_result_takes_cache(self):
        from core.cache import MemoryCache, cache_result

        result = cache_result(cache=MemoryCache())
        assert callable(result)

    def test_cache_result_takes_ttl(self):
        from core.cache import MemoryCache, cache_result

        result = cache_result(cache=MemoryCache(), ttl=3600)
        assert callable(result)

    def test_cache_result_takes_key_func(self):
        from core.cache import MemoryCache, cache_result

        result = cache_result(cache=MemoryCache(), key_func=lambda x: f"test:{x}")
        assert callable(result)
