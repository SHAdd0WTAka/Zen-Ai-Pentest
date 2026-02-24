"""
Comprehensive Tests for Enhanced Reconnaissance Module

This module tests the EnhancedReconModule class which provides
advanced reconnaissance capabilities including technology detection,
WAF detection, and directory brute-forcing.

Target Coverage: 70%+
"""

from unittest.mock import MagicMock, patch

import pytest

from modules.enhanced_recon import EnhancedReconModule


class TestEnhancedReconModuleInit:
    """Test EnhancedReconModule initialization"""

    def test_default_init(self):
        """Test default initialization"""
        with (
            patch("modules.enhanced_recon.ZenOrchestrator") as mock_orch,
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):

            mock_orch.return_value = MagicMock()
            recon = EnhancedReconModule()

            assert recon.orchestrator is not None

    def test_custom_orchestrator_init(self):
        """Test initialization with custom orchestrator"""
        with (
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):

            mock_orch = MagicMock()
            recon = EnhancedReconModule(orchestrator=mock_orch)

            assert recon.orchestrator == mock_orch


class TestTechnologyDetection:
    """Test technology detection functionality"""

    @pytest.fixture
    def recon(self):
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):
            return EnhancedReconModule()

    def test_technology_detection_success(self, recon):
        """Test successful technology detection"""
        mock_tech = MagicMock()
        mock_tech.name = "Apache"
        mock_tech.version = "2.4.41"
        mock_tech.confidence = 100
        mock_tech.category = "Web Server"

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "http://example.com"
        mock_result.technologies = [mock_tech]
        mock_result.headers = {"Server": "Apache/2.4.41"}

        with patch("modules.enhanced_recon.scan_sync", return_value=mock_result):
            result = recon.technology_detection("http://example.com")

            assert result["success"] is True
            assert result["url"] == "http://example.com"
            assert len(result["technologies"]) == 1
            assert result["technologies"][0]["name"] == "Apache"

    def test_technology_detection_failure(self, recon):
        """Test technology detection failure"""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Connection refused"

        with patch("modules.enhanced_recon.scan_sync", return_value=mock_result):
            result = recon.technology_detection("http://example.com")

            assert result["success"] is False
            assert "error" in result
            assert result["technologies"] == []

    def test_technology_detection_multiple_technologies(self, recon):
        """Test detection of multiple technologies"""
        # Create mock techs with proper attribute access
        mock_tech1 = MagicMock()
        mock_tech1.name = "Apache"
        mock_tech1.version = "2.4.41"
        mock_tech1.confidence = 100
        mock_tech1.category = "Web Server"

        mock_tech2 = MagicMock()
        mock_tech2.name = "PHP"
        mock_tech2.version = "7.4.0"
        mock_tech2.confidence = 95
        mock_tech2.category = "Programming Language"

        mock_tech3 = MagicMock()
        mock_tech3.name = "WordPress"
        mock_tech3.version = "5.8"
        mock_tech3.confidence = 90
        mock_tech3.category = "CMS"

        mock_techs = [mock_tech1, mock_tech2, mock_tech3]

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "http://example.com"
        mock_result.technologies = mock_techs
        mock_result.headers = {}

        with patch("modules.enhanced_recon.scan_sync", return_value=mock_result):
            result = recon.technology_detection("http://example.com")

            assert len(result["technologies"]) == 3
            tech_names = [t["name"] for t in result["technologies"]]
            assert "Apache" in tech_names
            assert "PHP" in tech_names
            assert "WordPress" in tech_names


