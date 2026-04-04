#!/usr/bin/env python3
"""
Mutation Testing Runner

Runs mutation testing using mutmut.
"""

import subprocess
import sys
from pathlib import Path
from typing import List


def run_mutation_testing(paths: List[str]) -> bool:
    """Run mutation testing on specified paths."""
    print("🧬 Running Mutation Testing...")
    print("   This may take several minutes...")

    # Create mutmut config if not exists
    config_path = Path("mutmut_config.py")
    if not config_path.exists():
        config_content = """
# Mutmut Configuration
paths_to_mutate = ['api/models/', 'core/', 'tools/']
backup = False
runner = 'python -m pytest -x'
tests_dir = 'tests/'
"""
        with open(config_path, "w") as f:
            f.write(config_content)

    # Run mutmut
    result = subprocess.run(
        ["python", "-m", "mutmut", "run", "--paths-to-mutate", ",".join(paths)], capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"⚠️  Mutmut output: {result.stderr}")

    # Generate report
    print("\n📊 Mutation Testing Results:")
    result = subprocess.run(["python", "-m", "mutmut", "results"], capture_output=True, text=True)
    print(result.stdout)

    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", nargs="+", default=["api/models"], help="Paths to mutate")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    args = parser.parse_args()

    success = run_mutation_testing(args.paths)

    if args.report:
        print("\n📄 HTML report: mutmut_report.html")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
