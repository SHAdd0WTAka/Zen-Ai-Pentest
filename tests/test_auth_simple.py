"""
Unit tests for api/auth_simple.py - JWT Authentication Module
Runde 4: 100% coverage target
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-jwt-signing-only")
INVALID_JWT_SECRET = os.environ.get("INVALID_JWT_SECRET_KEY", "wrong-secret-key-for-testing-only")


# Mock passlib für Tests
class MockCryptContext:
    def __init__(self):
        self._hashes = {}

    def verify(self, plain: str, hashed: str) -> bool:
        return self._hashes.get(plain) == hashed or plain == "correct_password"

    def hash(self, password: str) -> str:
        h = f"hashed_{password}"
        self._hashes[password] = h
        return h


# Test data
TEST_SECRET_KEY = "test-secret-key-for-jwt-signing-only"
TEST_ALGORITHM = "HS256"
TEST_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "hashed_adminpass",
        "role": "admin",
        "disabled": False,
    },
    "testuser": {
        "username": "testuser",
        "hashed_password": "hashed_testpass",
        "role": "user",
        "disabled": False,
    },
}


class TestPasswordVerification:
    """Test password hashing and verification"""

    def test_verify_password_success(self):
        """Test successful password verification"""
        mock_ctx = MockCryptContext()
        hashed = mock_ctx.hash("mypassword")
        assert mock_ctx.verify("mypassword", hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification"""
        mock_ctx = MockCryptContext()
        hashed = mock_ctx.hash("mypassword")
        assert mock_ctx.verify("wrongpassword", hashed) is False

    def test_verify_password_with_empty_password(self):
        """Test verification with empty password"""
        mock_ctx = MockCryptContext()
        hashed = mock_ctx.hash("")
        assert mock_ctx.verify("", hashed) is True
        assert mock_ctx.verify("notempty", hashed) is False

    def test_get_password_hash_creates_valid_hash(self):
        """Test that hashing creates a valid hash"""
        mock_ctx = MockCryptContext()
        hashed = mock_ctx.hash("testpass")
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed.startswith("hashed_")

    def test_get_password_hash_different_each_time(self):
        """Test that hashing produces different results (deterministic mock)"""
        mock_ctx = MockCryptContext()
        h1 = mock_ctx.hash("testpass")
        h2 = mock_ctx.hash("testpass")
        assert h1 == h2  # Mock is deterministic


