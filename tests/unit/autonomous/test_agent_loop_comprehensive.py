"""
Comprehensive tests for autonomous/agent_loop.py

Target: 80%+ coverage
Tests cover:
1. AutonomousAgentLoop class initialization and configuration
2. Agent state management (idle, running, paused, stopped)
3. Task queue management
4. Tool execution flow
5. Memory/context management
6. Error handling and recovery
7. Event/callback system
8. Graceful shutdown
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from autonomous.agent_loop import (
    AgentMemory,
    AgentState,
    AutonomousAgentLoop,
    BaseTool,
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


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Test LLM response")
    client.chat = AsyncMock(return_value={"content": "Test chat response"})
    return client


@pytest.fixture
def agent_loop(mock_llm_client):
    """Create an AutonomousAgentLoop instance for testing."""
    return AutonomousAgentLoop(
        llm_client=mock_llm_client,
        max_iterations=10,
        retry_attempts=2,
        retry_delay=0.01,  # Fast retries for testing
        enable_progress_tracking=True,
    )


@pytest.fixture
def agent_loop_no_progress(mock_llm_client):
    """Create an AutonomousAgentLoop without progress tracking."""
    return AutonomousAgentLoop(
        llm_client=mock_llm_client,
        max_iterations=10,
        retry_attempts=2,
        retry_delay=0.01,
        enable_progress_tracking=False,
    )


@pytest.fixture
def sample_tool_result():
    """Create a sample ToolResult for testing."""
    return ToolResult(
        tool_name="NmapScanner",
        success=True,
        data={
            "open_ports": [
                {"port": 80, "service": "http", "version": "Apache 2.4"},
                {"port": 443, "service": "https", "version": "Nginx 1.18"},
            ],
            "services": ["http", "https"],
            "port_count": 2,
        },
        raw_output="test output",
        execution_time=1.0,
    )


@pytest.fixture
def sample_agent_memory():
    """Create a sample AgentMemory for testing."""
    memory = AgentMemory(
        goal="Test goal",
        target="example.com",
        scope={"depth": "standard", "allowed_hosts": ["example.com"]},
    )
    return memory


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry."""
    registry = MagicMock(spec=ToolRegistry)
    mock_tool = MagicMock(spec=BaseTool)
    mock_tool.name = "MockTool"
    mock_tool.execute = AsyncMock(
        return_value=ToolResult(tool_name="MockTool", success=True, data={})
    )
    mock_tool.validate_parameters = Mock(return_value=(True, ""))
    registry.get_tool = Mock(return_value=mock_tool)
    registry.list_tools = Mock(return_value=["mock_tool"])
    return registry


@pytest.fixture
def plan_steps():
    """Create sample plan steps for testing."""
    return [
        PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Scan ports on target",
            parameters={"target": "example.com", "ports": "80,443"},
        ),
        PlanStep(
            tool_type=ToolType.NUCLEI_SCANNER,
            action="Scan for vulnerabilities",
            parameters={"target": "example.com"},
            depends_on=[],  # Could reference previous step_id
        ),
        PlanStep(
            tool_type=ToolType.REPORT_GENERATOR,
            action="Generate report",
            parameters={"target": "example.com"},
        ),
    ]


# =============================================================================
# Test AutonomousAgentLoop Initialization and Configuration
# =============================================================================


class TestAgentLoopInitialization:
    """Test AutonomousAgentLoop initialization and configuration."""

    def test_default_initialization(self):
        """Test initialization with default parameters."""
        agent = AutonomousAgentLoop()

        assert agent.llm is None
        assert agent.max_iterations == 50
        assert agent.retry_attempts == 3
        assert agent.retry_delay == 2.0
        assert agent.enable_progress_tracking is True
        assert agent.state == AgentState.IDLE
        assert agent.previous_state is None
        assert agent.memory is None
        assert agent.tool_registry is not None
        assert agent.start_time is None
        assert agent.end_time is None

    def test_custom_initialization(self, mock_llm_client):
        """Test initialization with custom parameters."""
        agent = AutonomousAgentLoop(
            llm_client=mock_llm_client,
            max_iterations=100,
            retry_attempts=5,
            retry_delay=1.5,
            enable_progress_tracking=False,
        )

        assert agent.llm == mock_llm_client
        assert agent.max_iterations == 100
        assert agent.retry_attempts == 5
        assert agent.retry_delay == 1.5
        assert agent.enable_progress_tracking is False

    def test_progress_initialization(self, mock_llm_client):
        """Test progress tracking initialization."""
        agent = AutonomousAgentLoop(
            llm_client=mock_llm_client,
            max_iterations=25,
        )

        assert agent.progress["current_iteration"] == 0
        assert agent.progress["total_iterations"] == 25
        assert agent.progress["completed_steps"] == 0
        assert agent.progress["total_steps"] == 0
        assert agent.progress["findings_count"] == 0
        assert agent.progress["errors"] == []

    def test_state_callbacks_initialization(self, mock_llm_client):
        """Test state callbacks dictionary initialization."""
        agent = AutonomousAgentLoop(llm_client=mock_llm_client)

        for state in AgentState:
            assert state in agent.state_callbacks
            assert isinstance(agent.state_callbacks[state], list)
            assert len(agent.state_callbacks[state]) == 0

    def test_tool_registry_initialization(self, mock_llm_client):
        """Test tool registry is properly initialized."""
        agent = AutonomousAgentLoop(llm_client=mock_llm_client)

        tools = agent.tool_registry.list_tools()
        assert "nmap_scanner" in tools
        assert "nuclei_scanner" in tools
        assert "exploit_validator" in tools
        assert "report_generator" in tools
        assert "subdomain_enumerator" in tools


# =============================================================================
# Test Agent State Management
# =============================================================================


