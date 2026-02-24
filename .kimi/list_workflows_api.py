#!/usr/bin/env python3
"""List workflows from GitHub API"""

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


def list_workflows():
    """List all workflows from API"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        workflows = response.json().get("workflows", [])
        print(f"\nTotal workflows: {len(workflows)}\n")
        print("=" * 60)

        for wf in workflows:
            name = wf.get("name", "Unknown")
            state = wf.get("state", "unknown")
            path = wf.get("path", "").replace(".github/workflows/", "")

            # Check if it has workflow_dispatch
            has_dispatch = "workflow_dispatch" in str(
                wf.get("raw_content", "")
            )

            print(f"\n{name}")
            print(f"  File: {path}")
            print(f"  State: {state}")
            print(f"  ID: {wf.get('id')}")

            if "coverage" in name.lower():
                print(f"  >>> COVERAGE WORKFLOW FOUND <<<")
    else:
        print(f"Failed: {response.status_code}")
        print(response.text[:500])


if __name__ == "__main__":
    list_workflows()
