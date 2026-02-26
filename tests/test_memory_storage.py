"""
Tests for memory/storage.py
Target: 85%+ Coverage (SQLiteStorage)
"""
import pytest
import tempfile
from datetime import datetime
from pathlib import Path


class TestSQLiteStorage:
    """Test SQLiteStorage class"""
    
    def test_init_creates_db(self):
        """Test initialization creates database"""
        from memory.storage import SQLiteStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            storage = SQLiteStorage(db_path=str(db_path))
            
            assert db_path.exists()
    
    def test_init_creates_directory(self):
        """Test initialization creates directory if needed"""
        from memory.storage import SQLiteStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "subdir" / "test.db"
            storage = SQLiteStorage(db_path=str(db_path))
            
            assert db_path.parent.exists()
            assert db_path.exists()
    
    def test_save_and_load(self):
        """Test saving and loading memory entry"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            entry = MemoryEntry(
                id="test-123",
                content="Test content",
                memory_type=MemoryType.CONVERSATION,
                metadata={"source": "test"},
                importance=0.8
            )
            
            storage.save(entry)
            loaded = storage.load("test-123")
            
            assert loaded is not None
            assert loaded.id == "test-123"
            assert loaded.content == "Test content"
            assert loaded.memory_type == MemoryType.CONVERSATION
            assert loaded.metadata["source"] == "test"
            assert loaded.importance == 0.8
    
    def test_load_nonexistent(self):
        """Test loading non-existent entry returns None"""
        from memory.storage import SQLiteStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            result = storage.load("nonexistent")
            assert result is None
    
    def test_save_updates_existing(self):
        """Test saving updates existing entry"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            entry1 = MemoryEntry(
                id="test-123",
                content="Original content",
                memory_type=MemoryType.CONVERSATION
            )
            storage.save(entry1)
            
            entry2 = MemoryEntry(
                id="test-123",
                content="Updated content",
                memory_type=MemoryType.WORKING
            )
            storage.save(entry2)
            
            loaded = storage.load("test-123")
            assert loaded.content == "Updated content"
            assert loaded.memory_type == MemoryType.WORKING
    
    def test_load_by_type(self):
        """Test loading entries by type"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            # Create entries of different types
            entry1 = MemoryEntry(
                id="conv-1",
                content="Conversation 1",
                memory_type=MemoryType.CONVERSATION
            )
            entry2 = MemoryEntry(
                id="conv-2",
                content="Conversation 2",
                memory_type=MemoryType.CONVERSATION
            )
            entry3 = MemoryEntry(
                id="work-1",
                content="Working 1",
                memory_type=MemoryType.WORKING
            )
            
            storage.save(entry1)
            storage.save(entry2)
            storage.save(entry3)
            
            conversations = storage.load_by_type(MemoryType.CONVERSATION)
            assert len(conversations) == 2
            
            working = storage.load_by_type(MemoryType.WORKING)
            assert len(working) == 1
    
    def test_load_by_type_limit(self):
        """Test load_by_type respects limit"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            # Create multiple entries
            for i in range(5):
                entry = MemoryEntry(
                    id=f"entry-{i}",
                    content=f"Content {i}",
                    memory_type=MemoryType.CONVERSATION
                )
                storage.save(entry)
            
            results = storage.load_by_type(MemoryType.CONVERSATION, limit=3)
            assert len(results) == 3
    
    def test_load_by_type_ordering(self):
        """Test load_by_type orders by timestamp descending"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        from datetime import datetime, timedelta
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            # Create entries with different timestamps
            entry1 = MemoryEntry(
                id="old",
                content="Old entry",
                memory_type=MemoryType.CONVERSATION,
                timestamp=datetime.now() - timedelta(hours=2)
            )
            entry2 = MemoryEntry(
                id="new",
                content="New entry",
                memory_type=MemoryType.CONVERSATION,
                timestamp=datetime.now()
            )
            
            storage.save(entry1)
            storage.save(entry2)
            
            results = storage.load_by_type(MemoryType.CONVERSATION)
            assert results[0].id == "new"  # Most recent first
            assert results[1].id == "old"
    
    def test_search(self):
        """Test searching memories"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            entry1 = MemoryEntry(
                id="search-1",
                content="This contains the keyword",
                memory_type=MemoryType.CONVERSATION
            )
            entry2 = MemoryEntry(
                id="search-2",
                content="This also has keyword in it",
                memory_type=MemoryType.CONVERSATION
            )
            entry3 = MemoryEntry(
                id="search-3",
                content="No match here",
                memory_type=MemoryType.CONVERSATION
            )
            
            storage.save(entry1)
            storage.save(entry2)
            storage.save(entry3)
            
            results = storage.search("keyword")
            assert len(results) == 2
    
    def test_search_limit(self):
        """Test search respects limit"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            # Create multiple matching entries
            for i in range(5):
                entry = MemoryEntry(
                    id=f"search-{i}",
                    content=f"Content with keyword {i}",
                    memory_type=MemoryType.CONVERSATION
                )
                storage.save(entry)
            
            results = storage.search("keyword", limit=3)
            assert len(results) == 3
    
    def test_search_no_results(self):
        """Test search with no matches"""
        from memory.storage import SQLiteStorage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            results = storage.search("nonexistent")
            assert results == []
    
    def test_metadata_roundtrip(self):
        """Test metadata is preserved correctly"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            complex_metadata = {
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "number": 42,
                "boolean": True
            }
            
            entry = MemoryEntry(
                id="meta-test",
                content="Test",
                memory_type=MemoryType.CONVERSATION,
                metadata=complex_metadata
            )
            
            storage.save(entry)
            loaded = storage.load("meta-test")
            
            assert loaded.metadata == complex_metadata
    
    def test_empty_metadata(self):
        """Test entry with empty metadata"""
        from memory.storage import SQLiteStorage
        from memory.base import MemoryEntry, MemoryType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = SQLiteStorage(db_path=str(Path(tmpdir) / "test.db"))
            
            entry = MemoryEntry(
                id="empty-meta",
                content="Test",
                memory_type=MemoryType.CONVERSATION,
                metadata={}
            )
            
            storage.save(entry)
            loaded = storage.load("empty-meta")
            
            assert loaded.metadata == {}


class TestRedisStorage:
    """Test RedisStorage class (without actual Redis)"""
    
    def test_redis_storage_import(self):
        """Test RedisStorage can be imported"""
        from memory.storage import RedisStorage, REDIS_AVAILABLE
        
        # Just verify the class exists
        assert hasattr(RedisStorage, 'save')
        assert hasattr(RedisStorage, 'load')
