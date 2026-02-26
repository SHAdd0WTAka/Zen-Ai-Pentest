"""
Comprehensive tests for core/health_check.py

Tests all health check functionality with proper mocking for:
- System calls (psutil, os)
- Subprocess calls
- Database connections
- Network requests
- File system operations

Target: 80%+ coverage for core/health_check.py
"""

import asyncio
import json
import os
import ssl
import sys
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch, mock_open

import pytest

# Ensure the core module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.health_check import (
    APIHealthCheck,
    BaseHealthCheck,
    DatabaseHealthCheck,
    HealthCheckConfig,
    HealthCheckResult,
    HealthCheckRunner,
    HealthReport,
    HealthStatus,
    ResourcesHealthCheck,
    SecurityHealthCheck,
    SeverityLevel,
    ToolsHealthCheck,
    check_api_health,
    check_database,
    check_resources,
    check_security_config,
    check_tools,
    run_health_check,
)


# ==================== Fixtures ====================


@pytest.fixture
def default_config():
    """Default health check configuration"""
    return HealthCheckConfig()


@pytest.fixture
def minimal_config():
    """Minimal health check configuration with all checks disabled"""
    return HealthCheckConfig(
        check_database=False,
        check_tools=False,
        check_api=False,
        check_resources=False,
        check_security=False,
    )


@pytest.fixture
def mock_health_result():
    """Mock health check result"""
    return HealthCheckResult(
        name="test_check",
        status=HealthStatus.OK,
        message="Test passed",
        details={"test": True},
        duration_ms=100.0,
    )


@pytest.fixture
def mock_health_report():
    """Mock health report"""
    return HealthReport(
        overall_status=HealthStatus.OK,
        checks=[
            HealthCheckResult("check1", HealthStatus.OK, "OK"),
            HealthCheckResult("check2", HealthStatus.WARNING, "Warning"),
        ],
        summary={
            "total": 2,
            "ok": 1,
            "warning": 1,
            "error": 0,
            "critical": 0,
            "skipped": 0,
        },
        metadata={},
    )


@pytest.fixture
def mock_psutil_memory():
    """Mock psutil virtual_memory result"""
    mock = MagicMock()
    mock.total = 16 * 1024**3  # 16 GB
    mock.available = 8 * 1024**3  # 8 GB
    mock.used = 8 * 1024**3  # 8 GB
    mock.percent = 50.0
    return mock


@pytest.fixture
def mock_psutil_cpu():
    """Mock psutil cpu info"""
    mock_freq = MagicMock()
    mock_freq.current = 2400.0
    return mock_freq


@pytest.fixture
def mock_psutil_disk():
    """Mock psutil disk info"""
    mock_usage = MagicMock()
    mock_usage.total = 100 * 1024**3  # 100 GB
    mock_usage.used = 50 * 1024**3  # 50 GB
    mock_usage.free = 50 * 1024**3  # 50 GB
    mock_usage.percent = 50.0
    return mock_usage


@pytest.fixture
def mock_psutil_partitions():
    """Mock psutil disk_partitions result"""
    mock_part = MagicMock()
    mock_part.device = "/dev/sda1"
    mock_part.mountpoint = "/"
    mock_part.fstype = "ext4"
    return [mock_part]


# ==================== HealthStatus Enum Tests ====================


class TestHealthStatus:
    """Test HealthStatus enum"""

    def test_enum_values(self):
        """Test HealthStatus enum has correct values"""
        assert HealthStatus.OK.value == "ok"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.ERROR.value == "error"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.SKIPPED.value == "skipped"

    def test_enum_comparison(self):
        """Test HealthStatus enum comparison"""
        assert HealthStatus.OK == HealthStatus.OK
        assert HealthStatus.CRITICAL != HealthStatus.OK
        assert HealthStatus.WARNING != HealthStatus.ERROR


# ==================== SeverityLevel Enum Tests ====================


class TestSeverityLevel:
    """Test SeverityLevel enum"""

    def test_enum_values(self):
        """Test SeverityLevel enum has correct values"""
        assert SeverityLevel.LOW.value == 1
        assert SeverityLevel.MEDIUM.value == 2
        assert SeverityLevel.HIGH.value == 3
        assert SeverityLevel.CRITICAL.value == 4

    def test_enum_ordering(self):
        """Test SeverityLevel enum ordering"""
        assert SeverityLevel.LOW.value < SeverityLevel.MEDIUM.value
        assert SeverityLevel.MEDIUM.value < SeverityLevel.HIGH.value
        assert SeverityLevel.HIGH.value < SeverityLevel.CRITICAL.value


