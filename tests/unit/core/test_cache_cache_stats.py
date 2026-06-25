"""Cache stats tests"""

import pytest


class TestCacheStats:
    """Test cache stats"""

    def test_cache_stats_import(self):
        from core.cache import CacheStats

        assert CacheStats is not None

    def test_cache_stats_has_hits(self):
        from core.cache import CacheStats

        stats = CacheStats()
        assert hasattr(stats, "hits")

    def test_cache_stats_has_misses(self):
        from core.cache import CacheStats

        stats = CacheStats()
        assert hasattr(stats, "misses")

    def test_cache_stats_has_sets(self):
        from core.cache import CacheStats

        stats = CacheStats()
        assert hasattr(stats, "total_sets")
