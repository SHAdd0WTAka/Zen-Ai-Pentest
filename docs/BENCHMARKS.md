# Performance Benchmarks

This document describes the performance benchmark system for Zen-AI-Pentest.

## Overview

The benchmark system provides comprehensive performance measurement for:
- **Scan throughput** (targets per minute)
- **Memory usage** during operations
- **API latency** and response times
- **Agent decision-making** time

## Quick Start

### Run All Benchmarks

```bash
python scripts/run_benchmarks.py
```

### Run Specific Benchmark Type

```bash
# Scan performance only
python scripts/run_benchmarks.py --type scan

# Agent performance only
python scripts/run_benchmarks.py --type agent

# API performance only
python scripts/run_benchmarks.py --type api
```

### Compare with Baselines

```bash
# Run benchmarks and compare with previous results
python scripts/run_benchmarks.py --compare

# Update baselines after successful run
python scripts/run_benchmarks.py --update-baseline
```

## Benchmark Categories

### 1. Scan Performance (`benchmarks/scan_performance.py`)

Measures scan execution speed and throughput.

**Metrics:**
- Targets scanned per minute
- Scan duration (min, max, avg, P95, P99)
- Memory usage during scans
- Concurrent scan performance

**Example:**
```python
from benchmarks.scan_performance import ScanPerformanceBenchmark

async def run_scan_benchmarks():
    benchmark = ScanPerformanceBenchmark()
    results = await benchmark.run_all()
    
    for result in results:
        print(f"{result.name}: {result.throughput.ops_per_minute:.2f} targets/min")
```

### 2. Agent Performance (`benchmarks/agent_performance.py`)

Measures AI agent decision-making and reasoning performance.

**Metrics:**
- Decision time (ms)
- ReAct loop iterations per second
- Tool selection speed
- Memory usage with context
- Reasoning quality vs time tradeoff

**Example:**
```python
from benchmarks.agent_performance import AgentPerformanceBenchmark

async def run_agent_benchmarks():
    benchmark = AgentPerformanceBenchmark()
    results = await benchmark.run_all()
    
    for result in results:
        print(f"{result.name}: {result.timing.avg_ms:.2f}ms avg")
```

### 3. API Performance (`benchmarks/api_performance.py`)

Measures API endpoint response times and throughput.

**Metrics:**
- Endpoint latency (P50, P95, P99)
- Requests per second (RPS)
- Concurrent request handling
- Memory usage under load
- WebSocket performance

**Example:**
```python
from benchmarks.api_performance import APIPerformanceBenchmark

async def run_api_benchmarks():
    benchmark = APIPerformanceBenchmark()
    results = await benchmark.run_all()
    
    for result in results:
        print(f"{result.name}: {result.timing.avg_ms:.2f}ms avg, "
              f"{result.custom_metrics.get('requests_per_second', 0):.2f} RPS")
```

## Benchmark Framework (`modules/benchmark.py`)

The core benchmark framework provides:

### BenchmarkRunner

Main class for running benchmarks with full metrics collection:

```python
from modules.benchmark import BenchmarkRunner, BenchmarkCategory

runner = BenchmarkRunner(output_dir="benchmark_results")

result = await runner.run_benchmark(
    name="my_benchmark",
    category=BenchmarkCategory.SCAN,
    description="Description of the benchmark",
    benchmark_func=my_async_function,
    iterations=10,
    warmup_iterations=2,
    monitor_resources=True
)
```

### ResourceMonitor

Monitors system resources during benchmark execution:

```python
from modules.benchmark import ResourceMonitor

monitor = ResourceMonitor(interval=0.5)
await monitor.start()

# ... run benchmark ...

await monitor.stop()
memory_metrics = monitor.get_memory_metrics()
cpu_metrics = monitor.get_cpu_metrics()
```

### Context Manager for Simple Timing

```python
from modules.benchmark import BenchmarkRunner, BenchmarkCategory

runner = BenchmarkRunner()

with runner.measure("operation_name", BenchmarkCategory.TOOL) as result:
    # Your code here
    await perform_operation()

# result.timing.duration_ms contains the elapsed time
```

## Metrics Collected

### Timing Metrics

| Metric | Description |
|--------|-------------|
| `duration_ms` | Total duration of benchmark |
| `avg_ms` | Average time per iteration |
| `min_ms` | Minimum iteration time |
| `max_ms` | Maximum iteration time |
| `median_ms` | Median iteration time |
| `p95_ms` | 95th percentile |
| `p99_ms` | 99th percentile |
| `std_dev_ms` | Standard deviation |

