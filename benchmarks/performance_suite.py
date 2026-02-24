"""
Comprehensive Performance Benchmark Suite for Zen-AI-Pentest

Benchmarks:
- Import performance
- Cache operations
- Database queries
- Tool execution
- Agent coordination
- API response times
- Memory usage
"""

import asyncio
import gc
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.performance import (
    get_timer,
)


@dataclass
class BenchmarkMetrics:
    """Metrics collected during a benchmark"""

    name: str
    duration_ms: float
    iterations: int
    ops_per_second: float
    memory_delta_mb: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Complete benchmark result"""

    category: str
    name: str
    metrics: BenchmarkMetrics
    baseline: Optional[float] = None  # For comparison
    status: str = "passed"  # passed, failed, skipped
    error: Optional[str] = None


class PerformanceBenchmarkSuite:
    """
    Comprehensive performance benchmark suite.

    Usage:
        suite = PerformanceBenchmarkSuite()
        results = suite.run_all()
        suite.generate_report(results)
    """

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timer = get_timer()
        self.results: List[BenchmarkResult] = []
        self.baselines: Dict[str, float] = {}

    # ========================================================================
    # Benchmark Runners
    # ========================================================================

    def run_all(self) -> List[BenchmarkResult]:
        """Run all benchmarks"""
        self.results = []
        print("=" * 70)
        print("ZEN-AI-PENTEST PERFORMANCE BENCHMARK SUITE")
        print("=" * 70)

        # Import benchmarks
        print("\n[IMPORT] Running Import Benchmarks...")
        self.results.extend(self._run_import_benchmarks())

        # Cache benchmarks
        print("\n[CACHE] Running Cache Benchmarks...")
        self.results.extend(self._run_cache_benchmarks())

        # Database benchmarks
        print("\n[DATABASE] Running Database Benchmarks...")
        self.results.extend(self._run_database_benchmarks())

        # Tool execution benchmarks
        print("\n[TOOLS] Running Tool Execution Benchmarks...")
        self.results.extend(self._run_tool_benchmarks())

        # Async benchmarks
        print("\n[ASYNC] Running Async/Await Benchmarks...")
        self.results.extend(self._run_async_benchmarks())

        # Memory benchmarks
        print("\n[MEMORY] Running Memory Benchmarks...")
        self.results.extend(self._run_memory_benchmarks())

        return self.results

    def _run_import_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark module imports"""
        results = []

        modules_to_test = [
            ("core.cache", "Cache Module"),
            ("core.database", "Database Module"),
            ("core.orchestrator", "Orchestrator Module"),
            ("api.main", "API Main Module"),
            ("agents.react_agent", "ReAct Agent"),
        ]

        for module_name, display_name in modules_to_test:
            try:
                # Clear module from cache if already imported
                if module_name in sys.modules:
                    del sys.modules[module_name]
                gc.collect()

                start = time.perf_counter()
                __import__(module_name)
                duration = (time.perf_counter() - start) * 1000

                metrics = BenchmarkMetrics(
                    name=f"import_{module_name.replace('.', '_')}",
                    duration_ms=duration,
                    iterations=1,
                    ops_per_second=(
                        1000 / duration if duration > 0 else float("inf")
                    ),
                    memory_delta_mb=0,
                )

                results.append(
                    BenchmarkResult(
                        category="Import",
                        name=display_name,
                        metrics=metrics,
                        baseline=self.baselines.get(f"import_{module_name}"),
                    )
                )
                print(f"  [OK] {display_name}: {duration:.2f}ms")

            except Exception as e:
                print(f"  [FAIL] {display_name}: {e}")
                results.append(
                    BenchmarkResult(
                        category="Import",
                        name=display_name,
                        metrics=None,
                        status="failed",
                        error=str(e),
                    )
                )

        return results

    def _run_cache_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark cache operations"""
        results = []

        try:
            from core.cache import MemoryCache

            cache = MemoryCache(max_size=1000)

            # Benchmark cache writes
            async def benchmark_writes():
                start = time.perf_counter()
                for i in range(1000):
                    await cache.set(f"key_{i}", {"data": i}, ttl=3600)
                return (time.perf_counter() - start) * 1000

            duration = asyncio.run(benchmark_writes())
            metrics = BenchmarkMetrics(
                name="cache_writes",
                duration_ms=duration,
                iterations=1000,
                ops_per_second=1000 * 1000 / duration,
                memory_delta_mb=0,
            )
            results.append(
                BenchmarkResult(
                    category="Cache", name="1000 Cache Writes", metrics=metrics
                )
            )
            print(
                f"  [OK] 1000 Cache Writes: {duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
            )

            # Benchmark cache reads
            async def benchmark_reads():
                start = time.perf_counter()
                for i in range(1000):
                    await cache.get(f"key_{i}")
                return (time.perf_counter() - start) * 1000

            duration = asyncio.run(benchmark_reads())
            metrics = BenchmarkMetrics(
                name="cache_reads",
                duration_ms=duration,
                iterations=1000,
                ops_per_second=1000 * 1000 / duration,
                memory_delta_mb=0,
            )
            results.append(
                BenchmarkResult(
                    category="Cache", name="1000 Cache Reads", metrics=metrics
                )
            )
            print(
                f"  [OK] 1000 Cache Reads: {duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
            )

        except Exception as e:
            print(f"  [FAIL] Cache benchmarks failed: {e}")

        return results

    def _run_database_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark database operations"""
        results = []

        try:
            from database.models import (
                SessionLocal,
                create_scan,
                get_scan,
                get_scans,
            )

            db = SessionLocal()

            try:
                # Benchmark create operations
                start = time.perf_counter()
                scan_ids = []
                for i in range(100):
                    scan = create_scan(
                        db,
                        name=f"Benchmark Scan {i}",
                        target=f"192.168.1.{i}",
                        scan_type="benchmark",
                        config={},
                        user_id=1,
                    )
                    scan_ids.append(scan.id)
                db.commit()
                create_duration = (time.perf_counter() - start) * 1000

                metrics = BenchmarkMetrics(
                    name="db_create_100",
                    duration_ms=create_duration,
                    iterations=100,
                    ops_per_second=100 * 1000 / create_duration,
                    memory_delta_mb=0,
                )
                results.append(
                    BenchmarkResult(
                        category="Database",
                        name="100 DB Inserts",
                        metrics=metrics,
                    )
                )
                print(
                    f"  [OK] 100 DB Inserts: {create_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
                )

                # Benchmark read operations
                start = time.perf_counter()
                for scan_id in scan_ids[:50]:
                    get_scan(db, scan_id)
                read_duration = (time.perf_counter() - start) * 1000

                metrics = BenchmarkMetrics(
                    name="db_reads_50",
                    duration_ms=read_duration,
                    iterations=50,
                    ops_per_second=50 * 1000 / read_duration,
                    memory_delta_mb=0,
                )
                results.append(
                    BenchmarkResult(
                        category="Database",
                        name="50 DB Reads",
                        metrics=metrics,
                    )
                )
                print(
                    f"  [OK] 50 DB Reads: {read_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
                )

                # Benchmark list query
                start = time.perf_counter()
                scans = get_scans(db, limit=100)
                list_duration = (time.perf_counter() - start) * 1000

                metrics = BenchmarkMetrics(
                    name="db_list_100",
                    duration_ms=list_duration,
                    iterations=1,
                    ops_per_second=1000 / list_duration,
                    memory_delta_mb=0,
                    metadata={"scans_returned": len(scans)},
                )
                results.append(
                    BenchmarkResult(
                        category="Database",
                        name="DB List Query (100)",
                        metrics=metrics,
                    )
                )
                print(f"  [OK] DB List Query: {list_duration:.2f}ms")

                # Cleanup
                from database.models import Scan

                for scan_id in scan_ids:
                    db.query(Scan).filter(Scan.id == scan_id).delete()
                db.commit()

            finally:
                db.close()

        except Exception as e:
            print(f"  [FAIL] Database benchmarks failed: {e}")

        return results

    def _run_tool_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark tool execution"""
        results = []

        # Simulate tool execution timing
        async def mock_tool_execution(duration: float):
            await asyncio.sleep(duration)
            return {"status": "completed"}

        async def run_tool_benchmarks():
            # Sequential execution
            start = time.perf_counter()
            for _ in range(10):
                await mock_tool_execution(0.01)
            seq_duration = (time.perf_counter() - start) * 1000

            metrics = BenchmarkMetrics(
                name="tool_sequential",
                duration_ms=seq_duration,
                iterations=10,
                ops_per_second=10 * 1000 / seq_duration,
                memory_delta_mb=0,
            )
            results.append(
                BenchmarkResult(
                    category="Tool Execution",
                    name="10 Sequential Tools",
                    metrics=metrics,
                )
            )
            print(
                f"  [OK] 10 Sequential Tools: {seq_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
            )

            # Parallel execution with gather
            start = time.perf_counter()
            await asyncio.gather(
                *[mock_tool_execution(0.01) for _ in range(10)]
            )
            par_duration = (time.perf_counter() - start) * 1000

            metrics = BenchmarkMetrics(
                name="tool_parallel",
                duration_ms=par_duration,
                iterations=10,
                ops_per_second=10 * 1000 / par_duration,
                memory_delta_mb=0,
                metadata={"speedup": seq_duration / par_duration},
            )
            results.append(
                BenchmarkResult(
                    category="Tool Execution",
                    name="10 Parallel Tools",
                    metrics=metrics,
                )
            )
            print(
                f"  [OK] 10 Parallel Tools: {par_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s, {seq_duration/par_duration:.1f}x speedup)"
            )

        asyncio.run(run_tool_benchmarks())
        return results

    def _run_async_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark async operations"""
        results = []

        async def run_async_benchmarks():
            # Benchmark asyncio.gather vs sequential
            async def async_task(n: int):
                await asyncio.sleep(0.001)
                return n * n

            # Sequential
            start = time.perf_counter()
            for i in range(100):
                await async_task(i)
            seq_duration = (time.perf_counter() - start) * 1000

            metrics = BenchmarkMetrics(
                name="async_sequential",
                duration_ms=seq_duration,
                iterations=100,
                ops_per_second=100 * 1000 / seq_duration,
                memory_delta_mb=0,
            )
            results.append(
                BenchmarkResult(
                    category="Async/Await",
                    name="100 Sequential Async Tasks",
                    metrics=metrics,
                )
            )
            print(
                f"  [OK] 100 Sequential Async: {seq_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
            )

            # Parallel with gather
            start = time.perf_counter()
            await asyncio.gather(*[async_task(i) for i in range(100)])
            par_duration = (time.perf_counter() - start) * 1000

            metrics = BenchmarkMetrics(
                name="async_parallel",
                duration_ms=par_duration,
                iterations=100,
                ops_per_second=100 * 1000 / par_duration,
                memory_delta_mb=0,
                metadata={"speedup": seq_duration / par_duration},
            )
            results.append(
                BenchmarkResult(
                    category="Async/Await",
                    name="100 Parallel Async Tasks",
                    metrics=metrics,
                )
            )
            print(
                f"  [OK] 100 Parallel Async: {par_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s, {seq_duration/par_duration:.1f}x speedup)"
            )

            # Benchmark semaphore-limited concurrency
            from core.performance import gather_with_concurrency

            start = time.perf_counter()
            await gather_with_concurrency(
                10, *[async_task(i) for i in range(100)]
            )
            sem_duration = (time.perf_counter() - start) * 1000

            metrics = BenchmarkMetrics(
                name="async_limited_concurrency",
                duration_ms=sem_duration,
                iterations=100,
                ops_per_second=100 * 1000 / sem_duration,
                memory_delta_mb=0,
            )
            results.append(
                BenchmarkResult(
                    category="Async/Await",
                    name="100 Tasks (10 concurrent)",
                    metrics=metrics,
                )
            )
            print(
                f"  [OK] 100 Tasks (10 concurrent): {sem_duration:.2f}ms ({metrics.ops_per_second:.0f} ops/s)"
            )

        asyncio.run(run_async_benchmarks())
        return results

    def _run_memory_benchmarks(self) -> List[BenchmarkResult]:
        """Benchmark memory usage"""
        results = []

        # Benchmark memory cache overhead
        try:
            from core.cache import MemoryCache

            gc.collect()
            start_mem = self._get_memory_mb()

            cache = MemoryCache(max_size=10000)

            async def populate_cache():
                for i in range(10000):
                    await cache.set(
                        f"key_{i}", {"data": i, "nested": {"value": i * 2}}
                    )

            asyncio.run(populate_cache())

            end_mem = self._get_memory_mb()
            delta = end_mem - start_mem

            metrics = BenchmarkMetrics(
                name="memory_cache_10k",
                duration_ms=0,
                iterations=10000,
                ops_per_second=0,
                memory_delta_mb=delta,
                metadata={"per_entry_kb": delta * 1024 / 10000},
            )
            results.append(
                BenchmarkResult(
                    category="Memory",
                    name="Cache Memory (10k entries)",
                    metrics=metrics,
                )
            )
            print(
                f"  [OK] Cache Memory: {delta:.2f}MB total, {delta * 1024 / 10000:.2f}KB/entry"
            )

        except Exception as e:
            print(f"  [FAIL] Memory benchmarks failed: {e}")

        return results

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    # ========================================================================
    # Report Generation
    # ========================================================================

    def generate_report(
        self, results: Optional[List[BenchmarkResult]] = None
    ) -> str:
        """Generate a comprehensive benchmark report"""
        results = results or self.results

        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE BENCHMARK REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Benchmarks: {len(results)}")
        lines.append("")

        # Group by category
        by_category: Dict[str, List[BenchmarkResult]] = {}
        for result in results:
            by_category.setdefault(result.category, []).append(result)

        # Print each category
        for category, cat_results in sorted(by_category.items()):
            lines.append(f"\n{'-' * 70}")
            lines.append(f"[{category.upper()}]")
            lines.append("-" * 70)

            for result in cat_results:
                if result.status == "failed":
                    lines.append(f"\n  [FAIL] {result.name}")
                    lines.append(f"    Error: {result.error}")
                    continue

                if result.metrics:
                    m = result.metrics
                    lines.append(f"\n  [OK] {result.name}")
                    lines.append(f"    Duration: {m.duration_ms:.2f}ms")
                    lines.append(
                        f"    Throughput: {m.ops_per_second:.0f} ops/s"
                    )
                    if m.memory_delta_mb > 0:
                        lines.append(f"    Memory: +{m.memory_delta_mb:.2f}MB")
                    if result.baseline:
                        change = (
                            (m.duration_ms - result.baseline) / result.baseline
                        ) * 100
                        lines.append(
                            f"    Change from baseline: {change:+.1f}%"
                        )

        # Summary statistics
        lines.append(f"\n{'=' * 70}")
        lines.append("SUMMARY")
        lines.append("=" * 70)

        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")

        report = "\n".join(lines)

        # Save to file
        report_file = (
            self.output_dir / f"performance_report_{int(time.time())}.txt"
        )
        report_file.write_text(report, encoding="utf-8")
        print(f"\n[REPORT] Report saved to: {report_file}")

        return report

    def save_json_results(
        self, results: Optional[List[BenchmarkResult]] = None
    ):
        """Save results as JSON for further analysis"""
        import json

        results = results or self.results

        data = []
        for result in results:
            data.append(
                {
                    "category": result.category,
                    "name": result.name,
                    "status": result.status,
                    "metrics": (
                        {
                            "duration_ms": result.metrics.duration_ms,
                            "iterations": result.metrics.iterations,
                            "ops_per_second": result.metrics.ops_per_second,
                            "memory_delta_mb": result.metrics.memory_delta_mb,
                            **result.metrics.metadata,
                        }
                        if result.metrics
                        else None
                    ),
                    "error": result.error,
                }
            )

        json_file = (
            self.output_dir / f"performance_results_{int(time.time())}.json"
        )
        json_file.write_text(json.dumps(data, indent=2))
        print(f"[JSON] JSON results saved to: {json_file}")


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Run the performance benchmark suite"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Zen-AI-Pentest Performance Benchmarks"
    )
    parser.add_argument(
        "--output",
        default="benchmark_results",
        help="Output directory for results",
    )
    parser.add_argument("--category", help="Run only specific category")
    parser.add_argument(
        "--compare",
        help="Compare against baseline file (JSON)",
    )

    args = parser.parse_args()

    suite = PerformanceBenchmarkSuite(output_dir=args.output)

    # Load baselines if provided
    if args.compare:
        import json

        baseline_data = json.loads(Path(args.compare).read_text())
        for item in baseline_data:
            if item.get("metrics"):
                suite.baselines[item["name"]] = item["metrics"]["duration_ms"]

    # Run benchmarks
    results = suite.run_all()

    # Generate reports
    suite.generate_report(results)
    suite.save_json_results(results)

    # Exit with error code if any benchmarks failed
    failed = sum(1 for r in results if r.status == "failed")
    if failed > 0:
        print(f"\n[WARN] {failed} benchmark(s) failed")
        sys.exit(1)

    print("\n[DONE] All benchmarks completed successfully")


if __name__ == "__main__":
    main()
