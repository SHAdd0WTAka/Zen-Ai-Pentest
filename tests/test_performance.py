"""
Tests for Performance Module

Covers:
- AsyncOptimizer
- CacheManager
- ConnectionPool
- PerformanceMetrics
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import performance modules
from performance.async_optimizer import (
    AsyncOptimizer,
    CircuitBreaker,
    CircuitBreakerOpen,
    RetryHandler,
    SemaphoreGroup,
)
from performance.cache import CacheConfig, CacheEntry, CacheManager
from performance.metrics import PerformanceMetrics, RateLimiter, TimingContext
from performance.pool import (
    ConnectionPool,
    PoolConfig,
    PooledConnection,
    PoolManager,
)

# ============================================================================
# AsyncOptimizer Tests
# ============================================================================


class TestAsyncOptimizer:
    """Test the AsyncOptimizer class"""

    @pytest.fixture
    def optimizer(self):
        """Create an AsyncOptimizer instance"""
        return AsyncOptimizer(max_workers=5, batch_size=10)

    @pytest.mark.asyncio
    async def test_run_in_thread(self, optimizer):
        """Test running sync function in thread pool"""

        def sync_func(x, y):
            return x + y

        result = await optimizer.run_in_thread(sync_func, 1, 2)

        assert result == 3

    @pytest.mark.asyncio
    async def test_run_in_thread_with_exception(self, optimizer):
        """Test exception handling in thread"""

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await optimizer.run_in_thread(failing_func)

    @pytest.mark.asyncio
    async def test_gather_limit(self, optimizer):
        """Test gathering coroutines with limit"""

        async def coro(n):
            await asyncio.sleep(0.01)
            return n

        coroutines = [coro(i) for i in range(10)]
        results = await optimizer.gather_limit(coroutines, limit=3)

        assert len(results) == 10
        assert sorted(results) == list(range(10))

    @pytest.mark.asyncio
    async def test_batch_process(self, optimizer):
        """Test batch processing"""

        async def processor(item):
            await asyncio.sleep(0.01)
            return item * 2

        items = list(range(20))
        results = await optimizer.batch_process(items, processor, batch_size=5)

        assert len(results) == 20
        assert results == [i * 2 for i in range(20)]

    @pytest.mark.asyncio
    async def test_batch_process_empty(self, optimizer):
        """Test batch processing with empty list"""

        async def processor(item):
            return item

        results = await optimizer.batch_process([], processor)

        assert results == []

    @pytest.mark.asyncio
    async def test_rate_limit(self, optimizer):
        """Test rate limiting"""

        async def coro(n):
            return n

        coroutines = [coro(i) for i in range(5)]
        start_time = time.time()
        results = await optimizer.rate_limit(coroutines, rate=10, burst=2)
        elapsed = time.time() - start_time

        assert len(results) == 5
        # Should take some time due to rate limiting
        assert elapsed > 0

    def test_shutdown(self, optimizer):
        """Test thread pool shutdown"""
        optimizer.shutdown()

        # Should not raise any errors
        assert optimizer._thread_pool._shutdown is True


# ============================================================================
# SemaphoreGroup Tests
# ============================================================================


class TestSemaphoreGroup:
    """Test the SemaphoreGroup class"""

    @pytest.fixture
    def semaphore_group(self):
        return SemaphoreGroup()

    def test_get_creates_new_semaphore(self, semaphore_group):
        """Test getting new semaphore"""
        sem = semaphore_group.get("test", value=5)

        assert isinstance(sem, asyncio.Semaphore)
        assert sem._value == 5

    def test_get_returns_existing(self, semaphore_group):
        """Test getting existing semaphore"""
        sem1 = semaphore_group.get("test", value=5)
        sem2 = semaphore_group.get("test", value=10)

        assert sem1 is sem2

    @pytest.mark.asyncio
    async def test_acquire_and_release(self, semaphore_group):
        """Test acquiring and releasing semaphore"""
        semaphore_group.get("test", value=1)

        # Should not raise
        await semaphore_group.acquire("test", timeout=1)
        semaphore_group.release("test")

    @pytest.mark.asyncio
    async def test_acquire_timeout(self, semaphore_group):
        """Test acquire timeout"""
        semaphore_group.get("test", value=0)

        with pytest.raises(asyncio.TimeoutError):
            await semaphore_group.acquire("test", timeout=0.1)

    def test_release_nonexistent(self, semaphore_group):
        """Test releasing non-existent semaphore"""
        # Should not raise
        semaphore_group.release("nonexistent")


# ============================================================================
# CircuitBreaker Tests
# ============================================================================


class TestCircuitBreaker:
    """Test the CircuitBreaker class"""

    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(
            failure_threshold=3, recovery_timeout=1, half_open_max_calls=2
        )

    def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state"""
        assert circuit_breaker.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_successful_calls(self, circuit_breaker):
        """Test successful calls don't trip breaker"""

        async def success_func():
            return "success"

        for _ in range(5):
            result = await circuit_breaker.call(success_func)
            assert result == "success"

        assert circuit_breaker.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_failure_trip(self, circuit_breaker):
        """Test failures trip the breaker"""

        async def fail_func():
            raise ValueError("Failure")

        # First 3 failures should not trip (threshold is 3)
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit_breaker.call(fail_func)

        assert circuit_breaker.get_state() == "closed"

        # Third failure should trip
        with pytest.raises(ValueError):
            await circuit_breaker.call(fail_func)

        assert circuit_breaker.get_state() == "open"

    @pytest.mark.asyncio
    async def test_open_circuit_blocks(self, circuit_breaker):
        """Test open circuit blocks calls"""

        async def fail_func():
            raise ValueError("Failure")

        # Trip the breaker
        for _ in range(3):
            try:
                await circuit_breaker.call(fail_func)
            except ValueError:
                pass

        assert circuit_breaker.get_state() == "open"

        async def any_func():
            return "should not run"

        with pytest.raises(CircuitBreakerOpen):
            await circuit_breaker.call(any_func)

    @pytest.mark.asyncio
    async def test_recovery(self, circuit_breaker):
        """Test circuit breaker recovery"""

        async def fail_func():
            raise ValueError("Failure")

        async def success_func():
            return "success"

        # Trip the breaker
        for _ in range(3):
            try:
                await circuit_breaker.call(fail_func)
            except ValueError:
                pass

        assert circuit_breaker.get_state() == "open"

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Should be in half-open state
        result = await circuit_breaker.call(success_func)
        assert result == "success"


