"""Comprehensive validation utility tests."""

import re

import pytest


class ValidationUtils:
    """Validation utilities for testing."""

    @staticmethod
    def is_valid_ip(ip):
        """Validate IPv4 address."""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, ip):
            return False
        parts = ip.split(".")
        return all(0 <= int(p) <= 255 for p in parts)

    @staticmethod
    def is_valid_cidr(cidr):
        """Validate CIDR notation."""
        try:
            ip, mask = cidr.split("/")
            if not ValidationUtils.is_valid_ip(ip):
                return False
            mask = int(mask)
            return 0 <= mask <= 32
        except ValueError:
            return False

    @staticmethod
    def is_valid_port(port):
        """Validate port number."""
        try:
            p = int(port)
            return 1 <= p <= 65535
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_hostname(hostname):
        """Validate hostname."""
        if len(hostname) > 255:
            return False
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        return bool(re.match(pattern, hostname))

    @staticmethod
    def sanitize_input(user_input):
        """Sanitize user input."""
        if not isinstance(user_input, str):
            return ""
        # Remove dangerous characters
        dangerous = [";", "|", "&", "`", "$", "(", ")", "{", "}", "<", ">"]
        for char in dangerous:
            user_input = user_input.replace(char, "")
        return user_input.strip()


class TestValidationUtils:
    """Test suite for validation utilities."""

    def test_valid_ipv4(self):
        """Test valid IPv4 addresses."""
        valid_ips = ["192.168.1.1", "10.0.0.1", "255.255.255.255", "0.0.0.0"]  # nosec B104
        for ip in valid_ips:
            assert ValidationUtils.is_valid_ip(ip) is True

    def test_invalid_ipv4(self):
        """Test invalid IPv4 addresses."""
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "abc.def.ghi.jkl",
            "",
        ]
        for ip in invalid_ips:
            assert ValidationUtils.is_valid_ip(ip) is False

    def test_valid_cidr(self):
        """Test valid CIDR notation."""
        valid_cidrs = [
            "192.168.1.0/24",
            "10.0.0.0/8",
            "172.16.0.0/16",
            "0.0.0.0/0",
        ]
        for cidr in valid_cidrs:
            assert ValidationUtils.is_valid_cidr(cidr) is True

    def test_invalid_cidr(self):
        """Test invalid CIDR notation."""
        invalid_cidrs = [
            "192.168.1.0/33",
            "10.0.0.0",
            "invalid/24",
            "192.168.1.0/abc",
        ]
        for cidr in invalid_cidrs:
            assert ValidationUtils.is_valid_cidr(cidr) is False

    def test_valid_ports(self):
        """Test valid port numbers."""
        valid_ports = [1, 80, 443, 8080, 65535]
        for port in valid_ports:
            assert ValidationUtils.is_valid_port(port) is True

    def test_invalid_ports(self):
        """Test invalid port numbers."""
        invalid_ports = [0, 65536, -1, "abc", None]
        for port in invalid_ports:
            assert ValidationUtils.is_valid_port(port) is False

    def test_valid_hostnames(self):
        """Test valid hostnames."""
        valid_hosts = [
            "example.com",
            "sub.domain.com",
            "localhost",
            "host-name",
        ]
        for host in valid_hosts:
            assert ValidationUtils.is_valid_hostname(host) is True

    def test_invalid_hostnames(self):
        """Test invalid hostnames."""
        invalid_hosts = ["-invalid.com", "invalid-.com", "a" * 256, ""]
        for host in invalid_hosts:
            assert ValidationUtils.is_valid_hostname(host) is False

    def test_sanitize_input(self):
        """Test input sanitization."""
        dangerous = "test; rm -rf / | cat /etc/passwd"
        sanitized = ValidationUtils.sanitize_input(dangerous)
        assert ";" not in sanitized
        assert "|" not in sanitized
        assert "rm" in sanitized  # rm remains, ; is removed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
