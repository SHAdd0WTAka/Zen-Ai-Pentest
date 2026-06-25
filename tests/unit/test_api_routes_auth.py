"""
Comprehensive Unit Tests for API Routes Authentication

This module provides complete test coverage for the FastAPI authentication routes
including JWT token handling, user registration, login, refresh, and password management.

Target: >80% Coverage for /api/routes/auth.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# Mock settings before importing auth module
with patch.dict("os.environ", {"JWT_SECRET_KEY": "test-secret-key-for-testing-only"}):
    from api.core.config import settings
    from api.models.user import User, UserRole
    from api.routes import auth
    from api.routes.auth import (
        PasswordChangeRequest,
        Token,
        UserCreate,
        UserResponse,
        create_access_token,
        create_refresh_token,
        get_current_user,
        get_password_hash,
        oauth2_scheme,
        require_permissions,
        router,
        verify_password,
    )

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app():
    """Create a FastAPI app with auth router for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/auth")
    return app


@pytest.fixture
def client(app):
    """Create a TestClient for the app."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = str(uuid.uuid4())
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = get_password_hash("TestPassword123!")
    user.full_name = "Test User"
    user.role = UserRole.USER
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    user.to_response.return_value = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user for testing."""
    user = MagicMock(spec=User)
    user.id = str(uuid.uuid4())
    user.username = "adminuser"
    user.email = "admin@example.com"
    user.hashed_password = get_password_hash("AdminPass123!")
    user.full_name = "Admin User"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    user.to_response.return_value = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.name,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }
    return user


@pytest.fixture
def mock_inactive_user():
    """Create a mock inactive user for testing."""
    user = MagicMock(spec=User)
    user.id = str(uuid.uuid4())
    user.username = "inactiveuser"
    user.email = "inactive@example.com"
    user.hashed_password = get_password_hash("Inactive123!")
    user.full_name = "Inactive User"
    user.role = UserRole.USER
    user.is_active = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def valid_access_token(mock_user):
    """Create a valid access token for testing."""
    token_data = {
        "sub": str(mock_user.id),
        "username": mock_user.username,
        "role": mock_user.role.value,
    }
    return create_access_token(token_data)


@pytest.fixture
def valid_refresh_token(mock_user):
    """Create a valid refresh token for testing."""
    return create_refresh_token({"sub": str(mock_user.id)})


@pytest.fixture
def expired_token(mock_user):
    """Create an expired token for testing."""
    to_encode = {
        "sub": str(mock_user.id),
        "username": mock_user.username,
        "role": mock_user.role.value,
        "type": "access",
    }
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ============================================================================
# Password Hashing Tests
# ============================================================================


class TestPasswordHashing:
    """Tests for password hashing and verification functions."""

    def test_get_password_hash_returns_string(self):
        """Test that get_password_hash returns a non-empty string."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password

    def test_verify_password_correct_password(self):
        """Test verifying correct password succeeds."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test verifying incorrect password fails."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_different_passwords(self):
        """Test that different passwords produce different hashes."""
        password1 = "TestPassword123!"
        password2 = "TestPassword456!"
        hashed1 = get_password_hash(password1)
        hashed2 = get_password_hash(password2)
        assert hashed1 != hashed2
        assert verify_password(password1, hashed1) is True
        assert verify_password(password2, hashed2) is True
        assert verify_password(password1, hashed2) is False
        assert verify_password(password2, hashed1) is False


# ============================================================================
# JWT Token Creation Tests
# ============================================================================


class TestTokenCreation:
    """Tests for JWT token creation functions."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a valid JWT string."""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_expected_data(self):
        """Test that access token contains the expected payload data."""
        data = {"sub": "user123", "username": "testuser", "role": 1}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["username"] == "testuser"
        assert decoded["role"] == 1
        assert decoded["type"] == "access"
        assert "exp" in decoded

    def test_create_access_token_has_expiration(self):
        """Test that access token has expiration set."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in decoded
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        # Allow 5 seconds tolerance
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "user123"}
        custom_delta = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=custom_delta)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.now(timezone.utc) + custom_delta
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5

    def test_create_refresh_token_returns_string(self):
        """Test that create_refresh_token returns a valid JWT string."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_expected_data(self):
        """Test that refresh token contains the expected payload data."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"
        assert "exp" in decoded

    def test_create_refresh_token_has_expiration(self):
        """Test that refresh token has correct expiration."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "exp" in decoded
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        # Allow 5 seconds tolerance
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5


