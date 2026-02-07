"""
Main Risk Scoring Implementation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .cvss import CVSSCalculator
from .epss import EPSSClient
from .business_impact import BusinessImpactCalculator


class SeverityLevel(Enum):
    """Risk severity levels with SLA requirements."""

    CRITICAL = (9.0, 10.0, "24h")
    HIGH = (7.0, 8.9, "72h")
    MEDIUM = (4.0, 6.9, "14d")
    LOW = (1.0, 3.9, "30d")
    INFO = (0.0, 0.9, "Best effort")

    def __init__(self, min_score: float, max_score: float, sla: str):
        self.min_score = min_score
        self.max_score = max_score
        self.sla = sla


@dataclass
class RiskScore:
    """Complete risk score with all components."""

    value: float  # 0-10
    severity: SeverityLevel

    # Component scores (0-1 each)
    cvss_score: float
    epss_score: float
    business_impact_score: float
    exploit_validation_score: float

    # Detailed breakdown
    components: Dict[str, Any] = field(default_factory=dict)

    # Context
    target_context: Dict[str, Any] = field(default_factory=dict)

    # Recommendations
    prioritized_actions: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "risk_score": round(self.value, 2),
            "severity": self.severity.name,
            "severity_range": f"{self.severity.min_score}-{self.severity.max_score}",
            "sla": self.severity.sla,
            "components": {
                "cvss": round(self.cvss_score, 3),
                "epss": round(self.epss_score, 3),
                "business_impact": round(self.business_impact_score, 3),
                "exploit_validation": round(self.exploit_validation_score, 3),
            },
            "detailed_breakdown": self.components,
            "target_context": self.target_context,
            "prioritized_actions": self.prioritized_actions,
            "timestamp": self.timestamp.isoformat(),
        }


class RiskScorer:
    """
    Multi-factor risk scoring engine.

    Combines:
    - CVSS (25%): Base vulnerability severity
    - EPSS (25%): Exploit probability
    - Business Impact (35%): Contextual risk
    - Exploit Validation (15%): Confirmed exploitation
    """

    WEIGHTS = {"cvss": 0.25, "epss": 0.25, "business": 0.35, "validation": 0.15}

    def __init__(self, enable_epss: bool = True, enable_business_context: bool = True):
        self.cvss_calc = CVSSCalculator()
        self.epss_client = EPSSClient() if enable_epss else None
        self.business_calc = BusinessImpactCalculator() if enable_business_context else None

    def calculate(self, finding: Dict[str, Any], target_context: Optional[Dict] = None) -> RiskScore:
        """
        Calculate comprehensive risk score for a finding.

        Args:
            finding: Vulnerability finding with CVE, severity, etc.
            target_context: Target information (internet-facing, data sensitivity, etc.)

        Returns:
            RiskScore with all components and recommendations
        """
        target_context = target_context or {}

        # 1. CVSS Score (normalize to 0-1)
        cvss_score = self._calculate_cvss(finding) / 10.0

        # 2. EPSS Score (0-1 probability)
        epss_score = self._get_epss(finding)

        # 3. Business Impact (0-1)
        business_score = self._calculate_business_impact(finding, target_context)

        # 4. Exploit Validation (0 or 1)
        validation_score = self._validate_exploit(finding)

        # Calculate weighted risk score (0-10)
        risk_value = (
            cvss_score * self.WEIGHTS["cvss"]
            + epss_score * self.WEIGHTS["epss"]
            + business_score * self.WEIGHTS["business"]
            + validation_score * self.WEIGHTS["validation"]
        ) * 10

        # Determine severity level
        severity = self._get_severity(risk_value)

        # Generate recommendations
        recommendations = self._generate_recommendations(finding, severity, cvss_score, epss_score)

        return RiskScore(
            value=risk_value,
            severity=severity,
            cvss_score=cvss_score,
            epss_score=epss_score,
            business_impact_score=business_score,
            exploit_validation_score=validation_score,
            components={
                "cvss_details": self.cvss_calc.get_details(finding),
                "epss_details": {"cve_id": finding.get("cve_id"), "score": epss_score},
                "business_factors": self._get_business_factors(target_context),
                "validation_status": self._get_validation_status(finding),
            },
            target_context=target_context,
            prioritized_actions=recommendations,
        )

    def _calculate_cvss(self, finding: Dict) -> float:
        """Calculate CVSS base score."""
        # Use provided CVSS or calculate from details
        if "cvss_score" in finding:
            return finding["cvss_score"]

        # Calculate from CVE ID
        if "cve_id" in finding:
            return self.cvss_calc.from_cve(finding["cve_id"])

        # Estimate from description
        return self.cvss_calc.estimate(finding.get("description", ""))

    def _get_epss(self, finding: Dict) -> float:
        """Get EPSS probability score."""
        if not self.epss_client:
            return 0.5  # Default if EPSS disabled

        cve_id = finding.get("cve_id")
        if not cve_id:
            return 0.0

        try:
            return self.epss_client.get_score(cve_id)
        except Exception:
            return 0.0

    def _calculate_business_impact(self, finding: Dict, context: Dict) -> float:
        """Calculate business impact score."""
        if not self.business_calc:
            return 0.5  # Default

        return self.business_calc.calculate(finding, context)

    def _validate_exploit(self, finding: Dict) -> float:
        """
        Validate if exploit is confirmed.
        Returns: 1.0 = confirmed, 0.5 = code available, 0.2 = theoretical, 0.0 = none
        """
        # Check if we have proof of exploitation
        if finding.get("exploit_validated", False):
            return 1.0

        # Check if exploit code is available
        if finding.get("exploit_available", False):
            return 0.5

        # Check if it's theoretically exploitable
        if finding.get("theoretically_exploitable", False):
            return 0.2

        return 0.0

    def _get_severity(self, risk_value: float) -> SeverityLevel:
        """Determine severity level from risk score."""
        for level in SeverityLevel:
            if level.min_score <= risk_value <= level.max_score:
                return level
        return SeverityLevel.INFO

    def _generate_recommendations(self, finding: Dict, severity: SeverityLevel, cvss: float, epss: float) -> List[str]:
        """Generate prioritized remediation actions."""
        recommendations = []

        if severity == SeverityLevel.CRITICAL:
            recommendations.append("IMMEDIATE: Isolate affected system")
            recommendations.append("Deploy emergency patch within 24h")
            recommendations.append("Activate incident response team")

        elif severity == SeverityLevel.HIGH:
            recommendations.append("Schedule patch deployment within 72h")
            recommendations.append("Implement temporary workaround/WAF rule")
            recommendations.append("Increase monitoring on affected assets")

        elif severity == SeverityLevel.MEDIUM:
            recommendations.append("Include in next maintenance window")
            recommendations.append("Review and update security policies")

        # EPSS-specific recommendations
        if epss > 0.5:
            recommendations.append(f"HIGH EXPLOIT PROBABILITY ({epss:.1%}) - Prioritize patching")

        # CVSS-specific
        if cvss > 0.8:
            recommendations.append("Critical technical severity - Network segmentation recommended")

        return recommendations

    def _get_business_factors(self, context: Dict) -> Dict:
        """Extract business impact factors."""
        return {
            "internet_facing": context.get("internet_facing", False),
            "data_sensitivity": context.get("data_sensitivity", "unknown"),
            "compliance_scope": context.get("compliance", []),
            "asset_criticality": context.get("asset_criticality", "medium"),
        }

    def _get_validation_status(self, finding: Dict) -> str:
        """Get human-readable validation status."""
        if finding.get("exploit_validated", False):
            return "Confirmed Exploitable"
        elif finding.get("exploit_available", False):
            return "Exploit Code Available"
        elif finding.get("theoretically_exploitable", False):
            return "Theoretically Exploitable"
        return "No Known Exploit"

    def prioritize_findings(self, findings: List[Dict], target_context: Optional[Dict] = None) -> List[Dict]:
        """
        Prioritize multiple findings by risk score.

        Returns:
            Findings sorted by risk (highest first) with risk scores attached
        """
        scored_findings = []

        for finding in findings:
            risk = self.calculate(finding, target_context)
            scored_findings.append({**finding, "risk_score": risk.to_dict()})

        # Sort by risk score descending
        scored_findings.sort(key=lambda x: x["risk_score"]["risk_score"], reverse=True)

        return scored_findings
