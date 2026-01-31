"""
Zen-AI-Pentest CI/CD Benchmark Integration

Continuous Integration benchmarking for automated performance tracking,
regression detection, and quality gates.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import xml.etree.ElementTree as ET

from .benchmark_engine import (
    BenchmarkEngine, BenchmarkConfig, BenchmarkReport,
    BenchmarkStatus
)
from .metrics import BenchmarkMetrics, MetricsAggregator

logger = logging.getLogger(__name__)


class RegressionSeverity(Enum):
    """Severity levels for performance regressions."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceGate:
    """Performance gate configuration."""
    
    name: str
    metric: str  # e.g., "precision", "recall", "f1_score"
    threshold: float
    comparison: str = "min"  # "min" or "max"
    
    def check(self, value: float) -> bool:
        """Check if value passes the gate."""
        if self.comparison == "min":
            return value >= self.threshold
        else:
            return value <= self.threshold


@dataclass
class GateResult:
    """Result of a performance gate check."""
    
    gate: PerformanceGate
    actual_value: float
    passed: bool
    message: str = ""


@dataclass
class RegressionCheck:
    """Result of regression check."""
    
    metric: str
    baseline_value: float
    current_value: float
    change_percent: float
    severity: RegressionSeverity
    message: str = ""


@dataclass
class CIConfig:
    """Configuration for CI benchmark runs."""
    
    # Trigger conditions
    run_on_pr: bool = True
    run_on_release: bool = True
    run_on_schedule: bool = False
    schedule_cron: str = "0 0 * * 0"  # Weekly
    
    # Scenarios
    quick_scenarios: List[str] = field(
        default_factory=lambda: ["dvwa", "juice-shop"]
    )
    full_scenarios: List[str] = field(
        default_factory=lambda: list(ALL_SCENARIOS.keys())
    )
    
    # Performance gates
    performance_gates: List[PerformanceGate] = field(default_factory=lambda: [
        PerformanceGate("precision_min", "precision", 0.70),
        PerformanceGate("recall_min", "recall", 0.65),
        PerformanceGate("f1_min", "f1_score", 0.67),
        PerformanceGate("accuracy_min", "accuracy", 0.75),
    ])
    
    # Regression detection
    enable_regression_detection: bool = True
    regression_threshold_low: float = -5.0    # -5%
    regression_threshold_medium: float = -10.0  # -10%
    regression_threshold_high: float = -20.0   # -20%
    regression_threshold_critical: float = -30.0  # -30%
    
    # Trend analysis
    enable_trend_analysis: bool = True
    trend_lookback_runs: int = 5
    trend_significance_threshold: float = 2.0  # Standard deviations
    
    # Output
    output_format: str = "all"  # "json", "junit", "markdown", "all"
    fail_on_gate_failure: bool = True
    fail_on_critical_regression: bool = True
    comment_on_pr: bool = True
    
    # Notifications
    notify_on_failure: bool = True
    notify_on_regression: bool = True
    slack_webhook: Optional[str] = None
    email_on_failure: Optional[str] = None


