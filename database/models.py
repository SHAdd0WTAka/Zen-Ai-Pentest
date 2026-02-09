"""
SQLAlchemy Database Models - Performance Optimized

PostgreSQL Datenbank-Schema für Zen-AI-Pentest.
Optimizations:
- Strategic indexes for common queries
- Connection pooling configuration
- Async database driver support
- Query optimization hints
"""

import os

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, 
    Float, ForeignKey, JSON, Index, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
from datetime import datetime
from typing import Optional
import enum

Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    XML = "xml"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# MODELS
# ============================================================================


class User(Base):
    """Benutzer-Account"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="operator")  # admin, operator, viewer
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scans = relationship("Scan", back_populates="user", lazy="dynamic")
    reports = relationship("Report", back_populates="user", lazy="dynamic")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_role_active', 'role', 'is_active'),
        Index('idx_user_created', 'created_at'),
    )


class Scan(Base):
    """Pentest Scan - Optimized with indexes for common query patterns."""

    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    target = Column(String(500), nullable=False, index=True)
    scan_type = Column(String(100), nullable=False, index=True)  # network, web, ad, wireless
    status = Column(String(50), default=ScanStatus.PENDING, index=True)
    config = Column(JSON, default={})  # Tool-Konfiguration
    result_summary = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime, index=True)
    duration_seconds = Column(Float)  # Calculated field for quick access
    findings_count = Column(Integer, default=0)  # Cached count

    # Relationships
    user = relationship("User", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan", lazy="dynamic")
    reports = relationship("Report", back_populates="scan", lazy="dynamic")

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for: get_scans_by_status ordered by created_at
        Index('idx_scan_status_created', 'status', 'created_at'),
        # Index for: get_scans_by_user ordered by created_at
        Index('idx_scan_user_created', 'user_id', 'created_at'),
        # Index for: get_scans_by_target
        Index('idx_scan_target_created', 'target', 'created_at'),
        # Index for: get_recent_scans
        Index('idx_scan_started', 'started_at'),
        # Index for: find scans by type and status
        Index('idx_scan_type_status', 'scan_type', 'status'),
    )


class Finding(Base):
    """Sicherheits-Befund - Optimized with indexes."""

    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    severity = Column(String(50), default=Severity.MEDIUM, index=True)
    cvss_score = Column(Float, index=True)
    cve_id = Column(String(100), index=True)
    evidence = Column(Text)  # Screenshots, Logs, etc.
    remediation = Column(Text)
    tool = Column(String(100), index=True)  # Welches Tool hat es gefunden
    target = Column(String(500), index=True)  # Spezifisches Ziel (IP, URL, etc.)
    port = Column(Integer, index=True)
    service = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    verified = Column(Integer, default=0, index=True)  # 0=unverified, 1=verified, 2=false_positive

    # Relationships
    scan = relationship("Scan", back_populates="findings")

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for: get_findings_by_scan ordered by severity
        Index('idx_finding_scan_severity', 'scan_id', 'severity'),
        # Index for: get_findings_by_severity
        Index('idx_finding_severity_created', 'severity', 'created_at'),
        # Index for: get_findings_by_cve
        Index('idx_finding_cve', 'cve_id'),
        # Index for: get_findings_by_tool
        Index('idx_finding_tool_created', 'tool', 'created_at'),
        # Index for: get_findings_by_target
        Index('idx_finding_target', 'target'),
        # Index for: get_critical_findings
        Index('idx_finding_severity_cvss', 'severity', 'cvss_score'),
    )


class Report(Base):
    """Generierter Bericht"""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    format = Column(String(50), default=ReportFormat.PDF, index=True)
    template = Column(String(100), default="default")
    status = Column(String(50), default=ReportStatus.PENDING, index=True)
    file_path = Column(String(1000))
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    generated_at = Column(DateTime, index=True)

    # Relationships
    scan = relationship("Scan", back_populates="reports")
    user = relationship("User", back_populates="reports")

    __table_args__ = (
        Index('idx_report_status_created', 'status', 'created_at'),
        Index('idx_report_scan_format', 'scan_id', 'format'),
    )


class VulnerabilityDB(Base):
    """Lokale CVE/Exploit-Datenbank"""

    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(100), unique=True, index=True)
    title = Column(String(500), index=True)
    description = Column(Text)
    severity = Column(String(50), index=True)
    cvss_score = Column(Float, index=True)
    epss_score = Column(Float, index=True)
    affected_products = Column(JSON)
    references = Column(JSON)
    exploits = Column(JSON)  # Links zu Exploits
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_vuln_severity_cvss', 'severity', 'cvss_score'),
        Index('idx_vuln_epss', 'epss_score'),
    )


class Asset(Base):
    """Asset-Management"""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    asset_type = Column(String(100), index=True)  # server, workstation, network_device, application
    ip_address = Column(String(50), index=True)
    hostname = Column(String(255), index=True)
    os = Column(String(100), index=True)
    services = Column(JSON)  # Offene Ports & Services
    owner = Column(String(255), index=True)
    criticality = Column(String(50), default="medium", index=True)  # critical, high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_scanned = Column(DateTime, index=True)

    __table_args__ = (
        Index('idx_asset_criticality', 'criticality', 'last_scanned'),
        Index('idx_asset_type_owner', 'asset_type', 'owner'),
    )


class AuditLog(Base):
    """Audit-Logging für Compliance"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False, index=True)  # create_scan, delete_scan, etc.
    resource_type = Column(String(100), index=True)  # scan, finding, report
    resource_id = Column(Integer, index=True)
    details = Column(JSON)
    ip_address = Column(String(50), index=True)
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )


