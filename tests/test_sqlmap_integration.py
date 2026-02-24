"""
Comprehensive tests for autonomous/sqlmap_integration.py

Target: 80%+ coverage
Tests: SQLMapIntegration, command building, safety controls, output parsing
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
def sample_sqlmap_output():
    """Sample SQLMap output for parsing tests."""
    return """
    [INFO] testing connection to the target URL
    [INFO] testing if the target URL content is stable
    [INFO] target URL appears to be GET parameter 'id' is vulnerable
    [INFO] testing if GET parameter 'id' is dynamic
    back-end DBMS: MySQL >= 5.0.12
    [INFO] GET parameter 'id' is vulnerable
    payload: id=1 AND 1=1
    [INFO] parameter 'id' is vulnerable
    """


# ============================================================================
# Test SQLMapResult
# ============================================================================


class TestSQLMapResult:
    """Test SQLMapResult dataclass."""

    def test_result_creation(self):
        """Test SQLMapResult creation."""
        result = SQLMapResult(
            success=True,
            vulnerable=True,
            dbms="MySQL",
            payload="' OR '1'='1",
            parameters=[{"type": "GET", "name": "id"}],
            findings=[{"type": "sqli", "severity": "critical"}],
            execution_time=5.5,
        )

        assert result.success is True
        assert result.vulnerable is True
        assert result.dbms == "MySQL"
        assert result.payload == "' OR '1'='1"
        assert len(result.parameters) == 1
        assert len(result.findings) == 1
        assert result.execution_time == 5.5

    def test_result_creation_defaults(self):
        """Test SQLMapResult with default values."""
        result = SQLMapResult(success=False, vulnerable=False)

        assert result.success is False
        assert result.vulnerable is False
        assert result.dbms is None
        assert result.payload is None
        assert result.parameters == []
        assert result.findings == []
        assert result.execution_time == 0.0


# ============================================================================
# Test SQLMapScanner
# ============================================================================


class TestSQLMapScanner:
    """Test SQLMapScanner class."""

    def test_initialization(self):
        """Test SQLMapScanner initialization."""
        scanner = SQLMapScanner(timeout=120, level=3, risk=2)

        assert scanner.timeout == 120
        assert scanner.level == 3
        assert scanner.risk == 2
        assert scanner.logger is not None

    def test_initialization_clamping(self):
        """Test that level and risk are clamped to valid ranges."""
        scanner_high = SQLMapScanner(level=10, risk=5)
        assert scanner_high.level == 5  # Clamped to max 5
        assert scanner_high.risk == 3  # Clamped to max 3

        scanner_low = SQLMapScanner(level=0, risk=0)
        assert scanner_low.level == 1  # Clamped to min 1
        assert scanner_low.risk == 1  # Clamped to min 1

    def test_initialization_defaults(self):
        """Test default initialization values."""
        scanner = SQLMapScanner()

        assert scanner.timeout == 600
        assert scanner.level == 1
        assert scanner.risk == 1

    @pytest.mark.asyncio
    async def test_scan_target_success(self, sqlmap_scanner):
        """Test successful SQLMap scan."""
        mock_output = """
        [INFO] the back-end DBMS is MySQL
        GET parameter 'id' is vulnerable
        back-end DBMS: MySQL >= 5.0
        payload: id=1' AND 1=1--
        """

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), b"")
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://testphp.vulnweb.com/artists.php?artist=1",
                method="GET",
            )

        assert result.success is True
        assert result.vulnerable is True
        assert result.dbms == "MySQL >= 5.0"
        assert result.payload == "id=1' AND 1=1--"
        assert len(result.findings) == 1
        assert result.findings[0]["type"] == "sql_injection"
        assert result.findings[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_scan_target_post_method(self, sqlmap_scanner):
        """Test SQLMap scan with POST method."""
        mock_output = (
            "GET parameter 'id' is vulnerable\nback-end DBMS: PostgreSQL"
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), b"")
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/login",
                method="POST",
                data="username=test&password=test",
            )

        assert result.success is True
        assert result.vulnerable is True
        assert result.dbms == "PostgreSQL"

    @pytest.mark.asyncio
    async def test_scan_target_with_cookies(self, sqlmap_scanner):
        """Test SQLMap scan with cookies."""
        mock_output = "[INFO] testing started"

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), b"")
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/page.php?id=1",
                cookies="session=abc123; auth=xyz",
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_scan_target_with_headers(self, sqlmap_scanner):
        """Test SQLMap scan with custom headers."""
        mock_output = "[INFO] testing started"

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), b"")
        )
        mock_process.returncode = 0

        headers = {"User-Agent": "CustomAgent", "X-Custom": "Value"}

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/page.php?id=1",
                headers=headers,
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_scan_target_timeout(self, sqlmap_scanner):
        """Test SQLMap scan timeout handling."""
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
    async def test_scan_target_not_found(self, sqlmap_scanner):
        """Test SQLMap not found error."""
        with patch(
            "asyncio.create_subprocess_exec", side_effect=FileNotFoundError()
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is False
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_scan_target_generic_exception(self, sqlmap_scanner):
        """Test generic exception handling."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=Exception("Unexpected error"),
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is False
        assert "Unexpected error" in result.error_message

    @pytest.mark.asyncio
    async def test_scan_target_safety_check_fails(self, sqlmap_scanner):
        """Test that safety checks prevent scanning invalid targets."""
        result = await sqlmap_scanner.scan_target("not_a_valid_url")

        assert result.success is False
        assert "Safety check failed" in result.error_message

    @pytest.mark.asyncio
    async def test_scan_target_not_vulnerable(self, sqlmap_scanner):
        """Test scan of non-vulnerable target."""
        mock_output = """
        [INFO] testing connection to the target URL
        [INFO] testing if the target URL content is stable
        [WARNING] GET parameter 'id' does not seem to be injectable
        """

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), b"")
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/page.php?id=1"
            )

        assert result.success is True
        assert result.vulnerable is False
        assert len(result.findings) == 0


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
        """Test validation rejects URLs without protocol."""
        valid, error = sqlmap_scanner._validate_target(
            "example.com/page.php?id=1"
        )

        assert valid is False
        assert "http:// or https://" in error

    def test_validate_target_private_ip_blocked(self, sqlmap_scanner):
        """Test validation blocks private IPs."""
        valid, error = sqlmap_scanner._validate_target(
            "http://192.168.1.1/page.php?id=1"
        )

        assert valid is False
        assert "blocked" in error.lower()

    def test_validate_target_loopback_allowed(self, sqlmap_scanner):
        """Test validation allows loopback for testing."""
        valid, error = sqlmap_scanner._validate_target(
            "http://127.0.0.1/page.php?id=1"
        )

        assert valid is True  # Loopback allowed for testing

    def test_validate_target_dangerous_chars(self, sqlmap_scanner):
        """Test validation blocks dangerous characters."""
        valid, error = sqlmap_scanner._validate_target(
            "http://example.com; rm -rf /"
        )

        assert valid is False
        assert "Invalid characters" in error

    def test_validate_target_invalid_url(self, sqlmap_scanner):
        """Test validation handles invalid URLs gracefully."""
        valid, error = sqlmap_scanner._validate_target("http://[invalid")

        assert valid is False

    def test_validate_target_10_x_private(self, sqlmap_scanner):
        """Test blocking 10.x.x.x private range."""
        valid, error = sqlmap_scanner._validate_target(
            "http://10.0.0.1/test.php?id=1"
        )
        assert valid is False

    def test_validate_target_172_private(self, sqlmap_scanner):
        """Test blocking 172.16-31.x.x private range."""
        valid, error = sqlmap_scanner._validate_target(
            "http://172.16.0.1/test.php?id=1"
        )
        assert valid is False


