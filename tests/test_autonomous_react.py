"""
Tests for autonomous/react.py - ReAct Pattern

Tests the ReactPattern class:
- ReActLoop initialization
- Reasoning step
- Action selection
- Reflection
- Execution flow
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from autonomous.react import (
    Action,
    ActionType,
    Observation,
    ReActLoop,
    Thought,
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
def mock_tools():
    """Mock tool executor for testing."""
    tools = MagicMock()
    tools.get_available_tools = Mock(
        return_value=[
            {"name": "nmap", "description": "Port scanner"},
            {"name": "nuclei", "description": "Vulnerability scanner"},
            {"name": "sqlmap", "description": "SQL injection scanner"},
        ]
    )
    tools.execute = AsyncMock(
        return_value={"result": "success", "data": "test"}
    )
    return tools


@pytest.fixture
def mock_memory():
    """Mock memory manager for testing."""
    memory = MagicMock()
    memory.add_goal = AsyncMock()
    memory.add_experience = AsyncMock()
    memory.get_relevant_context = AsyncMock(
        return_value={"goal": "test", "history": []}
    )
    memory.search = AsyncMock(return_value=[])
    memory.get_findings = AsyncMock(return_value=[{"type": "vuln"}])
    return memory


@pytest.fixture
def react_loop(mock_llm, mock_tools, mock_memory):
    """Create a ReActLoop instance for testing."""
    return ReActLoop(
        llm_client=mock_llm,
        tool_executor=mock_tools,
        memory_manager=mock_memory,
        max_iterations=10,
    )


# ============================================================================
# Test Thought Dataclass
# ============================================================================


class TestThought:
    """Test Thought dataclass."""

    def test_thought_creation(self):
        """Test Thought creation with all fields."""
        thought = Thought(
            content="The target has open ports 80 and 443",
            context={"target": "example.com", "ports_found": 2},
            step_number=1,
        )

        assert thought.content == "The target has open ports 80 and 443"
        assert thought.context == {"target": "example.com", "ports_found": 2}
        assert thought.step_number == 1
        assert isinstance(thought.timestamp, datetime)

    def test_thought_defaults(self):
        """Test Thought with default values."""
        thought = Thought(content="Simple thought")

        assert thought.content == "Simple thought"
        assert thought.context == {}
        assert thought.step_number == 0
        assert isinstance(thought.timestamp, datetime)

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
        """Test Action creation with all fields."""
        action = Action(
            type=ActionType.TOOL_CALL,
            tool_name="nmap",
            parameters={"target": "example.com", "ports": "80,443"},
            reasoning="Need to scan for open ports",
            step_number=2,
        )

        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nmap"
        assert action.parameters == {
            "target": "example.com",
            "ports": "80,443",
        }
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
        action_types = [
            ActionType.THINK,
            ActionType.TOOL_CALL,
            ActionType.SEARCH_MEMORY,
            ActionType.ASK_HUMAN,
            ActionType.REPORT,
            ActionType.TERMINATE,
        ]

        for action_type in action_types:
            action = Action(type=action_type)
            assert action.type == action_type


# ============================================================================
# Test Observation Dataclass
# ============================================================================


class TestObservation:
    """Test Observation dataclass."""

    def test_observation_creation_success(self):
        """Test successful Observation creation."""
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

    def test_observation_creation_failure(self):
        """Test failed Observation creation."""
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

    def test_default_initialization(self, mock_llm, mock_tools, mock_memory):
        """Test ReActLoop with default values."""
        loop = ReActLoop(
            llm_client=mock_llm,
            tool_executor=mock_tools,
            memory_manager=mock_memory,
        )

        assert loop.llm == mock_llm
        assert loop.tools == mock_tools
        assert loop.memory == mock_memory
        assert loop.max_iterations == 50
        assert loop.human_in_the_loop is False
        assert loop.history == []
        assert loop.current_step == 0
        assert loop.goal is None

    def test_custom_initialization(self, mock_llm, mock_tools, mock_memory):
        """Test ReActLoop with custom values."""
        loop = ReActLoop(
            llm_client=mock_llm,
            tool_executor=mock_tools,
            memory_manager=mock_memory,
            max_iterations=20,
            human_in_the_loop=True,
        )

        assert loop.max_iterations == 20
        assert loop.human_in_the_loop is True


# ============================================================================
# Test Reasoning Step
# ============================================================================


class TestReasoning:
    """Test the _reason method."""

    @pytest.mark.asyncio
    async def test_reason_generates_thought(self, react_loop, mock_memory):
        """Test that _reason generates a Thought."""
        react_loop.llm.generate = AsyncMock(
            return_value="I should scan the target"
        )
        react_loop.goal = "Find vulnerabilities"
        react_loop.current_step = 1

        thought = await react_loop._reason()

        assert isinstance(thought, Thought)
        assert thought.content == "I should scan the target"
        assert thought.step_number == 1
        assert thought.context["goal"] == "Find vulnerabilities"

    @pytest.mark.asyncio
    async def test_reason_includes_context(self, react_loop, mock_memory):
        """Test that reasoning includes context from memory."""
        react_loop.llm.generate = AsyncMock(return_value="Analysis")
        react_loop.goal = "Test goal"

        await react_loop._reason()

        # Should call memory for context
        mock_memory.get_relevant_context.assert_called_once_with("Test goal")

    @pytest.mark.asyncio
    async def test_reason_includes_history(self, react_loop):
        """Test that reasoning includes execution history."""
        react_loop.history = [
            {"type": "thought", "content": "Previous thought"},
            {"type": "action", "action_type": "TOOL_CALL"},
        ]
        react_loop.goal = "Test"
        react_loop.current_step = 2

        react_loop.llm.generate = AsyncMock(return_value="Next thought")

        await react_loop._reason()

        # Prompt should include history
        call_args = react_loop.llm.generate.call_args[0][0]
        assert "Execution History" in call_args
        assert "Previous thought" in call_args

    @pytest.mark.asyncio
    async def test_reason_prompt_contains_goal(self, react_loop):
        """Test that reasoning prompt contains the goal."""
        react_loop.goal = "Find all vulnerabilities"
        react_loop.llm.generate = AsyncMock(return_value="Thought")

        await react_loop._reason()

        prompt = react_loop.llm.generate.call_args[0][0]
        assert "Find all vulnerabilities" in prompt


# ============================================================================
# Test Action Selection
# ============================================================================


class TestActionSelection:
    """Test the _decide_action method."""

    @pytest.mark.asyncio
    async def test_decide_tool_call(self, react_loop):
        """Test deciding on a tool call action."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {
            "action_type": "TOOL_CALL",
            "tool_name": "nmap",
            "parameters": {"target": "example.com"},
            "reasoning": "Scan for open ports"
        }
        """
        )

        thought = Thought(content="I need to scan ports")
        react_loop.current_step = 1

        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nmap"
        assert action.parameters == {"target": "example.com"}
        assert action.reasoning == "Scan for open ports"

    @pytest.mark.asyncio
    async def test_decide_search_memory(self, react_loop):
        """Test deciding to search memory."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "SEARCH_MEMORY", "parameters": {"query": "previous scans"}}
        """
        )

        thought = Thought(content="Let me check what I found before")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.SEARCH_MEMORY

    @pytest.mark.asyncio
    async def test_decide_ask_human(self, react_loop):
        """Test deciding to ask human."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "ASK_HUMAN", "reasoning": "Need clarification"}
        """
        )

        thought = Thought(content="I'm unsure about this")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.ASK_HUMAN

    @pytest.mark.asyncio
    async def test_decide_report(self, react_loop):
        """Test deciding to report findings."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "REPORT", "reasoning": "I have findings"}
        """
        )

        thought = Thought(content="Found vulnerabilities")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.REPORT

    @pytest.mark.asyncio
    async def test_decide_terminate(self, react_loop):
        """Test deciding to terminate."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "TERMINATE", "reasoning": "Goal achieved"}
        """
        )

        thought = Thought(content="All done")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.TERMINATE

    @pytest.mark.asyncio
    async def test_decide_think(self, react_loop):
        """Test deciding to think."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "THINK", "reasoning": "Need more analysis"}
        """
        )

        thought = Thought(content="Analyzing")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.THINK

    @pytest.mark.asyncio
    async def test_decide_action_includes_tools_list(self, react_loop):
        """Test that action decision includes available tools."""
        react_loop.llm.generate = AsyncMock(
            return_value='{"action_type": "TERMINATE"}'
        )
        thought = Thought(content="Test")

        await react_loop._decide_action(thought)

        prompt = react_loop.llm.generate.call_args[0][0]
        assert "nmap" in prompt
        assert "nuclei" in prompt

    @pytest.mark.asyncio
    async def test_decide_action_json_extraction(self, react_loop):
        """Test JSON extraction from embedded response."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        Based on my analysis, I should run a scan:
        {"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}, "reasoning": "Test"}
        This will help find vulnerabilities.
        """
        )

        thought = Thought(content="Test")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nmap"

    @pytest.mark.asyncio
    async def test_decide_action_invalid_json_fallback(self, react_loop):
        """Test fallback to THINK on invalid JSON."""
        react_loop.llm.generate = AsyncMock(return_value="Not valid JSON")

        thought = Thought(content="Test")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.THINK
        assert "Failed to parse" in action.reasoning

    @pytest.mark.asyncio
    async def test_decide_action_invalid_action_type_fallback(
        self, react_loop
    ):
        """Test fallback to THINK on invalid action type."""
        react_loop.llm.generate = AsyncMock(
            return_value='{"action_type": "INVALID_TYPE"}'
        )

        thought = Thought(content="Test")
        action = await react_loop._decide_action(thought)

        assert action.type == ActionType.THINK


# ============================================================================
# Test Action Execution
# ============================================================================


class TestActionExecution:
    """Test the _execute_action method."""

    @pytest.mark.asyncio
    async def test_execute_tool_call(self, react_loop, mock_tools):
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
        assert observation.result == {"result": "success", "data": "test"}
        mock_tools.execute.assert_called_once_with(
            "nmap", {"target": "example.com"}
        )

    @pytest.mark.asyncio
    async def test_execute_search_memory(self, react_loop, mock_memory):
        """Test executing a search memory action."""
        action = Action(
            type=ActionType.SEARCH_MEMORY,
            parameters={"query": "vulnerabilities"},
        )
        mock_memory.search = AsyncMock(
            return_value=[{"content": "Found SQLi"}]
        )

        observation = await react_loop._execute_action(action)

        assert observation.success is True
        assert observation.result == [{"content": "Found SQLi"}]
        mock_memory.search.assert_called_once_with("vulnerabilities")

    @pytest.mark.asyncio
    async def test_execute_report(self, react_loop, mock_memory):
        """Test executing a report action."""
        action = Action(type=ActionType.REPORT)
        mock_memory.get_findings = AsyncMock(return_value=[{"type": "sqli"}])

        observation = await react_loop._execute_action(action)

        assert observation.success is True
        assert observation.result["findings"] == [{"type": "sqli"}]
        assert observation.result["ready"] is True

    @pytest.mark.asyncio
    async def test_execute_think(self, react_loop):
        """Test executing a think action (no-op)."""
        action = Action(type=ActionType.THINK)

        observation = await react_loop._execute_action(action)

        assert observation.success is True
        assert observation.result is None

    @pytest.mark.asyncio
    async def test_execute_ask_human(self, react_loop):
        """Test executing ask human action."""
        action = Action(type=ActionType.ASK_HUMAN)

        observation = await react_loop._execute_action(action)

        assert observation.success is True

    @pytest.mark.asyncio
    async def test_execute_terminate(self, react_loop):
        """Test executing terminate action."""
        action = Action(type=ActionType.TERMINATE)

        observation = await react_loop._execute_action(action)

        assert observation.success is True

    @pytest.mark.asyncio
    async def test_execute_tool_error(self, react_loop, mock_tools):
        """Test handling tool execution error."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap")
        mock_tools.execute = AsyncMock(side_effect=Exception("Tool failed"))

        observation = await react_loop._execute_action(action)

        assert observation.success is False
        assert "Tool failed" in observation.error_message

    @pytest.mark.asyncio
    async def test_execute_tool_without_name(self, react_loop):
        """Test tool call without tool name."""
        action = Action(type=ActionType.TOOL_CALL)  # No tool_name

        observation = await react_loop._execute_action(action)

        # Should succeed but not call any tool
        assert observation.success is True


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
# Test run() Method
# ============================================================================


