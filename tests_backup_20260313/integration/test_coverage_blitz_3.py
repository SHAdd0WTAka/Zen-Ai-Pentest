"""Coverage Blitz 3: 10 Tests für core/"""

import asyncio

import pytest


@pytest.mark.asyncio
async def test_cache_set_many():
    """Cache viele Werte setzen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    for i in range(20):
        await cache.set(f"key{i}", f"value{i}")

    for i in range(20):
        val = await cache.get(f"key{i}")
        assert val == f"value{i}"


@pytest.mark.asyncio
async def test_cache_ttl_variations():
    """Cache TTL Variationen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("short", "data", ttl=0.01)
    await cache.set("long", "data", ttl=3600)

    await asyncio.sleep(0.02)
    assert await cache.get("short") is None
    assert await cache.get("long") == "data"


@pytest.mark.asyncio
async def test_cache_overwrite():
    """Cache Werte überschreiben."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("overwrite", "original")
    assert await cache.get("overwrite") == "original"

    await cache.set("overwrite", "updated")
    assert await cache.get("overwrite") == "updated"


@pytest.mark.asyncio
async def test_cache_stats_many():
    """Cache Stats mit vielen Operationen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    for i in range(10):
        await cache.set(f"stat{i}", f"val{i}")

    for i in range(10):
        await cache.get(f"stat{i}")
        await cache.get(f"stat{i}")

    stats = cache.get_stats()
    assert stats.total_sets >= 10
    assert stats.total_gets >= 20


@pytest.mark.asyncio
async def test_cache_delete_many():
    """Cache viele Werte löschen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    for i in range(10):
        await cache.set(f"del{i}", f"val{i}")

    for i in range(10):
        await cache.delete(f"del{i}")

    for i in range(10):
        assert await cache.get(f"del{i}") is None


@pytest.mark.asyncio
async def test_cache_mixed_types():
    """Cache verschiedene Datentypen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("string", "text")
    await cache.set("int", 123)
    await cache.set("float", 3.14)
    await cache.set("bool", True)
    await cache.set("list", [1, 2, 3])
    await cache.set("dict", {"a": 1, "b": 2})

    assert await cache.get("string") == "text"
    assert await cache.get("int") == 123
    assert await cache.get("float") == 3.14
    assert await cache.get("bool") is True
    assert await cache.get("list") == [1, 2, 3]
    assert await cache.get("dict") == {"a": 1, "b": 2}


@pytest.mark.asyncio
async def test_cache_large_values():
    """Cache große Werte."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    large_data = "x" * 10000
    await cache.set("large", large_data)

    retrieved = await cache.get("large")
    assert len(retrieved) == 10000


@pytest.mark.asyncio
async def test_cache_special_chars():
    """Cache Special Characters in Keys."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    special_keys = [
        "key:with:colons",
        "key/with/slashes",
        "key.with.dots",
        "key-with-dashes",
    ]

    for key in special_keys:
        await cache.set(key, f"value_for_{key}")

    for key in special_keys:
        assert await cache.get(key) == f"value_for_{key}"


@pytest.mark.asyncio
async def test_cache_unicode_values():
    """Cache Unicode Werte."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    unicode_data = {
        "german": "Hällo Wörld",
        "chinese": "你好世界",
        "arabic": "مرحبا",
        "emoji": "🚀🎯🔥",
    }

    for key, value in unicode_data.items():
        await cache.set(key, value)

    for key, value in unicode_data.items():
        assert await cache.get(key) == value


@pytest.mark.asyncio
async def test_cache_empty_values():
    """Cache leere Werte."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("empty_string", "")
    await cache.set("empty_list", [])
    await cache.set("empty_dict", {})
    await cache.set("zero", 0)
    await cache.set("false", False)

    assert await cache.get("empty_string") == ""
    assert await cache.get("empty_list") == []
    assert await cache.get("empty_dict") == {}
    assert await cache.get("zero") == 0
    assert await cache.get("false") is False
