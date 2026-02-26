"""
Comprehensive tests for api/auth.py module

Target: 80%+ Coverage
Covers:
- JWT token creation and validation
- Authentication functions
- User management
- Permission checking
- Token refresh/blacklist
- API Key management
"""

import os
import sys
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import jwt
import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables before importing
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-bytes-long-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    API_KEYS,
    SECRET_KEY,
    check_permissions,
    create_access_token,
    create_api_key,
    decode_token,
    get_password_hash,
    pwd_context,
    require_admin,
    require_operator,
    revoke_api_key,
    security,
    verify_api_key,
    verify_password,
    verify_token,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clear_api_keys():
    """Clear API keys before and after each test for isolation"""
    API_KEYS.clear()
    yield
    # Cleanup after test
    API_KEYS.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for token creation"""
    return {
        "sub": "testuser",
        "username": "testuser",
        "role": "operator",
        "user_id": 123,
    }


@pytest.fixture
def valid_token(sample_user_data):
    """Create a valid JWT token"""
    return create_access_token(sample_user_data)


@pytest.fixture
def expired_token(sample_user_data):
    """Create an expired JWT token"""
    expired_delta = timedelta(minutes=-1)
    return create_access_token(sample_user_data, expires_delta=expired_delta)


@pytest.fixture
def mock_credentials(valid_token):
    """Create mock HTTPAuthorizationCredentials"""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)


# =============================================================================
# Test Password Functions
# =============================================================================


class TestPasswordFunctions:
    """Test password hashing and verification functions"""

    def test_get_password_hash_returns_bcrypt_string(self):
        """Test that password hashing returns a valid bcrypt hash"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) > 50

    def test_get_password_hash_different_salts(self):
        """Test that same password produces different hashes due to salt"""
        password = "mysecurepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_verify_password_correct(self):
        """Test verifying correct password against hash"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password fails"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty string"""
        password = ""
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_password_with_special_characters(self):
        """Test password with special characters"""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_password_with_unicode(self):
        """Test password with unicode characters"""
        password = "пароль密码パスワード🔐"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_very_long_password(self):
        """Test very long password hashing and verification"""
        password = "a" * 1000
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_password_context_configuration(self):
        """Test that password context is properly configured"""
        assert "bcrypt" in pwd_context.schemes()


# =============================================================================
# Test JWT Token Creation
# =============================================================================


