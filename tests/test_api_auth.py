"""
Tests for api/auth.py - JWT Authentication
Target: 90%+ Coverage
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordFunctions:
    """Test password hashing and verification"""

    def test_get_password_hash_returns_string(self):
        """Test that hashing returns a string"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 20  # bcrypt hashes are long

    def test_get_password_hash_different_each_time(self):
        """Test that same password produces different hashes (salt)"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2  # Different salts

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password"""
        password = ""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("notempty", hashed) is False


class TestJWTTokenFunctions:
    """Test JWT token creation and validation"""

    def test_create_access_token_returns_string(self):
        """Test token creation returns string"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_access_token_contains_data(self):
        """Test that created token contains the data"""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)

        # Decode and verify
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"

    def test_create_access_token_has_expiration(self):
        """Test that token has expiration"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in decoded

    def test_create_access_token_default_expiration(self):
        """Test default expiration time"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = decoded["exp"]

        # Should be roughly 30 minutes from now
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        actual_exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        diff = abs((expected_exp - actual_exp).total_seconds())
        assert diff < 60  # Within 1 minute

    def test_create_access_token_custom_expiration(self):
        """Test custom expiration time"""
        data = {"sub": "testuser"}
        custom_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta=custom_delta)

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = decoded["exp"]

        expected_exp = datetime.now(timezone.utc) + timedelta(hours=2)
        actual_exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        diff = abs((expected_exp - actual_exp).total_seconds())
        assert diff < 60


class TestConfiguration:
    """Test configuration loading"""

    def test_secret_key_exists(self):
        """Test that SECRET_KEY is set"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 10

    def test_algorithm_is_hs256(self):
        """Test that algorithm is HS256"""
        assert ALGORITHM == "HS256"

    def test_access_token_expire_minutes_is_int(self):
        """Test that expire minutes is an integer"""
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0


class TestIntegration:
    """Integration tests for auth flow"""

    def test_full_auth_flow(self):
        """Test complete auth flow: hash password, create token"""
        # 1. Hash password
        password = "mypassword"
        hashed = get_password_hash(password)

        # 2. Verify password
        assert verify_password(password, hashed)

        # 3. Create token
        user_data = {"sub": "testuser", "role": "user"}
        token = create_access_token(user_data)

        # 4. Verify token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "user"

    def test_multiple_users(self):
        """Test auth with multiple users"""
        users = [
            {"username": "user1", "password": "pass1", "role": "admin"},
            {"username": "user2", "password": "pass2", "role": "user"},
            {"username": "user3", "password": "pass3", "role": "viewer"},
        ]

        for user in users:
            # Hash and verify
            hashed = get_password_hash(user["password"])
            assert verify_password(user["password"], hashed)

            # Create token
            token = create_access_token(
                {"sub": user["username"], "role": user["role"]}
            )
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            assert decoded["sub"] == user["username"]
            assert decoded["role"] == user["role"]


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_password_with_special_characters(self):
        """Test password with special characters"""
        password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_password_with_unicode(self):
        """Test password with unicode characters"""
        password = "пароль密码パスワード"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_very_long_password(self):
        """Test very long password"""
        password = "a" * 1000
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)

    def test_token_with_complex_data(self):
        """Test token with complex nested data"""
        data = {
            "sub": "user",
            "permissions": ["read", "write", "delete"],
            "metadata": {"last_login": "2024-01-01", "ip": "127.0.0.1"},
        }
        token = create_access_token(data)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == "user"
        assert "read" in decoded["permissions"]
        assert decoded["metadata"]["ip"] == "127.0.0.1"
