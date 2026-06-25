"""
Tests for autonomous/memory module - aligned with actual implementation
"""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestMemoryEntry:
    """Test MemoryEntry dataclass"""

    def test_memory_entry_creation(self):
        """Test creating a MemoryEntry"""
        from autonomous.memory import MemoryEntry

        entry = MemoryEntry(id="test-123", content="Test content", memory_type="thought", metadata={"key": "value"})

        assert entry.id == "test-123"
        assert entry.content == "Test content"
        assert entry.memory_type == "thought"
        assert entry.metadata == {"key": "value"}
        assert isinstance(entry.timestamp, datetime)

    def test_memory_entry_to_dict(self):
        """Test MemoryEntry serialization"""
        from autonomous.memory import MemoryEntry

        entry = MemoryEntry(id="test-123", content="Test", memory_type="action", session_id="session-456")

        data = entry.to_dict()

        assert data["id"] == "test-123"
        assert data["content"] == "Test"
        assert data["type"] == "action"
        assert data["session_id"] == "session-456"
        assert "timestamp" in data


class TestWorkingMemory:
    """Test WorkingMemory class"""

    @pytest.fixture
    def working_memory(self):
        """Create a WorkingMemory instance"""
        from autonomous.memory import WorkingMemory

        return WorkingMemory(max_size=10)

    @pytest.mark.asyncio
    async def test_working_memory_initialization(self, working_memory):
        """Test WorkingMemory initialization"""
        assert working_memory.max_size == 10
        assert working_memory.entries == []
        assert working_memory.current_goal is None
        assert working_memory.context == {}
        assert len(working_memory.session_id) == 36  # UUID

    @pytest.mark.asyncio
    async def test_add_entry(self, working_memory):
        """Test adding entry to working memory"""
        from autonomous.memory import MemoryEntry

        entry = MemoryEntry(id="test-1", content="Test action", memory_type="action")

        await working_memory.add(entry)

        assert len(working_memory.entries) == 1
        assert working_memory.entries[0].session_id == working_memory.session_id

    @pytest.mark.asyncio
    async def test_max_size_trimming(self, working_memory):
        """Test that memory trims when exceeding max size"""
        from autonomous.memory import MemoryEntry

        # Add more entries than max_size
        for i in range(15):
            entry = MemoryEntry(id=f"test-{i}", content=f"Content {i}", memory_type="action")
            await working_memory.add(entry)

        assert len(working_memory.entries) == 10
        # Should keep most recent
        assert working_memory.entries[-1].content == "Content 14"

    @pytest.mark.asyncio
    async def test_search_entries(self, working_memory):
        """Test searching entries"""
        from autonomous.memory import MemoryEntry

        await working_memory.add(MemoryEntry(id="1", content="Scanning ports with nmap", memory_type="action"))
        await working_memory.add(MemoryEntry(id="2", content="Found SQL injection vulnerability", memory_type="finding"))
        await working_memory.add(MemoryEntry(id="3", content="Directory enumeration complete", memory_type="action"))

        results = await working_memory.search("nmap", limit=5)

        assert len(results) == 1
        assert "nmap" in results[0].content.lower()

    @pytest.mark.asyncio
    async def test_get_recent(self, working_memory):
        """Test getting recent entries"""
        from autonomous.memory import MemoryEntry

        for i in range(5):
            await working_memory.add(MemoryEntry(id=f"{i}", content=f"Entry {i}", memory_type="action"))

        recent = await working_memory.get_recent(3)

        assert len(recent) == 3
        assert recent[-1].content == "Entry 4"

    @pytest.mark.asyncio
    async def test_get_context_window(self, working_memory):
        """Test getting context window"""
        from autonomous.memory import MemoryEntry

        working_memory.set_goal("Find vulnerabilities", {"target": "example.com"})
        await working_memory.add(MemoryEntry(id="1", content="Started scan", memory_type="action"))

        context = await working_memory.get_context_window(n=5)

        assert context["session_id"] == working_memory.session_id
        assert context["goal"] == "Find vulnerabilities"
        assert context["context"]["target"] == "example.com"
        assert len(context["recent_actions"]) == 1

    def test_set_goal(self, working_memory):
        """Test setting goal"""
        working_memory.set_goal("Test goal", {"key": "value"})

        assert working_memory.current_goal == "Test goal"
        assert working_memory.context["key"] == "value"

    def test_update_context(self, working_memory):
        """Test updating context"""
        working_memory.update_context("target", "example.com")
        working_memory.update_context("port", 443)

        assert working_memory.context["target"] == "example.com"
        assert working_memory.context["port"] == 443

    def test_clear(self, working_memory):
        """Test clearing memory"""
        working_memory.set_goal("Test")
        working_memory.update_context("key", "value")

        working_memory.clear()

        assert working_memory.entries == []
        assert working_memory.current_goal is None
        assert working_memory.context == {}


