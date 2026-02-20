"""
Risk Engine Tests
=================

Comprehensive tests for the risk scoring engine including:
- RiskScorer class
- CVSS calculation
- EPSS client
- Business impact calculation
- Mock external API calls
"""

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest

from risk_engine.business_impact import BusinessImpactCalculator
from risk_engine.cvss import CVSSCalculator
from risk_engine.epss import EPSSClient
from risk_engine.scorer import RiskScore, RiskScorer, SeverityLevel


class TestCVSSCalculator:
    """Test CVSS v3.1 score calculation"""

    def test_calculate_network_attack_vector(self):
        """Calculate CVSS with network attack vector"""
        calc = CVSSCalculator()

        metrics = {
            "AV": "N",  # Network
            "AC": "L",  # Low
            "PR": "N",  # None
            "UI": "N",  # None
            "S": "U",  # Unchanged
            "C": "H",  # High
            "I": "H",  # High
            "A": "H",  # High
        }

        score = calc.calculate(metrics)
        assert 9.0 <= score <= 10.0  # Critical severity

    def test_calculate_local_attack_vector(self):
        """Calculate CVSS with local attack vector"""
        calc = CVSSCalculator()

        metrics = {
            "AV": "L",  # Local
            "AC": "H",  # High
            "PR": "H",  # High
            "UI": "R",  # Required
            "S": "U",  # Unchanged
            "C": "L",  # Low
            "I": "L",  # Low
            "A": "L",  # Low
        }

        score = calc.calculate(metrics)
        assert 0.0 <= score <= 4.0  # Low severity

    def test_calculate_scope_changed(self):
        """Calculate CVSS with changed scope"""
        calc = CVSSCalculator()

        metrics = {
            "AV": "N",
            "AC": "L",
            "PR": "L",
            "UI": "N",
            "S": "C",  # Changed
            "C": "H",
            "I": "H",
            "A": "H",
        }

        score = calc.calculate(metrics)
        assert score > 0  # Should have valid score

    def test_calculate_default_values(self):
        """Calculate CVSS with default values"""
        calc = CVSSCalculator()

        # Empty metrics should use defaults
        score = calc.calculate({})
        assert 0.0 <= score <= 10.0

    def test_calculate_invalid_metrics(self):
        """Handle invalid metric values gracefully"""
        calc = CVSSCalculator()

        metrics = {
            "AV": "INVALID",
            "AC": "INVALID",
        }

        score = calc.calculate(metrics)
        assert 0.0 <= score <= 10.0  # Should return default on error

    def test_from_cve_known_cves(self):
        """Get CVSS score for known CVEs"""
        calc = CVSSCalculator()

        # Log4j
        score = calc.from_cve("CVE-2021-44228")
        assert score == 10.0

        # EternalBlue
        score = calc.from_cve("CVE-2017-0144")
        assert score == 8.1

        # Heartbleed
        score = calc.from_cve("CVE-2014-0160")
        assert score == 5.0

    def test_from_cve_unknown_cve(self):
        """Return default score for unknown CVE"""
        calc = CVSSCalculator()

        score = calc.from_cve("CVE-9999-99999")
        assert score == 5.0  # Default

    def test_from_cve_case_insensitive(self):
        """CVE IDs should be case insensitive"""
        calc = CVSSCalculator()

        score_lower = calc.from_cve("cve-2021-44228")
        score_upper = calc.from_cve("CVE-2021-44228")

        assert score_lower == score_upper

    def test_estimate_rce(self):
        """Estimate CVSS for RCE vulnerability"""
        calc = CVSSCalculator()

        description = "Remote code execution vulnerability allows arbitrary code execution"
        score = calc.estimate(description)

        assert score >= 9.0  # RCE should be critical

    def test_estimate_sql_injection(self):
        """Estimate CVSS for SQL injection"""
        calc = CVSSCalculator()

        description = "SQL injection vulnerability in login form"
        score = calc.estimate(description)

        assert score >= 8.0  # SQLi should be high

    def test_estimate_xss(self):
        """Estimate CVSS for XSS"""
        calc = CVSSCalculator()

        description = "Cross-site scripting vulnerability in comment field"
        score = calc.estimate(description)

        assert 6.0 <= score <= 7.0  # XSS typically medium-high

    def test_estimate_with_network_keyword(self):
        """Adjust score for network accessibility"""
        calc = CVSSCalculator()

        description = "Remote unauthenticated SQL injection"
        score = calc.estimate(description)

        # Should be boosted due to "remote" and "unauthenticated"
        assert score >= 8.0

    def test_get_details(self):
        """Get detailed CVSS breakdown"""
        calc = CVSSCalculator()

        finding = {
            "cvss_score": 8.5,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "cvss_version": "3.1",
        }

        details = calc.get_details(finding)

        assert details["base_score"] == 8.5
        assert details["severity"] == "High"
        assert details["vector"] == finding["cvss_vector"]
        assert details["version"] == "3.1"

    def test_get_details_severity_levels(self):
        """Test all severity levels"""
        calc = CVSSCalculator()

        test_cases = [
            (9.5, "Critical"),
            (8.0, "High"),
            (5.5, "Medium"),
            (2.0, "Low"),
            (0.0, "None"),
        ]

        for score, expected_severity in test_cases:
            finding = {"cvss_score": score}
            details = calc.get_details(finding)
            assert details["severity"] == expected_severity

    def test_get_vector_from_metrics(self):
        """Generate CVSS vector string"""
        calc = CVSSCalculator()

        metrics = {
            "AV": "N",
            "AC": "L",
            "PR": "N",
            "UI": "N",
            "S": "U",
            "C": "H",
            "I": "H",
            "A": "H",
        }

        vector = calc.get_vector_from_metrics(metrics)

        assert vector.startswith("CVSS:3.1")
        assert "AV:N" in vector
        assert "AC:L" in vector


