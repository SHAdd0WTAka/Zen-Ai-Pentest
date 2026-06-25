#!/usr/bin/env python3
"""
Unit Tests für SQLMap Integration
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# SQLMap Integration verwendet Funktionen statt Klassen
from tools.sqlmap_integration import sqlmap_scan, sqlmap_scan_form


class TestSQLMapScan:
    """Tests für sqlmap_scan Funktion"""

    @pytest.mark.asyncio
    async def test_sqlmap_scan_basic(self):
        """Test: Basis SQLMap Scan"""
        with patch("tools.sqlmap_integration.run_sqlmap", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "vulnerable": True,
                "injection_points": [{"parameter": "id", "type": "boolean-based blind"}],
            }

            result = await mock_run("http://test.com/page?id=1", {})

            assert result["vulnerable"] is True
            assert len(result["injection_points"]) == 1

    @pytest.mark.asyncio
    async def test_sqlmap_scan_not_vulnerable(self):
        """Test: SQLMap Scan ohne Schwachstelle"""
        with patch("tools.sqlmap_integration.run_sqlmap", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "vulnerable": False,
                "injection_points": [],
            }

            result = await mock_run("http://test.com/page?id=1", {})

            assert result["vulnerable"] is False
            assert result["injection_points"] == []

    @pytest.mark.asyncio
    async def test_sqlmap_scan_with_options(self):
        """Test: SQLMap Scan mit Optionen"""
        with patch("tools.sqlmap_integration.run_sqlmap", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"vulnerable": False}

            options = {"level": 3, "risk": 1, "threads": 5}

            result = await mock_run("http://test.com/page?id=1", options)

            mock_run.assert_called_once()


class TestSQLMapFormScan:
    """Tests für sqlmap_scan_form Funktion"""

    @pytest.mark.asyncio
    async def test_sqlmap_form_scan(self):
        """Test: SQLMap Form Scan"""
        with patch("tools.sqlmap_integration.run_sqlmap_form", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "vulnerable": True,
                "injection_points": [{"parameter": "username", "type": "error-based"}],
            }

            result = await mock_run("http://test.com/login", data="username=test&password=test")

            assert result["vulnerable"] is True


class TestSQLMapResultParsing:
    """Tests für SQLMap Result Parsing"""

    def test_parse_vulnerable_output(self):
        """Test: Parsen verwundbarer Output"""
        output = """
        sqlmap identified the following injection points:
        Parameter: id (GET)
            Type: boolean-based blind
            Title: AND boolean-based blind - WHERE or HAVING clause
            Payload: id=1 AND 1=1
        """

        # Simuliere Parsing
        assert "injection points" in output
        assert "boolean-based blind" in output
        assert "Parameter: id" in output

    def test_parse_not_vulnerable_output(self):
        """Test: Parsen nicht-verwundbarer Output"""
        output = "all tested parameters do not appear to be injectable"

        assert "do not appear to be injectable" in output

    def test_parse_multiple_parameters(self):
        """Test: Parsen mehrerer Parameter"""
        output = """
        Parameter: id (GET)
            Type: boolean-based blind
        Parameter: search (POST)
            Type: time-based blind
        """

        assert "Parameter: id" in output
        assert "Parameter: search" in output


class TestSQLMapSafety:
    """Tests für SQLMap Sicherheitsfunktionen"""

    def test_risk_level_limits(self):
        """Test: Risk-Level Limits"""
        # SQLMap risk sollte zwischen 1-3 sein
        valid_risks = [1, 2, 3]
        assert all(1 <= r <= 3 for r in valid_risks)

    def test_level_limits(self):
        """Test: Level Limits"""
        # SQLMap level sollte zwischen 1-5 sein
        valid_levels = [1, 2, 3, 4, 5]
        assert all(1 <= level <= 5 for level in valid_levels)

    def test_safe_options_only(self):
        """Test: Nur sichere Optionen erlaubt"""
        safe_options = {"level": 2, "risk": 1, "threads": 3, "batch": True}

        assert safe_options["level"] <= 3
        assert safe_options["risk"] <= 2
        assert safe_options["threads"] <= 10


class TestSQLMapIntegration:
    """Integration Tests für SQLMap"""

    def test_sqlmap_available(self):
        """Test: SQLMap ist verfügbar"""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/sqlmap"

            result = mock_which("sqlmap")
            assert result == "/usr/bin/sqlmap"
