import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from core.cache import CacheStats, MemoryCache


@pytest.mark.parametrize(
    "hits,misses,total_gets,expected_hit_rate",
    [
        (0, 0, 0, 0.0),
        (1, 0, 1, 1.0),
        (2, 2, 4, 0.5),
    ],
)
def test_cache_stats_rates(hits, misses, total_gets, expected_hit_rate):
    stats = CacheStats(hits=hits, misses=misses, total_gets=total_gets)
    assert stats.hit_rate == expected_hit_rate
    assert stats.miss_rate == (0.0 if total_gets == 0 else misses / total_gets)


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_set_get_delete_exists_clear():
    c = MemoryCache(max_size=5, max_memory_mb=1)
    assert await c.set("a", {"x": 1}) is True
    assert await c.get("a") == {"x": 1}
    assert await c.exists("a") is True
    assert await c.delete("a") is True
    assert await c.exists("a") is False
    assert await c.clear() is True


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_ttl_expiry(monkeypatch):
    c = MemoryCache(max_size=5, max_memory_mb=1)
    now = [1000.0]
    monkeypatch.setattr("core.cache.time.time", lambda: now[0])

    await c.set("k", "v", ttl=1)
    assert await c.get("k") == "v"
    now[0] = 1002.0
    assert await c.get("k") is None


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_lru_eviction_by_max_size():
    c = MemoryCache(max_size=2, max_memory_mb=1)
    await c.set("a", 1)
    await c.set("b", 2)
    await c.get("a")  # make a recent
    await c.set("c", 3)  # evicts b

    assert await c.get("a") == 1
    assert await c.get("b") is None
    assert await c.get("c") == 3


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_skip_too_large_value(monkeypatch):
    c = MemoryCache(max_size=2, max_memory_mb=0.0001)

    monkeypatch.setattr("core.cache.pickle.dumps", lambda _v: b"x" * 100000)
    ok = await c.set("big", "data")
    assert ok is False


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_mget_mset_and_stats():
    c = MemoryCache(max_size=10, max_memory_mb=1)
    await c.mset({"a": 1, "b": 2})

    result = await c.mget(["a", "b", "missing"])
    assert result == {"a": 1, "b": 2}

    stats = c.get_stats().to_dict()
    assert stats["total_sets"] >= 2
    assert stats["total_gets"] >= 3


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_internal_remove_and_evict_paths(monkeypatch):
    c = MemoryCache(max_size=3, max_memory_mb=1)
    await c.set("a", "x", ttl=1)
    await c.set("b", "y")

    # force expired cleanup branch in _evict_lru
    fixed_now = [1000.0]
    monkeypatch.setattr("core.cache.time.time", lambda: fixed_now[0])
    c._expiry["a"] = 999.0

    c._evict_lru()
    assert "a" not in c._cache


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_exists_uses_get(monkeypatch):
    c = MemoryCache(max_size=2, max_memory_mb=1)
    c.get = AsyncMock(return_value="v")
    assert await c.exists("k") is True


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_memory_cache_mset_returns_true_even_with_items():
    c = MemoryCache(max_size=10, max_memory_mb=1)
    assert await c.mset({"x": 1, "y": 2}, ttl=5) is True
