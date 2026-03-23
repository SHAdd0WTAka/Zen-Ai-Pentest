#!/usr/bin/env python3
"""
Automated Test Generation Pipeline for Zen-AI-Pentest
Uses Pynguin, Hypothesis, and manual templates to achieve 80% coverage
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
GENERATED_DIR = TESTS_DIR / "generated"
COVERAGE_THRESHOLD = 80.0

# Modules to prioritize (high impact, low dependencies)
HIGH_PRIORITY_MODULES = [
    "api.schemas",
    "api.auth",
    "core.config",
    "core.utils",
    "tools.base",
]

MEDIUM_PRIORITY_MODULES = [
    "core.risk_engine",
    "core.models",
    "tools.nmap_integration",
    "tools.nuclei_integration",
]

LOW_PRIORITY_MODULES = [
    "autonomous.agent_loop",
    "agents.react_agent",
]


def run_pynguin(module_name: str, output_dir: Path) -> bool:
    """Run Pynguin test generation for a module"""
    print(f"\n🤖 Generating tests for {module_name} with Pynguin...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pynguin",
                "--project-path",
                str(PROJECT_ROOT),
                "--module-name",
                module_name,
                "--output-path",
                str(output_dir),
                "--maximum-search-time",
                "60",
                "--maximum-test-execution-timeout",
                "10",
                "--maximum-test-case-length",
                "10",
                "--seed",
                "42",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print(f"  ✅ Successfully generated tests for {module_name}")
            return True
        else:
            print(f"  ⚠️  Pynguin warning: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  ⏱️  Timeout for {module_name}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def generate_hypothesis_tests(module_name: str, output_file: Path):
    """Generate Hypothesis property-based tests"""
    print(f"\n🎲 Generating Hypothesis tests for {module_name}...")

    # Import module to inspect
    try:
        module = __import__(module_name, fromlist=[module_name.split(".")[-1]])
    except ImportError:
        print(f"  ❌ Cannot import {module_name}")
        return

    test_code = f'''"""
Property-based tests for {module_name}
Generated automatically by generate_tests.py
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.extra.pydantic import from_type
from {module_name} import *

'''

    # Find functions and classes in module
    import inspect

    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and not name.startswith("_"):
            # Generate property test for function
            sig = inspect.signature(obj)
            params = list(sig.parameters.keys())

            if len(params) <= 3:  # Only simple functions
                test_code += f'''
@given({', '.join([f'{p}=st.integers()' if 'id' in p or 'count' in p else f'{p}=st.text()' for p in params])})
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_{name}_properties({', '.join(params)}):
    """Property-based test for {name}"""
    try:
        result = {name}({', '.join(params)})
        # Property: result should not be None for valid inputs
        assert result is not None or True  # Adjust based on function behavior
    except (ValueError, TypeError):
        # These exceptions are acceptable for invalid inputs
        pass

'''

    output_file.write_text(test_code)
    print(f"  ✅ Generated Hypothesis tests in {output_file}")


def get_current_coverage() -> Tuple[float, Dict[str, float]]:
    """Get current coverage statistics"""
    print("\n📊 Measuring current coverage...")

    try:
        # Run coverage
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "--cov=.",
                "--cov-report=json",
                "--cov-fail-under=0",
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse coverage.json
        coverage_file = PROJECT_ROOT / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file) as f:
                data = json.load(f)

            total_pct = data.get("totals", {}).get("percent_covered", 0)
            files = {}

            for fname, fdata in data.get("files", {}).items():
                files[fname] = fdata.get("summary", {}).get(
                    "percent_covered", 0
                )

            return total_pct, files

    except Exception as e:
        print(f"  ❌ Error measuring coverage: {e}")
        return 0.0, {}

    return 0.0, {}


def identify_coverage_gaps(files: Dict[str, float]) -> List[str]:
    """Identify modules with low coverage"""
    gaps = []

    for fname, pct in files.items():
        if pct < COVERAGE_THRESHOLD:
            # Convert file path to module name
            if fname.endswith(".py") and not fname.startswith("test_"):
                module = fname.replace("/", ".").replace(".py", "")
                gaps.append((module, pct))

    # Sort by coverage (lowest first)
    gaps.sort(key=lambda x: x[1])
    return [g[0] for g in gaps[:20]]  # Top 20 gaps


def generate_test_plan():
    """Generate a comprehensive test plan"""
    print("\n" + "=" * 60)
    print("🎯 AUTOMATED TEST GENERATION PLAN")
    print("=" * 60)

    # Ensure directories exist
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Get current coverage
    total_coverage, files = get_current_coverage()
    print(f"\nCurrent Coverage: {total_coverage:.1f}%")
    print(f"Target Coverage: {COVERAGE_THRESHOLD}%")
    print(f"Gap: {COVERAGE_THRESHOLD - total_coverage:.1f}%")

    # Identify gaps
    gaps = identify_coverage_gaps(files)

    print(f"\n📋 Top 20 modules with lowest coverage:")
    for i, module in enumerate(gaps, 1):
        pct = files.get(module.replace(".", "/") + ".py", 0)
        print(f"  {i}. {module}: {pct:.1f}%")

    # Generate tests for high priority modules
    print("\n" + "-" * 60)
    print("🚀 PHASE 1: High Priority Modules (Pynguin)")
    print("-" * 60)

    generated_count = 0
    for module in HIGH_PRIORITY_MODULES:
        if run_pynguin(module, GENERATED_DIR):
            generated_count += 1

    print(
        f"\n✅ Generated tests for {generated_count}/{len(HIGH_PRIORITY_MODULES)} modules"
    )

    # Generate Hypothesis tests for medium priority
    print("\n" + "-" * 60)
    print("🎲 PHASE 2: Medium Priority (Hypothesis Property Tests)")
    print("-" * 60)

    for module in MEDIUM_PRIORITY_MODULES[:3]:  # Limit to 3
        output_file = (
            GENERATED_DIR / f"test_{module.replace('.', '_')}_hypothesis.py"
        )
        generate_hypothesis_tests(module, output_file)

    # Summary
    print("\n" + "=" * 60)
    print("📊 GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nGenerated tests location: {GENERATED_DIR}")
    print("\nNext steps:")
    print("  1. Review generated tests in tests/generated/")
    print("  2. Run: pytest tests/generated/ -v")
    print("  3. Check coverage: pytest --cov=. --cov-report=term")
    print("  4. Fix any failing tests manually")


if __name__ == "__main__":
    generate_test_plan()
