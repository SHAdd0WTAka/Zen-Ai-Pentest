"""
Async Database Operations with Connection Pooling

Provides:
- Async SQLAlchemy operations
- Connection pooling
- Query result caching
- Bulk operations
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, TypeVar

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import selectinload

# Import models
from database.models import (
    AuditLog,
    Finding,
    Report,
    Scan,
    ScanStatus,
    Severity,
    User,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncDatabaseManager:
    """
    Async database manager with connection pooling.

    Usage:
        db = AsyncDatabaseManager()

        async with db.session() as session:
            scan = await db.get_scan(session, scan_id)
            ...
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, database_url: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, database_url: str = None):
        if self._initialized:
            return

        self.database_url = database_url or self._get_database_url()
        self._engine = None
        self._session_factory = None
        self._initialized = True

    def _get_database_url(self) -> str:
        """Get database URL with async driver"""
        import os

        # Try to get from environment
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/zen_pentest",
        )

        # Convert to async URL if needed
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        return db_url

    async def initialize(self):
        """Initialize the async engine and session factory"""
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(f"Async database initialized: {self.database_url}")

    async def close(self):
        """Close the database connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        if self._session_factory is None:
            await self.initialize()

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # ========================================================================
    # Scan Operations
    # ========================================================================

    async def create_scan(
        self,
        session: AsyncSession,
        name: str,
        target: str,
        scan_type: str,
        config: dict,
        user_id: int,
    ) -> Scan:
        """Create a new scan"""
        scan = Scan(
            name=name,
            target=target,
            scan_type=scan_type,
            config=config,
            user_id=user_id,
            status=ScanStatus.PENDING,
        )
        session.add(scan)
        await session.flush()
        return scan

    async def get_scan(
        self,
        session: AsyncSession,
        scan_id: int,
        load_findings: bool = False,
    ) -> Optional[Scan]:
        """Get scan by ID"""
        query = select(Scan).where(Scan.id == scan_id)
        if load_findings:
            query = query.options(selectinload(Scan.findings))
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_scans(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[Scan]:
        """List scans with optional filtering"""
        query = select(Scan).order_by(Scan.created_at.desc())

        if status:
            query = query.where(Scan.status == status)
        if user_id:
            query = query.where(Scan.user_id == user_id)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    async def update_scan_status(
        self,
        session: AsyncSession,
        scan_id: int,
        status: str,
        result: Optional[dict] = None,
    ) -> Optional[Scan]:
        """Update scan status"""
        from datetime import datetime, timezone

        scan = await self.get_scan(session, scan_id)
        if scan:
            scan.status = status
            if result:
                scan.result_summary = str(result)
            if status == ScanStatus.RUNNING.value:
                scan.started_at = datetime.now(timezone.utc)
            if status in (ScanStatus.COMPLETED.value, ScanStatus.FAILED.value):
                scan.completed_at = datetime.now(timezone.utc)
            await session.flush()
        return scan

    # ========================================================================
    # Finding Operations
    # ========================================================================

    async def create_finding(
        self,
        session: AsyncSession,
        scan_id: int,
        title: str,
        description: str,
        severity: str = Severity.MEDIUM.value,
        cvss_score: float = None,
        evidence: str = None,
        tool: str = None,
        target: str = None,
    ) -> Finding:
        """Create a new finding"""
        finding = Finding(
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

    async def get_finding(
        self,
        session: AsyncSession,
        finding_id: int,
    ) -> Optional[Finding]:
        """Get finding by ID"""
        result = await session.execute(
            select(Finding).where(Finding.id == finding_id)
        )
        return result.scalar_one_or_none()

    async def get_findings(
        self,
        session: AsyncSession,
        scan_id: int,
        severity: Optional[str] = None,
        verified: Optional[bool] = None,
    ) -> List[Finding]:
        """Get findings for a scan"""
        query = select(Finding).where(Finding.scan_id == scan_id)

        if severity:
            query = query.where(Finding.severity == severity)
        if verified is not None:
            query = query.where(Finding.verified == (1 if verified else 0))

        query = query.order_by(Finding.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()

    async def bulk_create_findings(
        self,
        session: AsyncSession,
        findings_data: List[Dict[str, Any]],
    ) -> List[Finding]:
        """Efficiently create multiple findings"""
        findings = [Finding(**data) for data in findings_data]
        session.add_all(findings)
        await session.flush()
        return findings

    # ========================================================================
    # User Operations
    # ========================================================================

    async def get_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Get user by ID"""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(
        self,
        session: AsyncSession,
        username: str,
    ) -> Optional[User]:
        """Get user by username"""
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    # ========================================================================
    # Report Operations
    # ========================================================================

    async def create_report(
        self,
        session: AsyncSession,
        scan_id: int,
        format: str,
        template: str,
        user_id: int,
    ) -> Report:
        """Create a new report"""
        report = Report(
            scan_id=scan_id,
            format=format,
            template=template,
            user_id=user_id,
            status="pending",
        )
        session.add(report)
        await session.flush()
        return report

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.session() as session:
                start = asyncio.get_event_loop().time()
                await session.execute(text("SELECT 1"))
                latency = (asyncio.get_event_loop().time() - start) * 1000

                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "database_url": self.database_url.split("@")[
                        -1
                    ],  # Hide credentials
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# =============================================================================
# Global Instance and Convenience Functions
# =============================================================================

# Global instance
_db_manager: Optional[AsyncDatabaseManager] = None


def get_async_db() -> AsyncDatabaseManager:
    """Get the global async database manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = AsyncDatabaseManager()
    return _db_manager


async def init_async_db():
    """Initialize the async database"""
    db = get_async_db()
    await db.initialize()


async def close_async_db():
    """Close the async database"""
    db = get_async_db()
    await db.close()


# Convenience query functions
async def get_scan_async(scan_id: int) -> Optional[Scan]:
    """Async get scan by ID"""
    db = get_async_db()
    async with db.session() as session:
        return await db.get_scan(session, scan_id, load_findings=True)


async def get_scans_async(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[Scan]:
    """Async list scans"""
    db = get_async_db()
    async with db.session() as session:
        return await db.get_scans(session, skip, limit, status)


async def create_finding_async(
    scan_id: int,
    title: str,
    description: str,
    severity: str = "medium",
    **kwargs,
) -> Finding:
    """Async create finding"""
    db = get_async_db()
    async with db.session() as session:
        return await db.create_finding(
            session,
            scan_id=scan_id,
            title=title,
            description=description,
            severity=severity,
            **kwargs,
        )


__all__ = [
    # Main class
    "AsyncDatabaseManager",
    # Global instance
    "get_async_db",
    "init_async_db",
    "close_async_db",
    # Convenience functions
    "get_scan_async",
    "get_scans_async",
    "create_finding_async",
]
