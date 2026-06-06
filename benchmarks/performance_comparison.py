"""
Performance Comparison Benchmark Suite
Compares original vs optimized implementations

Run with: python -m benchmarks.performance_comparison
"""

import asyncio
import gc
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Benchmark result with comparison"""

    name: str
    original_time_ms: float
    optimized_time_ms: float
    speedup: float
    improvement_pct: float
    original_memory_mb: float = 0
    optimized_memory_mb: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "original_time_ms": round(self.original_time_ms, 2),
            "optimized_time_ms": round(self.optimized_time_ms, 2),
            "speedup": round(self.speedup, 2),
            "improvement_pct": round(self.improvement_pct, 2),
            "original_memory_mb": round(self.original_memory_mb, 2),
            "optimized_memory_mb": round(self.optimized_memory_mb, 2),
        }


class PerformanceComparisonSuite:
    """
    Benchmark suite comparing original vs optimized implementations
    """

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.iterations = 1000

    def run_all(self) -> List[BenchmarkResult]:
        """Run all benchmark comparisons"""
        print("=" * 80)
        print("PERFORMANCE OPTIMIZATION COMPARISON")
        print("=" * 80)

        # Cache benchmarks
        print("\n[1] CACHE BENCHMARKS")
        print("-" * 80)
        self.results.append(self._benchmark_cache_writes())
        self.results.append(self._benchmark_cache_reads())
        self.results.append(self._benchmark_cache_mget())
        self.results.append(self._benchmark_cache_mset())
        self.results.append(self._benchmark_cache_contention())

        # Tool executor benchmarks
        print("\n[2] TOOL EXECUTOR BENCHMARKS")
        print("-" * 80)
        self.results.append(self._benchmark_executor_concurrency())

        # Async benchmarks
        print("\n[3] ASYNC OPERATION BENCHMARKS")
        print("-" * 80)
        self.results.append(self._benchmark_parallel_tasks())
        self.results.append(self._benchmark_semaphore_control())

        return self.results

    def _benchmark_cache_writes(self) -> BenchmarkResult:
        """Benchmark cache write operations"""
        print("\nCache Writes (1000 ops):")

        # Original implementation
        from core.cache import MemoryCache as OriginalCache

        gc.collect()
        original_cache = OriginalCache(max_size=10000)

        async def original_writes():
            for i in range(self.iterations):
                await original_cache.set(f"key_{i}", {"data": i, "value": i * 2}, ttl=3600)

        start = time.perf_counter()
        asyncio.run(original_writes())
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Original: {original_time:.2f}ms ({self.iterations * 1000 / original_time:.0f} ops/s)")

        # Optimized implementation
        from core.cache_optimized import MemoryCache as OptimizedCache

        gc.collect()
        optimized_cache = OptimizedCache(max_size=10000, enable_compression=True)

        async def optimized_writes():
            for i in range(self.iterations):
                await optimized_cache.set(f"key_{i}", {"data": i, "value": i * 2}, ttl=3600)

        start = time.perf_counter()
        asyncio.run(optimized_writes())
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  Optimized: {optimized_time:.2f}ms ({self.iterations * 1000 / optimized_time:.0f} ops/s)")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Cache Writes (1000 ops)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_cache_reads(self) -> BenchmarkResult:
        """Benchmark cache read operations"""
        print("\nCache Reads (1000 ops):")

        # Original implementation
        from core.cache import MemoryCache as OriginalCache

        gc.collect()
        original_cache = OriginalCache(max_size=10000)

        async def setup_original():
            for i in range(self.iterations):
                await original_cache.set(f"key_{i}", {"data": i, "value": i * 2}, ttl=3600)

        asyncio.run(setup_original())

        async def original_reads():
            for i in range(self.iterations):
                await original_cache.get(f"key_{i}")

        start = time.perf_counter()
        asyncio.run(original_reads())
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Original: {original_time:.2f}ms ({self.iterations * 1000 / original_time:.0f} ops/s)")

        # Optimized implementation
        from core.cache_optimized import MemoryCache as OptimizedCache

        gc.collect()
        optimized_cache = OptimizedCache(max_size=10000, enable_compression=True)

        async def setup_optimized():
            for i in range(self.iterations):
                await optimized_cache.set(f"key_{i}", {"data": i, "value": i * 2}, ttl=3600)

        asyncio.run(setup_optimized())

        async def optimized_reads():
            for i in range(self.iterations):
                await optimized_cache.get(f"key_{i}")

        start = time.perf_counter()
        asyncio.run(optimized_reads())
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  Optimized: {optimized_time:.2f}ms ({self.iterations * 1000 / optimized_time:.0f} ops/s)")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Cache Reads (1000 ops)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_cache_mget(self) -> BenchmarkResult:
        """Benchmark batch cache get operations"""
        print("\nCache Batch Get (100 keys):")

        keys = [f"key_{i}" for i in range(100)]

        # Original implementation
        from core.cache import MemoryCache as OriginalCache

        gc.collect()
        original_cache = OriginalCache(max_size=10000)

        async def setup_original():
            for i in range(100):
                await original_cache.set(f"key_{i}", {"data": i}, ttl=3600)

        asyncio.run(setup_original())

        start = time.perf_counter()
        asyncio.run(original_cache.mget(keys))
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Original: {original_time:.2f}ms ({100 * 1000 / original_time:.0f} ops/s)")

        # Optimized implementation
        from core.cache_optimized import MemoryCache as OptimizedCache

        gc.collect()
        optimized_cache = OptimizedCache(max_size=10000)

        async def setup_optimized():
            for i in range(100):
                await optimized_cache.set(f"key_{i}", {"data": i}, ttl=3600)

        asyncio.run(setup_optimized())

        start = time.perf_counter()
        asyncio.run(optimized_cache.mget(keys))
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  Optimized: {optimized_time:.2f}ms ({100 * 1000 / optimized_time:.0f} ops/s)")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Cache Batch Get (100 keys)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_cache_mset(self) -> BenchmarkResult:
        """Benchmark batch cache set operations"""
        print("\nCache Batch Set (100 keys):")

        items = {f"key_{i}": {"data": i, "value": i * 2} for i in range(100)}

        # Original implementation
        from core.cache import MemoryCache as OriginalCache

        gc.collect()
        original_cache = OriginalCache(max_size=10000)

        start = time.perf_counter()
        asyncio.run(original_cache.mset(items, ttl=3600))
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Original: {original_time:.2f}ms ({100 * 1000 / original_time:.0f} ops/s)")

        # Optimized implementation
        from core.cache_optimized import MemoryCache as OptimizedCache

        gc.collect()
        optimized_cache = OptimizedCache(max_size=10000)

        start = time.perf_counter()
        asyncio.run(optimized_cache.mset(items, ttl=3600))
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  Optimized: {optimized_time:.2f}ms ({100 * 1000 / optimized_time:.0f} ops/s)")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Cache Batch Set (100 keys)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_cache_contention(self) -> BenchmarkResult:
        """Benchmark cache under high contention"""
        print("\nCache Contention (100 concurrent ops):")

        # Original implementation
        from core.cache import MemoryCache as OriginalCache

        gc.collect()
        original_cache = OriginalCache(max_size=1000)

        async def original_contention():
            async def worker(worker_id: int):
                for i in range(10):
                    await original_cache.set(f"worker_{worker_id}_key_{i}", {"data": i}, ttl=3600)
                    await original_cache.get(f"worker_{worker_id}_key_{i}")

            await asyncio.gather(*[worker(i) for i in range(10)])

        start = time.perf_counter()
        asyncio.run(original_contention())
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Original: {original_time:.2f}ms")

        # Optimized implementation with sharded locks
        from core.cache_optimized import MemoryCache as OptimizedCache

        gc.collect()
        optimized_cache = OptimizedCache(max_size=1000, num_lock_shards=16)

        async def optimized_contention():
            async def worker(worker_id: int):
                for i in range(10):
                    await optimized_cache.set(f"worker_{worker_id}_key_{i}", {"data": i}, ttl=3600)
                    await optimized_cache.get(f"worker_{worker_id}_key_{i}")

            await asyncio.gather(*[worker(i) for i in range(10)])

        start = time.perf_counter()
        asyncio.run(optimized_contention())
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  Optimized: {optimized_time:.2f}ms")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Cache Contention (100 concurrent ops)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_executor_concurrency(self) -> BenchmarkResult:
        """Benchmark tool executor concurrency control"""
        print("\nExecutor Concurrency (10 concurrent tasks):")

        # Test: Original implementation without semaphore control
        async def original_exec():
            async def task(i: int):
                await asyncio.sleep(0.01)  # 10ms simulated work
                return i

            await asyncio.gather(*[task(i) for i in range(10)])

        start = time.perf_counter()
        asyncio.run(original_exec())
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Without Semaphore: {original_time:.2f}ms")

        # Optimized implementation with semaphore control
        semaphore = asyncio.Semaphore(5)

        async def optimized_exec():
            async def task(i: int):
                async with semaphore:
                    await asyncio.sleep(0.01)
                    return i

            await asyncio.gather(*[task(i) for i in range(10)])

        start = time.perf_counter()
        asyncio.run(optimized_exec())
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  With Semaphore (5): {optimized_time:.2f}ms")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Executor Concurrency (10 tasks)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_parallel_tasks(self) -> BenchmarkResult:
        """Benchmark parallel async task execution"""
        print("\nParallel Tasks (100 tasks with gather):")

        async def async_task(n: int) -> int:
            await asyncio.sleep(0.001)  # 1ms simulated work
            return n * n

        async def original_parallel():
            # Sequential execution (baseline)
            for i in range(100):
                await async_task(i)

        start = time.perf_counter()
        asyncio.run(original_parallel())
        original_time = (time.perf_counter() - start) * 1000
        print(f"  Sequential: {original_time:.2f}ms")

        async def optimized_parallel():
            # True parallel execution
            await asyncio.gather(*[async_task(i) for i in range(100)])

        start = time.perf_counter()
        asyncio.run(optimized_parallel())
        optimized_time = (time.perf_counter() - start) * 1000
        print(f"  Parallel: {optimized_time:.2f}ms")

        speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        improvement = ((original_time - optimized_time) / original_time * 100) if original_time > 0 else 0
        print(f"  Speedup: {speedup:.2f}x ({improvement:+.1f}%)")

        return BenchmarkResult(
            name="Parallel Tasks (100 tasks)",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            speedup=speedup,
            improvement_pct=improvement,
        )

    def _benchmark_semaphore_control(self) -> BenchmarkResult:
        """Benchmark semaphore-based concurrency control"""
        print("\nSemaphore Control (50 tasks, max 10 concurrent):")

        async def async_task(n: int) -> int:
            await asyncio.sleep(0.001)
            return n * n

        # Without semaphore (unlimited concurrency)
        async def unlimited():
            await asyncio.gather(*[async_task(i) for i in range(50)])

        start = time.perf_counter()
        asyncio.run(unlimited())
        unlimited_time = (time.perf_counter() - start) * 1000
        print(f"  Unlimited: {unlimited_time:.2f}ms")

        # With semaphore (limited concurrency)
        semaphore = asyncio.Semaphore(10)

        async def limited_task(n: int) -> int:
            async with semaphore:
                return await async_task(n)

        async def limited():
            await asyncio.gather(*[limited_task(i) for i in range(50)])

        start = time.perf_counter()
        asyncio.run(limited())
        limited_time = (time.perf_counter() - start) * 1000
        print(f"  Limited (10): {limited_time:.2f}ms")

        # The semaphore adds overhead but provides resource protection
        overhead = ((limited_time - unlimited_time) / unlimited_time * 100) if unlimited_time > 0 else 0
        print(f"  Overhead: {overhead:.1f}% (provides resource protection)")

        return BenchmarkResult(
            name="Semaphore Control (50 tasks, 10 max)",
            original_time_ms=unlimited_time,
            optimized_time_ms=limited_time,
            speedup=unlimited_time / limited_time if limited_time > 0 else 1.0,
            improvement_pct=-overhead,  # Negative because it's overhead
        )

    def generate_report(self) -> str:
        """Generate comprehensive benchmark report"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("PERFORMANCE OPTIMIZATION SUMMARY")
        lines.append("=" * 80)
        lines.append("")

        total_speedup = 0
        improvements = []

        for result in self.results:
            lines.append(f"\n{result.name}:")
            lines.append(f"  Original:   {result.original_time_ms:.2f}ms")
            lines.append(f"  Optimized:  {result.optimized_time_ms:.2f}ms")
            lines.append(f"  Speedup:    {result.speedup:.2f}x")
            lines.append(f"  Improvement: {result.improvement_pct:+.1f}%")

            total_speedup += result.speedup
            improvements.append(result.improvement_pct)

        avg_speedup = total_speedup / len(self.results) if self.results else 1.0
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

        lines.append("\n" + "=" * 80)
        lines.append("OVERALL RESULTS")
        lines.append("=" * 80)
        lines.append(f"Average Speedup: {avg_speedup:.2f}x")
        lines.append(f"Average Improvement: {avg_improvement:+.1f}%")
        lines.append(f"Benchmarks Run: {len(self.results)}")

        # Performance grade
        if avg_speedup >= 2.0:
            grade = "EXCELLENT"
        elif avg_speedup >= 1.5:
            grade = "VERY GOOD"
        elif avg_speedup >= 1.2:
            grade = "GOOD"
        elif avg_speedup >= 1.0:
            grade = "ACCEPTABLE"
        else:
            grade = "NEEDS WORK"

        lines.append(f"Performance Grade: {grade}")
        lines.append("")

        report = "\n".join(lines)
        print(report)

        # Save report
        report_file = Path("benchmark_results/performance_comparison_report.txt")
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(report, encoding="utf-8")
        print(f"\nReport saved to: {report_file}")

        return report


def main():
    """Run performance comparison"""
    suite = PerformanceComparisonSuite()
    suite.run_all()
    suite.generate_report()


if __name__ == "__main__":
    main()
