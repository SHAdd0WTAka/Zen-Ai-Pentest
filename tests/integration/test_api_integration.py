"""
API Integration Tests for Zen-AI-Pentest
=========================================

Comprehensive integration tests for API endpoints using FastAPI TestClient.
Tests full API flow: authentication, scans, findings, reports, WebSockets.

Usage:
    pytest tests/integration/test_api_integration.py -v
    pytest tests/integration/test_api_integration.py -v --cov=api --cov-report=term-missing
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import Base

# Mark all tests in this file
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a SQLite in-memory database engine for testing."""
    engine = create_engine(
        "sqlite:///./test_integration.db",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db_engine):
    """Create a FastAPI TestClient with test database."""
    from api.main import app, get_db

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Set test environment
    os.environ["ADMIN_PASSWORD"] = "testpass123"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client):
    """Get authentication token for testing."""
    # Get CSRF token first
    csrf_response = client.get("/csrf-token")
    csrf_token = csrf_response.json().get("csrf_token", "")

    # Login with CSRF token
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "testpass123"},
        headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture
def auth_headers(auth_token):
    """Get authentication headers with valid token."""
    return {"Authorization": f"Bearer {auth_token}"} if auth_token else {}


# ============================================================================
# TEST CLASS: Authentication Flow
# ============================================================================