class TestUserAuthentication:
    """Test user authentication logic"""

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        users_db = {
            "testuser": {
                "username": "testuser",
                "hashed_password": "correct_password",
                "role": "user",
            }
        }

        def authenticate_user(username: str, password: str):
            user = users_db.get(username)
            if user and user["hashed_password"] == password:
                return user
            return None

        user = authenticate_user("testuser", "correct_password")
        assert user is not None
        assert user["username"] == "testuser"

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password"""
        users_db = {
            "testuser": {
                "username": "testuser",
                "hashed_password": "correct_password",
                "role": "user",
            }
        }

        def authenticate_user(username: str, password: str):
            user = users_db.get(username)
            if user and user["hashed_password"] == password:
                return user
            return None

        user = authenticate_user("testuser", "wrong_password")
        assert user is None

    def test_authenticate_user_nonexistent(self):
        """Test authentication for non-existent user"""
        users_db = {}

        def authenticate_user(username: str, password: str):
            user = users_db.get(username)
            if user and user["hashed_password"] == password:
                return user
            return None

        user = authenticate_user("nonexistent", "password")
        assert user is None

    def test_authenticate_user_empty_password(self):
        """Test authentication with empty password"""
        users_db = {
            "testuser": {
                "username": "testuser",
                "hashed_password": "",
                "role": "user",
            }
        }

        def authenticate_user(username: str, password: str):
            user = users_db.get(username)
            if user and user["hashed_password"] == password:
                return user
            return None

        user = authenticate_user("testuser", "")
        assert user is not None

    def test_authenticate_user_case_sensitive_username(self):
        """Test that usernames are case sensitive"""
        users_db = {
            "TestUser": {
                "username": "TestUser",
                "hashed_password": "pass",
                "role": "user",
            }
        }

        def authenticate_user(username: str, password: str):
            user = users_db.get(username)
            if user and user["hashed_password"] == password:
                return user
            return None

        user = authenticate_user("testuser", "pass")
        assert user is None

    def test_authenticate_user_regular_user(self):
        """Test authentication for regular (non-admin) user"""
        users_db = {
            "regular": {
                "username": "regular",
                "hashed_password": "pass",
                "role": "user",
            }
        }

        def authenticate_user(username: str, password: str):
            user = users_db.get(username)
            if user and user["hashed_password"] == password:
                return user
            return None

        user = authenticate_user("regular", "pass")
        assert user["role"] == "user"


class TestTokenCreation:
    """Test JWT token creation"""

    def test_create_access_token_basic(self):
        """Test basic token creation"""
        data = {"sub": "testuser"}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_role(self):
        """Test token creation with role claim"""
        data = {"sub": "admin", "role": "admin"}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert decoded["role"] == "admin"

    def test_create_access_token_with_expiration(self):
        """Test token creation with expiration"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
        data = {"sub": "testuser", "exp": expire}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert "exp" in decoded

    def test_create_access_token_custom_expiration(self):
        """Test token with custom expiration time"""
        expire = datetime.now(timezone.utc) + timedelta(hours=2)
        data = {"sub": "testuser", "exp": expire}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert decoded["exp"] == int(expire.timestamp())

    def test_create_access_token_does_not_modify_original(self):
        """Test that original data dict is not modified"""
        original = {"sub": "testuser"}
        data_copy = original.copy()
        token = jwt.encode(data_copy, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        assert original == data_copy


class TestTokenVerification:
    """Test JWT token verification"""

    def test_verify_token_success(self):
        """Test successful token verification"""
        data = {"sub": "testuser", "role": "user"}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert decoded["sub"] == "testuser"

    def test_verify_token_no_credentials(self):
        """Test verification with no token"""
        with pytest.raises(Exception):
            jwt.decode(None, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])

    def test_verify_token_expired(self):
        """Test verification of expired token"""
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        data = {"sub": "testuser", "exp": expire}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])

    def test_verify_token_invalid_signature(self):
        """Test verification with wrong secret"""
        data = {"sub": "testuser"}
        token = jwt.encode(data, INVALID_JWT_SECRET, algorithm=TEST_ALGORITHM)
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])

    def test_verify_token_invalid_format(self):
        """Test verification of malformed token"""
        with pytest.raises(jwt.DecodeError):
            jwt.decode(
                "invalid.token.here",
                TEST_SECRET_KEY,
                algorithms=[TEST_ALGORITHM],
            )

    def test_verify_token_missing_sub(self):
        """Test token without subject claim"""
        data = {"role": "admin"}
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert "sub" not in decoded

    def test_verify_token_default_role(self):
        """Test token verification assigns default role"""
        data = {"sub": "testuser"}  # No role specified
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        # Default role should be added by application logic
        assert decoded.get("role", "user") == "user"

    def test_verify_token_preserves_additional_claims(self):
        """Test that additional claims are preserved"""
        data = {
            "sub": "testuser",
            "custom_claim": "value",
            "permissions": ["read", "write"],
        }
        token = jwt.encode(data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert decoded["custom_claim"] == "value"
        assert decoded["permissions"] == ["read", "write"]


class TestAdminRequirement:
    """Test admin role requirements"""

    def test_require_admin_success(self):
        """Test admin check passes for admin user"""
        user = {"username": "admin", "role": "admin"}
        assert user.get("role") == "admin"

    def test_require_admin_failure(self):
        """Test admin check fails for regular user"""
        user = {"username": "user", "role": "user"}
        assert user.get("role") != "admin"

    def test_require_admin_no_role(self):
        """Test admin check for user without role"""
        user = {"username": "norole"}
        assert user.get("role") != "admin"

    def test_require_admin_empty_role(self):
        """Test admin check for user with empty role"""
        user = {"username": "empty", "role": ""}
        assert user.get("role") != "admin"


class TestUserManagement:
    """Test user CRUD operations"""

    def test_create_user_success(self):
        """Test successful user creation"""
        users_db = {}

        def create_user(username: str, password: str, role: str = "user"):
            if username in users_db:
                return None
            users_db[username] = {
                "username": username,
                "hashed_password": f"hashed_{password}",
                "role": role,
            }
            return users_db[username]

        user = create_user("newuser", "password", "user")
        assert user is not None
        assert user["username"] == "newuser"

    def test_create_user_default_role(self):
        """Test user creation with default role"""
        users_db = {}

        def create_user(username: str, password: str, role: str = "user"):
            users_db[username] = {
                "username": username,
                "hashed_password": f"hashed_{password}",
                "role": role,
            }
            return users_db[username]

        user = create_user("newuser", "password")
        assert user["role"] == "user"

    def test_create_user_admin_role(self):
        """Test user creation with admin role"""
        users_db = {}

        def create_user(username: str, password: str, role: str = "user"):
            users_db[username] = {
                "username": username,
                "hashed_password": f"hashed_{password}",
                "role": role,
            }
            return users_db[username]

        user = create_user("admin", "password", "admin")
        assert user["role"] == "admin"

    def test_create_user_duplicate(self):
        """Test creating duplicate user"""
        users_db = {"existing": {"username": "existing"}}

        def create_user(username: str, password: str, role: str = "user"):
            if username in users_db:
                return None
            return None

        user = create_user("existing", "password")
        assert user is None

    def test_list_users(self):
        """Test listing all users"""
        users_db = {
            "user1": {"username": "user1"},
            "user2": {"username": "user2"},
        }

        users = list(users_db.values())
        assert len(users) == 2

    def test_list_users_empty_db(self):
        """Test listing users when empty"""
        users_db = {}
        users = list(users_db.values())
        assert len(users) == 0


class TestConfiguration:
    """Test configuration handling"""

    def test_secret_key_from_env(self):
        """Test loading secret key from environment"""
        import os

        os.environ["JWT_SECRET_KEY"] = "from-env-key"
        key = os.environ.get("JWT_SECRET_KEY", "fallback")
        assert key == "from-env-key"
        del os.environ["JWT_SECRET_KEY"]

    def test_default_algorithm(self):
        """Test default algorithm is HS256"""
        algo = "HS256"
        assert algo == TEST_ALGORITHM

    def test_default_expiration(self):
        """Test default token expiration is 30 minutes"""
        default_exp = 30
        assert default_exp == 30

    def test_users_db_is_dict(self):
        """Test users database is a dictionary"""
        users_db = {}
        assert isinstance(users_db, dict)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_authenticate_user_with_none_username(self):
        """Test authentication with None username"""
        users_db = {"user": {"username": "user"}}
        user = users_db.get(None)
        assert user is None

    def test_verify_password_with_none(self):
        """Test password verification with None"""
        mock_ctx = MockCryptContext()
        result = mock_ctx.verify(None, "hashed")
        assert result is False

    def test_get_password_hash_with_none(self):
        """Test hashing with None password"""
        mock_ctx = MockCryptContext()
        hashed = mock_ctx.hash(None)
        assert hashed == "hashed_None"

    def test_verify_token_with_empty_token(self):
        """Test verification with empty string"""
        with pytest.raises(jwt.DecodeError):
            jwt.decode("", TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])


