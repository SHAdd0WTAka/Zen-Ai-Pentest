"""
Optimized CRUD Operations for Zen-AI-Pentest Database

Optimizations:
- Async/await support throughout
- Batch operations with bulk_insert
- Connection pooling with optimized settings
- N+1 query prevention with eager loading
- Query result caching
- Prepared statement reuse
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from . import models

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Async Database Session Manager
# ============================================================================


class AsyncDatabaseSession:
    """Async database session manager with connection pooling"""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        from database.models import DATABASE_URL

        # Convert to async URL
        async_url = DATABASE_URL
        if DATABASE_URL.startswith("postgresql://"):
            async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif DATABASE_URL.startswith("sqlite:///"):
            async_url = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        self.engine = create_async_engine(
            async_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_use_lifo=True,
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self._initialized = True

    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close database connections"""
        await self.engine.dispose()


# Global instance
_db_session: Optional[AsyncDatabaseSession] = None


def get_async_db_session() -> AsyncDatabaseSession:
    """Get global async database session manager"""
    global _db_session
    if _db_session is None:
        _db_session = AsyncDatabaseSession()
    return _db_session


# ============================================================================
# SYNC SCAN CRUD (Legacy - kept for compatibility)
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
        user_id=user_id,
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    return db_scan


def get_scan(db: Session, scan_id: int):
    """Gibt einen spezifischen Scan zurück"""
    return db.query(models.Scan).filter(models.Scan.id == scan_id).first()


def get_scan_with_findings(db: Session, scan_id: int):
    """Get scan with findings loaded (prevents N+1 query)"""
    return db.query(models.Scan).filter(models.Scan.id == scan_id).options(selectinload(models.Scan.findings)).first()