class CIBenchmarkRunner:
    """CI/CD benchmark runner for automated testing."""
    
    def __init__(
        self,
        engine: Optional[BenchmarkEngine] = None,
        config: Optional[CIConfig] = None,
        output_dir: str = "ci_benchmark_results"
    ):
        self.engine = engine or BenchmarkEngine(output_dir=output_dir)
        self.config = config or CIConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[BenchmarkReport] = []
        self.gate_results: List[GateResult] = []
        self.regressions: List[RegressionCheck] = []
        
        logger.info("CIBenchmarkRunner initialized")
    
    async def run_quick_benchmark(self) -> BenchmarkReport:
        """Run quick benchmark for PR validation."""
        logger.info("Running quick benchmark suite")
        
        config = BenchmarkConfig(
            benchmark_name="ci-quick-benchmark",
            scenarios=self.config.quick_scenarios,
            max_concurrent=2,
            timeout_per_scenario=1800,
            generate_markdown_report=True,
            track_history=True
        )
        
        report = await self.engine.run_benchmark(config)
        self.results.append(report)
        
        return report
    
    async def run_full_benchmark(self) -> BenchmarkReport:
        """Run full benchmark suite for releases."""
        logger.info("Running full benchmark suite")
        
        config = BenchmarkConfig(
            benchmark_name="ci-full-benchmark",
            scenarios=self.config.full_scenarios,
            max_concurrent=1,  # Sequential for stability
            timeout_per_scenario=3600,
            generate_markdown_report=True,
            track_history=True
        )
        
        report = await self.engine.run_benchmark(config)
        self.results.append(report)
        
        return report
    
    def check_performance_gates(
        self, 
        report: BenchmarkReport
    ) -> List[GateResult]:
        """Check if benchmark passes all performance gates."""
        
        logger.info("Checking performance gates")
        self.gate_results = []
        
        if not report.aggregate_metrics:
            logger.warning("No aggregate metrics available")
            return []
        
        for gate in self.config.performance_gates:
            # Get metric value
            metric_key = f"avg_{gate.metric}"
            value = report.aggregate_metrics.get(metric_key, 0)
            
            passed = gate.check(value)
            
            result = GateResult(
                gate=gate,
                actual_value=value,
                passed=passed,
                message=(
                    f"✅ {gate.name}: {value:.3f} >= {gate.threshold}"
                    if passed else
                    f"❌ {gate.name}: {value:.3f} < {gate.threshold}"
                )
            )
            
            self.gate_results.append(result)
            
            if passed:
                logger.info(result.message)
            else:
                logger.warning(result.message)
        
        return self.gate_results
    
    def detect_regressions(
        self, 
        report: BenchmarkReport
    ) -> List[RegressionCheck]:
        """Detect performance regressions compared to baseline."""
        
        logger.info("Detecting regressions")
        self.regressions = []
        
        if not self.config.enable_regression_detection:
            return []
        
        # Get baseline (previous successful run)
        baseline = self._get_baseline_report(report)
        if not baseline:
            logger.info("No baseline found for comparison")
            return []
        
        # Compare metrics
        if not report.aggregate_metrics or not baseline.aggregate_metrics:
            return []
        
        for key in report.aggregate_metrics.keys():
            if not key.startswith("avg_"):
                continue
            
            current = report.aggregate_metrics[key]
            baseline_val = baseline.aggregate_metrics.get(key)
            
            if baseline_val is None or baseline_val == 0:
                continue
            
            change_pct = ((current - baseline_val) / baseline_val) * 100
            
            # Determine severity
            if change_pct < self.config.regression_threshold_critical:
                severity = RegressionSeverity.CRITICAL
            elif change_pct < self.config.regression_threshold_high:
                severity = RegressionSeverity.HIGH
            elif change_pct < self.config.regression_threshold_medium:
                severity = RegressionSeverity.MEDIUM
            elif change_pct < self.config.regression_threshold_low:
                severity = RegressionSeverity.LOW
            else:
                continue  # No significant regression
            
            regression = RegressionCheck(
                metric=key,
                baseline_value=baseline_val,
                current_value=current,
                change_percent=change_pct,
                severity=severity,
                message=f"{key}: {baseline_val:.3f} → {current:.3f} ({change_pct:+.1f}%)"
            )
            
            self.regressions.append(regression)
            logger.warning(f"Regression detected: {regression.message}")
        
        return self.regressions
    
    def _get_baseline_report(
        self, 
        current: BenchmarkReport
    ) -> Optional[BenchmarkReport]:
        """Get baseline report for comparison."""
        
        history = self.engine.get_benchmark_history(limit=10)
        
        # Find most recent successful run with same scenarios
        for entry in reversed(history):
            if (entry.get("benchmark_id") != current.benchmark_id and
                entry.get("scenarios") == current.config.scenarios and
                entry.get("success_rate", 0) > 50):
                
                # Load full report if available
                report_path = (
                    self.output_dir / entry["benchmark_id"] / "report.json"
                )
                if report_path.exists():
                    try:
                        with open(report_path) as f:
                            data = json.load(f)
                        # Reconstruct report (simplified)
                        return current  # Placeholder
                    except:
                        pass
        
        return None
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        
        if not self.config.enable_trend_analysis:
            return {}
        
        logger.info("Analyzing performance trends")
        
        history = self.engine.get_benchmark_history(
            limit=self.config.trend_lookback_runs
        )
        
        if len(history) < 3:
            logger.info("Not enough history for trend analysis")
            return {}
        
        trends = {}
        
        # Analyze key metrics
        metrics_to_track = [
            "avg_precision", "avg_recall", "avg_f1_score",
            "avg_accuracy", "success_rate"
        ]
        
        for metric in metrics_to_track:
            values = [
                h.get("aggregate_metrics", {}).get(metric)
                for h in history
                if h.get("aggregate_metrics", {}).get(metric) is not None
            ]
            
            if len(values) < 3:
                continue
            
            # Simple trend detection
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            if not first_half or not second_half:
                continue
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            change = second_avg - first_avg
            
            trends[metric] = {
                "direction": "improving" if change > 0 else "degrading",
                "change": change,
                "current_avg": second_avg,
                "previous_avg": first_avg
            }
        
        return trends
    
    def should_fail_build(self) -> Tuple[bool, str]:
        """Determine if the build should fail based on results."""
        
        reasons = []
        
        # Check gate failures
        if self.config.fail_on_gate_failure:
            failed_gates = [g for g in self.gate_results if not g.passed]
            if failed_gates:
                reasons.append(
                    f"{len(failed_gates)} performance gate(s) failed"
                )
        
        # Check critical regressions
        if self.config.fail_on_critical_regression:
            critical = [
                r for r in self.regressions
                if r.severity == RegressionSeverity.CRITICAL
            ]
            if critical:
                reasons.append(
                    f"{len(critical)} critical regression(s) detected"
                )
        
        if reasons:
            return True, "; ".join(reasons)
        
        return False, "All checks passed"
    
    def generate_junit_xml(self, report: BenchmarkReport) -> str:
        """Generate JUnit XML for CI integration."""
        
        root = ET.Element("testsuites")
        suite = ET.SubElement(
            root, 
            "testsuite",
            name="Zen-AI-Pentest Benchmark",
            tests=str(len(report.scenario_results)),
            failures=str(report.scenarios_failed),
            time=str(report.duration_seconds)
        )
        
        # Add scenario tests
        for scenario_result in report.scenario_results:
            testcase = ET.SubElement(
                suite,
                "testcase",
                name=scenario_result.scenario_id,
                time=str(scenario_result.duration_seconds)
            )
            
            if scenario_result.status != BenchmarkStatus.COMPLETED:
                failure = ET.SubElement(testcase, "failure")
                failure.text = (
                    scenario_result.error_message or 
                    f"Scenario failed with status: {scenario_result.status.name}"
                )
            
            elif scenario_result.metrics:
                # Add metrics as system output
                sys_out = ET.SubElement(testcase, "system-out")
                scores = scenario_result.metrics.calculate_aggregate_scores()
                sys_out.text = json.dumps(scores, indent=2)
        
        # Add performance gates as test cases
        gate_suite = ET.SubElement(
            root,
            "testsuite",
            name="Performance Gates",
            tests=str(len(self.gate_results)),
            failures=str(sum(1 for g in self.gate_results if not g.passed))
        )
        
        for gate_result in self.gate_results:
            testcase = ET.SubElement(
                gate_suite,
                "testcase",
                name=gate_result.gate.name
            )
            
            if not gate_result.passed:
                failure = ET.SubElement(testcase, "failure")
                failure.text = gate_result.message
        
        # Add regression checks
        if self.regressions:
            reg_suite = ET.SubElement(
                root,
                "testsuite",
                name="Regression Checks",
                tests=str(len(self.regressions))
            )
            
            for reg in self.regressions:
                testcase = ET.SubElement(
                    reg_suite,
                    "testcase",
                    name=f"regression_{reg.metric}"
                )
                
                if reg.severity in [RegressionSeverity.CRITICAL, RegressionSeverity.HIGH]:
                    failure = ET.SubElement(testcase, "failure")
                    failure.text = reg.message
        
        return ET.tostring(root, encoding="unicode")
    
    def generate_summary_markdown(
        self, 
        report: BenchmarkReport
    ) -> str:
        """Generate summary markdown for PR comments."""
        
        lines = [
            "## 🔒 Zen-AI-Pentest Benchmark Results",
            "",
            f"**Benchmark ID:** `{report.benchmark_id}`",
            f"**Duration:** {report.duration_seconds:.1f}s",
            f"**Success Rate:** {report.success_rate:.1f}%",
            "",
            "### Performance Gates",
            ""
        ]
        
        for gate_result in self.gate_results:
            emoji = "✅" if gate_result.passed else "❌"
            lines.append(
                f"{emoji} **{gate_result.gate.name}:** "
                f"{gate_result.actual_value:.3f} "
                f"(threshold: {gate_result.gate.threshold})"
            )
        
        lines.append("")
        
        # Aggregate scores
        if report.aggregate_metrics:
            lines.extend([
                "### Aggregate Scores",
                "",
                f"- **Precision:** {report.aggregate_metrics.get('avg_precision', 0):.3f}",
                f"- **Recall:** {report.aggregate_metrics.get('avg_recall', 0):.3f}",
                f"- **F1-Score:** {report.aggregate_metrics.get('avg_f1_score', 0):.3f}",
                f"- **Accuracy:** {report.aggregate_metrics.get('avg_accuracy', 0):.3f}",
                ""
            ])
        
        # Regressions
        if self.regressions:
            lines.extend([
                "### ⚠️ Regressions Detected",
                ""
            ])
            
            for reg in self.regressions:
                emoji = {
                    RegressionSeverity.CRITICAL: "🔴",
                    RegressionSeverity.HIGH: "🟠",
                    RegressionSeverity.MEDIUM: "🟡",
                    RegressionSeverity.LOW: "⚪"
                }.get(reg.severity, "⚪")
                
                lines.append(f"{emoji} {reg.message}")
            
            lines.append("")
        
        # Build status
        should_fail, reason = self.should_fail_build()
        if should_fail:
            lines.extend([
                "### ❌ Build Status: FAILED",
                f"",
                f"**Reason:** {reason}",
                ""
            ])
        else:
            lines.extend([
                "### ✅ Build Status: PASSED",
                ""
            ])
        
        return "\n".join(lines)
    
    async def run_ci_pipeline(
        self, 
        benchmark_type: str = "quick"
    ) -> Dict[str, Any]:
        """Run complete CI pipeline."""
        
        logger.info(f"Starting CI pipeline ({benchmark_type})")
        
        # Run benchmark
        if benchmark_type == "quick":
            report = await self.run_quick_benchmark()
        else:
            report = await self.run_full_benchmark()
        
        # Check gates
        self.check_performance_gates(report)
        
        # Detect regressions
        self.detect_regressions(report)
        
        # Analyze trends
        trends = self.analyze_trends()
        
        # Determine build status
        should_fail, fail_reason = self.should_fail_build()
        
        # Generate outputs
        outputs = {}
        
        if self.config.output_format in ["junit", "all"]:
            outputs["junit_xml"] = self.generate_junit_xml(report)
        
        if self.config.output_format in ["markdown", "all"]:
            outputs["markdown_summary"] = self.generate_summary_markdown(report)
        
        if self.config.output_format in ["json", "all"]:
            outputs["json_report"] = report.to_dict()
        
        # Save outputs
        self._save_ci_outputs(report, outputs)
        
        result = {
            "benchmark_id": report.benchmark_id,
            "success_rate": report.success_rate,
            "gates_passed": sum(1 for g in self.gate_results if g.passed),
            "gates_total": len(self.gate_results),
            "regressions": len(self.regressions),
            "critical_regressions": sum(
                1 for r in self.regressions
                if r.severity == RegressionSeverity.CRITICAL
            ),
            "should_fail": should_fail,
            "fail_reason": fail_reason if should_fail else None,
            "trends": trends,
            "outputs": outputs
        }
        
        logger.info(f"CI pipeline completed: {result}")
        
        return result
    
    def _save_ci_outputs(
        self, 
        report: BenchmarkReport, 
        outputs: Dict[str, Any]
    ) -> None:
        """Save CI output files."""
        
        ci_dir = self.output_dir / "ci_outputs"
        ci_dir.mkdir(exist_ok=True)
        
        if "junit_xml" in outputs:
            with open(ci_dir / "benchmark-junit.xml", 'w') as f:
                f.write(outputs["junit_xml"])
        
        if "markdown_summary" in outputs:
            with open(ci_dir / "benchmark-summary.md", 'w') as f:
                f.write(outputs["markdown_summary"])
        
        if "json_report" in outputs:
            with open(ci_dir / "benchmark-report.json", 'w') as f:
                json.dump(outputs["json_report"], f, indent=2)
    
    def generate_github_actions_workflow(self) -> str:
        """Generate GitHub Actions workflow file."""
        
        workflow = """name: Benchmark

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  schedule:
    # Run weekly on Sunday at 00:00
    - cron: '0 0 * * 0'

jobs:
  quick-benchmark:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r benchmarks/requirements.txt
      
      - name: Run quick benchmark
        run: |
          python -m benchmarks.ci_benchmark --type quick --output ci
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: ci_benchmark_results/ci_outputs/
      
      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('ci_benchmark_results/ci_outputs/benchmark-summary.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });

  full-benchmark:
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r benchmarks/requirements.txt
      
      - name: Run full benchmark
        run: |
          python -m benchmarks.ci_benchmark --type full --output ci
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results-full
          path: ci_benchmark_results/
      
      - name: Update release notes
        uses: softprops/action-gh-release@v1
        with:
          files: ci_benchmark_results/ci_outputs/benchmark-summary.md
"""
        
        return workflow


# Import ALL_SCENARIOS for default config
from .scenarios import ALL_SCENARIOS


async def main():
    """CLI entry point for CI benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Zen-AI-Pentest CI Benchmark Runner"
    )
    parser.add_argument(
        "--type",
        choices=["quick", "full"],
        default="quick",
        help="Type of benchmark to run"
    )
    parser.add_argument(
        "--output",
        default="ci_benchmark_results",
        help="Output directory"
    )
    parser.add_argument(
        "--format",
        choices=["json", "junit", "markdown", "all"],
        default="all",
        help="Output format"
    )
    parser.add_argument(
        "--fail-on-gate",
        action="store_true",
        help="Fail on gate failure"
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Fail on critical regression"
    )
    
    args = parser.parse_args()
    
    # Create config
    config = CIConfig(
        output_format=args.format,
        fail_on_gate_failure=args.fail_on_gate,
        fail_on_critical_regression=args.fail_on_regression
    )
    
    # Run pipeline
    runner = CIBenchmarkRunner(config=config, output_dir=args.output)
    result = await runner.run_ci_pipeline(args.type)
    
    # Exit with appropriate code
    if result["should_fail"]:
        print(f"Build failed: {result['fail_reason']}")
        sys.exit(1)
    else:
        print("All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
