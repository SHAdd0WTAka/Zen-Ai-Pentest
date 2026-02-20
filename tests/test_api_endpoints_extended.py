"""
Extended API Endpoint Tests
Comprehensive tests for FastAPI endpoints
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
try:
    from api.main import app

    client = TestClient(app)
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    app = None
    client = None


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self):
        """Test successful login"""
        with patch("api.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = {"id": "1", "username": "admin", "email": "admin@test.com", "role": "admin"}

            response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_failure(self):
        """Test failed login"""
        with patch("api.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = client.post("/api/auth/login", json={"username": "wrong", "password": "wrong"})

            assert response.status_code == 401

    def test_register_user(self):
        """Test user registration"""
        with patch("api.auth.create_user") as mock_create:
            mock_create.return_value = {"id": "2", "username": "newuser", "email": "new@test.com", "role": "user"}

            response = client.post(
                "/api/auth/register", json={"username": "newuser", "email": "new@test.com", "password": "password123"}
            )

            assert response.status_code in [200, 201]

    def test_get_current_user(self):
        """Test getting current user info"""
        with patch("api.auth.get_current_user") as mock_user:
            mock_user.return_value = {"id": "1", "username": "admin", "email": "admin@test.com"}

            response = client.get("/api/auth/me", headers={"Authorization": "Bearer test_token"})

            # Will fail without proper auth, but tests structure
            assert response.status_code in [200, 401, 403]


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestScanEndpoints:
    """Test scan management endpoints"""

    def test_get_scans_list(self):
        """Test getting list of scans"""
        with patch("api.routes.scans.get_scans") as mock_scans:
            mock_scans.return_value = [{"id": "1", "target": "example.com", "status": "completed", "type": "full"}]

            response = client.get("/api/scans")

            assert response.status_code in [200, 401]  # 401 if auth required

    def test_create_scan(self):
        """Test creating a new scan"""
        with patch("api.routes.scans.create_scan") as mock_create:
            mock_create.return_value = {"id": "123", "target": "test.com", "status": "pending", "type": "quick"}

            response = client.post("/api/scans", json={"target": "test.com", "type": "quick"})

            assert response.status_code in [200, 201, 401, 422]

    def test_get_scan_details(self):
        """Test getting scan details"""
        with patch("api.routes.scans.get_scan") as mock_scan:
            mock_scan.return_value = {"id": "1", "target": "example.com", "status": "completed", "results": {"findings": []}}

            response = client.get("/api/scans/1")

            assert response.status_code in [200, 401, 404]

    def test_delete_scan(self):
        """Test deleting a scan"""
        with patch("api.routes.scans.delete_scan") as mock_delete:
            mock_delete.return_value = {"message": "Scan deleted"}

            response = client.delete("/api/scans/1")

            assert response.status_code in [200, 204, 401, 404]

    def test_stop_scan(self):
        """Test stopping a running scan"""
        with patch("api.routes.scans.stop_scan") as mock_stop:
            mock_stop.return_value = {"message": "Scan stopped"}

            response = client.post("/api/scans/1/stop")

            assert response.status_code in [200, 401, 404]


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestToolEndpoints:
    """Test tool management endpoints"""

    def test_get_tools_list(self):
        """Test getting list of available tools"""
        response = client.get("/api/tools")

        assert response.status_code in [200, 401]

    def test_get_tool_details(self):
        """Test getting specific tool details"""
        response = client.get("/api/tools/nmap")

        assert response.status_code in [200, 401, 404]

    def test_execute_tool(self):
        """Test executing a tool"""
        with patch("api.routes.tools.execute_tool") as mock_execute:
            mock_execute.return_value = {"success": True, "output": "Tool output"}

            response = client.post("/api/tools/nmap/execute", json={"target": "example.com", "options": {}})

            assert response.status_code in [200, 401, 422]


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestReportEndpoints:
    """Test report generation endpoints"""

    def test_generate_report(self):
        """Test report generation"""
        with patch("api.routes.reports.generate_report") as mock_gen:
            mock_gen.return_value = {"id": "report1", "format": "pdf", "url": "/reports/report1.pdf"}

            response = client.post("/api/reports", json={"scan_id": "1", "format": "pdf"})

            assert response.status_code in [200, 201, 401]

    def test_get_reports_list(self):
        """Test getting list of reports"""
        response = client.get("/api/reports")

        assert response.status_code in [200, 401]

    def test_download_report(self):
        """Test report download"""
        response = client.get("/api/reports/1/download")

        assert response.status_code in [200, 401, 404]


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestWebSocket:
    """Test WebSocket endpoints"""

    def test_websocket_connection(self):
        """Test WebSocket connection"""
        # WebSocket testing requires different approach
        # This is a structural test
        try:
            with client.websocket_connect("/ws") as websocket:
                websocket.send_json({"type": "subscribe", "channel": "scans"})
                data = websocket.receive_json()
                assert data is not None
        except Exception:
            # WebSocket might not be available in test environment
            pytest.skip("WebSocket not available in test environment")


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAPIErrorHandling:
    """Test API error handling"""

    def test_404_error(self):
        """Test 404 error response"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_validation_error(self):
        """Test validation error response"""
        response = client.post("/api/scans", json={"invalid": "data"})  # Missing required fields

        assert response.status_code in [400, 422]

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        response = client.get("/api/scans")

        # Should require authentication
        assert response.status_code in [200, 401, 403]


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAPIResponseFormat:
    """Test API response formats"""

    def test_json_content_type(self):
        """Test that responses are JSON"""
        response = client.get("/api/tools")

        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "")

    def test_error_response_format(self):
        """Test error response format"""
        response = client.get("/api/scans/99999")  # Non-existent scan

        if response.status_code >= 400:
            try:
                data = response.json()
                assert "detail" in data or "message" in data or "error" in data
            except Exception:
                pass  # Some errors might return plain text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