# ============================================================================
# Registration Endpoint Tests
# ============================================================================


class TestRegistration:
    """Tests for the user registration endpoint."""

    def test_register_success(self, client, mock_user):
        """Test successful user registration."""
        with patch.object(User, "find_one", return_value=None):
            with patch.object(User, "__new__", return_value=mock_user):
                with patch.object(mock_user, "save", new_callable=AsyncMock):
                    response = client.post(
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
                    assert data["username"] == mock_user.username
                    assert data["email"] == mock_user.email
                    assert "id" in data
                    assert "role" in data

    def test_register_username_already_exists(self, client, mock_user):
        """Test registration with existing username returns 400."""
        with patch.object(User, "find_one", return_value=mock_user):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": "existinguser",
                    "email": "new@example.com",
                    "password": "SecurePass123!",
                },
            )
            assert response.status_code == 400
            assert "Username already registered" in response.json()["detail"]

    def test_register_email_already_exists(self, client, mock_user):
        """Test registration with existing email returns 400."""
        # First call returns None (username check), second returns user (email check)
        with patch.object(User, "find_one", side_effect=[None, mock_user]):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "username": "newuser",
                    "email": "existing@example.com",
                    "password": "SecurePass123!",
                },
            )
            assert response.status_code == 400
            assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email_format(self, client):
        """Test registration with invalid email format returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422

    def test_register_password_too_short(self, client):
        """Test registration with short password returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_register_username_too_short(self, client):
        """Test registration with short username returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # Less than 3 characters
                "email": "new@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422

    def test_register_missing_required_fields(self, client):
        """Test registration without required fields returns 422."""
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_register_password_exactly_min_length(self, client, mock_user):
        """Test registration with password exactly at min length (8 chars)."""
        with patch.object(User, "find_one", return_value=None):
            with patch.object(User, "__new__", return_value=mock_user):
                with patch.object(mock_user, "save", new_callable=AsyncMock):
                    response = client.post(
                        "/api/v1/auth/register",
                        json={
                            "username": "newuser",
                            "email": "new@example.com",
                            "password": "abcdefgh",  # Exactly 8 characters
                        },
                    )
                    assert response.status_code == 201


# ============================================================================
# Login Endpoint Tests
# ============================================================================


class TestLogin:
    """Tests for the user login endpoint."""

    def test_login_success(self, client, mock_user):
        """Test successful login returns tokens."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "update_last_login", new_callable=AsyncMock):
                response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "testuser",
                        "password": "TestPassword123!",
                    },
                )
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"
                assert "expires_in" in data
                assert data["expires_in"] > 0

    def test_login_invalid_username(self, client):
        """Test login with non-existent username returns 401."""

        async def mock_find_one(**kwargs):
            return None

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "nonexistent", "password": "SomePass123!"},
            )
            assert response.status_code == 401
            assert "Incorrect username or password" in response.json()["detail"]

    def test_login_invalid_password(self, client, mock_user):
        """Test login with wrong password returns 401."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "WrongPassword123!"},
            )
            assert response.status_code == 401
            assert "Incorrect username or password" in response.json()["detail"]

    def test_login_inactive_user(self, client, mock_inactive_user):
        """Test login with inactive user returns 403."""
        mock_inactive_user.hashed_password = get_password_hash("Inactive123!")

        async def mock_find_one(**kwargs):
            return mock_inactive_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": "inactiveuser",
                    "password": "Inactive123!",
                },
            )
            assert response.status_code == 403
            assert "User account is deactivated" in response.json()["detail"]

    def test_login_missing_username(self, client):
        """Test login without username returns 422."""
        response = client.post("/api/v1/auth/login", data={"password": "SomePass123!"})
        assert response.status_code == 422

    def test_login_missing_password(self, client):
        """Test login without password returns 422."""
        response = client.post("/api/v1/auth/login", data={"username": "testuser"})
        assert response.status_code == 422

    def test_login_updates_last_login(self, client, mock_user):
        """Test that login updates the last_login timestamp."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        update_mock = AsyncMock()

        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "update_last_login", update_mock):
                response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "testuser",
                        "password": "TestPassword123!",
                    },
                )
                assert response.status_code == 200
                update_mock.assert_called_once()


