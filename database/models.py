"""
SQLAlchemy Database Models - Optimized with Indexes

PostgreSQL Database Schema für Zen-AI-Pentest.
Performance optimizations:
- Strategic indexes for common queries
- Connection pooling configuration
- Query optimization hints
"""

import enum
import os
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

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
    """Benutzer-Account with optimized indexes"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="operator", index=True)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    scans = relationship("Scan", back_populates="user", lazy="dynamic")
    reports = relationship("Report", back_populates="user", lazy="dynamic")

    # Composite index for common lookup pattern
    __table_args__ = (Index("ix_users_role_active", "role", "is_active"),)


class Scan(Base):
    """Pentest Scan with performance indexes"""

    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    target = Column(String(500), nullable=False, index=True)
    scan_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default=ScanStatus.PENDING, index=True)
    config = Column(JSON, default={})
    result_summary = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime, index=True)

    # Relationships
    user = relationship("User", back_populates="scans")
    findings = relationship(
        "Finding",
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    reports = relationship("Report", back_populates="scan", lazy="dynamic")

    # Composite indexes for common query patterns
    __table_args__ = (
        # For filtering by status and date range
        Index("ix_scans_status_created", "status", "created_at"),
        # For user scans sorted by date
        Index("ix_scans_user_created", "user_id", "created_at"),
        # For target-based lookups
        Index("ix_scans_target_type", "target", "scan_type"),
    )


class Finding(Base):
    """Sicherheits-Befund with optimized indexes"""

    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(
        Integer, ForeignKey("scans.id"), nullable=False, index=True
    )
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(50), default=Severity.MEDIUM, index=True)
    cvss_score = Column(Float, index=True)
    cve_id = Column(String(100), index=True)
    evidence = Column(Text)
    remediation = Column(Text)
    tool = Column(String(100), index=True)
    target = Column(String(500), index=True)
    port = Column(Integer, index=True)
    service = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    verified = Column(Integer, default=0, index=True)

    # Relationships
    scan = relationship("Scan", back_populates="findings")

    # Composite indexes for efficient querying
    __table_args__ = (
        # For severity filtering within a scan
        Index("ix_findings_scan_severity", "scan_id", "severity"),
        # For verified findings by severity
        Index("ix_findings_severity_verified", "severity", "verified"),
        # For tool-based analysis
        Index("ix_findings_tool_created", "tool", "created_at"),
        # For target-based searches
        Index("ix_findings_target_severity", "target", "severity"),
    )


class Report(Base):
    """Generierter Bericht"""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    format = Column(String(50), default=ReportFormat.PDF)
    template = Column(String(100))
    status = Column(String(50), default=ReportStatus.PENDING, index=True)
    file_path = Column(String(1000))
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    generated_at = Column(DateTime)

    # Relationships
    scan = relationship("Scan", back_populates="reports")
    user = relationship("User", back_populates="reports")

    __table_args__ = (
        Index("ix_reports_status_created", "status", "created_at"),
    )


class VulnerabilityDB(Base):
    """Lokale CVE/Exploit-Datenbank with full-text search support"""

    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500))
    description = Column(Text)
    severity = Column(String(50), index=True)
    cvss_score = Column(Float, index=True)
    epss_score = Column(Float, index=True)
    affected_products = Column(JSON)
    references = Column(JSON)
    exploits = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_vulns_severity_cvss", "severity", "cvss_score"),
        Index("ix_vulns_cve_updated", "cve_id", "updated_at"),
    )


class Asset(Base):
    """Asset-Management with geographic and network indexes"""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    asset_type = Column(String(100), index=True)
    ip_address = Column(String(50), index=True)
    hostname = Column(String(255), index=True)
    os = Column(String(100))
    services = Column(JSON)
    owner = Column(String(255), index=True)
    criticality = Column(String(50), default="medium", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_scanned = Column(DateTime, index=True)

    __table_args__ = (
        Index("ix_assets_type_criticality", "asset_type", "criticality"),
        Index("ix_assets_owner_scanned", "owner", "last_scanned"),
    )


class AuditLog(Base):
    """Audit-Logging für Compliance with time-series indexing"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), index=True)
    resource_id = Column(Integer, index=True)
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        # For time-based audit queries
        Index("ix_audit_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_action_timestamp", "action", "timestamp"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )


