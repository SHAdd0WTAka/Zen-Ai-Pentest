"""
Domain Validator
================

Validates domain names to prevent scanning of internal/sensitive domains.
Blocks localhost, internal domains, and certain TLDs.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set
from urllib.parse import urlparse


@dataclass
class DomainValidationResult:
    """Result of domain validation"""

    is_valid: bool
    reason: Optional[str] = None
    blocked_patterns: List[str] = None

    def __post_init__(self):
        if self.blocked_patterns is None:
            self.blocked_patterns = []


class DomainValidator:
    """
    Validates domain names for safe scanning.

    Blocks:
    - localhost and variations
    - .local, .internal, .corp TLDs
    - IP addresses in URLs
    - File:// URLs
    """

    # Blocked TLDs (internal use only)
    BLOCKED_TLDS = {
        ".local",
        ".internal",
        ".corp",
        ".home",
        ".lan",
        ".private",
    }

    # Blocked exact matches
    BLOCKED_DOMAINS = {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
    }

    # Blocked patterns (regex)
    BLOCKED_PATTERNS = [
        r"^\d+\.\d+\.\d+\.\d+$",  # IP addresses
        r"^.*\.localhost$",  # *.localhost
        r"^localhost\.\w+$",  # localhost.*
    ]

    # Allowed exceptions
    ALLOWED_EXCEPTIONS: Set[str] = set()

    def __init__(
        self,
        blocked_tlds: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        blocked_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize domain validator.

        Args:
            blocked_tlds: Additional TLDs to block
            blocked_domains: Additional domains to block
            blocked_patterns: Additional regex patterns to block
        """
        self.blocked_tlds = self.BLOCKED_TLDS | (blocked_tlds or set())
        self.blocked_domains = self.BLOCKED_DOMAINS | (
            blocked_domains or set()
        )
        self.blocked_patterns = self.BLOCKED_PATTERNS + (
            blocked_patterns or []
        )
        self._compiled_patterns = [
            re.compile(p) for p in self.blocked_patterns
        ]

    def validate_domain(self, domain: str) -> DomainValidationResult:
        """
        Validate a domain name.

        Args:
            domain: Domain to validate (e.g., "example.com")

        Returns:
            DomainValidationResult with is_valid status
        """
        # Normalize
        domain = domain.lower().strip()

        # Check exceptions
        if domain in self.ALLOWED_EXCEPTIONS:
            return DomainValidationResult(is_valid=True)

        # Check exact matches
        if domain in self.blocked_domains:
            return DomainValidationResult(
                is_valid=False,
                reason=f"Domain '{domain}' is blocked",
                blocked_patterns=[domain],
            )

        # Check TLD
        for tld in self.blocked_tlds:
            if domain.endswith(tld):
                return DomainValidationResult(
                    is_valid=False,
                    reason=f"Domain '{domain}' uses blocked TLD '{tld}'",
                    blocked_patterns=[tld],
                )

        # Check regex patterns
        for pattern, compiled in zip(
            self.blocked_patterns, self._compiled_patterns
        ):
            if compiled.match(domain):
                return DomainValidationResult(
                    is_valid=False,
                    reason=f"Domain '{domain}' matches blocked pattern: {pattern}",
                    blocked_patterns=[pattern],
                )

        return DomainValidationResult(is_valid=True)

    def validate_url(self, url: str) -> DomainValidationResult:
        """
        Validate a URL.

        Args:
            url: URL to validate

        Returns:
            DomainValidationResult with is_valid status
        """
        # Check exceptions
        if url in self.ALLOWED_EXCEPTIONS:
            return DomainValidationResult(is_valid=True)

        # Block file:// URLs
        if url.startswith("file://"):
            return DomainValidationResult(
                is_valid=False,
                reason="File:// URLs are not allowed",
                blocked_patterns=["file://"],
            )

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return DomainValidationResult(
                is_valid=False, reason=f"Invalid URL format: {e}"
            )

        # Extract domain
        domain = parsed.netloc
        if not domain:
            # Try without scheme
            if "://" not in url:
                return self.validate_domain(url)
            domain = parsed.path.split("/")[0]

        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]

        return self.validate_domain(domain)

    def add_exception(self, domain: str):
        """Add an allowed exception"""
        self.ALLOWED_EXCEPTIONS.add(domain.lower().strip())

    def remove_exception(self, domain: str):
        """Remove an exception"""
        self.ALLOWED_EXCEPTIONS.discard(domain.lower().strip())

    def is_internal_domain(self, domain: str) -> bool:
        """
        Check if a domain is likely internal/private.

        Args:
            domain: Domain to check

        Returns:
            True if domain appears to be internal
        """
        result = self.validate_domain(domain)
        return not result.is_valid


# Singleton instance
_default_validator: Optional[DomainValidator] = None


def get_domain_validator() -> DomainValidator:
    """Get or create default domain validator instance"""
    global _default_validator
    if _default_validator is None:
        _default_validator = DomainValidator()
    return _default_validator


def validate_domain(domain: str) -> DomainValidationResult:
    """Convenience function to validate a domain"""
    return get_domain_validator().validate_domain(domain)


def validate_url(url: str) -> DomainValidationResult:
    """Convenience function to validate a URL"""
    return get_domain_validator().validate_url(url)
