"""
Comprehensive tests for autonomous/react.py

Target: 80%+ coverage
Tests: ReActLoop, Thought, Action, Observation, reasoning, action selection, reflection
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from autonomous.react import Action, ActionType, Observation, ReActLoop, Thought

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Test LLM response")
    return client


@pytest.fixture
def mock_tool_executor():
    """Mock tool executor for testing."""
    executor = MagicMock()
    executor.get_available_tools = Mock(
        return_value=[
            {"name": "nmap", "description": "Port scanner"},
            {"name": "nuclei", "description": "Vulnerability scanner"},
        ]
    )
    executor.execute = AsyncMock(return_value={"result": "success"})
    return executor


@pytest.fixture
def mock_memory_manager():
    """Mock memory manager for testing."""
    memory = MagicMock()
    memory.add_goal = AsyncMock()
    memory.add_experience = AsyncMock()
    memory.get_relevant_context = AsyncMock(return_value={"test": "context"})
    memory.search = AsyncMock(return_value=[])
    memory.get_findings = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def react_loop(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Create a ReActLoop instance for testing."""
    return ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=10,
    )


# ============================================================================
# Test Thought Dataclass
# ============================================================================


class TestThought:
    """Test Thought dataclass."""

    def test_thought_creation(self):
        """Test Thought creation."""
        thought = Thought(
            content="The target appears to have open ports 80 and 443",
            context={"target": "example.com"},
            step_number=1,
        )

        assert thought.content == "The target appears to have open ports 80 and 443"
        assert thought.context == {"target": "example.com"}
        assert thought.step_number == 1
        assert isinstance(thought.timestamp, datetime)

    def test_thought_defaults(self):
        """Test Thought with default values."""
        thought = Thought(content="Simple thought")

        assert thought.content == "Simple thought"
        assert thought.context == {}
        assert thought.step_number == 0

    def test_thought_to_dict(self):
        """Test Thought to_dict method."""
        thought = Thought(
            content="Test thought",
            context={"key": "value"},
            step_number=5,
        )

        result = thought.to_dict()

        assert result["type"] == "thought"
        assert result["content"] == "Test thought"
        assert result["context"] == {"key": "value"}
        assert result["step"] == 5
        assert "timestamp" in result


# ============================================================================
# Test Action Dataclass
# ============================================================================


class TestAction:
    """Test Action dataclass."""

    def test_action_creation(self):
        """Test Action creation."""
        action = Action(
            type=ActionType.TOOL_CALL,
            tool_name="nmap",
            parameters={"target": "example.com"},
            reasoning="Need to scan for open ports",
            step_number=2,
        )

        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nmap"
        assert action.parameters == {"target": "example.com"}
        assert action.reasoning == "Need to scan for open ports"
        assert action.step_number == 2

    def test_action_defaults(self):
        """Test Action with default values."""
        action = Action(type=ActionType.THINK)

        assert action.type == ActionType.THINK
        assert action.tool_name is None
        assert action.parameters == {}
        assert action.reasoning == ""
        assert action.step_number == 0

    def test_action_to_dict(self):
        """Test Action to_dict method."""
        action = Action(
            type=ActionType.TOOL_CALL,
            tool_name="nuclei",
            parameters={"target": "test.com"},
            reasoning="Scan for vulnerabilities",
            step_number=3,
        )

        result = action.to_dict()

        assert result["type"] == "action"
        assert result["action_type"] == "TOOL_CALL"
        assert result["tool"] == "nuclei"
        assert result["parameters"] == {"target": "test.com"}
        assert result["reasoning"] == "Scan for vulnerabilities"
        assert result["step"] == 3

    def test_all_action_types(self):
        """Test all ActionType enum values."""
        types = [
            ActionType.THINK,
            ActionType.TOOL_CALL,
            ActionType.SEARCH_MEMORY,
            ActionType.ASK_HUMAN,
            ActionType.REPORT,
            ActionType.TERMINATE,
        ]

        for action_type in types:
            action = Action(type=action_type)
            assert action.type == action_type


# ============================================================================
# Test Observation Dataclass
# ============================================================================


