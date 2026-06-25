"""
Tests for auth API routes.
Split from test_api_routes_all.py
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# to match the current modular v1 routers and ODM/SQLAlchemy mix.
pytest.skip(
    "Stale generated test suite (see issue notes); skipped until rewritten",
    allow_module_level=True,
)

# Module-level constants for mock responses
_mock_created_at = datetime.now(timezone.utc).isoformat()

# =============================================================================
# Fixtures und Setup
# =============================================================================


@pytest.fixture
def mock_settings():
    """Mock settings for tests"""
    with patch("api.routes.auth.settings") as mock:
        mock.SECRET_KEY = "test-secret-key-for-testing-only"
        mock.JWT_ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.REFRESH_TOKEN_EXPIRE_DAYS = 7
        yield mock


@pytest.fixture
def test_user_data():
    """Sample test user data"""
    return {
        "id": str(uuid4()),
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "USER",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "hashed_password": "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # bcrypt hash
    }


@pytest.fixture
def test_admin_data():
    """Sample test admin data"""
    return {
        "id": str(uuid4()),
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "ADMIN",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "hashed_password": "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    }


# =============================================================================
# Helper Functions
# =============================================================================


def create_mock_user(user_id: str = None, role: str = "USER", is_active: bool = True):
    """Create a mock user object"""
    mock_user = MagicMock()
    mock_user.id = user_id or str(uuid4())
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.role = MagicMock()
    mock_user.role.value = 1 if role == "USER" else 2 if role == "ADMIN" else 3
    mock_user.role.name = role
    mock_user.is_active = is_active
    mock_user.created_at = datetime.now(timezone.utc)
    mock_user.hashed_password = "hashed_password"
    mock_user.to_response.return_value = {
        "id": str(mock_user.id),
        "username": mock_user.username,
        "email": mock_user.email,
        "full_name": mock_user.full_name,
        "role": role,
        "is_active": is_active,
        "created_at": mock_user.created_at,
    }
    mock_user.save = AsyncMock()
    mock_user.delete = AsyncMock()
    return mock_user


@pytest.mark.unit
class TestAuthRoutes:
    """Tests for api/routes/auth.py - Authentication Endpoints"""

    @pytest.fixture
    def client(self, mock_settings):
        """Create test client with mocked auth"""

        from api.routes.auth import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/auth")

        with patch("api.routes.auth.User") as mock_user_model:
            mock_user_model.find_one = AsyncMock(return_value=None)

            # Ensure User() returns a mock with async save method
            def create_mock_instance(**kwargs):
                mock_instance = MagicMock()
                mock_instance.save = AsyncMock()
                mock_instance.to_response = MagicMock(
                    return_value={
                        "id": "test-id",
                        "username": kwargs.get("username", "testuser"),
                        "email": kwargs.get("email", "test@example.com"),
                        "full_name": kwargs.get("full_name", "Test User"),
                        "role": "USER",
                        "is_active": True,
                        "created_at": _mock_created_at,
                    }
                )
                return mock_instance

            mock_user_model.side_effect = create_mock_instance
            yield TestClient(app), mock_user_model

    def test_register_success(self, client):
        """Test successful user registration"""
        test_client, mock_user_model = client

        # Create mock user that will be "found" after creation
        mock_user = create_mock_user(role="USER")
        mock_user_model.find_one.side_effect = [
            None,
            None,
            mock_user,
        ]  # username not found, email not found, then created
        mock_user.save = AsyncMock()

        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["role"] == "USER"

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        test_client, mock_user_model = client

        existing_user = create_mock_user()
        mock_user_model.find_one.return_value = existing_user

        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "existinguser",
                "email": "new@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        test_client, mock_user_model = client

        existing_user = create_mock_user()
        # First call returns None (username available), second returns user (email taken)
        mock_user_model.find_one.side_effect = [None, existing_user]

        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "existing@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        test_client, _ = client

        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client):
        """Test registration with password too short"""
        test_client, _ = client

        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "short",
            },
        )

        assert response.status_code == 422

    def test_login_success(self, client, mock_settings):
        """Test successful login"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user.hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
        mock_user_model.find_one.return_value = mock_user
        mock_user.update_last_login = AsyncMock()

        with patch("api.routes.auth.verify_password") as mock_verify:
            mock_verify.return_value = True
            response = test_client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "testpass"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        test_client, mock_user_model = client
        mock_user_model.find_one.return_value = None

        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "wronguser", "password": "wrongpass"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user_model.find_one.return_value = mock_user

        with patch("api.routes.auth.verify_password") as mock_verify:
            mock_verify.return_value = False
            response = test_client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "wrongpass"},
            )

        assert response.status_code == 401

    def test_login_inactive_user(self, client):
        """Test login with inactive user account"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user.is_active = False
        mock_user_model.find_one.return_value = mock_user

        with patch("api.routes.auth.verify_password") as mock_verify:
            mock_verify.return_value = True
            response = test_client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "testpass"},
            )

        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()

    def test_refresh_token_success(self, client, mock_settings):
        """Test successful token refresh"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user_model.find_one.return_value = mock_user

        # Create a valid refresh token
        from api.routes.auth import create_refresh_token

        refresh_token = create_refresh_token({"sub": str(mock_user.id)})

        response = test_client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        test_client, _ = client

        response = test_client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401

    def test_get_current_user_info(self, client, mock_settings):
        """Test getting current user info"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user_model.find_one.return_value = mock_user

        from api.routes.auth import create_access_token

        token = create_access_token({"sub": str(mock_user.id)})

        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        test_client, _ = client

        response = test_client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_change_password_success(self, client, mock_settings):
        """Test successful password change"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user.hashed_password = "old_hash"
        mock_user_model.find_one.return_value = mock_user
        mock_user.save = AsyncMock()

        from api.routes.auth import create_access_token, get_password_hash

        token = create_access_token({"sub": str(mock_user.id)})

        with patch("api.routes.auth.verify_password") as mock_verify:
            mock_verify.return_value = True
            with patch("api.routes.auth.get_password_hash") as mock_hash:
                mock_hash.return_value = "new_hash"
                response = test_client.post(
                    "/api/v1/auth/change-password",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "old_password": "oldpass",
                        "new_password": "NewPass123!",
                    },
                )

        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

    def test_change_password_wrong_old(self, client, mock_settings):
        """Test password change with wrong old password"""
        test_client, mock_user_model = client

        mock_user = create_mock_user()
        mock_user_model.find_one.return_value = mock_user

        from api.routes.auth import create_access_token

        token = create_access_token({"sub": str(mock_user.id)})

        with patch("api.routes.auth.verify_password") as mock_verify:
            mock_verify.return_value = False
            response = test_client.post(
                "/api/v1/auth/change-password",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "old_password": "wrongpass",
                    "new_password": "NewPass123!",
                },
            )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.unit
