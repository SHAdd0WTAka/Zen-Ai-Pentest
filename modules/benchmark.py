"""
Zen-AI-Pentest Benchmark Framework Module

Core benchmark framework for performance metrics collection, timing measurements,
resource usage tracking, and baseline comparisons.

Author: Zen-AI Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import platform
import statistics
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil

# Configure logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""

    TIMING = "timing"
    MEMORY = "memory"
    CPU = "cpu"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    COUNT = "count"
    PERCENTAGE = "percentage"


class BenchmarkCategory(Enum):
    """Benchmark categories."""

    SCAN = "scan"
    AGENT = "agent"
    API = "api"
    TOOL = "tool"
    OVERALL = "overall"


@dataclass
class MetricValue:
    """Single metric measurement."""

    name: str
    value: float
    unit: str
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class TimingMetrics:
    """Timing-related metrics."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    iterations: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    avg_ms: float = 0.0
    median_ms: float = 0.0
    std_dev_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "duration_seconds": self.duration_seconds,
            "iterations": self.iterations,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "avg_ms": self.avg_ms,
            "median_ms": self.median_ms,
            "std_dev_ms": self.std_dev_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
        }


@dataclass
class MemoryMetrics:
    """Memory usage metrics."""

    initial_mb: float = 0.0
    peak_mb: float = 0.0
    final_mb: float = 0.0
    delta_mb: float = 0.0
    avg_mb: float = 0.0
    samples: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_mb": self.initial_mb,
            "peak_mb": self.peak_mb,
            "final_mb": self.final_mb,
            "delta_mb": self.delta_mb,
            "avg_mb": self.avg_mb,
            "sample_count": len(self.samples),
        }


@dataclass
class CPUMetrics:
    """CPU usage metrics."""

    avg_percent: float = 0.0
    peak_percent: float = 0.0
    samples: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"avg_percent": self.avg_percent, "peak_percent": self.peak_percent, "sample_count": len(self.samples)}


@dataclass
class ThroughputMetrics:
    """Throughput metrics (operations per time unit)."""

    operations: int = 0
    duration_seconds: float = 0.0
    ops_per_second: float = 0.0
    ops_per_minute: float = 0.0

    def calculate(self) -> None:
        """Calculate throughput rates."""
        if self.duration_seconds > 0:
            self.ops_per_second = self.operations / self.duration_seconds
            self.ops_per_minute = self.ops_per_second * 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operations": self.operations,
            "duration_seconds": self.duration_seconds,
            "ops_per_second": self.ops_per_second,
            "ops_per_minute": self.ops_per_minute,
        }


