"""Multi tier cache full tests"""

import pytest


class TestMultiTierCacheFull:
    """Test multi tier cache full"""

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

    def test_multi_tier_has_get_stats(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "get_stats")

    def test_multi_tier_has_close(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "close")

    def test_multi_tier_has_mget(self):
        from core.cache import MultiTierCache

        assert hasattr(MultiTierCache, "mget")

    def test_multi_tier_has_l1(self):
        from core.cache import MultiTierCache

        mtc = MultiTierCache()
        assert hasattr(mtc, "l1")

    def test_multi_tier_has_l2(self):
        from core.cache import MultiTierCache

        mtc = MultiTierCache()
        assert hasattr(mtc, "l2")

    def test_multi_tier_has_l3(self):
        from core.cache import MultiTierCache

        mtc = MultiTierCache()
        assert hasattr(mtc, "l3")
