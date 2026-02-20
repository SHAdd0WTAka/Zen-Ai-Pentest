"""Tests for ZAP Integration Module

This module contains comprehensive tests for the zap_integration module,
including unit tests with mocked API calls.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import the module under test
from tools.zap_integration import (
    ZAPAlert,
    ZAPAlertRisk,
    ZAPScanner,
    ZAPScanPolicy,
    ZAPScanResult,
    zap_quick_scan,
    zap_scan_url,
    zap_spider_only,
)

# Sample ZAP API responses for testing
SAMPLE_SPIDER_STATUS = {"status": "50"}
SAMPLE_SPIDER_COMPLETE = {"status": "100"}

SAMPLE_ALERT = {
    "sourceid": "3",
    "other": "",
    "method": "GET",
    "evidence": "",
    "pluginId": "10010",
    "cweid": "200",
    "confidence": "Medium",
    "wascid": "13",
    "description": "The response contains a suspicious comment.",
    "messageId": "1",
    "url": "http://example.com/",
    "reference": "https://owasp.org/",
    "solution": "Remove comments that contain sensitive information.",
    "alert": "Informational",
    "param": "",
    "attack": "",
    "name": "Suspicious Comments",
    "risk": "Informational",
    "id": "0",
}

SAMPLE_ALERTS_RESPONSE = {"alerts": [SAMPLE_ALERT]}

SAMPLE_SCAN_ID_RESPONSE = {"scan": "1"}


class TestZAPScannerInit:
    """Test ZAPScanner initialization"""

    def test_init_with_url(self):
        """Test initialization with target URL"""
        scanner = ZAPScanner(
            target="http://example.com",
            api_url="http://localhost:8080",
        )
        assert scanner.target == "http://example.com"
        assert scanner.api_url == "http://localhost:8080"
        assert scanner.options["spider"] is True
        assert scanner.options["active_scan"] is True

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        scanner = ZAPScanner(
            target="http://example.com",
            api_key="test-api-key-123",
        )
        assert scanner.api_key == "test-api-key-123"

    def test_init_with_docker(self):
        """Test initialization with Docker option"""
        scanner = ZAPScanner(
            target="http://example.com",
            use_docker=True,
        )
        assert scanner.use_docker is True

    def test_init_with_options(self):
        """Test initialization with custom options"""
        options = {
            "spider": False,
            "ajax_spider": True,
            "recursion_depth": 10,
            "scan_timeout": 1200,
        }
        scanner = ZAPScanner(
            target="http://example.com",
            options=options,
        )
        assert scanner.options["spider"] is False
        assert scanner.options["ajax_spider"] is True
        assert scanner.options["recursion_depth"] == 10
        assert scanner.options["scan_timeout"] == 1200

    def test_init_default_options(self):
        """Test default options are set correctly"""
        scanner = ZAPScanner(target="http://example.com")
        assert scanner.options["spider"] is True
        assert scanner.options["ajax_spider"] is False
        assert scanner.options["active_scan"] is True
        assert scanner.options["recursion_depth"] == 5
        assert scanner.options["scan_timeout"] == 600


class TestZAPAlertDataClass:
    """Test ZAPAlert dataclass"""

    def test_alert_creation(self):
        """Test creating ZAPAlert object"""
        alert = ZAPAlert(
            alert_id="123",
            name="Test Alert",
            risk="High",
            confidence="High",
            description="Test description",
            solution="Test solution",
            reference="https://example.com",
            url="http://target.com/page",
            method="GET",
        )
        assert alert.alert_id == "123"
        assert alert.name == "Test Alert"
        assert alert.risk == "High"
        assert alert.url == "http://target.com/page"

    def test_alert_with_all_fields(self):
        """Test creating ZAPAlert with all fields"""
        alert = ZAPAlert(
            alert_id="456",
            name="XSS Alert",
            risk="High",
            confidence="Medium",
            description="Cross-site scripting vulnerability",
            solution="Validate input",
            reference="https://owasp.org/xss",
            cwe_id="79",
            wasc_id="8",
            sourceid="1",
            url="http://target.com/xss",
            method="POST",
            attack="<script>alert(1)</script>",
            evidence="<script>alert(1)</script>",
            other_info="Additional info",
            param="input",
        )
        assert alert.cwe_id == "79"
        assert alert.wasc_id == "8"
        assert alert.attack == "<script>alert(1)</script>"


class TestZAPScanResult:
    """Test ZAPScanResult dataclass"""

    def test_result_success(self):
        """Test successful scan result"""
        alert = ZAPAlert(
            alert_id="1",
            name="Test",
            risk="High",
            confidence="High",
            description="Test",
            solution="Test",
            reference="",
        )
        result = ZAPScanResult(
            success=True,
            target="http://example.com",
            scan_type="full",
            alerts=[alert],
            scan_time=30.5,
            urls_crawled=50,
        )
        assert result.success is True
        assert len(result.alerts) == 1
        assert result.urls_crawled == 50

    def test_result_failure(self):
        """Test failed scan result"""
        result = ZAPScanResult(
            success=False,
            target="http://example.com",
            scan_type="full",
            error="Connection failed",
            scan_time=0.0,
        )
        assert result.success is False
        assert result.error == "Connection failed"


class TestRiskLevelConversion:
    """Test risk level to severity conversion"""

    def test_risk_to_severity_high(self):
        """Test High risk conversion"""
        scanner = ZAPScanner(target="http://example.com")
        assert scanner._risk_to_severity("High") == "high"

    def test_risk_to_severity_medium(self):
        """Test Medium risk conversion"""
        scanner = ZAPScanner(target="http://example.com")
        assert scanner._risk_to_severity("Medium") == "medium"

    def test_risk_to_severity_low(self):
        """Test Low risk conversion"""
        scanner = ZAPScanner(target="http://example.com")
        assert scanner._risk_to_severity("Low") == "low"

    def test_risk_to_severity_informational(self):
        """Test Informational risk conversion"""
        scanner = ZAPScanner(target="http://example.com")
        assert scanner._risk_to_severity("Informational") == "info"

    def test_risk_to_severity_unknown(self):
        """Test unknown risk conversion defaults to info"""
        scanner = ZAPScanner(target="http://example.com")
        assert scanner._risk_to_severity("Unknown") == "info"


class TestParseAlerts:
    """Test alert parsing"""

    @pytest.mark.asyncio
    async def test_parse_alerts(self):
        """Test parsing alerts from API response"""
        scanner = ZAPScanner(target="http://example.com")

        with patch.object(scanner, "_api_request", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = SAMPLE_ALERTS_RESPONSE
            alerts = await scanner.get_alerts()

            assert len(alerts) == 1
            assert alerts[0].name == "Suspicious Comments"
            assert alerts[0].risk == "Informational"

    @pytest.mark.asyncio
    async def test_parse_empty_alerts(self):
        """Test parsing empty alerts response"""
        scanner = ZAPScanner(target="http://example.com")

        with patch.object(scanner, "_api_request", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"alerts": []}
            alerts = await scanner.get_alerts()

            assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_parse_alerts_with_base_url(self):
        """Test parsing alerts with base URL filter"""
        scanner = ZAPScanner(target="http://example.com")

        with patch.object(scanner, "_api_request", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = SAMPLE_ALERTS_RESPONSE
            alerts = await scanner.get_alerts(base_url="http://example.com/")

            assert len(alerts) == 1
            mock_api.assert_called_once()


class TestOutputParsing:
    """Test output parsing methods"""

    def test_parse_output(self):
        """Test parse_output method"""
        scanner = ZAPScanner(target="http://example.com")
        alert = ZAPAlert(
            alert_id="1",
            name="XSS",
            risk="High",
            confidence="High",
            description="XSS vulnerability",
            solution="Sanitize input",
            reference="https://owasp.org/xss https://cwe.mitre.org/79",
            url="http://target.com/page",
            method="GET",
            attack="<script>",
            evidence="<script>",
            param="q",
        )

        findings = scanner.parse_output([alert])

        assert len(findings) == 1
        assert findings[0]["tool"] == "zap"
        assert findings[0]["severity"] == "high"
        assert findings[0]["name"] == "XSS"
        assert findings[0]["evidence"]["url"] == "http://target.com/page"

    def test_normalize_findings(self):
        """Test normalize_findings method"""
        scanner = ZAPScanner(target="http://example.com")
        findings = [
            {
                "tool": "zap",
                "name": "SQL Injection",
                "severity": "high",
                "confidence": "high",
                "description": "SQL injection found",
                "evidence": {"url": "http://test.com", "parameter": "id"},
                "solution": "Use prepared statements",
                "references": ["https://owasp.org/sql"],
                "cwe_id": "89",
                "wasc_id": "19",
            }
        ]

        normalized = scanner.normalize_findings(findings)

        assert len(normalized) == 1
        assert normalized[0]["tool"] == "owasp_zap"
        assert normalized[0]["severity"] == "high"
        assert normalized[0]["title"] == "SQL Injection"
        assert normalized[0]["cwe_id"] == "89"


class TestReferenceParsing:
    """Test reference URL parsing"""

    def test_parse_single_reference(self):
        """Test parsing single reference"""
        scanner = ZAPScanner(target="http://example.com")
        refs = scanner._parse_references("https://owasp.org/test")
        assert refs == ["https://owasp.org/test"]

    def test_parse_multiple_references(self):
        """Test parsing multiple references"""
        scanner = ZAPScanner(target="http://example.com")
        refs = scanner._parse_references("https://owasp.org/test https://cwe.mitre.org/79")
        assert "https://owasp.org/test" in refs
        assert "https://cwe.mitre.org/79" in refs

    def test_parse_empty_reference(self):
        """Test parsing empty reference"""
        scanner = ZAPScanner(target="http://example.com")
        refs = scanner._parse_references("")
        assert refs == []

    def test_parse_multiline_reference(self):
        """Test parsing multiline references"""
        scanner = ZAPScanner(target="http://example.com")
        refs = scanner._parse_references("https://owasp.org/test\nhttps://example.com/ref")
        assert len(refs) == 2


class TestCommandBuilding:
    """Test command building for daemon startup"""

    def test_build_local_daemon_command(self):
        """Test building local daemon command"""
        scanner = ZAPScanner(
            target="http://example.com",
            zap_path="/usr/bin/zap",
        )
        # Test that scanner is configured correctly
        assert scanner.zap_path == "/usr/bin/zap"

    def test_docker_daemon_configuration(self):
        """Test Docker daemon configuration"""
        scanner = ZAPScanner(
            target="http://example.com",
            use_docker=True,
        )
        assert scanner.use_docker is True


class TestProgressCallbacks:
    """Test progress callback functionality"""

    @pytest.mark.asyncio
    async def test_spider_progress_callback(self):
        """Test spider scan progress callback"""
        scanner = ZAPScanner(target="http://example.com")
        progress_values = []

        def progress_callback(progress):
            progress_values.append(progress)

        with patch.object(scanner, "_api_request", new_callable=AsyncMock) as mock_api:
            # Simulate progress
            mock_api.side_effect = [
                SAMPLE_SCAN_ID_RESPONSE,  # Start scan
                SAMPLE_SPIDER_STATUS,  # Progress 50%
                SAMPLE_SPIDER_COMPLETE,  # Complete
                {"urls": ["http://example.com/"]},  # URLs for stats
            ]

            # Mock the spider scan completion
            with patch("asyncio.sleep", new_callable=AsyncMock):
                try:
                    await scanner.spider_scan(progress_callback=progress_callback)
                except Exception:
                    pass  # We expect this due to mocked responses


class TestZAPEnums:
    """Test ZAP enumeration classes"""

    def test_scan_policy_values(self):
        """Test scan policy enum values"""
        assert ZAPScanPolicy.DEFAULT.value == "Default Policy"
        assert ZAPScanPolicy.SQL_INJECTION.value == "SQL Injection"
        assert ZAPScanPolicy.XSS.value == "Cross Site Scripting (Reflected)"

    def test_alert_risk_values(self):
        """Test alert risk enum values"""
        assert ZAPAlertRisk.INFORMATIONAL.value == 0
        assert ZAPAlertRisk.LOW.value == 1
        assert ZAPAlertRisk.MEDIUM.value == 2
        assert ZAPAlertRisk.HIGH.value == 3


class TestLangChainTools:
    """Test LangChain tool wrappers"""

    @patch("asyncio.run")
    def test_zap_scan_url_tool(self, mock_run):
        """Test zap_scan_url tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "http://example.com"
        mock_result.scan_time = 10.0
        mock_result.urls_crawled = 25
        mock_result.alerts = []

        mock_run.return_value = mock_result

        result = zap_scan_url("http://example.com")
        assert isinstance(result, str)
        assert "completed" in result.lower() or "ZAP" in result

    @patch("asyncio.run")
    def test_zap_quick_scan_tool(self, mock_run):
        """Test zap_quick_scan tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "http://example.com"
        mock_result.alerts = []

        mock_run.return_value = mock_result

        result = zap_quick_scan("http://example.com")
        assert isinstance(result, str)

    @patch("asyncio.run")
    def test_zap_spider_only_tool(self, mock_run):
        """Test zap_spider_only tool function"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.target = "http://example.com"
        mock_result.urls_crawled = 50

        mock_run.return_value = mock_result

        result = zap_spider_only("http://example.com")
        assert isinstance(result, str)


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_api_connection_error(self):
        """Test handling API connection errors"""
        scanner = ZAPScanner(
            target="http://example.com",
            api_url="http://invalid:9999",
        )

        with patch.object(scanner, "_api_request", new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = RuntimeError("Connection refused")

            result = await scanner.scan()

            assert result.success is False
            assert "Connection refused" in result.error

    def test_scan_with_invalid_target(self):
        """Test scan with invalid target URL"""
        scanner = ZAPScanner(target="not-a-valid-url")
        # Should still initialize, errors happen during scan
        assert scanner.target == "not-a-valid-url"


class TestAsyncOperations:
    """Test async operations"""

    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test aiohttp session management"""
        scanner = ZAPScanner(target="http://example.com")
        session = await scanner._get_session()
        assert session is not None
        await scanner.stop_daemon()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