def get_scans(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    """Gibt eine Liste von Scans zurück"""
    query = db.query(models.Scan)
    if status:
        query = query.filter(models.Scan.status == status)
    return query.offset(skip).limit(limit).all()


def get_scans_with_counts(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    """Get scans with finding counts (optimized single query)"""
    from sqlalchemy import func

    query = (
        db.query(models.Scan, func.count(models.Finding.id).label("finding_count"))
        .outerjoin(models.Finding, models.Scan.id == models.Finding.scan_id)
        .group_by(models.Scan.id)
    )

    if status:
        query = query.filter(models.Scan.status == status)

    results = query.offset(skip).limit(limit).all()

    # Attach count to scan objects
    for scan, count in results:
        scan.finding_count = count

    return [scan for scan, _ in results]


def update_scan_status(db: Session, scan_id: int, status: str, result: dict = None):
    """Aktualisiert den Status eines Scans"""
    db_scan = get_scan(db, scan_id)
    if db_scan:
        db_scan.status = status
        if status == "running":
            db_scan.started_at = datetime.now(timezone.utc)
        elif status in ["completed", "failed"]:
            db_scan.completed_at = datetime.now(timezone.utc)
        if result:
            db_scan.result_summary = str(result)[:1000]  # Limit length
        db.commit()
        db.refresh(db_scan)
    return db_scan


def bulk_update_scan_status(db: Session, scan_ids: List[int], status: str):
    """Bulk update scan status (optimized)"""
    update_data = {
        "status": status,
    }

    if status == "running":
        update_data["started_at"] = datetime.now(timezone.utc)
    elif status in ["completed", "failed"]:
        update_data["completed_at"] = datetime.now(timezone.utc)

    db.query(models.Scan).filter(models.Scan.id.in_(scan_ids)).update(update_data, synchronize_session=False)

    db.commit()


# ============================================================================
# ASYNC SCAN CRUD
# ============================================================================


async def async_create_scan(
    name: str,
    target: str,
    scan_type: str,
    config: dict,
    user_id: int,
) -> models.Scan:
    """Async create scan"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        scan = models.Scan(
            name=name,
            target=target,
            scan_type=scan_type,
            config=config,
            user_id=user_id,
            status=models.ScanStatus.PENDING,
        )
        session.add(scan)
        await session.flush()
        return scan


async def async_get_scan(
    scan_id: int,
    load_findings: bool = False,
    load_user: bool = False,
) -> Optional[models.Scan]:
    """Async get scan with optional eager loading"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        query = select(models.Scan).where(models.Scan.id == scan_id)

        if load_findings:
            query = query.options(selectinload(models.Scan.findings))
        if load_user:
            query = query.options(joinedload(models.Scan.user))

        result = await session.execute(query)
        return result.scalar_one_or_none()


async def async_get_scans(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
) -> List[models.Scan]:
    """Async list scans with filtering"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        query = select(models.Scan).order_by(models.Scan.created_at.desc())

        if status:
            query = query.where(models.Scan.status == status)
        if user_id:
            query = query.where(models.Scan.user_id == user_id)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


async def async_update_scan_status(
    scan_id: int,
    status: str,
    result: Optional[dict] = None,
) -> Optional[models.Scan]:
    """Async update scan status"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        # Use optimized update statement
        update_data = {"status": status}

        if status == "running":
            update_data["started_at"] = datetime.now(timezone.utc)
        elif status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now(timezone.utc)
        if result:
            update_data["result_summary"] = str(result)[:1000]

        await session.execute(update(models.Scan).where(models.Scan.id == scan_id).values(**update_data))

        # Return updated scan
        result = await session.execute(select(models.Scan).where(models.Scan.id == scan_id))
        return result.scalar_one_or_none()


async def async_bulk_update_scan_status(
    scan_ids: List[int],
    status: str,
) -> int:
    """Async bulk update scan status - returns number of rows updated"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        update_data = {"status": status}

        if status == "running":
            update_data["started_at"] = datetime.now(timezone.utc)
        elif status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.now(timezone.utc)

        result = await session.execute(update(models.Scan).where(models.Scan.id.in_(scan_ids)).values(**update_data))

        return result.rowcount


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


def get_findings_by_severity(db: Session, severity: str, limit: int = 100):
    """Get findings by severity with index optimization"""
    return (
        db.query(models.Finding)
        .filter(models.Finding.severity == severity)
        .order_by(models.Finding.created_at.desc())
        .limit(limit)
        .all()
    )


def bulk_create_findings(db: Session, findings_data: List[Dict[str, Any]]):
    """Efficiently create multiple findings using bulk insert"""
    if not findings_data:
        return []

    db.bulk_insert_mappings(models.Finding, findings_data)
    db.commit()


def get_finding_stats(db: Session, scan_id: int):
    """Get finding statistics for a scan (optimized aggregation)"""
    from sqlalchemy import func

    result = (
        db.query(models.Finding.severity, func.count(models.Finding.id).label("count"))
        .filter(models.Finding.scan_id == scan_id)
        .group_by(models.Finding.severity)
        .all()
    )

    return {severity: count for severity, count in result}


# ============================================================================
# ASYNC FINDING CRUD
# ============================================================================


async def async_create_finding(
    scan_id: int,
    title: str,
    description: str,
    severity: str = "medium",
    cvss_score: float = None,
    evidence: str = None,
    tool: str = None,
    target: str = None,
) -> models.Finding:
    """Async create finding"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        finding = models.Finding(
            scan_id=scan_id,
            title=title,
            description=description,
            severity=severity,
            cvss_score=cvss_score,
            evidence=evidence,
            tool=tool,
            target=target,
        )
        session.add(finding)
        await session.flush()
        return finding


async def async_get_findings(
    scan_id: int,
    severity: Optional[str] = None,
    verified: Optional[bool] = None,
    limit: int = 100,
) -> List[models.Finding]:
    """Async get findings with filtering"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        query = select(models.Finding).where(models.Finding.scan_id == scan_id)

        if severity:
            query = query.where(models.Finding.severity == severity)
        if verified is not None:
            query = query.where(models.Finding.verified == (1 if verified else 0))

        query = query.order_by(models.Finding.created_at.desc()).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


async def async_bulk_create_findings(findings_data: List[Dict[str, Any]]) -> int:
    """Async bulk create findings - returns number of rows inserted"""
    if not findings_data:
        return 0

    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        # Use bulk insert for better performance
        await session.execute(insert(models.Finding).__values__(findings_data))
        return len(findings_data)


async def async_get_finding_stats(scan_id: int) -> Dict[str, int]:
    """Async get finding statistics for a scan"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        result = await session.execute(
            select(models.Finding.severity, func.count(models.Finding.id).label("count"))
            .where(models.Finding.scan_id == scan_id)
            .group_by(models.Finding.severity)
        )

        return {severity: count for severity, count in result.all()}


# ============================================================================
# SYNC REPORT CRUD
# ============================================================================