### Memory Metrics

| Metric | Description |
|--------|-------------|
| `initial_mb` | Initial memory usage |
| `peak_mb` | Peak memory usage |
| `final_mb` | Final memory usage |
| `delta_mb` | Memory change |
| `avg_mb` | Average memory usage |

### CPU Metrics

| Metric | Description |
|--------|-------------|
| `avg_percent` | Average CPU usage |
| `peak_percent` | Peak CPU usage |

### Throughput Metrics

| Metric | Description |
|--------|-------------|
| `operations` | Total operations performed |
| `ops_per_second` | Operations per second |
| `ops_per_minute` | Operations per minute |

## CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/benchmark.yml` workflow runs benchmarks:

- **Schedule:** Weekly on Sundays at 3 AM UTC
- **Pull Requests:** When performance-critical code changes
- **Manual:** Via workflow_dispatch

### Features

1. **Automated Execution**: Runs all benchmarks automatically
2. **Artifact Storage**: Results stored as workflow artifacts (90 days)
3. **Baseline Comparison**: Compares with previous results
4. **PR Comments**: Posts results to pull requests
5. **Regression Detection**: Fails build on significant regressions

### Workflow Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `benchmark_type` | Type to run (all/scan/agent/api/quick) | `all` |
| `compare_with_baseline` | Compare with baseline | `true` |
| `update_baseline` | Update baseline after run | `false` |

## Baseline Management

Baselines are stored in `benchmark_results/baselines.json`.

### Setting a New Baseline

```bash
python scripts/run_benchmarks.py --update-baseline
```

### Comparing with Baseline

```bash
python scripts/run_benchmarks.py --compare
```

### Regression Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Duration | +10% | Warning |
| Memory | +20% | Warning |

## Output Files

After running benchmarks, the following files are generated:

```
benchmark_results/
├── benchmark_report.md       # Markdown report
├── benchmark_report.json     # JSON report
├── baselines.json            # Baseline results
├── comparison_report.json    # Comparison with baseline
├── scan_*.json               # Individual scan benchmarks
├── agent_*.json              # Individual agent benchmarks
└── api_*.json                # Individual API benchmarks
```

## Interpreting Results

### Example Report

```markdown
# Performance Benchmark Report

**Generated:** 2024-01-15 10:30:00 UTC
**Total Benchmarks:** 15

## Summary

### scan

| Benchmark | Duration | Avg Time | Throughput | Peak Memory |
|-----------|----------|----------|------------|-------------|
| nmap_scan_speed | 5210ms | 521.00ms | 115.20 | 45.23MB |
| web_scan_speed | 6200ms | 1240.00ms | 48.39 | 52.10MB |

## Detailed Results

### nmap_scan_speed

**Category:** scan
**Description:** Nmap scan speed for 10 targets

#### Timing

- **Duration:** 5210.00ms
- **Average:** 521.00ms
- **Min:** 480.00ms
- **Max:** 580.00ms
- **P95:** 570.00ms
- **P99:** 578.00ms

#### Resources

- **Peak Memory:** 45.23 MB
- **Avg Memory:** 38.50 MB
- **Peak CPU:** 25.0%
- **Avg CPU:** 15.5%
```

## Best Practices

1. **Run on Dedicated Hardware**: For consistent results, run benchmarks on dedicated hardware
2. **Multiple Iterations**: Use at least 10 iterations for statistical significance
3. **Warmup**: Always include warmup iterations to prime caches
4. **Baseline Updates**: Update baselines only after intentional performance improvements
5. **Monitor Trends**: Track benchmark trends over time, not just single results

## Troubleshooting

### Benchmarks Fail to Run

1. Check Python version (3.9+ required)
2. Install dependencies: `pip install psutil pytest pytest-asyncio`
3. Ensure write permissions to output directory

### Inconsistent Results

1. Close other applications
2. Run on idle system
3. Increase iteration count
4. Check for thermal throttling

### Memory Benchmarks Show 0

Resource monitoring may not work on all platforms. Ensure:
- `psutil` is installed
- Running on supported OS (Linux, macOS, Windows)
- Sufficient permissions to read process info

## Contributing

To add a new benchmark:

1. Create benchmark function in appropriate file (`scan_performance.py`, `agent_performance.py`, `api_performance.py`)
2. Add to `run_all()` method
3. Update this documentation
4. Run benchmarks to verify

## References

- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [psutil documentation](https://psutil.readthedocs.io/)
- [Python time module](https://docs.python.org/3/library/time.html)