class Notification(Base):
    """Benachrichtigungen with read status indexing"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(String(50), index=True)
    title = Column(String(255))
    message = Column(Text)
    read = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        # For unread notifications per user
        Index("ix_notifications_user_read", "user_id", "read", "created_at"),
    )


class ToolConfig(Base):
    """Tool-Konfigurationen pro User/Team"""

    __tablename__ = "tool_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_toolconfig_user_tool", "user_id", "tool_name"),
    )


# ============================================================================
# DATABASE CONNECTION - OPTIMIZED
# ============================================================================

# PostgreSQL URL - in production aus Umgebungsvariablen
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/zen_pentest"
)

# =============================================================================
# Connection Pool Configuration - Optimized
# =============================================================================
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

# Connection Pool arguments - Optimized for production
engine_args = {
    "pool_size": POOL_SIZE,
    "max_overflow": MAX_OVERFLOW,
    "pool_timeout": POOL_TIMEOUT,
    "pool_recycle": POOL_RECYCLE,
    "pool_pre_ping": POOL_PRE_PING,
    "pool_use_lifo": True,  # LIFO for better cache locality
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
}

# Connection arguments for PostgreSQL
connect_args = {
    "connect_timeout": 10,
    "application_name": "zen-ai-pentest",
}

try:
    # Try PostgreSQL with optimized settings
    print(
        f"Connecting to PostgreSQL with pool_size={POOL_SIZE}, max_overflow={MAX_OVERFLOW}"
    )
    engine = create_engine(
        DATABASE_URL,
        **engine_args,
        connect_args=connect_args,
    )
except ImportError:
    # Fallback auf SQLite für lokale Entwicklung/Tests
    print(
        "Warning: PostgreSQL/psycopg2 not available. Using SQLite fallback (zen_pentest.db)"
    )
    DATABASE_URL = "sqlite:///./zen_pentest.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        **{
            k: v
            for k, v in engine_args.items()
            if k not in ["pool_use_lifo", "pool_pre_ping"]
        },
    )
except Exception as e:
    print(
        f"Warning: PostgreSQL connection failed ({e}). Using SQLite fallback (zen_pentest.db)"
    )
    DATABASE_URL = "sqlite:///./zen_pentest.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        **{
            k: v
            for k, v in engine_args.items()
            if k not in ["pool_use_lifo", "pool_pre_ping"]
        },
    )

# Optimized session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Better performance for read-heavy workloads
)


def init_db():
    """Initialisiert die Datenbank mit all indexes"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency für FastAPI with automatic cleanup"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# OPTIMIZED CRUD OPERATIONS
# ============================================================================


def create_scan(
    db, name: str, target: str, scan_type: str, config: dict, user_id: int
):
    """Erstellt neuen Scan"""
    db_scan = Scan(
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


def get_scan(db, scan_id: int):
    """Holt Scan by ID - uses index on id"""
    return db.query(Scan).filter(Scan.id == scan_id).first()


def get_scans(db, skip: int = 0, limit: int = 100, status: str = None):
    """Listet Scans auf - uses composite index"""
    query = db.query(Scan)
    if status:
        query = query.filter(Scan.status == status)
    # Use the composite index (status, created_at) or (user_id, created_at)
    return (
        query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
    )


def get_scans_by_user(db, user_id: int, skip: int = 0, limit: int = 100):
    """Get scans for a specific user - uses composite index"""
    return (
        db.query(Scan)
        .filter(Scan.user_id == user_id)
        .order_by(Scan.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_scan_status(db, scan_id: int, status: str, result: dict = None):
    """Aktualisiert Scan-Status"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.status = status
        if result:
            scan.result_summary = str(result)
        if status == "running":
            scan.started_at = datetime.now(timezone.utc)
        if status in ["completed", "failed"]:
            scan.completed_at = datetime.now(timezone.utc)
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
    """Erstellt neuen Befund"""
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
    db.commit()
    db.refresh(db_finding)
    return db_finding


def bulk_create_findings(db, findings_data: list):
    """Efficiently create multiple findings using bulk insert"""
    db.bulk_insert_mappings(Finding, findings_data)
    db.commit()


def get_findings(db, scan_id: int, severity: str = None):
    """Holt Befunde für Scan - uses composite index"""
    query = db.query(Finding).filter(Finding.scan_id == scan_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    return query.order_by(Finding.created_at.desc()).all()


def get_findings_by_severity(db, severity: str, limit: int = 100):
    """Get findings filtered by severity - uses index"""
    return (
        db.query(Finding)
        .filter(Finding.severity == severity)
        .order_by(Finding.created_at.desc())
        .limit(limit)
        .all()
    )


def create_report(db, scan_id: int, format: str, template: str, user_id: int):
    """Erstellt Report-Eintrag"""
    db_report = Report(
        scan_id=scan_id,
        format=format,
        template=template,
        user_id=user_id,
        status="pending",
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def get_reports(db, skip: int = 0, limit: int = 100):
    """Listet Reports auf"""
    return (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_audit_log(
    db,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    details: dict,
    ip_address: str = None,
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
            admin = User(
                username="admin",
                email="admin@zen-pentest.local",
                hashed_password=hashed,
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("Default admin user created (admin/admin)")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    create_default_admin()
    print("Database initialized with optimized indexes")
