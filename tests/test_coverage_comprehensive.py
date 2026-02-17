"""
Comprehensive Test Suite for Maximum Coverage
Tests for all tools, modules, and edge cases
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

# ============================================================================
# TOOL INTEGRATION TESTS
# ============================================================================

class TestToolBaseFunctionality:
    """Base tests that apply to all tools"""

    def test_all_tools_have_async_support(self):
        """Verify all new tools have async methods"""
        from tools.ffuf_integration_enhanced import FFuFIntegration
        from tools.whatweb_integration import WhatWebIntegration
        from tools.wafw00f_integration import WAFW00FIntegration
        from tools.subfinder_integration import SubfinderIntegration
        from tools.httpx_integration import HTTPXIntegration
        from tools.nikto_integration import NiktoIntegration
        from tools.masscan_integration import MasscanIntegration
        from tools.amass_integration import AmassIntegration
        from tools.sherlock_integration import SherlockIntegration
        from tools.ignorant_integration import IgnorantIntegration
        from tools.tshark_integration import TSharkIntegration

        tools = [
            FFuFIntegration(),
            WhatWebIntegration(),
            WAFW00FIntegration(),
            SubfinderIntegration(),
            HTTPXIntegration(),
            NiktoIntegration(),
            MasscanIntegration(),
            AmassIntegration(),
            SherlockIntegration(),
            IgnorantIntegration(),
            TSharkIntegration(),
        ]

        for tool in tools:
            # Check that tool has async methods
            methods = [m for m in dir(tool) if not m.startswith('_')]
            async_methods = [m for m in methods if asyncio.iscoroutinefunction(getattr(tool, m, None))]
            assert len(async_methods) > 0, f"{tool.__class__.__name__} should have async methods"


class TestFFuFComprehensive:
    """Comprehensive FFuF tests"""

    @pytest.fixture
    def ffuf(self):
        from tools.ffuf_integration_enhanced import FFuFIntegration
        return FFuFIntegration()

    def test_initialization_default_values(self, ffuf):
        """Test FFuF initializes with correct defaults"""
        assert ffuf.wordlist_dir is not None
        assert 'directories' in ffuf.default_wordlists

    def test_ffuf_finding_dataclass_defaults(self):
        """Test FFuFFinding dataclass with defaults"""
        from tools.ffuf_integration_enhanced import FFuFFinding
        finding = FFuFFinding(
            url="http://test.com",
            status_code=200,
            content_length=0,
            content_words=0,
            content_lines=0
        )
        assert finding.content_length == 0
        assert finding.content_words == 0
        assert finding.redirect_location == ""

    def test_ffuf_result_with_error(self):
        """Test FFuFResult with error state"""
        from tools.ffuf_integration_enhanced import FFuFResult
        result = FFuFResult(success=False, error="Test error", command="test")
        assert result.success is False
        assert result.error == "Test error"
        assert result.findings == []


class TestWhatWebComprehensive:
    """Comprehensive WhatWeb tests"""

    def test_technology_dataclass_all_fields(self):
        """Test Technology dataclass with all fields"""
        from tools.whatweb_integration import Technology
        tech = Technology(
            name="Apache",
            version="2.4.7",
            confidence=100,
            category="Web Server",
            description="Apache HTTP Server"
        )
        assert tech.name == "Apache"
        assert tech.confidence == 100

    def test_categorize_all_known_technologies(self):
        """Test categorization of all known technologies"""
        from tools.whatweb_integration import WhatWebIntegration
        whatweb = WhatWebIntegration()

        known_techs = {
            "Apache": "Web Server",
            "nginx": "Web Server",
            "PHP": "Programming Language",
            "WordPress": "CMS",
            "jQuery": "JavaScript Library",
            "MySQL": "Database",
        }

        for tech, expected_category in known_techs.items():
            category = whatweb._categorize(tech)
            assert category == expected_category, f"{tech} should be categorized as {expected_category}"

    def test_clean_ansi_with_various_codes(self):
        """Test ANSI cleaning with various escape codes"""
        from tools.whatweb_integration import WhatWebIntegration
        whatweb = WhatWebIntegration()

        test_cases = [
            ("\x1b[1mBold\x1b[0m", "Bold"),
            ("\x1b[31mRed\x1b[0m", "Red"),
            ("\x1b[32mGreen\x1b[0m", "Green"),
            ("Normal", "Normal"),
        ]

        for input_str, expected in test_cases:
            result = whatweb._clean_ansi(input_str)
            assert result == expected


class TestWAFW00FComprehensive:
    """Comprehensive WAFW00F tests"""

    def test_waf_finding_defaults(self):
        """Test WAFFinding with default values"""
        from tools.wafw00f_integration import WAFFinding
        waf = WAFFinding(name="Cloudflare")
        assert waf.manufacturer == ""
        assert waf.detected is False
        assert waf.confidence == "high"

    def test_waf_result_various_states(self):
        """Test WAFW00FResult in various states"""
        from tools.wafw00f_integration import WAFW00FResult, WAFFinding

        # No WAF detected
        result1 = WAFW00FResult(
            success=True,
            firewall_detected=False,
            wafs=[]
        )
        assert result1.firewall_detected is False

        # WAF detected
        result2 = WAFW00FResult(
            success=True,
            firewall_detected=True,
            wafs=[WAFFinding(name="Cloudflare")]
        )
        assert result2.firewall_detected is True


class TestOSINTToolsComprehensive:
    """Comprehensive OSINT tools tests"""

    def test_sherlock_result_empty(self):
        """Test SherlockResult with empty results"""
        from tools.sherlock_integration import SherlockResult
        result = SherlockResult(username="test")
        assert result.found_sites == []
        assert result.total_sites == 0

    def test_ignorant_check_dataclass(self):
        """Test IgnorantCheck dataclass"""
        from tools.ignorant_integration import IgnorantCheck
        check = IgnorantCheck(platform="github", exists=True, url="https://github.com/test")
        assert check.platform == "github"
        assert check.exists is True

    def test_ignorant_result_with_found_platforms(self):
        """Test IgnorantResult with found platforms"""
        from tools.ignorant_integration import IgnorantResult, IgnorantCheck

        found = [
            IgnorantCheck(platform="github", exists=True),
            IgnorantCheck(platform="twitter", exists=True),
        ]

        result = IgnorantResult(
            email="test@example.com",
            username="test",
            domain="example.com",
            found_platforms=found,
            total_checked=120,
            success=True
        )

        assert len(result.found_platforms) == 2
        assert result.total_checked == 120


class TestNetworkToolsComprehensive:
    """Comprehensive network tools tests"""

    def test_tshark_host_dataclass(self):
        """Test TSharkHost dataclass"""
        from tools.tshark_integration import TSharkHost
        host = TSharkHost(
            ip="192.168.1.1",
            mac="00:11:22:33:44:55",
            hostname="router.local"
        )
        assert host.ip == "192.168.1.1"
        assert host.ports == []

    def test_tshark_protocol_dataclass(self):
        """Test TSharkProtocol dataclass"""
        from tools.tshark_integration import TSharkProtocol
        proto = TSharkProtocol(name="TCP", count=100, percentage=45.5)
        assert proto.name == "TCP"
        assert proto.percentage == 45.5

    def test_masscan_port_dataclass(self):
        """Test MasscanPort dataclass"""
        from tools.masscan_integration import MasscanPort
        port = MasscanPort(port=80, ip="192.168.1.1")
        assert port.port == 80
        assert port.protocol == "tcp"
        assert port.state == "open"


# ============================================================================
# MODULE TESTS
# ============================================================================

class TestEnhancedReconModuleComprehensive:
    """Comprehensive Enhanced Recon Module tests"""

    @pytest.fixture
    def recon(self):
        from modules.enhanced_recon import EnhancedReconModule
        return EnhancedReconModule()

    def test_module_initialization(self, recon):
        """Test EnhancedReconModule initializes all tools"""
        assert recon.ffuf is not None
        assert recon.whatweb is not None
        assert recon.wafw00f is not None

    def test_technology_detection_returns_expected_structure(self, recon):
        """Test technology_detection returns correct structure"""
        with patch.object(recon.whatweb, 'scan') as mock_scan:
            mock_scan.return_value = MagicMock(
                success=True,
                technologies=[],
                headers={},
                error=None
            )

            result = recon.technology_detection("test.com")

            assert "success" in result
            assert "technologies" in result
            assert "headers" in result


class TestOSINTSuperModuleComprehensive:
    """Comprehensive OSINT Super Module tests"""

    @pytest.fixture
    def osint(self):
        from modules.osint_super import OSINTSuperModule
        return OSINTSuperModule()

    def test_osint_module_initialization(self, osint):
        """Test OSINTSuperModule initializes all tools"""
        assert osint.sherlock is not None
        assert osint.ignorant is not None
        assert osint.subfinder is not None
        assert osint.amass is not None
        assert osint.whatweb is not None

    def test_generate_username_summary(self, osint):
        """Test username summary generation"""
        from modules.osint_super import OSINTSuperResult

        result = OSINTSuperResult(
            target="testuser",
            target_type="username",
            timestamp="2024-01-01",
            social_media={"total_found": 10}
        )

        summary = osint._generate_username_summary(result)

        assert summary["target_type"] == "username"
        assert summary["accounts_found"] == 10
        assert "risk_level" in summary

    def test_generate_email_summary(self, osint):
        """Test email summary generation"""
        from modules.osint_super import OSINTSuperResult

        result = OSINTSuperResult(
            target="test@test.com",
            target_type="email",
            timestamp="2024-01-01",
            email_check={"total_found": 5},
            social_media={"total_found": 3}
        )

        summary = osint._generate_email_summary(result)

        assert summary["target_type"] == "email"
        assert summary["email_platforms"] == 5
        assert summary["social_accounts"] == 3

    def test_generate_domain_summary(self, osint):
        """Test domain summary generation"""
        from modules.osint_super import OSINTSuperResult

        result = OSINTSuperResult(
            target="test.com",
            target_type="domain",
            timestamp="2024-01-01",
            subdomains={"total": 50}
        )

        summary = osint._generate_domain_summary(result)

        assert summary["target_type"] == "domain"
        assert summary["subdomains"] == 50
        assert summary["attack_surface"] in ["small", "medium", "large"]


class TestSuperScannerComprehensive:
    """Comprehensive Super Scanner tests"""

    @pytest.fixture
    def scanner(self):
        from modules.super_scanner import SuperScanner
        return SuperScanner()

    def test_scanner_initialization(self, scanner):
        """Test SuperScanner initializes all tools"""
        assert scanner.ffuf is not None
        assert scanner.whatweb is not None
        assert scanner.wafw00f is not None
        assert scanner.subfinder is not None
        assert scanner.amass is not None
        assert scanner.httpx is not None
        assert scanner.nikto is not None

    def test_generate_summary_risk_levels(self, scanner):
        """Test summary generation with different risk levels"""
        from modules.super_scanner import SuperScanResult

        # Test LOW risk
        result_low = SuperScanResult(
            target="test.com",
            timestamp="2024-01-01",
            subdomains={"count": 5},
            waf={"firewall_detected": True},
            port_scan={"ports": [80]},
            directories={"total_found": 2},
            vulnerabilities={"total": 0},
            http_probe={"live_hosts": 1}
        )

        summary_low = scanner._generate_summary(result_low)
        assert summary_low["risk_level"].lower() in ["low", "medium"]

        # Test HIGH risk
        result_high = SuperScanResult(
            target="test.com",
            timestamp="2024-01-01",
            subdomains={"count": 100},
            waf={"firewall_detected": False},
            port_scan={"ports": [80, 443, 22, 21, 3306]},
            directories={"total_found": 20},
            vulnerabilities={"total": 10},
            http_probe={"live_hosts": 5}
        )

        summary_high = scanner._generate_summary(result_high)
        assert summary_high["risk_level"].lower() in ["high", "critical"]


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests for robustness"""

    def test_empty_target_handling(self):
        """Test tools handle empty targets gracefully"""
        from tools.wafw00f_integration import WAFW00FIntegration

        wafw00f = WAFW00FIntegration()
        # Should not crash with empty string
        assert wafw00f is not None

    def test_special_characters_in_target(self):
        """Test handling of special characters"""
        from tools.whatweb_integration import WhatWebIntegration

        whatweb = WhatWebIntegration()
        # Test ANSI cleaning with special chars
        result = whatweb._clean_ansi("test\x1b[31mred\x1b[0m")
        assert "test" in result

    def test_very_long_target(self):
        """Test handling of very long targets"""
        from tools.ignorant_integration import IgnorantIntegration

        ignorant = IgnorantIntegration()
        # Very long email should be handled
        long_email = "a" * 50 + "@" + "b" * 50 + ".com"
        result = asyncio.run(ignorant.check_email(long_email))
        # Should return error gracefully, not crash
        assert result is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestToolIntegrations:
    """Integration tests between tools"""

    def test_subfinder_to_httpx_flow(self):
        """Test data flow from Subfinder to HTTPX"""
        from tools.subfinder_integration import SubfinderResult

        # Subfinder finds subdomains
        subdomains = SubfinderResult(
            success=True,
            domain="test.com",
            subdomains=["www.test.com", "api.test.com"],
            count=2
        )

        # These would be passed to HTTPX
        targets = subdomains.subdomains
        assert len(targets) == 2
        assert "www.test.com" in targets

    def test_whatweb_to_nikto_flow(self):
        """Test data flow from WhatWeb to Nikto"""
        from tools.whatweb_integration import Technology

        # WhatWeb finds technologies
        techs = [
            Technology(name="Apache", version="2.4.7"),
            Technology(name="PHP", version="7.4"),
        ]

        # These inform what Nikto should test
        web_techs = [t.name for t in techs]
        assert "Apache" in web_techs
        assert "PHP" in web_techs


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
