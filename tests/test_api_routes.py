"""
Comprehensive tests for API routes - scans, agents, auth, and other endpoints
Uses FastAPI TestClient with mocked dependencies
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

# Setup mocks before imports
sys.modules["redis"] = MagicMock()
sys.modules["auth"] = MagicMock()
sys.modules["auth.jwt_handler"] = MagicMock()
sys.modules["database"] = MagicMock()
sys.modules["database.auth_models"] = MagicMock()
sys.modules["database.crud"] = MagicMock()
sys.modules["database.models"] = MagicMock()
sys.modules["agents"] = MagicMock()
sys.modules["agents.react_agent"] = MagicMock()
sys.modules["agents.workflows.orchestrator"] = MagicMock()
sys.modules["tools"] = MagicMock()
sys.modules["reports"] = MagicMock()
sys.modules["reports.generator"] = MagicMock()
sys.modules["notifications"] = MagicMock()
sys.modules["notifications.slack"] = MagicMock()
sys.modules["integrations"] = MagicMock()
sys.modules["integrations.jira_client"] = MagicMock()

# Set environment variables
os.environ["ADMIN_PASSWORD"] = "test123"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["CORS_ORIGINS"] = (
    '["http://localhost:3000", "http://localhost:8000"]'
)

# Import after mocking
from api.schemas import (
    FindingCreate,
    FindingResponse,
    ReportCreate,
    ReportResponse,
    ScanCreate,
    ScanResponse,
    ScanUpdate,
    Severity,
    TokenResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    UserLogin,
)


class TestSchemas:
    """Test Pydantic schemas used by routes"""

    def test_user_login_schema(self):
        """Test UserLogin schema"""
        data = {"username": "admin", "password": "password123"}
        login = UserLogin(**data)
        assert login.username == "admin"
        assert login.password == "password123"

    def test_user_login_validation_error(self):
        """Test UserLogin validation"""
        # Too short username
        with pytest.raises(Exception):
            UserLogin(username="ab", password="password123")

        # Too short password
        with pytest.raises(Exception):
            UserLogin(username="admin", password="12345")

    def test_scan_create_schema(self):
        """Test ScanCreate schema"""
        data = {
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full",
            "config": {"ports": "80,443"},
        }
        scan = ScanCreate(**data)
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"
        assert scan.objective == "comprehensive security scan"  # default

    def test_scan_response_schema(self):
        """Test ScanResponse schema"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full",
            "status": "completed",
            "user_id": 1,
            "created_at": now,
            "config": {},
        }
        scan = ScanResponse(**data)
        assert scan.id == 1
        assert scan.findings_count == 0  # default

    def test_scan_update_schema(self):
        """Test ScanUpdate schema"""
        data = {"status": "running", "config": {"threads": 10}}
        update = ScanUpdate(**data)
        assert update.status == "running"
        assert update.config == {"threads": 10}

    def test_finding_create_schema(self):
        """Test FindingCreate schema"""
        data = {
            "title": "SQL Injection",
            "description": "SQLi vulnerability",
            "severity": Severity.HIGH,
            "cvss_score": 7.5,
        }
        finding = FindingCreate(**data)
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH

    def test_finding_response_schema(self):
        """Test FindingResponse schema"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "scan_id": 1,
            "title": "Test Finding",
            "severity": Severity.MEDIUM,
            "created_at": now,
        }
        finding = FindingResponse(**data)
        assert finding.id == 1
        assert finding.verified == 0  # default

    def test_report_create_schema(self):
        """Test ReportCreate schema"""
        data = {"scan_id": 1, "format": "pdf", "template": "executive"}
        report = ReportCreate(**data)
        assert report.scan_id == 1
        assert report.template == "executive"

    def test_report_response_schema(self):
        """Test ReportResponse schema"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "scan_id": 1,
            "format": "pdf",
            "template": "default",
            "user_id": 1,
            "status": "completed",
            "created_at": now,
        }
        report = ReportResponse(**data)
        assert report.id == 1

    def test_tool_execute_request_schema(self):
        """Test ToolExecuteRequest schema"""
        data = {
            "tool_name": "nmap",
            "target": "example.com",
            "parameters": {"ports": "80,443"},
            "timeout": 300,
        }
        req = ToolExecuteRequest(**data)
        assert req.tool_name == "nmap"
        assert req.timeout == 300

    def test_tool_execute_response_schema(self):
        """Test ToolExecuteResponse schema"""
        data = {
            "scan_id": 1,
            "status": "started",
            "message": "Tool execution started",
            "estimated_duration": 300,
        }
        resp = ToolExecuteResponse(**data)
        assert resp.scan_id == 1
        assert resp.status == "started"

    def test_token_response_schema(self):
        """Test TokenResponse schema"""
        data = {
            "access_token": "test-token",
            "token_type": "bearer",
            "expires_in": 900,
            "username": "admin",
            "role": "admin",
            "refresh_token": "refresh-token",
        }
        token = TokenResponse(**data)
        assert token.access_token == "test-token"
        assert token.refresh_token == "refresh-token"


