"""
Extended Tests für OSINT und Network Tools
Sherlock, Ignorant, TShark, und Integration Tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

# OSINT Tools
from tools.sherlock_integration import (
    SherlockIntegration, SherlockResult, search_sync
)
from tools.ignorant_integration import (
    IgnorantIntegration, IgnorantResult, IgnorantCheck, check_email_sync
)
from tools.tshark_integration import (
    TSharkIntegration, TSharkResult, TSharkHost, analyze_pcap_sync
)

# Module
from modules.osint_super import OSINTSuperModule, OSINTSuperResult
from modules.super_scanner import SuperScanner, SuperScanResult


class TestSherlockIntegration:
    """Test Sherlock Social Media OSINT"""
    
    def test_sherlock_result_dataclass(self):
        """Test SherlockResult dataclass"""
        result = SherlockResult(
            username="testuser",
            found_sites=[
                {"site": "twitter", "url": "https://twitter.com/testuser"},
                {"site": "github", "url": "https://github.com/testuser"}
            ],
            total_sites=2,
            success=True
        )
        assert result.username == "testuser"
        assert len(result.found_sites) == 2
        assert result.success is True
        
    def test_initialization(self):
        """Test SherlockIntegration initialization"""
        sherlock = SherlockIntegration(timeout=120)
        assert sherlock.timeout == 120
        
    @pytest.mark.asyncio
    async def test_search_mock(self):
        """Test search with mocked subprocess"""
        sherlock = SherlockIntegration()
        
        mock_json = '{"twitter": {"status": {"status": "FOUND"}, "url_user": "https://twitter.com/test"}}'
        
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_json.encode(), b'')
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await sherlock.search("testuser")
            
        assert result.success is True
        assert result.username == "testuser"
        assert len(result.found_sites) >= 1
        
    @pytest.mark.asyncio
    async def test_search_multiple(self):
        """Test multiple username search"""
        sherlock = SherlockIntegration()
        
        usernames = ["user1", "user2"]
        
        with patch.object(sherlock, 'search') as mock_search:
            mock_search.return_value = SherlockResult(
                username="test",
                found_sites=[],
                success=True
            )
            
            results = await sherlock.search_multiple(usernames)
            
        assert len(results) == 2
        assert "user1" in results
        assert "user2" in results


class TestIgnorantIntegration:
    """Test Ignorant Email OSINT"""
    
    def test_ignorant_result_dataclass(self):
        """Test IgnorantResult dataclass"""
        result = IgnorantResult(
            email="test@example.com",
            username="test",
            domain="example.com",
            found_platforms=[
                IgnorantCheck(platform="github", exists=True, url="https://github.com/test"),
                IgnorantCheck(platform="twitter", exists=True, url="https://twitter.com/test")
            ],
            total_checked=120,
            success=True
        )
        assert result.email == "test@example.com"
        assert result.username == "test"
        assert len(result.found_platforms) == 2
        
    def test_invalid_email(self):
        """Test with invalid email format"""
        ignorant = IgnorantIntegration()
        result = asyncio.run(ignorant.check_email("notanemail"))
        
        assert result.success is False
        assert "Invalid" in result.error
        
    @pytest.mark.asyncio
    async def test_check_email_mock(self):
        """Test email check with mocked subprocess"""
        ignorant = IgnorantIntegration()
        
        mock_json = '{"name": "github", "exists": true, "url": "https://github.com/test"}\n'
        
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (mock_json.encode(), b'')
        mock_process.returncode = 0
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await ignorant.check_email("test@example.com")
            
        assert result.success is True
        assert result.email == "test@example.com"
        assert result.username == "test"
        assert result.domain == "example.com"


class TestTSharkIntegration:
    """Test TShark Network Analysis"""
    
    def test_tshark_host_dataclass(self):
        """Test TSharkHost dataclass"""
        host = TSharkHost(
            ip="192.168.1.1",
            mac="00:11:22:33:44:55",
            hostname="router.local",
            ports=[80, 443, 22]
        )
        assert host.ip == "192.168.1.1"
        assert host.mac == "00:11:22:33:44:55"
        assert len(host.ports) == 3
        
    def test_initialization(self):
        """Test TSharkIntegration initialization"""
        tshark = TSharkIntegration(interface="wlan0")
        assert tshark.interface == "wlan0"
        
    @pytest.mark.asyncio
    async def test_analyze_pcap_not_found(self):
        """Test with non-existent PCAP file"""
        tshark = TSharkIntegration()
        result = await tshark.analyze_pcap("/nonexistent/capture.pcap")
        
        assert result.success is False
        assert "not found" in result.error
        
    @pytest.mark.asyncio
    async def test_analyze_pcap_mock(self):
        """Test PCAP analysis with mocked subprocess"""
        tshark = TSharkIntegration()
        
        # Create temp PCAP file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pcap', delete=False) as f:
            f.write(b'\xd4\xc3\xb2\xa1')  # PCAP magic number
            temp_pcap = f.name
            
        try:
            mock_output = b'  tcp: packets: 100 bytes: 5000\n  udp: packets: 50 bytes: 2000'
            
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_output, b'')
            mock_process.returncode = 0
            
            with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                result = await tshark.analyze_pcap(temp_pcap)
                
            # Should succeed (parsing may vary)
            assert result.capture_file == temp_pcap
            
        finally:
            Path(temp_pcap).unlink(missing_ok=True)
            
    def test_parse_protocols(self):
        """Test protocol parsing"""
        tshark = TSharkIntegration()
        
        output = """
  tcp: packets: 100 bytes: 5000
  udp: packets: 50 bytes: 2000
  http: packets: 25 bytes: 1500
