#!/usr/bin/env python3
"""
Obsidian MCP Server for Secure Credential Storage
Reads encrypted or plaintext secrets from Obsidian vault
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional

# Obsidian Vault Path (anpassen!)
VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "~/Documents/Obsidian Vault/Secrets")


def get_secret(name: str) -> Optional[str]:
    """Retrieve secret from Obsidian vault"""
    vault = Path(VAULT_PATH).expanduser()

    # Try YAML format (recommended)
    yaml_file = vault / "secrets.yaml"
    if yaml_file.exists():
        with open(yaml_file) as f:
            secrets = yaml.safe_load(f)
            return secrets.get(name)

    # Try JSON format
    json_file = vault / "secrets.json"
    if json_file.exists():
        with open(json_file) as f:
            secrets = json.load(f)
            return secrets.get(name)

    # Try individual markdown files
    md_file = vault / f"{name}.md"
    if md_file.exists():
        content = md_file.read_text()
        # Extract from code block: ```secret\nvalue\n```
        if "```secret" in content:
            return content.split("```secret")[1].split("```")[0].strip()

    return None


def list_secrets() -> list:
    """List all available secrets"""
    vault = Path(VAULT_PATH).expanduser()
    secrets = []

    if not vault.exists():
        return []

    # Check YAML file
    yaml_file = vault / "secrets.yaml"
    if yaml_file.exists():
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            secrets.extend(data.keys())

    # Check markdown files
    for md_file in vault.glob("*.md"):
        secrets.append(md_file.stem)

    return secrets


def main():
    """MCP Server main loop"""
    print("Obsidian MCP Server started", file=os.sys.stderr)

    while True:
        try:
            line = input()
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})

            if method == "get_secret":
                name = params.get("name")
                value = get_secret(name)
                response = {"result": value, "error": None if value else f"Secret '{name}' not found"}

            elif method == "list_secrets":
                secrets = list_secrets()
                response = {"result": secrets, "error": None}

            elif method == "health":
                vault = Path(VAULT_PATH).expanduser()
                response = {
                    "result": {"status": "ok", "vault_exists": vault.exists(), "vault_path": str(vault)},
                    "error": None,
                }

            else:
                response = {"error": f"Unknown method: {method}"}

            print(json.dumps(response))

        except EOFError:
            break
        except Exception as e:
            print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
