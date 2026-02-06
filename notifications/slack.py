"""
Slack Integration für Zen-AI-Pentest
"""

import requests
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Sendet Benachrichtigungen an Slack"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_message(self, message: str, channel: str = None) -> bool:
        """Sendet einfache Text-Nachricht"""
        payload = {"text": message}
        if channel:
            payload["channel"] = channel

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack send error: {e}")
            return False

    def send_scan_completed(self, scan_id: int, target: str, findings_count: int, critical_count: int) -> bool:
        """Sendet Scan-Completion Benachrichtigung"""
        color = "danger" if critical_count > 0 else "warning" if findings_count > 0 else "good"

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "Pentest Scan Completed",
                    "fields": [
                        {"title": "Scan ID", "value": str(scan_id), "short": True},
                        {"title": "Target", "value": target, "short": True},
                        {"title": "Total Findings", "value": findings_count, "short": True},
                        {"title": "Critical", "value": critical_count, "short": True},
                    ],
                    "footer": "Zen-AI-Pentest",
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
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
                        {"title": "Severity", "value": "CRITICAL", "short": True},
                        {"title": "Target", "value": finding.get("target", "N/A"), "short": True},
                        {"title": "Tool", "value": finding.get("tool", "Unknown"), "short": True},
                        {"title": "CVSS", "value": str(finding.get("cvss_score", "N/A")), "short": True},
                    ],
                }
            ]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack send error: {e}")
            return False


def slack_notify_scan_complete(scan_id: int, target: str, findings_count: int, critical_count: int) -> str:
    """Sendet Slack-Benachrichtigung bei Scan-Abschluss"""
    import os

    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return "Slack webhook not configured"

    notifier = SlackNotifier(webhook)
    success = notifier.send_scan_completed(scan_id, target, findings_count, critical_count)
    return "Notification sent" if success else "Failed to send notification"
