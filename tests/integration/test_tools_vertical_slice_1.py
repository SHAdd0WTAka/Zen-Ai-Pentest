"""Vertical Slice 4: Tools Integration - Nmap & Results."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_nmap_result_parsing():
    """Nmap XML Parsing testen."""
    from tools.nmap_integration import NmapResult

    # Mock Result erstellen
    result = NmapResult(
        success=True,
        hosts=[
            {
                "address": "192.168.1.1",
                "ports": [
                    {
                        "portid": "22",
                        "state": "open",
                        "service": {"name": "ssh"},
                    },
                    {
                        "portid": "80",
                        "state": "open",
                        "service": {"name": "http"},
                    },
                ],
            }
        ],
        command="nmap -p 22,80 192.168.1.1",
        scan_time=1.5,
        error=None,
        raw_xml="<xml>test</xml>",
        summary={"total_hosts": 1, "up_hosts": 1, "open_ports": 2},
    )

    # Assertions
    assert result.success is True
    assert len(result.hosts) == 1
    assert result.hosts[0]["address"] == "192.168.1.1"
    assert len(result.hosts[0]["ports"]) == 2


def test_nmap_scanner_initialization():
    """NmapScanner Initialisierung testen."""
    from tools.nmap_integration import NmapScanner

    with patch.object(NmapScanner, "_validate_nmap_path", return_value="/usr/bin/nmap"):
        scanner = NmapScanner(
            target="scanme.nmap.org",
            options={"ports": "22,80,443", "timing": 3},
        )

        # Scanner hat Targets
        assert "scanme.nmap.org" in scanner.targets
        # Options gesetzt
        assert scanner.options.get("ports") == "22,80,443"


def test_cache_integration_with_scan():
    """Cache mit Scan Results testen."""
    from core.cache import MemoryCache

    cache = MemoryCache()

    # Scan Ergebnis cachen
    scan_result = {
        "target": "test.com",
        "open_ports": [80, 443],
        "timestamp": "2024-01-01T00:00:00",
    }

    # In Cache speichern
    import asyncio

    asyncio.run(cache.set("scan:test.com", scan_result, ttl=3600))

    # Aus Cache lesen
    cached = asyncio.run(cache.get("scan:test.com"))

    assert cached is not None
    assert cached["target"] == "test.com"
    assert 80 in cached["open_ports"]
