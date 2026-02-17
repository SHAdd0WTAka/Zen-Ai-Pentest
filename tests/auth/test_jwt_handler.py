"""
Tests for JWT Handler
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestJWTHandler:
    """Test JWT token handling"""

    def test_jwt_handler_import(self):
        """Test JWT handler can be imported"""
        from auth.jwt_handler import JWTHandler
        assert JWTHandler is not None

    def test_create_access_token(self):
        """Test creating access token"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_access_token(
            data={"sub": "testuser", "role": "admin"}
        )
        
        assert token is not None
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        """Test creating refresh token"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_refresh_token(
            data={"sub": "testuser"}
        )
        
        assert token is not None
        assert isinstance(token, str)

    def test_decode_token(self):
        """Test decoding a valid token"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_access_token(
            data={"sub": "testuser", "role": "admin"}
        )
        
        payload = handler.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"

    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        payload = handler.decode_token("invalid.token.here")
        
        assert payload is None

    def test_token_expiration(self):
        """Test token expiration"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        payload = handler.decode_token(token)
        assert payload is None  # Should be expired


class TestTokenBlacklist:
    """Test token blacklist functionality"""

    def test_blacklist_token(self):
        """Test blacklisting a token"""
        from auth.jwt_handler import TokenBlacklist
        
        blacklist = TokenBlacklist()
        token = "test.token.here"
        
        blacklist.blacklist(token)
        
        assert blacklist.is_blacklisted(token) is True

    def test_is_not_blacklisted(self):
        """Test checking non-blacklisted token"""
        from auth.jwt_handler import TokenBlacklist
        
        blacklist = TokenBlacklist()
        
        assert blacklist.is_blacklisted("not.blacklisted") is False
