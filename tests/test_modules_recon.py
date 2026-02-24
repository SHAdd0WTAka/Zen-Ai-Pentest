"""
Comprehensive tests for the reconnaissance module.

Tests ReconModule functionality including:
- Target analysis
- DNS resolution
- DNS records retrieval
- WHOIS lookup
- Attack vector parsing
- Nmap command generation
- Subdomain enumeration
- Comprehensive subdomain scanning
- Attack surface discovery
"""

import asyncio
import socket
import subprocess
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.recon import ReconModule


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
def recon_module(mock_orchestrator):
    """Create a ReconModule instance with mock orchestrator"""
    return ReconModule(orchestrator=mock_orchestrator)


class TestReconModuleInit:
    """Test ReconModule initialization"""

    def test_init_with_orchestrator(self, mock_orchestrator):
        """Test initialization with orchestrator"""
        module = ReconModule(orchestrator=mock_orchestrator)
        assert module.orchestrator == mock_orchestrator
        assert module.results == {}

    def test_init_without_orchestrator(self):
        """Test initialization without orchestrator"""
        module = ReconModule(orchestrator=None)
        assert module.orchestrator is None
        assert module.results == {}


class TestReconTargetAnalysis:
    """Test target analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_target_success(self, recon_module, mock_orchestrator):
        """Test successful target analysis"""
        mock_orchestrator.process.return_value = MockResponse(
            content="""
Attack Vectors:
1. Web application vulnerabilities
2. Outdated SSL/TLS configuration
3. Information disclosure in headers

Suggested Tools:
- nmap for port scanning
- gobuster for directory enumeration
- sslscan for SSL analysis
"""
        )

        with patch.object(recon_module, "_resolve_ip", return_value="93.184.216.34"):
            with patch.object(recon_module, "_get_dns_records", return_value=["A: 93.184.216.34"]):
                with patch.object(recon_module, "_get_whois", return_value="Domain Name: EXAMPLE.COM"):
                    result = await recon_module.analyze_target("example.com")

        assert result["target"] == "example.com"
        assert result["ip"] == "93.184.216.34"
        assert "dns_records" in result
        assert "whois" in result
        assert "llm_analysis" in result
        assert "attack_vectors" in result
        mock_orchestrator.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_target_dns_failure(self, recon_module, mock_orchestrator):
        """Test target analysis with DNS failure"""
        mock_orchestrator.process.return_value = MockResponse(content="No attack vectors found")

        with patch.object(recon_module, "_resolve_ip", return_value="Could not resolve"):
            with patch.object(recon_module, "_get_dns_records", return_value=["No DNS records found"]):
                with patch.object(recon_module, "_get_whois", return_value="WHOIS not available"):
                    result = await recon_module.analyze_target("invalid.invalid")

        assert result["target"] == "invalid.invalid"
        assert result["ip"] == "Could not resolve"


class TestReconDNSResolution:
    """Test DNS resolution functionality"""

    @pytest.mark.asyncio
    async def test_resolve_ip_success(self, recon_module):
        """Test successful IP resolution"""
        with patch("socket.gethostbyname", return_value="93.184.216.34"):
            result = await recon_module._resolve_ip("example.com")
        assert result == "93.184.216.34"

    @pytest.mark.asyncio
    async def test_resolve_ip_failure(self, recon_module):
        """Test IP resolution failure"""
        with patch("socket.gethostbyname", side_effect=socket.gaierror("DNS Error")):
            result = await recon_module._resolve_ip("invalid.invalid")
        assert result == "Could not resolve"


class TestReconDNSRecords:
    """Test DNS records retrieval"""

    @pytest.mark.asyncio
    async def test_get_dns_records_success(self, recon_module):
        """Test successful DNS records retrieval"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name: example.com\\nAddress: 93.184.216.34"

        with patch("subprocess.run", return_value=mock_result):
            result = await recon_module._get_dns_records("example.com")

        assert len(result) > 0
        assert any("A:" in r for r in result)

    @pytest.mark.asyncio
    async def test_get_dns_records_failure(self, recon_module):
        """Test DNS records retrieval failure"""
        with patch("subprocess.run", side_effect=subprocess.SubprocessError("Command failed")):
            result = await recon_module._get_dns_records("example.com")

        assert result == ["No DNS records found"]

    @pytest.mark.asyncio
    async def test_get_dns_records_partial_failure(self, recon_module):
        """Test DNS records with some failures"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Name: example.com"

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise subprocess.SubprocessError("Failed")
            return mock_result

        with patch("subprocess.run", side_effect=side_effect):
            result = await recon_module._get_dns_records("example.com")

        # Should have some results from successful calls
        assert isinstance(result, list)


class TestReconWHOIS:
    """Test WHOIS functionality"""

    @pytest.mark.asyncio
    async def test_get_whois_success(self, recon_module):
        """Test successful WHOIS lookup"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Domain Name: EXAMPLE.COM\\nRegistrar: Example Registrar"

        with patch("subprocess.run", return_value=mock_result):
            result = await recon_module._get_whois("example.com")

        assert "EXAMPLE.COM" in result

    @pytest.mark.asyncio
    async def test_get_whois_failure(self, recon_module):
        """Test WHOIS lookup failure"""
        with patch("subprocess.run", side_effect=subprocess.SubprocessError("Command failed")):
            result = await recon_module._get_whois("example.com")

        assert result == "WHOIS not available"

    @pytest.mark.asyncio
    async def test_get_whois_nonzero_returncode(self, recon_module):
        """Test WHOIS with non-zero return code"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error"

        with patch("subprocess.run", return_value=mock_result):
            result = await recon_module._get_whois("example.com")

        assert result == "WHOIS failed"


class TestReconAttackVectorParsing:
    """Test attack vector parsing"""

    def test_parse_attack_vectors_with_keywords(self, recon_module):
        """Test parsing attack vectors from LLM response"""
        content = """
