"""
Comprehensive tests for api/schemas.py - Pydantic models validation and serialization
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

# Import all schemas
from api.schemas import (
    AssetBase,
    AssetResponse,
    DashboardResponse,
    DashboardStats,
    FindingBase,
    FindingCreate,
    FindingResponse,
    FindingUpdate,
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    PaginatedResponse,
    PaginationParams,
    RecentActivity,
    ReportBase,
    ReportFormat,
    ReportResponse,
    ScheduleExecutionResponse,
    ScheduleFrequency,
    ScheduledScanCreate,
    ScheduledScanResponse,
    ScheduledScanUpdate,
    ScanBase,
    ScanCreate,
    ScanResponse,
    ScanStatus,
    ScanUpdate,
    Severity,
    TokenResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    ToolInfo,
    UserCreate,
    UserInfo,
    UserLogin,
    VulnerabilityDBResponse,
    WSCommand,
    WSMessage,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Test enum definitions"""

    def test_scan_status_values(self):
        """Test ScanStatus enum values"""
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"

    def test_severity_values(self):
        """Test Severity enum values"""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"

    def test_report_format_values(self):
        """Test ReportFormat enum values"""
        assert ReportFormat.PDF == "pdf"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.JSON == "json"
        assert ReportFormat.XML == "xml"

    def test_schedule_frequency_values(self):
        """Test ScheduleFrequency enum values"""
        assert ScheduleFrequency.ONCE == "once"
        assert ScheduleFrequency.DAILY == "daily"
        assert ScheduleFrequency.WEEKLY == "weekly"
        assert ScheduleFrequency.MONTHLY == "monthly"


# ============================================================================
# AUTH SCHEMAS TESTS
# ============================================================================

class TestUserLogin:
    """Test UserLogin schema"""

    def test_valid_user_login(self):
        """Test valid user login data"""
        data = {"username": "testuser", "password": "password123"}
        user = UserLogin(**data)
        assert user.username == "testuser"
        assert user.password == "password123"

    def test_username_too_short(self):
        """Test username validation - too short"""
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(username="ab", password="password123")
        assert "username" in str(exc_info.value)

    def test_username_too_long(self):
        """Test username validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(username="a" * 51, password="password123")
        assert "username" in str(exc_info.value)

    def test_password_too_short(self):
        """Test password validation - too short"""
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(username="testuser", password="12345")
        assert "password" in str(exc_info.value)


class TestUserCreate:
    """Test UserCreate schema"""

    def test_valid_user_create(self):
        """Test valid user creation data"""
        data = {"username": "testuser", "password": "password123", "role": "user"}
        user = UserCreate(**data)
        assert user.username == "testuser"
        assert user.password == "password123"
        assert user.role == "user"

    def test_default_role(self):
        """Test default role is 'user'"""
        data = {"username": "testuser", "password": "password123"}
        user = UserCreate(**data)
        assert user.role == "user"

    def test_invalid_role(self):
        """Test invalid role validation"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="testuser", password="password123", role="superadmin")
        assert "role" in str(exc_info.value)


class TestTokenResponse:
    """Test TokenResponse schema"""

    def test_valid_token_response(self):
        """Test valid token response"""
        data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
            "token_type": "bearer",
            "expires_in": 900,
            "username": "testuser",
            "role": "admin",
            "refresh_token": "refresh_token_here"
        }
        token = TokenResponse(**data)
        assert token.access_token == data["access_token"]
        assert token.token_type == "bearer"
        assert token.expires_in == 900
        assert token.username == "testuser"
        assert token.role == "admin"
        assert token.refresh_token == "refresh_token_here"

    def test_token_response_without_refresh(self):
        """Test token response without refresh token (backward compatibility)"""
        data = {
            "access_token": "token123",
            "token_type": "bearer",
            "expires_in": 900,
            "username": "testuser",
            "role": "user"
        }
        token = TokenResponse(**data)
        assert token.refresh_token is None


class TestUserInfo:
    """Test UserInfo schema"""

    def test_valid_user_info(self):
        """Test valid user info"""
        data = {"username": "testuser", "role": "admin"}
        user = UserInfo(**data)
        assert user.username == "testuser"
        assert user.role == "admin"


# ============================================================================
# SCAN SCHEMAS TESTS
# ============================================================================

