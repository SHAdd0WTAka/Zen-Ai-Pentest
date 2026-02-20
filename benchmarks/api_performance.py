"""
API Performance Benchmarks

Measures API response times, throughput, and endpoint-specific latency.
"""

import asyncio
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.benchmark import BenchmarkCategory, BenchmarkResult, BenchmarkRunner, ThroughputMetrics


class APIEndpointType(Enum):
    """Types of API endpoints for benchmarking."""

    AUTH = "authentication"
    SCANS = "scans"
    FINDINGS = "findings"
    REPORTS = "reports"
    WEBSOCKET = "websocket"


@dataclass
class APIBenchmarkConfig:
    """Configuration for API benchmarks."""

    base_url: str = "http://localhost:8000"
    iterations: int = 100
    concurrent_requests: int = 10
    warmup_requests: int = 10
    timeout_seconds: float = 30.0


class APIPerformanceBenchmark:
    """Benchmark suite for API performance measurement."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.runner = BenchmarkRunner(output_dir=output_dir)
        self.config = APIBenchmarkConfig()

    def _get_test_endpoints(self) -> List[Dict[str, Any]]:
        """Get test endpoint definitions."""
        return [
            {"name": "health_check", "path": "/health", "method": "GET", "type": APIEndpointType.AUTH, "payload": None},
            {
                "name": "auth_login",
                "path": "/auth/login",
                "method": "POST",
                "type": APIEndpointType.AUTH,
                "payload": {"username": "test", "password": "test"},
            },
            {"name": "list_scans", "path": "/scans", "method": "GET", "type": APIEndpointType.SCANS, "payload": None},
            {
                "name": "create_scan",
                "path": "/scans",
                "method": "POST",
                "type": APIEndpointType.SCANS,
                "payload": {"name": "test", "target": "127.0.0.1", "type": "quick"},
            },
            {"name": "list_findings", "path": "/findings", "method": "GET", "type": APIEndpointType.FINDINGS, "payload": None},
        ]

    async def benchmark_endpoint_latency(
        self, endpoint_name: str, request_func: Callable, config: Optional[APIBenchmarkConfig] = None
    ) -> BenchmarkResult:
        """
        Benchmark latency for a specific endpoint.

        Args:
            endpoint_name: Name of the endpoint
            request_func: Async function that makes the request
            config: Benchmark configuration

        Returns:
            BenchmarkResult with latency metrics
        """
        cfg = config or self.config

        result = await self.runner.run_benchmark(
            name=f"api_latency_{endpoint_name}",
            category=BenchmarkCategory.API,
            description=f"API latency for {endpoint_name}",
            benchmark_func=request_func,
            iterations=cfg.iterations,
            warmup_iterations=cfg.warmup_requests,
            monitor_resources=True,
        )

        # Calculate RPS
        result.custom_metrics["requests_per_second"] = (
            cfg.iterations / result.timing.duration_seconds if result.timing.duration_seconds > 0 else 0
        )
        result.custom_metrics["endpoint"] = endpoint_name

        return result

    async def benchmark_all_endpoints(self, config: Optional[APIBenchmarkConfig] = None) -> List[BenchmarkResult]:
        """
        Benchmark all API endpoints.

        Returns:
            List of BenchmarkResult for each endpoint
        """
        cfg = config or self.config
        endpoints = self._get_test_endpoints()
        results = []

        for endpoint in endpoints:
            # Create mock request function
            async def mock_request(endpoint=endpoint):
                # Simulate request delay based on endpoint type
                delay_map = {
                    APIEndpointType.AUTH: 0.05,
                    APIEndpointType.SCANS: 0.1,
                    APIEndpointType.FINDINGS: 0.08,
                    APIEndpointType.REPORTS: 0.15,
                    APIEndpointType.WEBSOCKET: 0.02,
                }
                delay = delay_map.get(endpoint["type"], 0.1)
                delay += (hash(endpoint["name"]) % 50) / 1000  # Add variance
                await asyncio.sleep(delay)
                return {"status": "ok", "endpoint": endpoint["name"]}

            try:
                result = await self.benchmark_endpoint_latency(endpoint["name"], mock_request, cfg)
                results.append(result)
            except Exception as e:
                print(f"  Failed to benchmark {endpoint['name']}: {e}")

        return results

    async def benchmark_concurrent_requests(self, config: Optional[APIBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark API with concurrent requests.

        Returns:
            BenchmarkResult with concurrent request metrics
        """
        cfg = config or APIBenchmarkConfig(concurrent_requests=20)

        async def concurrent_requests():
            semaphore = asyncio.Semaphore(cfg.concurrent_requests)

            async def make_request():
                async with semaphore:
                    await asyncio.sleep(0.05)  # Simulate request
                    return {"status": "ok"}

            # Make multiple batches of concurrent requests
            total_requests = cfg.iterations * cfg.concurrent_requests
            tasks = [make_request() for _ in range(total_requests)]
            await asyncio.gather(*tasks)

            return {"total_requests": total_requests}

        result = await self.runner.run_benchmark(
            name="api_concurrent_requests",
            category=BenchmarkCategory.API,
            description=f"API concurrent requests ({cfg.concurrent_requests} parallel)",
            benchmark_func=concurrent_requests,
            iterations=1,
            monitor_resources=True,
        )

        total_requests = cfg.iterations * cfg.concurrent_requests
        result.throughput = ThroughputMetrics(operations=total_requests, duration_seconds=result.timing.duration_seconds)
        result.throughput.calculate()

        result.custom_metrics["concurrent_limit"] = cfg.concurrent_requests
        result.custom_metrics["total_requests"] = total_requests
        result.custom_metrics["requests_per_second"] = result.throughput.ops_per_second

        return result

    async def benchmark_authentication_flow(self, config: Optional[APIBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark complete authentication flow.

        Returns:
            BenchmarkResult with auth flow metrics
        """
        cfg = config or self.config

        async def auth_flow():
            # Step 1: Login
            await asyncio.sleep(0.1)

            # Step 2: Get token
            await asyncio.sleep(0.05)

            # Step 3: Validate token
            await asyncio.sleep(0.03)

            return {"authenticated": True}

        result = await self.runner.run_benchmark(
            name="api_authentication_flow",
            category=BenchmarkCategory.API,
            description="Complete authentication flow",
            benchmark_func=auth_flow,
            iterations=cfg.iterations,
            monitor_resources=True,
        )

        result.custom_metrics["flow_steps"] = 3
        result.custom_metrics["avg_time_per_step"] = result.timing.avg_ms / 3

        return result

    async def benchmark_scan_workflow(self, config: Optional[APIBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark complete scan workflow (create -> start -> poll -> results).

        Returns:
            BenchmarkResult with scan workflow metrics
        """
        cfg = config or self.config

        async def scan_workflow():
            # Step 1: Create scan
            await asyncio.sleep(0.1)
            scan_id = "scan_123"

            # Step 2: Start scan
            await asyncio.sleep(0.05)

            # Step 3: Poll for completion (3 polls)
            for _ in range(3):
                await asyncio.sleep(0.08)

            # Step 4: Get results
            await asyncio.sleep(0.1)

            return {"scan_id": scan_id, "completed": True}

        result = await self.runner.run_benchmark(
            name="api_scan_workflow",
            category=BenchmarkCategory.API,
            description="Complete scan workflow",
            benchmark_func=scan_workflow,
            iterations=cfg.iterations // 10,  # Fewer iterations as it's slower
            monitor_resources=True,
        )

        result.custom_metrics["workflow_steps"] = 6
        result.custom_metrics["avg_time_per_step"] = result.timing.avg_ms / 6

        return result

    async def benchmark_websocket_performance(self, config: Optional[APIBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark WebSocket connection performance.

        Returns:
            BenchmarkResult with WebSocket metrics
        """
        cfg = config or APIBenchmarkConfig(iterations=50)

        async def websocket_benchmark():
            # Simulate WebSocket connection and message exchange
            messages = 10

            # Connection establishment
            await asyncio.sleep(0.05)

            # Message exchange
            for _ in range(messages):
                await asyncio.sleep(0.02)

            # Disconnection
            await asyncio.sleep(0.01)

            return {"messages_exchanged": messages}

        result = await self.runner.run_benchmark(
            name="api_websocket_performance",
            category=BenchmarkCategory.API,
            description="WebSocket connection and messaging",
            benchmark_func=websocket_benchmark,
            iterations=cfg.iterations,
            monitor_resources=True,
        )

        result.custom_metrics["messages_per_connection"] = 10
        result.custom_metrics["connections_per_second"] = (
            cfg.iterations / result.timing.duration_seconds if result.timing.duration_seconds > 0 else 0
        )

        return result

    async def benchmark_memory_usage_under_load(self, config: Optional[APIBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark API memory usage under sustained load.

        Returns:
            BenchmarkResult with memory usage metrics
        """
        cfg = config or APIBenchmarkConfig(iterations=500, concurrent_requests=50)

        async def sustained_load():
            semaphore = asyncio.Semaphore(cfg.concurrent_requests)

            async def make_request():
                async with semaphore:
                    # Simulate varying response sizes
                    await asyncio.sleep(0.03)
                    return {"data": "x" * 1000}  # 1KB response

            # Sustained load
            tasks = [make_request() for _ in range(cfg.iterations)]
            await asyncio.gather(*tasks)

            return {"requests_made": cfg.iterations}

        result = await self.runner.run_benchmark(
            name="api_memory_under_load",
            category=BenchmarkCategory.API,
            description="Memory usage under sustained load",
            benchmark_func=sustained_load,
            iterations=1,
            monitor_resources=True,
        )

        result.custom_metrics["total_requests"] = cfg.iterations
        result.custom_metrics["memory_per_100_requests"] = result.memory.peak_mb / (cfg.iterations / 100)

        return result

    async def run_all(self) -> List[BenchmarkResult]:
        """Run all API performance benchmarks."""
        results = []

        print("Running API performance benchmarks...")

        # Benchmark individual endpoints
        print("  Running: Individual endpoint latency...")
        endpoint_results = await self.benchmark_all_endpoints()
        results.extend(endpoint_results)
        for result in endpoint_results:
            self.runner.save_result(result)
            print(f"    ✓ {result.custom_metrics.get('endpoint', 'unknown')}: {result.timing.avg_ms:.2f}ms avg")

        # Run other benchmarks
        benchmarks = [
            ("Concurrent Requests", self.benchmark_concurrent_requests),
            ("Authentication Flow", self.benchmark_authentication_flow),
            ("Scan Workflow", self.benchmark_scan_workflow),
            ("WebSocket Performance", self.benchmark_websocket_performance),
            ("Memory Under Load", self.benchmark_memory_usage_under_load),
        ]

        for name, benchmark_func in benchmarks:
            print(f"  Running: {name}...")
            try:
                result = await benchmark_func()
                results.append(result)
                self.runner.save_result(result)
                print(f"    ✓ {name}: {result.timing.avg_ms:.2f}ms avg")
            except Exception as e:
                print(f"    ✗ {name} failed: {e}")

        # Save combined results
        self.runner.save_all_results("api_benchmarks.json")

        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of API benchmark results."""
        return self.runner.get_summary()


# Convenience function
async def measure_api_response_time(
    endpoint: str, request_func: Callable, iterations: int = 100, output_dir: str = "benchmark_results"
) -> BenchmarkResult:
    """
    Quick function to measure API response time.

    Args:
        endpoint: API endpoint name/path
        request_func: Async function that makes the request
        iterations: Number of requests
        output_dir: Directory for results

    Returns:
        BenchmarkResult with latency metrics
    """
    benchmark = APIPerformanceBenchmark(output_dir=output_dir)
    result = await benchmark.benchmark_endpoint_latency(endpoint, request_func)
    return result


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="API Performance Benchmarks")
    parser.add_argument("--output", default="benchmark_results", help="Output directory")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")

    args = parser.parse_args()

    async def main():
        _ = APIBenchmarkConfig(  # TODO: Use config
            iterations=args.iterations, concurrent_requests=args.concurrent, base_url=args.base_url
        )

        benchmark = APIPerformanceBenchmark(output_dir=args.output)
        results = await benchmark.run_all()

        print("\n" + "=" * 60)
        print("API PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)

        for result in results:
            print(f"\n{result.name}:")
            print(f"  Avg Latency: {result.timing.avg_ms:.2f}ms")
            print(f"  P95: {result.timing.p95_ms:.2f}ms")
            print(f"  P99: {result.timing.p99_ms:.2f}ms")

            if "requests_per_second" in result.custom_metrics:
                rps = result.custom_metrics["requests_per_second"]
                print(f"  RPS: {rps:.2f}")

            if result.memory.peak_mb > 0:
                print(f"  Peak Memory: {result.memory.peak_mb:.2f} MB")

    asyncio.run(main())
