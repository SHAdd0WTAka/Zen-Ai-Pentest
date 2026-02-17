#!/usr/bin/env python3
"""Fix GitHub Pages source branch"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github_app_auth import get_installation_token, get_headers, REPO_OWNER, REPO_NAME
import requests

def fix_pages_source():
    """Update Pages source from master to main"""
    try:
        token = get_installation_token()
        headers = get_headers(token)

        print("Updating GitHub Pages source to 'main' branch...")

        # Update Pages configuration
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pages"
        data = {
            "source": {
                "branch": "main",
                "path": "/docs"
            }
        }

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 204:
            print("SUCCESS: Pages source updated to 'main' branch!")

            # Trigger a new Pages build by creating a dummy commit
            print("\nTriggering new Pages build...")

            # Get latest commit on main
            commits_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/main"
            commits_resp = requests.get(commits_url, headers=headers)

            if commits_resp.status_code == 200:
                latest_sha = commits_resp.json().get('sha')
                print(f"Latest commit: {latest_sha[:7]}")

                # Create a Pages build request
                build_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pages/builds"
                build_resp = requests.post(build_url, headers=headers)

                if build_resp.status_code == 201:
                    print("Pages build triggered successfully!")
                else:
                    print(f"Build trigger status: {build_resp.status_code}")

            return True
        else:
            print(f"Failed to update: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    fix_pages_source()
