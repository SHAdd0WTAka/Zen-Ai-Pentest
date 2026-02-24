"""
Rate Limiting & Circuit Breaker
Prevents API abuse and handles backend failures gracefully
"""

import asyncio
import hashlib
import importlib.util
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

REDIS_AVAILABLE = importlib.util.find_spec("aioredis") is not None

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_second: float = 1.0
    burst_size: int = 5
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3


class TokenBucket:
    """
    Token bucket rate limiter.
    Allows burst traffic while maintaining average rate.
    """

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens. Returns wait time if not enough tokens.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0

            # Calculate wait time
            needed = tokens - self.tokens
            wait_time = needed / self.rate

            return wait_time

    async def wait(self, tokens: int = 1):
        """Wait until tokens are available"""
        wait_time = await self.acquire(tokens)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            async with self._lock:
                self.tokens -= tokens


class ExponentialBackoff:
    """
    Exponential backoff with jitter for retries.
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.attempt = 0

    def next_delay(self) -> float:
        """Calculate next delay with exponential backoff"""
        delay = min(
            self.base_delay * (self.exponential_base**self.attempt),
            self.max_delay,
        )

        if self.jitter:
            # Add random jitter (±25%)
            delay *= random.uniform(0.75, 1.25)

        self.attempt += 1
        return delay

    def reset(self):
        """Reset attempt counter"""
        self.attempt = 0


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures when backends are down.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(
                        f"Circuit {self.name}: Entering HALF_OPEN state"
                    )
                else:
                    raise CircuitBreakerOpen(f"Circuit {self.name} is OPEN")

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpen(
                        f"Circuit {self.name} HALF_OPEN limit reached"
                    )
                self.half_open_calls += 1

        # Execute outside lock
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try recovery"""
        if self.last_failure_time is None:
            return True
        return (
            time.monotonic() - self.last_failure_time
        ) >= self.config.recovery_timeout

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
                self.half_open_calls = 0
                logger.info(f"Circuit {self.name}: CLOSED (recovered)")

    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failures += 1
            self.last_failure_time = time.monotonic()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name}: OPEN (recovery failed)")
            elif self.failures >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit {self.name}: OPEN ({self.failures} failures)"
                )

    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state

    async def force_reset(self):
        """Force circuit to CLOSED state"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.half_open_calls = 0
            logger.info(f"Circuit {self.name}: Force reset to CLOSED")


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""

    pass


class RateLimitedClient:
    """
    HTTP client with rate limiting, retries, and circuit breaker.
    """

    def __init__(
        self,
        name: str,
        rate_config: RateLimitConfig = None,
        circuit_config: CircuitBreakerConfig = None,
    ):
        self.name = name
        self.rate_config = rate_config or RateLimitConfig()
        self.circuit = CircuitBreaker(name, circuit_config)

        # Token bucket for rate limiting
        self.bucket = TokenBucket(
            rate=self.rate_config.requests_per_second,
            capacity=self.rate_config.burst_size,
        )

        self._session: Optional[Any] = None

    async def request(
        self, method: str, url: str, retries: int = None, **kwargs
    ) -> Any:
        """
        Make rate-limited request with circuit breaker.
        """
        retries = retries or self.rate_config.max_retries
        backoff = ExponentialBackoff(
            base_delay=self.rate_config.base_delay,
            max_delay=self.rate_config.max_delay,
        )

        last_error = None

        for attempt in range(retries + 1):
            # Wait for rate limit
            await self.bucket.wait()

            try:
                return await self.circuit.call(
                    self._do_request, method, url, **kwargs
                )
            except CircuitBreakerOpen:
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    f"{self.name} request failed (attempt {attempt + 1}): {e}"
                )

                if attempt < retries:
                    delay = backoff.next_delay()
                    logger.info(f"Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)

        raise last_error or Exception("Max retries exceeded")

    async def _do_request(self, method: str, url: str, **kwargs) -> Any:
        """Actual request implementation - override in subclass"""
        raise NotImplementedError("Subclasses must implement _do_request")

    async def close(self):
        """Close client resources"""
        pass


class SmartRouter:
    """
    Intelligent backend routing with health checks and circuit breakers.
    """

    def __init__(self):
        self.backends: Dict[str, Any] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_status: Dict[str, bool] = {}
        self._lock = asyncio.Lock()

    def register_backend(
        self,
        name: str,
        backend: Any,
        priority: int = 0,
        circuit_config: CircuitBreakerConfig = None,
    ):
        """Register a backend with circuit breaker"""
        self.backends[name] = {
            "instance": backend,
            "priority": priority,
            "name": name,
        }
        self.circuit_breakers[name] = CircuitBreaker(name, circuit_config)
        self.health_status[name] = True

    async def get_healthy_backend(
        self, min_priority: int = 0
    ) -> Optional[Any]:
        """
        Get a healthy backend based on priority and circuit state.
        """
        # Sort by priority (highest first)
        candidates = sorted(
            self.backends.values(), key=lambda b: b["priority"], reverse=True
        )

        for backend_info in candidates:
            name = backend_info["name"]

            # Check circuit breaker state
            circuit = self.circuit_breakers[name]
            if circuit.state == CircuitState.OPEN:
                continue

            # Check health status
            if await self._is_healthy(name):
                return backend_info["instance"]

        # Fallback: try any backend even if circuit is half-open
        for backend_info in candidates:
            name = backend_info["name"]
            circuit = self.circuit_breakers[name]
            if circuit.state == CircuitState.HALF_OPEN:
                return backend_info["instance"]

        return None

    async def _is_healthy(self, name: str) -> bool:
        """Check if backend is healthy"""
        # Could implement actual health check here
        return self.health_status.get(name, False)

    async def execute(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if name not in self.circuit_breakers:
            raise ValueError(f"Unknown backend: {name}")

        circuit = self.circuit_breakers[name]
        return await circuit.call(func, *args, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        """Get status of all backends"""
        return {
            name: {
                "circuit_state": cb.state.value,
                "failures": cb.failures,
                "healthy": self.health_status.get(name, False),
            }
            for name, cb in self.circuit_breakers.items()
        }


def rate_limited(
    requests_per_second: float = 1.0, burst_size: int = 5, max_retries: int = 3
):
    """
    Decorator for rate limiting async functions.
    """
    bucket = TokenBucket(rate=requests_per_second, capacity=burst_size)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await bucket.wait()

            backoff = ExponentialBackoff()
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = backoff.next_delay()
                        await asyncio.sleep(delay)

            raise last_error

        return wrapper

    return decorator


def cached_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()
