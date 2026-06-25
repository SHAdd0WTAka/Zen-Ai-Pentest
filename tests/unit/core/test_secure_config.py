"""
Unit Tests for core.secure_config module
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from core.secure_config import (
    APIKeyConfig,
    SecureConfigManager,
    get_secure_config,
    migrate_plain_config,
)


class TestAPIKeyConfig:
    """Tests for APIKeyConfig dataclass"""

    def test_init_default(self):
        config = APIKeyConfig()
        assert config.openrouter_key is None
        assert config.openai_key is None
        assert config.anthropic_key is None

    def test_init_with_values(self):
        config = APIKeyConfig(
            openrouter_key="test-router-key",
            openai_key="test-openai-key",
            github_token="test-github-token",
        )
        assert config.openrouter_key == "test-router-key"
        assert config.openai_key == "test-openai-key"
        assert config.github_token == "test-github-token"

    def test_get_key_openrouter(self):
        config = APIKeyConfig(openrouter_key="router-key")
        assert config.get_key("openrouter") == "router-key"

    def test_get_key_openai(self):
        config = APIKeyConfig(openai_key="openai-key")
        assert config.get_key("openai") == "openai-key"

    def test_get_key_anthropic_aliases(self):
        config = APIKeyConfig(anthropic_key="anthropic-key")
        assert config.get_key("anthropic") == "anthropic-key"
        assert config.get_key("claude") == "anthropic-key"

    def test_get_key_openai_aliases(self):
        config = APIKeyConfig(openai_key="openai-key")
        assert config.get_key("chatgpt") == "openai-key"

    def test_get_key_censys(self):
        config = APIKeyConfig(censys_id="censys-id", censys_secret="censys-secret")
        assert config.get_key("censys_id") == "censys-id"
        assert config.get_key("censys_secret") == "censys-secret"

    def test_get_key_unknown_provider(self):
        config = APIKeyConfig()
        assert config.get_key("unknown_provider") is None


class TestSecureConfigManager:
    """Tests for SecureConfigManager"""

    def test_init_creates_config_dir(self, tmp_path):
        """Test that init creates config directory"""
        config_dir = tmp_path / ".config" / "zen-ai-pentest"
        manager = SecureConfigManager(config_dir=config_dir)

        assert manager.config_dir.exists()
        assert manager.config_file == config_dir / "config.json"
        assert manager.encrypted_config == config_dir / "config.enc"

    def test_init_loads_dotenv(self, tmp_path):
        """Test that init loads .env file"""
        config_dir = tmp_path / ".config" / "zen-ai-pentest"
        config_dir.mkdir(parents=True)

        env_file = config_dir / ".env"
        env_file.write_text("TEST_VAR=value\n")

        with patch.dict(os.environ, {}, clear=True):
            SecureConfigManager(config_dir=config_dir)
            # dotenv should have loaded TEST_VAR
            assert os.getenv("TEST_VAR") == "value"

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_get_keyring_password_success(self):
        """Test getting password from keyring"""
        manager = SecureConfigManager()

        with patch("core.secure_config.keyring.get_password") as mock_get:
            mock_get.return_value = "secret-password"
            result = manager._get_keyring_password("test_key")

            assert result == "secret-password"
            mock_get.assert_called_once_with("zen-ai-pentest", "test_key")

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_get_keyring_password_failure(self):
        """Test keyring failure handling"""
        manager = SecureConfigManager()

        with patch("core.secure_config.keyring.get_password") as mock_get:
            mock_get.side_effect = Exception("Keyring error")
            result = manager._get_keyring_password("test_key")

            assert result is None

    @patch("core.secure_config.KEYRING_AVAILABLE", False)
    def test_get_keyring_password_not_available(self):
        """Test when keyring is not available"""
        manager = SecureConfigManager()
        result = manager._get_keyring_password("test_key")
        assert result is None

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_set_keyring_password_success(self):
        """Test setting password in keyring"""
        manager = SecureConfigManager()

        with patch("keyring.set_password") as mock_set:
            result = manager._set_keyring_password("test_key", "secret")

            assert result is True
            mock_set.assert_called_once_with("zen-ai-pentest", "test_key", "secret")

    @patch("core.secure_config.KEYRING_AVAILABLE", False)
    def test_set_keyring_password_not_available(self):
        """Test setting password when keyring not available"""
        manager = SecureConfigManager()
        result = manager._set_keyring_password("test_key", "secret")
        assert result is False

    def test_get_api_key_from_env(self, tmp_path):
        """Test getting API key from environment"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.dict(os.environ, {"ZEN_OPENAI_KEY": "env-openai-key"}):
            result = manager.get_api_key("openai")
            assert result == "env-openai-key"

    def test_get_api_key_from_env_alt_name(self, tmp_path):
        """Test getting API key with alternative env var name"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.dict(os.environ, {"OPENAI_KEY": "alt-openai-key"}):
            result = manager.get_api_key("openai")
            assert result == "alt-openai-key"

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_get_api_key_from_keyring(self, tmp_path):
        """Test getting API key from keyring"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(manager, "_get_keyring_password") as mock_get:
                mock_get.return_value = "keyring-secret"
                result = manager.get_api_key("openai")
                assert result == "keyring-secret"

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_get_api_key_skip_keyring(self, tmp_path):
        """Test getting API key with prefer_keyring=False"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.dict(os.environ, {"ZEN_OPENAI_KEY": "env-key"}):
            with patch.object(manager, "_get_keyring_password") as mock_get:
                mock_get.return_value = "keyring-key"
                result = manager.get_api_key("openai", prefer_keyring=False)
                # Should use env key even though keyring has different value
                assert result == "env-key"

    def test_get_api_key_not_found(self, tmp_path):
        """Test getting non-existent API key"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.dict(os.environ, {}, clear=True):
            result = manager.get_api_key("nonexistent")
            assert result is None

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_set_api_key_keyring(self, tmp_path):
        """Test setting API key in keyring"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.object(manager, "_set_keyring_password") as mock_set:
            mock_set.return_value = True
            result = manager.set_api_key("openai", "secret-key", storage="keyring")
            assert result is True
            mock_set.assert_called_once_with("openai_key", "secret-key")

    @patch("core.secure_config.CRYPTO_AVAILABLE", False)
    def test_set_api_key_encrypted_no_crypto(self, tmp_path):
        """Test setting encrypted key without crypto library"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        result = manager.set_api_key("openai", "secret", storage="encrypted")
        assert result is False

    def test_set_api_key_env(self, tmp_path):
        """Test setting API key in env file"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        result = manager.set_api_key("openai", "env-secret", storage="env")
        assert result is True

        env_file = config_dir / ".env"
        assert env_file.exists()
        content = env_file.read_text()
        assert "ZEN_OPENAI_KEY=env-secret" in content

    def test_set_api_key_env_update_existing(self, tmp_path):
        """Test updating existing env variable"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        # First set
        manager.set_api_key("openai", "old-secret", storage="env")
        # Update
        manager.set_api_key("openai", "new-secret", storage="env")

        env_file = config_dir / ".env"
        content = env_file.read_text()
        assert "ZEN_OPENAI_KEY=new-secret" in content
        assert "old-secret" not in content

    def test_set_api_key_invalid_storage(self, tmp_path):
        """Test setting key with invalid storage type"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        result = manager.set_api_key("openai", "secret", storage="invalid")
        assert result is False

    def test_list_configured_keys(self, tmp_path):
        """Test listing configured keys"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.object(manager, "get_api_key") as mock_get:

            def side_effect(provider):
                return "key" if provider in ["openai", "github"] else None

            mock_get.side_effect = side_effect
            result = manager.list_configured_keys()

            assert "openai" in result
            assert "github" in result
            assert "anthropic" not in result

    @patch("core.secure_config.KEYRING_AVAILABLE", True)
    def test_remove_api_key_keyring(self, tmp_path):
        """Test removing API key from keyring"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch("core.secure_config.keyring.delete_password") as mock_delete:
            result = manager.remove_api_key("openai")
            assert result is True
            mock_delete.assert_called_once_with("zen-ai-pentest", "openai_key")

    @patch("core.secure_config.KEYRING_AVAILABLE", False)
    def test_remove_api_key_encrypted(self, tmp_path):
        """Test removing API key from encrypted config"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        # Create encrypted config file
        encrypted_file = config_dir / "config.enc"
        encrypted_file.write_bytes(b"test-encrypted-data")

        # Create mock encrypted config
        with patch.object(manager, "_load_encrypted_config") as mock_load:
            with patch.object(manager, "_save_encrypted_config") as mock_save:
                mock_load.return_value = {
                    "openai": "secret",
                    "github": "token",
                }
                mock_save.return_value = True

                result = manager.remove_api_key("openai")
                assert result is True
                mock_save.assert_called_once_with({"github": "token"})


