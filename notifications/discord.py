"""
Discord Integration für Zen-AI-Pentest

SSRF Protection: All outbound requests are restricted to official Discord webhook URLs.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Final, List, Tuple, Union
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

ALLOWED_DISCORD_HOSTS: Final[Tuple[str, ...]] = (
    "discord.com",
    "discordapp.com",
    "canary.discord.com",
    "ptb.discord.com",
)

ALLOWED_SCHEMES: Final[Tuple[str, ...]] = ("https",)


class ValidatedDiscordWebhook:
    """A Discord webhook URL that has been validated and is safe to use."""

    __slots__ = ("url",)

    def __init__(self, url: str) -> None:
        self.url = self._validate(url)

    @staticmethod
    def _validate(url: str) -> str:
        """Validate Discord webhook URL for SSRF protection."""
        if not url:
            raise ValueError("webhook_url is required")

        parsed = urlparse(url)

        if parsed.scheme not in ALLOWED_SCHEMES:
            raise ValueError(f"Invalid scheme: '{parsed.scheme}'. Only HTTPS allowed.")

        if not parsed.netloc:
            raise ValueError("Invalid URL: no hostname found")

        host = parsed.hostname or ""

        if host not in ALLOWED_DISCORD_HOSTS:
            raise ValueError(f"Host not allowed: '{host}'")

        return url

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        parsed = urlparse(self.url)
        return f"ValidatedDiscordWebhook(https://{parsed.netloc}/...)"


class DiscordNotifier:
    """Sendet Benachrichtigungen an Discord"""

    def __init__(self, webhook_url: Union[str, ValidatedDiscordWebhook]) -> None:
        if isinstance(webhook_url, str):
            webhook_url = ValidatedDiscordWebhook(webhook_url)
        self._webhook: Final[str] = webhook_url.url

    @classmethod
    def from_raw_url(cls, webhook_url: str) -> "DiscordNotifier":
        """Create from raw URL string with validation."""
        validated = ValidatedDiscordWebhook(webhook_url)
        return cls(validated)

    def send_message(self, content: str, username: str = "Zen-AI-Pentest") -> bool:
        """Sendet einfache Text-Nachricht"""
        payload = {
            "content": content,
            "username": username,
        }

        try:
            response = requests.post(
                self._webhook,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            return response.status_code in (200, 204)
        except requests.RequestException as e:
            logger.error(f"Discord send error: {e}")
            return False

    def send_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00D4FF,
        fields: List[Dict] = None,
        footer: str = None,
    ) -> bool:
        """Sendet Embedded Nachricht"""
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if fields:
            embed["fields"] = [
                {
                    "name": f["name"],
                    "value": str(f["value"]),
                    "inline": f.get("inline", False),
                }
                for f in fields
            ]

        if footer:
            embed["footer"] = {"text": footer}

        payload = {
            "embeds": [embed],
            "username": "Zen-AI-Pentest",
        }

        try:
            response = requests.post(
                self._webhook,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            return response.status_code in (200, 204)
        except requests.RequestException as e:
            logger.error(f"Discord embed error: {e}")
            return False

    def send_scan_completed(
        self,
        scan_id: int,
        target: str,
        findings_count: int,
        critical_count: int,
    ) -> bool:
        """Sendet Scan-Completion Benachrichtigung"""
        if critical_count > 0:
            color = 0xFF0000  # Red
            status = "🔴 CRITICAL ISSUES FOUND"
        elif findings_count > 0:
            color = 0xFFA500  # Orange
            status = "🟠 ISSUES FOUND"
        else:
            color = 0x00FF00  # Green
            status = "🟢 NO ISSUES"

        return self.send_embed(
            title=status,
            description=f"Scan of **{target}** completed",
            color=color,
            fields=[
                {"name": "Scan ID", "value": str(scan_id), "inline": True},
                {"name": "Target", "value": target, "inline": True},
                {
                    "name": "Findings",
                    "value": str(findings_count),
                    "inline": True,
                },
                {
                    "name": "Critical",
                    "value": str(critical_count),
                    "inline": True,
                },
            ],
            footer="Zen-AI-Pentest",
        )

    def send_critical_finding(self, finding: Dict) -> bool:
        """Sendet Critical Finding Alert"""
        return self.send_embed(
            title=f"🚨 CRITICAL: {finding.get('title', 'Unknown')}",
            description=finding.get("description", "")[:500],
            color=0xFF0000,
            fields=[
                {
                    "name": "Target",
                    "value": finding.get("target", "N/A"),
                    "inline": True,
                },
                {
                    "name": "Tool",
                    "value": finding.get("tool", "Unknown"),
                    "inline": True,
                },
                {
                    "name": "CVSS",
                    "value": str(finding.get("cvss_score", "N/A")),
                    "inline": True,
                },
            ],
            footer="Zen-AI-Pentest",
        )


def discord_notify_scan_complete(scan_id: int, target: str, findings_count: int, critical_count: int) -> str:
    """Sendet Discord-Benachrichtigung bei Scan-Abschluss"""
    import os

    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        return "Discord webhook not configured"

    try:
        notifier = DiscordNotifier(webhook)
    except ValueError as e:
        logger.error(f"Invalid Discord webhook: {e}")
        return "Invalid Discord webhook configuration"

    success = notifier.send_scan_completed(scan_id, target, findings_count, critical_count)
    return "Notification sent" if success else "Failed to send notification"