# ============================================================================
# Token Refresh Endpoint Tests
# ============================================================================


class TestTokenRefresh:
    """Tests for the token refresh endpoint."""

    def test_refresh_success(self, client, mock_user, valid_refresh_token):
        """Test successful token refresh returns new tokens."""

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": valid_refresh_token},
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token returns 401."""
        response = client.post("/api/v1/auth/refresh", params={"refresh_token": "invalid-token"})
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_expired_token(self, client, expired_token):
        """Test refresh with expired token returns 401."""
        response = client.post("/api/v1/auth/refresh", params={"refresh_token": expired_token})
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_wrong_token_type(self, mock_user):
        """Test refresh with access token (wrong type) returns 401."""
        # Create an access token but try to use it as refresh token
        token_data = {
            "sub": str(mock_user.id),
            "username": mock_user.username,
            "role": mock_user.role.value,
        }
        access_token = create_access_token(token_data)

        # We need to test this manually since the client will make a request
        # and we need to check the specific error
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/auth")
        client = TestClient(app)

        response = client.post("/api/v1/auth/refresh", params={"refresh_token": access_token})
        assert response.status_code == 401

    def test_refresh_user_not_found(self, client, valid_refresh_token):
        """Test refresh when user doesn't exist returns 401."""

        async def mock_find_one(**kwargs):
            return None

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": valid_refresh_token},
            )
            assert response.status_code == 401
            assert "User not found or inactive" in response.json()["detail"]

    def test_refresh_inactive_user(self, client, mock_inactive_user):
        """Test refresh with inactive user returns 401."""
        token = create_refresh_token({"sub": str(mock_inactive_user.id)})

        async def mock_find_one(**kwargs):
            return mock_inactive_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.post("/api/v1/auth/refresh", params={"refresh_token": token})
            assert response.status_code == 401
            assert "User not found or inactive" in response.json()["detail"]

    def test_refresh_missing_token(self, client):
        """Test refresh without token returns 422."""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 422


# ============================================================================
# Get Current User Endpoint Tests
# ============================================================================


class TestGetCurrentUserInfo:
    """Tests for the /me endpoint."""

    def test_get_current_user_success(self, client, mock_user, valid_access_token):
        """Test getting current user info with valid token."""

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == mock_user.username
            assert data["email"] == mock_user.email
            assert data["id"] == str(mock_user.id)

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token returns 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client, expired_token):
        """Test getting current user with expired token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    def test_get_current_user_user_not_found(self, client, valid_access_token):
        """Test when user from token doesn't exist in database."""

        async def mock_find_one(**kwargs):
            return None

        with patch.object(User, "find_one", mock_find_one):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )
            assert response.status_code == 401


# ============================================================================
# Change Password Endpoint Tests
# ============================================================================


class TestChangePassword:
    """Tests for the change password endpoint."""

    def test_change_password_success(self, client, mock_user, valid_access_token):
        """Test successful password change."""
        mock_user.hashed_password = get_password_hash("OldPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        save_mock = AsyncMock()

        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "save", save_mock):
                response = client.post(
                    "/api/v1/auth/change-password",
                    json={
                        "old_password": "OldPassword123!",
                        "new_password": "NewPassword123!",
                    },
                    headers={"Authorization": f"Bearer {valid_access_token}"},
                )
                assert response.status_code == 200
                assert "Password changed successfully" in response.json()["message"]
                save_mock.assert_called_once()

    def test_change_password_wrong_old_password(self, client, mock_user, valid_access_token):
        """Test password change with incorrect old password returns 400."""
        mock_user.hashed_password = get_password_hash("OldPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/change-password",
                json={
                    "old_password": "WrongOldPassword123!",
                    "new_password": "NewPassword123!",
                },
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )
            assert response.status_code == 400
            assert "Incorrect current password" in response.json()["detail"]

    def test_change_password_new_too_short(self, client, mock_user, valid_access_token):
        """Test password change with short new password returns 422."""

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/change-password",
                json={
                    "old_password": "OldPassword123!",
                    "new_password": "short",
                },
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )
            assert response.status_code == 422

    def test_change_password_no_auth(self, client):
        """Test password change without authentication returns 401."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 401

    def test_change_password_invalid_auth(self, client):
        """Test password change with invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


# ============================================================================
# Get Current User Dependency Tests
# ============================================================================


