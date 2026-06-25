"""Cached batch tests"""

import pytest


class TestCachedBatch:
    """Test cached batch"""

    def test_cached_batch_import(self):
        from core.cache import cached_batch

        assert cached_batch is not None

    def test_cached_batch_is_callable(self):
        from core.cache import cached_batch

        assert callable(cached_batch)

    def test_cached_batch_takes_backend(self):
        from core.cache import MemoryCache, cached_batch

        result = cached_batch(backend=MemoryCache())
        assert callable(result)

    def test_cached_batch_takes_ttl(self):
        from core.cache import MemoryCache, cached_batch

        result = cached_batch(backend=MemoryCache(), ttl=3600)
        assert callable(result)

    def test_cached_batch_takes_batch_size(self):
        from core.cache import MemoryCache, cached_batch

        result = cached_batch(backend=MemoryCache(), batch_size=100)
        assert callable(result)
