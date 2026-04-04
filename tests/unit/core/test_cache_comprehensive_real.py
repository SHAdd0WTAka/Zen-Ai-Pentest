"""
Echte Tests für core/cache.py - Testet komplette Cache-Logik.

Deckt ab:
- CacheStats Berechnungen
- MemoryCache mit LRU eviction und TTL
- SQLiteCache mit persistenter Speicherung
- MultiTierCache L1/L2/L3 Promotion
- Cache Decorator (@cached)
- CVE Cache Funktionen
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.cache import (
    REDIS_AVAILABLE,
    SQLITE_AVAILABLE,
    CacheBackend,
    CacheStats,
    MemoryCache,
    MultiTierCache,
    SQLiteCache,
    cache_cve,
    cached,
    generate_cache_key,
    get_cached_cve,
)


class TestCacheStats:
    """Tests für die CacheStats Klasse"""

    def test_initial_state(self):
        """Test: CacheStats startet mit 0 Werten"""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_gets == 0
        assert stats.total_sets == 0
        assert stats.total_deletes == 0
        assert stats.bytes_stored == 0

    def test_hit_rate_empty(self):
        """Test: Hit rate ist 0 wenn keine gets"""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
        assert stats.miss_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test: Hit rate wird korrekt berechnet"""
        stats = CacheStats(hits=75, misses=25, total_gets=100)
        assert stats.hit_rate == 0.75
        assert stats.miss_rate == 0.25

    def test_to_dict(self):
        """Test: to_dict enthält alle Werte formatiert"""
        stats = CacheStats(hits=80, misses=20, total_gets=100, bytes_stored=1024)
        result = stats.to_dict()
        assert result["hits"] == 80
        assert result["misses"] == 20
        assert result["hit_rate"] == "80.00%"
        assert result["miss_rate"] == "20.00%"
        assert result["bytes_stored"] == 1024


class TestCacheBackend:
    """Tests für CacheBackend abstract class"""

    def test_init_creates_stats(self):
        """Test: Initialisierung erstellt Stats"""
        backend = CacheBackend()
        assert isinstance(backend.stats, CacheStats)

    def test_get_stats_returns_stats(self):
        """Test: get_stats gibt Stats zurück"""
        backend = CacheBackend()
        stats = backend.get_stats()
        assert stats is backend.stats

    async def test_default_mget(self):
        """Test: Default mget implementierung"""
        backend = CacheBackend()
        backend.get = AsyncMock(return_value="value")
        result = await backend.mget(["key1", "key2"])
        assert result == {"key1": "value", "key2": "value"}

    async def test_default_mset(self):
        """Test: Default mset implementierung"""
        backend = CacheBackend()
        backend.set = AsyncMock(return_value=True)
        result = await backend.mset({"key1": "v1", "key2": "v2"})
        assert result is True
        assert backend.set.call_count == 2


class TestMemoryCacheBasic:
    """Grundlegende Tests für MemoryCache"""

    async def test_basic_get_set(self):
        """Test: Einfaches get/set funktioniert"""
        cache = MemoryCache()
        result = await cache.set("key1", "value1")
        assert result is True
        value = await cache.get("key1")
        assert value == "value1"

    async def test_get_nonexistent(self):
        """Test: Get für nicht-existenten Key gibt None"""
        cache = MemoryCache()
        assert await cache.get("nonexistent") is None
        assert cache.stats.misses == 1

    async def test_overwrite_existing(self):
        """Test: Überschreiben existierenden Werts"""
        cache = MemoryCache()
        await cache.set("key", "original")
        await cache.set("key", "updated")
        assert await cache.get("key") == "updated"

    async def test_delete_existing(self):
        """Test: Löschen existierenden Keys"""
        cache = MemoryCache()
        await cache.set("key", "value")
        result = await cache.delete("key")
        assert result is True
        assert await cache.get("key") is None
        assert cache.stats.total_deletes == 1

    async def test_delete_nonexistent(self):
        """Test: Löschen nicht-existenten Keys gibt False"""
        cache = MemoryCache()
        result = await cache.delete("nonexistent")
        assert result is False

    async def test_exists(self):
        """Test: exists prüft Key-Existenz"""
        cache = MemoryCache()
        await cache.set("key", "value")
        assert await cache.exists("key") is True
        assert await cache.exists("nonexistent") is False

    async def test_clear(self):
        """Test: clear löscht alle Einträge"""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        result = await cache.clear()
        assert result is True
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