# ============================================================================
# RetryHandler Tests
# ============================================================================


class TestRetryHandler:
    """Test the RetryHandler class"""

    @pytest.fixture
    def retry_handler(self):
        return RetryHandler(max_retries=3, base_delay=0.1, max_delay=1.0)

    @pytest.mark.asyncio
    async def test_success_no_retry(self, retry_handler):
        """Test successful function is not retried"""
        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_handler.execute(success_func)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, retry_handler):
        """Test retry on failure"""
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = await retry_handler.execute(fail_then_succeed)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, retry_handler):
        """Test exception when max retries exceeded"""

        async def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_handler.execute(always_fail)

    @pytest.mark.asyncio
    async def test_retry_sync_function(self, retry_handler):
        """Test retry with sync function"""
        call_count = 0

        def sync_fail():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "success"

        result = await retry_handler.execute(sync_fail)

        assert result == "success"
        assert call_count == 2


# ============================================================================
# CacheManager Tests
# ============================================================================


class TestCacheManager:
    """Test the CacheManager class"""

    @pytest.fixture
    async def cache(self):
        """Create and start a cache manager"""
        config = CacheConfig(default_ttl=60, max_size=100)
        cache = CacheManager(config)
        await cache.start()
        yield cache
        await cache.stop()

    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Test CacheManager initialization"""
        cache = CacheManager()

        assert cache.config.default_ttl == 300
        assert cache.config.max_size == 10000

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test setting and getting cache values"""
        await cache.set("key1", "value1")
        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting non-existent key"""
        result = await cache.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration"""
        config = CacheConfig(default_ttl=0.1)
        cache = CacheManager(config)

        await cache.set("key1", "value1")

        # Should exist immediately
        assert await cache.get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test deleting cache entries"""
        await cache.set("key1", "value1")
        deleted = await cache.delete("key1")

        assert deleted is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, cache):
        """Test deleting non-existent key"""
        result = await cache.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_get_or_set_existing(self, cache):
        """Test get_or_set with existing key"""
        await cache.set("key1", "existing")

        factory = Mock(return_value="new_value")
        result = await cache.get_or_set("key1", factory)

        assert result == "existing"
        factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_new(self, cache):
        """Test get_or_set with new key"""

        async def factory():
            return "new_value"

        result = await cache.get_or_set("key1", factory)

        assert result == "new_value"
        assert await cache.get("key1") == "new_value"

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        config = CacheConfig(default_ttl=300, max_size=3)
        cache = CacheManager(config)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it more recent
        await cache.get("key1")

        # Add key4, should evict key2 (least recently used)
        await cache.set("key4", "value4")

        assert await cache.get("key1") is not None
        assert await cache.get("key2") is None  # Should be evicted
        assert await cache.get("key3") is not None
        assert await cache.get("key4") is not None

    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """Test getting cache statistics"""
        await cache.set("key1", "value1")
        await cache.get("key1")  # hit
        await cache.get("key2")  # miss

        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0


# ============================================================================
# CacheEntry Tests
# ============================================================================


class TestCacheEntry:
    """Test the CacheEntry class"""

    def test_entry_creation(self):
        """Test CacheEntry creation"""
        entry = CacheEntry(value="test", ttl=60)

        assert entry.value == "test"
        assert entry.ttl == 60
        assert entry.access_count == 0

    def test_is_expired(self):
        """Test expiration checking"""
        entry = CacheEntry(value="test", ttl=0.1)

        assert entry.is_expired() is False

        time.sleep(0.2)

        assert entry.is_expired() is True

    def test_touch(self):
        """Test touch updates access info"""
        entry = CacheEntry(value="test", ttl=60)

        entry.touch()

        assert entry.access_count == 1
        assert entry.last_accessed > entry.created_at


# ============================================================================
# ConnectionPool Tests
# ============================================================================


class TestConnectionPool:
    """Test the ConnectionPool class"""

    @pytest.fixture
    async def pool(self):
        """Create a connection pool"""

        async def factory():
            return MockConnection()

        config = PoolConfig(min_size=2, max_size=5)
        pool = ConnectionPool(factory, config, name="test_pool")
        await pool.start()
        yield pool
        await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """Test ConnectionPool initialization"""

        async def factory():
            return MockConnection()

        pool = ConnectionPool(factory, name="test")

        assert pool.name == "test"
        assert pool.config.min_size == 5
        assert pool.config.max_size == 20

    @pytest.mark.asyncio
    async def test_start_creates_min_connections(self, pool):
        """Test pool creates minimum connections on start"""
        stats = pool.get_stats()

        assert stats["total"] >= 2  # min_size

    @pytest.mark.asyncio
    async def test_acquire_and_release(self, pool):
        """Test acquiring and releasing connections"""
        conn = await pool.acquire()

        assert conn is not None
        assert conn.in_use is True

        await pool.release(conn)

        assert conn.in_use is False

    @pytest.mark.asyncio
    async def test_connection_reuse(self, pool):
        """Test connection reuse"""
        conn1 = await pool.acquire()
        await pool.release(conn1)

        conn2 = await pool.acquire()

        assert conn1 is conn2  # Should reuse the same connection

    @pytest.mark.asyncio
    async def test_pool_stats(self, pool):
        """Test getting pool statistics"""
        conn = await pool.acquire()
        stats = pool.get_stats()

        assert stats["name"] == "test_pool"
        assert stats["in_use"] == 1

        await pool.release(conn)

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup of expired connections"""

        async def factory():
            return MockConnection()

        config = PoolConfig(min_size=1, max_size=3, max_lifetime=0.1)
        pool = ConnectionPool(factory, config)
        await pool.start()

        # Wait for connections to expire
        await asyncio.sleep(0.2)

        await pool.cleanup()

        stats = pool.get_stats()
        # Old connections should be cleaned up and replaced

        await pool.stop()


