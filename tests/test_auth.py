"""
Tests für API Authentication
"""

import pytest
import sys
import os


sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from api.auth import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)


class TestJWTToken:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=30)
        )
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_without_expiry(self):
        """Test JWT token with default expiry"""
        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
    
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        token = create_access_token(
            data={"sub": "testuser", "role": "admin"},
            expires_delta=timedelta(minutes=30)
        )
        
        payload = verify_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
    
    def test_verify_expired_token(self):
        """Test verifying an expired token"""
        # Create expired token
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=-1)  # Already expired
        )
        
        # Should raise exception or return None
        result = verify_token(token)
        assert result is None
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        result = verify_token("invalid.token.here")
        assert result is None


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
        
        # Verify the password matches
        assert verify_password(password, hashed) is True
        # Verify wrong password doesn't match
        assert verify_password("wrong", hashed) is False


class TestTokenPayload:
    """Test token payload structure"""
    
    def test_token_contains_expiry(self):
        """Test that token contains expiry time"""
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        
        assert "exp" in payload
        assert "iat" in payload
        assert payload["sub"] == "testuser"
    
    def test_token_custom_claims(self):
        """Test that token can contain custom claims"""
        token = create_access_token(data={
            "sub": "testuser",
            "role": "admin",
            "tier": "premium"
        })
        
        payload = verify_token(token)
        
        assert payload["role"] == "admin"
        assert payload["tier"] == "premium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