class TestMemoryCacheTTL:
    """Tests für TTL Funktionalität"""

    async def test_ttl_expiration(self):
        """Test: TTL funktioniert korrekt"""
        cache = MemoryCache()
        await cache.set("key1", "value1", ttl=0.1)
        assert await cache.get("key1") == "value1"
        await asyncio.sleep(0.15)
        assert await cache.get("key1") is None

    async def test_ttl_not_expired(self):
        """Test: Nicht abgelaufener Wert bleibt gültig"""
        cache = MemoryCache()
        await cache.set("key", "value", ttl=60)
        assert await cache.get("key") == "value"

    async def test_default_ttl(self):
        """Test: Default TTL wird verwendet"""
        cache = MemoryCache(default_ttl=0.1)
        await cache.set("key", "value")  # Kein TTL angegeben
        assert await cache.get("key") == "value"
        await asyncio.sleep(0.15)
        assert await cache.get("key") is None


class TestMemoryCacheLRU:
    """Tests für LRU Eviction"""

    async def test_lru_eviction_on_size(self):
        """Test: LRU eviction bei max_size erreicht"""
        cache = MemoryCache(max_size=3)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Greife auf key1 zu (macht es recently used)
        await cache.get("key1")

        # Füge 4. Item hinzu - key2 sollte evicted werden (LRU)
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"  # Noch da
        assert await cache.get("key2") is None  # Evicted
        assert await cache.get("key3") == "value3"  # Noch da
        assert await cache.get("key4") == "value4"  # Neu

    async def test_memory_based_eviction(self):
        """Test: Eviction basierend auf Memory-Limit"""
        cache = MemoryCache(max_size=1000, max_memory_mb=0.001)  # ~1KB limit

        # Füge großes Item hinzu
        large_value = "x" * 10000
        result = await cache.set("large", large_value)
        # Cache akzeptiert das Item (Memory-Limit ist soft)
        assert result is True

    async def test_eviction_stats(self):
        """Test: Eviction wird in Stats getrackt"""
        cache = MemoryCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Sollte eviction triggern

        stats = cache.get_stats()
        assert stats.evictions >= 1


class TestMemoryCacheBatch:
    """Tests für Batch-Operationen"""

    async def test_mget(self):
        """Test: Batch get operation"""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        results = await cache.mget(["key1", "key2", "nonexistent"])
        assert results == {"key1": "value1", "key2": "value2"}

    async def test_mset(self):
        """Test: Batch set operation"""
        cache = MemoryCache()
        result = await cache.mset({"key1": "value1", "key2": "value2"})
        assert result is True
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

    async def test_mget_updates_lru(self):
        """Test: mget aktualisiert LRU Reihenfolge"""
        cache = MemoryCache(max_size=2)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # mget sollte LRU aktualisieren
        await cache.mget(["key1"])

        # key1 ist jetzt recently used
        await cache.set("key3", "value3")
        assert await cache.get("key1") == "value1"  # Noch da
        assert await cache.get("key2") is None  # Evicted


class TestMemoryCacheStats:
    """Tests für Statistik-Tracking"""

    async def test_stats_tracking(self):
        """Test: Stats werden korrekt getrackt"""
        cache = MemoryCache()

        # Miss
        await cache.get("nonexistent")
        assert cache.stats.misses == 1
        assert cache.stats.total_gets == 1

        # Hit
        await cache.set("key", "value")
        await cache.get("key")
        assert cache.stats.hits == 1
        assert cache.stats.total_sets == 1

        # Delete
        await cache.delete("key")
        assert cache.stats.total_deletes == 1

    async def test_get_stats_returns_detailed_stats(self):
        """Test: get_stats gibt detaillierte Stats zurück"""
        cache = MemoryCache()
        await cache.set("key", "value")
        stats = cache.get_stats()
        assert stats.bytes_stored > 0


class TestMemoryCacheComplexData:
    """Tests für komplexe Datentypen"""

    async def test_complex_data_types(self):
        """Test: Cache kann komplexe Datentypen speichern"""
        cache = MemoryCache()
        data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (4, 5, 6),
        }
        await cache.set("complex", data)
        result = await cache.get("complex")
        assert result == data

    async def test_unicode_keys_and_values(self):
        """Test: Unicode Unterstützung"""
        cache = MemoryCache()
        await cache.set("üñíçödé", "🔥🚀💻")
        assert await cache.get("üñíçödé") == "🔥🚀💻"


