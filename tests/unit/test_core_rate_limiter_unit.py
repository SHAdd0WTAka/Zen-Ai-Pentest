"""
Unit Tests for Rate Limiter Module
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestTokenBucket:
    """Test Token Bucket"""

    def test_module_imports(self):
        """Test that the module can be imported"""
        from core import rate_limiter

        assert rate_limiter is not None

    def test_token_bucket_creation(self):
        """Test token bucket creation"""
        from core.rate_limiter import TokenBucket

        bucket = TokenBucket(rate=10, capacity=100)
        assert bucket is not None


class TestCircuitBreaker:
    """Test Circuit Breaker"""

    def test_circuit_breaker_creation(self):
        """Test circuit breaker creation"""
        from core.rate_limiter import CircuitBreaker

        cb = CircuitBreaker(name="test")
        assert cb is not None


class TestRateLimitedClient:
    """Test Rate Limited Client"""

    def test_client_creation(self):
        """Test rate limited client creation"""
        from core.rate_limiter import RateLimitedClient

        client = RateLimitedClient(name="test_client")
        assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
