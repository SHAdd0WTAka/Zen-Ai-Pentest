"""
CRUD Operations for Zen-AI-Pentest Database
"""

from datetime import datetime

from sqlalchemy.orm import Session

from . import models

# ============================================================================
# SCAN CRUD
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

    db_scan = models.Scan(name=name, target=target, scan_type=scan_type, config=config, user_id=user_id)
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    return db_scan


def get_scan(db: Session, scan_id: int):
    """Gibt einen spezifischen Scan zurück"""
    return db.query(models.Scan).filter(models.Scan.id == scan_id).first()


def get_scans(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    """Gibt eine Liste von Scans zurück"""
    query = db.query(models.Scan)
    if status:
        query = query.filter(models.Scan.status == status)
    return query.offset(skip).limit(limit).all()


def update_scan_status(db: Session, scan_id: int, status: str, result: dict = None):
    """Aktualisiert den Status eines Scans"""
    db_scan = get_scan(db, scan_id)
    if db_scan:
        db_scan.status = status
        if status == "running":
            db_scan.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            db_scan.completed_at = datetime.utcnow()
        if result:
            db_scan.result_summary = str(result)[:1000]  # Limit length
        db.commit()
        db.refresh(db_scan)
    return db_scan


# ============================================================================
# FINDING CRUD
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
    )
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    return db_finding


def get_findings(db: Session, scan_id: int = None, skip: int = 0, limit: int = 100):
    """Gibt Befunde zurück (optional für einen Scan gefiltert)"""
    query = db.query(models.Finding)
    if scan_id:
        query = query.filter(models.Finding.scan_id == scan_id)
    return query.offset(skip).limit(limit).all()


# ============================================================================
# REPORT CRUD
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


def get_reports(db: Session, skip: int = 0, limit: int = 100):
    """Gibt eine Liste von Reports zurück"""
    return db.query(models.Report).offset(skip).limit(limit).all()
