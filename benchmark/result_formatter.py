#!/usr/bin/env python3
"""
Result Formatter - Formats evaluation results for SWE-bench style output.
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Any


class ResultFormatter:
    """Formats benchmark results."""

    def __init__(self):
        self.results: list[dict[str, Any]] = []

    def load_results(self, input_file: Path) -> list[dict[str, Any]]:
        """Load results from JSON file."""
        with open(input_file) as f:
            self.results = json.load(f)
        return self.results

    def format_json(self, output_file: Path, pretty: bool = True) -> None:
        """Save results as JSON."""
        with open(output_file, "w") as f:
            if pretty:
                json.dump(self.results, f, indent=2, default=str)
            else:
                json.dump(self.results, f, default=str)
        print(f"JSON results saved to {output_file}")

    def format_csv(self, output_file: Path) -> None:
        """Save results as CSV."""
        if not self.results:
            print("No results to format")
            return

        fieldnames = [
            "issue_id",
            "passed",
            "elapsed_seconds",
            "returncode",
            "timestamp",
        ]

        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                row = {
                    "issue_id": result.get("issue_id", "unknown"),
                    "passed": result.get("passed", False),
                    "elapsed_seconds": result.get("elapsed_seconds", 0),
                    "returncode": result.get("returncode", -1),
                    "timestamp": result.get("timestamp", ""),
                }
                writer.writerow(row)

        print(f"CSV results saved to {output_file}")

    def format_swe_bench(self, output_file: Path) -> None:
        """Format results in SWE-bench style."""
        if not self.results:
            print("No results to format")
            return

        swe_results = []

        for result in self.results:
            swe_results.append(
                {
                    "instance_id": result.get("issue_id", "unknown"),
                    "status": "RESOLVED" if result.get("passed") else "FAILED",
                    "predicted_patch": result.get("patch", ""),
                    "gold_patch": result.get("gold_patch", ""),
                    "metrics": {
                        "elapsed_seconds": result.get("elapsed_seconds", 0),
                        "returncode": result.get("returncode", -1),
                    },
                }
            )

        with open(output_file, "w") as f:
            json.dump(swe_results, f, indent=2, default=str)

        print(f"SWE-bench format results saved to {output_file}")

    def print_summary(self) -> None:
        """Print summary statistics."""
        if not self.results:
            print("No results to summarize")
            return

        passed = sum(1 for r in self.results if r.get("passed"))
        failed = len(self.results) - passed
        total = len(self.results)

        total_time = sum(r.get("elapsed_seconds", 0) for r in self.results)
        avg_time = total_time / total if total > 0 else 0

        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total evaluations: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass rate: {passed / total * 100:.1f}%")
        print(f"Total time: {total_time:.1f}s")
        print(f"Average time: {avg_time:.1f}s")
        print("=" * 60)

    def print_detailed(self, limit: int = 20) -> None:
        """Print detailed results."""
        if not self.results:
            print("No results to print")
            return

        print("\nDetailed Results:")
        print("-" * 60)

        for i, result in enumerate(self.results[:limit]):
            issue_id = result.get("issue_id", "unknown")[:30]
            passed = "PASS" if result.get("passed") else "FAIL"
            elapsed = result.get("elapsed_seconds", 0)

            print(f"{i + 1:2}. {issue_id:<30} {passed} ({elapsed:.1f}s)")

        if len(self.results) > limit:
            print(f"... and {len(self.results) - limit} more")


def main():
    parser = argparse.ArgumentParser(description="Format benchmark results")
    parser.add_argument("--input", required=True, help="Input results file (JSON)")
    parser.add_argument("--output", help="Output file (derived from format)")
    parser.add_argument(
        "--format",
        choices=["json", "csv", "swe-bench"],
        default="json",
        help="Output format",
    )
    parser.add_argument("--summary", action="store_true", help="Print summary")
    parser.add_argument("--details", action="store_true", help="Print detailed results")
    args = parser.parse_args()

    formatter = ResultFormatter()
    input_file = Path(args.input)

    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        return

    formatter.load_results(input_file)

    if args.summary:
        formatter.print_summary()

    if args.details:
        formatter.print_detailed()

    if args.output:
        output_file = Path(args.output)
    else:
        stem = input_file.stem
        output_file = input_file.parent / f"{stem}_formatted.{args.format}"

    if args.format == "json":
        formatter.format_json(output_file)
    elif args.format == "csv":
        formatter.format_csv(output_file)
    elif args.format == "swe-bench":
        formatter.format_swe_bench(output_file)


if __name__ == "__main__":
    main()
