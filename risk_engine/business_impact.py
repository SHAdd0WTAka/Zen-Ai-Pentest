"""
Business Impact Calculator

Assesses contextual business risk based on:
- Network exposure (internet-facing vs internal)
- Data sensitivity
- Compliance requirements
- Asset criticality
"""

from typing import Any, Dict, List


class BusinessImpactCalculator:
    """
    Calculate business impact score for vulnerabilities.
    """

    # Weight factors
    WEIGHTS = {
        "internet_facing": 0.40,
        "data_sensitivity": 0.30,
        "compliance": 0.20,
        "asset_criticality": 0.10,
    }

    def calculate(
        self, finding: Dict[str, Any], context: Dict[str, Any]
    ) -> float:
        """
        Calculate business impact score (0-1).

        Args:
            finding: Vulnerability finding
            context: Business context

        Returns:
            Business impact score 0.0-1.0
        """
        # Calculate individual factors
        internet_score = self._score_internet_facing(context)
        data_score = self._score_data_sensitivity(context)
        compliance_score = self._score_compliance(context, finding)
        criticality_score = self._score_asset_criticality(context)

        # Weighted sum
        total = (
            internet_score * self.WEIGHTS["internet_facing"]
            + data_score * self.WEIGHTS["data_sensitivity"]
            + compliance_score * self.WEIGHTS["compliance"]
            + criticality_score * self.WEIGHTS["asset_criticality"]
        )

        return round(min(total, 1.0), 3)

    def _score_internet_facing(self, context: Dict) -> float:
        """
        Score based on network exposure.

        Returns:
            1.0 = Internet-facing
            0.6 = DMZ
            0.3 = Internal network
            0.1 = Air-gapped
        """
        exposure = context.get("network_exposure", "internal")

        scores = {
            "internet": 1.0,
            "public": 1.0,
            "dmz": 0.6,
            "internal": 0.3,
            "private": 0.3,
            "airgapped": 0.1,
            "isolated": 0.1,
        }

        # Also check boolean flag
        if context.get("internet_facing", False):
            return 1.0

        return scores.get(exposure.lower(), 0.3)

    def _score_data_sensitivity(self, context: Dict) -> float:
        """
        Score based on data sensitivity.

        Returns:
            1.0 = PII/PHI/Financial
            0.7 = Confidential business data
            0.4 = Internal data
            0.1 = Public data
        """
        sensitivity = context.get("data_sensitivity", "internal")

        scores = {
            "critical": 1.0,
            "pii": 1.0,  # Personally Identifiable Information
            "phi": 1.0,  # Protected Health Information
            "financial": 1.0,  # Financial data
            "pci": 1.0,  # PCI DSS scope
            "confidential": 0.7,
            "internal": 0.4,
            "restricted": 0.4,
            "public": 0.1,
            "open": 0.1,
        }

        # Handle list of data types
        if isinstance(sensitivity, list):
            return max(scores.get(s.lower(), 0.4) for s in sensitivity)

        return scores.get(sensitivity.lower(), 0.4)

    def _score_compliance(self, context: Dict, finding: Dict) -> float:
        """
        Score based on compliance requirements.

        Returns:
            Score based on applicable regulations
        """
        compliance = context.get("compliance", [])

        if not compliance:
            return 0.3  # Default

        # Compliance framework weights
        framework_weights = {
            "sox": 0.9,  # Sarbanes-Oxley
            "pci-dss": 1.0,  # Payment Card Industry
            "hipaa": 1.0,  # Health Insurance Portability
            "gdpr": 0.9,  # EU Data Protection
            "ccpa": 0.8,  # California Privacy
            "iso27001": 0.7,  # ISO 27001
            "soc2": 0.7,  # SOC 2
            "nist": 0.6,  # NIST Framework
        }

        # Calculate average weight of applicable frameworks
        total_weight = 0
        for framework in compliance:
            fw_lower = framework.lower().replace("_", "-")
            total_weight += framework_weights.get(fw_lower, 0.5)

        avg_weight = total_weight / len(compliance)

        # Boost if finding directly violates compliance
        if self._is_compliance_violation(finding, compliance):
            avg_weight = min(avg_weight * 1.2, 1.0)

        return round(avg_weight, 3)

    def _score_asset_criticality(self, context: Dict) -> float:
        """
        Score based on asset criticality.

        Returns:
            1.0 = Business-critical
            0.6 = Important
            0.3 = Standard
            0.1 = Low-value
        """
        criticality = context.get("asset_criticality", "medium")

        scores = {
            "critical": 1.0,
            "high": 0.8,
            "important": 0.6,
            "medium": 0.4,
            "standard": 0.3,
            "low": 0.1,
            "minimal": 0.05,
        }

        return scores.get(criticality.lower(), 0.4)

    def _is_compliance_violation(
        self, finding: Dict, compliance: List[str]
    ) -> bool:
        """Check if finding violates specific compliance requirements."""
        # This would check against compliance-specific rules
        # Simplified implementation

        description = finding.get("description", "").lower()

        # PCI-DSS violations
        if "pci" in str(compliance).lower():
            if any(
                kw in description
                for kw in ["unencrypted", "ssl", "tls", "card"]
            ):
                return True

        # GDPR violations
        if "gdpr" in str(compliance).lower():
            if any(kw in description for kw in ["data exposure", "pii leak"]):
                return True

        return False

    def generate_context_questions(self) -> List[Dict]:
        """
        Generate questions to collect business context.

        Returns:
            List of question dicts for UI
        """
        return [
            {
                "key": "network_exposure",
                "question": "Where is the system deployed?",
                "options": [
                    "Internet/Public",
                    "DMZ",
                    "Internal Network",
                    "Air-gapped",
                ],
                "type": "single_choice",
            },
            {
                "key": "data_sensitivity",
                "question": "What type of data does the system handle?",
                "options": [
                    "PII (Personally Identifiable Information)",
                    "PHI (Protected Health Information)",
                    "Financial/Payment Data",
                    "Confidential Business Data",
                    "Internal Data",
                    "Public Data",
                ],
                "type": "multi_choice",
            },
            {
                "key": "compliance",
                "question": "Which compliance frameworks apply?",
                "options": [
                    "PCI-DSS",
                    "HIPAA",
                    "GDPR",
                    "SOX",
                    "ISO 27001",
                    "SOC 2",
                    "None",
                ],
                "type": "multi_choice",
            },
            {
                "key": "asset_criticality",
                "question": "How critical is this asset to business operations?",
                "options": [
                    "Critical - Business cannot function without it",
                    "High - Significant impact if unavailable",
                    "Medium - Moderate impact",
                    "Low - Minimal impact",
                ],
                "type": "single_choice",
            },
        ]

    def get_impact_description(self, score: float) -> str:
        """Get human-readable description of business impact."""
        if score >= 0.9:
            return "SEVERE - Critical business impact, immediate attention required"
        elif score >= 0.7:
            return "HIGH - Significant business risk, prioritize remediation"
        elif score >= 0.5:
            return "MODERATE - Notable business impact, include in planning"
        elif score >= 0.3:
            return "LOW - Limited business impact, standard remediation"
        else:
            return "MINIMAL - Negligible business impact"
