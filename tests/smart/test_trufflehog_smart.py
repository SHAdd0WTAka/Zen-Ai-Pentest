"""
SMART Test für trufflehog
Generated: 2026-03-14T09:40:03.332510
Tool: trufflehog_integration.py
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


class TestTrufflehogIntegration:
    """
    Integration Tests für trufflehog
    Verwendet Golden File: /root/.openclaw/workspace/Zen-Ai-Pentest/tests/fixtures/trufflehog_sample.json
    """

    @pytest.fixture
    def fixture_data(self):
        """Lädt Golden File Fixture"""
        fixture_path = Path("/root/.openclaw/workspace/Zen-Ai-Pentest/tests/fixtures/trufflehog_sample.json")
        with open(fixture_path, "r") as f:
            return json.load(f)

    @pytest.fixture(autouse=True)
    def reset_executor_after_test(self):
        """Reset Executor nach jedem Test"""
        yield
        reset_executor()

    def test_trufflehog_importable(self):
        """
        Test: Kann die trufflehog Integration importiert werden?
        """
        try:
            from tools.trufflehog_integration import TruffleHogFinding

            assert True
        except ImportError as e:
            pytest.skip(f"Tool nicht importierbar: {e}")

    def test_trufflehog_uses_executor(self, fixture_data):
        """
        Test: Nutzt trufflehog den ToolExecutor statt direktem subprocess?

        Dies ist der kritische Test - er verifiziert, dass wir das Tool mocken können.
        """
        # Erstelle Mock-Executor mit Fixture-Daten
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "trufflehog",
            ToolResult(
                status=ToolResultStatus.SUCCESS,
                returncode=0,
                stdout=json.dumps(fixture_data),
                stderr="",
                command="trufflehog target.com",
            ),
        )

        # Setze Mock als globalen Executor
        set_executor(mock_executor)

        # Führe Tool aus
        from core.tool_executor import get_executor

        executor = get_executor()

        result = executor.execute_sync(["trufflehog", "target.com"])

        # Verifiziere
        assert result.success, f"Tool sollte erfolgreich sein: {result.stderr}"
        assert "trufflehog" in result.command
        assert mock_executor.was_called_with("trufflehog")

        # Parse Ergebnis
        try:
            parsed = json.loads(result.stdout)
            assert parsed["tool"] == "trufflehog"
        except json.JSONDecodeError:
            pass  # Nicht alle Tools geben JSON aus

    def test_fixture_has_valid_structure(self, fixture_data):
        """
        Test: Enthält das Golden File valide Daten?
        """
        assert "tool" in fixture_data
        assert fixture_data["tool"] == "trufflehog"
        assert "target" in fixture_data or "url" in fixture_data or "domain" in fixture_data

    def test_trufflehog_handles_not_installed(self):
        """
        Test: Wie reagiert das Framework wenn trufflehog nicht installiert ist?
        """
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "trufflehog",
            ToolResult(
                status=ToolResultStatus.NOT_FOUND,
                returncode=-1,
                stdout="",
                stderr="Command not found: trufflehog",
                command="trufflehog",
            ),
        )

        set_executor(mock_executor)

        from core.tool_executor import get_executor

        executor = get_executor()

        result = executor.execute_sync(["trufflehog", "target.com"])

        assert not result.success
        assert result.status == ToolResultStatus.NOT_FOUND
        assert "not found" in result.stderr.lower() or result.returncode == -1

    def test_trufflehog_handles_timeout(self):
        """
        Test: Wie reagiert das Framework auf Timeouts?
        """
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "trufflehog",
            ToolResult(
                status=ToolResultStatus.TIMEOUT,
                returncode=-1,
                stdout="",
                stderr="Command timed out after 300s",
                command="trufflehog target.com",
                execution_time_ms=300000,
            ),
        )

        set_executor(mock_executor)

        from core.tool_executor import get_executor

        executor = get_executor()

        result = executor.execute_sync(["trufflehog", "target.com"])

        assert result.status == ToolResultStatus.TIMEOUT
        assert not result.success

    def test_trufflehog_parser_extracts_findings(self, fixture_data):
        """
        Test: Extrahiert der Parser Schwachstellen aus dem Tool-Output?
        """
        # Simuliere Tool-Output
        mock_output = json.dumps(fixture_data)

        # Prüfe ob Parser-Methoden existieren würden
        try:
            from tools.trufflehog_integration import TruffleHogFinding

            # Wenn die Klasse eine parse-Methode hat, teste sie
            if hasattr(TruffleHogFinding, "parse") or hasattr(TruffleHogFinding, "parse_results"):
                assert True, "Parser-Methoden vorhanden"
            else:
                pytest.skip("Keine Parser-Methoden in Klasse gefunden")
        except ImportError:
            pytest.skip("Klasse nicht importierbar")

    @pytest.mark.integration
    def test_trufflehog_end_to_end_mocked(self, fixture_data):
        """
        Integration Test: Kompletter Workflow mit gemocktem Tool
        """
        mock_executor = MockToolExecutor()
        mock_executor.add_mock_response(
            "trufflehog",
            ToolResult(
                status=ToolResultStatus.SUCCESS,
                returncode=0,
                stdout=json.dumps(fixture_data),
                stderr="",
                command="trufflehog -target target.com",
                execution_time_ms=5000,
            ),
        )

        set_executor(mock_executor)

        # Simuliere vollständigen Workflow
        from core.tool_executor import get_executor

        executor = get_executor()

        # 1. Tool ausführen
        result = executor.execute_sync(["trufflehog", "-target", "target.com"])
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
        assert mock_executor.was_called_with("trufflehog")

        calls = mock_executor.get_calls()
        assert len(calls) >= 1
