"""
Unit Tests für core/models.py

Tests Pydantic Models ohne Datenbank/API Abhängigkeiten.
"""

from datetime import datetime

import pytest

from core.models import APIKeyConfig, BackendType, ScanConfig, ScanStatus, Severity, TimestampedModel

# Mark all tests as unit tests
pytestmark = pytest.mark.unit


class TestEnums:
    """Test für Enum Klassen"""

    def test_severity_enum_values(self):
        """Test Severity Enum hat alle Werte"""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"

    def test_scan_status_enum_values(self):
        """Test ScanStatus Enum hat alle Werte"""
        assert ScanStatus.PENDING == "pending"
        assert ScanStatus.RUNNING == "running"
        assert ScanStatus.COMPLETED == "completed"
        assert ScanStatus.FAILED == "failed"
        assert ScanStatus.CANCELLED == "cancelled"

    def test_backend_type_enum_values(self):
        """Test BackendType Enum hat alle Werte"""
        assert BackendType.DUCKDUCKGO == "duckduckgo"
        assert BackendType.OPENROUTER == "openrouter"
        assert BackendType.OPENAI == "openai"
        assert BackendType.ANTHROPIC == "anthropic"


class TestTimestampedModel:
    """Test für TimestampedModel"""

    def test_default_timestamps(self):
        """Test that created_at is set automatically"""
        model = TimestampedModel()
        assert model.created_at is not None
        assert isinstance(model.created_at, datetime)

    def test_updated_at_optional(self):
        """Test that updated_at is optional"""
        model = TimestampedModel()
        assert model.updated_at is None

        # Set updated_at
        now = datetime.utcnow()
        model.updated_at = now
        assert model.updated_at == now


class TestAPIKeyConfig:
    """Test für APIKeyConfig"""

    def test_empty_config(self):
        """Test empty config is valid"""
        config = APIKeyConfig()
        assert config.openrouter_key is None
        assert config.openai_key is None
        assert config.anthropic_key is None

    def test_openrouter_key_validation(self):
        """Test OpenRouter key validation"""
        # Valid key
        config = APIKeyConfig(openrouter_key="sk-or-12345678901234567890")
        assert config.openrouter_key is not None

        # Invalid key (wrong prefix)
        with pytest.raises(ValueError):
            APIKeyConfig(openrouter_key="invalid-key")

    def test_openai_key_validation(self):
        """Test OpenAI key validation"""
        # Valid key
        config = APIKeyConfig(openai_key="sk-1234567890123456789012345678")
        assert config.openai_key is not None

        # Invalid key (wrong prefix)
        with pytest.raises(ValueError):
            APIKeyConfig(openai_key="not-an-openai-key")

    def test_anthropic_key_validation(self):
        """Test Anthropic key validation"""
        # Valid key
        config = APIKeyConfig(anthropic_key="sk-ant-123456789012345678901234")
        assert config.anthropic_key is not None

        # Invalid key
        with pytest.raises(ValueError):
            APIKeyConfig(anthropic_key="invalid-key")

    def test_get_key_mapping(self):
        """Test get_key returns correct key for provider"""
        config = APIKeyConfig(openrouter_key="sk-or-12345678901234567890", openai_key="sk-1234567890123456789012345678")

        assert config.get_key(BackendType.OPENROUTER) == "sk-or-12345678901234567890"
        assert config.get_key(BackendType.OPENAI) == "sk-1234567890123456789012345678"
        assert config.get_key(BackendType.ANTHROPIC) is None
        assert config.get_key(BackendType.DUCKDUCKGO) is None

    def test_no_extra_fields(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(ValueError):
            APIKeyConfig(invalid_field="should fail")


class TestScanConfig:
    """Test für ScanConfig"""

    def test_default_values(self):
        """Test default scan configuration"""
        config = ScanConfig(target="example.com")

        assert config.target == "example.com"
        assert config.scan_type == "quick"
        assert config.ports == [80, 443]
        assert config.templates == []
        assert config.timeout == 300
        assert config.concurrent == 5
        assert config.follow_redirects is True

    def test_custom_values(self):
        """Test custom scan configuration"""
        config = ScanConfig(
            target="test.com", scan_type="full", ports=[22, 80, 443, 8080], timeout=600, concurrent=10, follow_redirects=False
        )

        assert config.target == "test.com"
        assert config.scan_type == "full"
        assert config.ports == [22, 80, 443, 8080]
        assert config.timeout == 600
        assert config.concurrent == 10
        assert config.follow_redirects is False

    def test_target_validation_min_length(self):
        """Test target must not be empty"""
        with pytest.raises(ValueError):
            ScanConfig(target="")

    def test_target_validation_max_length(self):
        """Test target max length"""
        with pytest.raises(ValueError):
            ScanConfig(target="a" * 254)

    def test_target_dangerous_characters(self):
        """Test target rejects dangerous characters"""
        dangerous = [";", "|", "&", "`", "$", "(", ")"]
        for char in dangerous:
            with pytest.raises(ValueError):
                ScanConfig(target=f"test{char}.com")

    def test_timeout_validation(self):
        """Test timeout bounds"""
        # Too low
        with pytest.raises(ValueError):
            ScanConfig(target="test.com", timeout=5)

        # Too high
        with pytest.raises(ValueError):
            ScanConfig(target="test.com", timeout=4000)

        # Valid bounds
        config1 = ScanConfig(target="test.com", timeout=10)
        assert config1.timeout == 10

        config2 = ScanConfig(target="test.com", timeout=3600)
        assert config2.timeout == 3600

    def test_concurrent_validation(self):
        """Test concurrent bounds"""
        # Too low
        with pytest.raises(ValueError):
            ScanConfig(target="test.com", concurrent=0)

        # Too high
        with pytest.raises(ValueError):
            ScanConfig(target="test.com", concurrent=100)

        # Valid
        config = ScanConfig(target="test.com", concurrent=25)
        assert config.concurrent == 25

    def test_scan_type_literal(self):
        """Test scan_type must be valid literal"""
        # Valid types
        ScanConfig(target="test.com", scan_type="quick")
        ScanConfig(target="test.com", scan_type="full")
        ScanConfig(target="test.com", scan_type="stealth")

        # Invalid type
        with pytest.raises(ValueError):
            ScanConfig(target="test.com", scan_type="invalid")

    def test_target_normalization(self):
        """Test target is normalized (lowercase, stripped)"""
        config = ScanConfig(target="  EXAMPLE.COM  ")
        assert config.target == "example.com"


class TestModelSerialization:
    """Test Model serialization/deserialization"""

    def test_api_key_config_dict(self):
        """Test APIKeyConfig converts to dict"""
        config = APIKeyConfig(openai_key="sk-1234567890123456789012345678")
        data = config.model_dump()

        assert "openai_key" in data
        assert "openrouter_key" in data
        assert data["openai_key"] == "sk-1234567890123456789012345678"

    def test_scan_config_dict(self):
        """Test ScanConfig converts to dict"""
        config = ScanConfig(target="example.com", scan_type="full")
        data = config.model_dump()

        assert data["target"] == "example.com"
        assert data["scan_type"] == "full"

    def test_scan_config_json(self):
        """Test ScanConfig converts to JSON"""
        import json

        config = ScanConfig(target="example.com")
        json_str = config.model_dump_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["target"] == "example.com"