class TestLongTermMemory:
    """Test LongTermMemory class"""

    @pytest.fixture
    def ltm(self):
        """Create a LongTermMemory instance"""
        from autonomous.memory import LongTermMemory

        return LongTermMemory()

    @pytest.mark.asyncio
    async def test_add_with_embedding(self, ltm):
        """Test adding entry with auto-generated embedding"""
        from autonomous.memory import MemoryEntry

        entry = MemoryEntry(id="test-1", content="This is a test entry", memory_type="thought")

        await ltm.add(entry)

        assert entry.id in ltm.entries
        assert entry.embedding is not None
        assert len(entry.embedding) == 128

    @pytest.mark.asyncio
    async def test_semantic_search(self, ltm):
        """Test semantic search"""
        from autonomous.memory import MemoryEntry

        # Add entries
        await ltm.add(MemoryEntry(id="1", content="Port scanning with nmap tool", memory_type="action"))
        await ltm.add(MemoryEntry(id="2", content="SQL injection found in login form", memory_type="finding"))
        await ltm.add(MemoryEntry(id="3", content="Directory brute force enumeration", memory_type="action"))

        # Search
        results = await ltm.search("vulnerability security", limit=3)

        assert len(results) > 0
        # SQL injection should rank higher for "vulnerability"
        assert any("SQL" in r.content for r in results)

    @pytest.mark.asyncio
    async def test_get_recent_ltm(self, ltm):
        """Test getting recent from LTM"""
        from autonomous.memory import MemoryEntry

        for i in range(5):
            await ltm.add(MemoryEntry(id=f"{i}", content=f"Entry {i}", memory_type="action"))

        recent = await ltm.get_recent(3)

        assert len(recent) == 3

    def test_simple_hash_embedding(self, ltm):
        """Test embedding generation"""
        embedding1 = ltm._simple_hash_embedding("test text")
        embedding2 = ltm._simple_hash_embedding("test text")

        assert len(embedding1) == 128
        assert embedding1 == embedding2  # Deterministic

        # Different text should give different embedding
        embedding3 = ltm._simple_hash_embedding("different text")
        assert embedding1 != embedding3

    def test_cosine_similarity(self, ltm):
        """Test cosine similarity calculation"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]

        sim_same = ltm._cosine_similarity(vec1, vec2)
        sim_diff = ltm._cosine_similarity(vec1, vec3)

        assert sim_same == 1.0  # Same vector
        assert sim_diff == 0.0  # Orthogonal

    def test_cosine_similarity_zero(self, ltm):
        """Test cosine similarity with zero vectors"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        sim = ltm._cosine_similarity(vec1, vec2)

        assert sim == 0.0


class TestEpisodicMemory:
    """Test EpisodicMemory class"""

    @pytest.mark.asyncio
    async def test_episodic_memory_creation(self):
        """Test EpisodicMemory initialization"""
        from autonomous.memory import EpisodicMemory

        em = EpisodicMemory()

        assert em.episodes == []

    def test_record_episode(self):
        """Test recording an episode"""
        from autonomous.memory import EpisodicMemory

        em = EpisodicMemory()

        # Record episode
        em.record_episode(
            goal="Find vulnerabilities",
            steps=[{"action": "recon", "result": "found subdomains"}, {"action": "scan", "result": "found open ports"}],
            outcome="Found 3 vulnerabilities",
            success=True,
            lessons_learned=["Always check for default credentials"],
        )

        assert len(em.episodes) == 1
        episode = em.episodes[0]
        assert episode["goal"] == "Find vulnerabilities"
        assert episode["outcome"] == "Found 3 vulnerabilities"
        assert episode["success"] is True
        assert len(episode["lessons_learned"]) == 1

    def test_get_episode_by_index(self):
        """Test retrieving an episode by index"""
        from autonomous.memory import EpisodicMemory

        em = EpisodicMemory()

        em.record_episode(goal="Test goal", steps=[], outcome="Test", success=True, lessons_learned=[])

        episode = em.episodes[0]

        assert episode is not None
        assert episode["goal"] == "Test goal"

    def test_episodes_empty_initially(self):
        """Test that episodes are empty initially"""
        from autonomous.memory import EpisodicMemory

        em = EpisodicMemory()

        assert len(em.episodes) == 0

    def test_get_similar_episodes(self):
        """Test finding similar episodes by goal"""
        from autonomous.memory import EpisodicMemory

        em = EpisodicMemory()

        # Create episodes
        em.record_episode(goal="Web Application Test", steps=[], outcome="Success", success=True, lessons_learned=[])
        em.record_episode(goal="Network Scan", steps=[], outcome="Success", success=True, lessons_learned=[])
        em.record_episode(
            goal="Web App Security Assessment", steps=[], outcome="Found vulnerabilities", success=True, lessons_learned=[]
        )

        # Find similar to "web application testing"
        similar = em.get_similar_episodes("web application testing")

        assert len(similar) > 0
        # Should return "Web Application Test" or "Web App Security Assessment" first
        assert "Web" in similar[0]["goal"]

    def test_get_similar_episodes_jaccard(self):
        """Test Jaccard similarity calculation"""
        from autonomous.memory import EpisodicMemory

        em = EpisodicMemory()

        # Create episodes with overlapping words
        em.record_episode(
            goal="find sql injection vulnerabilities", steps=[], outcome="Success", success=True, lessons_learned=[]
        )
        em.record_episode(goal="test xss in web application", steps=[], outcome="Success", success=True, lessons_learned=[])

        similar = em.get_similar_episodes("find injection vulnerabilities")

        # SQL injection should rank higher
        assert len(similar) > 0
        assert "injection" in similar[0]["goal"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
