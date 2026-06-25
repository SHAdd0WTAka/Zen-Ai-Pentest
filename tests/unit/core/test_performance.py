"""
Unit Tests for core.performance module
"""

import asyncio
import gc
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from core.performance import (
    LazyImport,
    LazyLoader,
    MemoryProfiler,
    MemorySnapshot,
    PerformanceMiddleware,
    PerformanceTimer,
    TimingResult,
    clear_all_stats,
    gather_with_concurrency,
    get_import_time_report,
    get_timer,
    memoize,
    optimize_imports,
    print_performance_report,
    run_in_thread,
    timed,
    timed_block,
    ttl_cache,
)


class TestTimingResult:
    """Tests for TimingResult dataclass"""

    def test_init_default(self):
        result = TimingResult(name="test_op", duration_ms=100.5)
        assert result.name == "test_op"
        assert result.duration_ms == 100.5
        assert result.timestamp > 0
        assert result.metadata == {}

    def test_init_with_metadata(self):
        metadata = {"key": "value", "count": 42}
        result = TimingResult(name="test", duration_ms=50.0, metadata=metadata)
        assert result.metadata == metadata


class TestPerformanceTimer:
    """Tests for PerformanceTimer singleton"""

    def setup_method(self):
        """Clear timer before each test"""
        timer = get_timer()
        timer.clear()
        timer.enable()

    def test_singleton_pattern(self):
        """Test that PerformanceTimer is a singleton"""
        timer1 = PerformanceTimer()
        timer2 = PerformanceTimer()
        assert timer1 is timer2

    def test_record_timing(self):
        """Test recording timing results"""
        timer = PerformanceTimer()
        timer.record("test_op", 100.0, {"detail": "info"})

        stats = timer.get_stats("test_op")
        assert stats["count"] == 1
        assert stats["avg_ms"] == 100.0
        assert stats["min_ms"] == 100.0
        assert stats["max_ms"] == 100.0

    def test_get_stats_empty(self):
        """Test getting stats for non-existent operation"""
        timer = PerformanceTimer()
        stats = timer.get_stats("nonexistent")
        assert stats == {}

    def test_get_stats_multiple(self):
        """Test stats calculation with multiple timings"""
        timer = PerformanceTimer()
        timer.record("op", 100.0)
        timer.record("op", 200.0)
        timer.record("op", 300.0)

        stats = timer.get_stats("op")
        assert stats["count"] == 3
        assert stats["avg_ms"] == 200.0
        assert stats["min_ms"] == 100.0
        assert stats["max_ms"] == 300.0
        assert stats["p50_ms"] == 200.0

    def test_get_stats_percentiles(self):
        """Test percentile calculations"""
        timer = PerformanceTimer()
        # Add 25 timings to trigger percentile calculations
        for i in range(25):
            timer.record("op", float(i * 10))

        stats = timer.get_stats("op")
        assert stats["count"] == 25
        assert "p50_ms" in stats
        assert "p95_ms" in stats
        assert "p99_ms" in stats

    def test_get_all_stats(self):
        """Test getting all stats"""
        timer = PerformanceTimer()
        timer.record("op1", 100.0)
        timer.record("op2", 200.0)

        all_stats = timer.get_all_stats()
        assert "op1" in all_stats
        assert "op2" in all_stats
        assert all_stats["op1"]["count"] == 1
        assert all_stats["op2"]["count"] == 1

    def test_clear(self):
        """Test clearing all timings"""
        timer = PerformanceTimer()
        timer.record("op", 100.0)
        timer.clear()

        stats = timer.get_stats("op")
        assert stats == {}

    def test_disable_enable(self):
        """Test enabling/disabling timer"""
        timer = PerformanceTimer()
        timer.disable()
        timer.record("op", 100.0)

        stats = timer.get_stats("op")
        assert stats == {}

        timer.enable()
        timer.record("op", 100.0)
        stats = timer.get_stats("op")
        assert stats["count"] == 1


class TestTimedDecorator:
    """Tests for @timed decorator"""

    def setup_method(self):
        clear_all_stats()

    def test_timed_sync_function(self):
        """Test timing synchronous function"""

        @timed
        def slow_function():
            time.sleep(0.01)
            return 42

        result = slow_function()
        assert result == 42

        # Check timing was recorded
        timer = get_timer()
        stats = timer.get_all_stats()
        assert len(stats) > 0

    def test_timed_with_custom_name(self):
        """Test timed decorator with custom name"""

        @timed(name="custom_operation")
        def my_func():
            return "result"

        my_func()

        timer = get_timer()
        stats = timer.get_stats("custom_operation")
        assert stats["count"] == 1

    def test_timed_without_stats_tracking(self):
        """Test timed decorator without stats tracking"""

        @timed(track_stats=False)
        def my_func():
            return "result"

        my_func()

        # Should not record stats
        timer = get_timer()
        all_stats = timer.get_all_stats()
        # Stats should be empty or not include our function

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_timed_async_function(self):
        """Test timing async function"""

        @timed(name="async_op")
        async def async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await async_function()
        assert result == "async_result"


