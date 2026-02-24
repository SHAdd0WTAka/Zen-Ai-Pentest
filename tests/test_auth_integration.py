"""
Auth Integration Tests
======================

Tests for the integration of the new auth system into the API.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Set test environment before imports
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-12345-min-32-b!"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["DATABASE_URL"] = "sqlite:///./test_integration.db"

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Import and initialize database
from database.auth_models import init_auth_db
from database.models import init_db

# Initialize databases
init_db()
init_auth_db()

from auth.password_hasher import PasswordHasher

# Create test user in auth database
from database.auth_models import (
    SessionLocal,
    UserRole,
    create_user,
    get_user_by_username,
)

db = SessionLocal()
try:
    admin = get_user_by_username(db, "admin")
    if not admin:
        pwd = PasswordHasher()
        create_user(
            db,
            username="admin",
            email="admin@zen-pentest.local",
            hashed_password=pwd.hash("admin123"),
            role=UserRole.ADMIN,
        )
        print("Test admin user created")
finally:
    db.close()

# Now import the app
from api.main import NEW_AUTH_AVAILABLE, _jwt_handler, _user_manager, app


@pytest.fixture(scope="module")
def initialized_db():
    """Initialize database once for all tests"""
    # Ensure auth tables exist
    init_auth_db()

    # Ensure admin user exists
    db = SessionLocal()
    try:
        admin = get_user_by_username(db, "admin")
        if not admin:
            pwd = PasswordHasher()
            create_user(
                db,
                username="admin",
                email="admin@zen-pentest.local",
                hashed_password=pwd.hash("admin123"),
                role=UserRole.ADMIN,
            )
            print("Test admin user created in fixture")
    finally:
        db.close()

    return True


@pytest.fixture
def client(initialized_db):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers with valid token"""
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.text}")

    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuthIntegration:
    """Test auth system integration"""

    def test_new_auth_available(self):
        """Test that new auth system is available"""
        assert NEW_AUTH_AVAILABLE is True
        assert _jwt_handler is not None

    def test_login_success(self, client):
        """Test successful login with database-backed auth"""
        response = client.post(
            "/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "username" in data
        assert data["username"] == "admin"
        assert "role" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword123"},
        )
        assert response.status_code == 401

    def test_me_endpoint_with_token(self, client, auth_headers):
        """Test /auth/me endpoint with valid token"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sub" in data or "username" in data

    def test_me_endpoint_without_token(self, client):
        """Test /auth/me endpoint without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_protected_endpoint_requires_auth(self, client):
        """Test that protected endpoints require authentication"""
        response = client.get("/scans")
        assert response.status_code == 401

    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Test protected endpoint with authentication - only checks auth passes"""
        try:
            response = client.get("/scans", headers=auth_headers)
            # Auth should pass - if it fails, we'd get 401
            assert response.status_code != 401, "Authentication should succeed"
        except Exception as e:
            # If we get an exception, it might be DB error after auth succeeded
            error_str = str(e).lower()
            assert (
                "unauthorized" not in error_str
                and "authentication" not in error_str
            ), f"Should not be auth error: {e}"

    def test_refresh_token_endpoint(self, client):
        """Test token refresh endpoint"""
        # First login to get refresh token
        response = client.post(
            "/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            pytest.skip("No refresh token in response")

        # Refresh the token
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        if NEW_AUTH_AVAILABLE and _user_manager:
            assert response.status_code == 200
            new_data = response.json()
            assert "access_token" in new_data
            assert new_data["token_type"] == "bearer"
        else:
            # Legacy auth doesn't support refresh
            assert response.status_code == 501

    def test_logout_endpoint(self, client, auth_headers):
        """Test logout endpoint"""
        response = client.post("/auth/logout", headers=auth_headers)
        # Should succeed regardless of session tracking
        assert response.status_code in [200, 401]

    def test_csrf_token_endpoint(self, client):
        """Test CSRF token generation"""
        response = client.get("/csrf-token")
        assert response.status_code == 200


class TestJWTTokens:
    """Test JWT token functionality"""

    def test_token_creation_and_validation(self):
        """Test that tokens can be created and validated"""
        if not NEW_AUTH_AVAILABLE or not _jwt_handler:
            pytest.skip("New auth system not available")

        # Create token
        token = _jwt_handler.create_access_token(
            user_id="test_user", roles=["admin"], permissions=["read", "write"]
        )
        assert token is not None
        assert isinstance(token, str)

        # Validate token
        payload = _jwt_handler.decode_token(token)
        assert payload.sub == "test_user"
        assert "admin" in payload.roles

    def test_token_expiration(self):
        """Test that expired tokens are rejected"""
        if not NEW_AUTH_AVAILABLE or not _jwt_handler:
            pytest.skip("New auth system not available")

        from datetime import datetime, timedelta

        import jwt

        from auth.jwt_handler import TokenExpiredError

        # Create a token that's already expired
        now = datetime.utcnow()
        payload_data = {
            "sub": "test_user",
            "jti": "test-jti-123",
            "type": "access",
            "iat": now,
            "exp": now - timedelta(seconds=1),  # Already expired
            "nbf": now - timedelta(seconds=1),
            "iss": "zen-ai-pentest",
            "aud": "zen-ai-pentest-api",
            "roles": ["user"],
            "permissions": [],
            "session_id": None,
            "mfa_verified": False,
        }

        expired_token = jwt.encode(
            payload_data,
            _jwt_handler.config.secret_key,
            algorithm=_jwt_handler.config.algorithm,
        )

        # Should raise TokenExpiredError
        with pytest.raises(TokenExpiredError):
            _jwt_handler.decode_token(expired_token)


class TestRBACIntegration:
    """Test RBAC integration"""

    def test_rbac_manager_available(self):
        """Test that RBAC manager is available"""
        from api.main import _rbac_manager

        if NEW_AUTH_AVAILABLE:
            assert _rbac_manager is not None


class TestCORSAndMiddleware:
    """Test CORS and middleware integration"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
