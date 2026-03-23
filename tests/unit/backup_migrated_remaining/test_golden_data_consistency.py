"""Golden Test 2: Data Integrity – Von API bis Cache."""

# flake8: noqa: D102

from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
class TestDataIntegrityChain:
    """Ein Test. Ein Scan. Von Start bis Cache. Alles muss konsistent sein."""

    async def test_end_to_end_data_consistency(self):
        # 1. Simuliere API Input
        scan_id = "test-scan-001"
        scan_data = {
            "scan_id": scan_id,
            "target": "test.local",
            "ports": [22, 80, 443],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 2. Cache (Schnellzugriff)
        from core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set(f"scan:{scan_id}:data", scan_data, ttl=300)

        # 3. Verifikation: Cache hat korrekte Daten
        cached = await cache.get(f"scan:{scan_id}:data")

        # 4. GOLDEN ASSERTION: Data Integrity
        assert cached is not None, "Cache ist leer!"
        assert cached["scan_id"] == scan_id, "SCAN ID MISMATCH!"
        assert cached["ports"] == [22, 80, 443], "PORTS CORRUPTED!"
        assert "timestamp" in cached, "TIMESTAMP MISSING!"

        # 5. Cleanup
        await cache.delete(f"scan:{scan_id}:data")