class TestDeriveKey:
    """Tests for key derivation"""

    @patch("core.secure_config.CRYPTO_AVAILABLE", True)
    def test_derive_key(self):
        """Test key derivation from password"""
        manager = SecureConfigManager()

        with patch("core.secure_config.PBKDF2HMAC") as mock_kdf:
            mock_instance = MagicMock()
            mock_instance.derive.return_value = b"derived_key"
            mock_kdf.return_value = mock_instance

            with patch("core.secure_config.base64.urlsafe_b64encode") as mock_b64:
                mock_b64.return_value = b"encoded_key"
                result = manager._derive_key("password", b"salt")

                assert result == b"encoded_key"


class TestEncryptedConfig:
    """Tests for encrypted config operations"""

    @patch("core.secure_config.CRYPTO_AVAILABLE", True)
    def test_load_encrypted_config_not_exists(self, tmp_path):
        """Test loading when encrypted config doesn't exist"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        result = manager._load_encrypted_config()
        assert result is None

    @patch("core.secure_config.CRYPTO_AVAILABLE", True)
    def test_load_encrypted_config_success(self, tmp_path):
        """Test successful loading of encrypted config"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        # Create encrypted file
        encrypted_file = config_dir / "config.enc"
        encrypted_file.write_bytes(b"salt" + b"encrypted_data")

        with patch.object(manager, "_get_keyring_password") as mock_get:
            with patch("core.secure_config.Fernet") as mock_fernet:
                mock_get.return_value = "master-password"

                mock_cipher = MagicMock()
                mock_cipher.decrypt.return_value = json.dumps({"openai": "key"}).encode()
                mock_fernet.return_value = mock_cipher

                with patch.object(manager, "_derive_key") as mock_derive:
                    mock_derive.return_value = b"derived_key"
                    result = manager._load_encrypted_config()

                    assert result == {"openai": "key"}

    @patch("core.secure_config.CRYPTO_AVAILABLE", True)
    def test_save_encrypted_config(self, tmp_path):
        """Test saving encrypted config"""
        config_dir = tmp_path / "config"
        manager = SecureConfigManager(config_dir=config_dir)

        with patch.object(manager, "_get_keyring_password") as mock_get:
            with patch.object(manager, "_set_keyring_password") as mock_set:
                with patch("core.secure_config.Fernet") as mock_fernet:
                    with patch.object(manager, "_derive_key") as mock_derive:
                        with patch("secrets.token_bytes") as mock_token:
                            mock_get.return_value = "master-password"
                            mock_set.return_value = True
                            mock_derive.return_value = b"derived_key"
                            mock_token.return_value = b"salt"

                            mock_cipher = MagicMock()
                            mock_cipher.encrypt.return_value = b"encrypted_data"
                            mock_fernet.return_value = mock_cipher

                            result = manager._save_encrypted_config({"openai": "key"})

                            assert result is True
                            encrypted_file = config_dir / "config.enc"
                            assert encrypted_file.exists()


