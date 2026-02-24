"""
Tests für Enhanced Tool Integrations
FFuF, WhatWeb, WAFW00F, Subfinder, HTTPX, Nikto
"""

from unittest.mock import AsyncMock, patch

import pytest

# Import tools
from tools.ffuf_integration_enhanced import (
    FFuFFinding,
    FFuFIntegration,
    FFuFResult,
)
from tools.httpx_integration import HTTPXHost, HTTPXIntegration
from tools.nikto_integration import NiktoFinding, NiktoIntegration
from tools.subfinder_integration import SubfinderIntegration, SubfinderResult
from tools.wafw00f_integration import WAFFinding, WAFW00FIntegration
from tools.whatweb_integration import Technology, WhatWebIntegration


class TestFFuFIntegration:
    """Test FFuF Integration"""

    def test_initialization(self):
        """Test FFuFIntegration initialization"""
        ffuf = FFuFIntegration()
        # Wordlist dir may not exist in test environment
        assert ffuf.wordlist_dir is not None

    def test_ffuf_finding_dataclass(self):
        """Test FFuFFinding dataclass"""
        finding = FFuFFinding(
            url="http://example.com/admin",
            status_code=200,
            content_length=1234,
            content_words=50,
            content_lines=20,
        )
        assert finding.url == "http://example.com/admin"
        assert finding.status_code == 200
        assert finding.content_length == 1234

    def test_ffuf_result_dataclass(self):
        """Test FFuFResult dataclass"""
        result = FFuFResult(
            success=True, findings=[], command="ffuf -u target"
        )
        assert result.success is True
        assert result.findings == []
        assert result.command == "ffuf -u target"

    @pytest.mark.asyncio
    async def test_directory_bruteforce_mock(self):
        """Test directory bruteforce with mocked subprocess"""
        ffuf = FFuFIntegration()

        # Mock subprocess
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b'{"type":"result","url":"http://test.com/admin","status":200,"length":1234}\n'
            b'{"type":"summary","total":2}',
            b"",
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await ffuf.directory_bruteforce("http://test.com/FUZZ")

        assert result.success is True
        assert len(result.findings) == 1
        assert result.findings[0].url == "http://test.com/admin"
        assert result.findings[0].status_code == 200


class TestWhatWebIntegration:
    """Test WhatWeb Integration"""

    def test_initialization(self):
        """Test WhatWebIntegration initialization"""
        whatweb = WhatWebIntegration(aggression=3)
        assert whatweb.aggression == 3

    def test_technology_dataclass(self):
        """Test Technology dataclass"""
        tech = Technology(
            name="Apache",
            version="2.4.7",
            confidence=100,
            category="Web Server",
        )
        assert tech.name == "Apache"
        assert tech.version == "2.4.7"
        assert tech.confidence == 100

    def test_categorize(self):
        """Test technology categorization"""
        whatweb = WhatWebIntegration()

        assert whatweb._categorize("Apache") == "Web Server"
        assert whatweb._categorize("PHP") == "Programming Language"
        assert whatweb._categorize("WordPress") == "CMS"
        assert whatweb._categorize("UnknownTech") == "Other"

    def test_clean_ansi(self):
        """Test ANSI escape code cleaning"""
        whatweb = WhatWebIntegration()

        dirty = "\x1b[1mApache\x1b[0m"
        clean = whatweb._clean_ansi(dirty)
        assert clean == "Apache"

    @pytest.mark.asyncio
    async def test_scan_mock(self):
        """Test scan with mocked subprocess"""
        whatweb = WhatWebIntegration()

        mock_json = '{"target":"http://test.com","plugins":{"Apache":{"version":["2.4.7"]}}}\n'

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_json.encode(), b"")
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await whatweb.scan("http://test.com")

        assert result.success is True
        assert len(result.technologies) >= 1