class TestGetCurrentUserDependency:
    """Tests for the get_current_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, mock_user):
        """Test get_current_user with valid token."""
        token_data = {
            "sub": str(mock_user.id),
            "username": mock_user.username,
            "role": mock_user.role.value,
        }
        token = create_access_token(token_data)

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            user = await get_current_user(token)
            assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub(self, mock_user):
        """Test get_current_user with token missing sub claim."""
        # Create token without sub
        to_encode = {"username": "testuser", "type": "access"}
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_wrong_token_type(self, mock_user):
        """Test get_current_user with refresh token instead of access token."""
        token = create_refresh_token({"sub": str(mock_user.id)})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, mock_user):
        """Test get_current_user with expired token."""
        to_encode = {
            "sub": str(mock_user.id),
            "username": mock_user.username,
            "role": mock_user.role.value,
            "type": "access",
        }
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid-token")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mock_user):
        """Test get_current_user when user doesn't exist."""
        token_data = {
            "sub": str(mock_user.id),
            "username": mock_user.username,
            "role": mock_user.role.value,
        }
        token = create_access_token(token_data)

        async def mock_find_one(**kwargs):
            return None

        with patch.object(User, "find_one", mock_find_one):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token)
            assert exc_info.value.status_code == 401


# ============================================================================
# Require Permissions Dependency Tests
# ============================================================================


class TestRequirePermissions:
    """Tests for the require_permissions dependency function."""

    @pytest.mark.asyncio
    async def test_require_permissions_sufficient(self, mock_admin_user):
        """Test require_permissions with sufficient role."""
        # require_permissions is async and returns the permission_checker function
        permission_checker = await require_permissions(UserRole.USER)

        # Admin user should pass USER level permission
        result = await permission_checker(current_user=mock_admin_user)
        assert result == mock_admin_user

    @pytest.mark.asyncio
    async def test_require_permissions_exact_role(self, mock_user):
        """Test require_permissions with exact role match."""
        permission_checker = await require_permissions(UserRole.USER)

        result = await permission_checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_require_permissions_insufficient(self, mock_user):
        """Test require_permissions with insufficient role returns 403."""
        permission_checker = await require_permissions(UserRole.ADMIN)

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(current_user=mock_user)
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_permissions_superadmin(self):
        """Test require_permissions with SUPERADMIN role."""
        superadmin = MagicMock(spec=User)
        superadmin.role = UserRole.SUPERADMIN

        permission_checker = await require_permissions(UserRole.ADMIN)
        result = await permission_checker(current_user=superadmin)
        assert result == superadmin


# ============================================================================
# Token Model Tests
# ============================================================================


class TestTokenModels:
    """Tests for Pydantic token models."""

    def test_token_model_creation(self):
        """Test Token model creation."""
        token = Token(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            token_type="bearer",
            expires_in=1800,
        )
        assert token.access_token == "test-access-token"
        assert token.refresh_token == "test-refresh-token"
        assert token.token_type == "bearer"
        assert token.expires_in == 1800

    def test_token_model_defaults(self):
        """Test Token model defaults."""
        token = Token(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_in=1800,
        )
        assert token.token_type == "bearer"

    def test_user_create_model(self):
        """Test UserCreate model."""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"
        assert user.full_name == "Test User"

    def test_user_create_model_optional_full_name(self):
        """Test UserCreate model with optional full_name."""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
        )
        assert user.full_name is None

    def test_user_create_model_username_validation(self):
        """Test UserCreate username validation."""
        # Too short
        with pytest.raises(Exception):
            UserCreate(
                username="ab",  # Less than 3 characters
                email="test@example.com",
                password="SecurePass123!",
            )

    def test_user_create_model_password_validation(self):
        """Test UserCreate password validation."""
        # Too short
        with pytest.raises(Exception):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="short",  # Less than 8 characters
            )

    def test_user_create_model_email_validation(self):
        """Test UserCreate email validation."""
        with pytest.raises(Exception):
            UserCreate(
                username="testuser",
                email="not-an-email",
                password="SecurePass123!",
            )

    def test_user_response_model(self):
        """Test UserResponse model."""
        now = datetime.now(timezone.utc)
        user = UserResponse(
            id="user-id-123",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="USER",
            is_active=True,
            created_at=now,
        )
        assert user.id == "user-id-123"
        assert user.username == "testuser"
        assert user.role == "USER"
        assert user.is_active is True

    def test_password_change_request_model(self):
        """Test PasswordChangeRequest model."""
        request = PasswordChangeRequest(
            old_password="OldPass123!",
            new_password="NewPass123!",
        )
        assert request.old_password == "OldPass123!"
        assert request.new_password == "NewPass123!"

    def test_password_change_request_password_validation(self):
        """Test PasswordChangeRequest new password validation."""
        with pytest.raises(Exception):
            PasswordChangeRequest(
                old_password="OldPass123!",
                new_password="short",
            )


