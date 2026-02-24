"""
Common Benchmarks Module

Shared test cases and comparison utilities for competitive benchmarking.
Provides standardized metrics, test validation, and result aggregation.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

logger = logging.getLogger(__name__)


class TestCategory(Enum):
    """Categories of security tests."""

    RECONNAISSANCE = "reconnaissance"
    VULNERABILITY_SCAN = "vulnerability_scan"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    API_SECURITY = "api_security"
    WEB_SECURITY = "web_security"
    NETWORK_SECURITY = "network_security"
    CLOUD_SECURITY = "cloud_security"
    CONTAINER_SECURITY = "container_security"
    REPORTING = "reporting"


class SeverityLevel(Enum):
    """Severity levels for vulnerabilities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestStatus(Enum):
    """Status of a test execution."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ExpectedFinding:
    """Expected vulnerability finding in a test case."""

    vuln_type: str
    severity: str
    location: str
    cwe_id: Optional[str] = None
    confidence: float = 0.9
    description: str = ""
    verification_method: str = ""


@dataclass
class BenchmarkTestCase:
    """Standardized test case for competitive benchmarking."""

    # Identification
    id: str
    name: str
    description: str
    category: TestCategory

    # Test configuration
    target_url: Optional[str] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    target_type: str = "web"  # web, api, network, container, cloud

    # Expected results
    expected_findings: List[ExpectedFinding] = field(default_factory=list)
    expected_duration_seconds: int = 300  # 5 minutes default

    # Test parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Success criteria
    min_detection_rate: float = 0.7  # 70% minimum detection rate
    max_false_positive_rate: float = 0.2  # 20% maximum FP rate
    max_duration_seconds: int = 600  # 10 minutes timeout

    # Metadata
    tags: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard, expert
    owasp_categories: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary."""
        return asdict(self)

    def to_yaml(self) -> str:
        """Convert test case to YAML string."""
        return yaml.dump(self.to_dict(), sort_keys=False, allow_unicode=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkTestCase":
        """Create test case from dictionary."""
        # Handle expected_findings conversion
        if "expected_findings" in data:
            data["expected_findings"] = [
                ExpectedFinding(**f) if isinstance(f, dict) else f
                for f in data["expected_findings"]
            ]
        return cls(**data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "BenchmarkTestCase":
        """Create test case from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    def get_hash(self) -> str:
        """Generate unique hash for this test case."""
        content = f"{self.id}:{self.name}:{self.version}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class BenchmarkSuite:
    """Collection of benchmark test cases."""

    name: str
    description: str
    version: str = "1.0"
    test_cases: List[BenchmarkTestCase] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    tags: List[str] = field(default_factory=list)

    def add_test_case(self, test_case: BenchmarkTestCase) -> None:
        """Add a test case to the suite."""
        self.test_cases.append(test_case)

    def get_by_category(
        self, category: TestCategory
    ) -> List[BenchmarkTestCase]:
        """Get test cases by category."""
        return [tc for tc in self.test_cases if tc.category == category]

    def get_by_difficulty(self, difficulty: str) -> List[BenchmarkTestCase]:
        """Get test cases by difficulty."""
        return [tc for tc in self.test_cases if tc.difficulty == difficulty]

    def to_dict(self) -> Dict[str, Any]:
        """Convert suite to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "tags": self.tags,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
        }

    def to_yaml(self) -> str:
        """Convert suite to YAML string."""
        return yaml.dump(self.to_dict(), sort_keys=False, allow_unicode=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkSuite":
        """Create suite from dictionary."""
        test_cases = [
            BenchmarkTestCase.from_dict(tc)
            for tc in data.pop("test_cases", [])
        ]
        return cls(test_cases=test_cases, **data)


@dataclass
class FindingResult:
    """Result of a single finding detection."""

    vuln_type: str
    severity: str
    location: str
    confidence: float
    description: str = ""
    verified: bool = False
    exploited: bool = False
    cwe_id: Optional[str] = None
    detection_time_ms: int = 0


@dataclass
class CompetitorResult:
    """Result from a competitor tool execution."""

    # Tool identification
    tool_name: str
    tool_version: str

    # Test identification
    test_case_id: str
    test_suite_id: str = ""

    # Execution info
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

    # Results
    findings: List[FindingResult] = field(default_factory=list)
    raw_output: Dict[str, Any] = field(default_factory=dict)

    # Metrics
    detection_rate: float = 0.0
    false_positive_rate: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0

    # Performance
    scan_duration_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Cost (for AI-based tools)
    tokens_used: int = 0
    cost_usd: float = 0.0
    api_calls: int = 0

    def calculate_metrics(
        self, expected_findings: List[ExpectedFinding]
    ) -> None:
        """Calculate comparison metrics against expected findings."""
        if not expected_findings:
            return

        # Build sets of finding types and locations
        expected_set = set(
            f"{f.vuln_type}:{f.location}" for f in expected_findings
        )
        found_set = set(f"{f.vuln_type}:{f.location}" for f in self.findings)

        # True positives: found and expected
        tp = len(expected_set & found_set)

        # False positives: found but not expected
        fp = len(found_set - expected_set)

        # False negatives: expected but not found
        fn = len(expected_set - found_set)

        # Calculate metrics
        total_expected = len(expected_findings)
        total_found = len(self.findings)

        self.detection_rate = tp / total_expected if total_expected > 0 else 0
        self.false_positive_rate = fp / total_found if total_found > 0 else 0
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        self.f1_score = (
            2 * (self.precision * self.recall) / (self.precision + self.recall)
            if (self.precision + self.recall) > 0
            else 0
        )

        # Accuracy: (TP + TN) / Total (simplified, assuming TN = 0 for security tests)
        self.accuracy = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return self.scan_duration_seconds


@dataclass
class ZenResult(CompetitorResult):
    """Result from Zen-AI-Pentest execution."""

    # Zen-specific metrics
    agents_used: List[str] = field(default_factory=list)
    tool_invocations: Dict[str, int] = field(default_factory=dict)
    llm_calls: int = 0
    exploitation_success_rate: float = 0.0
    report_quality_score: float = 0.0

    def __post_init__(self):
        """Set tool name after initialization."""
        if not self.tool_name:
            self.tool_name = "Zen-AI-Pentest"


@dataclass
class ComparisonMetrics:
    """Aggregated comparison metrics between tools."""

    test_case_id: str
    zen_result: Optional[ZenResult] = None
    competitor_results: List[CompetitorResult] = field(default_factory=list)

    # Winner determination
    winner: Optional[str] = None
    winner_reason: str = ""

    def add_competitor_result(self, result: CompetitorResult) -> None:
        """Add a competitor result."""
        self.competitor_results.append(result)

    def determine_winner(self, metric: str = "f1_score") -> Tuple[str, float]:
        """Determine winner based on specified metric."""
        all_results = []

        if self.zen_result:
            all_results.append(
                ("Zen-AI-Pentest", getattr(self.zen_result, metric, 0))
            )

        for comp in self.competitor_results:
            all_results.append((comp.tool_name, getattr(comp, metric, 0)))

        if not all_results:
            return ("none", 0.0)

        winner = max(all_results, key=lambda x: x[1])
        self.winner = winner[0]
        self.winner_reason = f"Highest {metric}: {winner[1]:.3f}"
        return winner

    def calculate_improvement(
        self, competitor_name: str, metric: str
    ) -> float:
        """Calculate improvement percentage over a competitor."""
        if not self.zen_result:
            return 0.0

        zen_value = getattr(self.zen_result, metric, 0)

        competitor = next(
            (
                c
                for c in self.competitor_results
                if c.tool_name == competitor_name
            ),
            None,
        )

        if not competitor:
            return 0.0

        comp_value = getattr(competitor, metric, 0)

        if comp_value == 0:
            return 100.0 if zen_value > 0 else 0.0

        return ((zen_value - comp_value) / comp_value) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_case_id": self.test_case_id,
            "zen_result": asdict(self.zen_result) if self.zen_result else None,
            "competitor_results": [asdict(r) for r in self.competitor_results],
            "winner": self.winner,
            "winner_reason": self.winner_reason,
        }


class TestScenarioValidator:
    """Validator for test scenarios and results."""

    @staticmethod
    def validate_test_case(
        test_case: BenchmarkTestCase,
    ) -> Tuple[bool, List[str]]:
        """Validate a test case configuration."""
        errors = []

        if not test_case.id:
            errors.append("Test case ID is required")

        if not test_case.name:
            errors.append("Test case name is required")

        if not test_case.target_url and not test_case.target_host:
            errors.append("Either target_url or target_host is required")

        if (
            test_case.min_detection_rate < 0
            or test_case.min_detection_rate > 1
        ):
            errors.append("min_detection_rate must be between 0 and 1")

        if (
            test_case.max_false_positive_rate < 0
            or test_case.max_false_positive_rate > 1
        ):
            errors.append("max_false_positive_rate must be between 0 and 1")

        return len(errors) == 0, errors

    @staticmethod
    def validate_result(
        result: CompetitorResult, test_case: BenchmarkTestCase
    ) -> Tuple[bool, List[str]]:
        """Validate a test result against expectations."""
        errors = []
        warnings = []

        # Check if scan completed
        if result.status != TestStatus.PASSED:
            errors.append(
                f"Test did not complete successfully: {result.status.value}"
            )

        # Check detection rate
        if result.detection_rate < test_case.min_detection_rate:
            errors.append(
                f"Detection rate {result.detection_rate:.2%} below minimum {test_case.min_detection_rate:.2%}"
            )

        # Check false positive rate
        if result.false_positive_rate > test_case.max_false_positive_rate:
            warnings.append(
                f"False positive rate {result.false_positive_rate:.2%} above maximum {test_case.max_false_positive_rate:.2%}"
            )

        # Check duration
        if result.duration_seconds > test_case.max_duration_seconds:
            warnings.append(
                f"Duration {result.duration_seconds:.1f}s exceeds maximum {test_case.max_duration_seconds}s"
            )

        return len(errors) == 0, errors + warnings


class CompetitorAdapter(ABC):
    """Abstract base class for competitor tool adapters."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the competitor tool is available."""
        pass

    @abstractmethod
    async def execute_test(
        self, test_case: BenchmarkTestCase, timeout_seconds: int = 600
    ) -> CompetitorResult:
        """Execute a test case and return results."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get tool capabilities."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata."""
        pass


def load_test_suite(yaml_path: Union[str, Path]) -> BenchmarkSuite:
    """Load a benchmark suite from YAML file."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return BenchmarkSuite.from_dict(data)


def save_test_suite(
    suite: BenchmarkSuite, yaml_path: Union[str, Path]
) -> None:
    """Save a benchmark suite to YAML file."""
    with open(yaml_path, "w") as f:
        f.write(suite.to_yaml())


def load_test_case(yaml_path: Union[str, Path]) -> BenchmarkTestCase:
    """Load a single test case from YAML file."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    return BenchmarkTestCase.from_dict(data)


def save_test_case(
    test_case: BenchmarkTestCase, yaml_path: Union[str, Path]
) -> None:
    """Save a single test case to YAML file."""
    with open(yaml_path, "w") as f:
        f.write(test_case.to_yaml())


# Standard scoring weights
SCORING_WEIGHTS = {
    "detection_rate": 0.30,
    "precision": 0.20,
    "recall": 0.15,
    "f1_score": 0.15,
    "speed": 0.10,  # Based on 1/duration
    "cost_efficiency": 0.10,  # Based on findings per dollar
}


def calculate_overall_score(result: CompetitorResult) -> float:
    """Calculate weighted overall score for a result."""
    score = (
        SCORING_WEIGHTS["detection_rate"] * result.detection_rate
        + SCORING_WEIGHTS["precision"] * result.precision
        + SCORING_WEIGHTS["recall"] * result.recall
        + SCORING_WEIGHTS["f1_score"] * result.f1_score
    )

    # Speed factor (normalized to 0-1, faster is better)
    # Assuming 600s is baseline, anything faster gets bonus
    speed_factor = min(1.0, 600 / max(result.duration_seconds, 1))
    score += SCORING_WEIGHTS["speed"] * speed_factor

    # Cost efficiency (for AI tools)
    if result.cost_usd > 0:
        findings_per_dollar = len(result.findings) / result.cost_usd
        cost_factor = min(
            1.0, findings_per_dollar / 100
        )  # 100 findings/$ is max
        score += SCORING_WEIGHTS["cost_efficiency"] * cost_factor
    else:
        score += SCORING_WEIGHTS["cost_efficiency"]  # Full points if free

    return score