class TestGetSecureConfig:
    """Tests for get_secure_config singleton"""

    def test_singleton(self):
        """Test that get_secure_config returns singleton"""
        config1 = get_secure_config()
        config2 = get_secure_config()
        assert config1 is config2


class TestMigratePlainConfig:
    """Tests for migrate_plain_config"""

    def test_migrate_nonexistent_file(self, tmp_path):
        """Test migrating non-existent file"""
        config_path = tmp_path / "nonexistent.json"
        result = migrate_plain_config(config_path)
        assert result is False

    def test_migrate_success(self, tmp_path):
        """Test successful migration"""
        config_path = tmp_path / "old_config.json"
        config_data = {
            "openai_key": "openai-secret",
            "anthropic_key": "anthropic-secret",
            "github_token": "github-secret",
        }
        config_path.write_text(json.dumps(config_data))

        with patch("core.secure_config.get_secure_config") as mock_get_config:
            mock_manager = MagicMock()
            mock_get_config.return_value = mock_manager
            mock_manager.set_api_key.return_value = True

            result = migrate_plain_config(config_path)

            assert result is True
            assert mock_manager.set_api_key.call_count == 3

            # Check backup was created
            backup_path = tmp_path / "old_config.json.backup"
            assert backup_path.exists()

    def test_migrate_failure(self, tmp_path):
        """Test migration failure handling"""
        config_path = tmp_path / "bad_config.json"
        config_path.write_text("not valid json")

        result = migrate_plain_config(config_path)
        assert result is False
