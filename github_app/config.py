"""
Konfiguration für die Zen-AI-Pentest GitHub App.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitHubAppConfig:
    """GitHub App Konfiguration."""

    # GitHub App Credentials
    app_id: str
    private_key: str
    webhook_secret: Optional[str] = None

    # OAuth
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

    # Zen-AI-Pentest API
    zen_api_url: str = "http://localhost:8000"
    zen_api_key: Optional[str] = None

    # Scanning Defaults
    default_policy: str = "safe"
    default_timeout: int = 300
    max_scan_duration: int = 1800  # 30 Minuten

    # Feature Flags
    enable_pr_comments: bool = True
    enable_checks: bool = True
    enable_annotations: bool = True
    enable_summary: bool = True

    # Rate Limiting
    rate_limit_per_hour: int = 100

    @classmethod
    def from_env(cls) -> "GitHubAppConfig":
        """Lade Konfiguration aus Umgebungsvariablen."""

        # Private Key kann aus Datei oder direkt aus Env kommen
        private_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "")
        private_key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")

        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, "r") as f:
                private_key = f.read()

        return cls(
            app_id=os.getenv("GITHUB_APP_ID", ""),
            private_key=private_key,
            webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            zen_api_url=os.getenv("ZEN_API_URL", "http://localhost:8000"),
            zen_api_key=os.getenv("ZEN_API_KEY"),
            default_policy=os.getenv("ZEN_DEFAULT_POLICY", "safe"),
            default_timeout=int(os.getenv("ZEN_DEFAULT_TIMEOUT", "300")),
            max_scan_duration=int(os.getenv("ZEN_MAX_SCAN_DURATION", "1800")),
            enable_pr_comments=os.getenv("ZEN_ENABLE_PR_COMMENTS", "true").lower() == "true",
            enable_checks=os.getenv("ZEN_ENABLE_CHECKS", "true").lower() == "true",
            enable_annotations=os.getenv("ZEN_ENABLE_ANNOTATIONS", "true").lower() == "true",
            enable_summary=os.getenv("ZEN_ENABLE_SUMMARY", "true").lower() == "true",
            rate_limit_per_hour=int(os.getenv("ZEN_RATE_LIMIT_PER_HOUR", "100")),
        )

    def validate(self) -> list[str]:
        """Validiere die Konfiguration und gib Liste von Fehlern zurück."""
        errors = []

        if not self.app_id:
            errors.append("GITHUB_APP_ID ist erforderlich")

        if not self.private_key:
            errors.append("GITHUB_APP_PRIVATE_KEY oder GITHUB_APP_PRIVATE_KEY_PATH ist erforderlich")

        return errors


# Konfigurationsschema für .github/zen-pentest.yml
ZEN_PENTEST_CONFIG_SCHEMA = {
    "version": {"type": "integer", "default": 1},
    "scans": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "required": True},
                "target": {"type": "string", "required": True},
                "type": {"type": "string", "enum": ["web", "api", "network", "full"], "default": "web"},
                "policy": {"type": "string", "enum": ["safe", "normal", "elevated", "aggressive"], "default": "safe"},
                "fail_on": {"type": "string", "enum": ["none", "low", "medium", "high", "critical"], "default": "high"},
                "timeout": {"type": "integer", "default": 300},
                "tools": {"type": "array", "items": {"type": "string"}},
                "exclude_paths": {"type": "array", "items": {"type": "string"}},
                "headers": {"type": "object"},
                "auth": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "token": {"type": "string"},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                    },
                },
            },
        },
    },
    "notifications": {
        "type": "object",
        "properties": {
            "pr_comments": {"type": "boolean", "default": True},
            "checks": {"type": "boolean", "default": True},
            "slack": {"type": "string"},
            "email": {"type": "array", "items": {"type": "string"}},
            "discord": {"type": "string"},
        },
    },
    "global": {
        "type": "object",
        "properties": {
            "fail_fast": {"type": "boolean", "default": False},
            "parallel_scans": {"type": "integer", "default": 1},
            "timeout": {"type": "integer", "default": 300},
            "retry_count": {"type": "integer", "default": 1},
        },
    },
}
