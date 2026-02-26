"""
Tests for memory/manager.py
Target: 90%+ Coverage
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestMemoryManagerInit:
    """Test MemoryManager initialization"""
    
    @patch('memory.manager.SQLiteStorage')
    def test_init_sqlite(self, mock_sqlite):
        """Test initialization with SQLite"""
        from memory.manager import MemoryManager
        
        mock_storage = MagicMock()
        mock_sqlite.return_value = mock_storage
        
        manager = MemoryManager(storage_backend="sqlite", db_path="/tmp/test.db")
        
        mock_sqlite.assert_called_once_with(db_path="/tmp/test.db")
        assert manager.storage == mock_storage
    
    @patch('memory.manager.RedisStorage')
    def test_init_redis(self, mock_redis):
        """Test initialization with Redis"""
        from memory.manager import MemoryManager
        
        mock_storage = MagicMock()
        mock_redis.return_value = mock_storage
        
        manager = MemoryManager(storage_backend="redis", host="localhost")
        
        mock_redis.assert_called_once_with(host="localhost")
        assert manager.storage == mock_storage
    
    def test_init_unknown_backend(self):
        """Test initialization with unknown backend"""
        from memory.manager import MemoryManager
        
        with pytest.raises(ValueError):
            MemoryManager(storage_backend="unknown")


class TestCreateConversationMemory:
    """Test create_conversation_memory"""
    
    @patch('memory.manager.SQLiteStorage')
    @patch('memory.manager.ConversationMemory')
    def test_create_new_memory(self, mock_conv_class, mock_sqlite):
        """Test creating new conversation memory"""
        from memory.manager import MemoryManager
        
        mock_storage = MagicMock()
        mock_sqlite.return_value = mock_storage
        
        mock_memory = MagicMock()
        mock_conv_class.return_value = mock_memory
        
        manager = MemoryManager()
        result = manager.create_conversation_memory("session-123", max_history=50)
        
        mock_conv_class.assert_called_once_with(
            session_id="session-123",
            storage=mock_storage,
            max_history=50
        )
        assert result == mock_memory
    
    @patch('memory.manager.SQLiteStorage')
    @patch('memory.manager.ConversationMemory')
    def test_get_existing_memory(self, mock_conv_class, mock_sqlite):
        """Test getting existing memory"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        mock_memory = MagicMock()
        mock_conv_class.return_value = mock_memory
        
        manager = MemoryManager()
        
        # First call creates
        result1 = manager.create_conversation_memory("session-123")
        # Second call retrieves
        result2 = manager.create_conversation_memory("session-123")
        
        # Should only create once
        mock_conv_class.assert_called_once()
        assert result1 == result2


class TestGetMemory:
    """Test get_memory"""
    
    @patch('memory.manager.SQLiteStorage')
    def test_get_existing(self, mock_sqlite):
        """Test getting existing memory"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        # Create memory first
        with patch('memory.manager.ConversationMemory') as mock_conv:
            mock_memory = MagicMock()
            mock_conv.return_value = mock_memory
            manager.create_conversation_memory("session-123")
        
        result = manager.get_memory("session-123")
        assert result is not None
    
    @patch('memory.manager.SQLiteStorage')
    def test_get_nonexistent(self, mock_sqlite):
        """Test getting non-existent memory"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        result = manager.get_memory("nonexistent")
        assert result is None


class TestClearSession:
    """Test clear_session"""
    
    @patch('memory.manager.SQLiteStorage')
    def test_clear_existing_session(self, mock_sqlite):
        """Test clearing existing session"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        with patch('memory.manager.ConversationMemory') as mock_conv:
            mock_memory = MagicMock()
            mock_conv.return_value = mock_memory
            manager.create_conversation_memory("session-123")
        
        manager.clear_session("session-123")
        
        mock_memory.clear.assert_called_once()
        assert "session-123" not in manager._memories
    
    @patch('memory.manager.SQLiteStorage')
    def test_clear_nonexistent_session(self, mock_sqlite):
        """Test clearing non-existent session doesn't error"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        # Should not raise
        manager.clear_session("nonexistent")


class TestGetAllSessions:
    """Test get_all_sessions"""
    
    @patch('memory.manager.SQLiteStorage')
    def test_get_all_sessions(self, mock_sqlite):
        """Test listing all sessions"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        with patch('memory.manager.ConversationMemory') as mock_conv:
            mock_conv.return_value = MagicMock()
            manager.create_conversation_memory("session-1")
            manager.create_conversation_memory("session-2")
        
        sessions = manager.get_all_sessions()
        
        assert len(sessions) == 2
        assert "session-1" in sessions
        assert "session-2" in sessions


class TestCleanupOldSessions:
    """Test cleanup_old_sessions"""
    
    @patch('memory.manager.SQLiteStorage')
    def test_cleanup_no_old_sessions(self, mock_sqlite):
        """Test cleanup with no old sessions"""
        from memory.manager import MemoryManager
        from memory.base import MemoryEntry, MemoryType
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        with patch('memory.manager.ConversationMemory') as mock_conv:
            mock_memory = MagicMock()
            # Recent entry
            mock_memory._cache = [
                MemoryEntry(id="1", content="recent", memory_type=MemoryType.CONVERSATION)
            ]
            mock_conv.return_value = mock_memory
            manager.create_conversation_memory("session-123")
        
        count = manager.cleanup_old_sessions(max_age_hours=24)
        
        assert count == 0
    
    @patch('memory.manager.SQLiteStorage')
    def test_cleanup_old_sessions(self, mock_sqlite):
        """Test cleanup removes old sessions"""
        from memory.manager import MemoryManager
        from memory.base import MemoryEntry, MemoryType
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        with patch('memory.manager.ConversationMemory') as mock_conv:
            mock_memory = MagicMock()
            # Old entry (25 hours ago)
            old_entry = MemoryEntry(
                id="1", 
                content="old", 
                memory_type=MemoryType.CONVERSATION,
                timestamp=datetime.now() - timedelta(hours=25)
            )
            mock_memory._cache = [old_entry]
            mock_conv.return_value = mock_memory
            manager.create_conversation_memory("old-session")
        
        count = manager.cleanup_old_sessions(max_age_hours=24)
        
        assert count == 1
        assert "old-session" not in manager._memories
    
    @patch('memory.manager.SQLiteStorage')
    def test_cleanup_empty_cache(self, mock_sqlite):
        """Test cleanup with empty cache"""
        from memory.manager import MemoryManager
        
        mock_sqlite.return_value = MagicMock()
        manager = MemoryManager()
        
        with patch('memory.manager.ConversationMemory') as mock_conv:
            mock_memory = MagicMock()
            mock_memory._cache = []
            mock_conv.return_value = mock_memory
            manager.create_conversation_memory("empty-session")
        
        count = manager.cleanup_old_sessions(max_age_hours=24)
        
        assert count == 0
