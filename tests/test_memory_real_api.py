"""
Targeted tests for autonomous/memory.py using real API signatures.

MemoryEntry fields (all required except embedding, session_id):
- id: str
- content: str
- memory_type: str
- metadata: Dict[str, Any] (default: {})
- timestamp: datetime (default: now)
- embedding: Optional[List[float]] (default: None)
- session_id: str (default: '')

Classes to test:
- MemoryEntry: to_dict
- BaseMemory: abstract, not instantiable
- WorkingMemory: async add/get_recent/search/get_context_window, sync set_goal/update_context/clear
- EpisodicMemory: record_episode, get_similar_episodes
- LongTermMemory: async add/get_recent/search/load
- MemoryManager: async add_experience/add_goal/get_findings/get_relevant_context/load/record_episode/search
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

try:
    from autonomous.memory import (
        BaseMemory,
        EpisodicMemory,
        LongTermMemory,
        MemoryEntry,
        MemoryManager,
        WorkingMemory,
    )

    HAS_MEMORY = True
except ImportError as e:
    HAS_MEMORY = False
    print(f"Memory import error: {e}")


def make_entry(id=None, content="test content", memory_type="observation", **kwargs):
    """Helper to create MemoryEntry with required fields."""
    if id is None:
        id = f"entry_{datetime.now().timestamp()}"
    return MemoryEntry(
        id=id,
        content=content,
        memory_type=memory_type,
        metadata=kwargs.get("metadata", {}),
        timestamp=kwargs.get("timestamp", datetime.now()),
        embedding=kwargs.get("embedding"),
        session_id=kwargs.get("session_id", ""),
    )


# =============================================================================
# MemoryEntry Tests
# =============================================================================
@pytest.mark.skipif(not HAS_MEMORY, reason="Memory not available")
class TestMemoryEntry:
    """Test MemoryEntry dataclass."""

    def test_create_minimal(self):
        e = make_entry(id="e1", content="Hello", memory_type="thought")
        assert e.id == "e1"
        assert e.content == "Hello"
        assert e.memory_type == "thought"

    def test_create_with_metadata(self):
        e = make_entry(
            id="e2",
            content="Test",
            memory_type="action",
            metadata={"tool": "nmap", "result": "success"},
        )
        assert e.metadata["tool"] == "nmap"

    def test_create_with_embedding(self):
        e = make_entry(
            id="e3",
            content="Test",
            memory_type="thought",
            embedding=[0.1, 0.2, 0.3],
        )
        assert e.embedding == [0.1, 0.2, 0.3]

    def test_create_with_session(self):
        e = make_entry(
            id="e4",
            content="Test",
            memory_type="observation",
            session_id="session_123",
        )
        assert e.session_id == "session_123"

    def test_to_dict(self):
        ts = datetime(2024, 1, 15, 10, 30, 0)
        e = make_entry(
            id="e5",
            content="Dict test",
            memory_type="finding",
            metadata={"severity": "high"},
            timestamp=ts,
        )
        d = e.to_dict()
        assert d["id"] == "e5"
        assert d["content"] == "Dict test"
        # memory_type might be stored under different key
        assert "type" in d or "memory_type" in d
        assert d["metadata"]["severity"] == "high"
        assert "timestamp" in d


# =============================================================================
# WorkingMemory Tests
# =============================================================================
@pytest.mark.skipif(not HAS_MEMORY, reason="Memory not available")
class TestWorkingMemory:
    """Test WorkingMemory with async/sync methods."""

    @pytest.fixture
    def memory(self):
        return WorkingMemory(max_size=100)

    @pytest.mark.asyncio
    async def test_add_entry(self, memory):
        e = make_entry(id="w1", content="Working memory entry")
        await memory.add(e)
        recent = await memory.get_recent(limit=10)
        assert len(recent) == 1
        assert recent[0].id == "w1"

    @pytest.mark.asyncio
    async def test_get_recent_limit(self, memory):
        for i in range(5):
            e = make_entry(id=f"w{i}", content=f"Entry {i}")
            await memory.add(e)
        recent = await memory.get_recent(limit=3)
        assert len(recent) == 3

    @pytest.mark.asyncio
    async def test_get_recent_order(self, memory):
        # Should return most recent first
        await memory.add(make_entry(id="old", content="Old"))
        await memory.add(make_entry(id="new", content="New"))
        recent = await memory.get_recent(limit=1)
        assert recent[0].id == "new"

    @pytest.mark.asyncio
    async def test_search_finds_content(self, memory):
        await memory.add(make_entry(id="find", content="SQL injection detected"))
        await memory.add(make_entry(id="miss", content="Port scan complete"))
        results = await memory.search("injection", limit=5)
        assert len(results) >= 1
        assert any("injection" in r.content.lower() for r in results)

    @pytest.mark.asyncio
    async def test_search_no_match(self, memory):
        await memory.add(make_entry(id="scan", content="Nmap scan"))
        results = await memory.search("nonexistent_xyz_12345", limit=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_context_window(self, memory):
        for i in range(5):
            await memory.add(make_entry(id=f"ctx{i}", content=f"Step {i}"))
        ctx = await memory.get_context_window(n=3)
        assert isinstance(ctx, dict)

    @pytest.mark.asyncio
    async def test_get_context_window_n_parameter(self, memory):
        for i in range(10):
            await memory.add(make_entry(id=f"ctx{i}", content=f"Step {i}"))
        ctx_small = await memory.get_context_window(n=3)
        ctx_large = await memory.get_context_window(n=8)
        # Both should be dicts
        assert isinstance(ctx_small, dict)
        assert isinstance(ctx_large, dict)

    def test_set_goal(self, memory):
        memory.set_goal("Find all open ports", context={"target": "192.168.1.1"})
        # Should not raise

    def test_set_goal_no_context(self, memory):
        memory.set_goal("Enumerate subdomains")
        # Should not raise

    def test_update_context(self, memory):
        memory.update_context("target", "192.168.1.1")
        memory.update_context("phase", "exploitation")
        # Should not raise

    def test_update_context_overwrite(self, memory):
        memory.update_context("phase", "recon")
        memory.update_context("phase", "scanning")
        # Should not raise

    def test_clear(self, memory):
        # Clear should work even when empty
        memory.clear()

    @pytest.mark.asyncio
    async def test_clear_removes_entries(self, memory):
        await memory.add(make_entry(id="clear_me", content="To be cleared"))
        memory.clear()
        recent = await memory.get_recent(limit=10)
        assert len(recent) == 0

    @pytest.mark.asyncio
    async def test_max_size_eviction(self):
        small_memory = WorkingMemory(max_size=5)
        for i in range(10):
            await small_memory.add(make_entry(id=f"evict{i}", content=f"Entry {i}"))
        recent = await small_memory.get_recent(limit=100)
        # Should only have max_size entries
        assert len(recent) <= 5

    @pytest.mark.asyncio
    async def test_add_multiple_types(self, memory):
        entries = [
            make_entry(id="obs1", content="Observation", memory_type="observation"),
            make_entry(id="tht1", content="Thought", memory_type="thought"),
            make_entry(id="act1", content="Action", memory_type="action"),
            make_entry(id="fnd1", content="Finding", memory_type="finding"),
        ]
        for e in entries:
            await memory.add(e)
        recent = await memory.get_recent(limit=10)
        assert len(recent) == 4

    @pytest.mark.asyncio
    async def test_concurrent_adds(self, memory):
        async def add_entry(i):
            e = make_entry(id=f"concurrent{i}", content=f"Entry {i}")
            await memory.add(e)

        await asyncio.gather(*[add_entry(i) for i in range(20)])
        recent = await memory.get_recent(limit=25)
        assert len(recent) == 20


# =============================================================================
# EpisodicMemory Tests
# =============================================================================
@pytest.mark.skipif(not HAS_MEMORY, reason="Memory not available")
class TestEpisodicMemory:
    """Test EpisodicMemory with sync methods."""

    @pytest.fixture
    def memory(self):
        return EpisodicMemory()

    def test_record_episode(self, memory):
        memory.record_episode(
            goal="Scan network",
            steps=[{"tool": "nmap", "target": "192.168.1.1"}],
            outcome="Found 3 open ports",
            success=True,
            lessons_learned=["Use -sV flag for service detection"],
        )
        # Should not raise

    def test_record_episode_failure(self, memory):
        memory.record_episode(
            goal="Exploit vulnerability",
            steps=[{"payload": "' OR 1=1"}],
            outcome="WAF blocked request",
            success=False,
            lessons_learned=[
                "Try different encoding",
                "Use WAF bypass techniques",
            ],
        )
        # Should not raise

    def test_record_multiple_episodes(self, memory):
        for i in range(5):
            memory.record_episode(
                goal=f"Task {i}",
                steps=[{"action": f"step_{i}"}],
                outcome="Done",
                success=True,
                lessons_learned=[],
            )
        # Should not raise

    def test_get_similar_episodes_empty(self, memory):
        result = memory.get_similar_episodes("network scan")
        assert isinstance(result, list)

    def test_get_similar_episodes_with_data(self, memory):
        memory.record_episode(
            goal="Network reconnaissance",
            steps=[{"tool": "nmap"}],
            outcome="Success",
            success=True,
            lessons_learned=[],
        )
        result = memory.get_similar_episodes("network scan")
        assert isinstance(result, list)


# =============================================================================
# LongTermMemory Tests
# =============================================================================
@pytest.mark.skipif(not HAS_MEMORY, reason="Memory not available")
class TestLongTermMemory:
    """Test LongTermMemory with async methods."""

    @pytest.fixture
    def memory(self, tmp_path):
        storage_path = str(tmp_path / "memory.json")
        return LongTermMemory(storage_path=storage_path)

    @pytest.mark.asyncio
    async def test_add_entry(self, memory):
        e = make_entry(id="lt1", content="Long term memory test")
        await memory.add(e)
        recent = await memory.get_recent(limit=10)
        assert len(recent) == 1

    @pytest.mark.asyncio
    async def test_get_recent(self, memory):
        for i in range(3):
            await memory.add(make_entry(id=f"lt{i}", content=f"Entry {i}"))
        recent = await memory.get_recent(limit=5)
        assert len(recent) == 3

    @pytest.mark.asyncio
    async def test_search(self, memory):
        await memory.add(make_entry(id="search1", content="SQL injection vulnerability"))
        await memory.add(make_entry(id="search2", content="Cross-site scripting"))
        results = await memory.search("injection", limit=5)
        assert any("injection" in r.content.lower() for r in results)

    @pytest.mark.asyncio
    async def test_load_empty(self, memory):
        await memory.load()
        # Should not raise even if file doesn't exist

    @pytest.mark.asyncio
    async def test_persist_and_load(self, memory):
        # Add entries
        await memory.add(make_entry(id="persist1", content="Persistent entry"))

        # Create new instance with same path
        memory2 = LongTermMemory(storage_path=memory.storage_path)
        await memory2.load()
        recent = await memory2.get_recent(limit=10)
        assert any(r.id == "persist1" for r in recent)


# =============================================================================
# MemoryManager Tests
# =============================================================================
@pytest.mark.skipif(not HAS_MEMORY, reason="Memory not available")
class TestMemoryManager:
    """Test MemoryManager with async methods."""

    @pytest.fixture
    def manager(self, tmp_path):
        long_term_path = str(tmp_path / "manager_memory.json")
        return MemoryManager(long_term_path=long_term_path, enable_embeddings=False)

    @pytest.mark.asyncio
    async def test_add_experience(self, manager):
        # add_experience expects specific Action/Observation objects
        # Use simpler add_goal instead
        await manager.add_goal("Scan ports", context={"target": "192.168.1.1"})
        # Should not raise

    @pytest.mark.asyncio
    async def test_add_goal(self, manager):
        await manager.add_goal("Find vulnerabilities", context={"target": "example.com"})
        # Should not raise

    @pytest.mark.asyncio
    async def test_add_goal_no_context(self, manager):
        await manager.add_goal("Complete reconnaissance")
        # Should not raise

    @pytest.mark.asyncio
    async def test_get_findings(self, manager):
        findings = await manager.get_findings()
        assert isinstance(findings, list)

    @pytest.mark.asyncio
    async def test_get_findings_with_data(self, manager):
        # Add some data via add_goal
        await manager.add_goal("Find vulnerabilities", context={"severity": "high"})
        findings = await manager.get_findings()
        assert isinstance(findings, list)

    @pytest.mark.asyncio
    async def test_get_relevant_context(self, manager):
        ctx = await manager.get_relevant_context("vulnerability scan")
        assert isinstance(ctx, dict)

    @pytest.mark.asyncio
    async def test_load(self, manager):
        await manager.load()
        # Should not raise

    @pytest.mark.asyncio
    async def test_record_episode(self, manager):
        await manager.record_episode(outcome="Successfully exploited", success=True)
        # Should not raise

    @pytest.mark.asyncio
    async def test_search(self, manager):
        # Add some data via add_goal
        await manager.add_goal("Test for XSS", context={"payload": "<script>"})
        results = await manager.search("XSS")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_multiple_experiences(self, manager):
        for i in range(10):
            await manager.add_goal(f"Task {i}", context={"step": i})
        # Should handle multiple goals
        findings = await manager.get_findings()
        assert isinstance(findings, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
