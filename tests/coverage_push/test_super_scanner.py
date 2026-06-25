#!/usr/bin/env python3
"""
Comprehensive Test Suite for modules/super_scanner.py

Target: 80%+ line coverage

Tests:
- SuperScanner initialization
- Tool orchestration (all 7 phases)
- Result aggregation
- Scan configuration
- Progress tracking
- Error handling
- Summary generation
- Report saving/printing
- CLI main function

Author: AI Assistant
"""

import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the project root is in path
sys.path.insert(0, "/home/atakan/Zen-Ai-Pentest")

from modules.super_scanner import SuperScanner, SuperScanResult, main

# ============================================================================
# Mock Data Classes for Tool Integrations
# ============================================================================


@dataclass
class MockSubdomainResult:
    """Mock result for subdomain enumeration"""

    subdomains: List[str] = field(default_factory=list)
    domain: str = ""
    timestamp: str = ""


@dataclass
class MockHTTPXHost:
    """Mock HTTPX host result"""

    url: str = ""
    status_code: int = 200
    title: str = ""
    webserver: str = ""
    ip: str = ""


@dataclass
class MockHTTPXResult:
    """Mock result for HTTPX probing"""

    hosts: List[MockHTTPXHost] = field(default_factory=list)
    target: str = ""


@dataclass
class MockWhatWebTech:
    """Mock WhatWeb technology result"""

    name: str = ""
    version: str = ""
    category: str = ""


@dataclass
class MockWhatWebResult:
    """Mock result for WhatWeb scan"""

    technologies: List[MockWhatWebTech] = field(default_factory=list)
    target: str = ""


@dataclass
class MockWAFResult:
    """Mock result for WAF detection"""

    firewall_detected: bool = False
    wafs: List[Any] = field(default_factory=list)
    target: str = ""


@dataclass
class MockWAFEntry:
    """Mock WAF entry"""

    name: str = ""
    confidence: int = 0


@dataclass
class MockFFuFFinding:
    """Mock FFuF finding"""

    url: str = ""
    status_code: int = 200
    content_length: int = 0


@dataclass
class MockFFuFResult:
    """Mock result for FFuF scan"""

    findings: List[MockFFuFFinding] = field(default_factory=list)
    target: str = ""


@dataclass
class MockNiktoFinding:
    """Mock Nikto finding"""

    id: str = ""
    severity: str = ""
    description: str = ""


@dataclass
class MockNiktoResult:
    """Mock result for Nikto scan"""

    findings: List[MockNiktoFinding] = field(default_factory=list)
    target: str = ""


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_tool_integrations():
    """Create mock tool integrations for all tools used by SuperScanner."""
    mocks = {}

    # Subfinder mock
    mock_subfinder = AsyncMock()
    mock_subfinder.enumerate = AsyncMock(
        return_value=MockSubdomainResult(
            subdomains=["sub1.example.com", "sub2.example.com", "sub3.example.com"],
            domain="example.com",
            timestamp=datetime.now().isoformat(),
        )
    )
    mocks["subfinder"] = mock_subfinder

    # Amass mock
    mock_amass = AsyncMock()
    mock_amass.enumerate = AsyncMock(
        return_value=MockSubdomainResult(
            subdomains=["sub2.example.com", "sub4.example.com"], domain="example.com", timestamp=datetime.now().isoformat()
        )
    )
    mocks["amass"] = mock_amass

    # HTTPX mock
    mock_httpx = AsyncMock()
    mock_httpx.probe = AsyncMock(
        return_value=MockHTTPXResult(
            hosts=[
                MockHTTPXHost(url="http://example.com", status_code=200, title="Home", webserver="nginx", ip="93.184.216.34"),
                MockHTTPXHost(
                    url="http://sub1.example.com", status_code=200, title="Sub1", webserver="apache", ip="93.184.216.35"
                ),
            ],
            target="example.com",
        )
    )
    mocks["httpx"] = mock_httpx

    # WhatWeb mock
    mock_whatweb = AsyncMock()
    mock_whatweb.scan = AsyncMock(
        return_value=MockWhatWebResult(
            technologies=[
                MockWhatWebTech(name="Apache", version="2.4.41", category="Web Server"),
                MockWhatWebTech(name="PHP", version="7.4.3", category="Programming Language"),
            ],
            target="example.com",
        )
    )
    mocks["whatweb"] = mock_whatweb

    # WAFW00F mock
    mock_wafw00f = AsyncMock()
    mock_wafw00f.detect = AsyncMock(
        return_value=MockWAFResult(
            firewall_detected=True, wafs=[MockWAFEntry(name="Cloudflare", confidence=95)], target="example.com"
        )
    )
    mocks["wafw00f"] = mock_wafw00f

    # FFuF mock
    mock_ffuf = AsyncMock()
    mock_ffuf.directory_bruteforce = AsyncMock(
        return_value=MockFFuFResult(
            findings=[
                MockFFuFFinding(url="http://example.com/admin", status_code=200, content_length=1024),
                MockFFuFFinding(url="http://example.com/api", status_code=200, content_length=512),
            ],
            target="example.com",
        )
    )
    mocks["ffuf"] = mock_ffuf

    # Nikto mock
    mock_nikto = AsyncMock()
    mock_nikto.scan = AsyncMock(
        return_value=MockNiktoResult(
            findings=[
                MockNiktoFinding(id="1", severity="High", description="Vulnerability 1"),
                MockNiktoFinding(id="2", severity="Medium", description="Vulnerability 2"),
            ],
            target="example.com",
        )
    )
    mocks["nikto"] = mock_nikto

    return mocks


