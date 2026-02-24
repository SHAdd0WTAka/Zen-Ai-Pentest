"""
Zen-AI-Pentest Competitive Benchmark Comparison Module

Provides comprehensive comparison capabilities against competitor tools
including PentestGPT and AutoPentest-DRL.
"""

from .autopentest_comparison import (
    AutoPentestCapabilities,
    AutoPentestComparator,
    AutoPentestResultParser,
)
from .common_benchmarks import (
    BenchmarkSuite,
    BenchmarkTestCase,
    ComparisonMetrics,
    CompetitorResult,
    TestScenarioValidator,
    ZenResult,
    load_test_suite,
    save_test_suite,
)
from .pentestgpt_comparison import (
    PentestGPTCapabilities,
    PentestGPTComparator,
    PentestGPTResultParser,
)

__all__ = [
    # Common benchmarks
    "BenchmarkTestCase",
    "BenchmarkSuite",
    "CompetitorResult",
    "ZenResult",
    "ComparisonMetrics",
    "TestScenarioValidator",
    "load_test_suite",
    "save_test_suite",
    # PentestGPT
    "PentestGPTComparator",
    "PentestGPTCapabilities",
    "PentestGPTResultParser",
    # AutoPentest
    "AutoPentestComparator",
    "AutoPentestCapabilities",
    "AutoPentestResultParser",
]
