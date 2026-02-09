"""
Tests für Monitoring Metrics
"""

import pytest
import sys

from unittest.mock import Mock

sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

from monitoring.metrics import (
    record_scan_created,
    record_scan_completed,
    record_finding,
    record_report_generated,
    record_auth_attempt,
    record_rate_limit_hit,
    get_health_status,
    init_app_info,
)


class TestBusinessMetrics:
    """Test business metric recording"""

    def test_record_scan_created(self):
        """Test recording scan creation"""
        # Should not raise exception
        record_scan_created("web")
        record_scan_created("network")
        record_scan_created("api")

    def test_record_scan_completed(self):
        """Test recording scan completion"""
        record_scan_completed("web", "success", 120.5)
        record_scan_completed("network", "failed", 60.0)

    def test_record_finding(self):
        """Test recording findings"""
        record_finding("critical", "sqli")
        record_finding("high", "xss")
        record_finding("medium", "csrf")

    def test_record_report_generated(self):
        """Test recording report generation"""
        record_report_generated("pdf")
        record_report_generated("json")
        record_report_generated("html")

    def test_record_auth_attempt(self):
        """Test recording auth attempts"""
        record_auth_attempt(True)
        record_auth_attempt(False)

    def test_record_rate_limit_hit(self):
        """Test recording rate limit hits"""
        record_rate_limit_hit("anonymous", "/api/scans")
        record_rate_limit_hit("user", "/api/reports")


class TestHealthStatus:
    """Test health status function"""

    def test_get_health_status(self):
        """Test getting health status"""
        status = get_health_status()

        assert "status" in status
        assert "metrics" in status
        assert status["status"] == "healthy"

    def test_health_status_structure(self):
        """Test health status response structure"""
        status = get_health_status()

        metrics = status["metrics"]
        assert "total_requests" in metrics
        assert "active_scans" in metrics
        assert "active_sessions" in metrics


class TestAppInfo:
    """Test app info initialization"""

    def test_init_app_info(self):
        """Test initializing app info"""
        init_app_info(version="2.3.9", environment="testing")


class TestMetricsMiddleware:
    """Test metrics middleware"""

    def test_middleware_initialization(self):
        """Test middleware can be initialized"""
        from monitoring.metrics import MetricsMiddleware

        mock_app = Mock()
        middleware = MetricsMiddleware(mock_app)

        assert middleware.app == mock_app

    def test_middleware_excluded_paths(self):
        """Test middleware excludes certain paths"""
        from monitoring.metrics import MetricsMiddleware

        mock_app = Mock()
        middleware = MetricsMiddleware(mock_app)

        # Check that common paths are excluded
        assert "/metrics" in middleware.exclude_paths
        assert "/health" in middleware.exclude_paths


class TestTokenBucket:
    """Test token bucket metrics"""

    def test_token_bucket_creation(self):
        """Test creating token bucket"""
        from monitoring.metrics import TokenBucket

        bucket = TokenBucket(rate=1.0, burst_size=10)
        assert bucket.tokens == 10
        assert bucket.burst_size == 10

    def test_token_bucket_consume(self):
        """Test consuming tokens"""
        from monitoring.metrics import TokenBucket

        bucket = TokenBucket(rate=1.0, burst_size=10)

        # Should be able to consume burst_size tokens
        for _ in range(10):
            assert bucket.consume() is True

        # Should fail after burst is exhausted
        assert bucket.consume() is False


class TestRateLimitStorage:
    """Test rate limit storage"""

    def test_storage_get_bucket(self):
        """Test getting bucket from storage"""
        from monitoring.metrics import RateLimitStorage

        storage = RateLimitStorage()
        bucket = storage.get_bucket("test_key", 1.0, 10)

        assert bucket is not None
        assert bucket.rate == 1.0
        assert bucket.burst_size == 10

    def test_storage_returns_same_bucket(self):
        """Test that same key returns same bucket"""
        from monitoring.metrics import RateLimitStorage

        storage = RateLimitStorage()
        bucket1 = storage.get_bucket("same_key", 1.0, 10)
        bucket1.tokens = 5

        bucket2 = storage.get_bucket("same_key", 1.0, 10)

        assert bucket1 is bucket2
        assert bucket2.tokens == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
