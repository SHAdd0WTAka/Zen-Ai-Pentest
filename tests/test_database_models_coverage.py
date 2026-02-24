"""
Tests for database/models module - Coverage Boost
"""


class TestUserModel:
    """Test User model"""

    def test_user_creation(self):
        """Test User creation"""
        from database.models import User

        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_pass",
            role="operator",
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "operator"

    def test_user_admin_role(self):
        """Test User with admin role"""
        from database.models import User

        user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="admin_pass",
            role="admin",
        )

        assert user.role == "admin"


class TestScanModel:
    """Test Scan model"""

    def test_scan_creation(self):
        """Test Scan creation"""
        from database.models import Scan

        scan = Scan(
            target="example.com",
            scan_type="quick",
            status="pending",
            user_id=1,
        )

        assert scan.target == "example.com"
        assert scan.scan_type == "quick"
        assert scan.status == "pending"

    def test_scan_status_transitions(self):
        """Test Scan status transitions"""
        from database.models import Scan

        scan = Scan(target="example.com", scan_type="full", user_id=1)

        # Update status
        scan.status = "running"
        assert scan.status == "running"

        scan.status = "completed"
        assert scan.status == "completed"


class TestFindingModel:
    """Test Finding model"""

    def test_finding_creation(self):
        """Test Finding creation"""
        from database.models import Finding

        finding = Finding(
            title="SQL Injection",
            severity="critical",
            description="A SQL injection vulnerability was found",
            scan_id=1,
        )

        assert finding.title == "SQL Injection"
        assert finding.severity == "critical"
        assert finding.description == "A SQL injection vulnerability was found"

    def test_finding_severity_levels(self):
        """Test Finding severity levels"""
        from database.models import Finding

        severities = ["critical", "high", "medium", "low", "info"]

        for sev in severities:
            finding = Finding(title="Test", severity=sev, scan_id=1)
            assert finding.severity == sev


class TestReportModel:
    """Test Report model"""

    def test_report_creation(self):
        """Test Report creation"""
        from database.models import Report

        report = Report(format="pdf", user_id=1, scan_id=1)

        assert report.format == "pdf"
        assert report.format == "pdf"


class TestVulnerabilityDBModel:
    """Test VulnerabilityDB model"""

    def test_vulnerability_creation(self):
        """Test Vulnerability creation"""
        from database.models import VulnerabilityDB

        vuln = VulnerabilityDB(
            cve_id="CVE-2021-1234", title="Test Vulnerability", severity="high"
        )

        assert vuln.cve_id == "CVE-2021-1234"
        assert vuln.title == "Test Vulnerability"
        assert vuln.severity == "high"


class TestAssetModel:
    """Test Asset model"""

    def test_asset_creation(self):
        """Test Asset creation"""
        from database.models import Asset

        asset = Asset(
            name="Web Server",
            asset_type="server",
            ip_address="192.168.1.1",
            hostname="web.example.com",
        )

        assert asset.name == "Web Server"
        assert asset.asset_type == "server"
        assert asset.ip_address == "192.168.1.1"


class TestNotificationModel:
    """Test Notification model"""

    def test_notification_creation(self):
        """Test Notification creation"""
        from database.models import Notification

        notification = Notification(
            title="Scan Complete",
            message="Your scan has completed successfully",
            user_id=1,
            type="scan_complete",
        )

        assert notification.title == "Scan Complete"


class TestAuditLogModel:
    """Test AuditLog model"""

    def test_audit_log_creation(self):
        """Test AuditLog creation"""
        from database.models import AuditLog

        log = AuditLog(
            action="CREATE_SCAN",
            user_id=1,
            details="Created scan for example.com",
        )

        assert log.action == "CREATE_SCAN"
        assert log.details == "Created scan for example.com"


class TestToolConfigModel:
    """Test ToolConfig model"""

    def test_tool_config_creation(self):
        """Test ToolConfig creation"""
        from database.models import ToolConfig

        config = ToolConfig(
            tool_name="nmap", config={"args": "-sV"}, user_id=1
        )

        assert config.tool_name == "nmap"


class TestDatabaseSchema:
    """Test database schema integrity"""

    def test_all_models_importable(self):
        """Test that all models can be imported"""
        from database import models

        # Check that key models exist
        assert hasattr(models, "User")
        assert hasattr(models, "Scan")
        assert hasattr(models, "Finding")
        assert hasattr(models, "Report")
        assert hasattr(models, "VulnerabilityDB")
        assert hasattr(models, "Asset")
        assert hasattr(models, "Notification")
        assert hasattr(models, "AuditLog")
        assert hasattr(models, "ToolConfig")

    def test_model_base_class(self):
        """Test that models use the correct base class"""
        from database.models import Base, Scan, User

        # Check that models inherit from Base
        assert issubclass(User, Base)
        assert issubclass(Scan, Base)


class TestModelRelationships:
    """Test model relationships"""

    def test_user_scans_relationship(self):
        """Test User-Scan relationship attributes"""
        from database.models import Scan, User

        # Check that relationship attributes exist
        assert hasattr(User, "scans")
        assert hasattr(Scan, "user")

    def test_scan_findings_relationship(self):
        """Test Scan-Finding relationship"""
        from database.models import Finding, Scan

        # Check that relationship attributes exist
        assert hasattr(Scan, "findings")
        assert hasattr(Finding, "scan")


class TestModelSerialization:
    """Test model serialization"""

    def test_user_attributes(self):
        """Test User attribute access"""
        from database.models import User

        user = User(
            username="testuser", email="test@example.com", role="admin"
        )

        # Should be able to access attributes
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "admin"

    def test_scan_attributes(self):
        """Test Scan attribute access"""
        from database.models import Scan

        scan = Scan(
            target="192.168.1.1",
            scan_type="network",
            status="completed",
            user_id=1,
        )

        assert scan.target == "192.168.1.1"
        assert scan.scan_type == "network"
        assert scan.status == "completed"


class TestModelTableNames:
    """Test model table names"""

    def test_user_table_name(self):
        """Test User table name"""
        from database.models import User

        assert User.__tablename__ == "users"

    def test_scan_table_name(self):
        """Test Scan table name"""
        from database.models import Scan

        assert Scan.__tablename__ == "scans"

    def test_finding_table_name(self):
        """Test Finding table name"""
        from database.models import Finding

        assert Finding.__tablename__ == "findings"

    def test_vulnerability_db_table_name(self):
        """Test VulnerabilityDB table name"""
        from database.models import VulnerabilityDB

        assert VulnerabilityDB.__tablename__ == "vulnerabilities"
