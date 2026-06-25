"""
Comprehensive tests for autonomous/tool_executor.py
Target: 80%+ coverage
"""

import asyncio
import subprocess
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from autonomous.tool_executor import (
    SafetyLevel,
    ToolDefinition,
    ToolExecutor,
    ToolRegistry,
    ToolResult,
)


# ============================================================================
# SafetyLevel Enum Tests
# ============================================================================
class TestSafetyLevel:
    """Tests for SafetyLevel enum."""

    def test_safety_level_values(self):
        """Test that SafetyLevel enum has correct values."""
        assert SafetyLevel.READ_ONLY.value == 1
        assert SafetyLevel.NON_DESTRUCTIVE.value == 2
        assert SafetyLevel.DESTRUCTIVE.value == 3
        assert SafetyLevel.EXPLOIT.value == 4

    def test_safety_level_ordering(self):
        """Test that safety levels can be compared."""
        assert SafetyLevel.READ_ONLY.value < SafetyLevel.NON_DESTRUCTIVE.value
        assert SafetyLevel.NON_DESTRUCTIVE.value < SafetyLevel.DESTRUCTIVE.value
        assert SafetyLevel.DESTRUCTIVE.value < SafetyLevel.EXPLOIT.value

    def test_safety_level_from_value(self):
        """Test creating SafetyLevel from value."""
        assert SafetyLevel(1) == SafetyLevel.READ_ONLY
        assert SafetyLevel(2) == SafetyLevel.NON_DESTRUCTIVE
        assert SafetyLevel(3) == SafetyLevel.DESTRUCTIVE
        assert SafetyLevel(4) == SafetyLevel.EXPLOIT


# ============================================================================
# ToolResult Dataclass Tests
# ============================================================================
class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_tool_result_defaults(self):
        """Test ToolResult with default values."""
        result = ToolResult(
            tool="nmap",
            command="nmap -sS target",
            return_code=0,
            stdout="output",
            stderr="",
            duration=1.5,
        )
        assert result.tool == "nmap"
        assert result.command == "nmap -sS target"
        assert result.return_code == 0
        assert result.stdout == "output"
        assert result.stderr == ""
        assert result.duration == 1.5
        assert result.parsed_output == {}
        assert result.findings == []
        assert result.success is True
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)

    def test_tool_result_custom_values(self):
        """Test ToolResult with custom values."""
        result = ToolResult(
            tool="sqlmap",
            command="sqlmap -u target",
            return_code=1,
            stdout="",
            stderr="error",
            duration=2.0,
            parsed_output={"key": "value"},
            findings=[{"type": "vuln"}],
            success=False,
            error_message="Execution failed",
        )
        assert result.parsed_output == {"key": "value"}
        assert result.findings == [{"type": "vuln"}]
        assert result.success is False
        assert result.error_message == "Execution failed"

    def test_tool_result_failure(self):
        """Test ToolResult for failed execution."""
        result = ToolResult(
            tool="nmap",
            command="nmap target",
            return_code=-1,
            stdout="",
            stderr="timeout",
            duration=300.0,
            success=False,
            error_message="Timeout",
        )
        assert result.return_code == -1
        assert result.success is False


