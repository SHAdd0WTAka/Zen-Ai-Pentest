#!/usr/bin/env python3
"""
Generate GitHub App Installation Access Token
Uses Private Key to authenticate as the GitHub App
"""
import sys
import time
from pathlib import Path

import jwt
import requests

# GitHub App Configuration
APP_ID = "2872904"
PRIVATE_KEY_PATH = (
    Path.home()
    / "Downloads"
    / "zen-ai-pentest-kimi-assistant.2026-02-23.private-key.pem"
)


def generate_jwt():
    """Generate JWT from App ID and Private Key"""
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID,
    }  # 10 minutes expiry

    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


def get_installation_token(jwt_token):
    """Exchange JWT for Installation Access Token"""
    # First, get the installation ID
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get installations
    resp = requests.get(
        "https://api.github.com/app/installations", headers=headers
    )
    resp.raise_for_status()
    installations = resp.json()

    if not installations:
        print("❌ No installations found!")
        sys.exit(1)

    installation_id = installations[0]["id"]
    print(f"✅ Found Installation ID: {installation_id}")

    # Generate access token for this installation
    resp = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers,
    )
    resp.raise_for_status()

    return resp.json()["token"]


def main():
    print("🔐 Generating GitHub App Installation Token...")
    print(f"   App ID: {APP_ID}")
    print(f"   Private Key: {PRIVATE_KEY_PATH}")

    if not PRIVATE_KEY_PATH.exists():
        print(f"❌ Private key not found at {PRIVATE_KEY_PATH}")
        print("   Bitte passe PRIVATE_KEY_PATH im Script an!")
        sys.exit(1)

    try:
        # Generate JWT
        jwt_token = generate_jwt()
        print("✅ JWT generated successfully")

        # Get installation token
        token = get_installation_token(jwt_token)
        print("\n" + "=" * 60)
        print("🎉 INSTALLATION ACCESS TOKEN:")
        print("=" * 60)
        print(token)
        print("=" * 60)
        print("\n📋 Verwendung:")
        print(f"   export GITHUB_TOKEN='{token}'")
        print(
            "   git push https://$GITHUB_TOKEN@github.com/SHAdd0WTAka/obsidian-vault.git"
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