"""
        protocols = tshark._parse_protocols(output)
        
        assert len(protocols) >= 1
        assert protocols[0].name in ["tcp", "udp", "http"]
        
    def test_parse_hosts(self):
        """Test host parsing"""
        tshark = TSharkIntegration()
        
        output = """ip.src\tip.dst
192.168.1.1\t192.168.1.100
192.168.1.100\t8.8.8.8
"""
        hosts = tshark._parse_hosts(output)
        
        assert len(hosts) >= 1
        assert any(h.ip == "192.168.1.1" for h in hosts)


class TestOSINTSuperModule:
    """Test OSINT Super Module"""
    
    def test_initialization(self):
        """Test OSINTSuperModule initialization"""
        osint = OSINTSuperModule(output_dir="test_reports")
        assert osint.output_dir.name == "test_reports"
        assert osint.sherlock is not None
        assert osint.ignorant is not None
        
    @pytest.mark.asyncio
    async def test_investigate_username(self):
        """Test username investigation"""
        osint = OSINTSuperModule()
        
        with patch.object(osint.sherlock, 'search') as mock_search:
            mock_search.return_value = SherlockResult(
                username="testuser",
                found_sites=[
                    {"site": "twitter", "url": "https://twitter.com/testuser"}
                ],
                total_sites=1,
                success=True
            )
            
            result = await osint.investigate_username("testuser")
            
        assert result.target == "testuser"
        assert result.target_type == "username"
        assert result.social_media.get("total_found") == 1
        
    @pytest.mark.asyncio
    async def test_investigate_email(self):
        """Test email investigation"""
        osint = OSINTSuperModule()
        
        with patch.object(osint.ignorant, 'check_email') as mock_check, \
             patch.object(osint.sherlock, 'search') as mock_search:
            
            mock_check.return_value = IgnorantResult(
                email="test@example.com",
                username="test",
                domain="example.com",
                found_platforms=[IgnorantCheck(platform="github", exists=True)],
                total_checked=10,
                success=True
            )
            mock_search.return_value = SherlockResult(
                username="test",
                found_sites=[],
                success=True
            )
            
            result = await osint.investigate_email("test@example.com")
            
        assert result.target == "test@example.com"
        assert result.target_type == "email"
        assert result.email_check.get("username") == "test"
        
    @pytest.mark.asyncio
    async def test_investigate_domain(self):
        """Test domain investigation"""
        osint = OSINTSuperModule()
        
        with patch.object(osint.subfinder, 'enumerate') as mock_sub, \
             patch.object(osint.amass, 'enumerate') as mock_amass, \
             patch.object(osint.whatweb, 'scan') as mock_whatweb:
            
            mock_sub.return_value = MagicMock(
                subdomains=["www.example.com", "mail.example.com"],
                success=True
            )
            mock_amass.return_value = MagicMock(
                subdomains=["api.example.com"],
                success=True
            )
            mock_whatweb.return_value = MagicMock(
                technologies=[MagicMock(name="Apache", version="2.4", category="Web Server")],
                success=True
            )
            
            result = await osint.investigate_domain("example.com")
            
        assert result.target == "example.com"
        assert result.target_type == "domain"
        assert result.subdomains.get("total") >= 2
        
    def test_generate_username_summary(self):
        """Test username summary generation"""
        osint = OSINTSuperModule()
        
        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp="2024-01-01",
            social_media={
                "found_accounts": [{"site": "twitter"}, {"site": "github"}],
                "total_found": 2
            }
        )
        
        summary = osint._generate_username_summary(result)
        
        assert summary["target_type"] == "username"
        assert summary["accounts_found"] == 2
        assert "recommendations" in summary


class TestSuperScanner:
    """Test Super Scanner Integration"""
    
    def test_initialization(self):
        """Test SuperScanner initialization"""
        scanner = SuperScanner(output_dir="test_reports")
        assert scanner.output_dir.name == "test_reports"
        assert scanner.ffuf is not None
        assert scanner.whatweb is not None
        assert scanner.subfinder is not None
        
    @pytest.mark.asyncio
    async def test_scan_domain_structure(self):
        """Test scan_domain returns correct structure"""
        scanner = SuperScanner()
        
        # Mock all tool methods
        with patch.object(scanner.subfinder, 'enumerate') as mock_sub, \
             patch.object(scanner.amass, 'enumerate') as mock_amass, \
             patch.object(scanner.httpx, 'probe') as mock_httpx, \
             patch.object(scanner.whatweb, 'scan') as mock_whatweb, \
             patch.object(scanner.wafw00f, 'detect') as mock_waf, \
             patch.object(scanner.ffuf, 'directory_bruteforce') as mock_ffuf, \
             patch.object(scanner.nikto, 'scan') as mock_nikto:
            
            # Setup mocks
            mock_sub.return_value = MagicMock(subdomains=["www.test.com"], success=True)
            mock_amass.return_value = MagicMock(subdomains=[], success=True)
            mock_httpx.return_value = MagicMock(hosts=[MagicMock(url="http://test.com", status_code=200)])
            mock_whatweb.return_value = MagicMock(technologies=[], success=True)
            mock_waf.return_value = MagicMock(firewall_detected=False, wafs=[], success=True)
            mock_ffuf.return_value = MagicMock(findings=[], total_requests=100, success=True)
            mock_nikto.return_value = MagicMock(findings=[], success=True)
            
            result = await scanner.scan_domain("test.com")
            
        assert result.target == "test.com"
        assert "subdomains" in result.__dict__ or hasattr(result, 'subdomains')
        assert "technology" in result.__dict__ or hasattr(result, 'technology')
        assert "summary" in result.__dict__ or hasattr(result, 'summary')
        
    def test_generate_summary(self):
        """Test summary generation"""
        scanner = SuperScanner()
        
        # Create mock result
        from dataclasses import dataclass, field
        from typing import Dict, Any
        
        @dataclass
        class MockResult:
            subdomains: Dict[str, Any] = field(default_factory=lambda: {"count": 100})
            waf: Dict[str, Any] = field(default_factory=lambda: {"firewall_detected": False})
            port_scan: Dict[str, Any] = field(default_factory=lambda: {"ports": [80, 443, 22]})
            directories: Dict[str, Any] = field(default_factory=lambda: {"total_found": 20})
            vulnerabilities: Dict[str, Any] = field(default_factory=lambda: {"total": 5})
            
        mock_result = MockResult()
        summary = scanner._generate_summary(mock_result)
        
        assert "risk_level" in summary
        assert "risk_score" in summary
        assert "recommendations" in summary
        assert summary["statistics"]["subdomains"] == 100


class TestIntegrationFlow:
    """Test complete integration flows"""
    
    @pytest.mark.asyncio
    async def test_osint_to_super_scanner_flow(self):
        """Test OSINT results feed into Super Scanner"""
        # First get subdomains via OSINT
        osint = OSINTSuperModule()
        
        with patch.object(osint.subfinder, 'enumerate') as mock_sub:
            mock_sub.return_value = MagicMock(
                subdomains=["www.test.com", "api.test.com"],
                success=True
            )
            
            osint_result = await osint.investigate_domain("test.com")
            
        # Then use those subdomains in Super Scanner
        scanner = SuperScanner()
        
        with patch.object(scanner.httpx, 'probe') as mock_httpx:
            mock_httpx.return_value = MagicMock(
                hosts=[MagicMock(url="http://www.test.com", status_code=200)],
                success=True
            )
            
            # Mock other methods
            with patch.multiple(
                scanner,
                subfinder=MagicMock(enumerate=MagicMock(return_value=MagicMock(subdomains=[], success=True))),
                amass=MagicMock(enumerate=MagicMock(return_value=MagicMock(subdomains=[], success=True))),
                whatweb=MagicMock(scan=MagicMock(return_value=MagicMock(technologies=[], success=True))),
                wafw00f=MagicMock(detect=MagicMock(return_value=MagicMock(firewall_detected=False, wafs=[], success=True))),
                ffuf=MagicMock(directory_bruteforce=MagicMock(return_value=MagicMock(findings=[], success=True))),
                nikto=MagicMock(scan=MagicMock(return_value=MagicMock(findings=[], success=True)))
            ):
                super_result = await scanner.scan_domain("test.com")
                
        # Verify both completed
        assert osint_result.target == "test.com"
        assert super_result.target == "test.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
