"""
Zen-AI-Pentest Competitive Benchmark Comparison Module

Provides comprehensive comparison capabilities against competitor tools
including PentestGPT and AutoPentest-DRL.
"""

from .common_benchmarks import (
    BenchmarkTestCase,
    BenchmarkSuite,
    CompetitorResult,
    ZenResult,
    ComparisonMetrics,
    TestScenarioValidator,
    load_test_suite,
    save_test_suite
)

from .pentestgpt_comparison import (
    PentestGPTComparator,
    PentestGPTCapabilities,
    PentestGPTResultParser
)

from .autopentest_comparison import (
    AutoPentestComparator,
    AutoPentestCapabilities,
    AutoPentestResultParser
)

__all__ = [
    # Common benchmarks
    'BenchmarkTestCase',
    'BenchmarkSuite',
    'CompetitorResult',
    'ZenResult',
    'ComparisonMetrics',
    'TestScenarioValidator',
    'load_test_suite',
    'save_test_suite',
    # PentestGPT
    'PentestGPTComparator',
    'PentestGPTCapabilities',
    'PentestGPTResultParser',
    # AutoPentest
    'AutoPentestComparator',
    'AutoPentestCapabilities',
    'AutoPentestResultParser',
]
