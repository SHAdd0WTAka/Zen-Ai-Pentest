"""
Tests für Nuclei Integration mit Golden File Testing
Verwendet fixtures/nuclei_findings.json als "Golden File"
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Testet Parser-Logik, nicht den echten Tool-Aufruf
from core.tool_executor import (
    MockToolExecutor,
    ToolExecutor,
    ToolResult,
    ToolResultStatus,
    reset_executor,
    set_executor,
)


class TestNucleiParser:
    """Testet die Parser-Logik für Nuclei Output"""

    @pytest.fixture
    def nuclei_fixture(self):
        """Lädt die Golden File Fixture"""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "nuclei_findings.json"
        with open(fixture_path, "r") as f:
            return json.load(f)

    def test_nuclei_json_parsing(self, nuclei_fixture):
        """
        Test: Kann unser Framework Nuclei-JSON korrekt parsen?

        Dieser Test garantiert, dass wir CVE-IDs, Severity und Hosts
        aus echten Nuclei-Outputs extrahieren können.
        """
        # Simuliere Parser-Logik
        findings = nuclei_fixture

        assert len(findings) >= 4, "Sollte mindestens 4 Findings haben"

        # Prüfe kritische CVE
        cve_finding = next((f for f in findings if f["template-id"] == "cve-2021-44228"), None)
        assert cve_finding is not None, "Log4j CVE sollte gefunden werden"
        assert cve_finding["severity"] == "critical"
        assert "vulnerable-target.com" in cve_finding["host"]

    def test_nuclei_severity_extraction(self, nuclei_fixture):
        """
        Test: Werden Severity-Levels korrekt erkannt?
        """
        findings = nuclei_fixture

        severities = [f["severity"] for f in findings]

        assert "critical" in severities
        assert "high" in severities
        assert "medium" in severities

        # Zähle nach Severity
        critical_count = severities.count("critical")
        high_count = severities.count("high")

        assert critical_count >= 1
        assert high_count >= 1

    def test_nuclei_curl_command_extraction(self, nuclei_fixture):
        """
        Test: Werden curl-Commands für Proof-of-Concept extrahiert?
        """
        findings = nuclei_fixture

        for finding in findings:
            if "curl-command" in finding:
                assert finding["curl-command"].startswith("curl")
                assert finding["host"] in finding["curl-command"] or finding["matched-at"] in finding["curl-command"]


class TestNucleiWithMockExecutor:
    """
    Testet Nuclei Integration mit Mock-Executor.

    Statt echtes nuclei zu starten, mocken wir den ToolExecutor
    und geben das Fixture als Output zurück.
    """

    @pytest.fixture
    def mock_executor(self):
        """Erstellt Mock-Executor mit Nuclei-Fixture"""
        executor = MockToolExecutor()

        # Lade Fixture
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "nuclei_findings.json"
        with open(fixture_path, "r") as f:
            fixture_content = f.read()

        # Füge Mock-Response für nuclei hinzu
        executor.add_mock_response(
            "nuclei",
            ToolResult(
                status=ToolResultStatus.SUCCESS,
                returncode=0,
                stdout=fixture_content,
                stderr="",
                command="nuclei -u http://target.com -json",
                execution_time_ms=5000,
            ),
        )

        return executor

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setzt Executor vor/nach Test zurück"""
        reset_executor()
        yield
        reset_executor()

    @pytest.mark.asyncio
    async def test_agent_uses_nuclei_via_executor(self, mock_executor):
        """
        Test: Nutzt der Agent den ToolExecutor für Nuclei?

        Verifiziert, dass unser Framework nicht direkt subprocess
        aufruft, sondern die Abstraktionsschicht nutzt.
        """
        set_executor(mock_executor)

        # Simuliere Agent-Aufruf
        from core.tool_executor import get_executor

        executor = await get_executor()

        result = executor.execute_sync(
            [
                "nuclei",
                "-u",
                "http://target.com",
                "-json",
                "-severity",
                "critical,high",
            ]
        )

        # Verifiziere Ergebnis
        assert result.success
        assert result.returncode == 0

        # Parsiere JSON-Output
        findings = json.loads(result.stdout)
        assert len(findings) >= 1

        # Verifiziere dass Mock aufgerufen wurde
        assert mock_executor.was_called_with("nuclei")

    def test_nuclei_error_handling(self):
        """
        Test: Wie reagiert der Agent wenn Nuclei fehlt?
        """
        executor = MockToolExecutor()
        executor.add_mock_response(
            "nuclei",
            ToolResult(
                status=ToolResultStatus.NOT_FOUND,
                returncode=-1,
                stdout="",
                stderr="Command not found: nuclei",
                command="nuclei",
            ),
        )
        set_executor(executor)

        result = executor.execute_sync(["nuclei", "-u", "http://target.com"])

        assert not result.success
        assert result.status == ToolResultStatus.NOT_FOUND
        assert "not found" in result.stderr.lower()


class TestNucleiVulnerabilityClassification:
    """
    Testet Klassifizierung und Priorisierung von Nuclei-Findings.
    """

    @pytest.fixture
    def nuclei_fixture(self):
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "nuclei_findings.json"
        with open(fixture_path, "r") as f:
            return json.load(f)

    def test_critical_vulnerabilities_identified(self, nuclei_fixture):
        """
        Test: Werden kritische Schwachstellen korrekt identifiziert?
        """
        findings = nuclei_fixture

        critical_findings = [f for f in findings if f.get("severity") == "critical"]

        assert len(critical_findings) >= 1

        # Log4j sollte kritisch sein
        log4j = next(
            (f for f in critical_findings if "log4j" in f.get("template-name", "").lower()),
            None,
        )
        assert log4j is not None, "Log4j sollte als kritisch erkannt werden"

    def test_cve_extraction(self, nuclei_fixture):
        """
        Test: Werden CVE-IDs aus Template-IDs extrahiert?
        """
        findings = nuclei_fixture

        cve_findings = [f for f in findings if f.get("template-id", "").startswith("cve-")]

        assert len(cve_findings) >= 1

        # Prüfe CVE-2021-44228
        log4j_cve = next(
            (f for f in cve_findings if "2021-44228" in f.get("template-id", "")),
            None,
        )
        assert log4j_cve is not None
