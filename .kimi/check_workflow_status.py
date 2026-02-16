#!/usr/bin/env python3
"""Check workflow run status"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests
import time

def check_workflow_status(workflow_name="coverage"):
    """Check latest workflow run status"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"
    
    # Get latest workflow runs
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    params = {"per_page": 5}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        runs = response.json().get('workflow_runs', [])
        
        print("\n" + "=" * 60)
        print(" RECENT WORKFLOW RUNS")
        print("=" * 60)
        
        for run in runs:
            wf_name = run.get('name', 'Unknown')
            status = run.get('status', 'unknown')
            conclusion = run.get('conclusion') or 'N/A'
            
            # Status text
            if conclusion == 'success':
                icon = "[OK]"
            elif conclusion == 'failure':
                icon = "[FAIL]"
            elif status == 'in_progress':
                icon = "[RUNNING]"
            elif status == 'queued':
                icon = "[QUEUED]"
            else:
                icon = "[?]"
            
            print(f"\n{icon} {wf_name}")
            print(f"   Status: {status}")
            if conclusion != 'N/A':
                print(f"   Result: {conclusion}")
            print(f"   Branch: {run.get('head_branch', 'N/A')}")
            print(f"   Started: {run.get('created_at', 'N/A')}")
            print(f"   URL: {run.get('html_url', 'N/A')}")
        
        print("\n" + "=" * 60)
    else:
        print(f"Failed to get workflow runs: {response.status_code}")

if __name__ == "__main__":
    check_workflow_status()
