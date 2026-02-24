"""
Rate Limiter
============

Limits the rate of security tool execution to prevent:
- Accidental DoS against targets
- Excessive resource usage
- Detection by defensive systems
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    max_requests: int = 10  # Max requests per window
    window_seconds: int = 60  # Time window in seconds
    burst_size: int = 3  # Allow burst of N requests
    cooldown_seconds: int = 5  # Cooldown between requests


@dataclass
class RateLimitState:
    """State for rate limiting a specific key"""

    requests: list = field(default_factory=list)
    last_request: float = 0
    blocked_until: Optional[float] = None


class RateLimiter:
    """
    Token bucket rate limiter for tool execution.

    Tracks requests per target/user and enforces limits.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limiting configuration
        """
        self.config = config or RateLimitConfig()
        self._states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, key: str) -> Dict:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., "user_id:target")

        Returns:
            Dict with allowed status and wait time
        """
        async with self._lock:
            now = time.time()
            state = self._states[key]

            # Check if blocked
            if state.blocked_until and now < state.blocked_until:
                wait_time = state.blocked_until - now
                return {
                    "allowed": False,
                    "wait_seconds": wait_time,
                    "reason": f"Rate limit exceeded. Blocked for {wait_time:.1f} seconds",
                    "remaining": 0,
                }

            # Clear expired blocked status
            if state.blocked_until and now >= state.blocked_until:
                state.blocked_until = None
                state.requests = []

            # Remove old requests outside window
            cutoff = now - self.config.window_seconds
            state.requests = [t for t in state.requests if t > cutoff]

            # Check cooldown (skip if no previous request)
            if state.last_request > 0:
                time_since_last = now - state.last_request
                if time_since_last < self.config.cooldown_seconds:
                    wait_time = self.config.cooldown_seconds - time_since_last
                    return {
                        "allowed": False,
                        "wait_seconds": wait_time,
                        "reason": f"Cooldown period active. Wait {wait_time:.1f} seconds",
                        "remaining": self.config.max_requests
                        - len(state.requests),
                    }

            # Check request count
            if len(state.requests) >= self.config.max_requests:
                # Block for remaining window time
                oldest_request = min(state.requests)
                block_duration = self.config.window_seconds - (
                    now - oldest_request
                )
                state.blocked_until = now + block_duration

                return {
                    "allowed": False,
                    "wait_seconds": block_duration,
                    "reason": f"Rate limit exceeded. Blocked for {block_duration:.1f} seconds",
                    "remaining": 0,
                }

            # Check burst
            recent_requests = sum(1 for t in state.requests if now - t < 1)
            if recent_requests >= self.config.burst_size:
                return {
                    "allowed": False,
                    "wait_seconds": 1.0,
                    "reason": "Burst limit exceeded. Slow down requests",
                    "remaining": self.config.max_requests
                    - len(state.requests),
                }

            # Allow request
            remaining = self.config.max_requests - len(state.requests) - 1
            return {
                "allowed": True,
                "wait_seconds": 0,
                "reason": None,
                "remaining": remaining,
            }

    async def record_request(self, key: str):
        """
        Record a successful request.

        Args:
            key: Unique identifier
        """
        async with self._lock:
            state = self._states[key]
            state.requests.append(time.time())
            state.last_request = time.time()

    async def acquire(self, key: str, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request, optionally waiting.

        Args:
            key: Unique identifier
            timeout: Max time to wait (None = no wait)

        Returns:
            True if permission acquired
        """
        result = await self.check_rate_limit(key)

        if result["allowed"]:
            await self.record_request(key)
            return True

        if timeout is None or result["wait_seconds"] > timeout:
            return False

        # Wait and retry
        await asyncio.sleep(result["wait_seconds"])
        result = await self.check_rate_limit(key)

        if result["allowed"]:
            await self.record_request(key)
            return True

        return False

    def get_stats(self, key: Optional[str] = None) -> Dict:
        """
        Get rate limiting statistics.

        Args:
            key: Specific key or None for all

        Returns:
            Statistics dict
        """
        now = time.time()

        if key:
            state = self._states.get(key)
            if not state:
                return {
                    "key": key,
                    "requests_in_window": 0,
                    "remaining": self.config.max_requests,
                }

            cutoff = now - self.config.window_seconds
            active_requests = len([t for t in state.requests if t > cutoff])

            return {
                "key": key,
                "requests_in_window": active_requests,
                "remaining": max(
                    0, self.config.max_requests - active_requests
                ),
                "blocked": state.blocked_until is not None
                and now < state.blocked_until,
                "blocked_until": state.blocked_until,
            }

        # All stats
        total_keys = len(self._states)
        total_blocked = sum(
            1
            for s in self._states.values()
            if s.blocked_until and now < s.blocked_until
        )

        return {
            "total_keys": total_keys,
            "blocked_keys": total_blocked,
            "config": {
                "max_requests": self.config.max_requests,
                "window_seconds": self.config.window_seconds,
                "burst_size": self.config.burst_size,
                "cooldown_seconds": self.config.cooldown_seconds,
            },
        }

    async def reset(self, key: Optional[str] = None):
        """
        Reset rate limit state.

        Args:
            key: Specific key or None for all
        """
        async with self._lock:
            if key:
                if key in self._states:
                    del self._states[key]
            else:
                self._states.clear()


class ToolRateLimiter:
    """
    Rate limiter specifically for security tools.

    Combines global and per-target rate limiting.
    """

    def __init__(self):
        # Global rate limiter (all tools combined)
        self.global_limiter = RateLimiter(
            RateLimitConfig(
                max_requests=100,  # 100 requests per hour globally
                window_seconds=3600,
                burst_size=10,
                cooldown_seconds=1,
            )
        )

        # Per-target rate limiter
        self.target_limiter = RateLimiter(
            RateLimitConfig(
                max_requests=20,  # 20 requests per target per hour
                window_seconds=3600,
                burst_size=3,
                cooldown_seconds=5,
            )
        )

        # Per-tool rate limiter
        self.tool_limiter = RateLimiter(
            RateLimitConfig(
                max_requests=30,  # 30 requests per tool per hour
                window_seconds=3600,
                burst_size=5,
                cooldown_seconds=2,
            )
        )

    async def check_tool_execution(
        self,
        tool_name: str,
        target: str,
        user_id: Optional[str] = None,
    ) -> Dict:
        """
        Check if tool execution is allowed.

        Args:
            tool_name: Name of the tool
            target: Target being scanned
            user_id: Optional user identifier

        Returns:
            Result dict with allowed status
        """
        # Build keys
        global_key = user_id or "anonymous"
        target_key = f"{global_key}:{target}"
        tool_key = f"{global_key}:{tool_name}"

        # Check all limiters
        checks = await asyncio.gather(
            self.global_limiter.check_rate_limit(global_key),
            self.target_limiter.check_rate_limit(target_key),
            self.tool_limiter.check_rate_limit(tool_key),
        )

        # Find most restrictive
        for check in checks:
            if not check["allowed"]:
                return {
                    "allowed": False,
                    "reason": check["reason"],
                    "wait_seconds": check["wait_seconds"],
                    "limiter": (
                        "global"
                        if check == checks[0]
                        else ("target" if check == checks[1] else "tool")
                    ),
                }

        return {
            "allowed": True,
            "reason": None,
            "wait_seconds": 0,
        }

    async def record_execution(
        self,
        tool_name: str,
        target: str,
        user_id: Optional[str] = None,
    ):
        """Record a tool execution"""
        global_key = user_id or "anonymous"
        target_key = f"{global_key}:{target}"
        tool_key = f"{global_key}:{tool_name}"

        await asyncio.gather(
            self.global_limiter.record_request(global_key),
            self.target_limiter.record_request(target_key),
            self.tool_limiter.record_request(tool_key),
        )


# Convenience functions
_default_limiter: Optional[ToolRateLimiter] = None


def get_rate_limiter() -> ToolRateLimiter:
    """Get default tool rate limiter"""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = ToolRateLimiter()
    return _default_limiter


async def check_tool_execution(
    tool_name: str,
    target: str,
    user_id: Optional[str] = None,
) -> Dict:
    """Check if tool execution is allowed"""
    return await get_rate_limiter().check_tool_execution(
        tool_name, target, user_id
    )