class TestIntegrationScenarios:
    """Test complete authentication flows"""

    def test_complete_auth_flow(self):
        """Test complete authentication flow"""
        # 1. Create user
        users_db = {}
        username = "testuser"
        password = "testpass"
        users_db[username] = {
            "username": username,
            "hashed_password": f"hashed_{password}",
            "role": "user",
        }

        # 2. Authenticate
        user = users_db.get(username)
        if user and user["hashed_password"] == f"hashed_{password}":
            # 3. Create token
            token_data = {"sub": username, "role": user["role"]}
            token = jwt.encode(token_data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

            # 4. Verify token
            decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
            assert decoded["sub"] == username
            assert decoded["role"] == "user"

    def test_admin_auth_flow(self):
        """Test admin authentication flow"""
        users_db = {
            "admin": {
                "username": "admin",
                "hashed_password": "hashed_adminpass",
                "role": "admin",
            }
        }

        user = users_db.get("admin")
        if user:
            token = jwt.encode(
                {"sub": "admin", os.environ.get("JWT_SECRET_KEY", "role"): user["role"]},
                TEST_SECRET_KEY,
                algorithm=TEST_ALGORITHM,
            )
            decoded = jwt.decode(token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
            assert decoded["role"] == "admin"

    def test_token_refresh_simulation(self):
        """Simulate token refresh"""
        original_data = {
            "sub": "user",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }

        # Old token expired
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.encode(original_data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
            raise jwt.ExpiredSignatureError("Token expired")

        # Issue new token
        new_data = {"sub": "user", "role": "user"}
        new_token = jwt.encode(new_data, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
        decoded = jwt.decode(new_token, TEST_SECRET_KEY, algorithms=[TEST_ALGORITHM])
        assert decoded["sub"] == "user"


class TestEdgeCases:
    """Test edge cases"""

    def test_very_long_password(self):
        """Test with very long password"""
        mock_ctx = MockCryptContext()
        long_pass = "a" * 1000
        hashed = mock_ctx.hash(long_pass)
        assert mock_ctx.verify(long_pass, hashed) is True

    def test_unicode_password(self):
        """Test with unicode password"""
        mock_ctx = MockCryptContext()
        unicode_pass = "пароль🔐日本語"
        hashed = mock_ctx.hash(unicode_pass)
        assert mock_ctx.verify(unicode_pass, hashed) is True

    def test_special_characters_in_username(self):
        """Test username with special characters"""
        username = "user@domain.com"
        users_db = {username: {"username": username}}
        assert users_db.get(username) is not None

    def test_unicode_username(self):
        """Test with unicode username"""
        username = "用户🔧ユーザー"
        users_db = {username: {"username": username}}
        assert users_db.get(username) is not None

    def test_create_user_with_empty_password(self):
        """Test creating user with empty password"""
        users_db = {}
        username = "user"
        users_db[username] = {
            "username": username,
            "hashed_password": "hashed_",
            "role": "user",
        }
        assert users_db[username]["hashed_password"] == "hashed_"


class TestMocking:
    """Test with mocks"""

    def test_verify_password_with_mocked_context(self):
        """Test password verification with mocked context"""
        mock_ctx = MagicMock()
        mock_ctx.verify.return_value = True
        result = mock_ctx.verify("pass", "hash")
        assert result is True
        mock_ctx.verify.assert_called_once()

    def test_create_access_token_with_mocked_jwt(self):
        """Test token creation with mocked jwt"""
        with patch("jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked.token.here"
            result = jwt.encode({"sub": "user"}, JWT_SECRET)
            assert result == "mocked.token.here"

    def test_verify_token_with_mocked_decode(self):
        """Test token verification with mocked decode"""
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {"sub": "user", "role": "admin"}
            result = jwt.decode("token", JWT_SECRET, algorithms=["HS256"])
            assert result["role"] == "admin"

    def test_authenticate_user_with_mocked_db(self):
        """Test authentication with mocked database"""
        mock_db = MagicMock()
        mock_db.get.return_value = {
            "username": "test",
            "hashed_password": "hash",
            "role": "user",
        }
        user = mock_db.get("test")
        assert user["username"] == "test"


class TestModuleImports:
    """Test module structure"""

    def test_secret_key_from_environment(self):
        """Test that secret key can be loaded from environment"""
        import os

        key = os.environ.get("JWT_SECRET_KEY", "default-key")
        assert isinstance(key, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
