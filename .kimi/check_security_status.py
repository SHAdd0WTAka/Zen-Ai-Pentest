#!/usr/bin/env python3
"""Check detailed security status from GitHub API"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests

def check_detailed_alerts():
    """Get detailed information about open alerts"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github+json"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dependabot/alerts"
    params = {"state": "open", "per_page": 100}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        alerts = response.json()
        print(f"\n{'='*80}")
        print(f" OPEN DEPENDABOT ALERTS: {len(alerts)}")
        print(f"{'='*80}\n")
        
        for alert in alerts:
            adv = alert.get('security_advisory', {})
            dep = alert.get('dependency', {})
            pkg = dep.get('package', {})
            
            print(f"Alert #{alert.get('number')}")
            print(f"  Package: {pkg.get('name')} ({pkg.get('ecosystem')})")
            print(f"  Severity: {adv.get('severity', 'unknown').upper()}")
            print(f"  Current: {dep.get('version_requirement', 'N/A')}")
            print(f"  Vulnerable: {dep.get('vulnerable_requirement', 'N/A')}")
            print(f"  Fixed in: {adv.get('patched_versions', 'N/A')}")
            print(f"  File: {dep.get('manifest_path', 'N/A')}")
            print(f"  Title: {adv.get('summary', 'No summary')[:60]}...")
            print()
            
    else:
        print(f"Failed to get alerts: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    check_detailed_alerts()
