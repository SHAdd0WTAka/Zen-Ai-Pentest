"""
Tests for autonomous/sqlmap_integration.py - SQLMap Integration

Tests the SQLMapIntegration class:
- SQLMapScanner initialization
- Command building with safety controls
- Risk level validation
- Output parsing
- Subprocess mocking
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from autonomous.sqlmap_integration import (
    SQLMapResult,
    SQLMapScanner,
    SQLMapTool,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sqlmap_scanner():
    """Create a SQLMapScanner instance for testing."""
    return SQLMapScanner(timeout=60, level=1, risk=1)


@pytest.fixture
def mock_subprocess():
    """Create a mock subprocess for testing."""
    process = AsyncMock()
    process.communicate = AsyncMock(return_value=(b"test output", b""))
    process.returncode = 0
    process.kill = Mock()
    process.wait = AsyncMock()
    return process


# ============================================================================
# Test SQLMapScanner Initialization
# ============================================================================


class TestSQLMapScannerInitialization:
    """Test SQLMapScanner initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        scanner = SQLMapScanner()

        assert scanner.timeout == 600
        assert scanner.level == 1
        assert scanner.risk == 1
        assert scanner.logger is not None

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        scanner = SQLMapScanner(timeout=120, level=3, risk=2)

        assert scanner.timeout == 120
        assert scanner.level == 3
        assert scanner.risk == 2

    def test_level_clamping_high(self):
        """Test that level is clamped to max 5."""
        scanner = SQLMapScanner(level=10)
        assert scanner.level == 5

    def test_level_clamping_low(self):
        """Test that level is clamped to min 1."""
        scanner = SQLMapScanner(level=0)
        assert scanner.level == 1

    def test_risk_clamping_high(self):
        """Test that risk is clamped to max 3."""
        scanner = SQLMapScanner(risk=5)
        assert scanner.risk == 3

    def test_risk_clamping_low(self):
        """Test that risk is clamped to min 1."""
        scanner = SQLMapScanner(risk=0)
        assert scanner.risk == 1


# ============================================================================
# Test Command Building
# ============================================================================


