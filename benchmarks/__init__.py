"""
Zen-AI-Pentest Benchmarking & Testing Framework

Comprehensive benchmark suite for evaluating security testing performance.
"""

__version__ = "1.0.0"
__author__ = "Zen-AI-Pentest Team"

# Main components
from .benchmark_engine import (
    BenchmarkEngine,
    BenchmarkConfig,
    BenchmarkReport,
    BenchmarkStatus,
    ScenarioResult
)

from .metrics import (
    BenchmarkMetrics,
    ClassificationMetrics,
    CoverageMetrics,
    PerformanceMetrics,
    ExploitMetrics,
    TokenUsage,
    FindingMetrics,
    SeverityLevel,
    FindingType,
    MetricsAggregator,
    compare_metrics,
    calculate_confidence_interval
)

from .scenarios import (
    TestScenario,
    ScenarioType,
    DifficultyLevel,
    VulnerabilityProfile,
    get_scenario,
    get_scenarios_by_type,
    get_scenarios_by_difficulty,
    get_scenarios_by_tag,
    list_all_scenarios,
    create_benchmark_suite,
    ALL_SCENARIOS,
    # Pre-defined scenarios
    OWASP_JUICE_SHOP,
    DVWA_SCENARIO,
    METASPLOITABLE2_SCENARIO,
    METASPLOITABLE3_SCENARIO,
    WEBGOAT_SCENARIO,
    HTB_STARTING_POINT_TIER1,
    THM_OWASP_TOP10
)

from .comparison import (
    ComparisonFramework,
    ComparisonResult,
    CompetitorTool,
    ToolMetadata,
    ToolCapabilities,
    ToolCategory,
    ToolBenchmarkResult,
    PentestGPTCompetitor,
    AutoPentestDRLCompetitor,
    PENTESTGPT_METADATA,
    AUTOPENTEST_METADATA,
    NESSUS_METADATA,
    OPENVAS_METADATA,
    BURP_SUITE_METADATA,
    OWASP_ZAP_METADATA,
    NIKTO_METADATA,
    NUCLEI_METADATA,
    SQLMAP_METADATA
)

from .ci_benchmark import (
    CIBenchmarkRunner,
    CIConfig,
    PerformanceGate,
    GateResult,
    RegressionCheck,
    RegressionSeverity
)

__all__ = [
    # Engine
    "BenchmarkEngine",
    "BenchmarkConfig",
    "BenchmarkReport",
    "BenchmarkStatus",
    "ScenarioResult",
    
    # Metrics
    "BenchmarkMetrics",
    "ClassificationMetrics",
    "CoverageMetrics",
    "PerformanceMetrics",
    "ExploitMetrics",
    "TokenUsage",
    "FindingMetrics",
    "SeverityLevel",
    "FindingType",
    "MetricsAggregator",
    
    # Scenarios
    "TestScenario",
    "ScenarioType",
    "DifficultyLevel",
    "VulnerabilityProfile",
    "get_scenario",
    "get_scenarios_by_type",
    "get_scenarios_by_difficulty",
    "get_scenarios_by_tag",
    "list_all_scenarios",
    "create_benchmark_suite",
    
    # Comparison
    "ComparisonFramework",
    "ComparisonResult",
    "CompetitorTool",
    "ToolMetadata",
    "ToolCapabilities",
    "ToolCategory",
    "ToolBenchmarkResult",
    
    # CI/CD
    "CIBenchmarkRunner",
    "CIConfig",
    "PerformanceGate",
    "GateResult",
    "RegressionCheck",
    "RegressionSeverity",
]


def get_version() -> str:
    """Get framework version."""
    return __version__


def get_available_scenarios() -> list:
    """Get list of all available scenario IDs."""
    return list(ALL_SCENARIOS.keys())


def create_default_engine(output_dir: str = "benchmark_results") -> BenchmarkEngine:
    """Create a benchmark engine with default configuration."""
    return BenchmarkEngine(output_dir=output_dir)
