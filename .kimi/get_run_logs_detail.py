#!/usr/bin/env python3
"""Get detailed workflow run logs"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests
import zipfile
import io

def get_latest_coverage_run():
    """Get latest Test Coverage run"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    params = {"per_page": 10}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        runs = response.json().get('workflow_runs', [])
        for run in runs:
            if run.get('name') == 'Test Coverage':
                return run
    return None

def get_job_logs(run_id):
    """Get job logs"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    # Get jobs
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        jobs = response.json().get('jobs', [])

        for job in jobs:
            print(f"\nJob: {job.get('name')}")
            print(f"Status: {job.get('status')}")
            print(f"Conclusion: {job.get('conclusion')}")
            print("\nSteps:")

            for step in job.get('steps', []):
                status = step.get('status', 'unknown')
                conclusion = step.get('conclusion', 'N/A')

                # Status indicator
                if conclusion == 'success':
                    icon = "[OK]"
                elif conclusion == 'failure':
                    icon = "[FAIL]"
                elif status == 'in_progress':
                    icon = "[RUNNING]"
                else:
                    icon = "[PENDING]"

                print(f"  {icon} {step.get('name')}")

                # Show failed step details
                if conclusion == 'failure':
                    print(f"       -> FAILED!")

if __name__ == "__main__":
    run = get_latest_coverage_run()
    if run:
        print(f"Run ID: {run.get('id')}")
        print(f"Run URL: {run.get('html_url')}")
        get_job_logs(run.get('id'))
    else:
        print("No Test Coverage run found")