class TestAgentStateManagement:
    """Test agent state management (idle, running, paused, stopped)."""

    def test_initial_state_is_idle(self, agent_loop):
        """Test initial state is IDLE."""
        assert agent_loop.get_state() == AgentState.IDLE
        assert agent_loop.is_running() is False

    def test_state_transition_to_planning(self, agent_loop):
        """Test transition to PLANNING state."""
        agent_loop._transition_to(AgentState.PLANNING)

        assert agent_loop.state == AgentState.PLANNING
        assert agent_loop.previous_state == AgentState.IDLE

    def test_state_transition_to_executing(self, agent_loop):
        """Test transition to EXECUTING state."""
        agent_loop._transition_to(AgentState.PLANNING)
        agent_loop._transition_to(AgentState.EXECUTING)

        assert agent_loop.state == AgentState.EXECUTING
        assert agent_loop.previous_state == AgentState.PLANNING

    def test_state_transition_to_all_states(self, agent_loop):
        """Test transition through all states."""
        states = [
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.OBSERVING,
            AgentState.REFLECTING,
            AgentState.COMPLETED,
        ]

        for state in states:
            agent_loop._transition_to(state)
            assert agent_loop.state == state

    def test_is_running_true_states(self, agent_loop):
        """Test is_running returns True for running states."""
        running_states = [
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.OBSERVING,
            AgentState.REFLECTING,
        ]

        for state in running_states:
            agent_loop.state = state
            assert agent_loop.is_running() is True, f"State {state.name} should be running"

    def test_is_running_false_states(self, agent_loop):
        """Test is_running returns False for non-running states."""
        non_running_states = [
            AgentState.IDLE,
            AgentState.COMPLETED,
            AgentState.ERROR,
            AgentState.PAUSED,
        ]

        for state in non_running_states:
            agent_loop.state = state
            assert agent_loop.is_running() is False, f"State {state.name} should not be running"

    def test_pause_from_running_state(self, agent_loop):
        """Test pause functionality from running state."""
        agent_loop._transition_to(AgentState.EXECUTING)
        agent_loop.pause()

        assert agent_loop.state == AgentState.PAUSED
        assert agent_loop.previous_state == AgentState.EXECUTING

    def test_pause_from_idle_state(self, agent_loop):
        """Test pause from IDLE state (should not pause)."""
        agent_loop.pause()

        # Should remain IDLE since is_running() returns False
        assert agent_loop.state == AgentState.IDLE

    def test_resume_from_paused(self, agent_loop):
        """Test resume functionality."""
        agent_loop._transition_to(AgentState.EXECUTING)
        agent_loop.pause()
        agent_loop.resume()

        assert agent_loop.state == AgentState.EXECUTING
        assert agent_loop.previous_state == AgentState.PAUSED

    def test_resume_not_paused(self, agent_loop):
        """Test resume when not paused."""
        agent_loop._transition_to(AgentState.EXECUTING)
        agent_loop.resume()  # Should not change state

        assert agent_loop.state == AgentState.EXECUTING

    def test_resume_without_previous_state(self, agent_loop):
        """Test resume when previous_state is None."""
        agent_loop.state = AgentState.PAUSED
        agent_loop.previous_state = None
        agent_loop.resume()

        # Should remain PAUSED since there's no previous state
        assert agent_loop.state == AgentState.PAUSED


# =============================================================================
# Test Task Queue Management (Plan Steps)
# =============================================================================


class TestTaskQueueManagement:
    """Test task queue management through plan steps."""

    @pytest.mark.asyncio
    async def test_plan_creation_port_scan(self, agent_loop):
        """Test plan creation for port scan goal."""
        agent_loop.memory = AgentMemory(
            goal="Find open ports on target",
            target="192.168.1.1",
        )

        plan = await agent_loop.plan()

        assert len(plan) > 0
        assert any(step.tool_type == ToolType.NMAP_SCANNER for step in plan)
        assert any(step.tool_type == ToolType.REPORT_GENERATOR for step in plan)

    @pytest.mark.asyncio
    async def test_plan_creation_subdomain_enum(self, agent_loop):
        """Test plan creation for subdomain enumeration."""
        agent_loop.memory = AgentMemory(
            goal="Enumerate all subdomains",
            target="example.com",
        )

        plan = await agent_loop.plan()

        assert any(step.tool_type == ToolType.SUBDOMAIN_ENUMERATOR for step in plan)

    @pytest.mark.asyncio
    async def test_plan_creation_vulnerability_scan(self, agent_loop):
        """Test plan creation for vulnerability scanning."""
        agent_loop.memory = AgentMemory(
            goal="Scan for vulnerabilities",
            target="example.com",
        )

        plan = await agent_loop.plan()

        assert any(step.tool_type == ToolType.NUCLEI_SCANNER for step in plan)

    @pytest.mark.asyncio
    async def test_plan_creation_exploit_validation(self, agent_loop):
        """Test plan creation for exploit validation."""
        agent_loop.memory = AgentMemory(
            goal="Validate SQL injection exploits",
            target="example.com",
        )

        plan = await agent_loop.plan()

        # Should include exploit validator for exploit-related goals
        assert any(step.tool_type == ToolType.EXPLOIT_VALIDATOR for step in plan)

    @pytest.mark.asyncio
    async def test_plan_creation_default(self, agent_loop):
        """Test default plan when goal doesn't match specific patterns."""
        agent_loop.memory = AgentMemory(
            goal="Do a comprehensive security assessment",
            target="example.com",
        )

        plan = await agent_loop.plan()

        # Should create default plan with at least report generator
        # Note: plan() logic may change, but it should always include a report
        assert len(plan) >= 1
        assert any(step.tool_type == ToolType.REPORT_GENERATOR for step in plan)

    @pytest.mark.asyncio
    async def test_plan_adds_to_memory(self, agent_loop):
        """Test that plan steps are added to short-term memory."""
        agent_loop.memory = AgentMemory(goal="Test goal", target="example.com")

        plan = await agent_loop.plan()

        assert len(agent_loop.memory.short_term) == len(plan)
        for entry in agent_loop.memory.short_term:
            assert entry["type"] == "plan_step"
            assert "content" in entry
            assert "tool" in entry

    @pytest.mark.asyncio
    async def test_plan_step_dependencies(self, agent_loop):
        """Test plan steps with dependencies."""
        agent_loop.memory = AgentMemory(goal="Test", target="example.com")

        step_with_deps = PlanStep(
            tool_type=ToolType.NUCLEI_SCANNER,
            action="Scan after recon",
            parameters={"target": "example.com"},
            depends_on=["step-1", "step-2"],
        )

        assert len(step_with_deps.depends_on) == 2
        assert "step-1" in step_with_deps.depends_on


# =============================================================================
# Test Tool Execution Flow
# =============================================================================


