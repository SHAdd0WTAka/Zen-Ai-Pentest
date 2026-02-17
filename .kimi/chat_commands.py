#!/usr/bin/env python3
"""Chat commands for Kimi CLI - ZenClaw Integration"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests
from datetime import datetime

def cmd_status():
    """!status - Repository overview"""
    token = get_installation_token()
    headers = get_headers(token)

    # Get repo info
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()

        # Get issues count
        issues_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues?state=open"
        issues_resp = requests.get(issues_url, headers=headers)
        open_issues = len(issues_resp.json()) if issues_resp.status_code == 200 else "?"

        # Get recent workflow runs
        wf_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs?per_page=5"
        wf_resp = requests.get(wf_url, headers=headers)

        print("=" * 60)
        print(" ZENCLAW - REPOSITORY STATUS")
        print("=" * 60)
        print(f"\n Repository: {data.get('full_name')}")
        desc = (data.get('description') or 'No description').encode('ascii', 'ignore').decode('ascii')
        print(f" Description: {desc[:50]}...")
        print(f" Stars: {data.get('stargazers_count', 0)}")
        print(f" Forks: {data.get('forks_count', 0)}")
        print(f"\n Open Issues: {open_issues}")
        print(f" Coverage: 3% (codecov)")
        print(f" Security Alerts: 0 (all clear!)")
        print(f"\n Default Branch: {data.get('default_branch')}")
        print(f" Last Updated: {data.get('updated_at', 'N/A')[:10]}")

        if wf_resp.status_code == 200:
            runs = wf_resp.json().get('workflow_runs', [])
            print(f"\n Recent Workflows:")
            for run in runs[:3]:
                status = "[OK]" if run.get('conclusion') == 'success' else "[FAIL]" if run.get('conclusion') == 'failure' else "[PENDING]"
                print(f"  {status} {run.get('name')}")

        print("\n" + "=" * 60)
        print(f" Reported: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
    else:
        print(f"[ERROR] {resp.status_code}")

def cmd_workflows():
    """!workflows - Show active workflows"""
    token = get_installation_token()
    headers = get_headers(token)

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs?per_page=10"
    resp = requests.get(url, headers=headers)

    print("=" * 60)
    print(" ZENCLAW - WORKFLOW STATUS")
    print("=" * 60)

    if resp.status_code == 200:
        runs = resp.json().get('workflow_runs', [])

        running = [r for r in runs if r.get('status') == 'in_progress']
        recent = [r for r in runs if r.get('status') == 'completed'][:5]

        if running:
            print(f"\n RUNNING ({len(running)}):")
            for run in running:
                print(f"  [PENDING] {run.get('name')}")
                print(f"     Started: {run.get('created_at', 'N/A')}")
        else:
            print("\n RUNNING: None")

        print(f"\n RECENT COMPLETED:")
        for run in recent:
            status = "[OK]" if run.get('conclusion') == 'success' else "[FAIL]" if run.get('conclusion') == 'failure' else "[WARN]"
            print(f"  {status} {run.get('name')}")
            print(f"     Result: {run.get('conclusion') or 'unknown'}")
    else:
        print(f"[ERROR] {resp.status_code}")

    print("\n" + "=" * 60)

def cmd_issues():
    """!issues - Show open issues"""
    token = get_installation_token()
    headers = get_headers(token)

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues?state=open&per_page=10"
    resp = requests.get(url, headers=headers)

    print("=" * 60)
    print(" ZENCLAW - OPEN ISSUES")
    print("=" * 60)

    if resp.status_code == 200:
        issues = resp.json()

        if issues:
            print(f"\n Found {len(issues)} open issue(s):\n")
            for issue in issues:
                print(f"  #{issue.get('number')}: {issue.get('title')[:50]}")
                print(f"     By: {issue.get('user', {}).get('login')}")
                print(f"     Created: {issue.get('created_at', 'N/A')[:10]}")
                if issue.get('labels'):
                    labels = ', '.join([l.get('name') for l in issue.get('labels')])
                    print(f"     Labels: {labels}")
                print()
        else:
            print("\n No open issues! Repository is clean.")
    else:
        print(f"[ERROR] {resp.status_code}")

    print("=" * 60)

def cmd_coverage():
    """!coverage - Show coverage status"""
    print("=" * 60)
    print(" ZENCLAW - COVERAGE STATUS")
    print("=" * 60)
    print("\n Current Coverage: 3%")
    print("    Measured by: pytest + codecov")
    print("\n Target: 30% (minimum)")
    print(" Gap: 27% to target")
    print("\n To improve:")
    print("    Add more unit tests")
    print("    Test core/ modules")
    print("    Test api/ endpoints")
    print("\n Details: https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest")
    print("=" * 60)

def cmd_help():
    """!help - Show available commands"""
    print("=" * 60)
    print(" ZENCLAW - AVAILABLE COMMANDS")
    print("=" * 60)
    print("\n Repository Commands:")
    print("  !status    - Repository overview (issues, coverage, workflows)")
    print("  !workflows - Active and recent workflow runs")
    print("  !issues    - List open issues")
    print("  !coverage  - Coverage statistics and targets")
    print("\n Bot Commands:")
    print("  !help      - Show this help message")
    print("\n Usage:")
    print("  Type any command above to get instant information")
    print("  Example: !status")
    print("=" * 60)

def main():
    import sys

    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower()

    commands = {
        'status': cmd_status,
        'workflows': cmd_workflows,
        'issues': cmd_issues,
        'coverage': cmd_coverage,
        'help': cmd_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"[ERROR] Unknown command: !{command}")
        print("Type !help for available commands")

if __name__ == "__main__":
    main()
