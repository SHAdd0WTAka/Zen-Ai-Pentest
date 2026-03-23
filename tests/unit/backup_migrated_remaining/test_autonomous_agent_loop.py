"""
Tests for autonomous/agent_loop.py - ReAct Agent Loop

Tests the AutonomousAgentLoop class with ReAct pattern implementation:
- Agent initialization
- run() method execution
- Tool execution
- Memory integration
- State management
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from autonomous.agent_loop import (
    AgentMemory,
    AgentState,
    AutonomousAgentLoop,
    PlanStep,
    ToolRegistry,
    ToolResult,
    ToolType,
    create_agent_loop,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm():
    """Mock LLM client for testing."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Test LLM response")
    return client


@pytest.fixture
def agent(mock_llm):
    """Create an AutonomousAgentLoop instance for testing."""
    return AutonomousAgentLoop(
        llm_client=mock_llm,
        max_iterations=10,
        retry_attempts=2,
        retry_delay=0.1,
    )


@pytest.fixture
def agent_memory():
    """Create a sample AgentMemory for testing."""
    return AgentMemory(
        goal="Test goal",
        target="example.com",
        scope={"depth": "standard"},
    )


@pytest.fixture
def sample_plan():
    """Create a sample execution plan."""
    return [
        PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Scan open ports",
            parameters={"target": "example.com", "ports": "80,443"},
        ),
        PlanStep(
            tool_type=ToolType.REPORT_GENERATOR,
            action="Generate report",
            parameters={"target": "example.com"},
        ),
    ]


# ============================================================================
# Test ReActAgent Initialization
# ============================================================================


class TestReActAgentInitialization:
    """Test AutonomousAgentLoop initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        agent = AutonomousAgentLoop()

        assert agent.max_iterations == 50
        assert agent.retry_attempts == 3
        assert agent.retry_delay == 2.0
        assert agent.state == AgentState.IDLE
        assert agent.memory is None
        assert agent.llm is None
        assert agent.enable_progress_tracking is True

    def test_custom_initialization(self, mock_llm):
        """Test initialization with custom values."""
        agent = AutonomousAgentLoop(
            llm_client=mock_llm,
            max_iterations=20,
            retry_attempts=5,
            retry_delay=1.0,
            enable_progress_tracking=False,
        )

        assert agent.llm == mock_llm
        assert agent.max_iterations == 20
        assert agent.retry_attempts == 5
        assert agent.retry_delay == 1.0
        assert agent.enable_progress_tracking is False

    def test_tool_registry_initialized(self, agent):
        """Test that tool registry is initialized."""
        assert agent.tool_registry is not None
        assert isinstance(agent.tool_registry, ToolRegistry)

    def test_progress_tracking_initialized(self, agent):
        """Test that progress tracking is initialized."""
        progress = agent.progress

        assert progress["current_iteration"] == 0
        assert progress["total_iterations"] == 10
        assert progress["completed_steps"] == 0
        assert progress["total_steps"] == 0
        assert progress["findings_count"] == 0
        assert progress["errors"] == []


# ============================================================================
# Test State Management
# ============================================================================


class TestStateManagement:
    """Test agent state transitions and callbacks."""

    def test_initial_state(self, agent):
        """Test initial state is IDLE."""
        assert agent.get_state() == AgentState.IDLE

    def test_state_transition(self, agent):
        """Test state transitions."""
        agent._transition_to(AgentState.PLANNING)

        assert agent.state == AgentState.PLANNING
        assert agent.previous_state == AgentState.IDLE

    def test_multiple_transitions(self, agent):
        """Test multiple state transitions."""
        states = [
            AgentState.PLANNING,
            AgentState.EXECUTING,
            AgentState.OBSERVING,
            AgentState.REFLECTING,
        ]

        for state in states:
            agent._transition_to(state)
            assert agent.state == state

    def test_state_callback_registration(self, agent):
        """Test registering state callbacks."""
        callback = Mock()

        agent.register_state_callback(AgentState.EXECUTING, callback)

        assert callback in agent.state_callbacks[AgentState.EXECUTING]

    def test_state_callback_triggered(self, agent):
        """Test that callbacks are triggered on state transition."""
        callback = Mock()
        agent.register_state_callback(AgentState.PLANNING, callback)

        agent._transition_to(AgentState.PLANNING)

        callback.assert_called_once_with(AgentState.PLANNING)

    def test_state_callback_error_handling(self, agent):
        """Test that callback errors don't break state transition."""
        bad_callback = Mock(side_effect=Exception("Callback error"))
        agent.register_state_callback(AgentState.EXECUTING, bad_callback)

        # Should not raise
        agent._transition_to(AgentState.EXECUTING)

        assert agent.state == AgentState.EXECUTING


