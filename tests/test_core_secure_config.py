"""
Tests for core/secure_config.py
Target: 85%+ Coverage
"""
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


class TestAPIKeyConfig:
    """Test APIKeyConfig dataclass"""
    
    def test_default_creation(self):
        """Test default creation"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig()
        assert config.openrouter_key is None
        assert config.openai_key is None
        assert config.anthropic_key is None
    
    def test_get_key_openrouter(self):
        """Test get_key for openrouter"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(openrouter_key="sk-or-test")
        assert config.get_key("openrouter") == "sk-or-test"
    
    def test_get_key_openai(self):
        """Test get_key for openai"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(openai_key="sk-test")
        assert config.get_key("openai") == "sk-test"
        assert config.get_key("chatgpt") == "sk-test"  # Alias
    
    def test_get_key_anthropic(self):
        """Test get_key for anthropic"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(anthropic_key="sk-ant-test")
        assert config.get_key("anthropic") == "sk-ant-test"
        assert config.get_key("claude") == "sk-ant-test"  # Alias
    
    def test_get_key_github(self):
        """Test get_key for github"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(github_token="ghp_test")
        assert config.get_key("github") == "ghp_test"
    
    def test_get_key_shodan(self):
        """Test get_key for shodan"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(shodan_key="shodan_test")
        assert config.get_key("shodan") == "shodan_test"
    
    def test_get_key_censys(self):
        """Test get_key for censys"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(censys_id="id123", censys_secret="secret456")
        assert config.get_key("censys_id") == "id123"
        assert config.get_key("censys_secret") == "secret456"
    
    def test_get_key_unknown(self):
        """Test get_key for unknown provider"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig()
        assert config.get_key("unknown") is None
    
    def test_get_key_case_insensitive(self):
        """Test get_key is case insensitive"""
        from core.secure_config import APIKeyConfig
        
        config = APIKeyConfig(openai_key="sk-test")
        assert config.get_key("OPENAI") == "sk-test"
        assert config.get_key("OpenAI") == "sk-test"


class TestSecureConfigManagerInit:
    """Test SecureConfigManager initialization"""
    
    def test_default_init(self, tmp_path):
        """Test default initialization"""
        from core.secure_config import SecureConfigManager
        
        with patch.object(Path, 'home', return_value=tmp_path):
            manager = SecureConfigManager()
            
            assert manager.config_dir == tmp_path / ".config" / "zen-ai-pentest"
            assert manager.config_file == tmp_path / ".config" / "zen-ai-pentest" / "config.json"
    
    def test_custom_config_dir(self, tmp_path):
        """Test custom config directory"""
        from core.secure_config import SecureConfigManager
        
        custom_dir = tmp_path / "custom"
        manager = SecureConfigManager(config_dir=custom_dir)
        
        assert manager.config_dir == custom_dir
        assert manager.config_file == custom_dir / "config.json"
    
    def test_init_creates_directory(self, tmp_path):
        """Test init creates config directory"""
        from core.secure_config import SecureConfigManager
        
        config_dir = tmp_path / "new_config"
        assert not config_dir.exists()
        
        SecureConfigManager(config_dir=config_dir)
        
        assert config_dir.exists()


class TestGetApiKey:
    """Test get_api_key method"""
    
    def test_get_from_environment(self, tmp_path):
        """Test getting key from environment variable"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        with patch.dict(os.environ, {"ZEN_OPENAI_KEY": "sk-env-test"}):
            result = manager.get_api_key("openai")
            assert result == "sk-env-test"
    
    def test_get_from_env_without_prefix(self, tmp_path):
        """Test getting key from env without ZEN_ prefix"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        with patch.dict(os.environ, {"OPENAI_KEY": "sk-env-test"}):
            result = manager.get_api_key("openai")
            assert result == "sk-env-test"
    
    def test_env_priority_over_keyring(self, tmp_path):
        """Test environment variable has priority"""
        from core.secure_config import SecureConfigManager, KEYRING_AVAILABLE
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        with patch.dict(os.environ, {"ZEN_OPENAI_KEY": "sk-env"}):
            # Even if keyring has a value, env should win
            result = manager.get_api_key("openai")
            assert result == "sk-env"
    
    def test_no_key_found(self, tmp_path):
        """Test when no key is found"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        # Ensure no env var and no keyring
        with patch.dict(os.environ, {}, clear=True):
            result = manager.get_api_key("nonexistent")
            assert result is None


class TestSetApiKey:
    """Test set_api_key method"""
    
    def test_set_to_env_file(self, tmp_path):
        """Test setting key to env file"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        with patch('os.chmod'):
            result = manager.set_api_key("openai", "sk-test", storage="env")
            assert result is True
            
            # Check file was created
            env_file = tmp_path / ".env"
            assert env_file.exists()
            content = env_file.read_text()
            assert "ZEN_OPENAI_KEY=sk-test" in content
    
    def test_set_to_env_file_update_existing(self, tmp_path):
        """Test updating existing key in env file"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        env_file = tmp_path / ".env"
        env_file.write_text("ZEN_OPENAI_KEY=old_key\n")
        
        with patch('os.chmod'):
            manager.set_api_key("openai", "sk-new", storage="env")
            
            content = env_file.read_text()
            assert "ZEN_OPENAI_KEY=sk-new" in content
            assert "old_key" not in content
    
    def test_set_keyring_not_available(self, tmp_path):
        """Test keyring storage when not available"""
        from core.secure_config import SecureConfigManager
        
        with patch('core.secure_config.KEYRING_AVAILABLE', False):
            manager = SecureConfigManager(config_dir=tmp_path)
            result = manager.set_api_key("openai", "sk-test", storage="keyring")
            assert result is False
    
    def test_set_invalid_storage(self, tmp_path):
        """Test invalid storage option"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        result = manager.set_api_key("openai", "sk-test", storage="invalid")
        assert result is False


