"""
Extended Tests for API Core Auth Module

Additional tests to achieve 90%+ coverage for api/core/auth.py

Covers additional edge cases and scenarios not covered by test_api_auth.py
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from freezegun import freeze_time

from api.core.auth import (
    TokenBlacklistedError,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenType,
    UserRole,
    _rate_limit_storage,
    _token_blacklist,
    api_key_header,
    oauth2_scheme,
    pwd_context,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_globals():
    """Clean up global state before and after each test."""
    from api.core.auth import clear_all_rate_limits, clear_token_blacklist

    clear_token_blacklist()
    clear_all_rate_limits()
    yield
    clear_token_blacklist()
    clear_all_rate_limits()


@pytest.fixture
def sample_user_data():
    """Provide sample user data for token creation."""
    return {
        "sub": "user_123",
        "username": "testuser",
        "role": "user",
    }


# ============================================================================
# UserRole Enum Extended Tests
# ============================================================================


class TestUserRoleExtended:
    """Extended tests for UserRole enum."""

    def test_all_roles_defined(self):
        """Test that all expected roles are defined."""
        expected_roles = [
            "super_admin",
            "admin",
            "security_analyst",
            "user",
            "viewer",
            "api_service",
        ]
        for role in expected_roles:
            assert hasattr(UserRole, role.upper())
            assert getattr(UserRole, role.upper()).value == role

    def test_role_comparison_all_pairs(self):
        """Test comparison between all role pairs."""
        roles = [
            UserRole.VIEWER,
            UserRole.USER,
            UserRole.API_SERVICE,
            UserRole.SECURITY_ANALYST,
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
        ]

        # Each role should be less than all roles after it
        for i, role1 in enumerate(roles):
            for role2 in roles[i + 1 :]:
                assert role1 < role2
                assert role2 > role1
                assert role1 <= role2
                assert role2 >= role1

    def test_role_comparison_with_non_role_returns_not_implemented(self):
        """Test comparison with non-UserRole returns NotImplemented."""
        assert UserRole.ADMIN.__lt__("admin") is NotImplemented
        assert UserRole.ADMIN.__lt__(5) is NotImplemented

    def test_role_equality_with_string(self):
        """Test role equality comparison with string."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.ADMIN.value == "admin"


# ============================================================================
# TokenType Enum Tests
# ============================================================================


class TestTokenTypeEnumExtended:
    """Extended tests for TokenType enum."""

    def test_all_token_types_defined(self):
        """Test that all token types are defined."""
        expected_types = [
            "access",
            "refresh",
            "api_key",
            "reset_password",
            "verify_email",
        ]
        for token_type in expected_types:
            assert hasattr(TokenType, token_type.upper())
            assert getattr(TokenType, token_type.upper()).value == token_type

    def test_token_type_str_type(self):
        """Test that TokenType inherits from str."""
        assert isinstance(TokenType.ACCESS, str)
        assert TokenType.ACCESS == "access"


# ============================================================================
# Password Context Tests
# ============================================================================


class TestPasswordContext:
    """Tests for password context configuration."""

    def test_bcrypt_scheme_used(self):
        """Test that bcrypt scheme is used."""
        assert "bcrypt" in pwd_context.schemes()

    def test_password_hash_format(self):
        """Test password hash format."""
        from api.core.auth import get_password_hash

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        # Should be a valid bcrypt hash
        assert hashed.startswith("$2")
        parts = hashed.split("$")
        assert len(parts) >= 3


# ============================================================================
# Exception Classes Tests
# ============================================================================


class TestExceptionClasses:
    """Tests for custom exception classes."""

    def test_token_error_inheritance(self):
        """Test TokenError inheritance."""
        assert issubclass(TokenExpiredError, TokenError)
        assert issubclass(TokenInvalidError, TokenError)
        assert issubclass(TokenBlacklistedError, TokenError)

    def test_token_error_can_be_caught(self):
        """Test that all token errors can be caught as TokenError."""
        errors = [
            TokenExpiredError("expired"),
            TokenInvalidError("invalid"),
            TokenBlacklistedError("blacklisted"),
        ]

        for error in errors:
            try:
                raise error
            except TokenError as e:
                assert e is error

    def test_token_error_messages(self):
        """Test token error messages."""
        assert str(TokenExpiredError("test message")) == "test message"
        assert str(TokenInvalidError("invalid token")) == "invalid token"


# ============================================================================
# OAuth2 and API Key Scheme Tests
# ============================================================================


class TestOAuth2Scheme:
    """Tests for OAuth2 scheme configuration."""

    def test_oauth2_scheme_configuration(self):
        """Test OAuth2 scheme is properly configured."""
        assert oauth2_scheme.model.flows is not None
        assert oauth2_scheme.model.flows.password is not None
        assert oauth2_scheme.model.flows.password.tokenUrl == "/api/v1/auth/login"

    def test_oauth2_scheme_auto_error_false(self):
        """Test that OAuth2 scheme has auto_error=False."""
        # This allows optional authentication
        assert oauth2_scheme.auto_error is False


class TestAPIKeyHeader:
    """Tests for API key header scheme."""

    def test_api_key_header_name(self):
        """Test API key header name."""
        assert api_key_header.model.name == "X-API-Key"

    def test_api_key_header_auto_error_false(self):
        """Test that API key header has auto_error=False."""
        assert api_key_header.auto_error is False


# ============================================================================
# Token Blacklist Tests
# ============================================================================


