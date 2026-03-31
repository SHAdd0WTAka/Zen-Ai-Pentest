"""Basic tests for autonomous module"""

import pytest


class TestMemory:
    """Test memory module"""

    def test_memory_import(self):
        from autonomous.memory import LongTermMemory

        assert LongTermMemory is not None

    def test_memory_entry_import(self):
        from autonomous.memory import MemoryEntry

        assert MemoryEntry is not None

    def test_memory_entry_creation(self):
        from autonomous.memory import MemoryEntry

        entry = MemoryEntry(id="1", content="Test", memory_type="action")
        assert entry.id == "1"
        assert entry.content == "Test"
        assert entry.memory_type == "action"


class TestAgentLoop:
    """Test agent loop"""

    def test_agent_loop_import(self):
        from autonomous.agent_loop import AutonomousAgentLoop

        assert AutonomousAgentLoop is not None


class TestExploitValidator:
    """Test exploit validator"""

    def test_exploit_validator_import(self):
        from autonomous.exploit_validator import ExploitValidator

        assert ExploitValidator is not None


class TestSubdomainEnum:
    """Test subdomain enumeration"""

    def test_subdomain_enum_import(self):
        from autonomous.subdomain_enum import SubdomainEnumerator

        assert SubdomainEnumerator is not None
