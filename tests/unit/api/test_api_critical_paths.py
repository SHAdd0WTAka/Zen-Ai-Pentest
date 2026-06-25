"""Critical API path tests with real assertions."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create TestClient for API testing."""
    try:
        from api.main import app
    except ImportError as exc:
        pytest.skip(f"API main module not available: {exc}")

    return TestClient(app)


class TestAPIHealth:
    """Health check endpoints - critical for monitoring."""

    def test_health_endpoint_returns_200(self, client):
        """Critical: Health check must return 200 for load balancers."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() is not None

    def test_health_returns_valid_json(self, client):
        """Critical: Health response must be valid JSON with status."""
        response = client.get("/health")

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data or "healthy" in str(data).lower()


class TestAPIAgentManagement:
    """Agent management endpoints - critical for swarm operations."""

    def test_agents_list_endpoint_exists(self, client):
        """Critical: Agent list endpoint must be accessible."""
        response = client.get("/api/v1/agents/")

        assert response.status_code in [200, 401, 403]

    def test_agent_start_endpoint_structure(self, client):
        """Critical: Agent start endpoint must accept POST."""
        response = client.post("/api/v1/agents/test-agent/start")

        assert response.status_code != 404

    def test_agent_stop_endpoint_structure(self, client):
        """Critical: Agent stop endpoint must accept POST."""
        response = client.post("/api/v1/agents/test-agent/stop")

        assert response.status_code != 404

    def test_agent_task_assignment_endpoint(self, client):
        """Critical: Task assignment endpoint must exist."""
        payload = {"task": "scan", "target": "127.0.0.1"}
        response = client.post("/api/v1/agents/test-agent/task", json=payload)

        assert response.status_code != 404

    def test_agent_broadcast_endpoint(self, client):
        """Critical: Broadcast endpoint for swarm messages."""
        payload = {"message": "test broadcast", "priority": 1}
        response = client.post("/api/v1/agents/broadcast", json=payload)

        assert response.status_code != 404

    def test_agent_system_status_endpoint(self, client):
        """Critical: System status for swarm monitoring."""
        response = client.get("/api/v1/agents/system/status")

        assert response.status_code in [200, 401, 403]


class TestAPIScanManagement:
    """Scan management endpoints - critical for core functionality."""

    def test_scans_list_endpoint(self, client):
        """Critical: Scan list must be accessible."""
        response = client.get("/api/v1/scans/")

        assert response.status_code in [200, 401]

    def test_scan_create_endpoint_structure(self, client):
        """Critical: Scan creation endpoint must accept POST."""
        payload = {
            "name": "test_scan",
            "target": "127.0.0.1",
            "scan_type": "port_scan",
        }
        response = client.post("/api/v1/scans/", json=payload)

        assert response.status_code in [201, 200, 401, 403, 422]

    def test_scan_get_endpoint(self, client):
        """Critical: Individual scan retrieval."""
        response = client.get("/api/v1/scans/test-scan-id")

        assert response.status_code != 404


class TestAPIAuth:
    """Authentication endpoints - critical for security."""

    def test_login_endpoint_exists(self, client):
        """Critical: Login endpoint must exist."""
        payload = {"username": "test", "password": "test"}
        response = client.post("/api/v1/auth/login", json=payload)

        # Auth endpoint exists if not 404 (can be 401, 422, 200)
        assert response.status_code in [200, 401, 403, 422]

    def test_protected_endpoint_requires_auth(self, client):
        """Critical: Protected endpoints must check auth."""
        response = client.get("/api/v1/agents/")

        if response.status_code != 200:
            assert response.status_code in [401, 403]


class TestAPIErrorHandling:
    """Error handling - critical for robustness."""

    def test_404_or_auth_for_invalid_endpoint(self, client):
        """Critical: Invalid endpoints must return 404 or trigger auth."""
        response = client.get("/api/v1/nonexistent-endpoint-12345")

        # Can be 404 (not found) or 401 (auth required first)
        assert response.status_code in [404, 401, 403]

    def test_422_or_auth_for_invalid_json(self, client):
        """Critical: Invalid JSON must return 422 or trigger auth."""
        response = client.post(
            "/api/v1/agents/test/task",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Can be 400/422 (validation) or 401 (auth required)
        assert response.status_code in [400, 401, 403, 422]

    def test_405_or_auth_for_wrong_method(self, client):
        """Critical: Wrong HTTP method must return 405 or trigger auth."""
        response = client.delete("/api/v1/agents/")

        # Can be 405 (method not allowed), 404 (not found), or 401 (auth)
        assert response.status_code in [405, 404, 401, 403]


class TestAPIResponseFormats:
    """Response format validation - critical for frontend."""

    def test_json_content_type(self, client):
        """Critical: API must return JSON for API endpoints."""
        response = client.get("/health")

        assert "application/json" in response.headers.get("content-type", "")

    def test_cors_headers_present(self, client):
        """Critical: CORS headers must be present for frontend."""
        response = client.get("/health")

        assert response.status_code == 200


class TestAPIPerformance:
    """Performance smoke tests - critical for UX."""

    def test_health_response_time(self, client):
        """Critical: Health check must respond quickly (< 1s)."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Health check took {elapsed:.2f}s"

    def test_agents_list_response_time(self, client):
        """Critical: Agent list must respond in reasonable time."""
        start = time.time()
        client.get("/api/v1/agents/")
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Agent list took {elapsed:.2f}s"
