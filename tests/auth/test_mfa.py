"""
Tests for Multi-Factor Authentication (TOTP)
"""

import pytest
from unittest.mock import patch, MagicMock


class TestMFAHandler:
    """Test TOTP MFA functionality"""

    def test_mfa_handler_import(self):
        """Test MFA handler can be imported"""
        from auth.mfa import MFAHandler, MFAError
        assert MFAHandler is not None

    def test_generate_secret(self):
        """Test generating TOTP secret"""
        from auth.mfa import MFAHandler
        
        handler = MFAHandler()
        secret = handler.generate_secret()
        
        assert secret is not None
        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_generate_qr_code_uri(self):
        """Test generating QR code URI"""
        from auth.mfa import MFAHandler
        
        handler = MFAHandler()
        secret = handler.generate_secret()
        uri = handler.get_qr_code_uri(
            secret=secret,
            username="testuser",
            issuer="ZenAI"
        )
        
        assert uri is not None
        assert isinstance(uri, str)
        assert "otpauth://" in uri

    def test_verify_valid_totp(self):
        """Test verifying valid TOTP code"""
        from auth.mfa import MFAHandler
        
        handler = MFAHandler()
        secret = handler.generate_secret()
        
        # Generate a code
        code = handler.generate_totp(secret)
        
        # Verify it
        is_valid = handler.verify_totp(secret, code)
        
        assert is_valid is True

    def test_verify_invalid_totp(self):
        """Test verifying invalid TOTP code"""
        from auth.mfa import MFAHandler
        
        handler = MFAHandler()
        secret = handler.generate_secret()
        
        is_valid = handler.verify_totp(secret, "000000")
        
        assert is_valid is False

    def test_generate_backup_codes(self):
        """Test generating backup codes"""
        from auth.mfa import MFAHandler
        
        handler = MFAHandler()
        codes = handler.generate_backup_codes(count=10)
        
        assert codes is not None
        assert len(codes) == 10
        assert all(isinstance(c, str) for c in codes)

    def test_verify_backup_code(self):
        """Test verifying backup code"""
        from auth.mfa import MFAHandler
        
        handler = MFAHandler()
        codes = handler.generate_backup_codes(count=10)
        
        # Verify first code
        is_valid = handler.verify_backup_code(codes[0], codes)
        
        assert is_valid is True
