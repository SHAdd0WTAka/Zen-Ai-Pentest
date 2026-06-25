"""
Smart Tests for subdomain_scan.py

Agent: #024
Module: subdomain_scan.py
Pattern: TOOLEXECUTOR, GOLDEN FILES, COMMANDRUNNER
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import module under test
from autonomous import subdomain_scan
from autonomous.subdomain_scan import (
    BatchScanResult,
    SubdomainScanner,
    SubdomainScanResult,
    SubdomainScanTool,
)
from autonomous.tool_executor import SafetyLevel, ToolExecutor

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def scanner():
    """Create SubdomainScanner instance."""
    return SubdomainScanner(timeout=30, ports=[80, 443])


@pytest.fixture
def mock_tool_executor():
    """Mock ToolExecutor for testing."""
    with patch("autonomous.subdomain_scan.ToolExecutor") as mock:
        executor = MagicMock()
        executor.execute = AsyncMock(
            return_value=MagicMock(
                success=True,
                stdout="80/tcp open http\n443/tcp open https",
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
    """Test that subdomain_scan module can be imported."""
    assert subdomain_scan is not None
    assert hasattr(subdomain_scan, "SubdomainScanner")
    assert hasattr(subdomain_scan, "SubdomainScanResult")
    assert hasattr(subdomain_scan, "BatchScanResult")
    assert hasattr(subdomain_scan, "SubdomainScanTool")


# =============================================================================
# TEST 2: ToolExecutor Pattern
# =============================================================================


def test_module_uses_tool_executor(scanner):
    """Test that module follows ToolExecutor pattern."""
    assert hasattr(scanner, "executor")
    assert scanner.timeout > 0
    assert len(scanner.ports) > 0


# =============================================================================
# TEST 3: NOT_FOUND Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_not_found_error():
    """Test handling when tools are not found."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
        result = await scanner.scan("www.example.com", probe_http=False, probe_ports=True)

    assert isinstance(result, SubdomainScanResult)


# =============================================================================
# TEST 4: TIMEOUT Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_timeout_error():
    """Test handling of timeout errors."""
    scanner = SubdomainScanner(timeout=1)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        proc_mock.kill = Mock()
        proc_mock.wait = AsyncMock()
        mock.return_value = proc_mock

        result = await scanner.scan("www.example.com", probe_http=True)

    assert isinstance(result, SubdomainScanResult)


# =============================================================================
# TEST 5: Parser Extracts Findings
# =============================================================================


def test_module_parser_extracts_findings(scanner):
    """Test that parser correctly extracts port information."""
    test_output = """
    80/tcp open http
    443/tcp open https
    8080/tcp open http-proxy
    """

    # Parse using the executor's parser
    ports = scanner.executor._parse_nmap(test_output)

    assert "open_ports" in ports
    assert len(ports["open_ports"]) == 3


# =============================================================================
# TEST 6: End-to-End with Mock
# =============================================================================


@pytest.mark.asyncio
async def test_module_end_to_end_mocked():
    """Test full workflow with mocked subprocess."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(b"93.184.216.34", b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.scan("www.example.com", probe_http=False)

    assert isinstance(result, SubdomainScanResult)
    assert result.subdomain == "www.example.com"


# =============================================================================
# TEST 7: Empty Input Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_empty_input():
    """Test handling of empty subdomain list."""
    scanner = SubdomainScanner(timeout=30)

    result = await scanner.scan_batch([], probe_http=True)

    assert isinstance(result, BatchScanResult)
    assert result.total_scanned == 0


# =============================================================================
# TEST 8: Invalid Output Handling
# =============================================================================


def test_module_invalid_output(scanner):
    """Test handling of invalid/malformed output."""
    garbage_output = "garbage data without any valid ports"

    ports = scanner.executor._parse_nmap(garbage_output)

    assert "open_ports" in ports
    assert len(ports["open_ports"]) == 0


# =============================================================================
# ADDITIONAL TESTS for Coverage
# =============================================================================


def test_subdomain_scan_result_dataclass():
    """Test SubdomainScanResult dataclass."""
    result = SubdomainScanResult(
        success=True,
        subdomain="www.example.com",
        ip_address="93.184.216.34",
        http_status=200,
        http_title="Example Domain",
        is_alive=True,
        execution_time=1.5,
    )

    assert result.success is True
    assert result.subdomain == "www.example.com"
    assert result.is_alive is True


def test_batch_scan_result_dataclass():
    """Test BatchScanResult dataclass."""
    single_result = SubdomainScanResult(success=True, subdomain="www.example.com", is_alive=True)

    result = BatchScanResult(
        success=True,
        results=[single_result],
        total_scanned=1,
        alive_count=1,
        error_count=0,
        execution_time=2.0,
    )

    assert result.success is True
    assert result.total_scanned == 1
    assert result.alive_count == 1


def test_validate_subdomain_valid(scanner):
    """Test subdomain validation with valid subdomain."""
    valid, error = scanner._validate_subdomain("www.example.com")
    assert valid is True
    assert error == ""


def test_validate_subdomain_empty(scanner):
    """Test subdomain validation with empty subdomain."""
    valid, error = scanner._validate_subdomain("")
    assert valid is False
    assert "empty" in error.lower()


def test_validate_subdomain_dangerous_chars(scanner):
    """Test subdomain validation with dangerous characters."""
    valid, error = scanner._validate_subdomain("example.com;rm -rf /")
    assert valid is False
    assert "invalid" in error.lower()


@pytest.mark.asyncio
async def test_scan_with_http_probe():
    """Test scanning with HTTP probing."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(b"HTTP/1.1 200 OK\r\nServer: nginx\r\n\r\n", b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.scan("www.example.com", probe_http=True)

    assert isinstance(result, SubdomainScanResult)


