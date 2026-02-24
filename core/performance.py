"""
Performance Utilities for Zen-AI-Pentest

Provides:
- Timing decorators and context managers
- Memory profiling utilities
- Performance monitoring middleware
- Lazy loading helpers
- Import optimization utilities
"""

import asyncio
import functools
import gc
import importlib
import importlib.util
import inspect
import logging
import sys
import threading
import time
import tracemalloc
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Timing Decorators and Context Managers
# =============================================================================


@dataclass
class TimingResult:
    """Result from timing a function or code block"""

    name: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceTimer:
    """High-precision performance timer with statistics"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._timings: Dict[str, List[TimingResult]] = defaultdict(list)
        self._enabled = True
        self._initialized = True

    def record(self, name: str, duration_ms: float, metadata: Optional[Dict] = None):
        """Record a timing result"""
        if not self._enabled:
            return
        result = TimingResult(name=name, duration_ms=duration_ms, metadata=metadata or {})
        self._timings[name].append(result)

    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a timed operation"""
        timings = self._timings.get(name, [])
        if not timings:
            return {}

        durations = [t.duration_ms for t in timings]
        durations.sort()

        n = len(durations)
        return {
            "count": n,
            "avg_ms": sum(durations) / n,
            "min_ms": durations[0],
            "max_ms": durations[-1],
            "p50_ms": durations[int(n * 0.5)],
            "p95_ms": durations[int(n * 0.95)] if n > 20 else durations[-1],
            "p99_ms": durations[int(n * 0.99)] if n > 100 else durations[-1],
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all timed operations"""
        return {name: self.get_stats(name) for name in self._timings.keys()}

    def clear(self):
        """Clear all recorded timings"""
        self._timings.clear()

    def enable(self):
        """Enable timing collection"""
        self._enabled = True

    def disable(self):
        """Disable timing collection"""
        self._enabled = False


# Global timer instance
_timer = PerformanceTimer()


def timed(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    log_level: int = logging.DEBUG,
    track_stats: bool = True,
):
    """
    Decorator to time function execution.

    Usage:
        @timed
        def my_func(): ...

        @timed(name="custom_name", log_level=logging.INFO)
        async def my_async_func(): ...
    """

    def decorator(fn: Callable) -> Callable:
        timer_name = name or f"{fn.__module__}.{fn.__name__}"

        if asyncio.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return await fn(*args, **kwargs)
                finally:
                    duration = (time.perf_counter() - start) * 1000
                    if track_stats:
                        _timer.record(timer_name, duration)
                    logger.log(log_level, f"{timer_name}: {duration:.2f}ms")

            return async_wrapper
        else:

            @wraps(fn)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return fn(*args, **kwargs)
                finally:
                    duration = (time.perf_counter() - start) * 1000
                    if track_stats:
                        _timer.record(timer_name, duration)
                    logger.log(log_level, f"{timer_name}: {duration:.2f}ms")

            return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator


@contextmanager
def timed_block(name: str, log_level: int = logging.DEBUG):
    """Context manager for timing code blocks"""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = (time.perf_counter() - start) * 1000
        _timer.record(name, duration)
        logger.log(log_level, f"{name}: {duration:.2f}ms")


# =============================================================================
# Memory Profiling
# =============================================================================


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""

    current_mb: float
    peak_mb: float
    timestamp: float = field(default_factory=time.time)


class MemoryProfiler:
    """Memory profiling utilities"""

    def __init__(self):
        self._snapshots: List[MemorySnapshot] = []
        self._tracing = False

    def start_tracing(self):
        """Start memory tracing with tracemalloc"""
        if not self._tracing:
            tracemalloc.start()
            self._tracing = True

    def stop_tracing(self):
        """Stop memory tracing"""
        if self._tracing:
            tracemalloc.stop()
            self._tracing = False

    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory snapshot"""
        if self._tracing:
            current, peak = tracemalloc.get_traced_memory()
            snapshot = MemorySnapshot(current_mb=current / 1024 / 1024, peak_mb=peak / 1024 / 1024)
        else:
            gc.collect()
            import psutil

            process = psutil.Process()
            mem_info = process.memory_info()
            snapshot = MemorySnapshot(
                current_mb=mem_info.rss / 1024 / 1024,
                peak_mb=mem_info.rss / 1024 / 1024,  # Approximation
            )
        self._snapshots.append(snapshot)
        return snapshot

    def get_top_allocations(self, limit: int = 10) -> List[Dict]:
        """Get top memory allocations (requires tracing)"""
        if not self._tracing:
            return []
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")[:limit]
        return [
            {"file": str(stat.traceback.format()[-1]), "size_mb": stat.size / 1024 / 1024, "count": stat.count}
            for stat in top_stats
        ]


@contextmanager
def memory_profile(name: str = "memory_block"):
    """Context manager for profiling memory usage"""
    profiler = MemoryProfiler()
    profiler.start_tracing()
    gc.collect()
    start_snapshot = profiler.take_snapshot()

    try:
        yield profiler
    finally:
        end_snapshot = profiler.take_snapshot()
        gc.collect()
        final_snapshot = profiler.take_snapshot()

        profiler.stop_tracing()

        delta = final_snapshot.current_mb - start_snapshot.current_mb
        logger.debug(
            f"{name}: Memory delta: {delta:+.2f}MB "
            f"(start: {start_snapshot.current_mb:.2f}MB, "
            f"end: {final_snapshot.current_mb:.2f}MB, "
            f"peak: {end_snapshot.peak_mb:.2f}MB)"
        )


# =============================================================================
# Lazy Loading Utilities
# =============================================================================


class LazyImport:
    """
    Lazy module importer - delays import until first use.

    Usage:
        # Instead of: import heavy_module
        heavy_module = LazyImport("heavy_module")

        # Module is only imported when accessed:
        heavy_module.some_function()
    """

    def __init__(self, module_name: str, attr: Optional[str] = None):
        self._module_name = module_name
        self._attr = attr
        self._module = None
        self._imported = False

    def _import(self):
        if not self._imported:
            self._module = importlib.import_module(self._module_name)
            if self._attr:
                self._module = getattr(self._module, self._attr)
            self._imported = True
        return self._module

    def __getattr__(self, name: str):
        return getattr(self._import(), name)

    def __call__(self, *args, **kwargs):
        return self._import()(*args, **kwargs)

    def __iter__(self):
        return iter(self._import())

    def __getitem__(self, key):
        return self._import()[key]


class LazyLoader:
    """
    Class-based lazy loader for expensive resources.

    Usage:
        class MyService:
            _expensive_resource = LazyLoader(lambda: load_expensive_resource())

            def use_resource(self):
                resource = self._expensive_resource.get()
                ...
    """

    def __init__(self, factory: Callable[[], T], cache: bool = True):
        self._factory = factory
        self._cache = cache
        self._value: Optional[T] = None
        self._loaded = False
        self._lock = threading.Lock()

    def get(self) -> T:
        if not self._loaded:
            with self._lock:
                if not self._loaded:
                    self._value = self._factory()
                    self._loaded = True
                    if not self._cache:
                        # Don't keep reference if not caching
                        result = self._value
                        self._value = None
                        return result
        return self._value

    def clear(self):
        """Clear cached value"""
        self._value = None
        self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded


# =============================================================================
# Caching Decorators
# =============================================================================


def memoize(maxsize: int = 128, typed: bool = False):
    """
    Memoization decorator with LRU cache.
    Works with both sync and async functions.

    Usage:
        @memoize(maxsize=256)
        def expensive_calculation(x, y): ...

        @memoize(maxsize=100)
        async def expensive_async_op(x): ...
    """

    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):
            # Async version
            cache: Dict = {}
            cache_order: List = []

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                key = _make_key(args, kwargs, typed)

                if key in cache:
                    # Move to end (most recently used)
                    cache_order.remove(key)
                    cache_order.append(key)
                    return cache[key]

                result = await fn(*args, **kwargs)

                if len(cache) >= maxsize:
                    # Remove least recently used
                    lru_key = cache_order.pop(0)
                    del cache[lru_key]

                cache[key] = result
                cache_order.append(key)
                return result

            # Attach cache management
            async_wrapper.cache_clear = lambda: (cache.clear(), cache_order.clear())
            async_wrapper.cache_info = lambda: {"size": len(cache), "maxsize": maxsize}

            return async_wrapper
        else:
            # Sync version - use functools.lru_cache
            return lru_cache(maxsize=maxsize, typed=typed)(fn)

    return decorator


