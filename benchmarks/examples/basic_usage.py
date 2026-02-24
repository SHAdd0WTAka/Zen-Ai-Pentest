"""
Basic Usage Examples for Zen-AI-Pentest Benchmark Framework

This file demonstrates common use cases for the benchmark framework.
"""

import asyncio

# Import main components
from benchmarks import (
    BenchmarkConfig,
    BenchmarkEngine,
    BenchmarkMetrics,
    ClassificationMetrics,
    ComparisonFramework,
    CoverageMetrics,
    FindingMetrics,
    FindingType,
    SeverityLevel,
    TokenUsage,
    create_benchmark_suite,
    list_all_scenarios,
)


async def example_1_list_scenarios():
    """Example 1: List all available benchmark scenarios."""
    print("=" * 60)
    print("Example 1: List Available Scenarios")
    print("=" * 60)

    scenarios = list_all_scenarios()

    print(f"\nTotal scenarios available: {len(scenarios)}\n")

    # Show first 5 scenarios
    for scenario in scenarios[:5]:
        print(f"ID: {scenario['id']}")
        print(f"  Name: {scenario['name']}")
        print(f"  Type: {scenario['type']}")
        print(f"  Difficulty: {scenario['difficulty']}")
        print(
            f"  Expected Vulnerabilities: {scenario['expected_vulnerabilities_count']}"
        )
        print()


async def example_2_run_simple_benchmark():
    """Example 2: Run a simple benchmark."""
    print("=" * 60)
    print("Example 2: Run Simple Benchmark")
    print("=" * 60)

    # Create benchmark engine
    _ = BenchmarkEngine(output_dir="example_results")  # TODO: Use engine

    # Configure benchmark
    config = BenchmarkConfig(
        benchmark_name="example-quick-benchmark",
        scenarios=["dvwa", "juice-shop"],  # Run these two scenarios
        max_concurrent=1,  # Run sequentially
        timeout_per_scenario=1800,
        generate_markdown_report=True,
    )

    print(f"\nStarting benchmark: {config.benchmark_name}")
    print(f"Scenarios: {config.scenarios}")
    print(f"Concurrent: {config.max_concurrent}")

    # Run benchmark (in real usage, this would actually run the scans)
    # report = await engine.run_benchmark(config)

    print("\nBenchmark completed!")
    print("Results saved to: example_results/")


async def example_3_work_with_metrics():
    """Example 3: Working with metrics."""
    print("=" * 60)
    print("Example 3: Working with Metrics")
    print("=" * 60)

    # Create a benchmark metrics instance
    metrics = BenchmarkMetrics(
        benchmark_id="demo-001", scenario_name="DVWA", tool_version="1.0.0"
    )

    # Set classification metrics
    metrics.classification = ClassificationMetrics(
        true_positives=42,
        false_positives=3,
        true_negatives=95,
        false_negatives=5,
    )

    # Calculate and display metrics
    print("\nClassification Metrics:")
    print(f"  True Positives: {metrics.classification.true_positives}")
    print(f"  False Positives: {metrics.classification.false_positives}")
    print(f"  True Negatives: {metrics.classification.true_negatives}")
    print(f"  False Negatives: {metrics.classification.false_negatives}")
    print()
    print(f"  Precision: {metrics.classification.precision:.4f}")
    print(f"  Recall: {metrics.classification.recall:.4f}")
    print(f"  F1-Score: {metrics.classification.f1_score:.4f}")
    print(f"  Accuracy: {metrics.classification.accuracy:.4f}")
    print(
        f"  Matthews Correlation: {metrics.classification.matthews_correlation:.4f}"
    )

    # Set coverage metrics
    metrics.coverage = CoverageMetrics(
        total_endpoints=50,
        scanned_endpoints=45,
        total_parameters=200,
        tested_parameters=180,
        total_attack_vectors=30,
        tested_attack_vectors=28,
        owasp_categories_covered=[
            "A01:2021-Broken Access Control",
            "A03:2021-Injection",
            "A05:2021-Security Misconfiguration",
        ],
    )

    print("\nCoverage Metrics:")
    print(f"  Endpoint Coverage: {metrics.coverage.endpoint_coverage:.1f}%")
    print(f"  Parameter Coverage: {metrics.coverage.parameter_coverage:.1f}%")
    print(
        f"  Attack Vector Coverage: {metrics.coverage.attack_vector_coverage:.1f}%"
    )
    print(f"  OWASP Coverage: {metrics.coverage.owasp_coverage:.1f}%")

    # Add some findings
    metrics.findings = [
        FindingMetrics(
            finding_type=FindingType.SQL_INJECTION,
            severity=SeverityLevel.CRITICAL,
            confidence=0.95,
            exploitability=0.90,
            detection_time_ms=1250,
            verified=True,
            exploited=True,
            cve_id=None,
        ),
        FindingMetrics(
            finding_type=FindingType.XSS,
            severity=SeverityLevel.HIGH,
            confidence=0.88,
            exploitability=0.75,
            detection_time_ms=2300,
            verified=True,
            exploited=False,
            cve_id="CVE-2023-12345",
        ),
    ]

    print(f"\nFindings: {len(metrics.findings)}")
    for finding in metrics.findings:
        print(
            f"  - {finding.finding_type.value}: {finding.severity.value} (confidence: {finding.confidence:.2f})"
        )

    # Set token usage
    metrics.token_usage = TokenUsage(
        prompt_tokens=5000,
        completion_tokens=3000,
        cost_usd=0.15,
        model="gpt-4",
    )

    print("\nToken Usage:")
    print(f"  Prompt Tokens: {metrics.token_usage.prompt_tokens}")
    print(f"  Completion Tokens: {metrics.token_usage.completion_tokens}")
    print(f"  Total Tokens: {metrics.token_usage.total_tokens}")
    print(f"  Cost: ${metrics.token_usage.cost_usd:.4f}")

    # Calculate aggregate scores
    scores = metrics.calculate_aggregate_scores()
    print("\nAggregate Scores:")
    for score_name, score_value in scores.items():
        print(f"  {score_name}: {score_value:.4f}")

    # Export to JSON
    json_output = metrics.to_json(indent=2)
    print("\n\nJSON Export (truncated):")
    print(json_output[:500] + "...")


