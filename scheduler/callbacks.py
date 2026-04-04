"""
Task callbacks for the scheduler
These are the actual functions that run when a scheduled job triggers
"""

import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def run_vulnerability_scan(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a vulnerability scan

    Args:
        task_data: {"target": "example.com", "scan_type": "quick"}

    Returns:
        Scan results
    """
    target = task_data.get("target", "localhost")
    scan_type = task_data.get("scan_type", "quick")

    logger.info(f"[SCHEDULER] Starting {scan_type} scan on {target}")

    # Import here to avoid circular imports
    from tools.nmap_integration import NmapScanner

    scanner = NmapScanner()

    # Different scan types
    if scan_type == "quick":
        results = scanner.scan(target, ports="80,443")
    elif scan_type == "full":
        results = scanner.scan(target, ports="1-65535")
    else:
        results = scanner.scan(target)

    logger.info(f"[SCHEDULER] Scan completed: {len(results.get('findings', []))} findings")

    return results


async def generate_report(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a security report

    Args:
        task_data: {"type": "summary", "format": "pdf"}

    Returns:
        Report metadata
    """
    report_type = task_data.get("type", "summary")
    format_type = task_data.get("format", "pdf")

    logger.info(f"[SCHEDULER] Generating {report_type} report in {format_type} format")

    # Simulate report generation
    await asyncio.sleep(2)

    return {
        "report_type": report_type,
        "format": format_type,
        "generated_at": "2024-01-01T00:00:00Z",
        "download_url": f"/reports/report_{report_type}.{format_type}",
    }


async def subdomain_enumeration(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enumerate subdomains

    Args:
        task_data: {"domain": "example.com"}

    Returns:
        List of subdomains
    """
    domain = task_data.get("domain", "example.com")

    logger.info(f"[SCHEDULER] Enumerating subdomains for {domain}")

    try:
        from tools.subfinder_integration import SubfinderScanner

        scanner = SubfinderScanner()
        results = scanner.scan(domain)
        return results
    except ImportError:
        logger.warning("Subfinder not available, using mock data")
        return {"subdomains": [f"www.{domain}", f"api.{domain}"]}


async def cleanup_old_data(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleanup old scan data

    Args:
        task_data: {"days": 30}

    Returns:
        Cleanup stats
    """
    days = task_data.get("days", 30)

    logger.info(f"[SCHEDULER] Cleaning up data older than {days} days")

    # Placeholder - would actually delete from DB
    return {
        "deleted_scans": 0,
        "deleted_reports": 0,
        "days_threshold": days,
    }


def get_all_callbacks() -> Dict[str, Any]:
    """
    Get all available callbacks for registration

    Returns:
        Dict mapping task_type to callback function
    """
    return {
        "vulnerability_scan": run_vulnerability_scan,
        "generate_report": generate_report,
        "subdomain_enum": subdomain_enumeration,
        "cleanup": cleanup_old_data,
        # Aliases
        "scan": run_vulnerability_scan,
        "report": generate_report,
    }