class TestCommandBuilding:
    """Test SQLMap command construction."""

    @pytest.mark.asyncio
    async def test_basic_command_construction(
        self, sqlmap_scanner, mock_subprocess
    ):
        """Test basic command construction."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ) as mock_exec:
            await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

            call_args = mock_exec.call_args[0]

            assert "sqlmap" in call_args[0]
            assert "-u" in call_args
            assert "http://example.com/test.php?id=1" in call_args
            assert "--batch" in call_args
            assert "--json" in call_args

    @pytest.mark.asyncio
    async def test_post_method_command(self, sqlmap_scanner, mock_subprocess):
        """Test command with POST method."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ) as mock_exec:
            await sqlmap_scanner.scan_target(
                "http://example.com/login",
                method="POST",
                data="username=test&password=test",
            )

            call_args = mock_exec.call_args[0]

            assert "--data" in call_args
            assert "username=test&password=test" in call_args

    @pytest.mark.asyncio
    async def test_cookie_command(self, sqlmap_scanner, mock_subprocess):
        """Test command with cookies."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ) as mock_exec:
            await sqlmap_scanner.scan_target(
                "http://example.com/page.php?id=1",
                cookies="session=abc123; auth=xyz",
            )

            call_args = mock_exec.call_args[0]

            assert "--cookie" in call_args
            assert "session=abc123; auth=xyz" in call_args

    @pytest.mark.asyncio
    async def test_headers_command(self, sqlmap_scanner, mock_subprocess):
        """Test command with custom headers."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ) as mock_exec:
            await sqlmap_scanner.scan_target(
                "http://example.com/page.php?id=1",
                headers={"User-Agent": "CustomAgent", "X-Custom": "Value"},
            )

            call_args = mock_exec.call_args[0]

            assert "--header" in call_args
            assert "User-Agent: CustomAgent" in call_args
            assert "X-Custom: Value" in call_args

    @pytest.mark.asyncio
    async def test_safety_flags_present(self, sqlmap_scanner, mock_subprocess):
        """Test that safety flags are included."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ) as mock_exec:
            await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

            call_args = mock_exec.call_args[0]

            assert "--no-union" in call_args
            assert "--no-exploit" in call_args
            assert "--no-stored" in call_args

    @pytest.mark.asyncio
    async def test_level_and_risk_in_command(self, mock_subprocess):
        """Test that level and risk are in command."""
        scanner = SQLMapScanner(level=3, risk=2)

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ) as mock_exec:
            await scanner.scan_target("http://example.com/test.php?id=1")

            call_args = mock_exec.call_args[0]

            assert "--level" in call_args
            assert "3" in call_args
            assert "--risk" in call_args
            assert "2" in call_args


# ============================================================================
# Test Safety Controls
# ============================================================================


class TestSafetyControls:
    """Test SQLMap safety controls."""

    def test_validate_target_valid(self, sqlmap_scanner):
        """Test validation of valid targets."""
        valid, error = sqlmap_scanner._validate_target(
            "http://example.com/page.php?id=1"
        )

        assert valid is True
        assert error == ""

    def test_validate_target_no_protocol(self, sqlmap_scanner):
        """Test rejection of URLs without protocol."""
        valid, error = sqlmap_scanner._validate_target(
            "example.com/page.php?id=1"
        )

        assert valid is False
        assert "http:// or https://" in error

    def test_validate_target_private_ip_192_168(self, sqlmap_scanner):
        """Test blocking of 192.168.x.x private IPs."""
        valid, error = sqlmap_scanner._validate_target(
            "http://192.168.1.1/page.php?id=1"
        )

        assert valid is False
        assert "blocked" in error.lower()

    def test_validate_target_private_ip_10_x(self, sqlmap_scanner):
        """Test blocking of 10.x.x.x private IPs."""
        valid, error = sqlmap_scanner._validate_target(
            "http://10.0.0.1/test.php?id=1"
        )

        assert valid is False

    def test_validate_target_private_ip_172_16(self, sqlmap_scanner):
        """Test blocking of 172.16-31.x.x private IPs."""
        valid, error = sqlmap_scanner._validate_target(
            "http://172.16.0.1/test.php?id=1"
        )

        assert valid is False

    def test_validate_target_loopback_allowed(self, sqlmap_scanner):
        """Test that loopback is allowed for testing."""
        valid, error = sqlmap_scanner._validate_target(
            "http://127.0.0.1/test.php?id=1"
        )

        assert valid is True

    def test_validate_target_localhost_allowed(self, sqlmap_scanner):
        """Test that localhost is allowed for testing."""
        valid, error = sqlmap_scanner._validate_target(
            "http://localhost/test.php?id=1"
        )

        assert valid is True

    def test_validate_target_dangerous_chars_semicolon(self, sqlmap_scanner):
        """Test blocking of semicolon in URL."""
        valid, error = sqlmap_scanner._validate_target(
            "http://example.com; rm -rf /"
        )

        assert valid is False
        assert "Invalid characters" in error

    def test_validate_target_dangerous_chars_pipe(self, sqlmap_scanner):
        """Test blocking of pipe character in URL."""
        valid, error = sqlmap_scanner._validate_target(
            "http://example.com|cat /etc/passwd"
        )

        assert valid is False

    def test_validate_target_dangerous_chars_ampersand(self, sqlmap_scanner):
        """Test blocking of ampersand injection attempt."""
        valid, error = sqlmap_scanner._validate_target(
            "http://example.com && whoami"
        )

        assert valid is False

    @pytest.mark.asyncio
    async def test_safety_check_prevents_execution(self, sqlmap_scanner):
        """Test that safety check prevents scanning invalid targets."""
        result = await sqlmap_scanner.scan_target("not_a_valid_url")

        assert result.success is False
        assert "Safety check failed" in result.error_message


# ============================================================================
# Test Risk Level Validation
# ============================================================================


class TestRiskLevelValidation:
    """Test risk level configurations."""

    def test_risk_level_1_safest(self):
        """Test risk level 1 (safest)."""
        scanner = SQLMapScanner(risk=1)
        assert scanner.risk == 1

    def test_risk_level_2_moderate(self):
        """Test risk level 2 (moderate)."""
        scanner = SQLMapScanner(risk=2)
        assert scanner.risk == 2

    def test_risk_level_3_aggressive(self):
        """Test risk level 3 (most aggressive)."""
        scanner = SQLMapScanner(risk=3)
        assert scanner.risk == 3

    def test_detection_levels(self):
        """Test all valid detection levels."""
        for level in range(1, 6):
            scanner = SQLMapScanner(level=level)
            assert scanner.level == level


# ============================================================================
# Test Output Parsing
# ============================================================================


class TestOutputParsing:
    """Test SQLMap output parsing."""

    def test_parse_vulnerable_mysql(self, sqlmap_scanner):
        """Test parsing MySQL vulnerability detection."""
        output = """
        [INFO] testing connection to the target URL
        GET parameter 'id' is vulnerable
        back-end DBMS: MySQL >= 5.0.12
        payload: id=1' AND 1=1--
        """

        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output(output)
        )

        assert vulnerable is True
        assert dbms == "MySQL >= 5.0.12"
        assert payload == "id=1' AND 1=1--"

    def test_parse_vulnerable_postgresql(self, sqlmap_scanner):
        """Test parsing PostgreSQL vulnerability detection."""
        output = """
        POST parameter 'username' is vulnerable
        back-end DBMS: PostgreSQL
        payload: username=admin' OR '1'='1
        """

        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output(output)
        )

        assert vulnerable is True
        assert dbms == "PostgreSQL"

    def test_parse_not_vulnerable(self, sqlmap_scanner):
        """Test parsing output with no vulnerability."""
        output = """
        [INFO] testing connection to the target URL
        [WARNING] GET parameter 'id' does not seem to be vulnerable
        [INFO] tested 100 parameters
        """

        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output(output)
        )

        assert vulnerable is False
        assert dbms is None
        assert payload is None

    def test_parse_injectable_keyword(self, sqlmap_scanner):
        """Test detecting 'injectable' keyword."""
        output = "parameter 'search' might be injectable"

        vulnerable, _, _, _ = sqlmap_scanner._parse_sqlmap_output(output)

        assert vulnerable is True

    def test_parse_parameter_extraction_get(self, sqlmap_scanner):
        """Test extracting GET parameters."""
        output = "GET parameter 'id' is vulnerable"

        _, _, _, params = sqlmap_scanner._parse_sqlmap_output(output)

        assert len(params) == 1
        assert params[0]["type"] == "GET"
        assert params[0]["name"] == "id"

    def test_parse_parameter_extraction_post(self, sqlmap_scanner):
        """Test extracting POST parameters."""
        output = "POST parameter 'username' appears to be injectable"

        _, _, _, params = sqlmap_scanner._parse_sqlmap_output(output)

        assert len(params) == 1
        assert params[0]["type"] == "POST"
        assert params[0]["name"] == "username"

    def test_parse_multiple_parameters(self, sqlmap_scanner):
        """Test extracting multiple parameters."""
        output = """
        GET parameter 'id' is vulnerable
        POST parameter 'username' appears to be injectable
        Cookie parameter 'session' might be vulnerable
        """

        _, _, _, params = sqlmap_scanner._parse_sqlmap_output(output)

        assert len(params) >= 2
        param_names = [p["name"] for p in params]
        assert "id" in param_names or "username" in param_names

    def test_parse_empty_output(self, sqlmap_scanner):
        """Test parsing empty output."""
        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output("")
        )

        assert vulnerable is False
        assert dbms is None
        assert payload is None
        assert params == []

    def test_parse_various_dbms(self, sqlmap_scanner):
        """Test parsing different DBMS types."""
        dbms_types = [
            ("back-end DBMS: MySQL >= 5.7", "MySQL >= 5.7"),
            (
                "back-end DBMS: Microsoft SQL Server 2019",
                "Microsoft SQL Server 2019",
            ),
            ("back-end DBMS: Oracle 12c", "Oracle 12c"),
            ("back-end DBMS: SQLite 3.x", "SQLite 3.x"),
            ("back-end DBMS: PostgreSQL 12.0", "PostgreSQL 12.0"),
        ]

        for dbms_line, expected_dbms in dbms_types:
            output = f"[INFO] testing\n{dbms_line}\npayload: test"
            _, dbms, _, _ = sqlmap_scanner._parse_sqlmap_output(output)
            assert dbms == expected_dbms


# ============================================================================
# Test Execution Results
# ============================================================================


class TestExecutionResults:
    """Test execution result handling."""

    @pytest.mark.asyncio
    async def test_successful_scan_result(
        self, sqlmap_scanner, mock_subprocess
    ):
        """Test successful scan result."""
        output = """
        GET parameter 'id' is vulnerable
        back-end DBMS: MySQL >= 5.0
        payload: id=1' AND 1=1--
        """
        mock_subprocess.communicate = AsyncMock(
            return_value=(output.encode(), b"")
        )

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is True
        assert result.vulnerable is True
        assert result.dbms == "MySQL >= 5.0"
        assert result.execution_time > 0
        assert len(result.findings) == 1
        assert result.findings[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_not_vulnerable_result(
        self, sqlmap_scanner, mock_subprocess
    ):
        """Test result when target is not vulnerable."""
        output = """
        [INFO] testing connection
        [WARNING] parameter 'id' does not seem to be vulnerable
        """
        mock_subprocess.communicate = AsyncMock(
            return_value=(output.encode(), b"")
        )

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is True
        assert result.vulnerable is False
        assert len(result.findings) == 0

    @pytest.mark.asyncio
    async def test_scan_with_stderr(self, sqlmap_scanner, mock_subprocess):
        """Test scan with stderr output."""
        mock_subprocess.communicate = AsyncMock(
            return_value=(b"test", b"[WARNING] using default settings")
        )

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is True
        assert result.error_message == "[WARNING] using default settings"

    @pytest.mark.asyncio
    async def test_scan_timeout(self, sqlmap_scanner):
        """Test scan timeout handling."""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is False
        assert result.vulnerable is False
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_scan_tool_not_found(self, sqlmap_scanner):
        """Test handling when SQLMap is not installed."""
        with patch(
            "asyncio.create_subprocess_exec", side_effect=FileNotFoundError()
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is False
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_scan_generic_exception(self, sqlmap_scanner):
        """Test handling of generic exceptions."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=Exception("Unexpected error"),
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is False
        assert "Unexpected error" in result.error_message