class Notification(Base):
    """Benachrichtigungen"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(String(50), index=True)  # scan_completed, finding_critical, etc.
    title = Column(String(255))
    message = Column(Text)
    read = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'read', 'created_at'),
    )


class ToolConfig(Base):
    """Tool-Konfigurationen pro User/Team"""

    __tablename__ = "tool_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    config = Column(JSON, default={})  # Tool-spezifische Einstellungen
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_toolconfig_user_tool', 'user_id', 'tool_name'),
    )


class CacheEntry(Base):
    """Database-backed cache entries for query result caching."""

    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(JSON)
    expires_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)

    __table_args__ = (
        Index('idx_cache_expires', 'expires_at'),
    )


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

# PostgreSQL URL - in production aus Umgebungsvariablen
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/zen_pentest")

# =============================================================================
# Connection Pool Configuration - Optimized
# =============================================================================
# Pool settings from environment variables
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))  # Default connections
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))  # Extra connections under load
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # Seconds to wait for connection
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # Recycle connections after 1 hour
POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"  # Check connection health

# Connection Pool arguments - optimized for performance
engine_args = {
    "pool_size": POOL_SIZE,
    "max_overflow": MAX_OVERFLOW,
    "pool_timeout": POOL_TIMEOUT,
    "pool_recycle": POOL_RECYCLE,
    "pool_pre_ping": POOL_PRE_PING,
    "pool_use_lifo": True,  # LIFO for better connection reuse
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
}

# Async database configuration
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if "postgresql" in DATABASE_URL else DATABASE_URL

engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None

def init_engines():
    """Initialize database engines with proper fallback."""
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    try:
        # Teste Verbindung (import check)
        # Versuche PostgreSQL Engine zu erstellen mit Connection Pooling
        print(f"Connecting to PostgreSQL with pool_size={POOL_SIZE}, max_overflow={MAX_OVERFLOW}")
        engine = create_engine(DATABASE_URL, **engine_args)
        
        # Try to create async engine if asyncpg is available
        try:
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            async_engine = create_async_engine(ASYNC_DATABASE_URL, **engine_args)
            AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
            print("Async database engine initialized")
        except ImportError:
            print("asyncpg not available, async features disabled")
            async_engine = None
            
    except ImportError:
        # Fallback auf SQLite für lokale Entwicklung/Tests
        print("Warning: PostgreSQL/psycopg2 not available. Using SQLite fallback (zen_pentest.db)")
        DATABASE_URL = "sqlite:///./zen_pentest.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, **engine_args)
    except Exception as e:
        print(f"Warning: PostgreSQL connection failed ({e}). Using SQLite fallback (zen_pentest.db)")
        DATABASE_URL = "sqlite:///./zen_pentest.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, **engine_args)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize engines on module load
init_engines()


def init_db():
    """Initialisiert die Datenbank"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency für FastAPI (sync)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency für FastAPI (async)"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not available")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# OPTIMIZED CRUD OPERATIONS
# ============================================================================


def create_scan(db, name: str, target: str, scan_type: str, config: dict, user_id: int):
    """Erstellt neuen Scan"""
    db_scan = Scan(name=name, target=target, scan_type=scan_type, config=config, user_id=user_id)
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    return db_scan


