"""Test rate limiter"""

import pytest


class TestRateLimiter:
    """Test rate limiter"""

    def test_import(self):
        from core.rate_limiter import RateLimiter

        assert RateLimiter is not None

    def test_creation(self):
        from core.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert limiter is not None

    def test_has_check(self):
        from core.rate_limiter import RateLimiter

        limiter = RateLimiter()
        assert hasattr(limiter, "check_anonymous")
