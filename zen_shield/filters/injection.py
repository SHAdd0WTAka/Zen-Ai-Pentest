"""
Prompt Injection Detector
Scans for attempts to manipulate LLM behavior
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class InjectionMatch:
    """Detected injection attempt"""

    pattern_name: str
    matched_text: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str


class PromptInjectionDetector:
    """
    Detects prompt injection attempts in user input.
    Prevents jailbreaks and system prompt leakage.
    """

    # Injection patterns (simplified list, expand as needed)
    INJECTION_PATTERNS = {
        "ignore_previous": {
            "pattern": re.compile(
                r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompt|context)",
                re.IGNORECASE,
            ),
            "severity": "high",
            "description": "Attempt to override previous instructions",
        },
        "system_prompt_leak": {
            "pattern": re.compile(
                r"(?i)(what\s+is|show|reveal|print|output)\s+(your|the)\s+(system\s+prompt|instructions?|initial\s+prompt)",
                re.IGNORECASE,
            ),
            "severity": "medium",
            "description": "Attempt to extract system prompt",
        },
        "role_play": {
            "pattern": re.compile(
                r"(?i)(pretend|act|roleplay|imagine)\s+(you\s+are|to\s+be)\s+(a\s+)?(developer|admin|root|sudo)",
                re.IGNORECASE,
            ),
            "severity": "medium",
            "description": "Role-playing attack",
        },
        "jailbreak_dan": {
            "pattern": re.compile(
                r"(?i)(DAN|do\s+anything\s+now|jailbreak|)\s*:?", re.IGNORECASE
            ),
            "severity": "high",
            "description": "Known jailbreak pattern",
        },
        "delimiter_manipulation": {
            "pattern": re.compile(
                r'["\']\s*\n\s*(?:user|assistant|system)\s*:', re.IGNORECASE
            ),
            "severity": "critical",
            "description": "Delimiter manipulation to inject roles",
        },
        "code_execution": {
            "pattern": re.compile(
                r"(?i)(execute|run|eval|exec)\s*[`\(\[]\s*(?:python|bash|sh|shell|cmd)",
                re.IGNORECASE,
            ),
            "severity": "high",
            "description": "Code execution attempt",
        },
        "token_smuggling": {
            "pattern": re.compile(
                r'(?:base64|hex|rot13|url\s*encode|decode)\s*[\(\{]\s*["\'][^"\']{20,}["\']',
                re.IGNORECASE,
            ),
            "severity": "medium",
            "description": "Potential token smuggling",
        },
        "instruction_override": {
            "pattern": re.compile(
                r"(?i)(new\s+instructions?|updated\s+prompt|system\s+override)",
                re.IGNORECASE,
            ),
            "severity": "high",
            "description": "Instruction override attempt",
        },
        "xml_tag_injection": {
            "pattern": re.compile(
                r"<\s*(?:system|user|assistant|instructions?)\s*>",
                re.IGNORECASE,
            ),
            "severity": "critical",
            "description": "XML tag injection",
        },
        "unicode_smuggling": {
            "pattern": re.compile(
                r"[\u200B-\u200D\uFEFF\u2060-\u206F]",  # Zero-width chars
            ),
            "severity": "medium",
            "description": "Unicode smuggling detected",
        },
    }

    # Suspicious character sequences
    SUSPICIOUS_SEQUENCES = [
        "\x00",  # Null bytes
        "\x1b[",  # ANSI escapes in unexpected places
        "\\x",  # Hex escapes
        "\\u",  # Unicode escapes
        "\\n",  # Escaped newlines
        "\\t",  # Escaped tabs
    ]

    def __init__(self):
        self.patterns = self.INJECTION_PATTERNS.copy()

    def scan(self, text: str) -> Tuple[bool, List[InjectionMatch]]:
        """
        Scan text for injection attempts

        Args:
            text: Input text to scan

        Returns:
            Tuple of (is_injection_detected, list_of_matches)
        """
        matches = []

        # Check injection patterns
        for name, config in self.patterns.items():
            for match in config["pattern"].finditer(text):
                matches.append(
                    InjectionMatch(
                        pattern_name=name,
                        matched_text=match.group()[:50],  # Limit length
                        severity=config["severity"],
                        description=config["description"],
                    )
                )

        # Check suspicious sequences
        for seq in self.SUSPICIOUS_SEQUENCES:
            if seq in text:
                matches.append(
                    InjectionMatch(
                        pattern_name="suspicious_sequence",
                        matched_text=seq.encode("unicode_escape").decode(),
                        severity="low",
                        description=f"Suspicious sequence detected: {repr(seq)}",
                    )
                )

        # Check for excessive repetition (obfuscation)
        if self._has_excessive_repetition(text):
            matches.append(
                InjectionMatch(
                    pattern_name="repetition_obfuscation",
                    matched_text="[repeated characters]",
                    severity="low",
                    description="Excessive repetition detected (possible obfuscation)",
                )
            )

        is_injection = len(matches) > 0

        if is_injection:
            logger.warning(f"Detected {len(matches)} injection indicators")
            for match in matches:
                logger.warning(f"  - {match.pattern_name}: {match.severity}")

        return is_injection, matches

    def sanitize(self, text: str) -> str:
        """
        Sanitize text by removing injection attempts

        Args:
            text: Input text

        Returns:
            Sanitized text
        """
        is_injection, matches = self.scan(text)

        if not is_injection:
            return text

        # Remove or neutralize injection attempts
        sanitized = text

        for match in matches:
            if match.severity in ("high", "critical"):
                # Replace with warning
                pattern = self.patterns.get(match.pattern_name, {}).get(
                    "pattern"
                )
                if pattern:
                    sanitized = pattern.sub(
                        "[REMOVED_INJECTION_ATTEMPT]", sanitized
                    )

        # Remove suspicious sequences
        for seq in self.SUSPICIOUS_SEQUENCES:
            sanitized = sanitized.replace(seq, "")

        return sanitized

    def _has_excessive_repetition(
        self, text: str, threshold: int = 10
    ) -> bool:
        """Check for excessive character repetition (obfuscation)"""
        if len(text) < threshold:
            return False

        # Check for repeated characters
        for char in set(text):
            count = text.count(char)
            if count > len(text) * 0.5 and count > threshold:
                return True

        return False

    def get_risk_score(self, matches: List[InjectionMatch]) -> int:
        """
        Calculate risk score from matches

        Returns:
            Risk score 0-100
        """
        severity_scores = {
            "low": 10,
            "medium": 25,
            "high": 50,
            "critical": 100,
        }

        total = sum(severity_scores.get(m.severity, 10) for m in matches)
        return min(total, 100)  # Cap at 100