# ============================================================================
# Test Output Parsing
# ============================================================================


class TestOutputParsing:
    """Test SQLMap output parsing."""

    def test_parse_sqlmap_output_vulnerable(self, sqlmap_scanner):
        """Test parsing output indicating vulnerability."""
        output = """
        [INFO] the back-end DBMS is MySQL
        GET parameter 'id' is vulnerable
        back-end DBMS: MySQL >= 5.0.12
        payload: id=1' AND SLEEP(5)--
        POST parameter 'username' is dynamic
        """

        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output(output)
        )

        assert vulnerable is True
        assert dbms == "MySQL >= 5.0.12"
        assert payload == "id=1' AND SLEEP(5)--"
        assert len(params) == 2

    def test_parse_sqlmap_output_not_vulnerable(self, sqlmap_scanner):
        """Test parsing output indicating no vulnerability."""
        output = """
        [INFO] testing connection to the target URL
        [WARNING] parameter 'id' does not seem to be injectable
        [INFO] tested 100 parameters
        """

        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output(output)
        )

        assert vulnerable is False
        assert dbms is None
        assert payload is None

    def test_parse_sqlmap_output_dbms_variants(self, sqlmap_scanner):
        """Test parsing different DBMS outputs."""
        dbms_variants = [
            ("back-end DBMS: PostgreSQL", "PostgreSQL"),
            (
                "back-end DBMS: Microsoft SQL Server 2019",
                "Microsoft SQL Server 2019",
            ),
            ("back-end DBMS: Oracle 12c", "Oracle 12c"),
            ("back-end DBMS: SQLite 3.x", "SQLite 3.x"),
        ]

        for dbms_line, expected_dbms in dbms_variants:
            output = f"[INFO] testing\n{dbms_line}\n"
            _, dbms, _, _ = sqlmap_scanner._parse_sqlmap_output(output)
            assert dbms == expected_dbms

    def test_parse_sqlmap_output_payload_variants(self, sqlmap_scanner):
        """Test parsing different payload formats."""
        payloads = [
            "payload: id=1' AND 1=1--",
            "Payload: admin' OR '1'='1",
            "PAYLOAD: 1 UNION SELECT null,null--",
        ]

        for payload_line in payloads:
            output = f"parameter 'id' is vulnerable\n{payload_line}"
            _, _, payload, _ = sqlmap_scanner._parse_sqlmap_output(output)
            assert payload is not None

    def test_parse_sqlmap_output_parameter_extraction(self, sqlmap_scanner):
        """Test extracting parameter information."""
        output = """
        GET parameter 'id' is vulnerable
        POST parameter 'username' appears to be injectable
        Cookie parameter 'session' might be vulnerable
        """

        _, _, _, params = sqlmap_scanner._parse_sqlmap_output(output)

        assert len(params) >= 1
        param_names = [p["name"] for p in params]
        assert "id" in param_names or "username" in param_names

    def test_parse_sqlmap_output_empty(self, sqlmap_scanner):
        """Test parsing empty output."""
        vulnerable, dbms, payload, params = (
            sqlmap_scanner._parse_sqlmap_output("")
        )

        assert vulnerable is False
        assert dbms is None
        assert payload is None
        assert params == []

    def test_parse_sqlmap_output_injectable_keyword(self, sqlmap_scanner):
        """Test detecting 'injectable' keyword."""
        output = "parameter 'id' might be injectable"

        vulnerable, _, _, _ = sqlmap_scanner._parse_sqlmap_output(output)

        assert vulnerable is True


