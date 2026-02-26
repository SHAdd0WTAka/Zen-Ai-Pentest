"""
Tests for memory/config.py
Target: 100% Coverage
"""


class TestMemoryConfig:
    """Test MEMORY_CONFIG dictionary"""
    
    def test_config_exists(self):
        """Test MEMORY_CONFIG is defined"""
        from memory.config import MEMORY_CONFIG
        
        assert isinstance(MEMORY_CONFIG, dict)
    
    def test_default_storage(self):
        """Test default storage is sqlite"""
        from memory.config import MEMORY_CONFIG
        
        assert MEMORY_CONFIG["default_storage"] == "sqlite"
    
    def test_sqlite_config(self):
        """Test SQLite configuration"""
        from memory.config import MEMORY_CONFIG
        
        assert "db_path" in MEMORY_CONFIG["sqlite"]
        assert MEMORY_CONFIG["sqlite"]["db_path"] == "data/memory.db"
    
    def test_redis_config(self):
        """Test Redis configuration"""
        from memory.config import MEMORY_CONFIG
        
        redis_config = MEMORY_CONFIG["redis"]
        assert redis_config["host"] == "localhost"
        assert redis_config["port"] == 6379
        assert redis_config["db"] == 0
    
    def test_conversation_memory_config(self):
        """Test conversation memory settings"""
        from memory.config import MEMORY_CONFIG
        
        conv_config = MEMORY_CONFIG["conversation_memory"]
        assert conv_config["max_history"] == 20
        assert conv_config["persist"] is True
    
    def test_working_memory_config(self):
        """Test working memory settings"""
        from memory.config import MEMORY_CONFIG
        
        work_config = MEMORY_CONFIG["working_memory"]
        assert work_config["max_items"] == 50
        assert work_config["persist"] is False
    
    def test_cleanup_config(self):
        """Test cleanup settings"""
        from memory.config import MEMORY_CONFIG
        
        cleanup_config = MEMORY_CONFIG["cleanup"]
        assert cleanup_config["auto_cleanup"] is True
        assert cleanup_config["max_session_age_hours"] == 24
    
    def test_all_keys_present(self):
        """Test all expected keys are present"""
        from memory.config import MEMORY_CONFIG
        
        expected_keys = [
            "default_storage",
            "sqlite",
            "redis",
            "conversation_memory",
            "working_memory",
            "cleanup"
        ]
        
        for key in expected_keys:
            assert key in MEMORY_CONFIG