# ============================================================================
# ToolDefinition Dataclass Tests
# ============================================================================
class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_tool_definition_defaults(self):
        """Test ToolDefinition with default values."""
        tool = ToolDefinition(
            name="nmap",
            description="Network scanner",
            command_template="nmap {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        assert tool.name == "nmap"
        assert tool.description == "Network scanner"
        assert tool.command_template == "nmap {target}"
        assert tool.safety_level == SafetyLevel.READ_ONLY
        assert tool.category == "recon"
        assert tool.needs_docker is False
        assert tool.output_parser is None
        assert tool.timeout == 300
        assert tool.installed is False

    def test_tool_definition_custom_values(self):
        """Test ToolDefinition with custom values."""

        def parser(x):
            return x

        tool = ToolDefinition(
            name="sqlmap",
            description="SQL injection tool",
            command_template="sqlmap -u {target} {options}",
            safety_level=SafetyLevel.DESTRUCTIVE,
            category="exploitation",
            needs_docker=True,
            output_parser=parser,
            timeout=600,
            installed=True,
        )
        assert tool.needs_docker is True
        assert tool.output_parser == parser
        assert tool.timeout == 600
        assert tool.installed is True


# ============================================================================
# ToolRegistry Tests
# ============================================================================
class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_registry_initialization(self):
        """Test that registry initializes with default tools."""
        registry = ToolRegistry()
        # Check that default tools are registered
        expected_tools = [
            "nmap",
            "masscan",
            "nuclei",
            "ffuf",
            "gospider",
            "sqlmap",
            "subfinder",
            "amass",
            "dnsrecon",
            "sslscan",
            "gobuster",
            "nikto",
        ]
        for tool_name in expected_tools:
            assert tool_name in registry.tools

    def test_register_tool(self):
        """Test registering a new tool."""
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="custom_tool",
            description="Custom tool",
            command_template="custom {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="custom",
        )
        registry.register(tool)
        assert "custom_tool" in registry.tools
        assert registry.get("custom_tool") == tool

    def test_get_existing_tool(self):
        """Test getting an existing tool."""
        registry = ToolRegistry()
        tool = registry.get("nmap")
        assert tool is not None
        assert tool.name == "nmap"
        assert tool.category == "recon"
        assert tool.safety_level == SafetyLevel.READ_ONLY

    def test_get_nonexistent_tool(self):
        """Test getting a nonexistent tool."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools_no_filters(self):
        """Test listing all tools without filters."""
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert len(tools) == 12  # All default tools

    def test_list_tools_by_category(self):
        """Test listing tools filtered by category."""
        registry = ToolRegistry()
        recon_tools = registry.list_tools(category="recon")
        web_tools = registry.list_tools(category="web")
        exploit_tools = registry.list_tools(category="exploitation")

        # Check recon tools
        recon_names = {t.name for t in recon_tools}
        assert "nmap" in recon_names
        assert "masscan" in recon_names
        assert "subfinder" in recon_names
        assert "amass" in recon_names
        assert "dnsrecon" in recon_names

        # Check web tools
        web_names = {t.name for t in web_tools}
        assert "nuclei" in web_names
        assert "ffuf" in web_names
        assert "gospider" in web_names
        assert "sslscan" in web_names
        assert "gobuster" in web_names
        assert "nikto" in web_names

        # Check exploitation tools
        exploit_names = {t.name for t in exploit_tools}
        assert "sqlmap" in exploit_names

    def test_list_tools_by_safety_level(self):
        """Test listing tools filtered by safety level."""
        registry = ToolRegistry()

        # Get tools at or below READ_ONLY level
        safe_tools = registry.list_tools(safety=SafetyLevel.READ_ONLY)
        safe_names = {t.name for t in safe_tools}
        assert "nmap" in safe_names
        assert "masscan" in safe_names
        assert "subfinder" in safe_names
        assert "sqlmap" not in safe_names  # DESTRUCTIVE
        assert "nuclei" not in safe_names  # NON_DESTRUCTIVE

        # Get tools at or below NON_DESTRUCTIVE level
        normal_tools = registry.list_tools(safety=SafetyLevel.NON_DESTRUCTIVE)
        normal_names = {t.name for t in normal_tools}
        assert "nmap" in normal_names
        assert "nuclei" in normal_names
        assert "sqlmap" not in normal_names  # DESTRUCTIVE

        # Get tools at or below DESTRUCTIVE level
        elevated_tools = registry.list_tools(safety=SafetyLevel.DESTRUCTIVE)
        elevated_names = {t.name for t in elevated_tools}
        assert "nmap" in elevated_names
        assert "nuclei" in elevated_names
        assert "sqlmap" in elevated_names

    def test_list_tools_combined_filters(self):
        """Test listing tools with both category and safety filters."""
        registry = ToolRegistry()
        tools = registry.list_tools(category="recon", safety=SafetyLevel.READ_ONLY)
        names = {t.name for t in tools}
        assert "nmap" in names
        assert "masscan" in names
        assert "sqlmap" not in names  # Wrong category and safety
        assert "nuclei" not in names  # Wrong category

    @patch("subprocess.run")
    def test_check_installed_true(self, mock_run):
        """Test check_installed when tool is installed."""
        mock_run.return_value = Mock(return_code=0)
        registry = ToolRegistry()
        assert registry.check_installed("nmap") is True
        mock_run.assert_called_once_with(["which", "nmap"], capture_output=True, timeout=5)

    @patch("subprocess.run")
    def test_check_installed_false(self, mock_run):
        """Test check_installed when tool is not installed."""
        mock_run.return_value = Mock(return_code=1)
        registry = ToolRegistry()
        assert registry.check_installed("nonexistent") is False

    @patch("subprocess.run")
    def test_check_installed_exception(self, mock_run):
        """Test check_installed when subprocess raises exception."""
        mock_run.side_effect = subprocess.SubprocessError("Error")
        registry = ToolRegistry()
        assert registry.check_installed("nmap") is False


# ============================================================================
# ToolExecutor Initialization Tests
# ============================================================================
class TestToolExecutorInit:
    """Tests for ToolExecutor initialization."""

    def test_default_initialization(self):
        """Test ToolExecutor with default parameters."""
        executor = ToolExecutor()
        assert executor.registry is not None
        assert executor.max_safety == SafetyLevel.NON_DESTRUCTIVE
        assert executor.use_docker is False
        assert executor.execution_log == []

    def test_custom_initialization(self):
        """Test ToolExecutor with custom parameters."""
        registry = ToolRegistry()
        executor = ToolExecutor(
            registry=registry,
            safety_level=SafetyLevel.READ_ONLY,
            use_docker=True,
            output_dir="/custom/dir",
        )
        assert executor.registry == registry
        assert executor.max_safety == SafetyLevel.READ_ONLY
        assert executor.use_docker is True
        assert executor.output_dir == "/custom/dir"

    def test_tempdir_default(self):
        """Test that default output_dir is temp directory."""
        executor = ToolExecutor()
        assert executor.output_dir == tempfile.gettempdir()


# ============================================================================
# ToolExecutor.get_available_tools Tests
# ============================================================================
class TestToolExecutorGetAvailableTools:
    """Tests for get_available_tools method."""

    @patch.object(ToolRegistry, "check_installed")
    def test_get_available_tools(self, mock_check):
        """Test getting available tools for LLM."""
        mock_check.side_effect = lambda name: name in ["nmap", "nuclei"]
        executor = ToolExecutor(safety_level=SafetyLevel.NON_DESTRUCTIVE)
        tools = executor.get_available_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "category" in tool
            assert "safety" in tool
            assert "installed" in tool

        # Check that nmap is marked installed
        nmap_tool = next((t for t in tools if t["name"] == "nmap"), None)
        assert nmap_tool is not None
        assert nmap_tool["installed"] is True

        # Check that sqlmap is not in list (safety level too high)
        sqlmap_tool = next((t for t in tools if t["name"] == "sqlmap"), None)
        assert sqlmap_tool is None

    @patch.object(ToolRegistry, "check_installed")
    def test_get_available_tools_respects_safety(self, mock_check):
        """Test that safety level limits returned tools."""
        mock_check.return_value = True

        # With READ_ONLY safety
        executor_readonly = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        readonly_tools = executor_readonly.get_available_tools()
        readonly_names = {t["name"] for t in readonly_tools}
        assert "nmap" in readonly_names
        assert "nuclei" not in readonly_names  # NON_DESTRUCTIVE
        assert "sqlmap" not in readonly_names  # DESTRUCTIVE

        # With EXPLOIT safety (all tools allowed)
        executor_exploit = ToolExecutor(safety_level=SafetyLevel.EXPLOIT)
        exploit_tools = executor_exploit.get_available_tools()
        exploit_names = {t["name"] for t in exploit_tools}
        assert "nmap" in exploit_names
        assert "nuclei" in exploit_names
        assert "sqlmap" in exploit_names


# ============================================================================
# ToolExecutor._build_command Tests
# ============================================================================
class TestToolExecutorBuildCommand:
    """Tests for _build_command method."""

    def test_build_command_basic(self):
        """Test building basic command."""
        executor = ToolExecutor()
        tool = ToolDefinition(
            name="nmap",
            description="Network scanner",
            command_template="nmap {options} {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        command = executor._build_command(tool, {"target": "scanme.nmap.org", "options": "-sS"})
        assert "nmap" in command
        assert "scanme.nmap.org" in command
        assert "-sS" in command

    def test_build_command_with_special_chars(self):
        """Test building command with special characters in target."""
        executor = ToolExecutor()
        tool = ToolDefinition(
            name="nmap",
            description="Network scanner",
            command_template="nmap {options} {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        # Target with special characters should be quoted
        command = executor._build_command(tool, {"target": "target; rm -rf /", "options": ""})
        assert "'target; rm -rf /'" in command or '"target; rm -rf /"' in command

    def test_build_command_with_ports(self):
        """Test building command with ports parameter."""
        executor = ToolExecutor()
        tool = ToolDefinition(
            name="masscan",
            description="Port scanner",
            command_template="masscan {target} -p{ports} {options}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        command = executor._build_command(tool, {"target": "1.2.3.4", "ports": "80,443", "options": "--rate 1000"})
        assert "masscan" in command
        assert "1.2.3.4" in command
        assert "-p80,443" in command
        assert "--rate 1000" in command

    def test_build_command_empty_target(self):
        """Test building command with empty target."""
        executor = ToolExecutor()
        tool = ToolDefinition(
            name="nmap",
            description="Network scanner",
            command_template="nmap {options} {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )
        command = executor._build_command(tool, {"target": "", "options": "-sS"})
        assert "nmap" in command
        assert "-sS" in command

    def test_build_command_custom_params(self):
        """Test building command with custom parameters."""
        executor = ToolExecutor()
        tool = ToolDefinition(
            name="custom",
            description="Custom tool",
            command_template="custom {target} {extra}",
            safety_level=SafetyLevel.READ_ONLY,
            category="custom",
        )
        command = executor._build_command(tool, {"target": "host", "options": "", "extra": "--verbose"})
        assert "custom" in command
        assert "host" in command
        assert "--verbose" in command


# ============================================================================
# ToolExecutor.execute Tests - Error Cases
# ============================================================================
class TestToolExecutorExecuteErrors:
    """Tests for execute method error cases."""

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing an unknown tool."""
        executor = ToolExecutor()
        result = await executor.execute("unknown_tool", {})

        assert result.success is False
        assert result.return_code == -1
        assert "not found" in result.stderr.lower()
        assert "Unknown tool" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_safety_violation(self):
        """Test executing tool that exceeds safety level."""
        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("sqlmap", {"target": "test.com"})

        assert result.success is False
        assert result.return_code == -1
        assert "safety" in result.stderr.lower()
        assert "Safety violation" in result.error_message

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_build_command")
    async def test_execute_command_build_error(self, mock_build):
        """Test handling error during command building."""
        mock_build.side_effect = ValueError("Invalid parameter")
        executor = ToolExecutor(safety_level=SafetyLevel.EXPLOIT)
        result = await executor.execute("nmap", {"target": "test.com"})

        assert result.success is False
        assert result.return_code == -1
        assert "Invalid parameter" in result.stderr
        assert "Command build failed" in result.error_message