def _make_key(args, kwargs, typed: bool) -> tuple:
    """Create cache key from arguments"""
    key = (args, tuple(sorted(kwargs.items())))
    if typed:
        key += tuple(type(arg) for arg in args)
        key += tuple(type(v) for k, v in sorted(kwargs.items()))
    return key


def ttl_cache(ttl: float, maxsize: int = 128):
    """
    Time-based cache with TTL expiration.

    Usage:
        @ttl_cache(ttl=300, maxsize=100)  # Cache for 5 minutes
        def get_expensive_data(key): ...
    """

    def decorator(fn: Callable) -> Callable:
        cache: Dict[Any, tuple[Any, float]] = {}
        lock = threading.Lock()

        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs, typed=False)
            now = time.time()

            with lock:
                # Check cache
                if key in cache:
                    value, expiry = cache[key]
                    if now < expiry:
                        return value
                    else:
                        del cache[key]

            # Compute value
            result = fn(*args, **kwargs)

            with lock:
                # Store with TTL
                if len(cache) >= maxsize:
                    # Remove oldest entry
                    oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                    del cache[oldest_key]

                cache[key] = (result, now + ttl)

            return result

        def cache_clear():
            with lock:
                cache.clear()

        def cache_info():
            with lock:
                now = time.time()
                valid = sum(1 for _, expiry in cache.values() if now < expiry)
                return {"size": len(cache), "valid": valid, "maxsize": maxsize, "ttl": ttl}

        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info

        return wrapper

    return decorator


