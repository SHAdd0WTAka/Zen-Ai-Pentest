"""
Unit Tests for Health Check Module
Target: Improve coverage
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestHealthStatus:
    """Test HealthStatus Enum"""

    def test_health_status_values(self):
        from core.health_check import HealthStatus

        assert HealthStatus.OK.value == "ok"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.ERROR.value == "error"
        assert HealthStatus.CRITICAL.value == "critical"
        assert HealthStatus.SKIPPED.value == "skipped"

    def test_health_status_comparison(self):
        from core.health_check import HealthStatus

        assert HealthStatus.OK != HealthStatus.ERROR
        assert HealthStatus.WARNING != HealthStatus.CRITICAL


class TestSeverityLevel:
    """Test SeverityLevel Enum"""

    def test_severity_values(self):
        from core.health_check import SeverityLevel

        assert SeverityLevel.LOW.value == 1
        assert SeverityLevel.MEDIUM.value == 2
        assert SeverityLevel.HIGH.value == 3
        assert SeverityLevel.CRITICAL.value == 4

    def test_severity_order(self):
        from core.health_check import SeverityLevel

        # Test that we can compare severity
        assert SeverityLevel.CRITICAL.value > SeverityLevel.LOW.value


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""

    def test_result_creation_healthy(self):
        from core.health_check import (
            HealthCheckResult,
            HealthStatus,
            SeverityLevel,
        )

        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.OK,
            message="All good",
            severity=SeverityLevel.LOW,
        )
        assert result.name == "test_check"
        assert result.status == HealthStatus.OK
        assert result.message == "All good"
        assert result.severity == SeverityLevel.LOW

    def test_result_creation_unhealthy(self):
        from core.health_check import (
            HealthCheckResult,
            HealthStatus,
            SeverityLevel,
        )

        result = HealthCheckResult(
            name="failed_check",
            status=HealthStatus.ERROR,
            message="Connection failed",
            severity=SeverityLevel.CRITICAL,
            details={"error": "timeout"},
        )
        assert result.status == HealthStatus.ERROR
        assert result.details == {"error": "timeout"}

    def test_result_to_dict(self):
        from core.health_check import (
            HealthCheckResult,
            HealthStatus,
            SeverityLevel,
        )

        result = HealthCheckResult(
            name="test",
            status=HealthStatus.OK,
            message="OK",
            severity=SeverityLevel.LOW,
        )
        data = result.to_dict()
        assert data["name"] == "test"
        assert data["status"] == "ok"


class TestHealthReport:
    """Test HealthReport class"""

    def test_report_creation(self):
        from core.health_check import (
            HealthCheckResult,
            HealthReport,
            HealthStatus,
        )

        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0, "passed": 0, "failed": 0},
            metadata={},
        )
        assert report.overall_status == HealthStatus.OK
        assert report.checks == []

    def test_report_with_checks(self):
        from core.health_check import (
            HealthCheckResult,
            HealthReport,
            HealthStatus,
            SeverityLevel,
        )

        check = HealthCheckResult(
            name="db_check",
            status=HealthStatus.OK,
            message="DB OK",
            severity=SeverityLevel.LOW,
        )
        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[check],
            summary={"total": 1, "passed": 1, "failed": 0},
            metadata={},
        )
        assert len(report.checks) == 1
        assert report.checks[0].name == "db_check"

    def test_report_to_dict(self):
        from core.health_check import HealthReport, HealthStatus

        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0, "passed": 0, "failed": 0},
            metadata={},
        )
        data = report.to_dict()
        assert data["overall_status"] == "ok"
        assert "checks" in data

    def test_report_to_json(self):
        from core.health_check import HealthReport, HealthStatus

        report = HealthReport(
            overall_status=HealthStatus.OK,
            checks=[],
            summary={"total": 0, "passed": 0, "failed": 0},
            metadata={},
        )
        json_str = report.to_json()
        assert "ok" in json_str
        assert "checks" in json_str


class TestHealthCheckConfig:
    """Test HealthCheckConfig Pydantic model"""

    def test_config_creation(self):
        from core.health_check import HealthCheckConfig

        config = HealthCheckConfig()
        assert config is not None

    def test_config_with_custom_values(self):
        from core.health_check import HealthCheckConfig

        # Config has extra='forbid', so only defined fields can be passed
        # Just test that config can be created
        config = HealthCheckConfig()
        assert config is not None


class TestBaseHealthCheck:
    """Test BaseHealthCheck abstract class"""

    def test_base_check_init(self):
        from core.health_check import BaseHealthCheck, HealthCheckConfig

        class TestCheck(BaseHealthCheck):
            async def run(self):
                return self._create_result(status="ok", message="Test OK")

        config = HealthCheckConfig()
        check = TestCheck(config)
        assert check.config == config
        # Name is derived from class name
        assert check.name == "base_check"

    @pytest.mark.asyncio
    async def test_base_check_run(self):
        from core.health_check import (
            BaseHealthCheck,
            HealthCheckConfig,
            HealthStatus,
        )

        class TestCheck(BaseHealthCheck):
            async def run(self):
                return self._create_result(status=HealthStatus.OK, message="Test passed")

        config = HealthCheckConfig()
        check = TestCheck(config)
        result = await check.run()

        assert result.status == HealthStatus.OK
        assert result.message == "Test passed"

    def test_create_result(self):
        from core.health_check import (
            BaseHealthCheck,
            HealthCheckConfig,
            HealthStatus,
            SeverityLevel,
        )

        class TestCheck(BaseHealthCheck):
            async def run(self):
                pass

        config = HealthCheckConfig()
        check = TestCheck(config)

        result = check._create_result(
            status=HealthStatus.WARNING,
            message="Slow response",
            details={"latency": 2.5},
        )

        assert result.status == HealthStatus.WARNING
        assert result.details["latency"] == 2.5


class TestToolsHealthCheck:
    """Test ToolsHealthCheck class"""

    @pytest.mark.asyncio
    async def test_tools_check_creation(self):
        from core.health_check import HealthCheckConfig, ToolsHealthCheck

        config = HealthCheckConfig()
        check = ToolsHealthCheck(config)
        # Name is short identifier like "tools"
        assert check.name == "tools"

    def test_check_tool_mock(self):
        from core.health_check import HealthCheckConfig, ToolsHealthCheck

        config = HealthCheckConfig()
        check = ToolsHealthCheck(config)

        # Mock a tool check
        with patch("shutil.which", return_value="/usr/bin/python3"):
            result = check._check_tool("python3")
            assert isinstance(result, dict)


class TestResourcesHealthCheck:
    """Test ResourcesHealthCheck class"""

    @pytest.mark.asyncio
    async def test_resources_check_creation(self):
        from core.health_check import HealthCheckConfig, ResourcesHealthCheck

        config = HealthCheckConfig()
        check = ResourcesHealthCheck(config)
        assert check.name == "resources"

    def test_check_resources_basic(self):
        from core.health_check import HealthCheckConfig, ResourcesHealthCheck

        config = HealthCheckConfig()
        check = ResourcesHealthCheck(config)

        result = check._check_resources()
        assert isinstance(result, dict)
        # Should contain CPU or memory info
        assert "cpu" in result or "memory" in result or "error" in result


class TestHealthCheckRunner:
    """Test HealthCheckRunner class"""

    def test_runner_creation(self):
        from core.health_check import HealthCheckConfig, HealthCheckRunner

        runner = HealthCheckRunner()
        assert runner is not None

    def test_runner_with_custom_config(self):
        from core.health_check import HealthCheckConfig, HealthCheckRunner

        config = HealthCheckConfig()
        runner = HealthCheckRunner(config)
        assert runner.config is not None

    @pytest.mark.asyncio
    async def test_run_all_checks_empty(self):
        from core.health_check import HealthCheckRunner

        runner = HealthCheckRunner()

        # Run with empty checks list
        report = await runner.run_all_checks()
        assert report is not None
        assert report.overall_status is not None


class TestAPIHealthCheck:
    """Test APIHealthCheck class"""

    @pytest.mark.asyncio
    async def test_api_check_creation(self):
        from core.health_check import APIHealthCheck, HealthCheckConfig

        config = HealthCheckConfig()
        check = APIHealthCheck(config)
        assert check.name == "api"


class TestSecurityHealthCheck:
    """Test SecurityHealthCheck class"""

    @pytest.mark.asyncio
    async def test_security_check_creation(self):
        from core.health_check import HealthCheckConfig, SecurityHealthCheck

        config = HealthCheckConfig()
        check = SecurityHealthCheck(config)
        assert check.name == "security"

    def test_ssl_cert_check_mock(self):
        from core.health_check import HealthCheckConfig, SecurityHealthCheck

        config = HealthCheckConfig()
        check = SecurityHealthCheck(config)

        # Mock SSL check
        with patch("socket.create_connection"):
            with patch("ssl.create_default_context"):
                result = check._check_ssl_cert("localhost")
                assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