@pytest.mark.asyncio
async def test_scan_with_port_scanning(mock_tool_executor):
    """Test scanning with port scanning."""
    scanner = SubdomainScanner(timeout=30)

    result = await scanner.scan("www.example.com", probe_http=False, probe_ports=True)

    assert isinstance(result, SubdomainScanResult)


@pytest.mark.asyncio
async def test_scan_batch_multiple_subdomains():
    """Test batch scanning multiple subdomains."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(b"93.184.216.34", b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner.scan_batch(
            ["www.example.com", "mail.example.com"],
            max_concurrent=2,
            probe_http=False,
        )

    assert isinstance(result, BatchScanResult)
    assert result.total_scanned == 2


@pytest.mark.asyncio
async def test_resolve_dns_success():
    """Test successful DNS resolution."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(b"93.184.216.34\n", b""))
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        ip = await scanner._resolve_dns("www.example.com")

    assert ip == "93.184.216.34"


@pytest.mark.asyncio
async def test_resolve_dns_failure():
    """Test DNS resolution failure."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(return_value=(b"", b"error"))
        proc_mock.returncode = 1
        mock.return_value = proc_mock

        ip = await scanner._resolve_dns("nonexistent.example.com")

    assert ip is None


@pytest.mark.asyncio
async def test_probe_http_success():
    """Test successful HTTP probe."""
    scanner = SubdomainScanner(timeout=30)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(
            return_value=(
                b"HTTP/1.1 200 OK\r\nServer: nginx/1.18.0\r\n\r\n",
                b"",
            )
        )
        proc_mock.returncode = 0
        mock.return_value = proc_mock

        result = await scanner._probe_http("www.example.com")

    assert result is not None
    assert result.get("alive") is True


@pytest.mark.asyncio
async def test_probe_http_timeout():
    """Test HTTP probe timeout."""
    scanner = SubdomainScanner(timeout=1)

    with patch("asyncio.create_subprocess_exec") as mock:
        proc_mock = AsyncMock()
        proc_mock.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        proc_mock.kill = Mock()
        mock.return_value = proc_mock

        result = await scanner._probe_http("www.example.com")

    assert result is not None
    assert result.get("alive") is False


@pytest.mark.asyncio
async def test_scan_ports_success(mock_tool_executor):
    """Test successful port scanning."""
    scanner = SubdomainScanner(timeout=30)

    ports = await scanner._scan_ports("www.example.com")

    assert isinstance(ports, list)


@pytest.mark.asyncio
async def test_subdomain_scan_tool_single():
    """Test SubdomainScanTool with single subdomain."""
    tool = SubdomainScanTool()

    with patch.object(tool.scanner, "scan", new_callable=AsyncMock) as mock:
        mock.return_value = SubdomainScanResult(
            success=True,
            subdomain="www.example.com",
            is_alive=True,
            http_status=200,
            execution_time=1.0,
        )

        result = await tool.execute({"subdomains": "www.example.com", "probe_http": True})

    assert result["tool"] == "subdomain_scan"
    assert result["subdomain"] == "www.example.com"


@pytest.mark.asyncio
async def test_subdomain_scan_tool_batch():
    """Test SubdomainScanTool with multiple subdomains."""
    tool = SubdomainScanTool()

    with patch.object(tool.scanner, "scan_batch", new_callable=AsyncMock) as mock:
        mock.return_value = BatchScanResult(
            success=True,
            total_scanned=2,
            alive_count=2,
            error_count=0,
            results=[
                SubdomainScanResult(success=True, subdomain="www.example.com", is_alive=True),
                SubdomainScanResult(success=True, subdomain="mail.example.com", is_alive=True),
            ],
        )

        result = await tool.execute(
            {
                "subdomains": ["www.example.com", "mail.example.com"],
                "probe_http": True,
            }
        )

    assert result["tool"] == "subdomain_scan_batch"
    assert result["total_scanned"] == 2


def test_scanner_initialization():
    """Test scanner initialization with different parameters."""
    scanner = SubdomainScanner(timeout=60, ports=[80, 443, 8080])

    assert scanner.timeout == 60
    assert scanner.ports == [80, 443, 8080]


@pytest.mark.asyncio
async def test_scan_batch_with_exceptions():
    """Test batch scan with some exceptions."""
    scanner = SubdomainScanner(timeout=30)

    with patch.object(
        scanner,
        "scan",
        side_effect=[
            SubdomainScanResult(success=True, subdomain="www.example.com", is_alive=True),
            Exception("Scan failed"),
            SubdomainScanResult(success=True, subdomain="mail.example.com", is_alive=True),
        ],
    ):
        result = await scanner.scan_batch(["www.example.com", "fail.example.com", "mail.example.com"])

    assert isinstance(result, BatchScanResult)
    assert result.error_count >= 1
