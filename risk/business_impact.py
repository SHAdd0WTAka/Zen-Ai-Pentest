"""
Business Impact Scorer
Assesses business impact of vulnerabilities
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ImpactLevel(Enum):
    """Business impact levels"""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


@dataclass
class BusinessContext:
    """Business context for impact assessment"""

    asset_type: str  # "web_server", "database", "workstation", etc.
    asset_value: ImpactLevel
    data_classification: str  # "public", "internal", "confidential", "restricted"
    exposure: str  # "internet", "intranet", "internal"
    compliance_requirements: List[str]  # ["PCI-DSS", "GDPR", "HIPAA"]
    business_critical: bool
    user_impact: int  # Number of users affected


class BusinessImpactScorer:
    """
    Calculates business impact score based on:
    - Asset value and criticality
    - Data sensitivity
    - Compliance requirements
    - Exposure level
    """

    # Data classification impact weights
    DATA_IMPACT = {
        "public": 1.0,
        "internal": 2.0,
        "confidential": 3.5,
        "restricted": 5.0,
    }

    # Exposure multipliers
    EXPOSURE_MULTIPLIER = {
        "internal": 0.8,
        "intranet": 1.2,
        "internet": 1.5,
    }

    # Compliance penalty for critical/high vulnerabilities
    COMPLIANCE_PENALTY = {
        "PCI-DSS": 1.3,
        "GDPR": 1.4,
        "HIPAA": 1.5,
        "SOX": 1.2,
        "ISO27001": 1.1,
    }

    def __init__(self):
        self.assessment_history: List[Dict] = []

    def calculate_impact(self, cvss_severity: str, business_context: BusinessContext) -> Dict:
        """
        Calculate business impact score
        """
        # Base impact from CVSS severity
        severity_scores = {
            "None": 0,
            "Low": 2,
            "Medium": 5,
            "High": 8,
            "Critical": 10,
        }
        base_impact = severity_scores.get(cvss_severity, 5)

        # Asset value multiplier (1-5)
        asset_multiplier = business_context.asset_value.value

        # Data classification impact
        data_multiplier = self.DATA_IMPACT.get(business_context.data_classification.lower(), 1.0)

        # Exposure multiplier
        exposure_mult = self.EXPOSURE_MULTIPLIER.get(business_context.exposure.lower(), 1.0)

        # Calculate raw business impact
        raw_impact = base_impact * asset_multiplier * data_multiplier * exposure_mult

        # Cap at 10
        impact_score = min(raw_impact, 10.0)

        # Compliance penalties
        compliance_penalties = []
        for req in business_context.compliance_requirements:
            if req in self.COMPLIANCE_PENALTY and cvss_severity in ["High", "Critical"]:
                penalty = self.COMPLIANCE_PENALTY[req]
                compliance_penalties.append(f"{req} violation risk (x{penalty})")
                impact_score *= penalty

        # Business critical bonus
        if business_context.business_critical:
            impact_score *= 1.2

        # User impact scaling
        if business_context.user_impact > 10000:
            impact_score *= 1.3
        elif business_context.user_impact > 1000:
            impact_score *= 1.2
        elif business_context.user_impact > 100:
            impact_score *= 1.1

        final_score = min(round(impact_score, 1), 10.0)

        result = {
            "business_impact_score": final_score,
            "impact_level": self._get_impact_level(final_score),
            "factors": {
                "cvss_severity": cvss_severity,
                "asset_value": business_context.asset_value.name,
                "data_classification": business_context.data_classification,
                "exposure": business_context.exposure,
                "business_critical": business_context.business_critical,
            },
            "compliance_concerns": compliance_penalties,
        }

        self.assessment_history.append(result)
        return result

    def _get_impact_level(self, score: float) -> str:
        """Get impact level from score"""
        if score >= 8.0:
            return "Critical Business Impact"
        elif score >= 6.0:
            return "High Business Impact"
        elif score >= 4.0:
            return "Medium Business Impact"
        elif score >= 2.0:
            return "Low Business Impact"
        else:
            return "Minimal Business Impact"

    def prioritize_vulnerabilities(self, vulns: List[Dict], business_context: BusinessContext) -> List[Dict]:
        """
        Sort vulnerabilities by combined risk + business impact
        """
        scored_vulns = []

        for vuln in vulns:
            cvss_severity = vuln.get("severity", "Medium")
            impact = self.calculate_impact(cvss_severity, business_context)

            vuln_with_impact = {
                **vuln,
                "business_impact": impact,
                "combined_score": (vuln.get("cvss_score", 5) * 0.5 + impact["business_impact_score"] * 0.5),
            }
            scored_vulns.append(vuln_with_impact)

        # Sort by combined score descending
        return sorted(scored_vulns, key=lambda x: x["combined_score"], reverse=True)
