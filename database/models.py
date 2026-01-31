"""
SQLAlchemy Database Models

PostgreSQL Datenbank-Schema für Zen-AI-Pentest.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scans = relationship("Scan", back_populates="user")
    reports = relationship("Report", back_populates="user")

class Scan(Base):
    """Pentest Scan"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    target = Column(String(500), nullable=False)
    scan_type = Column(String(100), nullable=False)  # network, web, ad, wireless
    status = Column(String(50), default=ScanStatus.PENDING)
    config = Column(JSON, default={})  # Tool-Konfiguration
    result_summary = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan")

class Finding(Base):
    """Sicherheits-Befund"""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(50), default=Severity.MEDIUM)
    cvss_score = Column(Float)
    cve_id = Column(String(100))
    evidence = Column(Text)  # Screenshots, Logs, etc.
    remediation = Column(Text)
    tool = Column(String(100))  # Welches Tool hat es gefunden
    target = Column(String(500))  # Spezifisches Ziel (IP, URL, etc.)
    port = Column(Integer)
    service = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    verified = Column(Integer, default=0)  # 0=unverified, 1=verified, 2=false_positive
    
    # Relationships
    scan = relationship("Scan", back_populates="findings")

class Report(Base):
    """Generierter Bericht"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    format = Column(String(50), default=ReportFormat.PDF)
    template = Column(String(100), default="default")
    status = Column(String(50), default=ReportStatus.PENDING)
    file_path = Column(String(1000))
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_at = Column(DateTime)
    
    # Relationships
    scan = relationship("Scan", back_populates="reports")
    user = relationship("User", back_populates="reports")

class VulnerabilityDB(Base):
    """Lokale CVE/Exploit-Datenbank"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(100), unique=True, index=True)
    title = Column(String(500))
    description = Column(Text)
    severity = Column(String(50))
    cvss_score = Column(Float)
    epss_score = Column(Float)
    affected_products = Column(JSON)
    references = Column(JSON)
    exploits = Column(JSON)  # Links zu Exploits
    updated_at = Column(DateTime, default=datetime.utcnow)

class Asset(Base):
    """Asset-Management"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(100))  # server, workstation, network_device, application
    ip_address = Column(String(50))
    hostname = Column(String(255))
    os = Column(String(100))
    services = Column(JSON)  # Offene Ports & Services
    owner = Column(String(255))
    criticality = Column(String(50), default="medium")  # critical, high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scanned = Column(DateTime)

class AuditLog(Base):
    """Audit-Logging für Compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)  # create_scan, delete_scan, etc.
    resource_type = Column(String(100))  # scan, finding, report
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    """Benachrichtigungen"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50))  # scan_completed, finding_critical, etc.
    title = Column(String(255))
    message = Column(Text)
    read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ToolConfig(Base):
    """Tool-Konfigurationen pro User/Team"""
    __tablename__ = "tool_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tool_name = Column(String(100), nullable=False)
    config = Column(JSON, default={})  # Tool-spezifische Einstellungen
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

import os

# PostgreSQL URL - in production aus Umgebungsvariablen
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/zen_pentest")

try:
    # Versuche PostgreSQL Engine zu erstellen
    engine = create_engine(DATABASE_URL)
    # Teste Verbindung (import check)
    import psycopg2
except (ImportError, Exception):
    # Fallback auf SQLite für lokale Entwicklung/Tests
    print("⚠️  PostgreSQL/psycopg2 nicht verfügbar. Nutze SQLite Fallback (zen_pentest.db)")
    DATABASE_URL = "sqlite:///./zen_pentest.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialisiert die Datenbank"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency für FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# CRUD OPERATIONS
# ============================================================================

def create_scan(db, name: str, target: str, scan_type: str, 
                config: dict, user_id: int):
    """Erstellt neuen Scan"""
    db_scan = Scan(
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

def get_scan(db, scan_id: int):
    """Holt Scan by ID"""
    return db.query(Scan).filter(Scan.id == scan_id).first()

def get_scans(db, skip: int = 0, limit: int = 100, status: str = None):
    """Listet Scans auf"""
    query = db.query(Scan)
    if status:
        query = query.filter(Scan.status == status)
    return query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()

def update_scan_status(db, scan_id: int, status: str, result: dict = None):
    """Aktualisiert Scan-Status"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.status = status
        if result:
            scan.result_summary = str(result)
        if status == "running":
            scan.started_at = datetime.utcnow()
        if status in ["completed", "failed"]:
            scan.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(scan)
    return scan

def create_finding(db, scan_id: int, title: str, description: str,
                  severity: str = "medium", cvss_score: float = None,
                  evidence: str = None, tool: str = None):
    """Erstellt neuen Befund"""
    db_finding = Finding(
        scan_id=scan_id,
        title=title,
        description=description,
        severity=severity,
        cvss_score=cvss_score,
        evidence=evidence,
        tool=tool
    )
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    return db_finding

def get_findings(db, scan_id: int, severity: str = None):
    """Holt Befunde für Scan"""
    query = db.query(Finding).filter(Finding.scan_id == scan_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    return query.order_by(Finding.created_at.desc()).all()

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

def get_reports(db, skip: int = 0, limit: int = 100):
    """Listet Reports auf"""
    return db.query(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit).all()

def create_audit_log(db, user_id: int, action: str, resource_type: str,
                    resource_id: int, details: dict, ip_address: str = None):
    """Erstellt Audit-Log-Eintrag"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
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
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("Default admin user created (admin/admin)")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    create_default_admin()
    print("Database initialized")
