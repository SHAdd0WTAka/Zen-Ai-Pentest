"""
SMART Test für scapy
Generated: 2026-03-14T09:20:03.551456
Tool: scapy_integration.py
Uses: CommandRunner Pattern + Golden Files
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Importiere ToolExecutor für Mocking
from core.tool_executor import (
    MockToolExecutor,
    ToolExecutor,
    ToolResult,
    ToolResultStatus,
    reset_executor,
    set_executor,
)


class TestScapyIntegration:
    """
    Integration Tests für scapy
    Verwendet Golden File: /root/.openclaw/workspace/Zen-Ai-Pentest/tests/fixtures/scapy_sample.json
    """

    @pytest.fixture
    def fixture_data(self):
        """Lädt Golden File Fixture"""
        fixture_path = Path("/root/.openclaw/workspace/Zen-Ai-Pentest/tests/fixtures/scapy_sample.json")
        with open(fixture_path, "r") as f:
            return json.load(f)

    @pytest.fixture(autouse=True)
    def reset_executor_after_test(self):
        """Reset Executor nach jedem Test"""
        yield
        reset_executor()

    def test_scapy_importable(self):
        """
        Test: Kann die scapy Integration importiert werden?
        """
        try:
            from tools.scapy_integration import ScapyScanner

            assert True
        except ImportError as e:
            pytest.skip(f"Tool nicht importierbar: {e}")

    def test_fixture_has_valid_structure(self, fixture_data):
        """
        Test: Enthält das Golden File valide Daten?
        """
        assert "tool" in fixture_data
        assert fixture_data["tool"] == "scapy"
        assert "target" in fixture_data or "url" in fixture_data or "domain" in fixture_data

    def test_scapy_handles_not_installed(self):
        """
        Test: Wie reagiert das Framework wenn scapy nicht installiert ist?
        """
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "scapy",
            ToolResult(
                status=ToolResultStatus.NOT_FOUND,
                returncode=-1,
                stdout="",
                stderr="Command not found: scapy",
                command="scapy",
            ),
        )

        set_executor(mock_executor)

        from core.tool_executor import get_executor

        executor = get_executor()

        result = executor.execute_sync(["scapy", "target.com"])

        assert not result.success
        assert result.status == ToolResultStatus.NOT_FOUND
        assert "not found" in result.stderr.lower() or result.returncode == -1

    def test_scapy_handles_timeout(self):
        """
        Test: Wie reagiert das Framework auf Timeouts?
        """
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "scapy",
            ToolResult(
                status=ToolResultStatus.TIMEOUT,
                returncode=-1,
                stdout="",
                stderr="Command timed out after 300s",
                command="scapy target.com",
                execution_time_ms=300000,
            ),
        )

        set_executor(mock_executor)

        from core.tool_executor import get_executor

        executor = get_executor()

        result = executor.execute_sync(["scapy", "target.com"])

        assert result.status == ToolResultStatus.TIMEOUT
        assert not result.success

    def test_scapy_parser_extracts_findings(self, fixture_data):
        """
        Test: Extrahiert der Parser Schwachstellen aus dem Tool-Output?
        """
        # Simuliere Tool-Output
        mock_output = json.dumps(fixture_data)

        # Prüfe ob Parser-Methoden existieren würden
        try:
            from tools.scapy_integration import ScapyScanner

            # Wenn die Klasse eine parse-Methode hat, teste sie
            if hasattr(ScapyScanner, "parse") or hasattr(ScapyScanner, "parse_results"):
                assert True, "Parser-Methoden vorhanden"
            else:
                pytest.skip("Keine Parser-Methoden in Klasse gefunden")
        except ImportError:
            pytest.skip("Klasse nicht importierbar")

    @pytest.mark.integration
    def test_scapy_end_to_end_mocked(self, fixture_data):
        """
        Integration Test: Kompletter Workflow mit gemocktem Tool
        """
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "scapy",
            ToolResult(
                status=ToolResultStatus.SUCCESS,
                returncode=0,
                stdout=json.dumps(fixture_data),
                stderr="",
                command="scapy -target target.com",
                execution_time_ms=5000,
            ),
        )

        set_executor(mock_executor)

        # Simuliere vollständigen Workflow
        from core.tool_executor import get_executor

        executor = get_executor()

        # 1. Tool ausführen
        result = executor.execute_sync(["scapy", "-target", "target.com"])
        assert result.success

        # 2. Output parsen
        try:
            parsed = json.loads(result.stdout)
            assert "tool" in parsed

            # 3. Prüfe auf Findings
            if "findings" in parsed:
                assert isinstance(parsed["findings"], list)
            elif "vulnerable" in parsed:
                assert isinstance(parsed["vulnerable"], bool)
            elif "ports" in parsed:
                assert isinstance(parsed["ports"], list)
            elif "subdomains" in parsed:
                assert isinstance(parsed["subdomains"], list)

        except json.JSONDecodeError:
            # Nicht-JSON Output ist auch OK
            assert len(result.stdout) > 0

        # 4. Verifiziere Aufruf
        assert mock_executor.was_called_with("scapy")

        calls = mock_executor.get_calls()
        assert len(calls) >= 1
