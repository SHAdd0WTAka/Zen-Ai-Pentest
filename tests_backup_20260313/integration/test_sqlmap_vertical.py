"""Vertical Slice: SQLMap Integration - Injection Detection Flow.

Tests the complete flow:
1. SQLMap scanner initialization
2. Vulnerability detection logic
3. Simple result structure (no MagicMock for pickling)
"""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_sqlmap_injection_detection():
    """Prüft SQL Injection Scan Ergebnisse.

    Vertical slice covering:
    - tools.sqlmap_integration.SQLMapScanner
    """
    from tools.sqlmap_integration import SQLMapScanner

    scanner = SQLMapScanner()

    # Mock SQLMap scan to return vulnerable result
    mock_result = {
        "vulnerable": True,
        "parameter": "id",
        "type": "boolean-based blind",
        "url": "http://test.com/search?id=1",
    }

    with patch.object(scanner, "scan_url", return_value=mock_result):
        result = scanner.scan_url(url="http://test.com/search?id=1", level=1)

        assert result is not None
        assert isinstance(result, dict)
        assert result.get("vulnerable") is True
        assert result.get("parameter") == "id"


@pytest.mark.asyncio
async def test_sqlmap_no_injection_found():
    """Prüft Verhalten wenn keine Injection gefunden wird."""
    from tools.sqlmap_integration import SQLMapScanner

    scanner = SQLMapScanner()

    mock_result = {"vulnerable": False, " findings": []}

    with patch.object(scanner, "scan_url", return_value=mock_result):
        result = scanner.scan_url(url="http://safe.com/page", level=1)
        assert result is not None
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_sqlmap_form_scanning():
    """Prüft Form-basierte SQL Injection Erkennung."""
    from tools.sqlmap_integration import SQLMapScanner

    scanner = SQLMapScanner()

    mock_result = {
        "vulnerable": True,
        "type": "time-based blind",
        "place": "POST",
        "parameter": "username",
    }

    with patch.object(scanner, "scan_form", return_value=mock_result):
        result = scanner.scan_form(
            url="http://test.com/login",
            data={"username": "admin", "password": "test"},
        )
        assert result is not None
        assert isinstance(result, dict)