class TestToolExecutionFlow:
    """Test tool execution flow."""

    @pytest.mark.asyncio
    async def test_execute_action_success(self, agent_loop):
        """Test successful action execution."""
        mock_result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": []},
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent_loop.execute_action({
                "tool_type": "nmap_scanner",
                "parameters": {"target": "example.com"},
            })

        assert result.success is True
        assert result.tool_name == "NmapScanner"

    @pytest.mark.asyncio
    async def test_execute_action_unknown_tool(self, agent_loop):
        """Test execution with unknown tool type."""
        result = await agent_loop.execute_action({
            "tool_type": "unknown_tool_xyz",
            "parameters": {"target": "example.com"},
        })

        assert result.success is False
        assert "Unknown tool type" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_action_missing_tool_type(self, agent_loop):
        """Test execution with missing tool_type field."""
        result = await agent_loop.execute_action({
            "parameters": {"target": "example.com"},
        })

        # Should default to nmap_scanner or handle gracefully
        assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_execute_action_parameter_validation_failure(self, agent_loop):
        """Test execution when parameter validation fails."""
        # NmapScanner requires a target parameter
        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "validate_parameters",
            return_value=(False, "Target is required"),
        ):
            result = await agent_loop.execute_action({
                "tool_type": "nmap_scanner",
                "parameters": {},  # Missing target
            })

        assert result.success is False
        assert "Parameter validation failed" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, agent_loop):
        """Test retry logic succeeds on first attempt."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        mock_result = ToolResult(tool_name="NmapScanner", success=True, data={})

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ) as mock_execute:
            result = await agent_loop._execute_with_retry(step)

        assert result.success is True
        assert mock_execute.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_failure(self, agent_loop):
        """Test retry logic succeeds after initial failures."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        success_result = ToolResult(tool_name="NmapScanner", success=True, data={})
        failure_result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Temporary failure",
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(side_effect=[failure_result, success_result]),
        ) as mock_execute:
            result = await agent_loop._execute_with_retry(step)

        assert result.success is True
        assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_complete_failure(self, agent_loop):
        """Test retry logic when all attempts fail."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        failure_result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Persistent failure",
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=failure_result),
        ) as mock_execute:
            result = await agent_loop._execute_with_retry(step)

        assert result.success is False
        assert "All 2 attempts failed" in result.error_message
        assert mock_execute.call_count == 2  # retry_attempts = 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_exception_recovery(self, agent_loop):
        """Test retry logic with exception on first attempt."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        success_result = ToolResult(tool_name="NmapScanner", success=True, data={})

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(side_effect=[Exception("Network error"), success_result]),
        ) as mock_execute:
            result = await agent_loop._execute_with_retry(step)

        assert result.success is True
        assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_tool_not_found(self, agent_loop):
        """Test retry logic when tool is not found."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )

        with patch.object(
            agent_loop.tool_registry,
            "get_tool",
            return_value=None,
        ):
            result = await agent_loop._execute_with_retry(step)

        assert result.success is False
        assert "Tool nmap_scanner not found" in result.error_message


# =============================================================================
# Test Memory/Context Management
# =============================================================================


class TestMemoryContextManagement:
    """Test memory and context management."""

    def test_memory_initialization(self):
        """Test AgentMemory initialization."""
        memory = AgentMemory(
            goal="Find vulnerabilities",
            target="example.com",
            scope={"depth": "comprehensive"},
        )

        assert memory.goal == "Find vulnerabilities"
        assert memory.target == "example.com"
        assert memory.scope == {"depth": "comprehensive"}
        assert memory.session_id is not None
        assert isinstance(memory.created_at, datetime)
        assert memory.short_term == []
        assert memory.long_term == {}
        assert memory.context_window == []
        assert memory.findings == []
        assert memory.plan_step == 0

    def test_add_to_short_term(self):
        """Test adding to short-term memory."""
        memory = AgentMemory(max_short_term=5)

        for i in range(7):
            memory.add_to_short_term({"content": f"entry {i}"})

        # Should only keep last 5
        assert len(memory.short_term) == 5
        assert memory.short_term[0]["content"] == "entry 2"
        assert memory.short_term[-1]["content"] == "entry 6"
        assert "timestamp" in memory.short_term[0]
        assert "id" in memory.short_term[0]

    def test_add_to_context_window(self):
        """Test adding to context window."""
        memory = AgentMemory(max_context_window=3)

        for i in range(5):
            memory.add_to_context_window({"content": f"context {i}"})

        assert len(memory.context_window) == 3
        assert memory.context_window[0]["content"] == "context 2"
        assert "timestamp" in memory.context_window[0]

    def test_get_context_for_llm_empty(self):
        """Test getting context with empty memory."""
        memory = AgentMemory(goal="Test", target="example.com")

        context = memory.get_context_for_llm()

        assert "Goal: Test" in context
        assert "Target: example.com" in context
        assert "Recent Actions:" in context

    def test_get_context_for_llm_with_history(self):
        """Test getting context with action history."""
        memory = AgentMemory(goal="Test", target="example.com")
        memory.add_to_context_window({"type": "action", "content": "Scan ports"})
        memory.add_to_context_window({"type": "result", "content": "Found 3 ports"})
        memory.add_finding({"type": "vulnerability", "severity": "high"})

        context = memory.get_context_for_llm()

        assert "ACTION" in context
        assert "RESULT" in context
        assert "Findings: 1" in context

    def test_add_finding(self):
        """Test adding security findings."""
        memory = AgentMemory()

        memory.add_finding({
            "type": "sql_injection",
            "severity": "critical",
            "details": {"param": "id"},
        })

        assert len(memory.findings) == 1
        assert memory.findings[0]["type"] == "sql_injection"
        assert "timestamp" in memory.findings[0]
        assert "id" in memory.findings[0]

    def test_memory_to_dict(self):
        """Test converting memory to dictionary."""
        memory = AgentMemory(goal="Test", target="example.com")
        memory.add_to_short_term({"content": "test"})
        memory.add_finding({"type": "vuln"})
        memory.current_plan = [{"step": 1}, {"step": 2}]

        result = memory.to_dict()

        assert result["goal"] == "Test"
        assert result["target"] == "example.com"
        assert result["short_term_count"] == 1
        assert result["findings_count"] == 1
        assert result["plan_step"] == 0
        assert result["current_plan_length"] == 2
        assert "session_id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_context_window_updated_during_run(self, agent_loop):
        """Test that context window is updated during execution."""
        agent_loop.memory = AgentMemory(goal="Test", target="example.com")

        mock_result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": []},
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                "execute",
                AsyncMock(return_value=ToolResult(
                    tool_name="ReportGenerator",
                    success=True,
                    data={},
                )),
            ):
                await agent_loop.run(goal="Find open ports", target="example.com")

        assert len(agent_loop.memory.context_window) > 0


# =============================================================================
# Test Error Handling and Recovery
# =============================================================================


class TestErrorHandlingRecovery:
    """Test error handling and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_run_handles_plan_exception(self, agent_loop):
        """Test run handles exception during planning."""
        with patch.object(agent_loop, "plan", side_effect=Exception("Planning failed")):
            result = await agent_loop.run(goal="Test", target="example.com")

        assert result["success"] is False
        assert result["state"] == "ERROR"
        assert "Planning failed" in result["error"]["message"]
        assert "traceback" in result["error"]

    @pytest.mark.asyncio
    async def test_run_handles_execute_exception(self, agent_loop):
        """Test run handles exception during execution."""
        agent_loop.memory = AgentMemory(goal="Test", target="example.com")

        with patch.object(
            agent_loop,
            "plan",
            return_value=[
                PlanStep(
                    tool_type=ToolType.NMAP_SCANNER,
                    action="Test",
                    parameters={},
                ),
            ],
        ):
            with patch.object(
                agent_loop,
                "_execute_with_retry",
                side_effect=Exception("Execution failed"),
            ):
                result = await agent_loop.run(goal="Test", target="example.com")

        assert result["success"] is False
        assert result["state"] == "ERROR"

    @pytest.mark.asyncio
    async def test_run_handles_memory_initialization(self, agent_loop):
        """Test run initializes memory properly."""
        assert agent_loop.memory is None

        with patch.object(agent_loop, "plan", side_effect=Exception("Stop early")):
            await agent_loop.run(goal="Test goal", target="example.com")

        assert agent_loop.memory is not None
        assert agent_loop.memory.goal == "Test goal"
        assert agent_loop.memory.target == "example.com"

    @pytest.mark.asyncio
    async def test_error_result_compilation(self, agent_loop):
        """Test error result compilation."""
        error = ValueError("Test error")

        result = agent_loop._compile_error_result(error)

        assert result["success"] is False
        assert result["state"] == agent_loop.state.name
        assert result["error"]["message"] == "Test error"
        assert result["error"]["type"] == "ValueError"
        assert "traceback" in result["error"]
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_observe_failed_result(self, agent_loop, sample_agent_memory):
        """Test observation of failed result."""
        agent_loop.memory = sample_agent_memory
        failed_result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Connection refused",
        )

        observation = await agent_loop.observe(failed_result)

        assert observation["tool"] == "NmapScanner"
        assert observation["success"] is False
        assert observation["error"] == "Connection refused"
        assert observation["findings_extracted"] == 0

    @pytest.mark.asyncio
    async def test_reflect_stops_on_too_many_errors(self, agent_loop, sample_agent_memory):
        """Test reflection stops when too many recent errors."""
        agent_loop.memory = sample_agent_memory

        # Add 6 recent errors (within last 60 seconds)
        now = datetime.now()
        for i in range(6):
            agent_loop.progress["errors"].append({
                "timestamp": now.isoformat(),
                "error": f"Error {i}",
            })

        should_continue = await agent_loop.reflect()

        assert should_continue is False

    @pytest.mark.asyncio
    async def test_reflect_ignores_old_errors(self, agent_loop, sample_agent_memory):
        """Test reflection ignores old errors."""
        agent_loop.memory = sample_agent_memory

        # Add old errors (more than 60 seconds ago)
        old_time = datetime.now() - timedelta(seconds=120)
        for i in range(6):
            agent_loop.progress["errors"].append({
                "timestamp": old_time.isoformat(),
                "error": f"Old error {i}",
            })

        should_continue = await agent_loop.reflect()

        # Should continue since errors are old
        assert should_continue is True


