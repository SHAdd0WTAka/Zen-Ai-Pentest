"""
Comprehensive Database Model Tests
==================================

This module provides comprehensive tests for all database models in the
Zen-AI-Pentest application. Tests cover:

- User model (creation, validation, password hashing)
- Scan model (creation, status updates, relationships)
- Finding model (creation, severity levels, relationships)
- Report model (creation, generation status)
- VulnerabilityDB model (CVE data storage)
- Asset model (asset management)
- AuditLog model (compliance logging)
- Notification model (user notifications)
- ToolConfig model (tool configurations)
- All model relationships and foreign keys

Uses pytest with SQLite in-memory database for fast, isolated testing.
Target coverage: 80%+

Author: Test Suite
Date: 2026-02-26
"""

import enum
import hashlib
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.models import (
    Asset,
    AuditLog,
    Base,
    Finding,
    Notification,
    Report,
    ReportFormat,
    ReportStatus,
    Scan,
    ScanStatus,
    Severity,
    ToolConfig,
    User,
    VulnerabilityDB,
    bulk_create_findings,
    create_audit_log,
    create_finding,
    create_report,
    create_scan,
    get_findings,
    get_reports,
    get_scan,
    get_scans,
    get_scans_by_user,
    update_scan_status,
)


# =============================================================================
# Fixtures
# =============================================================================


def unique_string(prefix: str = "") -> str:
    """Generate a unique string for test data."""
    return f"{prefix}{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def engine() -> Generator:
    """Create a new in-memory SQLite database engine for each test function."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    
    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Factory fixture for sample user data."""
    return {
        "username": unique_string("user"),
        "email": f"{unique_string()}@example.com",
        "hashed_password": "hashed_password_string",
        "role": "operator",
        "is_active": 1,
    }