class TestScanBase:
    """Test ScanBase schema"""

    def test_valid_scan_base(self):
        """Test valid scan base data"""
        data = {
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full",
            "config": {"ports": "80,443"}
        }
        scan = ScanBase(**data)
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"
        assert scan.scan_type == "full"
        assert scan.config == {"ports": "80,443"}

    def test_scan_base_default_config(self):
        """Test scan base with default config"""
        data = {
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full"
        }
        scan = ScanBase(**data)
        assert scan.config == {}

    def test_name_too_long(self):
        """Test name validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            ScanBase(name="a" * 256, target="example.com", scan_type="full")
        assert "name" in str(exc_info.value)

    def test_target_too_long(self):
        """Test target validation - too long"""
        with pytest.raises(ValidationError) as exc_info:
            ScanBase(name="Test", target="a" * 501, scan_type="full")
        assert "target" in str(exc_info.value)

    def test_empty_name(self):
        """Test empty name validation"""
        with pytest.raises(ValidationError) as exc_info:
            ScanBase(name="", target="example.com", scan_type="full")
        assert "name" in str(exc_info.value)


class TestScanCreate:
    """Test ScanCreate schema"""

    def test_valid_scan_create(self):
        """Test valid scan creation"""
        data = {
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full",
            "objective": "comprehensive security scan"
        }
        scan = ScanCreate(**data)
        assert scan.objective == "comprehensive security scan"

    def test_default_objective(self):
        """Test default objective"""
        data = {
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full"
        }
        scan = ScanCreate(**data)
        assert scan.objective == "comprehensive security scan"


class TestScanUpdate:
    """Test ScanUpdate schema"""

    def test_valid_scan_update(self):
        """Test valid scan update"""
        data = {"status": "running", "config": {"threads": 10}}
        update = ScanUpdate(**data)
        assert update.status == "running"
        assert update.config == {"threads": 10}

    def test_partial_update(self):
        """Test partial scan update"""
        data = {"status": "completed"}
        update = ScanUpdate(**data)
        assert update.status == "completed"
        assert update.config is None


class TestScanResponse:
    """Test ScanResponse schema"""

    def test_valid_scan_response(self):
        """Test valid scan response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "name": "Test Scan",
            "target": "example.com",
            "scan_type": "full",
            "status": "completed",
            "user_id": 1,
            "created_at": now,
            "started_at": now,
            "completed_at": now,
            "result_summary": "Scan completed successfully",
            "findings_count": 5,
            "config": {}
        }
        scan = ScanResponse(**data)
        assert scan.id == 1
        assert scan.findings_count == 5

    def test_scan_response_from_attributes(self):
        """Test ScanResponse from_attributes config"""
        assert ScanResponse.model_config.get("from_attributes") is True


# ============================================================================
# FINDING SCHEMAS TESTS
# ============================================================================

class TestFindingBase:
    """Test FindingBase schema"""

    def test_valid_finding_base(self):
        """Test valid finding base data"""
        data = {
            "title": "SQL Injection",
            "description": "SQLi vulnerability found",
            "severity": Severity.HIGH,
            "cvss_score": 7.5,
            "cve_id": "CVE-2023-1234",
            "evidence": "Payload: ' OR 1=1--",
            "remediation": "Use parameterized queries",
            "tool": "sqlmap",
            "target": "example.com",
            "port": 443,
            "service": "https"
        }
        finding = FindingBase(**data)
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH
        assert finding.cvss_score == 7.5

    def test_default_severity(self):
        """Test default severity is MEDIUM"""
        data = {"title": "Test Finding"}
        finding = FindingBase(**data)
        assert finding.severity == Severity.MEDIUM

    def test_cvss_score_range(self):
        """Test CVSS score range validation"""
        # Valid scores
        FindingBase(title="Test", cvss_score=0)
        FindingBase(title="Test", cvss_score=10)
        FindingBase(title="Test", cvss_score=5.5)

        # Invalid scores
        with pytest.raises(ValidationError):
            FindingBase(title="Test", cvss_score=-1)
        with pytest.raises(ValidationError):
            FindingBase(title="Test", cvss_score=11)

    def test_title_too_long(self):
        """Test title validation - too long"""
        with pytest.raises(ValidationError):
            FindingBase(title="a" * 501)


class TestFindingCreate:
    """Test FindingCreate schema"""

    def test_valid_finding_create(self):
        """Test valid finding creation"""
        data = {
            "title": "XSS Vulnerability",
            "description": "Reflected XSS found",
            "severity": Severity.CRITICAL
        }
        finding = FindingCreate(**data)
        assert finding.title == "XSS Vulnerability"


