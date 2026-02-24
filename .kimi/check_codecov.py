#!/usr/bin/env python3
"""Check Codecov coverage status via API"""

import json

import requests

REPO_OWNER = "SHAdd0WTAka"
REPO_NAME = "Zen-Ai-Pentest"


def check_codecov():
    """Get coverage data from Codecov API"""

    # Codecov API endpoint
    url = (
        f"https://api.codecov.io/api/v2/github/{REPO_OWNER}/repos/{REPO_NAME}/"
    )

    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("=" * 60)
            print(" CODECOV API RESPONSE")
            print("=" * 60)
            print(f"\nRepository: {data.get('name')}")
            print(f"Coverage: {data.get('coverage')}%")
            print(f"Branch: {data.get('branch')}")
            print(f"Updated: {data.get('updated_at')}")
            print(
                f"Commit: {data.get('head_commit', {}).get('commitid', 'N/A')[:8] if data.get('head_commit') else 'N/A'}"
            )
            print("\n" + "=" * 60)
            return True
        else:
            print(f"API Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def check_badge_url():
    """Check badge URL directly"""
    print("\n" + "=" * 60)
    print(" BADGE URL CHECK")
    print("=" * 60)

    badge_url = (
        f"https://codecov.io/gh/{REPO_OWNER}/{REPO_NAME}/graph/badge.svg"
    )
    print(f"\nBadge URL: {badge_url}")

    try:
        response = requests.get(badge_url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            # Badge SVG content
            content = response.text

            # Extract percentage from SVG
            if "percent" in content or "%" in content:
                # Try to find percentage in SVG
                import re

                match = re.search(r">(\d+)%<", content)
                if match:
                    print(f"\n[OK] Badge zeigt: {match.group(1)}% Coverage")
                else:
                    print(
                        f"\n[WARN] Badge geladen, aber Prozent nicht erkannt"
                    )
                    print(f"   (Erster Teil SVG: {content[:200]}...)")
            else:
                print(
                    f"\n[WARN] Badge zeigt wahrscheinlich 'unknown' oder '0%'"
                )
                print(f"   (Erster Teil SVG: {content[:200]}...)")
        else:
            print(f"[FAIL] Badge nicht erreichbar: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    check_codecov()
    check_badge_url()
