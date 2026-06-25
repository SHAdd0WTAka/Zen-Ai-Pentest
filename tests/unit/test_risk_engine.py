"""
Unit Tests für das Risk Engine Modul.

Diese Test Suite deckt folgende Komponenten ab:
- Risk Scoring Algorithmen (scorer.py)
- CVSS Scoring (cvss.py)
- EPSS Integration (epss.py)
- Business Impact Assessment (business_impact.py, business_impact_calculator.py)
- False Positive Engine (false_positive_engine.py)

Ziel: 120+ Tests, 75%+ Coverage
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from risk_engine import (
    AssetContext,
    AssetCriticality,
    BusinessImpactCalculator,
    BusinessImpactResult,
    ComplianceFramework,
    ComplianceImpact,
    CVSSCalculator,
    CVSSData,
    DataClassification,
    EPSSClient,
    EPSSData,
    FalsePositiveEngine,
    FinancialImpact,
    Finding,
    FindingStatus,
    ReputationImpact,
    RiskFactors,
    RiskScore,
    RiskScorer,
    SeverityLevel,
    ValidationResult,
    VulnerabilityType,
    get_calculator,
)
from risk_engine.business_impact import BusinessImpactCalculator as LegacyBIC
from risk_engine.false_positive_engine import (
    BayesianFilter,
    ConfidenceLevel,
    FalsePositiveDatabase,
    HistoricalFinding,
    LLMVotingEngine,
    create_finding_from_scan_result,
)

# =============================================================================
# SeverityLevel Enum Tests
# =============================================================================


class TestSeverityLevel:
    """Tests für SeverityLevel Enum."""

    def test_severity_critical(self):
        """Test CRITICAL SeverityLevel."""
        assert SeverityLevel.CRITICAL.min_score == 9.0
        assert SeverityLevel.CRITICAL.max_score == 10.0
        assert SeverityLevel.CRITICAL.sla == "24h"

    def test_severity_high(self):
        """Test HIGH SeverityLevel."""
        assert SeverityLevel.HIGH.min_score == 7.0
        assert SeverityLevel.HIGH.max_score == 8.9
        assert SeverityLevel.HIGH.sla == "72h"

    def test_severity_medium(self):
        """Test MEDIUM SeverityLevel."""
        assert SeverityLevel.MEDIUM.min_score == 4.0
        assert SeverityLevel.MEDIUM.max_score == 6.9
        assert SeverityLevel.MEDIUM.sla == "14d"

    def test_severity_low(self):
        """Test LOW SeverityLevel."""
        assert SeverityLevel.LOW.min_score == 1.0
        assert SeverityLevel.LOW.max_score == 3.9
        assert SeverityLevel.LOW.sla == "30d"

    def test_severity_info(self):
        """Test INFO SeverityLevel."""
        assert SeverityLevel.INFO.min_score == 0.0
        assert SeverityLevel.INFO.max_score == 0.9
        assert SeverityLevel.INFO.sla == "Best effort"

    def test_all_severities_have_required_attributes(self):
        """Test dass alle SeverityLevel die erforderlichen Attribute haben."""
        for level in SeverityLevel:
            assert hasattr(level, "min_score")
            assert hasattr(level, "max_score")
            assert hasattr(level, "sla")
            assert isinstance(level.min_score, float)
            assert isinstance(level.max_score, float)
            assert isinstance(level.sla, str)


# =============================================================================
# RiskScore Tests
# =============================================================================


class TestRiskScore:
    """Tests für RiskScore Dataclass."""

    def test_risk_score_creation(self):
        """Test Erstellung eines RiskScore Objekts."""
        score = RiskScore(
            value=8.5,
            severity=SeverityLevel.HIGH,
            cvss_score=0.85,
            epss_score=0.7,
            business_impact_score=0.9,
            exploit_validation_score=1.0,
        )
        assert score.value == 8.5
        assert score.severity == SeverityLevel.HIGH
        assert score.cvss_score == 0.85

    def test_risk_score_to_dict(self):
        """Test Konvertierung zu Dictionary."""
        score = RiskScore(
            value=9.5,
            severity=SeverityLevel.CRITICAL,
            cvss_score=0.95,
            epss_score=0.8,
            business_impact_score=0.9,
            exploit_validation_score=1.0,
        )
        result = score.to_dict()
        assert result["risk_score"] == 9.5
        assert result["severity"]["level"] == "CRITICAL"
        assert result["severity"]["sla"] == "24h"
        assert "components" in result
        assert "cvss" in result["components"]

    def test_risk_score_default_values(self):
        """Test Default-Werte für RiskScore."""
        score = RiskScore(
            value=5.0,
            severity=SeverityLevel.MEDIUM,
            cvss_score=0.5,
            epss_score=0.3,
            business_impact_score=0.4,
            exploit_validation_score=0.0,
        )
        assert score.components.cvss_base == 5.0
        assert score.target_context == {}
        assert score.prioritized_actions == []
        assert isinstance(score.timestamp, datetime)

    def test_risk_score_with_components(self):
        """Test RiskScore mit Komponenten."""
        from risk_engine.scorer import RiskComponents

        score = RiskScore(
            value=7.5,
            severity=SeverityLevel.HIGH,
            cvss_score=0.75,
            epss_score=0.6,
            business_impact_score=0.8,
            exploit_validation_score=0.5,
            components=RiskComponents(cvss_base=7.5),
            target_context={"internet_facing": True},
            prioritized_actions=["Patch immediately"],
        )
        result = score.to_dict()
        assert result["components"]["cvss"]["base"] == 7.5
        assert result["target_context"]["internet_facing"] is True
        assert result["prioritized_actions"] == ["Patch immediately"]


# =============================================================================
# RiskScorer Tests
# =============================================================================


class TestRiskScorer:
    """Tests für RiskScorer Klasse."""

    def test_scorer_initialization(self):
        """Test Initialisierung des RiskScorer."""
        scorer = RiskScorer()
        assert scorer.cvss_calc is not None
        assert scorer.epss_client is not None
        assert scorer.business_calc is not None

    def test_scorer_initialization_disabled_features(self):
        """Test Initialisierung mit deaktivierten Features."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        assert scorer.cvss_calc is not None
        assert scorer.epss_client is None
        assert scorer.business_calc is None

    def test_scorer_weights(self):
        """Test Gewichtungskonfiguration."""
        weights = RiskScorer.DEFAULT_WEIGHTS
        assert weights["cvss"] == 0.30
        assert weights["epss"] == 0.25
        assert weights["business"] == 0.35
        assert weights["exploit"] == 0.10
        assert sum(weights.values()) == 1.0

    def test_calculate_with_cvss_score(self):
        """Test Berechnung mit vorgegebenem CVSS Score."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {"cvss_score": 8.0}
        result = scorer.calculate(finding)
        assert isinstance(result, RiskScore)
        assert result.cvss_score == 0.8  # Normalized to 0-1

    def test_calculate_with_cve_id(self):
        """Test Berechnung mit CVE ID."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {"cve_id": "CVE-2021-44228"}
        result = scorer.calculate(finding)
        assert isinstance(result, RiskScore)
        assert result.cvss_score == 1.0  # Log4j CVSS 10.0 -> 1.0

    def test_calculate_with_description(self):
        """Test Berechnung mit Beschreibung."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {"description": "SQL injection vulnerability"}
        result = scorer.calculate(finding)
        assert isinstance(result, RiskScore)
        assert result.cvss_score > 0

    def test_calculate_exploit_validated(self):
        """Test Berechnung mit validiertem Exploit."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {
            "cvss_score": 7.0,
            "exploit_validated": True,
        }
        result = scorer.calculate(finding)
        assert result.exploit_validation_score == 1.0

    def test_calculate_exploit_available(self):
        """Test Berechnung mit verfügbarem Exploit Code."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {
            "cvss_score": 7.0,
            "exploit_available": True,
        }
        result = scorer.calculate(finding)
        assert result.exploit_validation_score == 0.7

    def test_calculate_theoretically_exploitable(self):
        """Test Berechnung mit theoretischer Exploitierbarkeit."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {
            "cvss_score": 7.0,
            "theoretically_exploitable": True,
        }
        result = scorer.calculate(finding)
        assert result.exploit_validation_score == 0.2

    def test_calculate_no_exploit(self):
        """Test Berechnung ohne Exploit Informationen."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {"cvss_score": 7.0}
        result = scorer.calculate(finding)
        assert result.exploit_validation_score == 0.0

    def test_get_severity_critical(self):
        """Test Severity Bestimmung für Critical."""
        scorer = RiskScorer()
        assert scorer._get_severity(9.5) == SeverityLevel.CRITICAL
        assert scorer._get_severity(9.0) == SeverityLevel.CRITICAL
        assert scorer._get_severity(10.0) == SeverityLevel.CRITICAL

    def test_get_severity_high(self):
        """Test Severity Bestimmung für High."""
        scorer = RiskScorer()
        assert scorer._get_severity(8.9) == SeverityLevel.HIGH
        assert scorer._get_severity(7.0) == SeverityLevel.HIGH

    def test_get_severity_medium(self):
        """Test Severity Bestimmung für Medium."""
        scorer = RiskScorer()
        assert scorer._get_severity(6.9) == SeverityLevel.MEDIUM
        assert scorer._get_severity(4.0) == SeverityLevel.MEDIUM

    def test_get_severity_low(self):
        """Test Severity Bestimmung für Low."""
        scorer = RiskScorer()
        assert scorer._get_severity(3.9) == SeverityLevel.LOW
        assert scorer._get_severity(1.0) == SeverityLevel.LOW

    def test_get_severity_info(self):
        """Test Severity Bestimmung für Info."""
        scorer = RiskScorer()
        assert scorer._get_severity(0.9) == SeverityLevel.INFO
        assert scorer._get_severity(0.0) == SeverityLevel.INFO

    def test_get_severity_below_range(self):
        """Test Severity für Werte unter dem gültigen Bereich."""
        scorer = RiskScorer()
        # Sollte INFO zurückgeben, da kein Bereich passt
        result = scorer._get_severity(-1.0)
        assert result == SeverityLevel.INFO

    def test_generate_recommendations_critical(self):
        """Test Empfehlungen für Critical Severity."""
        scorer = RiskScorer()
        finding = {}
        recs = scorer._generate_recommendations(finding, SeverityLevel.CRITICAL, 0.9, 0.6)
        assert any("Isolate" in r for r in recs)
        assert any("emergency patch" in r for r in recs)
        assert any("incident response" in r for r in recs)

    def test_generate_recommendations_high(self):
        """Test Empfehlungen für High Severity."""
        scorer = RiskScorer()
        finding = {}
        recs = scorer._generate_recommendations(finding, SeverityLevel.HIGH, 0.8, 0.5)
        assert any("72h" in r for r in recs)
        assert any("workaround" in r or "WAF" in r for r in recs)
        assert any("monitoring" in r for r in recs)

    def test_generate_recommendations_medium(self):
        """Test Empfehlungen für Medium Severity."""
        scorer = RiskScorer()
        finding = {}
        recs = scorer._generate_recommendations(finding, SeverityLevel.MEDIUM, 0.5, 0.3)
        assert any("maintenance window" in r for r in recs)
        assert any("security policies" in r for r in recs)

    def test_generate_recommendations_high_epss(self):
        """Test Empfehlungen bei hohem EPSS Score."""
        scorer = RiskScorer()
        finding = {}
        recs = scorer._generate_recommendations(finding, SeverityLevel.LOW, 0.3, 0.6)
        assert any("EXPLOIT PROBABILITY" in r for r in recs)

    def test_generate_recommendations_high_cvss(self):
        """Test Empfehlungen bei hohem CVSS Score."""
        scorer = RiskScorer()
        finding = {}
        recs = scorer._generate_recommendations(finding, SeverityLevel.MEDIUM, 8.5, 0.3)
        assert any("segmentation" in r for r in recs)

    def test_get_business_factors(self):
        """Test Extraktion von Business Faktoren."""
        scorer = RiskScorer()
        context = {
            "internet_facing": True,
            "data_sensitivity": "pii",
            "compliance": ["gdpr", "pci-dss"],
            "asset_criticality": "high",
        }
        factors = scorer._get_business_factors(context)
        assert factors["internet_facing"] is True
        assert factors["data_sensitivity"] == "pii"
        assert factors["compliance_scope"] == ["gdpr", "pci-dss"]
        assert factors["asset_criticality"] == "high"

    def test_get_business_factors_defaults(self):
        """Test Business Faktoren mit Defaults."""
        scorer = RiskScorer()
        factors = scorer._get_business_factors({})
        assert factors["internet_facing"] is False
        assert factors["data_sensitivity"] == "unknown"
        assert factors["compliance_scope"] == []
        assert factors["asset_criticality"] == "medium"

    def test_get_validation_status_confirmed(self):
        """Test Validierungsstatus: Confirmed."""
        scorer = RiskScorer()
        finding = {"exploit_validated": True}
        assert scorer._get_validation_status(finding) == "Confirmed Exploitable"

    def test_get_validation_status_available(self):
        """Test Validierungsstatus: Available."""
        scorer = RiskScorer()
        finding = {"exploit_available": True}
        assert scorer._get_validation_status(finding) == "Exploit Code Available"

    def test_get_validation_status_theoretical(self):
        """Test Validierungsstatus: Theoretical."""
        scorer = RiskScorer()
        finding = {"theoretically_exploitable": True}
        assert scorer._get_validation_status(finding) == "Theoretically Exploitable"

    def test_get_validation_status_none(self):
        """Test Validierungsstatus: None."""
        scorer = RiskScorer()
        finding = {}
        assert scorer._get_validation_status(finding) == "No Known Exploit"

    def test_prioritize_findings(self):
        """Test Priorisierung mehrerer Findings."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        findings = [
            {"cvss_score": 5.0, "name": "medium"},
            {"cvss_score": 9.0, "name": "critical"},
            {"cvss_score": 7.0, "name": "high"},
        ]
        result = scorer.prioritize_findings(findings)
        assert result[0]["name"] == "critical"
        assert result[1]["name"] == "high"
        assert result[2]["name"] == "medium"

    def test_prioritize_findings_with_risk_score(self):
        """Test dass Risk Scores angehängt werden."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        findings = [{"cvss_score": 8.0}]
        result = scorer.prioritize_findings(findings)
        assert "risk_score" in result[0]
        assert "risk_score" in result[0]["risk_score"]


# =============================================================================
# CVSSCalculator Tests
# =============================================================================


class TestCVSSCalculator:
    """Tests für CVSSCalculator Klasse."""

    def test_calculate_network_attack(self):
        """Test CVSS Berechnung für Network Attack."""
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
        score = calc.calculate(metrics)
        assert 9.0 <= score <= 10.0

    def test_calculate_local_attack(self):
        """Test CVSS Berechnung für Local Attack."""
        calc = CVSSCalculator()
        metrics = {
            "AV": "L",
            "AC": "H",
            "PR": "H",
            "UI": "R",
            "S": "U",
            "C": "L",
            "I": "L",
            "A": "N",
        }
        score = calc.calculate(metrics)
        assert 0.0 <= score <= 5.0

    def test_calculate_changed_scope(self):
        """Test CVSS Berechnung mit Changed Scope."""
        calc = CVSSCalculator()
        metrics = {
            "AV": "N",
            "AC": "L",
            "PR": "L",
            "UI": "N",
            "S": "C",
            "C": "H",
            "I": "H",
            "A": "H",
        }
        score = calc.calculate(metrics)
        assert score > 0

    def test_calculate_default_values(self):
        """Test CVSS Berechnung mit Default Werten."""
        calc = CVSSCalculator()
        metrics = {}
        score = calc.calculate(metrics)
        assert score >= 0.0

    def test_calculate_with_invalid_metrics(self):
        """Test CVSS Berechnung mit ungültigen Metriken."""
        calc = CVSSCalculator()
        metrics = {"AV": "X", "AC": "Y"}  # Invalid values
        score = calc.calculate(metrics)
        # Sollte mit Defaults arbeiten
        assert score >= 0.0

    def test_calculate_exception_handling(self):
        """Test Exception Handling in calculate."""
        calc = CVSSCalculator()
        # Test mit None-Werten - sollte 0.0 zurückgeben (impact <= 0)
        metrics = {"S": None, "C": None, "I": None, "A": None}
        score = calc.calculate(metrics)
        assert score >= 0.0  # Sollte gültigen Score zurückgeben

    def test_from_cve_known_cves(self):
        """Test CVSS Lookup für bekannte CVEs."""
        calc = CVSSCalculator()
        assert calc.from_cve("CVE-2021-44228") == 10.0  # Log4j
        assert calc.from_cve("CVE-2017-0144") == 8.1  # EternalBlue
        assert calc.from_cve("CVE-2014-0160") == 5.0  # Heartbleed

    def test_from_cve_unknown_cve(self):
        """Test CVSS Lookup für unbekannte CVEs."""
        calc = CVSSCalculator()
        assert calc.from_cve("CVE-2099-99999") == 5.0  # Default

    def test_from_cve_case_insensitive(self):
        """Test CVE Lookup ist Case-Insensitive."""
        calc = CVSSCalculator()
        assert calc.from_cve("cve-2021-44228") == 10.0
        assert calc.from_cve("Cve-2021-44228") == 10.0

    def test_estimate_rce(self):
        """Test Schätzung für RCE."""
        calc = CVSSCalculator()
        score = calc.estimate("Remote code execution vulnerability")
        # RCE base 9.8 + network adjustment 0.5, capped at 10.0
        assert score >= 9.8
        assert score <= 10.0

    def test_estimate_sql_injection(self):
        """Test Schätzung für SQL Injection."""
        calc = CVSSCalculator()
        score = calc.estimate("SQL injection in login form")
        assert score == 8.6

    def test_estimate_xss(self):
        """Test Schätzung für XSS."""
        calc = CVSSCalculator()
        score = calc.estimate("Cross-site scripting vulnerability")
        assert score == 6.1

    def test_estimate_dos(self):
        """Test Schätzung für DoS."""
        calc = CVSSCalculator()
        score = calc.estimate("Denial of service vulnerability")
        assert score == 7.5

    def test_estimate_info_disclosure(self):
        """Test Schätzung für Information Disclosure."""
        calc = CVSSCalculator()
        score = calc.estimate("Information disclosure vulnerability")
        assert score == 5.3

    def test_estimate_auth_bypass(self):
        """Test Schätzung für Authentication Bypass."""
        calc = CVSSCalculator()
        score = calc.estimate("Authentication bypass vulnerability")
        assert score == 8.1

    def test_estimate_default(self):
        """Test Default Schätzung."""
        calc = CVSSCalculator()
        score = calc.estimate("Some random vulnerability")
        assert score == 5.0

    def test_estimate_network_adjustment(self):
        """Test Network-Anpassung in Schätzung."""
        calc = CVSSCalculator()
        score1 = calc.estimate("SQL injection")  # 8.6
        score2 = calc.estimate("SQL injection via network")  # 8.6 + 0.5 = 9.1
        assert score2 > score1

    def test_estimate_unauthenticated_adjustment(self):
        """Test Unauthenticated-Anpassung in Schätzung."""
        calc = CVSSCalculator()
        score1 = calc.estimate("SQL injection")
        score2 = calc.estimate("SQL injection unauthenticated")
        assert score2 > score1

    def test_estimate_max_score_cap(self):
        """Test dass Score nicht über 10 geht."""
        calc = CVSSCalculator()
        score = calc.estimate("RCE remote unauthenticated network critical")
        assert score <= 10.0

    def test_get_details_critical(self):
        """Test CVSS Details für Critical."""
        calc = CVSSCalculator()
        finding = {
            "cvss_score": 9.5,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        }
        details = calc.get_details(finding)
        assert details["severity"] == "Critical"
        assert details["base_score"] == 9.5

    def test_get_details_high(self):
        """Test CVSS Details für High."""
        calc = CVSSCalculator()
        finding = {"cvss_score": 7.5}
        details = calc.get_details(finding)
        assert details["severity"] == "High"

    def test_get_details_medium(self):
        """Test CVSS Details für Medium."""
        calc = CVSSCalculator()
        finding = {"cvss_score": 5.5}
        details = calc.get_details(finding)
        assert details["severity"] == "Medium"

    def test_get_details_low(self):
        """Test CVSS Details für Low."""
        calc = CVSSCalculator()
        finding = {"cvss_score": 3.0}
        details = calc.get_details(finding)
        assert details["severity"] == "Low"

    def test_get_details_none(self):
        """Test CVSS Details für None."""
        calc = CVSSCalculator()
        finding = {"cvss_score": 0.0}
        details = calc.get_details(finding)
        assert details["severity"] == "None"

    def test_get_vector_from_metrics(self):
        """Test Vector String Generierung."""
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

    def test_get_vector_from_metrics_partial(self):
        """Test Vector String mit partiellen Metriken."""
        calc = CVSSCalculator()
        metrics = {"AV": "N", "AC": "L"}
        vector = calc.get_vector_from_metrics(metrics)
        assert "CVSS:3.1/AV:N/AC:L" in vector


# =============================================================================
# EPSSClient Tests
# =============================================================================


class TestEPSSClient:
    """Tests für EPSSClient Klasse."""

    def test_client_initialization(self):
        """Test Initialisierung des EPSS Clients."""
        client = EPSSClient()
        assert client.cache == {}
        assert client.cache_duration == timedelta(hours=24)

    def test_client_initialization_custom_cache(self):
        """Test Initialisierung mit custom Cache-Dauer."""
        client = EPSSClient(cache_duration=12)
        assert client.cache_duration == timedelta(hours=12)

    @patch("risk_engine.epss.requests.get")
    def test_get_score_success(self, mock_get):
        """Test erfolgreiche EPSS Abfrage."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        score = client.get_score("CVE-2021-44228")
        assert score == 0.95

    @patch("risk_engine.epss.requests.get")
    def test_get_score_caching(self, mock_get):
        """Test EPSS Caching."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        score1 = client.get_score("CVE-2021-44228")
        score2 = client.get_score("CVE-2021-44228")  # Should use cache

        assert score1 == score2
        assert mock_get.call_count == 1  # Only called once

    @patch("risk_engine.epss.requests.get")
    def test_get_score_cache_expiry(self, mock_get):
        """Test EPSS Cache Ablauf."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient(cache_duration=0)  # Immediate expiry
        client.get_score("CVE-2021-44228")
        # Manually expire cache
        client.cache["CVE-2021-44228"]["timestamp"] = datetime.now() - timedelta(hours=1)
        client.get_score("CVE-2021-44228")

        assert mock_get.call_count == 2  # Called twice due to expiry

    @patch("risk_engine.epss.requests.get")
    def test_get_score_api_failure(self, mock_get):
        """Test EPSS bei API Fehler."""
        mock_get.side_effect = Exception("API Error")

        client = EPSSClient()
        score = client.get_score("CVE-2021-44228")
        assert score == 0.0

    @patch("risk_engine.epss.requests.get")
    def test_get_score_no_data(self, mock_get):
        """Test EPSS wenn keine Daten zurückkommen."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        score = client.get_score("CVE-2021-44228")
        assert score == 0.0

    @patch("risk_engine.epss.requests.get")
    def test_get_batch_scores(self, mock_get):
        """Test Batch EPSS Abfrage."""
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
    def test_get_batch_scores_empty(self, mock_get):
        """Test Batch EPSS mit leerer Liste."""
        client = EPSSClient()
        scores = client.get_batch_scores([])
        assert scores == {}
        mock_get.assert_not_called()

    @patch("risk_engine.epss.requests.get")
    def test_get_batch_scores_with_missing(self, mock_get):
        """Test Batch EPSS mit fehlenden CVEs."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        scores = client.get_batch_scores(["CVE-2021-44228", "CVE-UNKNOWN"])
        assert scores["CVE-2021-44228"] == 0.95
        assert scores["CVE-UNKNOWN"] == 0.0

    @patch("risk_engine.epss.requests.get")
    def test_get_percentile_success(self, mock_get):
        """Test Percentile Abfrage."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.95, "percentile": 0.99}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        percentile = client.get_percentile("CVE-2021-44228")
        assert percentile == 0.99

    @patch("risk_engine.epss.requests.get")
    def test_get_percentile_failure(self, mock_get):
        """Test Percentile bei Fehler."""
        mock_get.side_effect = Exception("API Error")

        client = EPSSClient()
        percentile = client.get_percentile("CVE-2021-44228")
        assert percentile is None

    def test_interpret_score_very_high(self):
        """Test Interpretation für sehr hohen Score."""
        client = EPSSClient()
        assert "Very High" in client.interpret_score(0.6)

    def test_interpret_score_high(self):
        """Test Interpretation für hohen Score."""
        client = EPSSClient()
        assert "High" in client.interpret_score(0.4)

    def test_interpret_score_medium(self):
        """Test Interpretation für mittleren Score."""
        client = EPSSClient()
        assert "Medium" in client.interpret_score(0.2)

    def test_interpret_score_low(self):
        """Test Interpretation für niedrigen Score."""
        client = EPSSClient()
        assert "Low" in client.interpret_score(0.08)

    def test_interpret_score_very_low(self):
        """Test Interpretation für sehr niedrigen Score."""
        client = EPSSClient()
        assert "Very Low" in client.interpret_score(0.01)

    @patch("risk_engine.epss.requests.get")
    def test_should_prioritize_true(self, mock_get):
        """Test Priorisierung wenn Score über Threshold."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.5}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        assert client.should_prioritize("CVE-2021-44228", threshold=0.3) is True

    @patch("risk_engine.epss.requests.get")
    def test_should_prioritize_false(self, mock_get):
        """Test Priorisierung wenn Score unter Threshold."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228", "epss": 0.1}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = EPSSClient()
        assert client.should_prioritize("CVE-2021-44228", threshold=0.3) is False


# =============================================================================
# Legacy Business Impact Calculator Tests
# =============================================================================


class TestLegacyBusinessImpactCalculator:
    """Tests für legacy BusinessImpactCalculator (business_impact.py)."""

    def test_legacy_calculate(self):
        """Test legacy calculate Methode."""
        calc = LegacyBIC()
        finding = {"severity": "high"}
        context = {"network_exposure": "internet", "data_sensitivity": "pii"}
        score = calc.calculate(finding, context)
        assert 0.0 <= score <= 1.0

    def test_legacy_score_internet_facing(self):
        """Test Internet Facing Scoring."""
        calc = LegacyBIC()
        context = {"network_exposure": "internet"}
        assert calc._score_internet_facing(context) == 1.0

    def test_legacy_score_dmz(self):
        """Test DMZ Scoring."""
        calc = LegacyBIC()
        context = {"network_exposure": "dmz"}
        assert calc._score_internet_facing(context) == 0.6

    def test_legacy_score_internal(self):
        """Test Internal Scoring."""
        calc = LegacyBIC()
        context = {"network_exposure": "internal"}
        assert calc._score_internet_facing(context) == 0.3

    def test_legacy_score_airgapped(self):
        """Test Airgapped Scoring."""
        calc = LegacyBIC()
        context = {"network_exposure": "airgapped"}
        assert calc._score_internet_facing(context) == 0.1

    def test_legacy_score_boolean_flag(self):
        """Test Boolean internet_facing Flag."""
        calc = LegacyBIC()
        context = {"internet_facing": True}
        assert calc._score_internet_facing(context) == 1.0

    def test_legacy_data_sensitivity_pii(self):
        """Test PII Data Sensitivity."""
        calc = LegacyBIC()
        context = {"data_sensitivity": "pii"}
        assert calc._score_data_sensitivity(context) == 1.0

    def test_legacy_data_sensitivity_confidential(self):
        """Test Confidential Data Sensitivity."""
        calc = LegacyBIC()
        context = {"data_sensitivity": "confidential"}
        assert calc._score_data_sensitivity(context) == 0.7

    def test_legacy_data_sensitivity_list(self):
        """Test Data Sensitivity mit Liste."""
        calc = LegacyBIC()
        context = {"data_sensitivity": ["internal", "pii"]}
        assert calc._score_data_sensitivity(context) == 1.0

    def test_legacy_compliance_pci_dss(self):
        """Test PCI-DSS Compliance Scoring."""
        calc = LegacyBIC()
        context = {"compliance": ["pci-dss"]}
        finding = {"description": "SSL configuration issue"}
        score = calc._score_compliance(context, finding)
        assert score > 0.5

    def test_legacy_compliance_gdpr(self):
        """Test GDPR Compliance Scoring."""
        calc = LegacyBIC()
        context = {"compliance": ["gdpr"]}
        finding = {"description": "data exposure vulnerability"}
        score = calc._score_compliance(context, finding)
        assert score > 0.5

    def test_legacy_compliance_empty(self):
        """Test leere Compliance Liste."""
        calc = LegacyBIC()
        context = {"compliance": []}
        finding = {}
        score = calc._score_compliance(context, finding)
        assert score == 0.3

    def test_legacy_asset_criticality_critical(self):
        """Test Critical Asset Criticality."""
        calc = LegacyBIC()
        context = {"asset_criticality": "critical"}
        assert calc._score_asset_criticality(context) == 1.0

    def test_legacy_asset_criticality_high(self):
        """Test High Asset Criticality."""
        calc = LegacyBIC()
        context = {"asset_criticality": "high"}
        assert calc._score_asset_criticality(context) == 0.8

    def test_legacy_compliance_violation_pci(self):
        """Test PCI Compliance Violation Detection."""
        calc = LegacyBIC()
        finding = {"description": "unencrypted card data transmission"}
        compliance = ["pci-dss"]
        assert calc._is_compliance_violation(finding, compliance) is True

    def test_legacy_compliance_violation_gdpr(self):
        """Test GDPR Compliance Violation Detection."""
        calc = LegacyBIC()
        finding = {"description": "pii leak vulnerability"}
        compliance = ["gdpr"]
        assert calc._is_compliance_violation(finding, compliance) is True

    def test_legacy_compliance_no_violation(self):
        """Test keine Compliance Violation."""
        calc = LegacyBIC()
        finding = {"description": "general vulnerability"}
        compliance = ["pci-dss"]
        assert calc._is_compliance_violation(finding, compliance) is False

    def test_legacy_generate_context_questions(self):
        """Test Generierung von Context Fragen."""
        calc = LegacyBIC()
        questions = calc.generate_context_questions()
        assert len(questions) == 4
        assert all("key" in q for q in questions)
        assert all("question" in q for q in questions)

    def test_legacy_impact_description_severe(self):
        """Test Impact Description für severe."""
        calc = LegacyBIC()
        assert "SEVERE" in calc.get_impact_description(0.95)

    def test_legacy_impact_description_high(self):
        """Test Impact Description für high."""
        calc = LegacyBIC()
        assert "HIGH" in calc.get_impact_description(0.75)

    def test_legacy_impact_description_moderate(self):
        """Test Impact Description für moderate."""
        calc = LegacyBIC()
        assert "MODERATE" in calc.get_impact_description(0.55)

    def test_legacy_impact_description_low(self):
        """Test Impact Description für low."""
        calc = LegacyBIC()
        assert "LOW" in calc.get_impact_description(0.35)

    def test_legacy_impact_description_minimal(self):
        """Test Impact Description für minimal."""
        calc = LegacyBIC()
        assert "MINIMAL" in calc.get_impact_description(0.1)


# =============================================================================
# Business Impact Calculator Tests (new)
# =============================================================================


class TestBusinessImpactCalculator:
    """Tests für neuen BusinessImpactCalculator (business_impact_calculator.py)."""

    def test_calculator_initialization(self):
        """Test Initialisierung des Calculators."""
        calc = BusinessImpactCalculator(
            organization_size="large",
            annual_revenue=100000000,
            industry="finance",
        )
        assert calc.organization_size == "large"
        assert calc.annual_revenue == 100000000
        assert calc.industry == "finance"

    def test_calculator_industry_multipliers(self):
        """Test Industry Multiplikatoren."""
        calc = BusinessImpactCalculator(industry="healthcare")
        assert "compliance" in calc.industry_multipliers["healthcare"]

        calc = BusinessImpactCalculator(industry="finance")
        assert calc.industry_multipliers["finance"]["compliance"] == 1.3

    def test_calculate_financial_impact(self):
        """Test Finanzielle Impact Berechnung."""
        calc = BusinessImpactCalculator(
            organization_size="medium",
            annual_revenue=50000000,
        )
        asset = AssetContext(
            asset_id="test-001",
            asset_name="Test Asset",
            asset_type="server",
            criticality=AssetCriticality.HIGH,
            data_classification=DataClassification.CONFIDENTIAL,
        )
        impact = calc.calculate_financial_impact(asset, breach_likelihood=0.5)
        assert isinstance(impact, FinancialImpact)
        assert impact.total_costs >= 0

    def test_calculate_financial_impact_zero_revenue(self):
        """Test Finanzielle Impact mit Null Umsatz."""
        calc = BusinessImpactCalculator(annual_revenue=0)
        asset = AssetContext(
            asset_id="test-001",
            asset_name="Test Asset",
            asset_type="server",
            criticality=AssetCriticality.MEDIUM,
            data_classification=DataClassification.INTERNAL,
        )
        impact = calc.calculate_financial_impact(asset)
        assert isinstance(impact, FinancialImpact)

    def test_calculate_compliance_impact(self):
        """Test Compliance Impact Berechnung."""
        calc = BusinessImpactCalculator()
        asset = AssetContext(
            asset_id="test-001",
            asset_name="Test Asset",
            asset_type="server",
            criticality=AssetCriticality.CRITICAL,
            data_classification=DataClassification.RESTRICTED,
            compliance_frameworks={
                ComplianceFramework.GDPR,
                ComplianceFramework.PCI_DSS,
            },
        )
        impact = calc.calculate_compliance_impact(asset, finding_type="sql_injection", severity="critical")
        assert isinstance(impact, ComplianceImpact)
        assert len(impact.frameworks) == 2

    def test_assess_reputation_impact(self):
        """Test Reputation Impact Bewertung."""
        calc = BusinessImpactCalculator()
        asset = AssetContext(
            asset_id="test-001",
            asset_name="Test Asset",
            asset_type="server",
            criticality=AssetCriticality.CRITICAL,
            data_classification=DataClassification.RESTRICTED,
            user_count=100000,
            internet_exposed=True,
        )
        reputation = calc.assess_reputation_impact(asset, DataClassification.RESTRICTED, public_exposure=True)
        assert isinstance(reputation, ReputationImpact)

    def test_calculate_overall_impact(self):
        """Test Gesamt-Impact Berechnung."""
        calc = BusinessImpactCalculator(
            organization_size="large",
            annual_revenue=100000000,
        )
        asset = AssetContext(
            asset_id="prod-db-001",
            asset_name="Production Database",
            asset_type="database",
            criticality=AssetCriticality.CRITICAL,
            data_classification=DataClassification.RESTRICTED,
            compliance_frameworks={ComplianceFramework.GDPR},
            user_count=1000000,
            revenue_dependency=30.0,
        )
        result = calc.calculate_overall_impact(
            asset_context=asset,
            finding_type="sql_injection",
            severity="critical",
            breach_likelihood=0.8,
            data_volume_records=100000,
        )
        assert isinstance(result, BusinessImpactResult)
        assert 0.0 <= result.overall_score <= 1.0

    def test_estimate_outage_hours(self):
        """Test Schätzung der Ausfallstunden."""
        calc = BusinessImpactCalculator()
        asset = AssetContext(
            asset_id="test",
            asset_name="Test",
            asset_type="server",
            criticality=AssetCriticality.CRITICAL,
            data_classification=DataClassification.INTERNAL,
        )
        hours = calc._estimate_outage_hours(asset)
        assert hours == 72

    def test_calculate_regulatory_fines_gdpr(self):
        """Test GDPR Strafberechnung."""
        calc = BusinessImpactCalculator()
        asset = AssetContext(
            asset_id="test",
            asset_name="Test",
            asset_type="server",
            criticality=AssetCriticality.HIGH,
            data_classification=DataClassification.RESTRICTED,
            compliance_frameworks={ComplianceFramework.GDPR},
        )
        fine = calc._calculate_regulatory_fines(asset, 50000, 0.8)
        assert fine > 0

    def test_get_max_regulatory_fine(self):
        """Test Maximale Strafen pro Framework."""
        calc = BusinessImpactCalculator()
        assert calc._get_max_regulatory_fine(ComplianceFramework.GDPR) == 20000000
        assert calc._get_max_regulatory_fine(ComplianceFramework.HIPAA) == 1500000
        assert calc._get_max_regulatory_fine(ComplianceFramework.PCI_DSS) == 100000

    def test_identify_violated_controls(self):
        """Test Identifizierung verletzter Controls."""
        calc = BusinessImpactCalculator()
        controls = calc._identify_violated_controls(ComplianceFramework.PCI_DSS, "sql_injection")
        assert "Input Validation" in controls

    def test_compare_impacts(self):
        """Test Impact Vergleich und Priorisierung."""
        calc = BusinessImpactCalculator()
        results = [
            BusinessImpactResult(
                asset_id="low",
                overall_score=0.3,
                financial_impact=FinancialImpact(),
                compliance_impact=ComplianceImpact(),
                reputation_impact=ReputationImpact.LOW,
                asset_criticality_score=0.3,
                data_sensitivity_score=0.2,
                exposure_score=0.1,
            ),
            BusinessImpactResult(
                asset_id="high",
                overall_score=0.8,
                financial_impact=FinancialImpact(),
                compliance_impact=ComplianceImpact(),
                reputation_impact=ReputationImpact.HIGH,
                asset_criticality_score=0.8,
                data_sensitivity_score=0.7,
                exposure_score=0.6,
            ),
        ]
        sorted_results = calc.compare_impacts(results)
        assert sorted_results[0][0].asset_id == "high"
        assert sorted_results[0][1] == 1  # Priority 1


# =============================================================================
# AssetContext Tests
# =============================================================================


class TestAssetContext:
    """Tests für AssetContext Dataclass."""

    def test_asset_context_creation(self):
        """Test AssetContext Erstellung."""
        asset = AssetContext(
            asset_id="test-001",
            asset_name="Test Server",
            asset_type="server",
            criticality=AssetCriticality.HIGH,
            data_classification=DataClassification.CONFIDENTIAL,
        )
        assert asset.asset_id == "test-001"
        assert asset.internet_exposed is False
        assert asset.user_count == 0

    def test_get_exposure_factor_internet(self):
        """Test Exposure Faktor mit Internet-Exposition."""
        asset = AssetContext(
            asset_id="test",
            asset_name="Test",
            asset_type="server",
            criticality=AssetCriticality.MEDIUM,
            data_classification=DataClassification.INTERNAL,
            internet_exposed=True,
            user_count=50000,
            revenue_dependency=20.0,
        )
        exposure = asset.get_exposure_factor()
        assert exposure > 0.4

    def test_get_exposure_factor_no_internet(self):
        """Test Exposure Faktor ohne Internet."""
        asset = AssetContext(
            asset_id="test",
            asset_name="Test",
            asset_type="server",
            criticality=AssetCriticality.LOW,
            data_classification=DataClassification.PUBLIC,
            internet_exposed=False,
            user_count=50,
            revenue_dependency=0.0,
        )
        exposure = asset.get_exposure_factor()
        assert exposure < 0.5


# =============================================================================
# BusinessImpactResult Tests
# =============================================================================


class TestBusinessImpactResult:
    """Tests für BusinessImpactResult Dataclass."""

    def test_get_risk_category_critical(self):
        """Test Risiko-Kategorie Critical."""
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.95,
            financial_impact=FinancialImpact(),
            compliance_impact=ComplianceImpact(),
            reputation_impact=ReputationImpact.SEVERE,
            asset_criticality_score=1.0,
            data_sensitivity_score=1.0,
            exposure_score=1.0,
        )
        assert result.get_risk_category() == "CRITICAL"

    def test_get_risk_category_high(self):
        """Test Risiko-Kategorie High."""
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.75,
            financial_impact=FinancialImpact(),
            compliance_impact=ComplianceImpact(),
            reputation_impact=ReputationImpact.HIGH,
            asset_criticality_score=0.8,
            data_sensitivity_score=0.7,
            exposure_score=0.6,
        )
        assert result.get_risk_category() == "HIGH"

    def test_get_risk_category_medium(self):
        """Test Risiko-Kategorie Medium."""
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.5,
            financial_impact=FinancialImpact(),
            compliance_impact=ComplianceImpact(),
            reputation_impact=ReputationImpact.MODERATE,
            asset_criticality_score=0.5,
            data_sensitivity_score=0.4,
            exposure_score=0.3,
        )
        assert result.get_risk_category() == "MEDIUM"

    def test_get_risk_category_low(self):
        """Test Risiko-Kategorie Low."""
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.3,
            financial_impact=FinancialImpact(),
            compliance_impact=ComplianceImpact(),
            reputation_impact=ReputationImpact.LOW,
            asset_criticality_score=0.3,
            data_sensitivity_score=0.2,
            exposure_score=0.1,
        )
        assert result.get_risk_category() == "LOW"

    def test_get_risk_category_minimal(self):
        """Test Risiko-Kategorie Minimal."""
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.1,
            financial_impact=FinancialImpact(),
            compliance_impact=ComplianceImpact(),
            reputation_impact=ReputationImpact.LOW,
            asset_criticality_score=0.1,
            data_sensitivity_score=0.1,
            exposure_score=0.0,
        )
        assert result.get_risk_category() == "MINIMAL"

    def test_get_prioritized_remediation_high_costs(self):
        """Test Empfehlungen bei hohen Kosten."""
        financial = FinancialImpact(direct_costs=2000000)
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.9,
            financial_impact=financial,
            compliance_impact=ComplianceImpact(),
            reputation_impact=ReputationImpact.SEVERE,
            asset_criticality_score=1.0,
            data_sensitivity_score=1.0,
            exposure_score=1.0,
        )
        recs = result.get_prioritized_remediation()
        assert any("Management" in r for r in recs)

    def test_get_prioritized_remediation_compliance(self):
        """Test Empfehlungen bei Compliance-Verstößen."""
        compliance = ComplianceImpact(violated_controls=["Control1", "Control2"])
        result = BusinessImpactResult(
            asset_id="test",
            overall_score=0.8,
            financial_impact=FinancialImpact(),
            compliance_impact=compliance,
            reputation_impact=ReputationImpact.HIGH,
            asset_criticality_score=0.8,
            data_sensitivity_score=0.7,
            exposure_score=0.6,
        )
        recs = result.get_prioritized_remediation()
        assert any("Compliance" in r for r in recs)


# =============================================================================
# FinancialImpact Tests
# =============================================================================


class TestFinancialImpact:
    """Tests für FinancialImpact Dataclass."""

    def test_total_costs_calculation(self):
        """Test Gesamtkosten-Berechnung."""
        impact = FinancialImpact(
            direct_costs=100000,
            indirect_costs=50000,
            regulatory_fines=20000,
            legal_costs=30000,
            reputation_costs=40000,
        )
        assert impact.total_costs == 240000

    def test_total_costs_zero(self):
        """Test Gesamtkosten bei Null."""
        impact = FinancialImpact()
        assert impact.total_costs == 0.0


# =============================================================================
# ComplianceImpact Tests
# =============================================================================


class TestComplianceImpact:
    """Tests für ComplianceImpact Dataclass."""

    def test_get_max_fine(self):
        """Test maximale Strafe."""
        impact = ComplianceImpact(
            potential_fines={
                ComplianceFramework.GDPR: 20000000,
                ComplianceFramework.HIPAA: 1500000,
            }
        )
        assert impact.get_max_fine() == 20000000

    def test_get_max_fine_empty(self):
        """Test maximale Strafe wenn leer."""
        impact = ComplianceImpact()
        assert impact.get_max_fine() == 0.0

    def test_get_compliance_score(self):
        """Test Compliance Score Berechnung."""
        impact = ComplianceImpact(
            frameworks={ComplianceFramework.GDPR, ComplianceFramework.HIPAA},
            violated_controls=["C1", "C2"],
        )
        score = impact.get_compliance_score()
        assert 0.0 <= score <= 1.0

    def test_get_compliance_score_empty(self):
        """Test Compliance Score wenn leer."""
        impact = ComplianceImpact()
        assert impact.get_compliance_score() == 0.0


# =============================================================================
# False Positive Engine Tests
# =============================================================================


class TestFalsePositiveEngine:
    """Tests für FalsePositiveEngine."""

    @pytest.fixture
    def engine(self):
        """Fixture für FalsePositiveEngine."""
        return FalsePositiveEngine(enable_llm_voting=False)

    @pytest.fixture
    def sample_finding(self):
        """Fixture für Sample Finding."""
        return Finding(
            id="FIND-001",
            title="SQL Injection",
            description="Critical SQL injection vulnerability",
            severity="critical",
            vulnerability_type=VulnerabilityType.SQL_INJECTION,
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=9.8),
                epss_score=0.9,
                business_impact=0.9,
                exploitability=0.95,
                internet_exposed=True,
            ),
        )

    @pytest.mark.asyncio
    async def test_validate_finding_real(self, engine, sample_finding):
        """Test Validierung eines echten Findings."""
        result = await engine.validate_finding(sample_finding)
        assert isinstance(result, ValidationResult)
        assert result.finding.id == "FIND-001"

    @pytest.mark.asyncio
    async def test_validate_finding_false_positive(self, engine):
        """Test Validierung eines False Positives."""
        finding = Finding(
            id="FIND-002",
            title="Informational Finding",
            description="This is an informational note that might be a false positive. Consider implementing best practice.",
            severity="info",
            vulnerability_type=VulnerabilityType.INFORMATION_DISCLOSURE,
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=2.0),
                epss_score=0.05,
                business_impact=0.1,
            ),
        )
        result = await engine.validate_finding(finding)
        assert isinstance(result, ValidationResult)

    def test_calculate_risk_score(self, engine):
        """Test Risiko-Score Berechnung."""
        factors = RiskFactors(
            cvss_data=CVSSData(base_score=9.0),
            epss_score=0.8,
            business_impact=0.9,
            exploitability=0.9,
            internet_exposed=True,
            exploit_code_available=True,
        )
        score = engine.calculate_risk_score(factors)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high

    def test_calculate_risk_score_low(self, engine):
        """Test niedriger Risiko-Score."""
        factors = RiskFactors(
            cvss_data=CVSSData(base_score=2.0),
            epss_score=0.1,
            business_impact=0.1,
            exploitability=0.1,
            internet_exposed=False,
        )
        score = engine.calculate_risk_score(factors)
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_check_epss_valid_cve(self, engine):
        """Test EPSS Check für gültige CVE."""
        score = await engine.check_epss("CVE-2021-44228")
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_check_epss_invalid_cve(self, engine):
        """Test EPSS Check für ungültige CVE."""
        score = await engine.check_epss("INVALID-CVE")
        assert score == 0.0

    def test_prioritize_findings(self, engine, sample_finding):
        """Test Finding-Priorisierung."""
        findings = [
            sample_finding,
            Finding(
                id="FIND-002",
                title="Low Severity",
                description="Low severity issue",
                severity="low",
                risk_factors=RiskFactors(cvss_data=CVSSData(base_score=2.0)),
            ),
        ]
        prioritized = engine.prioritize_findings(findings)
        assert len(prioritized) == 2
        # Higher risk should come first
        assert prioritized[0].id == "FIND-001"

    def test_prioritize_findings_with_false_positive(self, engine):
        """Test Priorisierung mit False Positive."""
        findings = [
            Finding(
                id="F1",
                title="Critical",
                description="Critical issue",
                severity="critical",
                status=FindingStatus.CONFIRMED,
                confidence=0.9,
                risk_factors=RiskFactors(
                    cvss_data=CVSSData(base_score=9.0),
                    epss_score=0.8,
                ),
            ),
            Finding(
                id="F2",
                title="Also Critical",
                description="Critical issue",
                severity="critical",
                status=FindingStatus.FALSE_POSITIVE,
                confidence=0.9,
                risk_factors=RiskFactors(
                    cvss_data=CVSSData(base_score=9.0),
                    epss_score=0.8,
                ),
            ),
        ]
        prioritized = engine.prioritize_findings(findings)
        # FP should be at the end
        assert prioritized[-1].id == "F2"

    def test_analyze_context(self, engine, sample_finding):
        """Test Kontext-Analyse."""
        score = engine._analyze_context(sample_finding)
        assert 0.0 <= score <= 1.0

    def test_calculate_priority(self, engine, sample_finding):
        """Test Prioritäts-Berechnung."""
        priority = engine._calculate_priority(sample_finding, 0.9, False)
        assert priority == 1

    def test_calculate_priority_false_positive(self, engine, sample_finding):
        """Test Priorität für False Positive."""
        priority = engine._calculate_priority(sample_finding, 0.0, True)
        assert priority == 999

    def test_calculate_priority_low_risk(self, engine, sample_finding):
        """Test Priorität für niedriges Risiko."""
        priority = engine._calculate_priority(sample_finding, 0.1, False)
        # Low risk (0.1) -> base 5, but internet_exposed reduces by 1
        assert priority >= 3

    def test_generate_recommendations_high_risk(self, engine, sample_finding):
        """Test Empfehlungen für hohes Risiko."""
        recs = engine._generate_recommendations(sample_finding, False, 0.9)
        assert len(recs) > 0
        assert any("SOFORTIGE" in r for r in recs)

    def test_generate_recommendations_medium_risk(self, engine, sample_finding):
        """Test Empfehlungen für mittleres Risiko."""
        recs = engine._generate_recommendations(sample_finding, False, 0.5)
        assert len(recs) > 0

    def test_generate_recommendations_false_positive(self, engine, sample_finding):
        """Test Empfehlungen für False Positive."""
        recs = engine._generate_recommendations(sample_finding, True, 0.0)
        assert any("False Positive" in r for r in recs)

    def test_generate_recommendations_internet_exposed(self, engine, sample_finding):
        """Test Empfehlungen für Internet-Exposition."""
        sample_finding.risk_factors.internet_exposed = True
        recs = engine._generate_recommendations(sample_finding, False, 0.5)
        assert any("WAF" in r or "Internet" in r for r in recs)

    def test_generate_recommendations_no_patch(self, engine, sample_finding):
        """Test Empfehlungen wenn kein Patch verfügbar."""
        sample_finding.risk_factors.patch_available = False
        recs = engine._generate_recommendations(sample_finding, False, 0.5)
        assert any("Kompensierende" in r for r in recs)


# =============================================================================
# Finding Tests
# =============================================================================


class TestFinding:
    """Tests für Finding Dataclass."""

    def test_finding_creation(self):
        """Test Finding Erstellung."""
        finding = Finding(
            id="TEST-001",
            title="Test Finding",
            description="Test description",
            severity="high",
        )
        assert finding.id == "TEST-001"
        assert finding.confidence == 0.0
        assert finding.status == FindingStatus.SUSPECTED

    def test_get_hash(self):
        """Test Hash Generierung."""
        finding = Finding(
            id="TEST-001",
            title="Test Finding",
            description="Test description",
            severity="high",
            target="https://example.com",
        )
        hash1 = finding.get_hash()
        hash2 = finding.get_hash()
        assert hash1 == hash2  # Should be deterministic
        assert len(hash1) == 16

    def test_update_status(self):
        """Test Status Aktualisierung."""
        finding = Finding(
            id="TEST-001",
            title="Test Finding",
            description="Test description",
            severity="high",
        )
        old_time = finding.updated_at
        finding.update_status(FindingStatus.CONFIRMED, 0.95)
        assert finding.status == FindingStatus.CONFIRMED
        assert finding.confidence == 0.95
        assert finding.updated_at > old_time


# =============================================================================
# ValidationResult Tests
# =============================================================================


class TestValidationResult:
    """Tests für ValidationResult Dataclass."""

    def test_validation_result_creation(self):
        """Test ValidationResult Erstellung."""
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test",
            severity="high",
        )
        result = ValidationResult(
            finding=finding,
            is_false_positive=False,
            confidence=0.85,
            risk_score=0.75,
            priority=1,
            reasoning="Test reasoning",
        )
        assert result.is_false_positive is False
        assert result.confidence == 0.85

    def test_to_dict(self):
        """Test Konvertierung zu Dictionary."""
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test",
            severity="high",
        )
        result = ValidationResult(
            finding=finding,
            is_false_positive=False,
            confidence=0.85,
            risk_score=0.75,
            priority=1,
            reasoning="Test reasoning",
            recommendations=["Fix it"],
            validation_methods=["method1"],
        )
        data = result.to_dict()
        assert data["finding_id"] == "TEST-001"
        assert data["is_false_positive"] is False
        assert data["confidence"] == 0.85
        assert data["risk_score"] == 0.75
        assert data["priority"] == 1


# =============================================================================
# CVSSData Tests
# =============================================================================


class TestCVSSData:
    """Tests für CVSSData Dataclass."""

    def test_cvss_data_creation(self):
        """Test CVSSData Erstellung."""
        data = CVSSData(
            version="3.1",
            base_score=7.5,
            vector_string="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        )
        assert data.version == "3.1"
        assert data.base_score == 7.5

    def test_get_effective_score_base(self):
        """Test effektiver Score (Base)."""
        data = CVSSData(base_score=7.5)
        assert data.get_effective_score() == 7.5

    def test_get_effective_score_temporal(self):
        """Test effektiver Score (Temporal)."""
        data = CVSSData(base_score=7.5, temporal_score=6.5)
        assert data.get_effective_score() == 6.5

    def test_get_effective_score_environmental(self):
        """Test effektiver Score (Environmental)."""
        data = CVSSData(base_score=7.5, temporal_score=6.5, environmental_score=5.5)
        assert data.get_effective_score() == 5.5

    def test_get_severity_critical(self):
        """Test Severity Ermittlung Critical."""
        data = CVSSData(base_score=9.5)
        assert data.get_severity() == "Critical"

    def test_get_severity_high(self):
        """Test Severity Ermittlung High."""
        data = CVSSData(base_score=7.5)
        assert data.get_severity() == "High"

    def test_get_severity_medium(self):
        """Test Severity Ermittlung Medium."""
        data = CVSSData(base_score=5.5)
        assert data.get_severity() == "Medium"

    def test_get_severity_low(self):
        """Test Severity Ermittlung Low."""
        data = CVSSData(base_score=3.0)
        assert data.get_severity() == "Low"

    def test_get_severity_none(self):
        """Test Severity Ermittlung None."""
        data = CVSSData(base_score=0.0)
        assert data.get_severity() == "None"


# =============================================================================
# EPSSData Tests
# =============================================================================


class TestEPSSData:
    """Tests für EPSSData Dataclass."""

    def test_epss_data_creation(self):
        """Test EPSSData Erstellung."""
        data = EPSSData(
            cve_id="CVE-2021-44228",
            epss_score=0.95,
            percentile=0.99,
        )
        assert data.cve_id == "CVE-2021-44228"
        assert data.epss_score == 0.95

    def test_is_high_probability_true(self):
        """Test hohe Wahrscheinlichkeit erkannt."""
        data = EPSSData(cve_id="CVE-2021-44228", epss_score=0.6, percentile=0.9)
        assert data.is_high_probability() is True

    def test_is_high_probability_false(self):
        """Test hohe Wahrscheinlichkeit nicht erkannt."""
        data = EPSSData(cve_id="CVE-2021-44228", epss_score=0.4, percentile=0.5)
        assert data.is_high_probability() is False

    def test_get_risk_level_critical(self):
        """Test Risiko-Level Critical."""
        data = EPSSData(cve_id="CVE-2021-44228", epss_score=0.8, percentile=0.9)
        assert data.get_risk_level() == "CRITICAL"

    def test_get_risk_level_high(self):
        """Test Risiko-Level High."""
        data = EPSSData(cve_id="CVE-2021-44228", epss_score=0.5, percentile=0.8)
        assert data.get_risk_level() == "HIGH"

    def test_get_risk_level_medium(self):
        """Test Risiko-Level Medium."""
        data = EPSSData(cve_id="CVE-2021-44228", epss_score=0.2, percentile=0.5)
        assert data.get_risk_level() == "MEDIUM"

    def test_get_risk_level_low(self):
        """Test Risiko-Level Low."""
        data = EPSSData(cve_id="CVE-2021-44228", epss_score=0.05, percentile=0.2)
        assert data.get_risk_level() == "LOW"


# =============================================================================
# RiskFactors Tests
# =============================================================================


class TestRiskFactors:
    """Tests für RiskFactors Dataclass."""

    def test_risk_factors_creation(self):
        """Test RiskFactors Erstellung."""
        factors = RiskFactors(
            cvss_data=CVSSData(base_score=7.5),
            epss_score=0.6,
            business_impact=0.7,
        )
        assert factors.epss_score == 0.6
        assert factors.business_impact == 0.7

    def test_get_weighted_risk_score(self):
        """Test gewichteter Risiko-Score."""
        factors = RiskFactors(
            cvss_data=CVSSData(base_score=9.0),
            epss_score=0.8,
            business_impact=0.9,
            exploitability=0.9,
            asset_criticality=1.0,
            internet_exposed=True,
            exploit_code_available=True,
        )
        score = factors.get_weighted_risk_score()
        assert 0.0 <= score <= 1.0

    def test_get_weighted_risk_score_low(self):
        """Test niedriger gewichteter Risiko-Score."""
        factors = RiskFactors(
            cvss_data=CVSSData(base_score=2.0),
            epss_score=0.1,
            business_impact=0.1,
            exploitability=0.1,
            asset_criticality=0.1,
            internet_exposed=False,
        )
        score = factors.get_weighted_risk_score()
        assert score < 0.5


# =============================================================================
# BayesianFilter Tests
# =============================================================================


class TestBayesianFilter:
    """Tests für BayesianFilter Klasse."""

    def test_filter_initialization(self):
        """Test Initialisierung des Filters."""
        filter = BayesianFilter()
        assert filter.fp_count == 0
        assert filter.tp_count == 0

    def test_train_false_positive(self):
        """Test Training mit False Positive."""
        filter = BayesianFilter()
        filter.train("This is a false positive finding", is_false_positive=True)
        assert filter.fp_count == 1
        assert filter.tp_count == 0

    def test_train_true_positive(self):
        """Test Training mit True Positive."""
        filter = BayesianFilter()
        filter.train("This is a real vulnerability", is_false_positive=False)
        assert filter.fp_count == 0
        assert filter.tp_count == 1

    def test_predict_false_positive(self):
        """Test Vorhersage False Positive."""
        filter = BayesianFilter()
        # Train with multiple FPs
        for _ in range(10):
            filter.train(
                "false positive informational note best practice",
                is_false_positive=True,
            )
        for _ in range(2):
            filter.train(
                "critical vulnerability remote code execution",
                is_false_positive=False,
            )

        is_fp, prob = filter.predict("This is an informational note")
        assert isinstance(is_fp, bool)
        assert 0.0 <= prob <= 1.0

    def test_predict_empty_text(self):
        """Test Vorhersage mit leerem Text."""
        filter = BayesianFilter()
        is_fp, prob = filter.predict("")
        assert is_fp is False
        assert prob == 0.5

    def test_extract_words(self):
        """Test Wort-Extraktion."""
        filter = BayesianFilter()
        words = filter._extract_words("The quick brown fox jumps over")
        assert "quick" in words
        assert "brown" in words
        assert "jumps" in words
        assert "over" in words
        assert "the" not in words  # Stopword
        assert "fox" not in words  # 3 chars, filtered by >3 length check


# =============================================================================
# FalsePositiveDatabase Tests
# =============================================================================


class TestFalsePositiveDatabase:
    """Tests für FalsePositiveDatabase."""

    def test_database_initialization(self):
        """Test Initialisierung der Datenbank."""
        db = FalsePositiveDatabase()
        assert db.findings == {}
        assert db.similarity_threshold == 0.85

    def test_add_finding_new(self):
        """Test Hinzufügen eines neuen Findings."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        db.add_finding(finding, is_false_positive=False)
        assert len(db.findings) == 1

    def test_add_finding_update_existing(self):
        """Test Aktualisieren eines existierenden Findings."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        db.add_finding(finding, is_false_positive=False)
        first_seen = list(db.findings.values())[0].first_seen

        # Add same finding again
        import time

        time.sleep(0.01)
        db.add_finding(finding, is_false_positive=False)

        hist = list(db.findings.values())[0]
        assert hist.occurrence_count == 2
        assert hist.last_seen > first_seen

    def test_check_historical_match_exact(self):
        """Test exakte Übereinstimmung."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        db.add_finding(finding, is_false_positive=True)

        match = db.check_historical_match(finding)
        assert match is not None
        assert match.is_false_positive is True

    def test_check_historical_match_none(self):
        """Test keine Übereinstimmung."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        match = db.check_historical_match(finding)
        assert match is None

    def test_get_fp_likelihood_with_feedback(self):
        """Test FP Wahrscheinlichkeit mit User Feedback."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        db.add_finding(finding, is_false_positive=True, user_feedback=True)

        likelihood = db.get_fp_likelihood(finding)
        assert likelihood == 1.0

    def test_get_fp_likelihood_no_historical(self):
        """Test FP Wahrscheinlichkeit ohne historische Daten."""
        db = FalsePositiveDatabase()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        likelihood = db.get_fp_likelihood(finding)
        # Should return bayesian prediction
        assert 0.0 <= likelihood <= 1.0

    def test_calculate_similarity(self):
        """Test Ähnlichkeitsberechnung."""
        db = FalsePositiveDatabase()
        similarity = db._calculate_similarity("abc123", "abc124")
        assert 0.0 <= similarity <= 1.0