class TestRunMethod:
    """Test the main run() method."""

    @pytest.mark.asyncio
    async def test_run_single_iteration_termination(self, react_loop):
        """Test run with single iteration and termination."""
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "TERMINATE", "reasoning": "Done"}
        """
        )

        result = await react_loop.run(goal="Test goal")

        assert result["goal"] == "Test goal"
        assert result["completed"] is True
        assert result["steps_taken"] == 1
        # TERMINATE action breaks before observation, so only 2 items
        assert len(result["history"]) == 2  # Thought + Action

    @pytest.mark.asyncio
    async def test_run_max_iterations(self, react_loop):
        """Test run hitting max iterations."""
        react_loop.max_iterations = 3
        react_loop.llm.generate = AsyncMock(
            return_value="""
        {"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}, "reasoning": "Scan"}
        """
        )

        result = await react_loop.run(goal="Test goal")

        assert result["steps_taken"] == 3
        assert result["completed"] is False  # Hit max iterations

    @pytest.mark.asyncio
    async def test_run_with_context(self, react_loop, mock_memory):
        """Test run with additional context."""
        react_loop.llm.generate = AsyncMock(
            return_value='{"action_type": "TERMINATE"}'
        )

        context = {"target": "example.com", "scope": "limited"}
        result = await react_loop.run(goal="Test goal", context=context)

        mock_memory.add_goal.assert_called_once_with("Test goal", context)
        assert result["goal"] == "Test goal"

    @pytest.mark.asyncio
    async def test_run_history_tracking(self, react_loop):
        """Test that history is properly tracked."""
        react_loop.llm.generate = AsyncMock(
            return_value='{"action_type": "TERMINATE"}'
        )

        await react_loop.run(goal="Test")

        # TERMINATE action breaks before observation, so only 2 items
        assert len(react_loop.history) == 2
        assert react_loop.history[0]["type"] == "thought"
        assert react_loop.history[1]["type"] == "action"

    @pytest.mark.asyncio
    async def test_run_memory_updated(self, react_loop, mock_memory):
        """Test that memory is updated during execution with TOOL_CALL."""
        react_loop.llm.generate = AsyncMock(
            side_effect=[
                "Thought 1",  # First call for _reason()
                '{"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}}',  # Second for _decide_action()
                "Thought 2",
                '{"action_type": "TERMINATE"}',
            ]
        )

        await react_loop.run(goal="Test")

        # Memory should be updated after tool execution
        mock_memory.add_experience.assert_called()


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
        assert len(result["findings"]) == 1

    def test_compile_result_max_iterations(self, react_loop):
        """Test result when max iterations reached."""
        react_loop.goal = "Test"
        react_loop.current_step = 10
        react_loop.max_iterations = 10
        react_loop.history = []

        result = react_loop._compile_result()

        assert result["completed"] is False


# ============================================================================
# Test Integration
# ============================================================================


class TestIntegration:
    """Integration tests for full ReAct cycle."""

    @pytest.mark.asyncio
    async def test_full_cycle_tool_call(self):
        """Test full cycle with tool call."""
        llm = MagicMock()
        tools = MagicMock()
        memory = MagicMock()

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
        result = await loop.run(
            goal="Scan target", context={"target": "test.com"}
        )

        assert result["goal"] == "Scan target"
        assert result["steps_taken"] == 2
        # Cycle 1: Thought+Action+Observation=3, Cycle 2: Thought+Action=2 (TERMINATE breaks)
        assert len(result["history"]) == 5

    @pytest.mark.asyncio
    async def test_human_in_the_loop(self):
        """Test human in the loop mode."""
        llm = MagicMock()
        tools = MagicMock()
        memory = MagicMock()

        llm.generate = AsyncMock(
            side_effect=[
                "I should scan",
                '{"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}}',
                "Done",
                '{"action_type": "TERMINATE"}',
            ]
        )

        tools.get_available_tools = Mock(return_value=[{"name": "nmap"}])
        tools.execute = AsyncMock(return_value={})
        memory.add_goal = AsyncMock()
        memory.add_experience = AsyncMock()
        memory.get_relevant_context = AsyncMock(return_value={})

        loop = ReActLoop(
            llm, tools, memory, max_iterations=5, human_in_the_loop=True
        )
        result = await loop.run(goal="Test")

        assert result["completed"] is True


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_goal(self, react_loop):
        """Test with empty goal."""
        react_loop.llm.generate = AsyncMock(
            return_value='{"action_type": "TERMINATE"}'
        )

        result = await react_loop.run(goal="")

        assert result["goal"] == ""

    @pytest.mark.asyncio
    async def test_none_context(self, react_loop):
        """Test with None context."""
        react_loop.llm.generate = AsyncMock(
            return_value='{"action_type": "TERMINATE"}'
        )

        result = await react_loop.run(goal="Test", context=None)

        assert result["goal"] == "Test"

    @pytest.mark.asyncio
    async def test_consecutive_tool_calls(self, react_loop):
        """Test multiple consecutive tool calls."""
        react_loop.llm.generate = AsyncMock(
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
