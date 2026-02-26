"""
Tests for safety/config.py
Target: 100% Coverage
"""


class TestSafetyConfig:
    """Test SAFETY_CONFIG dictionary"""
    
    def test_config_exists(self):
        """Test SAFETY_CONFIG is defined"""
        from safety.config import SAFETY_CONFIG
        
        assert isinstance(SAFETY_CONFIG, dict)
    
    def test_default_level(self):
        """Test default safety level"""
        from safety.config import SAFETY_CONFIG
        from safety.guardrails import SafetyLevel
        
        assert SAFETY_CONFIG["default_level"] == SafetyLevel.STANDARD
    
    def test_auto_correct(self):
        """Test auto_correct setting"""
        from safety.config import SAFETY_CONFIG
        
        assert SAFETY_CONFIG["auto_correct"] is True
    
    def test_thresholds(self):
        """Test threshold values"""
        from safety.config import SAFETY_CONFIG
        
        assert SAFETY_CONFIG["retry_threshold"] == 0.6
        assert SAFETY_CONFIG["alert_threshold"] == 0.5
    
    def test_max_retries(self):
        """Test max retries setting"""
        from safety.config import SAFETY_CONFIG
        
        assert SAFETY_CONFIG["max_retries"] == 2
    
    def test_context_levels(self):
        """Test context-specific safety levels"""
        from safety.config import SAFETY_CONFIG
        from safety.guardrails import SafetyLevel
        
        context_levels = SAFETY_CONFIG["context_levels"]
        
        assert context_levels["production"] == SafetyLevel.STRICT
        assert context_levels["pentest"] == SafetyLevel.STANDARD
        assert context_levels["development"] == SafetyLevel.PERMISSIVE
        assert context_levels["critical"] == SafetyLevel.PARANOID
    
    def test_all_keys_present(self):
        """Test all expected keys are present"""
        from safety.config import SAFETY_CONFIG
        
        expected_keys = [
            "default_level",
            "auto_correct",
            "retry_threshold",
            "alert_threshold",
            "max_retries",
            "context_levels"
        ]
        
        for key in expected_keys:
            assert key in SAFETY_CONFIG
