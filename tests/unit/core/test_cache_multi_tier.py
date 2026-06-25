"""Cache multi tier tests"""

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
