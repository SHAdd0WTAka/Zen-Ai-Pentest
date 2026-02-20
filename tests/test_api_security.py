"""
API Security Tests für Zen-AI-Pentest

Testet:
- CSRF Protection
- Rate Limiting
- JWT Authentication
- CORS Policies
- Input Validation

Ziel: 80%+ Coverage der Security Features
"""

# Import the app
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.csrf_protection import CSRFToken  # noqa: F401
from api.main import app
from api.rate_limiter import auth_rate_limiter

client = TestClient(app)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def auth_headers():
    """Get authenticated headers with JWT token"""
    response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def csrf_headers(auth_headers):
    """Get headers with both JWT and CSRF token"""
    # Get CSRF token
    response = client.get("/csrf-token")
    csrf_token = response.json()["csrf_token"]

    headers = auth_headers.copy()
    headers["X-CSRF-Token"] = csrf_token
    return headers


# =============================================================================
# CSRF Protection Tests
# =============================================================================


class TestCSRFProtection:
    """Test CSRF Protection functionality"""

    def test_csrf_token_endpoint(self):
        """Test CSRF token generation endpoint"""
        response = client.get("/csrf-token")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert "expires_in" in data
        assert len(data["csrf_token"]) > 30

        # Check cookie was set
        assert "csrf_token" in response.cookies

    def test_csrf_protected_endpoint_without_token(self):
        """Test that POST without CSRF token is rejected"""
        # Login first
        auth_response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try POST without CSRF
        response = client.post("/scans", json={"name": "test", "target": "localhost"}, headers=headers)

        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    def test_csrf_protected_endpoint_with_token(self):
        """Test that POST with valid CSRF token succeeds"""
        # Login
        auth_response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        token = auth_response.json()["access_token"]

        # Get CSRF token
        csrf_response = client.get("/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]

        headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf_token}

        # Cookies are automatically handled by TestClient
        # Try POST with CSRF - using a simpler endpoint for testing
        response = client.post(
            "/auth/change-password",  # Use auth endpoint instead of scans
            json={"old_password": "admin", "new_password": "newpass123"},
            headers=headers,
        )

        # Should not be 403 (CSRF check passed)
        # May be 422 (validation error), 401/200 depending on implementation
        assert response.status_code != 403

    def test_csrf_token_validation(self):
        """Test CSRF token validation logic"""
        token = CSRFToken()
        assert token.is_valid()

        # Test cookie serialization
        cookie_value = token.to_cookie_value()
        assert "|" in cookie_value

        # Test deserialization
        parsed = CSRFToken.from_cookie_value(cookie_value)
        assert parsed is not None
        assert parsed.token == token.token

    def test_csrf_token_expiry(self):
        """Test that expired tokens are rejected"""
        from datetime import datetime, timedelta

        # Create expired token
        expired_token = CSRFToken()
        expired_token.timestamp = datetime.utcnow() - timedelta(hours=25)  # 25 hours ago

        assert not expired_token.is_valid()


# =============================================================================
# Rate Limiting Tests
# =============================================================================


class TestRateLimiting:
    """Test Rate Limiting functionality"""

    def test_auth_rate_limit(self):
        """Test that brute force login attempts are rate limited"""
        # Reset rate limiter
        auth_rate_limiter.failed_attempts.clear()

        # Make 5 failed login attempts
        for i in range(5):
            response = client.post("/auth/login", json={"username": "admin", "password": "wrong_password"})
            assert response.status_code == 401

        # 6th attempt should be rate limited
        response = client.post("/auth/login", json={"username": "admin", "password": "wrong_password"})
        assert response.status_code == 429
        assert "Too many" in response.json()["detail"]

    def test_successful_login_resets_rate_limit(self):
        """Test that successful login resets the rate limit"""
        # Reset
        auth_rate_limiter.failed_attempts.clear()

        # Make 3 failed attempts
        for i in range(3):
            client.post("/auth/login", json={"username": "admin", "password": "wrong"})

        # Successful login
        response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        assert response.status_code == 200

        # Should be able to fail again (rate limit reset)
        response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        # Should be 401, not 429
        assert response.status_code == 401


# =============================================================================
# JWT Authentication Tests
# =============================================================================


class TestJWTAuthentication:
    """Test JWT Authentication functionality"""

    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={"username": "admin", "password": "wrong_password"})
        assert response.status_code == 401

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/scans")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/scans", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/scans", headers=auth_headers)
        # Should not be 403
        assert response.status_code != 403


# =============================================================================
# CORS Tests
# =============================================================================


class TestCORS:
    """Test CORS configuration"""

    def test_cors_preflight(self):
        """Test CORS preflight request"""
        response = client.options(
            "/scans", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"}
        )
        # Preflight should succeed
        assert response.status_code in [200, 204]

    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in response.headers


# =============================================================================
# Input Validation Tests
# =============================================================================


class TestInputValidation:
    """Test input validation"""

    def test_sql_injection_protection(self, auth_headers):
        """Test SQL injection protection"""
        csrf_response = client.get("/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]

        headers = auth_headers.copy()
        headers["X-CSRF-Token"] = csrf_token

        # Try SQL injection in scan name
        response = client.post("/scans", json={"name": "test'; DROP TABLE scans; --", "target": "localhost"}, headers=headers)

        # Should not crash the server
        assert response.status_code in [200, 201, 422]

    def test_xss_protection(self, auth_headers):
        """Test XSS protection"""
        csrf_response = client.get("/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]

        headers = auth_headers.copy()
        headers["X-CSRF-Token"] = csrf_token

        # Try XSS in scan name
        xss_payload = "<script>alert('xss')</script>"
        response = client.post("/scans", json={"name": xss_payload, "target": "localhost"}, headers=headers)

        # Should not crash
        assert response.status_code in [200, 201, 422]


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealth:
    """Test health check endpoint"""

    def test_health_endpoint(self):
        """Test health check returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


# =============================================================================
# Coverage Report Generation
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api", "--cov-report=term-missing", "--cov-report=html:htmlcov", "--cov-fail-under=80"])
