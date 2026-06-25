#!/usr/bin/env python3
"""
Slow Test Analyzer

Identifies slow tests and provides optimization recommendations.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class SlowTest:
    """Represents a slow test."""

    nodeid: str
    duration: float
    setup_time: float
    call_time: float
    teardown_time: float
    recommendation: str


def analyze_test_duration(test: Dict) -> Dict:
    """Analyze a single test's duration breakdown."""
    duration = test.get("duration", 0)

    setup_time = test.get("setup", {}).get("duration", 0)
    call_time = test.get("call", {}).get("duration", 0)
    teardown_time = test.get("teardown", {}).get("duration", 0)

    return {
        "total": duration,
        "setup": setup_time,
        "call": call_time,
        "teardown": teardown_time,
    }


def generate_recommendation(test: Dict, durations: Dict) -> str:
    """Generate optimization recommendation."""
    recommendations = []

    setup_pct = (durations["setup"] / durations["total"] * 100) if durations["total"] > 0 else 0
    (durations["call"] / durations["total"] * 100) if durations["total"] > 0 else 0
    teardown_pct = (durations["teardown"] / durations["total"] * 100) if durations["total"] > 0 else 0

    # Check setup time
    if setup_pct > 50:
        recommendations.append("Setup is slow - use session-scoped fixtures")
    elif durations["setup"] > 1:
        recommendations.append("Consider optimizing setup")

    # Check call time
    if durations["call"] > 5:
        recommendations.append("Long test execution - split into smaller tests")
    elif durations["call"] > 1:
        recommendations.append("Consider async operations or mocking")

    # Check teardown time
    if teardown_pct > 30:
        recommendations.append("Teardown is slow - use yield fixtures")

    # Check for network operations
    if any(keyword in test["nodeid"].lower() for keyword in ["network", "http", "api", "db"]):
        recommendations.append("Consider mocking external dependencies")

    # Check for sleep statements
    if "sleep" in str(test).lower():
        recommendations.append("Replace time.sleep() with event-based waiting")

    return "; ".join(recommendations) if recommendations else "No specific recommendations"


def analyze_slow_tests(json_report: str, threshold: float = 1.0) -> List[SlowTest]:
    """Analyze tests and find slow ones."""
    data = json.loads(Path(json_report).read_text())
    tests = data.get("tests", [])

    slow_tests = []

    for test in tests:
        duration = test.get("duration", 0)

        if duration >= threshold:
            durations = analyze_test_duration(test)
            recommendation = generate_recommendation(test, durations)

            slow_tests.append(
                SlowTest(
                    nodeid=test["nodeid"],
                    duration=duration,
                    setup_time=durations["setup"],
                    call_time=durations["call"],
                    teardown_time=durations["teardown"],
                    recommendation=recommendation,
                )
            )

    # Sort by duration (slowest first)
    slow_tests.sort(key=lambda x: x.duration, reverse=True)

    return slow_tests


def generate_report(slow_tests: List[SlowTest], output: str = "slow_tests_report.md"):
    """Generate markdown report."""
    if not slow_tests:
        content = """# Slow Test Analysis

✅ No slow tests detected! All tests execute within acceptable time limits.
"""
    else:
        total_slow = len(slow_tests)
        total_time = sum(t.duration for t in slow_tests)
        avg_time = total_time / total_slow if total_slow > 0 else 0

        content = f"""# 🐌 Slow Test Analysis Report

## Summary

- **Slow Tests Found:** {total_slow}
- **Total Time:** {total_time:.2f}s
- **Average Slow Test Time:** {avg_time:.2f}s

## Slow Tests

| Rank | Test | Total | Setup | Call | Teardown | Recommendation |
|------|------|-------|-------|------|----------|----------------|
"""

        for i, test in enumerate(slow_tests[:20], 1):  # Top 20
            content += f"| {i} | `{test.nodeid}` | {test.duration:.2f}s | {test.setup_time:.2f}s | {test.call_time:.2f}s | {test.teardown_time:.2f}s | {test.recommendation} |\n"

        if total_slow > 20:
            content += f"\n*... and {total_slow - 20} more slow tests*\n"

        content += """
## Optimization Strategies

### 1. Fixture Optimization
- Use `scope="session"` for expensive setup
- Use `scope="module"` for module-level resources
- Avoid redundant setup in each test

### 2. Mock External Dependencies
```python
# Instead of real HTTP calls
@patch('requests.get')
def test_api(mock_get):
    mock_get.return_value.json.return_value = {'key': 'value'}
    # test logic
```

### 3. Async Testing
```python
# Use async tests for I/O operations
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result == expected
```

### 4. Parallel Test Execution
```bash
# Run tests in parallel
pytest -n auto --dist loadgroup
```

### 5. Selective Test Running
```bash
# Run only changed tests
pytest --changed-only

# Run specific test file
pytest tests/unit/test_specific.py
```

## Recommended Actions

1. **Immediate (P0):** Fix tests taking >5s
2. **This Sprint (P1):** Optimize tests taking 2-5s
3. **Backlog (P2):** Review tests taking 1-2s

## Monitoring

Run this analysis regularly:
```bash
python scripts/analyze_slow_tests.py .report.json
```
"""

    Path(output).write_text(content)
    print(f"Report saved: {output}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze slow tests")
    parser.add_argument("json_report", help="Path to pytest JSON report")
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=1.0,
        help="Duration threshold in seconds (default: 1.0)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="slow_tests_report.md",
        help="Output report file",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not Path(args.json_report).exists():
        print(f"Error: Report not found: {args.json_report}", file=sys.stderr)
        sys.exit(1)

    slow_tests = analyze_slow_tests(args.json_report, args.threshold)

    if args.json:
        output = json.dumps(
            [
                {
                    "nodeid": t.nodeid,
                    "duration": t.duration,
                    "recommendation": t.recommendation,
                }
                for t in slow_tests
            ],
            indent=2,
        )
        Path(args.output.replace(".md", ".json")).write_text(output)
    else:
        generate_report(slow_tests, args.output)

    # Print summary
    print(f"\n{'=' * 60}")
    print("Slow Tests Analysis Summary")
    print(f"{'=' * 60}")
    print(f"Threshold: {args.threshold}s")
    print(f"Slow tests found: {len(slow_tests)}")
    if slow_tests:
        print(f"Slowest test: {slow_tests[0].nodeid} ({slow_tests[0].duration:.2f}s)")
        print(f"Time saved if all optimized: {sum(t.duration for t in slow_tests) * 0.5:.2f}s")


if __name__ == "__main__":
    main()