@dataclass
class BenchmarkResult:
    """Complete benchmark result."""

    benchmark_id: str
    name: str
    category: BenchmarkCategory
    description: str

    # Timing
    timing: TimingMetrics = field(default_factory=TimingMetrics)

    # Resources
    memory: MemoryMetrics = field(default_factory=MemoryMetrics)
    cpu: CPUMetrics = field(default_factory=CPUMetrics)

    # Throughput
    throughput: ThroughputMetrics = field(default_factory=ThroughputMetrics)

    # Additional metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    environment: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "timing": self.timing.to_dict(),
            "memory": self.memory.to_dict(),
            "cpu": self.cpu.to_dict(),
            "throughput": self.throughput.to_dict(),
            "custom_metrics": self.custom_metrics,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "environment": self.environment,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class ResourceMonitor:
    """Monitor system resources during benchmark execution."""

    def __init__(self, interval: float = 0.5):
        self.interval = interval
        self.monitoring = False
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
        self._monitor_task: Optional[asyncio.Task] = None
        self._process = psutil.Process()

    async def start(self) -> None:
        """Start resource monitoring."""
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.debug("Resource monitoring started")

    async def stop(self) -> None:
        """Stop resource monitoring."""
        self.monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.debug("Resource monitoring stopped")

    async def _monitor_loop(self) -> None:
        """Monitoring loop."""
        while self.monitoring:
            try:
                # Memory usage in MB
                mem_info = self._process.memory_info()
                memory_mb = mem_info.rss / (1024 * 1024)
                self.memory_samples.append(memory_mb)

                # CPU usage percentage
                cpu_percent = self._process.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)

                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.warning(f"Error in resource monitoring: {e}")
                break

    def get_memory_metrics(self) -> MemoryMetrics:
        """Get memory metrics from samples."""
        if not self.memory_samples:
            return MemoryMetrics()

        return MemoryMetrics(
            initial_mb=self.memory_samples[0] if self.memory_samples else 0,
            peak_mb=max(self.memory_samples) if self.memory_samples else 0,
            final_mb=self.memory_samples[-1] if self.memory_samples else 0,
            delta_mb=(self.memory_samples[-1] - self.memory_samples[0]) if len(self.memory_samples) > 1 else 0,
            avg_mb=statistics.mean(self.memory_samples) if self.memory_samples else 0,
            samples=self.memory_samples.copy(),
        )

    def get_cpu_metrics(self) -> CPUMetrics:
        """Get CPU metrics from samples."""
        if not self.cpu_samples:
            return CPUMetrics()

        return CPUMetrics(
            avg_percent=statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
            peak_percent=max(self.cpu_samples) if self.cpu_samples else 0,
            samples=self.cpu_samples.copy(),
        )


