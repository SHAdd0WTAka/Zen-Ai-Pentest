"""
Comprehensive Tests for Database Models
"""

import datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import (
    Base,
    Finding,
    Report,
    ReportFormat,
    ReportStatus,
    Scan,
    ScanStatus,
    Severity,
    Target,
    User,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ============================================================================
# ENUM TESTS
# ============================================================================


class TestScanStatus:
    """Tests for ScanStatus enum"""

    def test_enum_values(self):
        """Test all scan status values"""
        assert ScanStatus.PENDING.value == "pending"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"
        assert ScanStatus.CANCELLED.value == "cancelled"

    def test_enum_comparison(self):
        """Test enum comparison"""
        assert ScanStatus.PENDING == ScanStatus.PENDING
        assert ScanStatus.COMPLETED != ScanStatus.FAILED


class TestSeverity:
    """Tests for Severity enum"""

    def test_severity_values(self):
        """Test all severity values"""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_severity_ordering(self):
        """Test severity ordering (conceptual)"""
        severities = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]
        assert len(severities) == 5


class TestReportFormat:
    """Tests for ReportFormat enum"""

    def test_format_values(self):
        """Test all report format values"""
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.XML.value == "xml"


class TestReportStatus:
    """Tests for ReportStatus enum"""

    def test_status_values(self):
        """Test all report status values"""
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.GENERATING.value == "generating"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"


# ============================================================================
# USER MODEL TESTS
# ============================================================================


