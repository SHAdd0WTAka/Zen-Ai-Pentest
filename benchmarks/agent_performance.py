"""
Agent Performance Benchmarks

Measures agent decision-making time, ReAct loop iterations, and tool selection speed.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.benchmark import (
    BenchmarkRunner, BenchmarkResult, BenchmarkCategory,
    TimingMetrics
)


class AgentTaskType(Enum):
    """Types of agent tasks for benchmarking."""
    RECONNAISSANCE = "reconnaissance"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"
    EXPLOIT_SELECTION = "exploit_selection"
    REPORT_GENERATION = "report_generation"


@dataclass
class AgentBenchmarkConfig:
    """Configuration for agent benchmarks."""
    iterations: int = 10
    task_type: AgentTaskType = AgentTaskType.VULNERABILITY_ANALYSIS
    complexity: str = "medium"  # simple, medium, complex
    max_react_iterations: int = 5


class AgentPerformanceBenchmark:
    """Benchmark suite for AI agent performance measurement."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.runner = BenchmarkRunner(output_dir=output_dir)
        self.config = AgentBenchmarkConfig()
    
    def _get_test_task(self, task_type: AgentTaskType, complexity: str) -> Dict[str, Any]:
        """Generate test tasks for benchmarking."""
        tasks = {
            AgentTaskType.RECONNAISSANCE: {
                "target": "example.com",
                "scope": "subdomains",
                "description": "Discover subdomains"
            },
            AgentTaskType.VULNERABILITY_ANALYSIS: {
                "target": "192.168.1.1",
                "scan_type": "full",
                "description": "Analyze vulnerabilities"
            },
            AgentTaskType.EXPLOIT_SELECTION: {
                "finding": {"type": "sqli", "severity": "high"},
                "target_info": {"os": "linux", "services": ["apache", "mysql"]},
                "description": "Select appropriate exploit"
            },
            AgentTaskType.REPORT_GENERATION: {
                "findings_count": 10 if complexity == "simple" else 50 if complexity == "medium" else 100,
                "format": "pdf",
                "description": "Generate security report"
            }
        }
        return tasks.get(task_type, tasks[AgentTaskType.VULNERABILITY_ANALYSIS])
    
    async def benchmark_decision_time(self, config: Optional[AgentBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark agent decision-making time.
        
        Returns:
            BenchmarkResult with decision timing metrics
        """
        cfg = config or self.config
        task = self._get_test_task(cfg.task_type, cfg.complexity)
        
        async def make_decision():
            # Simulate agent decision-making process
            # This would integrate with actual agent in production
            base_delay = 0.5 if cfg.complexity == "simple" else 1.0 if cfg.complexity == "medium" else 2.0
            await asyncio.sleep(base_delay + (hash(str(task)) % 100) / 1000)
            return {"decision": "scan", "confidence": 0.85}
        
        result = await self.runner.run_benchmark(
            name="agent_decision_time",
            category=BenchmarkCategory.AGENT,
            description=f"Agent decision time for {cfg.task_type.value} ({cfg.complexity})",
            benchmark_func=make_decision,
            iterations=cfg.iterations,
            monitor_resources=True
        )
        
        result.custom_metrics["task_type"] = cfg.task_type.value
        result.custom_metrics["complexity"] = cfg.complexity
        result.custom_metrics["decisions_per_second"] = (
            cfg.iterations / result.timing.duration_seconds
            if result.timing.duration_seconds > 0 else 0
        )
        
        return result
    
    async def benchmark_react_loop(self, config: Optional[AgentBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark ReAct loop performance.
        
        Returns:
            BenchmarkResult with ReAct loop metrics
        """
        cfg = config or AgentBenchmarkConfig(
            iterations=5,
            max_react_iterations=5
        )
        
        async def run_react_loop():
            # Simulate ReAct loop iterations
            for iteration in range(cfg.max_react_iterations):
                # Thought
                await asyncio.sleep(0.2)
                # Action
                await asyncio.sleep(0.3)
                # Observation
                await asyncio.sleep(0.1)
            
            return {"iterations": cfg.max_react_iterations, "completed": True}
        
        result = await self.runner.run_benchmark(
            name="react_loop_performance",
            category=BenchmarkCategory.AGENT,
            description=f"ReAct loop with {cfg.max_react_iterations} iterations",
            benchmark_func=run_react_loop,
            iterations=cfg.iterations,
            monitor_resources=True
        )
        
        # Calculate per-iteration metrics
        avg_per_iteration = result.timing.avg_ms / cfg.max_react_iterations
        
        result.custom_metrics["max_iterations"] = cfg.max_react_iterations
        result.custom_metrics["ms_per_iteration"] = avg_per_iteration
        result.custom_metrics["iterations_per_second"] = (
            1000 / avg_per_iteration if avg_per_iteration > 0 else 0
        )
        
        return result
    
    async def benchmark_tool_selection(self, config: Optional[AgentBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark tool selection speed.
        
        Returns:
            BenchmarkResult with tool selection metrics
        """
        cfg = config or self.config
        
        test_scenarios = [
            {"task": "port_scan", "tools_available": 5},
            {"task": "web_enum", "tools_available": 8},
            {"task": "vuln_check", "tools_available": 12},
            {"task": "exploit", "tools_available": 6},
        ]
        
        async def select_tools():
            for scenario in test_scenarios:
                # Simulate tool selection decision
                await asyncio.sleep(0.15 * scenario["tools_available"])
            return {"selections": len(test_scenarios)}
        
        result = await self.runner.run_benchmark(
            name="tool_selection_speed",
            category=BenchmarkCategory.AGENT,
            description="AI tool selection performance",
            benchmark_func=select_tools,
            iterations=cfg.iterations,
            monitor_resources=True
        )
        
        result.custom_metrics["scenarios_tested"] = len(test_scenarios)
        result.custom_metrics["selections_per_second"] = (
            (len(test_scenarios) * cfg.iterations) / result.timing.duration_seconds
            if result.timing.duration_seconds > 0 else 0
        )
        
        return result
    
    async def benchmark_memory_usage(self, config: Optional[AgentBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark agent memory usage during operations.
        
        Returns:
            BenchmarkResult with memory metrics
        """
        cfg = config or AgentBenchmarkConfig(complexity="complex")
        
        async def agent_operation():
            # Simulate agent operation that builds context
            context_size = 100 if cfg.complexity == "simple" else 500 if cfg.complexity == "medium" else 1000
            
            context = []
            for i in range(context_size):
                context.append({
                    "step": i,
                    "observation": f"Observation {i}",
                    "action": f"Action {i}",
                    "result": f"Result data for step {i}" * 10
                })
                if i % 100 == 0:
                    await asyncio.sleep(0.01)
            
            return {"context_size": len(context)}
        
        result = await self.runner.run_benchmark(
            name="agent_memory_usage",
            category=BenchmarkCategory.AGENT,
            description=f"Agent memory usage ({cfg.complexity} context)",
            benchmark_func=agent_operation,
            iterations=3,
            monitor_resources=True
        )
        
        result.custom_metrics["complexity"] = cfg.complexity
        result.custom_metrics["memory_per_100_context"] = (
            result.memory.peak_mb / 10 if cfg.complexity == "complex" else
            result.memory.peak_mb / 5 if cfg.complexity == "medium" else
            result.memory.peak_mb
        )
        
        return result
    
    async def benchmark_reasoning_quality(self, config: Optional[AgentBenchmarkConfig] = None) -> BenchmarkResult:
        """
        Benchmark reasoning quality vs time tradeoff.
        
        Returns:
            BenchmarkResult with reasoning metrics
        """
        cfg = config or AgentBenchmarkConfig()
        
        reasoning_depths = ["fast", "balanced", "thorough"]
        
        async def reasoning_benchmark():
            for depth in reasoning_depths:
                delay = {"fast": 0.5, "balanced": 1.0, "thorough": 2.0}[depth]
                await asyncio.sleep(delay)
            return {"depths_tested": reasoning_depths}
        
        result = await self.runner.run_benchmark(
            name="reasoning_quality_time",
            category=BenchmarkCategory.AGENT,
            description="Reasoning quality vs time tradeoff",
            benchmark_func=reasoning_benchmark,
            iterations=cfg.iterations,
            monitor_resources=True
        )
        
        result.custom_metrics["reasoning_depths"] = reasoning_depths
        result.custom_metrics["avg_time_per_depth"] = (
            result.timing.avg_ms / len(reasoning_depths)
        )
        
        return result
    
    async def run_all(self) -> List[BenchmarkResult]:
        """Run all agent performance benchmarks."""
        results = []
        
        print("Running agent performance benchmarks...")
        
        benchmarks = [
            ("Decision Time", self.benchmark_decision_time),
            ("ReAct Loop", self.benchmark_react_loop),
            ("Tool Selection", self.benchmark_tool_selection),
            ("Memory Usage", self.benchmark_memory_usage),
            ("Reasoning Quality", self.benchmark_reasoning_quality),
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
        self.runner.save_all_results("agent_benchmarks.json")
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of agent benchmark results."""
        return self.runner.get_summary()


# Convenience function
async def measure_agent_decision_time(
    decision_func: Callable,
    iterations: int = 10,
    output_dir: str = "benchmark_results"
) -> BenchmarkResult:
    """
    Quick function to measure agent decision time.
    
    Args:
        decision_func: Async function for agent decision
        iterations: Number of iterations
        output_dir: Directory for results
    
    Returns:
        BenchmarkResult with timing metrics
    """
    runner = BenchmarkRunner(output_dir=output_dir)
    
    result = await runner.run_benchmark(
        name="agent_decision",
        category=BenchmarkCategory.AGENT,
        description="Agent decision time measurement",
        benchmark_func=decision_func,
        iterations=iterations,
        monitor_resources=True
    )
    
    runner.save_result(result)
    return result


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Performance Benchmarks")
    parser.add_argument("--output", default="benchmark_results", help="Output directory")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
    parser.add_argument("--complexity", default="medium", 
                       choices=["simple", "medium", "complex"],
                       help="Task complexity")
    
    args = parser.parse_args()
    
    async def main():
        config = AgentBenchmarkConfig(
            iterations=args.iterations,
            complexity=args.complexity
        )
        
        benchmark = AgentPerformanceBenchmark(output_dir=args.output)
        results = await benchmark.run_all()
        
        print("\n" + "="*60)
        print("AGENT PERFORMANCE BENCHMARK RESULTS")
        print("="*60)
        
        for result in results:
            print(f"\n{result.name}:")
            print(f"  Avg Time: {result.timing.avg_ms:.2f}ms")
            print(f"  P95: {result.timing.p95_ms:.2f}ms")
            print(f"  Peak Memory: {result.memory.peak_mb:.2f} MB")
            
            if result.custom_metrics:
                print("  Custom Metrics:")
                for key, value in result.custom_metrics.items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.3f}")
                    else:
                        print(f"    {key}: {value}")
    
    asyncio.run(main())
