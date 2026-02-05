"""
Scan Performance Benchmarks

Measures scan throughput, target processing speed, and tool execution times.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.benchmark import (
    BenchmarkRunner, BenchmarkResult, BenchmarkCategory,
    ThroughputMetrics, measure_scan_throughput
)


@dataclass
class ScanBenchmarkConfig:
    """Configuration for scan benchmarks."""
    target_count: int = 10
    target_type: str = "host"  # host, web, network
    ports: str = "top-100"
    scan_depth: str = "quick"  # quick, standard, deep
    concurrent_scans: int = 3
    warmup_targets: int = 2


class ScanPerformanceBenchmark:
    """Benchmark suite for scan performance measurement."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.runner = BenchmarkRunner(output_dir=output_dir)
        self.config = ScanBenchmarkConfig()
    
    def _generate_test_targets(self, count: int, target_type: str) -> List[str]:
        """Generate test targets for benchmarking."""
        if target_type == "host":
            # Generate local network targets for testing
            return [f"192.168.1.{i}" for i in range(1, min(count + 1, 255))]
        elif target_type == "web":
            # Generate test web targets
            return [f"test-target-{i}.local" for i in range(count)]
        elif target_type == "network":
            # Generate network ranges
            ranges = []
            for i in range(min(count, 10)):
                ranges.append(f"10.0.{i}.0/24")
            return ranges
        return []
    
    async def benchmark_nmap_speed(self, config: Optional[ScanBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark Nmap scan speed.
        
        Returns:
            BenchmarkResult with scan timing metrics
        """
        cfg = config or self.config
        targets = self._generate_test_targets(cfg.target_count, cfg.target_type)
        
        # Mock scan function for benchmarking structure
        async def mock_nmap_scan(target: str) -> Dict[str, Any]:
            # Simulate scan delay
            await asyncio.sleep(0.5)
            return {"target": target, "status": "completed", "ports_found": 5}
        
        result, _ = await measure_scan_throughput(
            scan_func=mock_nmap_scan,
            targets=targets,
        )
        
        result.name = "nmap_scan_speed"
        result.description = f"Nmap scan speed for {len(targets)} targets"
        
        return result
    
    async def benchmark_web_scan_speed(self, config: Optional[ScanBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark web vulnerability scan speed.
        
        Returns:
            BenchmarkResult with web scan timing metrics
        """
        cfg = config or ScanBenchmarkConfig(target_count=5, target_type="web")
        targets = self._generate_test_targets(cfg.target_count, cfg.target_type)
        
        async def mock_web_scan(target: str) -> Dict[str, Any]:
            # Simulate web scan with crawling
            await asyncio.sleep(1.2)
            return {
                "target": target,
                "pages_scanned": 15,
                "vulnerabilities_found": 3
            }
        
        result, _ = await measure_scan_throughput(
            scan_func=mock_web_scan,
            targets=targets,
        )
        
        result.name = "web_scan_speed"
        result.description = f"Web vulnerability scan speed for {len(targets)} targets"
        
        return result
    
    async def benchmark_scan_throughput(self, config: Optional[ScanBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark overall scan throughput (targets per minute).
        
        Returns:
            BenchmarkResult with throughput metrics
        """
        cfg = config or self.config
        targets = self._generate_test_targets(cfg.target_count, cfg.target_type)
        
        async def mock_scan(target: str) -> Dict[str, Any]:
            # Simulate varying scan times
            delay = 0.3 + (hash(target) % 10) / 10  # 0.3-1.3s
            await asyncio.sleep(delay)
            return {"target": target, "completed": True}
        
        result, _ = await measure_scan_throughput(
            scan_func=mock_scan,
            targets=targets,
        )
        
        result.name = "scan_throughput"
        result.description = f"Overall scan throughput: {len(targets)} targets"
        
        return result
    
    async def benchmark_concurrent_scans(self, config: Optional[ScanBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark performance with concurrent scans.
        
        Returns:
            BenchmarkResult with concurrent scan metrics
        """
        cfg = config or self.config
        targets = self._generate_test_targets(cfg.target_count * 2, cfg.target_type)
        
        async def concurrent_benchmark():
            semaphore = asyncio.Semaphore(cfg.concurrent_scans)
            
            async def scan_with_limit(target: str):
                async with semaphore:
                    await asyncio.sleep(0.4)
                    return {"target": target}
            
            await asyncio.gather(*[scan_with_limit(t) for t in targets])
        
        result = await self.runner.run_benchmark(
            name="concurrent_scan_performance",
            category=BenchmarkCategory.SCAN,
            description=f"Concurrent scan performance ({cfg.concurrent_scans} parallel)",
            benchmark_func=concurrent_benchmark,
            iterations=1,
            monitor_resources=True
        )
        
        # Calculate effective throughput
        result.throughput = ThroughputMetrics(
            operations=len(targets),
            duration_seconds=result.timing.duration_seconds
        )
        result.throughput.calculate()
        
        result.custom_metrics["concurrent_scans"] = cfg.concurrent_scans
        result.custom_metrics["total_targets"] = len(targets)
        
        return result
    
    async def run_all(self) -> List[BenchmarkResult]:
        """Run all scan performance benchmarks."""
        results = []
        
        print("Running scan performance benchmarks...")
        
        # Run each benchmark
        benchmarks = [
            ("Nmap Speed", self.benchmark_nmap_speed),
            ("Web Scan Speed", self.benchmark_web_scan_speed),
            ("Scan Throughput", self.benchmark_scan_throughput),
            ("Concurrent Scans", self.benchmark_concurrent_scans),
        ]
        
        for name, benchmark_func in benchmarks:
            print(f"  Running: {name}...")
            try:
                result = await benchmark_func()
                results.append(result)
                self.runner.save_result(result)
                print(f"    ✓ {name}: {result.throughput.ops_per_minute:.1f} targets/min")
            except Exception as e:
                print(f"    ✗ {name} failed: {e}")
        
        # Save combined results
        self.runner.save_all_results("scan_benchmarks.json")
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of scan benchmark results."""
        return self.runner.get_summary()


# Convenience function
async def measure_scan_speed(
    scan_func: Callable,
    targets: List[str],
    output_dir: str = "benchmark_results"
) -> BenchmarkResult:
    """
    Quick function to measure scan speed.
    
    Args:
        scan_func: Async function to perform scan
        targets: List of targets
        output_dir: Directory for results
    
    Returns:
        BenchmarkResult with scan metrics
    """
    result, _ = await measure_scan_throughput(
        scan_func=scan_func,
        targets=targets
    )
    
    # Save result
    runner = BenchmarkRunner(output_dir=output_dir)
    runner.save_result(result)
    
    return result


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan Performance Benchmarks")
    parser.add_argument("--output", default="benchmark_results", help="Output directory")
    parser.add_argument("--targets", type=int, default=10, help="Number of test targets")
    parser.add_argument("--type", default="host", choices=["host", "web", "network"],
                       help="Target type")
    
    args = parser.parse_args()
    
    async def main():
        _ = ScanBenchmarkConfig(
            target_count=args.targets,
            target_type=args.type
        )
        
        benchmark = ScanPerformanceBenchmark(output_dir=args.output)
        results = await benchmark.run_all()
        
        print("\n" + "="*60)
        print("SCAN PERFORMANCE BENCHMARK RESULTS")
        print("="*60)
        
        for result in results:
            print(f"\n{result.name}:")
            print(f"  Duration: {result.timing.duration_ms:.2f}ms")
            print(f"  Throughput: {result.throughput.ops_per_minute:.2f} ops/min")
            print(f"  Peak Memory: {result.memory.peak_mb:.2f} MB")
    
    asyncio.run(main())