class TestObservation:
    """Test Observation dataclass."""

    def test_observation_creation(self):
        """Test Observation creation."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap")
        observation = Observation(
            action=action,
            result={"open_ports": [80, 443]},
            success=True,
            step_number=2,
        )

        assert observation.action == action
        assert observation.result == {"open_ports": [80, 443]}
        assert observation.success is True
        assert observation.error_message is None
        assert observation.step_number == 2

    def test_observation_failure(self):
        """Test Observation with failure."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap")
        observation = Observation(
            action=action,
            result=None,
            success=False,
            error_message="Connection timeout",
            step_number=3,
        )

        assert observation.success is False
        assert observation.error_message == "Connection timeout"

    def test_observation_to_dict(self):
        """Test Observation to_dict method."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap")
        observation = Observation(
            action=action,
            result={"data": "test"},
            success=True,
            step_number=4,
        )

        result = observation.to_dict()

        assert result["type"] == "observation"
        assert result["action"]["tool"] == "nmap"
        assert result["result"] == {"data": "test"}
        assert result["success"] is True
        assert result["step"] == 4


# ============================================================================
# Test ReActLoop Initialization
# ============================================================================


class TestReActLoopInitialization:
    """Test ReActLoop initialization."""

    def test_initialization(self, mock_llm_client, mock_tool_executor, mock_memory_manager):
        """Test ReActLoop initialization."""
        loop = ReActLoop(
            llm_client=mock_llm_client,
            tool_executor=mock_tool_executor,
            memory_manager=mock_memory_manager,
            max_iterations=50,
            human_in_the_loop=True,
        )

        assert loop.llm == mock_llm_client
        assert loop.tools == mock_tool_executor
        assert loop.memory == mock_memory_manager
        assert loop.max_iterations == 50
        assert loop.human_in_the_loop is True
        assert loop.history == []
        assert loop.current_step == 0
        assert loop.goal is None

    def test_default_initialization(self):
        """Test ReActLoop with defaults."""
        loop = ReActLoop(
            llm_client=MagicMock(),
            tool_executor=MagicMock(),
            memory_manager=MagicMock(),
        )

        assert loop.max_iterations == 50
        assert loop.human_in_the_loop is False


# ============================================================================
# Test ReActLoop Run Method
# ============================================================================


class TestReActLoopRun:
    """Test ReActLoop main run method."""

    @pytest.mark.asyncio
    async def test_run_single_iteration(self, react_loop, mock_llm_client, mock_tool_executor):
        """Test run with single iteration and termination."""
        # Mock LLM to return termination action
        mock_llm_client.generate = AsyncMock(return_value='{"action_type": "TERMINATE", "reasoning": "Done"}')

        result = await react_loop.run(goal="Test goal")

        assert result["goal"] == "Test goal"
        assert result["completed"] is True
        assert result["steps_taken"] == 1
        assert len(result["history"]) == 3  # Thought + Action + Observation

    @pytest.mark.asyncio
    async def test_run_max_iterations(self, react_loop, mock_llm_client):
        """Test run hitting max iterations."""
        react_loop.max_iterations = 3

        # Always return tool call action
        mock_llm_client.generate = AsyncMock(
            return_value="""
        {"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}, "reasoning": "Scan"}
        """
        )

        result = await react_loop.run(goal="Test goal")

        assert result["steps_taken"] == 3
        assert result["completed"] is False  # Hit max iterations

    @pytest.mark.asyncio
    async def test_run_with_context(self, react_loop, mock_memory_manager):
        """Test run with additional context."""
        mock_llm_client = react_loop.llm
        mock_llm_client.generate = AsyncMock(return_value='{"action_type": "TERMINATE"}')

        context = {"target": "example.com", "scope": "limited"}
        result = await react_loop.run(goal="Test goal", context=context)

        # Memory should be initialized with goal and context
        mock_memory_manager.add_goal.assert_called_once_with("Test goal", context)
        assert result["goal"] == "Test goal"

    @pytest.mark.asyncio
    async def test_run_history_tracking(self, react_loop, mock_llm_client, mock_tool_executor):
        """Test that history is properly tracked."""
        # First call for reasoning, second for action decision
        mock_llm_client.generate = AsyncMock(return_value='{"action_type": "TERMINATE"}')

        await react_loop.run(goal="Test")

        # Should have thought, action, and observation in history
        assert len(react_loop.history) == 3
        assert react_loop.history[0]["type"] == "thought"
        assert react_loop.history[1]["type"] == "action"
        assert react_loop.history[2]["type"] == "observation"


# ============================================================================
# Test Reasoning
# ============================================================================


class TestReasoning:
    """Test the _reason method."""

    @pytest.mark.asyncio
    async def test_reason_generates_thought(self, react_loop, mock_llm_client, mock_memory_manager):
        """Test that _reason generates a Thought."""
        mock_llm_client.generate = AsyncMock(return_value="I should scan the target for vulnerabilities")
        react_loop.goal = "Find vulnerabilities"
        react_loop.current_step = 1

        thought = await react_loop._reason()

        assert isinstance(thought, Thought)
        assert thought.content == "I should scan the target for vulnerabilities"
        assert thought.step_number == 1
        assert thought.context["goal"] == "Find vulnerabilities"

        # LLM should be called with context
        mock_llm_client.generate.assert_called_once()
        call_args = mock_llm_client.generate.call_args[0][0]
        assert "Find vulnerabilities" in call_args

    @pytest.mark.asyncio
    async def test_reason_includes_history(self, react_loop, mock_llm_client):
        """Test that reasoning includes history."""
        react_loop.history = [
            {"type": "thought", "content": "Previous thought"},
            {"type": "action", "action_type": "TOOL_CALL"},
        ]
        react_loop.goal = "Test"
        react_loop.current_step = 2

        mock_llm_client.generate = AsyncMock(return_value="Next thought")

        await react_loop._reason()

        # Prompt should include history
        call_args = mock_llm_client.generate.call_args[0][0]
        assert "Execution History" in call_args
        assert "Previous thought" in call_args


# ============================================================================
# Test Action Decision
# ============================================================================


class TestActionDecision:
    """Test the _decide_action method."""

    @pytest.mark.asyncio
    async def test_decide_tool_call(self, react_loop, mock_llm_client):
        """Test deciding on a tool call action."""
        mock_llm_client.generate = AsyncMock(
            return_value="""
        {
            "action_type": "TOOL_CALL",
            "tool_name": "nmap",
            "parameters": {"target": "example.com", "ports": "80,443"},
            "reasoning": "Need to scan for open ports"
        }
        """
        )

        thought = Thought(content="I need to scan ports")
        react_loop.current_step = 1

        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nmap"
        assert action.parameters == {"target": "example.com", "ports": "80,443"}
        assert action.reasoning == "Need to scan for open ports"
        assert action.step_number == 1

    @pytest.mark.asyncio
    async def test_decide_search_memory(self, react_loop, mock_llm_client):
        """Test deciding to search memory."""
        mock_llm_client.generate = AsyncMock(
            return_value="""
        {"action_type": "SEARCH_MEMORY", "parameters": {"query": "previous scans"}}
        """
        )

        thought = Thought(content="Let me check what I found before")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.SEARCH_MEMORY

    @pytest.mark.asyncio
    async def test_decide_report(self, react_loop, mock_llm_client):
        """Test deciding to report."""
        mock_llm_client.generate = AsyncMock(
            return_value="""
        {"action_type": "REPORT", "reasoning": "I have findings to report"}
        """
        )

        thought = Thought(content="Found vulnerabilities")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.REPORT

    @pytest.mark.asyncio
    async def test_decide_terminate(self, react_loop, mock_llm_client):
        """Test deciding to terminate."""
        mock_llm_client.generate = AsyncMock(
            return_value="""
        {"action_type": "TERMINATE", "reasoning": "Goal achieved"}
        """
        )

        thought = Thought(content="All done")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.TERMINATE

    @pytest.mark.asyncio
    async def test_decide_action_json_extraction(self, react_loop, mock_llm_client):
        """Test JSON extraction from LLM response."""
        # LLM returns JSON embedded in text
        mock_llm_client.generate = AsyncMock(
            return_value="""
        Based on my analysis, I should run a tool. Here's my decision:
        {"action_type": "TOOL_CALL", "tool_name": "nuclei", "parameters": {}, "reasoning": "Test"}
        This should find vulnerabilities.
        """
        )

        thought = Thought(content="Test")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nuclei"

    @pytest.mark.asyncio
    async def test_decide_action_invalid_json(self, react_loop, mock_llm_client):
        """Test handling invalid JSON from LLM."""
        mock_llm_client.generate = AsyncMock(return_value="Not valid JSON")

        thought = Thought(content="Test")
        action = await react_loop._decide_action(thought)

        # Should fallback to THINK action
        assert action.type == ActionType.THINK
        assert "Failed to parse" in action.reasoning

    @pytest.mark.asyncio
    async def test_decide_action_missing_action_type(self, react_loop, mock_llm_client):
        """Test handling JSON with invalid action type."""
        mock_llm_client.generate = AsyncMock(return_value='{"action_type": "INVALID_TYPE"}')

        thought = Thought(content="Test")
        action = await react_loop._decide_action(thought)

        # Should fallback to THINK
        assert action.type == ActionType.THINK


# ============================================================================
# Test Action Execution
# ============================================================================


class TestActionExecution:
    """Test the _execute_action method."""

    @pytest.mark.asyncio
    async def test_execute_tool_call(self, react_loop, mock_tool_executor):
        """Test executing a tool call action."""
        action = Action(
            type=ActionType.TOOL_CALL,
            tool_name="nmap",
            parameters={"target": "example.com"},
        )
        react_loop.current_step = 1

        observation = await react_loop._execute_action(action)

        assert isinstance(observation, Observation)
        assert observation.action == action
        assert observation.success is True
        assert observation.result == {"result": "success"}

        mock_tool_executor.execute.assert_called_once_with("nmap", {"target": "example.com"})

    @pytest.mark.asyncio
    async def test_execute_search_memory(self, react_loop, mock_memory_manager):
        """Test executing a search memory action."""
        action = Action(
            type=ActionType.SEARCH_MEMORY,
            parameters={"query": "vulnerabilities"},
        )
        mock_memory_manager.search = AsyncMock(return_value=[{"content": "Found SQLi"}])

        observation = await react_loop._execute_action(action)

        assert observation.success is True
        assert observation.result == [{"content": "Found SQLi"}]
        mock_memory_manager.search.assert_called_once_with("vulnerabilities")

    @pytest.mark.asyncio
    async def test_execute_report(self, react_loop, mock_memory_manager):
        """Test executing a report action."""
        action = Action(type=ActionType.REPORT)
        mock_memory_manager.get_findings = AsyncMock(return_value=[{"type": "sqli"}])

        observation = await react_loop._execute_action(action)

        assert observation.success is True
        assert observation.result["findings"] == [{"type": "sqli"}]
        assert observation.result["ready"] is True

    @pytest.mark.asyncio
    async def test_execute_think(self, react_loop):
        """Test executing a think action (no tool)."""
        action = Action(type=ActionType.THINK)

        observation = await react_loop._execute_action(action)

        assert observation.success is True
        assert observation.result is None

    @pytest.mark.asyncio
    async def test_execute_tool_error(self, react_loop, mock_tool_executor):
        """Test handling tool execution error."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap")
        mock_tool_executor.execute = AsyncMock(side_effect=Exception("Tool failed"))

        observation = await react_loop._execute_action(action)

        assert observation.success is False
        assert "Tool failed" in observation.error_message


