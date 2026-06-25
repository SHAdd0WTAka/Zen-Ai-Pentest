"""
Unit Tests for Input Validator Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestInputValidator:
    """Test Input Validator"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import input_validator

        assert input_validator is not None

    def test_validate_url(self):
        """Test URL validation"""
        from core.input_validator import InputValidator

        validator = InputValidator()
        # Valid URLs
        result = validator.validate_url("http://example.com")
        # Just check it doesn't raise an exception


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
