"""
Pytest Configuration for Autonomous Module Tests

Agent: #074
Module: All autonomous modules
Pattern: TOOLEXECUTOR, GOLDEN FILES, COMMANDRUNNER
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_tool_executor():
    """Create a mock ToolExecutor for testing."""
    executor = MagicMock()
    executor.execute = AsyncMock(
        return_value=MagicMock(
            success=True,
            return_code=0,
            stdout="Mock output",
            stderr="",
            duration=1.0,
            findings=[],
            parsed_output={},
        )
    )
    executor.get_available_tools = MagicMock(
        return_value=[
            {
                "name": "nmap",
                "description": "Network scanner",
                "category": "recon",
            },
            {
                "name": "nuclei",
                "description": "Vulnerability scanner",
                "category": "web",
            },
        ]
    )
    return executor


@pytest.fixture
def mock_memory_manager():
    """Create a mock MemoryManager for testing."""
    memory = MagicMock()
    memory.store = AsyncMock(return_value=True)
    memory.retrieve = AsyncMock(return_value=[])
    memory.search = AsyncMock(return_value=[])
    return memory


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    client = MagicMock()
    client.generate = AsyncMock(return_value="Mock LLM response")
    client.chat = AsyncMock(return_value={"content": "Mock chat response"})
    return client