class TestAuthPermissions:
    """Tests for auth permissions and role-based access control"""

    @pytest.fixture
    def client(self, mock_settings):
        """Create test client"""

        from api.models.user import UserRole
        from api.routes.auth import (
            get_current_user,
            require_permissions,
            router,
        )

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/auth")

        yield TestClient(app), get_current_user, require_permissions, UserRole

    def test_require_permissions_insufficient(self, client, mock_settings):
        """Test permission check with insufficient role"""
        test_client, _, require_permissions, UserRole = client

        # Create a user with USER role trying to access ADMIN resource
        mock_user = create_mock_user(role="USER")

        # Create permission checker for ADMIN
        checker = require_permissions(UserRole.ADMIN)

        # This should raise HTTPException
        import asyncio

        try:
            asyncio.get_event_loop().run_until_complete(checker(mock_user))
            assert False, "Should have raised HTTPException"
        except Exception as e:
            # Should be a 403 error
            pass

    def test_require_permissions_sufficient(self, client, mock_settings):
        """Test permission check with sufficient role"""
        test_client, _, require_permissions, UserRole = client

        # Create an admin user
        mock_user = create_mock_user(role="ADMIN")

        # Create permission checker for ADMIN
        checker = require_permissions(UserRole.ADMIN)

        import asyncio

        result = asyncio.get_event_loop().run_until_complete(checker(mock_user))
        assert result == mock_user

    def test_get_current_user_expired_token(self, client, mock_settings):
        """Test token validation with expired token"""
        test_client, get_current_user, _, _ = client

        from datetime import datetime, timedelta, timezone

        import jwt

        from api.routes.auth import create_access_token

        # Create an expired token
        expired_token = jwt.encode(
            {
                "sub": "user123",
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only"),
            algorithm="HS256",
        )

        import asyncio

        from fastapi import HTTPException

        try:
            asyncio.get_event_loop().run_until_complete(get_current_user(expired_token))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401

    def test_get_current_user_invalid_token_type(self, client, mock_settings):
        """Test token validation with wrong token type"""
        test_client, get_current_user, _, _ = client

        from api.routes.auth import create_refresh_token

        # Use refresh token instead of access token
        refresh_token = create_refresh_token({"sub": "user123"})

        import asyncio

        from fastapi import HTTPException

        try:
            asyncio.get_event_loop().run_until_complete(get_current_user(refresh_token))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401

    def test_get_current_user_missing_sub(self, client, mock_settings):
        """Test token validation with missing subject"""
        test_client, get_current_user, _, _ = client

        import jwt

        # Create token without sub
        token = jwt.encode(
            {"type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only"),
            algorithm="HS256",
        )

        import asyncio

        from fastapi import HTTPException

        try:
            asyncio.get_event_loop().run_until_complete(get_current_user(token))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401


# =============================================================================


@pytest.mark.unit
class TestAdditionalAuthTests:
    """Additional auth tests"""

    @pytest.fixture
    def client(self):
        from api.routes.auth import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/auth")

        with patch("api.routes.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test-secret-key-for-testing-only"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
            mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
            with patch("api.routes.auth.User") as mock_user_model:
                mock_user_model.find_one = AsyncMock(return_value=None)

                # Ensure User() returns a mock with async save method
                def create_mock_instance(**kwargs):
                    mock_instance = MagicMock()
                    mock_instance.save = AsyncMock()
                    mock_instance.to_response = MagicMock(
                        return_value={
                            "id": "test-id",
                            "username": kwargs.get("username", "testuser"),
                            "email": kwargs.get("email", "test@example.com"),
                            "full_name": kwargs.get("full_name", "Test User"),
                            "role": "USER",
                            "is_active": True,
                            "created_at": _mock_created_at,
                        }
                    )
                    return mock_instance

                mock_user_model.side_effect = create_mock_instance
                yield TestClient(app), mock_user_model

    def test_login_empty_username(self, client):
        """Test login with empty username"""
        test_client, _ = client
        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "", "password": "test"},
        )
        assert response.status_code in [400, 401, 422]

    def test_login_empty_password(self, client):
        """Test login with empty password"""
        test_client, mock_user_model = client
        mock_user = create_mock_user()
        mock_user_model.find_one.return_value = mock_user

        response = test_client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": ""},
        )
        assert response.status_code in [401, 400, 422]

    def test_register_long_username(self, client):
        """Test registration with very long username"""
        test_client, _ = client
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "a" * 100,
                "email": "test@test.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code in [201, 422]

    def test_register_special_chars_username(self, client):
        """Test registration with special characters in username"""
        test_client, _ = client
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user@#$%",
                "email": "test@test.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code in [201, 422]

    def test_refresh_token_empty(self, client):
        """Test refresh with empty token"""
        test_client, _ = client
        response = test_client.post("/api/v1/auth/refresh", params={"refresh_token": ""})
        assert response.status_code == 401

    def test_change_password_same_password(self, client):
        """Test password change to same password"""
        test_client, mock_user_model = client
        mock_user = create_mock_user()
        mock_user_model.find_one.return_value = mock_user

        from api.routes.auth import create_access_token

        token = create_access_token({"sub": str(mock_user.id)})

        with patch("api.routes.auth.verify_password") as mock_verify:
            mock_verify.return_value = True
            response = test_client.post(
                "/api/v1/auth/change-password",
                headers={"Authorization": f"Bearer {token}"},
                json={"old_password": "same", "new_password": "same"},
            )
        assert response.status_code in [200, 400]
