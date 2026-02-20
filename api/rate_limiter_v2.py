"""
User-based Rate Limiting für Zen-AI-Pentest API v2

Features:
- IP-basiertes Limiting für anonyme User
- Account-basiertes Limiting für authentifizierte User
- Verschiedene Limits je nach User-Tier (anonymous, user, admin)
- Redis-Unterstützung für verteilte Systeme
- Detaillierte Rate Limit Headers
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Dict, Literal, Optional

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Rate limits by user tier (requests per minute)
RATE_LIMITS = {
    "anonymous": {
        "requests_per_minute": int(os.getenv("RATE_LIMIT_ANON_RPM", "30")),
        "burst_size": int(os.getenv("RATE_LIMIT_ANON_BURST", "5")),
        "description": "Unauthenticated users",
    },
    "user": {
        "requests_per_minute": int(os.getenv("RATE_LIMIT_USER_RPM", "60")),
        "burst_size": int(os.getenv("RATE_LIMIT_USER_BURST", "10")),
        "description": "Standard authenticated users",
    },
    "premium": {
        "requests_per_minute": int(os.getenv("RATE_LIMIT_PREMIUM_RPM", "120")),
        "burst_size": int(os.getenv("RATE_LIMIT_PREMIUM_BURST", "20")),
        "description": "Premium users",
    },
    "admin": {
        "requests_per_minute": int(os.getenv("RATE_LIMIT_ADMIN_RPM", "300")),
        "burst_size": int(os.getenv("RATE_LIMIT_ADMIN_BURST", "50")),
        "description": "Administrators",
    },
}

# Auth endpoints - stricter limits
AUTH_RATE_LIMIT = int(os.getenv("AUTH_RATE_LIMIT", "5"))
AUTH_LOCKOUT_DURATION = int(os.getenv("AUTH_LOCKOUT_DURATION", "300"))  # 5 minutes

# User tier detection (customize based on your auth system)
UserTier = Literal["anonymous", "user", "premium", "admin"]


# =============================================================================
# Token Bucket (Thread-safe)
# =============================================================================


@dataclass
class TokenBucket:
    """Token Bucket für Rate Limiting"""

    rate: float  # Tokens per second
    burst_size: int
    tokens: float = 0
    last_update: float = 0

    def __post_init__(self):
        if self.last_update == 0:
            self.last_update = time.time()
            self.tokens = self.burst_size

    def _add_tokens(self):
        now = time.time()
        time_passed = now - self.last_update
        tokens_to_add = time_passed * self.rate
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        self._add_tokens()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        self._add_tokens()
        if self.tokens >= tokens:
            return 0
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.rate

    def to_dict(self) -> dict:
        self._add_tokens()
        return {"tokens": self.tokens, "burst_size": self.burst_size, "rate": self.rate, "last_update": self.last_update}

    @classmethod
    def from_dict(cls, data: dict) -> "TokenBucket":
        bucket = cls(rate=data["rate"], burst_size=data["burst_size"], tokens=data["tokens"], last_update=data["last_update"])
        return bucket


# =============================================================================
# Storage Backends
# =============================================================================


class RateLimitStorage:
    """Base storage class for rate limits"""

    def get_bucket(self, key: str, rate: float, burst_size: int) -> TokenBucket:
        raise NotImplementedError

    def save_bucket(self, key: str, bucket: TokenBucket):
        raise NotImplementedError

    def cleanup(self):
        pass


class MemoryStorage(RateLimitStorage):
    """In-Memory storage (single instance only)"""

    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_access: Dict[str, float] = {}
        self.metadata: Dict[str, dict] = {}  # Store tier info

    def get_bucket(self, key: str, rate: float, burst_size: int) -> TokenBucket:
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(rate=rate, burst_size=burst_size)

        self.last_access[key] = time.time()
        return self.buckets[key]

    def save_bucket(self, key: str, bucket: TokenBucket):
        self.buckets[key] = bucket
        self.last_access[key] = time.time()

    def set_metadata(self, key: str, metadata: dict):
        self.metadata[key] = metadata

    def get_metadata(self, key: str) -> Optional[dict]:
        return self.metadata.get(key)

    def cleanup(self, max_age: float = 3600):
        now = time.time()
        to_remove = [key for key, last in self.last_access.items() if now - last > max_age]
        for key in to_remove:
            del self.buckets[key]
            del self.last_access[key]
            if key in self.metadata:
                del self.metadata[key]


class RedisStorage(RateLimitStorage):
    """Redis storage for distributed systems"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None
        self._init_redis()

    def _init_redis(self):
        try:
            import redis

            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("Redis connection established for rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available, falling back to memory: {e}")
            self._redis = None

    def _get_key(self, key: str) -> str:
        return f"rate_limit:{key}"

    def get_bucket(self, key: str, rate: float, burst_size: int) -> TokenBucket:
        if not self._redis:
            # Fallback to memory
            return MemoryStorage().get_bucket(key, rate, burst_size)

        redis_key = self._get_key(key)
        data = self._redis.get(redis_key)

        if data:
            try:
                bucket_data = json.loads(data)
                return TokenBucket.from_dict(bucket_data)
            except (json.JSONDecodeError, KeyError):
                pass

        return TokenBucket(rate=rate, burst_size=burst_size)

    def save_bucket(self, key: str, bucket: TokenBucket):
        if not self._redis:
            return

        redis_key = self._get_key(key)
        data = json.dumps(bucket.to_dict())
        # TTL: 1 hour
        self._redis.setex(redis_key, 3600, data)


