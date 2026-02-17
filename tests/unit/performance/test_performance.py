"""
Performance Module Tests

Tests caching, pooling, and async optimization.
"""

import pytest
import asyncio

# Import performance components
try:
    from performance import CacheManager, PerformanceMetrics
    from performance.pool import ConnectionPool, PoolConfig
    from performance.async_optimizer import AsyncOptimizer, CircuitBreaker, RetryHandler
except ImportError:
    import sys
    sys.path.insert(0, "../../..")
    from performance import CacheManager, PerformanceMetrics
    from performance.pool import ConnectionPool, PoolConfig
    from performance.async_optimizer import AsyncOptimizer, CircuitBreaker, RetryHandler


class TestCacheManager:
    """Test cache manager"""

    @pytest.fixture
    async def cache(self):
        """Create test cache"""
        c = CacheManager()
        await c.start()
        yield c
        await c.stop()

    @pytest.mark.asyncio
    async def test_basic_get_set(self, cache):
        """Test basic get/set operations"""
        await cache.set("key1", "value1", ttl=60)
        value = await cache.get("key1")

        assert value == "value1"

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss"""
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test TTL expiration"""
        await cache.set("key", "value", ttl=1)

        # Should exist immediately
        assert await cache.get("key") == "value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        """Test cache deletion"""
        await cache.set("key", "value")

        success = await cache.delete("key")
        assert success is True

        assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_get_or_set(self, cache):
        """Test get_or_set operation"""
        call_count = 0

        async def factory():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"

        # First call should create
        value1 = await cache.get_or_set("key", factory, ttl=60)
        assert value1 == "value_1"

        # Second call should use cached value
        value2 = await cache.get_or_set("key", factory, ttl=60)
        assert value2 == "value_1"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics"""
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] >= 1


class TestConnectionPool:
    """Test connection pool"""

    @pytest.fixture
    async def pool(self):
        """Create test pool"""
        conn_counter = 0

        async def factory():
            nonlocal conn_counter
            conn_counter += 1
            return {"id": conn_counter}

        config = PoolConfig(min_size=2, max_size=5)
        p = ConnectionPool(factory, config, name="test")
        await p.start()
        yield p
        await p.stop()

    @pytest.mark.asyncio
    async def test_pool_initialization(self, pool):
        """Test pool initializes with minimum connections"""
        stats = pool.get_stats()
        assert stats["total"] >= 2  # min_size

    @pytest.mark.asyncio
    async def test_acquire_release(self, pool):
        """Test acquiring and releasing connections"""
        conn = await pool.acquire()
        assert conn.in_use is True

        await pool.release(conn)
        assert conn.in_use is False

    @pytest.mark.asyncio
    async def test_pool_limits(self, pool):
        """Test pool respects max size"""
        # Acquire all available connections
        connections = []
        for _ in range(5):  # max_size
            try:
                conn = await pool.acquire()
                connections.append(conn)
            except RuntimeError:
                break

        # Release all
        for conn in connections:
            await pool.release(conn)

        stats = pool.get_stats()
        assert stats["total"] <= 5


class TestAsyncOptimizer:
    """Test async optimizer"""

    @pytest.mark.asyncio
    async def test_gather_limit(self):
        """Test gather with concurrency limit"""
        optimizer = AsyncOptimizer(max_workers=3)

        async def task(n):
            await asyncio.sleep(0.01)
            return n

        coros = [task(i) for i in range(10)]
        results = await optimizer.gather_limit(coros, limit=3)

        assert len(results) == 10
        assert sorted(results) == list(range(10))

    @pytest.mark.asyncio
    async def test_batch_process(self):
        """Test batch processing"""
        optimizer = AsyncOptimizer(batch_size=3)

        async def processor(item):
            await asyncio.sleep(0.01)
            return item * 2

        items = [1, 2, 3, 4, 5, 6, 7, 8]
        results = await optimizer.batch_process(items, processor, batch_size=3)

        assert results == [2, 4, 6, 8, 10, 12, 14, 16]


class TestCircuitBreaker:
    """Test circuit breaker"""

    @pytest.mark.asyncio
    async def test_circuit_closed(self):
        """Test circuit breaker in closed state"""
        cb = CircuitBreaker(failure_threshold=3)

        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_circuit_opens(self):
        """Test circuit breaker opens after failures"""
        cb = CircuitBreaker(failure_threshold=2)

        async def fail_func():
            raise Exception("Failure")

        # First failure
        with pytest.raises(Exception):
            await cb.call(fail_func)

        # Second failure - should open circuit
        with pytest.raises(Exception):
            await cb.call(fail_func)

        assert cb.get_state() == "open"

        # Subsequent calls should fail fast
        with pytest.raises(Exception) as exc_info:
            await cb.call(fail_func)
        assert "Circuit breaker is open" in str(exc_info.value)


class TestRetryHandler:
    """Test retry handler"""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test successful execution without retry"""
        retry = RetryHandler(max_retries=3)

        async def success_func():
            return "success"

        result = await retry.execute(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test success after some retries"""
        retry = RetryHandler(max_retries=3, base_delay=0.01)

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Failure {call_count}")
            return "success"

        result = await retry.execute(flaky_func)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self):
        """Test failure after all retries"""
        retry = RetryHandler(max_retries=2, base_delay=0.01)

        async def always_fail():
            raise Exception("Always fails")

        with pytest.raises(Exception) as exc_info:
            await retry.execute(always_fail)
        assert "Always fails" in str(exc_info.value)


class TestPerformanceMetrics:
    """Test performance metrics"""

    def test_record_and_get_stats(self):
        """Test recording and retrieving stats"""
        metrics = PerformanceMetrics()

        # Record some samples
        for i in range(10):
            metrics.record("response_time", 0.1 * i)

        stats = metrics.get_stats("response_time")

        assert stats["count"] == 10
        assert stats["min"] == 0.0
        assert stats["max"] == 0.9
        assert "mean" in stats
        assert "median" in stats

    def test_counters(self):
        """Test counter increments"""
        metrics = PerformanceMetrics()

        metrics.increment("requests")
        metrics.increment("requests")
        metrics.increment("errors")

        counters = metrics.get_counters()
        assert counters["requests"] == 2
        assert counters["errors"] == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
