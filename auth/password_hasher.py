"""
Password Hasher Module
======================

Secure password hashing using bcrypt (fallback from Argon2id)

Features:
- bcrypt algorithm (widely supported)
- Secure salt generation
- Constant-time verification
- Password strength validation

Note: Using bcrypt instead of Argon2id due to system package constraints.
For production, consider upgrading to Argon2id.
"""

import re
from typing import Optional, Tuple

# Try to use passlib's bcrypt
from passlib.context import CryptContext


class PasswordStrengthError(Exception):
    """Password does not meet strength requirements"""

    pass


class PasswordHashError(Exception):
    """Error during password hashing"""

    pass


class PasswordVerificationError(Exception):
    """Error during password verification"""

    pass


class PasswordHasher:
    """
    Secure password hashing using bcrypt

    Uses passlib's CryptContext with bcrypt for password hashing.
    Provides secure password storage with automatic salt generation.
    """

    def __init__(self):
        """Initialize password hasher with bcrypt context"""
        self._context = CryptContext(
            schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12
        )  # Work factor

    def hash(self, password: str) -> str:
        """
        Hash a password

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        try:
            return self._context.hash(password)
        except Exception as e:
            raise PasswordHashError(f"Failed to hash password: {e}")

    def verify(self, password: str, hash_value: str) -> bool:
        """
        Verify a password against a hash

        Args:
            password: Plain text password to verify
            hash_value: Stored hash to verify against

        Returns:
            bool: True if password matches
        """
        try:
            return self._context.verify(password, hash_value)
        except Exception:
            return False

    def needs_rehash(self, hash_value: str) -> bool:
        """
        Check if password needs rehashing (e.g., parameters changed)

        Args:
            hash_value: Current password hash

        Returns:
            bool: True if rehash is recommended
        """
        return self._context.needs_update(hash_value)

    @staticmethod
    def validate_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength

        Requirements:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

        Args:
            password: Password to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters long"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return (
                False,
                "Password must contain at least one special character",
            )

        return True, None

    def hash_with_validation(self, password: str) -> str:
        """
        Hash password with strength validation

        Args:
            password: Password to hash

        Returns:
            str: Hashed password

        Raises:
            PasswordStrengthError: If password doesn't meet requirements
        """
        is_valid, error = self.validate_strength(password)
        if not is_valid:
            raise PasswordStrengthError(error)

        return self.hash(password)


# Global instance for convenience
_default_hasher = None


def get_password_hasher() -> PasswordHasher:
    """Get default password hasher instance"""
    global _default_hasher
    if _default_hasher is None:
        _default_hasher = PasswordHasher()
    return _default_hasher


def hash_password(password: str) -> str:
    """Convenience function to hash a password"""
    return get_password_hasher().hash(password)


def verify_password(password: str, hash_value: str) -> bool:
    """Convenience function to verify a password"""
    return get_password_hasher().verify(password, hash_value)
