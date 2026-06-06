"""
Microsoft Teams Integration für Zen-AI-Pentest

SSRF Protection: All outbound requests are restricted to official Teams webhook URLs.
"""

import logging
from datetime import datetime
from typing import Dict, Final, Tuple, Union
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

ALLOWED_TEAMS_HOSTS: Final[Tuple[str, ...]] = (
    "outlook.office.com",
    "outlook.office365.com",
    "teams.microsoft.com",
)

ALLOWED_SCHEMES: Final[Tuple[str, ...]] = ("https",)


class ValidatedTeamsWebhook:
    """A Teams webhook URL that has been validated and is safe to use."""

    __slots__ = ("url",)

    def __init__(self, url: str) -> None:
        self.url = self._validate(url)

    @staticmethod
    def _validate(url: str) -> str:
        """Validate Teams webhook URL for SSRF protection."""
        if not url:
            raise ValueError("webhook_url is required")

        parsed = urlparse(url)

        if parsed.scheme not in ALLOWED_SCHEMES:
            raise ValueError(f"Invalid scheme: '{parsed.scheme}'. Only HTTPS allowed.")

        if not parsed.netloc:
            raise ValueError("Invalid URL: no hostname found")

        host = parsed.hostname or ""

        if not any(host.endswith(allowed) for allowed in ALLOWED_TEAMS_HOSTS):
            raise ValueError(f"Host not allowed: '{host}'")

        return url

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return "ValidatedTeamsWebhook(...)"


class TeamsNotifier:
    """Sendet Benachrichtigungen an Microsoft Teams"""

    def __init__(self, webhook_url: Union[str, ValidatedTeamsWebhook]) -> None:
        if isinstance(webhook_url, str):
            webhook_url = ValidatedTeamsWebhook(webhook_url)
        self._webhook: Final[str] = webhook_url.url

    @classmethod
    def from_raw_url(cls, webhook_url: str) -> "TeamsNotifier":
        """Create from raw URL string with validation."""
        validated = ValidatedTeamsWebhook(webhook_url)
        return cls(validated)

    def send_message(self, title: str, text: str) -> bool:
        """Sendet einfache Text-Nachricht"""
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": "0078D7",
            "summary": title,
            "sections": [
                {
                    "activityTitle": title,
                    "activitySubtitle": "Zen-AI-Pentest",
                    "facts": [],
                    "text": text,
                }
            ],
        }

        try:
            response = requests.post(
                self._webhook,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            return response.status_code in (200, 202)
        except requests.RequestException as e:
            logger.error(f"Teams send error: {e}")
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
            theme_color = "FF0000"
            status = "🔴 CRITICAL ISSUES FOUND"
        elif findings_count > 0:
            theme_color = "FFA500"
            status = "🟠 ISSUES FOUND"
        else:
            theme_color = "00FF00"
            status = "🟢 NO ISSUES"

        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": theme_color,
            "summary": status,
            "sections": [
                {
                    "activityTitle": status,
                    "activitySubtitle": f"Zen-AI-Pentest - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "facts": [
                        {"name": "Scan ID:", "value": str(scan_id)},
                        {"name": "Target:", "value": target},
                        {"name": "Findings:", "value": str(findings_count)},
                        {"name": "Critical:", "value": str(critical_count)},
                    ],
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Report",
                    "targets": [{"os": "default", "uri": "#"}],
                }
            ],
        }

        try:
            response = requests.post(
                self._webhook,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            return response.status_code in (200, 202)
        except requests.RequestException as e:
            logger.error(f"Teams send error: {e}")
            return False

    def send_critical_finding(self, finding: Dict) -> bool:
        """Sendet Critical Finding Alert"""
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": f"CRITICAL: {finding.get('title', 'Unknown')}",
            "sections": [
                {
                    "activityTitle": f"🚨 CRITICAL: {finding.get('title', 'Unknown')}",
                    "activitySubtitle": f"Target: {finding.get('target', 'N/A')}",
                    "facts": [
                        {"name": "Severity:", "value": "CRITICAL"},
                        {
                            "name": "Tool:",
                            "value": finding.get("tool", "Unknown"),
                        },
                        {
                            "name": "CVSS Score:",
                            "value": str(finding.get("cvss_score", "N/A")),
                        },
                    ],
                    "text": finding.get("description", "")[:500],
                }
            ],
        }

        try:
            response = requests.post(
                self._webhook,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            return response.status_code in (200, 202)
        except requests.RequestException as e:
            logger.error(f"Teams send error: {e}")
            return False


def teams_notify_scan_complete(scan_id: int, target: str, findings_count: int, critical_count: int) -> str:
    """Sendet Teams-Benachrichtigung bei Scan-Abschluss"""
    import os

    webhook = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook:
        return "Teams webhook not configured"

    try:
        notifier = TeamsNotifier(webhook)
    except ValueError as e:
        logger.error(f"Invalid Teams webhook: {e}")
        return "Invalid Teams webhook configuration"

    success = notifier.send_scan_completed(scan_id, target, findings_count, critical_count)
    return "Notification sent" if success else "Failed to send notification"
