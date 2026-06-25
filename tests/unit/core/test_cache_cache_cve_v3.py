"""Cache CVE tests"""

import pytest


class TestCacheCVE:
    """Test cache CVE"""

    def test_get_cached_cve_import(self):
        from core.cache import get_cached_cve

        assert get_cached_cve is not None

    def test_cache_cve_import(self):
        from core.cache import cache_cve

        assert cache_cve is not None

    def test_get_cached_cve_is_callable(self):
        from core.cache import get_cached_cve

        assert callable(get_cached_cve)

    def test_cache_cve_is_callable(self):
        from core.cache import cache_cve

        assert callable(cache_cve)