# =============================================================================
# Async Optimizations
# =============================================================================


async def gather_with_concurrency(limit: int, *tasks, return_exceptions: bool = False):
    """
    Run tasks with limited concurrency.

    Usage:
        results = await gather_with_concurrency(
            10,  # Max 10 concurrent
            *[fetch_data(url) for url in urls]
        )
    """
    semaphore = asyncio.Semaphore(limit)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*[sem_task(task) for task in tasks], return_exceptions=return_exceptions)


async def run_in_thread(func: Callable, *args, executor=None, **kwargs):
    """
    Run a blocking function in a thread pool.

    Usage:
        # Instead of blocking the event loop:
        result = await run_in_thread(cpu_intensive_func, data)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))


# =============================================================================
# Import Optimization
# =============================================================================


def optimize_imports(module_names: List[str]) -> Dict[str, float]:
    """
    Profile import times for given modules.

    Returns dict of module name -> import time in ms.
    """
    results = {}
    for name in module_names:
        start = time.perf_counter()
        try:
            importlib.import_module(name)
        except ImportError:
            pass
        results[name] = (time.perf_counter() - start) * 1000
    return results


def get_import_time_report() -> str:
    """Generate a report of import times from sys.modules"""
    lines = ["Import Time Report", "=" * 50]
    # Note: This only works if importtime was enabled at startup
    lines.append("Use 'python -X importtime' for detailed import profiling")
    return "\n".join(lines)


# =============================================================================
# Performance Monitoring Middleware (for FastAPI)
# =============================================================================


class PerformanceMiddleware:
    """
    FastAPI middleware for performance monitoring.

    Usage:
        from fastapi import FastAPI
        from core.performance import PerformanceMiddleware

        app = FastAPI()
        app.add_middleware(PerformanceMiddleware)
    """

    def __init__(self, app, slow_request_threshold_ms: float = 1000.0):
        self.app = app
        self.slow_request_threshold = slow_request_threshold_ms
        self._request_count = 0
        self._total_time_ms = 0.0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        self._request_count += 1

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                duration = (time.perf_counter() - start) * 1000
                self._total_time_ms += duration

                # Add timing header
                headers = list(message.get("headers", []))
                headers.append((b"X-Response-Time", f"{duration:.2f}ms".encode()))
                message["headers"] = headers

                # Log slow requests
                if duration > self.slow_request_threshold:
                    path = scope.get("path", "unknown")
                    logger.warning(f"Slow request: {path} took {duration:.2f}ms")

            await send(message)

        await self.app(scope, receive, wrapped_send)

    def get_stats(self) -> Dict[str, float]:
        """Get middleware statistics"""
        return {
            "request_count": self._request_count,
            "total_time_ms": self._total_time_ms,
            "avg_time_ms": self._total_time_ms / self._request_count if self._request_count > 0 else 0,
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def get_timer() -> PerformanceTimer:
    """Get the global performance timer instance"""
    return _timer


def clear_all_stats():
    """Clear all performance statistics"""
    _timer.clear()


def print_performance_report():
    """Print a performance report to the logger"""
    stats = _timer.get_all_stats()

    if not stats:
        logger.info("No performance data collected")
        return

    logger.info("=" * 60)
    logger.info("PERFORMANCE REPORT")
    logger.info("=" * 60)

    for name, stat in sorted(stats.items(), key=lambda x: x[1].get("avg_ms", 0), reverse=True):
        logger.info(f"\n{name}:")
        logger.info(f"  Count: {stat['count']}")
        logger.info(f"  Avg: {stat['avg_ms']:.2f}ms")
        logger.info(f"  Min: {stat['min_ms']:.2f}ms")
        logger.info(f"  Max: {stat['max_ms']:.2f}ms")
        if "p95_ms" in stat:
            logger.info(f"  P95: {stat['p95_ms']:.2f}ms")


# Export all public APIs
__all__ = [
    # Timing
    "timed",
    "timed_block",
    "TimingResult",
    "PerformanceTimer",
    "get_timer",
    # Memory
    "MemorySnapshot",
    "MemoryProfiler",
    "memory_profile",
    # Lazy Loading
    "LazyImport",
    "LazyLoader",
    # Caching
    "memoize",
    "ttl_cache",
    # Async
    "gather_with_concurrency",
    "run_in_thread",
    # Import optimization
    "optimize_imports",
    "get_import_time_report",
    # Middleware
    "PerformanceMiddleware",
    # Utilities
    "clear_all_stats",
    "print_performance_report",
]
