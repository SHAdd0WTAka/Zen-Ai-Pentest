#!/usr/bin/env python3
"""Setup Kimi Claw Integration for Zen-AI-Pentest"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests
import json

def create_or_update_secret(secret_name, secret_value):
    """Create or update a GitHub repository secret"""
    # Note: In real usage, you'd need to encrypt the secret with the repo's public key
    # For now, we just provide instructions
    print(f"\n📋 Secret: {secret_name}")
    print(f"   Value: {secret_value[:20]}..." if len(str(secret_value)) > 20 else f"   Value: {secret_value}")
    return True

def setup_kimi_claw():
    """Interactive setup for Kimi Claw"""
    print("=" * 70)
    print(" 🤖 KIMI CLAW INTEGRATION SETUP")
    print("=" * 70)
    print()
    print("Kimi Claw acts as a unified gateway for all repository notifications.")
    print("Instead of managing Discord, Telegram, and Slack separately,")
    print("Claw receives all events and distributes them intelligently.")
    print()
    print("=" * 70)

    # Check current secrets
    print("\n📊 Current Configuration:")
    secrets_needed = [
        ("KIMI_CLAW_TOKEN", "API Token from Kimi Claw", "Required for Claw integration"),
        ("KIMI_CLAW_API_URL", "Claw API endpoint", "Optional (defaults to Moonshot)"),
        ("KIMI_CLAW_DISCORD_ENABLED", "Enable Discord output", "true/false"),
        ("KIMI_CLAW_TELEGRAM_ENABLED", "Enable Telegram output", "true/false"),
        ("KIMI_CLAW_SLACK_ENABLED", "Enable Slack output", "true/false"),
    ]

    for secret_name, description, note in secrets_needed:
        print(f"\n  • {secret_name}")
        print(f"    Purpose: {description}")
        print(f"    Note: {note}")

    print("\n" + "=" * 70)
    print(" SETUP INSTRUCTIONS")
    print("=" * 70)

    print("""
1. GET YOUR KIMI CLAW TOKEN:
   - Go to: https://claw.moonshot.cn or your Kimi Claw dashboard
   - Navigate to: Settings → API Tokens
   - Generate a new token for this repository
   - Copy the token (starts with 'claw_')

2. ADD SECRETS TO GITHUB:
   URL: https://github.com/{REPO_OWNER}/{REPO_NAME}/settings/secrets/actions

   Add these secrets:

   Name: KIMI_CLAW_TOKEN
   Value: [Your token from step 1]

   Name: KIMI_CLAW_DISCORD_ENABLED
   Value: true

   Name: KIMI_CLAW_TELEGRAM_ENABLED
   Value: true

3. TEST THE INTEGRATION:
   - Go to Actions → Kimi Claw Gateway
   - Click "Run workflow"
   - Enter a test message
   - Check if you receive notifications

4. CUSTOMIZE EVENTS (Optional):
   Edit .github/workflows/kimi-claw-gateway.yml to:
   - Add/remove event types
   - Customize message formats
   - Add filters (e.g., only notify on failures)
""".format(REPO_OWNER=REPO_OWNER, REPO_NAME=REPO_NAME))

    print("=" * 70)
    print(" WORKFLOW FEATURES")
    print("=" * 70)
    print("""
The Kimi Claw Gateway automatically handles:

✅ Push Events → Commit summaries
✅ Pull Requests → Open/merge/close notifications
✅ Issues → New/resolved issue alerts
✅ Workflow Runs → CI/CD status updates
✅ Security Alerts → Vulnerability notifications

Smart Features:
• Severity levels (info/warning/error/success)
• Emoji indicators for quick visual parsing
• Direct links to commits, PRs, and issues
• Fallback to Discord/Telegram if Claw is unavailable
""")

    print("=" * 70)
    print(" NEXT STEPS")
    print("=" * 70)
    print("""
1. Add the secrets above to your repository
2. The workflow will activate automatically
3. Make a test commit to verify notifications
4. Adjust settings in the workflow file as needed

Need help? Check the workflow file:
.github/workflows/kimi-claw-gateway.yml
""")

def test_notification():
    """Test the notification setup"""
    print("\n" + "=" * 70)
    print(" TEST NOTIFICATION")
    print("=" * 70)
    print("\nTriggering test notification...")
    print("(Requires KIMI_CLAW_TOKEN to be set)")
    print("\nRun this command to test manually:")
    print(f"  gh workflow run kimi-claw-gateway.yml -R {REPO_OWNER}/{REPO_NAME}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test the setup")
    args = parser.parse_args()

    if args.test:
        test_notification()
    else:
        setup_kimi_claw()