1. SQL Injection vector in login form
2. Attack: XSS vulnerability
3. Exploit path traversal
4. Vulnerability: Information disclosure
5. Regular line without keywords
6. Another vector: weak authentication
"""
        result = recon_module._parse_attack_vectors(content)

        assert len(result) == 5  # Should find 5 lines with keywords
        assert all(any(kw in line.lower() for kw in ["vector", "attack", "exploit", "vulnerability"]) for line in result)

    def test_parse_attack_vectors_limit(self, recon_module):
        """Test that parsing limits to 10 vectors"""
        content = "\n".join([f"Vector {i}" for i in range(20)])
        result = recon_module._parse_attack_vectors(content)

        assert len(result) == 10  # Should be limited to 10

    def test_parse_attack_vectors_empty(self, recon_module):
        """Test parsing empty content"""
        result = recon_module._parse_attack_vectors("")
        assert result == []


class TestReconNmapCommandGeneration:
    """Test nmap command generation"""

    @pytest.mark.asyncio
    async def test_generate_nmap_command_valid(self, recon_module, mock_orchestrator):
        """Test generating valid nmap command"""
        mock_orchestrator.process.return_value = MockResponse(content="nmap -sV -sC -p- -O example.com")

        result = await recon_module.generate_nmap_command("example.com", "normal")

        assert result.startswith("nmap")
        assert "example.com" in result

    @pytest.mark.asyncio
    async def test_generate_nmap_command_fallback(self, recon_module, mock_orchestrator):
        """Test fallback when LLM returns invalid command"""
        mock_orchestrator.process.return_value = MockResponse(content="This is not a valid nmap command")

        result = await recon_module.generate_nmap_command("example.com", "normal")

        assert result == "nmap -sV -sC -O example.com"

    @pytest.mark.asyncio
    async def test_generate_nmap_command_different_intensities(self, recon_module, mock_orchestrator):
        """Test generating commands for different intensities"""
        intensities = ["stealth", "normal", "aggressive"]

        for intensity in intensities:
            mock_orchestrator.process.return_value = MockResponse(content=f"nmap -sV {intensity} example.com")
            result = await recon_module.generate_nmap_command("example.com", intensity)
            assert result.startswith("nmap")


class TestReconSubdomainEnum:
    """Test subdomain enumeration"""

    @pytest.mark.asyncio
    async def test_subdomain_enum_success(self, recon_module, mock_orchestrator):
        """Test successful subdomain enumeration"""
        mock_orchestrator.process.return_value = MockResponse(content="admin, api, dev, staging, test, mail, ftp, vpn")

        result = await recon_module.subdomain_enum("example.com")

        assert len(result) > 0
        assert all(sub.endswith(".example.com") for sub in result)
        assert "admin.example.com" in result
        assert "api.example.com" in result

    @pytest.mark.asyncio
    async def test_subdomain_enum_multiline(self, recon_module, mock_orchestrator):
        """Test subdomain enumeration with multiline response"""
        mock_orchestrator.process.return_value = MockResponse(content="admin\\napi\\ndev\\nstaging")

        result = await recon_module.subdomain_enum("example.com")

        assert len(result) > 0
        assert all(sub.endswith(".example.com") for sub in result)

    @pytest.mark.asyncio
    async def test_subdomain_enum_no_duplicates(self, recon_module, mock_orchestrator):
        """Test that duplicates are removed"""
        mock_orchestrator.process.return_value = MockResponse(content="admin, admin, api, api, dev")

        result = await recon_module.subdomain_enum("example.com")

        # Should have unique values only
        assert len(result) == len(set(result))


class TestReconComprehensiveSubdomainScan:
    """Test comprehensive subdomain scanning"""

    @pytest.mark.asyncio
    async def test_comprehensive_subdomain_scan_no_scanner(self, recon_module):
        """Test scan when SubdomainScanner is not available"""
        with patch("modules.recon.SUBDOMAIN_SCANNER_AVAILABLE", False):
            with patch.object(recon_module, "subdomain_enum", return_value=["admin.example.com"]):
                result = await recon_module.comprehensive_subdomain_scan("example.com")

        assert result["domain"] == "example.com"
        assert result["method"] == "basic_llm"

    @pytest.mark.asyncio
    async def test_comprehensive_subdomain_scan_standard(self, recon_module):
        """Test standard subdomain scan"""
        mock_result = MagicMock()
        mock_result.ip_addresses = ["93.184.216.34"]
        mock_result.status_code = 200
        mock_result.server_header = "nginx"
        mock_result.technologies = ["nginx", "PHP"]
        mock_result.is_alive = True

        mock_scanner = MagicMock()
        mock_scanner.scan = AsyncMock(return_value={"admin.example.com": mock_result})

        with patch("modules.recon.SUBDOMAIN_SCANNER_AVAILABLE", True):
            with patch("modules.recon.SubdomainScanner", return_value=mock_scanner):
                result = await recon_module.comprehensive_subdomain_scan("example.com", advanced=False)

        assert result["domain"] == "example.com"
        assert result["total_discovered"] == 1
        assert result["live_hosts"] == 1
        assert result["method"] == "standard_scan"

    @pytest.mark.asyncio
    async def test_comprehensive_subdomain_scan_advanced(self, recon_module):
        """Test advanced subdomain scan"""
        mock_result = MagicMock()
        mock_result.ip_addresses = ["93.184.216.34"]
        mock_result.status_code = 200
        mock_result.server_header = "apache"
        mock_result.technologies = ["apache", "WordPress"]
        mock_result.is_alive = True

        mock_scanner = MagicMock()
        mock_scanner.scan_advanced = AsyncMock(return_value={"blog.example.com": mock_result})

        with patch("modules.recon.SUBDOMAIN_SCANNER_AVAILABLE", True):
            with patch("modules.recon.AdvancedSubdomainScanner", return_value=mock_scanner):
                result = await recon_module.comprehensive_subdomain_scan("example.com", advanced=True)

        assert result["method"] == "advanced_scan"
        assert "subdomains" in result


class TestReconAttackSurfaceDiscovery:
    """Test attack surface discovery"""

    @pytest.mark.asyncio
    async def test_discover_attack_surface_success(self, recon_module, mock_orchestrator):
        """Test successful attack surface discovery"""
        mock_orchestrator.process.return_value = MockResponse(
            content="Priority targets: admin.example.com\\nEntry points: login, api"
        )

        subdomain_data = {
            "total_discovered": 5,
            "live_hosts": 3,
            "subdomains": {
                "admin.example.com": {"is_alive": True},
                "api.example.com": {"is_alive": True},
                "dev.example.com": {"is_alive": False},
            },
        }

        with patch.object(recon_module, "comprehensive_subdomain_scan", return_value=subdomain_data):
            with patch.object(recon_module, "_resolve_ip", return_value="93.184.216.34"):
                with patch.object(recon_module, "_get_dns_records", return_value=["A: 93.184.216.34"]):
                    with patch.object(recon_module, "_get_whois", return_value="Domain: example.com"):
                        result = await recon_module.discover_attack_surface("example.com")

        assert result["domain"] == "example.com"
        assert "target_info" in result
        assert "subdomain_data" in result
        assert "analysis" in result
        assert "recommended_targets" in result

    @pytest.mark.asyncio
    async def test_discover_attack_surface_llm_failure(self, recon_module, mock_orchestrator):
        """Test attack surface discovery when LLM fails"""
        mock_orchestrator.process.side_effect = Exception("LLM Error")

        subdomain_data = {"total_discovered": 2, "live_hosts": 1, "subdomains": {"admin.example.com": {"is_alive": True}}}

        with patch.object(recon_module, "comprehensive_subdomain_scan", return_value=subdomain_data):
            with patch.object(recon_module, "_resolve_ip", return_value="93.184.216.34"):
                with patch.object(recon_module, "_get_dns_records", return_value=["A: 93.184.216.34"]):
                    with patch.object(recon_module, "_get_whois", return_value="Domain: example.com"):
                        result = await recon_module.discover_attack_surface("example.com")

        assert result["analysis"] == "LLM analysis not available"
        assert result["recommended_targets"] == ["admin.example.com"]

    @pytest.mark.asyncio
    async def test_discover_attack_surface_no_live_subdomains(self, recon_module, mock_orchestrator):
        """Test attack surface discovery with no live subdomains"""
        mock_orchestrator.process.return_value = MockResponse(content="No live targets found")

        subdomain_data = {"total_discovered": 2, "live_hosts": 0, "subdomains": {"dead.example.com": {"is_alive": False}}}

        with patch.object(recon_module, "comprehensive_subdomain_scan", return_value=subdomain_data):
            with patch.object(recon_module, "_resolve_ip", return_value="93.184.216.34"):
                with patch.object(recon_module, "_get_dns_records", return_value=["A: 93.184.216.34"]):
                    with patch.object(recon_module, "_get_whois", return_value="Domain: example.com"):
                        result = await recon_module.discover_attack_surface("example.com")

        # Should default to the main domain
        assert "example.com" in result["recommended_targets"]


class TestReconEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_concurrent_analyze_calls(self, recon_module, mock_orchestrator):
        """Test concurrent target analysis"""
        mock_orchestrator.process.return_value = MockResponse(content="Analysis complete")

        with patch.object(recon_module, "_resolve_ip", return_value="93.184.216.34"):
            with patch.object(recon_module, "_get_dns_records", return_value=["A: 93.184.216.34"]):
                with patch.object(recon_module, "_get_whois", return_value="Domain: example.com"):
                    # Run multiple analyses concurrently
                    tasks = [recon_module.analyze_target(f"example{i}.com") for i in range(5)]
                    results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["ip"] == "93.184.216.34" for r in results)

    def test_parse_attack_vectors_case_insensitive(self, recon_module):
        """Test that attack vector parsing is case insensitive"""
        content = "VECTOR: Test\nAttack: Test\nEXPLOIT: Test\nVULNERABILITY: Test"
        result = recon_module._parse_attack_vectors(content)

        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_subdomain_enum_filters_invalid(self, recon_module, mock_orchestrator):
        """Test that invalid subdomains are filtered"""
        mock_orchestrator.process.return_value = MockResponse(content="admin, sub.example.com, valid, another.test.com")

        result = await recon_module.subdomain_enum("example.com")

        # Should only include simple names without dots
        assert "admin.example.com" in result
        assert "valid.example.com" in result
        # Items with dots should be filtered
        assert not any("sub.example.com" in r for r in result)
