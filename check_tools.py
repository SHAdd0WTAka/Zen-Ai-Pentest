#!/usr/bin/env python3
"""Check tool availability"""

from tools.integrations.tool_checker import ToolChecker

checker = ToolChecker()
report = checker.get_status_report()

print("=" * 60)
print("PENTEST TOOLS STATUS CHECK")
print("=" * 60)
print()
ready_status = "YES" if report["ready"] else "NO"
print(f"System Ready: {ready_status}")
print()
print(
    f"Required Tools: {report['required']['available']}/{report['required']['total']}"
)
if report["required"]["missing"]:
    print("Missing Required:")
    for tool in report["required"]["missing"]:
        print(f"  - {tool}")
print()
print(
    f"Optional Tools: {report['optional']['available']}/{report['optional']['total']}"
)

if not report["ready"]:
    print()
    print("To install tools:")
    print("  Linux/macOS: bash scripts/install-tools.sh --all")
    print("  Windows: PowerShell -File scripts/install-tools.ps1 -All")