# Global storage instance
storage_backend = os.getenv("RATE_LIMIT_STORAGE", "memory")
if storage_backend == "redis":
    try:
        rate_limit_storage = RedisStorage()
    except Exception as e:
        logger.warning(f"Failed to initialize Redis storage: {e}")
        rate_limit_storage = MemoryStorage()
else:
    rate_limit_storage = MemoryStorage()


# =============================================================================
# User Context
# =============================================================================


@dataclass
class UserContext:
    """User information for rate limiting"""

    user_id: Optional[str] = None
    username: Optional[str] = None
    tier: UserTier = "anonymous"
    ip_address: str = "unknown"

    def get_rate_limit_key(self) -> str:
        """Generate unique key for this user"""
        if self.user_id:
            return f"user:{self.user_id}"
        # For anonymous: hash IP + user agent
        ip_hash = hashlib.sha256(self.ip_address.encode()).hexdigest()[:16]
        return f"anon:{ip_hash}"

    def get_limits(self) -> dict:
        """Get rate limits for this user's tier"""
        return RATE_LIMITS.get(self.tier, RATE_LIMITS["anonymous"])


def get_user_from_request(request: Request) -> UserContext:
    """
    Extract user information from request.

    Customize this based on your auth system!
    """
    client_ip = request.client.host if request.client else "unknown"

    # Try to get user from JWT token or session
    # This is a simplified example - adapt to your auth system
    auth_header = request.headers.get("authorization", "")
    user_id = None
    username = None
    tier: UserTier = "anonymous"

    if auth_header.startswith("Bearer "):
        # Extract user from JWT (simplified)
        # In production: verify token and extract claims
        try:
            # Placeholder - integrate with your JWT auth
            # user_id = decode_jwt(auth_header[7:]).get("sub")
            # tier = get_user_tier(user_id)
            pass
        except Exception:
            pass

    # Check for admin/premium in headers (customize this!)
    user_tier_header = request.headers.get("x-user-tier")
    if user_tier_header in RATE_LIMITS:
        tier = user_tier_header  # type: ignore

    return UserContext(user_id=user_id, username=username, tier=tier, ip_address=client_ip)


# =============================================================================
# Rate Limiting Decorator
# =============================================================================


def rate_limit(requests_per_minute: Optional[int] = None, burst_size: Optional[int] = None, tier: Optional[UserTier] = None):
    """
    Rate limiting decorator with user-based limits.

    Usage:
        @app.get("/api/data")
        @rate_limit()  # Uses user's tier limits
        async def get_data(request: Request):
            return {"data": "value"}

        @app.get("/api/admin")
        @rate_limit(requests_per_minute=600)  # Custom limit
        async def admin_endpoint(request: Request):
            return {"admin": "data"}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                return await func(*args, **kwargs)

            # Get user context
            user = get_user_from_request(request)

            # Determine limits
            if tier:
                limits = RATE_LIMITS[tier]
            elif requests_per_minute:
                limits = {"requests_per_minute": requests_per_minute, "burst_size": burst_size or 10}
            else:
                limits = user.get_limits()

            # Get or create bucket
            key = user.get_rate_limit_key()
            rate_per_second = limits["requests_per_minute"] / 60
            bucket = rate_limit_storage.get_bucket(key, rate_per_second, limits["burst_size"])

            # Store metadata
            if isinstance(rate_limit_storage, MemoryStorage):
                rate_limit_storage.set_metadata(key, {"tier": user.tier, "user_id": user.user_id, "ip": user.ip_address})

            # Check rate limit
            if not bucket.consume():
                wait_time = bucket.get_wait_time()
                logger.warning(f"Rate limit exceeded for {user.tier} user {user.user_id or user.ip_address}")

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": int(wait_time),
                        "tier": user.tier,
                        "limit": limits["requests_per_minute"],
                    },
                    headers={
                        "Retry-After": str(int(wait_time)),
                        "X-RateLimit-Limit": str(limits["requests_per_minute"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Tier": user.tier,
                    },
                )

            # Save bucket state
            rate_limit_storage.save_bucket(key, bucket)

            # Add rate limit headers to response
            response = await func(*args, **kwargs)

            return response

        return wrapper

    return decorator


# =============================================================================
# Middleware für globales Rate Limiting
# =============================================================================


class UserRateLimitMiddleware:
    """
    ASGI Middleware für user-basiertes Rate Limiting.

    Usage:
        app.add_middleware(UserRateLimitMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Build minimal request for user detection
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        # Simple tier detection from headers (customize!)
        headers = dict(scope.get("headers", []))
        user_tier = headers.get(b"x-user-tier", b"anonymous").decode()

        if user_tier not in RATE_LIMITS:
            user_tier = "anonymous"

        limits = RATE_LIMITS[user_tier]

        # Create key (simplified)
        key = f"middleware:{user_tier}:{client_ip}"
        rate_per_second = limits["requests_per_minute"] / 60

        bucket = rate_limit_storage.get_bucket(key, rate_per_second, limits["burst_size"])

        if not bucket.consume():
            wait_time = bucket.get_wait_time()

            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"retry-after", str(int(wait_time)).encode()],
                        [b"x-ratelimit-tier", user_tier.encode()],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": json.dumps(
                        {"error": "Rate limit exceeded", "retry_after": int(wait_time), "tier": user_tier}
                    ).encode(),
                }
            )
            return

        rate_limit_storage.save_bucket(key, bucket)
        await self.app(scope, receive, send)


