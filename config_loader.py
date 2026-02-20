#!/usr/bin/env python3
import json
import os
from pathlib import Path


def load_config():
    """Lädt config.json und merged mit Environment Variables"""

    config_path = Path(__file__).parent / "config.json"

    with open(config_path) as f:
        config = json.load(f)

    env_mapping = {
        "OPENROUTER_API_KEY": ("backends", "openrouter_api_key"),
        "KIMI_API_KEY": ("backends", "kimi_api_key"),
        "CHATGPT_TOKEN": ("backends", "chatgpt_token"),
        "CLAUDE_SESSION": ("backends", "claude_session"),
        "LOG_LEVEL": ("output", "log_level"),
    }

    for env_var, (section, key) in env_mapping.items():
        value = os.getenv(env_var)
        if value:
            config[section][key] = value

    return config


if __name__ == "__main__":
    cfg = load_config()
    print(json.dumps(cfg, indent=2))