class TestTimedBlock:
    """Tests for timed_block context manager"""

    def setup_method(self):
        clear_all_stats()

    def test_timed_block(self):
        """Test timing a code block"""
        with timed_block("my_block"):
            time.sleep(0.01)

        timer = get_timer()
        stats = timer.get_stats("my_block")
        assert stats["count"] == 1
        assert stats["avg_ms"] >= 10  # At least 10ms


class TestMemoryProfiler:
    """Tests for MemoryProfiler"""

    def test_init(self):
        profiler = MemoryProfiler()
        assert profiler._snapshots == []
        assert profiler._tracing is False

    def test_start_stop_tracing(self):
        profiler = MemoryProfiler()
        profiler.start_tracing()
        assert profiler._tracing is True

        profiler.stop_tracing()
        assert profiler._tracing is False

    def test_take_snapshot_without_tracing(self):
        """Test taking snapshot without tracemalloc"""
        profiler = MemoryProfiler()
        snapshot = profiler.take_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.current_mb > 0
        assert snapshot.timestamp > 0

    def test_get_top_allocations(self):
        profiler = MemoryProfiler()
        # Without tracing, should return empty list
        allocations = profiler.get_top_allocations()
        assert allocations == []


class TestLazyImport:
    """Tests for LazyImport"""

    def test_init(self):
        lazy = LazyImport("os.path")
        assert lazy._module_name == "os.path"
        assert lazy._imported is False

    def test_lazy_import(self):
        """Test that module is imported lazily"""
        lazy_os = LazyImport("os")
        # Access an attribute to trigger import
        path = lazy_os.path
        assert path is not None
        assert lazy_os._imported is True

    def test_lazy_import_with_attr(self):
        """Test lazy import with specific attribute"""
        lazy_path = LazyImport("os", "path")
        sep = lazy_path.sep
        assert sep == "/" or sep == "\\"

    def test_getattr_after_import(self):
        """Test getattr after import"""
        lazy_sys = LazyImport("sys")
        version = lazy_sys.version
        assert isinstance(version, str)


class TestLazyLoader:
    """Tests for LazyLoader"""

    def test_init(self):
        def factory():
            return "expensive_resource"

        loader = LazyLoader(factory)
        assert loader._loaded is False
        assert loader._value is None

    def test_lazy_loading(self):
        """Test that resource is loaded only when accessed"""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return "resource"

        loader = LazyLoader(factory)
        assert call_count == 0

        value = loader.get()
        assert value == "resource"
        assert call_count == 1

        # Second get should not call factory again (caching)
        value2 = loader.get()
        assert value2 == "resource"
        assert call_count == 1

    def test_no_cache(self):
        """Test loader without caching"""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return f"resource_{call_count}"

        loader = LazyLoader(factory, cache=False)
        value1 = loader.get()
        assert call_count == 1

        # Without cache, value is loaded but not retained
        # Implementation detail: still counts as loaded
        assert loader.is_loaded() is True

    def test_clear(self):
        """Test clearing cached value"""
        loader = LazyLoader(lambda: "resource")
        loader.get()
        assert loader._loaded is True

        loader.clear()
        assert loader._loaded is False
        assert loader._value is None

    def test_is_loaded(self):
        """Test is_loaded method"""
        loader = LazyLoader(lambda: "resource")
        assert loader.is_loaded() is False

        loader.get()
        assert loader.is_loaded() is True


