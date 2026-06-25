"""
Database Model Tests
====================

Comprehensive tests for database layer:
- SQLAlchemy models
- CRUD operations
- Model relationships
- Uses in-memory SQLite for tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.crud import create_finding as crud_create_finding
from database.crud import create_report as crud_create_report
from database.crud import create_scan as crud_create_scan
from database.crud import get_findings as crud_get_findings
from database.crud import get_reports as crud_get_reports
from database.crud import get_scan as crud_get_scan
from database.crud import get_scans as crud_get_scans
from database.crud import update_scan_status as crud_update_scan_status

# Import models
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
)
from database.models import create_audit_log as models_create_audit_log
from database.models import create_finding as models_create_finding
from database.models import create_report as models_create_report
from database.models import create_scan as models_create_scan
from database.models import get_findings as models_get_findings
from database.models import get_reports as models_get_reports
from database.models import get_scan as models_get_scan
from database.models import get_scans as models_get_scans
from database.models import update_scan_status as models_update_scan_status

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# Test User Model
# ============================================================================


class TestUserModel:
    """Test User model"""

    def test_user_creation(self, db_session):
        """Test user model creation"""
        user = User(
            username="testuser",
            email="test@test.com",
            hashed_password="hashed_pass",
            role="operator",
            is_active=1,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.role == "operator"
        assert user.is_active == 1
        assert user.created_at is not None

    def test_user_unique_username(self, db_session):
        """Test username uniqueness constraint"""
        user1 = User(
            username="uniqueuser",
            email="user1@test.com",
            hashed_password="pass1",
        )
        user2 = User(
            username="uniqueuser",
            email="user2@test.com",
            hashed_password="pass2",
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_unique_email(self, db_session):
        """Test email uniqueness constraint"""
        user1 = User(
            username="user1", email="same@test.com", hashed_password="pass1"
        )
        user2 = User(
            username="user2", email="same@test.com", hashed_password="pass2"
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_user_default_role(self, db_session):
        """Test default role is operator"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.role == "operator"

    def test_user_default_active(self, db_session):
        """Test default is_active is 1"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.is_active == 1


# ============================================================================
# Test Scan Model
# ============================================================================


class TestScanModel:
    """Test Scan model"""

    def test_scan_creation(self, db_session):
        """Test scan model creation"""
        # Create user first
        user = User(
            username="scanuser", email="scan@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            status=ScanStatus.PENDING,
            config={"ports": "80,443"},
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()
        db_session.refresh(scan)

        assert scan.id is not None
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"
        assert scan.scan_type == "web"
        assert scan.status == ScanStatus.PENDING
        assert scan.config == {"ports": "80,443"}
        assert scan.user_id == user.id
        assert scan.created_at is not None

    def test_scan_status_transitions(self, db_session):
        """Test scan status transitions"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test",
            target="example.com",
            scan_type="network",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        # Transition to running
        scan.status = ScanStatus.RUNNING
        db_session.commit()
        assert scan.status == ScanStatus.RUNNING

        # Transition to completed
        scan.status = ScanStatus.COMPLETED
        db_session.commit()
        assert scan.status == ScanStatus.COMPLETED

    def test_scan_all_status_values(self, db_session):
        """Test all scan status values"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        statuses = [
            ScanStatus.PENDING,
            ScanStatus.RUNNING,
            ScanStatus.COMPLETED,
            ScanStatus.FAILED,
            ScanStatus.CANCELLED,
        ]

        for i, status in enumerate(statuses):
            scan = Scan(
                name=f"Scan {i}",
                target=f"target{i}.com",
                scan_type="network",
                status=status,
                user_id=user.id,
            )
            db_session.add(scan)

        db_session.commit()

        for i, status in enumerate(statuses):
            scan = (
                db_session.query(Scan).filter(Scan.name == f"Scan {i}").first()
            )
            assert scan.status == status


# ============================================================================
# Test Finding Model
# ============================================================================


class TestFindingModel:
    """Test Finding model"""

    def test_finding_creation(self, db_session):
        """Test finding model creation"""
        # Create user and scan first
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(
            scan_id=scan.id,
            title="SQL Injection",
            description="SQL injection vulnerability found in login form",
            severity=Severity.HIGH,
            cvss_score=8.5,
            cve_id="CVE-2023-12345",
            evidence="Screenshot and HTTP request",
            remediation="Use parameterized queries",
            tool="sqlmap",
            target="http://example.com/login",
            port=80,
            service="http",
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)

        assert finding.id is not None
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH
        assert finding.cvss_score == 8.5
        assert finding.cve_id == "CVE-2023-12345"

    def test_finding_all_severities(self, db_session):
        """Test finding with all severity levels"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        severities = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]

        for i, severity in enumerate(severities):
            finding = Finding(
                scan_id=scan.id,
                title=f"Finding {i}",
                severity=severity,
            )
            db_session.add(finding)

        db_session.commit()

        for i, severity in enumerate(severities):
            finding = (
                db_session.query(Finding)
                .filter(Finding.title == f"Finding {i}")
                .first()
            )
            assert finding.severity == severity

    def test_finding_default_severity(self, db_session):
        """Test default severity is medium"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(scan_id=scan.id, title="Test Finding")
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)

        assert finding.severity == Severity.MEDIUM

    def test_finding_default_verified(self, db_session):
        """Test default verified status is 0"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(scan_id=scan.id, title="Test Finding")
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)

        assert finding.verified == 0


