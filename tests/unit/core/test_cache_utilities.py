"""Cache utilities tests"""

import pytest


class TestCacheUtilities:
    """Test cache utilities"""

    def test_cached_cve(self):
        from core.cache import get_cached_cve

        assert get_cached_cve is not None

    def test_cache_cve(self):
        from core.cache import cache_cve

        assert cache_cve is not None

    def test_sharded_lock(self):
        from core.cache import ShardedLock

        assert ShardedLock is not None
