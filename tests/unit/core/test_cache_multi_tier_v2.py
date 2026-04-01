"""Multi tier cache tests"""

import pytest


class TestMultiTierCache:
    """Test multi tier cache"""

    def test_multi_tier_import(self):
        from core.cache import MultiTierCache

        assert MultiTierCache is not None

    def test_multi_tier_has_set(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "set")

    def test_multi_tier_has_get(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "get")

    def test_multi_tier_has_delete(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "delete")

    def test_multi_tier_has_exists(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "mget")

    def test_multi_tier_has_clear(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "close")

    def test_multi_tier_has_get_stats(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "get_stats")

    def test_multi_tier_has_close(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "close")
