#!/usr/bin/env python3
"""
Helper utilities for Zen AI Pentest
Author: SHAdd0WTAka
"""

import ipaddress
import json
import os
import re
from typing import Dict, Optional


def load_config(config_path: str = "config.json") -> Dict:
    """Load configuration from JSON file"""
    defaults = {
        "backends": {
            "openrouter_api_key": None,
            "chatgpt_token": None,
            "claude_session": None,
        },
        "rate_limits": {"requests_per_minute": 10, "backoff_seconds": 60},
        "stealth": {"delay_min": 1, "delay_max": 3, "random_user_agent": True},
        "output": {"save_logs": True, "log_level": "INFO", "report_format": "markdown"},
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
        except Exception as e:
            print(f"[Config] Error loading config: {e}, using defaults")

    return defaults


def save_config(config: Dict, config_path: str = "config.json"):
    """Save configuration to JSON file"""
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def save_session(backend_name: str, session_data: Dict, session_dir: str = "sessions"):
    """Save session data for a backend"""
    os.makedirs(session_dir, exist_ok=True)
    filepath = os.path.join(session_dir, f"{backend_name}_session.json")

    with open(filepath, "w") as f:
        json.dump(session_data, f, indent=2)

    print(f"[Session] Saved {backend_name} session")


def load_session(backend_name: str, session_dir: str = "sessions") -> Optional[Dict]:
    """Load session data for a backend"""
    filepath = os.path.join(session_dir, f"{backend_name}_session.json")

    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Session] Error loading {backend_name} session: {e}")

    return None


def validate_target(target: str) -> Dict[str, bool]:
    """
    Validate if target is a valid IP, domain, or URL
    Returns dict with validation results
    """
    result = {
        "valid": False,
        "is_ip": False,
        "is_domain": False,
        "is_url": False,
        "type": None,
    }

    if not target:
        return result

    # Check if IP address
    try:
        ipaddress.ip_address(target)
        result["valid"] = True
        result["is_ip"] = True
        result["type"] = "ip"
        return result
    except ValueError:
        pass

    # Check if URL
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if url_pattern.match(target):
        result["valid"] = True
        result["is_url"] = True
        result["type"] = "url"
        return result

    # Check if domain
    domain_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
    )

    if domain_pattern.match(target) and "." in target:
        result["valid"] = True
        result["is_domain"] = True
        result["type"] = "domain"
        return result

    return result


def sanitize_filename(filename: str) -> str:
    """Sanitize a string for use as filename"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Limit length
    return sanitized[:100]


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def banner():
    """Print Zen AI banner"""
    return """
============================================================
    ZEN AI PENTEST - AI-Powered Penetration Testing
    Author: SHAdd0WTAka | Version: 1.0.0
============================================================
"""


def colorize(text: str, color: str) -> str:
    """Add ANSI color codes to text"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }

    return f"{colors.get(color, '')}{text}{colors['reset']}"


def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    severity_colors = {
        "Critical": "red",
        "High": "magenta",
        "Medium": "yellow",
        "Low": "blue",
        "Info": "white",
    }
    return severity_colors.get(severity, "white")
