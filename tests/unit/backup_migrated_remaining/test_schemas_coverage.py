"""
Unit Tests for API Schemas - High Coverage Target
Tests all Pydantic models in api/schemas.py
"""

from datetime import datetime

import pytest

from api.schemas import (
    AssetBase,
    AssetCreate,
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
    ReportCreate,
    ReportFormat,
    ReportResponse,
    ScanBase,
    ScanCreate,
    ScanResponse,
    ScanStatus,
    ScanUpdate,
    ScheduledScanCreate,
    ScheduledScanResponse,
    ScheduledScanUpdate,
    ScheduleExecutionResponse,
    ScheduleFrequency,
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


class TestEnums:
    """Test all Enum classes"""

    def test_scan_status_values(self):
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"

    def test_severity_values(self):
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"

    def test_report_format_values(self):
        assert ReportFormat.PDF == "pdf"
        assert ReportFormat.HTML == "html"
        assert ReportFormat.JSON == "json"
        assert ReportFormat.XML == "xml"


class TestAuthSchemas:
    """Test authentication-related schemas"""

    def test_user_login_valid(self):
        login = UserLogin(username="testuser", password="securepass123")
        assert login.username == "testuser"
        assert login.password == "securepass123"

    def test_user_login_validation_error(self):
        # Test validation for username length
        with pytest.raises(ValueError):
            UserLogin(username="ab", password="securepass123")

    def test_user_create_valid(self):
        user = UserCreate(
            username="newuser", password="securepass123", role="user"
        )
        assert user.username == "newuser"
        assert user.role == "user"

    def test_user_create_default_role(self):
        user = UserCreate(username="newuser", password="securepass123")
        assert user.role == "user"

    def test_token_response(self):
        token = TokenResponse(
            access_token="token123",
            token_type="bearer",
            expires_in=3600,
            username="test",
            role="user",
        )
        assert token.access_token == "token123"
        assert token.token_type == "bearer"
        assert token.expires_in == 3600

    def test_token_response_with_refresh(self):
        token = TokenResponse(
            access_token="token123",
            token_type="bearer",
            expires_in=3600,
            username="test",
            role="user",
            refresh_token="refresh456",
        )
        assert token.refresh_token == "refresh456"

    def test_user_info(self):
        info = UserInfo(username="test", role="admin")
        assert info.username == "test"
        assert info.role == "admin"


class TestScanSchemas:
    """Test scan-related schemas"""

    def test_scan_base(self):
        scan = ScanBase(
            name="Test Scan", target="example.com", scan_type="port_scan"
        )
        assert scan.name == "Test Scan"
        assert scan.target == "example.com"
        assert scan.scan_type == "port_scan"
        assert scan.config == {}

    def test_scan_base_with_config(self):
        scan = ScanBase(
            name="Test Scan",
            target="example.com",
            scan_type="port_scan",
            config={"ports": "80,443"},
        )
        assert scan.config == {"ports": "80,443"}

    def test_scan_create(self):
        scan = ScanCreate(
            name="Test Scan",
            target="example.com",
            scan_type="port_scan",
            objective="quick check",
        )
        assert scan.objective == "quick check"

    def test_scan_update(self):
        update = ScanUpdate(status="running")
        assert update.status == "running"
        assert update.config is None

    def test_scan_update_with_config(self):
        update = ScanUpdate(status="running", config={"timeout": 30})
        assert update.config == {"timeout": 30}

    def test_scan_response(self):
        now = datetime.now()
        scan = ScanResponse(
            id=1,
            name="Test Scan",
            target="example.com",
            scan_type="port_scan",
            status="running",
            user_id=1,
            created_at=now,
            config={},
        )
        assert scan.id == 1
        assert scan.status == "running"
        assert scan.findings_count == 0


class TestFindingSchemas:
    """Test finding/vulnerability schemas"""

    def test_finding_base(self):
        finding = FindingBase(
            title="SQL Injection",
            description="SQLi found in login",
            severity=Severity.HIGH,
            target="example.com",
        )
        assert finding.title == "SQL Injection"
        assert finding.severity == Severity.HIGH

    def test_finding_create(self):
        finding = FindingCreate(
            title="XSS",
            description="Cross-site scripting",
            severity=Severity.MEDIUM,
            target="example.com",
            scan_id=1,
        )
        assert finding.scan_id == 1

    def test_finding_response(self):
        now = datetime.now()
        finding = FindingResponse(
            id=1,
            title="XSS",
            description="Cross-site scripting",
            severity=Severity.MEDIUM,
            target="example.com",
            scan_id=1,
            created_at=now,
            status="open",
        )
        assert finding.id == 1
        assert finding.status == "open"

    def test_finding_update(self):
        update = FindingUpdate(status="resolved")
        assert update.status == "resolved"


class TestReportSchemas:
    """Test report-related schemas"""

    def test_report_base(self):
        report = ReportBase(scan_id=1, format=ReportFormat.PDF)
        assert report.scan_id == 1
        assert report.format == ReportFormat.PDF

    def test_report_create(self):
        report = ReportCreate(
            scan_id=1, format=ReportFormat.HTML, template="detailed"
        )
        assert report.template == "detailed"

    def test_report_response(self):
        now = datetime.now()
        report = ReportResponse(
            id=1,
            scan_id=1,
            format=ReportFormat.JSON,
            status="completed",
            download_url="/downloads/report.pdf",
            created_at=now,
        )
        assert report.status == "completed"
        assert report.download_url == "/downloads/report.pdf"


class TestAssetSchemas:
    """Test asset-related schemas"""

    def test_asset_base(self):
        asset = AssetBase(
            name="Web Server", asset_type="server", target="192.168.1.1"
        )
        assert asset.name == "Web Server"
        assert asset.asset_type == "server"

    def test_asset_create(self):
        asset = AssetCreate(
            name="API Server",
            asset_type="server",
            target="api.example.com",
            description="Production API",
        )
        assert asset.description == "Production API"

    def test_asset_response(self):
        now = datetime.now()
        asset = AssetResponse(
            id=1,
            name="DB Server",
            asset_type="database",
            target="db.example.com",
            created_at=now,
            status="active",
        )
        assert asset.id == 1
        assert asset.status == "active"


class TestNotificationSchemas:
    """Test notification schemas"""

    def test_notification_base(self):
        notif = NotificationBase(
            type="email",
            title="Scan Complete",
            message="Your scan has finished",
        )
        assert notif.type == "email"
        assert notif.title == "Scan Complete"

    def test_notification_create(self):
        notif = NotificationCreate(
            type="slack",
            title="Alert",
            message="High severity finding",
            recipient="#security",
        )
        assert notif.recipient == "#security"

    def test_notification_response(self):
        now = datetime.now()
        notif = NotificationResponse(
            id=1,
            type="email",
            title="Test",
            message="Test message",
            status="sent",
            created_at=now,
        )
        assert notif.status == "sent"


class TestScheduledScanSchemas:
    """Test scheduled scan schemas"""

    def test_schedule_frequency_values(self):
        assert ScheduleFrequency.ONCE == "once"
        assert ScheduleFrequency.DAILY == "daily"
        assert ScheduleFrequency.WEEKLY == "weekly"
        assert ScheduleFrequency.MONTHLY == "monthly"

    def test_scheduled_scan_create(self):
        schedule = ScheduledScanCreate(
            name="Daily Scan",
            target="example.com",
            scan_type="port",
            frequency=ScheduleFrequency.DAILY,
            cron="0 0 * * *",
        )
        assert schedule.name == "Daily Scan"
        assert schedule.frequency == ScheduleFrequency.DAILY

    def test_scheduled_scan_update(self):
        update = ScheduledScanUpdate(name="Updated Scan", enabled=False)
        assert update.name == "Updated Scan"
        assert update.enabled is False

    def test_scheduled_scan_response(self):
        now = datetime.now()
        schedule = ScheduledScanResponse(
            id=1,
            name="Weekly Scan",
            target="example.com",
            scan_type="full",
            frequency=ScheduleFrequency.WEEKLY,
            cron="0 0 * * 0",
            created_at=now,
            next_run=now,
            enabled=True,
        )
        assert schedule.id == 1
        assert schedule.enabled is True


class TestToolSchemas:
    """Test tool execution schemas"""

    def test_tool_execute_request(self):
        req = ToolExecuteRequest(
            tool_name="nmap",
            parameters={"target": "example.com", "ports": "80,443"},
        )
        assert req.tool_name == "nmap"
        assert req.parameters["target"] == "example.com"

    def test_tool_execute_response(self):
        resp = ToolExecuteResponse(
            tool_name="nmap",
            status="success",
            output="Open ports: 80, 443",
            result={"ports": [80, 443]},
            execution_time=5.5,
        )
        assert resp.tool_name == "nmap"
        assert resp.status == "success"
        assert resp.execution_time == 5.5

    def test_tool_info(self):
        tool = ToolInfo(
            name="nmap",
            description="Network scanner",
            category="recon",
            parameters={},
        )
        assert tool.name == "nmap"
        assert tool.category == "recon"


class TestDashboardSchemas:
    """Test dashboard schemas"""

    def test_recent_activity(self):
        now = datetime.now()
        activity = RecentActivity(
            id=1,
            type="scan_completed",
            description="Port scan finished",
            timestamp=now,
            user="admin",
        )
        assert activity.type == "scan_completed"
        assert activity.id == 1

    def test_dashboard_stats(self):
        stats = DashboardStats(
            total_scans=100,
            active_scans=5,
            completed_scans=90,
            failed_scans=5,
            total_findings=50,
            critical_findings=2,
            high_findings=10,
            reports_generated=20,
        )
        assert stats.total_scans == 100
        assert stats.critical_findings == 2
        assert stats.completed_scans == 90

    def test_dashboard_response(self):
        now = datetime.now()
        dashboard = DashboardResponse(
            stats=DashboardStats(
                total_scans=100,
                active_scans=5,
                completed_scans=90,
                failed_scans=5,
                total_findings=50,
                critical_findings=2,
                high_findings=10,
                reports_generated=20,
            ),
            recent_activities=[],
            scans_by_status={},
            findings_by_severity={},
        )
        assert dashboard.stats.total_scans == 100


class TestVulnerabilityDBSchemas:
    """Test vulnerability database schemas"""

    def test_vulnerability_db_response(self):
        vuln = VulnerabilityDBResponse(
            id=1,
            cve_id="CVE-2023-1234",
            title="Sample Vulnerability",
            description="A test vulnerability",
            severity=Severity.HIGH,
            cvss_score=8.5,
            epss_score=0.5,
            affected_products=["Product 1.0"],
            references=["https://example.com"],
            exploits=[],
        )
        assert vuln.cve_id == "CVE-2023-1234"
        assert vuln.cvss_score == 8.5


class TestWebSocketSchemas:
    """Test WebSocket schemas"""

    def test_ws_message(self):
        msg = WSMessage(
            type="status_update",
            scan_id=1,
            message="Scan running",
            data={"status": "running"},
            timestamp=datetime.now(),
        )
        assert msg.type == "status_update"
        assert msg.scan_id == 1

    def test_ws_command(self):
        cmd = WSCommand(action="stop_scan", scan_id=1, parameters={})
        assert cmd.action == "stop_scan"


class TestPaginationSchemas:
    """Test pagination schemas"""

    def test_pagination_params_default(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 50

    def test_pagination_params_custom(self):
        params = PaginationParams(page=2, page_size=100)
        assert params.page == 2
        assert params.page_size == 100

    def test_paginated_response(self):
        paginated = PaginatedResponse(
            items=[{"id": 1}, {"id": 2}],
            total=100,
            page=1,
            page_size=50,
            pages=2,
        )
        assert paginated.total == 100
        assert len(paginated.items) == 2


class TestEdgeCases:
    """Test edge cases and validation"""

    def test_empty_config_dict(self):
        scan = ScanBase(
            name="Test", target="example.com", scan_type="port", config={}
        )
        assert scan.config == {}

    def test_optional_fields_none(self):
        update = ScanUpdate()
        assert update.status is None
        assert update.config is None

    def test_datetime_fields(self):
        now = datetime.now()
        scan = ScanResponse(
            id=1,
            name="Test",
            target="example.com",
            scan_type="port",
            status="running",
            user_id=1,
            created_at=now,
            started_at=now,
            completed_at=now,
        )
        assert scan.created_at == now
        assert scan.started_at == now
        assert scan.completed_at == now

    def test_severity_enum_comparison(self):
        finding = FindingBase(
            title="Test",
            description="Test",
            severity=Severity.CRITICAL,
            target="example.com",
        )
        assert finding.severity.value == "critical"
        assert finding.severity == Severity.CRITICAL