# ============================================================================
# Test Report Model
# ============================================================================


class TestReportModel:
    """Test Report model"""

    def test_report_creation(self, db_session):
        """Test report model creation"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report = Report(
            scan_id=scan.id,
            user_id=user.id,
            format=ReportFormat.PDF,
            template="default",
            status=ReportStatus.PENDING,
            file_path="/reports/report1.pdf",
            file_size=1024,
        )
        db_session.add(report)
        db_session.commit()
        db_session.refresh(report)

        assert report.id is not None
        assert report.format == ReportFormat.PDF
        assert report.status == ReportStatus.PENDING
        assert report.file_path == "/reports/report1.pdf"
        assert report.file_size == 1024

    def test_report_all_formats(self, db_session):
        """Test all report formats"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        formats = [
            ReportFormat.PDF,
            ReportFormat.HTML,
            ReportFormat.JSON,
            ReportFormat.XML,
        ]

        for i, fmt in enumerate(formats):
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=fmt,
                status=ReportStatus.COMPLETED,
            )
            db_session.add(report)

        db_session.commit()

        for i, fmt in enumerate(formats):
            report = (
                db_session.query(Report).filter(Report.format == fmt).first()
            )
            assert report is not None
            assert report.format == fmt

    def test_report_all_statuses(self, db_session):
        """Test all report statuses"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        statuses = [
            ReportStatus.PENDING,
            ReportStatus.GENERATING,
            ReportStatus.COMPLETED,
            ReportStatus.FAILED,
        ]

        for i, status in enumerate(statuses):
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=ReportFormat.PDF,
                status=status,
            )
            db_session.add(report)

        db_session.commit()

        for i, status in enumerate(statuses):
            report = (
                db_session.query(Report)
                .filter(Report.status == status)
                .first()
            )
            assert report is not None
            assert report.status == status


# ============================================================================
# Test Asset Model
# ============================================================================


class TestAssetModel:
    """Test Asset model"""

    def test_asset_creation(self, db_session):
        """Test asset model creation"""
        asset = Asset(
            name="Web Server 01",
            asset_type="server",
            ip_address="192.168.1.10",
            hostname="web01.internal",
            os="Ubuntu 22.04",
            services=[
                {"port": 80, "service": "http"},
                {"port": 443, "service": "https"},
            ],
            owner="IT Team",
            criticality="high",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        assert asset.id is not None
        assert asset.name == "Web Server 01"
        assert asset.asset_type == "server"
        assert asset.ip_address == "192.168.1.10"
        assert asset.hostname == "web01.internal"
        assert asset.os == "Ubuntu 22.04"
        assert asset.criticality == "high"
        assert asset.created_at is not None

    def test_asset_default_criticality(self, db_session):
        """Test default criticality is medium"""
        asset = Asset(name="Test Asset")
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        assert asset.criticality == "medium"


# ============================================================================
# Test VulnerabilityDB Model
# ============================================================================


class TestVulnerabilityDBModel:
    """Test VulnerabilityDB model"""

    def test_vulnerability_creation(self, db_session):
        """Test vulnerability database entry creation"""
        vuln = VulnerabilityDB(
            cve_id="CVE-2023-12345",
            title="Test Vulnerability",
            description="This is a test vulnerability description",
            severity=Severity.HIGH,
            cvss_score=7.5,
            epss_score=0.85,
            affected_products=["Product A v1.0", "Product B v2.0"],
            references=["https://example.com/advisory"],
            exploits=["https://exploit-db.com/12345"],
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)

        assert vuln.id is not None
        assert vuln.cve_id == "CVE-2023-12345"
        assert vuln.cvss_score == 7.5
        assert vuln.epss_score == 0.85
        assert len(vuln.affected_products) == 2

    def test_vulnerability_unique_cve(self, db_session):
        """Test CVE ID uniqueness"""
        vuln1 = VulnerabilityDB(cve_id="CVE-2023-UNIQUE", title="Vuln 1")
        vuln2 = VulnerabilityDB(cve_id="CVE-2023-UNIQUE", title="Vuln 2")

        db_session.add(vuln1)
        db_session.commit()

        db_session.add(vuln2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


# ============================================================================
# Test AuditLog Model
# ============================================================================


class TestAuditLogModel:
    """Test AuditLog model"""

    def test_audit_log_creation(self, db_session):
        """Test audit log entry creation"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        log = AuditLog(
            user_id=user.id,
            action="create_scan",
            resource_type="scan",
            resource_id=1,
            details={"target": "example.com", "type": "web"},
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.action == "create_scan"
        assert log.resource_type == "scan"
        assert log.details == {"target": "example.com", "type": "web"}
        assert log.timestamp is not None

    def test_audit_log_no_user(self, db_session):
        """Test audit log without user (system action)"""
        log = AuditLog(
            action="system_cleanup",
            resource_type="temp_files",
            resource_id=0,
            details={"files_removed": 10},
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.user_id is None


# ============================================================================
# Test Notification Model
# ============================================================================


class TestNotificationModel:
    """Test Notification model"""

    def test_notification_creation(self, db_session):
        """Test notification creation"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        notification = Notification(
            user_id=user.id,
            type="scan_completed",
            title="Scan Completed",
            message="Your scan of example.com has completed successfully.",
            read=0,
        )
        db_session.add(notification)
        db_session.commit()
        db_session.refresh(notification)

        assert notification.id is not None
        assert notification.type == "scan_completed"
        assert notification.title == "Scan Completed"
        assert notification.read == 0
        assert notification.created_at is not None

    def test_notification_default_read(self, db_session):
        """Test default read status is 0 (unread)"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

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


# ============================================================================
# Test ToolConfig Model
# ============================================================================


class TestToolConfigModel:
    """Test ToolConfig model"""

    def test_tool_config_creation(self, db_session):
        """Test tool configuration creation"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        config = ToolConfig(
            user_id=user.id,
            tool_name="nmap",
            config={
                "default_ports": "80,443,8080",
                "timing_template": "T4",
                "scripts": "default,vuln",
            },
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.id is not None
        assert config.tool_name == "nmap"
        assert config.config["timing_template"] == "T4"


# ============================================================================
# Test Model Relationships
# ============================================================================


class TestModelRelationships:
    """Test model relationships"""

    def test_user_scans_relationship(self, db_session):
        """Test User-Scan relationship"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan1 = Scan(
            name="Scan 1",
            target="target1.com",
            scan_type="web",
            user_id=user.id,
        )
        scan2 = Scan(
            name="Scan 2",
            target="target2.com",
            scan_type="network",
            user_id=user.id,
        )
        db_session.add_all([scan1, scan2])
        db_session.commit()

        # Refresh user to load relationship
        db_session.refresh(user)

        assert len(user.scans) == 2
        assert user.scans[0].name in ["Scan 1", "Scan 2"]

    def test_scan_findings_relationship(self, db_session):
        """Test Scan-Finding relationship"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding1 = Finding(
            scan_id=scan.id, title="Finding 1", severity=Severity.HIGH
        )
        finding2 = Finding(
            scan_id=scan.id, title="Finding 2", severity=Severity.MEDIUM
        )
        db_session.add_all([finding1, finding2])
        db_session.commit()

        # Refresh scan to load relationship
        db_session.refresh(scan)

        assert len(scan.findings) == 2

    def test_scan_reports_relationship(self, db_session):
        """Test Scan-Report relationship"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report = Report(
            scan_id=scan.id,
            user_id=user.id,
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
        )
        db_session.add(report)
        db_session.commit()

        # Refresh scan to load relationship
        db_session.refresh(scan)

        assert len(scan.reports) == 1

    def test_user_reports_relationship(self, db_session):
        """Test User-Report relationship"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report = Report(
            scan_id=scan.id,
            user_id=user.id,
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
        )
        db_session.add(report)
        db_session.commit()

        # Refresh user to load relationship
        db_session.refresh(user)

        assert len(user.reports) == 1

    def test_finding_scan_relationship(self, db_session):
        """Test Finding-Scan back-reference"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(
            scan_id=scan.id, title="Test Finding", severity=Severity.HIGH
        )
        db_session.add(finding)
        db_session.commit()
        db_session.refresh(finding)

        # Access scan through relationship
        assert finding.scan.id == scan.id
        assert finding.scan.name == "Test Scan"


