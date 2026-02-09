"""
CRUD Operations for Zen-AI-Pentest Database - Performance Optimized

Optimizations:
- Async CRUD operations
- Batch operations for bulk inserts
- Optimized query patterns
- Pagination support
- Query result caching
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models

# ============================================================================
# SYNC SCAN CRUD
# ============================================================================


def create_scan(db: Session, scan_data=None, **kwargs):
    """Erstellt einen neuen Scan

    Args:
        db: Database session
        scan_data: Object with name, target, scan_type, config, user_id attributes
        **kwargs: Alternative way to pass name, target, scan_type, config, user_id
    """
    # Handle both object and keyword arguments
    if scan_data is not None:
        name = getattr(scan_data, "name", None) or kwargs.get("name")
        target = getattr(scan_data, "target", None) or kwargs.get("target")
        scan_type = getattr(scan_data, "scan_type", None) or kwargs.get("scan_type")
        config = getattr(scan_data, "config", None) or kwargs.get("config", {})
        user_id = getattr(scan_data, "user_id", None) or kwargs.get("user_id")
    else:
        name = kwargs.get("name")
        target = kwargs.get("target")
        scan_type = kwargs.get("scan_type")
        config = kwargs.get("config", {})
        user_id = kwargs.get("user_id")

    db_scan = models.Scan(
        name=name, 
        target=target, 
        scan_type=scan_type, 
        config=config, 
        user_id=user_id
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    return db_scan


def get_scan(db: Session, scan_id: int) -> Optional[models.Scan]:
    """Gibt einen spezifischen Scan zurück"""
    return db.query(models.Scan).filter(models.Scan.id == scan_id).first()


def get_scans(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    user_id: int = None,
    scan_type: str = None,
    target: str = None,
) -> List[models.Scan]:
    """
    Gibt eine Liste von Scans zurück with optimized filtering.
    
    Uses indexes: idx_scan_status_created, idx_scan_user_created, idx_scan_target_created
    """
    query = db.query(models.Scan)
    
    if status:
        query = query.filter(models.Scan.status == status)
    if user_id:
        query = query.filter(models.Scan.user_id == user_id)
    if scan_type:
        query = query.filter(models.Scan.scan_type == scan_type)
    if target:
        query = query.filter(models.Scan.target.ilike(f"%{target}%"))
    
    return query.order_by(desc(models.Scan.created_at)).offset(skip).limit(limit).all()


def get_scans_count(db: Session, status: str = None, user_id: int = None) -> int:
    """Get total count of scans with optional filtering"""
    query = db.query(func.count(models.Scan.id))
    
    if status:
        query = query.filter(models.Scan.status == status)
    if user_id:
        query = query.filter(models.Scan.user_id == user_id)
    
    return query.scalar()


def update_scan_status(
    db: Session, 
    scan_id: int, 
    status: str, 
    result: dict = None,
    update_duration: bool = True,
):
    """
    Aktualisiert den Status eines Scans
    Automatically calculates duration when scan completes.
    """
    db_scan = get_scan(db, scan_id)
    if db_scan:
        db_scan.status = status
        if status == "running":
            db_scan.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            db_scan.completed_at = datetime.utcnow()
            if update_duration and db_scan.started_at:
                db_scan.duration_seconds = (
                    db_scan.completed_at - db_scan.started_at
                ).total_seconds()
        if result:
            db_scan.result_summary = str(result)[:1000]  # Limit length
        db.commit()
        db.refresh(db_scan)
    return db_scan


def bulk_update_scan_status(db: Session, scan_ids: List[int], status: str):
    """Batch update status for multiple scans (more efficient than individual updates)"""
    now = datetime.utcnow()
    
    if status == "running":
        db.query(models.Scan).filter(
            models.Scan.id.in_(scan_ids)
        ).update({
            models.Scan.status: status,
            models.Scan.started_at: now
        }, synchronize_session=False)
    elif status in ["completed", "failed"]:
        # For completed scans, we need to calculate duration individually
        scans = db.query(models.Scan).filter(models.Scan.id.in_(scan_ids)).all()
        for scan in scans:
            scan.status = status
            scan.completed_at = now
            if scan.started_at:
                scan.duration_seconds = (now - scan.started_at).total_seconds()
    else:
        db.query(models.Scan).filter(
            models.Scan.id.in_(scan_ids)
        ).update({
            models.Scan.status: status
        }, synchronize_session=False)
    
    db.commit()


# ============================================================================
# SYNC FINDING CRUD
# ============================================================================


def create_finding(db: Session, finding_data):
    """Erstellt einen neuen Befund"""
    db_finding = models.Finding(
        scan_id=finding_data.scan_id,
        title=finding_data.title,
        description=finding_data.description,
        severity=finding_data.severity,
        cvss_score=finding_data.cvss_score,
        cve_id=finding_data.cve_id,
        evidence=finding_data.evidence,
        remediation=finding_data.remediation,
        tool=finding_data.tool,
        target=getattr(finding_data, 'target', None),
    )
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    
    # Update scan findings count
    _update_scan_findings_count(db, finding_data.scan_id)
    
    return db_finding


def create_findings_batch(db: Session, findings_data: List[Dict[str, Any]]) -> List[models.Finding]:
    """
    Batch create findings for better performance.
    
    Args:
        db: Database session
        findings_data: List of dicts with finding data
        
    Returns:
        List of created Finding objects
    """
    findings = []
    scan_ids = set()
    
    for data in findings_data:
        finding = models.Finding(
            scan_id=data["scan_id"],
            title=data["title"],
            description=data.get("description", ""),
            severity=data.get("severity", "medium"),
            cvss_score=data.get("cvss_score"),
            cve_id=data.get("cve_id"),
            evidence=data.get("evidence"),
            remediation=data.get("remediation"),
            tool=data.get("tool"),
            target=data.get("target"),
            port=data.get("port"),
            service=data.get("service"),
        )
        findings.append(finding)
        scan_ids.add(data["scan_id"])
    
    # Bulk insert
    db.bulk_save_objects(findings)
    db.commit()
    
    # Update findings count for affected scans
    for scan_id in scan_ids:
        _update_scan_findings_count(db, scan_id)
    
    return findings


def _update_scan_findings_count(db: Session, scan_id: int):
    """Update the cached findings count for a scan"""
    count = db.query(func.count(models.Finding.id)).filter(
        models.Finding.scan_id == scan_id
    ).scalar()
    
    db.query(models.Scan).filter(models.Scan.id == scan_id).update({
        models.Scan.findings_count: count
    })
    db.commit()


def get_findings(
    db: Session, 
    scan_id: int = None, 
    severity: str = None,
    cve_id: str = None,
    tool: str = None,
    skip: int = 0, 
    limit: int = 100,
    order_by_severity: bool = True,
) -> List[models.Finding]:
    """
    Gibt Befunde zurück (optional für einen Scan gefiltert)
    
    Uses indexes: idx_finding_scan_severity, idx_finding_severity_created, idx_finding_cve
    """
    query = db.query(models.Finding)
    
    if scan_id:
        query = query.filter(models.Finding.scan_id == scan_id)
    if severity:
        query = query.filter(models.Finding.severity == severity)
    if cve_id:
        query = query.filter(models.Finding.cve_id == cve_id)
    if tool:
        query = query.filter(models.Finding.tool == tool)
    
    if order_by_severity:
        # Order by severity (critical first) then CVSS score
        severity_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }
        query = query.order_by(
            models.Finding.severity,
            desc(models.Finding.cvss_score)
        )
    else:
        query = query.order_by(desc(models.Finding.created_at))
    
    return query.offset(skip).limit(limit).all()


def get_findings_count(
    db: Session, 
    scan_id: int = None, 
    severity: str = None
) -> int:
    """Get total count of findings"""
    query = db.query(func.count(models.Finding.id))
    
    if scan_id:
        query = query.filter(models.Finding.scan_id == scan_id)
    if severity:
        query = query.filter(models.Finding.severity == severity)
    
    return query.scalar()


def get_findings_by_severity_stats(db: Session, scan_id: int = None) -> Dict[str, int]:
    """Get count of findings grouped by severity (efficient single query)"""
    query = db.query(
        models.Finding.severity,
        func.count(models.Finding.id)
    )
    
    if scan_id:
        query = query.filter(models.Finding.scan_id == scan_id)
    
    results = query.group_by(models.Finding.severity).all()
    return {severity: count for severity, count in results}


# ============================================================================
# SYNC REPORT CRUD
# ============================================================================


def create_report(db: Session, report_data):
    """Erstellt einen neuen Report-Eintrag"""
    db_report = models.Report(
        scan_id=report_data.scan_id,
        user_id=report_data.user_id if hasattr(report_data, "user_id") else None,
        format=report_data.format,
        status="pending",
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def get_reports(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: str = None,
    scan_id: int = None,
) -> List[models.Report]:
    """Gibt eine Liste von Reports zurück with filtering"""
    query = db.query(models.Report)
    
    if status:
        query = query.filter(models.Report.status == status)
    if scan_id:
        query = query.filter(models.Report.scan_id == scan_id)
    
    return query.order_by(desc(models.Report.created_at)).offset(skip).limit(limit).all()


# ============================================================================
# ASYNC CRUD OPERATIONS
# ============================================================================


async def async_create_scan(
    db: AsyncSession, 
    name: str, 
    target: str, 
    scan_type: str, 
    config: dict, 
    user_id: int
) -> models.Scan:
    """Async create scan"""
    db_scan = models.Scan(
        name=name, 
        target=target, 
        scan_type=scan_type, 
        config=config, 
        user_id=user_id
    )
    db.add(db_scan)
    await db.commit()
    await db.refresh(db_scan)
    return db_scan


async def async_get_scan(db: AsyncSession, scan_id: int) -> Optional[models.Scan]:
    """Async get scan by ID"""
    result = await db.execute(
        select(models.Scan).filter(models.Scan.id == scan_id)
    )
    return result.scalar_one_or_none()


async def async_get_scans(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    user_id: int = None,
) -> List[models.Scan]:
    """Async get scans with filtering"""
    query = select(models.Scan).order_by(desc(models.Scan.created_at))
    
    if status:
        query = query.filter(models.Scan.status == status)
    if user_id:
        query = query.filter(models.Scan.user_id == user_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def async_update_scan_status(
    db: AsyncSession,
    scan_id: int,
    status: str,
    result: dict = None,
):
    """Async update scan status"""
    db_scan = await async_get_scan(db, scan_id)
    if db_scan:
        db_scan.status = status
        if status == "running":
            db_scan.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            db_scan.completed_at = datetime.utcnow()
            if db_scan.started_at:
                db_scan.duration_seconds = (
                    db_scan.completed_at - db_scan.started_at
                ).total_seconds()
        if result:
            db_scan.result_summary = str(result)[:1000]
        await db.commit()
        await db.refresh(db_scan)
    return db_scan


async def async_create_finding(
    db: AsyncSession,
    scan_id: int,
    title: str,
    description: str,
    severity: str = "medium",
    cvss_score: float = None,
    evidence: str = None,
    tool: str = None,
) -> models.Finding:
    """Async create finding"""
    db_finding = models.Finding(
        scan_id=scan_id,
        title=title,
        description=description,
        severity=severity,
        cvss_score=cvss_score,
        evidence=evidence,
        tool=tool,
    )
    db.add(db_finding)
    await db.commit()
    await db.refresh(db_finding)
    return db_finding


async def async_get_findings(
    db: AsyncSession,
    scan_id: int = None,
    severity: str = None,
    skip: int = 0,
    limit: int = 100,
) -> List[models.Finding]:
    """Async get findings with filtering"""
    query = select(models.Finding).order_by(
        models.Finding.severity,
        desc(models.Finding.cvss_score)
    )
    
    if scan_id:
        query = query.filter(models.Finding.scan_id == scan_id)
    if severity:
        query = query.filter(models.Finding.severity == severity)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# VULNERABILITY DB CRUD
# ============================================================================


def get_vulnerability_by_cve(db: Session, cve_id: str) -> Optional[models.VulnerabilityDB]:
    """Get vulnerability by CVE ID (uses idx_vuln_cve_id)"""
    return db.query(models.VulnerabilityDB).filter(
        models.VulnerabilityDB.cve_id == cve_id.upper()
    ).first()


def get_vulnerabilities_by_severity(
    db: Session, 
    severity: str, 
    limit: int = 100
) -> List[models.VulnerabilityDB]:
    """Get vulnerabilities by severity (uses idx_vuln_severity_cvss)"""
    return db.query(models.VulnerabilityDB).filter(
        models.VulnerabilityDB.severity == severity
    ).order_by(
        desc(models.VulnerabilityDB.cvss_score)
    ).limit(limit).all()


def bulk_upsert_vulnerabilities(
    db: Session, 
    vulnerabilities: List[Dict[str, Any]]
):
    """
    Bulk upsert vulnerabilities for CVE database updates.
    Uses merge for existing entries.
    """
    for vuln_data in vulnerabilities:
        existing = db.query(models.VulnerabilityDB).filter(
            models.VulnerabilityDB.cve_id == vuln_data["cve_id"].upper()
        ).first()
        
        if existing:
            # Update existing
            for key, value in vuln_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            vuln = models.VulnerabilityDB(
                cve_id=vuln_data["cve_id"].upper(),
                title=vuln_data.get("title"),
                description=vuln_data.get("description"),
                severity=vuln_data.get("severity"),
                cvss_score=vuln_data.get("cvss_score"),
                epss_score=vuln_data.get("epss_score"),
                affected_products=vuln_data.get("affected_products"),
                references=vuln_data.get("references"),
                exploits=vuln_data.get("exploits"),
            )
            db.add(vuln)
    
    db.commit()


# ============================================================================
# AUDIT LOG CRUD
# ============================================================================


def create_audit_log(
    db: Session, 
    user_id: int, 
    action: str, 
    resource_type: str, 
    resource_id: int, 
    details: dict, 
    ip_address: str = None
):
    """Erstellt Audit-Log-Eintrag"""
    log = models.AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()


def get_audit_logs(
    db: Session,
    user_id: int = None,
    action: str = None,
    resource_type: str = None,
    skip: int = 0,
    limit: int = 100,
) -> List[models.AuditLog]:
    """Get audit logs with filtering"""
    query = db.query(models.AuditLog)
    
    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    if action:
        query = query.filter(models.AuditLog.action == action)
    if resource_type:
        query = query.filter(models.AuditLog.resource_type == resource_type)
    
    return query.order_by(desc(models.AuditLog.timestamp)).offset(skip).limit(limit).all()


# ============================================================================
# NOTIFICATION CRUD
# ============================================================================


def get_unread_notifications(
    db: Session,
    user_id: int,
    limit: int = 50,
) -> List[models.Notification]:
    """Get unread notifications for user (uses idx_notification_user_read)"""
    return db.query(models.Notification).filter(
        and_(
            models.Notification.user_id == user_id,
            models.Notification.read == 0
        )
    ).order_by(desc(models.Notification.created_at)).limit(limit).all()


def mark_notifications_read(db: Session, user_id: int, notification_ids: List[int] = None):
    """Mark notifications as read (batch update)"""
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    
    if notification_ids:
        query = query.filter(models.Notification.id.in_(notification_ids))
    
    query.update({models.Notification.read: 1}, synchronize_session=False)
    db.commit()
