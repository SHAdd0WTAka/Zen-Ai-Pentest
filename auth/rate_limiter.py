"""
Rate Limiting Module
====================

User-based rate limiting with:
- Sliding window algorithm
- Per-endpoint limits
- IP-based fallback
- Account lockout protection

Compliance: OWASP ASVS 2026 V11.2
"""

import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from .config import RateLimitConfig, get_config


class RateLimitType(Enum):
    """Rate limit types"""

    LOGIN = "login"
    API_KEY = "api_key"
    MFA = "mfa"
    PASSWORD_RESET = "password_reset"
    REGISTRATION = "registration"


@dataclass
class RateLimitEntry:
    """Rate limit tracking entry"""

    key: str  # user_id or IP
    limit_type: RateLimitType
    attempts: deque  # timestamps of attempts
    locked_until: Optional[float] = None

    def __post_init__(self):
        if isinstance(self.attempts, list):
            self.attempts = deque(self.attempts, maxlen=1000)


@dataclass
class RateLimitResult:
    """Rate limit check result"""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    message: Optional[str] = None


class RateLimitExceededError(Exception):
    """Rate limit exceeded error"""

    pass


class RateLimiter:
    """
    Rate Limiter

    Implements sliding window rate limiting for:
    - Login attempts
    - API requests
    - MFA attempts
    - Password resets

    Features:
    - Per-user tracking
    - IP-based fallback
    - Account lockout
    - Automatic cleanup
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or get_config().rate_limit
        self._entries: Dict[str, RateLimitEntry] = {}
        self._lock = threading.RLock()

        # Default limits
        self._limits = {
            RateLimitType.LOGIN: {
                "max_attempts": self.config.login_attempts,
                "window_seconds": self.config.login_window_seconds,
            },
            RateLimitType.API_KEY: {
                "max_attempts": self.config.api_key_requests,
                "window_seconds": self.config.api_key_window_seconds,
            },
            RateLimitType.MFA: {
                "max_attempts": self.config.mfa_attempts,
                "window_seconds": self.config.mfa_window_seconds,
            },
            RateLimitType.PASSWORD_RESET: {
                "max_attempts": 3,
                "window_seconds": 3600,  # 1 hour
            },
            RateLimitType.REGISTRATION: {
                "max_attempts": 5,
                "window_seconds": 3600,  # 1 hour
            },
        }

    def _get_key(self, identifier: str, limit_type: RateLimitType) -> str:
        """Generate storage key"""
        return f"{limit_type.value}:{identifier}"

    def _get_or_create_entry(self, identifier: str, limit_type: RateLimitType) -> RateLimitEntry:
        """Get or create rate limit entry"""
        key = self._get_key(identifier, limit_type)

        if key not in self._entries:
            self._entries[key] = RateLimitEntry(
                key=identifier,
                limit_type=limit_type,
                attempts=deque(maxlen=1000),
            )

        return self._entries[key]

    def check_rate_limit(
        self, identifier: str, limit_type: RateLimitType, custom_limits: Optional[Dict] = None
    ) -> RateLimitResult:
        """
        Check if request is within rate limit

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit
            custom_limits: Optional custom limits

        Returns:
            RateLimitResult with status
        """
        with self._lock:
            entry = self._get_or_create_entry(identifier, limit_type)

            # Check if locked
            if entry.locked_until:
                if time.time() < entry.locked_until:
                    retry_after = int(entry.locked_until - time.time())
                    return RateLimitResult(
                        allowed=False,
                        remaining=0,
                        reset_time=entry.locked_until,
                        retry_after=retry_after,
                        message=f"Account locked. Try again in {retry_after} seconds.",
                    )
                else:
                    # Lock expired, reset
                    entry.locked_until = None

            # Get limits
            limits = custom_limits or self._limits.get(limit_type, {})
            max_attempts = limits.get("max_attempts", 10)
            window_seconds = limits.get("window_seconds", 60)

            # Clean old attempts
            now = time.time()
            cutoff = now - window_seconds

            while entry.attempts and entry.attempts[0] < cutoff:
                entry.attempts.popleft()

            # Check current count
            current_count = len(entry.attempts)

            if current_count >= max_attempts:
                # Lock account for double the window
                lock_duration = window_seconds * 2
                entry.locked_until = now + lock_duration

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=entry.locked_until,
                    retry_after=int(lock_duration),
                    message=f"Rate limit exceeded. Account locked for {lock_duration} seconds.",
                )

            # Calculate reset time
            if entry.attempts:
                reset_time = entry.attempts[0] + window_seconds
            else:
                reset_time = now + window_seconds

            return RateLimitResult(
                allowed=True,
                remaining=max_attempts - current_count,
                reset_time=reset_time,
            )

    def record_attempt(self, identifier: str, limit_type: RateLimitType, success: bool = False) -> None:
        """
        Record an attempt

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit
            success: Whether the attempt was successful
        """
        with self._lock:
            entry = self._get_or_create_entry(identifier, limit_type)

            # Record attempt
            entry.attempts.append(time.time())

            # On success, clear attempts for this type
            if success:
                entry.attempts.clear()

    def is_allowed(self, identifier: str, limit_type: RateLimitType) -> bool:
        """
        Quick check if request is allowed

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit

        Returns:
            True if request is allowed
        """
        result = self.check_rate_limit(identifier, limit_type)
        return result.allowed

    def check_and_record(self, identifier: str, limit_type: RateLimitType, success: bool = False) -> RateLimitResult:
        """
        Check rate limit and record attempt

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit
            success: Whether this is a successful attempt

        Returns:
            RateLimitResult with status
        """
        result = self.check_rate_limit(identifier, limit_type)

        if result.allowed or not success:
            self.record_attempt(identifier, limit_type, success)

        return result

    def reset_limit(self, identifier: str, limit_type: RateLimitType) -> bool:
        """
        Reset rate limit for an identifier

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit

        Returns:
            True if limit was reset
        """
        with self._lock:
            key = self._get_key(identifier, limit_type)

            if key in self._entries:
                del self._entries[key]
                return True

            return False

    def reset_all_limits(self, identifier: str) -> int:
        """
        Reset all rate limits for an identifier

        Args:
            identifier: User ID or IP address

        Returns:
            Number of limits reset
        """
        with self._lock:
            count = 0
            keys_to_remove = []

            for key, entry in self._entries.items():
                if entry.key == identifier:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._entries[key]
                count += 1

            return count

    def get_limit_status(self, identifier: str, limit_type: RateLimitType) -> Optional[Dict]:
        """
        Get current rate limit status

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit

        Returns:
            Status dictionary or None
        """
        with self._lock:
            key = self._get_key(identifier, limit_type)
            entry = self._entries.get(key)

            if not entry:
                limits = self._limits.get(limit_type, {})
                return {
                    "attempts": 0,
                    "remaining": limits.get("max_attempts", 10),
                    "locked": False,
                }

            limits = self._limits.get(limit_type, {})
            max_attempts = limits.get("max_attempts", 10)
            window_seconds = limits.get("window_seconds", 60)

            # Clean old attempts
            now = time.time()
            cutoff = now - window_seconds

            while entry.attempts and entry.attempts[0] < cutoff:
                entry.attempts.popleft()

            return {
                "attempts": len(entry.attempts),
                "remaining": max(0, max_attempts - len(entry.attempts)),
                "locked": entry.locked_until is not None and entry.locked_until > now,
                "locked_until": entry.locked_until,
            }

    def cleanup_old_entries(self) -> int:
        """
        Clean up old rate limit entries

        Returns:
            Number of entries cleaned up
        """
        with self._lock:
            now = time.time()
            keys_to_remove = []

            for key, entry in self._entries.items():
                # Remove if no recent attempts and not locked
                if not entry.attempts:
                    if not entry.locked_until or entry.locked_until < now:
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._entries[key]

            return len(keys_to_remove)

    def set_custom_limit(self, limit_type: RateLimitType, max_attempts: int, window_seconds: int) -> None:
        """
        Set custom rate limit

        Args:
            limit_type: Type of rate limit
            max_attempts: Maximum attempts
            window_seconds: Window in seconds
        """
        self._limits[limit_type] = {
            "max_attempts": max_attempts,
            "window_seconds": window_seconds,
        }

    def lock_identifier(self, identifier: str, limit_type: RateLimitType, duration_seconds: int) -> None:
        """
        Manually lock an identifier

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit
            duration_seconds: Lock duration
        """
        with self._lock:
            entry = self._get_or_create_entry(identifier, limit_type)
            entry.locked_until = time.time() + duration_seconds

    def unlock_identifier(self, identifier: str, limit_type: RateLimitType) -> bool:
        """
        Manually unlock an identifier

        Args:
            identifier: User ID or IP address
            limit_type: Type of rate limit

        Returns:
            True if identifier was unlocked
        """
        with self._lock:
            key = self._get_key(identifier, limit_type)
            entry = self._entries.get(key)

            if entry and entry.locked_until:
                entry.locked_until = None
                return True

            return False


# Singleton instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