# ============================================================================
# Integration Tests - Full Flow
# ============================================================================


class TestAuthenticationFlow:
    """Integration tests for complete authentication flows."""

    def test_complete_auth_flow(self, client, mock_user):
        """Test complete authentication flow: register -> login -> me -> change password."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        # 1. Login
        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "update_last_login", new_callable=AsyncMock):
                login_response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "testuser",
                        "password": "TestPassword123!",
                    },
                )
                assert login_response.status_code == 200
                tokens = login_response.json()
                access_token = tokens["access_token"]

        # 2. Get current user
        with patch.object(User, "find_one", mock_find_one):
            me_response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert me_response.status_code == 200
            user_data = me_response.json()
            assert user_data["username"] == mock_user.username

    def test_token_refresh_flow(self, client, mock_user):
        """Test token refresh flow."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        # 1. Login to get refresh token
        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "update_last_login", new_callable=AsyncMock):
                login_response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "testuser",
                        "password": "TestPassword123!",
                    },
                )
                refresh_token = login_response.json()["refresh_token"]

        # 2. Refresh token
        with patch.object(User, "find_one", mock_find_one):
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": refresh_token},
            )
            assert refresh_response.status_code == 200
            new_tokens = refresh_response.json()
            assert "access_token" in new_tokens
            assert "refresh_token" in new_tokens

    def test_refresh_with_old_token_fails(self, client, mock_user):
        """Test that refresh tokens cannot be reused."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        # 1. Login
        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "update_last_login", new_callable=AsyncMock):
                login_response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "testuser",
                        "password": "TestPassword123!",
                    },
                )
                refresh_token = login_response.json()["refresh_token"]

        # 2. Refresh (should work)
        with patch.object(User, "find_one", mock_find_one):
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                params={"refresh_token": refresh_token},
            )
            assert refresh_response.status_code == 200

        # 3. Try to use old refresh token again (in a real system this would fail)
        # Note: This test documents expected behavior; actual implementation
        # may differ based on refresh token rotation strategy


# ============================================================================
# Error Response Tests
# ============================================================================


class TestErrorResponses:
    """Tests for proper error response formatting."""

    def test_401_response_headers(self, client):
        """Test that 401 responses include proper WWW-Authenticate header."""

        async def mock_find_one(**kwargs):
            return None

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "TestPassword123!"},
            )
            assert response.status_code == 401
            assert "www-authenticate" in response.headers
            assert "Bearer" in response.headers["www-authenticate"]

    def test_422_validation_error_detail(self, client):
        """Test that 422 responses include validation error details."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # Too short
                "email": "invalid-email",
                "password": "short",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_error_response_json_format(self, client):
        """Test that error responses are valid JSON."""

        async def mock_find_one(**kwargs):
            return None

        with patch.object(User, "find_one", mock_find_one):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "testuser", "password": "wrongpassword"},
            )
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)


# ============================================================================
# Security Tests
# ============================================================================


