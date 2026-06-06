#!/usr/bin/env python3
"""
Flaky Test Detection Script

Analyzes test results to detect flaky tests (tests that pass/fail inconsistently).
Generates a report of flaky tests for investigation.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class TestResult:
    """Represents a single test execution result."""

    nodeid: str
    outcome: str  # passed, failed, error, skipped
    duration: float
    setup_duration: float = 0.0
    call_duration: float = 0.0
    teardown_duration: float = 0.0
    reruns: int = 0

    @property
    def is_success(self) -> bool:
        return self.outcome in ("passed", "skipped")


@dataclass
class FlakyTest:
    """Represents a detected flaky test."""

    nodeid: str
    total_runs: int
    success_count: int
    failure_count: int
    failure_rate: float
    error_messages: List[str]
    suggested_action: str

    def to_dict(self) -> dict:
        return asdict(self)


class FlakyTestDetector:
    """Detects flaky tests by running them multiple times."""

    def __init__(self, runs: int = 5, threshold: float = 0.2):
        """
        Initialize detector.

        Args:
            runs: Number of times to run each test
            threshold: Failure rate threshold (0.2 = 20% failures = flaky)
        """
        self.runs = runs
        self.threshold = threshold
        self.results: Dict[str, List[TestResult]] = defaultdict(list)

    def run_tests(self, test_path: str, markers: str = None) -> None:
        """Run tests multiple times and collect results."""
        print(f"Running tests {self.runs} times: {test_path}")

        for run in range(self.runs):
            print(f"\n--- Run {run + 1}/{self.runs} ---")

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                output_file = f.name

            cmd = [
                "python",
                "-m",
                "pytest",
                test_path,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={output_file}",
                "--json-report-omit=streams",
            ]

            if markers:
                cmd.extend(["-m", markers])

            # Run tests
            subprocess.run(cmd, capture_output=True, text=True)

            # Parse results
            self._parse_results(output_file)

            # Clean up
            Path(output_file).unlink(missing_ok=True)

    def _parse_results(self, json_file: str) -> None:
        """Parse test results from JSON report."""
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            for test in data.get("tests", []):
                nodeid = test["nodeid"]
                result = TestResult(
                    nodeid=nodeid,
                    outcome=test["outcome"],
                    duration=test.get("duration", 0),
                    setup_duration=test.get("setup", {}).get("duration", 0),
                    call_duration=test.get("call", {}).get("duration", 0),
                    teardown_duration=test.get("teardown", {}).get("duration", 0),
                    reruns=test.get("rerun_count", 0),
                )
                self.results[nodeid].append(result)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing results: {e}", file=sys.stderr)

    def detect_flaky_tests(self) -> List[FlakyTest]:
        """Analyze results and detect flaky tests."""
        flaky_tests = []

        for nodeid, runs in self.results.items():
            if len(runs) < 2:
                continue

            total = len(runs)
            successes = sum(1 for r in runs if r.is_success)
            failures = total - successes
            failure_rate = failures / total

            # Check if test is flaky
            is_flaky = False

            # Condition 1: Some successes and some failures
            if 0 < successes < total:
                is_flaky = True

            # Condition 2: Failure rate above threshold but not 100%
            if 0 < failure_rate < 1.0 and failure_rate >= self.threshold:
                is_flaky = True

            # Condition 3: High variability in execution time
            durations = [r.duration for r in runs if r.duration > 0]
            if len(durations) > 1:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                if max_duration > avg_duration * 5:  # 5x variance
                    is_flaky = True

            if is_flaky:
                # Collect error messages
                error_messages = []
                for r in runs:
                    if not r.is_success:
                        error_messages.append(f"{r.outcome}: {r.nodeid}")

                # Determine suggested action
                if failure_rate > 0.8:
                    suggested_action = "Fix test - consistently failing"
                elif failure_rate > 0.5:
                    suggested_action = "High priority - major flakiness"
                elif failure_rate > 0.2:
                    suggested_action = "Medium priority - moderate flakiness"
                else:
                    suggested_action = "Low priority - minor flakiness"

                flaky_test = FlakyTest(
                    nodeid=nodeid,
                    total_runs=total,
                    success_count=successes,
                    failure_count=failures,
                    failure_rate=failure_rate,
                    error_messages=error_messages[:5],  # Limit to 5
                    suggested_action=suggested_action,
                )
                flaky_tests.append(flaky_test)

        # Sort by failure rate (highest first)
        flaky_tests.sort(key=lambda x: x.failure_rate, reverse=True)

        return flaky_tests

    def generate_report(self, flaky_tests: List[FlakyTest]) -> str:
        """Generate a formatted report of flaky tests."""
        if not flaky_tests:
            return """# 🎉 Flaky Test Report

