#!/usr/bin/env python3
"""
Performance Benchmarks for Zen-AI-Pentest

This module provides comprehensive performance benchmarks to measure
and compare the performance of various components before and after optimizations.

Usage:
    python -m benchmarks.performance_test
    python -m benchmarks.performance_test --component cache
    python -m benchmarks.performance_test --compare
"""

import asyncio
import time
import json
import sys
import argparse
import statistics
from dataclasses import dataclass, asdict
from typing import List, Dict, Callable, Any, Optional
from contextlib import contextmanager
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    name: str
    component: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    ops_per_second: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ComparisonResult:
    """Comparison between before and after optimization."""
    benchmark_name: str
    before_avg: float
    after_avg: float
    improvement_pct: float
    speedup_factor: float


class PerformanceBenchmarks:
    """Performance benchmarking suite for Zen-AI-Pentest."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.comparison_results: List[ComparisonResult] = []
    
    @contextmanager
    def _timer(self):
        """Simple timer context manager."""
        start = time.perf_counter()
        elapsed = []
        yield elapsed
        elapsed.append(time.perf_counter() - start)
    
    def _run_benchmark(
        self, 
        name: str, 
        component: str,
        func: Callable, 
        iterations: int = 100,
        warmup: int = 10,
        metadata: Dict = None
    ) -> BenchmarkResult:
        """Run a single benchmark with warmup and multiple iterations."""
        print(f"  Running {name} ({iterations} iterations)...", end=" ")
        
        # Warmup
        for _ in range(warmup):
            try:
                if asyncio.iscoroutinefunction(func):
                    asyncio.run(func())
                else:
                    func()
            except Exception as e:
                print(f"warmup error: {e}")
        
        # Actual benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(func):
                    asyncio.run(func())
                else:
                    func()
            except Exception as e:
                print(f"error: {e}")
                continue
            times.append(time.perf_counter() - start)
        
        result = BenchmarkResult(
            name=name,
            component=component,
            iterations=len(times),
            total_time=sum(times),
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            median_time=statistics.median(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            ops_per_second=len(times) / sum(times) if sum(times) > 0 else 0,
            metadata=metadata or {}
        )
        
        print(f"✓ {result.avg_time*1000:.3f}ms avg")
        return result
    
    # ========================================================================
    # Cache Benchmarks
    # ========================================================================
    
    def benchmark_cache_operations(self) -> List[BenchmarkResult]:
        """Benchmark cache get/set operations."""
        print("\n📦 Cache Performance Benchmarks")
        print("-" * 50)
        
        from core.cache import MemoryCache, SQLiteCache, generate_cache_key
        
        results = []
        
        # Memory cache benchmark
        async def memory_cache_ops():
            cache = MemoryCache(max_size=1000)
            
            # Set operations
            for i in range(100):
                await cache.set(f"key_{i}", {"data": f"value_{i}", "index": i})
            
            # Get operations
            for i in range(100):
                await cache.get(f"key_{i}")
        
        results.append(self._run_benchmark(
            "Memory Cache Operations",
            "cache",
            memory_cache_ops,
            iterations=50,
            metadata={"cache_type": "memory", "operations": 200}
        ))
        
        # Cache key generation benchmark
        def cache_key_gen():
            for i in range(100):
                generate_cache_key("test_func", i, foo="bar", baz=i*2)
        
        results.append(self._run_benchmark(
            "Cache Key Generation",
            "cache",
            cache_key_gen,
            iterations=1000,
            metadata={"operation": "key_generation"}
        ))
        
        return results
    
    # ========================================================================
    # Database Benchmarks
    # ========================================================================
    
    def benchmark_database_operations(self) -> List[BenchmarkResult]:
        """Benchmark database CRUD operations."""
        print("\n🗄️  Database Performance Benchmarks")
        print("-" * 50)
        
        results = []
        
        # Model instantiation benchmark
        from database.models import Scan, Finding, User
        
        def model_instantiation():
            for i in range(100):
                Scan(
                    name=f"Test Scan {i}",
                    target=f"192.168.1.{i}",
                    scan_type="network",
                    status="pending"
                )
        
        results.append(self._run_benchmark(
            "Model Instantiation",
            "database",
            model_instantiation,
            iterations=100,
            metadata={"model": "Scan", "operations": 100}
        ))
        
        # Finding model benchmark
        def finding_model_ops():
            for i in range(100):
                Finding(
                    scan_id=i,
                    title=f"Vulnerability {i}",
                    description="Test description",
                    severity="high",
                    cvss_score=7.5
                )
        
        results.append(self._run_benchmark(
            "Finding Model Operations",
            "database",
            finding_model_ops,
            iterations=100,
            metadata={"model": "Finding", "operations": 100}
        ))
        
        return results
    
    # ========================================================================
    # CVE Database Benchmarks
    # ========================================================================
    
    def benchmark_cve_database(self) -> List[BenchmarkResult]:
        """Benchmark CVE database operations."""
        print("\n🔒 CVE Database Performance Benchmarks")
        print("-" * 50)
        
        from modules.cve_database import CVEDatabase, search_cve_cached
        
        results = []
        cve_db = CVEDatabase()
        
        # Single CVE lookup
        def cve_lookup():
            cve_db.search_cve("CVE-2021-44228")
        
        results.append(self._run_benchmark(
            "Single CVE Lookup",
            "cve_database",
            cve_lookup,
            iterations=1000,
            metadata={"operation": "single_lookup", "cve": "CVE-2021-44228"}
        ))
        
        # Batch CVE lookup
        test_cves = ["CVE-2021-44228", "CVE-2021-45046", "CVE-2021-45105"]
        def batch_cve_lookup():
            cve_db.search_cve_batch(test_cves)
        
        results.append(self._run_benchmark(
            "Batch CVE Lookup (3)",
            "cve_database",
            batch_cve_lookup,
            iterations=500,
            metadata={"operation": "batch_lookup", "batch_size": 3}
        ))
        
        # Severity-based lookup
        def severity_lookup():
            cve_db.get_cves_by_severity("Critical")
        
        results.append(self._run_benchmark(
            "Severity-based Lookup",
            "cve_database",
            severity_lookup,
            iterations=100,
            metadata={"operation": "severity_lookup", "severity": "Critical"}
        ))
        
        # Cached lookup
        def cached_cve_lookup():
            search_cve_cached("CVE-2021-44228")
        
        results.append(self._run_benchmark(
            "Cached CVE Lookup",
            "cve_database",
            cached_cve_lookup,
            iterations=1000,
            metadata={"operation": "cached_lookup"}
        ))
        
        return results
    
    # ========================================================================
    # Tool Execution Benchmarks
    # ========================================================================
    
    def benchmark_tool_execution(self) -> List[BenchmarkResult]:
        """Benchmark tool execution framework."""
        print("\n🔧 Tool Execution Performance Benchmarks")
        print("-" * 50)
        
        from autonomous.tool_executor import ToolRegistry, ToolExecutor, ToolExecutionCache
        
        results = []
        
        # Tool registry operations
        def registry_ops():
            registry = ToolRegistry()
            for i in range(10):
                registry.check_installed("nmap")
                registry.list_tools(category="recon")
        
        results.append(self._run_benchmark(
            "Tool Registry Operations",
            "tool_execution",
            registry_ops,
            iterations=100,
            metadata={"operations": "check_installed + list_tools"}
        ))
        
        # Command building
        executor = ToolExecutor()
        from autonomous.tool_executor import ToolDefinition, SafetyLevel
        
        def command_build():
            tool = ToolDefinition(
                name="nmap",
                description="Test",
                command_template="nmap {options} {target}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon"
            )
            for i in range(100):
                executor._build_command(tool, {"target": f"192.168.1.{i}", "options": "-sS -p80,443"})
        
        results.append(self._run_benchmark(
            "Command Building",
            "tool_execution",
            command_build,
            iterations=500,
            metadata={"tool": "nmap", "operations": 100}
        ))
        
        # Tool execution cache
        async def execution_cache_ops():
            cache = ToolExecutionCache(ttl_seconds=300)
            
            # Simulate cache operations
            for i in range(50):
                key = f"tool_result_{i}"
                await cache.set(f"nmap_{i}", {"target": f"host_{i}"}, {"result": "open_ports: [80, 443]"})
            
            for i in range(50):
                await cache.get("nmap", {"target": f"host_{i}"})
        
        results.append(self._run_benchmark(
            "Tool Execution Cache",
            "tool_execution",
            execution_cache_ops,
            iterations=100,
            metadata={"cache_operations": 100}
        ))
        
        return results
    
    # ========================================================================
    # Agent Performance Benchmarks
    # ========================================================================
    
    def benchmark_agent_performance(self) -> List[BenchmarkResult]:
        """Benchmark agent performance."""
        print("\n🤖 Agent Performance Benchmarks")
        print("-" * 50)
        
        from agents.react_agent import ReActAgent, ReActAgentConfig, ContextWindowManager, LLMResponseCache
        
        results = []
        
        # Context window management
        def context_window_ops():
            manager = ContextWindowManager(max_messages=20)
            from langchain_core.messages import HumanMessage, AIMessage
            
            for i in range(50):
                manager.add_message(HumanMessage(content=f"Message {i}"))
                manager.add_message(AIMessage(content=f"Response {i}"))
            
            manager.get_context_messages([])
        
        results.append(self._run_benchmark(
            "Context Window Management",
            "agent",
            context_window_ops,
            iterations=200,
            metadata={"messages": 100}
        ))
        
        # LLM cache operations
        async def llm_cache_ops():
            cache = LLMResponseCache(ttl_seconds=300)
            from langchain_core.messages import HumanMessage, AIMessage
            
            messages = [HumanMessage(content="Test message")]
            tools = []
            
            for i in range(50):
                response = AIMessage(content=f"Response {i}")
                cache.set(messages, tools, response)
                cache.get(messages, tools)
        
        results.append(self._run_benchmark(
            "LLM Response Cache",
            "agent",
            llm_cache_ops,
            iterations=200,
            metadata={"cache_operations": 100}
        ))
        
        return results
    
    # ========================================================================
    # Memory Usage Benchmarks
    # ========================================================================
    
    def benchmark_memory_usage(self) -> List[BenchmarkResult]:
        """Benchmark memory usage."""
        print("\n💾 Memory Usage Benchmarks")
        print("-" * 50)
        
        import psutil
        import os
        
        results = []
        process = psutil.Process(os.getpid())
        
        # Memory before
        mem_before = process.memory_info().rss
        
        # CVE database memory usage
        from modules.cve_database import CVEDatabase
        
        def cve_db_memory():
            db = CVEDatabase()
            # Access some data to load into memory
            db.search_cve("CVE-2021-44228")
            db.get_cves_by_severity("Critical")
        
        results.append(self._run_benchmark(
            "CVE DB Initialization",
            "memory",
            cve_db_memory,
            iterations=10,
            metadata={"component": "CVEDatabase"}
        ))
        
        # Tool executor memory
        from autonomous.tool_executor import ToolExecutor, ToolRegistry
        
        def tool_executor_memory():
            registry = ToolRegistry()
            executor = ToolExecutor(registry=registry)
            _ = executor.get_available_tools()
        
        results.append(self._run_benchmark(
            "Tool Executor Initialization",
            "memory",
            tool_executor_memory,
            iterations=50,
            metadata={"component": "ToolExecutor"}
        ))
        
        # Memory after
        mem_after = process.memory_info().rss
        mem_diff = mem_after - mem_before
        
        print(f"  Memory delta: {mem_diff / (1024*1024):.2f} MB")
        
        return results
    
    # ========================================================================
    # Async Performance Benchmarks
    # ========================================================================
    
    def benchmark_async_performance(self) -> List[BenchmarkResult]:
        """Benchmark async operations performance."""
        print("\n⚡ Async Performance Benchmarks")
        print("-" * 50)
        
        results = []
        
        # Sequential vs Parallel execution simulation
        async def sequential_ops():
            async def task(i):
                await asyncio.sleep(0.001)  # Simulate I/O
                return i * 2
            
            for i in range(10):
                await task(i)
        
        async def parallel_ops():
            async def task(i):
                await asyncio.sleep(0.001)  # Simulate I/O
                return i * 2
            
            await asyncio.gather(*[task(i) for i in range(10)])
        
        results.append(self._run_benchmark(
            "Sequential Async Operations",
            "async",
            sequential_ops,
            iterations=50,
            metadata={"tasks": 10, "pattern": "sequential"}
        ))
        
        results.append(self._run_benchmark(
            "Parallel Async Operations",
            "async",
            parallel_ops,
            iterations=50,
            metadata={"tasks": 10, "pattern": "parallel"}
        ))
        
        return results
    
    # ========================================================================
    # Run All Benchmarks
    # ========================================================================
    
    def run_all(self, components: List[str] = None) -> Dict[str, List[BenchmarkResult]]:
        """Run all or selected benchmarks."""
        print("=" * 70)
        print("ZEN-AI-PENTEST PERFORMANCE BENCHMARKS")
        print("=" * 70)
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Python: {sys.version}")
        print("-" * 70)
        
        all_results = {}
        
        benchmark_methods = [
            ("cache", self.benchmark_cache_operations),
            ("database", self.benchmark_database_operations),
            ("cve_database", self.benchmark_cve_database),
            ("tool_execution", self.benchmark_tool_execution),
            ("agent", self.benchmark_agent_performance),
            ("memory", self.benchmark_memory_usage),
            ("async", self.benchmark_async_performance),
        ]
        
        for name, method in benchmark_methods:
            if components is None or name in components:
                try:
                    results = method()
                    all_results[name] = results
                    self.results.extend(results)
                except Exception as e:
                    print(f"\n❌ Error in {name} benchmarks: {e}")
                    import traceback
                    traceback.print_exc()
        
        return all_results
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate a benchmark report."""
        report_lines = [
            "# Zen-AI-Pentest Performance Benchmark Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"Python: {sys.version}",
            "\n## Summary",
            "",
            "| Component | Benchmark | Avg Time (ms) | Ops/Sec |",
            "|-----------|-----------|---------------|---------|",
        ]
        
        for result in self.results:
            avg_ms = result.avg_time * 1000
            report_lines.append(
                f"| {result.component} | {result.name} | {avg_ms:.3f} | {result.ops_per_second:.1f} |"
            )
        
        report_lines.extend([
            "",
            "## Detailed Results",
            "",
        ])
        
        for result in self.results:
            report_lines.extend([
                f"### {result.name}",
                f"- **Component**: {result.component}",
                f"- **Iterations**: {result.iterations}",
                f"- **Total Time**: {result.total_time:.3f}s",
                f"- **Average**: {result.avg_time*1000:.3f}ms",
                f"- **Median**: {result.median_time*1000:.3f}ms",
                f"- **Min**: {result.min_time*1000:.3f}ms",
                f"- **Max**: {result.max_time*1000:.3f}ms",
                f"- **Std Dev**: {result.std_dev*1000:.3f}ms",
                f"- **Ops/Sec**: {result.ops_per_second:.1f}",
                "",
            ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to: {output_file}")
        
        return report
    
    def save_json_results(self, output_file: str):
        """Save results as JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "benchmarks": [r.to_dict() for r in self.results]
        }
        
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"📊 JSON results saved to: {output_file}")
    
    def compare_with_baseline(self, baseline_file: str) -> List[ComparisonResult]:
        """Compare current results with a baseline."""
        try:
            with open(baseline_file, "r") as f:
                baseline = json.load(f)
            
            baseline_by_name = {
                b["name"]: b for b in baseline.get("benchmarks", [])
            }
            
            comparisons = []
            for result in self.results:
                if result.name in baseline_by_name:
                    baseline_result = baseline_by_name[result.name]
                    before_avg = baseline_result["avg_time"]
                    after_avg = result.avg_time
                    
                    improvement = ((before_avg - after_avg) / before_avg) * 100
                    speedup = before_avg / after_avg if after_avg > 0 else 1
                    
                    comparisons.append(ComparisonResult(
                        benchmark_name=result.name,
                        before_avg=before_avg,
                        after_avg=after_avg,
                        improvement_pct=improvement,
                        speedup_factor=speedup
                    ))
            
            self.comparison_results = comparisons
            return comparisons
            
        except FileNotFoundError:
            print(f"Baseline file not found: {baseline_file}")
            return []


def main():
    parser = argparse.ArgumentParser(description="Zen-AI-Pentest Performance Benchmarks")
    parser.add_argument(
        "--component", 
        choices=["cache", "database", "cve_database", "tool_execution", "agent", "memory", "async"],
        help="Run benchmarks for specific component only"
    )
    parser.add_argument("--output", "-o", help="Output file for report (markdown)")
    parser.add_argument("--json", "-j", help="Output file for JSON results")
    parser.add_argument("--compare", "-c", help="Compare with baseline JSON file")
    parser.add_argument("--baseline", "-b", help="Save results as baseline")
    
    args = parser.parse_args()
    
    benchmarks = PerformanceBenchmarks()
    
    # Run benchmarks
    components = [args.component] if args.component else None
    benchmarks.run_all(components=components)
    
    # Generate report
    report = benchmarks.generate_report(args.output)
    print("\n" + report)
    
    # Save JSON results
    if args.json:
        benchmarks.save_json_results(args.json)
    
    # Save baseline
    if args.baseline:
        benchmarks.save_json_results(args.baseline)
    
    # Compare with baseline
    if args.compare:
        comparisons = benchmarks.compare_with_baseline(args.compare)
        
        print("\n📊 Comparison with Baseline")
        print("-" * 70)
        print(f"{'Benchmark':<40} {'Before':>10} {'After':>10} {'Improvement':>12} {'Speedup':>8}")
        print("-" * 70)
        
        for comp in comparisons:
            before_ms = comp.before_avg * 1000
            after_ms = comp.after_avg * 1000
            improvement = f"{comp.improvement_pct:+.1f}%"
            speedup = f"{comp.speedup_factor:.2f}x"
            
            print(f"{comp.benchmark_name:<40} {before_ms:>8.2f}ms {after_ms:>8.2f}ms {improvement:>12} {speedup:>8}")
        
        # Overall improvement
        if comparisons:
            avg_improvement = sum(c.improvement_pct for c in comparisons) / len(comparisons)
            print("-" * 70)
            print(f"Average improvement: {avg_improvement:+.1f}%")
    
    print("\n✅ Benchmarks completed!")


if __name__ == "__main__":
    main()