def create_report(db: Session, report_data):
    """Erstellt einen neuen Report-Eintrag"""
    db_report = models.Report(
        scan_id=report_data.scan_id,
        user_id=(report_data.user_id if hasattr(report_data, "user_id") else None),
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


def get_reports_with_scans(db: Session, skip: int = 0, limit: int = 100):
    """Get reports with scan info (prevents N+1 query)"""
    return db.query(models.Report).options(joinedload(models.Report.scan)).offset(skip).limit(limit).all()


# ============================================================================
# ASYNC REPORT CRUD
# ============================================================================


async def async_create_report(
    scan_id: int,
    format: str,
    template: str,
    user_id: int,
) -> models.Report:
    """Async create report"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        report = models.Report(
            scan_id=scan_id,
            format=format,
            template=template,
            user_id=user_id,
            status="pending",
        )
        session.add(report)
        await session.flush()
        return report


async def async_get_reports(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[models.Report]:
    """Async get reports with filtering"""
    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        query = select(models.Report).order_by(models.Report.created_at.desc())

        if status:
            query = query.where(models.Report.status == status)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


# ============================================================================
# OPTIMIZED QUERY OPERATIONS
# ============================================================================


def get_dashboard_stats(db: Session):
    """Get dashboard statistics in optimized single query"""
    from sqlalchemy import case, func

    result = (
        db.query(
            func.count(models.Scan.id).label("total_scans"),
            func.sum(case((models.Scan.status == "running", 1), else_=0)).label("running_scans"),
            func.sum(case((models.Scan.status == "completed", 1), else_=0)).label("completed_scans"),
            func.sum(case((models.Scan.status == "failed", 1), else_=0)).label("failed_scans"),
            func.count(models.Finding.id).label("total_findings"),
            func.sum(case((models.Finding.severity == "critical", 1), else_=0)).label("critical_findings"),
            func.sum(case((models.Finding.severity == "high", 1), else_=0)).label("high_findings"),
        )
        .outerjoin(models.Finding, models.Scan.id == models.Finding.scan_id)
        .first()
    )

    return {
        "total_scans": result.total_scans or 0,
        "running_scans": result.running_scans or 0,
        "completed_scans": result.completed_scans or 0,
        "failed_scans": result.failed_scans or 0,
        "total_findings": result.total_findings or 0,
        "critical_findings": result.critical_findings or 0,
        "high_findings": result.high_findings or 0,
    }


async def async_get_dashboard_stats() -> Dict[str, Any]:
    """Async get dashboard statistics"""
    from sqlalchemy import case, func

    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        result = await session.execute(
            select(
                func.count(models.Scan.id).label("total_scans"),
                func.sum(case((models.Scan.status == "running", 1), else_=0)).label("running_scans"),
                func.sum(case((models.Scan.status == "completed", 1), else_=0)).label("completed_scans"),
                func.sum(case((models.Scan.status == "failed", 1), else_=0)).label("failed_scans"),
            )
        )
        scan_stats = result.one()

        result = await session.execute(
            select(
                func.count(models.Finding.id).label("total_findings"),
                func.sum(case((models.Finding.severity == "critical", 1), else_=0)).label("critical_findings"),
                func.sum(case((models.Finding.severity == "high", 1), else_=0)).label("high_findings"),
            )
        )
        finding_stats = result.one()

        return {
            "total_scans": scan_stats.total_scans or 0,
            "running_scans": scan_stats.running_scans or 0,
            "completed_scans": scan_stats.completed_scans or 0,
            "failed_scans": scan_stats.failed_scans or 0,
            "total_findings": finding_stats.total_findings or 0,
            "critical_findings": finding_stats.critical_findings or 0,
            "high_findings": finding_stats.high_findings or 0,
        }


# ============================================================================
# BATCH OPERATIONS
# ============================================================================


async def async_bulk_create_scans(scans_data: List[Dict[str, Any]]) -> int:
    """Async bulk create scans - returns number of rows inserted"""
    if not scans_data:
        return 0

    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        await session.execute(insert(models.Scan).__values__(scans_data))
        return len(scans_data)


async def async_bulk_delete_scans(scan_ids: List[int]) -> int:
    """Async bulk delete scans with cascade - returns number of rows deleted"""
    if not scan_ids:
        return 0

    db_session = get_async_db_session()

    async with db_session.get_session() as session:
        # Delete findings first (if cascade not configured)
        await session.execute(delete(models.Finding).where(models.Finding.scan_id.in_(scan_ids)))

        # Delete scans
        result = await session.execute(delete(models.Scan).where(models.Scan.id.in_(scan_ids)))

        return result.rowcount


# ============================================================================
# Import for insert
# ============================================================================

from sqlalchemy import insert

__all__ = [
    # Sync CRUD
    "create_scan",
    "get_scan",
    "get_scan_with_findings",
    "get_scans",
    "get_scans_with_counts",
    "update_scan_status",
    "bulk_update_scan_status",
    "create_finding",
    "get_findings",
    "get_findings_by_severity",
    "bulk_create_findings",
    "get_finding_stats",
    "create_report",
    "get_reports",
    "get_reports_with_scans",
    "get_dashboard_stats",
    # Async CRUD
    "async_create_scan",
    "async_get_scan",
    "async_get_scans",
    "async_update_scan_status",
    "async_bulk_update_scan_status",
    "async_create_finding",
    "async_get_findings",
    "async_bulk_create_findings",
    "async_get_finding_stats",
    "async_create_report",
    "async_get_reports",
    "async_get_dashboard_stats",
    "async_bulk_create_scans",
    "async_bulk_delete_scans",
    # Session management
    "AsyncDatabaseSession",
    "get_async_db_session",
]
