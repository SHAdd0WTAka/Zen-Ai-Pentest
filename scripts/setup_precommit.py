#!/usr/bin/env python3
"""
Setup script for pre-commit hooks in Zen-AI-Pentest.

This script:
1. Checks if pre-commit is installed
2. Installs pre-commit if missing
3. Installs the git hooks
4. Verifies the installation

Usage:
    python scripts/setup_precommit.py
    
Requirements:
    - Python 3.9+
    - Git repository initialized
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True, capture: bool = True) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            shell=False,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_git_repo() -> bool:
    """Check if we're in a git repository."""
    code, _, _ = run_command(["git", "rev-parse", "--git-dir"], check=False)
    return code == 0


def check_precommit_installed() -> bool:
    """Check if pre-commit is installed."""
    code, _, _ = run_command(["pre-commit", "--version"], check=False)
    return code == 0


def install_precommit() -> bool:
    """Install pre-commit using pip."""
    print("[+] Installing pre-commit...")
    
    # Try pip first, then pip3
    for pip_cmd in ["pip", "pip3", sys.executable + " -m pip"]:
        code, stdout, stderr = run_command(
            pip_cmd.split() + ["install", "pre-commit", "-q"],
            check=False,
        )
        if code == 0:
            print("[OK] pre-commit installed successfully")
            return True
    
    print("[ERROR] Failed to install pre-commit")
    print("        Please install manually: pip install pre-commit")
    return False


def install_hooks() -> bool:
    """Install pre-commit hooks."""
    print("[+] Installing pre-commit hooks...")
    
    code, stdout, stderr = run_command(
        ["pre-commit", "install"],
        check=False,
    )
    
    if code != 0:
        print("[ERROR] Failed to install hooks")
        print(f"        Error: {stderr}")
        return False
    
    print("[OK] Hooks installed successfully")
    return True


def install_commit_msg_hook() -> bool:
    """Install commit-msg hook for commit message validation."""
    print("[+] Installing commit-msg hook...")
    
    code, stdout, stderr = run_command(
        ["pre-commit", "install", "--hook-type", "commit-msg"],
        check=False,
    )
    
    if code != 0:
        print("[!] Failed to install commit-msg hook (optional)")
        return False
    
    print("[OK] Commit-msg hook installed")
    return True


def verify_installation() -> bool:
    """Verify that hooks are installed and working."""
    print("\n[*] Verifying installation...")
    
    # Check if hook file exists
    git_dir = Path(".git/hooks/pre-commit")
    if not git_dir.exists():
        print("[ERROR] Pre-commit hook file not found")
        return False
    
    print("[OK] Pre-commit hook file exists")
    
    # Run pre-commit on a sample file (just to check config is valid)
    print("\n[*] Testing pre-commit configuration...")
    code, stdout, stderr = run_command(
        ["pre-commit", "run", "--all-files", "trailing-whitespace"],
        check=False,
    )
    
    # trailing-whitespace might fail if there are issues, but config should be valid
    if code in [0, 1]:  # 0 = success, 1 = issues found (config is valid)
        print("[OK] Pre-commit configuration is valid")
    else:
        print(f"[!] Configuration test returned code {code}")
        if stderr:
            print(f"        Output: {stderr}")
    
    return True


def print_usage():
    """Print usage information."""
    print("\n" + "=" * 60)
    print("PRE-COMMIT USAGE")
    print("=" * 60)
    print("""
Quick commands:
    pre-commit run --all-files     Run all hooks on all files
    pre-commit run ruff            Run specific hook (ruff)
    pre-commit run --files file.py Run on specific file(s)
    SKIP=pytest git commit ...     Skip specific hooks
    
Skip hooks with environment variable:
    SKIP=ruff,pytest git commit -m "quick fix"
    
Update hooks to latest versions:
    pre-commit autoupdate
    
Uninstall hooks:
    pre-commit uninstall
""")


def print_summary():
    """Print summary of installed hooks."""
    print("\n" + "=" * 60)
    print("INSTALLED HOOKS SUMMARY")
    print("=" * 60)
    print("""
File checks:
  [x] trailing-whitespace    Remove trailing whitespace
  [x] end-of-file-fixer      Ensure files end with newline
  [x] check-yaml             Validate YAML syntax
  [x] check-json             Validate JSON syntax
  [x] check-added-large-files Block files >500KB

Python code quality:
  [x] ruff                   Fast Python linter (E, F, W rules)
  [x] black                  Python code formatter
  [x] isort                  Import sorting

Security:
  [x] bandit                 Security vulnerability scanner

Testing:
  [x] pytest-quick           Run quick unit tests (< 30s)

All hooks:
  - Run only on staged files (fast)
  - Can be skipped with SKIP=hook-name
  - Work on Windows, Linux, and macOS
""")


def main() -> int:
    """Main setup function."""
    print("=" * 60)
    print("Zen-AI-Pentest Pre-commit Setup")
    print("=" * 60)
    
    # Check if we're in a git repo
    if not check_git_repo():
        print("[ERROR] Not a git repository. Please run: git init")
        return 1
    print("[OK] Git repository detected")
    
    # Check if pre-commit is installed
    if not check_precommit_installed():
        if not install_precommit():
            return 1
    else:
        print("[OK] pre-commit is already installed")
    
    # Install hooks
    if not install_hooks():
        return 1
    
    # Install commit-msg hook (optional)
    install_commit_msg_hook()
    
    # Verify installation
    if not verify_installation():
        return 1
    
    # Print summary and usage
    print_summary()
    print_usage()
    
    print("\n" + "=" * 60)
    print("Setup complete! Pre-commit hooks are ready to use.")
    print("=" * 60)
    print("\n[*] Tip: Make your first commit to test the hooks!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