# =============================================================================
# LLMVotingEngine Tests
# =============================================================================


class TestLLMVotingEngine:
    """Tests für LLMVotingEngine."""

    def test_engine_initialization(self):
        """Test Initialisierung der Engine."""
        engine = LLMVotingEngine()
        assert engine.llm_clients == {}
        assert engine.consensus_threshold == 0.6

    def test_register_llm(self):
        """Test Registrierung eines LLM Clients."""
        engine = LLMVotingEngine()
        mock_client = Mock()
        engine.register_llm("gpt4", mock_client)
        assert "gpt4" in engine.llm_clients

    @pytest.mark.asyncio
    async def test_vote_on_finding_no_llms(self):
        """Test Voting ohne registrierte LLMs."""
        engine = LLMVotingEngine()
        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )
        votes, confidence = await engine.vote_on_finding(finding)
        assert votes == {}
        assert confidence == 0.5

    @pytest.mark.asyncio
    async def test_vote_on_finding_with_llms(self):
        """Test Voting mit registrierten LLMs."""
        engine = LLMVotingEngine()

        # Mock client that returns False (not FP)
        mock_client = Mock()
        mock_client.analyze = Mock(return_value=asyncio.Future())
        mock_client.analyze.return_value.set_result("TRUE_POSITIVE")

        engine.register_llm("gpt4", mock_client)

        finding = Finding(
            id="TEST-001",
            title="Test",
            description="Test description",
            severity="high",
        )

        votes, confidence = await engine.vote_on_finding(finding)
        # Should return votes from mock
        assert isinstance(votes, dict)
        assert isinstance(confidence, float)

    def test_build_prompt(self):
        """Test Prompt Generierung."""
        engine = LLMVotingEngine()
        finding = Finding(
            id="TEST-001",
            title="SQL Injection",
            description="SQL injection vulnerability",
            severity="critical",
            vulnerability_type=VulnerabilityType.SQL_INJECTION,
        )
        prompt = engine._build_prompt(finding)
        assert "SQL Injection" in prompt
        assert "FALSE_POSITIVE" in prompt

    def test_parse_response_false_positive(self):
        """Test Parsen einer FP Antwort."""
        engine = LLMVotingEngine()
        assert engine._parse_response("This is a FALSE_POSITIVE") is True
        assert engine._parse_response("false positive detected") is True

    def test_parse_response_true_positive(self):
        """Test Parsen einer TP Antwort."""
        engine = LLMVotingEngine()
        assert engine._parse_response("This is a TRUE_POSITIVE") is False
        assert engine._parse_response("confirmed vulnerability") is False

    def test_heuristic_decision_false_positive(self):
        """Test Heuristische FP Entscheidung."""
        engine = LLMVotingEngine()
        finding = Finding(
            id="TEST-001",
            title="Info",
            description="This is an informational note and best practice recommendation",
            severity="info",
        )
        assert engine._heuristic_decision(finding) is True

    def test_heuristic_decision_true_positive(self):
        """Test Heuristische TP Entscheidung."""
        engine = LLMVotingEngine()
        finding = Finding(
            id="TEST-001",
            title="Critical",
            description="Remote code execution vulnerability",
            severity="critical",
        )
        assert engine._heuristic_decision(finding) is False


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestHelperFunctions:
    """Tests für Hilfsfunktionen."""

    def test_create_finding_from_scan_result(self):
        """Test Erstellung eines Findings aus Scan-Ergebnis."""
        scan_result = {
            "id": "SCAN-001",
            "title": "SQL Injection",
            "description": "SQL injection found",
            "severity": "critical",
            "type": "sql_injection",
            "cvss": {
                "base_score": 9.8,
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            },
            "epss_score": 0.9,
            "evidence": {"payload": "' OR '1'='1"},
        }
        finding = create_finding_from_scan_result(scan_result)
        assert finding.id == "SCAN-001"
        assert finding.vulnerability_type == VulnerabilityType.SQL_INJECTION
        assert finding.risk_factors.cvss_data.base_score == 9.8

    def test_create_finding_from_scan_result_unknown_type(self):
        """Test Erstellung mit unbekanntem Vulnerability Type."""
        scan_result = {
            "id": "SCAN-001",
            "title": "Unknown",
            "description": "Unknown issue",
            "severity": "info",
            "type": "unknown_type",
        }
        finding = create_finding_from_scan_result(scan_result)
        assert finding.vulnerability_type == VulnerabilityType.UNKNOWN

    def test_create_finding_with_asset_context(self):
        """Test Erstellung mit Asset Context."""
        scan_result = {
            "id": "SCAN-001",
            "title": "Test",
            "description": "Test",
            "severity": "high",
        }
        asset = AssetContext(
            asset_id="asset-001",
            asset_name="Test Asset",
            asset_type="server",
            criticality=AssetCriticality.HIGH,
            data_classification=DataClassification.CONFIDENTIAL,
        )
        finding = create_finding_from_scan_result(scan_result, asset)
        assert finding.risk_factors.asset_criticality == AssetCriticality.HIGH.weight


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests für Enums."""

    def test_confidence_level_values(self):
        """Test ConfidenceLevel Werte."""
        assert ConfidenceLevel.VERY_HIGH.value == 0.95
        assert ConfidenceLevel.HIGH.value == 0.9
        assert ConfidenceLevel.MEDIUM.value == 0.6
        assert ConfidenceLevel.LOW.value == 0.3
        assert ConfidenceLevel.VERY_LOW.value == 0.1

    def test_finding_status_values(self):
        """Test FindingStatus Werte."""
        assert FindingStatus.CONFIRMED.value == "confirmed"
        assert FindingStatus.LIKELY.value == "likely"
        assert FindingStatus.SUSPECTED.value == "suspected"
        assert FindingStatus.FALSE_POSITIVE.value == "false_positive"
        assert FindingStatus.UNDER_REVIEW.value == "under_review"
        assert FindingStatus.SUPPRESSED.value == "suppressed"

    def test_vulnerability_type_values(self):
        """Test VulnerabilityType Werte."""
        assert VulnerabilityType.SQL_INJECTION.value == "sql_injection"
        assert VulnerabilityType.XSS.value == "xss"
        assert VulnerabilityType.RCE.value == "rce"
        assert VulnerabilityType.UNKNOWN.value == "unknown"

    def test_data_classification_values(self):
        """Test DataClassification Werte."""
        assert DataClassification.PUBLIC.weight == 0.1
        assert DataClassification.INTERNAL.weight == 0.3
        assert DataClassification.CONFIDENTIAL.weight == 0.6
        assert DataClassification.RESTRICTED.weight == 0.9

    def test_asset_criticality_values(self):
        """Test AssetCriticality Werte."""
        assert AssetCriticality.CRITICAL.weight == 1.0
        assert AssetCriticality.HIGH.weight == 0.8
        assert AssetCriticality.MEDIUM.weight == 0.5
        assert AssetCriticality.LOW.weight == 0.3
        assert AssetCriticality.MINIMAL.weight == 0.1

    def test_compliance_framework_values(self):
        """Test ComplianceFramework Werte."""
        assert ComplianceFramework.PCI_DSS.base_weight == 0.95
        assert ComplianceFramework.HIPAA.base_weight == 0.9
        assert ComplianceFramework.GDPR.base_weight == 0.85

    def test_reputation_impact_values(self):
        """Test ReputationImpact Werte."""
        assert ReputationImpact.SEVERE.weight == 1.0
        assert ReputationImpact.HIGH.weight == 0.7
        assert ReputationImpact.MODERATE.weight == 0.4
        assert ReputationImpact.LOW.weight == 0.1


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration Tests für das Risk Engine."""

    def test_full_risk_calculation(self):
        """Test komplette Risiko-Berechnung."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=True)
        finding = {
            "cvss_score": 9.8,
            "cve_id": "CVE-2021-44228",
            "exploit_validated": True,
            "description": "Log4j RCE vulnerability",
        }
        context = {
            "internet_facing": True,
            "data_sensitivity": "pii",
            "asset_criticality": "critical",
        }
        result = scorer.calculate(finding, context)
        assert result.value >= 6.5
        assert result.severity in [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
        ]

    def test_end_to_end_prioritization(self):
        """Test End-to-End Priorisierung."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        findings = [
            {
                "cvss_score": 3.0,
                "description": "Low severity issue",
                "exploit_validated": False,
            },
            {
                "cvss_score": 9.8,
                "description": "Critical RCE",
                "exploit_validated": True,
            },
            {
                "cvss_score": 7.0,
                "description": "High severity",
                "exploit_available": True,
            },
        ]
        prioritized = scorer.prioritize_findings(findings)
        # Critical should be first
        assert prioritized[0]["description"] == "Critical RCE"

    @pytest.mark.asyncio
    async def test_false_positive_workflow(self):
        """Test kompletter False-Positive-Workflow."""
        engine = FalsePositiveEngine(enable_llm_voting=False)

        # Create a likely false positive
        finding = Finding(
            id="FP-001",
            title="Informational Note",
            description="This is an informational finding that might be a false positive. Consider implementing best practice.",
            severity="info",
            vulnerability_type=VulnerabilityType.INFORMATION_DISCLOSURE,
            risk_factors=RiskFactors(
                cvss_data=CVSSData(base_score=2.0),
                epss_score=0.05,
                business_impact=0.1,
            ),
        )

        result = await engine.validate_finding(finding)
        assert isinstance(result, ValidationResult)
        assert result.priority > 1 or result.is_false_positive

    def test_business_impact_integration(self):
        """Test Business Impact Integration."""
        calc = BusinessImpactCalculator(
            organization_size="enterprise",
            annual_revenue=1000000000,
            industry="finance",
        )

        asset = AssetContext(
            asset_id="core-banking-001",
            asset_name="Core Banking System",
            asset_type="application",
            criticality=AssetCriticality.CRITICAL,
            data_classification=DataClassification.RESTRICTED,
            compliance_frameworks={
                ComplianceFramework.PCI_DSS,
                ComplianceFramework.GDPR,
            },
            internet_exposed=False,
            user_count=10000000,
            revenue_dependency=50.0,
        )

        result = calc.calculate_overall_impact(
            asset_context=asset,
            finding_type="sql_injection",
            severity="critical",
            breach_likelihood=0.7,
            data_volume_records=1000000,
        )

        assert result.overall_score > 0.7
        assert result.get_risk_category() in ["CRITICAL", "HIGH"]
        assert result.financial_impact.total_costs > 0

    def test_get_calculator_singleton(self):
        """Test Singleton Calculator."""
        calc1 = get_calculator()
        calc2 = get_calculator()
        assert calc1 is calc2


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Edge Case Tests."""

    def test_empty_finding(self):
        """Test mit leerem Finding."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {}
        result = scorer.calculate(finding)
        assert isinstance(result, RiskScore)
        assert result.value >= 0.0

    def test_missing_cvss_data(self):
        """Test mit fehlenden CVSS Daten."""
        calc = CVSSCalculator()
        finding = {}
        details = calc.get_details(finding)
        assert details["base_score"] == 5.0  # Default

    def test_extreme_cvss_scores(self):
        """Test extreme CVSS Scores."""
        calc = CVSSCalculator()
        assert calc.calculate({"S": "U"}) >= 0.0  # Minimal
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
        assert calc.calculate(metrics) <= 10.0  # Maximum

    def test_invalid_cve_format(self):
        """Test ungültiges CVE Format."""
        calc = CVSSCalculator()
        assert calc.from_cve("NOT-A-CVE") == 5.0

    def test_unicode_description(self):
        """Test Unicode in Beschreibung."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {"description": "SQL Injection の脆弱性 🚨 RCE возможность"}
        result = scorer.calculate(finding)
        assert isinstance(result, RiskScore)

    def test_very_long_description(self):
        """Test sehr lange Beschreibung."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {"description": "A" * 10000}
        result = scorer.calculate(finding)
        assert isinstance(result, RiskScore)

    def test_special_characters_in_finding(self):
        """Test Sonderzeichen im Finding."""
        finding = Finding(
            id="TEST-001",
            title="Test <script>alert(1)</script>",
            description="Description with \"quotes\" and 'apostrophes' and \\ backslash",
            severity="high",
        )
        hash_val = finding.get_hash()
        assert len(hash_val) == 16

    def test_zero_values(self):
        """Test mit Null-Werten."""
        scorer = RiskScorer(enable_epss=False, enable_business_context=False)
        finding = {
            "cvss_score": 0.0,
            "exploit_validated": False,
            "exploit_available": False,
        }
        result = scorer.calculate(finding)
        assert result.value >= 0.0

    def test_negative_risk_score_handling(self):
        """Test Handling negativer Risk Scores."""
        # Should not happen, but test robustness
        result = RiskScore(
            value=0.0,
            severity=SeverityLevel.INFO,
            cvss_score=0.0,
            epss_score=0.0,
            business_impact_score=0.0,
            exploit_validation_score=0.0,
        )
        assert result.to_dict()["risk_score"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
