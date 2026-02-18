"""
IP Address Validator
====================

Validates IP addresses and ranges to ensure they are safe to scan.
Blocks private networks, loopback, and other sensitive ranges.
"""

import ipaddress
from dataclasses import dataclass
from typing import List, Optional, Set, Union


@dataclass
class ValidationResult:
    """Result of IP validation"""

    is_valid: bool
    reason: Optional[str] = None
    blocked_ranges: List[str] = None

    def __post_init__(self):
        if self.blocked_ranges is None:
            self.blocked_ranges = []


class IPValidator:
    """
    Validates IP addresses and ranges for safe scanning.

    Blocks:
    - Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Loopback (127.0.0.0/8)
    - Link-local (169.254.0.0/16)
    - Multicast (224.0.0.0/4)
    - Broadcast (255.255.255.255)
    """

    # Default blocked ranges
    DEFAULT_BLOCKED_NETWORKS = [
        "10.0.0.0/8",  # Private Class A
        "172.16.0.0/12",  # Private Class B
        "192.168.0.0/16",  # Private Class C
        "127.0.0.0/8",  # Loopback
        "169.254.0.0/16",  # Link-local
        "224.0.0.0/4",  # Multicast
        "240.0.0.0/4",  # Reserved
        "255.255.255.255/32",  # Broadcast
        "0.0.0.0/8",  # Current network
        "::1/128",  # IPv6 loopback
        "fe80::/10",  # IPv6 link-local
        "fc00::/7",  # IPv6 unique local
        "ff00::/8",  # IPv6 multicast
    ]

    # Allowed exceptions for testing (e.g., scanme.nmap.org)
    ALLOWED_EXCEPTIONS: Set[str] = set()

    def __init__(self, blocked_networks: Optional[List[str]] = None):
        """
        Initialize validator with blocked networks.

        Args:
            blocked_networks: List of CIDR ranges to block (uses defaults if None)
        """
        networks = blocked_networks or self.DEFAULT_BLOCKED_NETWORKS
        self.blocked_networks = [ipaddress.ip_network(net, strict=False) for net in networks]

    def validate_ip(self, ip: str) -> ValidationResult:
        """
        Validate a single IP address.

        Args:
            ip: IP address to validate

        Returns:
            ValidationResult with is_valid status and reason if blocked
        """
        # Check exceptions
        if ip in self.ALLOWED_EXCEPTIONS:
            return ValidationResult(is_valid=True)

        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return ValidationResult(is_valid=False, reason=f"Invalid IP address format: {ip}")

        # Check against blocked networks
        blocked = []
        for network in self.blocked_networks:
            if addr in network:
                blocked.append(str(network))

        if blocked:
            return ValidationResult(
                is_valid=False, reason=f"IP {ip} is in blocked network range(s): {', '.join(blocked)}", blocked_ranges=blocked
            )

        return ValidationResult(is_valid=True)

    def validate_network(self, network: str) -> ValidationResult:
        """
        Validate a CIDR network range.

        Args:
            network: CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            ValidationResult with is_valid status
        """
        # Check exceptions
        if network in self.ALLOWED_EXCEPTIONS:
            return ValidationResult(is_valid=True)

        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError:
            return ValidationResult(is_valid=False, reason=f"Invalid network format: {network}")

        # Check if network overlaps with any blocked network
        blocked = []
        for blocked_net in self.blocked_networks:
            if net.overlaps(blocked_net):
                blocked.append(str(blocked_net))

        if blocked:
            return ValidationResult(
                is_valid=False,
                reason=f"Network {network} overlaps with blocked range(s): {', '.join(blocked)}",
                blocked_ranges=blocked,
            )

        return ValidationResult(is_valid=True)

    def validate_target(self, target: str) -> ValidationResult:
        """
        Validate a target which can be IP, CIDR, or hostname.

        Args:
            target: Target to validate (IP, CIDR, or hostname)

        Returns:
            ValidationResult with is_valid status
        """
        # Check exceptions first
        if target in self.ALLOWED_EXCEPTIONS:
            return ValidationResult(is_valid=True)

        # Try as IP address
        try:
            return self.validate_ip(target)
        except Exception:
            pass

        # Try as network
        if "/" in target:
            try:
                return self.validate_network(target)
            except Exception:
                pass

        # Assume it's a hostname - will be validated by DomainValidator
        return ValidationResult(is_valid=True)

    def add_exception(self, target: str):
        """Add an allowed exception (e.g., scanme.nmap.org)"""
        self.ALLOWED_EXCEPTIONS.add(target)

    def remove_exception(self, target: str):
        """Remove an exception"""
        self.ALLOWED_EXCEPTIONS.discard(target)

    def get_blocked_ranges(self) -> List[str]:
        """Get list of blocked network ranges"""
        return [str(net) for net in self.blocked_networks]


# Singleton instance for application-wide use
_default_validator: Optional[IPValidator] = None


def get_ip_validator() -> IPValidator:
    """Get or create default IP validator instance"""
    global _default_validator
    if _default_validator is None:
        _default_validator = IPValidator()
    return _default_validator


def validate_target(target: str) -> ValidationResult:
    """Convenience function to validate a target"""
    return get_ip_validator().validate_target(target)