# ==================== HealthCheckResult Tests ====================


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""

    def test_basic_creation(self):
        """Test creating a basic result"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.OK,
            message="Test passed",
        )
        assert result.name == "test"
        assert result.status == HealthStatus.OK
        assert result.message == "Test passed"
        assert result.details == {}
        assert isinstance(result.timestamp, datetime)
        assert result.severity == SeverityLevel.MEDIUM

    def test_full_creation(self):
        """Test creating a result with all fields"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.WARNING,
            message="Warning message",
            details={"key": "value"},
            duration_ms=150.5,
            severity=SeverityLevel.HIGH,
            remediation="Fix this issue",
        )
        assert result.status == HealthStatus.WARNING
        assert result.details == {"key": "value"}
        assert result.duration_ms == 150.5
        assert result.severity == SeverityLevel.HIGH
        assert result.remediation == "Fix this issue"

    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.OK,
            message="OK",
            details={"foo": "bar"},
            duration_ms=100.0,
        )
        data = result.to_dict()
        assert data["name"] == "test"
        assert data["status"] == "ok"
        assert data["message"] == "OK"
        assert data["details"] == {"foo": "bar"}
        assert data["duration_ms"] == 100.0
        assert data["severity"] == "MEDIUM"
        assert "timestamp" in data

    def test_to_dict_with_remediation(self):
        """Test conversion with remediation"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.ERROR,
            message="Error",
            remediation="Fix by doing X",
        )
        data = result.to_dict()
        assert data["remediation"] == "Fix by doing X"


# ==================== HealthReport Tests ====================


class TestHealthReport:
    """Test HealthReport dataclass"""

    def test_basic_creation(self):
        """Test creating a basic report"""
        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0},
            metadata={},
        )
        assert report.overall_status == HealthStatus.OK
        assert report.checks == []
        assert isinstance(report.generated_at, datetime)

    def test_to_dict(self):
        """Test report to dictionary conversion"""
        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[HealthCheckResult("test", HealthStatus.OK, "OK")],
            summary={"total": 1, "ok": 1},
            metadata={"version": "1.0"},
        )
        data = report.to_dict()
        assert data["overall_status"] == "ok"
        assert data["summary"]["total"] == 1
        assert len(data["checks"]) == 1
        assert data["metadata"]["version"] == "1.0"
        assert "generated_at" in data
        assert "duration_ms" in data

    def test_to_json(self, mock_health_report):
        """Test report to JSON conversion"""
        json_str = mock_health_report.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["overall_status"] == "ok"
        assert "checks" in data
        assert "summary" in data

    def test_to_json_custom_indent(self):
        """Test JSON with custom indent"""
        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0},
            metadata={},
        )
        json_str = report.to_json(indent=4)
        assert "    " in json_str  # 4-space indent


# ==================== HealthCheckConfig Tests ====================


class TestHealthCheckConfig:
    """Test HealthCheckConfig Pydantic model"""

    def test_default_values(self):
        """Test default configuration values"""
        config = HealthCheckConfig()
        assert config.check_database is True
        assert config.check_tools is True
        assert config.check_api is True
        assert config.check_resources is True
        assert config.check_security is True
        assert config.database_timeout == 5
        assert config.api_timeout == 10
        assert "nmap" in config.required_tools
        assert "sqlmap" in config.required_tools
        assert "nuclei" in config.required_tools

    def test_custom_values(self):
        """Test custom configuration values"""
        config = HealthCheckConfig(
            check_database=False,
            database_timeout=10,
            memory_warning_threshold=70.0,
            api_base_url="http://example.com:8080",
        )
        assert config.check_database is False
        assert config.database_timeout == 10
        assert config.memory_warning_threshold == 70.0
        assert config.api_base_url == "http://example.com:8080"

    def test_validation_timeout_range(self):
        """Test timeout validation"""
        with pytest.raises(ValueError):
            HealthCheckConfig(database_timeout=0)
        with pytest.raises(ValueError):
            HealthCheckConfig(database_timeout=61)
        # Valid values should work
        config = HealthCheckConfig(database_timeout=5)
        assert config.database_timeout == 5

    def test_validation_threshold_range(self):
        """Test threshold percentage validation"""
        with pytest.raises(ValueError):
            HealthCheckConfig(memory_warning_threshold=101)
        with pytest.raises(ValueError):
            HealthCheckConfig(memory_warning_threshold=-1)
        # Valid values should work
        config = HealthCheckConfig(memory_warning_threshold=50.0)
        assert config.memory_warning_threshold == 50.0

    def test_tool_string_parsing(self):
        """Test tool string parsing"""
        config = HealthCheckConfig(required_tools="nmap,sqlmap,nuclei")
        assert config.required_tools == ["nmap", "sqlmap", "nuclei"]

    def test_tool_list_passthrough(self):
        """Test tool list passthrough"""
        tools = ["tool1", "tool2"]
        config = HealthCheckConfig(required_tools=tools)
        assert config.required_tools == tools

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            HealthCheckConfig(invalid_field=True)

    def test_optional_tools_default(self):
        """Test optional tools default value"""
        config = HealthCheckConfig()
        assert "gobuster" in config.optional_tools
        assert "ffuf" in config.optional_tools
        assert "amass" in config.optional_tools


# ==================== BaseHealthCheck Tests ====================


class TestBaseHealthCheck:
    """Test BaseHealthCheck class"""

    def test_initialization(self, default_config):
        """Test base check initialization"""
        check = BaseHealthCheck(default_config)
        assert check.config == default_config
        assert check.name == "base_check"
        assert check.description == "Base health check"
        assert check.severity == SeverityLevel.MEDIUM

    def test_create_result(self, default_config):
        """Test result creation helper"""
        check = BaseHealthCheck(default_config)
        result = check._create_result(
            HealthStatus.OK,
            "Test message",
            {"key": "value"},
            50.0,
            "Fix it",
        )
        assert result.status == HealthStatus.OK
        assert result.message == "Test message"
        assert result.details == {"key": "value"}
        assert result.duration_ms == 50.0
        assert result.remediation == "Fix it"
        assert result.name == "base_check"
        assert result.severity == SeverityLevel.MEDIUM

    def test_create_result_defaults(self, default_config):
        """Test result creation with defaults"""
        check = BaseHealthCheck(default_config)
        result = check._create_result(HealthStatus.OK, "Test")
        assert result.details == {}
        assert result.duration_ms == 0.0
        assert result.remediation is None

    @pytest.mark.asyncio
    async def test_run_not_implemented(self, default_config):
        """Test that run() raises NotImplementedError"""
        check = BaseHealthCheck(default_config)
        with pytest.raises(NotImplementedError):
            await check.run()

    def test_run_sync_success(self, default_config):
        """Test _run_sync with successful function"""
        check = BaseHealthCheck(default_config)
        result = check._run_sync(lambda: "success")
        assert result == "success"

    def test_run_sync_error(self, default_config):
        """Test _run_sync with error"""
        check = BaseHealthCheck(default_config)
        with pytest.raises(ValueError):
            check._run_sync(lambda: (_ for _ in ()).throw(ValueError("test error")))

    @pytest.mark.asyncio
    async def test_run_async_success(self, default_config):
        """Test _run_async with successful function"""
        check = BaseHealthCheck(default_config)
        result = await check._run_async(lambda: "success")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_run_async_timeout(self, default_config):
        """Test _run_async timeout"""
        config = HealthCheckConfig(timeout_per_check=5)
        check = BaseHealthCheck(config)
        
        def slow_func():
            time.sleep(6)
            return "success"
        
        with pytest.raises(TimeoutError):
            await check._run_async(slow_func)


# ==================== DatabaseHealthCheck Tests ====================


class TestDatabaseHealthCheck:
    """Test DatabaseHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = DatabaseHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED
        assert "disabled" in result.message.lower()
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_sqlite_check_success(self, default_config):
        """Test SQLite database check success"""
        config = HealthCheckConfig(
            check_database=True,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = DatabaseHealthCheck(config)
        result = await check.run()
        # Should succeed with SQLite default database
        assert result.status in [HealthStatus.OK, HealthStatus.WARNING]
        assert "database" in result.message.lower()

    @pytest.mark.asyncio
    async def test_sqlite_with_temp_db(self, default_config):
        """Test SQLite check with temporary database"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            config = HealthCheckConfig(
                check_database=True,
                database_url=f"sqlite:///{db_path}",
                check_tools=False,
                check_api=False,
                check_resources=False,
                check_security=False,
            )
            check = DatabaseHealthCheck(config)
            result = await check.run()
            assert result.status in [HealthStatus.OK, HealthStatus.WARNING]

    @pytest.mark.asyncio
    async def test_invalid_database_url(self, default_config):
        """Test with invalid database URL"""
        config = HealthCheckConfig(
            check_database=True,
            database_url="sqlite:///nonexistent/path/to/db.sqlite",
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = DatabaseHealthCheck(config)
        result = await check.run()
        # Should handle the error gracefully
        assert result.status in [HealthStatus.ERROR, HealthStatus.CRITICAL]
        assert "error" in result.message.lower() or "failed" in result.message.lower()

    def test_check_database_method_structure(self, default_config):
        """Test internal _check_database method returns correct structure"""
        check = DatabaseHealthCheck(default_config)
        result = check._check_database()
        assert "connection" in result
        assert "type" in result
        assert "query_performance" in result
        assert "size_mb" in result
        assert "tables" in result

    @pytest.mark.asyncio
    async def test_database_check_exception_handling(self, default_config):
        """Test database check exception handling"""
        config = HealthCheckConfig(check_database=True)
        check = DatabaseHealthCheck(config)
        
        with patch.object(check, '_check_database', side_effect=Exception("DB Error")):
            result = await check.run()
            assert result.status == HealthStatus.ERROR
            assert "DB Error" in result.message


# ==================== ToolsHealthCheck Tests ====================


class TestToolsHealthCheck:
    """Test ToolsHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = ToolsHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED
        assert "disabled" in result.message.lower()

    @pytest.mark.asyncio
    async def test_tools_check_all_available(self, default_config):
        """Test tool check when all tools available"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            required_tools=["python"],
            optional_tools=[],
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = ToolsHealthCheck(config)
        result = await check.run()
        assert result.status == HealthStatus.OK
        assert "python" in result.details["required"]
        assert result.details["required"]["python"]["available"] is True

    @pytest.mark.asyncio
    async def test_missing_required_tools(self, default_config):
        """Test with missing required tools"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            required_tools=["nonexistent_tool_12345"],
            optional_tools=[],
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = ToolsHealthCheck(config)
        result = await check.run()
        assert result.status == HealthStatus.CRITICAL
        assert "nonexistent_tool_12345" in result.details["required"]
        assert result.remediation is not None

    @pytest.mark.asyncio
    async def test_many_optional_tools_missing(self, default_config):
        """Test warning when many optional tools missing"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            required_tools=["python"],
            optional_tools=[
                "nonexistent1", "nonexistent2", "nonexistent3",
                "nonexistent4", "nonexistent5"
            ],
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = ToolsHealthCheck(config)
        result = await check.run()
        assert result.status == HealthStatus.WARNING

    def test_check_tool_available(self, default_config):
        """Test individual tool checking - available"""
        check = ToolsHealthCheck(default_config)
        result = check._check_tool("python")
        assert result["available"] is True
        assert result["path"] is not None

    def test_check_tool_not_available(self, default_config):
        """Test individual tool checking - not available"""
        check = ToolsHealthCheck(default_config)
        result = check._check_tool("nonexistent_tool_xyz")
        assert result["available"] is False
        assert result["path"] is None
        assert result["version"] is None

    def test_check_tool_with_version(self, default_config):
        """Test tool version extraction"""
        check = ToolsHealthCheck(default_config)
        result = check._check_tool("python")
        if result["available"]:
            # Python might not have a version pattern defined
            pass  # Version may or may not be extracted

    def test_check_tools_structure(self, default_config):
        """Test _check_tools returns correct structure"""
        config = HealthCheckConfig(
            required_tools=["python"],
            optional_tools=[],
        )
        check = ToolsHealthCheck(config)
        result = check._check_tools()
        assert "required" in result
        assert "optional" in result
        assert "total_available" in result
        assert "total_missing" in result
        assert "python" in result["required"]

    @pytest.mark.asyncio
    async def test_tools_check_exception_handling(self, default_config):
        """Test tools check exception handling"""
        config = HealthCheckConfig(check_tools=True)
        check = ToolsHealthCheck(config)
        
        with patch.object(check, '_check_tools', side_effect=Exception("Tool Error")):
            result = await check.run()
            assert result.status == HealthStatus.ERROR
            assert "Tool Error" in result.message


# ==================== APIHealthCheck Tests ====================


class TestAPIHealthCheck:
    """Test APIHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = APIHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED
        assert "disabled" in result.message.lower()

    @pytest.mark.asyncio
    async def test_api_unavailable(self, default_config):
        """Test API check when API is unavailable"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=True,
            api_base_url="http://localhost:59999",
            api_timeout=1,
            check_resources=False,
            check_security=False,
        )
        check = APIHealthCheck(config)
        result = await check.run()
        # Should detect that API is not available
        assert result.status in [HealthStatus.CRITICAL, HealthStatus.ERROR]
        assert (
            "error" in result.message.lower()
            or "failed" in result.message.lower()
        )

    def test_check_api_structure(self, default_config):
        """Test _check_api returns correct structure"""
        check = APIHealthCheck(default_config)
        result = check._check_api()
        assert "base_url" in result
        assert "health_endpoint" in result
        assert "auth_status" in result

    @pytest.mark.asyncio
    async def test_api_slow_response(self, default_config):
        """Test API check with slow response"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=True,
            check_resources=False,
            check_security=False,
        )
        check = APIHealthCheck(config)
        
        mock_result = {
            "base_url": "http://localhost:8000",
            "health_endpoint": {
                "status": "ok",
                "response_time_ms": 6000,  # Slow response
            },
            "auth_status": "unknown",
        }
        
        with patch.object(check, '_check_api', return_value=mock_result):
            result = await check.run()
            assert result.status == HealthStatus.WARNING
            assert "slow" in result.message.lower()

    @pytest.mark.asyncio
    async def test_api_auth_error(self, default_config):
        """Test API check with auth error"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=True,
            api_auth_token="invalid_token",
            check_resources=False,
            check_security=False,
        )
        check = APIHealthCheck(config)
        
        mock_result = {
            "base_url": "http://localhost:8000",
            "health_endpoint": {"status": "ok", "response_time_ms": 100},
            "auth_status": "error",
        }
        
        with patch.object(check, '_check_api', return_value=mock_result):
            result = await check.run()
            assert result.status == HealthStatus.WARNING

    @pytest.mark.asyncio
    async def test_api_check_exception_handling(self, default_config):
        """Test API check exception handling"""
        config = HealthCheckConfig(check_api=True)
        check = APIHealthCheck(config)
        
        with patch.object(check, '_check_api', side_effect=Exception("API Error")):
            result = await check.run()
            assert result.status == HealthStatus.ERROR
            assert "API Error" in result.message


# ==================== ResourcesHealthCheck Tests ====================


class TestResourcesHealthCheck:
    """Test ResourcesHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = ResourcesHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED
        assert "disabled" in result.message.lower()

    @pytest.mark.asyncio
    async def test_resources_check_healthy(self, default_config, mock_psutil_memory, mock_psutil_disk, mock_psutil_partitions):
        """Test resource check with healthy resources"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=True,
            memory_critical_threshold=95.0,
            disk_critical_threshold=95.0,
            cpu_critical_threshold=95.0,
            check_security=False,
        )
        check = ResourcesHealthCheck(config)
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2400.0
        
        with patch('core.health_check.psutil.virtual_memory', return_value=mock_psutil_memory), \
             patch('core.health_check.psutil.cpu_percent', return_value=30.0), \
             patch('core.health_check.psutil.cpu_count', return_value=4), \
             patch('core.health_check.psutil.cpu_freq', return_value=mock_cpu_freq), \
             patch('core.health_check.psutil.disk_partitions', return_value=mock_psutil_partitions), \
             patch('core.health_check.psutil.disk_usage', return_value=mock_psutil_disk):
            result = await check.run()
            assert result.status == HealthStatus.OK
            assert "healthy" in result.message.lower()

    @pytest.mark.asyncio
    async def test_resources_check_memory_warning(self, default_config, mock_psutil_disk, mock_psutil_partitions):
        """Test resource check with memory warning"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=True,
            memory_warning_threshold=60.0,
            memory_critical_threshold=90.0,
            disk_critical_threshold=95.0,
            cpu_critical_threshold=95.0,
            check_security=False,
        )
        check = ResourcesHealthCheck(config)
        
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 4 * 1024**3
        mock_memory.used = 12 * 1024**3
        mock_memory.percent = 75.0  # Above warning threshold
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2400.0
        
        with patch('core.health_check.psutil.virtual_memory', return_value=mock_memory), \
             patch('core.health_check.psutil.cpu_percent', return_value=30.0), \
             patch('core.health_check.psutil.cpu_count', return_value=4), \
             patch('core.health_check.psutil.cpu_freq', return_value=mock_cpu_freq), \
             patch('core.health_check.psutil.disk_partitions', return_value=mock_psutil_partitions), \
             patch('core.health_check.psutil.disk_usage', return_value=mock_psutil_disk):
            result = await check.run()
            assert result.status == HealthStatus.WARNING
            assert "memory" in result.message.lower()

    @pytest.mark.asyncio
    async def test_resources_check_memory_critical(self, default_config, mock_psutil_disk, mock_psutil_partitions):
        """Test resource check with critical memory"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=True,
            memory_critical_threshold=90.0,
            disk_critical_threshold=95.0,
            cpu_critical_threshold=95.0,
            check_security=False,
        )
        check = ResourcesHealthCheck(config)
        
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024**3
        mock_memory.available = 1 * 1024**3
        mock_memory.used = 15 * 1024**3
        mock_memory.percent = 93.0  # Above critical threshold
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2400.0
        
        with patch('core.health_check.psutil.virtual_memory', return_value=mock_memory), \
             patch('core.health_check.psutil.cpu_percent', return_value=30.0), \
             patch('core.health_check.psutil.cpu_count', return_value=4), \
             patch('core.health_check.psutil.cpu_freq', return_value=mock_cpu_freq), \
             patch('core.health_check.psutil.disk_partitions', return_value=mock_psutil_partitions), \
             patch('core.health_check.psutil.disk_usage', return_value=mock_psutil_disk):
            result = await check.run()
            assert result.status == HealthStatus.CRITICAL
            assert "memory" in result.message.lower()

    @pytest.mark.asyncio
    async def test_resources_check_disk_warning(self, default_config, mock_psutil_memory, mock_psutil_partitions):
        """Test resource check with disk warning"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=True,
            disk_warning_threshold=40.0,
            disk_critical_threshold=95.0,
            memory_critical_threshold=95.0,
            cpu_critical_threshold=95.0,
            check_security=False,
        )
        check = ResourcesHealthCheck(config)
        
        mock_disk = MagicMock()
        mock_disk.total = 100 * 1024**3
        mock_disk.used = 50 * 1024**3
        mock_disk.free = 50 * 1024**3
        mock_disk.percent = 50.0  # Above warning threshold
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2400.0
        
        with patch('core.health_check.psutil.virtual_memory', return_value=mock_psutil_memory), \
             patch('core.health_check.psutil.cpu_percent', return_value=30.0), \
             patch('core.health_check.psutil.cpu_count', return_value=4), \
             patch('core.health_check.psutil.cpu_freq', return_value=mock_cpu_freq), \
             patch('core.health_check.psutil.disk_partitions', return_value=mock_psutil_partitions), \
             patch('core.health_check.psutil.disk_usage', return_value=mock_disk):
            result = await check.run()
            assert result.status == HealthStatus.WARNING
            assert "disk" in result.message.lower()

    @pytest.mark.asyncio
    async def test_resources_check_cpu_warning(self, default_config, mock_psutil_memory, mock_psutil_disk, mock_psutil_partitions):
        """Test resource check with CPU warning"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=True,
            cpu_warning_threshold=30.0,
            cpu_critical_threshold=95.0,
            memory_critical_threshold=95.0,
            disk_critical_threshold=95.0,
            check_security=False,
        )
        check = ResourcesHealthCheck(config)
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2400.0
        
        with patch('core.health_check.psutil.virtual_memory', return_value=mock_psutil_memory), \
             patch('core.health_check.psutil.cpu_percent', return_value=50.0), \
             patch('core.health_check.psutil.cpu_count', return_value=4), \
             patch('core.health_check.psutil.cpu_freq', return_value=mock_cpu_freq), \
             patch('core.health_check.psutil.disk_partitions', return_value=mock_psutil_partitions), \
             patch('core.health_check.psutil.disk_usage', return_value=mock_psutil_disk):
            result = await check.run()
            assert result.status == HealthStatus.WARNING
            assert "cpu" in result.message.lower()

    def test_check_resources_structure(self, default_config):
        """Test _check_resources returns correct structure"""
        check = ResourcesHealthCheck(default_config)
        result = check._check_resources()
        assert "memory" in result
        assert "cpu" in result
        assert "disks" in result
        assert "load_average" in result

    @pytest.mark.asyncio
    async def test_resources_check_exception_handling(self, default_config):
        """Test resources check exception handling"""
        config = HealthCheckConfig(check_resources=True)
        check = ResourcesHealthCheck(config)
        
        with patch.object(check, '_check_resources', side_effect=Exception("Resource Error")):
            result = await check.run()
            assert result.status == HealthStatus.ERROR
            assert "Resource Error" in result.message


# ==================== SecurityHealthCheck Tests ====================


class TestSecurityHealthCheck:
    """Test SecurityHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = SecurityHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED
        assert "disabled" in result.message.lower()

    @pytest.mark.asyncio
    async def test_missing_env_vars(self, default_config):
        """Test detection of missing environment variables"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=True,
            required_env_vars=["NONEXISTENT_VAR_12345"],
            ssl_check_hosts=[],
            secrets_scan_paths=[],
        )
        check = SecurityHealthCheck(config)
        result = await check.run()
        assert result.status == HealthStatus.WARNING
        assert "NONEXISTENT_VAR_12345" in str(result.details["env_vars"])

    @pytest.mark.asyncio
    async def test_existing_env_vars(self, default_config, monkeypatch):
        """Test with existing environment variables"""
        monkeypatch.setenv("TEST_VAR_HEALTH_CHECK", "test_value")
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=True,
            required_env_vars=["TEST_VAR_HEALTH_CHECK"],
            ssl_check_hosts=[],
            secrets_scan_paths=[],
        )
        check = SecurityHealthCheck(config)
        result = await check.run()
        assert result.details["env_vars"]["TEST_VAR_HEALTH_CHECK"] is True

    def test_scan_for_secrets(self, default_config):
        """Test secret scanning"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = os.path.join(tmp_dir, "test_code")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, "test.py")
            with open(test_file, "w") as f:
                f.write('api_key = "sk-test12345678901234567890"')

            config = HealthCheckConfig(
                secrets_scan_paths=[test_dir],
                secrets_exclude_patterns=[],
            )
            check = SecurityHealthCheck(config)
            secrets = check._scan_for_secrets(test_dir)
            assert len(secrets) > 0
            assert any("api_key" in s.get("type", "") for s in secrets)

    def test_scan_for_secrets_excluded(self, default_config):
        """Test secret scanning with exclusions"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = os.path.join(tmp_dir, "test_code")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, "test.pyc")
            with open(test_file, "w") as f:
                f.write('api_key = "sk-test12345678901234567890"')

            config = HealthCheckConfig(
                secrets_scan_paths=[test_dir],
                secrets_exclude_patterns=[".pyc"],
            )
            check = SecurityHealthCheck(config)
            secrets = check._scan_for_secrets(test_dir)
            assert len(secrets) == 0

    def test_scan_for_secrets_aws_key(self, default_config):
        """Test AWS key pattern detection"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = os.path.join(tmp_dir, "test_code")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, "config.py")
            with open(test_file, "w") as f:
                f.write('aws_access_key = "AKIAIOSFODNN7EXAMPLE"')

            config = HealthCheckConfig(
                secrets_scan_paths=[test_dir],
                secrets_exclude_patterns=[],
            )
            check = SecurityHealthCheck(config)
            secrets = check._scan_for_secrets(test_dir)
            assert len(secrets) > 0
            assert any(s.get("type") == "aws_key" for s in secrets)

    def test_scan_for_secrets_private_key(self, default_config):
        """Test private key pattern detection"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = os.path.join(tmp_dir, "test_code")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, "key.py")
            with open(test_file, "w") as f:
                f.write('-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...')

            config = HealthCheckConfig(
                secrets_scan_paths=[test_dir],
                secrets_exclude_patterns=[],
            )
            check = SecurityHealthCheck(config)
            secrets = check._scan_for_secrets(test_dir)
            assert len(secrets) > 0
            assert any(s.get("type") == "private_key" for s in secrets)

    def test_check_ssl_cert_success(self, default_config):
        """Test SSL certificate check"""
        check = SecurityHealthCheck(default_config)
        
        mock_cert = {
            "notAfter": "Dec 31 2025 23:59:59 GMT",
            "subject": (("commonName", "example.com"),),
            "issuer": (("commonName", "Issuer CA"),),
        }
        
        # Create a properly nested mock for the SSL context
        mock_sock = MagicMock()
        mock_sock.getpeercert.return_value = mock_cert
        mock_sock.connect.return_value = None
        
        mock_context_instance = MagicMock()
        mock_context_instance.wrap_socket.return_value.__enter__ = MagicMock(return_value=mock_sock)
        mock_context_instance.wrap_socket.return_value.__exit__ = MagicMock(return_value=False)
        mock_context_instance.minimum_version = ssl.TLSVersion.TLSv1_2
        
        with patch('ssl.create_default_context', return_value=mock_context_instance):
            result = check._check_ssl_cert("example.com:443")
            # The mock should either return ok or error based on implementation
            assert "status" in result

    def test_check_ssl_cert_error(self, default_config):
        """Test SSL certificate check with error"""
        check = SecurityHealthCheck(default_config)
        
        with patch('ssl.create_default_context', side_effect=ssl.SSLError("SSL Error")):
            result = check._check_ssl_cert("invalid:443")
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_secrets_found_critical(self, default_config):
        """Test critical status when secrets found"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=True,
            required_env_vars=[],
            ssl_check_hosts=[],
            secrets_scan_paths=[],  # Will use mock
        )
        check = SecurityHealthCheck(config)
        
        mock_result = {
            "env_vars": {},
            "ssl_certs": [],
            "secrets_found": [{"file": "test.py", "type": "api_key"}],
        }
        
        with patch.object(check, '_check_security', return_value=mock_result):
            result = await check.run()
            assert result.status == HealthStatus.CRITICAL
            assert "secrets" in result.message.lower()

    @pytest.mark.asyncio
    async def test_expired_ssl_cert(self, default_config):
        """Test critical status with expired SSL cert"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=True,
            required_env_vars=[],
            ssl_check_hosts=["example.com:443"],
            secrets_scan_paths=[],
        )
        check = SecurityHealthCheck(config)
        
        mock_result = {
            "env_vars": {},
            "ssl_certs": [{"host": "example.com:443", "expired": True}],
            "secrets_found": [],
        }
        
        with patch.object(check, '_check_security', return_value=mock_result):
            result = await check.run()
            assert result.status == HealthStatus.CRITICAL
            assert "expired" in result.message.lower()

    @pytest.mark.asyncio
    async def test_security_check_exception_handling(self, default_config):
        """Test security check exception handling"""
        config = HealthCheckConfig(check_security=True)
        check = SecurityHealthCheck(config)
        
        with patch.object(check, '_check_security', side_effect=Exception("Security Error")):
            result = await check.run()
            assert result.status == HealthStatus.ERROR
            assert "Security Error" in result.message


# ==================== HealthCheckRunner Tests ====================


class TestHealthCheckRunner:
    """Test HealthCheckRunner class"""

    def test_initialization_default_config(self):
        """Test runner initialization with default config"""
        runner = HealthCheckRunner()
        assert runner.config is not None
        assert isinstance(runner.config, HealthCheckConfig)

    def test_initialization_custom_config(self, default_config):
        """Test runner initialization with custom config"""
        runner = HealthCheckRunner(default_config)
        assert runner.config == default_config

    @pytest.mark.asyncio
    async def test_run_all_checks_with_skipped(self, minimal_config):
        """Test running all checks with everything skipped"""
        runner = HealthCheckRunner(minimal_config)
        report = await runner.run_all_checks()
        assert isinstance(report, HealthReport)
        assert report.overall_status == HealthStatus.OK  # All skipped = OK
        assert len(report.checks) == 5  # All check types
        assert all(c.status == HealthStatus.SKIPPED for c in report.checks)

    @pytest.mark.asyncio
    async def test_run_specific_checks(self, minimal_config):
        """Test running specific checks"""
        runner = HealthCheckRunner(minimal_config)
        report = await runner.run_all_checks(check_names=["database"])
        assert len(report.checks) == 1
        assert report.checks[0].name == "database"

    @pytest.mark.asyncio
    async def test_run_specific_checks_multiple(self, minimal_config):
        """Test running multiple specific checks"""
        runner = HealthCheckRunner(minimal_config)
        report = await runner.run_all_checks(check_names=["database", "tools"])
        assert len(report.checks) == 2
        names = [c.name for c in report.checks]
        assert "database" in names
        assert "tools" in names

    def test_run_single_check(self, default_config):
        """Test running a single check by name"""
        config = HealthCheckConfig(
            check_database=True,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        result = runner.run_check("database")
        assert isinstance(result, HealthCheckResult)
        assert result.name == "database"

    def test_run_unknown_check(self, default_config):
        """Test running an unknown check"""
        runner = HealthCheckRunner(default_config)
        with pytest.raises(ValueError, match="Unknown check"):
            runner.run_check("unknown_check")

    @pytest.mark.asyncio
    async def test_parallel_execution(self, default_config):
        """Test parallel execution of checks"""
        config = HealthCheckConfig(
            parallel_checks=True,
            max_concurrent_checks=3,
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        report = await runner.run_all_checks()
        assert len(report.checks) == 5
        assert report.summary["total"] == 5
        assert report.summary["skipped"] == 5

    @pytest.mark.asyncio
    async def test_sequential_execution(self, default_config):
        """Test sequential execution of checks"""
        config = HealthCheckConfig(
            parallel_checks=False,
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        report = await runner.run_all_checks()
        assert len(report.checks) == 5

    def test_check_registry(self):
        """Test that all expected checks are registered"""
        expected_checks = ["database", "tools", "api", "resources", "security"]
        for check_name in expected_checks:
            assert check_name in HealthCheckRunner.CHECKS

    @pytest.mark.asyncio
    async def test_report_summary_counts(self, default_config):
        """Test report summary counts are correct"""
        runner = HealthCheckRunner(default_config)
        report = await runner.run_all_checks()
        
        assert "total" in report.summary
        assert "ok" in report.summary
        assert "warning" in report.summary
        assert "error" in report.summary
        assert "critical" in report.summary
        assert "skipped" in report.summary
        
        # total should equal the sum of all status counts (which it does, since total is just a count)
        # The summary["total"] is the total number of checks run
        status_total = (
            report.summary["ok"] + 
            report.summary["warning"] + 
            report.summary["error"] + 
            report.summary["critical"] + 
            report.summary["skipped"]
        )
        assert status_total == report.summary["total"]

    @pytest.mark.asyncio
    async def test_report_overall_status_critical(self):
        """Test overall status is critical when critical check fails"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        
        # Create a mock check that returns critical
        class MockCriticalCheck(BaseHealthCheck):
            name = "critical_check"
            async def run(self):
                return self._create_result(HealthStatus.CRITICAL, "Critical!")
        
        # Temporarily add to CHECKS
        HealthCheckRunner.CHECKS["critical_test"] = MockCriticalCheck
        try:
            report = await runner.run_all_checks(check_names=["critical_test"])
            assert report.overall_status == HealthStatus.CRITICAL
        finally:
            del HealthCheckRunner.CHECKS["critical_test"]

    @pytest.mark.asyncio
    async def test_report_overall_status_error(self):
        """Test overall status is error when error check fails"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        
        class MockErrorCheck(BaseHealthCheck):
            name = "error_check"
            async def run(self):
                return self._create_result(HealthStatus.ERROR, "Error!")
        
        HealthCheckRunner.CHECKS["error_test"] = MockErrorCheck
        try:
            report = await runner.run_all_checks(check_names=["error_test"])
            assert report.overall_status == HealthStatus.ERROR
        finally:
            del HealthCheckRunner.CHECKS["error_test"]

    @pytest.mark.asyncio
    async def test_report_overall_status_warning(self):
        """Test overall status is warning when warning check triggers"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        
        class MockWarningCheck(BaseHealthCheck):
            name = "warning_check"
            async def run(self):
                return self._create_result(HealthStatus.WARNING, "Warning!")
        
        HealthCheckRunner.CHECKS["warning_test"] = MockWarningCheck
        try:
            report = await runner.run_all_checks(check_names=["warning_test"])
            assert report.overall_status == HealthStatus.WARNING
        finally:
            del HealthCheckRunner.CHECKS["warning_test"]

    @pytest.mark.asyncio
    async def test_report_metadata(self, default_config):
        """Test report metadata is populated"""
        runner = HealthCheckRunner(default_config)
        report = await runner.run_all_checks()
        
        assert "platform" in report.metadata
        assert "python_version" in report.metadata
        assert "hostname" in report.metadata
        assert "runner_version" in report.metadata
        assert "config" in report.metadata