class TestFindingResponse:
    """Test FindingResponse schema"""

    def test_valid_finding_response(self):
        """Test valid finding response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "scan_id": 1,
            "title": "Test Finding",
            "severity": Severity.HIGH,
            "created_at": now,
            "verified": 1
        }
        finding = FindingResponse(**data)
        assert finding.id == 1
        assert finding.scan_id == 1
        assert finding.verified == 1

    def test_default_verified(self):
        """Test default verified value"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "scan_id": 1,
            "title": "Test Finding",
            "created_at": now
        }
        finding = FindingResponse(**data)
        assert finding.verified == 0


class TestFindingUpdate:
    """Test FindingUpdate schema"""

    def test_valid_finding_update(self):
        """Test valid finding update"""
        data = {
            "severity": Severity.LOW,
            "verified": 1,
            "remediation": "Fixed in v2.0"
        }
        update = FindingUpdate(**data)
        assert update.severity == Severity.LOW
        assert update.verified == 1


# ============================================================================
# REPORT SCHEMAS TESTS
# ============================================================================

class TestReportBase:
    """Test ReportBase schema"""

    def test_valid_report_base(self):
        """Test valid report base data"""
        data = {
            "scan_id": 1,
            "format": ReportFormat.PDF,
            "template": "executive"
        }
        report = ReportBase(**data)
        assert report.scan_id == 1
        assert report.format == ReportFormat.PDF
        assert report.template == "executive"

    def test_default_format(self):
        """Test default format is PDF"""
        data = {"scan_id": 1}
        report = ReportBase(**data)
        assert report.format == ReportFormat.PDF

    def test_default_template(self):
        """Test default template"""
        data = {"scan_id": 1}
        report = ReportBase(**data)
        assert report.template == "default"


class TestReportResponse:
    """Test ReportResponse schema"""

    def test_valid_report_response(self):
        """Test valid report response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "scan_id": 1,
            "format": ReportFormat.HTML,
            "template": "default",
            "user_id": 1,
            "status": "completed",
            "file_path": "/reports/report_1.pdf",
            "file_size": 1024,
            "created_at": now,
            "generated_at": now
        }
        report = ReportResponse(**data)
        assert report.id == 1
        assert report.file_size == 1024


# ============================================================================
# TOOL EXECUTION SCHEMAS TESTS
# ============================================================================

class TestToolExecuteRequest:
    """Test ToolExecuteRequest schema"""

    def test_valid_tool_execute_request(self):
        """Test valid tool execution request"""
        data = {
            "tool_name": "nmap",
            "target": "example.com",
            "parameters": {"ports": "80,443", "script": "vuln"},
            "timeout": 300
        }
        req = ToolExecuteRequest(**data)
        assert req.tool_name == "nmap"
        assert req.target == "example.com"
        assert req.timeout == 300

    def test_default_parameters(self):
        """Test default empty parameters"""
        data = {
            "tool_name": "nmap",
            "target": "example.com"
        }
        req = ToolExecuteRequest(**data)
        assert req.parameters == {}
        assert req.timeout == 300


class TestToolExecuteResponse:
    """Test ToolExecuteResponse schema"""

    def test_valid_tool_execute_response(self):
        """Test valid tool execution response"""
        data = {
            "scan_id": 1,
            "status": "started",
            "message": "Tool execution started",
            "estimated_duration": 300
        }
        resp = ToolExecuteResponse(**data)
        assert resp.scan_id == 1
        assert resp.status == "started"
        assert resp.estimated_duration == 300


class TestToolInfo:
    """Test ToolInfo schema"""

    def test_valid_tool_info(self):
        """Test valid tool info"""
        data = {
            "name": "nmap",
            "description": "Network mapper",
            "category": "network",
            "parameters": {"ports": "Port range to scan"}
        }
        tool = ToolInfo(**data)
        assert tool.name == "nmap"
        assert tool.category == "network"


# ============================================================================
# DASHBOARD SCHEMAS TESTS
# ============================================================================

class TestDashboardStats:
    """Test DashboardStats schema"""

    def test_valid_dashboard_stats(self):
        """Test valid dashboard stats"""
        data = {
            "total_scans": 100,
            "active_scans": 5,
            "completed_scans": 90,
            "failed_scans": 5,
            "total_findings": 250,
            "critical_findings": 10,
            "high_findings": 40,
            "reports_generated": 20
        }
        stats = DashboardStats(**data)
        assert stats.total_scans == 100
        assert stats.critical_findings == 10


class TestRecentActivity:
    """Test RecentActivity schema"""

    def test_valid_recent_activity(self):
        """Test valid recent activity"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "type": "scan",
            "description": "Scan completed",
            "timestamp": now,
            "user": "admin"
        }
        activity = RecentActivity(**data)
        assert activity.type == "scan"
        assert activity.user == "admin"


