"""
Smart Tests for ffuf_integration_enhanced.py

Agent: #024
Module: ffuf_integration_enhanced.py
Pattern: TOOLEXECUTOR, GOLDEN FILES, COMMANDRUNNER
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import module under test
from autonomous import ffuf_integration_enhanced
from autonomous.ffuf_integration_enhanced import (
    FFUFEnhancedScanner,
    FFUFResult,
    FFUFTool,
)
from autonomous.tool_executor import SafetyLevel, ToolExecutor

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def scanner():
    """Create FFUFEnhancedScanner instance."""
    return FFUFEnhancedScanner(timeout=300, threads=40)


@pytest.fixture
def mock_tool_executor():
    """Mock ToolExecutor for testing."""
    with patch("autonomous.ffuf_integration_enhanced.ToolExecutor") as mock:
        executor = MagicMock()
        executor.execute = AsyncMock(
            return_value=MagicMock(
                success=True,
                stdout=json.dumps(
                    {
                        "results": [
                            {
                                "url": "http://example.com/admin",
                                "status": 200,
                                "length": 1234,
                            },
                            {
                                "url": "http://example.com/api",
                                "status": 403,
                                "length": 567,
                            },
                        ]
                    }
                ),
                stderr="",
                return_code=0,
            )
        )
        mock.return_value = executor
        yield mock


# =============================================================================
# TEST 1: Module Import
# =============================================================================


def test_module_importable():
    """Test that ffuf_integration_enhanced module can be imported."""
    assert ffuf_integration_enhanced is not None
    assert hasattr(ffuf_integration_enhanced, "FFUFEnhancedScanner")
    assert hasattr(ffuf_integration_enhanced, "FFUFResult")
    assert hasattr(ffuf_integration_enhanced, "FFUFTool")


# =============================================================================
# TEST 2: ToolExecutor Pattern
# =============================================================================


def test_module_uses_tool_executor(scanner):
    """Test that module follows ToolExecutor pattern."""
    assert hasattr(scanner, "executor")
    assert scanner.timeout > 0
    assert scanner.threads > 0


# =============================================================================
# TEST 3: NOT_FOUND Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_not_found_error():
    """Test handling when ffuf is not installed."""
    scanner = FFUFEnhancedScanner(timeout=60)

    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
        result = await scanner.directory_scan("http://example.com/FUZZ")

    assert result.success is False
    assert "not found" in result.error_message.lower() or "ffuf" in result.error_message.lower()


# =============================================================================
# TEST 4: TIMEOUT Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_timeout_error():
    """Test handling of timeout errors."""
    scanner = FFUFEnhancedScanner(timeout=1)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        proc_mock.kill = Mock()
        proc_mock.wait = AsyncMock()
        mock.return_value = proc_mock

        result = await scanner.directory_scan("http://example.com/FUZZ")

    assert result.success is False
    assert "timeout" in result.error_message.lower()


# =============================================================================
# TEST 5: Parser Extracts Findings
# =============================================================================


def test_module_parser_extracts_findings(scanner):
    """Test that parser correctly extracts fuzzing results."""
    test_output = json.dumps(
        {
            "results": [
                {
                    "url": "http://example.com/admin",
                    "status": 200,
                    "length": 1234,
                    "words": 100,
                    "lines": 20,
                },
                {
                    "url": "http://example.com/api",
                    "status": 403,
                    "length": 567,
                    "words": 50,
                    "lines": 10,
                },
            ]
        }
    )

    findings, summary = scanner._parse_ffuf_json(test_output)

    assert len(findings) == 2
    assert summary["total"] == 2
    assert "200" in summary["status_codes"]
    assert "403" in summary["status_codes"]


# =============================================================================
# TEST 6: End-to-End with Mock
# =============================================================================


@pytest.mark.asyncio
async def test_module_end_to_end_mocked():
    """Test full workflow with mocked subprocess."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps(
        {
            "results": [
                {
                    "url": "http://example.com/test",
                    "status": 200,
                    "length": 100,
                }
            ]
        }
    )

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.directory_scan("http://example.com/FUZZ")

    assert isinstance(result, FFUFResult)
    assert result.target == "http://example.com/FUZZ"
    assert result.execution_time >= 0


# =============================================================================
# TEST 7: Empty Input Handling
# =============================================================================


def test_module_empty_input(scanner):
    """Test handling of empty input."""
    findings, summary = scanner._parse_ffuf_json("")

    assert len(findings) == 0
    assert summary["total"] == 0