No flaky tests detected! All tests are passing consistently.
"""

        report = f"""# 🔍 Flaky Test Report

**Detected {len(flaky_tests)} flaky tests**

## Summary

| Metric | Value |
|--------|-------|
| Total Tests Analyzed | {len(self.results)} |
| Flaky Tests | {len(flaky_tests)} |
| Flakiness Rate | {len(flaky_tests) / len(self.results) * 100:.1f}% |

---

## Flaky Tests Details

"""

        for i, test in enumerate(flaky_tests, 1):
            report += f"""### {i}. `{test.nodeid}`

- **Total Runs:** {test.total_runs}
- **Successes:** {test.success_count} ✅
- **Failures:** {test.failure_count} ❌
- **Failure Rate:** {test.failure_rate * 100:.1f}%
- **Suggested Action:** {test.suggested_action}

"""
            if test.error_messages:
                report += "**Recent Errors:**\n"
                for msg in test.error_messages[:3]:
                    report += f"- {msg}\n"
                report += "\n"

            report += "---\n\n"

        # Add recommendations
        report += """## 💡 Recommendations

1. **Immediate Action:** Fix tests with >50% failure rate
2. **This Sprint:** Address tests with 20-50% failure rate
3. **Ongoing:** Monitor tests with <20% failure rate
4. **Prevention:**
   - Add proper test isolation
   - Use deterministic test data
   - Avoid timing-dependent assertions
   - Add retry logic for external dependencies

## Next Steps

Run the following to investigate specific tests:

```bash
# Run a specific flaky test with verbose output
pytest path/to/flaky_test.py::test_name -v --tb=long

# Run with debugging
pytest path/to/flaky_test.py::test_name -v --capture=no
```
"""

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Detect flaky tests by running them multiple times")
    parser.add_argument(
        "test_path",
        nargs="?",
        default="tests/",
        help="Path to tests (default: tests/)",
    )
    parser.add_argument(
        "-r",
        "--runs",
        type=int,
        default=5,
        help="Number of times to run each test (default: 5)",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=0.2,
        help="Failure rate threshold (default: 0.2 = 20%%)",
    )
    parser.add_argument("-m", "--markers", help="Only run tests with given markers")
    parser.add_argument("-o", "--output", help="Output file for report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--fail-on-flaky",
        action="store_true",
        help="Exit with error if flaky tests detected",
    )

    args = parser.parse_args()

    print("🔍 Flaky Test Detector")
    print(f"   Test path: {args.test_path}")
    print(f"   Runs: {args.runs}")
    print(f"   Threshold: {args.threshold * 100:.0f}%")
    print()

    # Run detection
    detector = FlakyTestDetector(runs=args.runs, threshold=args.threshold)
    detector.run_tests(args.test_path, args.markers)
    flaky_tests = detector.detect_flaky_tests()

    # Generate report
    if args.json:
        output = json.dumps([t.to_dict() for t in flaky_tests], indent=2)
    else:
        output = detector.generate_report(flaky_tests)

    # Output
    if args.output:
        Path(args.output).write_text(output)
        print(f"\nReport written to: {args.output}")
    else:
        print(output)

    # Exit code
    if args.fail_on_flaky and flaky_tests:
        print(f"\n❌ {len(flaky_tests)} flaky tests detected!")
        sys.exit(1)

    if flaky_tests:
        print(f"\n⚠️  {len(flaky_tests)} flaky tests detected (exit code 0)")
    else:
        print("\n✅ No flaky tests detected!")

    sys.exit(0)


if __name__ == "__main__":
    main()