class TestEPSSClient:
    """Test EPSS (Exploit Prediction Scoring System) client"""

    def test_init_default_cache_duration(self):
        """Initialize with default cache duration"""
        client = EPSSClient()

        assert client.cache_duration == timedelta(hours=24)
        assert client.cache == {}

    def test_init_custom_cache_duration(self):
        """Initialize with custom cache duration"""
        client = EPSSClient(cache_duration=12)

        assert client.cache_duration == timedelta(hours=12)

    @patch("risk_engine.epss.requests.get")
    def test_get_score_success(self, mock_get):
        """Successfully fetch EPSS score"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": 0.95}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        score = client.get_score("CVE-2021-44228")

        assert score == 0.95
        mock_get.assert_called_once()

    @patch("risk_engine.epss.requests.get")
    def test_get_score_caching(self, mock_get):
        """Cache EPSS scores"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()

        # First call - should hit API
        score1 = client.get_score("CVE-2021-44228")
        assert mock_get.call_count == 1

        # Second call - should use cache
        score2 = client.get_score("CVE-2021-44228")
        assert mock_get.call_count == 1  # No additional API call

        assert score1 == score2

    @patch("risk_engine.epss.requests.get")
    def test_get_score_api_error(self, mock_get):
        """Handle API errors gracefully"""
        from requests import RequestException

        mock_get.side_effect = RequestException("API Error")

        client = EPSSClient()
        score = client.get_score("CVE-2021-44228")

        assert score == 0.0  # Default on error

    def test_get_score_no_cve(self):
        """Return 0 for missing CVE ID in finding"""
        client = EPSSClient()
        
        # When CVE ID is not provided, _get_epss should return 0.0
        finding = {"description": "Test without CVE"}
        scorer = RiskScorer(enable_epss=True, enable_business_context=False)
        score = scorer._get_epss(finding)

        assert score == 0.0

    @patch("risk_engine.epss.requests.get")
    def test_get_batch_scores(self, mock_get):
        """Fetch multiple EPSS scores"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"cve": "CVE-2021-44228", "epss": 0.95},
                {"cve": "CVE-2017-0144", "epss": 0.85},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        scores = client.get_batch_scores(["CVE-2021-44228", "CVE-2017-0144"])

        assert scores["CVE-2021-44228"] == 0.95
        assert scores["CVE-2017-0144"] == 0.85

    @patch("risk_engine.epss.requests.get")
    def test_get_batch_scores_missing_cve(self, mock_get):
        """Handle missing CVEs in batch response"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        scores = client.get_batch_scores(["CVE-2021-44228", "CVE-UNKNOWN"])

        assert scores["CVE-2021-44228"] == 0.95
        assert scores["CVE-UNKNOWN"] == 0.0  # Default for missing

    def test_get_batch_scores_empty_list(self):
        """Handle empty CVE list"""
        client = EPSSClient()
        scores = client.get_batch_scores([])

        assert scores == {}

    @patch("risk_engine.epss.requests.get")
    def test_get_percentile(self, mock_get):
        """Fetch EPSS percentile"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": 0.95, "percentile": 0.99}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        percentile = client.get_percentile("CVE-2021-44228")

        assert percentile == 0.99

    @patch("risk_engine.epss.requests.get")
    def test_get_percentile_error(self, mock_get):
        """Handle percentile fetch error"""
        mock_get.side_effect = Exception("API Error")

        client = EPSSClient()
        percentile = client.get_percentile("CVE-2021-44228")

        assert percentile is None

    def test_interpret_score_very_high(self):
        """Interpret very high EPSS score"""
        client = EPSSClient()

        interpretation = client.interpret_score(0.6)
        assert "Very High" in interpretation

    def test_interpret_score_high(self):
        """Interpret high EPSS score"""
        client = EPSSClient()

        interpretation = client.interpret_score(0.4)
        assert "High" in interpretation

    def test_interpret_score_medium(self):
        """Interpret medium EPSS score"""
        client = EPSSClient()

        interpretation = client.interpret_score(0.15)
        assert "Medium" in interpretation

    def test_interpret_score_low(self):
        """Interpret low EPSS score"""
        client = EPSSClient()

        interpretation = client.interpret_score(0.07)
        assert "Low" in interpretation

    def test_interpret_score_very_low(self):
        """Interpret very low EPSS score"""
        client = EPSSClient()

        interpretation = client.interpret_score(0.01)
        assert "Very Low" in interpretation

    @patch("risk_engine.epss.requests.get")
    def test_should_prioritize_true(self, mock_get):
        """Check if CVE should be prioritized"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.5}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        should_prioritize = client.should_prioritize("CVE-2021-44228", threshold=0.2)

        assert should_prioritize is True

    @patch("risk_engine.epss.requests.get")
    def test_should_prioritize_false(self, mock_get):
        """Check if CVE should not be prioritized"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.1}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        should_prioritize = client.should_prioritize("CVE-2021-44228", threshold=0.2)

        assert should_prioritize is False


class TestBusinessImpactCalculator:
    """Test business impact calculation"""

    def test_calculate_internet_facing(self):
        """Calculate impact for internet-facing asset"""
        calc = BusinessImpactCalculator()

        finding = {"description": "Test vulnerability"}
        context = {"internet_facing": True, "data_sensitivity": "public"}

        score = calc.calculate(finding, context)

        assert 0.0 <= score <= 1.0
        # Internet facing should boost score
        assert score >= 0.3

    def test_calculate_pii_data(self):
        """Calculate impact for PII data"""
        calc = BusinessImpactCalculator()

        finding = {"description": "Test vulnerability"}
        context = {"data_sensitivity": "pii", "network_exposure": "internal"}

        score = calc.calculate(finding, context)

        # PII should have high impact
        assert score >= 0.5

    def test_calculate_pci_compliance(self):
        """Calculate impact for PCI-DSS scope"""
        calc = BusinessImpactCalculator()

        finding = {"description": "Unencrypted card data storage with SSL unencrypted"}
        context = {"compliance": ["pci-dss"], "network_exposure": "internal", "data_sensitivity": "financial"}

        score = calc.calculate(finding, context)

        # PCI with violation and financial data should have higher impact
        assert score >= 0.4

    def test_calculate_critical_asset(self):
        """Calculate impact for critical asset"""
        calc = BusinessImpactCalculator()

        finding = {"description": "Test vulnerability"}
        context = {"asset_criticality": "critical", "network_exposure": "internal"}

        score = calc.calculate(finding, context)

        # Critical asset should have higher impact
        assert score >= 0.3

    def test_score_internet_facing_variations(self):
        """Test different network exposure levels"""
        calc = BusinessImpactCalculator()

        test_cases = [
            ("internet", 1.0),
            ("dmz", 0.6),
            ("internal", 0.3),
            ("airgapped", 0.1),
        ]

        for exposure, expected_score in test_cases:
            context = {"network_exposure": exposure}
            score = calc._score_internet_facing(context)
            assert score == expected_score

    def test_score_data_sensitivity_variations(self):
        """Test different data sensitivity levels"""
        calc = BusinessImpactCalculator()

        test_cases = [
            ("pii", 1.0),
            ("phi", 1.0),
            ("financial", 1.0),
            ("confidential", 0.7),
            ("internal", 0.4),
            ("public", 0.1),
        ]

        for sensitivity, expected_score in test_cases:
            context = {"data_sensitivity": sensitivity}
            score = calc._score_data_sensitivity(context)
            assert score == expected_score

    def test_score_data_sensitivity_list(self):
        """Test data sensitivity with list of types"""
        calc = BusinessImpactCalculator()

        context = {"data_sensitivity": ["pii", "internal"]}
        score = calc._score_data_sensitivity(context)

        # Should take max of list
        assert score == 1.0

    def test_score_compliance_violation(self):
        """Test compliance violation detection"""
        calc = BusinessImpactCalculator()

        finding = {"description": "Unencrypted card data storage"}
        context = {"compliance": ["pci-dss"]}

        score = calc._score_compliance(context, finding)

        # Should be boosted due to violation
        assert score > 0.7

    def test_score_asset_criticality_variations(self):
        """Test different asset criticality levels"""
        calc = BusinessImpactCalculator()

        test_cases = [
            ("critical", 1.0),
            ("high", 0.8),
            ("medium", 0.4),
            ("low", 0.1),
        ]

        for criticality, expected_score in test_cases:
            context = {"asset_criticality": criticality}
            score = calc._score_asset_criticality(context)
            assert score == expected_score

    def test_generate_context_questions(self):
        """Generate context collection questions"""
        calc = BusinessImpactCalculator()

        questions = calc.generate_context_questions()

        assert len(questions) >= 4
        assert any(q["key"] == "network_exposure" for q in questions)
        assert any(q["key"] == "data_sensitivity" for q in questions)
        assert any(q["key"] == "compliance" for q in questions)
        assert any(q["key"] == "asset_criticality" for q in questions)

    def test_get_impact_description_severe(self):
        """Get impact description for severe score"""
        calc = BusinessImpactCalculator()

        description = calc.get_impact_description(0.95)
        assert "SEVERE" in description

    def test_get_impact_description_high(self):
        """Get impact description for high score"""
        calc = BusinessImpactCalculator()

        description = calc.get_impact_description(0.75)
        assert "HIGH" in description

    def test_get_impact_description_medium(self):
        """Get impact description for medium score"""
        calc = BusinessImpactCalculator()

        description = calc.get_impact_description(0.55)
        assert "MODERATE" in description

    def test_get_impact_description_low(self):
        """Get impact description for low score"""
        calc = BusinessImpactCalculator()

        description = calc.get_impact_description(0.35)
        assert "LOW" in description

    def test_get_impact_description_minimal(self):
        """Get impact description for minimal score"""
        calc = BusinessImpactCalculator()

        description = calc.get_impact_description(0.15)
        assert "MINIMAL" in description


class TestRiskScorer:
    """Test main risk scoring engine"""

    def test_init_with_all_features(self):
        """Initialize with all features enabled"""
        scorer = RiskScorer(enable_epss=True, enable_business_context=True)

        assert scorer.cvss_calc is not None
        assert scorer.epss_client is not None
        assert scorer.business_calc is not None

    def test_init_without_epss(self):
        """Initialize without EPSS"""
        scorer = RiskScorer(enable_epss=False, enable_business_context=True)

        assert scorer.cvss_calc is not None
        assert scorer.epss_client is None
        assert scorer.business_calc is not None

    def test_init_without_business_context(self):
        """Initialize without business context"""
        scorer = RiskScorer(enable_epss=True, enable_business_context=False)

        assert scorer.cvss_calc is not None
        assert scorer.epss_client is not None
        assert scorer.business_calc is None

    def test_calculate_with_cvss_score(self):
        """Calculate risk with provided CVSS score"""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)

        finding = {"cvss_score": 8.0, "description": "Test vulnerability"}
        risk = scorer.calculate(finding)

        assert isinstance(risk, RiskScore)
        assert risk.cvss_score == 0.8  # Normalized to 0-1
        assert risk.value > 0

    def test_calculate_with_cve(self):
        """Calculate risk with CVE ID"""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)

        finding = {"cve_id": "CVE-2021-44228", "description": "Test vulnerability"}
        risk = scorer.calculate(finding)

        assert isinstance(risk, RiskScore)
        # Log4j CVE should result in high CVSS
        assert risk.cvss_score == 1.0  # 10.0 normalized

    def test_calculate_estimate_from_description(self):
        """Calculate risk estimating from description"""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)

        finding = {"description": "SQL injection vulnerability"}
        risk = scorer.calculate(finding)

        assert isinstance(risk, RiskScore)
        assert risk.value > 0

    def test_get_severity_critical(self):
        """Get critical severity level"""
        scorer = RiskScorer()

        severity = scorer._get_severity(9.5)
        assert severity == SeverityLevel.CRITICAL

    def test_get_severity_high(self):
        """Get high severity level"""
        scorer = RiskScorer()

        severity = scorer._get_severity(7.5)
        assert severity == SeverityLevel.HIGH

    def test_get_severity_medium(self):
        """Get medium severity level"""
        scorer = RiskScorer()

        severity = scorer._get_severity(5.5)
        assert severity == SeverityLevel.MEDIUM

    def test_get_severity_low(self):
        """Get low severity level"""
        scorer = RiskScorer()

        severity = scorer._get_severity(2.5)
        assert severity == SeverityLevel.LOW

    def test_get_severity_info(self):
        """Get info severity level"""
        scorer = RiskScorer()

        severity = scorer._get_severity(0.5)
        assert severity == SeverityLevel.INFO

    def test_generate_recommendations_critical(self):
        """Generate recommendations for critical severity"""
        scorer = RiskScorer()

        finding = {}
        recommendations = scorer._generate_recommendations(finding, SeverityLevel.CRITICAL, 0.9, 0.8)

        assert any("immediate" in r.lower() or "24h" in r for r in recommendations)

    def test_generate_recommendations_high(self):
        """Generate recommendations for high severity"""
        scorer = RiskScorer()

        finding = {}
        recommendations = scorer._generate_recommendations(finding, SeverityLevel.HIGH, 0.8, 0.3)

        assert any("72h" in r for r in recommendations)

    def test_generate_recommendations_epss_high(self):
        """Generate recommendations for high EPSS"""
        scorer = RiskScorer()

        finding = {}
        recommendations = scorer._generate_recommendations(finding, SeverityLevel.MEDIUM, 0.5, 0.6)

        assert any("EXPLOIT PROBABILITY" in r for r in recommendations)

    def test_generate_recommendations_cvss_high(self):
        """Generate recommendations for high CVSS"""
        scorer = RiskScorer()

        finding = {}
        recommendations = scorer._generate_recommendations(finding, SeverityLevel.HIGH, 0.85, 0.1)

        assert any("Network segmentation" in r for r in recommendations)

    def test_validate_exploit_confirmed(self):
        """Validate confirmed exploit"""
        scorer = RiskScorer()

        finding = {"exploit_validated": True}
        score = scorer._validate_exploit(finding)

        assert score == 1.0

    def test_validate_exploit_available(self):
        """Validate exploit code available"""
        scorer = RiskScorer()

        finding = {"exploit_available": True}
        score = scorer._validate_exploit(finding)

        assert score == 0.5

    def test_validate_exploit_theoretical(self):
        """Validate theoretically exploitable"""
        scorer = RiskScorer()

        finding = {"theoretically_exploitable": True}
        score = scorer._validate_exploit(finding)

        assert score == 0.2

    def test_validate_exploit_none(self):
        """Validate no exploit"""
        scorer = RiskScorer()

        finding = {}
        score = scorer._validate_exploit(finding)

        assert score == 0.0

    def test_get_validation_status_confirmed(self):
        """Get validation status for confirmed exploit"""
        scorer = RiskScorer()

        finding = {"exploit_validated": True}
        status = scorer._get_validation_status(finding)

        assert status == "Confirmed Exploitable"

    def test_get_validation_status_available(self):
        """Get validation status for available exploit"""
        scorer = RiskScorer()

        finding = {"exploit_available": True}
        status = scorer._get_validation_status(finding)

        assert status == "Exploit Code Available"

    def test_prioritize_findings(self):
        """Prioritize multiple findings"""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)

        findings = [
            {"cvss_score": 5.0, "title": "Medium"},
            {"cvss_score": 9.0, "title": "Critical"},
            {"cvss_score": 7.0, "title": "High"},
        ]

        prioritized = scorer.prioritize_findings(findings)

        # Should be sorted by risk score descending
        assert prioritized[0]["title"] == "Critical"
        assert prioritized[1]["title"] == "High"
        assert prioritized[2]["title"] == "Medium"

    def test_risk_score_to_dict(self):
        """Convert RiskScore to dictionary"""
        risk = RiskScore(
            value=8.5,
            severity=SeverityLevel.HIGH,
            cvss_score=0.8,
            epss_score=0.3,
            business_impact_score=0.7,
            exploit_validation_score=0.5,
        )

        data = risk.to_dict()

        assert data["risk_score"] == 8.5
        assert data["severity"] == "HIGH"
        assert data["sla"] == "72h"
        assert "components" in data


class TestSeverityLevel:
    """Test SeverityLevel enum"""

    def test_severity_levels(self):
        """Test severity level definitions"""

        assert SeverityLevel.CRITICAL.min_score == 9.0
        assert SeverityLevel.CRITICAL.max_score == 10.0
        assert SeverityLevel.CRITICAL.sla == "24h"

        assert SeverityLevel.HIGH.min_score == 7.0
        assert SeverityLevel.HIGH.max_score == 8.9
        assert SeverityLevel.HIGH.sla == "72h"

        assert SeverityLevel.MEDIUM.min_score == 4.0
        assert SeverityLevel.MEDIUM.max_score == 6.9
        assert SeverityLevel.MEDIUM.sla == "14d"

        assert SeverityLevel.LOW.min_score == 1.0
        assert SeverityLevel.LOW.max_score == 3.9
        assert SeverityLevel.LOW.sla == "30d"

        assert SeverityLevel.INFO.min_score == 0.0
        assert SeverityLevel.INFO.max_score == 0.9
        assert SeverityLevel.INFO.sla == "Best effort"


class TestRiskScorerIntegration:
    """Integration tests for risk scorer"""

    @patch.object(EPSSClient, "get_score")
    def test_full_calculation_with_epss(self, mock_epss):
        """Test full calculation with mocked EPSS"""
        mock_epss.return_value = 0.75

        scorer = RiskScorer(enable_epss=True, enable_business_context=True)

        finding = {
            "cve_id": "CVE-2021-44228",
            "description": "Remote code execution vulnerability",
            "exploit_available": True,
        }
        context = {"internet_facing": True, "data_sensitivity": "pii"}

        risk = scorer.calculate(finding, context)

        assert risk.value > 0
        assert risk.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
        assert risk.epss_score == 0.75

    def test_risk_score_with_target_context(self):
        """Test risk score includes target context"""
        scorer = RiskScorer(enable_epss=False, enable_business_context=True)

        finding = {"cvss_score": 7.0, "description": "Test vulnerability"}
        context = {"internet_facing": True, "data_sensitivity": "confidential"}

        risk = scorer.calculate(finding, context)

        assert "internet_facing" in risk.target_context
        assert risk.target_context["data_sensitivity"] == "confidential"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
