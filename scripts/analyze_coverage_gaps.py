#!/usr/bin/env python3
"""
Analyze coverage gaps in tool_registry.py
"""

import re
from pathlib import Path


def analyze_module(filepath: str) -> dict:
    """Analyze a Python module for testability."""
    content = Path(filepath).read_text()
    lines = content.split("\n")

    # Find classes and methods
    classes = []
    current_class = None

    for i, line in enumerate(lines, 1):
        # Class definition
        class_match = re.match(r"^class (\w+)", line)
        if class_match:
            if current_class:
                classes.append(current_class)
            current_class = {
                "name": class_match.group(1),
                "line": i,
                "methods": [],
                "testable": "Enum" not in line,  # Enums are auto-tested
            }

        # Method definition
        method_match = re.match(r"    def (\w+)", line)
        if method_match and current_class:
            method_name = method_match.group(1)
            # Check if method has external dependencies
            testable = not any(x in method_name for x in ["_exec", "_run", "_call"])
            current_class["methods"].append({"name": method_name, "line": i, "testable": testable})

    if current_class:
        classes.append(current_class)

    return classes


def main():
    filepath = "tools/tool_registry.py"
    classes = analyze_module(filepath)

    print(f"\n📁 {filepath}")
    print("=" * 70)

    total_methods = 0
    testable_methods = 0

    for cls in classes:
        if not cls["methods"]:
            continue

        print(f"\n🔹 class {cls['name']} (line {cls['line']})")
        print(f"   Testable: {'✅' if cls['testable'] else '❌'}")

        for method in cls["methods"]:
            total_methods += 1
            if method["testable"] and cls["testable"]:
                testable_methods += 1
                status = "✅"
            else:
                status = "❌"
            print(f"      {status} {method['name']}() (line {method['line']})")

    print("\n" + "=" * 70)
    print(f"📊 Summary: {testable_methods}/{total_methods} methods testable ({100 * testable_methods / total_methods:.0f}%)")
    print(f"🎯 Estimated tests needed: {testable_methods} (not 800+)")


if __name__ == "__main__":
    main()
