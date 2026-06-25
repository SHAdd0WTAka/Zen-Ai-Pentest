"""Smoke tests for core/input_validator.py"""

import pytest

from core.input_validator import InputValidator, SecureSubprocess, ValidationRule, get_validator


class TestValidationRule:
    def test_creation(self):
        import re

        rule = ValidationRule(pattern=re.compile(r"^test$"), max_length=255)
        assert rule.max_length == 255
        assert rule.error_message == "Invalid input"


class TestInputValidator:
    def test_default_init(self):
        validator = InputValidator()
        assert validator.allow_private_ips is True
        assert "domain" in validator.rules
        assert "ip" in validator.rules
        assert "email" in validator.rules

    def test_custom_init(self):
        validator = InputValidator(allow_private_ips=False)
        assert validator.allow_private_ips is False

    def test_validate_domain_valid(self):
        validator = InputValidator()
        result = validator.validate_domain("example.com")
        assert result == "example.com"

    def test_validate_domain_invalid(self):
        validator = InputValidator()
        result = validator.validate_domain("")
        assert result is None

    def test_validate_ip_valid(self):
        validator = InputValidator()
        result = validator.validate_ip("192.168.1.1")
        assert result == "192.168.1.1"

    def test_validate_email_valid(self):
        validator = InputValidator()
        result = validator.validate_email("test@example.com")
        assert result == "test@example.com"


class TestSecureSubprocess:
    def test_validate_nuclei_args_allows_safe(self):
        result = SecureSubprocess.validate_nuclei_args(["-t", "template.yaml"])
        assert result is True

    def test_validate_nuclei_args_blocks_dangerous(self):
        result = SecureSubprocess.validate_nuclei_args(["-shell"])
        assert result is False


class TestGetValidator:
    def test_returns_validator_instance(self):
        v = get_validator()
        assert isinstance(v, InputValidator)
