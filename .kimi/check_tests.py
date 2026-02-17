#!/usr/bin/env python3
"""Check if tests exist and can run"""

import os
import subprocess
import sys

def check_tests():
    """Check test files"""
    test_dir = "tests"

    if not os.path.exists(test_dir):
        print(f"[ERROR] Test directory '{test_dir}' not found!")
        return False

    # Count test files
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                test_files.append(os.path.join(root, f))

    print(f"\nFound {len(test_files)} test files:")
    for tf in test_files[:10]:
        print(f"  - {tf}")
    if len(test_files) > 10:
        print(f"  ... and {len(test_files) - 10} more")

    # Try to run pytest collection
    print("\nChecking if pytest can collect tests...")
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            test_count = len([l for l in lines if "::" in l])
            print(f"[OK] pytest can collect {test_count} tests")
        else:
            print(f"[WARN] pytest collection failed:")
            print(result.stderr[:500])

    except Exception as e:
        print(f"[ERROR] Could not run pytest: {e}")

    return len(test_files) > 0

if __name__ == "__main__":
    print("=" * 60)
    print(" TEST CHECK")
    print("=" * 60)
    check_tests()
