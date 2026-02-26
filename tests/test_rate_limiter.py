"""Tests for core/rate_limiter.py - Rate Limiting & Circuit Breaker."""

import time
from unittest.mock import MagicMock

import pytest

from core.rate_limiter import (
    CircuitState,
    RateLimitConfig,
    CircuitBreakerConfig,
    TokenBucket,
    ExponentialBackoff,
    CircuitBreaker,
    CircuitBreakerOpen,
    SmartRouter,
    cached_key,
)


class TestCircuitState:
    """Test CircuitState enum."""

    def test_states(self):
        """Test circuit states."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""

    def test_defaults(self):
        """Test default configuration."""
        config = RateLimitConfig()
        assert config.requests_per_second == 1.0
        assert config.burst_size == 5
        assert config.max_retries == 3

    def test_custom_values(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            requests_per_second=10.0,
            burst_size=20,
            max_retries=5,
        )
        assert config.requests_per_second == 10.0
        assert config.burst_size == 20


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass."""

    def test_defaults(self):
        """Test default configuration."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 30.0
        assert config.half_open_max_calls == 3


class TestTokenBucket:
    """Test TokenBucket rate limiter."""

    def test_init(self):
        """Test initialization."""
        bucket = TokenBucket(rate=1.0, capacity=5)
        assert bucket.rate == 1.0
        assert bucket.capacity == 5
        assert bucket.tokens == 5


class TestExponentialBackoff:
    """Test ExponentialBackoff."""

    def test_defaults(self):
        """Test default initialization."""
        backoff = ExponentialBackoff()
        assert backoff.base_delay == 1.0
        assert backoff.max_delay == 60.0
        assert backoff.jitter is True
        assert backoff.attempt == 0

    def test_next_delay_increases(self):
        """Test delay increases with each attempt."""
        backoff = ExponentialBackoff(jitter=False)
        
        delay1 = backoff.next_delay()
        delay2 = backoff.next_delay()
        delay3 = backoff.next_delay()
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        backoff = ExponentialBackoff(
            base_delay=10.0,
            max_delay=50.0,
            jitter=False
        )
        
        for _ in range(10):
            delay = backoff.next_delay()
        
        assert delay == 50.0

    def test_reset(self):
        """Test reset clears attempt counter."""
        backoff = ExponentialBackoff()
        backoff.next_delay()
        backoff.next_delay()
        
        backoff.reset()
        
        assert backoff.attempt == 0


class TestCircuitBreaker:
    """Test CircuitBreaker."""

    def test_init(self):
        """Test initialization."""
        cb = CircuitBreaker("test")
        assert cb.name == "test"
        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0
        assert cb.last_failure_time is None

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        assert cb.config.failure_threshold == 3

    def test_get_state(self):
        """Test get_state returns current state."""
        cb = CircuitBreaker("test")
        assert cb.get_state() == CircuitState.CLOSED

    def test_should_attempt_reset_no_failures(self):
        """Test should attempt reset when no failures."""
        cb = CircuitBreaker("test")
        assert cb._should_attempt_reset() is True

    def test_should_attempt_reset_after_timeout(self):
        """Test should attempt reset after recovery timeout."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(recovery_timeout=1.0))
        cb.last_failure_time = time.monotonic() - 2.0
        
        assert cb._should_attempt_reset() is True

    def test_should_not_attempt_reset_before_timeout(self):
        """Test should not attempt reset before recovery timeout."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(recovery_timeout=60.0))
        cb.last_failure_time = time.monotonic()
        
        assert cb._should_attempt_reset() is False


class TestSmartRouter:
    """Test SmartRouter."""

    def test_init(self):
        """Test initialization."""
        router = SmartRouter()
        assert router.backends == {}
        assert router.circuit_breakers == {}
        assert router.health_status == {}

    def test_register_backend(self):
        """Test registering a backend."""
        router = SmartRouter()
        backend = MagicMock()
        
        router.register_backend("backend1", backend, priority=10)
        
        assert "backend1" in router.backends
        assert router.backends["backend1"]["priority"] == 10
        assert "backend1" in router.circuit_breakers

    def test_get_status_empty(self):
        """Test get_status with no backends."""
        router = SmartRouter()
        status = router.get_status()
        
        assert status == {}

    def test_get_status_with_backends(self):
        """Test get_status returns backend status."""
        router = SmartRouter()
        router.register_backend("b1", MagicMock())
        
        status = router.get_status()
        
        assert "b1" in status
        assert status["b1"]["circuit_state"] == "closed"
        assert status["b1"]["failures"] == 0


class TestCachedKey:
    """Test cached_key function."""

    def test_simple_args(self):
        """Test key generation with simple args."""
        key = cached_key("arg1", "arg2")
        assert isinstance(key, str)
        assert len(key) == 32

    def test_with_kwargs(self):
        """Test key generation with kwargs."""
        key1 = cached_key("arg", kwarg1="value1")
        key2 = cached_key("arg", kwarg1="value1")
        assert key1 == key2

    def test_different_args_different_keys(self):
        """Test different args produce different keys."""
        key1 = cached_key("arg1")
        key2 = cached_key("arg2")
        assert key1 != key2


class TestAllExports:
    """Test that all expected exports are available."""

    def test_exports(self):
        """Test that key classes are importable."""
        from core import rate_limiter
        
        assert hasattr(rate_limiter, 'CircuitState')
        assert hasattr(rate_limiter, 'RateLimitConfig')
        assert hasattr(rate_limiter, 'CircuitBreakerConfig')
        assert hasattr(rate_limiter, 'TokenBucket')
        assert hasattr(rate_limiter, 'ExponentialBackoff')
        assert hasattr(rate_limiter, 'CircuitBreaker')
        assert hasattr(rate_limiter, 'CircuitBreakerOpen')
        assert hasattr(rate_limiter, 'SmartRouter')
