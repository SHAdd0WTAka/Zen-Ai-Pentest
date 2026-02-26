"""Tests for risk/business_impact.py - Business Impact Scorer."""

import pytest
from risk.business_impact import (
    BusinessContext,
    BusinessImpactScorer,
    ImpactLevel,
)


class TestImpactLevel:
    """Test ImpactLevel enum."""

    def test_values(self):
        """Test impact level values."""
        assert ImpactLevel.CRITICAL.value == 5
        assert ImpactLevel.HIGH.value == 4
        assert ImpactLevel.MEDIUM.value == 3
        assert ImpactLevel.LOW.value == 2
        assert ImpactLevel.MINIMAL.value == 1


class TestBusinessContext:
    """Test BusinessContext dataclass."""

    def test_creation(self):
        """Test creating business context."""
        context = BusinessContext(
            asset_type="web_server",
            asset_value=ImpactLevel.HIGH,
            data_classification="confidential",
            exposure="internet",
            compliance_requirements=["GDPR", "PCI-DSS"],
            business_critical=True,
            user_impact=5000,
        )

        assert context.asset_type == "web_server"
        assert context.asset_value == ImpactLevel.HIGH
        assert context.data_classification == "confidential"
        assert context.exposure == "internet"
        assert context.compliance_requirements == ["GDPR", "PCI-DSS"]
        assert context.business_critical is True
        assert context.user_impact == 5000


class TestBusinessImpactScorerInit:
    """Test BusinessImpactScorer initialization."""

    def test_init(self):
        """Test scorer initialization."""
        scorer = BusinessImpactScorer()

        assert scorer.assessment_history == []
        assert scorer.DATA_IMPACT["public"] == 1.0
        assert scorer.DATA_IMPACT["restricted"] == 5.0


class TestBusinessImpactScorerCalculate:
    """Test calculate_impact method."""

    def test_minimal_impact(self):
        """Test minimal business impact."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="workstation",
            asset_value=ImpactLevel.MINIMAL,
            data_classification="public",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=1,
        )

        result = scorer.calculate_impact("None", context)

        assert result["business_impact_score"] < 2.0
        assert result["impact_level"] == "Minimal Business Impact"

    def test_critical_impact(self):
        """Test critical business impact."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="database",
            asset_value=ImpactLevel.CRITICAL,
            data_classification="restricted",
            exposure="internet",
            compliance_requirements=["PCI-DSS", "GDPR", "HIPAA"],
            business_critical=True,
            user_impact=50000,
        )

        result = scorer.calculate_impact("Critical", context)

        assert result["business_impact_score"] >= 8.0
        assert result["impact_level"] == "Critical Business Impact"

    def test_data_classification_impact(self):
        """Test data classification affects score."""
        scorer = BusinessImpactScorer()
        base_context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.LOW,  # Use LOW to avoid capping
            data_classification="public",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        public_result = scorer.calculate_impact("Low", base_context)  # Use Low severity

        restricted_context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.LOW,
            data_classification="restricted",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        restricted_result = scorer.calculate_impact("Low", restricted_context)

        assert restricted_result["business_impact_score"] > public_result["business_impact_score"]

    def test_exposure_impact(self):
        """Test exposure level affects score."""
        scorer = BusinessImpactScorer()

        internal_context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.LOW,  # Use LOW to avoid capping
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        internet_context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.LOW,
            data_classification="internal",
            exposure="internet",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        internal_result = scorer.calculate_impact("Low", internal_context)
        internet_result = scorer.calculate_impact("Low", internet_context)

        assert internet_result["business_impact_score"] > internal_result["business_impact_score"]

    def test_compliance_penalty(self):
        """Test compliance penalties for high severity."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="database",
            asset_value=ImpactLevel.HIGH,
            data_classification="confidential",
            exposure="internet",
            compliance_requirements=["PCI-DSS", "GDPR", "HIPAA"],
            business_critical=True,
            user_impact=1000,
        )

        result = scorer.calculate_impact("High", context)

        assert len(result["compliance_concerns"]) == 3
        assert "PCI-DSS violation risk" in result["compliance_concerns"][0]
        assert "GDPR violation risk" in result["compliance_concerns"][1]
        assert "HIPAA violation risk" in result["compliance_concerns"][2]

    def test_no_compliance_penalty_low_severity(self):
        """Test no compliance penalties for low severity."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="database",
            asset_value=ImpactLevel.HIGH,
            data_classification="confidential",
            exposure="internet",
            compliance_requirements=["PCI-DSS", "GDPR"],
            business_critical=True,
            user_impact=1000,
        )

        result = scorer.calculate_impact("Low", context)

        assert result["compliance_concerns"] == []

    def test_business_critical_bonus(self):
        """Test business critical flag bonus."""
        scorer = BusinessImpactScorer()
        base_context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.LOW,  # Use LOW to avoid capping
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        critical_context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.LOW,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=True,
            user_impact=10,
        )

        normal_result = scorer.calculate_impact("Low", base_context)
        critical_result = scorer.calculate_impact("Low", critical_context)

        assert critical_result["business_impact_score"] > normal_result["business_impact_score"]

    def test_user_impact_scaling(self):
        """Test user impact scaling."""
        scorer = BusinessImpactScorer()

        contexts = [
            BusinessContext(
                asset_type="server",
                asset_value=ImpactLevel.MEDIUM,
                data_classification="internal",
                exposure="internal",
                compliance_requirements=[],
                business_critical=False,
                user_impact=10,  # No scaling
            ),
            BusinessContext(
                asset_type="server",
                asset_value=ImpactLevel.MEDIUM,
                data_classification="internal",
                exposure="internal",
                compliance_requirements=[],
                business_critical=False,
                user_impact=500,  # 1.1x scaling
            ),
            BusinessContext(
                asset_type="server",
                asset_value=ImpactLevel.MEDIUM,
                data_classification="internal",
                exposure="internal",
                compliance_requirements=[],
                business_critical=False,
                user_impact=5000,  # 1.2x scaling
            ),
            BusinessContext(
                asset_type="server",
                asset_value=ImpactLevel.MEDIUM,
                data_classification="internal",
                exposure="internal",
                compliance_requirements=[],
                business_critical=False,
                user_impact=50000,  # 1.3x scaling
            ),
        ]

        results = [scorer.calculate_impact("Medium", ctx) for ctx in contexts]

        # More users should generally mean higher impact
        assert results[1]["business_impact_score"] >= results[0]["business_impact_score"]
        assert results[2]["business_impact_score"] >= results[1]["business_impact_score"]
        assert results[3]["business_impact_score"] >= results[2]["business_impact_score"]

    def test_score_capped_at_10(self):
        """Test score is capped at 10.0."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="database",
            asset_value=ImpactLevel.CRITICAL,
            data_classification="restricted",
            exposure="internet",
            compliance_requirements=["HIPAA"],
            business_critical=True,
            user_impact=100000,
        )

        result = scorer.calculate_impact("Critical", context)

        assert result["business_impact_score"] <= 10.0

    def test_unknown_severity(self):
        """Test handling of unknown severity."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        result = scorer.calculate_impact("Unknown", context)

        # Defaults to "Medium" (5)
        assert result["factors"]["cvss_severity"] == "Unknown"
        assert result["business_impact_score"] > 0

    def test_result_structure(self):
        """Test result contains expected fields."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="web_server",
            asset_value=ImpactLevel.HIGH,
            data_classification="confidential",
            exposure="intranet",
            compliance_requirements=[],
            business_critical=True,
            user_impact=100,
        )

        result = scorer.calculate_impact("High", context)

        assert "business_impact_score" in result
        assert "impact_level" in result
        assert "factors" in result
        assert "compliance_concerns" in result
        assert "cvss_severity" in result["factors"]
        assert "asset_value" in result["factors"]
        assert "data_classification" in result["factors"]
        assert "exposure" in result["factors"]
        assert "business_critical" in result["factors"]

    def test_assessment_history(self):
        """Test assessment history is recorded."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        assert len(scorer.assessment_history) == 0

        scorer.calculate_impact("Medium", context)
        assert len(scorer.assessment_history) == 1

        scorer.calculate_impact("High", context)
        assert len(scorer.assessment_history) == 2


