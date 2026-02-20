"""
Tests for ReAct Reasoning Loop
"""

from unittest.mock import AsyncMock, Mock

import pytest

from autonomous.memory import MemoryManager
from autonomous.react import Action, ActionType, Observation, ReActLoop, Thought
from autonomous.tool_executor import ToolExecutor


@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    llm = Mock()
    llm.generate = AsyncMock(return_value="Test reasoning")
    return llm


@pytest.fixture
def mock_tool_executor():
    """Mock tool executor."""
    executor = Mock(spec=ToolExecutor)
    executor.get_available_tools = Mock(return_value=[{"name": "nmap", "description": "Port scanner"}])
    executor.execute = AsyncMock(return_value={"stdout": "PORT   STATE SERVICE\n80/tcp open  http", "success": True})
    return executor


@pytest.fixture
def mock_memory():
    """Mock memory manager."""
    memory = Mock(spec=MemoryManager)
    memory.add_goal = AsyncMock()
    memory.add_experience = AsyncMock()
    memory.get_relevant_context = AsyncMock(return_value={})
    return memory


@pytest.fixture
def react_loop(mock_llm, mock_tool_executor, mock_memory):
    """Create ReAct loop instance."""
    return ReActLoop(llm_client=mock_llm, tool_executor=mock_tool_executor, memory_manager=mock_memory, max_iterations=5)


class TestReActLoop:
    """Test ReAct reasoning loop."""

    @pytest.mark.asyncio
    async def test_run_completes_successfully(self, react_loop, mock_llm):
        """Test that run completes when goal is achieved."""
        # Setup mock to return terminate action after one iteration
        mock_llm.generate.side_effect = [
            "I need to scan the target",
            '{"action_type": "TERMINATE", "reasoning": "Task complete"}',
        ]

        result = await react_loop.run(goal="Scan target")

        assert result["goal"] == "Scan target"
        assert "completed" in result
        assert "steps_taken" in result

    @pytest.mark.asyncio
    async def test_reason_generates_thought(self, react_loop, mock_llm):
        """Test reasoning step."""
        mock_llm.generate.return_value = "I should use nmap to scan ports"

        thought = await react_loop._reason()

        assert isinstance(thought, Thought)
        assert thought.content == "I should use nmap to scan ports"
        assert thought.step_number >= 0  # Step number starts at 0

    @pytest.mark.asyncio
    async def test_decide_action_parses_json(self, react_loop, mock_llm):
        """Test action decision parsing."""
        mock_llm.generate.return_value = """
        {
            "action_type": "TOOL_CALL",
            "tool_name": "nmap",
            "parameters": {"target": "192.168.1.1"},
            "reasoning": "Scan target ports"
        }
        """

        thought = Thought(content="Need to scan")
        action = await react_loop._decide_action(thought)

        assert isinstance(action, Action)
        assert action.type == ActionType.TOOL_CALL
        assert action.tool_name == "nmap"
        assert action.parameters == {"target": "192.168.1.1"}

    @pytest.mark.asyncio
    async def test_execute_tool_call(self, react_loop, mock_tool_executor):
        """Test tool execution."""
        action = Action(type=ActionType.TOOL_CALL, tool_name="nmap", parameters={"target": "192.168.1.1"}, step_number=1)

        observation = await react_loop._execute_action(action)

        assert isinstance(observation, Observation)
        assert observation.success is True
        mock_tool_executor.execute.assert_called_once_with("nmap", {"target": "192.168.1.1"})

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, react_loop, mock_llm):
        """Test that loop respects max iterations."""
        # Mock to never terminate
        mock_llm.generate.side_effect = [
            "Reasoning",
            '{"action_type": "TOOL_CALL", "tool_name": "nmap", "parameters": {}}',
        ] * 10

        result = await react_loop.run(goal="Test")

        assert result["steps_taken"] <= react_loop.max_iterations


class TestActionTypes:
    """Test different action types."""

    def test_action_type_enum(self):
        """Test action type enumeration."""
        assert ActionType.TOOL_CALL.name == "TOOL_CALL"
        assert ActionType.TERMINATE.name == "TERMINATE"
        assert ActionType.THINK.name == "THINK"


class TestThought:
    """Test Thought dataclass."""

    def test_thought_to_dict(self):
        """Test thought serialization."""
        thought = Thought(content="Test thought", context={"key": "value"}, step_number=1)

        d = thought.to_dict()

        assert d["type"] == "thought"
        assert d["content"] == "Test thought"
        assert d["context"] == {"key": "value"}
        assert d["step"] == 1


class TestAction:
    """Test Action dataclass."""

    def test_action_to_dict(self):
        """Test action serialization."""
        action = Action(
            type=ActionType.TOOL_CALL, tool_name="nmap", parameters={"target": "test"}, reasoning="Scan target", step_number=2
        )

        d = action.to_dict()

        assert d["type"] == "action"
        assert d["action_type"] == "TOOL_CALL"
        assert d["tool"] == "nmap"


class TestObservation:
    """Test Observation dataclass."""

    def test_observation_to_dict(self):
        """Test observation serialization."""
        action = Action(type=ActionType.TOOL_CALL, step_number=1)
        observation = Observation(action=action, result={"ports": [80, 443]}, success=True, step_number=1)

        d = observation.to_dict()

        assert d["type"] == "observation"
        assert d["success"] is True
        assert d["result"] == {"ports": [80, 443]}


# Integration tests
@pytest.mark.integration
class TestReActIntegration:
    """Integration tests requiring full setup."""

    @pytest.mark.asyncio
    async def test_full_react_cycle(self):
        """Test complete ReAct cycle with real components."""
        # This would require a real LLM backend
        pass
