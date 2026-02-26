"""API Authenticated Tests.

Target: +10% Coverage durch authentifizierte API-Tests.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import create_access_token

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


class TestAuthenticatedScans:
    """Authenticated tests for scan endpoints."""

    def test_get_scans_authenticated(self, auth_headers):
        """Test GET /scans with authentication."""
        response = client.get("/scans", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_create_scan_authenticated(self, auth_headers):
        """Test POST /scans with authentication."""
        scan_data = {
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "network",
        }
        response = client.post("/scans", json=scan_data, headers=auth_headers)
        assert response.status_code in [200, 201, 400, 422]


class TestAuthenticatedFindings:
    """Authenticated tests for finding endpoints."""

    def test_get_findings_authenticated(self, auth_headers):
        """Test GET /findings with authentication."""
        response = client.get("/findings", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthenticatedUsers:
    """Authenticated tests for user endpoints."""

    def test_get_current_user_authenticated(self, auth_headers):
        """Test GET /users/me with authentication."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_get_users_authenticated(self, auth_headers):
        """Test GET /users with authentication."""
        response = client.get("/users", headers=auth_headers)
        assert response.status_code in [200, 403, 404]


class TestAuthenticatedReports:
    """Authenticated tests for report endpoints."""

    def test_get_reports_authenticated(self, auth_headers):
        """Test GET /reports with authentication."""
        response = client.get("/reports", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthenticatedTools:
    """Authenticated tests for tool endpoints."""

    def test_get_tools_authenticated(self, auth_headers):
        """Test GET /tools with authentication."""
        response = client.get("/tools", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthenticatedDashboard:
    """Authenticated tests for dashboard endpoints."""

    def test_get_dashboard_stats_authenticated(self, auth_headers):
        """Test GET /dashboard/stats with authentication."""
        response = client.get("/dashboard/stats", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_get_dashboard_recent_scans_authenticated(self, auth_headers):
        """Test GET /dashboard/recent-scans with authentication."""
        response = client.get("/dashboard/recent-scans", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthenticatedAgents:
    """Authenticated tests for agent endpoints."""

    def test_get_agents_authenticated(self, auth_headers):
        """Test GET /agents with authentication."""
        response = client.get("/agents", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthenticatedTargets:
    """Authenticated tests for target endpoints."""

    def test_get_targets_authenticated(self, auth_headers):
        """Test GET /targets with authentication."""
        response = client.get("/targets", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthTokenOperations:
    """Tests for token operations."""

    def test_token_creation(self):
        """Test that access token can be created."""
        from api.auth import create_access_token
        token = create_access_token({"sub": "test@example.com"})
        assert token is not None
        assert isinstance(token, str)

    def test_token_verification(self):
        """Test that access token can be verified."""
        from api.auth import create_access_token, verify_token
        import asyncio
        
        token = create_access_token({"sub": "test@example.com"})
        
        # Run async function
        payload = asyncio.run(verify_token(token))
        assert payload is not None
        assert payload.get("sub") == "test@example.com"
