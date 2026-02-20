"""
Multi-Factor Authentication (MFA) Module
=========================================

TOTP-based MFA implementation with backup codes

Features:
- TOTP (Time-based One-Time Password) generation
- QR code generation for authenticator apps
- Backup codes for account recovery
- Secure secret storage

Note: Using simplified implementation. For production, install pyotp and qrcode.
"""

import base64
import hashlib
import hmac
import secrets
import time
from typing import List, Optional


class MFAError(Exception):
    """MFA operation error"""

    pass


class MFAHandler:
    """
    Handler for Multi-Factor Authentication operations

    Implements TOTP (RFC 6238) for time-based one-time passwords
    compatible with Google Authenticator, Authy, and similar apps.
    """

    def __init__(self, digits: int = 6, interval: int = 30):
        """
        Initialize MFA handler

        Args:
            digits: Number of digits in TOTP code (default: 6)
            interval: Time interval in seconds (default: 30)
        """
        self.digits = digits
        self.interval = interval

    def generate_secret(self) -> str:
        """
        Generate a new random secret

        Returns:
            str: Base32-encoded secret
        """
        # Generate 20 random bytes (160 bits)
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")

    def _get_counter(self, timestamp: Optional[float] = None) -> int:
        """Get counter value for TOTP"""
        if timestamp is None:
            timestamp = time.time()
        return int(timestamp) // self.interval

    def _generate_hotp(self, secret: str, counter: int) -> str:
        """Generate HOTP code"""
        # Decode base32 secret
        secret = secret.upper()
        # Add padding if needed
        padding = 8 - (len(secret) % 8)
        if padding != 8:
            secret += "=" * padding

        key = base64.b32decode(secret)
        counter_bytes = counter.to_bytes(8, byteorder="big")

        # HMAC-SHA1
        mac = hmac.new(key, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation
        offset = mac[-1] & 0x0F
        code = (
            (mac[offset] & 0x7F) << 24
            | (mac[offset + 1] & 0xFF) << 16
            | (mac[offset + 2] & 0xFF) << 8
            | (mac[offset + 3] & 0xFF)
        )

        # Modulo to get desired number of digits
        code = code % (10**self.digits)

        return str(code).zfill(self.digits)

    def generate_totp(self, secret: str, timestamp: Optional[float] = None) -> str:
        """
        Generate TOTP code

        Args:
            secret: Base32-encoded secret
            timestamp: Optional timestamp (default: current time)

        Returns:
            str: TOTP code
        """
        counter = self._get_counter(timestamp)
        return self._generate_hotp(secret, counter)

    def verify_totp(self, secret: str, code: str, window: int = 1) -> bool:
        """
        Verify TOTP code with time window

        Args:
            secret: Base32-encoded secret
            code: TOTP code to verify
            window: Number of intervals to check before/after (default: 1)

        Returns:
            bool: True if code is valid
        """
        if not code or not code.isdigit() or len(code) != self.digits:
            return False

        current_counter = self._get_counter()

        # Check current and adjacent time windows
        for i in range(-window, window + 1):
            expected = self._generate_hotp(secret, current_counter + i)
            if hmac.compare_digest(code, expected):
                return True

        return False

    def get_qr_code_uri(self, secret: str, username: str, issuer: str = "ZenAI") -> str:
        """
        Generate otpauth URI for QR code

        Args:
            secret: Base32-encoded secret
            username: User identifier
            issuer: Service name

        Returns:
            str: otpauth:// URI
        """
        # URL encode parameters
        label = f"{issuer}:{username}"
        return (
            f"otpauth://totp/{label}?"
            f"secret={secret}&"
            f"issuer={issuer}&"
            f"algorithm=SHA1&"
            f"digits={self.digits}&"
            f"period={self.interval}"
        )

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of codes to generate (default: 10)

        Returns:
            List[str]: List of backup codes
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
            codes.append(code)
        return codes

    def verify_backup_code(self, code: str, valid_codes: List[str]) -> bool:
        """
        Verify a backup code

        Args:
            code: Code to verify
            valid_codes: List of valid backup codes

        Returns:
            bool: True if code is valid
        """
        code = code.upper().replace("-", "").replace(" ", "")
        for valid in valid_codes:
            if hmac.compare_digest(code, valid):
                return True
        return False


# Global instance
_default_mfa = None


def get_mfa_handler() -> MFAHandler:
    """Get default MFA handler instance"""
    global _default_mfa
    if _default_mfa is None:
        _default_mfa = MFAHandler()
    return _default_mfa
