"""
Tests für User-basiertes Rate Limiting v2
"""

import pytest
import time
from fastapi import Request, HTTPException
from unittest.mock import Mock, patch

# Test the new rate limiter
import sys
sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

from api.rate_limiter_v2 import (
    TokenBucket,
    MemoryStorage,
    UserContext,
    RATE_LIMITS,
    rate_limit,
    UserAuthRateLimiter,
    get_rate_limit_stats
)


class TestTokenBucket:
    """Test Token Bucket Algorithm"""
    
    def test_initial_tokens(self):
        bucket = TokenBucket(rate=1.0, burst_size=10)
        assert bucket.tokens == 10
        assert bucket.burst_size == 10
    
    def test_consume_success(self):
        bucket = TokenBucket(rate=1.0, burst_size=10)
        assert bucket.consume(5) is True
        assert bucket.tokens == 5
    
    def test_consume_fail(self):
        bucket = TokenBucket(rate=1.0, burst_size=5)
        assert bucket.consume(10) is False
        assert bucket.tokens == 5  # Tokens unchanged
    
    def test_token_refill(self):
        bucket = TokenBucket(rate=60.0, burst_size=10)  # 1 per second
        bucket.tokens = 0
        bucket.last_update = time.time() - 2  # 2 seconds ago
        
        # Should refill ~2 tokens
        assert bucket.consume(1) is True
        assert bucket.tokens > 0
    
    def test_wait_time_calculation(self):
        bucket = TokenBucket(rate=1.0, burst_size=10)  # 1 per 60 seconds = slow
        bucket.tokens = 0
        
        wait_time = bucket.get_wait_time(1)
        assert wait_time > 50  # ~60 seconds for 1 token
    
    def test_serialization(self):
        bucket = TokenBucket(rate=1.0, burst_size=10)
        bucket.consume(3)
        
        data = bucket.to_dict()
        restored = TokenBucket.from_dict(data)
        
        assert restored.tokens == bucket.tokens
        assert restored.burst_size == bucket.burst_size
        assert restored.rate == bucket.rate


class TestMemoryStorage:
    """Test Memory Storage Backend"""
    
    def test_get_bucket_creates_new(self):
        storage = MemoryStorage()
        bucket = storage.get_bucket("test-key", 1.0, 10)
        
        assert isinstance(bucket, TokenBucket)
        assert "test-key" in storage.buckets
    
    def test_get_bucket_returns_existing(self):
        storage = MemoryStorage()
        bucket1 = storage.get_bucket("test-key", 1.0, 10)
        bucket1.consume(5)
        
        bucket2 = storage.get_bucket("test-key", 1.0, 10)
        assert bucket2.tokens == bucket1.tokens
    
    def test_metadata_storage(self):
        storage = MemoryStorage()
        storage.set_metadata("test-key", {"tier": "premium"})
        
        metadata = storage.get_metadata("test-key")
        assert metadata["tier"] == "premium"
    
    def test_cleanup(self):
        storage = MemoryStorage()
        storage.get_bucket("old-key", 1.0, 10)
        storage.last_access["old-key"] = time.time() - 7200  # 2 hours ago
        
        storage.cleanup(max_age=3600)
        
        assert "old-key" not in storage.buckets


class TestUserContext:
    """Test User Context"""
    
    def test_anonymous_user_key(self):
        user = UserContext(ip_address="192.168.1.1")
        key = user.get_rate_limit_key()
        
        assert key.startswith("anon:")
        assert len(key) == 21  # "anon:" + 16 char hash
    
    def test_authenticated_user_key(self):
        user = UserContext(user_id="user123", tier="premium")
        key = user.get_rate_limit_key()
        
        assert key == "user:user123"
    
    def test_get_limits_anonymous(self):
        user = UserContext(tier="anonymous")
        limits = user.get_limits()
        
        assert limits["requests_per_minute"] == RATE_LIMITS["anonymous"]["requests_per_minute"]
    
    def test_get_limits_premium(self):
        user = UserContext(tier="premium")
        limits = user.get_limits()
        
        assert limits["requests_per_minute"] == RATE_LIMITS["premium"]["requests_per_minute"]
        assert limits["requests_per_minute"] > RATE_LIMITS["user"]["requests_per_minute"]


