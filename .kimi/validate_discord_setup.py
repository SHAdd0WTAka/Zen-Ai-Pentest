#!/usr/bin/env python3
"""Validate Discord integration setup for ZenClaw"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from github_app_auth import (
    REPO_NAME,
    REPO_OWNER,
    get_headers,
    get_installation_token,
)


def check_discord_secret():
    """Check if Discord webhook secret exists"""
    print("=" * 60)
    print(" ZENCLAW DISCORD VALIDATION")
    print("=" * 60)

    # Note: We can't actually read the secret value (that's good!)
    # But we can check if the workflow would find it
    print("\n[1/3] Checking GitHub Secrets...")
    print("  Secret Name: DISCORD_WEBHOOK_URL")
    print("  Status: Must be set manually in GitHub UI")
    print(
        "  URL: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions"
    )
    print("  [WARN] This cannot be checked via API (security feature)")

    print("\n[2/3] Checking Workflow File...")
    workflow_path = ".github/workflows/zenclaw-discord.yml"
    if os.path.exists(workflow_path):
        print(f"  [OK] Workflow exists: {workflow_path}")
        with open(workflow_path, "r") as f:
            content = f.read()
            if "DISCORD_WEBHOOK_URL" in content:
                print("  [OK] References DISCORD_WEBHOOK_URL secret")
            if "secrets.DISCORD_WEBHOOK" in content:
                print("  [OK] Uses secrets context (secure)")
    else:
        print(f"  [FAIL] Workflow not found: {workflow_path}")

    print("\n[3/3] Checking Documentation...")
    doc_path = "docs/DISCORD_SETUP_ZENCLAW.md"
    if os.path.exists(doc_path):
        print(f"  [OK] Documentation exists: {doc_path}")
    else:
        print(f"  [FAIL] Documentation not found: {doc_path}")

    print("\n" + "=" * 60)
    print(" VALIDATION COMPLETE")
    print("=" * 60)

    print("\n NEXT STEPS:")
    print("1. Create Discord Webhook (see docs/DISCORD_SETUP_ZENCLAW.md)")
    print("2. Add DISCORD_WEBHOOK_URL to GitHub Secrets")
    print("3. Run workflow test via GitHub Actions")
    print("4. Verify message appears in Discord")

    print("\n SECURITY REMINDER:")
    print("• Never commit webhook URLs")
    print("• Never log webhook URLs")
    print("• Only store in GitHub Secrets")


if __name__ == "__main__":
    check_discord_secret()
