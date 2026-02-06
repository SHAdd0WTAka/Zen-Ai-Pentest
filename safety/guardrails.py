"""
Output Guardrails - Primary defense against hallucinations
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


class SafetyLevel(Enum):
    """Safety strictness levels"""

    PERMISSIVE = "permissive"  # Development/testing
    STANDARD = "standard"  # Default production
    STRICT = "strict"  # High-stakes operations
    PARANOID = "paranoid"  # Critical security contexts


@dataclass
class GuardrailResult:
    """Result of guardrail check"""

    passed: bool
    violations: List[str]
    safety_level: SafetyLevel
    confidence_penalty: float  # 0.0 - 1.0 reduction


class OutputGuardrails:
    """
    Multi-layer guardrail system for AI outputs.
    Prevents hallucinations through pattern detection and validation.
    """

    # Patterns indicating potential hallucinations
    HALLUCINATION_PATTERNS = {
        "uncertainty": [
            r"maybe",
            r"perhaps",
            r"possibly",
            r"might be",
            r"could be",
            r"I think",
            r"probably",
            r"likely",
            r"seems",
        ],
        "fabrication": [
            r"I remember",
            r"I recall",
            r"in my experience",
            r"I have seen",
            r"typically",
            r"usually",
        ],
        "over_confidence": [
            r"definitely",
            r"absolutely",
            r"without a doubt",
            r"certainly",
            r"100%",
            r"always",
        ],
        "vague_references": [
            r"some",
            r"certain",
            r"specific",
            r"various",
            r"several",
        ],
    }

    # Security-critical false claims patterns
    SECURITY_FALSEHOODS = [
        r"impossible to exploit",
        r"completely secure",
        r"no vulnerability",
        r"100% safe",
        r"immune to",
        r"unhackable",
    ]

    def __init__(self, safety_level: SafetyLevel = SafetyLevel.STANDARD):
        self.safety_level = safety_level
        self.violation_history: List[Dict] = []

        # Configure strictness based on level
        self.thresholds = {
            SafetyLevel.PERMISSIVE: {"max_uncertainty": 5, "max_fabrication": 3},
            SafetyLevel.STANDARD: {"max_uncertainty": 3, "max_fabrication": 1},
            SafetyLevel.STRICT: {"max_uncertainty": 1, "max_fabrication": 0},
            SafetyLevel.PARANOID: {"max_uncertainty": 0, "max_fabrication": 0},
        }[safety_level]

    def check(self, output: str, context: Optional[Dict] = None) -> GuardrailResult:
        """
        Run output through all guardrails
        """
        violations = []
        confidence_penalty = 0.0

        # Check 1: Hallucination patterns
        uncertainty_count = self._count_patterns(output, "uncertainty")
        fabrication_count = self._count_patterns(output, "fabrication")

        if uncertainty_count > self.thresholds["max_uncertainty"]:
            violations.append(f"Too many uncertainty indicators ({uncertainty_count})")
            confidence_penalty += 0.2 * uncertainty_count

        if fabrication_count > self.thresholds["max_fabrication"]:
            violations.append(f"Fabrication indicators detected ({fabrication_count})")
            confidence_penalty += 0.3 * fabrication_count

        # Check 2: Security falsehoods (always flag)
        falsehoods = self._detect_security_falsehoods(output)
        if falsehoods:
            violations.extend([f"Security falsehood: {f}" for f in falsehoods])
            confidence_penalty += 0.5 * len(falsehoods)

        # Check 3: Confidence calibration
        over_confidence = self._count_patterns(output, "over_confidence")
        if over_confidence > 2 and (uncertainty_count + fabrication_count) > 0:
            violations.append("Over-confidence with uncertainty indicators")
            confidence_penalty += 0.25

        # Check 4: Vague references (context-dependent)
        if self.safety_level in [SafetyLevel.STRICT, SafetyLevel.PARANOID]:
            vague_count = self._count_patterns(output, "vague_references")
            if vague_count > 2:
                violations.append(f"Too vague references ({vague_count})")
                confidence_penalty += 0.15 * vague_count

        # Record violations
        if violations:
            self.violation_history.append(
                {"output_snippet": output[:200], "violations": violations, "safety_level": self.safety_level.value}
            )

        passed = len(violations) == 0 or confidence_penalty < 0.5

        return GuardrailResult(
            passed=passed,
            violations=violations,
            safety_level=self.safety_level,
            confidence_penalty=min(confidence_penalty, 1.0),
        )

    def _count_patterns(self, text: str, category: str) -> int:
        """Count occurrences of pattern category"""
        patterns = self.HALLUCINATION_PATTERNS.get(category, [])
        text_lower = text.lower()
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text_lower, re.IGNORECASE))
        return count

    def _detect_security_falsehoods(self, text: str) -> List[str]:
        """Detect dangerous false security claims"""
        found = []
        text_lower = text.lower()
        for pattern in self.SECURITY_FALSEHOODS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(pattern)
        return found

    def get_stats(self) -> Dict[str, Any]:
        """Get guardrail statistics"""
        return {
            "total_checks": len(self.violation_history),
            "safety_level": self.safety_level.value,
            "recent_violations": self.violation_history[-10:],
        }