# ============================================================================
# Test Model CRUD Operations (from models.py)
# ============================================================================


class TestModelsCRUD:
    """Test CRUD operations defined in models.py"""

    def test_create_scan(self, db_session):
        """Test create_scan function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = models_create_scan(
            db_session,
            name="Test Scan",
            target="example.com",
            scan_type="web",
            config={"ports": "80,443"},
            user_id=user.id,
        )

        assert scan.id is not None
        assert scan.name == "Test Scan"

    def test_get_scan(self, db_session):
        """Test get_scan function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        retrieved = models_get_scan(db_session, scan.id)

        assert retrieved is not None
        assert retrieved.id == scan.id
        assert retrieved.name == "Test Scan"

    def test_get_scan_not_found(self, db_session):
        """Test get_scan returns None for non-existent scan"""
        retrieved = models_get_scan(db_session, 99999)

        assert retrieved is None

    def test_get_scans(self, db_session):
        """Test get_scans function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        for i in range(5):
            scan = Scan(
                name=f"Scan {i}",
                target=f"target{i}.com",
                scan_type="web",
                user_id=user.id,
            )
            db_session.add(scan)
        db_session.commit()

        scans = models_get_scans(db_session, skip=0, limit=3)

        assert len(scans) == 3

    def test_get_scans_by_status(self, db_session):
        """Test get_scans with status filter"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan1 = Scan(
            name="Scan 1",
            target="target1.com",
            scan_type="web",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        scan2 = Scan(
            name="Scan 2",
            target="target2.com",
            scan_type="web",
            status=ScanStatus.PENDING,
            user_id=user.id,
        )
        db_session.add_all([scan1, scan2])
        db_session.commit()

        completed_scans = models_get_scans(
            db_session, status=ScanStatus.COMPLETED
        )

        assert len(completed_scans) == 1
        assert completed_scans[0].name == "Scan 1"

    def test_update_scan_status(self, db_session):
        """Test update_scan_status function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            status=ScanStatus.PENDING,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        updated = models_update_scan_status(
            db_session, scan.id, ScanStatus.RUNNING
        )

        assert updated.status == ScanStatus.RUNNING
        assert updated.started_at is not None

    def test_create_finding(self, db_session):
        """Test create_finding function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = models_create_finding(
            db_session,
            scan_id=scan.id,
            title="SQL Injection",
            description="SQLi found",
            severity=Severity.HIGH,
            cvss_score=8.5,
        )

        assert finding.id is not None
        assert finding.title == "SQL Injection"

    def test_get_findings(self, db_session):
        """Test get_findings function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding1 = Finding(
            scan_id=scan.id, title="Finding 1", severity=Severity.HIGH
        )
        finding2 = Finding(
            scan_id=scan.id, title="Finding 2", severity=Severity.LOW
        )
        db_session.add_all([finding1, finding2])
        db_session.commit()

        findings = models_get_findings(db_session, scan_id=scan.id)

        assert len(findings) == 2

    def test_get_findings_by_severity(self, db_session):
        """Test get_findings with severity filter"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding1 = Finding(
            scan_id=scan.id, title="Finding 1", severity=Severity.HIGH
        )
        finding2 = Finding(
            scan_id=scan.id, title="Finding 2", severity=Severity.LOW
        )
        db_session.add_all([finding1, finding2])
        db_session.commit()

        high_findings = models_get_findings(
            db_session, scan_id=scan.id, severity=Severity.HIGH
        )

        assert len(high_findings) == 1
        assert high_findings[0].severity == Severity.HIGH

    def test_create_report(self, db_session):
        """Test create_report function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report = models_create_report(
            db_session,
            scan_id=scan.id,
            format=ReportFormat.PDF,
            template="default",
            user_id=user.id,
        )

        assert report.id is not None
        assert report.status == ReportStatus.PENDING

    def test_get_reports(self, db_session):
        """Test get_reports function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        for i in range(3):
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
            )
            db_session.add(report)
        db_session.commit()

        reports = models_get_reports(db_session, skip=0, limit=2)

        assert len(reports) == 2

    def test_create_audit_log(self, db_session):
        """Test create_audit_log function"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        # Should not raise exception
        models_create_audit_log(
            db_session,
            user_id=user.id,
            action="test_action",
            resource_type="test",
            resource_id=1,
            details={"key": "value"},
        )

        # Verify log was created
        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "test_action")
            .first()
        )
        assert log is not None
        assert log.details == {"key": "value"}


# ============================================================================
# Test CRUD Operations (from crud.py)
# ============================================================================


class TestCRUDOperations:
    """Test CRUD operations from crud.py"""

    def test_crud_create_scan_with_object(self, db_session):
        """Test create_scan with scan_data object"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan_data = MockNameTarget(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            config={},
            user_id=user.id,
        )
        scan = crud_create_scan(db_session, scan_data=scan_data)

        assert scan.name == "Test Scan"
        assert scan.user_id == user.id

    def test_crud_create_scan_with_kwargs(self, db_session):
        """Test create_scan with kwargs"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = crud_create_scan(
            db_session,
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )

        assert scan.name == "Test Scan"
        assert scan.target == "example.com"

    def test_crud_get_scan(self, db_session):
        """Test crud get_scan"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        retrieved = crud_get_scan(db_session, scan.id)

        assert retrieved is not None
        assert retrieved.id == scan.id

    def test_crud_get_scans(self, db_session):
        """Test crud get_scans"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        for i in range(3):
            scan = Scan(
                name=f"Scan {i}",
                target=f"target{i}.com",
                scan_type="web",
                user_id=user.id,
            )
            db_session.add(scan)
        db_session.commit()

        scans = crud_get_scans(db_session, skip=0, limit=10)

        assert len(scans) == 3

    def test_crud_update_scan_status(self, db_session):
        """Test crud update_scan_status"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            status=ScanStatus.PENDING,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        updated = crud_update_scan_status(
            db_session, scan.id, ScanStatus.RUNNING
        )

        assert updated is not None
        assert updated.status == ScanStatus.RUNNING
        assert updated.started_at is not None

    def test_crud_update_scan_status_to_completed(self, db_session):
        """Test crud update_scan_status to completed"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            status=ScanStatus.RUNNING,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        updated = crud_update_scan_status(
            db_session, scan.id, ScanStatus.COMPLETED, result={"findings": 5}
        )

        assert updated.status == ScanStatus.COMPLETED
        assert updated.completed_at is not None

    def test_crud_create_finding(self, db_session):
        """Test crud create_finding"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding_data = MockFindingData(
            scan_id=scan.id,
            title="SQL Injection",
            description="SQLi found",
            severity=Severity.HIGH,
        )

        finding = crud_create_finding(db_session, finding_data=finding_data)

        assert finding is not None
        assert finding.title == "SQL Injection"
        assert finding.scan_id == scan.id

    def test_crud_get_findings(self, db_session):
        """Test crud get_findings"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(
            scan_id=scan.id, title="Test Finding", severity=Severity.HIGH
        )
        db_session.add(finding)
        db_session.commit()

        findings = crud_get_findings(db_session, scan_id=scan.id)

        assert len(findings) == 1
        assert findings[0].title == "Test Finding"

    def test_crud_get_findings_no_filter(self, db_session):
        """Test crud get_findings without scan filter"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        for i in range(3):
            finding = Finding(
                scan_id=scan.id, title=f"Finding {i}", severity=Severity.HIGH
            )
            db_session.add(finding)
        db_session.commit()

        findings = crud_get_findings(db_session)

        assert len(findings) == 3

    def test_crud_create_report(self, db_session):
        """Test crud create_report"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report_data = MockReportData(
            scan_id=scan.id, user_id=user.id, format=ReportFormat.PDF
        )

        report = crud_create_report(db_session, report_data=report_data)

        assert report is not None
        assert report.scan_id == scan.id
        assert report.status == "pending"

    def test_crud_get_reports(self, db_session):
        """Test crud get_reports"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        for i in range(3):
            report = Report(
                scan_id=scan.id,
                user_id=user.id,
                format=ReportFormat.PDF,
                status=ReportStatus.COMPLETED,
            )
            db_session.add(report)
        db_session.commit()

        reports = crud_get_reports(db_session, skip=0, limit=10)

        assert len(reports) == 3

    def test_crud_create_audit_log(self, db_session):
        """Test models create_audit_log"""
        user = User(
            username="testuser", email="test@test.com", hashed_password="pass"
        )
        db_session.add(user)
        db_session.commit()

        # Should not raise exception - use models function
        models_create_audit_log(
            db_session,
            user_id=user.id,
            action="test_action",
            resource_type="scan",
            resource_id=1,
            details={"test": "data"},
        )

        log = (
            db_session.query(AuditLog)
            .filter(AuditLog.action == "test_action")
            .first()
        )
        assert log is not None


# Helper classes for mocking objects with attributes
class MockNameTarget:
    """Mock object with name, target attributes"""

    def __init__(
        self, name, target, scan_type=None, config=None, user_id=None
    ):
        self.name = name
        self.target = target
        self.scan_type = scan_type
        self.config = config
        self.user_id = user_id


class MockFindingData:
    """Mock finding data object"""

    def __init__(
        self,
        scan_id,
        title,
        description=None,
        severity=None,
        cvss_score=None,
        cve_id=None,
        evidence=None,
        remediation=None,
        tool=None,
    ):
        self.scan_id = scan_id
        self.title = title
        self.description = description
        self.severity = severity
        self.cvss_score = cvss_score
        self.cve_id = cve_id
        self.evidence = evidence
        self.remediation = remediation
        self.tool = tool


class MockReportData:
    """Mock report data object"""

    def __init__(self, scan_id, user_id=None, format=None):
        self.scan_id = scan_id
        self.user_id = user_id
        self.format = format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
