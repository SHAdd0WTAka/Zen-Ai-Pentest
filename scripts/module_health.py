#!/usr/bin/env python3
"""Score each module (0-100) based on code quality metrics."""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MODULES = ["core", "agents", "api", "tools", "database", "orchestrator"]


def analyze_module(name):
    mod_path = BASE / name
    if not mod_path.is_dir():
        return None

    py_files = list(mod_path.rglob("*.py"))
    total_files = len(py_files)
    total_functions = 0
    total_classes = 0
    total_lines = 0
    func_lengths = []

    for f in py_files:
        lines = f.read_text().splitlines()
        total_lines += len(lines)
        in_func = False
        func_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("def ") and stripped.endswith(":"):
                total_functions += 1
                in_func = True
                func_start = i
            elif stripped.startswith("class ") and stripped.endswith(":"):
                total_classes += 1
            elif in_func:
                if not stripped or i - func_start > 1:
                    in_func = False
                    func_lengths.append(i - func_start)

    avg_func_length = (sum(func_lengths) / len(func_lengths)) if func_lengths else 0

    lint_errors = 0
    try:
        result = subprocess.run(["ruff", "check", "--statistics", str(mod_path)], capture_output=True, text=True, timeout=30)
        for line in result.stdout.splitlines():
            if line.strip() and line[0].isdigit():
                parts = line.split()
                if len(parts) >= 1:
                    try:
                        lint_errors += int(parts[0])
                    except ValueError:
                        pass
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    score = 100 - (lint_errors * 2)
    if avg_func_length > 50:
        score -= 10
    score = max(0, min(100, score))

    return {
        "name": name,
        "files": total_files,
        "functions": total_functions,
        "avg_length": round(avg_func_length, 1),
        "lint_errors": lint_errors,
        "score": score,
    }


def main():
    print(f"{'Module':<15} {'Files':<7} {'Functions':<11} {'Avg Length':<12} {'Lint Errors':<13} {'Score':<6}")
    print("-" * 64)
    for mod in MODULES:
        result = analyze_module(mod)
        if result is None:
            print(f"{mod:<15} {'—':<7} {'—':<11} {'—':<12} {'—':<13} {'—':<6}")
        else:
            print(
                f"{result['name']:<15} {result['files']:<7} {result['functions']:<11} "
                f"{result['avg_length']:<12} {result['lint_errors']:<13} {result['score']:<6}"
            )


if __name__ == "__main__":
    main()
