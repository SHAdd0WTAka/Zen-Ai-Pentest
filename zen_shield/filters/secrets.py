"""
Secret Scrubber - Deterministic regex-based secret detection
Runs BEFORE the LLM, not instead of it.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Pattern, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RedactionMatch:
    """Match information for a redacted secret"""

    secret_type: str
    match: re.Match
    hash: str


class SecretScrubber:
    """
    Deterministic, regex-based, fast secret detection.
    Always active as first line of defense.
    """

    # Comprehensive secret patterns
    PATTERNS: Dict[str, Pattern] = {
        # API Keys
        "api_key": re.compile(r'(?i)(api[_-]?key\s*[=:]\s*)["\']?[a-z0-9]{20,}["\']?', re.IGNORECASE),
        "generic_api_key": re.compile(
            r'(?i)(api[_-]?(?:key|secret|token)|key[_-]?api)\s*[=:]\s*["\']?[a-z0-9]{16,}["\']?',
            re.IGNORECASE,
        ),
        # Authentication tokens
        "bearer_token": re.compile(r"(?i)(bearer\s+)[a-z0-9_\-\.]{20,}", re.IGNORECASE),
        "jwt_token": re.compile(r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", re.IGNORECASE),
        "oauth_token": re.compile(r'(?i)(access[_-]?token|refresh[_-]?token)\s*[=:]\s*["\']?[a-z0-9]{20,}["\']?'),
        # Cloud provider keys
        "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "aws_secret_key": re.compile(
            r'(?i)aws[_-]?(?:secret[_-]?access[_-]?key|session[_-]?token)\s*[=:]\s*["\']?[a-z0-9/+=]{40}["\']?'
        ),
        "azure_key": re.compile(r'(?i)azure[_-]?(?:key|secret|token)\s*[=:]\s*["\']?[a-z0-9]{32,}["\']?'),
        "gcp_key": re.compile(r'(?i)gcp[_-]?(?:key|secret|token)\s*[=:]\s*["\']?[a-z0-9_-]{20,}["\']?'),
        # Private keys
        "private_key_pem": re.compile(
            r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.MULTILINE,
        ),
        "ssh_private_key": re.compile(
            r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?-----END OPENSSH PRIVATE KEY-----",
            re.MULTILINE,
        ),
        # Database connections
        "db_connection_string": re.compile(r"(?i)(mongodb|mysql|postgresql|postgres|redis|elastic)://[^\s\"\']+"),
        "db_password": re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']'),
        # Internal IPs (RFC 1918)
        "ip_internal": re.compile(
            r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
        ),
        # Cookies and sessions
        "session_cookie": re.compile(r"(?i)(session|jwt|token|auth)[_=:\s]+[^;\s]{10,}"),
        "set_cookie_header": re.compile(r"(?i)set-cookie:\s*[^\r\n]+", re.MULTILINE),
        # Email addresses (potentially sensitive)
        "email_address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        # Credit cards (PCI DSS)
        "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        # Slack tokens
        "slack_token": re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"),
        # GitHub tokens
        "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
        # Docker registry auth
        "docker_auth": re.compile(r'"auths":\s*\{[\s\S]*?\}'),
        # Kubernetes secrets
        "k8s_secret": re.compile(r'(?i)(?:token|cert|key)\s*[=:]\s*["\']?[a-z0-9/+=]{20,}["\']?'),
    }

    MASK_TEMPLATE = "[REDACTED_{hash}_{type}]"

    def __init__(self, custom_patterns: Dict[str, str] = None):
        """
        Initialize scrubber with optional custom patterns

        Args:
            custom_patterns: Dict of pattern_name -> regex_string
        """
        self.patterns = self.PATTERNS.copy()

        if custom_patterns:
            for name, pattern in custom_patterns.items():
                try:
                    self.patterns[name] = re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{name}': {e}")

    def scrub(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Scrub secrets from text

        Args:
            text: Raw text to scrub

        Returns:
            Tuple of (cleaned_text, list_of_redactions)
        """
        if not text:
            return text, []

        redactions = []
        cleaned = text

        for secret_type, pattern in self.patterns.items():
            matches = list(pattern.finditer(cleaned))

            # Process in reverse to maintain positions
            for match in reversed(matches):
                original = match.group()

                # Skip if it's a test/example value
                if self._is_test_value(original):
                    continue

                # Create hash for tracking
                original_hash = hashlib.sha256(original.encode()).hexdigest()[:8]

                # Create mask
                mask = self.MASK_TEMPLATE.format(hash=original_hash, type=secret_type.upper())

                # Record redaction
                redactions.append(
                    {
                        "type": secret_type,
                        "position": match.span(),
                        "hash": original_hash,
                        "context": (original[:20] + "..." if len(original) > 20 else original),
                        "length": len(original),
                    }
                )

                # Replace in text
                start, end = match.span()
                cleaned = cleaned[:start] + mask + cleaned[end:]

        # Reverse redactions to maintain original order
        redactions.reverse()

        logger.info(f"Scrubbed {len(redactions)} secrets from text")
        return cleaned, redactions

    def _is_test_value(self, value: str) -> bool:
        """Check if value is a test/example value that should not be redacted"""
        test_patterns = [
            r"example",
            r"test",
            r"xxx",
            r"your_",
            r"my_",
            r"placeholder",
            r"dummy",
        ]

        value_lower = value.lower()
        return any(re.search(p, value_lower) for p in test_patterns)

    def analyze_risk(self, text: str) -> List[str]:
        """
        Analyze text for risk indicators without redacting

        Returns:
            List of risk indicator strings
        """
        indicators = []

        for secret_type, pattern in self.patterns.items():
            if pattern.search(text):
                indicators.append(f"contains_{secret_type}")

        # Additional heuristics
        if self._is_base64_encoded(text):
            indicators.append("base64_encoded_content")

        if self._is_json_web_token(text):
            indicators.append("jwt_detected")

        return indicators

    def _is_base64_encoded(self, text: str) -> bool:
        """Check if text contains base64 encoded content"""
        # Look for base64-like strings (at least 20 chars)
        b64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
        matches = b64_pattern.findall(text)

        for match in matches:
            try:
                import base64

                decoded = base64.b64decode(match)
                # If it decodes to readable text, likely meaningful
                if decoded.isascii() and len(decoded) > 10:
                    return True
            except Exception:
                continue

        return False

    def _is_json_web_token(self, text: str) -> bool:
        """Check if text contains JWT tokens"""
        jwt_pattern = re.compile(r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*")
        return bool(jwt_pattern.search(text))

    def get_stats(self, redactions: List[Dict]) -> Dict:
        """Get statistics about redactions"""
        if not redactions:
            return {"total": 0, "by_type": {}}

        by_type = {}
        for r in redactions:
            t = r["type"]
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total": len(redactions),
            "by_type": by_type,
            "total_chars_redacted": sum(r["length"] for r in redactions),
        }
