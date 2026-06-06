#!/usr/bin/env python3
"""
Parallel Module Executor

Executes independent workflow modules in parallel with
resource management and result aggregation.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("parallel_executor")


@dataclass
class ParallelTask:
    """A task for parallel execution."""

    name: str
    module: Any
    inputs: Dict[str, Any]
    priority: int = 0
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 1


@dataclass
class ParallelResult:
    """Result from parallel execution."""

    task_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0


class ParallelExecutor:
    """
    Executes multiple modules in parallel with resource control.

    Features:
    - Semaphore-based concurrency limiting
    - Priority queue for task ordering
    - Result aggregation
    - Error isolation
    """

    def __init__(self, max_concurrent: int = 3, max_workers: int = 10, default_timeout: int = 300):
        self.max_concurrent = max_concurrent
        self.max_workers = max_workers
        self.default_timeout = default_timeout

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def execute(
        self,
        tasks: List[ParallelTask],
        on_complete: Optional[Callable[[ParallelResult], None]] = None,
        fail_fast: bool = False,
    ) -> Dict[str, ParallelResult]:
        """
        Execute tasks in parallel.

        Args:
            tasks: List of tasks to execute
            on_complete: Callback for each completed task
            fail_fast: Stop on first failure

        Returns:
            Dictionary of results by task name
        """
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        # Create task coroutines
        coros = [self._execute_single(task, on_complete) for task in sorted_tasks]

        if fail_fast:
            # Execute with fail-fast behavior
            results = {}
            pending = list(zip(sorted_tasks, coros))

            while pending:
                # Start next batch up to max_concurrent
                batch = pending[: self.max_concurrent]
                pending = pending[self.max_concurrent :]

                batch_tasks = [t for t, _ in batch]
                batch_coros = [c for _, c in batch]

                # Wait for first completion or exception
                done, _ = await asyncio.wait(
                    [asyncio.create_task(c) for c in batch_coros], return_when=asyncio.FIRST_EXCEPTION
                )

                for task, coro_task in zip(batch_tasks, done):
                    try:
                        result = coro_task.result()
                        results[task.name] = result

                        if not result.success:
                            logger.error(f"Task {task.name} failed, stopping (fail_fast)")
                            # Cancel remaining
                            for p, _ in pending:
                                results[p.name] = ParallelResult(
                                    task_name=p.name, success=False, error="Cancelled due to fail_fast"
                                )
                            return results

                    except Exception as e:
                        logger.error(f"Task {task.name} raised exception: {e}")
                        results[task.name] = ParallelResult(task_name=task.name, success=False, error=str(e))
                        # Cancel remaining
                        for p, _ in pending:
                            results[p.name] = ParallelResult(
                                task_name=p.name, success=False, error="Cancelled due to fail_fast"
                            )
                        return results
        else:
            # Execute all with return_exceptions=True
            completed = await asyncio.gather(*coros, return_exceptions=True)

            results = {}
            for task, result in zip(sorted_tasks, completed):
                if isinstance(result, Exception):
                    results[task.name] = ParallelResult(task_name=task.name, success=False, error=str(result))
                else:
                    results[task.name] = result

        return results

    async def _execute_single(
        self, task: ParallelTask, on_complete: Optional[Callable[[ParallelResult], None]]
    ) -> ParallelResult:
        """Execute a single task with semaphore control."""
        import time

        async with self._semaphore:
            start_time = time.time()

            try:
                logger.debug(f"Executing task: {task.name}")

                # Execute module
                if hasattr(task.module, "run"):
                    coro = task.module.run(**task.inputs)
                    result_data = await asyncio.wait_for(coro, timeout=task.timeout)
                elif asyncio.iscoroutinefunction(task.module):
                    result_data = await asyncio.wait_for(task.module(**task.inputs), timeout=task.timeout)
                elif callable(task.module):
                    # Run in thread pool
                    loop = asyncio.get_event_loop()
                    result_data = await asyncio.wait_for(
                        loop.run_in_executor(self._thread_pool, task.module, **task.inputs), timeout=task.timeout
                    )
                else:
                    raise ValueError(f"Module {task.name} is not callable")

                execution_time = time.time() - start_time

                result = ParallelResult(
                    task_name=task.name,
                    success=True,
                    result=result_data,
                    execution_time=execution_time,
                    retry_count=task.retry_count,
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time

                # Retry if allowed
                if task.retry_count < task.max_retries:
                    logger.warning(f"Task {task.name} timeout, retrying...")
                    task.retry_count += 1
                    return await self._execute_single(task, on_complete)

                result = ParallelResult(
                    task_name=task.name,
                    success=False,
                    error=f"Timeout after {task.timeout}s",
                    execution_time=execution_time,
                    retry_count=task.retry_count,
                )

            except Exception as e:
                execution_time = time.time() - start_time

                # Retry if allowed
                if task.retry_count < task.max_retries:
                    logger.warning(f"Task {task.name} failed: {e}, retrying...")
                    task.retry_count += 1
                    return await self._execute_single(task, on_complete)

                result = ParallelResult(
                    task_name=task.name,
                    success=False,
                    error=str(e),
                    execution_time=execution_time,
                    retry_count=task.retry_count,
                )

            if on_complete:
                try:
                    on_complete(result)
                except Exception as e:
                    logger.error(f"on_complete callback error: {e}")

            return result

    async def execute_with_dependency_groups(
        self,
        groups: List[List[ParallelTask]],
        on_group_complete: Optional[Callable[[int, Dict[str, ParallelResult]], None]] = None,
    ) -> List[Dict[str, ParallelResult]]:
        """
        Execute groups sequentially, tasks within group in parallel.

        Args:
            groups: List of task groups (each group executes in parallel)
            on_group_complete: Callback when group completes

        Returns:
            List of result dictionaries (one per group)
        """
        all_results = []

        for i, group in enumerate(groups):
            logger.info(f"Executing group {i+1}/{len(groups)} ({len(group)} tasks)")

            results = await self.execute(group)
            all_results.append(results)

            if on_group_complete:
                on_group_complete(i, results)

            # Check if we should continue
            success_count = sum(1 for r in results.values() if r.success)
            if success_count == 0 and i < len(groups) - 1:
                logger.warning(f"Group {i+1} had no successes, continuing anyway")

        return all_results

    def shutdown(self):
        """Shutdown thread pool."""
        self._thread_pool.shutdown(wait=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "max_workers": self.max_workers,
            "active_tasks": len(self._running_tasks),
            "thread_pool_workers": self._thread_pool._max_workers,
        }


class BatchExecutor:
    """Execute batches of similar tasks efficiently."""

    def __init__(self, parallel_executor: ParallelExecutor):
        self.executor = parallel_executor

    async def batch_scan(
        self, targets: List[str], scanner_module: Any, batch_size: int = 10, **scanner_kwargs
    ) -> Dict[str, ParallelResult]:
        """
        Scan multiple targets in batches.

        Args:
            targets: List of targets to scan
            scanner_module: Scanner module to use
            batch_size: Number of targets per batch
            **scanner_kwargs: Additional scanner arguments

        Returns:
            Combined results from all batches
        """
        all_results = {}

        for i in range(0, len(targets), batch_size):
            batch = targets[i : i + batch_size]

            tasks = [
                ParallelTask(
                    name=f"scan_{target}", module=scanner_module, inputs={"target": target, **scanner_kwargs}, timeout=600
                )
                for target in batch
            ]

            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} targets)")
            batch_results = await self.executor.execute(tasks)
            all_results.update(batch_results)

        return all_results

    async def batch_test_endpoints(
        self, endpoints: List[Dict], tester_module: Any, **tester_kwargs
    ) -> Dict[str, ParallelResult]:
        """
        Test multiple endpoints in parallel.

        Args:
            endpoints: List of endpoint dictionaries with url, method, etc.
            tester_module: Testing module
            **tester_kwargs: Additional tester arguments

        Returns:
            Results by endpoint identifier
        """
        tasks = [
            ParallelTask(
                name=f"{ep.get('method', 'GET')}_{ep.get('path', ep.get('url', 'unknown'))}",
                module=tester_module,
                inputs={**ep, **tester_kwargs},
                priority=ep.get("priority", 0),
                timeout=ep.get("timeout", 300),
            )
            for ep in endpoints
        ]

        return await self.executor.execute(tasks)


if __name__ == "__main__":
    # Test parallel executor
    async def test():
        # Mock module
        class MockScanner:
            async def run(self, target: str, **kwargs):
                await asyncio.sleep(0.1)
                return {"target": target, "open_ports": [80, 443]}

        executor = ParallelExecutor(max_concurrent=3)

        # Create tasks
        targets = [f"target{i}.com" for i in range(5)]
        tasks = [ParallelTask(name=f"scan_{target}", module=MockScanner(), inputs={"target": target}) for target in targets]

        # Execute
        results = await executor.execute(tasks)

        for name, result in results.items():
            status = "✓" if result.success else "✗"
            print(f"{status} {name}: {result.execution_time:.2f}s")
            if result.success:
                print(f"  Result: {result.result}")
            else:
                print(f"  Error: {result.error}")

        executor.shutdown()

    asyncio.run(test())