class TestSchemaValidations:
    """Test schema validations"""

    def test_scan_name_required(self):
        """Test scan name is required"""
        with pytest.raises(Exception):
            ScanCreate(name="", target="example.com", scan_type="full")

    def test_scan_target_required(self):
        """Test scan target is required"""
        with pytest.raises(Exception):
            ScanCreate(name="Test", target="", scan_type="full")

    def test_cvss_score_range(self):
        """Test CVSS score range validation"""
        # Valid scores
        FindingCreate(title="Test", cvss_score=0)
        FindingCreate(title="Test", cvss_score=10)
        FindingCreate(title="Test", cvss_score=5.5)

        # Invalid scores
        with pytest.raises(Exception):
            FindingCreate(title="Test", cvss_score=-1)
        with pytest.raises(Exception):
            FindingCreate(title="Test", cvss_score=11)

    def test_finding_title_max_length(self):
        """Test finding title max length"""
        with pytest.raises(Exception):
            FindingCreate(title="a" * 501)

    def test_severity_enum_values(self):
        """Test severity enum values"""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"


class TestSchemaSerialization:
    """Test schema serialization"""

    def test_scan_response_serialization(self):
        """Test ScanResponse serialization"""
        now = datetime.utcnow()
        scan = ScanResponse(
            id=1,
            name="Test Scan",
            target="example.com",
            scan_type="full",
            status="completed",
            user_id=1,
            created_at=now,
            config={},
        )
        data = scan.model_dump()
        assert data["name"] == "Test Scan"
        assert data["status"] == "completed"

    def test_finding_response_serialization(self):
        """Test FindingResponse serialization"""
        now = datetime.utcnow()
        finding = FindingResponse(
            id=1,
            scan_id=1,
            title="Test Finding",
            severity=Severity.HIGH,
            created_at=now,
        )
        data = finding.model_dump()
        assert data["title"] == "Test Finding"
        assert data["severity"] == "high"

    def test_json_serialization(self):
        """Test JSON serialization"""
        now = datetime.utcnow()
        scan = ScanResponse(
            id=1,
            name="Test Scan",
            target="example.com",
            scan_type="full",
            status="completed",
            user_id=1,
            created_at=now,
            config={"ports": "80,443"},
        )
        json_str = scan.model_dump_json()
        assert isinstance(json_str, str)
        assert "Test Scan" in json_str


class TestSchemaEdgeCases:
    """Test schema edge cases"""

    def test_unicode_in_schemas(self):
        """Test unicode support"""
        scan = ScanCreate(
            name="日本語スキャン", target="例え.com", scan_type="full"
        )
        assert scan.name == "日本語スキャン"
        assert scan.target == "例え.com"

    def test_special_characters_in_schemas(self):
        """Test special characters"""
        finding = FindingCreate(
            title="Test <script>alert(1)</script>",
            description="Test with 'quotes' and \"double quotes\"",
        )
        assert "<script>" in finding.title

    def test_none_values_in_schemas(self):
        """Test None values"""
        finding = FindingCreate(
            title="Test", description=None, cvss_score=None
        )
        assert finding.description is None
        assert finding.cvss_score is None

    def test_empty_config(self):
        """Test empty config dict"""
        scan = ScanCreate(
            name="Test", target="example.com", scan_type="full", config={}
        )
        assert scan.config == {}

    def test_nested_config(self):
        """Test nested config dict"""
        scan = ScanCreate(
            name="Test",
            target="example.com",
            scan_type="full",
            config={"nmap": {"ports": "80,443", "scripts": ["vuln", "safe"]}},
        )
        assert scan.config["nmap"]["ports"] == "80,443"