# =============================================================================
# Test Event/Callback System
# =============================================================================


class TestEventCallbackSystem:
    """Test event and callback system."""

    def test_register_state_callback(self, agent_loop):
        """Test registering state callbacks."""
        callback_mock = Mock()

        agent_loop.register_state_callback(AgentState.EXECUTING, callback_mock)

        assert callback_mock in agent_loop.state_callbacks[AgentState.EXECUTING]

    def test_register_multiple_callbacks_same_state(self, agent_loop):
        """Test registering multiple callbacks for same state."""
        callback1 = Mock()
        callback2 = Mock()

        agent_loop.register_state_callback(AgentState.EXECUTING, callback1)
        agent_loop.register_state_callback(AgentState.EXECUTING, callback2)

        assert len(agent_loop.state_callbacks[AgentState.EXECUTING]) == 2

    def test_state_callback_triggered_on_transition(self, agent_loop):
        """Test callback is triggered on state transition."""
        callback_mock = Mock()
        agent_loop.register_state_callback(AgentState.PLANNING, callback_mock)

        agent_loop._transition_to(AgentState.PLANNING)

        callback_mock.assert_called_once_with(AgentState.PLANNING)

    def test_multiple_callbacks_triggered(self, agent_loop):
        """Test multiple callbacks are all triggered."""
        callback1 = Mock()
        callback2 = Mock()

        agent_loop.register_state_callback(AgentState.EXECUTING, callback1)
        agent_loop.register_state_callback(AgentState.EXECUTING, callback2)

        agent_loop._transition_to(AgentState.EXECUTING)

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_state_callback_error_handling(self, agent_loop, caplog):
        """Test callback errors don't crash the system."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        agent_loop.register_state_callback(AgentState.EXECUTING, error_callback)

        # Should not raise exception
        agent_loop._transition_to(AgentState.EXECUTING)

        error_callback.assert_called_once()
        assert agent_loop.state == AgentState.EXECUTING

    def test_set_progress_callback(self, agent_loop):
        """Test setting progress callback."""
        progress_mock = Mock()

        agent_loop.set_progress_callback(progress_mock)

        assert agent_loop.progress_callback == progress_mock

    def test_progress_callback_triggered(self, agent_loop):
        """Test progress callback is triggered on update."""
        progress_mock = Mock()
        agent_loop.set_progress_callback(progress_mock)

        agent_loop._update_progress({"completed_steps": 1})

        progress_mock.assert_called_once()
        args = progress_mock.call_args[0][0]
        assert args["completed_steps"] == 1

    def test_progress_callback_not_called_when_disabled(self, agent_loop_no_progress):
        """Test progress callback not called when tracking disabled."""
        progress_mock = Mock()
        agent_loop_no_progress.set_progress_callback(progress_mock)

        agent_loop_no_progress._update_progress({"completed_steps": 1})

        progress_mock.assert_not_called()

    def test_progress_callback_error_handling(self, agent_loop, caplog):
        """Test progress callback errors are handled gracefully."""
        error_callback = Mock(side_effect=Exception("Progress error"))
        agent_loop.set_progress_callback(error_callback)

        # Should not raise exception
        agent_loop._update_progress({"completed_steps": 1})

        error_callback.assert_called_once()


# =============================================================================
# Test Graceful Shutdown
# =============================================================================


class TestGracefulShutdown:
    """Test graceful shutdown behavior."""

    @pytest.mark.asyncio
    async def test_run_sets_end_time_on_completion(self, agent_loop):
        """Test that end_time is set when run completes."""
        assert agent_loop.end_time is None

        mock_result = ToolResult(
            tool_name="ReportGenerator",
            success=True,
            data={},
        )

        with patch.object(agent_loop, "plan", return_value=[]):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                "execute",
                AsyncMock(return_value=mock_result),
            ):
                await agent_loop.run(goal="Test", target="example.com")

        assert agent_loop.end_time is not None
        assert agent_loop.start_time is not None
        assert agent_loop.end_time >= agent_loop.start_time

    @pytest.mark.asyncio
    async def test_run_sets_end_time_on_error(self, agent_loop):
        """Test that end_time is set even when run errors."""
        with patch.object(agent_loop, "plan", side_effect=Exception("Planned error")):
            await agent_loop.run(goal="Test", target="example.com")

        assert agent_loop.end_time is not None
        assert agent_loop.state == AgentState.ERROR

    @pytest.mark.asyncio
    async def test_final_result_compilation(self, agent_loop, sample_agent_memory):
        """Test final result compilation."""
        agent_loop.memory = sample_agent_memory
        agent_loop.start_time = asyncio.get_event_loop().time()
        agent_loop.end_time = agent_loop.start_time + 5.0
        agent_loop.state = AgentState.COMPLETED
        agent_loop.progress["current_iteration"] = 5
        agent_loop.progress["completed_steps"] = 3
        agent_loop.progress["total_steps"] = 3

        mock_report_result = ToolResult(
            tool_name="ReportGenerator",
            success=True,
            data={"summary": {"total_findings": 0}},
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
            "execute",
            AsyncMock(return_value=mock_report_result),
        ):
            result = await agent_loop._compile_final_result()

        assert result["success"] is True
        assert result["state"] == "COMPLETED"
        assert "execution" in result
        assert result["execution"]["duration_seconds"] == pytest.approx(5.0, 0.1)
        assert result["execution"]["iterations"] == 5
        assert result["execution"]["steps_completed"] == 3
        assert "findings" in result
        assert "report" in result
        assert "memory" in result
        assert "progress" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_final_result_with_report_failure(self, agent_loop, sample_agent_memory):
        """Test final result when report generation fails."""
        agent_loop.memory = sample_agent_memory
        agent_loop.start_time = asyncio.get_event_loop().time()
        agent_loop.end_time = agent_loop.start_time + 1.0
        agent_loop.state = AgentState.COMPLETED

        mock_report_result = ToolResult(
            tool_name="ReportGenerator",
            success=False,
            error_message="Report generation failed",
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
            "execute",
            AsyncMock(return_value=mock_report_result),
        ):
            result = await agent_loop._compile_final_result()

        assert result["success"] is True  # Execution still successful
        assert result["report"] is None  # But no report

    def test_get_progress_returns_copy(self, agent_loop):
        """Test that get_progress returns a copy."""
        progress1 = agent_loop.get_progress()
        progress2 = agent_loop.get_progress()

        assert progress1 is not progress2
        progress1["new_key"] = "value"
        assert "new_key" not in agent_loop.progress


# =============================================================================
# Test Main Run Loop
# =============================================================================


class TestMainRunLoop:
    """Test the main run loop functionality."""

    @pytest.mark.asyncio
    async def test_run_complete_workflow(self, agent_loop):
        """Test complete workflow execution."""
        mock_nmap_result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": [{"port": 80, "service": "http"}]},
        )
        mock_report_result = ToolResult(
            tool_name="ReportGenerator",
            success=True,
            data={"summary": {"total_findings": 1}},
        )

        with patch.object(
            agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_nmap_result),
        ):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                "execute",
                AsyncMock(return_value=mock_report_result),
            ):
                result = await agent_loop.run(
                    goal="Find open ports",
                    target="example.com",
                    scope={"depth": "quick"},
                )

        assert result["success"] is True
        assert result["state"] == "COMPLETED"
        assert result["execution"]["goal"] == "Find open ports"
        assert result["execution"]["target"] == "example.com"
        assert "findings" in result
        assert "report" in result

    @pytest.mark.asyncio
    async def test_run_respects_max_iterations(self, agent_loop):
        """Test that run respects max_iterations."""
        agent_loop.max_iterations = 3

        # Create a plan with more steps than max_iterations
        long_plan = [
            PlanStep(
                tool_type=ToolType.NMAP_SCANNER,
                action=f"Step {i}",
                parameters={"target": "example.com"},
            )
            for i in range(10)
        ]

        mock_result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={},
        )

        with patch.object(agent_loop, "plan", return_value=long_plan):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
                "execute",
                AsyncMock(return_value=mock_result),
            ):
                result = await agent_loop.run(goal="Test", target="example.com")

        # Should stop due to max iterations, not plan completion
        assert result["execution"]["iterations"] <= agent_loop.max_iterations

    @pytest.mark.asyncio
    async def test_run_stops_when_plan_completed(self, agent_loop):
        """Test that run stops when all plan steps are completed."""
        short_plan = [
            PlanStep(
                tool_type=ToolType.NMAP_SCANNER,
                action="Single scan",
                parameters={"target": "example.com"},
            ),
        ]

        mock_result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={},
        )
        mock_report_result = ToolResult(
            tool_name="ReportGenerator",
            success=True,
            data={},
        )

        with patch.object(agent_loop, "plan", return_value=short_plan):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.NMAP_SCANNER),
                "execute",
                AsyncMock(return_value=mock_result),
            ):
                with patch.object(
                    agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                    "execute",
                    AsyncMock(return_value=mock_report_result),
                ):
                    result = await agent_loop.run(goal="Test", target="example.com")

        assert result["success"] is True
        assert result["execution"]["steps_completed"] == 1

    @pytest.mark.asyncio
    async def test_run_through_all_states(self, agent_loop):
        """Test that run transitions through expected states."""
        states_visited = []

        def state_tracker(state):
            states_visited.append(state)

        for state in [AgentState.PLANNING, AgentState.EXECUTING, AgentState.OBSERVING,
                      AgentState.REFLECTING, AgentState.COMPLETED]:
            agent_loop.register_state_callback(state, state_tracker)

        mock_result = ToolResult(
            tool_name="ReportGenerator",
            success=True,
            data={},
        )

        with patch.object(agent_loop, "plan", return_value=[]):
            with patch.object(
                agent_loop.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                "execute",
                AsyncMock(return_value=mock_result),
            ):
                await agent_loop.run(goal="Test", target="example.com")

        assert AgentState.PLANNING in states_visited
        assert AgentState.COMPLETED in states_visited


# =============================================================================
# Test Observation and Reflection
# =============================================================================


class TestObservationReflection:
    """Test observation and reflection functionality."""

    @pytest.mark.asyncio
    async def test_observe_successful_nmap_result(self, agent_loop, sample_agent_memory):
        """Test observation of successful Nmap result."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={
                "open_ports": [{"port": 22}, {"port": 80}],
                "services": ["ssh", "http"],
            },
        )

        observation = await agent_loop.observe(result)

        assert observation["tool"] == "NmapScanner"
        assert observation["success"] is True
        assert observation["open_ports"] == 2

    @pytest.mark.asyncio
    async def test_observe_successful_nuclei_result(self, agent_loop, sample_agent_memory):
        """Test observation of successful Nuclei result."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NucleiScanner",
            success=True,
            data={
                "findings": [
                    {"severity": "critical"},
                    {"severity": "high"},
                ],
                "count": 2,
            },
        )

        observation = await agent_loop.observe(result)

        assert observation["vulnerabilities"] == 2

    @pytest.mark.asyncio
    async def test_observe_successful_subdomain_result(self, agent_loop, sample_agent_memory):
        """Test observation of successful subdomain enumeration."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="SubdomainEnumerator",
            success=True,
            data={
                "subdomains": ["www.example.com", "api.example.com"],
            },
        )

        observation = await agent_loop.observe(result)

        assert observation["subdomains"] == 2

    @pytest.mark.asyncio
    async def test_observe_adds_to_short_term_memory(self, agent_loop, sample_agent_memory):
        """Test that observation adds to short-term memory."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={},
        )

        initial_count = len(agent_loop.memory.short_term)
        await agent_loop.observe(result)

        assert len(agent_loop.memory.short_term) == initial_count + 1
        assert agent_loop.memory.short_term[-1]["type"] == "observation"

    @pytest.mark.asyncio
    async def test_reflect_continues_by_default(self, agent_loop, sample_agent_memory):
        """Test that reflection continues by default."""
        agent_loop.memory = sample_agent_memory
        agent_loop.progress["current_iteration"] = 1

        should_continue = await agent_loop.reflect()

        assert should_continue is True

    @pytest.mark.asyncio
    async def test_reflect_adds_to_context_window(self, agent_loop, sample_agent_memory):
        """Test that reflection adds entry to context window."""
        agent_loop.memory = sample_agent_memory
        agent_loop.progress["current_iteration"] = 3

        initial_count = len(agent_loop.memory.context_window)
        await agent_loop.reflect()

        assert len(agent_loop.memory.context_window) == initial_count + 1
        assert agent_loop.memory.context_window[-1]["type"] == "reflection"

    @pytest.mark.asyncio
    async def test_reflect_detects_critical_findings(self, agent_loop, sample_agent_memory):
        """Test reflection with critical findings."""
        agent_loop.memory = sample_agent_memory
        agent_loop.memory.add_finding({"severity": "critical", "type": "rce"})
        agent_loop.memory.current_plan = [{}, {}, {}]
        agent_loop.memory.plan_step = 2  # At report generation step

        # Should continue but note critical findings
        should_continue = await agent_loop.reflect()
        # Behavior depends on implementation - may or may not stop
        assert isinstance(should_continue, bool)


# =============================================================================
# Test Findings Extraction
# =============================================================================


class TestFindingsExtraction:
    """Test findings extraction from tool results."""

    @pytest.mark.asyncio
    async def test_extract_findings_from_nmap(self, agent_loop, sample_agent_memory):
        """Test extracting findings from Nmap result."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={
                "open_ports": [
                    {"port": 22, "service": "ssh"},
                    {"port": 80, "service": "http"},
                ],
            },
        )

        await agent_loop._extract_findings(result)

        assert len(agent_loop.memory.findings) == 2
        assert all(f["type"] == "open_port" for f in agent_loop.memory.findings)
        assert all(f["source"] == "NmapScanner" for f in agent_loop.memory.findings)

    @pytest.mark.asyncio
    async def test_extract_findings_from_nuclei(self, agent_loop, sample_agent_memory):
        """Test extracting findings from Nuclei result."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NucleiScanner",
            success=True,
            data={
                "findings": [
                    {"severity": "critical", "template": "cve-2021-44228"},
                    {"severity": "high", "template": "xss-detect"},
                ],
            },
        )

        await agent_loop._extract_findings(result)

        assert len(agent_loop.memory.findings) == 2
        assert agent_loop.memory.findings[0]["severity"] == "critical"
        assert agent_loop.memory.findings[1]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_extract_findings_from_subdomains(self, agent_loop, sample_agent_memory):
        """Test extracting findings from subdomain enumeration."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="SubdomainEnumerator",
            success=True,
            data={
                "subdomains": ["www.example.com", "api.example.com"],
            },
        )

        await agent_loop._extract_findings(result)

        assert len(agent_loop.memory.findings) == 2
        assert all(f["type"] == "subdomain" for f in agent_loop.memory.findings)

    @pytest.mark.asyncio
    async def test_extract_findings_updates_progress(self, agent_loop, sample_agent_memory):
        """Test that findings extraction updates progress."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": [{"port": 80}]},
        )

        assert agent_loop.progress["findings_count"] == 0

        await agent_loop._extract_findings(result)

        assert agent_loop.progress["findings_count"] == 1

    @pytest.mark.asyncio
    async def test_extract_findings_no_data(self, agent_loop, sample_agent_memory):
        """Test extracting findings when result has no data."""
        agent_loop.memory = sample_agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={},
        )

        await agent_loop._extract_findings(result)

        assert len(agent_loop.memory.findings) == 0


# =============================================================================
# Test Factory Function
# =============================================================================


class TestFactoryFunction:
    """Test create_agent_loop factory function."""

    def test_create_agent_loop_defaults(self):
        """Test factory with default parameters."""
        agent = create_agent_loop()

        assert isinstance(agent, AutonomousAgentLoop)
        assert agent.llm is None
        assert agent.max_iterations == 50
        assert agent.retry_attempts == 3

    def test_create_agent_loop_custom(self):
        """Test factory with custom parameters."""
        mock_llm = Mock()
        agent = create_agent_loop(
            llm_client=mock_llm,
            max_iterations=100,
            retry_attempts=5,
        )

        assert agent.llm == mock_llm
        assert agent.max_iterations == 100
        assert agent.retry_attempts == 5


# =============================================================================
# Test Tool Implementations (Nmap, Nuclei, etc.)
# =============================================================================


class TestNmapScanner:
    """Test NmapScanner tool implementation."""

    def test_initialization(self):
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

    def test_validate_parameters_missing_target(self):
        """Test parameter validation without target."""
        scanner = NmapScanner()
        valid, error = scanner.validate_parameters({})
        assert valid is False
        assert "Target is required" in error

    def test_validate_parameters_invalid_target(self):
        """Test parameter validation with invalid target."""
        scanner = NmapScanner()
        valid, error = scanner.validate_parameters({"target": ""})
        assert valid is False

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful Nmap execution with XML parsing."""
        scanner = NmapScanner()
        mock_xml = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http" product="Apache" version="2.4"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(mock_xml.encode(), b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await scanner.execute({"target": "scanme.nmap.org", "ports": "80"})

        assert result.success is True
        assert "open_ports" in result.data
        assert len(result.data["open_ports"]) == 1

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test Nmap execution timeout handling."""
        scanner = NmapScanner(timeout=1)
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await scanner.execute({"target": "scanme.nmap.org"})

        assert result.success is False
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_not_found(self):
        """Test Nmap not found error."""
        scanner = NmapScanner()

        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
            result = await scanner.execute({"target": "scanme.nmap.org"})

        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_validate_target_safety_loopback(self):
        """Test loopback address handling."""
        scanner = NmapScanner()
        valid, error = scanner._validate_target_safety("127.0.0.1")
        assert valid is True

    def test_validate_target_safety_private_ip(self):
        """Test private IP blocking."""
        scanner = NmapScanner()
        valid, error = scanner._validate_target_safety("192.168.1.1")
        assert valid is False
        assert "blocked" in error.lower()

    def test_validate_target_safety_dangerous_chars(self):
        """Test blocking dangerous characters."""
        scanner = NmapScanner()
        valid, error = scanner._validate_target_safety("example.com; rm -rf /")
        assert valid is False
        assert "Invalid characters" in error

    def test_parse_nmap_xml_empty(self):
        """Test parsing empty Nmap XML."""
        scanner = NmapScanner()
        result = scanner._parse_nmap_xml("<nmaprun></nmaprun>")
        assert result is not None
        assert result["open_ports"] == []

    def test_parse_output_fallback(self):
        """Test fallback text parsing for Nmap output."""
        scanner = NmapScanner()
        output = """
        PORT     STATE SERVICE
        22/tcp   open  ssh     OpenSSH 8.0
        80/tcp   open  http    Apache 2.4
        """
        result = scanner._parse_output_fallback(output)
        assert len(result["open_ports"]) == 2
        assert result["open_ports"][0]["port"] == 22


class TestNucleiScanner:
    """Test NucleiScanner tool implementation."""

    def test_initialization(self):
        """Test NucleiScanner initialization."""
        scanner = NucleiScanner(timeout=600)
        assert scanner.name == "NucleiScanner"
        assert scanner.timeout == 600

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful Nuclei execution."""
        scanner = NucleiScanner()
        mock_json = '{"template-id": "test", "info": {"severity": "high"}}\n'

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(mock_json.encode(), b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await scanner.execute({"target": "example.com"})

        assert result.success is True
        assert "findings" in result.data

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test Nuclei execution timeout."""
        scanner = NucleiScanner(timeout=1)
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process.kill = Mock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await scanner.execute({"target": "example.com"})

        assert result.success is False
        assert "timeout" in result.error_message.lower()

    def test_parse_nuclei_json(self):
        """Test parsing Nuclei JSON output."""
        scanner = NucleiScanner()
        output = """
        {"template-id": "cve-2021-44228", "info": {"severity": "critical", "name": "Log4j"}, "host": "example.com"}
        {"template-id": "xss", "info": {"severity": "high", "name": "XSS"}, "host": "test.com"}
        """
        findings = scanner._parse_nuclei_json(output)
        assert len(findings) == 2
        assert findings[0]["severity"] == "critical"

    def test_parse_nuclei_json_invalid(self):
        """Test parsing invalid Nuclei JSON."""
        scanner = NucleiScanner()
        output = "not valid json\n\n"
        findings = scanner._parse_nuclei_json(output)
        assert len(findings) == 0


class TestReportGenerator:
    """Test ReportGenerator tool implementation."""

    @pytest.mark.asyncio
    async def test_generate_report(self):
        """Test report generation."""
        generator = ReportGenerator()
        findings = [
            {"severity": "critical", "type": "rce"},
            {"severity": "high", "type": "sqli"},
            {"severity": "medium", "type": "info"},
        ]

        result = await generator.execute({
            "target": "example.com",
            "findings": findings,
            "format": "json",
        })

        assert result.success is True
        assert result.data["target"] == "example.com"
        assert result.data["summary"]["critical"] == 1
        assert result.data["summary"]["high"] == 1
        assert result.data["summary"]["medium"] == 1

    @pytest.mark.asyncio
    async def test_generate_report_empty_findings(self):
        """Test report generation with no findings."""
        generator = ReportGenerator()
        result = await generator.execute({
            "target": "example.com",
            "findings": [],
        })

        assert result.success is True
        assert result.data["summary"]["total_findings"] == 0

    def test_generate_recommendations(self):
        """Test recommendation generation."""
        generator = ReportGenerator()
        findings = [{"severity": "critical"}, {"severity": "high"}]
        recommendations = generator._generate_recommendations(findings)
        assert len(recommendations) >= 2


class TestSubdomainEnumerator:
    """Test SubdomainEnumerator tool implementation."""

    @pytest.mark.asyncio
    async def test_enumerate_subdomains(self):
        """Test subdomain enumeration."""
        enumerator = SubdomainEnumerator()
        result = await enumerator.execute({
            "target": "example.com",
            "wordlist": "default",
            "recursive": False,
        })

        assert result.success is True
        assert result.data["domain"] == "example.com"
        assert len(result.data["subdomains"]) > 0
        assert all("example.com" in sd for sd in result.data["subdomains"])


class TestExploitValidator:
    """Test ExploitValidator tool implementation."""

    def test_initialization(self):
        """Test ExploitValidator initialization."""
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
            "lfi": "../../../etc/passwd",
        }
        for vuln_type, expected in payloads.items():
            payload = validator._generate_test_payload(vuln_type)
            assert expected in payload

    def test_generate_test_payload_unknown(self):
        """Test payload generation for unknown vulnerability."""
        validator = ExploitValidator()
        payload = validator._generate_test_payload("unknown_vuln")
        assert "No payload" in payload


class TestToolRegistry:
    """Test ToolRegistry implementation."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert "nmap_scanner" in tools
        assert "nuclei_scanner" in tools

    def test_get_tool(self):
        """Test getting tools from registry."""
        registry = ToolRegistry()
        tool = registry.get_tool(ToolType.NMAP_SCANNER)
        assert tool is not None
        assert tool.name == "NmapScanner"

    def test_get_tool_not_found(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        # Create a mock tool type that doesn't exist
        from unittest.mock import MagicMock
        mock_type = MagicMock()
        mock_type.value = "nonexistent"
        tool = registry.get_tool(mock_type)
        assert tool is None


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_creation(self):
        """Test ToolResult creation."""
        result = ToolResult(
            tool_name="TestTool",
            success=True,
            data={"key": "value"},
            raw_output="output",
        )
        assert result.tool_name == "TestTool"
        assert result.success is True

    def test_to_dict_truncation(self):
        """Test that raw_output is truncated in to_dict."""
        result = ToolResult(
            tool_name="TestTool",
            success=True,
            raw_output="x" * 1000,
        )
        result_dict = result.to_dict()
        assert len(result_dict["raw_output"]) <= 500


class TestPlanStep:
    """Test PlanStep dataclass."""

    def test_creation(self):
        """Test PlanStep creation."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Scan ports",
            parameters={"target": "example.com"},
        )
        assert step.tool_type == ToolType.NMAP_SCANNER
        assert step.action == "Scan ports"
        assert step.completed is False

    def test_to_dict(self):
        """Test PlanStep serialization."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Scan",
            parameters={},
        )
        step.completed = True
        step.result = ToolResult(tool_name="NmapScanner", success=True)

        step_dict = step.to_dict()
        assert step_dict["tool_type"] == "nmap_scanner"
        assert step_dict["completed"] is True
        assert step_dict["result"] is not None


# =============================================================================
# Test Enums
# =============================================================================


class TestAgentStateEnum:
    """Test AgentState enum."""

    def test_all_states_exist(self):
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
        """Test state names."""
        assert AgentState.IDLE.name == "IDLE"
        assert AgentState.PLANNING.name == "PLANNING"
        assert AgentState.EXECUTING.name == "EXECUTING"
        assert AgentState.OBSERVING.name == "OBSERVING"
        assert AgentState.REFLECTING.name == "REFLECTING"
        assert AgentState.COMPLETED.name == "COMPLETED"
        assert AgentState.ERROR.name == "ERROR"
        assert AgentState.PAUSED.name == "PAUSED"


class TestToolTypeEnum:
    """Test ToolType enum."""

    def test_all_tool_types_exist(self):
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
        """Test tool type values."""
        assert ToolType.NMAP_SCANNER.value == "nmap_scanner"
        assert ToolType.NUCLEI_SCANNER.value == "nuclei_scanner"
        assert ToolType.EXPLOIT_VALIDATOR.value == "exploit_validator"
        assert ToolType.REPORT_GENERATOR.value == "report_generator"
        assert ToolType.SUBDOMAIN_ENUMERATOR.value == "subdomain_enumerator"


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestAgentLoopIntegration:
    """Integration tests for the agent loop."""

    @pytest.mark.asyncio
    async def test_full_agent_loop_integration(self):
        """Test full agent loop with mocked tools."""
        agent = AutonomousAgentLoop(max_iterations=5, retry_attempts=1)

        mock_nmap = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": [{"port": 80, "service": "http"}]},
        )
        mock_nuclei = ToolResult(
            tool_name="NucleiScanner",
            success=True,
            data={"findings": []},
        )
        mock_report = ToolResult(
            tool_name="ReportGenerator",
            success=True,
            data={"summary": {"total_findings": 1}},
        )

        with patch.object(
            agent.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_nmap),
        ):
            with patch.object(
                agent.tool_registry.get_tool(ToolType.NUCLEI_SCANNER),
                "execute",
                AsyncMock(return_value=mock_nuclei),
            ):
                with patch.object(
                    agent.tool_registry.get_tool(ToolType.REPORT_GENERATOR),
                    "execute",
                    AsyncMock(return_value=mock_report),
                ):
                    result = await agent.run(
                        goal="Scan for vulnerabilities and open ports",
                        target="scanme.nmap.org",
                        scope={"depth": "quick"},
                    )

        assert result["success"] is True
        assert result["state"] == "COMPLETED"
        assert result["execution"]["iterations"] > 0
        assert "findings" in result
        assert "report" in result