class TestDashboardResponse:
    """Test DashboardResponse schema"""

    def test_valid_dashboard_response(self):
        """Test valid dashboard response"""
        now = datetime.utcnow()
        data = {
            "stats": {
                "total_scans": 10,
                "active_scans": 2,
                "completed_scans": 8,
                "failed_scans": 0,
                "total_findings": 50,
                "critical_findings": 5,
                "high_findings": 15,
                "reports_generated": 3
            },
            "recent_activities": [
                {
                    "id": 1,
                    "type": "scan",
                    "description": "Scan completed",
                    "timestamp": now,
                    "user": "admin"
                }
            ],
            "scans_by_status": {"pending": 2, "running": 1, "completed": 7},
            "findings_by_severity": {"critical": 5, "high": 15}
        }
        response = DashboardResponse(**data)
        assert response.stats.total_scans == 10
        assert len(response.recent_activities) == 1


# ============================================================================
# WEBSOCKET SCHEMAS TESTS
# ============================================================================

class TestWSMessage:
    """Test WSMessage schema"""

    def test_valid_ws_message(self):
        """Test valid WebSocket message"""
        data = {
            "type": "status",
            "scan_id": 1,
            "message": "Scan started",
            "data": {"progress": 50}
        }
        msg = WSMessage(**data)
        assert msg.type == "status"
        assert msg.scan_id == 1
        assert isinstance(msg.timestamp, datetime)

    def test_default_timestamp(self):
        """Test default timestamp is set"""
        data = {"type": "log", "message": "Test message"}
        msg = WSMessage(**data)
        assert isinstance(msg.timestamp, datetime)


class TestWSCommand:
    """Test WSCommand schema"""

    def test_valid_ws_command(self):
        """Test valid WebSocket command"""
        data = {
            "action": "start",
            "scan_id": 1,
            "parameters": {"target": "example.com"}
        }
        cmd = WSCommand(**data)
        assert cmd.action == "start"
        assert cmd.scan_id == 1


# ============================================================================
# NOTIFICATION SCHEMAS TESTS
# ============================================================================

class TestNotificationBase:
    """Test NotificationBase schema"""

    def test_valid_notification_base(self):
        """Test valid notification base"""
        data = {
            "type": "scan_complete",
            "title": "Scan Completed",
            "message": "Your scan has completed successfully"
        }
        notif = NotificationBase(**data)
        assert notif.type == "scan_complete"
        assert notif.title == "Scan Completed"


class TestNotificationCreate:
    """Test NotificationCreate schema"""

    def test_valid_notification_create(self):
        """Test valid notification creation"""
        data = {
            "type": "alert",
            "title": "Critical Finding",
            "message": "Critical vulnerability detected",
            "user_id": 1
        }
        notif = NotificationCreate(**data)
        assert notif.user_id == 1


class TestNotificationResponse:
    """Test NotificationResponse schema"""

    def test_valid_notification_response(self):
        """Test valid notification response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "type": "alert",
            "title": "Critical Finding",
            "message": "Critical vulnerability detected",
            "user_id": 1,
            "read": 0,
            "created_at": now
        }
        notif = NotificationResponse(**data)
        assert notif.id == 1
        assert notif.read == 0


# ============================================================================
# ASSET SCHEMAS TESTS
# ============================================================================

class TestAssetBase:
    """Test AssetBase schema"""

    def test_valid_asset_base(self):
        """Test valid asset base data"""
        data = {
            "name": "Web Server",
            "asset_type": "server",
            "ip_address": "192.168.1.1",
            "hostname": "web01.example.com",
            "os": "Ubuntu 22.04",
            "criticality": "high"
        }
        asset = AssetBase(**data)
        assert asset.name == "Web Server"
        assert asset.asset_type == "server"

    def test_default_criticality(self):
        """Test default criticality"""
        data = {"name": "Test Asset", "asset_type": "workstation"}
        asset = AssetBase(**data)
        assert asset.criticality == "medium"


class TestAssetResponse:
    """Test AssetResponse schema"""

    def test_valid_asset_response(self):
        """Test valid asset response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "name": "Database Server",
            "asset_type": "server",
            "services": {"mysql": {"port": 3306}},
            "created_at": now,
            "last_scanned": now
        }
        asset = AssetResponse(**data)
        assert asset.id == 1
        assert asset.services["mysql"]["port"] == 3306


