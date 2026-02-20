#!/usr/bin/env python3
"""
Workflow Local Test Script

This script simulates GitHub Actions workflow locally to catch issues before pushing.
Run this script before committing to verify your changes won't break CI.

Usage:
    python scripts/test_workflow_locally.py [options]

Options:
    --quick         Run only quick tests (default)
    --full          Run full test suite
    --coverage      Run with coverage reporting
    --lint          Run linting checks
    --all           Run everything

Exit Codes:
    0 - All checks passed
    1 - Some checks failed
    2 - Configuration error

Author: Zen-AI-Pentest Team
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Colors for terminal output
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Fallback color definitions
    class _DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = _DummyColor()


def print_header(text: str):
    """Print a formatted header"""
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_step(text: str):
    """Print a step indicator"""
    print(f"\n{Fore.CYAN}[STEP]{Style.RESET_ALL} {text}")


def print_success(text: str):
    """Print success message"""
    print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {text}")


def run_command(cmd: List[str], timeout: int = 300, env: dict = None) -> Tuple[int, str, str]:
    """
    Run a command and return (exit_code, stdout, stderr)

    Args:
        cmd: Command and arguments as list
        timeout: Maximum execution time in seconds
        env: Additional environment variables

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    # Ensure UTF-8 encoding
    full_env['PYTHONIOENCODING'] = 'utf-8'

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=full_env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -2, "", str(e)


def check_python_version() -> bool:
    """Check if Python version is compatible"""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} is not supported (requires 3.9+)")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    print_step("Checking dependencies...")

    required = ['pytest', 'fastapi', 'pydantic', 'requests']
    optional = ['pytest-cov', 'ruff', 'black', 'mypy']

    missing_required = []
    missing_optional = []

    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing_required.append(pkg)

    for pkg in optional:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing_optional.append(pkg)

    if missing_required:
        print_error(f"Missing required packages: {', '.join(missing_required)}")
        print("  Install with: pip install -r requirements.txt")
        return False

    if missing_optional:
        print_warning(f"Missing optional packages: {', '.join(missing_optional)}")
        print("  Some checks will be skipped")
    else:
        print_success("All dependencies found")

    return True


def check_file_structure() -> bool:
    """Check if critical files exist"""
    print_step("Checking file structure...")

    critical_files = [
        'requirements.txt',
        'requirements-dev.txt',
        'requirements-test.txt',
        'pytest.ini',
        'setup.py',
        '.github/workflows/tests-coverage.yml',
    ]

    critical_dirs = [
        'core',
        'api',
        'modules',
        'tests',
        'tools',
    ]

    all_ok = True

    for file in critical_files:
        if os.path.exists(file):
            print_success(f"File exists: {file}")
        else:
            print_error(f"Missing file: {file}")
            all_ok = False

    for dir_name in critical_dirs:
        if os.path.isdir(dir_name):
            print_success(f"Directory exists: {dir_name}")
        else:
            print_error(f"Missing directory: {dir_name}")
            all_ok = False

    return all_ok


def run_quick_tests() -> bool:
    """Run quick unit tests"""
    print_step("Running quick tests...")

    test_files = [
        'tests/test_core_basics.py',
        'tests/test_all_imports.py',
    ]

    all_passed = True

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"  Running {test_file}...")
            code, stdout, stderr = run_command(
                ['python', '-m', 'pytest', test_file, '-v', '--tb=short', '-x'],
                timeout=60
            )
            if code == 0:
                print_success(f"{test_file} passed")
            else:
                print_error(f"{test_file} failed")
                if stderr:
                    print(f"    Error: {stderr[:200]}")
                all_passed = False
        else:
            print_warning(f"Test file not found: {test_file}")

    return all_passed


def run_coverage_tests() -> bool:
    """Run tests with coverage"""
    print_step("Running coverage tests...")

    code, stdout, stderr = run_command(
        [
            'python', '-m', 'pytest', 'tests/',
            '--cov=core',
            '--cov-report=term-missing',
            '-v',
            '--tb=short',
        ],
        timeout=300
    )

    if code == 0:
        print_success("Coverage tests passed")
        return True
    else:
        print_error("Coverage tests failed")
        return False