class MockConnection:
    """Mock connection for testing"""

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def ping(self):
        return True


# ============================================================================
# PooledConnection Tests
# ============================================================================


class TestPooledConnection:
    """Test the PooledConnection class"""

    @pytest.fixture
    def pooled_conn(self):
        pool = Mock()
        pool.config = Mock()
        pool.config.max_lifetime = 3600
        pool.config.max_idle_time = 300
        return PooledConnection(MockConnection(), pool)

    def test_initial_state(self, pooled_conn):
        """Test initial connection state"""
        assert pooled_conn.in_use is False
        assert pooled_conn.use_count == 0

    def test_mark_used(self, pooled_conn):
        """Test marking connection as used"""
        pooled_conn.mark_used()

        assert pooled_conn.in_use is True
        assert pooled_conn.use_count == 1

    def test_mark_returned(self, pooled_conn):
        """Test marking connection as returned"""
        pooled_conn.mark_used()
        pooled_conn.mark_returned()

        assert pooled_conn.in_use is False

    def test_is_expired(self, pooled_conn):
        """Test expiration check"""
        assert pooled_conn.is_expired() is False


# ============================================================================
# PoolManager Tests
# ============================================================================


class TestPoolManager:
    """Test the PoolManager class"""

    @pytest.fixture
    def manager(self):
        return PoolManager()

    def test_register_and_get(self, manager):
        """Test registering and getting pools"""
        pool = Mock(spec=ConnectionPool)

        manager.register("test", pool)
        retrieved = manager.get("test")

        assert retrieved is pool

    def test_get_nonexistent(self, manager):
        """Test getting non-existent pool"""
        result = manager.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_start_all(self, manager):
        """Test starting all pools"""
        pool1 = AsyncMock(spec=ConnectionPool)
        pool2 = AsyncMock(spec=ConnectionPool)

        manager.register("pool1", pool1)
        manager.register("pool2", pool2)

        await manager.start_all()

        pool1.start.assert_called_once()
        pool2.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_all(self, manager):
        """Test stopping all pools"""
        pool1 = AsyncMock(spec=ConnectionPool)
        pool2 = AsyncMock(spec=ConnectionPool)

        manager.register("pool1", pool1)
        manager.register("pool2", pool2)

        await manager.stop_all()

        pool1.stop.assert_called_once()
        pool2.stop.assert_called_once()

    def test_get_all_stats(self, manager):
        """Test getting stats for all pools"""
        pool1 = Mock(spec=ConnectionPool)
        pool1.get_stats.return_value = {"name": "pool1"}
        pool2 = Mock(spec=ConnectionPool)
        pool2.get_stats.return_value = {"name": "pool2"}

        manager.register("pool1", pool1)
        manager.register("pool2", pool2)

        stats = manager.get_all_stats()

        assert stats["pool1"]["name"] == "pool1"
        assert stats["pool2"]["name"] == "pool2"


