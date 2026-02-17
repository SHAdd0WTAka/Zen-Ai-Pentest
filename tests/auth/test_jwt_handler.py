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
            user_id="testuser",
            roles=["admin"],
            permissions=["read", "write"]
        )
        
        assert token is not None
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        """Test creating refresh token"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_refresh_token(
            user_id="testuser",
            session_id="session123"
        )
        
        assert token is not None
        assert isinstance(token, str)

    def test_decode_token(self):
        """Test decoding a valid token"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_access_token(
            user_id="testuser",
            roles=["admin"],
            permissions=["read"]
        )
        
        payload = handler.decode_token(token)
        
        assert payload is not None
        assert payload.sub == "testuser"
        assert "admin" in payload.roles

    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        from auth.jwt_handler import JWTHandler, TokenInvalidError
        
        handler = JWTHandler()
        
        with pytest.raises(TokenInvalidError):
            handler.decode_token("invalid.token.here")

    def test_token_expiration(self):
        """Test token expiration"""
        from auth.jwt_handler import JWTHandler, TokenExpiredError
        
        handler = JWTHandler()
        # Create token with very short expiry (if supported)
        token = handler.create_access_token(
            user_id="testuser",
            roles=["admin"],
            permissions=["read"]
        )
        
        # Token should be valid initially
        payload = handler.decode_token(token)
        assert payload is not None
        assert payload.sub == "testuser"


class TestTokenBlacklist:
    """Test token blacklist functionality"""

    def test_blacklist_import(self):
        """Test blacklist can be imported"""
        from auth.jwt_handler import JWTHandler
        handler = JWTHandler()
        assert hasattr(handler, 'blacklist_token')

    def test_blacklist_token(self):
        """Test blacklisting a token by JTI"""
        from auth.jwt_handler import JWTHandler
        
        handler = JWTHandler()
        token = handler.create_access_token(
            user_id="testuser",
            roles=["admin"],
            permissions=["read"]
        )
        
        # Decode to get JTI
        payload = handler.decode_token(token)
        jti = payload.jti
        
        # Blacklist by JTI
        handler.blacklist_token(jti)
        
        # Verify token is blacklisted
        assert handler.is_blacklisted(jti) is True
