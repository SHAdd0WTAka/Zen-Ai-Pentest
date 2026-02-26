"""Tests for risk/cvss.py - CVSS 3.1 Calculator."""

import pytest
from risk.cvss import (
    CVSSCalculator,
    CVSSMetric,
    CVSSVector,
)


class TestCVSSMetric:
    """Test CVSSMetric enum."""

    def test_attack_vector_values(self):
        """Test attack vector metric values."""
        assert CVSSMetric.AV_NETWORK.value == "N"
        assert CVSSMetric.AV_ADJACENT.value == "A"
        assert CVSSMetric.AV_LOCAL.value == "L"
        assert CVSSMetric.AV_PHYSICAL.value == "P"

    def test_attack_complexity_values(self):
        """Test attack complexity metric values."""
        assert CVSSMetric.AC_LOW.value == "L"
        assert CVSSMetric.AC_HIGH.value == "H"

    def test_privileges_required_values(self):
        """Test privileges required metric values."""
        assert CVSSMetric.PR_NONE.value == "N"
        assert CVSSMetric.PR_LOW.value == "L"
        assert CVSSMetric.PR_HIGH.value == "H"

    def test_user_interaction_values(self):
        """Test user interaction metric values."""
        assert CVSSMetric.UI_NONE.value == "N"
        assert CVSSMetric.UI_REQUIRED.value == "R"

    def test_scope_values(self):
        """Test scope metric values."""
        assert CVSSMetric.S_UNCHANGED.value == "U"
        assert CVSSMetric.S_CHANGED.value == "C"

    def test_impact_values(self):
        """Test impact metric values."""
        # Confidentiality
        assert CVSSMetric.C_NONE.value == "N"
        assert CVSSMetric.C_LOW.value == "L"
        assert CVSSMetric.C_HIGH.value == "H"

        # Integrity
        assert CVSSMetric.I_NONE.value == "N"
        assert CVSSMetric.I_LOW.value == "L"
        assert CVSSMetric.I_HIGH.value == "H"

        # Availability
        assert CVSSMetric.A_NONE.value == "N"
        assert CVSSMetric.A_LOW.value == "L"
        assert CVSSMetric.A_HIGH.value == "H"


class TestCVSSVector:
    """Test CVSSVector dataclass."""

    def test_default_values(self):
        """Test default vector values."""
        vector = CVSSVector()

        assert vector.av == "N"
        assert vector.ac == "L"
        assert vector.pr == "N"
        assert vector.ui == "N"
        assert vector.s == "U"
        assert vector.c == "N"
        assert vector.i == "N"
        assert vector.a == "N"

    def test_to_vector_string_base(self):
        """Test generating base vector string."""
        vector = CVSSVector()
        result = vector.to_vector_string()

        assert result == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"

    def test_to_vector_string_with_temporal(self):
        """Test generating vector string with temporal metrics."""
        vector = CVSSVector(e="H", rl="O", rc="C")
        result = vector.to_vector_string()

        assert "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N" in result
        assert "/E:H" in result
        assert "/RL:O" in result
        assert "/RC:C" in result

    def test_from_vector_string(self):
        """Test parsing vector string."""
        vector_str = "CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:C/C:H/I:L/A:N"
        vector = CVSSVector.from_vector_string(vector_str)

        assert vector.av == "N"
        assert vector.ac == "H"
        assert vector.pr == "L"
        assert vector.ui == "R"
        assert vector.s == "C"
        assert vector.c == "H"
        assert vector.i == "L"
        assert vector.a == "N"


