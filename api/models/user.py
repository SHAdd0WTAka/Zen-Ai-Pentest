"""User model stub for CI/CD compatibility."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class UserRole(Enum):
    """User role enumeration."""

    USER = 1
    ADMIN = 2
    SUPERADMIN = 3


class User:
    """Stub User model for CI/CD compatibility."""

    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
    ):
        """Initialize user."""
        self.id = "stub-id"
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.full_name = full_name
        self.role = role
        self.is_active = is_active
        self.created_at = datetime.utcnow()
        self.last_login: Optional[datetime] = None

    @classmethod
    async def find_one(cls, **kwargs) -> Optional["User"]:
        """Stub find method - returns None for CI/CD."""
        return None

    async def save(self) -> None:
        """Stub save method."""
        pass

    async def update_last_login(self) -> None:
        """Stub update last login."""
        self.last_login = datetime.utcnow()

    def to_response(self) -> Dict[str, Any]:
        """Convert to response dict."""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.name,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
