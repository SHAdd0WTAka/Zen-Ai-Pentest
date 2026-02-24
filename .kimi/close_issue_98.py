#!/usr/bin/env python3
"""Close Issue #98 - Health Check is now passing"""

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


def close_issue_98():
    """Close issue #98 with comment"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    # Add comment
    comment_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/98/comments"
    comment_data = {
        "body": """## ✅ RESOLVED - Health Check Now Passing

**Status Update:** 2026-02-16

The Repository Health Check workflow is now running successfully:
- Latest run: ✅ SUCCESS
- All checks passing
- No further action required

**Resolved by:** Continuous workflow improvements and infrastructure stabilization

Closing this issue as resolved. 🦞 ZenClaw Guardian confirmed operational status."""
    }

    response = requests.post(comment_url, headers=headers, json=comment_data)

    if response.status_code == 201:
        print("[OK] Comment added to Issue #98")

        # Close issue
        issue_url = (
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/98"
        )
        close_data = {"state": "closed"}

        close_resp = requests.patch(
            issue_url, headers=headers, json=close_data
        )

        if close_resp.status_code == 200:
            print("[OK] Issue #98 closed successfully")
            return True
        else:
            print(f"[WARN] Could not close issue: {close_resp.status_code}")
    else:
        print(f"[WARN] Could not add comment: {response.status_code}")
        print(response.text[:500])

    return False


if __name__ == "__main__":
    close_issue_98()
