#!/usr/bin/env python3
"""Trigger a GitHub Actions workflow manually"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests
import json

def trigger_workflow(workflow_id, branch="main"):
    """Trigger a workflow dispatch event"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{workflow_id}/dispatches"
    
    data = {
        "ref": branch
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 204:
        print(f"[OK] Workflow '{workflow_id}' triggered successfully on branch '{branch}'")
        print(f"     Check status at: https://github.com/{REPO_OWNER}/{REPO_NAME}/actions")
        return True
    else:
        print(f"[FAIL] Failed to trigger workflow: {response.status_code}")
        print(response.text)
        return False

def list_workflows():
    """List available workflows"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        workflows = response.json().get('workflows', [])
        print(f"\nAvailable workflows ({len(workflows)}):")
        print("-" * 60)
        for wf in workflows:
            state = "✓" if wf.get('state') == "active" else "✗"
            print(f"{state} {wf.get('name')}")
            print(f"   ID: {wf.get('id')}")
            print(f"   File: {wf.get('path', '').replace('.github/workflows/', '')}")
            print()
    else:
        print(f"Failed to list workflows: {response.status_code}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", nargs="?", help="Workflow ID or filename")
    parser.add_argument("--branch", default="main", help="Branch to run on")
    parser.add_argument("--list", action="store_true", help="List workflows")
    args = parser.parse_args()
    
    if args.list:
        list_workflows()
    elif args.workflow:
        trigger_workflow(args.workflow, args.branch)
    else:
        # Default: trigger coverage workflow
        trigger_workflow("coverage.yml", "main")