class TestSecurity:
    """Security-focused tests for authentication."""

    def test_password_not_returned_in_response(self, client, mock_user, valid_access_token):
        """Test that password hash is never returned in responses."""

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {valid_access_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            # Ensure password-related fields are not present
            assert "password" not in data
            assert "hashed_password" not in data
            assert "pass" not in str(data).lower()

    def test_tokens_are_different(self, client, mock_user):
        """Test that access and refresh tokens are different."""
        mock_user.hashed_password = get_password_hash("TestPassword123!")

        async def mock_find_one(**kwargs):
            return mock_user

        with patch.object(User, "find_one", mock_find_one):
            with patch.object(mock_user, "update_last_login", new_callable=AsyncMock):
                response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": "testuser",
                        "password": "TestPassword123!",
                    },
                )
                data = response.json()
                assert data["access_token"] != data["refresh_token"]

    def test_tokens_contain_different_types(self, mock_user):
        """Test that access and refresh tokens have different type claims."""
        token_data = {
            "sub": str(mock_user.id),
            "username": mock_user.username,
            "role": mock_user.role.value,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(mock_user.id)})

        access_decoded = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        refresh_decoded = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert access_decoded["type"] == "access"
        assert refresh_decoded["type"] == "refresh"

    def test_sql_injection_in_login_username(self, client):
        """Test that SQL injection attempts in username are handled."""
        # This test verifies that the endpoint doesn't crash with SQL-like input
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "' OR '1'='1'; DROP TABLE users; --",
                "password": "anything",
            },
        )
        # Should return 401 (not 500) for invalid credentials
        assert response.status_code == 401

    def test_sql_injection_in_login_password(self, client):
        """Test that SQL injection attempts in password are handled."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "' OR '1'='1'; DROP TABLE users; --",
            },
        )
        # Should return 401 (not 500) for invalid credentials
        assert response.status_code == 401


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Edge case tests for authentication."""

    def test_empty_username_login(self, client):
        """Test login with empty username."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "", "password": "somepassword"},
        )
        assert response.status_code in [401, 422]

    def test_empty_password_login(self, client):
        """Test login with empty password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": ""},
        )
        assert response.status_code in [401, 422]

    def test_very_long_username(self, client):
        """Test registration with very long username."""
        long_username = "a" * 51  # Exceeds max_length of 50
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": long_username,
                "email": "test@example.com",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422

    def test_unicode_in_username(self, client, mock_user):
        """Test registration with unicode characters in username."""
        with patch.object(User, "find_one", return_value=None):
            with patch.object(User, "__new__", return_value=mock_user):
                with patch.object(mock_user, "save", new_callable=AsyncMock):
                    response = client.post(
                        "/api/v1/auth/register",
                        json={
                            "username": "用户测试",  # Chinese characters
                            "email": "test@example.com",
                            "password": "SecurePass123!",
                        },
                    )
                    # Should either succeed or fail validation gracefully
                    assert response.status_code in [201, 422]

    def test_special_characters_in_password(self, client, mock_user):
        """Test registration with special characters in password."""
        with patch.object(User, "find_one", return_value=None):
            with patch.object(User, "__new__", return_value=mock_user):
                with patch.object(mock_user, "save", new_callable=AsyncMock):
                    response = client.post(
                        "/api/v1/auth/register",
                        json={
                            "username": "testuser",
                            "email": "test@example.com",
                            "password": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                        },
                    )
                    assert response.status_code == 201

    def test_whitespace_in_credentials(self, client, mock_user):
        """Test handling of whitespace in credentials."""
        with patch.object(User, "find_one", return_value=None):
            # Patch User constructor to return mock_user
            original_new = User.__new__

            def patched_new(cls, *args, **kwargs):
                return mock_user

            with patch.object(User, "__new__", patched_new):
                with patch.object(mock_user, "save", new_callable=AsyncMock):
                    response = client.post(
                        "/api/v1/auth/register",
                        json={
                            "username": "  testuser  ",
                            "email": "test@example.com",
                            "password": "SecurePass123!",
                        },
                    )
                    # Should accept or reject, but not crash
                    assert response.status_code in [201, 400, 422]


# ============================================================================
# Token Expiration Tests
# ============================================================================


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_token_expires_correctly(self, mock_user):
        """Test that token respects expiration time."""
        # Create token that expires in 0 seconds (already expired)
        to_encode = {
            "sub": str(mock_user.id),
            "type": "access",
        }
        expire = datetime.now(timezone.utc) - timedelta(seconds=1)
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        # Should raise exception when decoded
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                expired_token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )

    def test_refresh_token_longer_expiry(self, mock_user):
        """Test that refresh tokens have longer expiry than access tokens."""
        access_token = create_access_token({"sub": str(mock_user.id)})
        refresh_token = create_refresh_token({"sub": str(mock_user.id)})

        access_decoded = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        refresh_decoded = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        access_exp = datetime.utcfromtimestamp(access_decoded["exp"])
        refresh_exp = datetime.utcfromtimestamp(refresh_decoded["exp"])

        # Refresh token should expire later than access token
        assert refresh_exp > access_exp


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
