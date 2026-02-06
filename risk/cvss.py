"""
CVSS 3.1 Calculator
Implements full CVSS v3.1 scoring
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class CVSSMetric(Enum):
    """CVSS 3.1 Base Metrics"""

    # Attack Vector
    AV_NETWORK = "N"
    AV_ADJACENT = "A"
    AV_LOCAL = "L"
    AV_PHYSICAL = "P"

    # Attack Complexity
    AC_LOW = "L"
    AC_HIGH = "H"

    # Privileges Required
    PR_NONE = "N"
    PR_LOW = "L"
    PR_HIGH = "H"

    # User Interaction
    UI_NONE = "N"
    UI_REQUIRED = "R"

    # Scope
    S_UNCHANGED = "U"
    S_CHANGED = "C"

    # Impact Metrics
    C_NONE = "N"
    C_LOW = "L"
    C_HIGH = "H"

    I_NONE = "N"
    I_LOW = "L"
    I_HIGH = "H"

    A_NONE = "N"
    A_LOW = "L"
    A_HIGH = "H"


@dataclass
class CVSSVector:
    """CVSS 3.1 Vector String"""

    av: str = "N"  # Attack Vector
    ac: str = "L"  # Attack Complexity
    pr: str = "N"  # Privileges Required
    ui: str = "N"  # User Interaction
    s: str = "U"  # Scope
    c: str = "N"  # Confidentiality
    i: str = "N"  # Integrity
    a: str = "N"  # Availability

    # Temporal (optional)
    e: Optional[str] = None  # Exploit Code Maturity
    rl: Optional[str] = None  # Remediation Level
    rc: Optional[str] = None  # Report Confidence

    # Environmental (optional)
    cr: Optional[str] = None  # Confidentiality Req.
    ir: Optional[str] = None  # Integrity Req.
    ar: Optional[str] = None  # Availability Req.
    mav: Optional[str] = None  # Modified AV
    mac: Optional[str] = None  # Modified AC
    mpr: Optional[str] = None  # Modified PR
    mui: Optional[str] = None  # Modified UI
    ms: Optional[str] = None  # Modified Scope
    mc: Optional[str] = None  # Modified C
    mi: Optional[str] = None  # Modified I
    ma: Optional[str] = None  # Modified A

    def to_vector_string(self) -> str:
        """Generate CVSS:3.1 vector string"""
        base = f"CVSS:3.1/AV:{self.av}/AC:{self.ac}/PR:{self.pr}/UI:{self.ui}/S:{self.s}/C:{self.c}/I:{self.i}/A:{self.a}"

        # Add temporal if present
        if any([self.e, self.rl, self.rc]):
            temporal = ""
            if self.e:
                temporal += f"/E:{self.e}"
            if self.rl:
                temporal += f"/RL:{self.rl}"
            if self.rc:
                temporal += f"/RC:{self.rc}"
            base += temporal

        return base

    @classmethod
    def from_vector_string(cls, vector: str) -> "CVSSVector":
        """Parse CVSS vector string"""
        metrics = {}
        for part in vector.split("/"):
            if ":" in part:
                key, value = part.split(":")
                metrics[key.lower()] = value

        return cls(
            av=metrics.get("av", "N"),
            ac=metrics.get("ac", "L"),
            pr=metrics.get("pr", "N"),
            ui=metrics.get("ui", "N"),
            s=metrics.get("s", "U"),
            c=metrics.get("c", "N"),
            i=metrics.get("i", "N"),
            a=metrics.get("a", "N"),
        )


class CVSSCalculator:
    """
    CVSS 3.1 Score Calculator
    Calculates Base, Temporal, and Environmental scores
    """

    # CVSS 3.1 Weights
    WEIGHTS = {
        "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
        "AC": {"L": 0.77, "H": 0.44},
        "PR": {"N": 0.85, "L": 0.62, "H": 0.27},  # Modified by Scope
        "PR_CHANGED": {"N": 0.85, "L": 0.68, "H": 0.5},
        "UI": {"N": 0.85, "R": 0.62},
        "CIA": {"N": 0.0, "L": 0.22, "H": 0.56},
    }

    TEMPORAL_WEIGHTS = {
        "E": {"X": 1.0, "U": 0.91, "P": 0.94, "F": 0.97, "H": 1.0},
        "RL": {"X": 1.0, "O": 0.95, "T": 0.96, "W": 0.97, "U": 1.0},
        "RC": {"X": 1.0, "U": 0.92, "R": 0.96, "C": 1.0},
    }

    def __init__(self):
        self.calculation_log: list = []

    def calculate_base_score(self, vector: CVSSVector) -> float:
        """
        Calculate CVSS Base Score
        """
        # Impact Sub-Score (ISS)
        iss_conf = self.WEIGHTS["CIA"][vector.c]
        iss_integ = self.WEIGHTS["CIA"][vector.i]
        iss_avail = self.WEIGHTS["CIA"][vector.a]

        iss = 1 - ((1 - iss_conf) * (1 - iss_integ) * (1 - iss_avail))

        # Impact
        if vector.s == "U":
            impact = 6.42 * iss
        else:  # Changed
            impact = 7.52 * (iss - 0.029) - 3.25 * pow(iss - 0.02, 15)

        # Exploitability
        av_weight = self.WEIGHTS["AV"][vector.av]
        ac_weight = self.WEIGHTS["AC"][vector.ac]

        # Privileges Required depends on Scope
        if vector.s == "U":
            pr_weight = self.WEIGHTS["PR"][vector.pr]
        else:
            pr_weight = self.WEIGHTS["PR_CHANGED"][vector.pr]

        ui_weight = self.WEIGHTS["UI"][vector.ui]

        exploitability = 8.22 * av_weight * ac_weight * pr_weight * ui_weight

        # Base Score
        if impact <= 0:
            base_score = 0.0
        elif vector.s == "U":
            base_score = min(impact + exploitability, 10.0)
        else:
            base_score = min(1.08 * (impact + exploitability), 10.0)

        return round(base_score, 1)

    def calculate_temporal_score(self, vector: CVSSVector, base_score: float) -> float:
        """
        Calculate Temporal Score (if temporal metrics present)
        """
        if not any([vector.e, vector.rl, vector.rc]):
            return base_score

        e_weight = self.TEMPORAL_WEIGHTS["E"].get(vector.e or "X", 1.0)
        rl_weight = self.TEMPORAL_WEIGHTS["RL"].get(vector.rl or "X", 1.0)
        rc_weight = self.TEMPORAL_WEIGHTS["RC"].get(vector.rc or "X", 1.0)

        temporal_score = round(base_score * e_weight * rl_weight * rc_weight, 1)
        return min(temporal_score, 10.0)

    def get_severity_rating(self, score: float) -> str:
        """Get severity rating from score"""
        if score == 0.0:
            return "None"
        elif score < 4.0:
            return "Low"
        elif score < 7.0:
            return "Medium"
        elif score < 9.0:
            return "High"
        else:
            return "Critical"

    def calculate_full(self, vector: CVSSVector) -> Dict:
        """
        Calculate complete CVSS scores
        """
        base_score = self.calculate_base_score(vector)
        temporal_score = self.calculate_temporal_score(vector, base_score)

        return {
            "base_score": base_score,
            "temporal_score": temporal_score,
            "severity": self.get_severity_rating(base_score),
            "vector_string": vector.to_vector_string(),
            "metrics": {
                "attack_vector": vector.av,
                "attack_complexity": vector.ac,
                "privileges_required": vector.pr,
                "user_interaction": vector.ui,
                "scope": vector.s,
                "confidentiality": vector.c,
                "integrity": vector.i,
                "availability": vector.a,
            },
        }

    def estimate_from_cve(self, cve_data: Dict) -> CVSSVector:
        """
        Estimate CVSS vector from CVE data
        """
        # Default to medium severity if no data
        vector = CVSSVector()

        if "cvss3" in cve_data:
            cvss3 = cve_data["cvss3"]
            if "vectorString" in cvss3:
                return CVSSVector.from_vector_string(cvss3["vectorString"])

        # Estimate from description keywords
        description = cve_data.get("description", "").lower()

        if "remote" in description or "network" in description:
            vector.av = "N"
        elif "local" in description:
            vector.av = "L"

        if "authentication" in description or "privilege" in description:
            vector.pr = "L"

        if "code execution" in description or "rce" in description:
            vector.c = "H"
            vector.i = "H"
            vector.a = "H"
        elif "information disclosure" in description:
            vector.c = "H"
        elif "dos" in description or "denial" in description:
            vector.a = "H"

        return vector