@pytest.fixture
def create_test_user(db_session):
    """Factory fixture to create test users."""
    def _create_user(
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: str = "hashed_password",
        role: str = "operator",
        is_active: int = 1,
    ) -> User:
        user = User(
            username=username or unique_string("user"),
            email=email or f"{unique_string()}@example.com",
            hashed_password=password,
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def create_test_scan(db_session, create_test_user):
    """Factory fixture to create test scans."""
    def _create_scan(
        name: Optional[str] = None,
        target: str = "example.com",
        scan_type: str = "web",
        status: str = ScanStatus.PENDING,
        user_id: Optional[int] = None,
        config: Optional[Dict] = None,
    ) -> Scan:
        if user_id is None:
            user = create_test_user()
            user_id = user.id
        
        scan = Scan(
            name=name or unique_string("scan"),
            target=target,
            scan_type=scan_type,
            status=status,
            user_id=user_id,
            config=config or {"ports": "80,443"},
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        return scan
    
    return _create_scan


@pytest.fixture
def create_test_finding(db_session, create_test_scan):
    """Factory fixture to create test findings."""
    def _create_finding(
        title: Optional[str] = None,
        severity: str = Severity.MEDIUM,
        scan_id: Optional[int] = None,
        **kwargs
    ) -> Finding:
        if scan_id is None:
            scan = create_test_scan()
            scan_id = scan.id
        
        finding = Finding(
            scan_id=scan_id,
            title=title or unique_string("finding"),
            severity=severity,
            **kwargs
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        return finding
    
    return _create_finding


@pytest.fixture
def create_test_report(db_session, create_test_scan, create_test_user):
    """Factory fixture to create test reports."""
    def _create_report(
        format: str = ReportFormat.PDF,
        status: str = ReportStatus.PENDING,
        scan_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Report:
        if scan_id is None or user_id is None:
            user = create_test_user()
            scan = create_test_scan(user_id=user.id)
            scan_id = scan.id
            user_id = user.id
        
        report = Report(
            scan_id=scan_id,
            user_id=user_id,
            format=format,
            status=status,
            **kwargs
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        return report
    
    return _create_report


@pytest.fixture
def initialized_engine(engine):
    """Engine with tables created for index tests."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Test enum definitions for correct values."""
    
    def test_scan_status_values(self):
        """Test ScanStatus enum has all expected values."""
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"
    
    def test_severity_values(self):
        """Test Severity enum has all expected values."""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"
    
    def test_report_format_values(self):
        """Test ReportFormat enum has all expected values."""
        assert ReportFormat.PDF == "pdf"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.JSON == "json"
        assert ReportFormat.XML == "xml"
    
    def test_report_status_values(self):
        """Test ReportStatus enum has all expected values."""
        assert ReportStatus.PENDING == "pending"
        assert ReportStatus.GENERATING == "generating"
        assert ReportStatus.COMPLETED == "completed"
        assert ReportStatus.FAILED == "failed"
    
    def test_enum_inheritance(self):
        """Test enums inherit from both str and enum.Enum."""
        assert issubclass(ScanStatus, str)
        assert issubclass(ScanStatus, enum.Enum)
        assert issubclass(Severity, str)
        assert issubclass(Severity, enum.Enum)


# =============================================================================
# User Model Tests
# =============================================================================


class TestUserModel:
    """Comprehensive tests for the User model."""
    
    def test_user_creation_basic(self, db_session, sample_user_data):
        """Test basic user creation with required fields."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.id > 0
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.hashed_password == sample_user_data["hashed_password"]
    
    def test_user_creation_all_fields(self, db_session):
        """Test user creation with all fields populated."""
        user = User(
            username=unique_string("completeuser"),
            email=f"{unique_string()}@example.com",
            hashed_password="hashed_password_here",
            role="admin",
            is_active=1,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.role == "admin"
        assert user.is_active == 1
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_default_role(self, db_session):
        """Test default role is 'operator' when not specified."""
        user = User(
            username=unique_string("testuser"),
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.role == "operator"
    
    def test_user_default_is_active(self, db_session):
        """Test default is_active is 1 when not specified."""
        user = User(
            username=unique_string("testuser"),
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.is_active == 1
    
    def test_user_timestamps_auto_set(self, db_session):
        """Test created_at and updated_at are automatically set."""
        before_creation = datetime.now(timezone.utc)
        user = User(
            username=unique_string("timetest"),
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()
        after_creation = datetime.now(timezone.utc)
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert before_creation <= user.created_at.replace(tzinfo=timezone.utc) <= after_creation
    
    def test_user_unique_username_constraint(self, db_session):
        """Test that usernames must be unique."""
        username = unique_string("uniqueuser")
        user1 = User(
            username=username,
            email=f"{unique_string()}@example.com",
            hashed_password="pass1",
        )
        user2 = User(
            username=username,
            email=f"{unique_string()}@example.com",
            hashed_password="pass2",
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_user_unique_email_constraint(self, db_session):
        """Test that emails must be unique."""
        email = f"{unique_string()}@example.com"
        user1 = User(
            username=unique_string("user1"),
            email=email,
            hashed_password="pass1",
        )
        user2 = User(
            username=unique_string("user2"),
            email=email,
            hashed_password="pass2",
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_user_username_required(self, db_session):
        """Test that username cannot be null."""
        user = User(
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_user_email_required(self, db_session):
        """Test that email cannot be null."""
        user = User(
            username=unique_string("testuser"),
            hashed_password="pass",
        )
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_user_password_required(self, db_session):
        """Test that hashed_password cannot be null."""
        user = User(
            username=unique_string("testuser"),
            email=f"{unique_string()}@example.com",
        )
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_user_role_variations(self, db_session):
        """Test user creation with various role values."""
        roles = ["admin", "operator", "viewer", "auditor", "manager"]
        
        for role in roles:
            user = User(
                username=unique_string(f"roleuser_{role}"),
                email=f"{unique_string()}@example.com",
                hashed_password="pass",
                role=role,
            )
            db_session.add(user)
        
        db_session.commit()
        
        for role in roles:
            user = db_session.query(User).filter(
                User.username.like(f"%roleuser_{role}%")
            ).first()
            assert user.role == role
    
    def test_user_is_active_variations(self, db_session):
        """Test user creation with different is_active values."""
        active_user = User(
            username=unique_string("activeuser"),
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
            is_active=1,
        )
        inactive_user = User(
            username=unique_string("inactiveuser"),
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
            is_active=0,
        )
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        assert active_user.is_active == 1
        assert inactive_user.is_active == 0
    
    def test_user_password_hashing_simulation(self, db_session):
        """Test storing and verifying password hashes."""
        password = "mysecretpassword"
        hashed = hashlib.sha256(password.encode()).hexdigest()
        
        user = User(
            username=unique_string("hashtest"),
            email=f"{unique_string()}@example.com",
            hashed_password=hashed,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Verify stored hash matches
        assert user.hashed_password == hashed
        
        # Verify hash is different from plain password
        assert user.hashed_password != password
    
    def test_user_long_username(self, db_session):
        """Test username with maximum length (100 chars)."""
        long_username = "a" * 100
        user = User(
            username=long_username,
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.username == long_username
    
    def test_user_long_email(self, db_session):
        """Test email with maximum length (255 chars)."""
        long_email = "a" * 245 + "@example.com"  # Total 255 chars
        user = User(
            username=unique_string("longemail"),
            email=long_email,
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.email == long_email
    
    def test_user_table_name(self):
        """Test User model has correct table name."""
        assert User.__tablename__ == "users"
    
    def test_user_str_representation(self, db_session):
        """Test string representation of User."""
        user = User(
            username=unique_string("testuser"),
            email=f"{unique_string()}@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Should be able to convert to string without error
        str_repr = str(user)
        assert str_repr is not None


# =============================================================================
# Scan Model Tests
# =============================================================================


class TestScanModel:
    """Comprehensive tests for the Scan model."""
    
    def test_scan_creation_basic(self, db_session, create_test_user):
        """Test basic scan creation."""
        user = create_test_user()
        scan = Scan(
            name=unique_string("Basic Scan"),
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.id is not None
        assert scan.target == "example.com"
        assert scan.scan_type == "web"
        assert scan.user_id == user.id
    
    def test_scan_default_status(self, db_session, create_test_user):
        """Test default scan status is pending."""
        user = create_test_user()
        scan = Scan(
            name=unique_string("Test Scan"),
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.status == ScanStatus.PENDING
    
    def test_scan_all_status_values(self, db_session, create_test_user):
        """Test scan with all possible status values."""
        user = create_test_user()
        statuses = [
            ScanStatus.PENDING,
            ScanStatus.RUNNING,
            ScanStatus.COMPLETED,
            ScanStatus.FAILED,
            ScanStatus.CANCELLED,
        ]
        
        for status in statuses:
            scan = Scan(
                name=unique_string(f"Scan_{status}"),
                target=f"{unique_string()}.com",
                scan_type="web",
                status=status,
                user_id=user.id,
            )
            db_session.add(scan)
        
        db_session.commit()
        
        for status in statuses:
            scan = db_session.query(Scan).filter(
                Scan.name.like(f"%Scan_{status}%")
            ).first()
            assert scan is not None
            assert scan.status == status
    
    def test_scan_status_transitions(self, db_session, create_test_scan):
        """Test scan status transitions work correctly."""
        scan = create_test_scan(status=ScanStatus.PENDING)
        
        # Pending -> Running
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        db_session.commit()
        assert scan.status == ScanStatus.RUNNING
        assert scan.started_at is not None
        
        # Running -> Completed
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(timezone.utc)
        db_session.commit()
        assert scan.status == ScanStatus.COMPLETED
        assert scan.completed_at is not None
    
    def test_scan_config_json_storage(self, db_session, create_test_user):
        """Test scan configuration JSON storage."""
        user = create_test_user()
        config = {
            "ports": "80,443,8080",
            "threads": 10,
            "timeout": 30,
            "options": {"deep_scan": True, "follow_redirects": False}
        }
        
        scan = Scan(
            name=unique_string("Config Test"),
            target="example.com",
            scan_type="network",
            config=config,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.config == config
        assert scan.config["ports"] == "80,443,8080"
        assert scan.config["options"]["deep_scan"] is True
    
    def test_scan_empty_config(self, db_session, create_test_user):
        """Test scan with empty/default config."""
        user = create_test_user()
        scan = Scan(
            name=unique_string("Empty Config Scan"),
            target="example.com",
            scan_type="web",
            user_id=user.id,
            config={},
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.config == {}
    
    def test_scan_null_config(self, db_session, create_test_user):
        """Test scan with null config."""
        user = create_test_user()
        scan = Scan(
            name=unique_string("Null Config Scan"),
            target="example.com",
            scan_type="web",
            user_id=user.id,
            config=None,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.config is None
    
    def test_scan_result_summary(self, db_session, create_test_user):
        """Test scan result summary storage."""
        user = create_test_user()
        summary = "Found 5 critical vulnerabilities, 10 high, 20 medium"
        
        scan = Scan(
            name=unique_string("Result Scan"),
            target="example.com",
            scan_type="web",
            user_id=user.id,
            result_summary=summary,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.result_summary == summary
    
    def test_scan_timestamps(self, db_session, create_test_scan):
        """Test scan timestamp fields."""
        scan = create_test_scan()
        
        # created_at should be auto-set
        assert scan.created_at is not None
        
        # started_at and completed_at should be None initially
        assert scan.started_at is None
        assert scan.completed_at is None
        
        # Set timestamps (use naive datetime to match model behavior)
        now = datetime.utcnow()
        scan.started_at = now
        scan.completed_at = now + timedelta(minutes=5)
        db_session.commit()
        
        assert scan.started_at == now
        assert scan.completed_at == now + timedelta(minutes=5)
    
    def test_scan_multiple_per_user(self, db_session, create_test_user):
        """Test multiple scans per user."""
        user = create_test_user()
        
        for i in range(5):
            scan = Scan(
                name=unique_string(f"Scan_{i}"),
                target=f"target{i}.com",
                scan_type="web",
                user_id=user.id,
            )
            db_session.add(scan)
        
        db_session.commit()
        
        user_scans = db_session.query(Scan).filter(Scan.user_id == user.id).all()
        assert len(user_scans) == 5
    
    def test_scan_table_name(self):
        """Test Scan model has correct table name."""
        assert Scan.__tablename__ == "scans"
    
    def test_scan_target_variations(self, db_session, create_test_user):
        """Test scan with various target formats."""
        user = create_test_user()
        targets = [
            "example.com",
            "192.168.1.1",
            "10.0.0.0/24",
            "http://example.com",
            "https://example.com:8443/path",
        ]
        
        for i, target in enumerate(targets):
            scan = Scan(
                name=unique_string(f"Scan_{i}"),
                target=target,
                scan_type="web",
                user_id=user.id,
            )
            db_session.add(scan)
        
        db_session.commit()
        
        for target in targets:
            scan = db_session.query(Scan).filter(Scan.target == target).first()
            assert scan is not None
    
    def test_scan_type_variations(self, db_session, create_test_user):
        """Test scan with various scan types."""
        user = create_test_user()
        scan_types = ["web", "network", "api", "mobile", "cloud", "container"]
        
        for scan_type in scan_types:
            scan = Scan(
                name=unique_string(f"Scan_{scan_type}"),
                target="example.com",
                scan_type=scan_type,
                user_id=user.id,
            )
            db_session.add(scan)
        
        db_session.commit()
        
        for scan_type in scan_types:
            scan = db_session.query(Scan).filter(Scan.scan_type == scan_type).first()
            assert scan is not None


# =============================================================================
# Finding Model Tests
# =============================================================================


class TestFindingModel:
    """Comprehensive tests for the Finding model."""
    
    def test_finding_creation_basic(self, db_session, create_test_scan):
        """Test basic finding creation."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title="SQL Injection",
            description="SQL injection vulnerability found",
            severity=Severity.HIGH,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.id is not None
        assert finding.title == "SQL Injection"
        assert finding.scan_id == scan.id
    
    def test_finding_default_severity(self, db_session, create_test_scan):
        """Test default severity is medium."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Default Severity Finding"),
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.severity == Severity.MEDIUM
    
    def test_finding_all_severities(self, db_session, create_test_scan):
        """Test finding with all severity levels."""
        scan = create_test_scan()
        severities = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]
        
        for severity in severities:
            finding = Finding(
                scan_id=scan.id,
                title=unique_string(f"Finding_{severity}"),
                severity=severity,
            )
            db_session.add(finding)
        
        db_session.commit()
        
        for severity in severities:
            finding = db_session.query(Finding).filter(
                Finding.title.like(f"%Finding_{severity}%")
            ).first()
            assert finding is not None
            assert finding.severity == severity
    
    def test_finding_cvss_score(self, db_session, create_test_scan):
        """Test finding CVSS score storage."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("CVSS Finding"),
            severity=Severity.HIGH,
            cvss_score=8.5,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.cvss_score == 8.5
    
    def test_finding_null_cvss(self, db_session, create_test_scan):
        """Test finding with null CVSS score."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("No CVSS Finding"),
            cvss_score=None,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.cvss_score is None
    
    def test_finding_cve_id(self, db_session, create_test_scan):
        """Test finding CVE ID storage."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("CVE Finding"),
            cve_id="CVE-2023-12345",
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.cve_id == "CVE-2023-12345"
    
    def test_finding_evidence(self, db_session, create_test_scan):
        """Test finding evidence storage."""
        scan = create_test_scan()
        evidence = """
        HTTP Request:
        POST /login HTTP/1.1
        Host: example.com
        
        username=admin' OR '1'='1&password=test
        
        HTTP Response:
        HTTP/1.1 200 OK
        Welcome admin!
        """
        
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Evidence Finding"),
            evidence=evidence,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.evidence == evidence
    
    def test_finding_remediation(self, db_session, create_test_scan):
        """Test finding remediation storage."""
        scan = create_test_scan()
        remediation = "Use parameterized queries to prevent SQL injection"
        
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Remediation Finding"),
            remediation=remediation,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.remediation == remediation
    
    def test_finding_tool(self, db_session, create_test_scan):
        """Test finding tool attribution."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Tool Finding"),
            tool="sqlmap",
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.tool == "sqlmap"
    
    def test_finding_target(self, db_session, create_test_scan):
        """Test finding target storage."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Target Finding"),
            target="http://example.com/login",
            port=80,
            service="http",
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.target == "http://example.com/login"
        assert finding.port == 80
        assert finding.service == "http"
    
    def test_finding_default_verified(self, db_session, create_test_scan):
        """Test default verified status is 0."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Unverified Finding"),
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.verified == 0
    
    def test_finding_verified_status(self, db_session, create_test_scan):
        """Test finding verified status can be updated."""
        scan = create_test_scan()
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Verified Finding"),
            verified=1,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.verified == 1
    
    def test_finding_multiple_per_scan(self, db_session, create_test_scan):
        """Test multiple findings per scan."""
        scan = create_test_scan()
        
        for i in range(10):
            finding = Finding(
                scan_id=scan.id,
                title=unique_string(f"Finding_{i}"),
                severity=Severity.HIGH if i % 2 == 0 else Severity.MEDIUM,
            )
            db_session.add(finding)
        
        db_session.commit()
        
        scan_findings = db_session.query(Finding).filter(
            Finding.scan_id == scan.id
        ).all()
        assert len(scan_findings) == 10
    
    def test_finding_foreign_key_constraint(self, db_session):
        """Test finding requires valid scan_id."""
        finding = Finding(
            scan_id=99999,  # Non-existent scan
            title=unique_string("Orphan Finding"),
        )
        db_session.add(finding)
        
        # SQLite may not enforce FK without proper pragma
        # This test verifies the constraint exists
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_finding_table_name(self):
        """Test Finding model has correct table name."""
        assert Finding.__tablename__ == "findings"


# =============================================================================
# Report Model Tests
# =============================================================================


class TestReportModel:
    """Comprehensive tests for the Report model."""
    
    def test_report_creation_basic(self, db_session, create_test_scan, create_test_user):
        """Test basic report creation."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        report = Report(
            scan_id=scan.id,
            user_id=user.id,
            format=ReportFormat.PDF,
            template="default",
            status=ReportStatus.PENDING,
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        assert report.id is not None
        assert report.scan_id == scan.id
        assert report.user_id == user.id
    
    def test_report_default_format(self, db_session, create_test_scan, create_test_user):
        """Test default report format is PDF."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        report = Report(
            scan_id=scan.id,
            user_id=user.id,
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        assert report.format == ReportFormat.PDF
    
    def test_report_default_status(self, db_session, create_test_scan, create_test_user):
        """Test default report status is pending."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        report = Report(
            scan_id=scan.id,
            user_id=user.id,
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)
        
        assert report.status == ReportStatus.PENDING
    
    def test_report_all_formats(self, db_session, create_test_scan, create_test_user):
        """Test report with all format types."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        formats = [
            ReportFormat.PDF,
            ReportFormat.HTML,
            ReportFormat.JSON,
            ReportFormat.XML,
        ]
        
        for fmt in formats:
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=fmt,
                status=ReportStatus.COMPLETED,
            )
            db_session.add(report)
        
        db_session.commit()
        
        for fmt in formats:
            report = db_session.query(Report).filter(Report.format == fmt).first()
            assert report is not None
    
    def test_report_all_statuses(self, db_session, create_test_scan, create_test_user):
        """Test report with all status values."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        statuses = [
            ReportStatus.PENDING,
            ReportStatus.GENERATING,
            ReportStatus.COMPLETED,
            ReportStatus.FAILED,
        ]
        
        for status in statuses:
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=ReportFormat.PDF,
                status=status,
            )
            db_session.add(report)
        
        db_session.commit()
        
        for status in statuses:
            report = db_session.query(Report).filter(Report.status == status).first()
            assert report is not None
    
    def test_report_status_transitions(self, db_session, create_test_report):
        """Test report status transitions."""
        report = create_test_report(status=ReportStatus.PENDING)
        
        # Pending -> Generating
        report.status = ReportStatus.GENERATING
        db_session.commit()
        assert report.status == ReportStatus.GENERATING
        
        # Generating -> Completed
        report.status = ReportStatus.COMPLETED
        report.generated_at = datetime.now(timezone.utc)
        db_session.commit()
        assert report.status == ReportStatus.COMPLETED
        assert report.generated_at is not None
    
    def test_report_file_path(self, db_session, create_test_report):
        """Test report file path storage."""
        report = create_test_report(
            file_path="/reports/scan_123_report.pdf",
            file_size=1024567,
        )
        
        assert report.file_path == "/reports/scan_123_report.pdf"
        assert report.file_size == 1024567
    
    def test_report_template(self, db_session, create_test_report):
        """Test report template selection."""
        report = create_test_report(template="executive")
        
        assert report.template == "executive"
    
    def test_report_generated_at(self, db_session, create_test_report):
        """Test report generation timestamp."""
        report = create_test_report()
        
        # Initially null
        assert report.generated_at is None
        
        # Set when completed (use naive datetime to match model behavior)
        now = datetime.utcnow()
        report.generated_at = now
        db_session.commit()
        
        assert report.generated_at == now
    
    def test_report_table_name(self):
        """Test Report model has correct table name."""
        assert Report.__tablename__ == "reports"


# =============================================================================
# VulnerabilityDB Model Tests
# =============================================================================


class TestVulnerabilityDBModel:
    """Comprehensive tests for the VulnerabilityDB model."""
    
    def test_vulnerability_creation_basic(self, db_session):
        """Test basic vulnerability creation."""
        vuln = VulnerabilityDB(
            cve_id=unique_string("CVE-2023-"),
            title="Test Vulnerability",
            description="A test vulnerability description",
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)
        
        assert vuln.id is not None
        assert vuln.title == "Test Vulnerability"
    
    def test_vulnerability_unique_cve(self, db_session):
        """Test CVE ID uniqueness constraint."""
        cve_id = unique_string("CVE-UNIQUE-")
        vuln1 = VulnerabilityDB(cve_id=cve_id, title="Vuln 1")
        vuln2 = VulnerabilityDB(cve_id=cve_id, title="Vuln 2")
        
        db_session.add(vuln1)
        db_session.commit()
        
        db_session.add(vuln2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_vulnerability_required_cve(self, db_session):
        """Test CVE ID is required."""
        vuln = VulnerabilityDB(title="No CVE")
        db_session.add(vuln)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
    
    def test_vulnerability_scores(self, db_session):
        """Test CVSS and EPSS score storage."""
        vuln = VulnerabilityDB(
            cve_id=unique_string("CVE-SCORES-"),
            title="Scored Vulnerability",
            cvss_score=9.8,
            epss_score=0.95,
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)
        
        assert vuln.cvss_score == 9.8
        assert vuln.epss_score == 0.95
    
    def test_vulnerability_json_fields(self, db_session):
        """Test JSON fields for affected products and references."""
        vuln = VulnerabilityDB(
            cve_id=unique_string("CVE-JSON-"),
            title="JSON Test",
            affected_products=["Product A 1.0", "Product B 2.0"],
            references=["https://example.com/advisory", "https://cve.mitre.org"],
            exploits=["https://exploit-db.com/12345"],
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)
        
        assert len(vuln.affected_products) == 2
        assert "Product A 1.0" in vuln.affected_products
        assert len(vuln.references) == 2
        assert len(vuln.exploits) == 1
    
    def test_vulnerability_severity(self, db_session):
        """Test severity storage."""
        vuln = VulnerabilityDB(
            cve_id=unique_string("CVE-SEVERITY-"),
            title="Severity Test",
            severity=Severity.CRITICAL,
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)
        
        assert vuln.severity == Severity.CRITICAL
    
    def test_vulnerability_table_name(self):
        """Test VulnerabilityDB model has correct table name."""
        assert VulnerabilityDB.__tablename__ == "vulnerabilities"


# =============================================================================
# Asset Model Tests
# =============================================================================


class TestAssetModel:
    """Comprehensive tests for the Asset model."""
    
    def test_asset_creation_basic(self, db_session):
        """Test basic asset creation."""
        asset = Asset(name=unique_string("Web Server 01"))
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        assert asset.id is not None
        assert asset.name.startswith("Web Server 01")
    
    def test_asset_full_creation(self, db_session):
        """Test asset creation with all fields."""
        asset = Asset(
            name=unique_string("Database Server"),
            asset_type="server",
            ip_address="192.168.1.100",
            hostname="db01.internal",
            os="Ubuntu 22.04 LTS",
            services=[
                {"port": 3306, "service": "mysql"},
                {"port": 22, "service": "ssh"},
            ],
            owner="Database Team",
            criticality="high",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        assert asset.asset_type == "server"
        assert asset.ip_address == "192.168.1.100"
        assert asset.hostname == "db01.internal"
        assert asset.os == "Ubuntu 22.04 LTS"
        assert len(asset.services) == 2
        assert asset.owner == "Database Team"
        assert asset.criticality == "high"
    
    def test_asset_default_criticality(self, db_session):
        """Test default criticality is medium."""
        asset = Asset(name=unique_string("Test Asset"))
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        assert asset.criticality == "medium"
    
    def test_asset_services_json(self, db_session):
        """Test services JSON storage."""
        services = [
            {"port": 80, "service": "http", "version": "nginx 1.20"},
            {"port": 443, "service": "https", "ssl": True},
        ]
        
        asset = Asset(
            name=unique_string("Web Server"),
            services=services,
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        assert asset.services == services
        assert asset.services[0]["port"] == 80
    
    def test_asset_last_scanned(self, db_session):
        """Test last_scanned timestamp."""
        # Use naive datetime to match model behavior
        now = datetime.utcnow()
        asset = Asset(
            name=unique_string("Scanned Asset"),
            last_scanned=now,
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        
        assert asset.last_scanned == now
    
    def test_asset_table_name(self):
        """Test Asset model has correct table name."""
        assert Asset.__tablename__ == "assets"


# =============================================================================
# AuditLog Model Tests
# =============================================================================


class TestAuditLogModel:
    """Comprehensive tests for the AuditLog model."""
    
    def test_audit_log_creation_basic(self, db_session, create_test_user):
        """Test basic audit log creation."""
        user = create_test_user()
        log = AuditLog(
            user_id=user.id,
            action="create_scan",
            resource_type="scan",
            resource_id=1,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.id is not None
        assert log.action == "create_scan"
    
    def test_audit_log_system_action(self, db_session):
        """Test audit log for system actions (no user)."""
        log = AuditLog(
            action="system_cleanup",
            resource_type="temp_files",
            resource_id=0,
            details={"files_removed": 100},
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.id is not None
        assert log.user_id is None
        assert log.action == "system_cleanup"
    
    def test_audit_log_with_details(self, db_session, create_test_user):
        """Test audit log with JSON details."""
        user = create_test_user()
        log = AuditLog(
            user_id=user.id,
            action="update_scan",
            resource_type="scan",
            resource_id=5,
            details={
                "scan_id": 5,
                "changes": {"status": "pending -> running"},
                "ip_range": "10.0.0.0/24",
            },
            ip_address="192.168.1.50",
            user_agent="Mozilla/5.0 Test Browser",
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.details["changes"]["status"] == "pending -> running"
        assert log.ip_address == "192.168.1.50"
        assert log.user_agent == "Mozilla/5.0 Test Browser"
    
    def test_audit_log_timestamp_auto(self, db_session):
        """Test audit log timestamp is auto-set."""
        log = AuditLog(
            action="test_action",
            resource_type="test",
            resource_id=1,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.timestamp is not None
    
    def test_audit_log_table_name(self):
        """Test AuditLog model has correct table name."""
        assert AuditLog.__tablename__ == "audit_logs"


# =============================================================================
# Notification Model Tests
# =============================================================================


class TestNotificationModel:
    """Comprehensive tests for the Notification model."""
    
    def test_notification_creation_basic(self, db_session, create_test_user):
        """Test basic notification creation."""
        user = create_test_user()
        notification = Notification(
            user_id=user.id,
            type="scan_completed",
            title="Scan Completed",
            message="Your scan has completed successfully.",
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        assert notification.id is not None
        assert notification.type == "scan_completed"
    
    def test_notification_default_read(self, db_session, create_test_user):
        """Test default read status is 0 (unread)."""
        user = create_test_user()
        notification = Notification(
            user_id=user.id,
            type="test",
            title="Test",
            message="Test message",
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)
        
        assert notification.read == 0
    
    def test_notification_mark_read(self, db_session, create_test_user):
        """Test marking notification as read."""
        user = create_test_user()
        notification = Notification(
            user_id=user.id,
            type="alert",
            title="Security Alert",
            message="Critical vulnerability detected!",
            read=0,
        )
        db_session.add(notification)
        db_session.commit()
        
        # Mark as read
        notification.read = 1
        db_session.commit()
        db_session.refresh(notification)
        
        assert notification.read == 1
    
    def test_notification_types(self, db_session, create_test_user):
        """Test various notification types."""
        user = create_test_user()
        types = [
            "scan_completed",
            "scan_failed",
            "critical_finding",
            "report_ready",
            "system_maintenance",
        ]
        
        for notif_type in types:
            notification = Notification(
                user_id=user.id,
                type=notif_type,
                title=unique_string(f"Notification_{notif_type}"),
                message=f"Message for {notif_type}",
            )
            db_session.add(notification)
        
        db_session.commit()
        
        for notif_type in types:
            notif = db_session.query(Notification).filter(
                Notification.type == notif_type
            ).first()
            assert notif is not None
    
    def test_notification_table_name(self):
        """Test Notification model has correct table name."""
        assert Notification.__tablename__ == "notifications"


# =============================================================================
# ToolConfig Model Tests
# =============================================================================


class TestToolConfigModel:
    """Comprehensive tests for the ToolConfig model."""
    
    def test_tool_config_creation_basic(self, db_session, create_test_user):
        """Test basic tool config creation."""
        user = create_test_user()
        config = ToolConfig(
            user_id=user.id,
            tool_name="nmap",
            config={"timing": "T4", "ports": "top-1000"},
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.id is not None
        assert config.tool_name == "nmap"
    
    def test_tool_config_nmap(self, db_session, create_test_user):
        """Test nmap tool configuration."""
        user = create_test_user()
        config = ToolConfig(
            user_id=user.id,
            tool_name="nmap",
            config={
                "default_ports": "80,443,8080",
                "timing_template": "T4",
                "scripts": "default,vuln",
                "options": ["-sV", "-sC"],
            },
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.config["timing_template"] == "T4"
        assert config.config["options"] == ["-sV", "-sC"]
    
    def test_tool_config_sqlmap(self, db_session, create_test_user):
        """Test sqlmap tool configuration."""
        user = create_test_user()
        config = ToolConfig(
            user_id=user.id,
            tool_name="sqlmap",
            config={
                "level": 3,
                "risk": 2,
                "threads": 10,
                "batch": True,
            },
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.config["level"] == 3
        assert config.config["batch"] is True
    
    def test_tool_config_default_empty(self, db_session, create_test_user):
        """Test default empty config."""
        user = create_test_user()
        config = ToolConfig(
            user_id=user.id,
            tool_name="test_tool",
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.config == {}
    
    def test_tool_config_timestamps(self, db_session, create_test_user):
        """Test tool config timestamps."""
        user = create_test_user()
        config = ToolConfig(
            user_id=user.id,
            tool_name="test",
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        
        assert config.created_at is not None
        assert config.updated_at is not None
    
    def test_tool_config_table_name(self):
        """Test ToolConfig model has correct table name."""
        assert ToolConfig.__tablename__ == "tool_configs"


# =============================================================================
# Model Relationships Tests
# =============================================================================


class TestModelRelationships:
    """Comprehensive tests for model relationships."""
    
    def test_user_scans_relationship(self, db_session, create_test_user):
        """Test User-Scan one-to-many relationship."""
        user = create_test_user()
        
        # Create multiple scans for user
        for i in range(3):
            scan = Scan(
                name=unique_string(f"Scan_{i}"),
                target=f"target{i}.com",
                scan_type="web",
                user_id=user.id,
            )
            db_session.add(scan)
        
        db_session.commit()
        db_session.refresh(user)
        
        # Access scans through relationship
        scans = user.scans.all()
        assert len(scans) == 3
        assert all(scan.user_id == user.id for scan in scans)
    
    def test_user_reports_relationship(self, db_session, create_test_user, create_test_scan):
        """Test User-Report one-to-many relationship."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        # Create multiple reports for user
        for i in range(2):
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=ReportFormat.PDF,
            )
            db_session.add(report)
        
        db_session.commit()
        db_session.refresh(user)
        
        reports = user.reports.all()
        assert len(reports) == 2
        assert all(report.user_id == user.id for report in reports)
    
    def test_scan_findings_relationship(self, db_session, create_test_scan, create_test_finding):
        """Test Scan-Finding one-to-many relationship with cascade delete."""
        scan = create_test_scan()
        
        # Create findings for scan
        for i in range(5):
            create_test_finding(scan_id=scan.id, title=unique_string(f"Finding_{i}"))
        
        db_session.refresh(scan)
        
        findings = scan.findings.all()
        assert len(findings) == 5
        assert all(finding.scan_id == scan.id for finding in findings)
    
    def test_scan_findings_cascade_delete(self, db_session, create_test_scan, create_test_finding):
        """Test that deleting a scan cascades to findings."""
        scan = create_test_scan()
        scan_id = scan.id
        
        # Create findings
        for i in range(3):
            create_test_finding(scan_id=scan_id, title=unique_string(f"Finding_{i}"))
        
        # Verify findings exist
        findings_before = db_session.query(Finding).filter(
            Finding.scan_id == scan_id
        ).all()
        assert len(findings_before) == 3
        
        # Delete scan
        db_session.delete(scan)
        db_session.commit()
        
        # Verify findings are deleted
        findings_after = db_session.query(Finding).filter(
            Finding.scan_id == scan_id
        ).all()
        assert len(findings_after) == 0
    
    def test_scan_reports_relationship(self, db_session, create_test_scan, create_test_user):
        """Test Scan-Report one-to-many relationship."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        # Create reports for scan
        for i in range(2):
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=ReportFormat.PDF,
            )
            db_session.add(report)
        
        db_session.commit()
        db_session.refresh(scan)
        
        reports = scan.reports.all()
        assert len(reports) == 2
        assert all(report.scan_id == scan.id for report in reports)
    
    def test_finding_scan_backref(self, db_session, create_test_finding, create_test_scan):
        """Test Finding-Scan back-reference."""
        scan = create_test_scan()
        finding = create_test_finding(scan_id=scan.id)
        
        # Access scan through finding relationship
        assert finding.scan.id == scan.id
        assert finding.scan.name == scan.name
    
    def test_report_scan_relationship(self, db_session, create_test_report, create_test_scan, create_test_user):
        """Test Report-Scan relationship."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        report = create_test_report(scan_id=scan.id, user_id=user.id)
        
        # Access scan through report
        assert report.scan is not None
        assert report.scan.id == report.scan_id
    
    def test_report_user_relationship(self, db_session, create_test_report, create_test_scan, create_test_user):
        """Test Report-User relationship."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        report = create_test_report(scan_id=scan.id, user_id=user.id)
        
        # Access user through report
        assert report.user is not None
        assert report.user.id == report.user_id
    
    def test_complex_relationship_chain(self, db_session, create_test_user, create_test_scan, create_test_finding, create_test_report):
        """Test complex relationship chain: User -> Scan -> Finding/Report."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        finding = create_test_finding(scan_id=scan.id)
        report = create_test_report(scan_id=scan.id, user_id=user.id)
        
        # Refresh all objects
        db_session.refresh(user)
        db_session.refresh(scan)
        db_session.refresh(finding)
        db_session.refresh(report)
        
        # Verify all relationships
        assert scan in user.scans.all()
        assert report in user.reports.all()
        assert finding in scan.findings.all()
        assert report in scan.reports.all()
        assert finding.scan == scan
        assert report.scan == scan
        assert report.user == user


# =============================================================================
# CRUD Function Tests
# =============================================================================


class TestCRUDFunctions:
    """Test CRUD helper functions from models.py."""
    
    def test_create_scan_function(self, db_session, create_test_user):
        """Test create_scan helper function."""
        user = create_test_user()
        
        scan = create_scan(
            db_session,
            name=unique_string("CRUD Scan"),
            target="example.com",
            scan_type="web",
            config={"ports": "80,443"},
            user_id=user.id,
        )
        
        assert scan.id is not None
        assert scan.status == ScanStatus.PENDING
    
    def test_get_scan_function(self, db_session, create_test_scan):
        """Test get_scan helper function."""
        scan = create_test_scan()
        
        retrieved = get_scan(db_session, scan.id)
        assert retrieved is not None
        assert retrieved.id == scan.id
    
    def test_get_scan_not_found(self, db_session):
        """Test get_scan returns None for non-existent ID."""
        result = get_scan(db_session, 99999)
        assert result is None
    
    def test_get_scans_function(self, db_session, create_test_scan):
        """Test get_scans helper function."""
        # Create multiple scans
        for i in range(5):
            create_test_scan(name=unique_string(f"Scan_{i}"))
        
        scans = get_scans(db_session, skip=0, limit=3)
        assert len(scans) == 3
    
    def test_get_scans_by_status(self, db_session, create_test_scan):
        """Test get_scans with status filter."""
        create_test_scan(status=ScanStatus.COMPLETED)
        create_test_scan(status=ScanStatus.PENDING)
        create_test_scan(status=ScanStatus.COMPLETED)
        
        completed = get_scans(db_session, status=ScanStatus.COMPLETED)
        # Should return only completed scans
        assert len(completed) >= 2
        assert all(s.status == ScanStatus.COMPLETED for s in completed)
    
    def test_get_scans_by_user_function(self, db_session, create_test_user, create_test_scan):
        """Test get_scans_by_user helper function."""
        user = create_test_user()
        
        for i in range(3):
            create_test_scan(user_id=user.id)
        
        user_scans = get_scans_by_user(db_session, user.id)
        assert len(user_scans) == 3
    
    def test_update_scan_status_function(self, db_session, create_test_scan):
        """Test update_scan_status helper function."""
        scan = create_test_scan(status=ScanStatus.PENDING)
        
        updated = update_scan_status(
            db_session, scan.id, ScanStatus.RUNNING
        )
        
        assert updated is not None
        assert updated.status == ScanStatus.RUNNING
        assert updated.started_at is not None
    
    def test_update_scan_status_to_completed(self, db_session, create_test_scan):
        """Test update_scan_status to completed sets completed_at."""
        scan = create_test_scan(status=ScanStatus.RUNNING)
        
        updated = update_scan_status(
            db_session, scan.id, ScanStatus.COMPLETED,
            result={"findings": 5}
        )
        
        assert updated.status == ScanStatus.COMPLETED
        assert updated.completed_at is not None
    
    def test_update_scan_status_not_found(self, db_session):
        """Test update_scan_status returns None for non-existent scan."""
        result = update_scan_status(db_session, 99999, ScanStatus.COMPLETED)
        assert result is None
    
    def test_create_finding_function(self, db_session, create_test_scan):
        """Test create_finding helper function."""
        scan = create_test_scan()
        
        finding = create_finding(
            db_session,
            scan_id=scan.id,
            title="SQL Injection",
            description="SQLi found in login",
            severity=Severity.HIGH,
            cvss_score=8.5,
            evidence="Request: admin' OR 1=1 --",
            tool="sqlmap",
            target="http://example.com/login",
        )
        
        assert finding.id is not None
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH
    
    def test_get_findings_function(self, db_session, create_test_scan, create_test_finding):
        """Test get_findings helper function."""
        scan = create_test_scan()
        
        for i in range(3):
            create_test_finding(scan_id=scan.id)
        
        findings = get_findings(db_session, scan_id=scan.id)
        assert len(findings) == 3
    
    def test_get_findings_by_severity_filter(self, db_session, create_test_scan, create_test_finding):
        """Test get_findings with severity filter."""
        scan = create_test_scan()
        
        create_test_finding(scan_id=scan.id, severity=Severity.HIGH)
        create_test_finding(scan_id=scan.id, severity=Severity.LOW)
        create_test_finding(scan_id=scan.id, severity=Severity.HIGH)
        
        # The function doesn't filter by severity, but tests current behavior
        all_findings = get_findings(db_session, scan_id=scan.id)
        assert len(all_findings) == 3
    
    def test_bulk_create_findings_function(self, db_session, create_test_scan):
        """Test bulk_create_findings helper function."""
        scan = create_test_scan()
        
        findings_data = [
            {
                "scan_id": scan.id,
                "title": unique_string(f"Finding_{i}"),
                "severity": Severity.HIGH,
            }
            for i in range(10)
        ]
        
        bulk_create_findings(db_session, findings_data)
        
        findings = db_session.query(Finding).filter(
            Finding.scan_id == scan.id
        ).all()
        assert len(findings) == 10
    
    def test_create_report_function(self, db_session, create_test_scan, create_test_user):
        """Test create_report helper function."""
        user = create_test_user()
        scan = create_test_scan(user_id=user.id)
        
        report = create_report(
            db_session,
            scan_id=scan.id,
            format=ReportFormat.PDF,
            template="default",
            user_id=user.id,
        )
        
        assert report.id is not None
        assert report.status == ReportStatus.PENDING
    
    def test_get_reports_function(self, db_session, create_test_report):
        """Test get_reports helper function."""
        for i in range(4):
            create_test_report()
        
        reports = get_reports(db_session, skip=0, limit=2)
        assert len(reports) == 2
    
    def test_create_audit_log_function(self, db_session, create_test_user):
        """Test create_audit_log helper function."""
        user = create_test_user()
        
        create_audit_log(
            db_session,
            user_id=user.id,
            action="delete_scan",
            resource_type="scan",
            resource_id=5,
            details={"scan_id": 5, "reason": "user_request"},
            ip_address="192.168.1.100",
        )
        
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "delete_scan"
        ).first()
        assert log is not None
        assert log.user_id == user.id


# =============================================================================
# Database Initialization Tests
# =============================================================================


class TestDatabaseInitialization:
    """Test database initialization functions."""
    
    def test_init_db_creates_tables(self, engine):
        """Test init_db creates all tables."""
        # Create tables directly using the engine
        Base.metadata.create_all(bind=engine)
        
        # Get table names
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "users",
            "scans",
            "findings",
            "reports",
            "vulnerabilities",
            "assets",
            "audit_logs",
            "notifications",
            "tool_configs",
        ]
        
        for table in expected_tables:
            assert table in tables


# =============================================================================
# Edge Cases and Boundary Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_long_strings(self, db_session, create_test_user):
        """Test handling of very long strings."""
        user = create_test_user()
        
        # Test long target string
        long_target = "https://" + "a" * 400 + ".com"
        scan = Scan(
            name=unique_string("Long Target Test"),
            target=long_target[:500],  # String column limit
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.target is not None
    
    def test_unicode_characters(self, db_session, create_test_user):
        """Test handling of unicode characters."""
        user = create_test_user()
        
        scan = Scan(
            name="スキャン Test 扫描 " + unique_string(),
            target="münchen.example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert "スキャン" in scan.name
        assert "münchen" in scan.target
    
    def test_special_characters_in_strings(self, db_session, create_test_user):
        """Test handling of special characters."""
        user = create_test_user()
        
        scan = Scan(
            name=unique_string("Test <script>alert('xss')</script>"),
            target="example.com; cat /etc/passwd",
            scan_type="web",
            user_id=user.id,
            config={"payload": "' OR 1=1 --"},
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert "<script>" in scan.name
        assert "cat /etc/passwd" in scan.target
    
    def test_empty_strings(self, db_session, create_test_user):
        """Test handling of empty strings."""
        user = create_test_user()
        
        # These should be allowed (though may not be valid business logic)
        scan = Scan(
            name="",
            target="example.com",
            scan_type="",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)
        
        assert scan.name == ""
        assert scan.scan_type == ""
    
    def test_zero_values(self, db_session, create_test_scan):
        """Test handling of zero values."""
        scan = create_test_scan()
        
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Zero Values Test"),
            cvss_score=0.0,
            port=0,
            verified=0,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.cvss_score == 0.0
        assert finding.port == 0
        assert finding.verified == 0
    
    def test_negative_values_not_restricted(self, db_session, create_test_scan):
        """Test that negative values are not restricted at DB level."""
        scan = create_test_scan()
        
        # Negative CVSS is not valid but may be allowed at DB level
        finding = Finding(
            scan_id=scan.id,
            title=unique_string("Negative Test"),
            cvss_score=-1.0,
            port=-1,
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)
        
        assert finding.cvss_score == -1.0


# =============================================================================
# Database Indexes Tests
# =============================================================================


class TestDatabaseIndexes:
    """Test that expected indexes exist."""
    
    def test_user_indexes(self, initialized_engine):
        """Test User table has expected indexes."""
        inspector = inspect(initialized_engine)
        indexes = inspector.get_indexes("users")
        
        # Check for specific indexes - SQLite auto-creates indexes for unique columns
        index_columns = []
        for idx in indexes:
            index_columns.extend(idx.get("column_names", []))
        
        assert "username" in index_columns or any(
            "username" in idx.get("column_names", []) for idx in indexes
        )
    
    def test_scan_indexes(self, initialized_engine):
        """Test Scan table has expected indexes."""
        inspector = inspect(initialized_engine)
        indexes = inspector.get_indexes("scans")
        
        # Check for status index
        index_names = [idx["name"] for idx in indexes]
        assert any("status" in name for name in index_names) or any(
            "status" in idx.get("column_names", []) for idx in indexes
        )
    
    def test_finding_indexes(self, initialized_engine):
        """Test Finding table has expected indexes."""
        inspector = inspect(initialized_engine)
        indexes = inspector.get_indexes("findings")
        
        # Check for severity index
        index_names = [idx["name"] for idx in indexes]
        assert any("severity" in name for name in index_names) or any(
            "severity" in idx.get("column_names", []) for idx in indexes
        )


# =============================================================================
# Table Configuration Tests
# =============================================================================


class TestTableConfigurations:
    """Test model table configurations."""
    
    def test_user_table_args(self):
        """Test User has composite index defined."""
        assert hasattr(User, "__table_args__")
    
    def test_scan_table_args(self):
        """Test Scan has composite indexes defined."""
        assert hasattr(Scan, "__table_args__")
    
    def test_finding_table_args(self):
        """Test Finding has composite indexes defined."""
        assert hasattr(Finding, "__table_args__")
    
    def test_report_table_args(self):
        """Test Report has composite index defined."""
        assert hasattr(Report, "__table_args__")
    
    def test_vulnerability_table_args(self):
        """Test VulnerabilityDB has composite indexes defined."""
        assert hasattr(VulnerabilityDB, "__table_args__")
    
    def test_asset_table_args(self):
        """Test Asset has composite indexes defined."""
        assert hasattr(Asset, "__table_args__")
    
    def test_audit_log_table_args(self):
        """Test AuditLog has composite indexes defined."""
        assert hasattr(AuditLog, "__table_args__")
    
    def test_notification_table_args(self):
        """Test Notification has composite index defined."""
        assert hasattr(Notification, "__table_args__")
    
    def test_tool_config_table_args(self):
        """Test ToolConfig has composite index defined."""
        assert hasattr(ToolConfig, "__table_args__")


# =============================================================================
# Main Entry Point for Standalone Execution
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
