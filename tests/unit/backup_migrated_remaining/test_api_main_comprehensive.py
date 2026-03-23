"""
Comprehensive Tests for api/main.py
Target: 80% Coverage
Strategy: Test all endpoints with valid and invalid inputs
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app

client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def valid_login_data():
    return {"username": "admin", "password": "admin"}


@pytest.fixture
def valid_scan_data():
    return {
        "name": "Test Scan",
        "target": "scanme.nmap.org",
        "scan_type": "port_scan",
        "config": {"ports": "80,443"},
    }


@pytest.fixture
def valid_finding_data():
    return {
        "title": "Test Finding",
        "description": "Test description",
        "severity": "medium",
        "target": "example.com",
    }


@pytest.fixture
def valid_tool_execute_data():
    return {
        "tool_name": "nmap",
        "parameters": {"target": "127.0.0.1", "ports": "80"},
    }


@pytest.fixture
def valid_schedule_data():
    return {
        "name": "Daily Scan",
        "target": "example.com",
        "scan_type": "port_scan",
        "frequency": "daily",
        "cron": "0 0 * * *",
    }


# =============================================================================
# APP INITIALIZATION
# =============================================================================


class TestAppInit:
    """Test FastAPI app initialization"""

    def test_app_exists(self):
        assert app is not None

    def test_app_title(self):
        assert "Zen-AI-Pentest" in app.title

    def test_cors_middleware_exists(self):
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    def test_docs_endpoint(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_endpoint(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================


class TestHealthEndpoints:
    """Test health and info endpoints"""

    def test_health_get(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_info_get(self):
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data or "name" in data


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_post_valid_format(self, valid_login_data):
        """Test login with valid format - may 401 but should not crash"""
        response = client.post("/auth/login", json=valid_login_data)
        assert response.status_code in [200, 401, 422]

    def test_login_post_invalid_format(self):
        response = client.post("/auth/login", json={})
        assert response.status_code == 422

    def test_login_post_missing_fields(self):
        response = client.post("/auth/login", json={"username": "test"})
        assert response.status_code == 422

    def test_me_get_unauthorized(self):
        response = client.get("/auth/me")
        assert response.status_code in [401, 403]

    def test_refresh_post_valid(self):
        response = client.post("/auth/refresh", json={"refresh_token": "test"})
        assert response.status_code in [200, 401, 422]

    def test_refresh_post_invalid(self):
        response = client.post("/auth/refresh", json={})
        assert response.status_code == 422

    def test_csrf_token_get(self):
        response = client.get("/csrf-token")
        assert response.status_code == 200

    def test_logout_post_unauthorized(self):
        response = client.post("/auth/logout")
        assert response.status_code in [401, 403, 200]

    def test_logout_all_post_unauthorized(self):
        response = client.post("/auth/logout-all")
        assert response.status_code in [401, 403, 200]


# =============================================================================
# SCAN ENDPOINTS
# =============================================================================


class TestScanEndpoints:
    """Test scan CRUD endpoints"""

    def test_scans_get_unauthorized(self):
        response = client.get("/scans")
        assert response.status_code in [200, 401, 403]

    def test_scans_post_valid_format(self, valid_scan_data):
        response = client.post("/scans", json=valid_scan_data)
        assert response.status_code in [200, 201, 401, 403, 422]

    def test_scans_post_invalid_format(self):
        response = client.post("/scans", json={"invalid": "data"})
        assert response.status_code in [401, 403, 422]

    def test_scan_get_by_id_invalid(self):
        response = client.get("/scans/invalid-id")
        assert response.status_code in [400, 404, 422]

    def test_scan_get_by_id_not_found(self):
        response = client.get("/scans/99999")
        assert response.status_code in [401, 403, 404]

    def test_scan_patch_by_id_unauthorized(self):
        response = client.patch("/scans/1", json={"status": "running"})
        assert response.status_code in [401, 403, 404]

    def test_scan_delete_by_id_unauthorized(self):
        response = client.delete("/scans/1")
        assert response.status_code in [401, 403, 404]


# =============================================================================
# SCAN FINDINGS ENDPOINTS
# =============================================================================


class TestScanFindingsEndpoints:
    """Test finding endpoints related to scans"""

    def test_scan_findings_get_unauthorized(self):
        response = client.get("/scans/1/findings")
        assert response.status_code in [401, 403, 404]

    def test_scan_findings_post_valid_format(self, valid_finding_data):
        response = client.post("/scans/1/findings", json=valid_finding_data)
        assert response.status_code in [200, 201, 401, 403, 404, 422]

    def test_scan_findings_post_invalid_scan(self):
        response = client.post("/scans/99999/findings", json={})
        assert response.status_code in [401, 403, 404, 422]


# =============================================================================
# FINDING ENDPOINTS
# =============================================================================


class TestFindingEndpoints:
    """Test finding endpoints"""

    def test_finding_patch_by_id_unauthorized(self):
        response = client.patch("/findings/1", json={"status": "resolved"})
        assert response.status_code in [401, 403, 404]

    def test_finding_patch_by_id_invalid(self):
        response = client.patch("/findings/invalid", json={})
        assert response.status_code in [400, 404, 422]


# =============================================================================
# TOOL ENDPOINTS
# =============================================================================


class TestToolEndpoints:
    """Test tool execution endpoints"""

    def test_tools_get(self):
        response = client.get("/tools")
        assert response.status_code in [200, 401, 403]

    def test_tools_execute_post_valid_format(self, valid_tool_execute_data):
        response = client.post("/tools/execute", json=valid_tool_execute_data)
        assert response.status_code in [200, 401, 403, 422]

    def test_tools_execute_post_invalid_tool(self):
        response = client.post(
            "/tools/execute",
            json={"tool_name": "nonexistent_tool", "parameters": {}},
        )
        assert response.status_code in [401, 403, 404, 422]

    def test_tools_execute_post_missing_params(self):
        response = client.post("/tools/execute", json={"tool_name": "nmap"})
        assert response.status_code in [401, 403, 422]


# =============================================================================
# REPORT ENDPOINTS
# =============================================================================


class TestReportEndpoints:
    """Test report generation endpoints"""

    def test_reports_get_unauthorized(self):
        response = client.get("/reports")
        assert response.status_code in [401, 403]

    def test_reports_post_valid_format(self):
        response = client.post(
            "/reports", json={"scan_id": 1, "format": "pdf"}
        )
        assert response.status_code in [200, 201, 401, 403, 422]

    def test_reports_post_invalid_format(self):
        response = client.post("/reports", json={"format": "invalid"})
        assert response.status_code in [401, 403, 422]

    def test_report_download_get_unauthorized(self):
        response = client.get("/reports/1/download")
        assert response.status_code in [401, 403, 404]


# =============================================================================
# SCHEDULED SCAN ENDPOINTS
# =============================================================================


class TestScheduledScanEndpoints:
    """Test scheduled scan endpoints"""

    def test_schedules_get_unauthorized(self):
        response = client.get("/schedules")
        assert response.status_code in [401, 403]

    def test_schedules_post_valid_format(self, valid_schedule_data):
        response = client.post("/schedules", json=valid_schedule_data)
        assert response.status_code in [200, 201, 401, 403, 422]

    def test_schedules_post_invalid_frequency(self):
        response = client.post(
            "/schedules",
            json={
                "name": "Test",
                "target": "example.com",
                "scan_type": "port",
                "frequency": "invalid",
            },
        )
        assert response.status_code in [401, 403, 422]

    def test_schedule_get_by_id_unauthorized(self):
        response = client.get("/schedules/1")
        assert response.status_code in [401, 403, 404]

    def test_schedule_patch_by_id_unauthorized(self):
        response = client.patch("/schedules/1", json={"enabled": False})
        assert response.status_code in [401, 403, 404]

    def test_schedule_delete_by_id_unauthorized(self):
        response = client.delete("/schedules/1")
        assert response.status_code in [401, 403, 404]

    def test_schedule_run_post_unauthorized(self):
        response = client.post("/schedules/1/run")
        assert response.status_code in [401, 403, 404]


# =============================================================================
# STATS ENDPOINTS
# =============================================================================


class TestStatsEndpoints:
    """Test statistics endpoints"""

    def test_stats_overview_get(self):
        response = client.get("/stats/overview")
        assert response.status_code in [200, 401, 403]

    def test_stats_trends_get(self):
        response = client.get("/stats/trends")
        assert response.status_code in [200, 401, 403]

    def test_stats_severity_get(self):
        response = client.get("/stats/severity")
        assert response.status_code in [200, 401, 403]

    def test_stats_tools_get(self):
        response = client.get("/stats/tools")
        assert response.status_code in [200, 401, 403]


# =============================================================================
# NOTIFICATION ENDPOINTS
# =============================================================================


class TestNotificationEndpoints:
    """Test notification endpoints"""

    def test_notifications_slack_test_post_unauthorized(self):
        response = client.post("/notifications/slack/test")
        assert response.status_code in [401, 403]

    def test_notifications_slack_scan_complete_post_unauthorized(self):
        response = client.post(
            "/notifications/slack/scan-complete", json={"scan_id": 1}
        )
        assert response.status_code in [401, 403, 422]


# =============================================================================
# SETTINGS ENDPOINTS
# =============================================================================


class TestSettingsEndpoints:
    """Test settings endpoints"""

    def test_settings_slack_get_unauthorized(self):
        response = client.get("/settings/slack")
        assert response.status_code in [401, 403]

    def test_settings_slack_post_unauthorized(self):
        response = client.post("/settings/slack", json={"webhook_url": "test"})
        assert response.status_code in [401, 403, 422]

    def test_settings_jira_get_unauthorized(self):
        response = client.get("/settings/jira")
        assert response.status_code in [401, 403]


# =============================================================================
# ERROR HANDLING
# =============================================================================


class TestErrorHandling:
    """Test error responses"""

    def test_404_not_found(self):
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_405_method_not_allowed(self):
        response = client.post("/health")
        assert response.status_code == 405

    def test_422_validation_error(self):
        response = client.post("/auth/login", json={"invalid": "data"})
        assert response.status_code == 422

    def test_invalid_json_body(self):
        response = client.post(
            "/auth/login",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


# =============================================================================
# WEBSOCKET ENDPOINTS (Connection tests only)
# =============================================================================


class TestWebSocketEndpoints:
    """Test WebSocket endpoint existence"""

    def test_websocket_scan_endpoint_exists(self):
        routes = [
            r
            for r in app.routes
            if hasattr(r, "path") and r.path == "/ws/scans/{scan_id}"
        ]
        assert len(routes) > 0

    def test_websocket_notifications_endpoint_exists(self):
        routes = [
            r
            for r in app.routes
            if hasattr(r, "path") and r.path == "/ws/notifications"
        ]
        assert len(routes) > 0

    def test_websocket_client_endpoint_exists(self):
        routes = [
            r
            for r in app.routes
            if hasattr(r, "path") and r.path == "/ws/{client_id}"
        ]
        assert len(routes) > 0

    def test_websocket_agents_endpoint_exists(self):
        routes = [
            r
            for r in app.routes
            if hasattr(r, "path") and r.path == "/agents/ws"
        ]
        assert len(routes) > 0


# =============================================================================
# PARAMETERIZED TESTS
# =============================================================================


@pytest.mark.parametrize(
    "endpoint",
    [
        "/health",
        "/info",
        "/docs",
        "/openapi.json",
        "/csrf-token",
    ],
)
def test_public_endpoints(endpoint):
    """Test endpoints that should be publicly accessible"""
    response = client.get(endpoint)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "endpoint,method",
    [
        ("/auth/login", "post"),
        ("/auth/refresh", "post"),
        ("/auth/logout", "post"),
        ("/auth/logout-all", "post"),
    ],
)
def test_auth_endpoints_exist(endpoint, method):
    """Test auth endpoints exist and handle requests"""
    func = getattr(client, method)
    response = func(endpoint, json={} if method == "post" else None)
    assert response.status_code in [200, 401, 403, 422]


@pytest.mark.parametrize(
    "endpoint",
    [
        "/scans",
        "/tools",
        "/reports",
        "/schedules",
        "/stats/overview",
    ],
)
def test_api_endpoints_require_auth_or_work(endpoint):
    """Test API endpoints either work or require auth"""
    response = client.get(endpoint)
    assert response.status_code in [200, 401, 403]