class TestWAFDetection:
    """Test WAF detection functionality"""

    @pytest.fixture
    def recon(self):
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):
            return EnhancedReconModule()

    def test_waf_detection_found(self, recon):
        """Test WAF detection when WAF is found"""
        mock_waf = MagicMock()
        mock_waf.name = "Cloudflare"
        mock_waf.confidence = 95

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "http://example.com"
        mock_result.firewall_detected = True
        mock_result.wafs = [mock_waf]

        with patch("modules.enhanced_recon.detect_sync", return_value=mock_result):
            result = recon.waf_detection("http://example.com")

            assert result["success"] is True
            assert result["firewall_detected"] is True
            assert len(result["wafs"]) == 1
            assert result["wafs"][0]["name"] == "Cloudflare"

    def test_waf_detection_not_found(self, recon):
        """Test WAF detection when no WAF is found"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "http://example.com"
        mock_result.firewall_detected = False
        mock_result.wafs = []

        with patch("modules.enhanced_recon.detect_sync", return_value=mock_result):
            result = recon.waf_detection("http://example.com")

            assert result["success"] is True
            assert result["firewall_detected"] is False
            assert len(result["wafs"]) == 0

    def test_waf_detection_error(self, recon):
        """Test WAF detection with error"""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Connection timeout"
        mock_result.wafs = []

        with patch("modules.enhanced_recon.detect_sync", return_value=mock_result):
            result = recon.waf_detection("http://example.com")

            assert result["success"] is False
            assert "error" in result

    def test_waf_detection_multiple_wafs(self, recon):
        """Test detection of multiple WAFs"""
        mock_waf1 = MagicMock()
        mock_waf1.name = "Cloudflare"
        mock_waf1.confidence = 95

        mock_waf2 = MagicMock()
        mock_waf2.name = "ModSecurity"
        mock_waf2.confidence = 80

        mock_wafs = [mock_waf1, mock_waf2]

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "http://example.com"
        mock_result.firewall_detected = True
        mock_result.wafs = mock_wafs

        with patch("modules.enhanced_recon.detect_sync", return_value=mock_result):
            result = recon.waf_detection("http://example.com")

            assert len(result["wafs"]) == 2
            waf_names = [w["name"] for w in result["wafs"]]
            assert "Cloudflare" in waf_names
            assert "ModSecurity" in waf_names


class TestDirectoryBruteforce:
    """Test directory brute-forcing functionality"""

    @pytest.fixture
    def recon(self):
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):
            return EnhancedReconModule()

    def test_directory_bruteforce_success(self, recon):
        """Test successful directory bruteforce"""
        mock_finding = MagicMock()
        mock_finding.url = "http://example.com/admin"
        mock_finding.status_code = 200
        mock_finding.content_length = 1234
        mock_finding.content_words = 150

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.findings = [mock_finding]
        mock_result.total_requests = 1000
        mock_result.duration = 5.5

        with patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_result):
            result = recon.directory_bruteforce("http://example.com")

            assert result["success"] is True
            assert len(result["findings"]) == 1
            assert result["findings"][0]["url"] == "http://example.com/admin"
            assert result["total_requests"] == 1000
            assert result["duration"] == 5.5

    def test_directory_bruteforce_with_fuzz(self, recon):
        """Test directory bruteforce with FUZZ placeholder"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.findings = []
        mock_result.total_requests = 100
        mock_result.duration = 2.0

        with patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_result) as mock_bruteforce:
            recon.directory_bruteforce("http://example.com/FUZZ")

            # Should pass URL as-is
            mock_bruteforce.assert_called_once()

    def test_directory_bruteforce_adds_fuzz(self, recon):
        """Test that FUZZ is added if not present"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.findings = []
        mock_result.total_requests = 100
        mock_result.duration = 2.0

        with patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_result) as mock_bruteforce:
            recon.directory_bruteforce("http://example.com")

            # Should add /FUZZ
            call_args = mock_bruteforce.call_args
            assert "/FUZZ" in call_args[0][0]

    def test_directory_bruteforce_with_extensions(self, recon):
        """Test directory bruteforce with file extensions"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.findings = []
        mock_result.total_requests = 500
        mock_result.duration = 3.0

        with patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_result) as mock_bruteforce:
            recon.directory_bruteforce("http://example.com", extensions=["php", "html"])

            call_kwargs = mock_bruteforce.call_args[1]
            assert call_kwargs["extensions"] == ["php", "html"]

    def test_directory_bruteforce_with_wordlist(self, recon):
        """Test directory bruteforce with custom wordlist"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.findings = []
        mock_result.total_requests = 50
        mock_result.duration = 1.0

        with patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_result) as mock_bruteforce:
            recon.directory_bruteforce("http://example.com", wordlist="/path/to/wordlist.txt")

            call_kwargs = mock_bruteforce.call_args[1]
            assert call_kwargs["wordlist"] == "/path/to/wordlist.txt"

    def test_directory_bruteforce_error(self, recon):
        """Test directory bruteforce with error"""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.findings = []
        mock_result.total_requests = 0
        mock_result.duration = 0
        mock_result.error = "Connection refused"

        with patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_result):
            result = recon.directory_bruteforce("http://example.com")

            assert result["success"] is False
            assert "error" in result


class TestFullRecon:
    """Test full reconnaissance functionality"""

    @pytest.fixture
    def recon(self):
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):
            return EnhancedReconModule()

    def test_full_recon_with_url(self, recon):
        """Test full recon with URL input"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {
                "success": True,
                "technologies": [{"name": "Apache"}],
            }
            mock_waf.return_value = {
                "success": True,
                "firewall_detected": False,
            }
            mock_dir.return_value = {
                "success": True,
                "findings": [{"url": "/admin"}],
            }

            result = recon.full_recon("http://example.com")

            assert "target" in result
            assert "technology_scan" in result
            assert "waf_detection" in result
            assert "directory_scan" in result
            assert "summary" in result

    def test_full_recon_with_domain(self, recon):
        """Test full recon with domain input (no protocol)"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {"success": True, "technologies": []}
            mock_waf.return_value = {"success": True, "firewall_detected": False}
            mock_dir.return_value = {"success": True, "findings": []}

            result = recon.full_recon("example.com")

            # Should prepend http://
            assert result["target"] == "example.com"

    def test_full_recon_risk_levels(self, recon):
        """Test risk level calculation"""
        test_cases = [
            # (waf_detected, num_findings, expected_risk)
            (False, 0, "low"),
            (True, 0, "medium"),
            (True, 3, "medium"),
            (False, 10, "high"),
            (True, 10, "high"),
        ]

        for waf_detected, num_findings, expected_risk in test_cases:
            with (
                patch.object(recon, "technology_detection") as mock_tech,
                patch.object(recon, "waf_detection") as mock_waf,
                patch.object(recon, "directory_bruteforce") as mock_dir,
            ):

                mock_tech.return_value = {"success": True, "technologies": []}
                mock_waf.return_value = {
                    "success": True,
                    "firewall_detected": waf_detected,
                }
                mock_dir.return_value = {
                    "success": True,
                    "findings": [{"url": f"/path{i}"} for i in range(num_findings)],
                }

                result = recon.full_recon("http://example.com")
                assert (
                    result["summary"]["risk_level"] == expected_risk
                ), f"Expected {expected_risk} for waf={waf_detected}, findings={num_findings}"

    def test_full_recon_recommendations_no_waf(self, recon):
        """Test recommendations when no WAF detected"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {"success": True, "technologies": []}
            mock_waf.return_value = {"success": True, "firewall_detected": False}
            mock_dir.return_value = {"success": True, "findings": []}

            result = recon.full_recon("http://example.com")

            # Should recommend WAF implementation
            assert any("WAF" in r for r in result["summary"]["recommendations"])

    def test_full_recon_recommendations_outdated_software(self, recon):
        """Test recommendations for outdated software"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {
                "success": True,
                "technologies": [
                    {"name": "Apache", "version": "2.4.7"},
                ],
            }
            mock_waf.return_value = {"success": True, "firewall_detected": True}
            mock_dir.return_value = {"success": True, "findings": []}

            result = recon.full_recon("http://example.com")

            # Should recommend updating Apache
            assert any("Apache" in r and "Update" in r for r in result["summary"]["recommendations"])

    def test_full_recon_recommendations_sensitive_dirs(self, recon):
        """Test recommendations for sensitive directories"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {"success": True, "technologies": []}
            mock_waf.return_value = {"success": True, "firewall_detected": True}
            mock_dir.return_value = {
                "success": True,
                "findings": [{}, {}, {}, {}, {}, {}],  # 6 findings
            }

            result = recon.full_recon("http://example.com")

            # Should recommend restricting directories
            recs = result["summary"]["recommendations"]
            assert any("directory" in r.lower() or "access" in r.lower() for r in recs)

    def test_full_recon_summary_counts(self, recon):
        """Test summary counts"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {
                "success": True,
                "technologies": [{"name": "Apache"}, {"name": "PHP"}],
            }
            mock_waf.return_value = {"success": True, "firewall_detected": True}
            mock_dir.return_value = {
                "success": True,
                "findings": [{"url": "/admin"}],
            }

            result = recon.full_recon("http://example.com")

            assert result["summary"]["technologies_found"] == 2
            assert result["summary"]["waf_detected"] is True
            assert result["summary"]["directories_found"] == 1


class TestEnhancedReconIntegration:
    """Integration-style tests"""

    @pytest.fixture
    def recon(self):
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):
            return EnhancedReconModule()

    def test_complete_recon_workflow(self, recon):
        """Test complete reconnaissance workflow"""
        mock_tech_result = MagicMock()
        mock_tech_result.success = True
        mock_tech_result.url = "http://example.com"
        mock_tech_result.technologies = [
            MagicMock(name="Apache", version="2.4.41", confidence=100, category="Web Server"),
        ]
        mock_tech_result.headers = {"Server": "Apache"}

        mock_waf_result = MagicMock()
        mock_waf_result.success = True
        mock_waf_result.firewall_detected = True
        mock_waf_result.wafs = [MagicMock(name="Cloudflare", confidence=95)]

        mock_dir_result = MagicMock()
        mock_dir_result.success = True
        mock_dir_result.findings = [
            MagicMock(url="/admin", status_code=200, content_length=1000, content_words=50),
        ]
        mock_dir_result.total_requests = 1000
        mock_dir_result.duration = 5.0

        with (
            patch("modules.enhanced_recon.scan_sync", return_value=mock_tech_result),
            patch("modules.enhanced_recon.detect_sync", return_value=mock_waf_result),
            patch("modules.enhanced_recon.directory_bruteforce_sync", return_value=mock_dir_result),
        ):

            result = recon.full_recon("http://example.com")

            assert result["technology_scan"]["success"] is True
            assert result["waf_detection"]["firewall_detected"] is True
            assert len(result["directory_scan"]["findings"]) == 1
            assert result["summary"]["risk_level"] in ["low", "medium", "high"]

    def test_recon_handles_empty_results(self, recon):
        """Test that recon handles empty results gracefully"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {"success": True, "technologies": []}
            mock_waf.return_value = {"success": True, "firewall_detected": False}
            mock_dir.return_value = {"success": True, "findings": []}

            result = recon.full_recon("http://example.com")

            assert result["summary"]["technologies_found"] == 0
            assert result["summary"]["waf_detected"] is False
            assert result["summary"]["directories_found"] == 0

    def test_recon_handles_errors(self, recon):
        """Test that recon handles errors gracefully"""
        with (
            patch.object(recon, "technology_detection") as mock_tech,
            patch.object(recon, "waf_detection") as mock_waf,
            patch.object(recon, "directory_bruteforce") as mock_dir,
        ):

            mock_tech.return_value = {"success": False, "error": "Connection failed"}
            mock_waf.return_value = {"success": False, "error": "Timeout"}
            mock_dir.return_value = {"success": False, "error": "DNS error"}

            # Should not raise exception
            result = recon.full_recon("http://example.com")

            assert "technology_scan" in result
            assert "waf_detection" in result
            assert "directory_scan" in result


class TestToolIntegrations:
    """Test that tool integrations are properly initialized"""

    def test_ffuf_integration_initialized(self):
        """Test that FFuF integration is initialized"""
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration") as mock_ffuf,
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):

            mock_ffuf.return_value = MagicMock()
            recon = EnhancedReconModule()

            assert recon.ffuf is not None

    def test_whatweb_integration_initialized(self):
        """Test that WhatWeb integration is initialized"""
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration") as mock_whatweb,
            patch("modules.enhanced_recon.WAFW00FIntegration"),
        ):

            mock_whatweb.return_value = MagicMock()
            recon = EnhancedReconModule()

            assert recon.whatweb is not None

    def test_wafw00f_integration_initialized(self):
        """Test that WAFW00F integration is initialized"""
        with (
            patch("modules.enhanced_recon.ZenOrchestrator"),
            patch("modules.enhanced_recon.FFuFIntegration"),
            patch("modules.enhanced_recon.WhatWebIntegration"),
            patch("modules.enhanced_recon.WAFW00FIntegration") as mock_wafw00f,
        ):

            mock_wafw00f.return_value = MagicMock()
            recon = EnhancedReconModule()

            assert recon.wafw00f is not None