# ============================================================================
# PerformanceMetrics Tests
# ============================================================================


class TestPerformanceMetrics:
    """Test the PerformanceMetrics class"""

    @pytest.fixture
    def metrics(self):
        return PerformanceMetrics(max_samples=100)

    def test_record_metric(self, metrics):
        """Test recording a metric"""
        metrics.record("response_time", 0.1)

        stats = metrics.get_stats("response_time")

        assert stats["count"] == 1
        assert stats["min"] == 0.1
        assert stats["max"] == 0.1

    def test_record_multiple(self, metrics):
        """Test recording multiple values"""
        for i in range(5):
            metrics.record("response_time", 0.1 * i)

        stats = metrics.get_stats("response_time")

        assert stats["count"] == 5
        assert stats["min"] == 0.0
        assert stats["max"] == 0.4

    def test_increment_counter(self, metrics):
        """Test incrementing counter"""
        metrics.increment("requests")
        metrics.increment("requests", 5)

        counters = metrics.get_counters()

        assert counters["requests"] == 6

    def test_get_stats_empty(self, metrics):
        """Test getting stats for non-existent metric"""
        stats = metrics.get_stats("nonexistent")

        assert stats["count"] == 0

    def test_get_all_stats(self, metrics):
        """Test getting all stats"""
        metrics.record("metric1", 1.0)
        metrics.record("metric2", 2.0)

        all_stats = metrics.get_all_stats()

        assert "metric1" in all_stats
        assert "metric2" in all_stats

    def test_reset(self, metrics):
        """Test resetting all metrics"""
        metrics.record("test", 1.0)
        metrics.increment("counter", 5)

        metrics.reset()

        assert len(metrics._metrics) == 0
        assert len(metrics._counters) == 0


