"""
Extended Tests for api/auth.py - Token verification & Permissions
Target: 90%+ Coverage
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.auth import (
    ALGORITHM,
    API_KEYS,
    SECRET_KEY,
    check_permissions,
    create_api_key,
    decode_token,
    revoke_api_key,
    verify_api_key,
)


class TestDecodeToken:
    """Test token decoding"""

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        from api.auth import create_access_token

        data = {"sub": "testuser"}
        token = create_access_token(data)

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"

    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        result = decode_token("invalid.token.here")
        assert result is None

    def test_decode_expired_token(self):
        """Test decoding expired token"""
        # Create expired token manually
        expired_data = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(
            expired_data, SECRET_KEY, algorithm=ALGORITHM
        )

        result = decode_token(expired_token)
        assert result is None

    def test_decode_token_wrong_signature(self):
        """Test decoding token with wrong signature"""
        token = jwt.encode(
            {"sub": "test"}, "wrong-secret", algorithm=ALGORITHM
        )
        result = decode_token(token)
        assert result is None


class TestCheckPermissions:
    """Test permission checking"""

    def test_check_permissions_admin_can_all(self):
        """Test admin can do everything"""
        admin = {"role": "admin"}
        assert check_permissions(admin, "admin") is True
        assert check_permissions(admin, "operator") is True
        assert check_permissions(admin, "viewer") is True

    def test_check_permissions_operator(self):
        """Test operator permissions"""
        operator = {"role": "operator"}
        assert check_permissions(operator, "admin") is False
        assert check_permissions(operator, "operator") is True
        assert check_permissions(operator, "viewer") is True

    def test_check_permissions_viewer(self):
        """Test viewer permissions"""
        viewer = {"role": "viewer"}
        assert check_permissions(viewer, "admin") is False
        assert check_permissions(viewer, "operator") is False
        assert check_permissions(viewer, "viewer") is True

    def test_check_permissions_no_role_defaults_to_viewer(self):
        """Test user without role defaults to viewer"""
        user = {}  # No role
        assert check_permissions(user, "admin") is False
        assert check_permissions(user, "operator") is False
        assert check_permissions(user, "viewer") is True

    def test_check_permissions_unknown_role(self):
        """Test unknown role handling"""
        user = {"role": "superuser"}  # Unknown role
        assert check_permissions(user, "admin") is False


class TestAPIKeys:
    """Test API key management"""

    def setup_method(self):
        """Clear API keys before each test"""
        API_KEYS.clear()

    def test_create_api_key_returns_string(self):
        """Test API key creation"""
        key = create_api_key(1, "test-key")
        assert isinstance(key, str)
        assert len(key) > 20

    def test_create_api_key_stores_data(self):
        """Test API key data is stored"""
        key = create_api_key(1, "my-key")

        assert key in API_KEYS
        assert API_KEYS[key]["user_id"] == 1
        assert API_KEYS[key]["name"] == "my-key"
        assert "created_at" in API_KEYS[key]

    def test_verify_api_key_valid(self):
        """Test verifying valid API key"""
        key = create_api_key(1, "test")
        result = verify_api_key(key)

        assert result is not None
        assert result["user_id"] == 1

    def test_verify_api_key_invalid(self):
        """Test verifying invalid API key"""
        result = verify_api_key("invalid-key")
        assert result is None

    def test_revoke_api_key_success(self):
        """Test revoking existing API key"""
        key = create_api_key(1, "to-revoke")
        assert key in API_KEYS

        result = revoke_api_key(key)
        assert result is True
        assert key not in API_KEYS

    def test_revoke_api_key_not_found(self):
        """Test revoking non-existent API key"""
        result = revoke_api_key("non-existent")
        assert result is False

    def test_multiple_api_keys(self):
        """Test multiple API keys for same user"""
        key1 = create_api_key(1, "key1")
        key2 = create_api_key(1, "key2")
        key3 = create_api_key(2, "key3")

        assert len(API_KEYS) == 3
        assert verify_api_key(key1)["name"] == "key1"
        assert verify_api_key(key2)["name"] == "key2"
        assert verify_api_key(key3)["name"] == "key3"


class TestAsyncFunctions:
    """Test async functions with mocks"""

    @pytest.mark.asyncio
    async def test_verify_token_valid(self):
        """Test verify_token with valid credentials"""
        from api.auth import create_access_token, verify_token

        # Create valid token
        token = create_access_token({"sub": "testuser"})

        # Mock credentials
        mock_creds = MagicMock()
        mock_creds.credentials = token

        # Should not raise
        result = await verify_token(mock_creds)
        assert result["sub"] == "testuser"

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test verify_token with invalid credentials"""
        from fastapi import HTTPException

        from api.auth import verify_token

        mock_creds = MagicMock()
        mock_creds.credentials = "invalid.token"

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_creds)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_admin_success(self):
        """Test require_admin with admin user"""
        from api.auth import create_access_token, require_admin

        token = create_access_token({"sub": "admin", "role": "admin"})
        mock_creds = MagicMock()
        mock_creds.credentials = token

        result = await require_admin(mock_creds)
        assert result["role"] == "admin"

    @pytest.mark.asyncio
    async def test_require_admin_forbidden(self):
        """Test require_admin with non-admin user"""
        from fastapi import HTTPException

        from api.auth import create_access_token, require_admin

        token = create_access_token({"sub": "user", "role": "viewer"})
        mock_creds = MagicMock()
        mock_creds.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_creds)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_operator_success(self):
        """Test require_operator with operator"""
        from api.auth import create_access_token, require_operator

        token = create_access_token({"sub": "op", "role": "operator"})
        mock_creds = MagicMock()
        mock_creds.credentials = token

        result = await require_operator(mock_creds)
        assert result["role"] == "operator"

    @pytest.mark.asyncio
    async def test_require_operator_forbidden(self):
        """Test require_operator with viewer"""
        from fastapi import HTTPException

        from api.auth import create_access_token, require_operator

        token = create_access_token({"sub": "viewer", "role": "viewer"})
        mock_creds = MagicMock()
        mock_creds.credentials = token

        with pytest.raises(HTTPException) as exc_info:
            await require_operator(mock_creds)

        assert exc_info.value.status_code == 403