# ============================================================================
# Test Progress Management
# ============================================================================


class TestProgressManagement:
    """Test progress tracking and callbacks."""

    def test_progress_callback(self, agent):
        """Test setting progress callback."""
        callback = Mock()

        agent.set_progress_callback(callback)

        assert agent.progress_callback == callback

    def test_progress_update(self, agent):
        """Test updating progress."""
        agent._update_progress({"completed_steps": 5, "findings_count": 3})

        assert agent.progress["completed_steps"] == 5
        assert agent.progress["findings_count"] == 3

    def test_progress_callback_triggered(self, agent):
        """Test that progress callback is triggered on update."""
        callback = Mock()
        agent.set_progress_callback(callback)

        agent._update_progress({"completed_steps": 1})

        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["completed_steps"] == 1

    def test_progress_callback_disabled(self, agent):
        """Test that callback respects enable_progress_tracking."""
        agent.enable_progress_tracking = False
        callback = Mock()
        agent.set_progress_callback(callback)

        agent._update_progress({"completed_steps": 1})

        callback.assert_not_called()


# ============================================================================
# Test run() Method
# ============================================================================


class TestRunMethod:
    """Test the main run() method."""

    @pytest.mark.asyncio
    async def test_run_successful_execution(self, agent, sample_plan):
        """Test successful execution of run()."""
        mock_result = ToolResult(
            tool_name="NmapScanner", success=True, data={"open_ports": []}
        )

        with patch.object(agent, "plan", AsyncMock(return_value=sample_plan)):
            with patch.object(
                agent,
                "_execute_with_retry",
                AsyncMock(return_value=mock_result),
            ):
                result = await agent.run(
                    goal="Scan ports", target="example.com"
                )

        assert result["success"] is True
        assert result["state"] == "COMPLETED"
        assert "execution" in result
        assert "findings" in result
        assert "report" in result

    @pytest.mark.asyncio
    async def test_run_with_error(self, agent):
        """Test run() handling execution errors."""
        with patch.object(
            agent, "plan", side_effect=Exception("Planning failed")
        ):
            result = await agent.run(goal="Test", target="example.com")

        assert result["success"] is False
        assert result["state"] == "ERROR"
        assert "Planning failed" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_run_memory_initialized(self, agent, sample_plan):
        """Test that memory is initialized during run()."""
        mock_result = ToolResult(tool_name="Test", success=True, data={})

        with patch.object(agent, "plan", AsyncMock(return_value=sample_plan)):
            with patch.object(
                agent,
                "_execute_with_retry",
                AsyncMock(return_value=mock_result),
            ):
                await agent.run(
                    goal="Test goal",
                    target="test.com",
                    scope={"depth": "full"},
                )

        assert agent.memory is not None
        assert agent.memory.goal == "Test goal"
        assert agent.memory.target == "test.com"
        assert agent.memory.scope == {"depth": "full"}

    @pytest.mark.asyncio
    async def test_run_all_steps_completed(self, agent, sample_plan):
        """Test that all plan steps are executed."""
        mock_result = ToolResult(tool_name="Test", success=True, data={})

        with patch.object(agent, "plan", AsyncMock(return_value=sample_plan)):
            with patch.object(
                agent,
                "_execute_with_retry",
                AsyncMock(return_value=mock_result),
            ):
                result = await agent.run(goal="Test", target="example.com")

        assert result["execution"]["steps_completed"] == len(sample_plan)


# ============================================================================
# Test Planning
# ============================================================================