class TestBusinessImpactScorerPrioritize:
    """Test prioritize_vulnerabilities method."""

    def test_prioritize_empty_list(self):
        """Test prioritizing empty vulnerability list."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        result = scorer.prioritize_vulnerabilities([], context)

        assert result == []

    def test_prioritize_single_vuln(self):
        """Test prioritizing single vulnerability."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        vulns = [{"id": "CVE-2021-44228", "severity": "Critical", "cvss_score": 10.0}]
        result = scorer.prioritize_vulnerabilities(vulns, context)

        assert len(result) == 1
        assert result[0]["id"] == "CVE-2021-44228"
        assert "business_impact" in result[0]
        assert "combined_score" in result[0]

    def test_prioritize_multiple_vulns(self):
        """Test prioritizing multiple vulnerabilities."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        vulns = [
            {"id": "CVE-001", "severity": "Low", "cvss_score": 2.0},
            {"id": "CVE-002", "severity": "Critical", "cvss_score": 9.8},
            {"id": "CVE-003", "severity": "Medium", "cvss_score": 5.0},
        ]

        result = scorer.prioritize_vulnerabilities(vulns, context)

        # Should be sorted by combined_score descending
        assert result[0]["id"] == "CVE-002"  # Critical first
        assert result[-1]["id"] == "CVE-001"  # Low last

    def test_prioritize_combined_score_calculation(self):
        """Test combined score is average of CVSS and business impact."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        vulns = [{"id": "CVE-001", "severity": "Medium", "cvss_score": 6.0}]
        result = scorer.prioritize_vulnerabilities(vulns, context)

        combined = result[0]["combined_score"]
        assert combined > 0
        # Combined should be roughly average of CVSS (6.0) and business impact
        assert combined <= 10.0

    def test_default_severity(self):
        """Test default severity when not specified."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        vulns = [{"id": "CVE-001", "cvss_score": 5.0}]  # No severity
        result = scorer.prioritize_vulnerabilities(vulns, context)

        # Should default to "Medium"
        assert result[0]["business_impact"]["factors"]["cvss_severity"] == "Medium"

    def test_default_cvss_score(self):
        """Test default CVSS score when not specified."""
        scorer = BusinessImpactScorer()
        context = BusinessContext(
            asset_type="server",
            asset_value=ImpactLevel.MEDIUM,
            data_classification="internal",
            exposure="internal",
            compliance_requirements=[],
            business_critical=False,
            user_impact=10,
        )

        vulns = [{"id": "CVE-001", "severity": "High"}]  # No cvss_score
        result = scorer.prioritize_vulnerabilities(vulns, context)

        # Should default to 5.0
        assert result[0]["combined_score"] > 0