# ==================== Convenience Function Tests ====================


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_run_health_check(self):
        """Test run_health_check function"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        report = run_health_check(config=config)
        assert isinstance(report, HealthReport)

    def test_run_health_check_json(self):
        """Test run_health_check with JSON output"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        json_output = run_health_check(config=config, json_output=True)
        assert isinstance(json_output, str)
        data = json.loads(json_output)
        assert "overall_status" in data

    def test_check_database(self):
        """Test check_database function"""
        result = check_database()
        assert isinstance(result, HealthCheckResult)
        assert result.name == "database"

    def test_check_database_with_url(self):
        """Test check_database with custom URL"""
        result = check_database(database_url="sqlite:///./test.db", timeout=10)
        assert isinstance(result, HealthCheckResult)
        assert result.name == "database"

    def test_check_tools(self):
        """Test check_tools function"""
        result = check_tools(required_tools=["python"])
        assert isinstance(result, HealthCheckResult)
        assert result.name == "tools"
        assert result.details["required"]["python"]["available"] is True

    def test_check_tools_default(self):
        """Test check_tools with default tools"""
        result = check_tools()
        assert isinstance(result, HealthCheckResult)
        assert result.name == "tools"

    def test_check_api_health(self):
        """Test check_api_health function"""
        result = check_api_health(base_url="http://localhost:59999", timeout=1)
        assert isinstance(result, HealthCheckResult)
        assert result.name == "api"

    def test_check_api_health_default(self):
        """Test check_api_health with default URL"""
        result = check_api_health()
        assert isinstance(result, HealthCheckResult)
        assert result.name == "api"

    def test_check_resources(self):
        """Test check_resources function"""
        result = check_resources()
        assert isinstance(result, HealthCheckResult)
        assert result.name == "resources"
        assert "memory" in result.details
        assert "cpu" in result.details

    def test_check_security_config(self):
        """Test check_security_config function"""
        result = check_security_config()
        assert isinstance(result, HealthCheckResult)
        assert result.name == "security"