class TestPlanning:
    """Test the plan() method."""

    @pytest.mark.asyncio
    async def test_plan_port_scan_goal(self, agent):
        """Test planning for port scan goal."""
        agent.memory = AgentMemory(
            goal="Find open ports", target="example.com"
        )

        plan = await agent.plan()

        assert len(plan) > 0
        assert any(step.tool_type == ToolType.NMAP_SCANNER for step in plan)

    @pytest.mark.asyncio
    async def test_plan_vulnerability_scan_goal(self, agent):
        """Test planning for vulnerability scan goal."""
        agent.memory = AgentMemory(
            goal="Scan for vulnerabilities", target="example.com"
        )

        plan = await agent.plan()

        assert any(step.tool_type == ToolType.NUCLEI_SCANNER for step in plan)

    @pytest.mark.asyncio
    async def test_plan_subdomain_enumeration_goal(self, agent):
        """Test planning for subdomain enumeration goal."""
        agent.memory = AgentMemory(
            goal="Enumerate subdomains", target="example.com"
        )

        plan = await agent.plan()

        assert any(
            step.tool_type == ToolType.SUBDOMAIN_ENUMERATOR for step in plan
        )

    @pytest.mark.asyncio
    async def test_plan_exploit_validation_goal(self, agent):
        """Test planning for exploit validation goal."""
        agent.memory = AgentMemory(
            goal="Validate exploits", target="example.com"
        )

        plan = await agent.plan()

        assert any(
            step.tool_type == ToolType.EXPLOIT_VALIDATOR for step in plan
        )

    @pytest.mark.asyncio
    async def test_plan_default_plan(self, agent):
        """Test default plan when no specific keywords match."""
        agent.memory = AgentMemory(goal="Do something", target="example.com")

        plan = await agent.plan()

        # Default plan only has REPORT_GENERATOR when no keywords match
        assert len(plan) >= 1
        assert any(
            step.tool_type == ToolType.REPORT_GENERATOR for step in plan
        )

    @pytest.mark.asyncio
    async def test_plan_stored_in_memory(self, agent):
        """Test that plan is stored in memory."""
        agent.memory = AgentMemory(goal="Test", target="example.com")

        await agent.plan()

        assert len(agent.memory.short_term) > 0
        assert any(
            entry.get("type") == "plan_step"
            for entry in agent.memory.short_term
        )


# ============================================================================
# Test Tool Execution
# ============================================================================


class TestToolExecution:
    """Test tool execution methods."""

    @pytest.mark.asyncio
    async def test_execute_action_success(self, agent):
        """Test successful action execution."""
        mock_result = ToolResult(
            tool_name="NmapScanner", success=True, data={"ports": [80]}
        )

        with patch.object(
            agent.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent.execute_action(
                {
                    "tool_type": "nmap_scanner",
                    "parameters": {"target": "example.com"},
                }
            )

        assert result.success is True
        assert result.tool_name == "NmapScanner"

    @pytest.mark.asyncio
    async def test_execute_action_unknown_tool(self, agent):
        """Test execution with unknown tool type."""
        result = await agent.execute_action(
            {
                "tool_type": "unknown_tool",
                "parameters": {},
            }
        )

        assert result.success is False
        assert "Unknown tool" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_action_invalid_parameters(self, agent):
        """Test execution with invalid parameters."""
        result = await agent.execute_action(
            {
                "tool_type": "nmap_scanner",
                "parameters": {"target": ""},  # Empty target
            }
        )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, agent):
        """Test retry logic succeeds on first attempt."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )
        mock_result = ToolResult(
            tool_name="NmapScanner", success=True, data={}
        )

        with patch.object(
            agent.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=mock_result),
        ):
            result = await agent._execute_with_retry(step)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self, agent):
        """Test retry logic succeeds after failures."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )
        fail_result = ToolResult(
            tool_name="NmapScanner", success=False, error_message="Temp error"
        )
        success_result = ToolResult(
            tool_name="NmapScanner", success=True, data={}
        )

        with patch.object(
            agent.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(side_effect=[fail_result, success_result]),
        ):
            result = await agent._execute_with_retry(step)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_retry_all_failures(self, agent):
        """Test retry logic when all attempts fail."""
        step = PlanStep(
            tool_type=ToolType.NMAP_SCANNER,
            action="Test scan",
            parameters={"target": "example.com"},
        )
        fail_result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Persistent error",
        )

        with patch.object(
            agent.tool_registry.get_tool(ToolType.NMAP_SCANNER),
            "execute",
            AsyncMock(return_value=fail_result),
        ):
            result = await agent._execute_with_retry(step)

        assert result.success is False
        assert "All 2 attempts failed" in result.error_message


# ============================================================================
# Test Observation
# ============================================================================


class TestObservation:
    """Test observation handling."""

    @pytest.mark.asyncio
    async def test_observe_success(self, agent, agent_memory):
        """Test observation of successful result."""
        agent.memory = agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={"open_ports": [{"port": 80}, {"port": 443}]},
        )

        observation = await agent.observe(result)

        assert observation["tool"] == "NmapScanner"
        assert observation["success"] is True
        assert observation["open_ports"] == 2

    @pytest.mark.asyncio
    async def test_observe_failure(self, agent, agent_memory):
        """Test observation of failed result."""
        agent.memory = agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=False,
            error_message="Connection timeout",
        )

        observation = await agent.observe(result)

        assert observation["success"] is False
        assert "Connection timeout" in observation["error"]

    @pytest.mark.asyncio
    async def test_observe_vulnerabilities(self, agent, agent_memory):
        """Test observation with vulnerability findings."""
        agent.memory = agent_memory
        result = ToolResult(
            tool_name="NucleiScanner",
            success=True,
            data={
                "findings": [{"severity": "high"}, {"severity": "critical"}]
            },
        )

        observation = await agent.observe(result)

        assert observation["vulnerabilities"] == 2