# ============================================================================
# VULNERABILITY DB SCHEMAS TESTS
# ============================================================================

class TestVulnerabilityDBResponse:
    """Test VulnerabilityDBResponse schema"""

    def test_valid_vulnerability_response(self):
        """Test valid vulnerability DB response"""
        data = {
            "id": 1,
            "cve_id": "CVE-2023-1234",
            "title": "Critical RCE Vulnerability",
            "description": "Remote code execution vulnerability in Example Software",
            "severity": "critical",
            "cvss_score": 9.8,
            "epss_score": 0.95,
            "affected_products": ["Example Software 1.0", "Example Software 1.1"],
            "references": ["https://example.com/advisory"],
            "exploits": ["https://exploit-db.com/example"]
        }
        vuln = VulnerabilityDBResponse(**data)
        assert vuln.cve_id == "CVE-2023-1234"
        assert vuln.cvss_score == 9.8
        assert len(vuln.affected_products) == 2


# ============================================================================
# PAGINATION SCHEMAS TESTS
# ============================================================================

class TestPaginationParams:
    """Test PaginationParams schema"""

    def test_valid_pagination_params(self):
        """Test valid pagination params"""
        data = {"page": 2, "page_size": 50}
        params = PaginationParams(**data)
        assert params.page == 2
        assert params.page_size == 50
        assert params.skip == 50  # (2-1) * 50

    def test_default_pagination_params(self):
        """Test default pagination params"""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.skip == 0

    def test_page_validation(self):
        """Test page number validation"""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)
        with pytest.raises(ValidationError):
            PaginationParams(page=-1)

    def test_page_size_validation(self):
        """Test page size validation"""
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)


class TestPaginatedResponse:
    """Test PaginatedResponse schema"""

    def test_valid_paginated_response(self):
        """Test valid paginated response"""
        data = {
            "items": [{"id": 1}, {"id": 2}],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "pages": 5
        }
        resp = PaginatedResponse(**data)
        assert len(resp.items) == 2
        assert resp.total == 100
        assert resp.pages == 5


# ============================================================================
# SCHEDULED SCAN SCHEMAS TESTS
# ============================================================================

class TestScheduledScanCreate:
    """Test ScheduledScanCreate schema"""

    def test_valid_scheduled_scan_create(self):
        """Test valid scheduled scan creation"""
        data = {
            "name": "Daily Security Scan",
            "target": "example.com",
            "scan_type": "comprehensive",
            "frequency": ScheduleFrequency.DAILY,
            "schedule_time": "02:00",
            "enabled": True,
            "notification_email": "admin@example.com"
        }
        scan = ScheduledScanCreate(**data)
        assert scan.name == "Daily Security Scan"
        assert scan.frequency == ScheduleFrequency.DAILY
        assert scan.schedule_time == "02:00"

    def test_default_values(self):
        """Test default values"""
        data = {
            "name": "Test Schedule",
            "target": "example.com",
            "schedule_time": "02:00"
        }
        scan = ScheduledScanCreate(**data)
        assert scan.scan_type == "comprehensive"
        assert scan.frequency == ScheduleFrequency.WEEKLY
        assert scan.enabled is True

    def test_schedule_time_format_validation(self):
        """Test schedule time format validation"""
        # Valid times
        ScheduledScanCreate(name="Test", target="example.com", schedule_time="00:00")
        ScheduledScanCreate(name="Test", target="example.com", schedule_time="23:59")
        ScheduledScanCreate(name="Test", target="example.com", schedule_time="9:30")

        # Invalid times
        with pytest.raises(ValidationError):
            ScheduledScanCreate(name="Test", target="example.com", schedule_time="25:00")
        with pytest.raises(ValidationError):
            ScheduledScanCreate(name="Test", target="example.com", schedule_time="12:60")
        with pytest.raises(ValidationError):
            ScheduledScanCreate(name="Test", target="example.com", schedule_time="invalid")

    def test_schedule_day_validation(self):
        """Test schedule day validation"""
        # Valid days
        ScheduledScanCreate(name="Test", target="example.com", schedule_time="02:00", schedule_day=0)
        ScheduledScanCreate(name="Test", target="example.com", schedule_time="02:00", schedule_day=6)

        # Invalid days
        with pytest.raises(ValidationError):
            ScheduledScanCreate(name="Test", target="example.com", schedule_time="02:00", schedule_day=-1)
        with pytest.raises(ValidationError):
            ScheduledScanCreate(name="Test", target="example.com", schedule_time="02:00", schedule_day=7)


