"""
Comprehensive tests for core/health_check.py - Health Check System

Tests all health check functionality including:
- Configuration validation
- Individual health checks (database, tools, API, resources, security)
- Health check runner
- Report generation
- JSON output

Target: 80%+ coverage for core/health_check.py
"""

import json
import os
import ssl
import sys
import time
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

# Ensure the core module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        summary={"total": 2, "ok": 1, "warning": 1, "error": 0, "critical": 0, "skipped": 0},
        metadata={},
    )


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

    def test_to_json(self, mock_health_report):
        """Test report to JSON conversion"""
        json_str = mock_health_report.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["overall_status"] == "ok"
        assert "checks" in data
        assert "summary" in data


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

    def test_custom_values(self):
        """Test custom configuration values"""
        config = HealthCheckConfig(
            check_database=False,
            database_timeout=10,
            memory_warning_threshold=70.0,
        )
        assert config.check_database is False
        assert config.database_timeout == 10
        assert config.memory_warning_threshold == 70.0

    def test_validation_timeout_range(self):
        """Test timeout validation"""
        with pytest.raises(ValueError):
            HealthCheckConfig(database_timeout=0)
        with pytest.raises(ValueError):
            HealthCheckConfig(database_timeout=61)

    def test_validation_threshold_range(self):
        """Test threshold percentage validation"""
        with pytest.raises(ValueError):
            HealthCheckConfig(memory_warning_threshold=101)
        with pytest.raises(ValueError):
            HealthCheckConfig(memory_warning_threshold=-1)

    def test_tool_string_parsing(self):
        """Test tool string parsing"""
        config = HealthCheckConfig(required_tools="nmap,sqlmap,nuclei")
        assert config.required_tools == ["nmap", "sqlmap", "nuclei"]

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            HealthCheckConfig(invalid_field=True)


# ==================== BaseHealthCheck Tests ====================


class TestBaseHealthCheck:
    """Test BaseHealthCheck class"""

    def test_initialization(self, default_config):
        """Test base check initialization"""
        check = BaseHealthCheck(default_config)
        assert check.config == default_config
        assert check.name == "base_check"
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

    def test_run_not_implemented(self, default_config):
        """Test that run() raises NotImplementedError"""
        check = BaseHealthCheck(default_config)
        with pytest.raises(NotImplementedError):
            # Note: This would need async context
            import asyncio

            asyncio.run(check.run())


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

    @pytest.mark.asyncio
    async def test_sqlite_check(self, default_config):
        """Test SQLite database check"""
        import tempfile

        # Create a temporary SQLite database
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
            # Should succeed with empty/new database
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

    def test_check_database_method(self, default_config):
        """Test internal _check_database method"""
        check = DatabaseHealthCheck(default_config)
        # This should not raise an exception
        result = check._check_database()
        assert "connection" in result
        assert "type" in result


# ==================== ToolsHealthCheck Tests ====================


class TestToolsHealthCheck:
    """Test ToolsHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = ToolsHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_tools_check(self, default_config):
        """Test tool availability check"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=True,
            required_tools=["python"],  # python should always be available
            optional_tools=["nonexistent_tool_12345"],
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = ToolsHealthCheck(config)
        result = await check.run()
        # Python should be available - status can be OK or WARNING
        assert result.status in [HealthStatus.OK, HealthStatus.WARNING]
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

    def test_check_tool(self, default_config):
        """Test individual tool checking"""
        check = ToolsHealthCheck(default_config)
        result = check._check_tool("python")
        assert result["available"] is True
        assert result["path"] is not None

        result = check._check_tool("nonexistent_tool_12345")
        assert result["available"] is False


# ==================== APIHealthCheck Tests ====================


class TestAPIHealthCheck:
    """Test APIHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = APIHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_api_unavailable(self, default_config):
        """Test API check when API is unavailable"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=True,
            api_base_url="http://localhost:59999",  # Unlikely to be used
            api_timeout=1,
            check_resources=False,
            check_security=False,
        )
        check = APIHealthCheck(config)
        result = await check.run()
        # Should detect that API is not available
        assert result.status in [HealthStatus.CRITICAL, HealthStatus.ERROR]
        assert "error" in result.message.lower() or "failed" in result.message.lower()


# ==================== ResourcesHealthCheck Tests ====================


