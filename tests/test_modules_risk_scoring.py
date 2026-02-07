"""Tests for risk scoring module"""

import pytest  # noqa: F401
from modules.risk_scoring import RiskScoringModule, RiskFactors, SeverityLevel


class TestRiskScoringModule:
    """Test RiskScoringModule functionality"""

    def test_init(self):
        """Test module initialization"""
        module = RiskScoringModule()
        assert module.name == "risk_scoring"
        assert module.enabled is True

    def test_calculate_cvss_score_log4j(self):
        """Test CVSS score for Log4j"""
        module = RiskScoringModule()
        score = module.calculate_cvss_score("CVE-2021-44228")
        assert score == 10.0

    def test_calculate_epss_score_log4j(self):
        """Test EPSS score for Log4j (high exploitation probability)"""
        module = RiskScoringModule()
        score = module.calculate_epss_score("CVE-2021-44228")
        assert score == 0.97

    def test_calculate_business_impact_production(self):
        """Test business impact for production"""
        module = RiskScoringModule()
        score = module.calculate_business_impact("production")
        assert score == 5

    def test_calculate_business_impact_database(self):
        """Test business impact for database"""
        module = RiskScoringModule()
        score = module.calculate_business_impact("database")
        assert score == 5

    def test_calculate_business_impact_workstation(self):
        """Test business impact for workstation"""
        module = RiskScoringModule()
        score = module.calculate_business_impact("workstation")
        assert score == 2

    def test_calculate_composite_score_max(self):
        """Test max composite score (100)"""
        module = RiskScoringModule()
        factors = RiskFactors(cvss_score=10.0, epss_score=1.0, business_impact=5, exposure=5, data_sensitivity=5)
        score = module.calculate_composite_score(factors)
        assert score == 100.0

    def test_calculate_composite_score_min(self):
        """Test min composite score (low values)"""
        module = RiskScoringModule()
        factors = RiskFactors(cvss_score=0.0, epss_score=0.0, business_impact=1, exposure=1, data_sensitivity=1)
        score = module.calculate_composite_score(factors)
        assert score < 20

    def test_score_to_severity_critical(self):
        """Test severity mapping - critical"""
        module = RiskScoringModule()
        severity = module.score_to_severity(85)
        assert severity == SeverityLevel.CRITICAL

    def test_score_to_severity_high(self):
        """Test severity mapping - high"""
        module = RiskScoringModule()
        severity = module.score_to_severity(65)
        assert severity == SeverityLevel.HIGH

    def test_score_to_severity_medium(self):
        """Test severity mapping - medium"""
        module = RiskScoringModule()
        severity = module.score_to_severity(45)
        assert severity == SeverityLevel.MEDIUM

    def test_score_to_severity_low(self):
        """Test severity mapping - low"""
        module = RiskScoringModule()
        severity = module.score_to_severity(25)
        assert severity == SeverityLevel.LOW

    def test_score_to_severity_info(self):
        """Test severity mapping - info"""
        module = RiskScoringModule()
        severity = module.score_to_severity(10)
        assert severity == SeverityLevel.INFO

    def test_score_vulnerability_structure(self):
        """Test vulnerability scoring returns correct structure"""
        module = RiskScoringModule()
        result = module.score_vulnerability("CVE-2021-44228", "production")

        assert "cve_id" in result
        assert "cvss_score" in result
        assert "epss_score" in result
        assert "composite_score" in result
        assert "severity" in result
        assert "priority" in result
        assert "remediation_timeline" in result

    def test_calculate_priority_p1(self):
        """Test P1 priority (critical)"""
        module = RiskScoringModule()
        priority = module._calculate_priority(85, 0.8)
        assert "P1" in priority

    def test_calculate_priority_p3(self):
        """Test P3 priority (medium)"""
        module = RiskScoringModule()
        priority = module._calculate_priority(45, 0.3)
        assert "P3" in priority

    def test_get_remediation_timeline_critical(self):
        """Test remediation timeline for critical"""
        module = RiskScoringModule()
        timeline = module._get_remediation_timeline(SeverityLevel.CRITICAL)
        assert "24 hours" in timeline

    def test_score_findings_sorting(self):
        """Test that findings are sorted by score"""
        module = RiskScoringModule()
        findings = [
            {"cve_id": "CVE-2024-9999", "asset_type": "workstation"},
            {"cve_id": "CVE-2021-44228", "asset_type": "production"},
        ]
        scored = module.score_findings(findings)

        # Log4j (critical) should be first
        assert scored[0]["cve_id"] == "CVE-2021-44228"

    def test_get_info(self):
        """Test module info"""
        module = RiskScoringModule()
        info = module.get_info()
        assert info["name"] == "risk_scoring"
        assert "CVSS" in info["description"]
        assert "EPSS" in info["description"]
