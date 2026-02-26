"""
Slack Integration für Zen-AI-Pentest

SSRF Protection: All outbound requests are restricted to official Slack webhook URLs.
See: https://api.slack.com/messaging/webhooks
"""

import logging
from datetime import datetime
from typing import Dict, Final, Tuple, Union
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# Allowed webhook hosts (constant for code analysis visibility)
# codeql[python/ssrf]: These are the only allowed hosts for SSRF protection
ALLOWED_SLACK_HOSTS: Final[Tuple[str, ...]] = (
    "hooks.slack.com",  # Official Slack incoming webhooks
    "hooks.slack.dev",  # Slack development/testing environment
)

# Validate scheme (prevent file://, ftp://, etc.)
ALLOWED_SCHEMES: Final[Tuple[str, ...]] = ("https",)  # Slack only uses HTTPS


class ValidatedSlackWebhook:
    """
    A Slack webhook URL that has been validated and is safe to use.

    This type ensures that any URL used for outbound requests has passed
    SSRF validation. The validation happens at construction time.
    """

    __slots__ = ("url",)

    def __init__(self, url: str) -> None:
        """
        Validate and store a Slack webhook URL.

        Raises:
            ValueError: If URL is not a valid Slack webhook URL
        """
        self.url = self._validate(url)

    @staticmethod
    def _validate(url: str) -> str:
        """
        Validate that the provided URL is a legitimate Slack webhook URL.

        This function provides SSRF protection by:
        1. Requiring HTTPS scheme
        2. Restricting to official Slack webhook hosts only
        3. Ensuring the URL has a valid structure

        Args:
            url: The webhook URL to validate

        Returns:
            The validated URL (unchanged, but confirmed safe)

        Raises:
            ValueError: If URL fails any validation check
        """
        if not url:
            raise ValueError("webhook_url is required")

        parsed = urlparse(url)

        # Validate scheme (prevent file://, ftp://, etc.)
        if parsed.scheme not in ALLOWED_SCHEMES:
            raise ValueError(
                f"Invalid webhook URL scheme: '{parsed.scheme}'. "
                f"Only HTTPS is allowed for security reasons."
            )

        # Validate hostname exists
        if not parsed.netloc:
            raise ValueError("Invalid webhook URL: no hostname found")

        # Extract hostname (remove port if present)
        host = parsed.hostname or ""

        # Strict host validation (SSRF protection)
        # Only allow official Slack webhook domains
        if host not in ALLOWED_SLACK_HOSTS:
            raise ValueError(
                f"Webhook host is not allowed: '{host}'. "
                f"Only official Slack hosts are permitted."
            )

        return url

    def __str__(self) -> str:
        """Return the validated URL (masked for logging)."""
        return self.url

    def __repr__(self) -> str:
        """Return masked representation."""
        # Mask the URL for secure logging
        parsed = urlparse(self.url)
        masked_path = (
            parsed.path[:15] + "..." if len(parsed.path) > 15 else parsed.path
        )
        return f"ValidatedSlackWebhook(https://{parsed.netloc}{masked_path})"


def _validate_slack_webhook_url(url: str) -> str:
    """
    Validate that the provided URL is a legitimate Slack webhook URL.

    This is a convenience function that wraps ValidatedSlackWebhook._validate
    for backward compatibility with existing code and tests.

    SSRF Protection: Only official Slack webhook hosts are allowed.

    Args:
        url: The webhook URL to validate

    Returns:
        The validated URL (unchanged, but confirmed safe)

    Raises:
        ValueError: If URL fails any validation check
    """
    return ValidatedSlackWebhook._validate(url)