# =============================================================================
# TEST 8: Invalid Output Handling
# =============================================================================


def test_module_invalid_output(scanner):
    """Test handling of invalid/malformed output."""
    garbage_output = "garbage data without any valid JSON"

    findings, summary = scanner._parse_ffuf_json(garbage_output)

    assert isinstance(findings, list)
    assert isinstance(summary, dict)


# =============================================================================
# ADDITIONAL TESTS for Coverage
# =============================================================================


def test_ffuf_result_dataclass():
    """Test FFUFResult dataclass."""
    result = FFUFResult(
        success=True,
        target="http://example.com/FUZZ",
        mode="directory",
        findings=[{"url": "http://example.com/admin", "status": 200}],
        summary={"total": 1, "status_codes": {"200": 1}},
        execution_time=5.5,
    )

    assert result.success is True
    assert result.target == "http://example.com/FUZZ"
    assert len(result.findings) == 1


def test_validate_target_valid(scanner):
    """Test target validation with valid URL."""
    valid, error = scanner._validate_target("http://example.com/FUZZ")
    assert valid is True
    assert error == ""


def test_validate_target_empty(scanner):
    """Test target validation with empty target."""
    valid, error = scanner._validate_target("")
    assert valid is False
    assert "empty" in error.lower()


def test_validate_target_no_fuzz(scanner):
    """Test target validation without FUZZ keyword."""
    valid, error = scanner._validate_target("http://example.com/path")
    assert valid is False
    assert "fuzz" in error.lower()


def test_validate_target_dangerous_chars(scanner):
    """Test target validation with dangerous characters."""
    valid, error = scanner._validate_target("http://example.com/FUZZ;rm -rf /")
    assert valid is False
    assert "invalid" in error.lower()


def test_validate_vhost_inputs_valid(scanner):
    """Test vhost inputs validation with valid inputs."""
    valid, error = scanner._validate_vhost_inputs("192.168.1.1", "example.com")
    assert valid is True
    assert error == ""


def test_validate_vhost_inputs_empty_ip(scanner):
    """Test vhost inputs validation with empty IP."""
    valid, error = scanner._validate_vhost_inputs("", "example.com")
    assert valid is False
    assert "empty" in error.lower()


def test_validate_vhost_inputs_empty_domain(scanner):
    """Test vhost inputs validation with empty domain."""
    valid, error = scanner._validate_vhost_inputs("192.168.1.1", "")
    assert valid is False
    assert "empty" in error.lower()


def test_validate_vhost_inputs_invalid_ip(scanner):
    """Test vhost inputs validation with invalid IP."""
    valid, error = scanner._validate_vhost_inputs("invalid_ip", "example.com")
    assert valid is False
    assert "invalid" in error.lower()


@pytest.mark.asyncio
async def test_directory_scan_success():
    """Test successful directory scan."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps(
        {
            "results": [
                {
                    "url": "http://example.com/admin",
                    "status": 200,
                    "length": 1234,
                },
                {
                    "url": "http://example.com/api",
                    "status": 403,
                    "length": 567,
                },
            ]
        }
    )

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.directory_scan("http://example.com/FUZZ")

    assert result.success is True
    assert len(result.findings) == 2


@pytest.mark.asyncio
async def test_directory_scan_with_extensions():
    """Test directory scan with extensions."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps({"results": []})

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.directory_scan("http://example.com/FUZZ", extensions=[".php", ".html"])

    assert result.success is True


@pytest.mark.asyncio
async def test_directory_scan_with_status_codes():
    """Test directory scan with status code filtering."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps({"results": []})

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.directory_scan(
            "http://example.com/FUZZ",
            match_codes=[200, 301, 302],
            filter_codes=[404],
        )

    assert result.success is True


@pytest.mark.asyncio
async def test_vhost_scan_success():
    """Test successful vhost scan."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps(
        {
            "results": [
                {"input": "admin", "status": 200},
                {"input": "api", "status": 403},
            ]
        }
    )

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.vhost_scan("192.168.1.1", "example.com")

    assert result.success is True
    assert result.mode == "vhost"