async def example_4_create_custom_suite():
    """Example 4: Create a custom benchmark suite."""
    print("=" * 60)
    print("Example 4: Create Custom Benchmark Suite")
    print("=" * 60)

    # Create a suite of web application scenarios
    web_suite = create_benchmark_suite(
        scenario_type="web_app",
        difficulty_levels=["easy", "medium"],
        tags=["owasp"],
        max_duration_minutes=60,
    )

    print("\nCreated web app benchmark suite:")
    print(f"  Total scenarios: {len(web_suite)}")
    for scenario in web_suite:
        print(f"    - {scenario.name} ({scenario.difficulty.value})")

    # Create a suite for beginners
    beginner_suite = create_benchmark_suite(
        difficulty_levels=["easy"], tags=["training"]
    )

    print("\nCreated beginner benchmark suite:")
    print(f"  Total scenarios: {len(beginner_suite)}")
    for scenario in beginner_suite:
        print(f"    - {scenario.name}")


async def example_5_compare_tools():
    """Example 5: Compare Zen-AI-Pentest with other tools."""
    print("=" * 60)
    print("Example 5: Tool Comparison")
    print("=" * 60)

    framework = ComparisonFramework()

    # Get metadata for various tools
    tools = [
        "Zen-AI-Pentest",
        "PentestGPT",
        "Nuclei",
        "OWASP ZAP",
        "Burp Suite",
    ]

    print("\nTool Capabilities Comparison:\n")

    for tool_name in tools:
        metadata = framework.get_tool_metadata(tool_name)
        if metadata:
            caps = metadata.capabilities
            print(f"{metadata.name}:")
            print(f"  Category: {metadata.category.value}")
            print(f"  License: {metadata.license_type}")
            print(f"  AI-Powered: {caps.uses_ai}")
            print(f"  Web Scanning: {caps.supports_web_scanning}")
            print(f"  Network Scanning: {caps.supports_network_scanning}")
            print(f"  Exploitation: {caps.supports_exploitation}")
            print()


async def example_6_historical_tracking():
    """Example 6: Historical tracking and trends."""
    print("=" * 60)
    print("Example 6: Historical Tracking")
    print("=" * 60)

    engine = BenchmarkEngine(output_dir="example_results")

    # Get benchmark history
    history = engine.get_benchmark_history(limit=10)

    print(f"\nBenchmark History ({len(history)} entries):")
    for entry in history:
        print(
            f"  - {entry.get('benchmark_id', 'N/A')}: {entry.get('success_rate', 0):.1f}% success"
        )


async def main():
    """Run all examples."""
    print("\n")
    print("█" * 60)
    print("█" + " " * 58 + "█")
    print(
        "█" + "  Zen-AI-Pentest Benchmark Framework Examples".center(58) + "█"
    )
    print("█" + " " * 58 + "█")
    print("█" * 60)
    print("\n")

    # Run examples
    await example_1_list_scenarios()
    print("\n")

    await example_2_run_simple_benchmark()
    print("\n")

    await example_3_work_with_metrics()
    print("\n")

    await example_4_create_custom_suite()
    print("\n")

    await example_5_compare_tools()
    print("\n")

    await example_6_historical_tracking()
    print("\n")

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
