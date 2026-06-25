"""
Unit Tests for Credential Lifecycle Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestCredentialLifecycle:
    """Test Credential Lifecycle"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import credential_lifecycle

        assert credential_lifecycle is not None


class TestCredentialManager:
    """Test Credential Manager"""

    def test_credential_manager_import(self):
        """Test credential manager import"""
        from core.credential_lifecycle import credential_lifecycle

        assert credential_lifecycle is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
