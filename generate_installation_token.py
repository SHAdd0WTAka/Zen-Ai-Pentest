#!/usr/bin/env python3
"""
Generate GitHub App Installation Access Token.

Uses Private Key to authenticate as the GitHub App.
"""
import sys
import time
from pathlib import Path

import jwt

# GitHub App Configuration
APP_ID = "2872904"
PRIVATE_KEY_PATH = (
    Path.home()
    / "Downloads"
    / "zen-ai-pentest-kimi-assistant.2026-02-23.private-key.pem"
)


def generate_jwt():
    """Generate JWT from App ID and Private Key."""
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),  # 10 minutes expiry
        "iss": APP_ID,
    }

    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


def get_installation_token(jwt_token):
    """Exchange JWT for Installation Access Token."""
    import json
    import urllib.request

    req = urllib.request.Request(
        "https://api.github.com/app/installations",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        installations = json.loads(resp.read())

    if not installations:
        return None

    installation_id = installations[0]["id"]

    req = urllib.request.Request(
        f"https://api.github.com/app/installations/"
        f"{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return data.get("token")


def main():
    """Generate and display GitHub App token."""
    print("🔐 Generating GitHub App Installation Token...")
    print(f"   App ID: {APP_ID}")
    print(f"   Private Key: {PRIVATE_KEY_PATH}")

    if not PRIVATE_KEY_PATH.exists():
        print(f"❌ Private key not found at {PRIVATE_KEY_PATH}")
        print("   Bitte passe PRIVATE_KEY_PATH im Script an!")
        sys.exit(1)

    try:
        jwt_token = generate_jwt()
        print("✅ JWT generated successfully")

        token = get_installation_token(jwt_token)
        print("\n" + "=" * 60)
        print("🎉 INSTALLATION ACCESS TOKEN:")
        print("=" * 60)
        print(token)
        print("=" * 60)
        print("\n📋 Verwendung:")
        print(f"   export GITHUB_TOKEN='{token}'")
        print("   git push https://$GITHUB_TOKEN@")
        print("github.com/SHAdd0WTAka/obsidian-vault.git")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