# ============================================================================
# Test SQLMapTool
# ============================================================================


class TestSQLMapTool:
    """Test SQLMapTool wrapper class."""

    def test_initialization(self):
        """Test SQLMapTool initialization."""
        tool = SQLMapTool()

        assert tool.scanner is not None
        assert isinstance(tool.scanner, SQLMapScanner)

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test SQLMapTool execute method."""
        tool = SQLMapTool()

        mock_result = SQLMapResult(
            success=True,
            vulnerable=True,
            dbms="MySQL",
            findings=[{"type": "sqli"}],
            execution_time=5.0,
            metadata={"target": "http://example.com"},
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
        assert len(result["findings"]) == 1
        assert result["execution_time"] == 5.0

    @pytest.mark.asyncio
    async def test_execute_with_post_data(self):
        """Test SQLMapTool with POST data."""
        tool = SQLMapTool()

        mock_result = SQLMapResult(
            success=True,
            vulnerable=False,
            execution_time=3.0,
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
        assert result["vulnerable"] is False

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """Test SQLMapTool execute with failure."""
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
# Test Risk Levels
# ============================================================================


class TestRiskLevels:
    """Test different risk level configurations."""

    def test_risk_level_1(self):
        """Test risk level 1 (safest)."""
        scanner = SQLMapScanner(risk=1)
        assert scanner.risk == 1

    def test_risk_level_2(self):
        """Test risk level 2 (moderate)."""
        scanner = SQLMapScanner(risk=2)
        assert scanner.risk == 2

    def test_risk_level_3(self):
        """Test risk level 3 (aggressive)."""
        scanner = SQLMapScanner(risk=3)
        assert scanner.risk == 3

    def test_level_ranges(self):
        """Test different detection levels."""
        for level in range(1, 6):
            scanner = SQLMapScanner(level=level)
            assert scanner.level == level


# ============================================================================
# Edge Cases and Integration
# ============================================================================


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_scan_with_stderr_output(self, sqlmap_scanner):
        """Test handling stderr output."""
        mock_output = "GET parameter 'id' is vulnerable"
        mock_stderr = "[WARNING] using unescaped version"

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), mock_stderr.encode())
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1"
            )

        assert result.success is True
        assert result.error_message == mock_stderr

    @pytest.mark.asyncio
    async def test_scan_with_complex_url(self, sqlmap_scanner):
        """Test scanning URL with multiple parameters."""
        mock_output = "GET parameter 'id' is vulnerable"

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_output.encode(), b"")
        )
        mock_process.returncode = 0

        complex_url = "http://example.com/page.php?id=1&cat=2&view=3"

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await sqlmap_scanner.scan_target(complex_url)

        assert result.success is True

    def test_result_with_findings(self):
        """Test SQLMapResult with findings."""
        finding = {
            "type": "sql_injection",
            "severity": "critical",
            "dbms": "MySQL",
            "payload": "' OR '1'='1",
            "parameters": [{"type": "GET", "name": "id"}],
            "description": "SQL Injection detected",
        }

        result = SQLMapResult(
            success=True,
            vulnerable=True,
            findings=[finding],
        )

        assert len(result.findings) == 1
        assert result.findings[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_command_construction(self, sqlmap_scanner):
        """Test that correct command is constructed."""
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b"test", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.return_value = mock_process

            await sqlmap_scanner.scan_target(
                "http://example.com/test.php?id=1",
                method="POST",
                data="username=test",
                cookies="session=abc",
            )

            call_args = mock_exec.call_args
            cmd = call_args[0]

            assert "sqlmap" in cmd[0]
            assert "-u" in cmd
            assert "http://example.com/test.php?id=1" in cmd
            assert "--data" in cmd
            assert "username=test" in cmd
            assert "--cookie" in cmd
            assert "session=abc" in cmd