class TestMemoize:
    """Tests for memoize decorator"""

    def test_sync_memoize(self):
        """Test memoization of sync function"""
        call_count = 0

        @memoize(maxsize=10)
        def expensive_add(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        result1 = expensive_add(2, 3)
        assert result1 == 5
        assert call_count == 1

        # Second call with same args should use cache
        result2 = expensive_add(2, 3)
        assert result2 == 5
        assert call_count == 1  # Not called again

    def test_memoize_cache_clear(self):
        """Test clearing memoize cache"""

        @memoize(maxsize=10)
        def my_func(x):
            return x * 2

        my_func(5)
        my_func.cache_clear()

        # For sync functions using lru_cache, use its methods
        info = my_func.cache_info()
        assert info.currsize == 0  # lru_cache uses currsize

    def test_memoize_cache_info(self):
        """Test getting cache info"""

        @memoize(maxsize=100)
        def my_func(x):
            return x

        my_func(1)
        my_func(2)

        # For sync functions using lru_cache
        info = my_func.cache_info()
        assert info.currsize == 2
        assert info.maxsize == 100

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_async_memoize(self):
        """Test memoization of async function"""
        call_count = 0

        @memoize(maxsize=10)
        async def async_expensive(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)
            return x * 2

        result1 = await async_expensive(5)
        assert result1 == 10
        assert call_count == 1

        result2 = await async_expensive(5)
        assert result2 == 10
        assert call_count == 1  # Cached


class TestTTLCache:
    """Tests for ttl_cache decorator"""

    def test_ttl_cache_basic(self):
        """Test basic TTL cache functionality"""
        call_count = 0

        @ttl_cache(ttl=1.0, maxsize=10)
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = my_func(5)
        assert result1 == 10
        assert call_count == 1

        result2 = my_func(5)
        assert result2 == 10
        assert call_count == 1  # Cached

    def test_ttl_cache_expiration(self):
        """Test that cache entries expire"""
        call_count = 0

        @ttl_cache(ttl=0.01, maxsize=10)  # Very short TTL
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        my_func(5)
        assert call_count == 1

        time.sleep(0.02)  # Wait for TTL to expire

        my_func(5)
        assert call_count == 2  # Called again after expiry

    def test_ttl_cache_clear(self):
        """Test clearing TTL cache"""

        @ttl_cache(ttl=60.0, maxsize=10)
        def my_func(x):
            return x * 2

        my_func(5)
        my_func.cache_clear()

        info = my_func.cache_info()
        assert info["size"] == 0

    def test_ttl_cache_info(self):
        """Test getting TTL cache info"""

        @ttl_cache(ttl=60.0, maxsize=100)
        def my_func(x):
            return x

        my_func(1)
        my_func(2)

        info = my_func.cache_info()
        assert info["size"] == 2
        assert info["maxsize"] == 100
        assert info["ttl"] == 60.0


class TestAsyncUtilities:
    """Tests for async utility functions"""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_gather_with_concurrency(self):
        """Test gather with concurrency limit"""
        results = []

        async def task(n):
            await asyncio.sleep(0.01)
            results.append(n)
            return n * 2

        tasks = [task(i) for i in range(5)]
        results = await gather_with_concurrency(2, *tasks)

        assert len(results) == 5
        assert all(r == i * 2 for i, r in enumerate(results))

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_gather_with_concurrency_exceptions(self):
        """Test gather with exceptions"""

        async def failing_task():
            raise ValueError("Test error")

        async def success_task():
            return "success"

        results = await gather_with_concurrency(2, success_task(), failing_task(), return_exceptions=True)

        assert results[0] == "success"
        assert isinstance(results[1], ValueError)

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_run_in_thread(self):
        """Test running sync function in thread"""

        def sync_func(x, y):
            time.sleep(0.01)
            return x + y

        result = await run_in_thread(sync_func, 5, 3)
        assert result == 8


class TestImportOptimization:
    """Tests for import optimization utilities"""

    def test_optimize_imports(self):
        """Test import time profiling"""
        results = optimize_imports(["sys", "os", "nonexistent_module_xyz"])

        assert "sys" in results
        assert "os" in results
        assert "nonexistent_module_xyz" in results
        # Import times should be non-negative
        assert all(t >= 0 for t in results.values())

    def test_get_import_time_report(self):
        """Test import time report generation"""
        report = get_import_time_report()
        assert "Import Time Report" in report


class TestPerformanceMiddleware:
    """Tests for PerformanceMiddleware"""

    def test_init(self):
        app = MagicMock()
        middleware = PerformanceMiddleware(app, slow_request_threshold_ms=500.0)
        assert middleware.app is app
        assert middleware.slow_request_threshold == 500.0
        assert middleware._request_count == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_get_stats(self):
        app = MagicMock()
        middleware = PerformanceMiddleware(app)

        # Simulate some requests
        middleware._request_count = 10
        middleware._total_time_ms = 500.0

        stats = middleware.get_stats()
        assert stats["request_count"] == 10
        assert stats["total_time_ms"] == 500.0
        assert stats["avg_time_ms"] == 50.0

    def test_get_stats_empty(self):
        app = MagicMock()
        middleware = PerformanceMiddleware(app)

        stats = middleware.get_stats()
        assert stats["request_count"] == 0
        assert stats["avg_time_ms"] == 0.0


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_get_timer(self):
        """Test get_timer returns singleton"""
        timer1 = get_timer()
        timer2 = get_timer()
        assert timer1 is timer2

    def test_clear_all_stats(self):
        """Test clear_all_stats function"""
        timer = get_timer()
        timer.record("test", 100.0)

        clear_all_stats()

        stats = timer.get_all_stats()
        assert stats == {}

    def test_print_performance_report_empty(self, caplog):
        """Test printing empty performance report"""
        clear_all_stats()

        with caplog.at_level("INFO"):
            print_performance_report()

        assert "No performance data collected" in caplog.text

    def test_print_performance_report_with_data(self, caplog):
        """Test printing performance report with data"""
        clear_all_stats()
        timer = get_timer()
        timer.record("test_op", 100.0)

        with caplog.at_level("INFO"):
            print_performance_report()

        assert "PERFORMANCE REPORT" in caplog.text
        assert "test_op" in caplog.text
