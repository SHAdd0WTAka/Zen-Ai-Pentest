"""
Test Runner

Runs all test suites with proper configuration.
"""

import sys
import subprocess
from pathlib import Path


def run_unit_tests():
    """Run unit tests"""
    print("=" * 70)
    print("RUNNING UNIT TESTS")
    print("=" * 70)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/unit",
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ], cwd=Path(__file__).parent.parent)
    
    return result.returncode


def run_integration_tests():
    """Run integration tests"""
    print("\n" + "=" * 70)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 70)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/integration",
        "-v",
        "--tb=short",
        "-m", "not e2e"  # Skip E2E tests
    ], cwd=Path(__file__).parent.parent)
    
    return result.returncode


def run_e2e_tests():
    """Run E2E tests (requires running server)"""
    print("\n" + "=" * 70)
    print("RUNNING E2E TESTS")
    print("=" * 70)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/e2e",
        "-v",
        "--tb=short",
        "-m", "e2e"
    ], cwd=Path(__file__).parent.parent)
    
    return result.returncode


def run_with_coverage():
    """Run all tests with coverage"""
    print("=" * 70)
    print("RUNNING TESTS WITH COVERAGE")
    print("=" * 70)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ], cwd=Path(__file__).parent.parent)
    
    return result.returncode


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Zen-AI-Pentest tests")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run E2E tests only"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    
    args = parser.parse_args()
    
    exit_codes = []
    
    if args.coverage:
        exit_codes.append(run_with_coverage())
    elif args.unit:
        exit_codes.append(run_unit_tests())
    elif args.integration:
        exit_codes.append(run_integration_tests())
    elif args.e2e:
        exit_codes.append(run_e2e_tests())
    elif args.all:
        exit_codes.append(run_unit_tests())
        exit_codes.append(run_integration_tests())
        # Don't run E2E by default (requires server)
    else:
        # Default: run unit and integration tests
        exit_codes.append(run_unit_tests())
        exit_codes.append(run_integration_tests())
    
    # Exit with failure if any test suite failed
    sys.exit(max(exit_codes))


if __name__ == "__main__":
    main()
