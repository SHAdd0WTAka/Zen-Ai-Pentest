"""
Tests for vulnerability scanner module

Tests VulnScannerModule functionality including:
- Vulnerability dataclass
- Nmap output analysis
- Web header analysis
- Web page analysis
- CVE database checks
- SSL/TLS analysis
- Vulnerability parsing
- Severity sorting and summary
"""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.vuln_scanner import VulnScannerModule, Vulnerability


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
def vuln_scanner(mock_orchestrator):
    """Create a VulnScannerModule instance with mock orchestrator"""
    return VulnScannerModule(orchestrator=mock_orchestrator)


class TestVulnerabilityDataclass:
    """Test Vulnerability dataclass"""

    def test_vulnerability_creation(self):
        """Test creating a Vulnerability object"""
        vuln = Vulnerability(
            name="SQL Injection",
            severity="High",
            description="SQL injection vulnerability in login form",
            evidence="' OR 1=1 --",
            remediation="Use parameterized queries",
            cvss_score=8.5,
            cve_ids=["CVE-2021-1234"],
        )
        assert vuln.name == "SQL Injection"
        assert vuln.severity == "High"
        assert vuln.cvss_score == 8.5
        assert vuln.cve_ids == ["CVE-2021-1234"]

    def test_vulnerability_defaults(self):
        """Test Vulnerability with default values"""
        vuln = Vulnerability(
            name="Info Disclosure",
            severity="Low",
            description="Server version exposed",
            evidence="Server: nginx/1.18.0",
            remediation="Hide server version",
        )
        assert vuln.cvss_score is None
        assert vuln.cve_ids is None


class TestVulnScannerInit:
    """Test VulnScannerModule initialization"""

    def test_init_with_orchestrator(self, mock_orchestrator):
        """Test initialization with orchestrator"""
        scanner = VulnScannerModule(orchestrator=mock_orchestrator)
        assert scanner.orchestrator == mock_orchestrator
        assert scanner.vulnerabilities == []

    def test_init_without_orchestrator(self):
        """Test initialization without orchestrator"""
        scanner = VulnScannerModule(orchestrator=None)
        assert scanner.orchestrator is None
        assert scanner.vulnerabilities == []

    def test_severity_order(self, mock_orchestrator):
        """Test severity order mapping"""
        scanner = VulnScannerModule(orchestrator=mock_orchestrator)
        assert scanner.SEVERITY_ORDER["Critical"] == 5
        assert scanner.SEVERITY_ORDER["High"] == 4
        assert scanner.SEVERITY_ORDER["Medium"] == 3
        assert scanner.SEVERITY_ORDER["Low"] == 2
        assert scanner.SEVERITY_ORDER["Info"] == 1


class TestAnalyzeNmapOutput:
    """Test nmap output analysis"""

    @pytest.mark.asyncio
    async def test_analyze_nmap_output_success(self, vuln_scanner, mock_orchestrator):
        """Test successful nmap output analysis"""
        mock_orchestrator.process.return_value = MockResponse(
            content="""
[VULN]
Name: Open SSH Port
Severity: Medium
Description: SSH service is exposed to the internet
Evidence: Port 22/tcp open
Remediation: Restrict SSH access with firewall rules
CVE: CVE-2018-15473
[/VULN]

[VULN]
Name: Outdated Apache
Severity: High
Description: Apache version 2.4.29 has known vulnerabilities
Evidence: Apache/2.4.29
Remediation: Update to latest version
CVE: CVE-2021-44790
[/VULN]
"""
        )

        nmap_output = "22/tcp open ssh\n80/tcp open http Apache httpd 2.4.29"
        result = await vuln_scanner.analyze_nmap_output(nmap_output)

        assert len(result) == 2
        assert result[0].name == "Open SSH Port"
        assert result[0].severity == "Medium"
        assert result[1].name == "Outdated Apache"
        assert result[1].severity == "High"
        mock_orchestrator.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_nmap_output_empty(self, vuln_scanner, mock_orchestrator):
        """Test nmap output analysis with no vulnerabilities"""
        mock_orchestrator.process.return_value = MockResponse(content="No vulnerabilities found")

        result = await vuln_scanner.analyze_nmap_output("Nothing interesting")
        assert result == []

    @pytest.mark.asyncio
    async def test_analyze_nmap_output_long_truncation(self, vuln_scanner, mock_orchestrator):
        """Test that long nmap output is truncated"""
        mock_orchestrator.process.return_value = MockResponse(content="Analysis complete")

        long_output = "A" * 5000
        await vuln_scanner.analyze_nmap_output(long_output)

        # Check that the prompt was truncated
        call_args = mock_orchestrator.process.call_args[0][0]
        assert len(call_args) < 5000