class TestListConfiguredKeys:
    """Test list_configured_keys method"""
    
    def test_list_empty(self, tmp_path):
        """Test listing when no keys configured"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        with patch.object(manager, 'get_api_key', return_value=None):
            result = manager.list_configured_keys()
            assert result == []
    
    def test_list_with_keys(self, tmp_path):
        """Test listing with configured keys"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        def mock_get_key(provider):
            if provider in ["openai", "github"]:
                return "key_value"
            return None
        
        with patch.object(manager, 'get_api_key', side_effect=mock_get_key):
            result = manager.list_configured_keys()
            assert "openai" in result
            assert "github" in result


class TestRemoveApiKey:
    """Test remove_api_key method"""
    
    def test_remove_from_keyring(self, tmp_path):
        """Test removing key from keyring"""
        from core.secure_config import SecureConfigManager
        
        with patch('core.secure_config.KEYRING_AVAILABLE', True):
            with patch.object(SecureConfigManager, '_get_keyring_password', return_value=None):
                manager = SecureConfigManager(config_dir=tmp_path)
                # Just verify no exception is raised
                manager.remove_api_key("openai")
    
    def test_remove_from_encrypted_config(self, tmp_path):
        """Test removing key from encrypted config"""
        from core.secure_config import SecureConfigManager
        
        manager = SecureConfigManager(config_dir=tmp_path)
        
        # Mock encrypted config exists with key
        with patch.object(manager, 'encrypted_config') as mock_encrypted:
            mock_encrypted.exists.return_value = True
            with patch.object(manager, '_load_encrypted_config') as mock_load:
                mock_load.return_value = {"openai": "sk-test", "other": "key"}
                with patch.object(manager, '_save_encrypted_config') as mock_save:
                    mock_save.return_value = True
                    
                    result = manager.remove_api_key("openai")
                    
                    assert result is True


class TestGetSecureConfig:
    """Test get_secure_config function"""
    
    def test_singleton(self):
        """Test get_secure_config returns singleton"""
        from core.secure_config import get_secure_config, SecureConfigManager
        
        # Clear cache first
        get_secure_config.cache_clear()
        
        config1 = get_secure_config()
        config2 = get_secure_config()
        
        assert config1 is config2
        assert isinstance(config1, SecureConfigManager)


class TestMigratePlainConfig:
    """Test migrate_plain_config function"""
    
    def test_migrate_nonexistent_file(self, tmp_path):
        """Test migrating non-existent file"""
        from core.secure_config import migrate_plain_config
        
        result = migrate_plain_config(tmp_path / "nonexistent.json")
        assert result is False
    
    def test_migrate_valid_config(self, tmp_path):
        """Test migrating valid config file"""
        from core.secure_config import migrate_plain_config
        import json
        
        config_file = tmp_path / "old_config.json"
        config_data = {
            "openai_key": "sk-openai",
            "anthropic_key": "sk-anthropic",
            "github_token": "ghp_token"
        }
        config_file.write_text(json.dumps(config_data))
        
        with patch('core.secure_config.get_secure_config') as mock_get:
            mock_manager = MagicMock()
            mock_manager.set_api_key.return_value = True
            mock_get.return_value = mock_manager
            
            result = migrate_plain_config(config_file)
            
            assert result is True
            # Check that set_api_key was called for each key
            assert mock_manager.set_api_key.call_count == 3


class TestModuleConstants:
    """Test module constants"""
    
    def test_keyring_service_name(self):
        """Test KEYRING_SERVICE constant"""
        from core.secure_config import KEYRING_SERVICE
        assert KEYRING_SERVICE == "zen-ai-pentest"
    
    def test_env_prefix(self):
        """Test ENV_PREFIX constant"""
        from core.secure_config import ENV_PREFIX
        assert ENV_PREFIX == "ZEN_"
