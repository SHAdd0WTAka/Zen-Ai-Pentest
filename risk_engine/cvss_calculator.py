"""
Erweiterter CVSS Calculator

Erweitert die Basis-CVSS-Funktionalität um:
- CVSS v3.1 und v4.0 Unterstützung
- NVD API Integration
- Vector String Parsing
- Temporal und Environmental Scoring
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests

from risk_engine.cvss import CVSSCalculator as BaseCVSSCalculator


@dataclass
class CVSSMetrics:
    """CVSS Metrics Container."""

    version: str = "3.1"
    attack_vector: str = "N"  # N/A/L/P
    attack_complexity: str = "L"  # L/H
    privileges_required: str = "N"  # N/L/H
    user_interaction: str = "N"  # N/R
    scope: str = "U"  # U/C
    confidentiality: str = "N"  # N/L/H
    integrity: str = "N"  # N/L/H
    availability: str = "N"  # N/L/H

    # Temporal (optional)
    exploit_code_maturity: str = "X"  # X/U/P/F/H
    remediation_level: str = "X"  # X/O/T/W/U
    report_confidence: str = "X"  # X/U/R/C

    # Environmental (optional)
    confidentiality_req: str = "X"  # X/L/M/H
    integrity_req: str = "X"  # X/L/M/H
    availability_req: str = "X"  # X/L/M/H


class CVSS4Calculator:
    """CVSS v4.0 Calculator (Preview)."""

    # CVSS 4.0 MacroVectors and their scores
    # Simplified implementation - full CVSS 4.0 is complex

    def calculate(self, metrics: Dict[str, str]) -> float:
        """
        Calculate CVSS 4.0 score.

        Note: CVSS 4.0 uses a different calculation method.
        This is a simplified approximation.
        """
        # For now, fall back to CVSS 3.1 equivalent
        # Full CVSS 4.0 implementation would require extensive lookup tables
        calculator = BaseCVSSCalculator()
        return calculator.calculate(metrics)


class NVDClient:
    """Client for NVD (National Vulnerability Database) API."""

    API_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self._cache: Dict[str, Dict] = {}

    def get_cve_data(self, cve_id: str) -> Optional[Dict]:
        """
        Fetch CVE data from NVD API.

        Args:
            cve_id: CVE ID (e.g., "CVE-2021-44228")

        Returns:
            CVE data dictionary or None if not found
        """
        cve_id = cve_id.upper()

        # Check cache
        if cve_id in self._cache:
            return self._cache[cve_id]

        try:
            headers = {}
            if self.api_key:
                headers["apiKey"] = self.api_key

            response = requests.get(
                self.API_BASE_URL,
                params={"cveId": cve_id},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("vulnerabilities"):
                cve_data = data["vulnerabilities"][0].get("cve", {})
                self._cache[cve_id] = cve_data
                return cve_data

            return None

        except requests.RequestException as e:
            self.logger.warning(f"NVD API request failed for {cve_id}: {e}")
            return None

    def get_cvss_score(self, cve_id: str) -> Tuple[float, str]:
        """
        Get CVSS score from NVD for a CVE.

        Returns:
            Tuple of (score, vector_string)
        """
        cve_data = self.get_cve_data(cve_id)

        if not cve_data:
            return 0.0, ""

        metrics = cve_data.get("metrics", {})

        # Try CVSS 3.1 first, then 3.0, then 2.0
        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if version in metrics and metrics[version]:
                metric_data = metrics[version][0]
                cvss_data = metric_data.get("cvssData", {})
                score = cvss_data.get("baseScore", 0.0)
                vector = cvss_data.get("vectorString", "")
                return float(score), vector

        return 0.0, ""


class CVSSVectorParser:
    """Parser for CVSS Vector Strings."""

    @staticmethod
    def parse(vector_string: str) -> Dict[str, str]:
        """
        Parse CVSS vector string into metrics dictionary.

        Args:
            vector_string: CVSS vector (e.g., "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")

        Returns:
            Dictionary of metrics
        """
        metrics = {}

        if not vector_string:
            return metrics

        # Remove CVSS version prefix if present
        if vector_string.startswith("CVSS:"):
            parts = vector_string.split("/")
            if len(parts) > 1:
                vector_parts = parts[1:]
            else:
                return metrics
        else:
            vector_parts = vector_string.split("/")

        # Parse each metric
        for part in vector_parts:
            if ":" in part:
                key, value = part.split(":", 1)
                metrics[key] = value

        return metrics

    @staticmethod
    def build(metrics: Dict[str, str], version: str = "3.1") -> str:
        """
        Build CVSS vector string from metrics.

        Args:
            metrics: Dictionary of metrics
            version: CVSS version

        Returns:
            CVSS vector string
        """
        parts = [f"CVSS:{version}"]

        # Standard order for CVSS 3.1
        order = ["AV", "AC", "PR", "UI", "S", "C", "I", "A"]

        for metric in order:
            if metric in metrics:
                parts.append(f"{metric}:{metrics[metric]}")

        return "/".join(parts)


class ExtendedCVSSCalculator(BaseCVSSCalculator):
    """
    Erweiterter CVSS Calculator mit zusätzlichen Features.
    """

    def __init__(self, nvd_api_key: Optional[str] = None):
        super().__init__()
        self.nvd = NVDClient(nvd_api_key)
        self.parser = CVSSVectorParser()
        self.cvss4 = CVSS4Calculator()
        self.logger = logging.getLogger(__name__)

    def calculate_extended(
        self,
        metrics: Dict[str, str],
        temporal: Optional[Dict[str, str]] = None,
        environmental: Optional[Dict[str, str]] = None,
    ) -> Dict[str, float]:
        """
        Calculate CVSS scores with temporal and environmental modifications.

        Args:
            metrics: Base metrics
            temporal: Temporal metrics (optional)
            environmental: Environmental metrics (optional)

        Returns:
            Dictionary with base, temporal, and environmental scores
        """
        # Base score
        base_score = self.calculate(metrics)

        # Temporal score
        temporal_score = self._apply_temporal(base_score, temporal or {})

        # Environmental score
        env_score = self._apply_environmental(metrics, environmental or {})

        return {
            "base_score": base_score,
            "temporal_score": temporal_score,
            "environmental_score": env_score,
            "overall_score": max(base_score, temporal_score, env_score),
        }

    def from_vector(self, vector_string: str) -> float:
        """
        Calculate CVSS score from vector string.

        Args:
            vector_string: CVSS vector string

        Returns:
            CVSS score
        """
        metrics = self.parser.parse(vector_string)
        return self.calculate(metrics)

    def from_nvd(self, cve_id: str) -> Dict[str, Any]:
        """
        Get CVSS data from NVD for a CVE.

        Args:
            cve_id: CVE ID

        Returns:
            Dictionary with score, vector, and metadata
        """
        score, vector = self.nvd.get_cvss_score(cve_id)

        if score == 0.0:
            # Fall back to local lookup
            score = self.from_cve(cve_id)

        return {
            "score": score,
            "vector": vector,
            "source": "NVD" if vector else "LOCAL",
            "severity": self._get_severity(score),
        }

    def estimate_detailed(self, description: str) -> Dict[str, Any]:
        """
        Detailed CVSS estimation from description.

        Returns estimated metrics and confidence level.
        """
        description_lower = description.lower()

        # Initialize with defaults
        metrics = {"AV": "N", "AC": "L", "PR": "N", "UI": "N", "S": "U", "C": "N", "I": "N", "A": "N"}

        confidence_factors = []

        # Attack Vector
        if any(kw in description_lower for kw in ["network", "remote", "internet", "wan"]):
            metrics["AV"] = "N"
            confidence_factors.append("network")
        elif any(kw in description_lower for kw in ["adjacent", "bluetooth", "local network"]):
            metrics["AV"] = "A"
            confidence_factors.append("adjacent")
        elif any(kw in description_lower for kw in ["local", "localhost", "filesystem"]):
            metrics["AV"] = "L"
            confidence_factors.append("local")
        elif any(kw in description_lower for kw in ["physical", "hardware", "usb"]):
            metrics["AV"] = "P"
            confidence_factors.append("physical")

        # Attack Complexity
        if any(kw in description_lower for kw in ["complex", "difficult", "race condition"]):
            metrics["AC"] = "H"
            confidence_factors.append("complex")
        else:
            metrics["AC"] = "L"

        # Privileges Required
        if any(kw in description_lower for kw in ["admin", "root", "system"]):
            metrics["PR"] = "H"
            confidence_factors.append("admin_priv")
        elif any(kw in description_lower for kw in ["user", "authenticated", "login required"]):
            metrics["PR"] = "L"
            confidence_factors.append("user_priv")
        else:
            metrics["PR"] = "N"
            confidence_factors.append("no_priv")

        # User Interaction
        if any(kw in description_lower for kw in ["user interaction", "click", "open file", "visit"]):
            metrics["UI"] = "R"
            confidence_factors.append("ui_required")
        else:
            metrics["UI"] = "N"

        # Scope
        if any(kw in description_lower for kw in ["escalate", "other component", "other process"]):
            metrics["S"] = "C"
            confidence_factors.append("scope_changed")
        else:
            metrics["S"] = "U"

        # Impact (C, I, A)
        if any(kw in description_lower for kw in ["rce", "remote code", "arbitrary code", "command injection"]):
            metrics["C"] = "H"
            metrics["I"] = "H"
            metrics["A"] = "H"
            confidence_factors.append("rce")
        elif "sql injection" in description_lower:
            metrics["C"] = "H"
            metrics["I"] = "H"
            metrics["A"] = "N"
            confidence_factors.append("sqli")
        elif any(kw in description_lower for kw in ["xss", "cross-site"]):
            metrics["C"] = "L"
            metrics["I"] = "L"
            metrics["A"] = "N"
            confidence_factors.append("xss")
        elif any(kw in description_lower for kw in ["information disclosure", "sensitive data", "pii"]):
            metrics["C"] = "H"
            confidence_factors.append("info_disclosure")
        elif any(kw in description_lower for kw in ["dos", "denial of service", "crash"]):
            metrics["A"] = "H"
            confidence_factors.append("dos")

        score = self.calculate(metrics)
        vector = self.parser.build(metrics)

        # Confidence based on number of identified factors
        confidence = "high" if len(confidence_factors) >= 5 else "medium" if len(confidence_factors) >= 3 else "low"

        return {
            "score": score,
            "vector": vector,
            "metrics": metrics,
            "confidence": confidence,
            "confidence_factors": confidence_factors,
        }

    def _apply_temporal(self, base_score: float, temporal: Dict[str, str]) -> float:
        """Apply temporal modifiers to base score."""
        # Temporal metrics weights (CVSS 3.1)
        e_weights = {"X": 1.0, "U": 0.91, "P": 0.94, "F": 0.97, "H": 1.0}
        rl_weights = {"X": 1.0, "O": 0.95, "T": 0.96, "W": 0.97, "U": 1.0}
        rc_weights = {"X": 1.0, "U": 0.92, "R": 0.96, "C": 1.0}

        e = e_weights.get(temporal.get("E", "X"), 1.0)
        rl = rl_weights.get(temporal.get("RL", "X"), 1.0)
        rc = rc_weights.get(temporal.get("RC", "X"), 1.0)

        return round(base_score * e * rl * rc, 1)

    def _apply_environmental(self, metrics: Dict[str, str], environmental: Dict[str, str]) -> float:
        """Apply environmental modifiers."""
        # Simplified environmental calculation
        # Modify metrics based on requirements
        modified_metrics = metrics.copy()

        # Adjust for confidentiality requirement
        cr = environmental.get("CR", "X")
        if cr == "H" and metrics.get("C") in ["L", "N"]:
            modified_metrics["C"] = "H"

        # Recalculate with modified metrics
        return self.calculate(modified_metrics)

    def _get_severity(self, score: float) -> str:
        """Get severity rating from score."""
        if score >= 9.0:
            return "Critical"
        elif score >= 7.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        elif score >= 0.1:
            return "Low"
        return "None"

    def compare_versions(self, vector_v31: str, vector_v4: str) -> Dict[str, Any]:
        """
        Compare CVSS 3.1 and CVSS 4.0 scores for the same vulnerability.

        Args:
            vector_v31: CVSS 3.1 vector
            vector_v4: CVSS 4.0 vector

        Returns:
            Comparison results
        """
        score_v31 = self.from_vector(vector_v31)
        score_v4 = self.cvss4.calculate(self.parser.parse(vector_v4))

        return {
            "cvss_3_1": {"vector": vector_v31, "score": score_v31},
            "cvss_4_0": {"vector": vector_v4, "score": score_v4},
            "difference": round(score_v4 - score_v31, 2),
            "trend": "increased" if score_v4 > score_v31 else "decreased" if score_v4 < score_v31 else "same",
        }


# Convenience functions
def calculate_cvss(
    metrics: Optional[Dict[str, str]] = None,
    vector: Optional[str] = None,
    cve_id: Optional[str] = None,
) -> float:
    """
    Calculate CVSS score from various inputs.

    Args:
        metrics: CVSS metrics dictionary
        vector: CVSS vector string
        cve_id: CVE ID for lookup

    Returns:
        CVSS score
    """
    calc = ExtendedCVSSCalculator()

    if metrics:
        return calc.calculate(metrics)
    elif vector:
        return calc.from_vector(vector)
    elif cve_id:
        result = calc.from_nvd(cve_id)
        return result["score"]

    return 0.0
