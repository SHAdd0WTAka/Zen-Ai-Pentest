"""
Unit Tests für risk_engine/cvss.py

Tests CVSS v3.1 scoring calculations.
"""

import pytest

from risk_engine.cvss import CVSSCalculator

pytestmark = pytest.mark.unit


class TestCVSSCalculatorInit:
    """Test CVSSCalculator initialization"""

    def test_init(self):
        """Test calculator initialization"""
        calc = CVSSCalculator()
        assert calc is not None
        assert hasattr(calc, "WEIGHTS")
        assert "AV" in calc.WEIGHTS
        assert "AC" in calc.WEIGHTS


class TestCVSSCalculate:
    """Test calculate method"""

    def test_critical_cvss(self):
        """Test critical CVSS score calculation"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "N",  # Network
            "AC": "L",  # Low
            "PR": "N",  # None
            "UI": "N",  # None
            "S": "C",  # Changed
            "C": "H",  # High
            "I": "H",  # High
            "A": "H",  # High
        }
        score = calc.calculate(metrics)
        assert 9.0 <= score <= 10.0
        assert score == 10.0

    def test_high_cvss(self):
        """Test high CVSS score calculation"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "N",
            "AC": "L",
            "PR": "L",  # Low privilege
            "UI": "N",
            "S": "U",  # Unchanged
            "C": "H",
            "I": "H",
            "A": "H",
        }
        score = calc.calculate(metrics)
        assert 7.0 <= score <= 8.9

    def test_medium_cvss(self):
        """Test medium CVSS score calculation"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "N",
            "AC": "H",  # High complexity
            "PR": "L",
            "UI": "R",  # Required
            "S": "U",
            "C": "L",  # Low
            "I": "L",
            "A": "L",
        }
        score = calc.calculate(metrics)
        assert 4.0 <= score <= 6.9

    def test_low_cvss(self):
        """Test low CVSS score calculation"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "L",  # Local
            "AC": "H",
            "PR": "H",  # High privilege
            "UI": "R",
            "S": "U",
            "C": "N",  # None
            "I": "N",
            "A": "L",
        }
        score = calc.calculate(metrics)
        assert 0.1 <= score <= 3.9

    def test_zero_impact(self):
        """Test CVSS with no impact (C=I=A=N)"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "N",
            "AC": "L",
            "PR": "N",
            "UI": "N",
            "S": "U",
            "C": "N",
            "I": "N",
            "A": "N",
        }
        score = calc.calculate(metrics)
        assert score == 0.0

    def test_default_values(self):
        """Test calculation with missing metrics uses defaults"""
        calc = CVSSCalculator()
        score = calc.calculate({})  # Empty metrics
        assert score >= 0.0
        assert score <= 10.0

    def test_partial_metrics(self):
        """Test calculation with partial metrics"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "N",
            "AC": "L",
        }
        score = calc.calculate(metrics)
        assert score >= 0.0
        assert score <= 10.0

    def test_network_scope_changed(self):
        """Test scope changed affects score"""
        calc = CVSSCalculator()
        base_metrics = {
            "AV": "N",
            "AC": "L",
            "PR": "N",
            "UI": "N",
            "C": "H",
            "I": "H",
            "A": "H",
        }

        unchanged = calc.calculate({**base_metrics, "S": "U"})
        changed = calc.calculate({**base_metrics, "S": "C"})

        # Changed scope should have higher or equal score
        assert changed >= unchanged

    def test_local_vs_network(self):
        """Test network accessibility increases score"""
        calc = CVSSCalculator()
        base_metrics = {
            "AC": "L",
            "PR": "N",
            "UI": "N",
            "S": "U",
            "C": "H",
            "I": "H",
            "A": "H",
        }

        local = calc.calculate({**base_metrics, "AV": "L"})
        network = calc.calculate({**base_metrics, "AV": "N"})

        assert network > local

    def test_invalid_metrics(self):
        """Test with invalid metric values"""
        calc = CVSSCalculator()
        metrics = {
            "AV": "INVALID",
            "AC": "INVALID",
        }
        # Should use defaults and return valid score
        score = calc.calculate(metrics)
        assert 0.0 <= score <= 10.0


class TestCVSSFromCVE:
    """Test from_cve method"""

    def test_known_cve_log4j(self):
        """Test Log4j CVE lookup"""
        calc = CVSSCalculator()
        score = calc.from_cve("CVE-2021-44228")
        assert score == 10.0

    def test_known_cve_eternalblue(self):
        """Test EternalBlue CVE lookup"""
        calc = CVSSCalculator()
        score = calc.from_cve("CVE-2017-0144")
        assert score == 8.1

    def test_known_cve_heartbleed(self):
        """Test Heartbleed CVE lookup"""
        calc = CVSSCalculator()
        score = calc.from_cve("CVE-2014-0160")
        assert score == 5.0

    def test_unknown_cve(self):
        """Test unknown CVE returns default"""
        calc = CVSSCalculator()
        score = calc.from_cve("CVE-2099-99999")
        assert score == 5.0

    def test_cve_case_insensitive(self):
        """Test CVE ID is case insensitive"""
        calc = CVSSCalculator()
        score_lower = calc.from_cve("cve-2021-44228")
        score_upper = calc.from_cve("CVE-2021-44228")
        assert score_lower == score_upper


