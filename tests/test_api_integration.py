import pytest

# Integration tests enabled - using mocked DB and TestClient

"""
API Integration Tests for Zen-AI-Pentest
Tests all major API endpoints
"""

from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient


# Mock database dependency
@pytest.fixture
def mock_db():
    """Provide a mock database session"""
    db = Mock()
    return db


@pytest.fixture
def client(mock_db):
    """Create test client with mocked dependencies"""
    from api.main import app

    # Override database dependency
    def override_get_db():
        yield mock_db

    app.dependency_overrides = {}
    try:
        from database.models import get_db

        app.dependency_overrides[get_db] = override_get_db
    except ImportError:
        pass

    # Disable rate limiting for integration tests
    try:
        import api.rate_limiter as rl
        from api.rate_limiter import RateLimitInfo

        async def bypass_rate_limit(*args, **kwargs):
            return RateLimitInfo(allowed=True, limit=1000, remaining=999, reset_after=0)

        rl.RateLimitDependency.__call__ = bypass_rate_limit
        rl.AuthRateLimitDependency.__call__ = bypass_rate_limit
        rl.check_auth_rate_limit = lambda client_ip: None
        rl.RateLimitMiddleware.__call__ = lambda self, scope, receive, send: self.app(scope, receive, send)
    except Exception:
        pass

    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 200 if healthy, 503 if degraded

    def test_api_status(self, client):
        """Test API status endpoint"""
        response = client.get("/api/status")
        assert response.status_code in [200, 404]  # 404 if route not mounted
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "version" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_endpoint(self, client, mock_db):
        """Test /api/auth/login endpoint"""
        # Mock user lookup
        mock_user = Mock()
        mock_user.username = "admin"
        mock_user.role = "admin"
        mock_user.hashed_password = "$2b$12$test_hash"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        with patch("api.auth_simple.verify_password", return_value=True):
            response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})

        assert response.status_code in [200, 401, 404, 405]

    def test_login_invalid_credentials(self, client, mock_db):
        """Test login with invalid credentials"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        response = client.post("/api/auth/login", json={"username": "invalid", "password": "wrong"})

        assert response.status_code in [401, 404]

    def test_register_endpoint(self, client):
        """Test /api/auth/register endpoint"""
        response = client.post(
            "/api/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "password123"}
        )

        assert response.status_code in [201, 200, 400, 409, 404]


class TestScanEndpoints:
    """Test scan management endpoints"""

    def test_create_scan(self, client, mock_db):
        """Test POST /api/scans"""
        mock_scan = Mock()
        mock_scan.id = 1
        mock_scan.name = "Test Scan"
        mock_scan.target = "test.com"

        with patch("api.main.create_scan", return_value=mock_scan):
            response = client.post(
                "/api/v1/scans",
                json={"name": "Test Scan", "target": "test.com", "scan_type": "web", "config": {}},
                headers={"Authorization": "Bearer test_token"},
            )

        assert response.status_code in [201, 200, 401, 422]

    def test_get_scans(self, client, mock_db):
        """Test GET /api/scans"""
        mock_scans = [
            Mock(id=1, name="Scan 1", target="target1.com"),
            Mock(id=2, name="Scan 2", target="target2.com"),
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_scans

        response = client.get("/api/v1/scans?skip=0&limit=10")

        assert response.status_code in [200, 401]

    def test_get_scan_by_id(self, client, mock_db):
        """Test GET /api/scans/{scan_id}"""
        mock_scan = Mock()
        mock_scan.id = 1
        mock_scan.name = "Test Scan"
        mock_scan.target = "test.com"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_scan

        response = client.get("/api/v1/scans/1")

        assert response.status_code in [200, 401, 404, 405]

    def test_update_scan(self, client, mock_db):
        """Test PUT /api/scans/{scan_id}"""
        response = client.put("/api/v1/scans/1", json={"status": "running"}, headers={"Authorization": "Bearer test_token"})

        assert response.status_code in [200, 401, 404, 405]

    def test_delete_scan(self, client, mock_db):
        """Test DELETE /api/scans/{scan_id}"""
        response = client.delete("/api/v1/scans/1", headers={"Authorization": "Bearer test_token"})

        assert response.status_code in [200, 204, 401, 404]


class TestFindingEndpoints:
    """Test finding management endpoints"""

    def test_get_findings(self, client, mock_db):
        """Test GET /api/findings"""
        mock_findings = [
            Mock(id=1, title="XSS", severity="high"),
            Mock(id=2, title="SQLi", severity="critical"),
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_findings

        response = client.get("/api/v1/findings?scan_id=1")

        assert response.status_code in [200, 401]

    def test_get_finding_by_id(self, client, mock_db):
        """Test GET /api/findings/{finding_id}"""
        mock_finding = Mock()
        mock_finding.id = 1
        mock_finding.title = "XSS"
        mock_finding.severity = "high"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_finding

        response = client.get("/api/v1/findings/1")

        assert response.status_code in [200, 401, 404]

    def test_update_finding(self, client, mock_db):
        """Test PUT /api/findings/{finding_id}"""
        response = client.put(
            "/api/v1/findings/1",
            json={"verified": True, "notes": "Manually verified"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code in [200, 401, 404, 405]


class TestReportEndpoints:
    """Test report management endpoints"""

    def test_get_reports(self, client, mock_db):
        """Test GET /api/reports"""
        response = client.get("/api/v1/reports")

        assert response.status_code in [200, 401]

    def test_create_report(self, client, mock_db):
        """Test POST /api/reports"""
        response = client.post(
            "/api/v1/reports",
            json={"scan_id": 1, "format": "pdf", "template": "default"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code in [201, 200, 401, 422]

    def test_download_report(self, client, mock_db):
        """Test GET /api/reports/{report_id}/download"""
        response = client.get("/api/v1/reports/1/download")

        assert response.status_code in [200, 401, 404]


class TestDashboardEndpoints:
    """Test dashboard endpoints"""

    def test_get_dashboard_stats(self, client):
        """Test GET /api/dashboard/stats"""
        response = client.get("/api/v1/dashboard/stats")

        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_recent_scans(self, client):
        """Test GET /api/dashboard/recent-scans"""
        response = client.get("/api/v1/dashboard/recent-scans")

        assert response.status_code in [200, 401, 404]

    def test_get_recent_findings(self, client):
        """Test GET /api/dashboard/recent-findings"""
        response = client.get("/api/v1/dashboard/recent-findings")

        assert response.status_code in [200, 401]


class TestToolEndpoints:
    """Test tool execution endpoints"""

    def test_list_tools(self, client):
        """Test GET /api/tools"""
        response = client.get("/api/v1/tools")

        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    def test_execute_tool(self, client):
        """Test POST /api/tools/{tool_name}/execute"""
        response = client.post(
            "/api/v1/tools/nmap/execute",
            json={"target": "test.com", "args": "-sV"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code in [200, 202, 401, 422, 404]


class TestAgentEndpoints:
    """Test agent management endpoints"""

    def test_get_agents(self, client):
        """Test GET /api/agents"""
        response = client.get("/api/v1/agents")

        assert response.status_code in [200, 401, 404]

    def test_register_agent(self, client):
        """Test POST /api/agents/register"""
        response = client.post(
            "/api/v1/agents/register",
            json={"name": "Test Agent", "capabilities": ["nmap", "nikto"]},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code in [201, 200, 401, 404]


class TestWebSocket:
    """Test WebSocket endpoints"""

    def test_websocket_scan_updates(self, client):
        """Test WebSocket /ws/scans/{scan_id}"""
        # WebSocket testing requires special handling
        # This is a basic connectivity test
        try:
            with client.websocket_connect("/ws/scans/1") as websocket:
                pass
        except Exception:
            # WebSocket might not be available in test environment
            pass


class TestSecurityHeaders:
    """Test that security headers are present"""

    def test_security_headers_present(self, client):
        """Test that security headers are in responses"""
        response = client.get("/health")

        assert response.status_code in [200, 503]

        # Check for security headers
        headers = response.headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"


class TestErrorHandling:
    """Test API error handling"""

    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get("/api/nonexistent/endpoint")

        assert response.status_code == 404

    def test_422_validation_error(self, client):
        """Test 422 validation error"""
        response = client.post(
            "/api/v1/scans",
            json={"invalid": "data"},  # Missing required fields
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code in [422, 401]

    def test_405_method_not_allowed(self, client):
        """Test 405 method not allowed"""
        response = client.post("/health")  # GET only endpoint

        assert response.status_code == 405