def get_scan(db, scan_id: int):
    """Holt Scan by ID with optimized eager loading"""
    return db.query(Scan).options(
        joinedload(Scan.user),
        joinedload(Scan.findings)
    ).filter(Scan.id == scan_id).first()


def get_scans(db, skip: int = 0, limit: int = 100, status: str = None, user_id: int = None):
    """Listet Scans auf with optional filtering"""
    query = db.query(Scan)
    if status:
        query = query.filter(Scan.status == status)
    if user_id:
        query = query.filter(Scan.user_id == user_id)
    return query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()


def get_scans_by_target(db, target: str, limit: int = 10):
    """Get recent scans for a specific target (uses idx_scan_target_created)"""
    return db.query(Scan).filter(
        Scan.target == target
    ).order_by(Scan.created_at.desc()).limit(limit).all()


def update_scan_status(db, scan_id: int, status: str, result: dict = None):
    """Aktualisiert Scan-Status with duration calculation"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.status = status
        if result:
            scan.result_summary = str(result)[:1000]
        if status == "running":
            scan.started_at = datetime.utcnow()
        if status in ["completed", "failed"]:
            scan.completed_at = datetime.utcnow()
            if scan.started_at:
                scan.duration_seconds = (scan.completed_at - scan.started_at).total_seconds()
        db.commit()
        db.refresh(scan)
    return scan


def create_finding(
    db,
    scan_id: int,
    title: str,
    description: str,
    severity: str = "medium",
    cvss_score: float = None,
    evidence: str = None,
    tool: str = None,
    target: str = None,
):
    """Erstellt neuen Befund and updates scan findings count"""
    db_finding = Finding(
        scan_id=scan_id,
        title=title,
        description=description,
        severity=severity,
        cvss_score=cvss_score,
        evidence=evidence,
        tool=tool,
        target=target,
    )
    db.add(db_finding)
    
    # Update scan findings count
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.findings_count = db.query(Finding).filter(Finding.scan_id == scan_id).count()
    
    db.commit()
    db.refresh(db_finding)
    return db_finding


def get_findings(db, scan_id: int, severity: str = None, skip: int = 0, limit: int = 100):
    """Holt Befunde für Scan with pagination"""
    query = db.query(Finding).filter(Finding.scan_id == scan_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    return query.order_by(
        Finding.severity.desc(),
        Finding.cvss_score.desc()
    ).offset(skip).limit(limit).all()


def get_findings_by_severity(db, severity: str, limit: int = 100):
    """Get findings by severity (uses idx_finding_severity_created)"""
    return db.query(Finding).filter(
        Finding.severity == severity
    ).order_by(Finding.created_at.desc()).limit(limit).all()


def get_findings_by_cve(db, cve_id: str):
    """Get findings by CVE ID (uses idx_finding_cve)"""
    return db.query(Finding).filter(Finding.cve_id == cve_id).all()


def create_report(db, scan_id: int, format: str, template: str, user_id: int):
    """Erstellt Report-Eintrag"""
    db_report = Report(
        scan_id=scan_id, 
        format=format, 
        template=template, 
        user_id=user_id, 
        status="pending"
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def get_reports(db, skip: int = 0, limit: int = 100, status: str = None):
    """Listet Reports auf with optional filtering"""
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


def create_audit_log(
    db, user_id: int, action: str, resource_type: str, resource_id: int, details: dict, ip_address: str = None
):
    """Erstellt Audit-Log-Eintrag"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()


# Query result caching
def get_cached_query(db, cache_key: str) -> Optional[dict]:
    """Get cached query result if not expired."""
    entry = db.query(CacheEntry).filter(
        CacheEntry.key == cache_key,
        CacheEntry.expires_at > datetime.utcnow()
    ).first()
    
    if entry:
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        db.commit()
        return entry.value
    return None


def set_cached_query(db, cache_key: str, value: dict, ttl_seconds: int = 300):
    """Cache query result."""
    entry = db.query(CacheEntry).filter(CacheEntry.key == cache_key).first()
    
    if entry:
        entry.value = value
        entry.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    else:
        entry = CacheEntry(
            key=cache_key,
            value=value,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds)
        )
        db.add(entry)
    
    db.commit()


# Default Admin User erstellen
def create_default_admin():
    """Erstellt default Admin-User"""
    db = SessionLocal()
    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            hashed = pwd_context.hash("admin")
            admin = User(username="admin", email="admin@zen-pentest.local", hashed_password=hashed, role="admin")
            db.add(admin)
            db.commit()
            print("Default admin user created (admin/admin)")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    create_default_admin()
    print("Database initialized")
