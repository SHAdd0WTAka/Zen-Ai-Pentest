#!/usr/bin/env python3
"""
Competitor Analysis Script

Analyzes competitor tool outputs, generates comparison reports,
and visualizes benchmark results.

Usage:
    python analyze_competitors.py --mode simulate --competitor pentestgpt --test-case vuln_01_sql_injection
    python analyze_competitors.py --mode compare --results-dir benchmark_results/
    python analyze_competitors.py --mode visualize --results-dir benchmark_results/ --output-dir charts/
"""

import argparse
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.comparison.common_benchmarks import (
    BenchmarkTestCase,
    CompetitorResult,
    FindingResult,
    TestCategory,
    TestStatus,
    load_test_case,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CompetitorSimulator:
    """Simulates competitor tool results based on known capabilities."""

    # Known capability profiles based on documentation and research
    CAPABILITY_PROFILES = {
        "pentestgpt": {
            "detection_rate": 0.75,
            "precision": 0.80,
            "recall": 0.70,
            "speed_factor": 0.6,  # Slower due to LLM latency
            "cost_per_test": 0.50,  # OpenAI API costs
            "strengths": ["web", "api", "complex_reasoning"],
            "weaknesses": ["network", "speed", "cost"],
            "test_performance": {
                "recon_01_basic_scan": {"detection": 0.70, "duration": 120},
                "vuln_01_sql_injection": {"detection": 0.85, "duration": 180},
                "vuln_02_xss": {"detection": 0.80, "duration": 150},
                "auth_01_jwt_test": {"detection": 0.75, "duration": 200},
                "api_01_rest_scan": {"detection": 0.80, "duration": 240},
                "web_01_crawl_depth": {"detection": 0.75, "duration": 300},
                "net_01_port_scan": {"detection": 0.50, "duration": 180},
                "cloud_01_s3_check": {"detection": 0.70, "duration": 150},
                "container_01_docker_scan": {"detection": 0.60, "duration": 200},
                "report_01_pdf_gen": {"detection": 0.85, "duration": 60},
            },
        },
        "autopentest": {
            "detection_rate": 0.65,
            "precision": 0.85,
            "recall": 0.60,
            "speed_factor": 0.8,
            "cost_per_test": 0.0,  # No API costs
            "strengths": ["network", "exploitation", "autonomous"],
            "weaknesses": ["web", "cloud", "containers"],
            "test_performance": {
                "recon_01_basic_scan": {"detection": 0.85, "duration": 90},
                "vuln_01_sql_injection": {"detection": 0.40, "duration": 120},
                "vuln_02_xss": {"detection": 0.30, "duration": 100},
                "auth_01_jwt_test": {"detection": 0.20, "duration": 120},
                "api_01_rest_scan": {"detection": 0.30, "duration": 150},
                "web_01_crawl_depth": {"detection": 0.35, "duration": 180},
                "net_01_port_scan": {"detection": 0.90, "duration": 120},
                "cloud_01_s3_check": {"detection": 0.10, "duration": 60},
                "container_01_docker_scan": {"detection": 0.20, "duration": 120},
                "report_01_pdf_gen": {"detection": 0.40, "duration": 45},
            },
        },
    }

    def __init__(self, competitor_name: str):
        self.competitor = competitor_name.lower()
        if self.competitor not in self.CAPABILITY_PROFILES:
            raise ValueError(f"Unknown competitor: {competitor_name}")
        self.profile = self.CAPABILITY_PROFILES[self.competitor]

    def simulate_test(self, test_case: BenchmarkTestCase) -> CompetitorResult:
        """Simulate a test execution with realistic results."""

        test_id = test_case.id
        perf = self.profile["test_performance"].get(
            test_id,
            {"detection": 0.50, "duration": 120},  # Default
        )

        # Add some randomness to simulate real-world variance
        detection_rate = perf["detection"]
        base_duration = perf["duration"]

        # Random variation (±15%)
        detection_variation = random.uniform(-0.15, 0.15)
        duration_variation = random.uniform(0.85, 1.15)

        actual_detection = max(0, min(1, detection_rate + detection_variation))
        actual_duration = base_duration * duration_variation

        # Calculate findings based on detection rate
        expected_count = len(test_case.expected_findings)
        found_count = int(expected_count * actual_detection)

        # Generate simulated findings
        findings = []
        for i, expected in enumerate(test_case.expected_findings[:found_count]):
            finding = FindingResult(
                vuln_type=expected.vuln_type,
                severity=expected.severity,
                location=expected.location,
                confidence=random.uniform(0.70, 0.95),
                description=f"Detected {expected.vuln_type} at {expected.location}",
                cwe_id=expected.cwe_id,
                verified=random.random() > 0.3,
                exploited=random.random() > 0.7,
                detection_time_ms=int(random.uniform(1000, 10000)),
            )
            findings.append(finding)

        # Add some false positives (5-15%)
        fp_count = int(found_count * random.uniform(0.05, 0.15))
        for _ in range(fp_count):
            fp_finding = FindingResult(
                vuln_type="potential_vulnerability",
                severity="medium",
                location=f"/unknown/path{random.randint(1, 100)}",
                confidence=random.uniform(0.50, 0.65),
                description="Potential issue detected (may be false positive)",
            )
            findings.append(fp_finding)

        # Create result
        result = CompetitorResult(
            tool_name=self.competitor.capitalize(),
            tool_version="1.0",
            test_case_id=test_id,
            status=TestStatus.PASSED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            scan_duration_seconds=actual_duration,
            findings=findings,
            tokens_used=int(random.uniform(10000, 50000)) if self.competitor == "pentestgpt" else 0,
            cost_usd=self.profile["cost_per_test"] * random.uniform(0.8, 1.2),
        )

        # Calculate metrics
        result.calculate_metrics(test_case.expected_findings)

        return result


class ComparisonAnalyzer:
    """Analyzes and compares benchmark results."""

    def __init__(self, results_dir: Path):
        self.results_dir = Path(results_dir)
        self.results: Dict[str, List[CompetitorResult]] = {}

    def load_results(self) -> None:
        """Load all benchmark results from directory."""
        for result_file in self.results_dir.glob("*.json"):
            try:
                with open(result_file, "r") as f:
                    data = json.load(f)

                # Determine tool name from filename
                tool_name = result_file.stem.split("_")[0]

                if tool_name not in self.results:
                    self.results[tool_name] = []

                # Convert to CompetitorResult
                result = CompetitorResult(**data)
                self.results[tool_name].append(result)

            except Exception as e:
                logger.warning(f"Failed to load {result_file}: {e}")

    def compare_tools(self) -> Dict[str, Any]:
        """Generate comprehensive comparison between tools."""
        comparison = {
            "generated_at": datetime.utcnow().isoformat(),
            "tools_compared": list(self.results.keys()),
            "summary": {},
            "detailed_results": {},
            "category_analysis": {},
            "recommendations": [],
        }

        # Calculate overall scores
        for tool_name, results in self.results.items():
            if not results:
                continue

            avg_detection = sum(r.detection_rate for r in results) / len(results)
            avg_precision = sum(r.precision for r in results) / len(results)
            avg_recall = sum(r.recall for r in results) / len(results)
            avg_f1 = sum(r.f1_score for r in results) / len(results)
            avg_duration = sum(r.duration_seconds for r in results) / len(results)

            comparison["summary"][tool_name] = {
                "tests_run": len(results),
                "avg_detection_rate": round(avg_detection, 3),
                "avg_precision": round(avg_precision, 3),
                "avg_recall": round(avg_recall, 3),
                "avg_f1_score": round(avg_f1, 3),
                "avg_duration_seconds": round(avg_duration, 1),
                "total_findings": sum(len(r.findings) for r in results),
                "overall_score": round(
                    0.3 * avg_detection
                    + 0.2 * avg_precision
                    + 0.15 * avg_recall
                    + 0.15 * avg_f1
                    + 0.1 * (1 / max(avg_duration / 300, 1)),
                    3,
                ),
            }

        # Determine winner
        if comparison["summary"]:
            winner = max(comparison["summary"].items(), key=lambda x: x[1]["overall_score"])
            comparison["winner"] = {"tool": winner[0], "score": winner[1]["overall_score"]}

        return comparison

    def generate_markdown_report(
        self, template_path: Optional[Path] = None, output_path: Path = Path("comparison_report.md")
    ) -> str:
        """Generate markdown comparison report."""
        comparison = self.compare_tools()

        if template_path and template_path.exists():
            # Use template-based generation
            with open(template_path, "r") as f:
                template = f.read()

            # Simple template substitution (in production, use Jinja2)
            report = self._fill_template(template, comparison)
        else:
            # Generate simple report
            report = self._generate_simple_report(comparison)

        # Write to file
        with open(output_path, "w") as f:
            f.write(report)

        logger.info(f"Report generated: {output_path}")
        return report

    def _generate_simple_report(self, comparison: Dict[str, Any]) -> str:
        """Generate a simple markdown report."""
        lines = [
            "# Competitive Benchmark Comparison Report",
            "",
            f"**Generated:** {comparison['generated_at']}",
            "",
            "## Summary",
            "",
            "| Tool | Tests | Detection Rate | Precision | F1 Score | Duration | Overall |",
            "|------|-------|----------------|-----------|----------|----------|---------|",
        ]

        for tool_name, metrics in comparison["summary"].items():
            lines.append(
                f"| {tool_name} | {metrics['tests_run']} | "
                f"{metrics['avg_detection_rate']:.1%} | "
                f"{metrics['avg_precision']:.3f} | "
                f"{metrics['avg_f1_score']:.3f} | "
                f"{metrics['avg_duration_seconds']:.1f}s | "
                f"{metrics['overall_score']:.3f} |"
            )

        if "winner" in comparison:
            lines.extend(["", f"### 🏆 Winner: {comparison['winner']['tool']} (Score: {comparison['winner']['score']:.3f})"])

        lines.extend(["", "## Detailed Results", ""])

        for tool_name, results in self.results.items():
            lines.extend(
                [
                    f"### {tool_name}",
                    "",
                    "| Test Case | Status | Detection | Duration | Findings |",
                    "|-----------|--------|-----------|----------|----------|",
                ]
            )

            for result in results:
                status_emoji = {
                    TestStatus.PASSED: "✅",
                    TestStatus.FAILED: "❌",
                    TestStatus.ERROR: "⚠️",
                    TestStatus.TIMEOUT: "⏱️",
                    TestStatus.SKIPPED: "⏭️",
                }.get(result.status, "❓")

                lines.append(
                    f"| {result.test_case_id} | {status_emoji} {result.status.value} | "
                    f"{result.detection_rate:.1%} | "
                    f"{result.duration_seconds:.1f}s | "
                    f"{len(result.findings)} |"
                )

            lines.append("")

        return "\n".join(lines)

    def _fill_template(self, template: str, comparison: Dict[str, Any]) -> str:
        """Simple template filling with placeholders."""
        # This is a simplified version - in production use Jinja2
        report = template

        # Replace basic placeholders
        report = report.replace("{{report_id}}", f"RPT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
        report = report.replace("{{generation_date}}", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        report = report.replace("{{total_test_cases}}", str(max(len(results) for results in self.results.values())))

        # Replace summary metrics
        if comparison["summary"]:
            for tool, metrics in comparison["summary"].items():
                prefix = tool.lower().replace("-", "_")
                for key, value in metrics.items():
                    placeholder = f"{{{{{prefix}_{key}}}}}"
                    if isinstance(value, float):
                        report = report.replace(placeholder, f"{value:.3f}")
                    else:
                        report = report.replace(placeholder, str(value))

        # Replace winner
        if "winner" in comparison:
            report = report.replace("{{overall_winner}}", comparison["winner"]["tool"])

        return report

    def generate_visualizations(self, output_dir: Path) -> None:
        """Generate comparison charts."""
        try:
            import matplotlib.pyplot as plt  # noqa: F401
            import numpy as np  # noqa: F401
        except ImportError:
            logger.warning("matplotlib not available, skipping visualizations")
            return

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        comparison = self.compare_tools()

        # 1. Overall Score Comparison
        self._create_bar_chart(
            output_dir / "overall_scores.png",
            "Overall Score Comparison",
            "Tool",
            "Score",
            {tool: data["overall_score"] for tool, data in comparison["summary"].items()},
        )

        # 2. Detection Rate by Category
        # Group results by test case category
        category_data = {}
        for tool_name, results in self.results.items():
            for result in results:
                # Extract category from test_case_id
                category = result.test_case_id.split("_")[0]
                if category not in category_data:
                    category_data[category] = {}
                if tool_name not in category_data[category]:
                    category_data[category][tool_name] = []
                category_data[category][tool_name].append(result.detection_rate)

        # Average by category
        for category, tools in category_data.items():
            category_data[category] = {tool: sum(rates) / len(rates) for tool, rates in tools.items()}

        self._create_grouped_bar_chart(
            output_dir / "detection_by_category.png", "Detection Rate by Category", "Category", "Detection Rate", category_data
        )

        # 3. Precision vs Recall Scatter
        self._create_scatter_plot(
            output_dir / "precision_recall.png",
            "Precision vs Recall",
            "Recall",
            "Precision",
            {tool: (data["avg_recall"], data["avg_precision"]) for tool, data in comparison["summary"].items()},
        )

        logger.info(f"Visualizations saved to {output_dir}")

    def _create_bar_chart(self, output_path: Path, title: str, xlabel: str, ylabel: str, data: Dict[str, float]) -> None:
        """Create a simple bar chart."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        tools = list(data.keys())
        values = list(data.values())

        bars = ax.bar(tools, values)

        # Color bars
        colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12"]
        for bar, color in zip(bars, colors):
            bar.set_color(color)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_ylim(0, 1)

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def _create_grouped_bar_chart(
        self, output_path: Path, title: str, xlabel: str, ylabel: str, data: Dict[str, Dict[str, float]]
    ) -> None:
        """Create a grouped bar chart."""
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(12, 6))

        categories = list(data.keys())
        tools = list(next(iter(data.values())).keys())

        x = np.arange(len(categories))
        width = 0.35

        for i, tool in enumerate(tools):
            values = [data[cat].get(tool, 0) for cat in categories]
            ax.bar(x + i * width, values, width, label=tool)

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x + width / 2)
        ax.set_xticklabels(categories, rotation=45, ha="right")
        ax.legend()
        ax.set_ylim(0, 1)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def _create_scatter_plot(
        self, output_path: Path, title: str, xlabel: str, ylabel: str, data: Dict[str, Tuple[float, float]]
    ) -> None:
        """Create a scatter plot."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 8))

        colors = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12"]

        for (tool, (x, y)), color in zip(data.items(), colors):
            ax.scatter(x, y, s=200, label=tool, color=color, alpha=0.7)
            ax.annotate(tool, (x, y), xytext=(5, 5), textcoords="offset points")

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze competitor benchmark results")
    parser.add_argument("--mode", choices=["simulate", "compare", "visualize", "badge"], required=True, help="Analysis mode")
    parser.add_argument("--competitor", choices=["pentestgpt", "autopentest"], help="Competitor name (for simulate mode)")
    parser.add_argument("--test-case", help="Test case ID (for simulate mode)")
    parser.add_argument("--results-dir", type=Path, help="Directory containing result files")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--output-dir", type=Path, help="Output directory for visualizations")
    parser.add_argument("--template", type=Path, help="Report template file")

    args = parser.parse_args()

    if args.mode == "simulate":
        if not args.competitor or not args.test_case:
            parser.error("simulate mode requires --competitor and --test-case")

        # Load test case
        test_case_path = Path(f"benchmarks/scenarios/test_cases/{args.test_case}.yml")
        if not test_case_path.exists():
            # Create dummy test case for testing
            test_case = BenchmarkTestCase(
                id=args.test_case,
                name=args.test_case,
                description="Simulated test case",
                category=TestCategory.VULNERABILITY_SCAN,
                target_url="http://localhost:8080",
                expected_findings=[],
            )
        else:
            test_case = load_test_case(test_case_path)

        # Simulate
        simulator = CompetitorSimulator(args.competitor)
        result = simulator.simulate_test(test_case)

        # Output
        output = {
            "tool_name": result.tool_name,
            "test_case_id": result.test_case_id,
            "status": result.status.value,
            "detection_rate": result.detection_rate,
            "precision": result.precision,
            "recall": result.recall,
            "f1_score": result.f1_score,
            "duration_seconds": result.duration_seconds,
            "findings_count": len(result.findings),
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2)
            logger.info(f"Result saved to {args.output}")
        else:
            print(json.dumps(output, indent=2))

    elif args.mode == "compare":
        if not args.results_dir:
            parser.error("compare mode requires --results-dir")

        analyzer = ComparisonAnalyzer(args.results_dir)
        analyzer.load_results()

        output_path = args.output or Path("comparison_report.md")
        _ = analyzer.generate_markdown_report(template_path=args.template, output_path=output_path)

        print(f"Report generated: {output_path}")

    elif args.mode == "visualize":
        if not args.results_dir:
            parser.error("visualize mode requires --results-dir")

        analyzer = ComparisonAnalyzer(args.results_dir)
        analyzer.load_results()

        output_dir = args.output_dir or Path("benchmark_charts")
        analyzer.generate_visualizations(output_dir)

        print(f"Visualizations saved to {output_dir}")

    elif args.mode == "badge":
        if not args.results_dir:
            parser.error("badge mode requires --results-dir")

        analyzer = ComparisonAnalyzer(args.results_dir)
        analyzer.load_results()
        comparison = analyzer.compare_tools()

        # Create badge status JSON
        badge_data = {
            "schemaVersion": 1,
            "label": "benchmark",
            "message": f"{comparison.get('winner', {}).get('tool', 'N/A')} winning",
            "color": "brightgreen",
        }

        output_path = args.output or Path("benchmark-badge.json")
        with open(output_path, "w") as f:
            json.dump(badge_data, f, indent=2)

        print(f"Badge data saved to {output_path}")


if __name__ == "__main__":
    main()
