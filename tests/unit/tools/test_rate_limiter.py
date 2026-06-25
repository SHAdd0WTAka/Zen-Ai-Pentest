"""Smoke tests for core/rate_limiter.py"""

import pytest


class TestRateLimiterImports:
    def test_import_rate_limiter(self):
        from core.rate_limiter import (
            InMemoryRateLimiter,
            InMemoryTokenBucket,
            RateLimitConfig,
            RateLimiter,
            RateLimitExceeded,
            RateLimitInfo,
            TokenBucketRateLimiter,
            get_rate_limiter,
        )

        assert RateLimiter is not None
        assert TokenBucketRateLimiter is not None

    def test_rate_limit_config_defaults(self):
        from core.rate_limiter import RateLimitConfig

        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.burst_capacity == 100

    def test_rate_limit_exceeded_exception(self):
        from core.rate_limiter import RateLimitExceeded

        with pytest.raises(RateLimitExceeded):
            raise RateLimitExceeded("too many requests")


class TestRateLimiterInit:
    @pytest.mark.timeout(5)
    def test_rate_limiter_creation(self):
        from core.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert limiter is not None
        assert limiter.AUTHENTICATED_RPM == 100
        assert limiter.ANONYMOUS_RPM == 20

    @pytest.mark.timeout(5)
    def test_token_bucket_limiter_creation(self):
        from core.rate_limiter import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter()
        assert limiter is not None
        assert limiter.config.requests_per_minute == 60

    @pytest.mark.timeout(5)
    def test_in_memory_bucket(self):
        from core.rate_limiter import InMemoryTokenBucket

        bucket = InMemoryTokenBucket(rate_per_minute=60, burst_capacity=10)
        assert bucket.tokens == 10.0
        assert bucket.rate_per_minute == 60

    @pytest.mark.timeout(5)
    async def test_in_memory_limiter_check(self):
        from core.rate_limiter import InMemoryRateLimiter

        limiter = InMemoryRateLimiter()
        allowed, info = await limiter.check_rate_limit("test_key", 60, 10, 1)
        assert allowed is True
        assert info.remaining >= 0

    @pytest.mark.timeout(5)
    async def test_rate_limiter_allow(self):
        from core.rate_limiter import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter()
        allowed = await limiter.allow("test_user")
        assert allowed is True

    @pytest.mark.timeout(5)
    async def test_check_anonymous(self):
        from core.rate_limiter import RateLimiter

        limiter = RateLimiter()
        allowed, info = await limiter.check_anonymous("127.0.0.1")
        assert allowed is True
        assert info.limit == limiter.ANONYMOUS_BURST
