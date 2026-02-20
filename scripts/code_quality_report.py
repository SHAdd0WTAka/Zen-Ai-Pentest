#!/usr/bin/env python3
"""
Code Quality Report Generator for Zen-AI-Pentest

Generates comprehensive reports on:
- Lines of code per module
- Test coverage per module
- Linting issues count
- Security issues count

Usage:
    python scripts/code_quality_report.py
    python scripts/code_quality_report.py --output report.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ModuleStats:
    """Statistics for a single module"""

    name: str
    path: str
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    linting_issues: int = 0
    security_issues: int = 0
    coverage_percent: Optional[float] = None


@dataclass
class QualityReport:
    """Complete code quality report"""

    generated_at: str = field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())
    total_files: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    total_modules: List[ModuleStats] = field(default_factory=list)
    linting_summary: Dict[str, int] = field(default_factory=dict)
    security_summary: Dict[str, int] = field(default_factory=dict)
    coverage_summary: Dict[str, Any] = field(default_factory=dict)


def count_lines_in_file(file_path: Path) -> tuple[int, int, int, int]:
    """Count total, code, blank, and comment lines in a file.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (total, code, blank, comment) line counts
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return 0, 0, 0, 0

    total = len(lines)
    blank = 0
    comment = 0
    code = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith("#"):
            comment += 1
        else:
            code += 1

    return total, code, blank, comment


def analyze_module(module_path: Path, module_name: str) -> ModuleStats:
    """Analyze a module directory.

    Args:
        module_path: Path to the module directory
        module_name: Name of the module

    Returns:
        ModuleStats object with line counts
    """
    stats = ModuleStats(name=module_name, path=str(module_path))

    if not module_path.exists():
        return stats

    for py_file in module_path.rglob("*.py"):
        if ".venv" in str(py_file) or "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue

        total, code, blank, comment = count_lines_in_file(py_file)
        stats.total_lines += total
        stats.code_lines += code
        stats.blank_lines += blank
        stats.comment_lines += comment

    return stats


