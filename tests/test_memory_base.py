"""
Tests for memory/base.py
Target: 95%+ Coverage
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock


class TestMemoryTypeEnum:
    """Test MemoryType enum"""
    
    def test_enum_values(self):
        """Test MemoryType enum values"""
        from memory.base import MemoryType
        
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.WORKING.value == "working"
        assert MemoryType.LONG_TERM.value == "long_term"
        assert MemoryType.EPISODIC.value == "episodic"


class TestMemoryEntry:
    """Test MemoryEntry dataclass"""
    
    def test_create_entry(self):
        """Test creating memory entry"""
        from memory.base import MemoryEntry, MemoryType
        
        entry = MemoryEntry(
            id="test-123",
            content="Test content",
            memory_type=MemoryType.CONVERSATION
        )
        
        assert entry.id == "test-123"
        assert entry.content == "Test content"
        assert entry.memory_type == MemoryType.CONVERSATION
        assert entry.importance == 1.0
        assert isinstance(entry.timestamp, datetime)
    
    def test_entry_with_metadata(self):
        """Test entry with metadata"""
        from memory.base import MemoryEntry, MemoryType
        
        entry = MemoryEntry(
            id="test-456",
            content="Test with metadata",
            memory_type=MemoryType.WORKING,
            metadata={"source": "user", "topic": "testing"},
            importance=0.8
        )
        
        assert entry.metadata["source"] == "user"
        assert entry.importance == 0.8
    
    def test_to_dict(self):
        """Test converting entry to dict"""
        from memory.base import MemoryEntry, MemoryType
        
        entry = MemoryEntry(
            id="test-789",
            content="Dict test",
            memory_type=MemoryType.LONG_TERM,
            metadata={"key": "value"}
        )
        
        data = entry.to_dict()
        
        assert data["id"] == "test-789"
        assert data["content"] == "Dict test"
        assert data["memory_type"] == "long_term"
        assert "timestamp" in data
        assert data["metadata"]["key"] == "value"
    
    def test_from_dict(self):
        """Test creating entry from dict"""
        from memory.base import MemoryEntry, MemoryType
        
        data = {
            "id": "from-dict-123",
            "content": "From dict",
            "memory_type": "episodic",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True},
            "importance": 0.5
        }
        
        entry = MemoryEntry.from_dict(data)
        
        assert entry.id == "from-dict-123"
        assert entry.content == "From dict"
        assert entry.memory_type == MemoryType.EPISODIC
        assert entry.importance == 0.5
    
    def test_from_dict_defaults(self):
        """Test from_dict with default values"""
        from memory.base import MemoryEntry, MemoryType
        
        data = {
            "id": "minimal",
            "content": "Minimal",
            "memory_type": "conversation",
            "timestamp": datetime.now().isoformat()
        }
        
        entry = MemoryEntry.from_dict(data)
        
        assert entry.metadata == {}
        assert entry.importance == 1.0


class TestBaseMemory:
    """Test BaseMemory abstract class"""
    
    def test_base_memory_init(self):
        """Test BaseMemory initialization"""
        from memory.base import BaseMemory, MemoryType
        
        # Create concrete implementation for testing
        class TestMemory(BaseMemory):
            def add(self, content, **metadata):
                return "id"
            def get(self, entry_id):
                return None
            def search(self, query, limit=5):
                return []
            def get_recent(self, limit=10):
                return []
        
        memory = TestMemory(MemoryType.CONVERSATION)
        
        assert memory.memory_type == MemoryType.CONVERSATION
        assert memory.storage is None
        assert memory._cache == []
    
    def test_base_memory_clear(self):
        """Test clear method"""
        from memory.base import BaseMemory, MemoryType, MemoryEntry
        
        class TestMemory(BaseMemory):
            def add(self, content, **metadata):
                return "id"
            def get(self, entry_id):
                return None
            def search(self, query, limit=5):
                return []
            def get_recent(self, limit=10):
                return []
        
        memory = TestMemory(MemoryType.WORKING)
        memory._cache.append(MemoryEntry(id="1", content="test", memory_type=MemoryType.WORKING))
        
        assert len(memory._cache) == 1
        memory.clear()
        assert len(memory._cache) == 0
    
    def test_get_context_string_empty(self):
        """Test get_context_string with no entries"""
        from memory.base import BaseMemory, MemoryType
        
        class TestMemory(BaseMemory):
            def add(self, content, **metadata):
                return "id"
            def get(self, entry_id):
                return None
            def search(self, query, limit=5):
                return []
            def get_recent(self, limit=10):
                return []
        
        memory = TestMemory(MemoryType.CONVERSATION)
        result = memory.get_context_string()
        
        assert result == ""
    
    def test_get_context_string_with_entries(self):
        """Test get_context_string with entries"""
        from memory.base import BaseMemory, MemoryType, MemoryEntry
        
        entries = [
            MemoryEntry(id="1", content="First entry", memory_type=MemoryType.CONVERSATION),
            MemoryEntry(id="2", content="Second entry", memory_type=MemoryType.CONVERSATION)
        ]
        
        class TestMemory(BaseMemory):
            def add(self, content, **metadata):
                return "id"
            def get(self, entry_id):
                return None
            def search(self, query, limit=5):
                return []
            def get_recent(self, limit=10):
                return entries[:limit]
        
        memory = TestMemory(MemoryType.CONVERSATION)
        result = memory.get_context_string(limit=2)
        
        assert "First entry" in result
        assert "Second entry" in result
        assert "[" in result  # Has timestamp


class TestMemoryEntryIntegration:
    """Integration tests for MemoryEntry"""
    
    def test_entry_serialization_roundtrip(self):
        """Test serialization roundtrip"""
        from memory.base import MemoryEntry, MemoryType
        
        original = MemoryEntry(
            id="roundtrip-123",
            content="Test roundtrip",
            memory_type=MemoryType.EPISODIC,
            metadata={"roundtrip": True, "count": 42},
            importance=0.75
        )
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = MemoryEntry.from_dict(data)
        
        assert restored.id == original.id
        assert restored.content == original.content
        assert restored.memory_type == original.memory_type
        assert restored.metadata == original.metadata
        assert restored.importance == original.importance
