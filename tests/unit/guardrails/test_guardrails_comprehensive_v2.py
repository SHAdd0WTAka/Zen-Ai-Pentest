"""Comprehensive guardrails tests v2"""

import pytest


class TestIPValidatorComprehensive:
    """Comprehensive IP validation tests"""

    def test_valid_public_ips(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        assert validator.validate_ip("8.8.8.8").is_valid is True
        assert validator.validate_ip("1.1.1.1").is_valid is True
        assert validator.validate_ip("208.67.222.222").is_valid is True

    def test_private_ips_blocked(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        assert validator.validate_ip("10.0.0.1").is_valid is False
        assert validator.validate_ip("172.16.0.1").is_valid is False
        assert validator.validate_ip("192.168.1.1").is_valid is False

    def test_loopback_blocked(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        assert validator.validate_ip("127.0.0.1").is_valid is False

    def test_invalid_ip(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        result = validator.validate_ip("999.999.999.999")
        assert result.is_valid is False

    def test_blocked_ranges(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        ranges = validator.get_blocked_ranges()
        assert isinstance(ranges, list)
        assert len(ranges) > 0


class TestDomainValidatorComprehensive:
    """Comprehensive domain validation tests"""

    def test_valid_domains(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        assert validator.validate_domain("example.com").is_valid is True
        assert validator.validate_domain("google.com").is_valid is True

    def test_internal_domains_blocked(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        assert validator.validate_domain("localhost").is_valid is False
        assert validator.validate_domain("test.local").is_valid is False
        assert validator.validate_domain("internal.corp").is_valid is False

    def test_is_internal(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        assert validator.is_internal_domain("localhost") is True
        assert validator.is_internal_domain("example.com") is False


class TestRiskLevelsComprehensive:
    """Comprehensive risk levels tests"""

    def test_risk_level_values(self):
        from guardrails.risk_levels import RiskLevel

        assert hasattr(RiskLevel, "SAFE")
        assert hasattr(RiskLevel, "NORMAL")
        assert hasattr(RiskLevel, "ELEVATED")
        assert hasattr(RiskLevel, "AGGRESSIVE")

    def test_risk_level_order(self):
        from guardrails.risk_levels import RiskLevel

        assert RiskLevel.SAFE.value < RiskLevel.NORMAL.value
        assert RiskLevel.NORMAL.value < RiskLevel.ELEVATED.value
        assert RiskLevel.ELEVATED.value < RiskLevel.AGGRESSIVE.value


class TestRateLimiterComprehensive:
    """Comprehensive rate limiter tests"""

    def test_rate_limiter_creation(self):
        from guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert limiter is not None

    def test_rate_limiter_has_methods(self):
        from guardrails.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert hasattr(limiter, "check_rate_limit") or hasattr(limiter, "reset")