# ============================================================================
# Test Human Approval
# ============================================================================


class TestHumanApproval:
    """Test the _human_approval method."""

    @pytest.mark.asyncio
    async def test_human_approval_auto_approve(self, react_loop):
        """Test that human approval auto-approves in test environment."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap")

        approved = await react_loop._human_approval(action)

        assert approved is True


# ============================================================================
# Test Result Compilation
# ============================================================================


class TestResultCompilation:
    """Test the _compile_result method."""

    def test_compile_result_basic(self, react_loop):
        """Test basic result compilation."""
        react_loop.goal = "Test goal"
        react_loop.current_step = 5
        react_loop.history = [
            {"type": "thought", "content": "Think"},
            {"type": "action", "action_type": "TOOL_CALL"},
            {"type": "observation", "result": "found port 80"},
        ]

        result = react_loop._compile_result()

        assert result["goal"] == "Test goal"
        assert result["completed"] is True
        assert result["steps_taken"] == 5
        assert result["execution_trace"] == "Completed in 5 steps"
        assert len(result["findings"]) == 1  # Only observations count as findings

    def test_compile_result_max_iterations(self, react_loop):
        """Test result when max iterations reached."""
        react_loop.goal = "Test"
        react_loop.current_step = 10
        react_loop.max_iterations = 10

        result = react_loop._compile_result()

        assert result["completed"] is False


# ============================================================================
# Test ActionType Enum
# ============================================================================


class TestActionTypeEnum:
    """Test ActionType enum."""

    def test_all_action_types(self):
        """Test all action types exist."""
        types = list(ActionType)

        assert ActionType.THINK in types
        assert ActionType.TOOL_CALL in types
        assert ActionType.SEARCH_MEMORY in types
        assert ActionType.ASK_HUMAN in types
        assert ActionType.REPORT in types
        assert ActionType.TERMINATE in types

    def test_action_type_names(self):
        """Test action type names."""
        assert ActionType.THINK.name == "THINK"
        assert ActionType.TOOL_CALL.name == "TOOL_CALL"
        assert ActionType.TERMINATE.name == "TERMINATE"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for ReActLoop."""

    @pytest.mark.asyncio
    async def test_full_cycle_tool_call(self):
        """Test full cycle with tool call."""
        llm = MagicMock()
        tools = MagicMock()
        memory = MagicMock()

        # First reasoning
        # Then decide to call tool
        # Then terminate
        llm.generate = AsyncMock(
            side_effect=[
                "I should scan the target",
                '{"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {"target": "test.com"}, "reasoning": "Scan"}',
                "I have the results",
                '{"action_type": "TERMINATE", "reasoning": "Done"}',
            ]
        )

        tools.get_available_tools = Mock(return_value=[{"name": "nmap"}])
        tools.execute = AsyncMock(return_value={"ports": [80]})

        memory.add_goal = AsyncMock()
        memory.add_experience = AsyncMock()
        memory.get_relevant_context = AsyncMock(return_value={})

        loop = ReActLoop(llm, tools, memory, max_iterations=10)
        result = await loop.run(goal="Scan target", context={"target": "test.com"})

        assert result["goal"] == "Scan target"
        assert result["steps_taken"] == 2
        assert len(result["history"]) == 6  # 2 cycles * 3 items

    @pytest.mark.asyncio
    async def test_memory_integration(self, react_loop, mock_memory_manager):
        """Test memory is updated throughout execution."""
        react_loop.llm.generate = AsyncMock(return_value='{"action_type": "TERMINATE"}')

        await react_loop.run(goal="Test")

        # Memory should be updated
        mock_memory_manager.add_experience.assert_called()
        # At least called once for each iteration
        assert mock_memory_manager.add_experience.call_count >= 1


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_goal(self, react_loop):
        """Test with empty goal."""
        react_loop.llm.generate = AsyncMock(return_value='{"action_type": "TERMINATE"}')

        result = await react_loop.run(goal="")

        assert result["goal"] == ""

    @pytest.mark.asyncio
    async def test_tool_not_specified(self, react_loop):
        """Test tool call without tool name."""
        action = Action(type=ActionType.TOOL_CALL)  # No tool_name

        observation = await react_loop._execute_action(action)

        assert observation.success is True  # Executes but no tool called

    @pytest.mark.asyncio
    async def test_consecutive_tool_calls(self, react_loop, mock_llm_client, mock_tool_executor):
        """Test multiple consecutive tool calls."""
        mock_llm_client.generate = AsyncMock(
            side_effect=[
                "First thought",
                '{"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}}',
                "Second thought",
                '{"action_type": "TOOL_CALL", "tool_name": "nuclei", "parameters": {}}',
                "Third thought",
                '{"action_type": "TERMINATE"}',
            ]
        )

        result = await react_loop.run(goal="Test")

        assert result["steps_taken"] == 3
        assert mock_tool_executor.execute.call_count == 2