class TestAnalyzeWebHeaders:
    """Test web header analysis"""

    @pytest.mark.asyncio
    async def test_analyze_web_headers_success(self, vuln_scanner, mock_orchestrator):
        """Test successful header analysis"""
        mock_orchestrator.process.return_value = MockResponse(
            content="""
[VULN]
Name: Missing HSTS Header
Severity: Medium
Description: HTTP Strict Transport Security header is missing
Evidence: No Strict-Transport-Security header found
Remediation: Add HSTS header to all responses
[/VULN]

[VULN]
Name: X-Frame-Options Missing
Severity: Low
Description: Clickjacking protection not enabled
Evidence: No X-Frame-Options header
Remediation: Add X-Frame-Options: DENY or SAMEORIGIN
[/VULN]
"""
        )

        headers = {
            "Server": "nginx/1.18.0",
            "Content-Type": "text/html",
        }
        result = await vuln_scanner.analyze_web_headers(headers, "https://example.com")

        assert len(result) == 2
        assert result[0].name == "Missing HSTS Header"
        assert result[1].name == "X-Frame-Options Missing"

    @pytest.mark.asyncio
    async def test_analyze_web_headers_empty(self, vuln_scanner, mock_orchestrator):
        """Test header analysis with empty headers"""
        mock_orchestrator.process.return_value = MockResponse(content="No issues found")

        result = await vuln_scanner.analyze_web_headers({}, "https://example.com")
        assert result == []


class TestAnalyzeWebPage:
    """Test web page content analysis"""

    @pytest.mark.asyncio
    async def test_analyze_web_page_success(self, vuln_scanner, mock_orchestrator):
        """Test successful web page analysis"""
        mock_orchestrator.process.return_value = MockResponse(
            content="""
[VULN]
Name: Missing CSRF Token
Severity: High
Description: Form submission lacks CSRF protection
Evidence: <form action="/login" method="POST">
Remediation: Add CSRF tokens to all forms
[/VULN]
"""
        )

        html = """
<html>
<body>
<form action="/login" method="POST">
    <input type="text" name="username">
    <input type="password" name="password">
</form>
<script>var api_key = "secret123";</script>
<!-- TODO: Remove debug code before production -->
</body>
</html>
"""
        result = await vuln_scanner.analyze_web_page(html, "https://example.com")

        assert len(result) == 1
        assert result[0].name == "Missing CSRF Token"
        assert result[0].severity == "High"

    @pytest.mark.asyncio
    async def test_analyze_web_page_no_forms(self, vuln_scanner, mock_orchestrator):
        """Test web page analysis with no forms"""
        mock_orchestrator.process.return_value = MockResponse(content="No vulnerabilities found")

        html = "<html><body><h1>Hello World</h1></body></html>"
        result = await vuln_scanner.analyze_web_page(html, "https://example.com")
        assert result == []