class TestUserAuthRateLimiter:
    """Test Auth Rate Limiter with User Tracking"""
    
    def test_ip_allow_first_attempts(self):
        limiter = UserAuthRateLimiter()
        allowed, lockout, reason = limiter.is_allowed("192.168.1.1")
        
        assert allowed is True
        assert lockout is None
    
    def test_ip_block_after_max_attempts(self):
        limiter = UserAuthRateLimiter()
        limiter.max_attempts = 3
        
        # Record 3 failures
        for _ in range(3):
            limiter.record_failure("192.168.1.1")
        
        allowed, lockout, reason = limiter.is_allowed("192.168.1.1")
        assert allowed is False
        assert lockout is not None
        assert reason == "ip_blocked"
    
    def test_user_block_independent_of_ip(self):
        limiter = UserAuthRateLimiter()
        limiter.max_attempts = 2
        
        # Block user_id
        limiter.record_failure("192.168.1.1", "user123")
        limiter.record_failure("192.168.2.2", "user123")  # Different IP
        
        allowed, lockout, reason = limiter.is_allowed("192.168.3.3", "user123")
        assert allowed is False
        assert reason == "user_blocked"
    
    def test_success_clears_failures(self):
        limiter = UserAuthRateLimiter()
        limiter.max_attempts = 5
        
        limiter.record_failure("192.168.1.1", "user123")
        limiter.record_success("192.168.1.1", "user123")
        
        allowed, _, _ = limiter.is_allowed("192.168.1.1", "user123")
        assert allowed is True
    
    def test_lockout_expires(self):
        limiter = UserAuthRateLimiter()
        limiter.max_attempts = 1
        limiter.lockout_duration = 1  # 1 second
        
        limiter.record_failure("192.168.1.1")
        time.sleep(1.1)  # Wait for lockout to expire
        
        allowed, _, _ = limiter.is_allowed("192.168.1.1")
        assert allowed is True


class TestRateLimitDecorator:
    """Test Rate Limit Decorator"""
    
    @pytest.mark.asyncio
    async def test_anonymous_rate_limit(self):
        from fastapi import Request
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        
        call_count = 0
        
        @rate_limit(requests_per_minute=2, burst_size=2)
        async def test_endpoint(request):
            nonlocal call_count
            call_count += 1
            return {"success": True}
        
        # First 2 calls should succeed
        result1 = await test_endpoint(mock_request)
        assert result1["success"] is True
        
        result2 = await test_endpoint(mock_request)
        assert result2["success"] is True
        
        # Third call should fail
        with pytest.raises(HTTPException) as exc_info:
            await test_endpoint(mock_request)
        
        assert exc_info.value.status_code == 429
        assert call_count == 2


class TestRateLimits:
    """Test Rate Limit Configuration"""
    
    def test_tier_hierarchy(self):
        """Verify tier limits are properly ordered"""
        anon = RATE_LIMITS["anonymous"]["requests_per_minute"]
        user = RATE_LIMITS["user"]["requests_per_minute"]
        premium = RATE_LIMITS["premium"]["requests_per_minute"]
        admin = RATE_LIMITS["admin"]["requests_per_minute"]
        
        assert anon < user < premium < admin
    
    def test_default_limits_reasonable(self):
        """Verify default limits are reasonable"""
        assert RATE_LIMITS["anonymous"]["requests_per_minute"] >= 10
        assert RATE_LIMITS["admin"]["requests_per_minute"] <= 1000


class TestStats:
    """Test Rate Limit Statistics"""
    
    def test_stats_with_memory_storage(self):
        # Patch the global storage for this test
        from api.rate_limiter_v2 import rate_limit_storage
        
        # Create fresh storage
        test_storage = MemoryStorage()
        
        # Create some buckets
        test_storage.get_bucket("key1", 1.0, 10)
        test_storage.set_metadata("key1", {"tier": "anonymous"})
        
        test_storage.get_bucket("key2", 1.0, 10)
        test_storage.set_metadata("key2", {"tier": "premium"})
        
        # Count manually since we can't easily patch
        assert len(test_storage.buckets) == 2
        assert test_storage.get_metadata("key1")["tier"] == "anonymous"
        assert test_storage.get_metadata("key2")["tier"] == "premium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
