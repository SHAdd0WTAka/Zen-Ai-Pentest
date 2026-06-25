"""
Tests for api/auth_deps.py — shared auth dependency functions.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def patch_jwt_handler():
    """Mock _jwt_handler on auth_deps so new-auth code path can be tested."""
    handler = MagicMock()
    handler.decode_token = MagicMock()
    with patch("api.auth_deps._jwt_handler", handler), patch("api.auth_deps.NEW_AUTH_AVAILABLE", True):
        yield handler


@pytest.fixture
def bearer_creds():
    """Build a fake HTTPAuthorizationCredentials object."""
    from fastapi.security.http import HTTPAuthorizationCredentials

    return HTTPAuthorizationCredentials(scheme="bearer", credentials="valid.jwt.token")


# ============================================================================
# verify_admin_credentials
# ============================================================================


class TestVerifyAdminCredentials:
    def test_correct_credentials_return_true(self):
        from api.auth_deps import verify_admin_credentials

        with patch("api.auth_deps.ADMIN_USERNAME", "admin"), patch("api.auth_deps.ADMIN_PASSWORD", "secret"):
            assert verify_admin_credentials("admin", "secret") is True

    def test_wrong_username_returns_false(self):
        from api.auth_deps import verify_admin_credentials

        with patch("api.auth_deps.ADMIN_USERNAME", "admin"), patch("api.auth_deps.ADMIN_PASSWORD", "secret"):
            assert verify_admin_credentials("hacker", "secret") is False

    def test_wrong_password_returns_false(self):
        from api.auth_deps import verify_admin_credentials

        with patch("api.auth_deps.ADMIN_USERNAME", "admin"), patch("api.auth_deps.ADMIN_PASSWORD", "secret"):
            assert verify_admin_credentials("admin", "wrongpass") is False

    def test_empty_password_env_returns_false(self):
        from api.auth_deps import verify_admin_credentials

        with patch("api.auth_deps.ADMIN_USERNAME", "admin"), patch("api.auth_deps.ADMIN_PASSWORD", None):
            assert verify_admin_credentials("admin", "anything") is False


# ============================================================================
# verify_token
# ============================================================================


class TestVerifyToken:
    @pytest.mark.asyncio
    async def test_no_credentials_raises_401(self):
        from api.auth_deps import verify_token

        with pytest.raises(Exception) as exc:
            await verify_token(None)
        assert exc.type.__name__ == "HTTPException"

    @pytest.mark.asyncio
    async def test_new_auth_flow_success(self, patch_jwt_handler, bearer_creds):
        """When NEW_AUTH_AVAILABLE and _jwt_handler present, use new flow."""
        from datetime import datetime, timezone

        from auth.jwt_handler import TokenPayload, TokenType

        now = datetime.now(timezone.utc)
        payload = TokenPayload(
            sub="alice",
            jti="test-jti",
            type=TokenType.ACCESS,
            iat=now,
            exp=now.replace(year=now.year + 1),
            nbf=now,
            iss="test-issuer",
            aud="test-audience",
            roles=["user"],
            permissions=["read"],
            session_id="sess_001",
            mfa_verified=True,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        patch_jwt_handler.decode_token.return_value = payload

        from api.auth_deps import verify_token

        result = await verify_token(bearer_creds)
        assert result["sub"] == "alice"
        assert result["role"] == "user"
        assert result["session_id"] == "sess_001"

    @pytest.mark.asyncio
    async def test_new_auth_token_expired_raises_401(self, patch_jwt_handler, bearer_creds):
        """TokenExpiredError from new handler -> 401."""
        from auth.jwt_handler import TokenExpiredError

        patch_jwt_handler.decode_token.side_effect = TokenExpiredError("expired")

        from api.auth_deps import verify_token

        with pytest.raises(Exception) as exc:
            await verify_token(bearer_creds)
        assert exc.type.__name__ == "HTTPException"

    @pytest.mark.asyncio
    async def test_fallback_to_legacy_when_no_new_auth(self, bearer_creds):
        """NEW_AUTH_AVAILABLE=False -> falls through to legacy verify."""
        mock_legacy = MagicMock(return_value={"username": "bob", "role": "user"})
        with (
            patch("api.auth_deps.NEW_AUTH_AVAILABLE", False),
            patch("api.auth_deps.legacy_verify_token", mock_legacy),
        ):
            from api.auth_deps import verify_token

            result = await verify_token(bearer_creds)
            assert result["username"] == "bob"
            mock_legacy.assert_called_once_with(bearer_creds)


# ============================================================================
# optional_auth
# ============================================================================


class TestOptionalAuth:
    @pytest.mark.asyncio
    async def test_no_auth_header_returns_none(self):
        """No Authorization header -> returns None."""
        request = MagicMock()
        request.headers.get.return_value = None

        from api.auth_deps import optional_auth

        result = await optional_auth(request)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_scheme_returns_none(self):
        """Authorization header with non-Bearer scheme -> None."""
        request = MagicMock()
        request.headers.get.return_value = "Basic dXNlcjpwYXNz"

        from api.auth_deps import optional_auth

        result = await optional_auth(request)
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """Valid Bearer token -> returns user dict."""
        request = MagicMock()
        request.headers.get.return_value = "Bearer mytoken"

        with patch("api.auth_deps.verify_token", new=AsyncMock()) as mock_vt:
            mock_vt.return_value = {"username": "charlie", "role": "admin"}

            from api.auth_deps import optional_auth

            result = await optional_auth(request)
            assert result["username"] == "charlie"

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self):
        """Expired token handled gracefully -> None."""
        request = MagicMock()
        request.headers.get.return_value = "Bearer expired_token"

        from fastapi import HTTPException

        with patch("api.auth_deps.verify_token", new=AsyncMock()) as mock_vt:
            mock_vt.side_effect = HTTPException(status_code=401)

            from api.auth_deps import optional_auth

            result = await optional_auth(request)
            assert result is None
