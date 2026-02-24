#!/usr/bin/env python3
"""
Pre-commit hooks setup for Zen AI Pentest.

This script installs and configures pre-commit hooks for:
- Ruff (linting & formatting)
- Bandit (security scanning)
- Gitleaks (secret detection)
- TruffleHog (additional secret detection)
- Generic file checks

Usage:
    python setup_precommit.py
"""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n[>] {description}...")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        print(f"[OK] {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed:")
        print(e.stderr)
        return False


def install_precommit() -> bool:
    """Install pre-commit hooks."""
    print("=" * 60)
    print("Setting up Pre-commit Hooks")
    print("=" * 60)

    # Check if pre-commit is installed
    result = subprocess.run(
        ["pre-commit", "--version"], capture_output=True, text=True
    )

    if result.returncode != 0:
        print("pre-commit not found. Installing...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "pre-commit"],
            "Installing pre-commit",
        ):
            return False
    else:
        print(f"[OK] pre-commit found: {result.stdout.strip()}")

    # Install hooks
    if not run_command(["pre-commit", "install"], "Installing git hooks"):
        return False

    # Run hooks on all files
    print("\n" + "=" * 60)
    print("Running pre-commit on all files (first run may take a while)...")
    print("=" * 60)

    result = subprocess.run(
        ["pre-commit", "run", "--all-files"], capture_output=True, text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    print("\n" + "=" * 60)
    print("Pre-commit setup complete!")
    print("=" * 60)
    print(
        """
Hooks installed:
  - Ruff (linting & formatting)
  - Bandit (security scanning)
  - Gitleaks (secret detection)
  - TruffleHog (additional secret detection)
  - Generic checks (trailing whitespace, YAML/JSON validation, etc.)

Usage:
  - Hooks run automatically on git commit
  - Run manually: pre-commit run --all-files
  - Update hooks: pre-commit autoupdate
  - Skip hooks: git commit --no-verify (not recommended!)
"""
    )

    return True


def main():
    """Main entry point."""
    success = install_precommit()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
