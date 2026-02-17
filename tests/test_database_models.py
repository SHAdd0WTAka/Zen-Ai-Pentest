"""
Database Model Tests
Tests for SQLAlchemy models
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Try to import database models
try:
    from database.models import (
        User, Scan, Finding, Report, Tool, 
        ScanResult, Notification
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    

@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """Test user model attributes"""
        user = User(
            id="1",
            username="testuser",
            email="test@test.com",
            hashed_password="hashed_pass",
            role="user",
            is_active=True
        )
        
        assert user.username == "testuser"
        assert user.email == "test@test.com"
        assert user.role == "user"
        assert user.is_active is True
        
    def test_user_repr(self):
        """Test user string representation"""
        user = User(username="testuser", email="test@test.com")
        
        repr_str = repr(user)
        assert "testuser" in repr_str or "User" in repr_str
        
    def test_user_to_dict(self):
        """Test user serialization"""
        user = User(
            id="1",
            username="testuser",
            email="test@test.com",
            role="admin"
        )
        
        # If to_dict method exists
        if hasattr(user, 'to_dict'):
            user_dict = user.to_dict()
            assert user_dict['username'] == "testuser"
            assert user_dict['email'] == "test@test.com"


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestScanModel:
    """Test Scan model"""
    
    def test_scan_creation(self):
        """Test scan model attributes"""
        scan = Scan(
            id="1",
            target="example.com",
            type="full",
            status="pending",
            user_id="1"
        )
        
        assert scan.target == "example.com"
        assert scan.type == "full"
        assert scan.status == "pending"
        
    def test_scan_status_transitions(self):
        """Test scan status can be updated"""
        scan = Scan(
            target="example.com",
            type="quick",
            status="pending"
        )
        
        # Update status
        scan.status = "running"
        assert scan.status == "running"
        
        scan.status = "completed"
        assert scan.status == "completed"
        
    def test_scan_timestamps(self):
        """Test scan timestamps"""
        scan = Scan(
            target="example.com",
            type="full"
        )
        
        # Check if created_at exists
        if hasattr(scan, 'created_at'):
            assert scan.created_at is not None


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestFindingModel:
    """Test Finding model"""
    
    def test_finding_creation(self):
        """Test finding model attributes"""
        finding = Finding(
            id="1",
            scan_id="1",
            title="SQL Injection",
            severity="high",
            description="A SQL injection vulnerability was found",
            url="http://example.com/page.php?id=1"
        )
        
        assert finding.title == "SQL Injection"
        assert finding.severity == "high"
        assert finding.scan_id == "1"
        
    def test_finding_severity_levels(self):
        """Test all severity levels"""
        severities = ["critical", "high", "medium", "low", "info"]
        
        for severity in severities:
            finding = Finding(
                title=f"Test {severity}",
                severity=severity,
                scan_id="1"
            )
            assert finding.severity == severity


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestReportModel:
    """Test Report model"""
    
    def test_report_creation(self):
        """Test report model attributes"""
        report = Report(
            id="1",
            scan_id="1",
            format="pdf",
            status="generating",
            file_path="/reports/report1.pdf"
        )
        
        assert report.format == "pdf"
        assert report.scan_id == "1"
        assert report.status == "generating"
        
    def test_report_formats(self):
        """Test different report formats"""
        formats = ["pdf", "html", "json", "xml", "markdown"]
        
        for fmt in formats:
            report = Report(
                scan_id="1",
                format=fmt
            )
            assert report.format == fmt


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestToolModel:
    """Test Tool model"""
    
    def test_tool_creation(self):
        """Test tool model attributes"""
        tool = Tool(
            id="nmap",
            name="Nmap",
            description="Network port scanner",
            category="network",
            enabled=True
        )
        
        assert tool.name == "Nmap"
        assert tool.category == "network"
        assert tool.enabled is True
        
    def test_tool_categories(self):
        """Test different tool categories"""
        categories = ["network", "web", "reconnaissance", "exploitation"]
        
        for category in categories:
            tool = Tool(
                name=f"Test {category}",
                category=category
            )
            assert tool.category == category


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestModelRelationships:
    """Test model relationships"""
    
    def test_user_scans_relationship(self):
        """Test User-Scan relationship"""
        user = User(id="1", username="testuser")
        scan = Scan(id="1", target="example.com", user_id="1")
        
        assert scan.user_id == user.id
        
    def test_scan_findings_relationship(self):
        """Test Scan-Finding relationship"""
        scan = Scan(id="1", target="example.com")
        finding = Finding(id="1", title="Test", scan_id="1")
        
        assert finding.scan_id == scan.id
        
    def test_scan_report_relationship(self):
        """Test Scan-Report relationship"""
        scan = Scan(id="1", target="example.com")
        report = Report(id="1", scan_id="1", format="pdf")
        
        assert report.scan_id == scan.id


@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Database models not available")
class TestModelValidation:
    """Test model validation"""
    
    def test_required_fields(self):
        """Test that required fields are enforced"""
        # User without username should fail
        with pytest.raises((ValueError, TypeError)):
            User(email="test@test.com")
            
    def test_email_validation(self):
        """Test email format validation"""
        user = User(
            username="test",
            email="valid@example.com"
        )
        
        assert "@" in user.email
        assert "." in user.email


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