# =============================================================================
# Auth Rate Limiting (mit User-ID Tracking)
# =============================================================================


class UserAuthRateLimiter:
    """
    Erweiterte Auth Rate Limiting mit User-ID Tracking.

    Trackt sowohl IP als auch User-ID für bessere Security.
    """

    def __init__(self):
        self.ip_attempts: Dict[str, list] = {}
        self.user_attempts: Dict[str, list] = {}
        self.lockout_duration = AUTH_LOCKOUT_DURATION
        self.max_attempts = 5

    def _cleanup_old(self, attempts: list, window: int = 60) -> list:
        now = time.time()
        return [t for t in attempts if now - t < window]

    def is_allowed(self, client_ip: str, user_id: Optional[str] = None) -> tuple[bool, Optional[int], str]:
        """
        Prüft ob Auth erlaubt.

        Returns: (allowed, lockout_seconds, reason)
        """
        now = time.time()

        # Check IP-based limits
        self.ip_attempts[client_ip] = self._cleanup_old(self.ip_attempts.get(client_ip, []))

        if len(self.ip_attempts[client_ip]) >= self.max_attempts:
            oldest = min(self.ip_attempts[client_ip])
            lockout = self.lockout_duration - (now - oldest)
            if lockout > 0:
                return False, int(lockout), "ip_blocked"
            self.ip_attempts[client_ip] = []

        # Check user-based limits (if user_id provided)
        if user_id:
            self.user_attempts[user_id] = self._cleanup_old(self.user_attempts.get(user_id, []))

            if len(self.user_attempts[user_id]) >= self.max_attempts:
                oldest = min(self.user_attempts[user_id])
                lockout = self.lockout_duration - (now - oldest)
                if lockout > 0:
                    return False, int(lockout), "user_blocked"
                self.user_attempts[user_id] = []

        return True, None, "ok"

    def record_failure(self, client_ip: str, user_id: Optional[str] = None):
        now = time.time()

        if client_ip not in self.ip_attempts:
            self.ip_attempts[client_ip] = []
        self.ip_attempts[client_ip].append(now)

        if user_id:
            if user_id not in self.user_attempts:
                self.user_attempts[user_id] = []
            self.user_attempts[user_id].append(now)

    def record_success(self, client_ip: str, user_id: Optional[str] = None):
        if client_ip in self.ip_attempts:
            del self.ip_attempts[client_ip]
        if user_id and user_id in self.user_attempts:
            del self.user_attempts[user_id]


# Global instance
user_auth_rate_limiter = UserAuthRateLimiter()


def check_user_auth_rate_limit(client_ip: str, user_id: Optional[str] = None):
    """Prüft Auth Rate Limit"""
    allowed, lockout, reason = user_auth_rate_limiter.is_allowed(client_ip, user_id)

    if not allowed:
        logger.warning(f"Auth rate limit exceeded: {reason} for {client_ip}/{user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "Too many login attempts", "retry_after": lockout, "reason": reason},
            headers={"Retry-After": str(lockout)},
        )


# =============================================================================
# Stats und Monitoring
# =============================================================================


def get_rate_limit_stats() -> dict:
    """Gibt aktuelle Rate Limiting Statistiken zurück"""
    if not isinstance(rate_limit_storage, MemoryStorage):
        return {"error": "Stats only available with memory storage"}

    stats = {
        "total_buckets": len(rate_limit_storage.buckets),
        "by_tier": {"anonymous": 0, "user": 0, "premium": 0, "admin": 0, "unknown": 0},
    }

    for key, metadata in rate_limit_storage.metadata.items():
        tier = metadata.get("tier", "unknown")
        stats["by_tier"][tier] = stats["by_tier"].get(tier, 0) + 1

    return stats


# Cleanup Job (optional)
def cleanup_rate_limits():
    """Entfernt alte Rate Limit Buckets"""
    if isinstance(rate_limit_storage, MemoryStorage):
        rate_limit_storage.cleanup()
        logger.info("Rate limit storage cleaned up")
