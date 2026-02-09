"""Risk Scoring Module: CVSS + EPSS + Business Impact

Combines multiple risk factors for comprehensive scoring:
- CVSS (Common Vulnerability Scoring System)
- EPSS (Exploit Prediction Scoring System)
- Business Impact (Criticality of affected asset)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class RiskFactors:
    """Risk factors for scoring"""

    cvss_score: float = 0.0  # 0.0 - 10.0
    epss_score: float = 0.0  # 0.0 - 1.0 (probability)
    business_impact: int = 1  # 1 - 5 (asset criticality)
    exposure: int = 1  # 1 - 5 (network exposure)
    data_sensitivity: int = 1  # 1 - 5 (data classification)


class RiskScoringModule:
    """Advanced risk scoring with CVSS + EPSS + Business Impact"""

    name = "risk_scoring"
    version = "1.0.0"
    enabled = True

    # Weight factors (must sum to 1.0)
    WEIGHTS = {"cvss": 0.35, "epss": 0.25, "business": 0.25, "exposure": 0.10, "data": 0.05}

    def __init__(self):
        self.name = "risk_scoring"
        self.enabled = True

    def calculate_cvss_score(self, cve_id: str) -> float:
        """Fetch CVSS score from CVE database"""
        # In production, this would query NVD API
        # For demo, return mock scores based on CVE ID
        cvss_map = {
            "CVE-2021-44228": 10.0,  # Log4j
            "CVE-2024-1234": 9.8,
            "CVE-2024-5678": 7.5,
            "CVE-2024-9999": 5.3,
        }
        return cvss_map.get(cve_id, 7.0)

    def calculate_epss_score(self, cve_id: str) -> float:
        """Fetch EPSS score (exploit probability)"""
        # EPSS = probability of exploitation in wild
        # In production: query EPSS API
        epss_map = {
            "CVE-2021-44228": 0.97,  # Log4j - very likely exploited
            "CVE-2024-1234": 0.75,
            "CVE-2024-5678": 0.35,
            "CVE-2024-9999": 0.10,
        }
        return epss_map.get(cve_id, 0.30)

    def calculate_business_impact(self, asset_type: str) -> int:
        """Calculate business impact score (1-5)"""
        impact_map = {
            "production": 5,
            "database": 5,
            "domain_controller": 5,
            "api_gateway": 4,
            "web_server": 3,
            "workstation": 2,
            "test": 1,
        }
        return impact_map.get(asset_type.lower(), 3)

    def calculate_composite_score(self, factors: RiskFactors) -> float:
        """Calculate composite risk score (0-100)"""
        # Normalize all factors to 0-100 scale
        cvss_normalized = factors.cvss_score * 10  # 0-10 -> 0-100
        epss_normalized = factors.epss_score * 100  # 0-1 -> 0-100
        business_normalized = factors.business_impact * 20  # 1-5 -> 20-100
        exposure_normalized = factors.exposure * 20  # 1-5 -> 20-100
        data_normalized = factors.data_sensitivity * 20  # 1-5 -> 20-100

        # Weighted sum
        score = (
            cvss_normalized * self.WEIGHTS["cvss"]
            + epss_normalized * self.WEIGHTS["epss"]
            + business_normalized * self.WEIGHTS["business"]
            + exposure_normalized * self.WEIGHTS["exposure"]
            + data_normalized * self.WEIGHTS["data"]
        )

        return round(score, 2)

    def score_to_severity(self, score: float) -> SeverityLevel:
        """Convert numeric score to severity level"""
        if score >= 80:
            return SeverityLevel.CRITICAL
        elif score >= 60:
            return SeverityLevel.HIGH
        elif score >= 40:
            return SeverityLevel.MEDIUM
        elif score >= 20:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.INFO

    def score_vulnerability(
        self, cve_id: str, asset_type: str = "web_server", exposure: int = 3, data_sensitivity: int = 3
    ) -> Dict:
        """Score a single vulnerability"""
        factors = RiskFactors(
            cvss_score=self.calculate_cvss_score(cve_id),
            epss_score=self.calculate_epss_score(cve_id),
            business_impact=self.calculate_business_impact(asset_type),
            exposure=exposure,
            data_sensitivity=data_sensitivity,
        )

        composite_score = self.calculate_composite_score(factors)
        severity = self.score_to_severity(composite_score)

        return {
            "cve_id": cve_id,
            "asset_type": asset_type,
            "cvss_score": factors.cvss_score,
            "epss_score": factors.epss_score,
            "business_impact": factors.business_impact,
            "composite_score": composite_score,
            "severity": severity.value,
            "priority": self._calculate_priority(composite_score, factors.epss_score),
            "remediation_timeline": self._get_remediation_timeline(severity),
        }

    def _calculate_priority(self, score: float, epss: float) -> str:
        """Calculate remediation priority"""
        if score >= 80 and epss > 0.5:
            return "P1 - Immediate (24h)"
        elif score >= 60 or (score >= 40 and epss > 0.5):
            return "P2 - High (72h)"
        elif score >= 40:
            return "P3 - Medium (7 days)"
        elif score >= 20:
            return "P4 - Low (30 days)"
        else:
            return "P5 - Info (next cycle)"

    def _get_remediation_timeline(self, severity: SeverityLevel) -> str:
        """Get recommended remediation timeline"""
        timelines = {
            SeverityLevel.CRITICAL: "Immediate - 24 hours",
            SeverityLevel.HIGH: "Urgent - 72 hours",
            SeverityLevel.MEDIUM: "Standard - 7 days",
            SeverityLevel.LOW: "Planned - 30 days",
            SeverityLevel.INFO: "Track - Next cycle",
        }
        return timelines[severity]

    def score_findings(self, findings: List[Dict], asset_inventory: Optional[Dict] = None) -> List[Dict]:
        """Score multiple findings"""
        scored_findings = []
        for finding in findings:
            cve = finding.get("cve_id", "CVE-2024-0000")
            asset = finding.get("asset_type", "web_server")
            exposure = finding.get("exposure", 3)
            data_sens = finding.get("data_sensitivity", 3)

            scored = self.score_vulnerability(cve, asset, exposure, data_sens)
            scored["original_finding"] = finding
            scored_findings.append(scored)

        # Sort by composite score (highest first)
        scored_findings.sort(key=lambda x: x["composite_score"], reverse=True)
        return scored_findings

    def get_info(self) -> Dict:
        """Get module info"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "Advanced risk scoring: CVSS + EPSS + Business Impact",
            "factors": list(self.WEIGHTS.keys()),
            "scoring_range": "0-100",
        }