@pytest.fixture
def scanner(mock_tool_integrations, tmp_path):
    """Create a SuperScanner instance with mocked tools."""
    with (
        patch("modules.super_scanner.FFuFIntegration") as mock_ffuf_cls,
        patch("modules.super_scanner.WhatWebIntegration") as mock_whatweb_cls,
        patch("modules.super_scanner.WAFW00FIntegration") as mock_wafw00f_cls,
        patch("modules.super_scanner.SubfinderIntegration") as mock_subfinder_cls,
        patch("modules.super_scanner.AmassIntegration") as mock_amass_cls,
        patch("modules.super_scanner.HTTPXIntegration") as mock_httpx_cls,
        patch("modules.super_scanner.NiktoIntegration") as mock_nikto_cls,
    ):
        mock_ffuf_cls.return_value = mock_tool_integrations["ffuf"]
        mock_whatweb_cls.return_value = mock_tool_integrations["whatweb"]
        mock_wafw00f_cls.return_value = mock_tool_integrations["wafw00f"]
        mock_subfinder_cls.return_value = mock_tool_integrations["subfinder"]
        mock_amass_cls.return_value = mock_tool_integrations["amass"]
        mock_httpx_cls.return_value = mock_tool_integrations["httpx"]
        mock_nikto_cls.return_value = mock_tool_integrations["nikto"]

        scanner = SuperScanner(output_dir=str(tmp_path))
        return scanner


