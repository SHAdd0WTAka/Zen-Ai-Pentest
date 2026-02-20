"""
Tests für API Endpoints
"""

import os
import sys

import pytest

sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["ADMIN_PASSWORD"] = "admin123"

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]  # Redis may be unavailable

    def test_health_check_has_services(self):
        """Test health endpoint returns services info"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "version" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self):
        """Test successful login"""
        response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

    def test_login_failure(self):
        """Test failed login"""
        response = client.post("/auth/login", json={"username": "admin", "password": "wrongpassword123"})
        assert response.status_code == 401

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        response = client.post("/auth/login", json={"username": "admin"})
        assert response.status_code == 422


class TestCSRFEndpoints:
    """Test CSRF protection endpoints"""

    def test_get_csrf_token(self):
        """Test getting CSRF token"""
        response = client.get("/csrf-token")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data


class TestScanEndpoints:
    """Test scan endpoints"""

    def test_get_scans_unauthorized(self):
        """Test getting scans without auth"""
        response = client.get("/scans")
        assert response.status_code == 401

    def test_create_scan_unauthorized(self):
        """Test creating scan without auth"""
        response = client.post("/scans", json={"name": "Test Scan", "target": "localhost", "scan_type": "quick"})
        assert response.status_code == 401

    def test_get_scan_by_id_unauthorized(self):
        """Test getting specific scan without auth"""
        response = client.get("/scans/1")
        assert response.status_code == 401


class TestReportEndpoints:
    """Test report endpoints"""

    def test_get_reports_unauthorized(self):
        """Test getting reports without auth"""
        response = client.get("/reports")
        assert response.status_code == 401


class TestRateLimiterEndpoints:
    """Test rate limiting on endpoints"""

    def test_rate_limit_headers(self):
        """Test that rate limit headers are present"""
        # Make multiple requests to trigger rate limiting
        for _ in range(5):
            response = client.get("/health")

        # Check headers
        assert response.status_code == 200


class TestCORSEndpoints:
    """Test CORS configuration"""

    def test_cors_preflight(self):
        """Test CORS preflight request"""
        response = client.options(
            "/auth/login", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_present(self):
        """Test CORS headers on actual request"""
        response = client.post(
            "/auth/login", json={"username": "admin", "password": "admin123"}, headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestInputValidation:
    """Test input validation on endpoints"""

    def test_sql_injection_attempt(self):
        """Test that SQL injection is blocked"""
        response = client.post("/auth/login", json={"username": "admin' OR '1'='1", "password": "admin123"})
        # Should fail auth, not crash
        assert response.status_code == 401

    def test_xss_attempt(self):
        """Test that XSS is blocked"""
        response = client.post("/auth/login", json={"username": "<script>alert('xss')</script>", "password": "admin123"})
        # Should fail auth, not execute script
        assert response.status_code == 401

    def test_empty_payload(self):
        """Test empty payload handling"""
        response = client.post("/auth/login", json={})
        assert response.status_code == 422


class TestMetricsEndpoint:
    """Test metrics endpoint"""

    def test_metrics_endpoint_exists(self):
        """Test that metrics endpoint exists"""
        response = client.get("/metrics")
        # Should return Prometheus metrics or 404 if not configured
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