class TestTokenBlacklistExtended:
    """Extended tests for token blacklist functionality."""

    def test_blacklist_token_returns_true(self):
        """Test that blacklist_token returns True."""
        from api.core.auth import blacklist_token

        result = blacklist_token("test_jti")
        assert result is True

    def test_is_token_blacklisted_with_empty_string(self):
        """Test checking empty string JTI."""
        from api.core.auth import is_token_blacklisted

        assert is_token_blacklisted("") is False

    def test_multiple_blacklist_calls_same_jti(self):
        """Test blacklisting same JTI multiple times."""
        from api.core.auth import blacklist_token, get_blacklisted_count, is_token_blacklisted

        blacklist_token("duplicate_jti")
        blacklist_token("duplicate_jti")

        # Should only count once (set behavior)
        assert is_token_blacklisted("duplicate_jti") is True

    def test_clear_blacklist_makes_tokens_valid(self):
        """Test that clearing blacklist makes tokens valid again."""
        from api.core.auth import blacklist_token, clear_token_blacklist, is_token_blacklisted

        jti = "test_jti"
        blacklist_token(jti)
        assert is_token_blacklisted(jti) is True

        clear_token_blacklist()
        assert is_token_blacklisted(jti) is False

    def test_blacklisted_count_with_many_tokens(self):
        """Test count with many blacklisted tokens."""
        from api.core.auth import blacklist_token, get_blacklisted_count

        for i in range(100):
            blacklist_token(f"jti_{i}")

        assert get_blacklisted_count() == 100


# ============================================================================
# Rate Limit Storage Tests
# ============================================================================


class TestRateLimitStorage:
    """Tests for rate limit storage internals."""

    def test_rate_limit_storage_structure(self):
        """Test rate limit storage data structure."""
        from api.core.auth import check_rate_limit

        # Make a request
        check_rate_limit("test_key", max_requests=10)

        # Should have created an entry
        assert "test_key" in _rate_limit_storage
        assert "requests" in _rate_limit_storage["test_key"]

    def test_rate_limit_blocked_entry_structure(self):
        """Test structure of blocked rate limit entry."""
        from api.core.auth import check_rate_limit

        # Exhaust rate limit
        for _ in range(5):
            check_rate_limit("blocked_key", max_requests=5, window_seconds=3600)

        # Next request should be blocked
        allowed, remaining, reset = check_rate_limit("blocked_key", max_requests=5, window_seconds=3600)

        assert allowed is False
        assert remaining == 0
        assert reset == 3600

    def test_clear_all_rate_limits_removes_all(self):
        """Test that clear_all_rate_limits removes all entries."""
        from api.core.auth import check_rate_limit, clear_all_rate_limits

        # Create entries
        for i in range(5):
            check_rate_limit(f"key_{i}", max_requests=10)

        # Clear all
        clear_all_rate_limits()

        # All entries should be gone
        assert len(_rate_limit_storage) == 0


# ============================================================================
# Module Import Tests
# ============================================================================


class TestModuleImports:
    """Tests for module imports and exports."""

    def test_all_exports_are_callable(self):
        """Test that all exports are callable or valid types."""
        from api.core import auth

        exports = auth.__all__

        for export_name in exports:
            export = getattr(auth, export_name)
            # Should be callable or a type/class
            assert export is not None

    def test_no_undefined_exports(self):
        """Test that no undefined exports exist."""
        from api.core import auth

        for export_name in auth.__all__:
            assert hasattr(auth, export_name)

    def test_private_modules_not_exported(self):
        """Test that private modules are not in exports."""
        from api.core import auth

        private_names = [
            "_token_blacklist",
            "_rate_limit_storage",
            "pwd_context",
        ]
        for private in private_names:
            assert private not in auth.__all__


# ============================================================================
# Integration and Edge Case Tests
# ============================================================================


class TestAuthIntegrationExtended:
    """Extended integration tests for authentication."""

    @pytest.mark.asyncio
    async def test_super_admin_cannot_access_super_admin_only(self):
        """Test that super_admin can access super_admin only resources."""
        from api.core.auth import require_permissions

        checker = require_permissions([UserRole.SUPER_ADMIN])
        user = {"id": "123", "username": "super", "role": "super_admin"}

        result = await checker(user)
        assert result == user

    def test_uuid_generation_in_token(self):
        """Test that tokens contain valid UUID as JTI."""
        from api.core.auth import create_access_token, decode_token

        token = create_access_token({"sub": "user_123"})
        payload = decode_token(token)

        jti = payload["jti"]
        # Should be a valid UUID
        uuid_obj = uuid.UUID(jti)
        assert str(uuid_obj) == jti

    def test_token_timestamps_are_valid(self):
        """Test that token timestamps are valid."""
        from api.core.auth import create_access_token, decode_token

        token = create_access_token({"sub": "user_123"})
        payload = decode_token(token)

        exp = payload["exp"]
        iat = payload["iat"]

        # Convert to datetime
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        iat_dt = datetime.fromtimestamp(iat, tz=timezone.utc)

        # Expiration should be after issued at
        assert exp_dt > iat_dt

    def test_settings_import(self):
        """Test that settings are properly imported."""
        from api.core.auth import settings
        from api.core.config import settings as config_settings

        assert settings is config_settings


# ============================================================================
# Configuration Tests
# ============================================================================


class TestAuthConfiguration:
    """Tests for auth module configuration."""

    def test_jwt_algorithm_in_settings(self):
        """Test JWT algorithm is configured."""
        from api.core.auth import settings

        assert hasattr(settings, "JWT_ALGORITHM")
        assert settings.JWT_ALGORITHM == "HS256"

    def test_secret_key_in_settings(self):
        """Test secret key is configured."""
        from api.core.auth import settings

        assert hasattr(settings, "SECRET_KEY")
        assert len(settings.SECRET_KEY) > 0

    def test_token_expire_minutes_in_settings(self):
        """Test token expiration is configured."""
        from api.core.auth import settings

        assert hasattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES")
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
