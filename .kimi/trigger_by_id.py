#!/usr/bin/env python3
"""Trigger workflow by ID"""

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


def trigger_by_id(workflow_id, branch="main"):
    """Trigger workflow using ID"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{workflow_id}/dispatches"

    data = {"ref": branch}

    response = requests.post(url, headers=headers, json=data)

    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"[OK] Workflow {workflow_id} triggered!")
    else:
        print(f"Response: {response.text}")


if __name__ == "__main__":
    # Coverage workflow ID from earlier
    trigger_by_id(229137469, "main")