class TestCheckCVEDatabase:
    """Test CVE database checks"""

    @pytest.mark.asyncio
    async def test_check_cve_database_success(self, vuln_scanner, mock_orchestrator):
        """Test successful CVE lookup"""
        mock_orchestrator.process.return_value = MockResponse(
            content="""
CVE-2021-44790: Apache HTTP Server buffer overflow
CVE-2021-42013: Apache HTTP Server path traversal
CVE-2021-41773: Apache HTTP Server path traversal
"""
        )

        result = await vuln_scanner.check_cve_database("apache", "2.4.49")

        assert len(result) == 3
        assert all("apache" in vuln.name.lower() for vuln in result)
        assert all(vuln.cve_ids for vuln in result)

    @pytest.mark.asyncio
    async def test_check_cve_database_no_cves(self, vuln_scanner, mock_orchestrator):
        """Test CVE lookup with no results"""
        mock_orchestrator.process.return_value = MockResponse(content="No known CVEs")

        result = await vuln_scanner.check_cve_database("unknown-service", "1.0")
        assert result == []

    @pytest.mark.asyncio
    async def test_check_cve_database_limit(self, vuln_scanner, mock_orchestrator):
        """Test that CVE results are limited to 5"""
        mock_orchestrator.process.return_value = MockResponse(
            content="\n".join([f"CVE-2021-{1000 + i}" for i in range(10)])
        )

        result = await vuln_scanner.check_cve_database("apache", "2.4.49")
        assert len(result) == 5  # Should be limited to 5


class TestSSLTLSAnalysis:
    """Test SSL/TLS analysis"""

    @pytest.mark.asyncio
    async def test_ssl_tls_analysis_success(self, vuln_scanner, mock_orchestrator):
        """Test successful SSL/TLS analysis"""
        mock_orchestrator.process.return_value = MockResponse(
            content="""
[VULN]
Name: Weak Cipher Suite
Severity: Medium
Description: TLS 1.0/1.1 with weak ciphers enabled
Evidence: TLS_RSA_WITH_AES_128_CBC_SHA
Remediation: Disable TLS 1.0/1.1 and weak ciphers
[/VULN]

[VULN]
Name: Expiring Certificate
Severity: High
Description: Certificate expires in 7 days
Evidence: Not After: 2024-01-01
Remediation: Renew certificate immediately
[/VULN]
"""
        )

        cert_info = "Certificate chain\nTLS 1.2 enabled\nTLS_RSA_WITH_AES_128_CBC_SHA"
        result = await vuln_scanner.ssl_tls_analysis(cert_info)

        assert len(result) == 2
        assert result[1].name == "Expiring Certificate"
        assert result[1].severity == "High"


class TestParseVulnerabilities:
    """Test vulnerability parsing"""

    def test_parse_vulnerabilities_with_blocks(self, vuln_scanner):
        """Test parsing [VULN] blocks"""
        content = """
[VULN]
Name: Test Vulnerability
Severity: High
Description: This is a test
Evidence: Test evidence
Remediation: Fix it
[/VULN]
"""
        result = vuln_scanner._parse_vulnerabilities(content)

        assert len(result) == 1
        assert result[0].name == "Test Vulnerability"
        assert result[0].severity == "High"

    def test_parse_vulnerabilities_alternate_format(self, vuln_scanner):
        """Test parsing alternate format (sections with keywords)"""
        content = """
Vulnerability: SQL Injection
Severity: Critical
Description: SQLi in login form

Vulnerability: XSS
Severity: Medium
Description: Stored XSS in comments
"""
        result = vuln_scanner._parse_vulnerabilities(content)

        assert len(result) == 2

    def test_parse_vulnerabilities_invalid_severity(self, vuln_scanner):
        """Test that invalid severity defaults to Info"""
        content = """
[VULN]
Name: Test Vuln
Severity: InvalidSeverity
Description: Test description
Evidence: Test evidence
Remediation: Fix it
[/VULN]
"""
        result = vuln_scanner._parse_vulnerabilities(content)

        assert result[0].severity == "Info"

    def test_parse_vulnerabilities_missing_fields(self, vuln_scanner):
        """Test parsing with missing fields"""
        content = """
[VULN]
Name: Minimal Vuln
[/VULN]
"""
        result = vuln_scanner._parse_vulnerabilities(content)

        assert len(result) == 1
        assert result[0].name == "Minimal Vuln"
        assert result[0].severity == "Info"
        assert "Name: Minimal Vuln" in result[0].description


