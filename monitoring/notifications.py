"""
Direct Slack/Discord Notifications for Zen AI Pentest

Sends real-time alerts for:
- Critical findings
- Authentication failures
- System errors
- Scan completions
"""

import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class NotificationManager:
    """
    Manages notifications to Slack and Discord.
    
    Environment variables:
    - SLACK_WEBHOOK_URL: Webhook URL for Slack
    - DISCORD_WEBHOOK_URL: Webhook URL for Discord
    - NOTIFICATION_ENABLED: 'true' or 'false'
    """
    
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.enabled = os.getenv("NOTIFICATION_ENABLED", "true").lower() == "true"
        
        if not self.enabled:
            logger.info("Notifications disabled")
        elif not self.slack_webhook and not self.discord_webhook:
            logger.warning("No webhook URLs configured - notifications will be logged only")
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        fields: Optional[Dict[str, Any]] = None,
        notify_channels: Optional[list] = None
    ):
        """
        Send alert to configured channels.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            fields: Additional fields to include
            notify_channels: List of channels ['slack', 'discord'] or None for all
        """
        if not self.enabled:
            logger.info(f"[ALERT - {severity.value.upper()}] {title}: {message}")
            return
        
        channels = notify_channels or ['slack', 'discord']
        
        tasks = []
        
        if 'slack' in channels and self.slack_webhook:
            tasks.append(self._send_slack(title, message, severity, fields))
        
        if 'discord' in channels and self.discord_webhook:
            tasks.append(self._send_discord(title, message, severity, fields))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_slack(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        fields: Optional[Dict[str, Any]] = None
    ):
        """Send alert to Slack"""
        
        # Color based on severity
        colors = {
            AlertSeverity.CRITICAL: "#FF0000",
            AlertSeverity.WARNING: "#FFA500",
            AlertSeverity.INFO: "#36A64F"
        }
        
        emoji = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.INFO: "ℹ️"
        }
        
        # Build attachment fields
        attachment_fields = []
        if fields:
            for key, value in fields.items():
                attachment_fields.append({
                    "title": key,
                    "value": str(value),
                    "short": len(str(value)) < 50
                })
        
        payload = {
            "attachments": [
                {
                    "color": colors.get(severity, "#808080"),
                    "title": f"{emoji.get(severity, '🔔')} {title}",
                    "text": message,
                    "fields": attachment_fields,
                    "footer": "Zen AI Pentest",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Slack notification failed: {response.status}")
                    else:
                        logger.debug(f"Slack notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_discord(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        fields: Optional[Dict[str, Any]] = None
    ):
        """Send alert to Discord"""
        
        # Color based on severity (Discord uses integer colors)
        colors = {
            AlertSeverity.CRITICAL: 0xFF0000,  # Red
            AlertSeverity.WARNING: 0xFFA500,   # Orange
            AlertSeverity.INFO: 0x36A64F       # Green
        }
        
        emoji = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.INFO: "ℹ️"
        }
        
        # Build embed fields
        embed_fields = []
        if fields:
            for key, value in fields.items():
                embed_fields.append({
                    "name": key,
                    "value": str(value)[:1024],  # Discord limit
                    "inline": len(str(value)) < 50
                })
        
        payload = {
            "embeds": [
                {
                    "title": f"{emoji.get(severity, '🔔')} {title}",
                    "description": message,
                    "color": colors.get(severity, 0x808080),
                    "fields": embed_fields,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "footer": {
                        "text": "Zen AI Pentest"
                    }
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status not in (200, 204):
                        logger.error(f"Discord notification failed: {response.status}")
                    else:
                        logger.debug(f"Discord notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    # Convenience methods for common alerts
    
    async def notify_critical_finding(
        self,
        target: str,
        vulnerability: str,
        severity: str,
        scan_id: Optional[str] = None
    ):
        """Notify about critical vulnerability finding"""
        await self.send_alert(
            title="Critical Vulnerability Discovered",
            message=f"A critical severity vulnerability was found on {target}",
            severity=AlertSeverity.CRITICAL,
            fields={
                "Target": target,
                "Vulnerability": vulnerability,
                "Severity": severity,
                "Scan ID": scan_id or "N/A",
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    
    async def notify_auth_failure(
        self,
        username: str,
        ip_address: str,
        failure_count: int
    ):
        """Notify about authentication failure"""
        severity = AlertSeverity.WARNING if failure_count > 3 else AlertSeverity.INFO
        
        await self.send_alert(
            title="Authentication Failure",
            message=f"Failed login attempt for user '{username}'",
            severity=severity,
            fields={
                "Username": username,
                "IP Address": ip_address,
                "Failure Count": failure_count,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    
    async def notify_scan_completed(
        self,
        scan_id: str,
        target: str,
        duration: float,
        findings_count: int
    ):
        """Notify about scan completion"""
        severity = AlertSeverity.WARNING if findings_count > 0 else AlertSeverity.INFO
        
        await self.send_alert(
            title="Scan Completed",
            message=f"Scan of {target} completed with {findings_count} findings",
            severity=severity,
            fields={
                "Scan ID": scan_id,
                "Target": target,
                "Duration": f"{duration:.1f}s",
                "Findings": findings_count,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    
    async def notify_system_error(
        self,
        error_type: str,
        error_message: str,
        endpoint: Optional[str] = None
    ):
        """Notify about system error"""
        await self.send_alert(
            title="System Error",
            message=f"An error occurred: {error_message}",
            severity=AlertSeverity.CRITICAL,
            fields={
                "Error Type": error_type,
                "Endpoint": endpoint or "N/A",
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    
    async def notify_rate_limit_hit(
        self,
        tier: str,
        endpoint: str,
        ip_address: str
    ):
        """Notify about rate limit hit (throttled)"""
        await self.send_alert(
            title="Rate Limit Exceeded",
            message=f"Rate limit hit on {endpoint}",
            severity=AlertSeverity.INFO,
            fields={
                "Tier": tier,
                "Endpoint": endpoint,
                "IP Address": ip_address,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            notify_channels=['slack']  # Only Slack, not Discord
        )


# Global notification manager instance
notification_manager = NotificationManager()


# Convenience functions for direct use

async def send_critical_finding(*args, **kwargs):
    await notification_manager.notify_critical_finding(*args, **kwargs)

async def send_auth_failure(*args, **kwargs):
    await notification_manager.notify_auth_failure(*args, **kwargs)

async def send_scan_completed(*args, **kwargs):
    await notification_manager.notify_scan_completed(*args, **kwargs)

async def send_system_error(*args, **kwargs):
    await notification_manager.notify_system_error(*args, **kwargs)


# Sync wrappers for use in synchronous code

def notify_critical_finding_sync(*args, **kwargs):
    asyncio.create_task(notification_manager.notify_critical_finding(*args, **kwargs))

def notify_auth_failure_sync(*args, **kwargs):
    asyncio.create_task(notification_manager.notify_auth_failure(*args, **kwargs))

def notify_scan_completed_sync(*args, **kwargs):
    asyncio.create_task(notification_manager.notify_scan_completed(*args, **kwargs))
