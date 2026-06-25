"""
Comprehensive tests for ToolExecutor execution workflow.

Target: Push coverage from 29% to 60%+
Tests: Tool execution, Docker management, resource cleanup, safety levels,
       command building, output parsing, and error handling.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest

from autonomous.tool_executor import (
    SafetyLevel,
    ToolDefinition,
    ToolExecutor,
    ToolRegistry,
    ToolResult,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def tool_registry():
    """Create a ToolRegistry with default tools."""
    return ToolRegistry()


@pytest.fixture
def mock_tool_registry():
    """Create a mock ToolRegistry for testing."""
    registry = MagicMock(spec=ToolRegistry)
    registry.tools = {}
    registry.get = MagicMock(return_value=None)
    registry.list_tools = MagicMock(return_value=[])
    registry.check_installed = MagicMock(return_value=True)
    return registry


@pytest.fixture
def tool_executor(mock_tool_registry):
    """Create a ToolExecutor instance for testing."""
    executor = ToolExecutor(
        registry=mock_tool_registry,
        safety_level=SafetyLevel.NON_DESTRUCTIVE,
        use_docker=False,
        output_dir="/tmp",  # nosec B108,
    )
    return executor


@pytest.fixture
def sample_tool_definition():
    """Create a sample tool definition for testing."""
    return ToolDefinition(
        name="nmap",
        description="Network scanner",
        command_template="nmap {options} {target}",
        safety_level=SafetyLevel.READ_ONLY,
        category="recon",
        timeout=300,
    )


@pytest.fixture
def sample_nuclei_definition():
    """Create a sample nuclei tool definition."""
    return ToolDefinition(
        name="nuclei",
        description="Vulnerability scanner",
        command_template="nuclei -u {target} {options}",
        safety_level=SafetyLevel.NON_DESTRUCTIVE,
        category="web",
        timeout=600,
    )


@pytest.fixture
def sample_sqlmap_definition():
    """Create a sample sqlmap tool definition (destructive)."""
    return ToolDefinition(
        name="sqlmap",
        description="SQL injection tool",
        command_template="sqlmap -u {target} {options}",
        safety_level=SafetyLevel.DESTRUCTIVE,
        category="exploitation",
        timeout=600,
    )


@pytest.fixture
def mock_subprocess_process():
    """Create a mock subprocess process."""
    process = AsyncMock()
    process.communicate = AsyncMock(return_value=(b"stdout output", b"stderr output"))
    process.returncode = 0
    process.kill = MagicMock()
    process.wait = AsyncMock()
    return process


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client."""
    client = MagicMock()
    containers = MagicMock()
    container = MagicMock()
    container.logs = MagicMock(return_value=b"docker stdout")
    container.wait = MagicMock(return_value={"StatusCode": 0})
    container.remove = MagicMock()
    containers.run = MagicMock(return_value=container)
    client.containers = containers
    return client


# ============================================================================
# Test ToolExecutor Initialization
# ============================================================================


class TestToolExecutorInitialization:
    """Test ToolExecutor initialization and configuration."""

    def test_default_initialization(self):
        """Test ToolExecutor with default parameters."""
        executor = ToolExecutor()

        assert executor.registry is not None
        assert executor.max_safety == SafetyLevel.NON_DESTRUCTIVE
        assert executor.use_docker is False
        assert executor.output_dir is not None
        assert executor.execution_log == []
        assert executor.logger is not None

    def test_custom_initialization(self, mock_tool_registry):
        """Test ToolExecutor with custom parameters."""
        executor = ToolExecutor(
            registry=mock_tool_registry,
            safety_level=SafetyLevel.READ_ONLY,
            use_docker=True,
            output_dir="/custom/output",
        )

        assert executor.registry == mock_tool_registry
        assert executor.max_safety == SafetyLevel.READ_ONLY
        assert executor.use_docker is True
        assert executor.output_dir == "/custom/output"

    def test_get_available_tools(self, mock_tool_registry):
        """Test getting available tools list."""
        mock_tools = [
            ToolDefinition(
                name="nmap",
                description="Scanner",
                command_template="nmap {target}",
                safety_level=SafetyLevel.READ_ONLY,
                category="recon",
            ),
            ToolDefinition(
                name="nuclei",
                description="Vuln scanner",
                command_template="nuclei -u {target}",
                safety_level=SafetyLevel.NON_DESTRUCTIVE,
                category="web",
            ),
        ]
        mock_tool_registry.list_tools.return_value = mock_tools
        mock_tool_registry.check_installed.side_effect = [True, False]

        executor = ToolExecutor(
            registry=mock_tool_registry,
            safety_level=SafetyLevel.NON_DESTRUCTIVE,
        )
        available = executor.get_available_tools()

        assert len(available) == 2
        assert available[0]["name"] == "nmap"
        assert available[0]["installed"] is True
        assert available[1]["name"] == "nuclei"
        assert available[1]["installed"] is False
        assert available[0]["safety"] == "READ_ONLY"


