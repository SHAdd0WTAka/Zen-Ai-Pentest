"""
Tests für Database Models
"""

import pytest
import os
import sys
from datetime import datetime


# Setup path
sys.path.insert(0, "C:\\Users\\Ataka\\source\\repos\\SHAdd0WTAka\\Zen-Ai-Pentest")

os.environ["DATABASE_URL"] = "sqlite:///./test_models.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from database.models import (
    User, Scan, Finding, Report, AuditLog
)


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashedpass123",
            role="user"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
    
    def test_user_repr(self):
        user = User(username="testuser", email="test@example.com")
        repr_str = repr(user)
        assert "testuser" in repr_str


class TestScanModel:
    """Test Scan model"""
    
    def test_scan_creation(self):
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            status="pending",
            user_id=1
        )
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"
        assert scan.status == "pending"
    
    def test_scan_repr(self):
        scan = Scan(name="Test Scan", target="example.com")
        repr_str = repr(scan)
        assert "Test Scan" in repr_str


class TestFindingModel:
    """Test Finding model"""
    
    def test_finding_creation(self):
        finding = Finding(
            scan_id=1,
            title="SQL Injection",
            severity="critical",
            vulnerability_type="sqli",
            description="A SQL injection vulnerability was found"
        )
        assert finding.title == "SQL Injection"
        assert finding.severity == "critical"
        assert finding.vulnerability_type == "sqli"
    
    def test_finding_severity_levels(self):
        severities = ["critical", "high", "medium", "low", "info"]
        for sev in severities:
            finding = Finding(title="Test", severity=sev)
            assert finding.severity == sev


class TestReportModel:
    """Test Report model"""
    
    def test_report_creation(self):
        report = Report(
            scan_id=1,
            format="pdf",
            status="generating",
            file_path="/reports/report_1.pdf"
        )
        assert report.format == "pdf"
        assert report.status == "generating"
    
    def test_report_repr(self):
        report = Report(scan_id=1, format="pdf")
        repr_str = repr(report)
        assert "pdf" in repr_str


class TestAuditLogModel:
    """Test AuditLog model"""
    
    def test_audit_log_creation(self):
        log = AuditLog(
            user_id=1,
            action="login",
            resource="auth",
            details={"ip": "192.168.1.1"}
        )
        assert log.action == "login"
        assert log.resource == "auth"
    
    def test_audit_log_to_dict(self):
        log = AuditLog(
            id=1,
            user_id=1,
            action="login",
            resource="auth",
            details={"ip": "192.168.1.1"},
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            ip_address="192.168.1.1"
        )
        log_dict = log.to_dict()
        assert log_dict["action"] == "login"
        assert log_dict["resource"] == "auth"


class TestScanCRUD:
    """Test Scan model methods"""
    
    def test_scan_status_update(self):
        """Test updating scan status"""
        scan = Scan(
            name="Test Scan",
            target="example.com",
            scan_type="web",
            status="pending",
            user_id=1
        )
        
        # Update status
        scan.status = "running"
        assert scan.status == "running"
        
        scan.status = "completed"
        assert scan.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
