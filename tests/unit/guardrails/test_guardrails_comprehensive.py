"""Comprehensive tests for guardrails module"""

import pytest


class TestRiskLevels:
    """Test RiskLevel enum"""

    def test_risk_level_import(self):
        from guardrails.risk_levels import RiskLevel

        assert RiskLevel is not None

    def test_safe_level(self):
        from guardrails.risk_levels import RiskLevel

        assert hasattr(RiskLevel, "SAFE")

    def test_aggressive_level(self):
        from guardrails.risk_levels import RiskLevel

        assert hasattr(RiskLevel, "AGGRESSIVE")


class TestIPValidator:
    """Test IP validation"""

    def test_ip_validator_import(self):
        from guardrails.ip_validator import IPValidator

        assert IPValidator is not None

    def test_valid_public_ip(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        result = validator.validate_ip("8.8.8.8")
        assert result.is_valid is True

    def test_private_ip_blocked(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        result = validator.validate_ip("10.0.0.1")
        assert result.is_valid is False

    def test_localhost_blocked(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        result = validator.validate_ip("127.0.0.1")
        assert result.is_valid is False

    def test_validation_result_import(self):
        from guardrails.ip_validator import ValidationResult

        assert ValidationResult is not None

    def test_get_blocked_ranges(self):
        from guardrails.ip_validator import IPValidator

        validator = IPValidator()
        ranges = validator.get_blocked_ranges()
        assert isinstance(ranges, list)
        assert len(ranges) > 0


class TestDomainValidator:
    """Test domain validation"""

    def test_domain_validator_import(self):
        from guardrails.domain_validator import DomainValidator

        assert DomainValidator is not None

    def test_valid_domain(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        result = validator.validate_domain("example.com")
        assert result.is_valid is True

    def test_localhost_blocked(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        result = validator.validate_domain("localhost")
        assert result.is_valid is False

    def test_local_domain_blocked(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        result = validator.validate_domain("test.local")
        assert result.is_valid is False

    def test_is_internal_domain(self):
        from guardrails.domain_validator import DomainValidator

        validator = DomainValidator()
        assert validator.is_internal_domain("test.local") is True
        assert validator.is_internal_domain("example.com") is False

    def test_domain_validation_result_import(self):
        from guardrails.domain_validator import DomainValidationResult

        assert DomainValidationResult is not None


class TestRateLimiter:
    """Test rate limiting"""

    def test_rate_limiter_import(self):
        from guardrails.rate_limiter import RateLimiter

        assert RateLimiter is not None