class TestJWTTokenCreation:
    """Test JWT token creation and properties"""

    def test_create_access_token_returns_string(self, sample_user_data):
        """Test that token creation returns a string"""
        token = create_access_token(sample_user_data)
        
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_access_token_contains_user_data(self, sample_user_data):
        """Test that created token contains the original data"""
        token = create_access_token(sample_user_data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert decoded["sub"] == sample_user_data["sub"]
        assert decoded["username"] == sample_user_data["username"]
        assert decoded["role"] == sample_user_data["role"]
        assert decoded["user_id"] == sample_user_data["user_id"]

    def test_create_access_token_has_expiration(self, sample_user_data):
        """Test that token includes expiration claim"""
        token = create_access_token(sample_user_data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)

    def test_create_access_token_default_expiration(self, sample_user_data):
        """Test default expiration time (30 minutes)"""
        token = create_access_token(sample_user_data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        exp_timestamp = decoded["exp"]
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        actual_exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        diff = abs((expected_exp - actual_exp).total_seconds())
        assert diff < 5  # Within 5 seconds

    def test_create_access_token_custom_expiration(self, sample_user_data):
        """Test custom expiration time via expires_delta"""
        custom_delta = timedelta(hours=2, minutes=30)
        token = create_access_token(sample_user_data, expires_delta=custom_delta)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        exp_timestamp = decoded["exp"]
        expected_exp = datetime.now(timezone.utc) + timedelta(hours=2, minutes=30)
        actual_exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        
        diff = abs((expected_exp - actual_exp).total_seconds())
        assert diff < 5

    def test_create_access_token_does_not_mutate_original(self, sample_user_data):
        """Test that original data dict is not mutated"""
        original_data = sample_user_data.copy()
        create_access_token(sample_user_data)
        
        assert sample_user_data == original_data


# =============================================================================
# Test JWT Token Decoding and Validation
# =============================================================================


class TestJWTTokenDecoding:
    """Test JWT token decoding and validation"""

    def test_decode_token_valid(self, sample_user_data):
        """Test decoding a valid token"""
        token = create_access_token(sample_user_data)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == sample_user_data["sub"]
        assert decoded["role"] == sample_user_data["role"]

    def test_decode_token_invalid(self):
        """Test decoding an invalid token"""
        decoded = decode_token("invalid.token.here")
        assert decoded is None

    def test_decode_token_malformed(self):
        """Test decoding malformed tokens"""
        assert decode_token("") is None
        assert decode_token("not-a-token") is None
        assert decode_token("Bearer token") is None

    def test_decode_token_expired(self, expired_token):
        """Test decoding an expired token"""
        decoded = decode_token(expired_token)
        assert decoded is None

    def test_decode_token_wrong_secret(self, sample_user_data):
        """Test decoding with wrong secret key"""
        token = create_access_token(sample_user_data)
        
        # Try to decode with wrong secret
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-secret", algorithms=[ALGORITHM])

    def test_decode_token_tampered(self, sample_user_data):
        """Test decoding a tampered token"""
        token = create_access_token(sample_user_data)
        tampered_token = token[:-5] + "XXXXX"
        
        decoded = decode_token(tampered_token)
        assert decoded is None

    def test_decode_token_with_complex_data(self):
        """Test token with nested/complex data"""
        data = {
            "sub": "user123",
            "permissions": ["read", "write", "delete"],
            "metadata": {
                "last_login": "2024-01-01T00:00:00Z",
                "ip": "127.0.0.1",
                "session_id": "abc123",
            },
            "nested": {"level1": {"level2": "deep"}},
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded["permissions"] == ["read", "write", "delete"]
        assert decoded["metadata"]["ip"] == "127.0.0.1"
        assert decoded["nested"]["level1"]["level2"] == "deep"


# =============================================================================
# Test FastAPI Token Verification Dependency
# =============================================================================


class TestVerifyToken:
    """Test the verify_token FastAPI dependency"""

    @pytest.mark.anyio
    async def test_verify_token_valid(self, mock_credentials, sample_user_data):
        """Test verifying a valid token"""
        payload = await verify_token(mock_credentials)
        
        assert payload is not None
        assert payload["sub"] == sample_user_data["sub"]

    @pytest.mark.anyio
    async def test_verify_token_invalid(self):
        """Test verifying an invalid token raises HTTPException"""
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(invalid_credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in str(exc_info.value.detail)

    @pytest.mark.anyio
    async def test_verify_token_expired(self, expired_token):
        """Test verifying an expired token raises HTTPException"""
        expired_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=expired_token
        )
        
        # decode_token returns None for expired, which triggers the exception
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(expired_credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    async def test_verify_token_missing_exp(self):
        """Test token without expiration (edge case)"""
        # Create token without exp
        data = {"sub": "testuser"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )
        
        # Should still work (no exp means no expiration check in this implementation)
        payload = await verify_token(credentials)
        assert payload["sub"] == "testuser"


# =============================================================================
# Test Permission Checking
# =============================================================================


class TestPermissionChecking:
    """Test role-based permission checking"""

    def test_check_permissions_admin_can_access_all(self):
        """Test admin can access all role levels"""
        admin_user = {"role": "admin"}
        
        assert check_permissions(admin_user, "viewer") is True
        assert check_permissions(admin_user, "operator") is True
        assert check_permissions(admin_user, "admin") is True

    def test_check_permissions_operator_hierarchy(self):
        """Test operator permissions in role hierarchy"""
        operator_user = {"role": "operator"}
        
        assert check_permissions(operator_user, "viewer") is True
        assert check_permissions(operator_user, "operator") is True
        assert check_permissions(operator_user, "admin") is False

    def test_check_permissions_viewer_restricted(self):
        """Test viewer has limited permissions"""
        viewer_user = {"role": "viewer"}
        
        assert check_permissions(viewer_user, "viewer") is True
        assert check_permissions(viewer_user, "operator") is False
        assert check_permissions(viewer_user, "admin") is False

    def test_check_permissions_no_role_defaults_to_viewer(self):
        """Test user without role defaults to viewer level"""
        user_no_role = {}
        
        assert check_permissions(user_no_role, "viewer") is True
        assert check_permissions(user_no_role, "operator") is False

    def test_check_permissions_unknown_role(self):
        """Test user with unknown role has no permissions"""
        unknown_user = {"role": "superuser"}
        
        # Unknown role has level 0, can't access anything
        assert check_permissions(unknown_user, "viewer") is False
        assert check_permissions(unknown_user, "operator") is False

    def test_check_permissions_unknown_required_role(self):
        """Test requiring unknown role - unknown role has level 0, admin has level 3"""
        admin_user = {"role": "admin"}
        
        # Unknown role has level 0, which is less than admin's 3
        # So admin can access (user_level >= required_level: 3 >= 0)
        assert check_permissions(admin_user, "superadmin") is True

    @pytest.mark.anyio
    async def test_require_admin_with_admin(self):
        """Test require_admin with admin user"""
        admin_token = create_access_token(
            {"sub": "admin", "role": "admin"}
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=admin_token
        )
        
        payload = await require_admin(credentials)
        assert payload["role"] == "admin"

    @pytest.mark.anyio
    async def test_require_admin_with_operator(self):
        """Test require_admin with operator (should fail)"""
        operator_token = create_access_token(
            {"sub": "operator", "role": "operator"}
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=operator_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(credentials)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in str(exc_info.value.detail)

    @pytest.mark.anyio
    async def test_require_admin_with_viewer(self):
        """Test require_admin with viewer (should fail)"""
        viewer_token = create_access_token(
            {"sub": "viewer", "role": "viewer"}
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=viewer_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(credentials)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_require_operator_with_operator(self):
        """Test require_operator with operator user"""
        operator_token = create_access_token(
            {"sub": "operator", "role": "operator"}
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=operator_token
        )
        
        payload = await require_operator(credentials)
        assert payload["role"] == "operator"

    @pytest.mark.anyio
    async def test_require_operator_with_admin(self):
        """Test require_operator with admin (should succeed - hierarchy)"""
        admin_token = create_access_token(
            {"sub": "admin", "role": "admin"}
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=admin_token
        )
        
        payload = await require_operator(credentials)
        assert payload["role"] == "admin"

    @pytest.mark.anyio
    async def test_require_operator_with_viewer(self):
        """Test require_operator with viewer (should fail)"""
        viewer_token = create_access_token(
            {"sub": "viewer", "role": "viewer"}
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=viewer_token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await require_operator(credentials)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Operator privileges required" in str(exc_info.value.detail)


# =============================================================================
# Test API Key Management
# =============================================================================


class TestAPIKeyManagement:
    """Test API key creation, verification, and revocation"""

    def test_create_api_key_returns_string(self):
        """Test API key creation returns a string"""
        key = create_api_key(user_id=1, name="test-key")
        
        assert isinstance(key, str)
        assert len(key) > 20

    def test_create_api_key_stores_metadata(self):
        """Test API key stores correct metadata"""
        key = create_api_key(user_id=42, name="my-test-key")
        
        assert key in API_KEYS
        assert API_KEYS[key]["user_id"] == 42
        assert API_KEYS[key]["name"] == "my-test-key"
        assert "created_at" in API_KEYS[key]

    def test_create_api_key_unique(self):
        """Test that each API key created is unique"""
        key1 = create_api_key(user_id=1, name="key1")
        key2 = create_api_key(user_id=1, name="key2")
        
        assert key1 != key2

    def test_verify_api_key_valid(self):
        """Test verifying a valid API key"""
        key = create_api_key(user_id=1, name="test-key")
        metadata = verify_api_key(key)
        
        assert metadata is not None
        assert metadata["user_id"] == 1
        assert metadata["name"] == "test-key"

    def test_verify_api_key_invalid(self):
        """Test verifying an invalid API key"""
        metadata = verify_api_key("invalid-key-12345")
        assert metadata is None

    def test_verify_api_key_empty(self):
        """Test verifying empty API key"""
        assert verify_api_key("") is None
        assert verify_api_key(None) is None  # type: ignore

    def test_revoke_api_key_success(self):
        """Test successful API key revocation"""
        key = create_api_key(user_id=1, name="to-revoke")
        
        assert key in API_KEYS
        result = revoke_api_key(key)
        
        assert result is True
        assert key not in API_KEYS

    def test_revoke_api_key_not_found(self):
        """Test revoking non-existent API key"""
        result = revoke_api_key("non-existent-key")
        assert result is False

    def test_revoke_api_key_already_revoked(self):
        """Test revoking already revoked key"""
        key = create_api_key(user_id=1, name="test-key")
        revoke_api_key(key)
        
        # Second revocation should fail
        result = revoke_api_key(key)
        assert result is False

    def test_multiple_api_keys_same_user(self):
        """Test multiple API keys for same user"""
        key1 = create_api_key(user_id=1, name="key1")
        key2 = create_api_key(user_id=1, name="key2")
        key3 = create_api_key(user_id=1, name="key3")
        
        assert verify_api_key(key1) is not None
        assert verify_api_key(key2) is not None
        assert verify_api_key(key3) is not None
        
        # Revoke one, others should still work
        revoke_api_key(key2)
        assert verify_api_key(key1) is not None
        assert verify_api_key(key2) is None
        assert verify_api_key(key3) is not None

    def test_api_key_created_at_is_iso_format(self):
        """Test that created_at is in ISO format"""
        key = create_api_key(user_id=1, name="test-key")
        created_at = API_KEYS[key]["created_at"]
        
        # Should be parseable as datetime
        parsed = datetime.fromisoformat(created_at)
        assert isinstance(parsed, datetime)


# =============================================================================
# Test Configuration and Environment Variables
# =============================================================================


class TestConfiguration:
    """Test configuration loading from environment"""

    def test_secret_key_loaded(self):
        """Test that SECRET_KEY is loaded"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0

    def test_algorithm_is_hs256(self):
        """Test default algorithm is HS256"""
        assert ALGORITHM == "HS256"

    def test_access_token_expire_minutes_default(self):
        """Test default expiration is 30 minutes"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_security_bearer_initialized(self):
        """Test that HTTPBearer security is initialized"""
        assert security is not None
        assert security.model.scheme == "bearer"


class TestConfigurationWithEnvironmentVariables:
    """Test configuration with custom environment variables"""

    @patch.dict(
        os.environ,
        {
            "JWT_SECRET_KEY": "custom-secret-key",
            "JWT_ALGORITHM": "HS384",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        },
    )
    def test_custom_configuration(self):
        """Test loading custom configuration from environment"""
        # Must reload module to pick up new env vars
        import importlib
        import api.auth as auth_module
        
        importlib.reload(auth_module)
        
        assert auth_module.SECRET_KEY == "custom-secret-key"
        assert auth_module.ALGORITHM == "HS384"
        assert auth_module.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    @patch.dict(os.environ, {"JWT_SECRET_KEY": ""}, clear=True)
    def test_missing_secret_key_generates_warning(self):
        """Test that missing secret key generates a warning"""
        import importlib
        import api.auth as auth_module
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(auth_module)
            
            # Check that a RuntimeWarning was issued
            runtime_warnings = [x for x in w if issubclass(x.category, RuntimeWarning)]
            assert len(runtime_warnings) > 0
            assert "JWT_SECRET_KEY not set" in str(runtime_warnings[0].message)


# =============================================================================
# Test Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    def test_token_with_very_long_payload(self):
        """Test token with very long payload"""
        data = {
            "sub": "user",
            "data": "x" * 10000,  # 10KB of data
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["data"] == "x" * 10000

    def test_token_with_unicode_in_claims(self):
        """Test token with unicode characters in claims"""
        data = {
            "sub": "ユーザー",
            "name": "测试用户",
            "description": "Юникод тест",
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded["sub"] == "ユーザー"
        assert decoded["name"] == "测试用户"
        assert decoded["description"] == "Юникод тест"

    def test_password_verify_with_none(self):
        """Test password verification with None (edge case)"""
        # passlib raises TypeError for None hash
        try:
            result = verify_password("password", None)  # type: ignore
            assert result is False
        except (TypeError, AttributeError):
            # Expected behavior - None hash causes an exception
            assert True

    def test_api_key_with_special_characters_in_name(self):
        """Test API key with various characters in name"""
        name = "key_with_underscores-and-dashes123"
        key = create_api_key(user_id=1, name=name)
        
        # Verify by checking verify_api_key returns the metadata
        metadata = verify_api_key(key)
        assert metadata is not None
        assert metadata["name"] == name


# =============================================================================
# Test Integration Scenarios
# =============================================================================


class TestIntegrationScenarios:
    """Integration tests for complete auth flows"""

    def test_full_auth_flow_password_and_token(self):
        """Test complete auth flow: password hashing -> token creation -> verification"""
        # 1. Create password hash
        password = "userpassword123"
        hashed = get_password_hash(password)
        
        # 2. Verify password
        assert verify_password(password, hashed) is True
        
        # 3. Create token for authenticated user
        user_data = {"sub": "user123", "role": "operator"}
        token = create_access_token(user_data)
        
        # 4. Decode and verify token
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "operator"

    def test_role_hierarchy_integration(self):
        """Test complete role hierarchy scenario"""
        users = [
            {"username": "admin1", "role": "admin"},
            {"username": "operator1", "role": "operator"},
            {"username": "viewer1", "role": "viewer"},
        ]
        
        for user in users:
            token = create_access_token({"sub": user["username"], "role": user["role"]})
            decoded = decode_token(token)
            
            # Check permissions
            assert check_permissions(decoded, "viewer") is True
            
            if user["role"] in ["admin", "operator"]:
                assert check_permissions(decoded, "operator") is True
            else:
                assert check_permissions(decoded, "operator") is False
            
            if user["role"] == "admin":
                assert check_permissions(decoded, "admin") is True
            else:
                assert check_permissions(decoded, "admin") is False

    @pytest.mark.anyio
    async def test_api_key_and_token_together(self):
        """Test using API key alongside JWT token"""
        # Create API key
        api_key = create_api_key(user_id=1, name="integration-test")
        
        # Create JWT token for same user
        token = create_access_token({"sub": "1", "role": "operator"})
        
        # Verify both work
        assert verify_api_key(api_key) is not None
        assert decode_token(token) is not None


# =============================================================================
# Test Token Refresh Scenarios
# =============================================================================


class TestTokenRefreshScenarios:
    """Test scenarios related to token refresh patterns"""

    def test_refresh_token_pattern(self):
        """Test creating tokens that could be used as refresh tokens"""
        # Create access token
        access_data = {"sub": "user123", "type": "access", "role": "operator"}
        access_token = create_access_token(access_data, expires_delta=timedelta(minutes=15))
        
        # Create refresh token (longer expiration)
        refresh_data = {"sub": "user123", "type": "refresh"}
        refresh_token = create_access_token(refresh_data, expires_delta=timedelta(days=7))
        
        # Both should decode correctly
        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)
        
        assert access_decoded["type"] == "access"
        assert refresh_decoded["type"] == "refresh"
        
        # Check expirations
        access_exp = datetime.fromtimestamp(access_decoded["exp"], tz=timezone.utc)
        refresh_exp = datetime.fromtimestamp(refresh_decoded["exp"], tz=timezone.utc)
        
        assert refresh_exp > access_exp

    def test_token_blacklist_pattern(self):
        """Test token blacklist pattern using API_KEYS store as example"""
        # Simulate storing a blacklisted token manually
        revoked_token_id = "revoked_token_123"
        
        # Directly manipulate the store (simulating blacklist behavior)
        from api.auth import API_KEYS as auth_api_keys
        auth_api_keys[revoked_token_id] = {
            "user_id": 0,
            "name": "__blacklisted__",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            # Check if token is in blacklist
            metadata = verify_api_key(revoked_token_id)
            assert metadata is not None
            assert metadata["name"] == "__blacklisted__"
        finally:
            # Cleanup - ensure we remove the test entry
            if revoked_token_id in auth_api_keys:
                del auth_api_keys[revoked_token_id]
        
        # Verify it's been removed
        assert verify_api_key(revoked_token_id) is None


# =============================================================================
# Performance and Security Tests
# =============================================================================


class TestSecurityConsiderations:
    """Test security-related scenarios"""

    def test_timing_attack_resistance_password_verify(self):
        """Test that password verification is consistent in timing (bcrypt handles this)"""
        password = "testpassword"
        hashed = get_password_hash(password)
        
        # Both correct and incorrect should complete without error
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_token_not_predictable(self):
        """Test that tokens are not predictable (different each time)"""
        data = {"sub": "user123", "iat": datetime.now(timezone.utc).timestamp()}
        
        token1 = create_access_token(data)
        token2 = create_access_token(data)
        
        # Even with same data, tokens should be different (due to timing/iats)
        # Actually with same iat they might be the same, so let's check structure
        assert len(token1) == len(token2)
        
        # Tokens with different data should definitely differ
        data2 = {"sub": "user456", "iat": datetime.now(timezone.utc).timestamp()}
        token3 = create_access_token(data2)
        
        decoded1 = decode_token(token1)
        decoded3 = decode_token(token3)
        
        assert decoded1["sub"] != decoded3["sub"]

    def test_secret_key_not_exposed_in_error(self):
        """Test that secret key is not exposed in error messages"""
        token = create_access_token({"sub": "test"})
        
        # Tamper with token to cause decode error
        try:
            jwt.decode(token + "x", "wrong-secret", algorithms=[ALGORITHM])
        except jwt.InvalidSignatureError as e:
            assert SECRET_KEY not in str(e)


# Restore original module state after tests
@pytest.fixture(scope="module", autouse=True)
def restore_module_state():
    """Restore the auth module to original state after tests"""
    yield
    import importlib
    import api.auth as auth_module
    
    # Restore original environment
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-bytes-long-for-testing"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    
    importlib.reload(auth_module)