class TestUserModel:
    """Tests for User model"""

    def test_user_creation(self, db_session):
        """Test creating a user"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            role="admin",
            is_active=1,
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "admin"
        assert user.is_active == 1
        assert user.created_at is not None

    def test_user_defaults(self, db_session):
        """Test user default values"""
        user = User(
            username="defaultuser",
            email="default@example.com",
            hashed_password="password",
        )
        db_session.add(user)
        db_session.commit()

        assert user.role == "operator"  # Default role
        assert user.is_active == 1  # Default active
        assert user.created_at is not None

    def test_user_unique_username(self, db_session):
        """Test that username must be unique"""
        user1 = User(
            username="uniqueuser",
            email="user1@example.com",
            hashed_password="pass1",
        )
        db_session.add(user1)
        db_session.commit()

        # Creating user with same username should fail
        user2 = User(
            username="uniqueuser",  # Same username
            email="user2@example.com",
            hashed_password="pass2",
        )
        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
        db_session.rollback()

    def test_user_unique_email(self, db_session):
        """Test that email must be unique"""
        user1 = User(
            username="user1",
            email="same@example.com",
            hashed_password="pass1",
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            username="user2",
            email="same@example.com",  # Same email
            hashed_password="pass2",
        )
        db_session.add(user2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_user_scans_relationship(self, db_session):
        """Test user-scans relationship"""
        user = User(
            username="scanuser",
            email="scan@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        # Initially no scans
        assert user.scans.count() == 0


# ============================================================================
# SCAN MODEL TESTS
# ============================================================================


class TestScanModel:
    """Tests for Scan model"""

    def test_scan_creation(self, db_session):
        """Test creating a scan"""
        user = User(
            username="scanuser",
            email="scanuser@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="192.168.1.1",
            scan_type="nmap",
            status=ScanStatus.PENDING,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        assert scan.id is not None
        assert scan.target == "192.168.1.1"
        assert scan.scan_type == "nmap"
        assert scan.status == ScanStatus.PENDING
        assert scan.user_id == user.id
        assert scan.created_at is not None

    def test_scan_status_transitions(self, db_session):
        """Test scan status transitions"""
        user = User(
            username="statususer",
            email="status@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="10.0.0.1",
            scan_type="nuclei",
            status=ScanStatus.PENDING,
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
        scan.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db_session.commit()
        assert scan.status == ScanStatus.COMPLETED
        assert scan.completed_at is not None

    def test_scan_findings_relationship(self, db_session):
        """Test scan-findings relationship"""
        user = User(
            username="findinguser",
            email="findings@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="example.com",
            scan_type="sqlmap",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        # Initially no findings
        assert scan.findings.count() == 0


# ============================================================================
# FINDING MODEL TESTS
# ============================================================================


class TestFindingModel:
    """Tests for Finding model"""

    def test_finding_creation(self, db_session):
        """Test creating a finding"""
        user = User(
            username="findingcreator",
            email="creator@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="test.com",
            scan_type="nmap",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(
            title="SQL Injection",
            description="SQLi found in login form",
            severity=Severity.HIGH,
            target="test.com",
            scan_id=scan.id,
            user_id=user.id,
            cvss_score=7.5,
            cve_id="CVE-2023-1234",
        )
        db_session.add(finding)
        db_session.commit()

        assert finding.id is not None
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH
        assert finding.cvss_score == 7.5
        assert finding.cve_id == "CVE-2023-1234"
        assert finding.created_at is not None

    def test_finding_all_severities(self, db_session):
        """Test findings with all severity levels"""
        user = User(
            username="sevuser",
            email="sev@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="vuln.com",
            scan_type="nuclei",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        for sev in [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]:
            finding = Finding(
                title=f"{sev.value} Finding",
                description=f"Test {sev.value} finding",
                severity=sev,
                target="vuln.com",
                scan_id=scan.id,
                user_id=user.id,
            )
            db_session.add(finding)

        db_session.commit()

        findings = db_session.query(Finding).all()
        assert len(findings) == 5

    def test_finding_with_evidence(self, db_session):
        """Test finding with evidence data"""
        user = User(
            username="evuser",
            email="ev@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="evidence.com",
            scan_type="sqlmap",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        evidence_data = {
            "request": "POST /login HTTP/1.1",
            "response": "SQL error: You have an error",
            "payload": "' OR 1=1 --",
        }

        finding = Finding(
            title="SQL Injection Evidence",
            description="SQLi with evidence",
            severity=Severity.CRITICAL,
            target="evidence.com",
            scan_id=scan.id,
            user_id=user.id,
            evidence=evidence_data,
        )
        db_session.add(finding)
        db_session.commit()

        assert finding.evidence == evidence_data
        assert finding.evidence["payload"] == "' OR 1=1 --"

    def test_finding_remediation(self, db_session):
        """Test finding with remediation info"""
        user = User(
            username="remuser",
            email="rem@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="remediate.com",
            scan_type="nuclei",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(
            title="XSS Vulnerability",
            description="Stored XSS found",
            severity=Severity.HIGH,
            target="remediate.com",
            scan_id=scan.id,
            user_id=user.id,
            remediation="Use output encoding and CSP headers",
            references=["https://owasp.org/www-community/attacks/xss/"],
        )
        db_session.add(finding)
        db_session.commit()

        assert finding.remediation == "Use output encoding and CSP headers"
        assert len(finding.references) == 1


# ============================================================================
# TARGET MODEL TESTS
# ============================================================================


class TestTargetModel:
    """Tests for Target model"""

    def test_target_creation(self, db_session):
        """Test creating a target"""
        user = User(
            username="targetuser",
            email="target@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        target = Target(
            name="Production Server",
            host="prod.example.com",
            description="Main production server",
            user_id=user.id,
            is_active=True,
        )
        db_session.add(target)
        db_session.commit()

        assert target.id is not None
        assert target.name == "Production Server"
        assert target.host == "prod.example.com"
        assert target.is_active is True

    def test_target_types(self, db_session):
        """Test different target types"""
        user = User(
            username="targettypes",
            email="types@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        targets = [
            Target(
                name="IP Target",
                host="192.168.1.1",
                target_type="ip",
                user_id=user.id,
            ),
            Target(
                name="Domain Target",
                host="example.com",
                target_type="domain",
                user_id=user.id,
            ),
            Target(
                name="CIDR Target",
                host="10.0.0.0/24",
                target_type="cidr",
                user_id=user.id,
            ),
        ]

        for target in targets:
            db_session.add(target)

        db_session.commit()

        all_targets = db_session.query(Target).all()
        assert len(all_targets) == 3

    def test_target_scans_relationship(self, db_session):
        """Test target-scans relationship"""
        user = User(
            username="targetscans",
            email="tscans@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        target = Target(
            name="Scan Target",
            host="scanme.example.com",
            user_id=user.id,
        )
        db_session.add(target)
        db_session.commit()

        # Initially no scans
        assert target.scans.count() == 0


# ============================================================================
# REPORT MODEL TESTS
# ============================================================================


class TestReportModel:
    """Tests for Report model"""

    def test_report_creation(self, db_session):
        """Test creating a report"""
        user = User(
            username="reportuser",
            email="report@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="report-test.com",
            scan_type="all",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report = Report(
            name="Security Assessment Report",
            description="Comprehensive security assessment",
            format=ReportFormat.PDF,
            status=ReportStatus.PENDING,
            scan_id=scan.id,
            user_id=user.id,
        )
        db_session.add(report)
        db_session.commit()

        assert report.id is not None
        assert report.name == "Security Assessment Report"
        assert report.format == ReportFormat.PDF
        assert report.status == ReportStatus.PENDING

    def test_report_all_formats(self, db_session):
        """Test reports in all formats"""
        user = User(
            username="formatuser",
            email="formats@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="formats.com",
            scan_type="nmap",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        for fmt in [
            ReportFormat.PDF,
            ReportFormat.HTML,
            ReportFormat.JSON,
            ReportFormat.XML,
        ]:
            report = Report(
                name=f"{fmt.value.upper()} Report",
                format=fmt,
                status=ReportStatus.COMPLETED,
                file_path=f"/reports/report.{fmt.value}",
                scan_id=scan.id,
                user_id=user.id,
            )
            db_session.add(report)

        db_session.commit()

        reports = db_session.query(Report).all()
        assert len(reports) == 4

    def test_report_status_transitions(self, db_session):
        """Test report status transitions"""
        user = User(
            username="repstatus",
            email="repstatus@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="status.com",
            scan_type="nuclei",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        report = Report(
            name="Status Report",
            format=ReportFormat.PDF,
            status=ReportStatus.PENDING,
            scan_id=scan.id,
            user_id=user.id,
        )
        db_session.add(report)
        db_session.commit()

        # Transition to generating
        report.status = ReportStatus.GENERATING
        db_session.commit()
        assert report.status == ReportStatus.GENERATING

        # Transition to completed
        report.status = ReportStatus.COMPLETED
        report.file_path = "/reports/final.pdf"
        report.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db_session.commit()
        assert report.status == ReportStatus.COMPLETED
        assert report.file_path == "/reports/final.pdf"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestModelIntegration:
    """Integration tests across multiple models"""

    def test_full_workflow(self, db_session):
        """Test a complete workflow with all models"""
        # Create user
        user = User(
            username="workflowuser",
            email="workflow@example.com",
            hashed_password="secure_password",
            role="admin",
        )
        db_session.add(user)
        db_session.commit()

        # Create target
        target = Target(
            name="Corporate Network",
            host="10.0.0.0/24",
            target_type="cidr",
            description="Internal corporate network",
            user_id=user.id,
        )
        db_session.add(target)
        db_session.commit()

        # Create scan
        scan = Scan(
            target="10.0.0.0/24",
            scan_type="nmap",
            status=ScanStatus.RUNNING,
            user_id=user.id,
            target_id=target.id,
        )
        db_session.add(scan)
        db_session.commit()

        # Add findings
        findings = [
            Finding(
                title="Open SSH Port",
                description="SSH service running on port 22",
                severity=Severity.INFO,
                target="10.0.0.5",
                scan_id=scan.id,
                user_id=user.id,
            ),
            Finding(
                title="Outdated Apache Version",
                description="Apache 2.4.29 has known vulnerabilities",
                severity=Severity.HIGH,
                target="10.0.0.10",
                scan_id=scan.id,
                user_id=user.id,
                cve_id="CVE-2021-44790",
                cvss_score=8.0,
            ),
        ]
        for finding in findings:
            db_session.add(finding)
        db_session.commit()

        # Complete scan
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db_session.commit()

        # Generate report
        report = Report(
            name="Corporate Network Security Scan",
            description="Security assessment of corporate network",
            format=ReportFormat.PDF,
            status=ReportStatus.COMPLETED,
            file_path="/reports/corporate_scan.pdf",
            scan_id=scan.id,
            user_id=user.id,
        )
        db_session.add(report)
        db_session.commit()

        # Verify relationships
        assert user.scans.count() == 1
        assert scan.findings.count() == 2
        assert target.scans.count() == 1

        # Verify finding counts by severity
        high_findings = db_session.query(Finding).filter_by(severity=Severity.HIGH).count()
        info_findings = db_session.query(Finding).filter_by(severity=Severity.INFO).count()
        assert high_findings == 1
        assert info_findings == 1

    def test_cascade_delete_scan_findings(self, db_session):
        """Test that deleting a scan cascades to findings"""
        user = User(
            username="cascadeuser",
            email="cascade@example.com",
            hashed_password="pass",
        )
        db_session.add(user)
        db_session.commit()

        scan = Scan(
            target="cascade.com",
            scan_type="nuclei",
            status=ScanStatus.COMPLETED,
            user_id=user.id,
        )
        db_session.add(scan)
        db_session.commit()

        finding = Finding(
            title="Test Finding",
            description="Will be deleted with scan",
            severity=Severity.MEDIUM,
            target="cascade.com",
            scan_id=scan.id,
            user_id=user.id,
        )
        db_session.add(finding)
        db_session.commit()

        # Verify finding exists
        assert db_session.query(Finding).count() == 1

        # Delete scan
        db_session.delete(scan)
        db_session.commit()

        # Finding should also be deleted (if cascade is configured)
        # This depends on the actual cascade configuration in the model