class TestCVSSEstimate:
    """Test estimate method"""

    def test_estimate_rce(self):
        """Test RCE description - RCE gets 9.8 base but network adds +0.5 = 10.0"""
        calc = CVSSCalculator()
        score = calc.estimate("Remote Code Execution vulnerability")
        # RCE = 9.8, contains "remote" = +0.5, capped at 10.0
        assert score == 10.0

    def test_estimate_sql_injection(self):
        """Test SQL injection description"""
        calc = CVSSCalculator()
        score = calc.estimate("SQL injection vulnerability")
        assert score == 8.6

    def test_estimate_xss(self):
        """Test XSS description"""
        calc = CVSSCalculator()
        score = calc.estimate("Cross-site scripting vulnerability")
        assert score == 6.1

    def test_estimate_dos(self):
        """Test DoS description"""
        calc = CVSSCalculator()
        score = calc.estimate("Denial of Service vulnerability")
        assert score == 7.5

    def test_estimate_info_disclosure(self):
        """Test information disclosure"""
        calc = CVSSCalculator()
        score = calc.estimate("Information disclosure vulnerability")
        assert score == 5.3

    def test_estimate_auth_bypass(self):
        """Test authentication bypass"""
        calc = CVSSCalculator()
        score = calc.estimate("Authentication bypass vulnerability")
        assert score == 8.1

    def test_estimate_network_boost(self):
        """Test network keyword increases score"""
        calc = CVSSCalculator()
        base = calc.estimate("SQL injection vulnerability")
        network = calc.estimate("SQL injection vulnerability network accessible")
        assert network > base

    def test_estimate_unauthenticated_boost(self):
        """Test unauthenticated keyword increases score"""
        calc = CVSSCalculator()
        base = calc.estimate("SQL injection vulnerability")
        unauth = calc.estimate("SQL injection without authentication")
        assert unauth > base

    def test_estimate_default(self):
        """Test default score for unknown description"""
        calc = CVSSCalculator()
        score = calc.estimate("Some random vulnerability")
        assert score == 5.0

    def test_estimate_caps_independent(self):
        """Test case insensitivity"""
        calc = CVSSCalculator()
        lower = calc.estimate("rce vulnerability")
        upper = calc.estimate("RCE vulnerability")
        assert lower == upper


class TestCVSSGetDetails:
    """Test get_details method"""

    def test_details_critical(self):
        """Test details for critical finding"""
        calc = CVSSCalculator()
        finding = {"cvss_score": 9.5, "cvss_vector": "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"}
        details = calc.get_details(finding)

        assert details["base_score"] == 9.5
        assert details["severity"] == "Critical"
        assert details["vector"] == "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"

    def test_details_high(self):
        """Test details for high finding"""
        calc = CVSSCalculator()
        finding = {"cvss_score": 7.5}
        details = calc.get_details(finding)

        assert details["severity"] == "High"

    def test_details_medium(self):
        """Test details for medium finding"""
        calc = CVSSCalculator()
        finding = {"cvss_score": 5.5}
        details = calc.get_details(finding)

        assert details["severity"] == "Medium"

    def test_details_low(self):
        """Test details for low finding"""
        calc = CVSSCalculator()
        finding = {"cvss_score": 2.0}
        details = calc.get_details(finding)

        assert details["severity"] == "Low"

    def test_details_none(self):
        """Test details for zero score"""
        calc = CVSSCalculator()
        finding = {"cvss_score": 0.0}
        details = calc.get_details(finding)

        assert details["severity"] == "None"

    def test_details_defaults(self):
        """Test defaults for missing fields"""
        calc = CVSSCalculator()
        finding = {}  # Empty finding
        details = calc.get_details(finding)

        assert details["base_score"] == 5.0  # Default
        assert details["vector"] == "Unknown"
        assert details["version"] == "3.1"


class TestCVSSGetVector:
    """Test get_vector_from_metrics method"""

    def test_full_vector(self):
        """Test generating full CVSS vector"""
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
        assert "C:H" in vector

    def test_partial_vector(self):
        """Test generating partial vector"""
        calc = CVSSCalculator()
        metrics = {"AV": "N", "AC": "L"}
        vector = calc.get_vector_from_metrics(metrics)

        assert vector == "CVSS:3.1/AV:N/AC:L"

    def test_empty_vector(self):
        """Test generating vector from empty metrics"""
        calc = CVSSCalculator()
        vector = calc.get_vector_from_metrics({})

        assert vector == "CVSS:3.1"


class TestCVSSWeights:
    """Test CVSS weights constants"""

    def test_av_weights(self):
        """Test Attack Vector weights"""
        calc = CVSSCalculator()
        assert calc.WEIGHTS["AV"]["N"] == 0.85  # Network
        assert calc.WEIGHTS["AV"]["A"] == 0.62  # Adjacent
        assert calc.WEIGHTS["AV"]["L"] == 0.55  # Local
        assert calc.WEIGHTS["AV"]["P"] == 0.2  # Physical

    def test_scope_weights(self):
        """Test Scope weights"""
        calc = CVSSCalculator()
        assert calc.WEIGHTS["S"]["U"] == 6.42  # Unchanged
        assert calc.WEIGHTS["S"]["C"] == 7.52  # Changed
