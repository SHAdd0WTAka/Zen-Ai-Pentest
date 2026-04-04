"""
CVSS (Common Vulnerability Scoring System) Calculator

Supports CVSS v3.1
"""

from typing import Dict


class CVSSCalculator:
    """Calculate CVSS v3.1 base scores."""

    # CVSS v3.1 weights
    WEIGHTS = {
        "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
        "AC": {"L": 0.77, "H": 0.44},
        "PR": {"N": 0.85, "L": 0.62, "H": 0.27},
        "UI": {"N": 0.85, "R": 0.62},
        "S": {"U": 6.42, "C": 7.52},
        "C": {"H": 0.56, "L": 0.22, "N": 0},
        "I": {"H": 0.56, "L": 0.22, "N": 0},
        "A": {"H": 0.56, "L": 0.22, "N": 0},
    }

    def calculate(self, metrics: Dict[str, str]) -> float:
        """
        Calculate CVSS v3.1 base score from metrics.

        Args:
            metrics: Dict with keys AV, AC, PR, UI, S, C, I, A

        Returns:
            CVSS score 0.0-10.0
        """
        try:
            # Exploitability
            av = self.WEIGHTS["AV"].get(metrics.get("AV", "N"), 0.85)
            ac = self.WEIGHTS["AC"].get(metrics.get("AC", "L"), 0.77)
            pr = self.WEIGHTS["PR"].get(metrics.get("PR", "N"), 0.85)
            ui = self.WEIGHTS["UI"].get(metrics.get("UI", "N"), 0.85)

            # Impact
            c = self.WEIGHTS["C"].get(metrics.get("C", "N"), 0)
            i = self.WEIGHTS["I"].get(metrics.get("I", "N"), 0)
            a = self.WEIGHTS["A"].get(metrics.get("A", "N"), 0)
            _ = self.WEIGHTS["S"].get(metrics.get("S", "U"), 6.42)

            # Calculate Impact Sub-Score (ISS)
            iss = 1 - ((1 - c) * (1 - i) * (1 - a))

            # Calculate Impact
            if metrics.get("S", "U") == "C":
                impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
            else:
                impact = 6.42 * iss

            # Calculate Exploitability
            exploitability = 8.22 * av * ac * pr * ui

            # Calculate Base Score
            if impact <= 0:
                base_score = 0.0
            else:
                if metrics.get("S", "U") == "C":
                    base_score = min(1.08 * (impact + exploitability), 10)
                else:
                    base_score = min(impact + exploitability, 10)

            # Round to one decimal place
            return round(base_score, 1)

        except Exception:
            return 5.0  # Default on error

    def from_cve(self, cve_id: str) -> float:
        """
        Get CVSS score from CVE ID.
        In production, query NVD API or local database.
        """
        # Simulated lookup - in production query NVD
        # Common CVEs for testing
        known_scores = {
            "CVE-2021-44228": 10.0,  # Log4j
            "CVE-2017-0144": 8.1,  # EternalBlue
            "CVE-2014-0160": 5.0,  # Heartbleed
            "CVE-2019-11358": 6.1,  # jQuery
        }

        return known_scores.get(cve_id.upper(), 5.0)

    def estimate(self, description: str) -> float:
        """
        Estimate CVSS score from vulnerability description.
        Uses keyword matching for quick estimation.
        """
        description_lower = description.lower()
        score = 5.0  # Default

        # Critical indicators
        if any(kw in description_lower for kw in ["rce", "remote code execution", "arbitrary code"]):
            score = 9.8
        elif "sql injection" in description_lower:
            score = 8.6
        elif "xss" in description_lower or "cross-site scripting" in description_lower:
            score = 6.1
        elif "denial of service" in description_lower or "dos" in description_lower:
            score = 7.5
        elif "information disclosure" in description_lower:
            score = 5.3
        elif "authentication bypass" in description_lower:
            score = 8.1

        # Adjust for network accessibility
        if "network" in description_lower or "remote" in description_lower:
            score = min(score + 0.5, 10.0)

        # Adjust for no auth required
        if "unauthenticated" in description_lower or "without authentication" in description_lower:
            score = min(score + 0.3, 10.0)

        return round(score, 1)

    def get_details(self, finding: Dict) -> Dict:
        """Get detailed CVSS breakdown."""
        score = finding.get("cvss_score", 5.0)

        # Determine severity rating
        if score >= 9.0:
            severity = "Critical"
        elif score >= 7.0:
            severity = "High"
        elif score >= 4.0:
            severity = "Medium"
        elif score >= 0.1:
            severity = "Low"
        else:
            severity = "None"

        return {
            "base_score": score,
            "severity": severity,
            "vector": finding.get("cvss_vector", "Unknown"),
            "version": finding.get("cvss_version", "3.1"),
        }

    def get_vector_from_metrics(self, metrics: Dict[str, str]) -> str:
        """Generate CVSS vector string from metrics."""
        parts = ["CVSS:3.1"]

        metric_order = ["AV", "AC", "PR", "UI", "S", "C", "I", "A"]
        for metric in metric_order:
            if metric in metrics:
                parts.append(f"{metric}:{metrics[metric]}")

        return "/".join(parts)
