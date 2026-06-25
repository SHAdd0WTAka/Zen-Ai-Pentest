import asyncio

import pytest

from core.cache import MemoryCache, cached, generate_cache_key


@pytest.mark.asyncio
@pytest.mark.parametrize("max_size", [1, 2, 3])
async def test_memory_cache_lru_eviction_by_size(max_size):
    cache = MemoryCache(max_size=max_size, max_memory_mb=1)

    for i in range(max_size + 1):
        assert await cache.set(f"k{i}", i) is True

    # oldest should be evicted
    assert await cache.get("k0") is None
    assert await cache.get(f"k{max_size}") == max_size


@pytest.mark.asyncio
@pytest.mark.parametrize("ttl", [1, 2])
async def test_memory_cache_ttl_expiry(monkeypatch, ttl):
    cache = MemoryCache(max_size=10, max_memory_mb=1)
    base = 1000.0
    monkeypatch.setattr("core.cache.time.time", lambda: base)
    assert await cache.set("a", 1, ttl=ttl)

    monkeypatch.setattr("core.cache.time.time", lambda: base + ttl + 0.1)
    assert await cache.get("a") is None


@pytest.mark.asyncio
async def test_memory_cache_mget_mset_exists_delete_clear():
    cache = MemoryCache(max_size=10, max_memory_mb=1)
    assert await cache.mset({"a": 1, "b": 2}) is True
    assert await cache.exists("a") is True

    values = await cache.mget(["a", "b", "c"])
    assert values == {"a": 1, "b": 2}

    assert await cache.delete("a") is True
    assert await cache.delete("missing") is False

    assert await cache.clear() is True
    assert await cache.get("b") is None


def test_generate_cache_key_is_stable_for_same_input():
    k1 = generate_cache_key(1, "a", x=2)
    k2 = generate_cache_key(1, "a", x=2)
    k3 = generate_cache_key(1, "a", x=3)
    assert k1 == k2
    assert k1 != k3


@pytest.mark.asyncio
async def test_cached_decorator_async_hits_cache():
    cache = MemoryCache(max_size=10, max_memory_mb=1)
    calls = {"n": 0}

    @cached(backend=cache, ttl=60)
    async def compute(x):
        calls["n"] += 1
        return x * 2

    assert await compute(3) == 6
    assert await compute(3) == 6
    assert calls["n"] == 1


def test_cached_decorator_sync_function_current_behavior():
    cache = MemoryCache(max_size=10, max_memory_mb=1)

    @cached(backend=cache, ttl=60)
    def sync_add(x, y):
        return x + y

    assert sync_add(1, 2) == 3


@pytest.mark.asyncio
async def test_cached_decorator_condition_blocks_storage():
    cache = MemoryCache(max_size=10, max_memory_mb=1)
    calls = {"n": 0}

    @cached(backend=cache, ttl=60, condition=lambda v: v > 10)
    async def compute(x):
        calls["n"] += 1
        return x

    assert await compute(1) == 1
    assert await compute(1) == 1
    # not cached due to condition false
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_memory_cache_rejects_huge_value(monkeypatch):
    cache = MemoryCache(max_size=10, max_memory_mb=0.0001)

    class Huge:
        pass

    # force huge pickle size path
    monkeypatch.setattr("core.cache.pickle.dumps", lambda _v: b"x" * 10_000_000)
    assert await cache.set("huge", Huge()) is False


def test_sync_cached_runs_without_existing_loop_current_behavior():
    cache = MemoryCache(max_size=10, max_memory_mb=1)

    @cached(backend=cache)
    def f(v):
        return v

    assert f("x") == "x"
