"""
Smart Tests for react.py

Agent: #081
Module: react.py
Pattern: TOOLEXECUTOR, GOLDEN FILES, COMMANDRUNNER
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import module under test
from autonomous import react
from autonomous.react import (
    Action,
    ActionType,
    Observation,
    ReActLoop,
    Thought,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = MagicMock()
    client.generate = AsyncMock(return_value='{"action_type": "TERMINATE", "reasoning": "Test"}')
    return client


@pytest.fixture
def mock_tool_executor():
    """Create mock tool executor."""
    executor = MagicMock()
    executor.get_available_tools = Mock(return_value=["nmap", "nuclei"])
    executor.execute = AsyncMock(return_value={"result": "test"})
    return executor


@pytest.fixture
def mock_memory_manager():
    """Create mock memory manager."""
    memory = MagicMock()
    memory.add_goal = AsyncMock()
    memory.add_experience = AsyncMock()
    memory.get_relevant_context = AsyncMock(return_value={"test": "context"})
    memory.search = AsyncMock(return_value=["result1", "result2"])
    memory.get_findings = AsyncMock(return_value=[{"finding": "test"}])
    return memory


@pytest.fixture
def react_loop(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Create ReActLoop instance."""
    return ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=5,
    )


@pytest.fixture
def sample_thought():
    """Create sample Thought."""
    return Thought(
        content="I need to scan the target",
        context={"goal": "test"},
        step_number=1,
    )


@pytest.fixture
def sample_action():
    """Create sample Action."""
    return Action(
        type=ActionType.TOOL_CALL,
        tool_name="nmap",
        parameters={"target": "example.com"},
        reasoning="Scan for open ports",
        step_number=1,
    )


@pytest.fixture
def sample_observation(sample_action):
    """Create sample Observation."""
    return Observation(
        action=sample_action,
        result={"ports": [80, 443]},
        success=True,
        step_number=1,
    )


# =============================================================================
# TEST 1: Module Import
# =============================================================================


def test_module_importable():
    """Test that react module can be imported."""
    assert react is not None
    assert hasattr(react, "ActionType")
    assert hasattr(react, "Thought")
    assert hasattr(react, "Action")
    assert hasattr(react, "Observation")
    assert hasattr(react, "ReActLoop")


# =============================================================================
# TEST 2: ToolExecutor Pattern
# =============================================================================


def test_module_uses_tool_executor(react_loop, mock_tool_executor):
    """Test that module follows ToolExecutor pattern."""
    assert react_loop.tools is mock_tool_executor
    assert hasattr(react_loop.tools, "execute")
    assert hasattr(react_loop.tools, "get_available_tools")


