"""
Discord Notification Backend for Zen-AI-Pentest

SSRF Protection: All outbound requests are restricted to official Discord webhook URLs.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Final, List, Optional, Tuple, Union
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


class DiscordBackend:
    """Discord Notification Backend with rate limiting and retry support"""

    # Color mapping for Discord (integer values)
    COLORS = {
        "danger": 0xFF0000,  # Red
        "warning": 0xFFA500,  # Orange
        "good": 0x00FF00,  # Green
        "info": 0x00D4FF,  # Cyan
        "primary": 0x3B82F6,  # Blue
    }

    def __init__(
        self,
        webhook_url: Union[str, ValidatedDiscordWebhook],
        username: str = "Zen-AI-Pentest",
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize Discord backend.

        Args:
            webhook_url: Discord webhook URL (validated)
            username: Bot username to display
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if isinstance(webhook_url, str):
            webhook_url = ValidatedDiscordWebhook(webhook_url)
        self._webhook: Final[str] = webhook_url.url
        self._username = username
        self._timeout = timeout
        self._max_retries = max_retries

    @classmethod
    def from_raw_url(
        cls,
        webhook_url: str,
        username: str = "Zen-AI-Pentest",
        timeout: int = 10,
        max_retries: int = 3,
    ) -> "DiscordBackend":
        """Create backend from raw URL with validation."""
        validated = ValidatedDiscordWebhook(webhook_url)
        return cls(validated, username, timeout, max_retries)

    def send(
        self,
        message: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Union[str, int] = 0x00D4FF,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send embed notification to Discord.

        Args:
            message: Optional plain text message (shown above embed)
            title: Embed title
            description: Embed description
            color: Color name (danger, warning, good, info, primary) or hex integer
            fields: List of field dicts with name, value, inline keys
            footer: Footer text
            timestamp: Optional timestamp
            url: Optional URL for the title

        Returns:
            Dict with success status and response info
        """
        # Convert color name to integer
        if isinstance(color, str):
            color = self.COLORS.get(color, 0x00D4FF)

        embed = {
            "color": color,
        }

        if title:
            embed["title"] = title
        if url:
            embed["url"] = url
        if description:
            embed["description"] = description[:4096]  # Discord limit
        if timestamp:
            embed["timestamp"] = timestamp.isoformat()
        if footer:
            embed["footer"] = {"text": footer}

        if fields:
            embed["fields"] = [
                {
                    "name": f.get("title", f.get("name", ""))[:256],
                    "value": str(f.get("value", ""))[:1024],
                    "inline": f.get("inline", f.get("short", False)),
                }
                for f in fields
            ]

        payload = {
            "username": self._username,
            "embeds": [embed],
        }

        if message:
            payload["content"] = message[:2000]  # Discord limit

        return self._send_with_retry(payload)

    def send_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        template_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send event notification using templates.

        Args:
            event_type: Type of event
            data: Event data
            template_data: Optional pre-rendered template data

        Returns:
            Dict with success status
        """
        if template_data:
            return self.send(**template_data)

        builders = {
            "scan_started": self._build_scan_started,
            "scan_completed": self._build_scan_completed,
            "critical_finding": self._build_critical_finding,
            "high_severity_cve": self._build_high_severity_cve,
            "system_alert": self._build_system_alert,
            "report_ready": self._build_report_ready,
        }

        builder = builders.get(event_type, self._build_generic)
        message_data = builder(data)
        return self.send(**message_data)

    def _build_scan_started(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build scan started notification"""
        return {
            "title": "🔍 Scan Started",
            "description": f"Scan of **{data.get('target', 'Unknown')}** has started.",
            "color": "info",
            "fields": [
                {"name": "Scan ID", "value": str(data.get("scan_id", "N/A")), "inline": True},
                {"name": "Target", "value": data.get("target", "N/A"), "inline": True},
                {"name": "Scan Type", "value": data.get("scan_type", "N/A"), "inline": True},
                {"name": "Started By", "value": data.get("started_by", "N/A"), "inline": True},
            ],
            "footer": "Zen-AI-Pentest",
            "timestamp": datetime.now(timezone.utc),
        }

    def _build_scan_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build scan completed notification"""
        findings = data.get("findings_count", 0)
        critical = data.get("critical_count", 0)
        high = data.get("high_count", 0)

        if critical > 0:
            color = "danger"
            status = "🔴 CRITICAL ISSUES FOUND"
        elif high > 0:
            color = "warning"
            status = "🟠 HIGH SEVERITY ISSUES"
        elif findings > 0:
            color = "warning"
            status = "🟡 ISSUES FOUND"
        else:
            color = "good"
            status = "🟢 NO ISSUES FOUND"

        return {
            "message": f"**{status}**",
            "title": f"Scan Completed: {data.get('target', 'Unknown')}",
            "description": f"Scan completed in {data.get('duration', 'N/A')}s",
            "color": color,
            "fields": [
                {"name": "Scan ID", "value": str(data.get("scan_id", "N/A")), "inline": True},
                {"name": "Target", "value": data.get("target", "N/A"), "inline": True},
                {"name": "Total Findings", "value": str(findings), "inline": True},
                {"name": "Critical", "value": str(critical), "inline": True},
                {"name": "High", "value": str(high), "inline": True},
                {"name": "Duration", "value": f"{data.get('duration', 'N/A')}s", "inline": True},
            ],
            "footer": "Zen-AI-Pentest",
            "timestamp": datetime.now(timezone.utc),
        }

    def _build_critical_finding(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build critical finding notification"""
        return {
            "message": "🚨 **CRITICAL VULNERABILITY DETECTED**",
            "title": data.get("title", "Critical Finding"),
            "description": data.get("description", "")[:4096],
            "color": "danger",
            "fields": [
                {"name": "Target", "value": data.get("target", "N/A"), "inline": True},
                {"name": "CVE", "value": data.get("cve", "N/A"), "inline": True},
                {"name": "CVSS Score", "value": str(data.get("cvss", "N/A")), "inline": True},
                {"name": "Severity", "value": "CRITICAL", "inline": True},
                {"name": "Tool", "value": data.get("tool", "Unknown"), "inline": True},
                {"name": "Port", "value": str(data.get("port", "N/A")), "inline": True},
            ],
            "footer": "⚠️ Immediate Action Required | Zen-AI-Pentest",
            "timestamp": datetime.now(timezone.utc),
        }

    def _build_high_severity_cve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build high severity CVE notification"""
        return {
            "title": f"⚠️ High Severity CVE: {data.get('cve', 'Unknown')}",
            "description": data.get("description", "")[:4096],
            "color": "warning",
            "fields": [
                {"name": "CVE ID", "value": data.get("cve", "N/A"), "inline": True},
                {"name": "CVSS Score", "value": str(data.get("cvss", "N/A")), "inline": True},
                {"name": "Affected", "value": data.get("affected", "N/A"), "inline": True},
                {"name": "EPSS", "value": str(data.get("epss", "N/A")), "inline": True},
            ],
            "footer": "Zen-AI-Pentest",
            "timestamp": datetime.now(timezone.utc),
        }

    def _build_system_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build system alert notification"""
        alert_type = data.get("alert_type", "info")
        colors = {
            "error": "danger",
            "warning": "warning",
            "info": "info",
            "success": "good",
        }
        icons = {
            "error": "🔴",
            "warning": "🟠",
            "info": "🔵",
            "success": "🟢",
        }
        return {
            "message": f"{icons.get(alert_type, '🔔')} **System Alert: {data.get('title', 'Notification')}**",
            "title": data.get("title", "System Alert"),
            "description": data.get("message", ""),
            "color": colors.get(alert_type, "info"),
            "fields": [
                {"name": "Component", "value": data.get("component", "N/A"), "inline": True},
                {"name": "Severity", "value": alert_type.upper(), "inline": True},
            ],
            "footer": "Zen-AI-Pentest System",
            "timestamp": datetime.now(timezone.utc),
        }

    def _build_report_ready(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build report ready notification"""
        return {
            "title": "📊 Report Ready for Download",
            "description": f"Your security report for **{data.get('target', 'Unknown')}** is ready.",
            "color": "good",
            "fields": [
                {"name": "Report ID", "value": str(data.get("report_id", "N/A")), "inline": True},
                {"name": "Scan ID", "value": str(data.get("scan_id", "N/A")), "inline": True},
                {"name": "Format", "value": data.get("format", "PDF").upper(), "inline": True},
                {"name": "Size", "value": data.get("size", "N/A"), "inline": True},
            ],
            "footer": "Zen-AI-Pentest",
            "timestamp": datetime.now(timezone.utc),
        }

    def _build_generic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build generic notification"""
        return {
            "title": data.get("title", "Notification"),
            "description": data.get("message", data.get("description", "")),
            "color": data.get("color", "info"),
            "fields": [{"name": k, "value": str(v), "inline": True} for k, v in data.get("fields", {}).items()],
            "footer": "Zen-AI-Pentest",
            "timestamp": datetime.now(timezone.utc),
        }

    def _send_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send with retry logic"""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                response = requests.post(
                    self._webhook,
                    json=payload,
                    timeout=self._timeout,
                    headers={"Content-Type": "application/json"},
                )

                # Discord returns 204 on success
                if response.status_code in (200, 204):
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    }
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Discord rate limited, retrying after {retry_after}s")
                    import time

                    time.sleep(retry_after)
                    last_error = f"Rate limited (HTTP {response.status_code})"
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"Discord request failed: {last_error}")

            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"Discord request error (attempt {attempt + 1}): {e}")

            # Exponential backoff
            if attempt < self._max_retries - 1:
                import time

                time.sleep(2**attempt)

        return {
            "success": False,
            "error": last_error,
            "attempts": self._max_retries,
        }

    def test(self) -> Dict[str, Any]:
        """Test the Discord connection"""
        return self.send(
            message="🔔 **Test Notification**",
            title="Zen-AI-Pentest",
            description="This is a test notification from Zen-AI-Pentest.",
            color="good",
            fields=[
                {"name": "Status", "value": "✅ Connection successful", "inline": True},
                {"name": "Time", "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "inline": True},
            ],
            footer="Zen-AI-Pentest Notification System",
        )
