#!/usr/bin/env python3
"""
Git Credential Helper für GitHub App Authentication.

Generiert automatisch frische Installation Tokens.
"""
import sys
import time
from pathlib import Path

import jwt

APP_ID = "2872904"
PRIVATE_KEY_PATH = (
    Path.home()
    / "Downloads"
    / "zen-ai-pentest-kimi-assistant.2026-02-23.private-key.pem"
)


def generate_jwt():
    """Generate JWT from Private Key."""
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    payload = {
        "iat": int(time.time()) - 60,
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(jwt_token):
    """Exchange JWT for Installation Access Token via API."""
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
    """Git credential helper main loop."""
    lines = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            break
        lines.append(line)

    props = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            props[key] = value

    host = props.get("host", "")

    if host != "github.com":
        sys.exit(0)

    try:
        jwt_token = generate_jwt()
        install_token = get_installation_token(jwt_token)

        if install_token:
            print("protocol=https")
            print("host=github.com")
            print("username=x-access-token")
            print(f"password={install_token}")
            print("")
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
