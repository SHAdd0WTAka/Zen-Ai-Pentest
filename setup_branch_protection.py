#!/usr/bin/env python3
"""
Setup Branch Protection for Zen AI Pentest Repository
"""

import os
import sys

import requests


def setup_branch_protection():
    """Configure branch protection rules for master branch"""

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub personal access token:")
        print("  set GITHUB_TOKEN=your_token_here")
        sys.exit(1)

    owner = "SHAdd0WTAka"
    repo = "Zen-Ai-Pentest"
    branch = "master"

    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Branch protection configuration
    data = {
        "required_status_checks": {
            "strict": True,
            "contexts": [
                "backend (3.13)",
                "frontend",
                "pre-commit",
                "docker",
                "ci-summary",
            ],
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_last_push_approval": False,
        },
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "required_conversation_resolution": True,
        "lock_branch": False,
    }

    print("🔐 Setting up Branch Protection for Zen AI Pentest...")
    print(f"   Repository: {owner}/{repo}")
    print(f"   Branch: {branch}")
    print()

    try:
        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 200:
            print("✅ Branch Protection successfully configured!")
            print()
            print("📋 Configuration Summary:")
            print("   ✅ Require pull request before merging")
            print("   ✅ Require 1 approving review")
            print("   ✅ Dismiss stale reviews")
            print("   ✅ Require status checks to pass")
            print("   ✅ Require branches to be up to date")
            print("   ✅ Block force pushes")
            print("   ✅ Block deletions")
            print("   ✅ Require conversation resolution")
            print()
            print("🔗 View settings:")
            print(f"   https://github.com/{owner}/{repo}/settings/branches")
            return True
        elif response.status_code == 404:
            print("❌ Error: Repository or branch not found")
            print("   Make sure the repository exists and you have access")
            return False
        elif response.status_code == 403:
            print("❌ Error: Permission denied")
            print("   Your token needs 'repo' scope for private repositories")
            print("   or 'public_repo' scope for public repositories")
            print()
            print("   To create a token:")
            print("   1. Go to https://github.com/settings/tokens")
            print("   2. Click 'Generate new token (classic)'")
            print("   3. Select 'repo' scope")
            print("   4. Generate and copy the token")
            return False
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print("❌ Error: Network request failed")
        print(f"   {e}")
        return False


def verify_branch_protection():
    """Verify current branch protection settings"""

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return False

    owner = "SHAdd0WTAka"
    repo = "Zen-Ai-Pentest"
    branch = "master"

    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            protection = response.json()
            print("\n📊 Current Branch Protection Status:")
            print("   Enabled: ✅")
            if "required_status_checks" in protection:
                print("   Status Checks: ✅")
            if "required_pull_request_reviews" in protection:
                print("   PR Reviews: ✅")
            if not protection.get("allow_force_pushes", {}).get("enabled"):
                print("   Force Push Blocked: ✅")
            if not protection.get("allow_deletions", {}).get("enabled"):
                print("   Deletion Blocked: ✅")
            return True
        elif response.status_code == 404:
            print("\n⚠️  Branch Protection: Not configured")
            return False
        else:
            print(
                f"\n⚠️  Could not verify status (HTTP {response.status_code})"
            )
            return False
    except Exception as e:
        print(f"\n⚠️  Could not verify status: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("   Zen AI Pentest - Branch Protection Setup")
    print("=" * 60)
    print()

    # First verify current status
    verify_branch_protection()

    print()
    print("📝 This script will configure:")
    print("   • Require pull request before merging (1 approval)")
    print("   • Require status checks (CI/CD pipeline)")
    print("   • Block force pushes")
    print("   • Block branch deletions")
    print()

    if input("Continue? (y/n): ").lower() == "y":
        success = setup_branch_protection()
        sys.exit(0 if success else 1)
    else:
        print("\n❌ Setup cancelled")
        print("\nYou can manually configure branch protection at:")
        print(
            "   https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/branches"
        )
        sys.exit(0)
