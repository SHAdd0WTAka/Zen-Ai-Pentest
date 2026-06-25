"""
Tests für Legacy API Authentication
====================================

These tests use the api/auth.py legacy module.
"""

import os
import sys

import pytest

# Set up paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt"
os.environ["JWT_ALGORITHM"] = "HS256"
from datetime import timedelta

os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# Import from legacy auth module (api/auth.py)
from api.auth import create_access_token, get_password_hash, verify_password


class TestJWTToken:
    """Test JWT token creation"""

    def test_create_access_token(self):
        """Test JWT token creation"""
        token = create_access_token(data={"sub": "testuser"}, expires_delta=timedelta(minutes=30))
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_without_expiry(self):
        """Test JWT token with default expiry"""
        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)


class TestPasswordHashing:
    """Test password hashing functions"""

    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        """Test verifying correct password"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verifying wrong password"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        assert hash1 != hash2


class TestUserAuthentication:
    """Test user authentication functions that exist"""

    def test_password_hashing_integration(self):
        """Test password hashing works correctly"""
        password = "admin"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