class TestWAFW00FIntegration:
    """Test WAFW00F Integration"""

    def test_waf_finding_dataclass(self):
        """Test WAFFinding dataclass"""
        waf = WAFFinding(
            name="Cloudflare",
            manufacturer="Cloudflare Inc.",
            detected=True,
            confidence="high",
        )
        assert waf.name == "Cloudflare"
        assert waf.confidence == "high"

    @pytest.mark.asyncio
    async def test_detect_no_waf_mock(self):
        """Test WAF detection with no WAF found"""
        wafw00f = WAFW00FIntegration()

        mock_json = '[{"url":"http://test.com","firewall":"None"}]'

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_json.encode(), b"")
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await wafw00f.detect("http://test.com")

        assert result.success is True
        assert result.firewall_detected is False


class TestSubfinderIntegration:
    """Test Subfinder Integration"""

    def test_subfinder_result_dataclass(self):
        """Test SubfinderResult dataclass"""
        result = SubfinderResult(
            success=True,
            domain="example.com",
            subdomains=["www.example.com", "mail.example.com"],
            count=2,
        )
        assert result.success is True
        assert result.count == 2
        assert len(result.subdomains) == 2

    @pytest.mark.asyncio
    async def test_enumerate_mock(self):
        """Test subdomain enumeration with mocked subprocess"""
        subfinder = SubfinderIntegration()

        mock_json = '{"host":"www.test.com"}\n{"host":"mail.test.com"}\n'

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_json.encode(), b"")
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await subfinder.enumerate("test.com")

        assert result.success is True
        assert result.count == 2
        assert "www.test.com" in result.subdomains
        assert "mail.test.com" in result.subdomains


class TestHTTPXIntegration:
    """Test HTTPX Integration"""

    def test_httpx_host_dataclass(self):
        """Test HTTPXHost dataclass"""
        host = HTTPXHost(
            url="http://test.com",
            status_code=200,
            title="Test Page",
            webserver="Apache",
            ip="192.168.1.1",
        )
        assert host.url == "http://test.com"
        assert host.status_code == 200
        assert host.title == "Test Page"

    @pytest.mark.asyncio
    async def test_probe_mock(self):
        """Test HTTP probing with mocked subprocess"""
        httpx = HTTPXIntegration()

        mock_json = (
            '{"url":"http://test.com","status_code":200,"title":"Test"}\n'
        )

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_json.encode(), b"")
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await httpx.probe(["test.com"])

        assert result.success is True
        assert result.count == 1
        assert result.hosts[0].url == "http://test.com"


class TestNiktoIntegration:
    """Test Nikto Integration"""

    def test_nikto_finding_dataclass(self):
        """Test NiktoFinding dataclass"""
        finding = NiktoFinding(
            id="OSVDB-1234",
            method="GET",
            path="/admin",
            description="Admin interface found",
            severity="medium",
        )
        assert finding.id == "OSVDB-1234"
        assert finding.severity == "medium"

    def test_classify_severity(self):
        """Test severity classification"""
        nikto = NiktoIntegration()

        assert (
            nikto._classify_severity("", "SQL Injection vulnerability")
            == "high"
        )
        assert (
            nikto._classify_severity("", "Information disclosure") == "medium"
        )
        assert nikto._classify_severity("", "Server header present") == "info"


class TestEnhancedReconModule:
    """Test Enhanced Recon Module"""

    def test_full_recon_structure(self):
        """Test that full_recon returns expected structure"""
        from modules.enhanced_recon import EnhancedReconModule

        with (
            patch.object(
                EnhancedReconModule, "technology_detection"
            ) as mock_tech,
            patch.object(EnhancedReconModule, "waf_detection") as mock_waf,
            patch.object(
                EnhancedReconModule, "directory_bruteforce"
            ) as mock_dir,
        ):

            mock_tech.return_value = {"technologies": [], "success": True}
            mock_waf.return_value = {
                "firewall_detected": False,
                "success": True,
            }
            mock_dir.return_value = {"findings": [], "success": True}

            recon = EnhancedReconModule()
            result = recon.full_recon("test.com")

            assert "technology_scan" in result
            assert "waf_detection" in result
            assert "directory_scan" in result
            assert "summary" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
