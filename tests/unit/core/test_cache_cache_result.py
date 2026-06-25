"""Cache cache result tests"""

import pytest


class TestCacheResult:
    """Test cache result"""

    def test_cache_result_import(self):
        from core.cache import cache_result

        assert cache_result is not None

    def test_cache_result_is_callable(self):
        from core.cache import cache_result

        assert callable(cache_result)
