"""Vertical Slice 6: Core - Cache, Config, State."""

import asyncio

import pytest


@pytest.mark.asyncio
async def test_memory_cache_basic():
    """MemoryCache set, get, delete."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("key1", "value1", ttl=60)
    result = await cache.get("key1")
    assert result == "value1"

    await cache.delete("key1")
    deleted = await cache.get("key1")
    assert deleted is None


@pytest.mark.asyncio
async def test_memory_cache_ttl_expiration():
    """Cache TTL Ablauf testen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("temp", "data", ttl=0.1)
    assert await cache.get("temp") == "data"

    await asyncio.sleep(0.15)
    expired = await cache.get("temp")
    assert expired is None


@pytest.mark.asyncio
async def test_cache_stats_tracking():
    """Cache Statistiken prüfen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    await cache.set("stat_key", "stat_value")
    _ = await cache.get("stat_key")
    _ = await cache.get("stat_key")
    _ = await cache.get("missing_key")

    stats = cache.get_stats()
    assert stats.hits >= 2
    assert stats.misses >= 1


def test_severity_enum_values():
    """Severity Enum alle Werte."""
    from database.models import Severity

    assert Severity.CRITICAL == "critical"
    assert Severity.HIGH == "high"
    assert Severity.MEDIUM == "medium"
    assert Severity.LOW == "low"
    assert Severity.INFO == "info"

    severities = [s.value for s in Severity]
    assert len(severities) == 5
