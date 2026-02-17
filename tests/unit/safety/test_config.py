"""
Unit Tests für safety/config.py
"""

import pytest
from safety.config import SAFETY_CONFIG
from safety.guardrails import SafetyLevel

pytestmark = pytest.mark.unit


class TestSafetyConfig:
    """Test SAFETY_CONFIG dictionary"""

    def test_config_has_default_level(self):
        """Test default_level exists"""
        assert "default_level" in SAFETY_CONFIG
        assert SAFETY_CONFIG["default_level"] == SafetyLevel.STANDARD

    def test_config_has_auto_correct(self):
        """Test auto_correct flag exists"""
        assert "auto_correct" in SAFETY_CONFIG
        assert isinstance(SAFETY_CONFIG["auto_correct"], bool)

    def test_config_has_thresholds(self):
        """Test threshold values exist"""
        assert "retry_threshold" in SAFETY_CONFIG
        assert "alert_threshold" in SAFETY_CONFIG
        assert 0 <= SAFETY_CONFIG["retry_threshold"] <= 1
        assert 0 <= SAFETY_CONFIG["alert_threshold"] <= 1

    def test_config_has_max_retries(self):
        """Test max_retries exists"""
        assert "max_retries" in SAFETY_CONFIG
        assert isinstance(SAFETY_CONFIG["max_retries"], int)
        assert SAFETY_CONFIG["max_retries"] >= 0

    def test_config_has_context_levels(self):
        """Test context_levels exists"""
        assert "context_levels" in SAFETY_CONFIG
        contexts = SAFETY_CONFIG["context_levels"]

        assert "production" in contexts
        assert "pentest" in contexts
        assert "development" in contexts
        assert "critical" in contexts

    def test_context_levels_are_safety_levels(self):
        """Test context levels are valid SafetyLevel enums"""
        contexts = SAFETY_CONFIG["context_levels"]

        assert contexts["production"] == SafetyLevel.STRICT
        assert contexts["pentest"] == SafetyLevel.STANDARD
        assert contexts["development"] == SafetyLevel.PERMISSIVE
        assert contexts["critical"] == SafetyLevel.PARANOID

    def test_thresholds_are_reasonable(self):
        """Test thresholds are within reasonable range"""
        assert 0.5 <= SAFETY_CONFIG["retry_threshold"] <= 0.8
        assert 0.3 <= SAFETY_CONFIG["alert_threshold"] <= 0.7