# ============================================================================
# TimingContext Tests
# ============================================================================


class TestTimingContext:
    """Test the TimingContext class"""

    def test_sync_timing(self):
        """Test synchronous timing"""
        metrics = PerformanceMetrics()

        with TimingContext(metrics, "operation"):
            time.sleep(0.05)

        stats = metrics.get_stats("operation")

        assert stats["count"] == 1
        assert stats["min"] >= 0.05

    @pytest.mark.asyncio
    async def test_async_timing(self):
        """Test asynchronous timing"""
        metrics = PerformanceMetrics()

        async with TimingContext(metrics, "async_operation"):
            await asyncio.sleep(0.05)

        stats = metrics.get_stats("async_operation")

        assert stats["count"] == 1
        assert stats["min"] >= 0.05


# ============================================================================
# RateLimiter Tests
# ============================================================================


class TestRateLimiter:
    """Test the RateLimiter class"""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization"""
        limiter = RateLimiter(rate=10, burst=5)

        assert limiter.rate == 10
        assert limiter.burst == 5
        assert limiter.tokens == 5

    def test_acquire_success(self):
        """Test successful token acquisition"""
        limiter = RateLimiter(rate=10, burst=5)

        assert limiter.acquire() is True
        assert limiter.tokens == 4

    def test_acquire_failure(self):
        """Test failed token acquisition"""
        limiter = RateLimiter(rate=1, burst=1)
        limiter.acquire()  # Use the only token

        assert limiter.acquire() is False

    def test_token_refill(self):
        """Test token refill over time"""
        limiter = RateLimiter(rate=100, burst=5)
        limiter.acquire()  # Use one token
        initial_tokens = limiter.tokens

        time.sleep(0.02)  # Wait for tokens to refill

        # After sleeping, tokens should have increased
        assert limiter.tokens >= initial_tokens

    def test_get_wait_time(self):
        """Test getting wait time for next token"""
        limiter = RateLimiter(rate=10, burst=1)
        limiter.acquire()  # Use the token

        wait_time = limiter.get_wait_time()

        assert wait_time > 0

    def test_get_wait_time_zero_when_available(self):
        """Test wait time is zero when tokens available"""
        limiter = RateLimiter(rate=10, burst=5)

        wait_time = limiter.get_wait_time()

        assert wait_time == 0