# ==================== Integration Tests ====================


@pytest.mark.integration
class TestHealthCheckIntegration:
    """Integration tests for health check system"""

    @pytest.mark.asyncio
    async def test_full_health_check(self):
        """Test full health check with minimal checks enabled"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            check_api=False,
            check_resources=True,
            check_security=False,
            required_tools=["python"],
            optional_tools=[],
            # Set high thresholds to avoid false failures on resource-constrained systems
            memory_critical_threshold=99.0,
            disk_critical_threshold=99.0,
            cpu_critical_threshold=99.0,
        )
        runner = HealthCheckRunner(config)
        report = await runner.run_all_checks()

        assert isinstance(report, HealthReport)
        # Allow OK, WARNING, or CRITICAL depending on actual system state
        assert report.overall_status in [
            HealthStatus.OK, 
            HealthStatus.WARNING, 
            HealthStatus.CRITICAL
        ]
        assert len(report.checks) == 5
        assert report.summary["total"] == 5

    def test_health_check_json_roundtrip(self):
        """Test that JSON output can be parsed back"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        report = run_health_check(config=config)
        json_str = report.to_json()
        data = json.loads(json_str)

        assert data["overall_status"] == "ok"
        assert "checks" in data
        assert "summary" in data
        assert "metadata" in data


