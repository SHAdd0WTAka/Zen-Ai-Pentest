"""
Async Tool Executor - Parallel Tool Execution with Semaphore Control

Features:
- Parallel tool execution with configurable concurrency limits
- Thread pool for CPU-bound operations
- Asyncio for I/O-bound operations
- Resource usage monitoring
- Error handling and retry logic
"""

import asyncio
import atexit
import logging
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar

from core.performance_monitor import PerformanceMonitor, get_monitor

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Registry to track all executor instances for cleanup
_executor_registry: Set[weakref.ref] = set()


def _cleanup_all_executors():
    """Cleanup all remaining executors at program exit"""
    for ref in list(_executor_registry):
        executor = ref()
        if executor is not None:
            try:
                if hasattr(executor, "_thread_pool") and executor._thread_pool:
                    executor._thread_pool.shutdown(wait=False)
            except Exception:
                pass
    _executor_registry.clear()


# Register cleanup at program exit
atexit.register(_cleanup_all_executors)


@dataclass
class ToolResult:
    """Result of a tool execution"""

    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionConfig:
    """Configuration for async execution"""

    max_concurrent: int = 5
    thread_pool_workers: int = 10
    timeout_seconds: float = 300.0
    retry_count: int = 0
    retry_delay_seconds: float = 1.0
    continue_on_error: bool = True


