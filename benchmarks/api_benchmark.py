#!/usr/bin/env python3
"""
API Performance Benchmark
"""

import asyncio
import statistics
import time
from typing import Dict


class APIBenchmark:
    """Benchmark API endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    async def benchmark_endpoint(self, method: str, path: str, iterations: int = 100) -> Dict:
        """Benchmark a single endpoint"""
        times = []

        for _ in range(iterations):
            start = time.time()
            # Simulate request
            await asyncio.sleep(0.001)
            elapsed = time.time() - start
            times.append(elapsed)

        sorted_times = sorted(times)
        return {
            "endpoint": f"{method} {path}",
            "requests": len(times),
            "mean_ms": statistics.mean(times) * 1000,
            "p50_ms": statistics.median(times) * 1000,
            "p95_ms": sorted_times[int(len(times) * 0.95)] * 1000,
            "p99_ms": sorted_times[int(len(times) * 0.99)] * 1000,
        }

    async def run_benchmarks(self):
        """Run all API benchmarks"""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/v1/tools/"),
        ]

        for method, path in endpoints:
            print(f"Benchmarking {method} {path}...")
            result = await self.benchmark_endpoint(method, path)
            self.results[f"{method} {path}"] = result

        return self.results

    def generate_report(self) -> str:
        """Generate report"""
        report = "# API Performance Benchmark\n\n"
        report += "| Endpoint | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) |\n"
        report += "|----------|-----------|----------|----------|----------|\n"

        for endpoint, data in self.results.items():
            report += f"| {endpoint} | {data['mean_ms']:.2f} | {data['p50_ms']:.2f} | {data['p95_ms']:.2f} | {data['p99_ms']:.2f} |\n"

        return report


if __name__ == "__main__":
    benchmark = APIBenchmark()
    results = asyncio.run(benchmark.run_benchmarks())
    print(benchmark.generate_report())