@pytest.mark.asyncio
async def test_parameter_fuzz_success():
    """Test successful parameter fuzzing."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps(
        {
            "results": [
                {"input": "id", "status": 200},
                {"input": "user", "status": 200},
            ]
        }
    )

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.parameter_fuzz("http://example.com/page", "param")

    assert result.success is True
    assert result.mode == "parameter"


@pytest.mark.asyncio
async def test_parameter_fuzz_with_method():
    """Test parameter fuzzing with different HTTP method."""
    scanner = FFUFEnhancedScanner(timeout=60)

    mock_output = json.dumps({"results": []})

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.parameter_fuzz("http://example.com/page", "param", method="POST")

    assert result.success is True


@pytest.mark.asyncio
async def test_ffuf_tool_execute_directory():
    """Test FFUFTool with directory scan."""
    tool = FFUFTool()

    with patch.object(tool.scanner, "directory_scan", new_callable=AsyncMock) as mock:
        mock.return_value = FFUFResult(
            success=True,
            target="http://example.com/FUZZ",
            mode="directory",
            findings=[{"url": "http://example.com/admin", "status": 200}],
            summary={"total": 1},
            execution_time=5.0,
        )

        result = await tool.execute(
            {
                "target": "http://example.com/FUZZ",
                "mode": "directory",
                "extensions": [".php"],
            }
        )

    assert result["tool"] == "ffuf"
    assert result["success"] is True
    assert result["mode"] == "directory"


@pytest.mark.asyncio
async def test_ffuf_tool_execute_vhost():
    """Test FFUFTool with vhost scan."""
    tool = FFUFTool()

    with patch.object(tool.scanner, "vhost_scan", new_callable=AsyncMock) as mock:
        mock.return_value = FFUFResult(
            success=True,
            target="192.168.1.1/example.com",
            mode="vhost",
            findings=[],
            summary={"total": 0},
            execution_time=3.0,
        )

        result = await tool.execute(
            {
                "target_ip": "192.168.1.1",
                "domain": "example.com",
                "mode": "vhost",
            }
        )

    assert result["tool"] == "ffuf"
    assert result["mode"] == "vhost"


@pytest.mark.asyncio
async def test_ffuf_tool_execute_parameter():
    """Test FFUFTool with parameter fuzz."""
    tool = FFUFTool()

    with patch.object(tool.scanner, "parameter_fuzz", new_callable=AsyncMock) as mock:
        mock.return_value = FFUFResult(
            success=True,
            target="http://example.com/page",
            mode="parameter",
            findings=[],
            summary={"total": 0},
            execution_time=2.0,
        )

        result = await tool.execute(
            {
                "target": "http://example.com/page",
                "parameter": "id",
                "mode": "parameter",
            }
        )

    assert result["tool"] == "ffuf"
    assert result["mode"] == "parameter"


@pytest.mark.asyncio
async def test_ffuf_tool_unknown_mode():
    """Test FFUFTool with unknown mode."""
    tool = FFUFTool()

    result = await tool.execute({"target": "http://example.com", "mode": "unknown"})

    assert result["tool"] == "ffuf"
    assert result["success"] is False


def test_parse_ffuf_json_plain_text(scanner):
    """Test parsing plain text output."""
    test_output = """
    [Status: 200, Size: 1234, Words: 100]
    [Status: 403, Size: 567, Words: 50]
    """

    findings, summary = scanner._parse_ffuf_json(test_output)

    assert isinstance(findings, list)
    assert isinstance(summary, dict)


def test_scanner_initialization():
    """Test scanner initialization with different parameters."""
    scanner = FFUFEnhancedScanner(timeout=120, threads=20, wordlist="/custom/wordlist.txt")

    assert scanner.timeout == 120
    assert scanner.threads == 20
    assert scanner.wordlist == "/custom/wordlist.txt"


@pytest.mark.asyncio
async def test_directory_scan_general_exception():
    """Test handling of general exceptions during directory scan."""
    scanner = FFUFEnhancedScanner(timeout=60)

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=Exception("Unexpected error"),
    ):
        result = await scanner.directory_scan("http://example.com/FUZZ")

    assert result.success is False


@pytest.mark.asyncio
async def test_vhost_scan_general_exception():
    """Test handling of general exceptions during vhost scan."""
    scanner = FFUFEnhancedScanner(timeout=60)

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=Exception("Unexpected error"),
    ):
        result = await scanner.vhost_scan("192.168.1.1", "example.com")

    assert result.success is False


@pytest.mark.asyncio
async def test_parameter_fuzz_general_exception():
    """Test handling of general exceptions during parameter fuzz."""
    scanner = FFUFEnhancedScanner(timeout=60)

    with patch(
        "asyncio.create_subprocess_exec",
        side_effect=Exception("Unexpected error"),
    ):
        result = await scanner.parameter_fuzz("http://example.com/page", "param")

    assert result.success is False
