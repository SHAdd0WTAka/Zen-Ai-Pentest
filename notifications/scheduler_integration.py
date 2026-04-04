"""
Notification Scheduler Integration for Zen-AI-Pentest

Integrates the notification system with the scan scheduler to automatically
send notifications on scan events.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def notify_scan_started(
    scan_id: int,
    target: str,
    user_id: int,
    scan_type: str = "security",
    started_by: str = "system",
    db: Optional[Session] = None,
):
    """
    Send notification when scan starts.

    Args:
        scan_id: Scan ID
        target: Target being scanned
        user_id: User ID to notify
        scan_type: Type of scan
        started_by: Who/what started the scan
        db: Database session
    """
    try:
        from notifications.manager import NotificationManager

        if db is None:
            from database.models import SessionLocal

            db = SessionLocal()

        manager = NotificationManager(db)

        import asyncio

        asyncio.create_task(
            manager.send_notification(
                user_id=user_id,
                event_type=manager.EVENT_SCAN_STARTED,
                data={
                    "scan_id": scan_id,
                    "target": target,
                    "scan_type": scan_type,
                    "started_by": started_by,
                },
            )
        )
    except Exception as e:
        logger.error(f"Failed to send scan started notification: {e}")


def notify_scan_completed(
    scan_id: int,
    target: str,
    user_id: int,
    findings_count: int = 0,
    critical_count: int = 0,
    high_count: int = 0,
    medium_count: int = 0,
    low_count: int = 0,
    duration: float = 0,
    db: Optional[Session] = None,
):
    """
    Send notification when scan completes.

    Args:
        scan_id: Scan ID
        target: Target that was scanned
        user_id: User ID to notify
        findings_count: Total findings
        critical_count: Critical findings
        high_count: High severity findings
        medium_count: Medium severity findings
        low_count: Low severity findings
        duration: Scan duration in seconds
        db: Database session
    """
    try:
        from notifications.manager import NotificationManager

        if db is None:
            from database.models import SessionLocal

            db = SessionLocal()

        manager = NotificationManager(db)

        import asyncio

        asyncio.create_task(
            manager.send_notification(
                user_id=user_id,
                event_type=manager.EVENT_SCAN_COMPLETED,
                data={
                    "scan_id": scan_id,
                    "target": target,
                    "findings_count": findings_count,
                    "critical_count": critical_count,
                    "high_count": high_count,
                    "medium_count": medium_count,
                    "low_count": low_count,
                    "duration": duration,
                },
            )
        )
    except Exception as e:
        logger.error(f"Failed to send scan completed notification: {e}")


def notify_critical_finding(
    finding_id: int,
    scan_id: int,
    target: str,
    user_id: int,
    title: str,
    description: str,
    cve: Optional[str] = None,
    cvss: Optional[float] = None,
    tool: str = "unknown",
    port: Optional[int] = None,
    db: Optional[Session] = None,
):
    """
    Send notification for critical finding.

    Args:
        finding_id: Finding ID
        scan_id: Scan ID
        target: Target
        user_id: User ID to notify
        title: Finding title
        description: Finding description
        cve: CVE ID if applicable
        cvss: CVSS score
        tool: Tool that found the vulnerability
        port: Affected port
        db: Database session
    """
    try:
        from notifications.manager import NotificationManager

        if db is None:
            from database.models import SessionLocal

            db = SessionLocal()

        manager = NotificationManager(db)

        import asyncio

        asyncio.create_task(
            manager.send_notification(
                user_id=user_id,
                event_type=manager.EVENT_CRITICAL_FINDING,
                data={
                    "finding_id": finding_id,
                    "scan_id": scan_id,
                    "target": target,
                    "title": title,
                    "description": description,
                    "cve": cve,
                    "cvss": cvss,
                    "tool": tool,
                    "port": port,
                },
            )
        )
    except Exception as e:
        logger.error(f"Failed to send critical finding notification: {e}")


def notify_report_ready(
    report_id: int,
    scan_id: int,
    target: str,
    user_id: int,
    format: str = "pdf",
    size: str = "N/A",
    db: Optional[Session] = None,
):
    """
    Send notification when report is ready.

    Args:
        report_id: Report ID
        scan_id: Scan ID
        target: Target
        user_id: User ID to notify
        format: Report format
        size: Report file size
        db: Database session
    """
    try:
        from notifications.manager import NotificationManager

        if db is None:
            from database.models import SessionLocal

            db = SessionLocal()

        manager = NotificationManager(db)

        import asyncio

        asyncio.create_task(
            manager.send_notification(
                user_id=user_id,
                event_type=manager.EVENT_REPORT_READY,
                data={
                    "report_id": report_id,
                    "scan_id": scan_id,
                    "target": target,
                    "format": format,
                    "size": size,
                },
            )
        )
    except Exception as e:
        logger.error(f"Failed to send report ready notification: {e}")


def notify_system_alert(
    title: str,
    message: str,
    user_id: int,
    alert_type: str = "info",
    component: str = "system",
    db: Optional[Session] = None,
):
    """
    Send system alert notification.

    Args:
        title: Alert title
        message: Alert message
        user_id: User ID to notify
        alert_type: Type of alert (error, warning, info, success)
        component: Component that generated the alert
        db: Database session
    """
    try:
        from notifications.manager import NotificationManager

        if db is None:
            from database.models import SessionLocal

            db = SessionLocal()

        manager = NotificationManager(db)

        import asyncio

        asyncio.create_task(
            manager.send_notification(
                user_id=user_id,
                event_type=manager.EVENT_SYSTEM_ALERT,
                data={
                    "title": title,
                    "message": message,
                    "alert_type": alert_type,
                    "component": component,
                },
            )
        )
    except Exception as e:
        logger.error(f"Failed to send system alert notification: {e}")


# ============================================================================
# Decorators for automatic notifications
# ============================================================================


def with_scan_notifications(func):
    """
    Decorator to automatically send notifications for scan functions.

    Usage:
        @with_scan_notifications
        async def run_scan(scan_id: int, target: str, user_id: int):
            # Scan logic here
            return scan_results
    """
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        scan_id = kwargs.get("scan_id") or (args[0] if args else None)
        target = kwargs.get("target") or (args[1] if len(args) > 1 else None)
        user_id = kwargs.get("user_id") or (args[2] if len(args) > 2 else None)

        # Send start notification
        if scan_id and target and user_id:
            notify_scan_started(scan_id, target, user_id)

        try:
            # Run the function
            result = await func(*args, **kwargs)

            # Send completion notification
            if scan_id and target and user_id:
                notify_scan_completed(
                    scan_id=scan_id,
                    target=target,
                    user_id=user_id,
                    findings_count=getattr(result, "findings_count", 0),
                    critical_count=getattr(result, "critical_count", 0),
                    high_count=getattr(result, "high_count", 0),
                    duration=getattr(result, "duration", 0),
                )

            return result

        except Exception as e:
            # Send failure notification
            if scan_id and target and user_id:
                notify_system_alert(
                    title="Scan Failed",
                    message=f"Scan {scan_id} of {target} failed: {str(e)}",
                    user_id=user_id,
                    alert_type="error",
                    component="scanner",
                )
            raise

    return wrapper


# ============================================================================
# Integration with core scan workflow
# ============================================================================


class ScanNotificationMixin:
    """Mixin to add notification capabilities to scan classes"""

    def __init__(self, user_id: int, db: Optional[Session] = None):
        self.user_id = user_id
        self.db = db
        self._findings_count = 0
        self._critical_count = 0
        self._high_count = 0
        self._start_time = None

    def on_scan_start(self, scan_id: int, target: str, scan_type: str = "security"):
        """Call when scan starts"""
        from datetime import datetime, timezone

        self._start_time = datetime.now(timezone.utc)
        notify_scan_started(scan_id, target, self.user_id, scan_type, db=self.db)

    def on_finding(self, scan_id: int, target: str, finding: Dict[str, Any]):
        """Call when a finding is discovered"""
        self._findings_count += 1

        severity = finding.get("severity", "info").lower()
        if severity == "critical":
            self._critical_count += 1
            # Send immediate notification for critical
            notify_critical_finding(
                finding_id=finding.get("id", 0),
                scan_id=scan_id,
                target=target,
                user_id=self.user_id,
                title=finding.get("title", "Unknown"),
                description=finding.get("description", ""),
                cve=finding.get("cve_id"),
                cvss=finding.get("cvss_score"),
                tool=finding.get("tool", "unknown"),
                port=finding.get("port"),
                db=self.db,
            )
        elif severity == "high":
            self._high_count += 1

    def on_scan_complete(self, scan_id: int, target: str):
        """Call when scan completes"""
        from datetime import datetime, timezone

        duration = 0
        if self._start_time:
            duration = (datetime.now(timezone.utc) - self._start_time).total_seconds()

        notify_scan_completed(
            scan_id=scan_id,
            target=target,
            user_id=self.user_id,
            findings_count=self._findings_count,
            critical_count=self._critical_count,
            high_count=self._high_count,
            duration=duration,
            db=self.db,
        )

    def on_report_generated(self, report_id: int, scan_id: int, target: str, format: str = "pdf", size: str = "N/A"):
        """Call when report is generated"""
        notify_report_ready(
            report_id=report_id,
            scan_id=scan_id,
            target=target,
            user_id=self.user_id,
            format=format,
            size=size,
            db=self.db,
        )