def run_ruff_check(module_path: Path) -> int:
    """Run ruff check on a module and count issues.

    Args:
        module_path: Path to the module

    Returns:
        Number of linting issues found
    """
    try:
        result = subprocess.run(
            ["ruff", "check", str(module_path), "--quiet"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Count non-empty lines in output
        issues = [line for line in result.stdout.split("\n") if line.strip()]
        return len(issues)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0


def run_bandit_check(module_path: Path) -> int:
    """Run bandit security check on a module.

    Args:
        module_path: Path to the module

    Returns:
        Number of security issues found
    """
    try:
        result = subprocess.run(
            ["bandit", "-r", str(module_path), "-ll", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Count issue lines (lines starting with >>)
        issues = [line for line in result.stdout.split("\n") if line.strip().startswith(">>")]
        return len(issues)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0


def get_coverage_data() -> dict[str, Any]:
    """Get coverage data if available.

    Returns:
        Dictionary with coverage summary
    """
    try:
        result = subprocess.run(
            ["python", "-m", "coverage", "json", "-o", "-"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            totals = data.get("totals", {})
            return {
                "available": True,
                "percent_covered": totals.get("percent_covered", 0),
                "covered_lines": totals.get("covered_lines", 0),
                "missing_lines": totals.get("missing_lines", 0),
                "num_statements": totals.get("num_statements", 0),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

    return {"available": False}


def generate_report(project_root: Path, include_linting: bool = True, include_security: bool = True) -> QualityReport:
    """Generate complete quality report.

    Args:
        project_root: Root directory of the project
        include_linting: Whether to include linting checks
        include_security: Whether to include security checks

    Returns:
        QualityReport object
    """
    report = QualityReport()

    # Define modules to analyze
    modules = [
        ("core", project_root / "core"),
        ("api", project_root / "api"),
        ("tools", project_root / "tools"),
        ("agents", project_root / "agents"),
        ("autonomous", project_root / "autonomous"),
        ("database", project_root / "database"),
        ("guardrails", project_root / "guardrails"),
        ("modules", project_root / "modules"),
        ("tests", project_root / "tests"),
    ]

    # Analyze each module
    for module_name, module_path in modules:
        stats = analyze_module(module_path, module_name)

        if stats.total_lines > 0:
            report.total_modules.append(stats)
            report.total_files += len(list(module_path.rglob("*.py")))
            report.total_lines += stats.total_lines
            report.total_code_lines += stats.code_lines

    # Run linting checks if requested
    if include_linting:
        linting_issues: dict[str, int] = {}
        for module in report.total_modules:
            issues = run_ruff_check(Path(module.path))
            module.linting_issues = issues
            linting_issues[module.name] = issues
        report.linting_summary = linting_issues

    # Run security checks if requested
    if include_security:
        security_issues: dict[str, int] = {}
        for module in report.total_modules:
            issues = run_bandit_check(Path(module.path))
            module.security_issues = issues
            security_issues[module.name] = issues
        report.security_summary = security_issues

    # Get coverage data
    report.coverage_summary = get_coverage_data()

    return report


def print_report(report: QualityReport) -> None:
    """Print report to console.

    Args:
        report: QualityReport to print
    """
    print("=" * 80)
    print("CODE QUALITY REPORT - Zen-AI-Pentest")
    print("=" * 80)
    print(f"Generated: {report.generated_at}")
    print()

    # Summary
    print("-" * 80)
    print("SUMMARY")
    print("-" * 80)
    print(f"Total Files:      {report.total_files}")
    print(f"Total Lines:      {report.total_lines:,}")
    print(f"Code Lines:       {report.total_code_lines:,}")
    print()

    # Module breakdown
    print("-" * 80)
    print("MODULE BREAKDOWN")
    print("-" * 80)
    print(f"{'Module':<15} {'Files':>8} {'Total':>10} {'Code':>10} {'Blank':>8} {'Comments':>10}")
    print("-" * 80)

    for module in sorted(report.total_modules, key=lambda x: x.total_lines, reverse=True):
        num_files = len(list(Path(module.path).rglob("*.py")))
        print(
            f"{module.name:<15} {num_files:>8} {module.total_lines:>10,} "
            f"{module.code_lines:>10,} {module.blank_lines:>8,} {module.comment_lines:>10,}"
        )

    print()

    # Linting summary
    if report.linting_summary:
        print("-" * 80)
        print("LINTING ISSUES (by module)")
        print("-" * 80)
        total_linting = sum(report.linting_summary.values())
        print(f"Total Issues: {total_linting}")
        print()
        for module, issues in sorted(report.linting_summary.items(), key=lambda x: x[1], reverse=True):
            if issues > 0:
                print(f"  {module:<15} {issues:>6} issues")
        print()

    # Security summary
    if report.security_summary:
        print("-" * 80)
        print("SECURITY ISSUES (by module)")
        print("-" * 80)
        total_security = sum(report.security_summary.values())
        print(f"Total Issues: {total_security}")
        print()
        for module, issues in sorted(report.security_summary.items(), key=lambda x: x[1], reverse=True):
            if issues > 0:
                print(f"  {module:<15} {issues:>6} issues")
        print()

    # Coverage summary
    if report.coverage_summary.get("available"):
        print("-" * 80)
        print("TEST COVERAGE")
        print("-" * 80)
        print(f"Coverage: {report.coverage_summary['percent_covered']:.1f}%")
        print(f"Covered Lines: {report.coverage_summary['covered_lines']:,}")
        print(f"Missing Lines: {report.coverage_summary['missing_lines']:,}")
        print()

    print("=" * 80)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Generate code quality report")
    parser.add_argument("--output", "-o", type=str, help="Output file (JSON)")
    parser.add_argument("--no-linting", action="store_true", help="Skip linting checks")
    parser.add_argument("--no-security", action="store_true", help="Skip security checks")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    print("Analyzing codebase...")
    report = generate_report(
        project_root,
        include_linting=not args.no_linting,
        include_security=not args.no_security,
    )

    print_report(report)

    if args.output:
        # Convert to JSON-serializable dict
        report_dict = {
            "generated_at": report.generated_at,
            "total_files": report.total_files,
            "total_lines": report.total_lines,
            "total_code_lines": report.total_code_lines,
            "modules": [
                {
                    "name": m.name,
                    "path": m.path,
                    "total_lines": m.total_lines,
                    "code_lines": m.code_lines,
                    "blank_lines": m.blank_lines,
                    "comment_lines": m.comment_lines,
                    "linting_issues": m.linting_issues,
                    "security_issues": m.security_issues,
                }
                for m in report.total_modules
            ],
            "linting_summary": report.linting_summary,
            "security_summary": report.security_summary,
            "coverage_summary": report.coverage_summary,
        }

        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        print(f"Report saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
