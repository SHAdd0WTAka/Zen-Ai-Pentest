#!/usr/bin/env python3
"""Add Codecov token to GitHub repository secrets"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64

import requests
from github_app_auth import (
    REPO_NAME,
    REPO_OWNER,
    get_headers,
    get_installation_token,
)
from nacl import encoding, public


def get_public_key():
    """Get repository public key for secret encryption"""
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/public-key"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get public key: {response.status_code}")
        print(response.text)
        return None


def encrypt_secret(public_key, secret_value):
    """Encrypt secret using repository public key"""
    public_key = public.PublicKey(
        public_key.encode("utf-8"), encoding.Base64Encoder()
    )
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def create_secret(secret_name, secret_value):
    """Create or update a repository secret"""
    # Get public key
    key_info = get_public_key()
    if not key_info:
        return False

    key_id = key_info.get("key_id")
    public_key = key_info.get("key")

    # Encrypt secret
    encrypted_value = encrypt_secret(public_key, secret_value)

    # Create/update secret
    token = get_installation_token()
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3+json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/{secret_name}"

    data = {"encrypted_value": encrypted_value, "key_id": key_id}

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [201, 204]:
        print(f"[OK] Secret '{secret_name}' created/updated successfully")
        return True
    else:
        print(f"[FAIL] Failed to create secret: {response.status_code}")
        print(response.text)
        return False


def main():
    print("=" * 60)
    print(" ADD CODECOV TOKEN TO GITHUB SECRETS")
    print("=" * 60)
    print()
    print("You need to provide your Codecov upload token.")
    print()
    print("Get it from:")
    print("  https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest/settings")
    print()

    # Note: We can't easily get user input in this environment
    # So we provide instructions instead
    print("INSTRUCTIONS:")
    print("1. Go to https://codecov.io/gh/SHAdd0WTAka/Zen-Ai-Pentest")
    print("2. Sign in with GitHub")
    print("3. Go to Settings")
    print("4. Copy the 'Repository Upload Token'")
    print("5. Add it to GitHub:")
    print(
        "   https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions"
    )
    print("   Name: CODECOV_TOKEN")
    print("   Value: [paste token]")


if __name__ == "__main__":
    main()
