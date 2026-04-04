"""
API Key Management Module
=========================

Secure API key generation and validation with:
- Cryptographically secure key generation
- Key hashing for storage
- Expiration tracking
- Usage statistics
- Key revocation

Compliance: OWASP ASVS 2026 V3.5, ISO 27001 A.9.4
"""

import base64
import hashlib
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from .config import APIKeyConfig, get_config


class APIKeyStatus(Enum):
    """API key status"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class APIKey:
    """API Key data structure"""

    id: str
    user_id: str
    name: str
    key_hash: str  # Hashed key for storage
    key_preview: str  # First/last few characters for display
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    status: APIKeyStatus
    permissions: List[str] = field(default_factory=list)
    allowed_ips: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class APIKeyCreationResult:
    """Result of API key creation"""

    api_key: APIKey
    plain_key: str  # The plain key (shown only once)


class APIKeyError(Exception):
    """Base API key error"""

    pass


class APIKeyNotFoundError(APIKeyError):
    """API key not found"""

    pass


class APIKeyRevokedError(APIKeyError):
    """API key has been revoked"""

    pass


class APIKeyExpiredError(APIKeyError):
    """API key has expired"""

    pass


class APIKeyLimitExceededError(APIKeyError):
    """Maximum number of API keys exceeded"""

    pass


class APIKeyManager:
    """
    API Key Manager

    Manages API key lifecycle:
    - Generation
    - Storage (hashed)
    - Validation
    - Revocation
    - Usage tracking
    """

    def __init__(self, config: Optional[APIKeyConfig] = None):
        self.config = config or get_config().api_key
        self._keys: Dict[str, APIKey] = {}  # key_hash -> APIKey
        self._user_keys: Dict[str, Set[str]] = {}  # user_id -> set of key_hashes

    def _generate_key(self) -> str:
        """
        Generate a cryptographically secure API key

        Returns:
            Plain API key string
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(self.config.key_length)

        # Encode to URL-safe base64
        key = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")

        # Add prefix
        return f"{self.config.key_prefix}{key}"

    def _hash_key(self, key: str) -> str:
        """
        Hash an API key for secure storage

        Args:
            key: Plain API key

        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def _create_key_preview(self, key: str) -> str:
        """
        Create a preview of the key for display

        Shows first 4 and last 4 characters, masks the rest.

        Args:
            key: Plain API key

        Returns:
            Masked key preview
        """
        if len(key) <= 12:
            return "****"
        return f"{key[:4]}...{key[-4:]}"

    def create_api_key(
        self,
        user_id: str,
        name: str,
        expires_in_days: Optional[int] = None,
        permissions: Optional[List[str]] = None,
        allowed_ips: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> APIKeyCreationResult:
        """
        Create a new API key for a user

        Args:
            user_id: User identifier
            name: Human-readable name for the key
            expires_in_days: Days until expiration (None for default)
            permissions: List of permissions for this key
            allowed_ips: List of allowed IP addresses
            rate_limit: Custom rate limit for this key
            metadata: Additional metadata

        Returns:
            APIKeyCreationResult with key and metadata

        Raises:
            APIKeyLimitExceededError: If user has too many keys
        """
        # Check key limit
        user_key_count = len(self._user_keys.get(user_id, set()))
        if user_key_count >= self.config.max_keys_per_user:
            raise APIKeyLimitExceededError(f"Maximum of {self.config.max_keys_per_user} API keys allowed per user")

        # Generate key
        plain_key = self._generate_key()
        key_hash = self._hash_key(plain_key)

        # Calculate expiration
        if expires_in_days is None:
            expires_in_days = self.config.default_expiry_days

        expires_at = None
        if expires_in_days > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Create API key object
        api_key = APIKey(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_preview=self._create_key_preview(plain_key),
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            last_used_at=None,
            usage_count=0,
            status=APIKeyStatus.ACTIVE,
            permissions=permissions or [],
            allowed_ips=allowed_ips,
            rate_limit=rate_limit,
            metadata=metadata or {},
        )

        # Store key
        self._keys[key_hash] = api_key

        # Add to user's keys
        if user_id not in self._user_keys:
            self._user_keys[user_id] = set()
        self._user_keys[user_id].add(key_hash)

        return APIKeyCreationResult(
            api_key=api_key,
            plain_key=plain_key,
        )

    def validate_api_key(self, key: str, ip_address: Optional[str] = None) -> Optional[APIKey]:
        """
        Validate an API key

        Args:
            key: Plain API key to validate
            ip_address: Optional client IP for IP restriction check

        Returns:
            APIKey if valid, None otherwise

        Raises:
            APIKeyRevokedError: If key has been revoked
            APIKeyExpiredError: If key has expired
        """
        key_hash = self._hash_key(key)

        # Find key
        api_key = self._keys.get(key_hash)
        if not api_key:
            return None

        # Check status
        if api_key.status == APIKeyStatus.REVOKED:
            raise APIKeyRevokedError("API key has been revoked")

        if api_key.status == APIKeyStatus.SUSPENDED:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            api_key.status = APIKeyStatus.EXPIRED
            raise APIKeyExpiredError("API key has expired")

        # Check IP restriction
        if api_key.allowed_ips and ip_address:
            if ip_address not in api_key.allowed_ips:
                return None

        return api_key

    def record_usage(self, key: str) -> None:
        """
        Record API key usage

        Args:
            key: Plain API key
        """
        key_hash = self._hash_key(key)
        api_key = self._keys.get(key_hash)

        if api_key:
            api_key.last_used_at = datetime.now(timezone.utc)
            api_key.usage_count += 1

    def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """
        Revoke an API key

        Args:
            user_id: User identifier
            key_id: API key ID

        Returns:
            True if key was revoked
        """
        # Find key by ID for this user
        for key_hash in self._user_keys.get(user_id, set()):
            api_key = self._keys.get(key_hash)
            if api_key and api_key.id == key_id:
                api_key.status = APIKeyStatus.REVOKED
                return True

        return False

    def revoke_all_user_keys(self, user_id: str, reason: str = "security") -> int:
        """
        Revoke all API keys for a user

        Args:
            user_id: User identifier
            reason: Reason for revocation

        Returns:
            Number of keys revoked
        """
        count = 0
        for key_hash in self._user_keys.get(user_id, set()):
            api_key = self._keys.get(key_hash)
            if api_key and api_key.status == APIKeyStatus.ACTIVE:
                api_key.status = APIKeyStatus.REVOKED
                api_key.metadata["revoked_reason"] = reason
                api_key.metadata["revoked_at"] = datetime.now(timezone.utc).isoformat()
                count += 1

        return count

    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """
        Get all API keys for a user

        Args:
            user_id: User identifier

        Returns:
            List of API keys (without sensitive data)
        """
        keys = []
        for key_hash in self._user_keys.get(user_id, set()):
            api_key = self._keys.get(key_hash)
            if api_key:
                keys.append(api_key)

        return sorted(keys, key=lambda k: k.created_at, reverse=True)

    def get_api_key_by_id(self, user_id: str, key_id: str) -> Optional[APIKey]:
        """
        Get an API key by ID

        Args:
            user_id: User identifier
            key_id: API key ID

        Returns:
            API key or None
        """
        for key_hash in self._user_keys.get(user_id, set()):
            api_key = self._keys.get(key_hash)
            if api_key and api_key.id == key_id:
                return api_key

        return None

    def delete_api_key(self, user_id: str, key_id: str) -> bool:
        """
        Permanently delete an API key

        Args:
            user_id: User identifier
            key_id: API key ID

        Returns:
            True if key was deleted
        """
        for key_hash in list(self._user_keys.get(user_id, set())):
            api_key = self._keys.get(key_hash)
            if api_key and api_key.id == key_id:
                del self._keys[key_hash]
                self._user_keys[user_id].discard(key_hash)
                return True

        return False

    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys

        Returns:
            Number of keys marked as expired
        """
        now = datetime.now(timezone.utc)
        count = 0

        for api_key in self._keys.values():
            if api_key.status == APIKeyStatus.ACTIVE and api_key.expires_at and api_key.expires_at < now:
                api_key.status = APIKeyStatus.EXPIRED
                count += 1

        return count

    def get_key_stats(self, user_id: str) -> Dict:
        """
        Get API key statistics for a user

        Args:
            user_id: User identifier

        Returns:
            Dictionary with statistics
        """
        keys = self.get_user_api_keys(user_id)

        return {
            "total_keys": len(keys),
            "active_keys": sum(1 for k in keys if k.status == APIKeyStatus.ACTIVE),
            "expired_keys": sum(1 for k in keys if k.status == APIKeyStatus.EXPIRED),
            "revoked_keys": sum(1 for k in keys if k.status == APIKeyStatus.REVOKED),
            "total_usage": sum(k.usage_count for k in keys),
        }

    def suspend_api_key(self, user_id: str, key_id: str) -> bool:
        """
        Suspend an API key (temporary disable)

        Args:
            user_id: User identifier
            key_id: API key ID

        Returns:
            True if key was suspended
        """
        for key_hash in self._user_keys.get(user_id, set()):
            api_key = self._keys.get(key_hash)
            if api_key and api_key.id == key_id:
                if api_key.status == APIKeyStatus.ACTIVE:
                    api_key.status = APIKeyStatus.SUSPENDED
                    return True

        return False

    def reactivate_api_key(self, user_id: str, key_id: str) -> bool:
        """
        Reactivate a suspended API key

        Args:
            user_id: User identifier
            key_id: API key ID

        Returns:
            True if key was reactivated
        """
        for key_hash in self._user_keys.get(user_id, set()):
            api_key = self._keys.get(key_hash)
            if api_key and api_key.id == key_id:
                if api_key.status == APIKeyStatus.SUSPENDED:
                    # Check if not expired
                    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                        api_key.status = APIKeyStatus.EXPIRED
                        return False
                    api_key.status = APIKeyStatus.ACTIVE
                    return True

        return False


# Singleton instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get singleton API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
