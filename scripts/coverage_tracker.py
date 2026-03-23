#!/usr/bin/env python3
"""
Coverage Tracker - Monitors progress toward 80% coverage goal
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COVERAGE_FILE = PROJECT_ROOT / "coverage.json"
HISTORY_FILE = PROJECT_ROOT / ".coverage_history.json"


def run_coverage():
    """Run tests with coverage"""
    print("🧪 Running tests with coverage...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_schemas_coverage.py",
            "-v",
            "--cov=.",
            "--cov-report=json",
            "--cov-report=term",
            "--cov-fail-under=0",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    return result.returncode == 0


def analyze_coverage():
    """Analyze coverage report"""
    if not COVERAGE_FILE.exists():
        print("❌ No coverage.json found. Run tests first.")
        return

    with open(COVERAGE_FILE) as f:
        data = json.load(f)

    total = data.get("totals", {})
    total_pct = total.get("percent_covered", 0)

    print(f"\n{'='*60}")
    print(f"📊 COVERAGE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"\n🎯 Total Coverage: {total_pct:.1f}%")
    print(f"   Target: 80.0%")
    print(f"   Gap: {80.0 - total_pct:.1f}%")

    # Categorize files
    files = data.get("files", {})

    high_coverage = []
    medium_coverage = []
    low_coverage = []
    no_coverage = []

    for fname, fdata in files.items():
        pct = fdata.get("summary", {}).get("percent_covered", 0)

        if pct >= 80:
            high_coverage.append((fname, pct))
        elif pct >= 50:
            medium_coverage.append((fname, pct))
        elif pct > 0:
            low_coverage.append((fname, pct))
        else:
            no_coverage.append((fname, pct))

    print(f"\n✅ High Coverage (≥80%): {len(high_coverage)} files")
    print(f"🟡 Medium Coverage (50-79%): {len(medium_coverage)} files")
    print(f"🟠 Low Coverage (1-49%): {len(low_coverage)} files")
    print(f"🔴 No Coverage (0%): {len(no_coverage)} files")

    # Show critical files (high importance, low coverage)
    print(f"\n{'-'*60}")
    print("🔴 CRITICAL: High Importance Files with Low/No Coverage")
    print(f"{'-'*60}")

    critical_patterns = ["api/", "core/", "tools/", "database/"]
    critical_files = []

    for fname, pct in sorted(low_coverage + no_coverage, key=lambda x: x[1]):
        for pattern in critical_patterns:
            if pattern in fname and not fname.startswith("test_"):
                critical_files.append((fname, pct))
                break

    for fname, pct in critical_files[:15]:
        status = "🔴" if pct == 0 else "🟠"
        print(f"  {status} {fname}: {pct:.1f}%")

    # Recommendations
    print(f"\n{'-'*60}")
    print("💡 RECOMMENDATIONS")
    print(f"{'-'*60}")

    if no_coverage:
        print(
            f"1. Priority 1: Write tests for {len(no_coverage)} files with 0% coverage"
        )
    if low_coverage:
        print(
            f"2. Priority 2: Improve {len(low_coverage)} files with low coverage"
        )
    if medium_coverage:
        print(f"3. Priority 3: Push {len(medium_coverage)} files to 80%+")

    print(f"\n🚀 Quick Wins (focus on these first):")
    for fname, pct in critical_files[:5]:
        module = fname.replace("/", ".").replace(".py", "")
        print(f"   - {module}")

    # Save history
    save_history(
        total_pct,
        len(high_coverage),
        len(medium_coverage),
        len(low_coverage),
        len(no_coverage),
    )


def save_history(total, high, medium, low, none):
    """Save coverage history"""
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            history = json.load(f)

    history.append(
        {
            "date": datetime.now().isoformat(),
            "total_coverage": total,
            "high": high,
            "medium": medium,
            "low": low,
            "none": none,
        }
    )

    # Keep only last 30 entries
    history = history[-30:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    # Show trend
    if len(history) >= 2:
        prev = history[-2]
        curr = history[-1]
        delta = curr["total_coverage"] - prev["total_coverage"]

        print(
            f"\n📈 Trend: {'+' if delta > 0 else ''}{delta:.1f}% since last run"
        )


if __name__ == "__main__":
    print("🎯 Zen-AI-Pentest Coverage Tracker")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "--analyze":
        analyze_coverage()
    else:
        if run_coverage():
            analyze_coverage()
        else:
            print("⚠️  Tests had failures, but analyzing coverage anyway...")
            analyze_coverage()
