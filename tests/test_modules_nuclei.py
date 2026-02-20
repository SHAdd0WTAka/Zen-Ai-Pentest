"""
Tests for Nuclei integration module

Tests NucleiIntegration functionality including:
- Initialization and setup
- Nuclei installation check
- Template updates
- Template categories
- Target scanning
- JSON output parsing
- AI analysis
- Results export
- Critical CVEs list
- Template manager
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from modules.nuclei_integration import NucleiFinding, NucleiIntegration, NucleiTemplateManager


@dataclass
class MockResponse:
    """Mock LLM response"""
    content: str


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator for testing"""
    orchestrator = MagicMock()
    orchestrator.process = AsyncMock()
    return orchestrator


@pytest.fixture
def nuclei_integration(mock_orchestrator):
    """Create a NucleiIntegration instance with mock orchestrator"""
    return NucleiIntegration(orchestrator=mock_orchestrator, nuclei_path="nuclei")


@pytest.fixture
def nuclei_integration_no_orchestrator():
    """Create a NucleiIntegration instance without orchestrator"""
    return NucleiIntegration(orchestrator=None, nuclei_path="nuclei")


class TestNucleiIntegrationInit:
    """Test NucleiIntegration initialization"""

    def test_init_with_orchestrator(self, mock_orchestrator):
        """Test initialization with orchestrator"""
        integration = NucleiIntegration(orchestrator=mock_orchestrator, nuclei_path="/usr/bin/nuclei")
        assert integration.orchestrator == mock_orchestrator
        assert integration.nuclei_path == "/usr/bin/nuclei"
        assert integration.templates_dir == "data/nuclei_templates"
        assert integration.scan_results == []

    def test_init_without_orchestrator(self):
        """Test initialization without orchestrator"""
        integration = NucleiIntegration(orchestrator=None)
        assert integration.orchestrator is None
        assert integration.nuclei_path == "nuclei"

    def test_severity_order(self):
        """Test severity order mapping"""
        integration = NucleiIntegration()
        assert integration.SEVERITY_ORDER["critical"] == 5
        assert integration.SEVERITY_ORDER["high"] == 4
        assert integration.SEVERITY_ORDER["medium"] == 3
        assert integration.SEVERITY_ORDER["low"] == 2
        assert integration.SEVERITY_ORDER["info"] == 1

    @patch("os.makedirs")
    def test_init_creates_directory(self, mock_makedirs):
        """Test that initialization creates templates directory"""
        NucleiIntegration()
        mock_makedirs.assert_called_once_with("data/nuclei_templates", exist_ok=True)


class TestCheckNucleiInstalled:
    """Test Nuclei installation check"""

    @pytest.mark.asyncio
    async def test_check_nuclei_installed_success(self, nuclei_integration):
        """Test successful installation check"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "2.9.1"

        with patch("subprocess.run", return_value=mock_result):
            result = await nuclei_integration.check_nuclei_installed()

        assert result is True

    @pytest.mark.asyncio
    async def test_check_nuclei_installed_failure(self, nuclei_integration):
        """Test installation check failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            result = await nuclei_integration.check_nuclei_installed()

        assert result is False

    @pytest.mark.asyncio
    async def test_check_nuclei_installed_not_found(self, nuclei_integration):
        """Test when nuclei is not found"""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = await nuclei_integration.check_nuclei_installed()

        assert result is False

    @pytest.mark.asyncio
    async def test_check_nuclei_installed_timeout(self, nuclei_integration):
        """Test installation check timeout"""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("nuclei", 10)):
            result = await nuclei_integration.check_nuclei_installed()

        assert result is False


class TestUpdateTemplates:
    """Test template updates"""

    @pytest.mark.asyncio
    async def test_update_templates_success(self, nuclei_integration):
        """Test successful template update"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Templates updated"

        with patch("subprocess.run", return_value=mock_result):
            result = await nuclei_integration.update_templates()

        assert result is True

    @pytest.mark.asyncio
    async def test_update_templates_failure(self, nuclei_integration):
        """Test template update failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Network error"

        with patch("subprocess.run", return_value=mock_result):
            result = await nuclei_integration.update_templates()

        assert result is False

    @pytest.mark.asyncio
    async def test_update_templates_exception(self, nuclei_integration):
        """Test template update with exception"""
        with patch("subprocess.run", side_effect=Exception("Unexpected error")):
            result = await nuclei_integration.update_templates()

        assert result is False