def run_lint_checks() -> bool:
    """Run linting checks"""
    print_step("Running lint checks...")

    all_passed = True

    # Ruff check
    print("  Running ruff...")
    code, stdout, stderr = run_command(['ruff', 'check', '.', '--output-format=text'])
    if code == 0:
        print_success("Ruff check passed")
    else:
        print_warning("Ruff found issues (non-blocking)")
        all_passed = False

    # Black check
    print("  Running black...")
    code, stdout, stderr = run_command(['black', '--check', '--diff', '--line-length', '127', '.'])
    if code == 0:
        print_success("Black check passed")
    else:
        print_warning("Black formatting issues (non-blocking)")
        all_passed = False

    return all_passed


def run_security_scan() -> bool:
    """Run security scan with bandit"""
    print_step("Running security scan...")

    code, stdout, stderr = run_command(
        ['bandit', '-r', 'core/', 'modules/', 'tools/', '-f', 'screen', '-ll'],
        timeout=60
    )

    if code == 0:
        print_success("No security issues found")
        return True
    else:
        print_warning("Security issues found (review recommended)")
        return False


def check_workflow_syntax() -> bool:
    """Check GitHub Actions workflow syntax"""
    print_step("Checking workflow syntax...")

    workflow_dir = Path('.github/workflows')
    if not workflow_dir.exists():
        print_error("Workflow directory not found")
        return False

    all_ok = True

    for workflow_file in workflow_dir.glob('*.yml'):
        print(f"  Checking {workflow_file}...")
        try:
            import yaml
            with open(workflow_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print_success(f"{workflow_file} syntax OK")
        except ImportError:
            print_warning("PyYAML not installed, skipping YAML validation")
            return True
        except yaml.YAMLError as e:
            print_error(f"{workflow_file} has syntax error: {e}")
            all_ok = False

    return all_ok


def create_test_summary(results: dict):
    """Create and print test summary"""
    print_header("Test Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for check, result in results.items():
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if result else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        print(f"  {check:.<40} {status}")

    print("\n" + "-" * 60)
    print(f"Total: {total} | Passed: {Fore.GREEN}{passed}{Style.RESET_ALL} | Failed: {Fore.RED}{failed}{Style.RESET_ALL}")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description='Test GitHub Actions workflow locally',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_workflow_locally.py           # Quick tests only
  python scripts/test_workflow_locally.py --all     # Run everything
  python scripts/test_workflow_locally.py --lint    # Lint checks only
        """
    )

    parser.add_argument('--quick', action='store_true', help='Run quick tests (default)')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage')
    parser.add_argument('--lint', action='store_true', help='Run linting checks')
    parser.add_argument('--security', action='store_true', help='Run security scan')
    parser.add_argument('--all', action='store_true', help='Run all checks')

    args = parser.parse_args()

    # If no specific args, run quick tests
    if not any([args.quick, args.full, args.coverage, args.lint, args.security, args.all]):
        args.quick = True

    # Set up environment
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['TESTING'] = 'true'
    os.environ['JWT_SECRET_KEY'] = 'test-local-workflow'

    print_header("GitHub Actions Local Test")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")

    results = {}

    # Always run these
    results['Python Version'] = check_python_version()
    results['File Structure'] = check_file_structure()
    results['Dependencies'] = check_dependencies()
    results['Workflow Syntax'] = check_workflow_syntax()

    # Optional checks
    if args.quick or args.all:
        results['Quick Tests'] = run_quick_tests()

    if args.coverage or args.full or args.all:
        results['Coverage Tests'] = run_coverage_tests()

    if args.lint or args.full or args.all:
        results['Lint Checks'] = run_lint_checks()

    if args.security or args.full or args.all:
        results['Security Scan'] = run_security_scan()

    # Summary
    success = create_test_summary(results)

    if success:
        print_header("All checks passed! Ready to push.")
        return 0
    else:
        print_header("Some checks failed. Please review and fix.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