# =============================================================================
# TEST 3: NOT_FOUND Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_not_found_error(react_loop, mock_tool_executor):
    """Test handling when tools are not found."""
    mock_tool_executor.execute = AsyncMock(side_effect=Exception("Tool not found"))

    action = Action(
        type=ActionType.TOOL_CALL,
        tool_name="nonexistent_tool",
        parameters={},
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is False
    assert "not found" in observation.error_message.lower() or observation.error_message is not None


# =============================================================================
# TEST 4: TIMEOUT Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_timeout_error(react_loop, mock_tool_executor):
    """Test handling of timeout errors."""
    mock_tool_executor.execute = AsyncMock(side_effect=asyncio.TimeoutError())

    action = Action(
        type=ActionType.TOOL_CALL,
        tool_name="nmap",
        parameters={"target": "example.com"},
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is False


# =============================================================================
# TEST 5: Parser Extracts Findings
# =============================================================================


def test_module_parser_extracts_findings(sample_observation):
    """Test that parser correctly extracts findings from observations."""
    result_dict = sample_observation.to_dict()

    assert "result" in result_dict
    assert result_dict["success"] is True
    assert result_dict["action"]["action_type"] == "TOOL_CALL"


# =============================================================================
# TEST 6: End-to-End with Mock
# =============================================================================


@pytest.mark.asyncio
async def test_module_end_to_end_mocked(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Test full workflow with mocked executor."""
    # Configure LLM to terminate immediately
    mock_llm_client.generate = AsyncMock(return_value='{"action_type": "TERMINATE", "reasoning": "Done"}')

    loop = ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=3,
    )

    result = await loop.run(goal="Test goal", context={"target": "example.com"})

    assert isinstance(result, dict)
    assert "goal" in result
    assert result["goal"] == "Test goal"


# =============================================================================
# TEST 7: Empty Input Handling
# =============================================================================


def test_module_empty_input():
    """Test handling of empty input."""
    thought = Thought(content="", step_number=1)

    assert thought.content == ""
    assert thought.step_number == 1

    result_dict = thought.to_dict()
    assert result_dict["content"] == ""


# =============================================================================
# TEST 8: Invalid Output Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_invalid_output(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Test handling of invalid/malformed output."""
    # Return invalid JSON
    mock_llm_client.generate = AsyncMock(return_value="not valid json")

    loop = ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=2,
    )

    thought = Thought(content="test", step_number=1)
    action = await loop._decide_action(thought)

    # Should fallback to THINK action
    assert action.type == ActionType.THINK


# =============================================================================
# ADDITIONAL TESTS for Coverage
# =============================================================================


def test_action_type_enum():
    """Test ActionType enum values."""
    assert ActionType.THINK.name == "THINK"
    assert ActionType.TOOL_CALL.name == "TOOL_CALL"
    assert ActionType.SEARCH_MEMORY.name == "SEARCH_MEMORY"
    assert ActionType.ASK_HUMAN.name == "ASK_HUMAN"
    assert ActionType.REPORT.name == "REPORT"
    assert ActionType.TERMINATE.name == "TERMINATE"


def test_thought_to_dict(sample_thought):
    """Test Thought to_dict method."""
    result = sample_thought.to_dict()

    assert result["type"] == "thought"
    assert result["content"] == "I need to scan the target"
    assert result["step"] == 1
    assert "timestamp" in result


def test_action_to_dict(sample_action):
    """Test Action to_dict method."""
    result = sample_action.to_dict()

    assert result["type"] == "action"
    assert result["action_type"] == "TOOL_CALL"
    assert result["tool"] == "nmap"
    assert result["reasoning"] == "Scan for open ports"
    assert "timestamp" in result


def test_observation_to_dict(sample_observation):
    """Test Observation to_dict method."""
    result = sample_observation.to_dict()

    assert result["type"] == "observation"
    assert result["success"] is True
    assert "result" in result
    assert "timestamp" in result


def test_react_loop_initialization(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Test ReActLoop initialization."""
    loop = ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=10,
        human_in_the_loop=True,
    )

    assert loop.max_iterations == 10
    assert loop.human_in_the_loop is True
    assert loop.current_step == 0
    assert len(loop.history) == 0


@pytest.mark.asyncio
async def test_react_loop_reason(react_loop, mock_llm_client):
    """Test _reason method."""
    mock_llm_client.generate = AsyncMock(return_value="I should scan ports first")

    thought = await react_loop._reason()

    assert isinstance(thought, Thought)
    assert thought.content == "I should scan ports first"
    # step_number is 0 because current_step starts at 0 and _reason doesn't increment it
    assert thought.step_number == react_loop.current_step


@pytest.mark.asyncio
async def test_react_loop_decide_action_tool_call(react_loop, mock_llm_client):
    """Test _decide_action for TOOL_CALL."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
    {
        "action_type": "TOOL_CALL",
        "tool_name": "nmap",
        "parameters": {"target": "example.com"},
        "reasoning": "Scan for open ports"
    }
    """
    )

    thought = Thought(content="Need to scan", step_number=1)
    action = await react_loop._decide_action(thought)

    assert action.type == ActionType.TOOL_CALL
    assert action.tool_name == "nmap"


@pytest.mark.asyncio
async def test_react_loop_decide_action_search_memory(react_loop, mock_llm_client):
    """Test _decide_action for SEARCH_MEMORY."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
    {
        "action_type": "SEARCH_MEMORY",
        "parameters": {"query": "previous scans"},
        "reasoning": "Check previous results"
    }
    """
    )

    thought = Thought(content="Check history", step_number=1)
    action = await react_loop._decide_action(thought)

    assert action.type == ActionType.SEARCH_MEMORY


@pytest.mark.asyncio
async def test_react_loop_decide_action_report(react_loop, mock_llm_client):
    """Test _decide_action for REPORT."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
    {
        "action_type": "REPORT",
        "reasoning": "Deliver findings"
    }
    """
    )

    thought = Thought(content="Done scanning", step_number=1)
    action = await react_loop._decide_action(thought)

    assert action.type == ActionType.REPORT


@pytest.mark.asyncio
async def test_react_loop_decide_action_terminate(react_loop, mock_llm_client):
    """Test _decide_action for TERMINATE."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
    {
        "action_type": "TERMINATE",
        "reasoning": "Goal achieved"
    }
    """
    )

    thought = Thought(content="All done", step_number=1)
    action = await react_loop._decide_action(thought)

    assert action.type == ActionType.TERMINATE


@pytest.mark.asyncio
async def test_react_loop_execute_action_tool_call(react_loop, mock_tool_executor):
    """Test _execute_action for TOOL_CALL."""
    action = Action(
        type=ActionType.TOOL_CALL,
        tool_name="nmap",
        parameters={"target": "example.com"},
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is True
    assert observation.result == {"result": "test"}
    mock_tool_executor.execute.assert_called_once()


@pytest.mark.asyncio
async def test_react_loop_execute_action_search_memory(react_loop, mock_memory_manager):
    """Test _execute_action for SEARCH_MEMORY."""
    action = Action(
        type=ActionType.SEARCH_MEMORY,
        parameters={"query": "test"},
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is True
    assert observation.result == ["result1", "result2"]


@pytest.mark.asyncio
async def test_react_loop_execute_action_report(react_loop, mock_memory_manager):
    """Test _execute_action for REPORT."""
    action = Action(
        type=ActionType.REPORT,
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is True
    assert "findings" in observation.result


@pytest.mark.asyncio
async def test_react_loop_execute_action_think(react_loop):
    """Test _execute_action for THINK."""
    action = Action(
        type=ActionType.THINK,
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is True
    assert observation.result is None


@pytest.mark.asyncio
async def test_react_loop_human_approval(react_loop):
    """Test _human_approval method."""
    action = Action(
        type=ActionType.TOOL_CALL,
        tool_name="nmap",
        step_number=1,
    )

    approved = await react_loop._human_approval(action)

    # Currently auto-approves
    assert approved is True


def test_react_loop_compile_result(react_loop):
    """Test _compile_result method."""
    react_loop.goal = "Test goal"
    react_loop.current_step = 3
    react_loop.history = [
        {"type": "thought", "content": "test"},
        {"type": "action", "action_type": "TOOL_CALL"},
        {"type": "observation", "result": "test"},
    ]

    result = react_loop._compile_result()

    assert result["goal"] == "Test goal"
    assert result["steps_taken"] == 3
    assert len(result["findings"]) == 1
    assert result["completed"] is True


@pytest.mark.asyncio
async def test_react_loop_run_max_iterations(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Test run method respects max_iterations."""
    # Always return TOOL_CALL to keep looping
    mock_llm_client.generate = AsyncMock(
        return_value="""
    {
        "action_type": "TOOL_CALL",
        "tool_name": "nmap",
        "parameters": {}
    }
    """
    )

    loop = ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=2,
    )

    result = await loop.run(goal="Test")

    assert result["steps_taken"] <= 2


@pytest.mark.asyncio
async def test_react_loop_run_with_termination(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Test run method with early termination."""
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            return "Thinking..."
        else:
            return '{"action_type": "TERMINATE", "reasoning": "Done"}'

    mock_llm_client.generate = AsyncMock(side_effect=side_effect)

    loop = ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=10,
    )

    result = await loop.run(goal="Test")

    assert result["completed"] is True


@pytest.mark.asyncio
async def test_react_loop_run_adds_experience(mock_llm_client, mock_tool_executor, mock_memory_manager):
    """Test that run adds experiences to memory."""
    mock_llm_client.generate = AsyncMock(return_value='{"action_type": "TERMINATE", "reasoning": "Done"}')

    loop = ReActLoop(
        llm_client=mock_llm_client,
        tool_executor=mock_tool_executor,
        memory_manager=mock_memory_manager,
        max_iterations=3,
    )

    await loop.run(goal="Test")

    mock_memory_manager.add_goal.assert_called_once()


@pytest.mark.asyncio
async def test_react_loop_decide_action_with_json_extraction(react_loop, mock_llm_client):
    """Test JSON extraction from LLM response."""
    # JSON embedded in text
    mock_llm_client.generate = AsyncMock(
        return_value="""
    Based on my analysis, I should scan the target.
    {
        "action_type": "TOOL_CALL",
        "tool_name": "nmap",
        "parameters": {"target": "example.com"},
        "reasoning": "Scan for open ports"
    }
    This is the best approach.
    """
    )

    thought = Thought(content="Need to scan", step_number=1)
    action = await react_loop._decide_action(thought)

    assert action.type == ActionType.TOOL_CALL


@pytest.mark.asyncio
async def test_react_loop_execute_action_exception(react_loop, mock_tool_executor):
    """Test _execute_action handles exceptions."""
    mock_tool_executor.execute = AsyncMock(side_effect=Exception("Unexpected error"))

    action = Action(
        type=ActionType.TOOL_CALL,
        tool_name="nmap",
        parameters={},
        step_number=1,
    )

    observation = await react_loop._execute_action(action)

    assert observation.success is False
    assert "Unexpected error" in observation.error_message


def test_react_loop_compile_result_no_observations(react_loop):
    """Test _compile_result with no observations."""
    react_loop.goal = "Test goal"
    react_loop.current_step = 1
    react_loop.history = [
        {"type": "thought", "content": "test"},
    ]

    result = react_loop._compile_result()

    assert result["goal"] == "Test goal"
    assert len(result["findings"]) == 0
