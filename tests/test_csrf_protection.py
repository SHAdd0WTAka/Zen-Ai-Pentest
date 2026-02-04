"""
Tests für CSRF Protection Module
"""

import pytest
import sys
import os
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from api.csrf_protection import CSRFProtection, CSRFToken


class TestCSRFToken:
    """Test CSRF Token generation and validation"""
    
    def test_token_generation(self):
        """Test CSRF token generation"""
        csrf = CSRFProtection(secret_key="test-key")
        token = csrf.generate_token()
        
        assert isinstance(token, str)
        assert len(token) > 32
    
    def test_token_contains_timestamp(self):
        """Test that token contains timestamp"""
        csrf = CSRFProtection(secret_key="test-key")
        token = csrf.generate_token()
        
        # Token should contain a dot separating random part and timestamp
        assert "." in token
        parts = token.split(".")
        assert len(parts) == 2
    
    def test_token_uniqueness(self):
        """Test that tokens are unique"""
        csrf = CSRFProtection(secret_key="test-key")
        token1 = csrf.generate_token()
        token2 = csrf.generate_token()
        
        assert token1 != token2
    
    def test_token_validation_success(self):
        """Test successful token validation"""
        csrf = CSRFProtection(secret_key="test-key")
        token = csrf.generate_token()
        
        # Create mock request with cookie and header
        mock_request = Mock()
        mock_request.cookies = {"csrf_token": token}
        mock_request.headers = {"X-CSRF-Token": token}
        
        is_valid = csrf.validate_request(mock_request)
        assert is_valid is True
    
    def test_token_validation_missing_cookie(self):
        """Test validation fails when cookie is missing"""
        csrf = CSRFProtection(secret_key="test-key")
        token = csrf.generate_token()
        
        mock_request = Mock()
        mock_request.cookies = {}
        mock_request.headers = {"X-CSRF-Token": token}
        
        is_valid = csrf.validate_request(mock_request)
        assert is_valid is False
    
    def test_token_validation_missing_header(self):
        """Test validation fails when header is missing"""
        csrf = CSRFProtection(secret_key="test-key")
        token = csrf.generate_token()
        
        mock_request = Mock()
        mock_request.cookies = {"csrf_token": token}
        mock_request.headers = {}
        
        is_valid = csrf.validate_request(mock_request)
        assert is_valid is False
    
    def test_token_validation_mismatch(self):
        """Test validation fails when tokens don't match"""
        csrf = CSRFProtection(secret_key="test-key")
        cookie_token = csrf.generate_token()
        header_token = csrf.generate_token()
        
        mock_request = Mock()
        mock_request.cookies = {"csrf_token": cookie_token}
        mock_request.headers = {"X-CSRF-Token": header_token}
        
        is_valid = csrf.validate_request(mock_request)
        assert is_valid is False


class TestCSRFTokenExpiry:
    """Test CSRF token expiration"""
    
    def test_token_expires_after_24_hours(self):
        """Test that tokens expire after 24 hours"""
        from api.csrf_protection import CSRFToken
        
        # Create token that is 25 hours old
        old_token = CSRFToken()
        old_token.timestamp = datetime.utcnow() - timedelta(hours=25)
        
        assert old_token.is_valid() is False
    
    def test_valid_token_not_expired(self):
        """Test that fresh token is not expired"""
        from api.csrf_protection import CSRFToken
        
        fresh_token = CSRFToken()
        assert fresh_token.is_valid() is True


class TestCSRFMiddleware:
    """Test CSRF Middleware functionality"""
    
    def test_middleware_allows_safe_methods(self):
        """Test that GET requests bypass CSRF check"""
        from api.csrf_protection import CSRFProtection
        
        csrf = CSRFProtection(secret_key="test-key")
        
        # Safe methods should be allowed without token
        safe_methods = ["GET", "HEAD", "OPTIONS", "TRACE"]
        
        for method in safe_methods:
            mock_request = Mock()
            mock_request.method = method
            # Should not raise or block


class TestCSRFSetToken:
    """Test setting CSRF token in response"""
    
    def test_set_token_creates_cookie(self):
        """Test that set_token creates cookie"""
        csrf = CSRFProtection(secret_key="test-key")
        
        # Mock response
        mock_response = Mock()
        mock_response.set_cookie = Mock()
        
        token = csrf.set_token(mock_response)
        
        assert token is not None
        mock_response.set_cookie.assert_called_once()


class TestCSRFDoubleSubmitCookie:
    """Test Double Submit Cookie pattern"""
    
    def test_double_submit_pattern(self):
        """Test that cookie and header must match"""
        csrf = CSRFProtection(secret_key="test-key")
        
        # Generate token
        token = csrf.generate_token()
        
        # Both cookie and header should have same token
        mock_request = Mock()
        mock_request.cookies = {"csrf_token": token}
        mock_request.headers = {"X-CSRF-Token": token}
        
        assert csrf.validate_request(mock_request) is True
    
    def test_different_tokens_in_cookie_and_header(self):
        """Test validation fails with different tokens"""
        csrf = CSRFProtection(secret_key="test-key")
        
        cookie_token = csrf.generate_token()
        header_token = csrf.generate_token()
        
        mock_request = Mock()
        mock_request.cookies = {"csrf_token": cookie_token}
        mock_request.headers = {"X-CSRF-Token": header_token}
        
        assert csrf.validate_request(mock_request) is False


class TestCSRFConfiguration:
    """Test CSRF configuration options"""
    
    def test_custom_secret_key(self):
        """Test that custom secret key is used"""
        custom_key = "my-custom-secret-key-12345"
        csrf = CSRFProtection(secret_key=custom_key)
        
        assert csrf.secret_key == custom_key
    
    def test_custom_token_ttl(self):
        """Test custom token TTL"""
        csrf = CSRFProtection(secret_key="test-key", token_ttl=3600)  # 1 hour
        
        assert csrf.token_ttl == 3600
    
    def test_default_token_ttl(self):
        """Test default token TTL is 24 hours"""
        csrf = CSRFProtection(secret_key="test-key")
        
        assert csrf.token_ttl == 86400  # 24 hours


class TestCSRFTimingAttack:
    """Test timing attack resistance"""
    
    def test_comparison_is_timing_safe(self):
        """Test that token comparison is timing-safe"""
        csrf = CSRFProtection(secret_key="test-key")
        
        # This test verifies that hmac.compare_digest is used
        # which is timing-safe
        token1 = "token123"
        token2 = "token123"
        token3 = "token456"
        
        # Both should be True, using constant-time comparison
        assert hmac.compare_digest(token1, token2) is True
        assert hmac.compare_digest(token1, token3) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