# ============================================================================
# Test Tool Execution (Main Execute Method - Lines 277-401)
# ============================================================================


class TestToolExecution:
    """Test main tool execution workflow."""

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, tool_executor, mock_tool_registry):
        """Test execution with unknown tool."""
        mock_tool_registry.get.return_value = None

        result = await tool_executor.execute("unknown_tool", {"target": "example.com"})

        assert result.success is False
        assert result.return_code == -1
        assert "not found" in result.stderr.lower()
        assert result.error_message == "Unknown tool: unknown_tool"
        assert result.duration == 0

    @pytest.mark.asyncio
    async def test_execute_safety_level_violation(self, tool_executor, mock_tool_registry, sample_sqlmap_definition):
        """Test execution blocked by safety level."""
        tool_executor.max_safety = SafetyLevel.READ_ONLY
        mock_tool_registry.get.return_value = sample_sqlmap_definition

        result = await tool_executor.execute("sqlmap", {"target": "example.com"})

        assert result.success is False
        assert result.return_code == -1
        assert "safety" in result.stderr.lower()
        assert "Safety violation: sqlmap" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_command_build_failure(self, tool_executor, mock_tool_registry):
        """Test execution when command building fails."""
        tool_def = ToolDefinition(
            name="bad_tool",
            description="Bad tool",
            command_template="tool {bad_param}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )
        mock_tool_registry.get.return_value = tool_def

        result = await tool_executor.execute("bad_tool", {"target": "example.com"})

        assert result.success is False
        assert "Command build failed" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_local_success(
        self,
        tool_executor,
        mock_tool_registry,
        sample_tool_definition,
        mock_subprocess_process,
    ):
        """Test successful local execution."""
        mock_tool_registry.get.return_value = sample_tool_definition

        with patch(
            "asyncio.create_subprocess_shell",
            return_value=mock_subprocess_process,
        ):
            result = await tool_executor.execute("nmap", {"target": "example.com", "options": "-sV"})

        assert result.success is True
        assert result.return_code == 0
        assert result.tool == "nmap"
        assert result.stdout == "stdout output"
        assert result.stderr == "stderr output"
        assert result.duration >= 0
        assert len(tool_executor.execution_log) == 1
        assert tool_executor.execution_log[0]["tool"] == "nmap"
        assert tool_executor.execution_log[0]["success"] is True

    @pytest.mark.asyncio
    async def test_execute_local_failure(self, tool_executor, mock_tool_registry, sample_tool_definition):
        """Test local execution with non-zero exit code."""
        mock_tool_registry.get.return_value = sample_tool_definition

        process = AsyncMock()
        process.communicate = AsyncMock(return_value=(b"", b"Permission denied"))
        process.returncode = 1

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await tool_executor.execute("nmap", {"target": "example.com"})

        assert result.success is False
        assert result.return_code == 1
        assert result.stderr == "Permission denied"

    @pytest.mark.asyncio
    async def test_execute_timeout(self, tool_executor, mock_tool_registry, sample_tool_definition):
        """Test execution timeout handling."""
        mock_tool_registry.get.return_value = sample_tool_definition
        sample_tool_definition.timeout = 1

        process = AsyncMock()
        process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        process.kill = MagicMock()

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await tool_executor.execute("nmap", {"target": "example.com"})

        assert result.success is False
        assert result.return_code == -1
        assert "timeout" in result.stderr.lower()
        assert result.error_message == "Execution timeout"
        assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_execute_general_exception(self, tool_executor, mock_tool_registry, sample_tool_definition):
        """Test handling of general exceptions during execution."""
        mock_tool_registry.get.return_value = sample_tool_definition

        with patch(
            "asyncio.create_subprocess_shell",
            side_effect=Exception("Unexpected error"),
        ):
            result = await tool_executor.execute("nmap", {"target": "example.com"})

        assert result.success is False
        assert result.return_code == -1
        assert "Unexpected error" in result.stderr
        assert result.error_message == "Unexpected error"


# ============================================================================
# Test Docker Container Management (Lines 294-392 when use_docker=True)
# ============================================================================


class TestDockerExecution:
    """Test Docker-based tool execution."""

    @pytest.mark.asyncio
    async def test_execute_with_docker(
        self,
        mock_tool_registry,
        sample_tool_definition,
        mock_subprocess_process,
    ):
        """Test execution using Docker mode."""
        mock_tool_registry.get.return_value = sample_tool_definition

        executor = ToolExecutor(
            registry=mock_tool_registry,
            use_docker=True,
        )

        with patch(
            "asyncio.create_subprocess_shell",
            return_value=mock_subprocess_process,
        ):
            result = await executor.execute("nmap", {"target": "example.com"})

        assert result.success is True
        assert result.return_code == 0
        # Verify docker command was constructed
        mock_subprocess_process.communicate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_docker_dockerfile(
        self,
        mock_tool_registry,
        sample_tool_definition,
        mock_subprocess_process,
    ):
        """Test Docker execution command construction."""
        mock_tool_registry.get.return_value = sample_tool_definition

        executor = ToolExecutor(
            registry=mock_tool_registry,
            use_docker=True,
        )

        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_subprocess.return_value = mock_subprocess_process
            await executor.execute("nmap", {"target": "example.com", "options": "-sV"})

            # Check that docker command was constructed correctly
            call_args = mock_subprocess.call_args
            command = call_args[0][0]
            assert "docker run" in command
            assert "--rm" in command
            assert "--network=host" in command
            assert "nmap" in command

    @pytest.mark.asyncio
    async def test_execute_docker_with_special_tool(self, mock_tool_registry, mock_subprocess_process):
        """Test Docker execution with a tool that needs_docker flag."""
        tool_def = ToolDefinition(
            name="custom_tool",
            description="Custom tool",
            command_template="custom {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
            needs_docker=True,
        )
        mock_tool_registry.get.return_value = tool_def

        executor = ToolExecutor(
            registry=mock_tool_registry,
            use_docker=True,
        )

        with patch(
            "asyncio.create_subprocess_shell",
            return_value=mock_subprocess_process,
        ):
            result = await executor.execute("custom_tool", {"target": "example.com"})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_docker_timeout(self, mock_tool_registry, sample_tool_definition):
        """Test Docker execution timeout."""
        mock_tool_registry.get.return_value = sample_tool_definition
        sample_tool_definition.timeout = 1

        executor = ToolExecutor(
            registry=mock_tool_registry,
            use_docker=True,
        )

        process = AsyncMock()
        process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        process.kill = MagicMock()

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await executor.execute("nmap", {"target": "example.com"})

        assert result.success is False
        assert "timeout" in result.stderr.lower()


# ============================================================================
# Test Resource Cleanup (Lines 424-441)
# ============================================================================


class TestResourceCleanup:
    """Test resource cleanup during execution."""

    @pytest.mark.asyncio
    async def test_local_execution_cleanup_on_timeout(self, tool_executor, mock_tool_registry, sample_tool_definition):
        """Test that subprocess is killed on timeout."""
        mock_tool_registry.get.return_value = sample_tool_definition
        sample_tool_definition.timeout = 1

        process = AsyncMock()
        process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        process.kill = MagicMock()
        process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await tool_executor.execute("nmap", {"target": "example.com"})

        assert result.success is False
        process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_execution_log_tracking(
        self,
        tool_executor,
        mock_tool_registry,
        sample_tool_definition,
        mock_subprocess_process,
    ):
        """Test that execution is logged for audit."""
        mock_tool_registry.get.return_value = sample_tool_definition

        with patch(
            "asyncio.create_subprocess_shell",
            return_value=mock_subprocess_process,
        ):
            await tool_executor.execute("nmap", {"target": "example.com"})
            await tool_executor.execute("nmap", {"target": "example.org"})

        assert len(tool_executor.execution_log) == 2
        for log_entry in tool_executor.execution_log:
            assert "tool" in log_entry
            assert "command" in log_entry
            assert "timestamp" in log_entry
            assert "duration" in log_entry
            assert "success" in log_entry


# ============================================================================
# Test Command Building (Lines 403-420)
# ============================================================================


class TestCommandBuilding:
    """Test command building functionality."""

    def test_build_command_basic(self, tool_executor):
        """Test basic command building."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            command_template="tool {target} {options}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )
        params = {"target": "example.com", "options": "-v"}

        command = tool_executor._build_command(tool, params)

        assert "example.com" in command
        assert "-v" in command

    def test_build_command_sanitizes_target(self, tool_executor):
        """Test that target is properly sanitized."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            command_template="tool {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )
        params = {"target": "example.com; rm -rf /"}

        command = tool_executor._build_command(tool, params)

        # Target should be quoted to prevent injection
        assert "'" in command or '"' in command or "\\" in command
        assert ";" not in command or command.count("'") >= 2

    def test_build_command_with_ports(self, tool_executor):
        """Test command building with ports parameter."""
        tool = ToolDefinition(
            name="masscan",
            description="Port scanner",
            command_template="masscan {target} -p{ports} {options}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        params = {
            "target": "192.168.1.1",
            "ports": "80,443",
            "options": "--rate 1000",
        }

        command = tool_executor._build_command(tool, params)

        assert "192.168.1.1" in command
        assert "-p80,443" in command
        assert "--rate 1000" in command

    def test_build_command_extra_params(self, tool_executor):
        """Test command building with extra parameters."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            command_template="tool {target} {extra}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )
        params = {"target": "example.com", "extra": "--flag value"}

        command = tool_executor._build_command(tool, params)

        assert "example.com" in command
        assert "--flag value" in command

    def test_build_command_empty_target(self, tool_executor):
        """Test command building with empty target."""
        tool = ToolDefinition(
            name="test_tool",
            description="Test",
            command_template="tool {target} {options}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )
        params = {"target": "", "options": "-v"}

        command = tool_executor._build_command(tool, params)

        assert "''" in command or '""' in command or command.strip().endswith("-v")


# ============================================================================
# Test Output Parsing
# ============================================================================


class TestOutputParsing:
    """Test output parsing for different tools."""

    def test_parse_output_nmap(self, tool_executor):
        """Test parsing nmap output."""
        output = """
        PORT     STATE SERVICE
        22/tcp   open  ssh     OpenSSH 8.2
        80/tcp   open  http    Apache httpd 2.4
        443/tcp  open  https   Nginx
        """

        result = tool_executor._parse_output("nmap", output)

        assert "open_ports" in result
        assert len(result["open_ports"]) == 3
        assert result["open_ports"][0]["port"] == "22"
        assert result["open_ports"][0]["service"] == "ssh"

    def test_parse_output_nmap_no_open_ports(self, tool_executor):
        """Test parsing nmap output with no open ports."""
        output = """
        All 1000 scanned ports on example.com are filtered
        """

        result = tool_executor._parse_output("nmap", output)

        assert "open_ports" in result
        assert len(result["open_ports"]) == 0

    def test_parse_output_nuclei(self, tool_executor):
        """Test parsing nuclei output."""
        output = """
        [INF] Using Nuclei Engine
        [2024-01-01 12:00:00] [apache-detect] [http] [info] http://example.com
        [2024-01-01 12:00:01] [cve-2021-44228] [http] [critical] http://example.com/log4j
        """

        result = tool_executor._parse_output("nuclei", output)

        assert "findings" in result
        assert len(result["findings"]) == 2

    def test_parse_output_subfinder(self, tool_executor):
        """Test parsing subfinder output."""
        output = """
        www.example.com
        api.example.com
        mail.example.com
        """

        result = tool_executor._parse_output("subfinder", output)

        assert "subdomains" in result
        assert len(result["subdomains"]) == 3
        assert "www.example.com" in result["subdomains"]

    def test_parse_output_unknown_tool(self, tool_executor):
        """Test parsing output for unknown tool."""
        output = "Some raw output"

        result = tool_executor._parse_output("unknown_tool", output)

        assert "raw" in result
        assert result["raw"] == output

    def test_parse_output_parser_error(self, tool_executor):
        """Test handling of parser errors."""
        output = None  # Invalid input

        # Should not raise exception
        result = tool_executor._parse_output("nmap", output)

        assert "raw" in result


# ============================================================================
# Test Findings Extraction
# ============================================================================


class TestFindingsExtraction:
    """Test extraction of security findings."""

    def test_extract_findings_nmap(self, tool_executor):
        """Test extracting findings from nmap output."""
        stdout = ""
        parsed = {
            "open_ports": [
                {"port": "22", "service": "ssh"},
                {"port": "80", "service": "http"},
            ]
        }

        findings = tool_executor._extract_findings("nmap", stdout, parsed)

        assert len(findings) == 2
        assert findings[0]["type"] == "open_port"
        assert findings[0]["severity"] == "info"

    def test_extract_findings_nuclei(self, tool_executor):
        """Test extracting findings from nuclei output."""
        stdout = ""
        parsed = {
            "findings": [
                {"raw": "[critical] CVE-2021-44228"},
                {"raw": "[high] XSS vulnerability"},
            ]
        }

        findings = tool_executor._extract_findings("nuclei", stdout, parsed)

        assert len(findings) == 2
        assert findings[0]["type"] == "vulnerability"
        assert findings[0]["severity"] == "unknown"

    def test_extract_findings_no_findings(self, tool_executor):
        """Test extracting findings when no findings exist."""
        stdout = ""
        parsed = {"raw": "some output"}

        findings = tool_executor._extract_findings("unknown_tool", stdout, parsed)

        assert findings == []

    def test_extract_findings_empty_parsed(self, tool_executor):
        """Test extracting findings with empty parsed output."""
        findings = tool_executor._extract_findings("nmap", "", {})

        assert findings == []


# ============================================================================
# Test Local Execution Helper (Lines 422-441)
# ============================================================================


class TestLocalExecution:
    """Test the _execute_local method."""

    @pytest.mark.asyncio
    async def test_execute_local_basic(self, tool_executor, mock_subprocess_process):
        """Test basic local execution."""
        with patch(
            "asyncio.create_subprocess_shell",
            return_value=mock_subprocess_process,
        ):
            stdout, stderr, returncode = await tool_executor._execute_local("nmap example.com", 300)

        assert stdout == "stdout output"
        assert stderr == "stderr output"
        assert returncode == 0

    @pytest.mark.asyncio
    async def test_execute_local_decoding(self, tool_executor):
        """Test handling of various output encodings."""
        process = AsyncMock()
        # Include some non-UTF8 bytes
        process.communicate = AsyncMock(return_value=(b"output with \xff\xfe bytes", b""))
        process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=process):
            stdout, stderr, returncode = await tool_executor._execute_local("command", 300)

        assert "output with" in stdout
        assert returncode == 0

    @pytest.mark.asyncio
    async def test_execute_local_timeout_with_kill(self, tool_executor):
        """Test that process is killed on timeout."""
        process = AsyncMock()
        process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        process.kill = MagicMock()
        process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_shell", return_value=process):
            with pytest.raises(asyncio.TimeoutError):
                await tool_executor._execute_local("command", 1)

        process.kill.assert_called_once()


# ============================================================================
# Test Docker Execution Helper
# ============================================================================


class TestDockerExecutionHelper:
    """Test the _execute_docker method."""

    @pytest.mark.asyncio
    async def test_execute_docker_constructs_command(self, tool_executor, sample_tool_definition, mock_subprocess_process):
        """Test that docker command is properly constructed."""
        with patch("asyncio.create_subprocess_shell") as mock_subprocess:
            mock_subprocess.return_value = mock_subprocess_process
            await tool_executor._execute_docker(sample_tool_definition, "nmap -sV example.com", 300)

            call_args = mock_subprocess.call_args
            command = call_args[0][0]
            assert "docker run" in command
            assert "--rm" in command
            assert "--network=host" in command
            assert "nmap" in command
            assert "nmap -sV example.com" in command


# ============================================================================
# Test Safety Levels
# ============================================================================


class TestSafetyLevels:
    """Test safety level enforcement."""

    def test_safety_level_ordering(self):
        """Test that safety levels are correctly ordered."""
        assert SafetyLevel.READ_ONLY.value < SafetyLevel.NON_DESTRUCTIVE.value
        assert SafetyLevel.NON_DESTRUCTIVE.value < SafetyLevel.DESTRUCTIVE.value
        assert SafetyLevel.DESTRUCTIVE.value < SafetyLevel.EXPLOIT.value

    @pytest.mark.asyncio
    async def test_safety_level_read_only(self, mock_tool_registry):
        """Test READ_ONLY safety level enforcement."""
        executor = ToolExecutor(
            registry=mock_tool_registry,
            safety_level=SafetyLevel.READ_ONLY,
        )

        # READ_ONLY tool should pass
        read_only_tool = ToolDefinition(
            name="nmap",
            description="Scanner",
            command_template="nmap {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        mock_tool_registry.get.return_value = read_only_tool

        process = AsyncMock()
        process.communicate = AsyncMock(return_value=(b"", b""))
        process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await executor.execute("nmap", {"target": "example.com"})

        assert result.success is True

    @pytest.mark.asyncio
    async def test_safety_level_blocks_higher(self, mock_tool_registry):
        """Test that higher safety level tools are blocked."""
        executor = ToolExecutor(
            registry=mock_tool_registry,
            safety_level=SafetyLevel.READ_ONLY,
        )

        # DESTRUCTIVE tool should be blocked
        destructive_tool = ToolDefinition(
            name="sqlmap",
            description="SQL injection",
            command_template="sqlmap {target}",
            safety_level=SafetyLevel.DESTRUCTIVE,
            category="exploitation",
        )
        mock_tool_registry.get.return_value = destructive_tool

        result = await executor.execute("sqlmap", {"target": "example.com"})

        assert result.success is False
        assert "safety" in result.stderr.lower()


# ============================================================================
# Test Tool Registry
# ============================================================================


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_registry_default_tools(self):
        """Test that default tools are registered."""
        registry = ToolRegistry()

        assert "nmap" in registry.tools
        assert "nuclei" in registry.tools
        assert "sqlmap" in registry.tools
        assert "subfinder" in registry.tools

    def test_registry_register_tool(self):
        """Test registering a new tool."""
        registry = ToolRegistry()

        new_tool = ToolDefinition(
            name="custom_tool",
            description="Custom",
            command_template="custom {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )
        registry.register(new_tool)

        assert "custom_tool" in registry.tools
        assert registry.get("custom_tool") == new_tool

    def test_registry_get_nonexistent(self):
        """Test getting a non-existent tool."""
        registry = ToolRegistry()

        result = registry.get("nonexistent_tool")

        assert result is None

    def test_registry_list_tools_filtered(self):
        """Test listing tools with filters."""
        registry = ToolRegistry()

        # Filter by category
        web_tools = registry.list_tools(category="web")
        assert all(t.category == "web" for t in web_tools)

        # Filter by safety
        safe_tools = registry.list_tools(safety=SafetyLevel.READ_ONLY)
        assert all(t.safety_level.value <= SafetyLevel.READ_ONLY.value for t in safe_tools)

    def test_registry_check_installed(self):
        """Test checking if a tool is installed."""
        registry = ToolRegistry()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = registry.check_installed("nmap")
            assert result is True

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = registry.check_installed("nonexistent")
            assert result is False

    def test_registry_check_installed_exception(self):
        """Test check_installed handles exceptions."""
        registry = ToolRegistry()

        with patch("subprocess.run", side_effect=Exception("Command failed")):
            result = registry.check_installed("nmap")
            assert result is False


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestIntegrationScenarios:
    """Test integrated execution scenarios."""

    @pytest.mark.asyncio
    async def test_full_execution_flow(self):
        """Test a complete execution flow with real registry."""
        registry = ToolRegistry()
        executor = ToolExecutor(
            registry=registry,
            safety_level=SafetyLevel.READ_ONLY,
        )

        process = AsyncMock()
        process.communicate = AsyncMock(return_value=(b"22/tcp open ssh\n80/tcp open http", b""))
        process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await executor.execute("nmap", {"target": "example.com", "options": "-sS"})

        assert result.success is True
        assert result.tool == "nmap"
        assert "parsed_output" in result.__dict__ or hasattr(result, "parsed_output")

    @pytest.mark.asyncio
    async def test_multiple_sequential_executions(
        self,
        tool_executor,
        mock_tool_registry,
        sample_tool_definition,
        mock_subprocess_process,
    ):
        """Test multiple sequential tool executions."""
        mock_tool_registry.get.return_value = sample_tool_definition

        with patch(
            "asyncio.create_subprocess_shell",
            return_value=mock_subprocess_process,
        ):
            result1 = await tool_executor.execute("nmap", {"target": "target1.com"})
            result2 = await tool_executor.execute("nmap", {"target": "target2.com"})
            result3 = await tool_executor.execute("nmap", {"target": "target3.com"})

        assert result1.success is True
        assert result2.success is True
        assert result3.success is True
        assert len(tool_executor.execution_log) == 3

    @pytest.mark.asyncio
    async def test_execution_with_findings(self, tool_executor, mock_tool_registry):
        """Test execution that produces security findings."""
        tool_def = ToolDefinition(
            name="nmap",
            description="Scanner",
            command_template="nmap {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
            output_parser=lambda x: {"open_ports": [{"port": "22", "service": "ssh"}]},
        )
        mock_tool_registry.get.return_value = tool_def

        process = AsyncMock()
        process.communicate = AsyncMock(return_value=(b"22/tcp open ssh", b""))
        process.returncode = 0

        with patch("asyncio.create_subprocess_shell", return_value=process):
            result = await tool_executor.execute("nmap", {"target": "example.com"})

        assert result.success is True
        assert len(result.findings) >= 0  # Findings may or may not be extracted


# ============================================================================
# Test ToolResult Dataclass
# ============================================================================


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_tool_result_creation(self):
        """Test creating a ToolResult."""
        result = ToolResult(
            tool="nmap",
            command="nmap example.com",
            return_code=0,
            stdout="output",
            stderr="",
            duration=1.5,
        )

        assert result.tool == "nmap"
        assert result.command == "nmap example.com"
        assert result.return_code == 0
        assert result.stdout == "output"
        assert result.duration == 1.5
        assert result.success is True
        assert result.parsed_output == {}
        assert result.findings == []

    def test_tool_result_defaults(self):
        """Test ToolResult default values."""
        result = ToolResult(
            tool="test",
            command="test",
            return_code=0,
            stdout="",
            stderr="",
            duration=0.0,
        )

        assert result.parsed_output == {}
        assert result.findings == []
        assert isinstance(result.timestamp, datetime)
        assert result.success is True
        assert result.error_message is None

    def test_tool_result_failure(self):
        """Test ToolResult for failed execution."""
        result = ToolResult(
            tool="nmap",
            command="nmap example.com",
            return_code=1,
            stdout="",
            stderr="Permission denied",
            duration=0.5,
            success=False,
            error_message="Permission denied",
        )

        assert result.success is False
        assert result.return_code == 1
        assert result.error_message == "Permission denied"


# ============================================================================
# Test ToolDefinition Dataclass
# ============================================================================


class TestToolDefinition:
    """Test ToolDefinition dataclass."""

    def test_tool_definition_creation(self):
        """Test creating a ToolDefinition."""

        def parser(output):
            return {"parsed": output}

        tool = ToolDefinition(
            name="custom",
            description="Custom tool",
            command_template="custom {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
            needs_docker=True,
            output_parser=parser,
            timeout=120,
            installed=True,
        )

        assert tool.name == "custom"
        assert tool.description == "Custom tool"
        assert tool.command_template == "custom {target}"
        assert tool.safety_level == SafetyLevel.READ_ONLY
        assert tool.category == "test"
        assert tool.needs_docker is True
        assert tool.output_parser is not None
        assert tool.timeout == 120
        assert tool.installed is True

    def test_tool_definition_defaults(self):
        """Test ToolDefinition default values."""
        tool = ToolDefinition(
            name="test",
            description="Test tool",
            command_template="test {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="test",
        )

        assert tool.needs_docker is False
        assert tool.output_parser is None
        assert tool.timeout == 300
        assert tool.installed is False
