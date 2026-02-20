"""
Local Benchmark Runner

Command-line interface for running all benchmarks locally.
Generates reports, compares with baselines, and outputs results.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.agent_performance import AgentPerformanceBenchmark
from benchmarks.api_performance import APIPerformanceBenchmark
from benchmarks.scan_performance import ScanPerformanceBenchmark
from modules.benchmark import BenchmarkCategory, BenchmarkResult


class LocalBenchmarkRunner:
    """Runner for executing all benchmarks locally."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        self.baseline_file = self.output_dir / "baselines.json"

    def load_baselines(self) -> Dict[str, Any]:
        """Load baseline results from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load baselines: {e}")
        return {}

    def save_baselines(self, results: List[BenchmarkResult]) -> None:
        """Save current results as new baselines."""
        baselines = {}
        for result in results:
            key = f"{result.category.value}:{result.name}"
            baselines[key] = result.to_dict()

        with open(self.baseline_file, "w") as f:
            json.dump(baselines, f, indent=2)
        print(f"\n✓ Saved {len(baselines)} baselines to {self.baseline_file}")

    def compare_with_baselines(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Compare results with baselines."""
        baselines = self.load_baselines()

        if not baselines:
            return {"status": "no_baselines", "message": "No baselines found for comparison"}

        comparison = {
            "timestamp": datetime.utcnow().isoformat(),
            "regressions_found": False,
            "regressions": [],
            "improvements": [],
            "unchanged": [],
            "summary": {},
        }

        for result in results:
            key = f"{result.category.value}:{result.name}"

            if key not in baselines:
                comparison["unchanged"].append({"benchmark": result.name, "reason": "no_baseline"})
                continue

            baseline = baselines[key]

            # Compare duration
            baseline_duration = baseline.get("timing", {}).get("duration_ms", 0)
            current_duration = result.timing.duration_ms

            if baseline_duration > 0:
                change_pct = ((current_duration - baseline_duration) / baseline_duration) * 100

                comparison_data = {
                    "benchmark": result.name,
                    "category": result.category.value,
                    "metric": "duration_ms",
                    "baseline": baseline_duration,
                    "current": current_duration,
                    "change_percent": round(change_pct, 2),
                }

                if change_pct > 10:  # 10% slower threshold
                    comparison["regressions_found"] = True
                    comparison["regressions"].append(comparison_data)
                elif change_pct < -10:  # 10% faster threshold
                    comparison["improvements"].append(comparison_data)
                else:
                    comparison["unchanged"].append(comparison_data)

            # Compare memory
            baseline_memory = baseline.get("memory", {}).get("peak_mb", 0)
            current_memory = result.memory.peak_mb

            if baseline_memory > 0 and current_memory > 0:
                memory_change = ((current_memory - baseline_memory) / baseline_memory) * 100
                if memory_change > 20:  # 20% memory increase threshold
                    comparison["regressions"].append(
                        {
                            "benchmark": result.name,
                            "category": result.category.value,
                            "metric": "peak_memory_mb",
                            "baseline": baseline_memory,
                            "current": current_memory,
                            "change_percent": round(memory_change, 2),
                        }
                    )

        # Summary
        comparison["summary"] = {
            "total_benchmarks": len(results),
            "regressions": len(comparison["regressions"]),
            "improvements": len(comparison["improvements"]),
            "unchanged": len(comparison["unchanged"]),
        }

        return comparison

    async def run_scan_benchmarks(self) -> List[BenchmarkResult]:
        """Run scan performance benchmarks."""
        print("\n" + "=" * 60)
        print("SCAN PERFORMANCE BENCHMARKS")
        print("=" * 60)

        benchmark = ScanPerformanceBenchmark(output_dir=str(self.output_dir))
        results = await benchmark.run_all()
        return results

    async def run_agent_benchmarks(self) -> List[BenchmarkResult]:
        """Run agent performance benchmarks."""
        print("\n" + "=" * 60)
        print("AGENT PERFORMANCE BENCHMARKS")
        print("=" * 60)

        benchmark = AgentPerformanceBenchmark(output_dir=str(self.output_dir))
        results = await benchmark.run_all()
        return results

    async def run_api_benchmarks(self) -> List[BenchmarkResult]:
        """Run API performance benchmarks."""
        print("\n" + "=" * 60)
        print("API PERFORMANCE BENCHMARKS")
        print("=" * 60)

        benchmark = APIPerformanceBenchmark(output_dir=str(self.output_dir))
        results = await benchmark.run_all()
        return results

    async def run_all(self, benchmark_type: str = "all") -> List[BenchmarkResult]:
        """Run all requested benchmarks."""
        all_results = []

        if benchmark_type in ["all", "scan"]:
            results = await self.run_scan_benchmarks()
            all_results.extend(results)

        if benchmark_type in ["all", "agent"]:
            results = await self.run_agent_benchmarks()
            all_results.extend(results)

        if benchmark_type in ["all", "api"]:
            results = await self.run_api_benchmarks()
            all_results.extend(results)

        self.results = all_results
        return all_results

    def generate_report(self, output_file: str = "benchmark_report.md") -> str:
        """Generate markdown report of benchmark results."""
        lines = [
            "# Performance Benchmark Report",
            "",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Total Benchmarks:** {len(self.results)}",
            "",
            "## Summary",
            "",
        ]

        # Group by category
        by_category: Dict[str, List[BenchmarkResult]] = {}
        for result in self.results:
            cat = result.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        for category, results in by_category.items():
            lines.extend(
                [
                    f"### {category.title()}",
                    "",
                    "| Benchmark | Duration | Avg Time | Throughput | Peak Memory |",
                    "|-----------|----------|----------|------------|-------------|",
                ]
            )

            for result in results:
                throughput = result.custom_metrics.get(
                    "targets_per_minute", result.custom_metrics.get("requests_per_second", "N/A")
                )
                throughput_str = f"{throughput:.2f}" if isinstance(throughput, float) else str(throughput)

                lines.append(
                    f"| {result.name} | "
                    f"{result.timing.duration_ms:.0f}ms | "
                    f"{result.timing.avg_ms:.2f}ms | "
                    f"{throughput_str} | "
                    f"{result.memory.peak_mb:.2f}MB |"
                )

            lines.append("")

        # Detailed results
        lines.extend(
            [
                "## Detailed Results",
                "",
            ]
        )

        for result in self.results:
            lines.extend(
                [
                    f"### {result.name}",
                    "",
                    f"**Category:** {result.category.value}",
                    f"**Description:** {result.description}",
                    "",
                    "#### Timing",
                    "",
                    f"- **Duration:** {result.timing.duration_ms:.2f}ms",
                    f"- **Average:** {result.timing.avg_ms:.2f}ms",
                    f"- **Min:** {result.timing.min_ms:.2f}ms",
                    f"- **Max:** {result.timing.max_ms:.2f}ms",
                    f"- **P95:** {result.timing.p95_ms:.2f}ms",
                    f"- **P99:** {result.timing.p99_ms:.2f}ms",
                    "",
                    "#### Resources",
                    "",
                    f"- **Peak Memory:** {result.memory.peak_mb:.2f} MB",
                    f"- **Avg Memory:** {result.memory.avg_mb:.2f} MB",
                    f"- **Peak CPU:** {result.cpu.peak_percent:.1f}%",
                    f"- **Avg CPU:** {result.cpu.avg_percent:.1f}%",
                    "",
                ]
            )

            if result.custom_metrics:
                lines.extend(
                    [
                        "#### Custom Metrics",
                        "",
                    ]
                )
                for key, value in result.custom_metrics.items():
                    if isinstance(value, float):
                        lines.append(f"- **{key}:** {value:.3f}")
                    else:
                        lines.append(f"- **{key}:** {value}")
                lines.append("")

        # Environment info
        if self.results:
            lines.extend(
                [
                    "## Environment",
                    "",
                    "```json",
                    json.dumps(self.results[0].environment, indent=2),
                    "```",
                    "",
                ]
            )

        report = "\n".join(lines)

        # Save report
        report_path = self.output_dir / output_file
        with open(report_path, "w") as f:
            f.write(report)

        return report

    def generate_json_report(self, output_file: str = "benchmark_report.json") -> str:
        """Generate JSON report of benchmark results."""
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_benchmarks": len(self.results),
            "results": [r.to_dict() for r in self.results],
        }

        report_path = self.output_dir / output_file
        with open(report_path, "w") as f:
            json.dump(data, f, indent=2)

        return str(report_path)

    def print_summary(self) -> None:
        """Print summary of results to console."""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"\nTotal Benchmarks: {len(self.results)}")

        # Group by category
        by_category: Dict[str, List[BenchmarkResult]] = {}
        for result in self.results:
            cat = result.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        for category, results in by_category.items():
            print(f"\n{category.upper()}:")
            for result in results:
                throughput = result.custom_metrics.get(
                    "targets_per_minute", result.custom_metrics.get("requests_per_second", None)
                )

                if throughput:
                    print(f"  ✓ {result.name}: {result.timing.avg_ms:.2f}ms avg, {throughput:.2f} throughput")
                else:
                    print(f"  ✓ {result.name}: {result.timing.avg_ms:.2f}ms avg")

        print(f"\nResults saved to: {self.output_dir}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Local Benchmark Runner for Zen-AI-Pentest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all benchmarks
  python run_benchmarks.py

  # Run specific benchmark type
  python run_benchmarks.py --type scan
  python run_benchmarks.py --type agent
  python run_benchmarks.py --type api

  # Compare with baselines
  python run_benchmarks.py --compare

  # Update baselines
  python run_benchmarks.py --update-baseline

  # Generate reports only
  python run_benchmarks.py --report --input benchmark_results/

  # Summarize existing results
  python run_benchmarks.py --summarize --input benchmark_results/
        """,
    )

    parser.add_argument(
        "--type", choices=["all", "scan", "agent", "api", "quick"], default="all", help="Type of benchmarks to run"
    )
    parser.add_argument("--output", default="benchmark_results", help="Output directory for results")
    parser.add_argument("--compare", action="store_true", help="Compare results with baselines")
    parser.add_argument("--update-baseline", action="store_true", help="Update baselines after running")
    parser.add_argument("--report", action="store_true", help="Generate markdown report from existing results")
    parser.add_argument("--summarize", action="store_true", help="Print summary of existing results")
    parser.add_argument("--input", help="Input directory for existing results")
    parser.add_argument("--baseline", help="Path to baseline file for comparison")
    parser.add_argument("--results", help="Path to results file for comparison")

    args = parser.parse_args()

    # Handle comparison mode
    if args.compare and args.baseline and args.results:
        print("Comparing results with baselines...")
        runner = LocalBenchmarkRunner(output_dir=args.output)

        # Load results
        with open(args.results) as f:
            results_data = json.load(f)

        results = []
        for r in results_data.get("results", []):
            # Reconstruct BenchmarkResult from dict
            result = BenchmarkResult(
                benchmark_id=r["benchmark_id"],
                name=r["name"],
                category=BenchmarkCategory(r["category"]),
                description=r["description"],
            )
            # ... parse other fields
            results.append(result)

        comparison = runner.compare_with_baselines(results)

        print("\nComparison Results:")
        print(f"  Regressions: {comparison['summary']['regressions']}")
        print(f"  Improvements: {comparison['summary']['improvements']}")
        print(f"  Unchanged: {comparison['summary']['unchanged']}")

        # Save comparison
        comparison_path = Path(args.output) / "comparison_report.json"
        with open(comparison_path, "w") as f:
            json.dump(comparison, f, indent=2)
        print(f"\nComparison saved to: {comparison_path}")

        return

    # Handle summarize mode
    if args.summarize and args.input:
        print("Summarizing existing results...")
        runner = LocalBenchmarkRunner(output_dir=args.input)

        # Load existing results
        report_file = Path(args.input) / "benchmark_report.json"
        if report_file.exists():
            with open(report_file) as f:
                data = json.load(f)

            print(f"\nFound {data.get('total_benchmarks', 0)} benchmarks")
            print(f"Timestamp: {data.get('timestamp', 'unknown')}")

            for r in data.get("results", []):
                print(f"\n  {r['name']}:")
                print(f"    Category: {r['category']}")
                print(f"    Duration: {r['timing']['duration_ms']:.2f}ms")
                print(f"    Memory: {r['memory']['peak_mb']:.2f}MB")
        else:
            print(f"No benchmark report found in {args.input}")
        return

    # Handle report generation mode
    if args.report and args.input:
        print("Generating report from existing results...")
        runner = LocalBenchmarkRunner(output_dir=args.input)

        # Load existing results
        report_file = Path(args.input) / "benchmark_report.json"
        if report_file.exists():
            with open(report_file) as f:
                data = json.load(f)

            # Convert dicts back to BenchmarkResult objects
            # (simplified - in production would need full reconstruction)
            _ = runner.generate_report()
            print(f"\nReport generated: {args.input}/benchmark_report.md")
        return

    # Run benchmarks
    print("=" * 60)
    print("Zen-AI-Pentest Benchmark Runner")
    print("=" * 60)

    runner = LocalBenchmarkRunner(output_dir=args.output)

    # Run benchmarks
    asyncio.run(runner.run_all(args.type))

    # Compare with baselines if requested
    if args.compare:
        print("\nComparing with baselines...")
        comparison = runner.compare_with_baselines(runner.results)

        if comparison.get("regressions_found"):
            print("\n⚠️  Performance regressions detected:")
            for reg in comparison["regressions"]:
                print(f"  - {reg['benchmark']}: +{reg['change_percent']}% {reg['metric']}")
        else:
            print("\n✅ No performance regressions detected")

        if comparison.get("improvements"):
            print("\n📈 Improvements:")
            for imp in comparison["improvements"]:
                print(f"  - {imp['benchmark']}: {imp['change_percent']}% {imp['metric']}")

        # Save comparison
        comparison_path = runner.output_dir / "comparison_report.json"
        with open(comparison_path, "w") as f:
            json.dump(comparison, f, indent=2)

    # Generate reports
    print("\nGenerating reports...")
    runner.generate_report()
    runner.generate_json_report()

    # Update baselines if requested
    if args.update_baseline:
        runner.save_baselines(runner.results)

    # Print summary
    runner.print_summary()

    print("\n✅ Benchmark run complete!")


if __name__ == "__main__":
    main()