# ============================================================================
# ToolExecutor.execute Tests - Local Execution
# ============================================================================
class TestToolExecutorExecuteLocal:
    """Tests for execute method with local execution."""

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    @patch.object(ToolExecutor, "_parse_output")
    @patch.object(ToolExecutor, "_extract_findings")
    async def test_execute_local_success(self, mock_extract, mock_parse, mock_execute):
        """Test successful local execution."""
        mock_execute.return_value = ("stdout content", "stderr content", 0)
        mock_parse.return_value = {"open_ports": ["80"]}
        mock_extract.return_value = [{"type": "port"}]

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is True
        assert result.return_code == 0
        assert result.stdout == "stdout content"
        assert result.stderr == "stderr content"
        assert result.parsed_output == {"open_ports": ["80"]}
        assert result.findings == [{"type": "port"}]
        assert result.duration > 0

        # Verify execution was logged
        assert len(executor.execution_log) == 1
        log_entry = executor.execution_log[0]
        assert log_entry["tool"] == "nmap"
        assert log_entry["success"] is True

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_local_failure(self, mock_execute):
        """Test local execution with non-zero return code."""
        mock_execute.return_value = ("", "permission denied", 1)

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is False
        assert result.return_code == 1
        assert result.stderr == "permission denied"

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_local_timeout(self, mock_execute):
        """Test local execution timeout handling."""
        mock_execute.side_effect = asyncio.TimeoutError()

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"}, timeout=10)

        assert result.success is False
        assert result.return_code == -1
        assert "timeout" in result.stderr.lower()
        assert result.error_message == "Execution timeout"

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_local_exception(self, mock_execute):
        """Test local execution with unexpected exception."""
        mock_execute.side_effect = RuntimeError("Unexpected error")

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is False
        assert result.return_code == -1
        assert "Unexpected error" in result.stderr


