"""Smoke tests for core/cache.py"""

import pytest

from core.cache import CacheBackend, CacheManager, CacheStats, MemoryCache, MultiTierCache, ShardedLock, generate_cache_key


class TestCacheStats:
    def test_defaults(self):
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate(self):
        stats = CacheStats(hits=80, misses=20, total_gets=100)
        assert stats.hit_rate == 0.8


class TestShardedLock:
    def test_init(self):
        lock = ShardedLock(num_shards=16)
        assert lock._num_shards == 16

    def test_get_shard(self):
        lock = ShardedLock()
        idx = lock._get_shard("test_key")
        assert 0 <= idx < lock._num_shards


class TestMemoryCache:
    def test_init_defaults(self):
        cache = MemoryCache()
        assert cache._max_size == 1000
        assert cache._default_ttl is None

    def test_init_custom(self):
        cache = MemoryCache(max_size=100, default_ttl=300)
        assert cache._max_size == 100
        assert cache._default_ttl == 300


class TestMultiTierCache:
    def test_init(self):
        cache = MultiTierCache(memory_size=100)
        assert cache.l1 is not None
        assert cache.l1._max_size == 100


class TestCacheManager:
    def test_init(self):
        mgr = CacheManager()
        assert mgr._backends == {}

    def test_register_backend(self):
        mgr = CacheManager()
        backend = MemoryCache()
        mgr.register_backend("test", backend)
        assert "test" in mgr._backends


class TestGenerateCacheKey:
    def test_returns_string(self):
        key = generate_cache_key("arg1", kwarg1="val1")
        assert isinstance(key, str)
        assert len(key) == 64
