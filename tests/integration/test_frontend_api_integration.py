"""
Integration Tests for Frontend API
Tests the connection between Frontend and API
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


@pytest.mark.frontend_integration
class TestFrontendAPIClient:
    """Test Frontend API Client"""

    def test_api_client_import(self):
        """Test that API client can be imported"""
        # Note: This is a TypeScript file, so we just verify it exists
        client_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "web_ui",
            "frontend",
            "src",
            "api",
            "client.ts",
        )
        assert os.path.exists(client_path)

    def test_api_client_structure(self):
        """Test API client has required methods"""
        # Read the TypeScript file and verify structure
        client_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "web_ui",
            "frontend",
            "src",
            "api",
            "client.ts",
        )

        with open(client_path, "r") as f:
            content = f.read()

        # Check for required methods
        assert "login" in content
        assert "logout" in content
        assert "getScans" in content
        assert "createScan" in content
        assert "getFindings" in content
        assert "getTools" in content
        assert "getSystemStatus" in content


@pytest.mark.frontend_integration
class TestFrontendComponents:
    """Test Frontend Components"""

    def test_components_directory_exists(self):
        """Test components directory exists"""
        components_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "web_ui",
            "frontend",
            "src",
            "components",
        )
        assert os.path.exists(components_path)

    def test_pages_directory_exists(self):
        """Test pages directory exists"""
        pages_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "web_ui",
            "frontend",
            "src",
            "pages",
        )
        assert os.path.exists(pages_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