# ============================================================================
# ToolExecutor.execute Tests - Docker Execution
# ============================================================================
class TestToolExecutorExecuteDocker:
    """Tests for execute method with Docker execution."""

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_docker")
    @patch.object(ToolExecutor, "_parse_output")
    @patch.object(ToolExecutor, "_extract_findings")
    async def test_execute_docker_success(self, mock_extract, mock_parse, mock_execute):
        """Test successful Docker execution."""
        mock_execute.return_value = ("docker stdout", "docker stderr", 0)
        mock_parse.return_value = {"findings": []}
        mock_extract.return_value = []

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY, use_docker=True)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is True
        assert result.stdout == "docker stdout"
        assert result.return_code == 0
        mock_execute.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_docker")
    async def test_execute_docker_timeout(self, mock_execute):
        """Test Docker execution timeout."""
        mock_execute.side_effect = asyncio.TimeoutError()

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY, use_docker=True)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is False
        assert "timeout" in result.stderr.lower()


# ============================================================================
# ToolExecutor._execute_local Tests
# ============================================================================
class TestToolExecutorExecuteLocalMethod:
    """Tests for _execute_local method."""

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    async def test_execute_local_success(self, mock_create):
        """Test successful local command execution."""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b"stdout output", b"stderr output")
        mock_create.return_value = mock_process

        executor = ToolExecutor()
        stdout, stderr, return_code = await executor._execute_local("nmap test.com", 60)

        assert stdout == "stdout output"
        assert stderr == "stderr output"
        assert return_code == 0
        mock_create.assert_called_once_with(
            "nmap test.com",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    @patch("asyncio.wait_for")
    async def test_execute_local_timeout_kill(self, mock_wait, mock_create):
        """Test that process is killed on timeout."""
        mock_process = AsyncMock()
        mock_create.return_value = mock_process
        mock_wait.side_effect = asyncio.TimeoutError()

        executor = ToolExecutor()
        with pytest.raises(asyncio.TimeoutError):
            await executor._execute_local("nmap test.com", 1)

        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_shell")
    async def test_execute_local_unicode_decode(self, mock_create):
        """Test handling of non-UTF8 bytes in output."""
        mock_process = AsyncMock()
        mock_process.returncode = 0
        # Include invalid UTF-8 bytes
        mock_process.communicate.return_value = (b"\xff\xfe output", b"\xff\xfe error")
        mock_create.return_value = mock_process

        executor = ToolExecutor()
        stdout, stderr, return_code = await executor._execute_local("nmap test.com", 60)

        # Should decode with errors="ignore"
        assert "output" in stdout or stdout == ""
        assert "error" in stderr or stderr == ""


# ============================================================================
# ToolExecutor._execute_docker Tests
# ============================================================================
class TestToolExecutorExecuteDockerMethod:
    """Tests for _execute_docker method."""

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_docker_builds_command(self, mock_execute_local):
        """Test that Docker command is built correctly."""
        mock_execute_local.return_value = ("output", "", 0)

        tool = ToolDefinition(
            name="nmap",
            description="Network scanner",
            command_template="nmap {target}",
            safety_level=SafetyLevel.READ_ONLY,
            category="recon",
        )

        executor = ToolExecutor()
        await executor._execute_docker(tool, "nmap scanme.nmap.org", 300)

        mock_execute_local.assert_called_once()
        call_args = mock_execute_local.call_args
        docker_cmd = call_args[0][0]
        assert "docker run --rm --network=host" in docker_cmd
        assert "nmap" in docker_cmd
        assert "nmap scanme.nmap.org" in docker_cmd

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_docker_returns_result(self, mock_execute_local):
        """Test that Docker execution returns result from local execution."""
        mock_execute_local.return_value = ("docker output", "docker error", 0)

        tool = ToolDefinition(
            name="nuclei",
            description="Vulnerability scanner",
            command_template="nuclei -u {target}",
            safety_level=SafetyLevel.NON_DESTRUCTIVE,
            category="web",
        )

        executor = ToolExecutor()
        result = await executor._execute_docker(tool, "nuclei -u test.com", 600)

        assert result == ("docker output", "docker error", 0)


# ============================================================================
# ToolExecutor._parse_output Tests
# ============================================================================
class TestToolExecutorParseOutput:
    """Tests for _parse_output method."""

    def test_parse_output_nmap(self):
        """Test parsing nmap output."""
        executor = ToolExecutor()
        output = """
Starting Nmap 7.91
PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH 7.4
80/tcp  open  http    Apache httpd 2.4.6
443/tcp open  https

Nmap done
"""
        result = executor._parse_output("nmap", output)
        assert "open_ports" in result
        assert len(result["open_ports"]) == 3
        assert result["open_ports"][0]["port"] == "22"
        assert result["open_ports"][0]["service"] == "ssh"

    def test_parse_output_nuclei(self):
        """Test parsing nuclei output."""
        executor = ToolExecutor()
        output = """
[infolder-panel] [http] [info] http://target.com/admin
[cve-2021-44228] [http] [critical] http://target.com/login
"""
        result = executor._parse_output("nuclei", output)
        assert "findings" in result
        assert len(result["findings"]) == 2

    def test_parse_output_subfinder(self):
        """Test parsing subfinder output."""
        executor = ToolExecutor()
        output = """
www.example.com
api.example.com
mail.example.com
"""
        result = executor._parse_output("subfinder", output)
        assert "subdomains" in result
        assert len(result["subdomains"]) == 3
        assert "www.example.com" in result["subdomains"]

    def test_parse_output_unknown_tool(self):
        """Test parsing output for unknown tool."""
        executor = ToolExecutor()
        output = "some raw output"
        result = executor._parse_output("unknown", output)
        assert result == {"raw": output}

    def test_parse_output_parser_exception(self):
        """Test handling parser exception."""
        executor = ToolExecutor()

        # Create a tool definition that will trigger parsing
        with patch.object(executor, "_parse_nmap") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            output = "22/tcp open ssh"
            result = executor._parse_output("nmap", output)
            # Should return raw output on parse error
            assert "raw" in result


# ============================================================================
# ToolExecutor._parse_nmap Tests
# ============================================================================
class TestToolExecutorParseNmap:
    """Tests for _parse_nmap method."""

    def test_parse_nmap_open_ports(self):
        """Test parsing nmap output with open ports."""
        executor = ToolExecutor()
        output = """
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.2p1
80/tcp   open  http       nginx 1.18.0
443/tcp  open  https      Apache
8080/tcp open  http-proxy
"""
        result = executor._parse_nmap(output)
        assert len(result["open_ports"]) == 4
        assert result["open_ports"][0] == {
            "port": "22",
            "service": "ssh",
            "version": "OpenSSH 8.2p1",
        }
        assert result["open_ports"][3] == {
            "port": "8080",
            "service": "http-proxy",
            "version": "",
        }

    def test_parse_nmap_no_ports(self):
        """Test parsing nmap output with no open ports."""
        executor = ToolExecutor()
        output = "Starting Nmap...\nNmap done"
        result = executor._parse_nmap(output)
        assert result["open_ports"] == []

    def test_parse_nmap_closed_ports(self):
        """Test that closed ports are not included."""
        executor = ToolExecutor()
        output = """
PORT    STATE  SERVICE
22/tcp  closed ssh
80/tcp  open   http
"""
        result = executor._parse_nmap(output)
        assert len(result["open_ports"]) == 1
        assert result["open_ports"][0]["port"] == "80"

    def test_parse_nmap_udp_ports(self):
        """Test parsing UDP ports."""
        executor = ToolExecutor()
        output = """
PORT    STATE SERVICE
53/udp  open  domain
"""
        result = executor._parse_nmap(output)
        # Should only match /tcp
        assert len(result["open_ports"]) == 0


# ============================================================================
# ToolExecutor._parse_nuclei Tests
# ============================================================================
class TestToolExecutorParseNuclei:
    """Tests for _parse_nuclei method."""

    def test_parse_nuclei_findings(self):
        """Test parsing nuclei output with findings."""
        executor = ToolExecutor()
        output = """
[2024-01-01 10:00:00] [CVE-2021-44228] [critical] http://target.com/login
[2024-01-01 10:00:01] [wordpress-login] [info] http://target.com/wp-admin
"""
        result = executor._parse_nuclei(output)
        assert len(result["findings"]) == 2

    def test_parse_nuclei_no_findings(self):
        """Test parsing nuclei output with no findings."""
        executor = ToolExecutor()
        output = "Starting nuclei scan...\nNo results found"
        result = executor._parse_nuclei(output)
        assert result["findings"] == []

    def test_parse_nuclei_empty_output(self):
        """Test parsing empty nuclei output."""
        executor = ToolExecutor()
        result = executor._parse_nuclei("")
        assert result["findings"] == []


# ============================================================================
# ToolExecutor._parse_subfinder Tests
# ============================================================================
class TestToolExecutorParseSubfinder:
    """Tests for _parse_subfinder method."""

    def test_parse_subfinder_domains(self):
        """Test parsing subfinder output with subdomains."""
        executor = ToolExecutor()
        output = """
www.example.com
api.example.com
mail.example.com
dev.example.com
"""
        result = executor._parse_subfinder(output)
        assert len(result["subdomains"]) == 4
        assert "www.example.com" in result["subdomains"]
        assert "api.example.com" in result["subdomains"]

    def test_parse_subfinder_empty_lines(self):
        """Test parsing subfinder output with empty lines."""
        executor = ToolExecutor()
        output = """
www.example.com

api.example.com

"""
        result = executor._parse_subfinder(output)
        assert len(result["subdomains"]) == 2

    def test_parse_subfinder_no_results(self):
        """Test parsing subfinder output with no results."""
        executor = ToolExecutor()
        output = ""
        result = executor._parse_subfinder(output)
        assert result["subdomains"] == []


# ============================================================================
# ToolExecutor._extract_findings Tests
# ============================================================================
class TestToolExecutorExtractFindings:
    """Tests for _extract_findings method."""

    def test_extract_findings_nmap(self):
        """Test extracting findings from nmap output."""
        executor = ToolExecutor()
        parsed = {"open_ports": [{"port": "22", "service": "ssh", "version": ""}]}
        findings = executor._extract_findings("nmap", "", parsed)

        assert len(findings) == 1
        assert findings[0]["type"] == "open_port"
        assert findings[0]["severity"] == "info"
        assert findings[0]["details"]["port"] == "22"

    def test_extract_findings_nmap_no_ports(self):
        """Test extracting findings when no ports found."""
        executor = ToolExecutor()
        parsed = {"open_ports": []}
        findings = executor._extract_findings("nmap", "", parsed)
        assert findings == []

    def test_extract_findings_nuclei(self):
        """Test extracting findings from nuclei output."""
        executor = ToolExecutor()
        parsed = {"findings": [{"raw": "[CVE-2021-44228]"}]}
        findings = executor._extract_findings("nuclei", "", parsed)

        assert len(findings) == 1
        assert findings[0]["type"] == "vulnerability"
        assert findings[0]["severity"] == "unknown"

    def test_extract_findings_nuclei_no_findings(self):
        """Test extracting findings when nuclei finds nothing."""
        executor = ToolExecutor()
        parsed = {"findings": []}
        findings = executor._extract_findings("nuclei", "", parsed)
        assert findings == []

    def test_extract_findings_unknown_tool(self):
        """Test extracting findings for unknown tool."""
        executor = ToolExecutor()
        findings = executor._extract_findings("unknown", "output", {})
        assert findings == []


# ============================================================================
# Integration Tests
# ============================================================================
class TestToolExecutorIntegration:
    """Integration tests for ToolExecutor."""

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_full_execution_workflow(self, mock_execute):
        """Test complete execution workflow."""
        mock_execute.return_value = ("PORT   STATE SERVICE\n22/tcp open  ssh\n80/tcp open  http", "", 0)

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org", "options": "-sS"})

        assert result.success is True
        assert result.return_code == 0
        assert result.tool == "nmap"
        assert "nmap" in result.command
        assert result.parsed_output is not None
        assert "open_ports" in result.parsed_output
        assert len(result.findings) > 0
        assert result.duration > 0

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_multiple_executions_logged(self, mock_execute):
        """Test that multiple executions are logged."""
        mock_execute.return_value = ("output", "", 0)

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)

        await executor.execute("nmap", {"target": "target1.com"})
        await executor.execute("nmap", {"target": "target2.com"})
        await executor.execute("nmap", {"target": "target3.com"})

        assert len(executor.execution_log) == 3
        for i, log in enumerate(executor.execution_log):
            assert log["tool"] == "nmap"
            assert log["success"] is True

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execution_with_custom_timeout(self, mock_execute):
        """Test execution with custom timeout override."""
        mock_execute.return_value = ("output", "", 0)

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"}, timeout=60)

        assert result.success is True
        # Verify timeout was passed to _execute_local
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0][1] == 60  # timeout parameter


