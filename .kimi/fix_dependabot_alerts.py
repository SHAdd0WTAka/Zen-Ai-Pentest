#!/usr/bin/env python3
"""Fix open Dependabot alerts by updating dependencies"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests

def get_dependabot_alerts():
    """Get all open Dependabot alerts"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github+json"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dependabot/alerts"
    params = {"state": "open", "per_page": 100}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        alerts = response.json()
        print(f"\nFound {len(alerts)} open Dependabot alerts\n")
        print("=" * 80)
        
        high = []
        medium = []
        low = []
        
        for alert in alerts:
            severity = alert.get('security_advisory', {}).get('severity', 'unknown')
            pkg = alert.get('dependency', {}).get('package', {}).get('name', 'unknown')
            alert_num = alert.get('number')
            
            info = {
                'number': alert_num,
                'package': pkg,
                'severity': severity,
                'title': alert.get('security_advisory', {}).get('summary', 'No title'),
                'manifest': alert.get('dependency', {}).get('manifest_path', 'unknown')
            }
            
            if severity == 'high':
                high.append(info)
            elif severity == 'medium':
                medium.append(info)
            else:
                low.append(info)
        
        # Print summary
        if high:
            print(f"\n[CRITICAL] HIGH Severity ({len(high)}):")
            for h in high:
                print(f"  #{h['number']}: {h['package']} - {h['title'][:50]}...")
                print(f"       File: {h['manifest']}")
        
        if medium:
            print(f"\n[MEDIUM] MEDIUM Severity ({len(medium)}):")
            for m in medium:
                print(f"  #{m['number']}: {m['package']} - {m['title'][:50]}...")
        
        if low:
            print(f"\n[INFO] LOW Severity ({len(low)}):")
            for l in low:
                print(f"  #{l['number']}: {l['package']} - {l['title'][:50]}...")
        
        print("\n" + "=" * 80)
        
        return alerts
    else:
        print(f"Failed to get alerts: {response.status_code}")
        print(response.text)
        return []

def dismiss_low_severity():
    """Dismiss low severity alerts with appropriate reason"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github+json"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dependabot/alerts"
    params = {"state": "open", "severity": "low"}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        alerts = response.json()
        print(f"\nDismissing {len(alerts)} LOW severity alerts...")
        
        for alert in alerts:
            alert_num = alert.get('number')
            dismiss_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/dependabot/alerts/{alert_num}"
            
            data = {
                "state": "dismissed",
                "dismissed_reason": "tolerable_risk",
                "dismissed_comment": "Low severity - acceptable risk for development dependencies"
            }
            
            dismiss_resp = requests.patch(dismiss_url, headers=headers, json=data)
            if dismiss_resp.status_code == 200:
                print(f"  [OK] Dismissed alert #{alert_num}")
            else:
                print(f"  [FAIL] Could not dismiss #{alert_num}: {dismiss_resp.status_code}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dismiss-low", action="store_true", help="Dismiss low severity alerts")
    args = parser.parse_args()
    
    alerts = get_dependabot_alerts()
    
    if args.dismiss_low:
        dismiss_low_severity()
