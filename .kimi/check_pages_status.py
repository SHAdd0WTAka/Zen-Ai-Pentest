#!/usr/bin/env python3
"""Check GitHub Pages deployment status"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from github_app_auth import get_installation_token, get_headers, APP_ID, INSTALLATION_ID, REPO_OWNER, REPO_NAME
import requests

def check_pages_status():
    """Check GitHub Pages build status"""
    try:
        token = get_installation_token()
        headers = get_headers(token)

        # Get Pages information
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pages"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            pages_info = response.json()
            print("\n" + "="*60)
            print(" GITHUB PAGES STATUS")
            print("="*60)
            print(f"Status: {pages_info.get('status', 'Unknown')}")
            print(f"URL: {pages_info.get('html_url', 'N/A')}")
            print(f"Source: {pages_info.get('source', {}).get('branch', 'N/A')}")
            print(f"Build Type: {pages_info.get('build_type', 'N/A')}")
        else:
            print(f"Could not get Pages info: {response.status_code}")

        # Get latest deployment
        deploy_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/deployments"
        deploy_response = requests.get(deploy_url, headers=headers, params={"environment": "github-pages"})

        if deploy_response.status_code == 200:
            deployments = deploy_response.json()
            if deployments:
                latest = deployments[0]
                print(f"\n LATEST DEPLOYMENT")
                print(f"Created: {latest.get('created_at', 'N/A')}")
                print(f"Creator: {latest.get('creator', {}).get('login', 'N/A')}")

                # Get deployment status
                status_url = latest.get('statuses_url')
                if status_url:
                    status_resp = requests.get(status_url, headers=headers)
                    if status_resp.status_code == 200:
                        statuses = status_resp.json()
                        if statuses:
                            latest_status = statuses[0]
                            print(f"State: {latest_status.get('state', 'Unknown').upper()}")
                            print(f"Description: {latest_status.get('description', 'N/A')}")
                            print(f"Updated: {latest_status.get('updated_at', 'N/A')}")
                        else:
                            print("State: No status available")

        # Check recent workflow runs for Pages
        runs_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
        runs_resp = requests.get(runs_url, headers=headers, params={"per_page": 10})

        if runs_resp.status_code == 200:
            runs = runs_resp.json().get('workflow_runs', [])
            pages_runs = [r for r in runs if 'pages' in r.get('name', '').lower()]

            if pages_runs:
                print(f"\n RECENT PAGES WORKFLOW RUNS")
                for run in pages_runs[:3]:
                    status_icon = "[OK]" if run.get('conclusion') == 'success' else "[FAIL]" if run.get('conclusion') == 'failure' else "[PENDING]"
                    print(f"  {status_icon} {run.get('name')} - {run.get('conclusion') or run.get('status')}")

        print("="*60)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_pages_status()