class TestGetTemplateCategories:
    """Test getting template categories"""

    def test_get_template_categories_structure(self, nuclei_integration):
        """Test that categories have correct structure"""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            categories = nuclei_integration.get_template_categories()

        expected_keys = [
            "cves", "vulnerabilities", "misconfiguration", "exposures",
            "technologies", "token-spray", "default-logins", "dns",
            "fuzzing", "helpers", "headless",
        ]
        assert all(key in categories for key in expected_keys)
        assert all(isinstance(categories[key], list) for key in expected_keys)

    def test_get_template_categories_from_nuclei(self, nuclei_integration):
        """Test getting categories from nuclei command"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "http/cves/2021/CVE-2021-1234.yaml\nhttp/vulnerabilities/xss.yaml"

        with patch("subprocess.run", return_value=mock_result):
            categories = nuclei_integration.get_template_categories()

        assert len(categories["cves"]) > 0
        assert "http/cves/2021/CVE-2021-1234.yaml" in categories["cves"]


class TestScanTarget:
    """Test target scanning"""

    @pytest.mark.asyncio
    async def test_scan_target_not_installed(self, nuclei_integration):
        """Test scanning when nuclei is not installed"""
        with patch.object(nuclei_integration, "check_nuclei_installed", return_value=False):
            result = await nuclei_integration.scan_target("example.com")

        assert result == []

    @pytest.mark.asyncio
    async def test_scan_target_success(self, nuclei_integration):
        """Test successful scan"""
        json_output = json.dumps({
            "info": {"id": "test-template", "name": "Test Finding", "severity": "high"},
            "host": "https://example.com",
            "matched-at": "https://example.com/path",
            "extracted-results": ["result1"],
        })

        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = AsyncMock(side_effect=[json_output.encode(), b""])
        mock_process.wait = AsyncMock(return_value=0)

        with patch.object(nuclei_integration, "check_nuclei_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                result = await nuclei_integration.scan_target("example.com")

        assert len(result) == 1
        assert result[0].template_id == "test-template"
        assert result[0].severity == "high"

    @pytest.mark.asyncio
    async def test_scan_target_with_filters(self, nuclei_integration):
        """Test scanning with severity and tag filters"""
        with patch.object(nuclei_integration, "check_nuclei_installed", return_value=True):
            mock_process = AsyncMock()
            mock_process.stdout = MagicMock()
            mock_process.stdout.readline = AsyncMock(return_value=b"")
            mock_process.wait = AsyncMock(return_value=0)

            with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
                await nuclei_integration.scan_target(
                    "example.com",
                    severity=["critical", "high"],
                    tags=["cve", "rce"],
                    templates=["custom.yaml"],
                    rate_limit=100,
                )

                # Check command was built correctly
                cmd = mock_exec.call_args[0]
                assert "-severity" in cmd
                assert "critical,high" in cmd
                assert "-tags" in cmd
                assert "cve,rce" in cmd
                assert "-t" in cmd
                assert "custom.yaml" in cmd
                assert "-rate-limit" in cmd
                assert "100" in cmd

    @pytest.mark.asyncio
    async def test_scan_target_invalid_json(self, nuclei_integration):
        """Test handling invalid JSON output"""
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = AsyncMock(side_effect=[b"invalid json", b""])
        mock_process.wait = AsyncMock(return_value=0)

        with patch.object(nuclei_integration, "check_nuclei_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                result = await nuclei_integration.scan_target("example.com")

        assert result == []


class TestParseNucleiOutput:
    """Test parsing Nuclei JSON output"""

    def test_parse_nuclei_output_success(self, nuclei_integration):
        """Test successful JSON parsing"""
        data = {
            "info": {"id": "cve-2021-1234", "name": "Test CVE", "severity": "critical"},
            "host": "https://example.com",
            "matched-at": "https://example.com/api",
            "extracted-results": ["admin:password"],
            "curl-command": "curl -X GET https://example.com/api",
            "request": "GET /api HTTP/1.1",
            "response": "HTTP/1.1 200 OK",
        }

        result = nuclei_integration._parse_nuclei_output(data)

        assert result is not None
        assert result.template_id == "cve-2021-1234"
        assert result.template_name == "Test CVE"
        assert result.severity == "critical"
        assert result.host == "https://example.com"
        assert result.curl_command == "curl -X GET https://example.com/api"

    def test_parse_nuclei_output_missing_fields(self, nuclei_integration):
        """Test parsing with missing fields"""
        data = {"info": {}}

        result = nuclei_integration._parse_nuclei_output(data)

        assert result is not None
        assert result.template_id == "unknown"
        assert result.template_name == "Unknown"
        assert result.severity == "info"

    def test_parse_nuclei_output_invalid_data(self, nuclei_integration):
        """Test parsing invalid data"""
        result = nuclei_integration._parse_nuclei_output(None)
        assert result is None


class TestScanWithAIAnalysis:
    """Test scan with AI analysis"""

    @pytest.mark.asyncio
    async def test_scan_with_ai_analysis_success(self, nuclei_integration, mock_orchestrator):
        """Test successful scan with AI analysis"""
        mock_finding = NucleiFinding(
            template_id="test-1",
            template_name="SQL Injection",
            severity="critical",
            host="https://example.com",
            matched_at="https://example.com/login",
            extract_results=["admin:admin"],
            timestamp=datetime.now().isoformat(),
        )

        mock_orchestrator.process.return_value = MockResponse(
            content="Risk assessment: Critical SQL injection found"
        )

        with patch.object(nuclei_integration, "scan_target", return_value=[mock_finding]):
            result = await nuclei_integration.scan_with_ai_analysis("example.com")

        assert "findings" in result
        assert "analysis" in result
        assert "severity_summary" in result
        assert result["findings"] == [mock_finding]
        assert "Critical SQL injection" in result["analysis"]

    @pytest.mark.asyncio
    async def test_scan_with_ai_analysis_no_findings(self, nuclei_integration):
        """Test scan with no findings"""
        with patch.object(nuclei_integration, "scan_target", return_value=[]):
            result = await nuclei_integration.scan_with_ai_analysis("example.com")

        assert result["findings"] == []
        assert result["analysis"] == "No vulnerabilities found"

    @pytest.mark.asyncio
    async def test_scan_with_ai_analysis_no_orchestrator(self, nuclei_integration_no_orchestrator):
        """Test scan without orchestrator"""
        mock_finding = NucleiFinding(
            template_id="test-1",
            template_name="Test Finding",
            severity="high",
            host="https://example.com",
            matched_at="https://example.com/path",
            extract_results=[],
            timestamp=datetime.now().isoformat(),
        )

        with patch.object(nuclei_integration_no_orchestrator, "scan_target", return_value=[mock_finding]):
            result = await nuclei_integration_no_orchestrator.scan_with_ai_analysis("example.com")

        assert "LLM analysis not available" in result["analysis"]


class TestGetSeveritySummary:
    """Test severity summary"""

    def test_get_severity_summary(self, nuclei_integration):
        """Test getting severity summary"""
        findings = [
            NucleiFinding("1", "F1", "critical", "h1", "m1", [], ""),
            NucleiFinding("2", "F2", "critical", "h2", "m2", [], ""),
            NucleiFinding("3", "F3", "high", "h3", "m3", [], ""),
            NucleiFinding("4", "F4", "medium", "h4", "m4", [], ""),
            NucleiFinding("5", "F5", "low", "h5", "m5", [], ""),
            NucleiFinding("6", "F6", "info", "h6", "m6", [], ""),
            NucleiFinding("7", "F7", "unknown", "h7", "m7", [], ""),
        ]

        summary = nuclei_integration._get_severity_summary(findings)

        assert summary["critical"] == 2
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 1
        assert summary["info"] == 1


class TestExportResults:
    """Test results export"""

    def test_export_results_default_filename(self, nuclei_integration):
        """Test export with default filename"""
        findings = [
            NucleiFinding("1", "Test", "high", "example.com", "/path", ["data"], "2024-01-01T00:00:00"),
        ]

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs"):
                with patch("json.dump") as mock_json_dump:
                    result = nuclei_integration.export_results(findings)

        assert "logs/nuclei_scan_" in result
        assert result.endswith(".json")

    def test_export_results_custom_filename(self, nuclei_integration):
        """Test export with custom filename"""
        findings = []

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                result = nuclei_integration.export_results(findings, "custom.json")

        assert result == "custom.json"
        mock_file.assert_called_once_with("custom.json", "w")


class TestGetCriticalCVEs:
    """Test getting critical CVEs list"""

    def test_get_critical_cves_structure(self, nuclei_integration):
        """Test that critical CVEs have correct structure"""
        cves = nuclei_integration.get_critical_cves()

        assert isinstance(cves, list)
        assert len(cves) > 0

        for cve in cves:
            assert "id" in cve
            assert "name" in cve
            assert "severity" in cve
            assert cve["id"].startswith("CVE-")

    def test_get_critical_cves_contains_log4shell(self, nuclei_integration):
        """Test that Log4Shell is in the list"""
        cves = nuclei_integration.get_critical_cves()

        cve_ids = [cve["id"] for cve in cves]
        assert "CVE-2021-44228" in cve_ids  # Log4Shell

    def test_get_critical_cves_contains_spring4shell(self, nuclei_integration):
        """Test that Spring4Shell is in the list"""
        cves = nuclei_integration.get_critical_cves()

        cve_ids = [cve["id"] for cve in cves]
        assert "CVE-2022-22965" in cve_ids  # Spring4Shell


class TestNucleiTemplateManager:
    """Test NucleiTemplateManager"""

    def test_init_creates_directory(self):
        """Test that initialization creates templates directory"""
        with patch("os.makedirs") as mock_makedirs:
            manager = NucleiTemplateManager("/custom/templates")
            mock_makedirs.assert_called_once_with("/custom/templates", exist_ok=True)

    @patch("yaml.dump")
    @patch("builtins.open", mock_open())
    def test_create_template(self, mock_yaml_dump):
        """Test creating a template"""
        manager = NucleiTemplateManager("/tmp/templates")

        request = {"method": "GET", "path": ["/test"], "headers": {}}
        matchers = [{"type": "word", "words": ["test"]}]

        result = manager.create_template(
            template_id="custom-test",
            name="Custom Test Template",
            severity="high",
            request=request,
            matchers=matchers,
            description="Test template description",
        )

        assert result.endswith("custom-test.yaml")
        assert "/tmp/templates" in result or "\\tmp\\templates" in result
        mock_yaml_dump.assert_called_once()

    def test_list_templates(self):
        """Test listing templates"""
        manager = NucleiTemplateManager("/tmp/templates")

        with patch("os.listdir", return_value=["template1.yaml", "template2.yml", "other.txt"]):
            result = manager.list_templates()

        assert len(result) == 2
        assert "template1.yaml" in [os.path.basename(p) for p in result]
        assert "template2.yml" in [os.path.basename(p) for p in result]

    def test_list_templates_empty(self):
        """Test listing templates when directory is empty"""
        manager = NucleiTemplateManager("/tmp/templates")

        with patch("os.listdir", return_value=[]):
            result = manager.list_templates()

        assert result == []


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_scan_target_exception(self, nuclei_integration):
        """Test scan with exception"""
        with patch.object(nuclei_integration, "check_nuclei_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", side_effect=Exception("Process error")):
                result = await nuclei_integration.scan_target("example.com")

        assert result == []

    def test_parse_nuclei_output_exception(self, nuclei_integration):
        """Test parsing with exception"""
        # Pass data that will cause an exception during parsing
        result = nuclei_integration._parse_nuclei_output({"info": None})
        assert result is None

    @pytest.mark.asyncio
    async def test_update_templates_timeout(self, nuclei_integration):
        """Test template update timeout"""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("nuclei", 300)):
            result = await nuclei_integration.update_templates()

        assert result is False


# Import subprocess for exception testing
import subprocess