# ============================================================================
# Additional Tests for 100% Coverage
# ============================================================================
class TestToolExecutorAdditionalCoverage:
    """Additional tests to achieve complete coverage."""

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_docker")
    async def test_execute_docker_general_exception(self, mock_execute):
        """Test Docker execution with general exception (covers line 390-401)."""
        mock_execute.side_effect = Exception("Docker daemon not running")

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY, use_docker=True)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is False
        assert result.return_code == -1
        assert "Docker daemon not running" in result.stderr

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_local_general_exception(self, mock_execute):
        """Test local execution with general exception (covers line 390-401)."""
        mock_execute.side_effect = Exception("Process spawn error")

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is False
        assert result.return_code == -1
        assert "Process spawn error" in result.stderr

    def test_parse_nmap_malformed_line(self):
        """Test parsing nmap output with malformed lines."""
        executor = ToolExecutor()
        output = """
PORT     STATE SERVICE
22/tcp   open  ssh
malformed line without enough parts
80/tcp   open  http
"""
        result = executor._parse_nmap(output)
        # Should only parse the valid lines
        assert len(result["open_ports"]) == 2

    def test_parse_nmap_line_with_only_two_parts(self):
        """Test parsing nmap line with only 2 parts."""
        executor = ToolExecutor()
        output = """
PORT     STATE
22/tcp   open
80/tcp   open
"""
        result = executor._parse_nmap(output)
        # Lines with less than 3 parts should be skipped
        assert len(result["open_ports"]) == 0

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_docker")
    async def test_execute_docker_with_custom_timeout(self, mock_execute):
        """Test Docker execution with custom timeout (covers line 341)."""
        mock_execute.return_value = ("output", "", 0)

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY, use_docker=True)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"}, timeout=120)

        assert result.success is True
        # Verify the timeout was passed to _execute_docker
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0][2] == 120  # timeout parameter

    @pytest.mark.asyncio
    @patch.object(ToolExecutor, "_execute_local")
    async def test_execute_local_with_tool_timeout(self, mock_execute):
        """Test execution using tool's default timeout."""
        mock_execute.return_value = ("output", "", 0)

        executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)
        result = await executor.execute("nmap", {"target": "scanme.nmap.org"})

        assert result.success is True
        # Verify nmap's default timeout (600) was used
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[0][1] == 600  # nmap's default timeout
