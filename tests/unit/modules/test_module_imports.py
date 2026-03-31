"""Test module imports"""

import pytest


class TestModuleImports:
    """Test all modules can be imported"""

    def test_agent_coordinator_import(self):
        from modules.agent_coordinator import AgentCoordinator

        assert AgentCoordinator is not None

    def test_api_scanner_import(self):
        from modules.api_scanner import VulnerabilitySeverity

        assert VulnerabilitySeverity is not None

    def test_cloud_scanner_import(self):
        try:
            from modules.cloud_scanner import CloudScanner

            assert CloudScanner is not None
        except ImportError:
            pytest.skip("CloudScanner has missing dependencies")

    def test_cve_database_import(self):
        from modules.cve_database import CVEDatabase

        assert CVEDatabase is not None

    def test_enhanced_recon_import(self):
        from modules.enhanced_recon import EnhancedReconModule

        assert EnhancedReconModule is not None

    def test_false_positive_filter_import(self):
        from modules.false_positive_filter import FalsePositiveFilter

        assert FalsePositiveFilter is not None

    def test_report_generator_import(self):
        from modules.report_generator import ReportGenerator

        assert ReportGenerator is not None

    def test_risk_scoring_import(self):
        from modules.risk_scoring import SeverityLevel

        assert SeverityLevel is not None

    def test_subdomain_scanner_import(self):
        from modules.subdomain_scanner import SubdomainScanner

        assert SubdomainScanner is not None

    def test_vuln_scanner_import(self):
        from modules.vuln_scanner import Vulnerability

        assert Vulnerability is not None
