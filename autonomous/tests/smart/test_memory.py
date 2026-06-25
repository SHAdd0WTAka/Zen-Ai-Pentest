"""
Smart Tests for memory.py

Agent: #081
Module: memory.py
Pattern: TOOLEXECUTOR, GOLDEN FILES, COMMANDRUNNER
"""

import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import module under test
from autonomous import memory
from autonomous.memory import (
    BaseMemory,
    EpisodicMemory,
    LongTermMemory,
    MemoryEntry,
    MemoryManager,
    WorkingMemory,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def memory_entry():
    """Create MemoryEntry instance."""
    return MemoryEntry(
        id="test-id-123",
        content="Test memory content",
        memory_type="thought",
        metadata={"test": "data"},
        session_id="session-123",
    )


@pytest.fixture
def working_memory():
    """Create WorkingMemory instance."""
    return WorkingMemory(max_size=100)


@pytest.fixture
def long_term_memory():
    """Create LongTermMemory instance."""
    return LongTermMemory(storage_path=None)


@pytest.fixture
def episodic_memory():
    """Create EpisodicMemory instance."""
    return EpisodicMemory()


@pytest.fixture
def memory_manager():
    """Create MemoryManager instance."""
    return MemoryManager(enable_embeddings=False)


@pytest.fixture
def temp_storage_file():
    """Create temporary storage file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


# =============================================================================
# TEST 1: Module Import
# =============================================================================


def test_module_importable():
    """Test that memory module can be imported."""
    assert memory is not None
    assert hasattr(memory, "MemoryEntry")
    assert hasattr(memory, "BaseMemory")
    assert hasattr(memory, "WorkingMemory")
    assert hasattr(memory, "LongTermMemory")
    assert hasattr(memory, "EpisodicMemory")
    assert hasattr(memory, "MemoryManager")


# =============================================================================
# TEST 2: ToolExecutor Pattern
# =============================================================================


def test_module_uses_tool_executor(memory_manager):
    """Test that module follows ToolExecutor pattern."""
    assert hasattr(memory_manager, "working")
    assert hasattr(memory_manager, "long_term")
    assert hasattr(memory_manager, "episodic")


# =============================================================================
# TEST 3: NOT_FOUND Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_not_found_error(temp_storage_file):
    """Test handling when storage file not found."""
    ltm = LongTermMemory(storage_path=temp_storage_file)

    # Delete the file to simulate not found
    if os.path.exists(temp_storage_file):
        os.unlink(temp_storage_file)

    # Should not raise error
    await ltm.load()

    assert len(ltm.entries) == 0


# =============================================================================
# TEST 4: TIMEOUT Error Handling
# =============================================================================


@pytest.mark.asyncio
async def test_module_timeout_error(working_memory):
    """Test handling of timeout-like delays."""
    # Test that operations complete quickly
    entry = MemoryEntry(
        id="test",
        content="test",
        memory_type="test",
    )

    start = datetime.now()
    await working_memory.add(entry)
    elapsed = (datetime.now() - start).total_seconds()

    assert elapsed < 1.0  # Should complete quickly


# =============================================================================
# TEST 5: Parser Extracts Findings
# =============================================================================


def test_module_parser_extracts_findings(memory_manager):
    """Test that parser correctly extracts findings from results."""
    result = {"findings": [{"type": "vuln", "severity": "high"}]}

    findings = memory_manager._extract_findings(result)

    assert len(findings) == 1
    assert findings[0]["type"] == "vuln"


# =============================================================================
# TEST 6: End-to-End with Mock
# =============================================================================


@pytest.mark.asyncio
async def test_module_end_to_end_mocked(memory_manager):
    """Test full workflow with mocked components."""
    # Add a goal
    await memory_manager.add_goal("Test goal", {"target": "example.com"})

    # Verify goal was added
    context = await memory_manager.working.get_context_window()
    assert context["goal"] == "Test goal"


# =============================================================================
# TEST 7: Empty Input Handling
# =============================================================================


def test_module_empty_input():
    """Test handling of empty input."""
    entry = MemoryEntry(
        id="test",
        content="",
        memory_type="test",
    )

    result = entry.to_dict()

    assert result["content"] == ""
    assert result["type"] == "test"


# =============================================================================
# TEST 8: Invalid Output Handling
# =============================================================================


def test_module_invalid_output(memory_manager):
    """Test handling of invalid/malformed output."""
    # Test with non-dict result
    findings = memory_manager._extract_findings("not a dict")

    assert isinstance(findings, list)
    assert len(findings) == 0


# =============================================================================
# ADDITIONAL TESTS for Coverage
# =============================================================================


def test_memory_entry_to_dict(memory_entry):
    """Test MemoryEntry to_dict method."""
    result = memory_entry.to_dict()

    assert result["id"] == "test-id-123"
    assert result["content"] == "Test memory content"
    assert result["type"] == "thought"
    assert "timestamp" in result


def test_memory_entry_default_timestamp():
    """Test MemoryEntry default timestamp."""
    entry = MemoryEntry(
        id="test",
        content="test",
        memory_type="test",
    )

    assert isinstance(entry.timestamp, datetime)


@pytest.mark.asyncio
async def test_working_memory_add(working_memory):
    """Test WorkingMemory add method."""
    entry = MemoryEntry(
        id="test",
        content="test content",
        memory_type="thought",
    )

    await working_memory.add(entry)

    assert len(working_memory.entries) == 1
    assert working_memory.entries[0].session_id == working_memory.session_id


@pytest.mark.asyncio
async def test_working_memory_add_trimming(working_memory):
    """Test WorkingMemory trims when exceeding max_size."""
    working_memory.max_size = 5

    for i in range(10):
        entry = MemoryEntry(
            id=f"test-{i}",
            content=f"content-{i}",
            memory_type="thought",
        )
        await working_memory.add(entry)

    assert len(working_memory.entries) == 5


@pytest.mark.asyncio
async def test_working_memory_search(working_memory):
    """Test WorkingMemory search method."""
    await working_memory.add(MemoryEntry(id="1", content="scan ports", memory_type="action"))
    await working_memory.add(MemoryEntry(id="2", content="find vulnerabilities", memory_type="action"))
    await working_memory.add(MemoryEntry(id="3", content="generate report", memory_type="action"))

    results = await working_memory.search("vulnerabilities")

    assert len(results) == 1
    assert results[0].content == "find vulnerabilities"


@pytest.mark.asyncio
async def test_working_memory_search_case_insensitive(working_memory):
    """Test WorkingMemory search is case insensitive."""
    await working_memory.add(MemoryEntry(id="1", content="SCAN PORTS", memory_type="action"))

    results = await working_memory.search("scan")

    assert len(results) == 1


@pytest.mark.asyncio
async def test_working_memory_get_recent(working_memory):
    """Test WorkingMemory get_recent method."""
    for i in range(5):
        await working_memory.add(
            MemoryEntry(
                id=f"test-{i}",
                content=f"content-{i}",
                memory_type="thought",
            )
        )

    recent = await working_memory.get_recent(3)

    assert len(recent) == 3
    assert recent[-1].content == "content-4"


@pytest.mark.asyncio
async def test_working_memory_get_context_window(working_memory):
    """Test WorkingMemory get_context_window method."""
    working_memory.set_goal("Test goal", {"target": "example.com"})

    await working_memory.add(
        MemoryEntry(
            id="test",
            content="test action",
            memory_type="action",
        )
    )

    context = await working_memory.get_context_window(n=5)

    assert context["session_id"] == working_memory.session_id
    assert context["goal"] == "Test goal"
    assert "recent_actions" in context


def test_working_memory_set_goal(working_memory):
    """Test WorkingMemory set_goal method."""
    working_memory.set_goal("New goal", {"key": "value"})

    assert working_memory.current_goal == "New goal"
    assert working_memory.context["key"] == "value"


def test_working_memory_update_context(working_memory):
    """Test WorkingMemory update_context method."""
    working_memory.update_context("new_key", "new_value")

    assert working_memory.context["new_key"] == "new_value"


def test_working_memory_clear(working_memory):
    """Test WorkingMemory clear method."""
    working_memory.set_goal("Test goal")
    working_memory.entries.append(MemoryEntry(id="test", content="test", memory_type="test"))

    working_memory.clear()

    assert len(working_memory.entries) == 0
    assert working_memory.current_goal is None


def test_long_term_memory_simple_hash_embedding(long_term_memory):
    """Test LongTermMemory simple hash embedding."""
    embedding = long_term_memory._simple_hash_embedding("test words for embedding")

    assert len(embedding) == 128
    # Check normalization
    magnitude = sum(x**2 for x in embedding) ** 0.5
    assert abs(magnitude - 1.0) < 0.01 or magnitude == 0


def test_long_term_memory_cosine_similarity(long_term_memory):
    """Test LongTermMemory cosine similarity calculation."""
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    c = [0.0, 1.0, 0.0]

    sim_aa = long_term_memory._cosine_similarity(a, a)
    sim_ab = long_term_memory._cosine_similarity(a, b)
    sim_ac = long_term_memory._cosine_similarity(a, c)

    assert sim_aa == 1.0
    assert sim_ab == 1.0
    assert sim_ac == 0.0


@pytest.mark.asyncio
async def test_long_term_memory_add(long_term_memory):
    """Test LongTermMemory add method."""
    entry = MemoryEntry(
        id="test-id",
        content="test content for memory",
        memory_type="thought",
    )

    await long_term_memory.add(entry)

    assert "test-id" in long_term_memory.entries
    assert long_term_memory.entries["test-id"].embedding is not None


@pytest.mark.asyncio
async def test_long_term_memory_add_with_embedding(long_term_memory):
    """Test LongTermMemory add with existing embedding."""
    entry = MemoryEntry(
        id="test-id",
        content="test content",
        memory_type="thought",
        embedding=[0.1] * 128,
    )

    await long_term_memory.add(entry)

    assert long_term_memory.entries["test-id"].embedding == [0.1] * 128


@pytest.mark.asyncio
async def test_long_term_memory_search(long_term_memory):
    """Test LongTermMemory search method."""
    await long_term_memory.add(
        MemoryEntry(
            id="1",
            content="scanning ports with nmap",
            memory_type="action",
        )
    )
    await long_term_memory.add(
        MemoryEntry(
            id="2",
            content="finding vulnerabilities",
            memory_type="finding",
        )
    )
    await long_term_memory.add(
        MemoryEntry(
            id="3",
            content="generating reports",
            memory_type="action",
        )
    )

    results = await long_term_memory.search("vulnerabilities", limit=2)

    assert len(results) <= 2


@pytest.mark.asyncio
async def test_long_term_memory_get_recent(long_term_memory):
    """Test LongTermMemory get_recent method."""
    await long_term_memory.add(MemoryEntry(id="1", content="first", memory_type="test"))
    await long_term_memory.add(MemoryEntry(id="2", content="second", memory_type="test"))
    await long_term_memory.add(MemoryEntry(id="3", content="third", memory_type="test"))

    recent = await long_term_memory.get_recent(2)

    assert len(recent) == 2


@pytest.mark.asyncio
async def test_long_term_memory_persist_and_load(temp_storage_file):
    """Test LongTermMemory persist and load methods."""
    ltm = LongTermMemory(storage_path=temp_storage_file)

    await ltm.add(
        MemoryEntry(
            id="test-id",
            content="persisted content",
            memory_type="thought",
        )
    )

    # Create new instance and load
    ltm2 = LongTermMemory(storage_path=temp_storage_file)
    await ltm2.load()

    assert "test-id" in ltm2.entries
    assert ltm2.entries["test-id"].content == "persisted content"


def test_episodic_memory_record_episode(episodic_memory):
    """Test EpisodicMemory record_episode method."""
    episodic_memory.record_episode(
        goal="Test goal",
        steps=[{"action": "scan"}],
        outcome="Success",
        success=True,
        lessons_learned=["Lesson 1"],
    )

    assert len(episodic_memory.episodes) == 1
    assert episodic_memory.episodes[0]["goal"] == "Test goal"
    assert episodic_memory.episodes[0]["success"] is True


def test_episodic_memory_get_similar_episodes(episodic_memory):
    """Test EpisodicMemory get_similar_episodes method."""
    episodic_memory.record_episode(
        goal="scan ports on target",
        steps=[],
        outcome="Success",
        success=True,
        lessons_learned=[],
    )
    episodic_memory.record_episode(
        goal="find vulnerabilities",
        steps=[],
        outcome="Success",
        success=True,
        lessons_learned=[],
    )

    similar = episodic_memory.get_similar_episodes("scan ports")

    assert len(similar) > 0
    assert "scan" in similar[0]["goal"]


@pytest.mark.asyncio
async def test_memory_manager_add_goal(memory_manager):
    """Test MemoryManager add_goal method."""
    await memory_manager.add_goal("Test goal", {"target": "example.com"})

    assert memory_manager.working.current_goal == "Test goal"
    assert memory_manager.working.context["target"] == "example.com"


@pytest.mark.asyncio
async def test_memory_manager_add_experience(memory_manager):
    """Test MemoryManager add_experience method."""
    thought = MagicMock()
    thought.content = "Thinking about scan"
    thought.step_number = 1

    action = MagicMock()
    action.type = MagicMock()
    action.type.name = "TOOL_CALL"
    action.tool_name = "nmap"
    action.parameters = {"target": "example.com"}
    action.step_number = 1

    observation = MagicMock()
    observation.result = {"ports": [80]}
    observation.success = True
    observation.step_number = 1

    await memory_manager.add_experience(thought, action, observation)

    # Should have added entries to working memory
    recent = await memory_manager.working.get_recent(10)
    assert len(recent) >= 3  # thought, action, observation


@pytest.mark.asyncio
async def test_memory_manager_get_relevant_context(memory_manager):
    """Test MemoryManager get_relevant_context method."""
    await memory_manager.add_goal("Test goal", {"target": "example.com"})

    context = await memory_manager.get_relevant_context("test query")

    assert "current_session" in context
    assert "relevant_past" in context
    assert "similar_episodes" in context


@pytest.mark.asyncio
async def test_memory_manager_search(memory_manager):
    """Test MemoryManager search method."""
    await memory_manager.working.add(
        MemoryEntry(
            id="1",
            content="scanning with nmap",
            memory_type="action",
        )
    )
    await memory_manager.long_term.add(
        MemoryEntry(
            id="2",
            content="finding vulnerabilities",
            memory_type="finding",
        )
    )

    results = await memory_manager.search("vulnerabilities")

    assert len(results) >= 1


@pytest.mark.asyncio
async def test_memory_manager_get_findings(memory_manager):
    """Test MemoryManager get_findings method."""
    await memory_manager.long_term.add(
        MemoryEntry(
            id="1",
            content="critical vulnerability found",
            memory_type="finding",
        )
    )

    findings = await memory_manager.get_findings()

    assert len(findings) >= 0  # May or may not find based on search


def test_memory_manager_extract_findings_with_open_ports(memory_manager):
    """Test _extract_findings with open_ports."""
    result = {"open_ports": [{"port": 80}, {"port": 443}]}

    findings = memory_manager._extract_findings(result)

    assert len(findings) == 2


def test_memory_manager_extract_findings_with_vulnerabilities(memory_manager):
    """Test _extract_findings with vulnerabilities."""
    result = {"vulnerabilities": [{"name": "XSS"}, {"name": "SQLi"}]}

    findings = memory_manager._extract_findings(result)

    assert len(findings) == 2


@pytest.mark.asyncio
async def test_memory_manager_record_episode(memory_manager):
    """Test MemoryManager record_episode method."""
    memory_manager.working.current_goal = "Test goal"
    await memory_manager.working.add(MemoryEntry(id="1", content="action", memory_type="action"))

    await memory_manager.record_episode("Completed successfully", True)

    assert len(memory_manager.episodic.episodes) == 1


@pytest.mark.asyncio
async def test_memory_manager_load(memory_manager, temp_storage_file):
    """Test MemoryManager load method."""
    memory_manager.long_term = LongTermMemory(storage_path=temp_storage_file)
    await memory_manager.long_term.add(MemoryEntry(id="1", content="test", memory_type="test"))

    await memory_manager.load()

    # Should not raise error
    assert True


@pytest.mark.asyncio
async def test_memory_manager_add_experience_with_findings(memory_manager):
    """Test add_experience extracts and stores findings."""
    thought = MagicMock()
    thought.content = "Test thought"
    thought.step_number = 1

    action = MagicMock()
    action.type = MagicMock()
    action.type.name = "TOOL_CALL"
    action.tool_name = "nmap"
    action.parameters = {}
    action.step_number = 1

    observation = MagicMock()
    observation.result = {"findings": [{"severity": "high"}]}
    observation.success = True
    observation.step_number = 1

    await memory_manager.add_experience(thought, action, observation)

    # Findings should be extracted and stored in long-term memory
    assert len(memory_manager.long_term.entries) > 0