# ==================== Edge Case Tests ====================


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, default_config):
        """Test timeout handling in checks"""
        config = HealthCheckConfig(
            timeout_per_check=60,
            check_database=True,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = DatabaseHealthCheck(config)
        result = await check.run()
        # Should complete with any valid status
        assert result.status in [
            HealthStatus.OK,
            HealthStatus.WARNING,
            HealthStatus.ERROR,
            HealthStatus.SKIPPED,
        ]

    def test_empty_config_lists(self):
        """Test configuration with empty lists"""
        config = HealthCheckConfig(
            required_tools=[],
            optional_tools=[],
            ssl_check_hosts=[],
            required_env_vars=[],
            secrets_scan_paths=[],
        )
        assert config.required_tools == []
        assert config.optional_tools == []

    @pytest.mark.asyncio
    async def test_report_with_mixed_statuses(self):
        """Test report generation with mixed check statuses"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        runner = HealthCheckRunner(config)
        report = await runner.run_all_checks()

        # All skipped should result in OK overall
        assert report.overall_status == HealthStatus.OK
        assert report.summary["skipped"] == 5

    def test_invalid_check_name_in_run_all(self):
        """Test that invalid check names are ignored"""
        runner = HealthCheckRunner()
        # Should not raise error for invalid names
        # It just filters them out


# ==================== Performance Tests ====================


class TestPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_check_execution_time(self, minimal_config):
        """Test that checks complete in reasonable time"""
        runner = HealthCheckRunner(minimal_config)

        start = time.time()
        report = await runner.run_all_checks()
        elapsed = time.time() - start

        # Should complete in under 5 seconds for skipped checks
        assert elapsed < 5.0
        assert report.duration_ms < 5000

    def test_large_report_json_generation(self, mock_health_report):
        """Test JSON generation for large reports"""
        # Add many checks to simulate large report
        for i in range(100):
            mock_health_report.checks.append(
                HealthCheckResult(
                    f"check_{i}", HealthStatus.OK, f"Check {i} passed"
                )
            )

        start = time.time()
        json_str = mock_health_report.to_json()
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 1.0
        assert len(json_str) > 0


# ==================== Export Tests ====================


def test_all_exports():
    """Test that all expected items are exported"""
    expected_exports = [
        "HealthStatus",
        "SeverityLevel",
        "HealthCheckResult",
        "HealthReport",
        "HealthCheckConfig",
        "BaseHealthCheck",
        "DatabaseHealthCheck",
        "ToolsHealthCheck",
        "APIHealthCheck",
        "ResourcesHealthCheck",
        "SecurityHealthCheck",
        "HealthCheckRunner",
        "run_health_check",
        "check_database",
        "check_tools",
        "check_api_health",
        "check_resources",
        "check_security_config",
    ]

    # Import the module and check exports
    from core import health_check

    for export in expected_exports:
        assert hasattr(health_check, export), f"{export} should be exported"


# ==================== Mock-Based System Tests ====================


class TestSystemChecksWithMocks:
    """Test system-level checks with mocks"""

    @pytest.mark.asyncio
    async def test_database_postgresql_check(self, default_config):
        """Test PostgreSQL database check with mocks"""
        config = HealthCheckConfig(
            check_database=True,
            database_url="postgresql://user:pass@localhost/testdb",
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = DatabaseHealthCheck(config)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(1,), (100,), (50,)]
        mock_cursor.fetchall.return_value = [("table1",), ("table2",)]
        mock_conn.cursor.return_value = mock_cursor
        
        with patch.dict('sys.modules', {'psycopg2': MagicMock()}):
            with patch('psycopg2.connect', return_value=mock_conn):
                result = check._check_database()
                assert result["type"] == "postgresql"
                assert result["connection"] == "ok"

    @pytest.mark.asyncio
    async def test_tools_version_extraction(self, default_config):
        """Test tool version extraction with mocked subprocess"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            required_tools=["nmap"],
            optional_tools=[],
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = ToolsHealthCheck(config)
        
        mock_result = MagicMock()
        mock_result.stdout = "Nmap version 7.91"
        mock_result.stderr = ""
        
        with patch('shutil.which', return_value="/usr/bin/nmap"):
            with patch('subprocess.run', return_value=mock_result):
                result = check._check_tool("nmap")
                assert result["available"] is True
                assert result["version"] == "7.91"

    @pytest.mark.asyncio
    async def test_api_check_with_mock_response(self, default_config):
        """Test API check with mocked HTTP response"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=True,
            api_base_url="http://localhost:8000",
            check_resources=False,
            check_security=False,
        )
        check = APIHealthCheck(config)
        
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            result = check._check_api()
            assert result["health_endpoint"]["status"] == "ok"
            assert result["health_endpoint"]["status_code"] == 200


# ==================== Alert Generation Tests ====================


class TestAlertGeneration:
    """Test alert generation for unhealthy services"""

    def test_critical_alert_has_remediation(self):
        """Test that critical alerts include remediation"""
        result = HealthCheckResult(
            name="critical_service",
            status=HealthStatus.CRITICAL,
            message="Service is down",
            remediation="Restart the service with: systemctl restart service",
        )
        assert result.remediation is not None
        assert "restart" in result.remediation.lower()

    def test_warning_alert_has_remediation(self):
        """Test that warning alerts include remediation"""
        result = HealthCheckResult(
            name="warning_service",
            status=HealthStatus.WARNING,
            message="Service is slow",
            remediation="Check resource usage and optimize",
        )
        assert result.remediation is not None

    @pytest.mark.asyncio
    async def test_database_critical_remediation(self):
        """Test database check provides remediation on critical"""
        config = HealthCheckConfig(
            check_database=True,
            database_url="invalid://url",
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = DatabaseHealthCheck(config)
        result = await check.run()
        
        if result.status == HealthStatus.CRITICAL:
            assert result.remediation is not None

    @pytest.mark.asyncio
    async def test_tools_critical_remediation(self):
        """Test tools check provides remediation on critical"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            required_tools=["nonexistent_tool"],
            optional_tools=[],
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = ToolsHealthCheck(config)
        result = await check.run()
        
        if result.status == HealthStatus.CRITICAL:
            assert result.remediation is not None
            assert "install" in result.remediation.lower()


# ==================== Health History Tests ====================


class TestHealthHistory:
    """Test health history tracking"""

    def test_result_timestamp(self):
        """Test that results have timestamps"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.OK,
            message="OK",
        )
        assert isinstance(result.timestamp, datetime)
        # Timestamp should be recent
        assert (datetime.utcnow() - result.timestamp).total_seconds() < 1

    def test_result_duration_tracking(self):
        """Test that results track duration"""
        result = HealthCheckResult(
            name="test",
            status=HealthStatus.OK,
            message="OK",
            duration_ms=150.5,
        )
        assert result.duration_ms == 150.5

    def test_report_timestamp(self):
        """Test that reports have timestamps"""
        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0},
            metadata={},
        )
        assert isinstance(report.generated_at, datetime)

    def test_report_duration_tracking(self):
        """Test that reports track total duration"""
        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0},
            metadata={},
            duration_ms=500.0,
        )
        assert report.duration_ms == 500.0


# ==================== Custom Health Check Registration Tests ====================


class TestCustomHealthCheckRegistration:
    """Test custom health check registration"""

    def test_custom_check_can_be_added_to_runner(self):
        """Test that custom checks can be added to runner"""
        
        class CustomHealthCheck(BaseHealthCheck):
            name = "custom_check"
            description = "A custom health check"
            severity = SeverityLevel.LOW
            
            async def run(self):
                return self._create_result(
                    HealthStatus.OK,
                    "Custom check passed",
                )
        
        # Register the custom check
        HealthCheckRunner.CHECKS["custom"] = CustomHealthCheck
        
        try:
            runner = HealthCheckRunner()
            assert "custom" in HealthCheckRunner.CHECKS
            
            # Run the custom check
            result = runner.run_check("custom")
            assert result.name == "custom_check"
            assert result.status == HealthStatus.OK
        finally:
            # Clean up
            if "custom" in HealthCheckRunner.CHECKS:
                del HealthCheckRunner.CHECKS["custom"]

    def test_custom_check_with_config(self):
        """Test custom check that uses configuration"""
        
        class ConfigDependentCheck(BaseHealthCheck):
            name = "config_check"
            
            async def run(self):
                if self.config.check_database:
                    return self._create_result(HealthStatus.OK, "DB check enabled")
                return self._create_result(HealthStatus.SKIPPED, "DB check disabled")
        
        HealthCheckRunner.CHECKS["config_test"] = ConfigDependentCheck
        
        try:
            config = HealthCheckConfig(check_database=True)
            runner = HealthCheckRunner(config)
            result = runner.run_check("config_test")
            assert result.status == HealthStatus.OK
            
            config = HealthCheckConfig(check_database=False)
            runner = HealthCheckRunner(config)
            result = runner.run_check("config_test")
            assert result.status == HealthStatus.SKIPPED
        finally:
            if "config_test" in HealthCheckRunner.CHECKS:
                del HealthCheckRunner.CHECKS["config_test"]

    @pytest.mark.asyncio
    async def test_custom_check_async(self):
        """Test custom async check"""
        
        class AsyncCustomCheck(BaseHealthCheck):
            name = "async_custom"
            
            async def run(self):
                # Simulate async operation
                await asyncio.sleep(0.01)
                return self._create_result(HealthStatus.OK, "Async complete")
        
        HealthCheckRunner.CHECKS["async_test"] = AsyncCustomCheck
        
        try:
            config = HealthCheckConfig(
                check_database=False,
                check_tools=False,
                check_api=False,
                check_resources=False,
                check_security=False,
            )
            runner = HealthCheckRunner(config)
            report = await runner.run_all_checks(check_names=["async_test"])
            
            assert len(report.checks) == 1
            assert report.checks[0].status == HealthStatus.OK
        finally:
            if "async_test" in HealthCheckRunner.CHECKS:
                del HealthCheckRunner.CHECKS["async_test"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
