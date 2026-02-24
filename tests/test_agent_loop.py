"""
Comprehensive tests for autonomous/agent_loop.py

Target: 80%+ coverage
Tests: ReActAgent, reasoning loop, action execution, observation handling, error recovery
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from autonomous.agent_loop import (
    AgentMemory,
    AgentState,
    AutonomousAgentLoop,
    ExploitValidator,
    NmapScanner,
    NucleiScanner,
    PlanStep,
    ReportGenerator,
    SubdomainEnumerator,
    ToolRegistry,
    ToolResult,
    ToolType,
    create_agent_loop,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Test response")
    return client


@pytest.fixture
def agent_loop(mock_llm_client):
    """Create an AutonomousAgentLoop instance for testing."""
    return AutonomousAgentLoop(
        llm_client=mock_llm_client,
        max_iterations=10,
        retry_attempts=2,
        retry_delay=0.1,
    )


@pytest.fixture
def sample_tool_result():
    """Create a sample ToolResult for testing."""
    return ToolResult(
        tool_name="NmapScanner",
        success=True,
        data={"open_ports": [{"port": 80, "service": "http"}]},
        raw_output="test output",
        execution_time=1.0,
    )


@pytest.fixture
def sample_agent_memory():
    """Create a sample AgentMemory for testing."""
    return AgentMemory(
        goal="Test goal",
        target="example.com",
        scope={"depth": "standard"},
    )


# ============================================================================
# Test AgentMemory
# ============================================================================


class TestAgentMemory:
    """Test AgentMemory dataclass and methods."""

    def test_memory_initialization(self):
        """Test AgentMemory initialization."""
        memory = AgentMemory(goal="Find vulnerabilities", target="example.com")

        assert memory.goal == "Find vulnerabilities"
        assert memory.target == "example.com"
        assert memory.session_id is not None
        assert isinstance(memory.created_at, datetime)
        assert memory.short_term == []
        assert memory.long_term == {}
        assert memory.findings == []

    def test_add_to_short_term(self):
        """Test adding entries to short term memory."""
        memory = AgentMemory(max_short_term=5)

        # Add entries
        for i in range(7):
            memory.add_to_short_term({"content": f"entry {i}"})

        # Should only keep last 5
        assert len(memory.short_term) == 5
        assert memory.short_term[0]["content"] == "entry 2"
        assert memory.short_term[-1]["content"] == "entry 6"

    def test_add_to_context_window(self):
        """Test adding entries to context window."""
        memory = AgentMemory(max_context_window=3)

        for i in range(5):
            memory.add_to_context_window({"content": f"context {i}"})

        assert len(memory.context_window) == 3

    def test_get_context_for_llm(self):
        """Test getting formatted context for LLM."""
        memory = AgentMemory(goal="Test goal", target="test.com")
        memory.add_to_context_window(
            {"type": "action", "content": "Scan ports"}
        )
        memory.add_to_finding({"type": "vulnerability", "severity": "high"})

        context = memory.get_context_for_llm()

        assert "Test goal" in context
        assert "test.com" in context
        assert "ACTION" in context
        assert "Findings: 1" in context

    def test_add_finding(self):
        """Test adding security findings."""
        memory = AgentMemory()
        finding = {"type": "sql_injection", "severity": "critical"}

        memory.add_finding(finding)

        assert len(memory.findings) == 1
        assert memory.findings[0]["type"] == "sql_injection"
        assert "timestamp" in memory.findings[0]
        assert "id" in memory.findings[0]

    def test_to_dict(self):
        """Test converting memory to dictionary."""
        memory = AgentMemory(goal="Test", target="test.com")
        memory.add_to_short_term({"content": "test"})
        memory.add_finding({"type": "vuln"})

        result = memory.to_dict()

        assert result["goal"] == "Test"
        assert result["target"] == "test.com"
        assert result["short_term_count"] == 1
        assert result["findings_count"] == 1
        assert "session_id" in result


# ============================================================================
# Test ToolResult and PlanStep
# ============================================================================


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_tool_result_creation(self):
        """Test ToolResult creation."""
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"ports": [80, 443]},
            raw_output="test output",
            execution_time=1.5,
        )

        assert result.tool_name == "NmapScanner"
        assert result.success is True
        assert result.data == {"ports": [80, 443]}
        assert result.execution_time == 1.5

    def test_tool_result_to_dict(self):
        """Test ToolResult to_dict method."""
        result = ToolResult(
            tool_name="TestTool",
            success=True,
            raw_output="x" * 1000,  # Test truncation
        )

        result_dict = result.to_dict()

        assert result_dict["tool_name"] == "TestTool"
        assert result_dict["success"] is True
        assert len(result_dict["raw_output"]) <= 500


class TestPlanStep:
    """Test PlanStep dataclass."""

    def test_plan_step_creation(self):
        """Test PlanStep creation."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Scan ports",
            parameters={"target": "example.com"},
        )

        assert step.tool_type == ToolType.NMAP_SCANNER
        assert step.action == "Scan ports"
        assert step.parameters == {"target": "example.com"}
        assert step.completed is False
        assert step.step_id is not None

    def test_plan_step_to_dict(self):
        """Test PlanStep to_dict method."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Scan",
            parameters={"target": "test.com"},
        )
        result = ToolResult(tool_name="NmapScanner", success=True)
        step.result = result
        step.completed = True

        step_dict = step.to_dict()

        assert step_dict["tool_type"] == "nmap_scanner"
        assert step_dict["action"] == "Scan"
        assert step_dict["completed"] is True
        assert step_dict["result"] is not None


# ============================================================================
# Test BaseTool and Tool Classes
# ============================================================================


class TestBaseTool:
    """Test BaseTool abstract class."""

    def test_base_tool_initialization(self):
        """Test BaseTool initialization."""
        tool = NmapScanner(timeout=600)

        assert tool.name == "NmapScanner"
        assert tool.timeout == 600
        assert tool.logger is not None

    def test_validate_parameters_base(self):
        """Test base parameter validation."""
        tool = NmapScanner()
        valid, error = tool.validate_parameters({})

        # NmapScanner overrides this, but BaseTool returns True
        assert isinstance(valid, bool)


class TestNmapScanner:
    """Test NmapScanner tool."""

    def test_nmap_scanner_initialization(self):
        """Test NmapScanner initialization."""
        scanner = NmapScanner(timeout=300)
        assert scanner.name == "NmapScanner"
        assert scanner.timeout == 300
        assert "-sV -sC" in scanner.default_options

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid input."""
        scanner = NmapScanner()
        valid, error = scanner.validate_parameters({"target": "example.com"})

        assert valid is True
        assert error == ""

    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid input."""
        scanner = NmapScanner()
        valid, error = scanner.validate_parameters({"target": ""})

        assert valid is False
        assert "Target is required" in error

    @pytest.mark.asyncio
    async def test_nmap_scanner_execute_success(self):
        """Test successful Nmap execution."""
        scanner = NmapScanner()

        mock_xml_output = """<?xml version="1.0"?>
        <nmaprun>
            <host><status state="up"/>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http" product="Apache" version="2.4"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_xml_output.encode(), b"")
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await scanner.execute(
                {"target": "scanme.nmap.org", "ports": "80"}
            )

        assert result.success is True
        assert result.tool_name == "NmapScanner"
        assert "open_ports" in result.data

    @pytest.mark.asyncio
    async def test_nmap_scanner_execute_timeout(self):
        """Test Nmap execution timeout."""
        scanner = NmapScanner(timeout=1)

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await scanner.execute({"target": "scanme.nmap.org"})

        assert result.success is False
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_nmap_scanner_execute_not_found(self):
        """Test Nmap not found error."""
        scanner = NmapScanner()

        with patch(
            "asyncio.create_subprocess_exec", side_effect=FileNotFoundError()
        ):
            result = await scanner.execute({"target": "scanme.nmap.org"})

        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_validate_target_safety_private_ip(self):
        """Test safety validation blocks private IPs."""
        scanner = NmapScanner()
        valid, error = scanner._validate_target_safety("192.168.1.1")

        assert valid is False
        assert "blocked" in error.lower()

    def test_validate_target_safety_loopback(self):
        """Test loopback address handling."""
        scanner = NmapScanner()
        valid, error = scanner._validate_target_safety("127.0.0.1")

        assert valid is True  # Loopback allowed with warning

    def test_validate_target_safety_dangerous_chars(self):
        """Test blocking dangerous characters."""
        scanner = NmapScanner()
        valid, error = scanner._validate_target_safety("example.com; rm -rf /")

        assert valid is False
        assert "Invalid characters" in error

    def test_parse_nmap_xml_valid(self):
        """Test parsing valid Nmap XML."""
        scanner = NmapScanner()
        xml = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http" product="Apache" version="2.4"/>
                    </port>
                    <port protocol="tcp" portid="443">
                        <state state="open"/>
                        <service name="https" product="Nginx"/>
                    </port>
                </ports>
                <os><osmatch name="Linux 5.0" accuracy="95"/></os>
            </host>
        </nmaprun>"""

        result = scanner._parse_nmap_xml(xml)

        assert result is not None
        assert len(result["open_ports"]) == 2
        assert result["open_ports"][0]["port"] == 80
        assert result["services"] == ["http", "https"]

    def test_parse_nmap_xml_invalid(self):
        """Test parsing invalid XML falls back to text parsing."""
        scanner = NmapScanner()
        xml = "not valid xml"

        result = scanner._parse_nmap_xml(xml)

        # Should return empty dict from fallback
        assert isinstance(result, dict)

    def test_parse_output_fallback(self):
        """Test fallback text parsing."""
        scanner = NmapScanner()
        output = """
        PORT     STATE SERVICE
        22/tcp   open  ssh
        80/tcp   open  http    Apache httpd 2.4
        """

        result = scanner._parse_output_fallback(output)

        assert len(result["open_ports"]) == 2
        assert result["open_ports"][0]["port"] == 22
        assert result["open_ports"][0]["service"] == "ssh"


class TestNucleiScanner:
    """Test NucleiScanner tool."""

    def test_nuclei_scanner_initialization(self):
        """Test NucleiScanner initialization."""
        scanner = NucleiScanner(timeout=600)
        assert scanner.name == "NucleiScanner"
        assert scanner.timeout == 600

    @pytest.mark.asyncio
    async def test_nuclei_scanner_execute_success(self):
        """Test successful Nuclei execution."""
        scanner = NucleiScanner()

        mock_json_output = (
            '{"template-id": "test", "info": {"severity": "high"}}\n'
        )

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(mock_json_output.encode(), b"")
        )
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ):
            result = await scanner.execute({"target": "example.com"})

        assert result.success is True
        assert "findings" in result.data

    def test_parse_nuclei_json(self):
        """Test parsing Nuclei JSON output."""
        scanner = NucleiScanner()
        output = """
        {"template-id": "cve-2021-44228", "info": {"severity": "critical", "name": "Log4j RCE"}, "host": "example.com"}
        {"template-id": "xss-detect", "info": {"severity": "high", "name": "XSS"}, "host": "test.com"}
        """

        findings = scanner._parse_nuclei_json(output)

        assert len(findings) == 2
        assert findings[0]["severity"] == "critical"
        assert findings[0]["template"] == "cve-2021-44228"

    def test_parse_nuclei_json_invalid(self):
        """Test parsing invalid JSON lines."""
        scanner = NucleiScanner()
        output = "not json\n{}\n"

        findings = scanner._parse_nuclei_json(output)

        assert len(findings) == 0  # Empty dict skipped


class TestReportGenerator:
    """Test ReportGenerator tool."""

    @pytest.mark.asyncio
    async def test_generate_report(self):
        """Test report generation."""
        generator = ReportGenerator()
        findings = [
            {"severity": "critical", "type": "rce"},
            {"severity": "high", "type": "sqli"},
            {"severity": "high", "type": "xss"},
            {"severity": "medium", "type": "info"},
        ]

        result = await generator.execute(
            {
                "target": "example.com",
                "findings": findings,
                "format": "json",
            }
        )

        assert result.success is True
        assert result.data["target"] == "example.com"
        assert result.data["summary"]["total_findings"] == 4
        assert result.data["summary"]["critical"] == 1
        assert result.data["summary"]["high"] == 2
        assert len(result.data["recommendations"]) > 0

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        generator = ReportGenerator()
        findings = [{"severity": "critical"}, {"severity": "high"}]

        recommendations = generator._generate_recommendations(findings)

        assert any("critical" in r.lower() for r in recommendations)
        assert any("high" in r.lower() for r in recommendations)


class TestSubdomainEnumerator:
    """Test SubdomainEnumerator tool."""

    @pytest.mark.asyncio
    async def test_enumerate_subdomains(self):
        """Test subdomain enumeration."""
        enumerator = SubdomainEnumerator()

        result = await enumerator.execute(
            {
                "target": "example.com",
                "wordlist": "default",
                "recursive": False,
            }
        )

        assert result.success is True
        assert result.data["domain"] == "example.com"
        assert len(result.data["subdomains"]) > 0
        assert all("example.com" in sd for sd in result.data["subdomains"])


class TestExploitValidatorTool:
    """Test ExploitValidator tool wrapper."""

    @pytest.mark.asyncio
    async def test_exploit_validator_initialization(self):
        """Test ExploitValidator tool initialization."""
        validator = ExploitValidator(timeout=300, safety_level="controlled")
        assert validator.name == "ExploitValidator"
        assert validator.safety_level == "controlled"

    def test_generate_test_payload(self):
        """Test payload generation."""
        validator = ExploitValidator()

        payloads = {
            "sqli": "' OR '1'='1",
            "xss": "<script>",
            "rce": "echo",
        }

        for vuln_type, expected in payloads.items():
            payload = validator._generate_test_payload(vuln_type)
            assert expected in payload


# ============================================================================
# Test ToolRegistry
# ============================================================================


class TestToolRegistry:
    """Test ToolRegistry class."""

    def test_registry_initialization(self):
        """Test registry initialization with default tools."""
        registry = ToolRegistry()

        tools = registry.list_tools()
        assert "nmap_scanner" in tools
        assert "nuclei_scanner" in tools
        assert "exploit_validator" in tools
        assert "report_generator" in tools
        assert "subdomain_enumerator" in tools

    def test_get_tool(self):
        """Test getting tools from registry."""
        registry = ToolRegistry()

        nmap_tool = registry.get_tool(ToolType.NMAP_SCANNER)
        assert nmap_tool is not None
        assert nmap_tool.name == "NmapScanner"

        unknown = registry.get_tool(
            ToolType(999) if hasattr(ToolType, "_value2member_map_") else None
        )
        assert unknown is None


# ============================================================================
# Test AutonomousAgentLoop
# ============================================================================


class TestAutonomousAgentLoop:
    """Test AutonomousAgentLoop main class."""

    def test_initialization(self, mock_llm_client):
        """Test AutonomousAgentLoop initialization."""
        agent = AutonomousAgentLoop(
            llm_client=mock_llm_client,
            max_iterations=50,
            retry_attempts=3,
        )

        assert agent.llm == mock_llm_client
        assert agent.max_iterations == 50
        assert agent.retry_attempts == 3
        assert agent.state == AgentState.IDLE
        assert agent.tool_registry is not None

    def test_state_callbacks(self, agent_loop):
        """Test state callback registration and triggering."""
        callback_mock = Mock()

        agent_loop.register_state_callback(AgentState.EXECUTING, callback_mock)
        agent_loop._transition_to(AgentState.EXECUTING)

        callback_mock.assert_called_once_with(AgentState.EXECUTING)
        assert agent_loop.state == AgentState.EXECUTING

    def test_progress_callback(self, agent_loop):
        """Test progress callback."""
        progress_mock = Mock()
        agent_loop.set_progress_callback(progress_mock)

        agent_loop._update_progress({"completed_steps": 1})

        progress_mock.assert_called_once()

    def test_transition_to(self, agent_loop):
        """Test state transitions."""
        agent_loop._transition_to(AgentState.PLANNING)

        assert agent_loop.state == AgentState.PLANNING
        assert agent_loop.previous_state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_run_complete_workflow(self, agent_loop):
        """Test complete agent loop workflow."""
        # Mock tool execution
        mock_result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": [{"port": 80, "service": "http"}]},
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                "execute",
                AsyncMock(
                    return_value=ToolResult(
                        tool_name="ReportGenerator", success=True, data={}
                    )
                ),
            ):
                result = await agent_loop.run(
                    goal="Find open ports",
                    target="example.com",
                )

        assert result["success"] is True
        assert result["state"] == "COMPLETED"
        assert "findings" in result
        assert "execution" in result

    @pytest.mark.asyncio
    async def test_run_with_error(self, agent_loop):
        """Test agent loop with execution error."""
        with patch.object(
            agent_loop, "plan", side_effect=Exception("Planning failed")
        ):
            result = await agent_loop.run(goal="Test", target="example.com")

        assert result["success"] is False
        assert result["state"] == "ERROR"
        assert "Planning failed" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_plan_port_scan(self, agent_loop):
        """Test planning for port scan goal."""
        agent_loop.memory = AgentMemory(
            goal="Find open ports", target="example.com"
        )

        plan = await agent_loop.plan()

        assert len(plan) > 0
        assert any(step.tool_type == ToolType.NMAP_SCANNER for step in plan)

    @pytest.mark.asyncio
    async def test_plan_vulnerability_scan(self, agent_loop):
        """Test planning for vulnerability scan goal."""
        agent_loop.memory = AgentMemory(
            goal="Scan for vulnerabilities", target="example.com"
        )

        plan = await agent_loop.plan()

        assert any(step.tool_type == ToolType.NUCLEI_SCANNER for step in plan)

    @pytest.mark.asyncio
    async def test_plan_default(self, agent_loop):
        """Test default plan when no specific goal matches."""
        agent_loop.memory = AgentMemory(
            goal="Do something generic", target="example.com"
        )

        plan = await agent_loop.plan()

        assert len(plan) > 0
        assert any(step.tool_type == ToolType.NMAP_SCANNER for step in plan)

    @pytest.mark.asyncio
    async def test_execute_action(self, agent_loop):
        """Test executing an action."""
        mock_result = ToolResult(
            tool_name="NmapScanner", success=True, data={}
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent_loop.execute_action(
                {
                    "tool_type": "nmap_scanner",
                    "parameters": {"target": "example.com"},
                }
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_action_unknown_tool(self, agent_loop):
        """Test executing with unknown tool type."""
        result = await agent_loop.execute_action(
            {
                "tool_type": "unknown_tool",
                "parameters": {},
            }
        )

        assert result.success is False
        assert "Unknown tool" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, agent_loop):
        """Test retry logic with eventual success."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        mock_result = ToolResult(
            tool_name="NmapScanner", success=True, data={}
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent_loop._execute_with_retry(step)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self, agent_loop):
        """Test retry logic with complete failure."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        mock_result = ToolResult(
            tool_name="NmapScanner", success=False, error_message="Failed"
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent_loop._execute_with_retry(step)

        assert result.success is False
        assert "All 2 attempts failed" in result.error_message

    @pytest.mark.asyncio
    async def test_observe_success(
        self, agent_loop, sample_agent_memory, sample_tool_result
    ):
        """Test observation of successful result."""
        agent_loop.memory = sample_agent_memory

        observation = await agent_loop.observe(sample_tool_result)

        assert observation["tool"] == "NmapScanner"
        assert observation["success"] is True
        assert observation["open_ports"] == 1

    @pytest.mark.asyncio
    async def test_observe_failure(self, agent_loop, sample_agent_memory):
        """Test observation of failed result."""
        agent_loop.memory = sample_agent_memory
        failed_result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Connection timeout",
        )

        observation = await agent_loop.observe(failed_result)

        assert observation["success"] is False
        assert "Connection timeout" in observation["error"]

    @pytest.mark.asyncio
    async def test_reflect_continue(self, agent_loop, sample_agent_memory):
        """Test reflection when should continue."""
        agent_loop.memory = sample_agent_memory
        agent_loop.progress["current_iteration"] = 1

        should_continue = await agent_loop.reflect()

        assert should_continue is True

    @pytest.mark.asyncio
    async def test_reflect_max_iterations(
        self, agent_loop, sample_agent_memory
    ):
        """Test reflection at max iterations."""
        agent_loop.memory = sample_agent_memory
        agent_loop.progress["current_iteration"] = agent_loop.max_iterations

        should_continue = await agent_loop.reflect()

        assert should_continue is False

    @pytest.mark.asyncio
    async def test_reflect_too_many_errors(
        self, agent_loop, sample_agent_memory
    ):
        """Test reflection with too many errors."""
        agent_loop.memory = sample_agent_memory
        # Add multiple recent errors
        for i in range(6):
            agent_loop.progress["errors"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Error {i}",
                }
            )

        should_continue = await agent_loop.reflect()

        assert should_continue is False

    @pytest.mark.asyncio
    async def test_extract_findings(self, agent_loop, sample_agent_memory):
        """Test extracting findings from results."""
        agent_loop.memory = sample_agent_memory

        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={
                "open_ports": [{"port": 80, "service": "http"}],
                "findings": [{"severity": "high", "type": "xss"}],
                "subdomains": ["www.example.com"],
            },
        )

        await agent_loop._extract_findings(result)

        assert len(agent_loop.memory.findings) == 3
        assert agent_loop.progress["findings_count"] == 3

    def test_get_state(self, agent_loop):
        """Test getting current state."""
        assert agent_loop.get_state() == AgentState.IDLE

        agent_loop._transition_to(AgentState.EXECUTING)
        assert agent_loop.get_state() == AgentState.EXECUTING

    def test_get_progress(self, agent_loop):
        """Test getting progress."""
        progress = agent_loop.get_progress()

        assert "current_iteration" in progress
        assert "completed_steps" in progress

    def test_is_running(self, agent_loop):
        """Test is_running check."""
        assert agent_loop.is_running() is False

        agent_loop._transition_to(AgentState.EXECUTING)
        assert agent_loop.is_running() is True

    def test_pause_resume(self, agent_loop):
        """Test pause and resume functionality."""
        agent_loop._transition_to(AgentState.EXECUTING)

        agent_loop.pause()
        assert agent_loop.state == AgentState.PAUSED

        agent_loop.resume()
        assert agent_loop.state == AgentState.EXECUTING


# ============================================================================
# Test Factory Function
# ============================================================================


class TestFactoryFunction:
    """Test create_agent_loop factory function."""

    def test_create_agent_loop(self):
        """Test factory function creates proper instance."""
        agent = create_agent_loop(max_iterations=20, retry_attempts=5)

        assert isinstance(agent, AutonomousAgentLoop)
        assert agent.max_iterations == 20
        assert agent.retry_attempts == 5


# ============================================================================
# Test AgentState Enum
# ============================================================================


class TestAgentState:
    """Test AgentState enum."""

    def test_states_exist(self):
        """Test all expected states exist."""
        states = [
            AgentState.IDLE,
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.OBSERVING,
            AgentState.REFLECTING,
            AgentState.COMPLETED,
            AgentState.ERROR,
            AgentState.PAUSED,
        ]

        for state in states:
            assert isinstance(state, AgentState)

    def test_state_names(self):
        """Test state names are correct."""
        assert AgentState.IDLE.name == "IDLE"
        assert AgentState.COMPLETED.name == "COMPLETED"


# ============================================================================
# Test ToolType Enum
# ============================================================================


class TestToolType:
    """Test ToolType enum."""

    def test_tool_types_exist(self):
        """Test all expected tool types exist."""
        tools = [
            ToolType.NMAP_SCANNER,
            ToolType.NUCLEI_SCANNER,
            ToolType.EXPLOIT_VALIDATOR,
            ToolType.REPORT_GENERATOR,
            ToolType.SUBDOMAIN_ENUMERATOR,
        ]

        for tool in tools:
            assert isinstance(tool, ToolType)

    def test_tool_type_values(self):
        """Test tool type string values."""
        assert ToolType.NMAP_SCANNER.value == "nmap_scanner"
        assert ToolType.NUCLEI_SCANNER.value == "nuclei_scanner"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_goal(self, agent_loop):
        """Test behavior with empty goal."""
        result = await agent_loop.run(goal="", target="example.com")
        # Should complete but maybe with minimal results
        assert "success" in result

    @pytest.mark.asyncio
    async def test_invalid_target(self, agent_loop):
        """Test behavior with invalid target."""
        # Mock to simulate invalid target handling
        mock_result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Invalid target",
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent_loop.run(goal="Scan ports", target="invalid")

        assert (
            result["success"] is True
        )  # Agent loop completes even with tool errors

    @pytest.mark.asyncio
    async def test_callback_exception(self, agent_loop):
        """Test handling of callback exceptions."""

        def bad_callback(state):
            raise Exception("Callback error")

        agent_loop.register_state_callback(AgentState.EXECUTING, bad_callback)

        # Should not raise even though callback throws
        agent_loop._transition_to(AgentState.EXECUTING)
        assert agent_loop.state == AgentState.EXECUTING

    @pytest.mark.asyncio
    async def test_memory_none_handling(self, agent_loop):
        """Test handling when memory is None."""
        # Call methods that use memory when it's None
        agent_loop.memory = None

        # Should handle gracefully
        result = agent_loop._compile_final_result()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execution_exception_handling(self, agent_loop):
        """Test handling of execution exceptions."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test",
            parameters={},
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(side_effect=Exception("Unexpected error")),
        ):
            result = await agent_loop._execute_with_retry(step)

        assert result.success is False
        assert "Unexpected error" in result.error_message
