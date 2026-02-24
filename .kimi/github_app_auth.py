#!/usr/bin/env python3
"""GitHub App Authentication Module"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import requests

# Configuration
APP_ID = "2872904"
INSTALLATION_ID = "110359081"
REPO_OWNER = "SHAdd0WTAka"
REPO_NAME = "Zen-Ai-Pentest"

# Private key path
PRIVATE_KEY_PATH = os.environ.get(
    "GITHUB_APP_KEY_PATH",
    r"G:\zen-ai-pentest-kimi-assistant.2026-02-15.private-key.pem",
)


def generate_jwt():
    """Generate JWT for GitHub App authentication"""
    now = datetime.now(timezone.utc)
    payload = {"iat": now, "exp": now + timedelta(minutes=10), "iss": APP_ID}

    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token():
    """Get installation access token"""
    jwt_token = generate_jwt()

    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.post(url, headers=headers)

    if response.status_code == 201:
        return response.json()["token"]
    else:
        raise Exception(
            f"Failed to get installation token: {response.status_code} - {response.text}"
        )


def get_headers(token=None):
    """Get headers with authentication"""
    if token is None:
        token = get_installation_token()

    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


if __name__ == "__main__":
    # Test authentication
    try:
        token = get_installation_token()
        headers = get_headers(token)

        # Test API access
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            repo_info = response.json()
            print(f"✅ Authentication successful!")
            print(f"Repository: {repo_info['full_name']}")
            print(f"Default branch: {repo_info['default_branch']}")
        else:
            print(f"❌ Failed to access repository: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