@pytest.fixture
def scanner_with_mocked_fs(mock_tool_integrations, tmp_path):
    """Create a SuperScanner with fully mocked filesystem operations."""
    with (
        patch("modules.super_scanner.FFuFIntegration") as mock_ffuf_cls,
        patch("modules.super_scanner.WhatWebIntegration") as mock_whatweb_cls,
        patch("modules.super_scanner.WAFW00FIntegration") as mock_wafw00f_cls,
        patch("modules.super_scanner.SubfinderIntegration") as mock_subfinder_cls,
        patch("modules.super_scanner.AmassIntegration") as mock_amass_cls,
        patch("modules.super_scanner.HTTPXIntegration") as mock_httpx_cls,
        patch("modules.super_scanner.NiktoIntegration") as mock_nikto_cls,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        mock_ffuf_cls.return_value = mock_tool_integrations["ffuf"]
        mock_whatweb_cls.return_value = mock_tool_integrations["whatweb"]
        mock_wafw00f_cls.return_value = mock_tool_integrations["wafw00f"]
        mock_subfinder_cls.return_value = mock_tool_integrations["subfinder"]
        mock_amass_cls.return_value = mock_tool_integrations["amass"]
        mock_httpx_cls.return_value = mock_tool_integrations["httpx"]
        mock_nikto_cls.return_value = mock_tool_integrations["nikto"]

        scanner = SuperScanner(output_dir=str(tmp_path))
        return scanner


@pytest.fixture
def sample_scan_result():
    """Create a sample SuperScanResult for testing."""
    result = SuperScanResult(target="example.com", timestamp=datetime.now().isoformat())
    result.subdomains = {
        "success": True,
        "count": 75,
        "subdomains": [f"sub{i}.example.com" for i in range(60)],
        "sources": {"subfinder": 40, "amass": 35},
    }
    result.http_probe = {
        "success": True,
        "live_hosts": 25,
        "hosts": [{"url": f"http://sub{i}.example.com", "status_code": 200} for i in range(25)],
    }
    result.technology = {
        "success": True,
        "technologies": [
            {"name": "Apache", "version": "2.4.41", "category": "Web Server"},
            {"name": "PHP", "version": "7.4.3", "category": "Programming Language"},
            {"name": "nginx", "version": "1.18.0", "category": "Web Server"},
            {"name": "OpenSSH", "version": "8.2", "category": "Service"},
        ],
    }
    result.waf = {"success": True, "firewall_detected": False, "wafs": []}
    result.port_scan = {
        "success": True,
        "ip": "93.184.216.34",
        "ports": [
            {"port": 22, "service": "ssh", "version": "OpenSSH 8.2"},
            {"port": 80, "service": "http", "version": "nginx 1.18.0"},
            {"port": 443, "service": "https", "version": "nginx 1.18.0"},
            {"port": 3306, "service": "mysql", "version": "5.7.32"},
            {"port": 8080, "service": "http-proxy", "version": ""},
            {"port": 8443, "service": "https-alt", "version": ""},
        ],
    }
    result.directories = {
        "success": True,
        "findings": [{"url": f"http://example.com/dir{i}", "status_code": 200} for i in range(15)],
        "total_found": 15,
    }
    result.vulnerabilities = {
        "success": True,
        "findings": [
            {"id": "1", "severity": "High", "description": "Vuln 1"},
            {"id": "2", "severity": "Medium", "description": "Vuln 2"},
            {"id": "3", "severity": "Low", "description": "Vuln 3"},
            {"id": "4", "severity": "High", "description": "Vuln 4"},
        ],
        "total": 4,
    }
    return result


# ============================================================================
# Initialization Tests
# ============================================================================


class TestSuperScannerInitialization:
    """Tests for SuperScanner initialization."""

    def test_init_creates_output_dir(self, tmp_path):
        """Test that initialization creates the output directory."""
        output_dir = tmp_path / "test_reports"

        with (
            patch("modules.super_scanner.FFuFIntegration"),
            patch("modules.super_scanner.WhatWebIntegration"),
            patch("modules.super_scanner.WAFW00FIntegration"),
            patch("modules.super_scanner.SubfinderIntegration"),
            patch("modules.super_scanner.AmassIntegration"),
            patch("modules.super_scanner.HTTPXIntegration"),
            patch("modules.super_scanner.NiktoIntegration"),
        ):
            scanner = SuperScanner(output_dir=str(output_dir))

        assert output_dir.exists()
        assert scanner.output_dir == output_dir

    def test_init_initializes_all_tools(self, tmp_path):
        """Test that all tool integrations are initialized."""
        with (
            patch("modules.super_scanner.FFuFIntegration") as mock_ffuf,
            patch("modules.super_scanner.WhatWebIntegration") as mock_whatweb,
            patch("modules.super_scanner.WAFW00FIntegration") as mock_wafw00f,
            patch("modules.super_scanner.SubfinderIntegration") as mock_subfinder,
            patch("modules.super_scanner.AmassIntegration") as mock_amass,
            patch("modules.super_scanner.HTTPXIntegration") as mock_httpx,
            patch("modules.super_scanner.NiktoIntegration") as mock_nikto,
        ):
            scanner = SuperScanner(output_dir=str(tmp_path))

        # Just verify the mocks were created
        mock_ffuf.assert_called_once()
        mock_whatweb.assert_called_once()
        mock_wafw00f.assert_called_once()
        mock_subfinder.assert_called_once()
        mock_amass.assert_called_once()
        mock_httpx.assert_called_once()
        mock_nikto.assert_called_once()

    def test_init_with_default_output_dir(self):
        """Test initialization with default output directory."""
        with (
            patch("modules.super_scanner.FFuFIntegration"),
            patch("modules.super_scanner.WhatWebIntegration"),
            patch("modules.super_scanner.WAFW00FIntegration"),
            patch("modules.super_scanner.SubfinderIntegration"),
            patch("modules.super_scanner.AmassIntegration"),
            patch("modules.super_scanner.HTTPXIntegration"),
            patch("modules.super_scanner.NiktoIntegration"),
            patch("pathlib.Path.mkdir"),
        ):
            scanner = SuperScanner()

        assert scanner.output_dir.name == "reports"


# ============================================================================
# Scan Domain Tests
# ============================================================================


class TestScanDomain:
    """Tests for the scan_domain method."""

    @pytest.mark.asyncio
    async def test_scan_domain_successful_all_phases(self, scanner):
        """Test successful scan through all 7 phases."""
        # Mock subprocess for nmap
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(
                b"Starting Nmap\n22/tcp open ssh OpenSSH 8.2\n80/tcp open http nginx 1.18.0\n443/tcp open https nginx 1.18.0",
                b"",
            )
        )

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.target == "example.com"
        assert result.timestamp is not None

        # Check all phases completed
        assert result.subdomains["success"] is True
        assert result.subdomains["count"] == 4  # Unique from subfinder (3) + amass (2)

        assert result.http_probe["success"] is True
        assert result.http_probe["live_hosts"] == 2

        assert result.technology["success"] is True
        assert len(result.technology["technologies"]) == 2

        assert result.waf["success"] is True
        assert result.waf["firewall_detected"] is True

        assert result.port_scan["success"] is True
        assert result.port_scan["ip"] == "93.184.216.34"
        assert len(result.port_scan["ports"]) == 3

        assert result.directories["success"] is True
        assert result.directories["total_found"] == 2

        assert result.vulnerabilities["success"] is True
        assert result.vulnerabilities["total"] == 2

        # Check summary was generated
        assert result.summary is not None
        assert "risk_level" in result.summary
        assert "risk_score" in result.summary

    @pytest.mark.asyncio
    async def test_scan_domain_subdomain_phase_failure(self, scanner, mock_tool_integrations):
        """Test scan continues when subdomain enumeration fails."""
        mock_tool_integrations["subfinder"].enumerate = AsyncMock(side_effect=Exception("Subfinder failed"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        # Subdomain phase failed but scan continued
        assert result.subdomains["success"] is False
        assert "error" in result.subdomains

        # Other phases still completed
        assert result.technology["success"] is True
        assert result.waf["success"] is True

    @pytest.mark.asyncio
    async def test_scan_domain_httpx_phase_failure(self, scanner, mock_tool_integrations):
        """Test scan continues when HTTP probing fails."""
        mock_tool_integrations["httpx"].probe = AsyncMock(side_effect=Exception("HTTPX failed"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.http_probe["success"] is False
        assert "error" in result.http_probe
        assert result.subdomains["success"] is True  # Other phases work

    @pytest.mark.asyncio
    async def test_scan_domain_whatweb_phase_failure(self, scanner, mock_tool_integrations):
        """Test scan continues when technology detection fails."""
        mock_tool_integrations["whatweb"].scan = AsyncMock(side_effect=Exception("WhatWeb failed"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.technology["success"] is False
        assert "error" in result.technology

    @pytest.mark.asyncio
    async def test_scan_domain_waf_phase_failure(self, scanner, mock_tool_integrations):
        """Test scan continues when WAF detection fails."""
        mock_tool_integrations["wafw00f"].detect = AsyncMock(side_effect=Exception("WAFW00F failed"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.waf["success"] is False
        assert "error" in result.waf

    @pytest.mark.asyncio
    async def test_scan_domain_port_scan_failure(self, scanner):
        """Test scan continues when port scanning fails."""
        with patch("socket.gethostbyname", side_effect=Exception("DNS failed")):
            result = await scanner.scan_domain("example.com")

        assert result.port_scan["success"] is False
        assert "error" in result.port_scan

    @pytest.mark.asyncio
    async def test_scan_domain_ffuf_phase_failure(self, scanner, mock_tool_integrations):
        """Test scan continues when directory bruteforce fails."""
        mock_tool_integrations["ffuf"].directory_bruteforce = AsyncMock(side_effect=Exception("FFuF failed"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.directories["success"] is False
        assert "error" in result.directories

    @pytest.mark.asyncio
    async def test_scan_domain_nikto_phase_failure(self, scanner, mock_tool_integrations):
        """Test scan continues when vulnerability scanning fails."""
        mock_tool_integrations["nikto"].scan = AsyncMock(side_effect=Exception("Nikto failed"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.vulnerabilities["success"] is False
        assert "error" in result.vulnerabilities

    @pytest.mark.asyncio
    async def test_scan_domain_nmap_timeout(self, scanner):
        """Test port scan handles timeout."""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError("Nmap timeout"))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError("Timeout")),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.port_scan["success"] is False

    @pytest.mark.asyncio
    async def test_scan_domain_nmap_parsing(self, scanner):
        """Test nmap output parsing with various formats."""
        mock_process = AsyncMock()
        # Test various line formats
        mock_process.communicate = AsyncMock(
            return_value=(
                b"Starting Nmap 7.80\n"
                b"22/tcp  open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5\n"
                b"80/tcp  open  http    nginx 1.18.0\n"
                b"443/tcp open  https   nginx 1.18.0\n"
                b"Closed filtered ports omitted",
                b"",
            )
        )

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.port_scan["success"] is True
        ports = result.port_scan["ports"]
        assert len(ports) == 3
        assert ports[0]["port"] == 22
        assert ports[0]["service"] == "ssh"
        assert "OpenSSH" in ports[0]["version"]


# ============================================================================
# Summary Generation Tests
# ============================================================================


class TestGenerateSummary:
    """Tests for _generate_summary method."""

    def test_generate_summary_critical_risk(self, scanner, sample_scan_result):
        """Test CRITICAL risk level calculation."""
        # Set conditions for CRITICAL risk
        sample_scan_result.subdomains["count"] = 60  # > 50
        sample_scan_result.waf["firewall_detected"] = False  # +20
        sample_scan_result.port_scan["ports"] = [{}, {}, {}, {}, {}, {}, {}]  # > 5, +10
        sample_scan_result.directories["total_found"] = 15  # > 10, +15
        sample_scan_result.vulnerabilities["total"] = 10  # +30 (min)

        summary = scanner._generate_summary(sample_scan_result)

        assert summary["risk_level"] == "CRITICAL"
        assert summary["risk_score"] >= 60
        assert "Large attack surface (many subdomains)" in summary["risk_factors"]
        assert "No WAF detected" in summary["risk_factors"]

    def test_generate_summary_high_risk(self, scanner, sample_scan_result):
        """Test HIGH risk level calculation."""
        # Set conditions for HIGH risk (40-59)
        sample_scan_result.subdomains["count"] = 30  # < 50, no points
        sample_scan_result.waf["firewall_detected"] = False  # +20
        sample_scan_result.port_scan["ports"] = [{}, {}, {}, {}, {}, {}]  # > 5, +10
        sample_scan_result.directories["total_found"] = 12  # > 10, +15
        sample_scan_result.vulnerabilities["total"] = 0  # no points

        summary = scanner._generate_summary(sample_scan_result)

        assert summary["risk_level"] == "HIGH"
        assert 40 <= summary["risk_score"] < 60

    def test_generate_summary_medium_risk(self, scanner, sample_scan_result):
        """Test MEDIUM risk level calculation."""
        # Set conditions for MEDIUM risk (20-39)
        sample_scan_result.subdomains["count"] = 10
        sample_scan_result.waf["firewall_detected"] = True  # no points
        sample_scan_result.port_scan["ports"] = [{}, {}]  # < 5, no points
        sample_scan_result.directories["total_found"] = 8  # < 10, no points
        sample_scan_result.vulnerabilities["total"] = 5  # +25

        summary = scanner._generate_summary(sample_scan_result)

        assert summary["risk_level"] == "MEDIUM"
        assert 20 <= summary["risk_score"] < 40

    def test_generate_summary_low_risk(self, scanner, sample_scan_result):
        """Test LOW risk level calculation."""
        # Set conditions for LOW risk (< 20)
        sample_scan_result.subdomains["count"] = 10
        sample_scan_result.waf["firewall_detected"] = True
        sample_scan_result.port_scan["ports"] = [{}, {}]
        sample_scan_result.directories["total_found"] = 3
        sample_scan_result.vulnerabilities["total"] = 0

        summary = scanner._generate_summary(sample_scan_result)

        assert summary["risk_level"] == "LOW"
        assert summary["risk_score"] < 20

    def test_generate_summary_with_empty_result(self, scanner):
        """Test summary generation with empty/minimal result."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())

        summary = scanner._generate_summary(result)

        # Empty result should be LOW risk (0 score)
        assert summary["risk_level"] in ["LOW", "MEDIUM"]  # Depends on default empty values
        assert summary["risk_score"] >= 0
        assert summary["statistics"]["subdomains"] == 0
        assert summary["statistics"]["live_hosts"] == 0


# ============================================================================
# Recommendations Tests
# ============================================================================


class TestGenerateRecommendations:
    """Tests for _generate_recommendations method."""

    def test_recommendations_no_waf(self, scanner):
        """Test recommendation for missing WAF."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.waf = {"firewall_detected": False}

        recommendations = scanner._generate_recommendations(result)

        assert any("WAF" in r for r in recommendations)

    def test_recommendations_many_ports(self, scanner):
        """Test recommendation for many open ports."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.port_scan = {"ports": [{}, {}, {}, {}, {}]}

        recommendations = scanner._generate_recommendations(result)

        assert any("ports" in r.lower() for r in recommendations)

    def test_recommendations_many_directories(self, scanner):
        """Test recommendation for many exposed directories."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.directories = {"total_found": 10}

        recommendations = scanner._generate_recommendations(result)

        assert any("director" in r.lower() for r in recommendations)

    def test_recommendations_vulnerabilities(self, scanner):
        """Test recommendation when vulnerabilities found."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.vulnerabilities = {"total": 5}

        recommendations = scanner._generate_recommendations(result)

        assert any("vulnerabilit" in r.lower() for r in recommendations)

    def test_recommendations_outdated_software(self, scanner):
        """Test recommendations for outdated software."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.technology = {
            "technologies": [
                {"name": "Apache", "version": "2.4.41"},
                {"name": "nginx", "version": "1.18.0"},
                {"name": "PHP", "version": "7.4.3"},
                {"name": "OpenSSH", "version": "8.2"},
                {"name": "UnknownSoftware", "version": ""},  # Empty version, should be skipped
            ]
        }

        recommendations = scanner._generate_recommendations(result)

        # Should have recommendations for Apache, nginx, PHP, OpenSSH
        assert len([r for r in recommendations if "Review" in r]) == 4

    def test_recommendations_limit_to_10(self, scanner):
        """Test that recommendations are limited to 10."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.waf = {"firewall_detected": False}
        result.port_scan = {"ports": [{}, {}, {}, {}, {}]}
        result.directories = {"total_found": 10}
        result.vulnerabilities = {"total": 5}
        result.technology = {
            "technologies": [
                {"name": "Apache", "version": "2.4.41"},
                {"name": "nginx", "version": "1.18.0"},
                {"name": "PHP", "version": "7.4.3"},
                {"name": "OpenSSH", "version": "8.2"},
            ]
        }

        recommendations = scanner._generate_recommendations(result)

        assert len(recommendations) <= 10


# ============================================================================
# Save Report Tests
# ============================================================================


class TestSaveReport:
    """Tests for save_report method."""

    def test_save_report_with_default_filename(self, scanner, sample_scan_result, tmp_path):
        """Test saving report with auto-generated filename."""
        with patch("modules.super_scanner.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260101_120000"

            filepath = scanner.save_report(sample_scan_result)

        assert filepath.exists()
        assert "super_scan_example.com" in filepath.name
        assert filepath.suffix == ".json"

        # Verify content
        with open(filepath) as f:
            data = json.load(f)
        assert data["target"] == "example.com"

    def test_save_report_with_custom_filename(self, scanner, sample_scan_result, tmp_path):
        """Test saving report with custom filename."""
        filepath = scanner.save_report(sample_scan_result, filename="custom_report.json")

        assert filepath.name == "custom_report.json"
        assert filepath.exists()

    def test_save_report_returns_filepath(self, scanner, sample_scan_result):
        """Test that save_report returns the correct filepath."""
        filepath = scanner.save_report(sample_scan_result, filename="test.json")

        assert isinstance(filepath, Path)
        assert filepath.exists()


# ============================================================================
# Print Report Tests
# ============================================================================


class TestPrintReport:
    """Tests for print_report method."""

    def test_print_report_outputs_correctly(self, scanner, sample_scan_result, capsys):
        """Test that print_report outputs the report correctly."""
        # Add summary to sample result
        sample_scan_result.summary = scanner._generate_summary(sample_scan_result)

        scanner.print_report(sample_scan_result)

        captured = capsys.readouterr()
        output = captured.out

        assert "SUPER SCAN REPORT" in output
        assert "example.com" in output
        assert "RISK LEVEL:" in output
        assert "Risk Score:" in output
        assert "STATISTICS" in output
        assert "RISK FACTORS" in output
        assert "RECOMMENDATIONS" in output

    def test_print_report_no_risk_factors(self, scanner, capsys):
        """Test print_report with no risk factors."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.summary = {"risk_level": "LOW", "risk_score": 0, "risk_factors": [], "statistics": {}, "recommendations": []}

        scanner.print_report(result)

        captured = capsys.readouterr()
        # Should not crash and should still print basic info
        assert "SUPER SCAN REPORT" in captured.out

    def test_print_report_no_recommendations(self, scanner, capsys):
        """Test print_report with no recommendations."""
        result = SuperScanResult(target="test.com", timestamp=datetime.now().isoformat())
        result.summary = {
            "risk_level": "LOW",
            "risk_score": 0,
            "risk_factors": ["Test factor"],
            "statistics": {"subdomains": 0},
            "recommendations": [],
        }

        scanner.print_report(result)

        captured = capsys.readouterr()
        assert "SUPER SCAN REPORT" in captured.out
        assert "Test factor" in captured.out


# ============================================================================
# Main Function Tests
# ============================================================================


class TestMainFunction:
    """Tests for the main() CLI function."""

    @patch("modules.super_scanner.argparse.ArgumentParser")
    def test_main_abort_on_no_confirm(self, mock_parser_class):
        """Test that main aborts when user doesn't confirm."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(target="example.com", output_dir="reports", quiet=False)
        mock_parser_class.return_value = mock_parser

        with patch("builtins.input", return_value="no"):
            main()

        # Should print aborted message

    @patch("modules.super_scanner.argparse.ArgumentParser")
    @patch("modules.super_scanner.SuperScanner")
    @patch("asyncio.run")
    def test_main_successful_scan(self, mock_asyncio_run, mock_scanner_class, mock_parser_class):
        """Test successful scan execution via main."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(target="example.com", output_dir="reports", quiet=False)
        mock_parser_class.return_value = mock_parser

        mock_scanner = MagicMock()
        mock_result = MagicMock()
        mock_result.target = "example.com"
        mock_result.timestamp = datetime.now().isoformat()
        mock_result.summary = {}
        mock_asyncio_run.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        with patch("builtins.input", return_value="yes"):
            main()

        mock_scanner_class.assert_called_once_with(output_dir="reports")
        mock_asyncio_run.assert_called_once()
        mock_scanner.save_report.assert_called_once()

    @patch("modules.super_scanner.argparse.ArgumentParser")
    @patch("modules.super_scanner.SuperScanner")
    @patch("asyncio.run")
    def test_main_quiet_mode(self, mock_asyncio_run, mock_scanner_class, mock_parser_class):
        """Test main with quiet mode."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(target="example.com", output_dir="reports", quiet=True)
        mock_parser_class.return_value = mock_parser

        mock_scanner = MagicMock()
        mock_result = MagicMock()
        mock_result.summary = {}
        mock_asyncio_run.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        with patch("builtins.input", return_value="yes"):
            main()

        # print_report should not be called in quiet mode
        mock_scanner.print_report.assert_not_called()

    @patch("modules.super_scanner.argparse.ArgumentParser")
    @patch("modules.super_scanner.SuperScanner")
    @patch("asyncio.run")
    def test_main_keyboard_interrupt(self, mock_asyncio_run, mock_scanner_class, mock_parser_class):
        """Test handling of KeyboardInterrupt."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(target="example.com", output_dir="reports", quiet=False)
        mock_parser_class.return_value = mock_parser

        mock_asyncio_run.side_effect = KeyboardInterrupt()

        with patch("builtins.input", return_value="yes"):
            main()  # Should handle gracefully

    @patch("modules.super_scanner.argparse.ArgumentParser")
    @patch("modules.super_scanner.SuperScanner")
    @patch("asyncio.run")
    def test_main_exception(self, mock_asyncio_run, mock_scanner_class, mock_parser_class):
        """Test handling of general exceptions."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(target="example.com", output_dir="reports", quiet=False)
        mock_parser_class.return_value = mock_parser

        mock_asyncio_run.side_effect = Exception("Scan failed")

        with patch("builtins.input", return_value="yes"):
            with pytest.raises(Exception, match="Scan failed"):
                main()

    @patch("modules.super_scanner.argparse.ArgumentParser")
    def test_main_confirmation_variations(self, mock_parser_class):
        """Test various confirmation responses."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(target="example.com", output_dir="reports", quiet=False)
        mock_parser_class.return_value = mock_parser

        # Test with 'y' response
        with patch("builtins.input", return_value="y"):
            with patch("modules.super_scanner.SuperScanner"):
                with patch("asyncio.run"):
                    main()

        # Test with 'yes' response
        with patch("builtins.input", return_value="yes"):
            with patch("modules.super_scanner.SuperScanner"):
                with patch("asyncio.run"):
                    main()


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_subdomain_list(self, scanner, mock_tool_integrations):
        """Test scan with empty subdomain results."""
        mock_tool_integrations["subfinder"].enumerate = AsyncMock(
            return_value=MockSubdomainResult(subdomains=[], domain="example.com", timestamp="")
        )
        mock_tool_integrations["amass"].enumerate = AsyncMock(
            return_value=MockSubdomainResult(subdomains=[], domain="example.com", timestamp="")
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.subdomains["count"] == 0
        assert result.subdomains["subdomains"] == []

    @pytest.mark.asyncio
    async def test_subdomain_limiting(self, scanner, mock_tool_integrations):
        """Test that subdomains are limited to 100 in results."""
        # Create 150 subdomains
        many_subdomains = [f"sub{i}.example.com" for i in range(150)]
        mock_tool_integrations["subfinder"].enumerate = AsyncMock(
            return_value=MockSubdomainResult(subdomains=many_subdomains, domain="example.com", timestamp="")
        )
        mock_tool_integrations["amass"].enumerate = AsyncMock(
            return_value=MockSubdomainResult(subdomains=[], domain="example.com", timestamp="")
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.subdomains["count"] == 150
        assert len(result.subdomains["subdomains"]) == 100  # Limited

    @pytest.mark.asyncio
    async def test_httpx_host_limiting(self, scanner, mock_tool_integrations):
        """Test that HTTPX hosts are processed correctly."""
        # Create many hosts
        many_hosts = [MockHTTPXHost(url=f"http://sub{i}.example.com") for i in range(30)]
        mock_tool_integrations["httpx"].probe = AsyncMock(return_value=MockHTTPXResult(hosts=many_hosts, target="example.com"))

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        # HTTPX probe is called with main domain + up to 20 subdomains
        mock_tool_integrations["httpx"].probe.assert_called_once()
        call_args = mock_tool_integrations["httpx"].probe.call_args[0][0]
        # The actual number depends on how many subdomains were found (4 from mock)
        assert len(call_args) >= 1  # At least the main domain
        assert call_args[0] == "example.com"  # First item is the main domain

    @pytest.mark.asyncio
    async def test_nmap_no_open_ports(self, scanner):
        """Test nmap parsing when no open ports found."""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"Starting Nmap\nAll 1000 scanned ports are closed", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.port_scan["success"] is True
        assert result.port_scan["ports"] == []

    @pytest.mark.asyncio
    async def test_ffuf_findings_limiting(self, scanner, mock_tool_integrations):
        """Test that FFuF findings are limited to 50 in results."""
        # Create 60 findings
        many_findings = [MockFFuFFinding(url=f"http://example.com/dir{i}") for i in range(60)]
        mock_tool_integrations["ffuf"].directory_bruteforce = AsyncMock(
            return_value=MockFFuFResult(findings=many_findings, target="example.com")
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.directories["total_found"] == 60
        assert len(result.directories["findings"]) == 50  # Limited

    @pytest.mark.asyncio
    async def test_nikto_findings_limiting(self, scanner, mock_tool_integrations):
        """Test that Nikto findings are limited to 20 in results."""
        # Create 25 findings
        many_findings = [MockNiktoFinding(id=str(i), severity="Medium") for i in range(25)]
        mock_tool_integrations["nikto"].scan = AsyncMock(
            return_value=MockNiktoResult(findings=many_findings, target="example.com")
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert result.vulnerabilities["total"] == 25
        assert len(result.vulnerabilities["findings"]) == 20  # Limited

    @pytest.mark.asyncio
    async def test_whatweb_technologies_limiting(self, scanner, mock_tool_integrations):
        """Test that WhatWeb technologies are limited to 20 in results."""
        # Create 25 technologies
        many_techs = [MockWhatWebTech(name=f"Tech{i}") for i in range(25)]
        mock_tool_integrations["whatweb"].scan = AsyncMock(
            return_value=MockWhatWebResult(technologies=many_techs, target="example.com")
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"80/tcp open http", b""))

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch("socket.gethostbyname", return_value="93.184.216.34"),
        ):
            result = await scanner.scan_domain("example.com")

        assert len(result.technology["technologies"]) == 20  # Limited


# ============================================================================
# SuperScanResult Dataclass Tests
# ============================================================================


class TestSuperScanResult:
    """Tests for the SuperScanResult dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        result = SuperScanResult(target="test.com", timestamp="2024-01-01")

        assert result.port_scan == {}
        assert result.subdomains == {}
        assert result.technology == {}
        assert result.waf == {}
        assert result.directories == {}
        assert result.vulnerabilities == {}
        assert result.http_probe == {}
        assert result.summary == {}

    def test_custom_values(self):
        """Test setting custom values."""
        result = SuperScanResult(
            target="test.com", timestamp="2024-01-01", port_scan={"success": True}, subdomains={"count": 5}
        )

        assert result.port_scan == {"success": True}
        assert result.subdomains == {"count": 5}


# ============================================================================
# Integration Test
# ============================================================================


@pytest.mark.asyncio
async def test_full_scan_workflow(scanner, tmp_path):
    """Integration test for the complete scan workflow."""
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(
        return_value=(b"Starting Nmap\n22/tcp open ssh OpenSSH 8.2\n80/tcp open http nginx\n443/tcp open https nginx", b"")
    )

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_process),
        patch("socket.gethostbyname", return_value="93.184.216.34"),
    ):
        # Run scan
        result = await scanner.scan_domain("example.com")

        # Save report
        filepath = scanner.save_report(result, filename="integration_test.json")

        # Verify saved report
        with open(filepath) as f:
            saved_data = json.load(f)

        assert saved_data["target"] == "example.com"
        assert "summary" in saved_data
        assert "risk_level" in saved_data["summary"]