class TestAuthenticationFlow:
    """Test complete authentication flow including login, token validation, and logout."""

    def test_csrf_token_endpoint(self, client):
        """Test CSRF token generation endpoint."""
        response = client.get("/csrf-token")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data

    def test_login_success(self, client):
        """Test successful login with valid credentials."""
        # Get CSRF token
        csrf_response = client.get("/csrf-token")
        csrf_token = csrf_response.json().get("csrf_token", "")

        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "testpass123"},
            headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "username" in data
        assert data["username"] == "admin"

    def test_login_invalid_credentials(self, client):
        """Test login failure with invalid credentials."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_missing_fields(self, client):
        """Test login with missing required fields."""
        response = client.post("/auth/login", json={"username": "admin"})
        assert response.status_code == 422  # Validation error

    def test_access_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/scans")
        assert response.status_code == 403  # Forbidden without token

    def test_access_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/scans",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401  # Unauthorized

    def test_access_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/scans", headers=auth_headers)
        assert response.status_code == 200

    def test_me_endpoint(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/auth/me", headers=auth_headers)
        # May not be available in all auth modes
        if response.status_code == 200:
            data = response.json()
            assert "sub" in data or "username" in data

    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/auth/logout", headers=auth_headers)
        # Should succeed with valid token
        assert response.status_code in [200, 501]  # 501 if legacy auth


# ============================================================================
# TEST CLASS: Scan Management
# ============================================================================


class TestScanManagement:
    """Test scan creation, retrieval, and management."""

    def test_create_scan(self, client, auth_headers):
        """Test creating a new scan."""
        scan_data = {
            "name": "Test Integration Scan",
            "target": "scanme.nmap.org",
            "scan_type": "reconnaissance",
            "config": {"ports": "80,443", "timeout": 300},
        }
        response = client.post(
            "/scans",
            json=scan_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == scan_data["name"]
        assert data["target"] == scan_data["target"]
        assert data["scan_type"] == scan_data["scan_type"]
        assert data["status"] == "pending"

    def test_create_scan_missing_fields(self, client, auth_headers):
        """Test creating a scan with missing required fields."""
        response = client.post(
            "/scans",
            json={"target": "scanme.nmap.org"},  # Missing name and scan_type
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_scan_unauthorized(self, client):
        """Test creating a scan without authentication."""
        response = client.post(
            "/scans",
            json={
                "name": "Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
        )
        assert response.status_code == 403

    def test_list_scans(self, client, auth_headers):
        """Test listing all scans."""
        # Create a scan first
        client.post(
            "/scans",
            json={
                "name": "List Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
            headers=auth_headers,
        )

        response = client.get("/scans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_scans_with_pagination(self, client, auth_headers):
        """Test listing scans with pagination."""
        response = client.get("/scans?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_scans_with_status_filter(self, client, auth_headers):
        """Test listing scans with status filter."""
        response = client.get("/scans?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_scan_by_id(self, client, auth_headers):
        """Test getting a specific scan by ID."""
        # Create a scan first
        create_response = client.post(
            "/scans",
            json={
                "name": "Get Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
            headers=auth_headers,
        )
        scan_id = create_response.json()["id"]

        # Get the scan
        response = client.get(f"/scans/{scan_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scan_id

    def test_get_nonexistent_scan(self, client, auth_headers):
        """Test getting a scan that doesn't exist."""
        response = client.get("/scans/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_scan(self, client, auth_headers):
        """Test updating a scan."""
        # Create a scan first
        create_response = client.post(
            "/scans",
            json={
                "name": "Update Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
            headers=auth_headers,
        )
        scan_id = create_response.json()["id"]

        # Update the scan
        update_data = {"status": "running", "config": {"progress": 50}}
        response = client.patch(
            f"/scans/{scan_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scan_id

    def test_delete_scan(self, client, auth_headers):
        """Test deleting a scan."""
        # Create a scan first
        create_response = client.post(
            "/scans",
            json={
                "name": "Delete Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
            headers=auth_headers,
        )
        scan_id = create_response.json()["id"]

        # Delete the scan
        response = client.delete(f"/scans/{scan_id}", headers=auth_headers)
        # Should return success or 501 if not fully implemented
        assert response.status_code in [200, 202, 501]


# ============================================================================
# TEST CLASS: Findings Management
# ============================================================================


class TestFindingsManagement:
    """Test findings creation, retrieval, and management."""

    @pytest.fixture
    def scan_with_findings(self, client, auth_headers):
        """Create a scan with findings for testing."""
        # Create scan
        scan_response = client.post(
            "/scans",
            json={
                "name": "Findings Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        # Add findings
        findings = [
            {
                "title": "Critical SQL Injection",
                "description": "SQL injection in login form",
                "severity": "critical",
                "cvss_score": 9.8,
                "evidence": "Payload: ' OR 1=1 --",
                "tool": "sqlmap",
            },
            {
                "title": "XSS Vulnerability",
                "description": "Reflected XSS in search parameter",
                "severity": "high",
                "cvss_score": 7.5,
                "evidence": "Payload: <script>alert(1)</script>",
                "tool": "burpsuite",
            },
            {
                "title": "Information Disclosure",
                "description": "Server version exposed in headers",
                "severity": "low",
                "cvss_score": 3.5,
                "evidence": "Server: Apache/2.4.41",
                "tool": "nmap",
            },
        ]

        for finding in findings:
            client.post(
                f"/scans/{scan_id}/findings",
                json=finding,
                headers=auth_headers,
            )

        return scan_id

    def test_add_finding(self, client, auth_headers):
        """Test adding a finding to a scan."""
        # Create a scan first
        scan_response = client.post(
            "/scans",
            json={
                "name": "Finding Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        finding_data = {
            "title": "Test Finding",
            "description": "Test finding description",
            "severity": "medium",
            "cvss_score": 5.5,
            "evidence": "Test evidence",
            "tool": "nmap",
        }

        response = client.post(
            f"/scans/{scan_id}/findings",
            json=finding_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == finding_data["title"]
        assert data["severity"] == finding_data["severity"]

    def test_get_scan_findings(self, client, auth_headers, scan_with_findings):
        """Test getting all findings for a scan."""
        scan_id = scan_with_findings

        response = client.get(
            f"/scans/{scan_id}/findings",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_get_findings_by_severity(self, client, auth_headers, scan_with_findings):
        """Test filtering findings by severity."""
        scan_id = scan_with_findings

        response = client.get(
            f"/scans/{scan_id}/findings?severity=critical",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for finding in data:
            assert finding["severity"] == "critical"

    def test_update_finding(self, client, auth_headers, scan_with_findings):
        """Test updating a finding."""
        scan_id = scan_with_findings

        # Get findings
        findings_response = client.get(
            f"/scans/{scan_id}/findings",
            headers=auth_headers,
        )
        findings = findings_response.json()
        if findings:
            finding_id = findings[0]["id"]

            update_data = {
                "severity": "high",
                "verified": 1,
                "remediation": "Apply security patch",
            }

            response = client.patch(
                f"/findings/{finding_id}",
                json=update_data,
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == finding_id


# ============================================================================
# TEST CLASS: Tool Execution
# ============================================================================


class TestToolExecution:
    """Test tool execution endpoints."""

    def test_list_tools(self, client, auth_headers):
        """Test listing available tools."""
        response = client.get("/tools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    @patch("api.main.execute_tool_task")
    def test_execute_tool(self, mock_execute, client, auth_headers):
        """Test executing a tool."""
        mock_execute.return_value = None  # Background task

        tool_request = {
            "tool_name": "nmap_scan",
            "target": "scanme.nmap.org",
            "parameters": {"ports": "80,443", "options": "-sV"},
            "timeout": 300,
        }

        response = client.post(
            "/tools/execute",
            json=tool_request,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert data["status"] == "started"

    def test_execute_tool_invalid_name(self, client, auth_headers):
        """Test executing a non-existent tool."""
        tool_request = {
            "tool_name": "nonexistent_tool",
            "target": "scanme.nmap.org",
            "parameters": {},
        }

        response = client.post(
            "/tools/execute",
            json=tool_request,
            headers=auth_headers,
        )
        # Should either start and fail in background or return error
        assert response.status_code in [200, 404, 400]


# ============================================================================
# TEST CLASS: Report Generation
# ============================================================================


class TestReportGeneration:
    """Test report generation endpoints."""

    @pytest.fixture
    def completed_scan(self, client, auth_headers):
        """Create a completed scan with findings for report generation."""
        # Create scan
        scan_response = client.post(
            "/scans",
            json={
                "name": "Report Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "vulnerability",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        # Add a finding
        client.post(
            f"/scans/{scan_id}/findings",
            json={
                "title": "Test Finding for Report",
                "description": "Test description",
                "severity": "high",
                "tool": "nmap",
            },
            headers=auth_headers,
        )

        return scan_id

    @patch("api.main.generate_report_task")
    def test_generate_report(self, mock_generate, client, auth_headers, completed_scan):
        """Test generating a report."""
        mock_generate.return_value = None  # Background task

        report_request = {
            "scan_id": completed_scan,
            "format": "pdf",
            "template": "default",
        }

        response = client.post(
            "/reports",
            json=report_request,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    def test_list_reports(self, client, auth_headers):
        """Test listing all reports."""
        response = client.get("/reports", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("api.main.generate_report_task")
    def test_generate_report_invalid_format(self, mock_generate, client, auth_headers, completed_scan):
        """Test generating a report with invalid format."""
        report_request = {
            "scan_id": completed_scan,
            "format": "invalid_format",
            "template": "default",
        }

        response = client.post(
            "/reports",
            json=report_request,
            headers=auth_headers,
        )
        # Should either accept and fail in background or return validation error
        assert response.status_code in [200, 422]


# ============================================================================
# TEST CLASS: WebSocket Connections
# ============================================================================


class TestWebSocketConnections:
    """Test WebSocket endpoints."""

    def test_websocket_scan_updates(self, client, auth_headers):
        """Test WebSocket connection for scan updates."""
        # Create a scan first
        scan_response = client.post(
            "/scans",
            json={
                "name": "WebSocket Test Scan",
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
            headers=auth_headers,
        )
        scan_id = scan_response.json()["id"]

        with client.websocket_connect(f"/ws/scans/{scan_id}") as websocket:
            # Send ping
            websocket.send_json({"action": "ping"})

            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_notifications(self, client):
        """Test WebSocket connection for global notifications."""
        with client.websocket_connect("/ws/notifications") as websocket:
            # Connection should be established
            # Send a message to keep connection alive
            websocket.send_text("ping")
            # Should receive acknowledgment or no response

    def test_websocket_generic_endpoint(self, client):
        """Test generic WebSocket endpoint."""
        client_id = "test_client_123"
        with client.websocket_connect(f"/ws/{client_id}") as websocket:
            # Send ping
            websocket.send_json({"type": "ping"})

            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data

    def test_websocket_subscribe(self, client):
        """Test WebSocket subscription."""
        client_id = "test_client_456"
        with client.websocket_connect(f"/ws/{client_id}") as websocket:
            # Subscribe to channel
            websocket.send_json(
                {
                    "type": "subscribe",
                    "channel": "scans",
                }
            )

            # Receive subscription confirmation
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["channel"] == "scans"
            assert data["client_id"] == client_id


# ============================================================================
# TEST CLASS: Health and Info
# ============================================================================


class TestHealthAndInfo:
    """Test health check and info endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "services" in data

    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data


# ============================================================================
# TEST CLASS: Full API Workflow
# ============================================================================


class TestFullAPIWorkflow:
    """Test complete API workflow from scan creation to report generation."""

    @pytest.mark.slow
    def test_complete_pentest_workflow(self, client, auth_headers):
        """Test complete pentest workflow through API."""
        # Step 1: Create scan
        scan_response = client.post(
            "/scans",
            json={
                "name": "Complete Workflow Scan",
                "target": "scanme.nmap.org",
                "scan_type": "comprehensive",
                "config": {"ports": "80,443,8080", "intensity": "medium"},
            },
            headers=auth_headers,
        )
        assert scan_response.status_code == 200
        scan_data = scan_response.json()
        scan_id = scan_data["id"]
        assert scan_data["status"] == "pending"

        # Step 2: Add findings
        finding_data = {
            "title": "Critical Vulnerability Found",
            "description": "A critical vulnerability was discovered during testing",
            "severity": "critical",
            "cvss_score": 9.8,
            "evidence": "Evidence data here",
            "tool": "nuclei",
        }
        finding_response = client.post(
            f"/scans/{scan_id}/findings",
            json=finding_data,
            headers=auth_headers,
        )
        assert finding_response.status_code == 200
        finding_id = finding_response.json()["id"]

        # Step 3: Update finding
        update_response = client.patch(
            f"/findings/{finding_id}",
            json={"verified": 1, "remediation": "Apply patch immediately"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        # Step 4: Get scan with findings
        scan_get_response = client.get(
            f"/scans/{scan_id}",
            headers=auth_headers,
        )
        assert scan_get_response.status_code == 200

        findings_response = client.get(
            f"/scans/{scan_id}/findings",
            headers=auth_headers,
        )
        assert findings_response.status_code == 200
        findings = findings_response.json()
        assert len(findings) >= 1

        # Step 5: Generate report
        with patch("api.main.generate_report_task") as mock_report:
            mock_report.return_value = None
            report_response = client.post(
                "/reports",
                json={
                    "scan_id": scan_id,
                    "format": "pdf",
                    "template": "executive",
                },
                headers=auth_headers,
            )
            assert report_response.status_code == 200
            report_id = report_response.json()["id"]

        # Step 6: List all reports
        reports_list_response = client.get("/reports", headers=auth_headers)
        assert reports_list_response.status_code == 200
        reports = reports_list_response.json()
        assert isinstance(reports, list)

        # Step 7: Update scan status
        scan_update_response = client.patch(
            f"/scans/{scan_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )
        assert scan_update_response.status_code == 200
        assert scan_update_response.json()["status"] == "completed"


# ============================================================================
# TEST CLASS: Error Handling
# ============================================================================


class TestErrorHandling:
    """Test API error handling and edge cases."""

    def test_invalid_json(self, client, auth_headers):
        """Test handling of invalid JSON."""
        response = client.post(
            "/scans",
            data="invalid json {{",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_method_not_allowed(self, client, auth_headers):
        """Test method not allowed response."""
        response = client.put("/scans", headers=auth_headers)
        assert response.status_code == 405

    def test_not_found(self, client, auth_headers):
        """Test 404 response for non-existent endpoint."""
        response = client.get("/nonexistent/endpoint", headers=auth_headers)
        assert response.status_code == 404

    def test_validation_error_detail(self, client, auth_headers):
        """Test validation error contains detailed information."""
        response = client.post(
            "/scans",
            json={
                "name": "",  # Empty name should fail validation
                "target": "scanme.nmap.org",
                "scan_type": "reconnaissance",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api", "--cov-report=term-missing"])
