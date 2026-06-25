"""
Unit Tests for GitHub App Integration Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestGitHubAppIntegration:
    """Test GitHub App Integration"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import github_app_integration

        assert github_app_integration is not None

    def test_github_app_auth(self):
        """Test GitHub App Auth"""
        from core.github_app_integration import GitHubAppAuth

        auth = GitHubAppAuth()
        assert auth is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