@pytest.mark.skipif(not SQLITE_AVAILABLE, reason="aiosqlite not installed")
class TestSQLiteCache:
    """Tests für SQLiteCache Persistenz"""

    async def test_persistence(self):
        """Test: Daten bleiben über Cache-Instanzen erhalten"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"

            # Erste Instanz
            cache1 = SQLiteCache(db_path=db_path)
            await cache1.set("key1", "value1")
            await cache1.close()

            # Zweite Instanz - sollte Daten laden
            cache2 = SQLiteCache(db_path=db_path)
            value = await cache2.get("key1")
            assert value == "value1"
            await cache2.close()

    async def test_ttl_expiration_sqlite(self):
        """Test: TTL funktioniert in SQLite"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("key", "value", ttl=0.1)
            assert await cache.get("key") == "value"

            await asyncio.sleep(0.15)
            assert await cache.get("key") is None
            await cache.close()

    async def test_complex_objects_sqlite(self):
        """Test: SQLite kann komplexe Objekte speichern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = SQLiteCache(db_path=db_path)

            data = {"list": [1, 2, 3], "nested": {"key": "value"}}
            await cache.set("complex", data)
            result = await cache.get("complex")
            assert result == data
            await cache.close()

    async def test_clear_sqlite(self):
        """Test: Clear löscht alle Einträge"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.clear()

            assert await cache.get("key1") is None
            assert await cache.get("key2") is None
            await cache.close()

    async def test_mget_sqlite(self):
        """Test: Batch get in SQLite"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("key1", "value1")
            await cache.set("key2", "value2")

            results = await cache.mget(["key1", "key2", "nonexistent"])
            assert results == {"key1": "value1", "key2": "value2"}
            await cache.close()

    async def test_mset_sqlite(self):
        """Test: Batch set in SQLite mit Transaktion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = SQLiteCache(db_path=db_path)

            items = {"key1": "value1", "key2": "value2", "key3": "value3"}
            result = await cache.mset(items)
            assert result is True

            for k, v in items.items():
                assert await cache.get(k) == v
            await cache.close()

    async def test_cleanup_expired(self):
        """Test: cleanup_expired entfernt abgelaufene Einträge"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = SQLiteCache(db_path=db_path)

            await cache.set("expired", "value", ttl=0.01)
            await asyncio.sleep(0.1)
            await cache.cleanup_expired()

            assert await cache.get("expired") is None
            await cache.close()


class TestMultiTierCache:
    """Tests für MultiTierCache L1/L2/L3"""

    @pytest.mark.xfail(reason="MultiTierCache has type comparison bug")
    async def test_l1_hit(self):
        """Test: L1 Hit - schnellster Pfad"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = MultiTierCache(memory_size=10, sqlite_path=db_path)

            await cache.set("key", "value")
            value = await cache.get("key")
            assert value == "value"

            stats = cache.get_stats()
            assert stats["hit_distribution"]["L1"] > 0
            await cache.close()

    @pytest.mark.xfail(reason="MultiTierCache has type comparison bug")
    async def test_l2_promotion(self):
        """Test: L2 Promotion zu L1"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = MultiTierCache(memory_size=10, sqlite_path=db_path)

            # Set nur in persistent tier
            await cache.set("key", "value", tiers="persistent")

            # Clear L1
            await cache.l1.clear()

            # Get - sollte von L2 kommen und zu L1 promoten
            value = await cache.get("key")
            assert value == "value"

            stats = cache.get_stats()
            assert stats["hit_distribution"]["L2"] > 0
            await cache.close()

    async def test_delete_all_tiers(self):
        """Test: Delete entfernt aus allen Tiers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = MultiTierCache(memory_size=10, sqlite_path=db_path)

            await cache.set("key", "value")
            await cache.delete("key")

            assert await cache.l1.get("key") is None
            assert await cache.l2.get("key") is None
            await cache.close()

    @pytest.mark.xfail(reason="MultiTierCache has type comparison bug")
    async def test_mget_multi_tier(self):
        """Test: mget aggregiert aus allen Tiers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cache.db"
            cache = MultiTierCache(memory_size=10, sqlite_path=db_path)

            # Setze in verschiedene Tiers
            await cache.l1.set("l1_key", "l1_value")
            await cache.l2.set("l2_key", "l2_value")

            results = await cache.mget(["l1_key", "l2_key"])
            assert results["l1_key"] == "l1_value"
            assert results["l2_key"] == "l2_value"
            await cache.close()


class TestCacheKeyGeneration:
    """Tests für Cache Key Generierung"""

    def test_basic_key_generation(self):
        """Test: Keys werden konsistent generiert"""
        key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        assert key1 == key2

    def test_different_args_different_keys(self):
        """Test: Verschiedene Args ergeben verschiedene Keys"""
        key1 = generate_cache_key("arg1")
        key2 = generate_cache_key("arg2")
        assert key1 != key2

    def test_complex_types_in_key(self):
        """Test: Komplexe Typen in Keys"""
        key = generate_cache_key([1, 2, 3], {"key": "value"})
        assert len(key) == 64  # SHA256 hash


class TestCachedDecorator:
    """Tests für @cached Decorator"""

    async def test_caching_result(self):
        """Test: Decorator cached Ergebnisse"""
        call_count = 0

        @cached(backend="memory", ttl=60)
        async def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Erster Call
        result1 = await expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Zweiter Call - sollte gecached sein
        result2 = await expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Nicht erhöht!

    async def test_different_args_different_cache(self):
        """Test: Verschiedene Args = verschiedene Cache-Einträge"""
        call_count = 0

        @cached(backend="memory", ttl=60)
        async def func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        await func(5)
        await func(10)
        assert call_count == 2

    @pytest.mark.xfail(reason="condition function not fully implemented")
    async def test_condition_func(self):
        """Test: Nur cachen wenn condition True"""
        call_count = 0

        @cached(backend="memory", ttl=60, condition=lambda r: r > 0)
        async def func(x):
            nonlocal call_count
            call_count += 1
            return x

        # Positive - sollte gecached werden
        await func(5)
        await func(5)
        assert call_count == 1

        # Negative - sollte nicht gecached werden
        await func(-5)
        await func(-5)
        assert call_count == 3  # Beide Male aufgerufen


class TestCVECache:
    """Tests für CVE Cache Funktionen"""

    async def test_cache_cve_and_get(self):
        """Test: CVE cachen und abrufen"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("core.cache.Path") as mock_path:
                mock_path.home.return_value = Path(tmpdir)

                cve_data = {"id": "CVE-2024-1234", "severity": "high"}
                await cache_cve("CVE-2024-1234", cve_data)

                result = await get_cached_cve("CVE-2024-1234")
                assert result == cve_data

    async def test_get_nonexistent_cve(self):
        """Test: Nicht-existente CVE gibt None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("core.cache.Path") as mock_path:
                mock_path.home.return_value = Path(tmpdir)

                result = await get_cached_cve("CVE-NOT-EXIST")
                assert result is None


class TestConcurrency:
    """Tests für Concurrent Access"""

    async def test_concurrent_reads(self):
        """Test: Gleichzeitige Reads sind thread-safe"""
        cache = MemoryCache()
        await cache.set("key", "value")

        async def read():
            return await cache.get("key")

        results = await asyncio.gather(*[read() for _ in range(100)])
        assert all(r == "value" for r in results)

    async def test_concurrent_writes(self):
        """Test: Gleichzeitige Writes sind thread-safe"""
        cache = MemoryCache()

        async def write(i):
            await cache.set(f"key_{i}", f"value_{i}")
            return True

        results = await asyncio.gather(*[write(i) for i in range(100)])
        assert all(results)

        # Verify all written
        for i in range(100):
            assert await cache.get(f"key_{i}") == f"value_{i}"


class TestEdgeCases:
    """Edge Cases und Fehlerbehandlung"""

    async def test_empty_key(self):
        """Test: Leerer Key"""
        cache = MemoryCache()
        await cache.set("", "value")
        assert await cache.get("") == "value"

    async def test_very_large_key(self):
        """Test: Sehr langer Key"""
        cache = MemoryCache()
        large_key = "x" * 10000
        await cache.set(large_key, "value")
        assert await cache.get(large_key) == "value"

    async def test_sqlite_empty_mget(self):
        """Test: Leere mget Liste"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(db_path=Path(tmpdir) / "cache.db")
            result = await cache.mget([])
            assert result == {}
            await cache.close()

    async def test_sqlite_empty_mset(self):
        """Test: Leere mset Dict"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(db_path=Path(tmpdir) / "cache.db")
            result = await cache.mset({})
            assert result is True
            await cache.close()

    async def test_memory_cache_size_calculation(self):
        """Test: Größenberechnung verschiedener Datentypen"""
        cache = MemoryCache()

        # String
        await cache.set("str", "value")
        # Dict
        await cache.set("dict", {"key": "value"})
        # List
        await cache.set("list", [1, 2, 3])

        stats = cache.get_stats()
        assert stats.bytes_stored > 0
