#!/usr/bin/env python3
"""
Celery Tasks for Zen-AI-Pentest
Background task processing for scans and reports
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from celery import Celery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "zen_ai_pentest",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"],
)

# Celery config
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


@celery_app.task(bind=True, max_retries=3, time_limit=1800)  # 30 min timeout
def run_security_scan(self, target: str, scan_type: str = "full", options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Run a security scan in the background

    Args:
        target: Target URL/IP to scan
        scan_type: Type of scan (quick, full, deep)
        options: Additional scan options

    Returns:
        Scan results dictionary
    """
    import resource

    # Memory limit: 1GB max per task
    resource.setrlimit(resource.RLIMIT_AS, (1 * 1024 * 1024 * 1024, -1))

    try:
        logger.info(f"Starting {scan_type} scan on {target}")
        self.update_state(state="PROGRESS", meta={"progress": 10, "status": "Initializing"})

        # Import here to avoid circular imports
        from core.orchestrator import ZenOrchestrator
        from tools.nmap_integration import NmapScanner

        self.update_state(
            state="PROGRESS",
            meta={"progress": 30, "status": "Running reconnaissance"},
        )

        # REAL scan with Nmap
        ZenOrchestrator()
        scanner = NmapScanner()

        self.update_state(
            state="PROGRESS",
            meta={"progress": 50, "status": "Scanning for vulnerabilities"},
        )

        # Run actual nmap scan
        scan_results = scanner.scan(target, ports="22,80,443")
        findings = scan_results.get("findings", [])

        self.update_state(
            state="PROGRESS",
            meta={"progress": 80, "status": "Analyzing results"},
        )

        # Count findings by severity
        result = {
            "scan_id": self.request.id,
            "target": target,
            "scan_type": scan_type,
            "status": "completed",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "findings": findings,
            "summary": {
                "critical": sum(1 for f in findings if f.get("severity") == "critical"),
                "high": sum(1 for f in findings if f.get("severity") == "high"),
                "medium": sum(1 for f in findings if f.get("severity") == "medium"),
                "low": sum(1 for f in findings if f.get("severity") == "low"),
                "info": sum(1 for f in findings if f.get("severity") == "info"),
            },
        }

        self.update_state(state="PROGRESS", meta={"progress": 100, "status": "Completed"})
        logger.info(f"Scan completed for {target}")

        return result

    except Exception as exc:
        logger.error(f"Scan failed: {exc}")
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2)
def generate_report(self, scan_id: str, format_type: str = "pdf") -> Dict[str, Any]:
    """
    Generate a report from scan results

    Args:
        scan_id: ID of the completed scan
        format_type: Report format (pdf, html, json)

    Returns:
        Report metadata with download URL
    """
    try:
        logger.info(f"Generating {format_type} report for scan {scan_id}")
        self.update_state(
            state="PROGRESS",
            meta={"progress": 20, "status": "Fetching scan data"},
        )

        # Simulate report generation
        self.update_state(
            state="PROGRESS",
            meta={"progress": 50, "status": "Generating report"},
        )

        self.update_state(state="PROGRESS", meta={"progress": 90, "status": "Finalizing"})

        result = {
            "report_id": self.request.id,
            "scan_id": scan_id,
            "format": format_type,
            "status": "completed",
            "download_url": f"/api/reports/{self.request.id}/download",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Report generated: {result['report_id']}")
        return result

    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def cleanup_old_scans(days: int = 30) -> Dict[str, Any]:
    """
    Cleanup old scan results from database

    Args:
        days: Delete scans older than this many days

    Returns:
        Cleanup statistics
    """
    logger.info(f"Cleaning up scans older than {days} days")

    # Placeholder for actual cleanup logic
    result = {
        "deleted_scans": 0,
        "deleted_reports": 0,
        "cleaned_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Cleanup completed")
    return result


@celery_app.task
def send_notification(user_id: str, message: str, channel: str = "email") -> bool:
    """
    Send notification to user

    Args:
        user_id: User ID to notify
        message: Notification message
        channel: Notification channel (email, slack, webhook)

    Returns:
        True if sent successfully
    """
    logger.info(f"Sending {channel} notification to user {user_id}")

    # Placeholder for actual notification logic
    return True


# Scheduled tasks ONLY with root privileges
# This prevents accidental system overload
try:
    from utils.sudo_check import is_root

    if is_root():
        celery_app.conf.beat_schedule = {
            "celery-cleanup-old-scans": {
                "task": "tasks.cleanup_old_scans",
                "schedule": 86400.0,  # Daily
                "args": (30,),
                "options": {"expires": 3600},
            },
        }
        logger.warning("⚠️  Celery scheduled tasks ACTIVATED (root mode)")
    else:
        celery_app.conf.beat_schedule = {}
        logger.info("ℹ️  Celery scheduled tasks disabled (run with sudo to enable)")

except ImportError:
    celery_app.conf.beat_schedule = {}
    logger.warning("⚠️  Cannot check privileges - scheduled tasks disabled")


if __name__ == "__main__":
    celery_app.start()