# ============================================================================
# Test Reflection
# ============================================================================


class TestReflection:
    """Test reflection phase."""

    @pytest.mark.asyncio
    async def test_reflect_continue(self, agent, agent_memory):
        """Test reflection when should continue."""
        agent.memory = agent_memory
        agent.progress["current_iteration"] = 5

        should_continue = await agent.reflect()

        assert should_continue is True

    @pytest.mark.asyncio
    async def test_reflect_max_iterations(self, agent, agent_memory):
        """Test reflection at max iterations."""
        agent.memory = agent_memory
        agent.progress["current_iteration"] = agent.max_iterations

        should_continue = await agent.reflect()

        assert should_continue is False

    @pytest.mark.asyncio
    async def test_reflect_too_many_errors(self, agent, agent_memory):
        """Test reflection with too many recent errors."""
        agent.memory = agent_memory
        for i in range(6):
            agent.progress["errors"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Error {i}",
                }
            )

        should_continue = await agent.reflect()

        assert should_continue is False


# ============================================================================
# Test Memory Integration
# ============================================================================


class TestMemoryIntegration:
    """Test memory operations during execution."""

    @pytest.mark.asyncio
    async def test_extract_findings_from_nmap(self, agent, agent_memory):
        """Test extracting findings from Nmap results."""
        agent.memory = agent_memory
        result = ToolResult(
            tool_name="NmapScanner",
            success=True,
            data={
                "open_ports": [
                    {"port": 22, "service": "ssh"},
                    {"port": 80, "service": "http"},
                ]
            },
        )

        await agent._extract_findings(result)

        assert len(agent.memory.findings) == 2
        assert agent.progress["findings_count"] == 2

    @pytest.mark.asyncio
    async def test_extract_findings_from_nuclei(self, agent, agent_memory):
        """Test extracting findings from Nuclei results."""
        agent.memory = agent_memory
        result = ToolResult(
            tool_name="NucleiScanner",
            success=True,
            data={"findings": [{"severity": "high", "type": "xss"}]},
        )

        await agent._extract_findings(result)

        assert len(agent.memory.findings) == 1
        assert agent.memory.findings[0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_extract_findings_from_subdomains(self, agent, agent_memory):
        """Test extracting findings from subdomain enumeration."""
        agent.memory = agent_memory
        result = ToolResult(
            tool_name="SubdomainEnumerator",
            success=True,
            data={"subdomains": ["www.example.com", "api.example.com"]},
        )

        await agent._extract_findings(result)

        assert len(agent.memory.findings) == 2


# ============================================================================
# Test Utility Methods
# ============================================================================


class TestUtilityMethods:
    """Test utility methods."""

    def test_is_running(self, agent):
        """Test is_running check."""
        assert agent.is_running() is False

        agent._transition_to(AgentState.EXECUTING)
        assert agent.is_running() is True

        agent._transition_to(AgentState.COMPLETED)
        assert agent.is_running() is False

    def test_pause_resume(self, agent):
        """Test pause and resume functionality."""
        agent._transition_to(AgentState.EXECUTING)

        agent.pause()
        assert agent.state == AgentState.PAUSED

        agent.resume()
        assert agent.state == AgentState.EXECUTING

    def test_get_progress(self, agent):
        """Test getting progress copy."""
        progress = agent.get_progress()

        # Should be a copy
        progress["test"] = "value"
        assert "test" not in agent.progress


# ============================================================================
# Test Factory Function
# ============================================================================


class TestFactoryFunction:
    """Test create_agent_loop factory function."""

    def test_factory_creates_instance(self):
        """Test factory creates proper instance."""
        agent = create_agent_loop(max_iterations=25, retry_attempts=4)

        assert isinstance(agent, AutonomousAgentLoop)
        assert agent.max_iterations == 25
        assert agent.retry_attempts == 4

    def test_factory_with_llm(self, mock_llm):
        """Test factory with LLM client."""
        agent = create_agent_loop(llm_client=mock_llm)

        assert agent.llm == mock_llm
