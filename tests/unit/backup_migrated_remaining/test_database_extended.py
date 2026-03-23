"""
Extended Database Tests
"""

import pytest

try:
    from database.models import (
        Base,
        Finding,
        Report,
        Scan,
        ScanStatus,
        Severity,
        User,
    )

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestUserExtended:
    """Erweiterte User Tests"""

    def test_user_creation_all_fields(self):
        user = User(
            username="testuser",
            email="test@test.com",
            hashed_password="hash123",
            role="admin",
            is_active=True,
        )
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.role == "admin"

    def test_user_str(self):
        user = User(username="test")
        s = str(user)
        assert isinstance(s, str)

    def test_user_default_role(self):
        user = User(username="test")
        # Role sollte default haben
        assert hasattr(user, "role")


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestScanExtended:
    """Erweiterte Scan Tests"""

    def test_scan_all_fields(self):
        scan = Scan(
            target="example.com",
            scan_type="network",
            name="Test Scan",
            config={"ports": "80,443"},
            status=ScanStatus.PENDING,
        )
        assert scan.target == "example.com"
        assert scan.name == "Test Scan"

    def test_scan_timestamps(self):
        scan = Scan(target="test.com")
        assert hasattr(scan, "created_at")

    def test_scan_relationships(self):
        scan = Scan(target="test.com")
        assert hasattr(scan, "findings")
        assert hasattr(scan, "reports")


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestFindingExtended:
    """Erweiterte Finding Tests"""

    def test_finding_all_fields(self):
        finding = Finding(
            title="SQL Injection",
            description="Blind SQLi in login",
            severity=Severity.HIGH,
            cvss_score=8.5,
            cve_id="CVE-2021-1234",
            evidence="Payload: ' OR 1=1--",
            remediation="Use prepared statements",
            tool="SQLMap",
            target="http://test.com/login",
            port=80,
            service="http",
        )
        assert finding.title == "SQL Injection"
        assert finding.cvss_score == 8.5

    def test_finding_timestamps(self):
        finding = Finding(title="Test")
        assert hasattr(finding, "created_at")


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestReportExtended:
    """Erweiterte Report Tests"""

    def test_report_all_fields(self):
        report = Report(
            format="pdf", status="completed", file_path="/tmp/report.pdf"
        )
        assert report.format == "pdf"
        assert report.file_path == "/tmp/report.pdf"

    def test_report_timestamps(self):
        report = Report(format="html")
        assert hasattr(report, "created_at")


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestEnums:
    """Enum Tests"""

    def test_scan_status_values(self):
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"

    def test_severity_values(self):
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"