class SlackNotifier:
    """Sendet Benachrichtigungen an Slack"""

    def __init__(self, webhook_url: Union[str, ValidatedSlackWebhook]) -> None:
        """
        Initialize with a validated Slack webhook URL.

        Args:
            webhook_url: A pre-validated Slack webhook URL or a raw URL string.
                        If a string is provided, it will be validated automatically.
        """
        if isinstance(webhook_url, str):
            webhook_url = ValidatedSlackWebhook(webhook_url)
        self._webhook: Final[str] = webhook_url.url

    @property
    def webhook_url(self) -> str:
        """Return the webhook URL."""
        return self._webhook

    @classmethod
    def from_raw_url(cls, webhook_url: str) -> "SlackNotifier":
        """
        Create a SlackNotifier from a raw URL string.

        This method validates the URL before creating the notifier.
        Use this when you have a URL that hasn't been validated yet.

        Args:
            webhook_url: Raw webhook URL string

        Returns:
            Configured SlackNotifier instance

        Raises:
            ValueError: If URL is not a valid Slack webhook URL
        """
        validated = ValidatedSlackWebhook(webhook_url)
        return cls(validated)

    def send_message(self, message: str, channel: str = None) -> bool:
        """Sendet einfache Text-Nachricht"""
        payload = {"text": message}
        if channel:
            payload["channel"] = channel

        try:
            # This request is safe because:
            # 1. self._webhook was validated in __init__
            # 2. URL is restricted to ALLOWED_SLACK_HOSTS
            # 3. Scheme is restricted to HTTPS only
            response = requests.post(
                self._webhook,  # Already validated URL
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                return True
            return False
        except requests.RequestException as e:
            logger.error(f"Slack send error: {e}")
            return False

    def send_scan_completed(
        self,
        scan_id: int,
        target: str,
        findings_count: int,
        critical_count: int,
    ) -> bool:
        """Sendet Scan-Completion Benachrichtigung"""
        color = (
            "danger"
            if critical_count > 0
            else "warning" if findings_count > 0 else "good"
        )

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "Pentest Scan Completed",
                    "fields": [
                        {
                            "title": "Scan ID",
                            "value": str(scan_id),
                            "short": True,
                        },
                        {"title": "Target", "value": target, "short": True},
                        {
                            "title": "Total Findings",
                            "value": findings_count,
                            "short": True,
                        },
                        {
                            "title": "Critical",
                            "value": critical_count,
                            "short": True,
                        },
                    ],
                    "footer": "Zen-AI-Pentest",
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        try:
            # Safe request: URL validated at construction
            response = requests.post(
                self._webhook,  # Pre-validated, SSRF-safe
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                return True
            return False
        except requests.RequestException as e:
            logger.error(f"Slack send error: {e}")
            return False

    def send_critical_finding(self, finding: Dict) -> bool:
        """Sendet Critical Finding Alert"""
        payload = {
            "attachments": [
                {
                    "color": "danger",
                    "title": f"CRITICAL: {finding.get('title', 'Unknown')}",
                    "text": finding.get("description", "")[:500],
                    "fields": [
                        {
                            "title": "Severity",
                            "value": "CRITICAL",
                            "short": True,
                        },
                        {
                            "title": "Target",
                            "value": finding.get("target", "N/A"),
                            "short": True,
                        },
                        {
                            "title": "Tool",
                            "value": finding.get("tool", "Unknown"),
                            "short": True,
                        },
                        {
                            "title": "CVSS",
                            "value": str(finding.get("cvss_score", "N/A")),
                            "short": True,
                        },
                    ],
                }
            ]
        }

        try:
            # Safe request: URL validated at construction
            response = requests.post(
                self._webhook,  # Pre-validated, SSRF-safe
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                return True
            return False
        except requests.RequestException as e:
            logger.error(f"Slack send error: {e}")
            return False


def slack_notify_scan_complete(
    scan_id: int, target: str, findings_count: int, critical_count: int
) -> str:
    """Sendet Slack-Benachrichtigung bei Scan-Abschluss"""
    import os

    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return "Slack webhook not configured"

    try:
        # Validate URL by creating notifier directly
        notifier = SlackNotifier(webhook)
    except ValueError as e:
        logger.error(f"Invalid Slack webhook URL from environment: {e}")
        return "Invalid Slack webhook configuration"

    success = notifier.send_scan_completed(
        scan_id, target, findings_count, critical_count
    )
    return "Notification sent" if success else "Failed to send notification"