class AsyncToolExecutor:
    """
    Execute tools in parallel with resource management.

    Features:
    - Semaphore-controlled concurrency
    - Thread pool for sync tools
    - Async-native tool support
    - Performance monitoring
    - Configurable timeouts
    """

    def __init__(
        self,
        config: Optional[ExecutionConfig] = None,
        monitor: Optional[PerformanceMonitor] = None,
    ):
        self.config = config or ExecutionConfig()
        self.monitor = monitor or get_monitor()

        # Concurrency control
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.config.thread_pool_workers,
            thread_name_prefix="tool_exec_",
        )

        # Statistics
        self._executed_count = 0
        self._failed_count = 0
        self._total_duration_ms = 0.0

        # Track this instance for cleanup
        self._closed = False
        _executor_registry.add(weakref.ref(self))

    async def execute_parallel(
        self,
        tools: List[Callable[..., T]],
        target: str,
        *args,
        **kwargs,
    ) -> List[ToolResult]:
        """
        Execute multiple tools in parallel.

        Args:
            tools: List of tool functions to execute
            target: Target to scan
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            List of ToolResult objects
        """
        tasks = [self._execute_with_limit(tool, target, *args, **kwargs) for tool in tools]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            tool_name = getattr(tools[i], "__name__", str(tools[i]))
            if isinstance(result, Exception):
                processed_results.append(
                    ToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def execute_batch(
        self,
        tool: Callable[..., T],
        targets: List[str],
        *args,
        **kwargs,
    ) -> List[ToolResult]:
        """
        Execute a single tool against multiple targets in parallel.

        Args:
            tool: Tool function to execute
            targets: List of targets
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            List of ToolResult objects
        """
        tasks = [self._execute_with_limit(tool, target, *args, **kwargs) for target in targets]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ToolResult(
                        tool_name=getattr(tool, "__name__", str(tool)),
                        success=False,
                        error=str(result),
                        metadata={"target": targets[i]},
                    )
                )
            else:
                result.metadata["target"] = targets[i]
                processed_results.append(result)

        return processed_results

    async def _execute_with_limit(
        self,
        tool: Callable[..., T],
        target: str,
        *args,
        **kwargs,
    ) -> ToolResult:
        """Execute tool with semaphore limit and monitoring"""
        tool_name = getattr(tool, "__name__", str(tool))

        async with self._semaphore:
            start_time = time.perf_counter()

            try:
                # Check if tool is async
                if asyncio.iscoroutinefunction(tool):
                    result = await asyncio.wait_for(
                        tool(target, *args, **kwargs),
                        timeout=self.config.timeout_seconds,
                    )
                else:
                    # Run sync tool in thread pool
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(
                            self._thread_pool,
                            lambda: tool(target, *args, **kwargs),
                        ),
                        timeout=self.config.timeout_seconds,
                    )

                duration_ms = (time.perf_counter() - start_time) * 1000
                self._executed_count += 1
                self._total_duration_ms += duration_ms

                # Record metric
                self.monitor._record_metric(
                    type(
                        "Metric",
                        (),
                        {
                            "name": f"tool.{tool_name}",
                            "duration_ms": duration_ms,
                            "timestamp": datetime.now(timezone.utc),
                            "memory_delta_mb": 0.0,
                            "metadata": {"target": target},
                        },
                    )()
                )

                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    result=result,
                    duration_ms=duration_ms,
                    metadata={"target": target},
                )

            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._failed_count += 1
                error_msg = f"Timeout after {self.config.timeout_seconds}s"
                logger.error(f"Tool {tool_name} timed out: {error_msg}")

                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=error_msg,
                    duration_ms=duration_ms,
                    metadata={"target": target, "timeout": True},
                )

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._failed_count += 1
                logger.error(f"Tool {tool_name} failed: {e}")

                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=str(e),
                    duration_ms=duration_ms,
                    metadata={"target": target},
                )

    async def execute_with_retry(
        self,
        tool: Callable[..., T],
        target: str,
        *args,
        **kwargs,
    ) -> ToolResult:
        """Execute tool with retry logic"""
        tool_name = getattr(tool, "__name__", str(tool))
        last_error = None

        for attempt in range(self.config.retry_count + 1):
            result = await self._execute_with_limit(tool, target, *args, **kwargs)

            if result.success:
                if attempt > 0:
                    result.metadata["retry_attempts"] = attempt
                return result

            last_error = result.error

            if attempt < self.config.retry_count:
                delay = self.config.retry_delay_seconds * (2**attempt)  # Exponential backoff
                logger.warning(f"Retrying {tool_name} in {delay}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)

        # All retries failed
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=f"Failed after {self.config.retry_count + 1} attempts: {last_error}",
            metadata={"target": target, "retries_exhausted": True},
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        avg_duration = self._total_duration_ms / self._executed_count if self._executed_count > 0 else 0.0

        return {
            "executed": self._executed_count,
            "failed": self._failed_count,
            "success_rate": (
                (self._executed_count - self._failed_count) / self._executed_count * 100 if self._executed_count > 0 else 0.0
            ),
            "total_duration_ms": self._total_duration_ms,
            "avg_duration_ms": avg_duration,
            "config": {
                "max_concurrent": self.config.max_concurrent,
                "thread_pool_workers": self.config.thread_pool_workers,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }

    async def close(self):
        """Clean up resources"""
        if self._closed:
            return
        self._closed = True

        # Remove from registry
        for ref in list(_executor_registry):
            if ref() is self:
                _executor_registry.discard(ref)
                break

        try:
            self._thread_pool.shutdown(wait=True)
            logger.info("AsyncToolExecutor shut down")
        except Exception as e:
            logger.warning(f"Error during executor shutdown: {e}")

    def __del__(self):
        """Destructor - only cleanup if not already closed"""
        if self._closed:
            return
        try:
            # Don't wait - we might be in interpreter shutdown
            if hasattr(self, "_thread_pool") and self._thread_pool:
                self._thread_pool.shutdown(wait=False)
        except Exception:
            pass


class BatchProcessor:
    """
    Process items in batches for optimal performance.

    Features:
    - Configurable batch sizes
    - Parallel batch processing
    - Progress tracking
    - Error isolation per batch
    """

    def __init__(
        self,
        batch_size: int = 100,
        max_concurrent_batches: int = 3,
        executor: Optional[AsyncToolExecutor] = None,
    ):
        self.batch_size = batch_size
        self.max_concurrent_batches = max_concurrent_batches
        self.executor = executor or AsyncToolExecutor()

    def _split_batches(self, items: List[Any]) -> List[List[Any]]:
        """Split items into batches"""
        return [items[i : i + self.batch_size] for i in range(0, len(items), self.batch_size)]

    async def process(
        self,
        items: List[Any],
        processor: Callable[[List[Any]], List[T]],
        *args,
        **kwargs,
    ) -> List[T]:
        """
        Process items in batches.

        Args:
            items: Items to process
            processor: Function that processes a batch
            *args: Additional arguments for processor
            **kwargs: Additional keyword arguments

        Returns:
            Combined results from all batches
        """
        batches = self._split_batches(items)
        results = []

        # Process batches with limited concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        async def process_batch(batch: List[Any]) -> List[T]:
            async with semaphore:
                try:
                    if asyncio.iscoroutinefunction(processor):
                        return await processor(batch, *args, **kwargs)
                    else:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(
                            None,
                            lambda: processor(batch, *args, **kwargs),
                        )
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    return []

        # Process all batches
        tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        for batch_result in batch_results:
            if isinstance(batch_result, list):
                results.extend(batch_result)
            elif isinstance(batch_result, Exception):
                logger.error(f"Batch failed: {batch_result}")

        return results


# Global executor instance
_global_executor: Optional[AsyncToolExecutor] = None


def get_executor() -> AsyncToolExecutor:
    """Get or create global async executor"""
    global _global_executor
    if _global_executor is None:
        _global_executor = AsyncToolExecutor()
    return _global_executor


def create_executor(
    config: Optional[ExecutionConfig] = None,
) -> AsyncToolExecutor:
    """Create a new executor with custom config"""
    return AsyncToolExecutor(config=config)


__all__ = [
    "AsyncToolExecutor",
    "ExecutionConfig",
    "ToolResult",
    "BatchProcessor",
    "get_executor",
    "create_executor",
]