# ============================================================================
# Test SQLMapResult Dataclass
# ============================================================================


class TestSQLMapResult:
    """Test SQLMapResult dataclass."""

    def test_result_defaults(self):
        """Test SQLMapResult with default values."""
        result = SQLMapResult(success=True, vulnerable=False)

        assert result.success is True
        assert result.vulnerable is False
        assert result.dbms is None
        assert result.payload is None
        assert result.parameters == []
        assert result.findings == []
        assert result.raw_output == ""
        assert result.error_message is None
        assert result.execution_time == 0.0
        assert result.metadata == {}

    def test_result_full(self):
        """Test SQLMapResult with all values."""
        result = SQLMapResult(
            success=True,
            vulnerable=True,
            dbms="MySQL",
            payload="' OR '1'='1",
            parameters=[{"type": "GET", "name": "id"}],
            findings=[{"type": "sqli", "severity": "critical"}],
            raw_output="test output",
            error_message=None,
            execution_time=5.5,
            metadata={"target": "http://example.com"},
        )

        assert result.success is True
        assert result.vulnerable is True
        assert result.dbms == "MySQL"
        assert result.execution_time == 5.5


# ============================================================================
# Test SQLMapTool Wrapper
# ============================================================================


class TestSQLMapTool:
    """Test SQLMapTool wrapper class."""

    def test_initialization(self):
        """Test SQLMapTool initialization."""
        tool = SQLMapTool()

        assert tool.scanner is not None
        assert isinstance(tool.scanner, SQLMapScanner)

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution through wrapper."""
        tool = SQLMapTool()
        mock_result = SQLMapResult(
            success=True,
            vulnerable=True,
            dbms="MySQL",
            findings=[{"type": "sqli"}],
            execution_time=5.0,
        )

        with patch.object(
            tool.scanner, "scan_target", AsyncMock(return_value=mock_result)
        ):
            result = await tool.execute(
                {
                    "target": "http://example.com/page.php?id=1",
                    "method": "GET",
                }
            )

        assert result["tool"] == "sqlmap"
        assert result["success"] is True
        assert result["vulnerable"] is True
        assert result["dbms"] == "MySQL"

    @pytest.mark.asyncio
    async def test_execute_with_post(self):
        """Test execution with POST data."""
        tool = SQLMapTool()
        mock_result = SQLMapResult(
            success=True, vulnerable=False, execution_time=3.0
        )

        with patch.object(
            tool.scanner, "scan_target", AsyncMock(return_value=mock_result)
        ):
            result = await tool.execute(
                {
                    "target": "http://example.com/login",
                    "method": "POST",
                    "data": "username=test&password=test",
                }
            )

        assert result["success"] is True
        assert result["execution_time"] == 3.0

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """Test execution with failure."""
        tool = SQLMapTool()
        mock_result = SQLMapResult(
            success=False,
            vulnerable=False,
            error_message="Connection timeout",
            execution_time=0,
        )

        with patch.object(
            tool.scanner, "scan_target", AsyncMock(return_value=mock_result)
        ):
            result = await tool.execute(
                {
                    "target": "http://example.com/page.php?id=1",
                }
            )

        assert result["success"] is False
        assert result["error"] == "Connection timeout"


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_https_url_allowed(self, sqlmap_scanner, mock_subprocess):
        """Test that HTTPS URLs are allowed."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ):
            result = await sqlmap_scanner.scan_target(
                "https://example.com/secure.php?id=1"
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_complex_url_parameters(
        self, sqlmap_scanner, mock_subprocess
    ):
        """Test URL with multiple parameters - ampersand in query string is blocked by safety."""
        # Note: The & character is blocked by safety validation as dangerous
        complex_url = "http://example.com/page.php?id=1&cat=2&view=3"

        # Check validation - ampersand is blocked by safety check
        valid, error = sqlmap_scanner._validate_target(complex_url)

        # The & character is blocked by safety validation
        assert valid is False
        assert "Invalid characters" in error

    @pytest.mark.asyncio
    async def test_url_with_fragment(self, sqlmap_scanner, mock_subprocess):
        """Test URL with fragment."""
        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_subprocess
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/page.php?id=1#section"
            )

        assert result.success is True
