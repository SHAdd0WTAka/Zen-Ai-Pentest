"""Tests for risk_engine module"""

import pytest


class TestCVSS:
    """Test CVSS scoring"""

    def test_cvss_import(self):
        from risk_engine.cvss import CVSSCalculator

        assert CVSSCalculator is not None

    def test_cvss_from_cve(self):
        from risk_engine.cvss import CVSSCalculator

        calc = CVSSCalculator()
        score = calc.from_cve("CVE-2021-44228")
        assert score > 0

    def test_cvss_estimate(self):
        from risk_engine.cvss import CVSSCalculator

        calc = CVSSCalculator()
        score = calc.estimate("Remote code execution vulnerability")
        assert score > 0

    def test_cvss_get_details(self):
        from risk_engine.cvss import CVSSCalculator

        calc = CVSSCalculator()
        details = calc.get_details({"severity": "high"})
        assert details is not None


class TestFalsePositiveEngine:
    """Test false positive detection"""

    def test_fp_engine_import(self):
        from risk_engine.false_positive_engine import FalsePositiveEngine

        assert FalsePositiveEngine is not None


class TestBusinessImpact:
    """Test business impact scoring"""

    def test_business_impact_import(self):
        from risk_engine.business_impact import BusinessImpactCalculator

        assert BusinessImpactCalculator is not None
