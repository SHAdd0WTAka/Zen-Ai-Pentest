#!/usr/bin/env python3
"""Get workflow run logs"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests

def get_latest_workflow_run(workflow_name="Test Coverage"):
    """Get latest run ID for a workflow"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
    params = {"per_page": 10}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        runs = response.json().get('workflow_runs', [])
        for run in runs:
            if run.get('name') == workflow_name:
                return run
    return None

def get_run_logs(run_id):
    """Get logs for a specific run"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    # Get run details
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        run = response.json()
        print(f"\nWorkflow: {run.get('name')}")
        print(f"Status: {run.get('status')}")
        print(f"Conclusion: {run.get('conclusion')}")
        print(f"URL: {run.get('html_url')}")

        # Get jobs
        jobs_url = run.get('jobs_url')
        jobs_resp = requests.get(jobs_url, headers=headers)

        if jobs_resp.status_code == 200:
            jobs = jobs_resp.json().get('jobs', [])
            print(f"\nJobs ({len(jobs)}):")
            for job in jobs:
                print(f"\n  - {job.get('name')}")
                print(f"    Status: {job.get('status')}")
                print(f"    Conclusion: {job.get('conclusion')}")

                # Get steps
                steps = job.get('steps', [])
                for step in steps:
                    if step.get('conclusion') == 'failure':
                        print(f"    FAILED STEP: {step.get('name')}")
                        print(f"      Status: {step.get('status')}")
                        print(f"      Number: {step.get('number')}")

if __name__ == "__main__":
    run = get_latest_workflow_run("Test Coverage")
    if run:
        get_run_logs(run.get('id'))
    else:
        print("No workflow run found")
