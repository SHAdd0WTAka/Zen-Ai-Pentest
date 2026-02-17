#!/usr/bin/env python3
"""Dismiss specific Dependabot alert"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests

def dismiss_alert(alert_number, reason="tolerable_risk", comment=""):
    """Dismiss a specific Dependabot alert"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dependabot/alerts/{alert_number}"

    data = {
        "state": "dismissed",
        "dismissed_reason": reason,
        "dismissed_comment": comment or f"Dismissed: Already on latest stable version"
    }

    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"[OK] Alert #{alert_number} dismissed successfully")
        return True
    else:
        print(f"[FAIL] Could not dismiss alert #{alert_number}: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("alert_number", type=int, help="Alert number to dismiss")
    parser.add_argument("--reason", default="tolerable_risk",
                       choices=["fix_started", "inaccurate", "no_bandwidth", "not_used", "tolerable_risk"])
    parser.add_argument("--comment", default="", help="Dismissal comment")
    args = parser.parse_args()

    dismiss_alert(args.alert_number, args.reason, args.comment)