class BenchmarkRunner:
    """Runner for executing benchmarks with full metrics collection."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.baselines: Dict[str, Dict[str, Any]] = {}
        self._load_baselines()

    def _load_baselines(self) -> None:
        """Load baseline metrics from file."""
        baseline_file = self.output_dir / "baselines.json"
        if baseline_file.exists():
            try:
                with open(baseline_file) as f:
                    self.baselines = json.load(f)
                logger.info(f"Loaded {len(self.baselines)} baselines")
            except Exception as e:
                logger.warning(f"Could not load baselines: {e}")

    def _save_baselines(self) -> None:
        """Save baseline metrics to file."""
        baseline_file = self.output_dir / "baselines.json"
        try:
            with open(baseline_file, "w") as f:
                json.dump(self.baselines, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save baselines: {e}")

    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": psutil.virtual_memory().total / (1024**3),
            "timestamp": datetime.utcnow().isoformat(),
        }

    @contextmanager
    def measure(self, name: str, category: BenchmarkCategory, description: str = ""):
        """Context manager for simple timing measurements."""
        start_time = time.perf_counter()
        start_dt = datetime.utcnow()

        result = BenchmarkResult(
            benchmark_id=str(uuid.uuid4())[:8],
            name=name,
            category=category,
            description=description,
            environment=self._get_environment_info(),
        )
        result.timing.start_time = start_dt

        try:
            yield result
        finally:
            end_time = time.perf_counter()
            result.timing.end_time = datetime.utcnow()
            result.timing.duration_ms = (end_time - start_time) * 1000

    async def run_benchmark(
        self,
        name: str,
        category: BenchmarkCategory,
        benchmark_func: Callable,
        description: str = "",
        iterations: int = 1,
        warmup_iterations: int = 0,
        monitor_resources: bool = True,
        **func_kwargs,
    ) -> BenchmarkResult:
        """
        Run a benchmark function with full metrics collection.

        Args:
            name: Benchmark name
            category: Benchmark category
            benchmark_func: Async function to benchmark
            description: Benchmark description
            iterations: Number of iterations to run
            warmup_iterations: Number of warmup iterations (not measured)
            monitor_resources: Whether to monitor resource usage
            **func_kwargs: Arguments to pass to benchmark function

        Returns:
            BenchmarkResult with all metrics
        """
        benchmark_id = str(uuid.uuid4())[:8]

        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            name=name,
            category=category,
            description=description,
            environment=self._get_environment_info(),
        )

        logger.info(f"Starting benchmark: {name} ({benchmark_id})")

        # Warmup iterations
        for i in range(warmup_iterations):
            logger.debug(f"Warmup iteration {i + 1}/{warmup_iterations}")
            await benchmark_func(**func_kwargs)

        # Start resource monitoring
        monitor = ResourceMonitor()
        if monitor_resources:
            await monitor.start()

        # Run benchmark iterations
        iteration_times = []
        result.timing.start_time = datetime.utcnow()

        for i in range(iterations):
            iter_start = time.perf_counter()

            try:
                await benchmark_func(**func_kwargs)
            except Exception as e:
                logger.error(f"Benchmark iteration {i + 1} failed: {e}")
                raise

            iter_end = time.perf_counter()
            iter_time_ms = (iter_end - iter_start) * 1000
            iteration_times.append(iter_time_ms)

        result.timing.end_time = datetime.utcnow()

        # Stop resource monitoring
        if monitor_resources:
            await monitor.stop()
            result.memory = monitor.get_memory_metrics()
            result.cpu = monitor.get_cpu_metrics()

        # Calculate timing metrics
        result.timing.iterations = iterations
        result.timing.duration_ms = sum(iteration_times)

        if iteration_times:
            result.timing.min_ms = min(iteration_times)
            result.timing.max_ms = max(iteration_times)
            result.timing.avg_ms = statistics.mean(iteration_times)
            result.timing.median_ms = statistics.median(iteration_times)

            if len(iteration_times) > 1:
                result.timing.std_dev_ms = statistics.stdev(iteration_times)

            # Calculate percentiles
            sorted_times = sorted(iteration_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            result.timing.p95_ms = sorted_times[min(p95_idx, len(sorted_times) - 1)]
            result.timing.p99_ms = sorted_times[min(p99_idx, len(sorted_times) - 1)]

        # Store result
        self.results.append(result)

        logger.info(
            f"Benchmark completed: {name} - Duration: {result.timing.duration_ms:.2f}ms, Avg: {result.timing.avg_ms:.2f}ms"
        )

        return result

    def compare_with_baseline(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Compare benchmark result with baseline."""
        baseline_key = f"{result.category.value}:{result.name}"

        if baseline_key not in self.baselines:
            return {"status": "no_baseline", "message": "No baseline found"}

        baseline = self.baselines[baseline_key]
        comparison = {"status": "compared", "baseline_timestamp": baseline.get("timestamp"), "metrics": {}}

        # Compare timing
        if "timing" in baseline:
            baseline_duration = baseline["timing"].get("duration_ms", 0)
            current_duration = result.timing.duration_ms

            if baseline_duration > 0:
                change_pct = (current_duration - baseline_duration) / baseline_duration * 100
                comparison["metrics"]["duration_ms"] = {
                    "baseline": baseline_duration,
                    "current": current_duration,
                    "change_percent": change_pct,
                    "regression": change_pct > 10,  # 10% threshold
                }

        # Compare memory
        if "memory" in baseline and baseline["memory"]:
            baseline_peak = baseline["memory"].get("peak_mb", 0)
            current_peak = result.memory.peak_mb

            if baseline_peak > 0:
                change_pct = (current_peak - baseline_peak) / baseline_peak * 100
                comparison["metrics"]["peak_memory_mb"] = {
                    "baseline": baseline_peak,
                    "current": current_peak,
                    "change_percent": change_pct,
                    "regression": change_pct > 20,  # 20% threshold
                }

        return comparison

    def set_baseline(self, result: BenchmarkResult) -> None:
        """Set benchmark result as new baseline."""
        baseline_key = f"{result.category.value}:{result.name}"
        self.baselines[baseline_key] = result.to_dict()
        self._save_baselines()
        logger.info(f"Set baseline for {baseline_key}")

    def save_result(self, result: BenchmarkResult, filename: Optional[str] = None) -> Path:
        """Save benchmark result to file."""
        if filename is None:
            filename = f"{result.category.value}_{result.name}_{result.benchmark_id}.json"
            filename = filename.replace(" ", "_").lower()

        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            f.write(result.to_json())

        logger.info(f"Saved benchmark result to {filepath}")
        return filepath

    def save_all_results(self, filename: str = "all_results.json") -> Path:
        """Save all benchmark results to a single file."""
        filepath = self.output_dir / filename

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(self.results),
            "results": [r.to_dict() for r in self.results],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all benchmark results."""
        if not self.results:
            return {"message": "No benchmark results"}

        by_category = {}
        for result in self.results:
            cat = result.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(
                {
                    "name": result.name,
                    "duration_ms": result.timing.duration_ms,
                    "avg_ms": result.timing.avg_ms,
                    "peak_memory_mb": result.memory.peak_mb,
                }
            )

        return {"total_benchmarks": len(self.results), "categories": list(by_category.keys()), "by_category": by_category}


def benchmark_timer(name: str, category: BenchmarkCategory = BenchmarkCategory.OVERALL):
    """Decorator for timing function execution."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000
                logger.debug(f"[Benchmark] {name}: {duration:.2f}ms")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000
                logger.debug(f"[Benchmark] {name}: {duration:.2f}ms")

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class ThroughputCalculator:
    """Calculate throughput metrics for operations."""

    def __init__(self):
        self.operations = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        """Start throughput measurement."""
        self.start_time = time.perf_counter()
        self.operations = 0

    def record_operation(self, count: int = 1) -> None:
        """Record operations completed."""
        self.operations += count

    def stop(self) -> ThroughputMetrics:
        """Stop measurement and return throughput metrics."""
        self.end_time = time.perf_counter()

        duration = (self.end_time - self.start_time) if self.start_time else 0

        metrics = ThroughputMetrics(operations=self.operations, duration_seconds=duration)
        metrics.calculate()

        return metrics