class TestResourcesHealthCheck:
    """Test ResourcesHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = ResourcesHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_resources_check(self, default_config):
        """Test resource check"""
        config = HealthCheckConfig(
            check_database=False,
            check_tools=False,
            check_api=False,
            check_resources=True,
            memory_critical_threshold=99.9,  # Set high to avoid critical
            disk_critical_threshold=99.9,
            cpu_critical_threshold=99.9,
            check_security=False,
        )
        check = ResourcesHealthCheck(config)
        result = await check.run()
        assert result.status in [HealthStatus.OK, HealthStatus.WARNING]
        assert "memory" in result.details
        assert "cpu" in result.details
        assert "disks" in result.details

    def test_check_resources_method(self, default_config):
        """Test internal _check_resources method"""
        check = ResourcesHealthCheck(default_config)
        result = check._check_resources()
        assert "memory" in result
        assert "cpu" in result
        assert "disks" in result
        assert isinstance(result["memory"]["total_gb"], float)
        assert isinstance(result["cpu"]["percent"], float)


# ==================== SecurityHealthCheck Tests ====================


class TestSecurityHealthCheck:
    """Test SecurityHealthCheck class"""

    @pytest.mark.asyncio
    async def test_skipped_when_disabled(self, minimal_config):
        """Test that check is skipped when disabled"""
        check = SecurityHealthCheck(minimal_config)
        result = await check.run()
        assert result.status == HealthStatus.SKIPPED

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
            ssl_check_hosts=[],  # Skip SSL checks for this test
            secrets_scan_paths=[],  # Skip secrets scan for this test
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
        import tempfile
        import os

        # Create a test directory and file with a potential secret
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
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = os.path.join(tmp_dir, "test_code")
            os.makedirs(test_dir, exist_ok=True)
            test_file = os.path.join(test_dir, "test.pyc")  # Should be excluded
            with open(test_file, "w") as f:
                f.write('api_key = "sk-test12345678901234567890"')

            config = HealthCheckConfig(
                secrets_scan_paths=[test_dir],
                secrets_exclude_patterns=[".pyc"],
            )
            check = SecurityHealthCheck(config)
            secrets = check._scan_for_secrets(test_dir)
            assert len(secrets) == 0


# ==================== HealthCheckRunner Tests ====================


class TestHealthCheckRunner:
    """Test HealthCheckRunner class"""

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

    def test_check_tools(self):
        """Test check_tools function"""
        result = check_tools(required_tools=["python"])
        assert isinstance(result, HealthCheckResult)
        assert result.name == "tools"
        assert result.details["required"]["python"]["available"] is True

    def test_check_api_health(self):
        """Test check_api_health function"""
        result = check_api_health(base_url="http://localhost:59999", timeout=1)
        assert isinstance(result, HealthCheckResult)
        assert result.name == "api"

    def test_check_resources(self):
        """Test check_resources function"""
        result = check_resources()
        assert isinstance(result, HealthCheckResult)
        assert result.name == "resources"
        assert "memory" in result.details

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
            check_database=False,  # Skip DB to avoid dependency
            check_tools=True,
            check_api=False,  # Skip API to avoid needing server
            check_resources=True,
            check_security=False,  # Skip security to avoid env var issues
            required_tools=["python"],
            optional_tools=[],  # No optional tools to avoid warnings
        )
        runner = HealthCheckRunner(config)
        report = await runner.run_all_checks()

        assert isinstance(report, HealthReport)
        assert report.overall_status in [HealthStatus.OK, HealthStatus.WARNING]
        assert len(report.checks) == 5
        assert report.summary["total"] == 5

        # Check that we got meaningful results for enabled checks
        tools_check = next(c for c in report.checks if c.name == "tools")
        resources_check = next(c for c in report.checks if c.name == "resources")

        # Tools check should be OK since python is required and available
        assert tools_check.status == HealthStatus.OK
        assert resources_check.status in [HealthStatus.OK, HealthStatus.WARNING]

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
            timeout_per_check=60,  # Use reasonable timeout for test
            check_database=True,
            check_tools=False,
            check_api=False,
            check_resources=False,
            check_security=False,
        )
        check = DatabaseHealthCheck(config)
        result = await check.run()
        # Should complete with any valid status
        assert result.status in [HealthStatus.OK, HealthStatus.WARNING, HealthStatus.ERROR, HealthStatus.SKIPPED]

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
                HealthCheckResult(f"check_{i}", HealthStatus.OK, f"Check {i} passed")
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
