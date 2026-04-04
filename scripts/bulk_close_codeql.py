#!/usr/bin/env python3
"""
Bulk Close CodeQL 'note' Severity Alerts

Closes all CodeQL alerts with severity 'note' (code style issues, not security)
"""

import subprocess
import sys
import time


def get_token():
    """Get GitHub token from gh CLI."""
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    return result.stdout.strip()


def close_alerts_batch():
    """Close CodeQL note alerts in batches using gh CLI."""

    print("Fetching CodeQL 'note' severity alerts...")

    # Get all open CodeQL alerts with note severity
    cmd = [
        "gh",
        "api",
        "repos/SHAdd0WTAka/Zen-Ai-Pentest/code-scanning/alerts",
        "-F",
        "state=open",
        "-F",
        "per_page=100",
        "--paginate",
        "--jq",
        '.[] | select(.tool.name == "CodeQL" and .rule.severity == "note") | .number',
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error fetching alerts: {result.stderr}")
        return 0

    alert_numbers = [n.strip() for n in result.stdout.strip().split("\n") if n.strip()]

    if not alert_numbers:
        print("No CodeQL 'note' alerts found!")
        return 0

    total = len(alert_numbers)
    print(f"Found {total} CodeQL 'note' alerts to close")

    closed = 0
    failed = 0

    for i, alert_num in enumerate(alert_numbers, 1):
        # Close the alert
        close_cmd = [
            "gh",
            "api",
            f"repos/SHAdd0WTAka/Zen-Ai-Pentest/code-scanning/alerts/{alert_num}",
            "-X",
            "PATCH",
            "-F",
            "state=dismissed",
            "-F",
            "dismissed_reason=false_positive",
            "-F",
            "dismissed_comment=Bulk close: CodeQL code style note, not security vulnerability",
        ]

        result = subprocess.run(close_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            closed += 1
            if closed % 50 == 0:
                print(f"  Progress: {closed}/{total} closed...")
        else:
            failed += 1
            if failed % 10 == 0:
                print(f"  Failed: {failed} alerts")

        # Rate limiting - slow down
        if i % 30 == 0:
            time.sleep(2)

    print(f"\n✅ Closed {closed} alerts")
    if failed > 0:
        print(f"❌ Failed to close {failed} alerts")

    return closed


if __name__ == "__main__":
    print("=" * 60)
    print("Bulk Close CodeQL 'note' Alerts")
    print("=" * 60)
    print()

    confirm = input("This will close ALL CodeQL 'note' severity alerts. Continue? (yes/no): ")

    if confirm.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)

    print()
    count = close_alerts_batch()

    print()
    print("=" * 60)
    print(f"Done! Closed {count} alerts.")
    print("=" * 60)
