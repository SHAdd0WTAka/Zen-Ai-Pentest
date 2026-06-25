"""
REAL tests for Database Models - No Mocks
Tests actual model creation and validation logic
"""

from datetime import datetime

import pytest

from database.models import (
    Asset,
    Finding,
    Report,
    ReportFormat,
    ReportStatus,
    Scan,
    ScanStatus,
    Severity,
    User,
)


class TestScanStatus:
    """Real tests for ScanStatus enum"""

    def test_scan_status_values(self):
        """Should have correct status values"""
        assert ScanStatus.PENDING.value == "pending"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"
        assert ScanStatus.CANCELLED.value == "cancelled"


class TestSeverity:
    """Real tests for Severity enum"""

    def test_severity_values(self):
        """Should have correct severity values"""
        assert Severity.INFO.value == "info"
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"


class TestReportFormat:
    """Real tests for ReportFormat enum"""

    def test_report_format_values(self):
        """Should have correct format values"""
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.XML.value == "xml"


class TestReportStatus:
    """Real tests for ReportStatus enum"""

    def test_report_status_values(self):
        """Should have correct status values"""
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.GENERATING.value == "generating"
        assert ReportStatus.COMPLETED.value == "completed"
        assert ReportStatus.FAILED.value == "failed"


class TestUserModel:
    """Real tests for User model"""

    def test_user_creation(self):
        """Should create user with attributes"""
        user = User(
            id=1, username="testuser", email="test@example.com", hashed_password="hashed_pass", is_active=1, role="admin"
        )

        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_pass"
        assert user.is_active == 1
        assert user.role == "admin"

    def test_user_creation_minimal(self):
        """Should create user with minimal fields"""
        user = User(username="newuser", email="new@example.com", hashed_password="pass")

        # User object created successfully
        assert user.username == "newuser"
        assert user.email == "new@example.com"


class TestScanModel:
    """Real tests for Scan model"""

    def test_scan_creation(self):
        """Should create scan with attributes"""
        scan = Scan(
            id=1, name="Network Scan", target="192.168.1.0/24", scan_type="network", status=ScanStatus.PENDING.value, user_id=1
        )

        assert scan.id == 1
        assert scan.name == "Network Scan"
        assert scan.target == "192.168.1.0/24"
        assert scan.scan_type == "network"
        assert scan.status == ScanStatus.PENDING.value
        assert scan.user_id == 1

    def test_scan_status_transition(self):
        """Should allow status transitions"""
        scan = Scan(name="Test Scan", target="example.com", scan_type="web", status=ScanStatus.PENDING.value)

        assert scan.status == ScanStatus.PENDING.value

        scan.status = ScanStatus.RUNNING.value
        assert scan.status == ScanStatus.RUNNING.value

        scan.status = ScanStatus.COMPLETED.value
        assert scan.status == ScanStatus.COMPLETED.value

    def test_scan_config(self):
        """Should handle scan configuration"""
        config = {"ports": "80,443", "threads": 10}

        scan = Scan(name="Config Scan", target="example.com", scan_type="web", config=config)

        assert scan.config == config


class TestFindingModel:
    """Real tests for Finding model"""

    def test_finding_creation(self):
        """Should create finding with attributes"""
        finding = Finding(
            id=1,
            title="SQL Injection",
            description="SQLi vulnerability found",
            severity=Severity.CRITICAL.value,
            target="example.com",
            scan_id=1,
        )

        assert finding.id == 1
        assert finding.title == "SQL Injection"
        assert finding.description == "SQLi vulnerability found"
        assert finding.severity == Severity.CRITICAL.value
        assert finding.target == "example.com"
        assert finding.scan_id == 1

    def test_finding_with_cve(self):
        """Should handle CVE references"""
        finding = Finding(
            title="RCE Vulnerability",
            description="Remote code execution",
            severity=Severity.CRITICAL.value,
            target="example.com",
            cve_id="CVE-2024-1234",
        )

        assert finding.cve_id == "CVE-2024-1234"

    def test_finding_with_cvss(self):
        """Should handle CVSS scores"""
        finding = Finding(
            title="High Severity", description="Test", severity=Severity.HIGH.value, target="example.com", cvss_score=8.5
        )

        assert finding.cvss_score == 8.5


class TestReportModel:
    """Real tests for Report model"""

    def test_report_creation(self):
        """Should create report with attributes"""
        report = Report(id=1, format=ReportFormat.PDF.value, status=ReportStatus.PENDING.value, scan_id=1, user_id=1)

        assert report.id == 1
        assert report.format == ReportFormat.PDF.value
        assert report.status == ReportStatus.PENDING.value

    def test_report_format_variants(self):
        """Should handle all report formats"""
        formats = [ReportFormat.PDF, ReportFormat.HTML, ReportFormat.JSON, ReportFormat.XML]

        for i, fmt in enumerate(formats):
            report = Report(id=i, format=fmt.value, scan_id=1)
            assert report.format == fmt.value


class TestAssetModel:
    """Real tests for Asset model"""

    def test_asset_creation(self):
        """Should create asset with attributes"""
        asset = Asset(id=1, name="Web Server", asset_type="host", ip_address="192.168.1.1")

        assert asset.id == 1
        assert asset.name == "Web Server"
        assert asset.asset_type == "host"
        assert asset.ip_address == "192.168.1.1"

    def test_asset_services(self):
        """Should handle asset services"""
        services = [{"port": 80, "service": "http"}]

        asset = Asset(name="Service Asset", asset_type="host", ip_address="192.168.1.1", services=services)

        assert asset.services == services