class TestCreateVulnFromText:
    """Test creating vulnerability from text"""

    def test_create_vuln_from_text_complete(self, vuln_scanner):
        """Test creating vuln from complete text"""
        text = """
Name: SQL Injection
Severity: Critical
Description: SQL injection vulnerability
Evidence: ' OR 1=1
Remediation: Use parameterized queries
CVE: CVE-2021-1234, CVE-2021-5678
"""
        result = vuln_scanner._create_vuln_from_text(text)

        assert result.name == "SQL Injection"
        assert result.severity == "Critical"
        assert result.cve_ids == ["CVE-2021-1234", "CVE-2021-5678"]

    def test_create_vuln_from_text_partial(self, vuln_scanner):
        """Test creating vuln from partial text"""
        text = "Some random text without proper format"
        result = vuln_scanner._create_vuln_from_text(text)

        assert result.name == "Unknown Vulnerability"
        assert result.severity == "Info"


class TestSeveritySummary:
    """Test severity summary functionality"""

    def test_get_severity_summary(self, vuln_scanner):
        """Test getting severity summary"""
        vulnerabilities = [
            Vulnerability(name="Vuln1", severity="Critical", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Vuln2", severity="Critical", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Vuln3", severity="High", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Vuln4", severity="Medium", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Vuln5", severity="Low", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Vuln6", severity="Info", description="D", evidence="E", remediation="R"),
        ]

        summary = vuln_scanner.get_severity_summary(vulnerabilities)

        assert summary["Critical"] == 2
        assert summary["High"] == 1
        assert summary["Medium"] == 1
        assert summary["Low"] == 1
        assert summary["Info"] == 1

    def test_get_severity_summary_empty(self, vuln_scanner):
        """Test severity summary with empty list"""
        summary = vuln_scanner.get_severity_summary([])

        assert all(count == 0 for count in summary.values())


class TestSortBySeverity:
    """Test sorting by severity"""

    def test_sort_by_severity(self, vuln_scanner):
        """Test sorting vulnerabilities by severity"""
        vulnerabilities = [
            Vulnerability(name="Low1", severity="Low", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Critical1", severity="Critical", description="D", evidence="E", remediation="R"),
            Vulnerability(name="High1", severity="High", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Info1", severity="Info", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Medium1", severity="Medium", description="D", evidence="E", remediation="R"),
        ]

        sorted_vulns = vuln_scanner.sort_by_severity(vulnerabilities)

        assert sorted_vulns[0].name == "Critical1"
        assert sorted_vulns[1].name == "High1"
        assert sorted_vulns[2].name == "Medium1"
        assert sorted_vulns[3].name == "Low1"
        assert sorted_vulns[4].name == "Info1"

    def test_sort_by_severity_unknown(self, vuln_scanner):
        """Test sorting with unknown severity"""
        vulnerabilities = [
            Vulnerability(name="Unknown", severity="Unknown", description="D", evidence="E", remediation="R"),
            Vulnerability(name="Critical", severity="Critical", description="D", evidence="E", remediation="R"),
        ]

        sorted_vulns = vuln_scanner.sort_by_severity(vulnerabilities)

        # Unknown should be treated as lowest priority
        assert sorted_vulns[0].name == "Critical"
        assert sorted_vulns[1].name == "Unknown"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_parse_vulnerabilities_empty_content(self, vuln_scanner):
        """Test parsing empty content"""
        result = vuln_scanner._parse_vulnerabilities("")
        assert result == []

    def test_parse_vulnerabilities_case_insensitive_severity(self, vuln_scanner):
        """Test case insensitive severity parsing"""
        content = """
[VULN]
Name: Test
Severity: critical
Description: Test
Evidence: Test
Remediation: Fix
[/VULN]
"""
        result = vuln_scanner._parse_vulnerabilities(content)
        assert result[0].severity == "Critical"

    @pytest.mark.asyncio
    async def test_analyze_nmap_output_no_orchestrator(self):
        """Test nmap analysis without orchestrator - should raise or return empty"""
        scanner = VulnScannerModule(orchestrator=None)
        # Module requires orchestrator, will raise AttributeError
        with pytest.raises(AttributeError):
            await scanner.analyze_nmap_output("test output")

    @pytest.mark.asyncio
    async def test_check_cve_database_no_orchestrator(self):
        """Test CVE check without orchestrator - should raise or return empty"""
        scanner = VulnScannerModule(orchestrator=None)
        # Module requires orchestrator, will raise AttributeError
        with pytest.raises(AttributeError):
            await scanner.check_cve_database("apache", "2.4.41")
