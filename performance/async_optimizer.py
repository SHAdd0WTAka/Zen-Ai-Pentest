"""
Async Optimization Utilities

Tools for optimizing async performance.
"""

import asyncio
import functools
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine, List, Optional

logger = logging.getLogger(__name__)


class AsyncOptimizer:
    """
    Async performance optimization utilities

    Provides:
    - Batched operations
    - Rate limiting
    - Bulk processing
    - Thread pool for sync operations
    """

    def __init__(self, max_workers: int = 10, batch_size: int = 100):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run sync function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._thread_pool, functools.partial(func, *args, **kwargs)
        )

    async def gather_limit(
        self, coroutines: List[Coroutine], limit: Optional[int] = None
    ) -> List[Any]:
        """
        Gather coroutines with concurrency limit

        Prevents overwhelming the event loop with too many concurrent tasks.
        """
        limit = limit or self.max_workers

        semaphore = asyncio.Semaphore(limit)

        async def sem_task(coro):
            async with semaphore:
                return await coro

        return await asyncio.gather(*[sem_task(c) for c in coroutines])

    async def batch_process(
        self,
        items: List[Any],
        processor: Callable[[Any], Coroutine],
        batch_size: Optional[int] = None,
    ) -> List[Any]:
        """
        Process items in batches

        Args:
            items: Items to process
            processor: Async function to process each item
            batch_size: Batch size (default from config)

        Returns:
            List of results
        """
        batch_size = batch_size or self.batch_size
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[processor(item) for item in batch]
            )
            results.extend(batch_results)

        return results

    async def rate_limit(
        self, coroutines: List[Coroutine], rate: int = 10, burst: int = 5
    ) -> List[Any]:  # per second
        """
        Execute coroutines with rate limiting

        Args:
            coroutines: Coroutines to execute
            rate: Maximum operations per second
            burst: Burst size

        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(burst)
        last_reset = asyncio.get_event_loop().time()
        tokens = burst

        async def rate_limited_task(coro):
            nonlocal tokens, last_reset

            async with semaphore:
                now = asyncio.get_event_loop().time()
                time_passed = now - last_reset
                tokens = min(burst, tokens + time_passed * rate)
                last_reset = now

                if tokens < 1:
                    sleep_time = (1 - tokens) / rate
                    await asyncio.sleep(sleep_time)
                    tokens = 0
                else:
                    tokens -= 1

                return await coro

        return await asyncio.gather(
            *[rate_limited_task(c) for c in coroutines]
        )

    def shutdown(self):
        """Shutdown thread pool"""
        self._thread_pool.shutdown(wait=True)


class SemaphoreGroup:
    """
    Group of semaphores for different resource types
    """

    def __init__(self):
        self._semaphores: dict = {}

    def get(self, name: str, value: int = 10) -> asyncio.Semaphore:
        """Get or create semaphore"""
        if name not in self._semaphores:
            self._semaphores[name] = asyncio.Semaphore(value)
        return self._semaphores[name]

    async def acquire(self, name: str, timeout: Optional[float] = None):
        """Acquire semaphore with timeout"""
        sem = self.get(name)
        return await asyncio.wait_for(sem.acquire(), timeout=timeout)

    def release(self, name: str):
        """Release semaphore"""
        sem = self._semaphores.get(name)
        if sem:
            sem.release()


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance

    Prevents cascading failures by failing fast when
    a service is experiencing problems.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = "closed"  # closed, open, half-open
        self._failures = 0
        self._successes = 0
        self._last_failure_time = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        """Call function with circuit breaker protection"""
        async with self._lock:
            if self._state == "open":
                if self._should_attempt_reset():
                    self._state = "half-open"
                    self._half_open_calls = 0
                else:
                    raise CircuitBreakerOpen("Circuit breaker is open")

            if self._state == "half-open":
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpen(
                        "Circuit breaker half-open limit reached"
                    )
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery"""
        if self._last_failure_time is None:
            return True
        import time

        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    async def _on_success(self):
        async with self._lock:
            if self._state == "half-open":
                self._successes += 1
                if self._successes >= self.half_open_max_calls:
                    self._state = "closed"
                    self._failures = 0
                    self._successes = 0
                    logger.info("Circuit breaker closed")

    async def _on_failure(self):
        async with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()

            if self._state == "half-open":
                self._state = "open"
                logger.warning("Circuit breaker opened (half-open failure)")
            elif self._failures >= self.failure_threshold:
                self._state = "open"
                logger.warning(
                    f"Circuit breaker opened ({self._failures} failures)"
                )

    def get_state(self) -> str:
        return self._state


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""

    pass


class RetryHandler:
    """
    Retry logic with exponential backoff
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base**attempt),
                        self.max_delay,
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        raise last_exception