class TestCVSSCalculator:
    """Test CVSSCalculator class."""

    def test_init(self):
        """Test calculator initialization."""
        calc = CVSSCalculator()

        assert isinstance(calc.calculation_log, list)
        assert calc.WEIGHTS["AV"]["N"] == 0.85
        assert calc.WEIGHTS["AC"]["L"] == 0.77

    def test_calculate_base_score_minimal(self):
        """Test base score calculation for minimal vector."""
        calc = CVSSCalculator()
        vector = CVSSVector()  # All None defaults

        score = calc.calculate_base_score(vector)

        # All None metrics = 0.0 score
        assert score == 0.0

    def test_calculate_base_score_network_critical(self):
        """Test base score for critical network vector."""
        calc = CVSSCalculator()
        vector = CVSSVector(
            av="N",  # Network
            ac="L",  # Low complexity
            pr="N",  # No privileges
            ui="N",  # No interaction
            s="U",   # Unchanged scope
            c="H",   # High confidentiality
            i="H",   # High integrity
            a="H",   # High availability
        )

        score = calc.calculate_base_score(vector)

        # Should be high/critical
        assert score >= 9.0

    def test_calculate_base_score_scope_changed(self):
        """Test base score with scope changed."""
        calc = CVSSCalculator()
        vector = CVSSVector(
            av="N",
            ac="L",
            pr="L",
            ui="N",
            s="C",  # Changed scope
            c="H",
            i="H",
            a="H",
        )

        score = calc.calculate_base_score(vector)

        # Scope changed increases score
        assert score > 0.0

    def test_calculate_base_score_low_impact(self):
        """Test base score for low impact vector."""
        calc = CVSSCalculator()
        vector = CVSSVector(
            av="P",  # Physical
            ac="H",  # High complexity
            pr="H",  # High privileges
            ui="R",  # Required interaction
            s="U",
            c="L",   # Low impact
            i="N",
            a="N",
        )

        score = calc.calculate_base_score(vector)

        # Should be low
        assert score < 4.0

    def test_calculate_temporal_score_no_temporal(self):
        """Test temporal score when no temporal metrics."""
        calc = CVSSCalculator()
        vector = CVSSVector()  # No temporal metrics
        base_score = 7.5

        temporal = calc.calculate_temporal_score(vector, base_score)

        assert temporal == base_score

    def test_calculate_temporal_score_with_exploit(self):
        """Test temporal score with exploit maturity."""
        calc = CVSSCalculator()
        vector = CVSSVector(e="H")  # High exploit maturity
        base_score = 7.5

        temporal = calc.calculate_temporal_score(vector, base_score)

        # High exploit maturity doesn't reduce score (weight 1.0)
        assert temporal == base_score

    def test_calculate_temporal_score_with_remediation(self):
        """Test temporal score with remediation level."""
        calc = CVSSCalculator()
        vector = CVSSVector(rl="O")  # Official fix
        base_score = 10.0

        temporal = calc.calculate_temporal_score(vector, base_score)

        # Official fix reduces score (weight 0.95)
        assert temporal < base_score

    def test_get_severity_rating(self):
        """Test severity rating from score."""
        calc = CVSSCalculator()

        assert calc.get_severity_rating(0.0) == "None"
        assert calc.get_severity_rating(1.0) == "Low"
        assert calc.get_severity_rating(3.9) == "Low"
        assert calc.get_severity_rating(4.0) == "Medium"
        assert calc.get_severity_rating(6.9) == "Medium"
        assert calc.get_severity_rating(7.0) == "High"
        assert calc.get_severity_rating(8.9) == "High"
        assert calc.get_severity_rating(9.0) == "Critical"
        assert calc.get_severity_rating(10.0) == "Critical"

    def test_calculate_full(self):
        """Test full calculation with all metrics."""
        calc = CVSSCalculator()
        vector = CVSSVector(
            av="N",
            ac="L",
            pr="N",
            ui="N",
            s="U",
            c="H",
            i="H",
            a="H",
            e="F",
            rl="W",
        )

        result = calc.calculate_full(vector)

        assert "base_score" in result
        assert "temporal_score" in result
        assert "severity" in result
        assert "vector_string" in result
        assert "metrics" in result

        assert result["severity"] == "Critical"
        assert result["metrics"]["attack_vector"] == "N"

    def test_estimate_from_cve_with_cvss3(self):
        """Test estimation from CVE with CVSS3 data."""
        calc = CVSSCalculator()
        cve_data = {
            "cvss3": {
                "vectorString": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H",
            }
        }

        vector = calc.estimate_from_cve(cve_data)

        assert vector.av == "N"
        assert vector.ac == "H"
        assert vector.c == "H"

    def test_estimate_from_cve_remote_rce(self):
        """Test estimation from CVE description with RCE."""
        calc = CVSSCalculator()
        cve_data = {
            "description": "Remote code execution vulnerability",
        }

        vector = calc.estimate_from_cve(cve_data)

        assert vector.av == "N"  # Remote = Network
        assert vector.c == "H"   # RCE = High confidentiality
        assert vector.i == "H"   # RCE = High integrity
        assert vector.a == "H"   # RCE = High availability

    def test_estimate_from_cve_local_info_disclosure(self):
        """Test estimation from CVE description with local info disclosure."""
        calc = CVSSCalculator()
        cve_data = {
            "description": "Local information disclosure with authentication required",
        }

        vector = calc.estimate_from_cve(cve_data)

        assert vector.av == "L"  # Local
        assert vector.pr == "L"  # Authentication required
        assert vector.c == "H"   # Info disclosure = High confidentiality

    def test_estimate_from_cve_dos(self):
        """Test estimation from CVE description with DoS."""
        calc = CVSSCalculator()
        cve_data = {
            "description": "Denial of service vulnerability",
        }

        vector = calc.estimate_from_cve(cve_data)

        assert vector.a == "H"  # DoS = High availability

    def test_estimate_from_cve_default(self):
        """Test estimation from empty CVE data."""
        calc = CVSSCalculator()
        cve_data = {}

        vector = calc.estimate_from_cve(cve_data)

        # Should return default vector
        assert vector.av == "N"
        assert vector.c == "N"


class TestIntegration:
    """Integration tests for CVSS calculator."""

    def test_vector_roundtrip(self):
        """Test vector string roundtrip."""
        original = CVSSVector(
            av="N",
            ac="H",
            pr="L",
            ui="R",
            s="C",
            c="H",
            i="L",
            a="N",
        )

        vector_str = original.to_vector_string()
        parsed = CVSSVector.from_vector_string(vector_str)

        assert parsed.av == original.av
        assert parsed.ac == original.ac
        assert parsed.pr == original.pr

    def test_realistic_cves(self):
        """Test with realistic CVE vectors."""
        calc = CVSSCalculator()

        # Heartbleed-like CVE
        heartbleed = CVSSVector(
            av="N", ac="L", pr="N", ui="N", s="U",
            c="H", i="N", a="N",
        )
        score = calc.calculate_base_score(heartbleed)
        assert score >= 7.0
        assert calc.get_severity_rating(score) == "High"

        # Log4j-like CVE
        log4j = CVSSVector(
            av="N", ac="L", pr="N", ui="N", s="C",
            c="H", i="H", a="H",
        )
        score = calc.calculate_base_score(log4j)
        assert score >= 10.0
        assert calc.get_severity_rating(score) == "Critical"