# Convenience functions
async def measure_scan_throughput(scan_func: Callable, targets: List[str], **kwargs) -> Tuple[BenchmarkResult, List[Any]]:
    """
    Measure scan throughput (targets per minute).

    Args:
        scan_func: Async scan function
        targets: List of targets to scan
        **kwargs: Additional arguments for scan function

    Returns:
        Tuple of (BenchmarkResult, scan results)
    """
    runner = BenchmarkRunner()
    scan_results = []

    async def benchmark_scan():
        for target in targets:
            result = await scan_func(target, **kwargs)
            scan_results.append(result)

    result = await runner.run_benchmark(
        name="scan_throughput",
        category=BenchmarkCategory.SCAN,
        description=f"Scan throughput for {len(targets)} targets",
        benchmark_func=benchmark_scan,
        iterations=1,
        monitor_resources=True,
    )

    # Calculate throughput
    result.throughput = ThroughputMetrics(operations=len(targets), duration_seconds=result.timing.duration_seconds)
    result.throughput.calculate()

    # Store targets per minute as custom metric
    result.custom_metrics["targets_per_minute"] = result.throughput.ops_per_minute
    result.custom_metrics["target_count"] = len(targets)

    return result, scan_results


async def measure_api_latency(endpoint: str, request_func: Callable, iterations: int = 100, **kwargs) -> BenchmarkResult:
    """
    Measure API endpoint latency.

    Args:
        endpoint: API endpoint name/path
        request_func: Async function that makes the request
        iterations: Number of requests to make
        **kwargs: Arguments for request function

    Returns:
        BenchmarkResult with latency metrics
    """
    runner = BenchmarkRunner()

    result = await runner.run_benchmark(
        name=f"api_latency_{endpoint}",
        category=BenchmarkCategory.API,
        description=f"API latency for {endpoint}",
        benchmark_func=request_func,
        iterations=iterations,
        monitor_resources=True,
        **kwargs,
    )

    # Calculate requests per second
    result.custom_metrics["requests_per_second"] = (
        iterations / result.timing.duration_seconds if result.timing.duration_seconds > 0 else 0
    )

    return result