class TestScheduledScanUpdate:
    """Test ScheduledScanUpdate schema"""

    def test_valid_scheduled_scan_update(self):
        """Test valid scheduled scan update"""
        data = {
            "name": "Updated Schedule",
            "enabled": False,
            "last_run_status": "completed"
        }
        update = ScheduledScanUpdate(**data)
        assert update.name == "Updated Schedule"
        assert update.enabled is False


class TestScheduledScanResponse:
    """Test ScheduledScanResponse schema"""

    def test_valid_scheduled_scan_response(self):
        """Test valid scheduled scan response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "name": "Weekly Scan",
            "target": "example.com",
            "scan_type": "comprehensive",
            "frequency": "weekly",
            "schedule_time": "02:00",
            "schedule_day": 1,
            "enabled": True,
            "notification_email": "admin@example.com",
            "last_run_at": now,
            "last_run_status": "completed",
            "next_run_at": now,
            "created_at": now,
            "created_by": "admin"
        }
        scan = ScheduledScanResponse(**data)
        assert scan.id == 1
        assert scan.schedule_day == 1


class TestScheduleExecutionResponse:
    """Test ScheduleExecutionResponse schema"""

    def test_valid_execution_response(self):
        """Test valid schedule execution response"""
        now = datetime.utcnow()
        data = {
            "id": 1,
            "scheduled_scan_id": 1,
            "scan_id": 5,
            "status": "completed",
            "started_at": now,
            "completed_at": now,
            "error_message": None
        }
        resp = ScheduleExecutionResponse(**data)
        assert resp.scheduled_scan_id == 1
        assert resp.scan_id == 5


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

class TestSerialization:
    """Test model serialization"""

    def test_scan_response_json_serialization(self):
        """Test ScanResponse JSON serialization"""
        now = datetime.utcnow()
        scan = ScanResponse(
            id=1,
            name="Test Scan",
            target="example.com",
            scan_type="full",
            status="completed",
            user_id=1,
            created_at=now,
            config={}
        )
        json_data = scan.model_dump_json()
        assert isinstance(json_data, str)
        assert "Test Scan" in json_data

    def test_finding_response_dict_serialization(self):
        """Test FindingResponse dict serialization"""
        now = datetime.utcnow()
        finding = FindingResponse(
            id=1,
            scan_id=1,
            title="Test Finding",
            severity=Severity.HIGH,
            created_at=now
        )
        data = finding.model_dump()
        assert data["title"] == "Test Finding"
        assert data["severity"] == "high"

    def test_enum_serialization(self):
        """Test enum value serialization"""
        scan = ScanCreate(
            name="Test",
            target="example.com",
            scan_type="full"
        )
        # Test that the model can be serialized
        data = scan.model_dump()
        assert data["name"] == "Test"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_strings_validation(self):
        """Test empty string validation"""
        with pytest.raises(ValidationError):
            UserLogin(username="", password="password123")

        with pytest.raises(ValidationError):
            ScanBase(name="", target="example.com", scan_type="full")

    def test_unicode_support(self):
        """Test unicode support in strings"""
        scan = ScanCreate(
            name="スキャン",  # Japanese
            target="例え.com",  # Japanese domain
            scan_type="full"
        )
        assert scan.name == "スキャン"
        assert scan.target == "例え.com"

    def test_special_characters(self):
        """Test special characters in strings"""
        finding = FindingBase(
            title="Test <script>alert(1)</script>",
            description="Test with 'quotes' and \"double quotes\""
        )
        assert "<script>" in finding.title

    def test_very_long_strings(self):
        """Test very long string handling"""
        long_description = "A" * 10000
        finding = FindingBase(
            title="Test",
            description=long_description
        )
        assert len(finding.description) == 10000

    def test_none_values(self):
        """Test None value handling"""
        finding = FindingBase(
            title="Test",
            description=None,
            cvss_score=None
        )
        assert finding.description is None
        assert finding.cvss_score is None

    def test_nested_dict_config(self):
        """Test nested dictionary in config"""
        scan = ScanCreate(
            name="Test",
            target="example.com",
            scan_type="full",
            config={
                "nmap": {
                    "ports": "80,443",
                    "scripts": ["vuln", "safe"]
                },
                "timeout": 300
            }
        )
        assert scan.config["nmap"]["ports"] == "80,443"
        assert len(scan.config["nmap"]["scripts"]) == 2
