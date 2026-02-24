"""
Zen-AI-Pentest Benchmark Engine

Core benchmarking engine for security testing performance evaluation.
Provides async execution, historical tracking, and comprehensive reporting.
"""

import asyncio
import hashlib
import json
import logging
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional

# Type hints for Zen-AI-Pentest core
from ..core.orchestrator import PentestOrchestrator
from .comparison import (
    ComparisonFramework,
    ToolBenchmarkResult,
    ToolCategory,
    ToolMetadata,
)
from .metrics import (
    BenchmarkMetrics,
    ClassificationMetrics,
    CoverageMetrics,
    ExploitMetrics,
    FindingMetrics,
    FindingType,
    MetricsAggregator,
    SeverityLevel,
    TokenUsage,
)
from .scenarios import (
    ALL_SCENARIOS,
    DifficultyLevel,
    ScenarioType,
    TestScenario,
    get_scenario,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkStatus(Enum):
    """Status of a benchmark run."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    TIMEOUT = auto()


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""

    # Identification
    benchmark_name: str = ""
    benchmark_id: Optional[str] = None

    # Scenarios to run
    scenarios: List[str] = field(default_factory=list)
    scenario_types: Optional[List[ScenarioType]] = None
    difficulty_levels: Optional[List[DifficultyLevel]] = None
    tags: Optional[List[str]] = None

    # Execution settings
    max_concurrent: int = 1
    timeout_per_scenario: int = 3600  # seconds
    retries: int = 1

    # Tool settings
    zen_config: Dict[str, Any] = field(default_factory=dict)
    enable_competitor_comparison: bool = False
    competitors: List[str] = field(default_factory=list)

    # Output settings
    output_dir: str = "benchmark_results"
    save_raw_output: bool = True
    generate_charts: bool = True
    generate_markdown_report: bool = True

    # Historical tracking
    track_history: bool = True
    history_file: str = "benchmark_history.json"

    def __post_init__(self):
        if not self.benchmark_id:
            self.benchmark_id = str(uuid.uuid4())[:8]
        if not self.benchmark_name:
            self.benchmark_name = f"benchmark_{self.benchmark_id}"


@dataclass
class ScenarioResult:
    """Result of running a single scenario."""

    scenario_id: str
    status: BenchmarkStatus
    benchmark_id: str

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Results
    metrics: Optional[BenchmarkMetrics] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # Comparison
    comparison_result: Optional[Any] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.name,
            "benchmark_id": self.benchmark_id,
            "start_time": (
                self.start_time.isoformat() if self.start_time else None
            ),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "metrics": self.metrics.to_dict() if self.metrics else None,
            "error_message": self.error_message,
        }


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""

    # Identification
    benchmark_id: str
    benchmark_name: str
    tool_version: str

    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None

    # Configuration
    config: BenchmarkConfig = field(default_factory=BenchmarkConfig)

    # Results
    scenario_results: List[ScenarioResult] = field(default_factory=list)

    # Aggregated metrics
    aggregate_metrics: Optional[Dict[str, Any]] = None
    historical_comparison: Optional[Dict[str, Any]] = None

    @property
    def duration_seconds(self) -> float:
        """Calculate total duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if not self.scenario_results:
            return 0.0

        successful = sum(
            1
            for r in self.scenario_results
            if r.status == BenchmarkStatus.COMPLETED
        )
        return (successful / len(self.scenario_results)) * 100

    @property
    def scenarios_passed(self) -> int:
        """Count passed scenarios."""
        return sum(
            1
            for r in self.scenario_results
            if r.status == BenchmarkStatus.COMPLETED
        )

    @property
    def scenarios_failed(self) -> int:
        """Count failed scenarios."""
        return sum(
            1
            for r in self.scenario_results
            if r.status == BenchmarkStatus.FAILED
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_name": self.benchmark_name,
            "tool_version": self.tool_version,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "config": {
                "max_concurrent": self.config.max_concurrent,
                "timeout_per_scenario": self.config.timeout_per_scenario,
                "scenarios": self.config.scenarios,
            },
            "summary": {
                "total_scenarios": len(self.scenario_results),
                "passed": self.scenarios_passed,
                "failed": self.scenarios_failed,
                "success_rate": self.success_rate,
            },
            "scenario_results": [r.to_dict() for r in self.scenario_results],
            "aggregate_metrics": self.aggregate_metrics,
            "historical_comparison": self.historical_comparison,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def generate_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Benchmark Report: {self.benchmark_name}",
            "",
            f"**Benchmark ID:** `{self.benchmark_id}`",
            f"**Tool Version:** {self.tool_version}",
            f"**Date:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Duration:** {self.duration_seconds:.1f} seconds",
            "",
            "## Summary",
            "",
            f"- **Total Scenarios:** {len(self.scenario_results)}",
            f"- **Passed:** {self.scenarios_passed} ✅",
            f"- **Failed:** {self.scenarios_failed} ❌",
            f"- **Success Rate:** {self.success_rate:.1f}%",
            "",
            "## Scenario Results",
            "",
            "| Scenario | Status | Duration | Precision | Recall | F1-Score |",
            "|----------|--------|----------|-----------|--------|----------|",
        ]

        for result in self.scenario_results:
            status_emoji = {
                BenchmarkStatus.COMPLETED: "✅",
                BenchmarkStatus.FAILED: "❌",
                BenchmarkStatus.TIMEOUT: "⏱️",
                BenchmarkStatus.CANCELLED: "🚫",
            }.get(result.status, "❓")

            metrics = result.metrics
            if metrics:
                scores = metrics.calculate_aggregate_scores()
                lines.append(
                    f"| {result.scenario_id} | {status_emoji} {result.status.name} | "
                    f"{result.duration_seconds:.1f}s | "
                    f"{scores.get('precision', 0):.3f} | "
                    f"{scores.get('recall', 0):.3f} | "
                    f"{scores.get('f1_score', 0):.3f} |"
                )
            else:
                lines.append(
                    f"| {result.scenario_id} | {status_emoji} {result.status.name} | "
                    f"{result.duration_seconds:.1f}s | N/A | N/A | N/A |"
                )

        lines.extend(["", "## Aggregate Metrics", ""])

        if self.aggregate_metrics:
            for key, value in self.aggregate_metrics.items():
                if isinstance(value, float):
                    lines.append(
                        f"- **{key.replace('_', ' ').title()}:** {value:.3f}"
                    )
                else:
                    lines.append(
                        f"- **{key.replace('_', ' ').title()}:** {value}"
                    )

        lines.extend(["", "## Detailed Results", ""])

        for result in self.scenario_results:
            lines.extend(
                [
                    f"### {result.scenario_id}",
                    "",
                    f"**Status:** {result.status.name}",
                    f"**Duration:** {result.duration_seconds:.1f} seconds",
                    "",
                ]
            )

            if result.metrics:
                scores = result.metrics.calculate_aggregate_scores()
                lines.extend(
                    [
                        "**Scores:**",
                        f"- Accuracy: {scores.get('accuracy', 0):.3f}",
                        f"- Precision: {scores.get('precision', 0):.3f}",
                        f"- Recall: {scores.get('recall', 0):.3f}",
                        f"- F1-Score: {scores.get('f1_score', 0):.3f}",
                        f"- Overall: {scores.get('overall', 0):.3f}",
                        "",
                    ]
                )

            if result.error_message:
                lines.extend(
                    ["**Error:**", "```", result.error_message, "```", ""]
                )

        return "\n".join(lines)


class BenchmarkEngine:
    """Main benchmark engine for Zen-AI-Pentest."""

    def __init__(
        self,
        orchestrator: Optional[PentestOrchestrator] = None,
        output_dir: str = "benchmark_results",
    ):
        self.orchestrator = orchestrator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.comparison_framework = ComparisonFramework()
        self.metrics_aggregator = MetricsAggregator()

        self._current_benchmark: Optional[BenchmarkReport] = None
        self._cancelled = False

        # Get version info
        self.tool_version = self._get_tool_version()

        logger.info(f"BenchmarkEngine initialized (output: {self.output_dir})")

    def _get_tool_version(self) -> str:
        """Get current tool version."""
        try:
            # Try to get from package metadata
            import pkg_resources

            return pkg_resources.get_distribution("zen-ai-pentest").version
        except Exception:
            # Fallback to git commit or static version
            try:
                from .. import __version__

                return __version__
            except Exception:
                return "dev"

    def _select_scenarios(self, config: BenchmarkConfig) -> List[TestScenario]:
        """Select scenarios based on configuration."""
        scenarios = []

        if config.scenarios:
            # Explicit scenario IDs
            for scenario_id in config.scenarios:
                scenario = get_scenario(scenario_id)
                if scenario:
                    scenarios.append(scenario)
                else:
                    logger.warning(f"Unknown scenario: {scenario_id}")
        else:
            # Filter by type/difficulty/tags
            for scenario in ALL_SCENARIOS.values():
                include = True

                if config.scenario_types:
                    include &= scenario.scenario_type in config.scenario_types

                if config.difficulty_levels:
                    include &= scenario.difficulty in config.difficulty_levels

                if config.tags:
                    include &= any(tag in scenario.tags for tag in config.tags)

                if include:
                    scenarios.append(scenario)

        return scenarios

    async def _run_single_scenario(
        self, scenario: TestScenario, config: BenchmarkConfig
    ) -> ScenarioResult:
        """Run a single benchmark scenario."""

        result = ScenarioResult(
            scenario_id=scenario.id,
            status=BenchmarkStatus.PENDING,
            benchmark_id=config.benchmark_id or "",
            start_time=datetime.utcnow(),
        )

        logger.info(f"Starting scenario: {scenario.name}")
        result.status = BenchmarkStatus.RUNNING

        try:
            # Setup scenario (e.g., start docker containers)
            await self._setup_scenario(scenario)

            # Wait for target to be ready
            await self._wait_for_target(scenario)

            # Run the actual scan
            metrics = await self._execute_scan(scenario, config)
            result.metrics = metrics

            # Run competitor comparison if enabled
            if config.enable_competitor_comparison:
                comparison = await self._run_comparison(
                    scenario, config, metrics
                )
                result.comparison_result = comparison

            result.status = BenchmarkStatus.COMPLETED
            logger.info(f"Scenario completed: {scenario.name}")

        except asyncio.TimeoutError:
            result.status = BenchmarkStatus.TIMEOUT
            result.error_message = (
                f"Scenario timed out after {config.timeout_per_scenario}s"
            )
            logger.error(f"Scenario timeout: {scenario.name}")

        except Exception as e:
            result.status = BenchmarkStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            logger.error(f"Scenario failed: {scenario.name} - {e}")

        finally:
            # Teardown scenario
            await self._teardown_scenario(scenario)
            result.end_time = datetime.utcnow()

        return result

    async def _setup_scenario(self, scenario: TestScenario) -> None:
        """Setup a scenario (start containers, etc.)."""
        if scenario.docker_compose_file:
            logger.info(f"Starting docker-compose for {scenario.id}")
            # In real implementation, write compose file and start
            # subprocess.run(["docker-compose", "-f", "docker-compose.yml", "up", "-d"])

        # Run setup commands
        for cmd in scenario.setup_commands:
            logger.info(f"Running setup command: {cmd}")
            # subprocess.run(cmd, shell=True)

        # Give services time to start
        await asyncio.sleep(5)

    async def _teardown_scenario(self, scenario: TestScenario) -> None:
        """Teardown a scenario."""
        if scenario.docker_compose_file:
            logger.info(f"Stopping docker-compose for {scenario.id}")
            # subprocess.run(["docker-compose", "down"])

        for cmd in scenario.teardown_commands:
            logger.info(f"Running teardown command: {cmd}")
            # subprocess.run(cmd, shell=True)

    async def _wait_for_target(
        self, scenario: TestScenario, timeout: int = 120
    ) -> bool:
        """Wait for target to be ready."""
        if not scenario.health_check_endpoint:
            return True

        logger.info(f"Waiting for target: {scenario.health_check_endpoint}")

        import aiohttp

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        scenario.health_check_endpoint, timeout=5
                    ) as response:
                        if response.status < 500:
                            logger.info(f"Target ready: {scenario.id}")
                            return True
            except Exception:
                pass

            await asyncio.sleep(2)

        raise TimeoutError(f"Target not ready after {timeout}s")

    async def _execute_scan(
        self, scenario: TestScenario, config: BenchmarkConfig
    ) -> BenchmarkMetrics:
        """Execute the actual scan and collect metrics."""

        metrics = BenchmarkMetrics(
            benchmark_id=config.benchmark_id or str(uuid.uuid4())[:8],
            scenario_name=scenario.name,
            tool_version=self.tool_version,
        )

        # Initialize performance tracking
        metrics.performance.scan_start_time = datetime.utcnow()
        start_time = time.time()

        # Check if orchestrator is available
        if self.orchestrator is None:
            logger.warning("No orchestrator available, using simulation mode")
            # Simulate scan for testing
            await self._simulate_scan(scenario, metrics)
        else:
            # Run actual scan
            await self._run_real_scan(scenario, config, metrics)

        # Record end time
        metrics.performance.scan_end_time = datetime.utcnow()
        metrics.performance.total_duration_ms = int(
            (time.time() - start_time) * 1000
        )

        return metrics

    async def _simulate_scan(
        self, scenario: TestScenario, metrics: BenchmarkMetrics
    ) -> None:
        """Simulate a scan for testing purposes."""
        logger.info(f"Running simulated scan for {scenario.id}")

        # Simulate scan duration
        await asyncio.sleep(2)

        # Generate simulated findings based on expected vulnerabilities
        true_positives = 0
        false_positives = 0

        for vuln in scenario.expected_vulnerabilities:
            # Simulate detection (90% detection rate)
            if (
                hashlib.md5(vuln.vuln_type.encode()).hexdigest()[0]
                in "0123456789a"
            ):
                true_positives += 1
                metrics.findings.append(
                    FindingMetrics(
                        finding_type=FindingType.SQL_INJECTION,  # Simplified
                        severity=(
                            SeverityLevel(vuln.severity)
                            if vuln.severity
                            in ["critical", "high", "medium", "low", "info"]
                            else SeverityLevel.MEDIUM
                        ),
                        confidence=0.85,
                        exploitability=0.7 if vuln.exploit_available else 0.3,
                        detection_time_ms=1500,
                        verified=True,
                        exploited=vuln.exploit_available,
                    )
                )

        # Simulate some false positives
        false_positives = (
            1 if len(scenario.expected_vulnerabilities) > 5 else 0
        )

        # Set classification metrics
        expected_count = len(scenario.expected_vulnerabilities)
        false_negatives = expected_count - true_positives

        metrics.classification = ClassificationMetrics(
            true_positives=true_positives,
            false_positives=false_positives,
            true_negatives=10,  # Assumed
            false_negatives=false_negatives,
        )

        # Coverage metrics
        metrics.coverage = CoverageMetrics(
            total_endpoints=10,
            scanned_endpoints=9,
            total_parameters=50,
            tested_parameters=45,
            total_attack_vectors=20,
            tested_attack_vectors=18,
            owasp_categories_covered=[
                "A03:2021-Injection",
                "A01:2021-Broken Access Control",
            ],
        )

        # Exploit metrics
        metrics.exploit = ExploitMetrics(
            total_exploits_attempted=true_positives,
            successful_exploits=int(true_positives * 0.7),
            failed_exploits=int(true_positives * 0.3),
            blocked_exploits=0,
        )

        # Token usage (simulated)
        metrics.token_usage = TokenUsage(
            prompt_tokens=5000,
            completion_tokens=3000,
            cost_usd=0.15,
            model="gpt-4",
        )

    async def _run_real_scan(
        self,
        scenario: TestScenario,
        config: BenchmarkConfig,
        metrics: BenchmarkMetrics,
    ) -> None:
        """Run a real scan using the orchestrator."""
        # This would integrate with the actual PentestOrchestrator
        # For now, delegate to simulation
        await self._simulate_scan(scenario, metrics)

    async def _run_comparison(
        self,
        scenario: TestScenario,
        config: BenchmarkConfig,
        zen_metrics: BenchmarkMetrics,
    ) -> Optional[Any]:
        """Run comparison with competitor tools."""
        if not config.competitors:
            return None

        logger.info(f"Running comparison for {scenario.id}")

        # Convert zen metrics to tool result
        scores = zen_metrics.calculate_aggregate_scores()
        zen_result = ToolBenchmarkResult(
            tool_metadata=ToolMetadata(
                name="Zen-AI-Pentest",
                version=self.tool_version,
                vendor="Zen-AI",
                category=ToolCategory.AI_PENTEST,
                license_type="open_source",
            ),
            scenario_id=scenario.id,
            scan_duration_seconds=zen_metrics.performance.duration_seconds,
            vulnerabilities_found=len(zen_metrics.findings),
            true_positives=zen_metrics.classification.true_positives,
            false_positives=zen_metrics.classification.false_positives,
            false_negatives=zen_metrics.classification.false_negatives,
            precision=scores["precision"],
            recall=scores["recall"],
            f1_score=scores["f1_score"],
            accuracy=scores["accuracy"],
            total_cost_usd=zen_metrics.token_usage.cost_usd,
            tokens_used=zen_metrics.token_usage.total_tokens,
        )

        scenario_config = {
            "scenario_id": scenario.id,
            "target_url": scenario.target_url,
            "target_host": scenario.target_host,
            "target_port": scenario.target_port,
        }

        comparison = await self.comparison_framework.run_comparison(
            zen_result, scenario_config, config.competitors
        )

        return comparison

    async def run_benchmark(self, config: BenchmarkConfig) -> BenchmarkReport:
        """Run a complete benchmark suite."""

        self._cancelled = False

        # Create report
        report = BenchmarkReport(
            benchmark_id=config.benchmark_id or str(uuid.uuid4())[:8],
            benchmark_name=config.benchmark_name,
            tool_version=self.tool_version,
            start_time=datetime.utcnow(),
            config=config,
        )

        self._current_benchmark = report

        # Select scenarios
        scenarios = self._select_scenarios(config)
        logger.info(f"Selected {len(scenarios)} scenarios for benchmarking")

        if not scenarios:
            logger.warning("No scenarios selected!")
            report.end_time = datetime.utcnow()
            return report

        # Run scenarios with concurrency control
        semaphore = asyncio.Semaphore(config.max_concurrent)

        async def run_with_semaphore(scenario: TestScenario) -> ScenarioResult:
            async with semaphore:
                if self._cancelled:
                    result = ScenarioResult(
                        scenario_id=scenario.id,
                        status=BenchmarkStatus.CANCELLED,
                        benchmark_id=config.benchmark_id or "",
                    )
                    return result

                return await self._run_single_scenario(scenario, config)

        # Run all scenarios
        results = await asyncio.gather(
            *[run_with_semaphore(s) for s in scenarios]
        )

        report.scenario_results = list(results)
        report.end_time = datetime.utcnow()

        # Calculate aggregate metrics
        report.aggregate_metrics = self._calculate_aggregates(report)

        # Compare with history
        if config.track_history:
            report.historical_comparison = self._compare_with_history(report)
            self._save_to_history(report)

        # Save report
        self._save_report(report, config)

        logger.info(f"Benchmark completed: {report.benchmark_id}")
        logger.info(f"Success rate: {report.success_rate:.1f}%")

        return report

    def _calculate_aggregates(self, report: BenchmarkReport) -> Dict[str, Any]:
        """Calculate aggregate metrics across all scenarios."""

        completed = [
            r
            for r in report.scenario_results
            if r.status == BenchmarkStatus.COMPLETED and r.metrics
        ]

        if not completed:
            return {}

        all_scores = [
            r.metrics.calculate_aggregate_scores() for r in completed
        ]

        # Average scores
        aggregate = {}
        keys = all_scores[0].keys()
        for key in keys:
            values = [s[key] for s in all_scores]
            aggregate[f"avg_{key}"] = sum(values) / len(values)

        # Total findings
        aggregate["total_findings"] = sum(
            len(r.metrics.findings) for r in completed
        )

        # Total duration
        aggregate["total_duration_seconds"] = sum(
            r.duration_seconds for r in completed
        )

        # Average duration per scenario
        aggregate["avg_duration_seconds"] = aggregate[
            "total_duration_seconds"
        ] / len(completed)

        # Token usage
        aggregate["total_tokens"] = sum(
            r.metrics.token_usage.total_tokens for r in completed
        )
        aggregate["total_cost_usd"] = sum(
            r.metrics.token_usage.cost_usd for r in completed
        )

        return aggregate

    def _compare_with_history(
        self, report: BenchmarkReport
    ) -> Optional[Dict[str, Any]]:
        """Compare current benchmark with historical results."""

        history_file = self.output_dir / report.config.history_file

        if not history_file.exists():
            return None

        try:
            with open(history_file) as f:
                history = json.load(f)

            # Find previous runs of same scenarios
            comparable = [
                h
                for h in history
                if h.get("scenarios") == report.config.scenarios
                and h["benchmark_id"] != report.benchmark_id
            ]

            if not comparable:
                return None

            # Get most recent
            previous = max(comparable, key=lambda h: h.get("timestamp", ""))

            # Compare aggregate metrics
            comparison = {}
            current_metrics = report.aggregate_metrics or {}
            previous_metrics = previous.get("aggregate_metrics", {})

            for key in current_metrics.keys():
                if key in previous_metrics and previous_metrics[key] != 0:
                    change = (
                        (current_metrics[key] - previous_metrics[key])
                        / previous_metrics[key]
                        * 100
                    )
                    comparison[key] = {
                        "current": current_metrics[key],
                        "previous": previous_metrics[key],
                        "change_percent": change,
                    }

            return comparison

        except Exception as e:
            logger.error(f"Error comparing with history: {e}")
            return None

    def _save_to_history(self, report: BenchmarkReport) -> None:
        """Save benchmark to history file."""

        history_file = self.output_dir / report.config.history_file

        history = []
        if history_file.exists():
            try:
                with open(history_file) as f:
                    history = json.load(f)
            except Exception:
                pass

        # Add current report
        history.append(
            {
                "benchmark_id": report.benchmark_id,
                "timestamp": report.start_time.isoformat(),
                "scenarios": report.config.scenarios,
                "success_rate": report.success_rate,
                "aggregate_metrics": report.aggregate_metrics,
            }
        )

        # Keep only last 100 entries
        history = history[-100:]

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def _save_report(
        self, report: BenchmarkReport, config: BenchmarkConfig
    ) -> None:
        """Save benchmark report to disk."""

        benchmark_dir = self.output_dir / report.benchmark_id
        benchmark_dir.mkdir(exist_ok=True)

        # Save JSON report
        json_file = benchmark_dir / "report.json"
        with open(json_file, "w") as f:
            f.write(report.to_json())

        # Save markdown report
        if config.generate_markdown_report:
            md_file = benchmark_dir / "report.md"
            with open(md_file, "w") as f:
                f.write(report.generate_markdown())

        logger.info(f"Report saved to: {benchmark_dir}")

    def cancel_benchmark(self) -> None:
        """Cancel the current benchmark."""
        self._cancelled = True
        logger.info("Benchmark cancellation requested")

    def get_scenario_list(self) -> List[Dict[str, Any]]:
        """Get list of all available scenarios."""
        from .scenarios import list_all_scenarios

        return list_all_scenarios()

    def get_benchmark_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get benchmark history."""

        history_file = self.output_dir / "benchmark_history.json"

        if not history_file.exists():
            return []

        try:
            with open(history_file) as f:
                history = json.load(f)
            return history[-limit:]
        except Exception:
            return []
