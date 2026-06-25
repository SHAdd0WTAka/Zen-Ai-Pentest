"""
Comprehensive tests for core/secure_config.py
Target: 90-100% Coverage

This module tests:
- Secure configuration management
- Configuration encryption/decryption
- Secret handling via keyring and env files
- Config validation
"""

import base64
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

# Now import the module under test
# Note: We import without stubbing to test with real dependencies when available
from core.secure_config import (
    CRYPTO_AVAILABLE,
    ENV_PREFIX,
    KEYRING_AVAILABLE,
    KEYRING_SERVICE,
    APIKeyConfig,
    SecureConfigManager,
    get_secure_config,
    migrate_plain_config,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    return tmp_path / "config"


@pytest.fixture
def manager(temp_config_dir):
    """Create a SecureConfigManager with temp directory."""
    with patch.object(Path, "home", return_value=temp_config_dir.parent):
        mgr = SecureConfigManager(config_dir=temp_config_dir)
        return mgr


@pytest.fixture(autouse=True)
def clear_singleton_cache():
    """Clear the singleton cache before each test."""
    get_secure_config.cache_clear()
    yield
    get_secure_config.cache_clear()


@pytest.fixture
def mock_crypto_available():
    """Mock cryptography as available."""
    from core.secure_config import CRYPTO_AVAILABLE

    original = CRYPTO_AVAILABLE
    with patch("core.secure_config.CRYPTO_AVAILABLE", True):
        yield
    # Restore original value
    import core.secure_config

    core.secure_config.CRYPTO_AVAILABLE = original


@pytest.fixture
def mock_keyring_available():
    """Mock keyring as available."""
    from core.secure_config import KEYRING_AVAILABLE

    original = KEYRING_AVAILABLE
    with patch("core.secure_config.KEYRING_AVAILABLE", True):
        yield
    # Restore original value
    import core.secure_config

    core.secure_config.KEYRING_AVAILABLE = original


# ============================================================================
# Tests for APIKeyConfig
# ============================================================================


class TestAPIKeyConfig:
    """Test APIKeyConfig dataclass."""

    def test_default_creation(self):
        """Test default creation with no values."""
        config = APIKeyConfig()
        assert config.openrouter_key is None
        assert config.openai_key is None
        assert config.anthropic_key is None
        assert config.github_token is None
        assert config.shodan_key is None
        assert config.censys_id is None
        assert config.censys_secret is None

    def test_creation_with_values(self):
        """Test creation with all values."""
        config = APIKeyConfig(
            openrouter_key="sk-or-test",
            openai_key="sk-openai-test",
            anthropic_key="sk-ant-test",
            github_token="ghp_test_token",
            shodan_key="shodan_api_key",
            censys_id="censys_id_val",
            censys_secret="censys_secret_val",
        )
        assert config.openrouter_key == "sk-or-test"
        assert config.openai_key == "sk-openai-test"
        assert config.anthropic_key == "sk-ant-test"
        assert config.github_token == "ghp_test_token"
        assert config.shodan_key == "shodan_api_key"
        assert config.censys_id == "censys_id_val"
        assert config.censys_secret == "censys_secret_val"

    def test_get_key_openrouter(self):
        """Test get_key for openrouter provider."""
        config = APIKeyConfig(openrouter_key="sk-or-test")
        assert config.get_key("openrouter") == "sk-or-test"

    def test_get_key_openai(self):
        """Test get_key for openai provider."""
        config = APIKeyConfig(openai_key="sk-test")
        assert config.get_key("openai") == "sk-test"

    def test_get_key_chatgpt_alias(self):
        """Test get_key for chatgpt alias returns openai key."""
        config = APIKeyConfig(openai_key="sk-test")
        assert config.get_key("chatgpt") == "sk-test"

    def test_get_key_anthropic(self):
        """Test get_key for anthropic provider."""
        config = APIKeyConfig(anthropic_key="sk-ant-test")
        assert config.get_key("anthropic") == "sk-ant-test"

    def test_get_key_claude_alias(self):
        """Test get_key for claude alias returns anthropic key."""
        config = APIKeyConfig(anthropic_key="sk-ant-test")
        assert config.get_key("claude") == "sk-ant-test"

    def test_get_key_github(self):
        """Test get_key for github provider."""
        config = APIKeyConfig(github_token="ghp_test")
        assert config.get_key("github") == "ghp_test"

    def test_get_key_shodan(self):
        """Test get_key for shodan provider."""
        config = APIKeyConfig(shodan_key="shodan_test")
        assert config.get_key("shodan") == "shodan_test"

    def test_get_key_censys_id(self):
        """Test get_key for censys_id provider."""
        config = APIKeyConfig(censys_id="id123")
        assert config.get_key("censys_id") == "id123"

    def test_get_key_censys_secret(self):
        """Test get_key for censys_secret provider."""
        config = APIKeyConfig(censys_secret="secret456")
        assert config.get_key("censys_secret") == "secret456"

    def test_get_key_unknown(self):
        """Test get_key for unknown provider returns None."""
        config = APIKeyConfig()
        assert config.get_key("unknown") is None

    def test_get_key_case_insensitive_upper(self):
        """Test get_key is case insensitive (uppercase)."""
        config = APIKeyConfig(openai_key="sk-test")
        assert config.get_key("OPENAI") == "sk-test"

    def test_get_key_case_insensitive_mixed(self):
        """Test get_key is case insensitive (mixed case)."""
        config = APIKeyConfig(openai_key="sk-test")
        assert config.get_key("OpenAI") == "sk-test"
        assert config.get_key("Anthropic") is None


# ============================================================================
# Tests for SecureConfigManager Initialization
# ============================================================================


class TestSecureConfigManagerInit:
    """Test SecureConfigManager initialization."""

    def test_default_init(self, tmp_path):
        """Test default initialization with home directory."""
        with patch.object(Path, "home", return_value=tmp_path):
            manager = SecureConfigManager()
            expected_dir = tmp_path / ".config" / "zen-ai-pentest"
            assert manager.config_dir == expected_dir
            assert manager.config_file == expected_dir / "config.json"
            assert manager.encrypted_config == expected_dir / "config.enc"

    def test_custom_config_dir(self, tmp_path):
        """Test custom config directory."""
        custom_dir = tmp_path / "custom_config"
        manager = SecureConfigManager(config_dir=custom_dir)

        assert manager.config_dir == custom_dir
        assert manager.config_file == custom_dir / "config.json"
        assert manager.encrypted_config == custom_dir / "config.enc"

    def test_init_creates_directory(self, tmp_path):
        """Test init creates config directory if it doesn't exist."""
        config_dir = tmp_path / "new_config_dir"
        assert not config_dir.exists()

        SecureConfigManager(config_dir=config_dir)

        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_init_with_existing_directory(self, tmp_path):
        """Test init with existing directory works fine."""
        config_dir = tmp_path / "existing"
        config_dir.mkdir()

        # Should not raise
        manager = SecureConfigManager(config_dir=config_dir)
        assert manager.config_dir == config_dir

    def test_init_loads_env_file_from_config_dir(self, tmp_path, monkeypatch):
        """Test init loads .env file from config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        env_file = config_dir / ".env"
        env_file.write_text("ZEN_TEST_KEY=from_config_dir\n")

        monkeypatch.delenv("ZEN_TEST_KEY", raising=False)

        with patch("core.secure_config.load_dotenv") as mock_load:
            SecureConfigManager(config_dir=config_dir)
            # Should be called twice: once for config dir, once for project root
            assert mock_load.call_count >= 1

    def test_init_loads_env_file_from_project_root(self, tmp_path):
        """Test init loads .env file from project root."""
        with patch("core.secure_config.load_dotenv") as mock_load:
            SecureConfigManager(config_dir=tmp_path)
            # Second call should be for project root
            calls = mock_load.call_args_list
            # Check that one of the calls is for Path(".env")
            has_project_root = any(str(call.args[0]) == ".env" for call in calls if call.args)
            assert has_project_root


# ============================================================================
# Tests for Keyring Operations
# ============================================================================


class TestKeyringOperations:
    """Test keyring password operations."""

    def test_get_keyring_password_when_not_available(self, manager):
        """Test _get_keyring_password returns None when keyring not available."""
        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            result = manager._get_keyring_password("test_key")
            assert result is None

    def test_get_keyring_password_success(self, manager, mock_keyring_available):
        """Test _get_keyring_password returns value from keyring."""
        with patch("core.secure_config.keyring.get_password", return_value="secret"):
            result = manager._get_keyring_password("test_key")
            assert result == "secret"

    def test_get_keyring_password_error(self, manager, mock_keyring_available):
        """Test _get_keyring_password handles keyring errors gracefully."""
        with patch(
            "core.secure_config.keyring.get_password",
            side_effect=Exception("Keyring error"),
        ):
            result = manager._get_keyring_password("test_key")
            assert result is None

    def test_set_keyring_password_when_not_available(self, manager, caplog):
        """Test _set_keyring_password returns False when keyring not available."""
        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            with caplog.at_level("WARNING"):
                result = manager._set_keyring_password("test_key", "password")
                assert result is False
                assert "Keyring not available" in caplog.text

    def test_set_keyring_password_success(self, manager, mock_keyring_available):
        """Test _set_keyring_password returns True on success."""
        with patch("core.secure_config.keyring.set_password") as mock_set:
            result = manager._set_keyring_password("test_key", "password")
            assert result is True
            mock_set.assert_called_once_with(KEYRING_SERVICE, "test_key", "password")

    def test_set_keyring_password_error(self, manager, mock_keyring_available, caplog):
        """Test _set_keyring_password handles errors gracefully."""
        with patch(
            "core.secure_config.keyring.set_password",
            side_effect=Exception("Keyring error"),
        ):
            with caplog.at_level("ERROR"):
                result = manager._set_keyring_password("test_key", "password")
                assert result is False
                assert "Failed to store" in caplog.text


# ============================================================================
# Tests for get_api_key Method
# ============================================================================


class TestGetApiKey:
    """Test get_api_key method with various sources."""

    def test_get_from_env_with_prefix(self, manager, monkeypatch):
        """Test getting key from environment variable with ZEN_ prefix."""
        monkeypatch.setenv("ZEN_OPENAI_KEY", "sk-env-prefixed")
        result = manager.get_api_key("openai")
        assert result == "sk-env-prefixed"

    def test_get_from_env_without_prefix(self, manager, monkeypatch):
        """Test getting key from environment variable without ZEN_ prefix."""
        monkeypatch.setenv("OPENAI_KEY", "sk-env-no-prefix")
        result = manager.get_api_key("openai")
        assert result == "sk-env-no-prefix"

    def test_env_with_prefix_takes_priority(self, manager, monkeypatch):
        """Test that ZEN_ prefixed env var takes priority."""
        monkeypatch.setenv("ZEN_OPENAI_KEY", "prefixed")
        monkeypatch.setenv("OPENAI_KEY", "no_prefix")
        result = manager.get_api_key("openai")
        assert result == "prefixed"

    def test_env_takes_priority_over_keyring(self, manager, monkeypatch, mock_keyring_available):
        """Test that environment takes priority over keyring."""
        monkeypatch.setenv("ZEN_OPENAI_KEY", "from_env")
        with patch.object(manager, "_get_keyring_password", return_value="from_keyring"):
            result = manager.get_api_key("openai")
            assert result == "from_env"

    def test_get_from_keyring(self, manager, mock_keyring_available):
        """Test getting key from keyring."""
        with patch.object(manager, "_get_keyring_password", return_value="sk-keyring") as mock_get:
            result = manager.get_api_key("openai")
            assert result == "sk-keyring"
            mock_get.assert_called_once_with("openai_key")

    def test_keyring_skipped_when_prefer_keyring_false(self, manager, mock_keyring_available):
        """Test keyring is skipped when prefer_keyring=False."""
        with patch.object(manager, "_get_keyring_password") as mock_get:
            result = manager.get_api_key("openai", prefer_keyring=False)
            mock_get.assert_not_called()

    def test_keyring_skipped_when_not_available(self, manager):
        """Test keyring is skipped when not available."""
        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            with patch.object(manager, "_get_keyring_password") as mock_get:
                result = manager.get_api_key("openai")
                # Should not call keyring methods
                mock_get.assert_not_called()

    def test_get_from_encrypted_config(self, manager, mock_crypto_available, monkeypatch):
        """Test getting key from encrypted config file."""
        monkeypatch.delenv("ZEN_OPENAI_KEY", raising=False)
        monkeypatch.delenv("OPENAI_KEY", raising=False)

        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"openai": "sk-encrypted"},
            ):
                result = manager.get_api_key("openai", prefer_keyring=False)
                assert result == "sk-encrypted"

    def test_no_key_found_returns_none(self, manager, monkeypatch):
        """Test returns None when no key is found anywhere."""
        monkeypatch.delenv("ZEN_OPENAI_KEY", raising=False)
        monkeypatch.delenv("OPENAI_KEY", raising=False)

        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            with patch.object(manager, "encrypted_config") as mock_encrypted:
                mock_encrypted.exists.return_value = False
                result = manager.get_api_key("nonexistent")
                assert result is None

    def test_get_api_key_logs_debug(self, manager, monkeypatch, caplog):
        """Test that get_api_key logs debug messages."""
        monkeypatch.setenv("ZEN_OPENAI_KEY", "sk-test")
        with caplog.at_level("DEBUG"):
            manager.get_api_key("openai")
            assert "Using API key for openai from environment" in caplog.text


# ============================================================================
# Tests for set_api_key Method
# ============================================================================


class TestSetApiKey:
    """Test set_api_key method with various storage options."""

    def test_set_to_keyring(self, manager, mock_keyring_available):
        """Test setting key to keyring storage."""
        with patch.object(manager, "_set_keyring_password", return_value=True) as mock_set:
            result = manager.set_api_key("openai", "sk-test", storage="keyring")
            assert result is True
            mock_set.assert_called_once_with("openai_key", "sk-test")

    def test_set_to_keyring_failure(self, manager, mock_keyring_available):
        """Test setting key to keyring when it fails."""
        with patch.object(manager, "_set_keyring_password", return_value=False):
            result = manager.set_api_key("openai", "sk-test", storage="keyring")
            assert result is False

    def test_set_to_env_file_new(self, manager, tmp_path):
        """Test setting key to new env file."""
        with patch("os.chmod") as mock_chmod:
            result = manager.set_api_key("openai", "sk-test", storage="env")
            assert result is True

            env_file = manager.config_dir / ".env"
            assert env_file.exists()
            content = env_file.read_text()
            assert "ZEN_OPENAI_KEY=sk-test" in content
            mock_chmod.assert_called_once()
            # Check permissions are set to 0o600
            assert mock_chmod.call_args[0][1] == 0o600

    def test_set_to_env_file_update_existing(self, manager):
        """Test updating existing key in env file."""
        env_file = manager.config_dir / ".env"
        env_file.write_text("ZEN_OPENAI_KEY=old_key\nZEN_OTHER_KEY=other\n")

        with patch("os.chmod"):
            result = manager.set_api_key("openai", "sk-new", storage="env")
            assert result is True

            content = env_file.read_text()
            assert "ZEN_OPENAI_KEY=sk-new" in content
            assert "ZEN_OTHER_KEY=other" in content
            assert "old_key" not in content

    def test_set_to_env_file_append_new(self, manager):
        """Test appending new key to existing env file."""
        env_file = manager.config_dir / ".env"
        env_file.write_text("ZEN_OTHER_KEY=other\n")

        with patch("os.chmod"):
            result = manager.set_api_key("openai", "sk-test", storage="env")
            assert result is True

            content = env_file.read_text()
            assert "ZEN_OPENAI_KEY=sk-test" in content
            assert "ZEN_OTHER_KEY=other" in content

    def test_set_to_encrypted(self, manager, mock_crypto_available):
        """Test setting key to encrypted storage."""
        with patch.object(manager, "_load_encrypted_config", return_value={}) as mock_load:
            with patch.object(manager, "_save_encrypted_config", return_value=True) as mock_save:
                result = manager.set_api_key("openai", "sk-test", storage="encrypted")
                assert result is True
                mock_load.assert_called_once()
                mock_save.assert_called_once_with({"openai": "sk-test"})

    def test_set_to_encrypted_crypto_not_available(self, manager, caplog):
        """Test encrypted storage when crypto not available."""
        with patch("core.secure_config.CRYPTO_AVAILABLE", False):
            with caplog.at_level("ERROR"):
                result = manager.set_api_key("openai", "sk-test", storage="encrypted")
                assert result is False
                assert "cryptography library required" in caplog.text

    def test_set_to_encrypted_with_existing_keys(self, manager, mock_crypto_available):
        """Test setting key to encrypted storage merges with existing keys."""
        existing = {"github": "ghp_existing"}
        with patch.object(manager, "_load_encrypted_config", return_value=existing):
            with patch.object(manager, "_save_encrypted_config", return_value=True) as mock_save:
                result = manager.set_api_key("openai", "sk-test", storage="encrypted")
                assert result is True
                expected = {"github": "ghp_existing", "openai": "sk-test"}
                mock_save.assert_called_once_with(expected)

    def test_set_invalid_storage(self, manager):
        """Test invalid storage option returns False."""
        result = manager.set_api_key("openai", "sk-test", storage="invalid")
        assert result is False


# ============================================================================
# Tests for Encrypted Config Operations
# ============================================================================


class TestEncryptedConfig:
    """Test encrypted configuration operations."""

    def test_derive_key(self, manager, mock_crypto_available):
        """Test _derive_key generates correct key format."""
        mock_kdf = MagicMock()
        mock_kdf.derive.return_value = b"derived_key_bytes"

        with patch("core.secure_config.PBKDF2HMAC", return_value=mock_kdf) as mock_kdf_class:
            salt = b"test_salt_16bytes"
            result = manager._derive_key("master_password", salt)

            # Should return base64 encoded key
            assert isinstance(result, bytes)
            mock_kdf_class.assert_called_once()
            mock_kdf.derive.assert_called_once_with(b"master_password")

    def test_load_encrypted_config_file_not_exists(self, manager):
        """Test _load_encrypted_config returns None when file doesn't exist."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = False
            result = manager._load_encrypted_config()
            assert result is None

    def test_load_encrypted_config_success(self, manager, mock_crypto_available):
        """Test _load_encrypted_config decrypts successfully."""
        salt = b"test_salt_16byte"
        encrypted_data = b"encrypted_content"
        decrypted_data = b'{"openai": "sk-test"}'

        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            mock_encrypted.read_bytes.return_value = salt + encrypted_data

            with patch.object(manager, "_get_keyring_password", return_value="master"):
                with patch.object(manager, "_derive_key", return_value=b"derived_key"):
                    mock_fernet = MagicMock()
                    mock_fernet.decrypt.return_value = decrypted_data
                    with patch("core.secure_config.Fernet", return_value=mock_fernet):
                        result = manager._load_encrypted_config()
                        assert result == {"openai": "sk-test"}

    def test_load_encrypted_config_no_master_password(self, manager, mock_crypto_available):
        """Test _load_encrypted_config returns None when no master password."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            with patch.object(manager, "_get_keyring_password", return_value=None):
                result = manager._load_encrypted_config()
                assert result is None

    def test_load_encrypted_config_decrypt_error(self, manager, mock_crypto_available, caplog):
        """Test _load_encrypted_config handles decrypt errors."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            mock_encrypted.read_bytes.return_value = b"invalid_data"

            with patch.object(manager, "_get_keyring_password", return_value="master"):
                with patch.object(manager, "_derive_key") as mock_derive:
                    mock_derive.side_effect = Exception("Decrypt failed")
                    with caplog.at_level("ERROR"):
                        result = manager._load_encrypted_config()
                        assert result is None
                        assert "Failed to decrypt config" in caplog.text

    def test_save_encrypted_config_new_master(self, manager, mock_crypto_available):
        """Test _save_encrypted_config creates new master password."""
        config = {"openai": "sk-test"}

        with patch.object(manager, "_get_keyring_password", return_value=None):
            with patch.object(manager, "_set_keyring_password", return_value=True):
                # Patch secrets module where it's used (in the function's namespace)
                mock_secrets = MagicMock()
                mock_secrets.token_urlsafe.return_value = "new_master"
                mock_secrets.token_bytes.return_value = b"new_salt_16bytes"
                with patch.dict("sys.modules", {"secrets": mock_secrets}):
                    with patch.object(manager, "_derive_key", return_value=b"derived_key"):
                        mock_fernet = MagicMock()
                        mock_fernet.encrypt.return_value = b"encrypted_data"
                        with patch(
                            "core.secure_config.Fernet",
                            return_value=mock_fernet,
                        ):
                            with patch("os.chmod"):
                                result = manager._save_encrypted_config(config)
                                assert result is True
                                # Verify encrypted config file was written
                                assert manager.encrypted_config.exists()

    def test_save_encrypted_config_existing_master(self, manager, mock_crypto_available):
        """Test _save_encrypted_config with existing master password."""
        config = {"openai": "sk-test"}

        mock_secrets = MagicMock()
        mock_secrets.token_bytes.return_value = b"salt_16bytes_1234"

        with patch.object(manager, "_get_keyring_password", return_value="existing_master"):
            with patch.dict("sys.modules", {"secrets": mock_secrets}):
                with patch.object(manager, "_derive_key", return_value=b"derived_key"):
                    mock_fernet = MagicMock()
                    mock_fernet.encrypt.return_value = b"encrypted_data"
                    with patch("core.secure_config.Fernet", return_value=mock_fernet):
                        with patch("os.chmod"):
                            result = manager._save_encrypted_config(config)
                            assert result is True
                            # Verify encrypted config file was written
                            assert manager.encrypted_config.exists()

    def test_save_encrypted_config_error(self, manager, mock_crypto_available, caplog):
        """Test _save_encrypted_config handles errors."""
        with patch.object(
            manager,
            "_get_keyring_password",
            side_effect=Exception("Keyring error"),
        ):
            with caplog.at_level("ERROR"):
                result = manager._save_encrypted_config({"openai": "sk"})
                assert result is False
                assert "Failed to encrypt config" in caplog.text

    def test_save_encrypted_config_sets_permissions(self, manager, mock_crypto_available):
        """Test _save_encrypted_config sets correct file permissions."""
        mock_secrets = MagicMock()
        mock_secrets.token_bytes.return_value = b"salt_16bytes_1234"

        with patch.object(manager, "_get_keyring_password", return_value="master"):
            with patch.dict("sys.modules", {"secrets": mock_secrets}):
                with patch.object(manager, "_derive_key", return_value=b"key"):
                    mock_fernet = MagicMock()
                    mock_fernet.encrypt.return_value = b"encrypted"
                    with patch("core.secure_config.Fernet", return_value=mock_fernet):
                        with patch("os.chmod") as mock_chmod:
                            manager._save_encrypted_config({})
                            mock_chmod.assert_called_once()
                            assert mock_chmod.call_args[0][1] == 0o600


# ============================================================================
# Tests for list_configured_keys Method
# ============================================================================


class TestListConfiguredKeys:
    """Test list_configured_keys method."""

    def test_list_empty(self, manager):
        """Test listing when no keys are configured."""
        with patch.object(manager, "get_api_key", return_value=None):
            result = manager.list_configured_keys()
            assert result == []

    def test_list_with_keys(self, manager):
        """Test listing with some configured keys."""
        configured = {"openai", "github", "shodan"}

        def mock_get_key(provider):
            return "key_value" if provider in configured else None

        with patch.object(manager, "get_api_key", side_effect=mock_get_key):
            result = manager.list_configured_keys()
            assert "openai" in result
            assert "github" in result
            assert "shodan" in result
            assert "anthropic" not in result
            assert "openrouter" not in result

    def test_list_all_providers_checked(self, manager):
        """Test that all provider names are checked."""
        checked_providers = []

        def mock_get_key(provider):
            checked_providers.append(provider)
            return None

        with patch.object(manager, "get_api_key", side_effect=mock_get_key):
            manager.list_configured_keys()
            assert "openai" in checked_providers
            assert "anthropic" in checked_providers
            assert "openrouter" in checked_providers
            assert "github" in checked_providers
            assert "shodan" in checked_providers


# ============================================================================
# Tests for remove_api_key Method
# ============================================================================


class TestRemoveApiKey:
    """Test remove_api_key method."""

    def test_remove_from_keyring_success(self, manager, mock_keyring_available):
        """Test removing key from keyring."""
        with patch("core.secure_config.keyring.delete_password") as mock_delete:
            result = manager.remove_api_key("openai")
            assert result is True
            mock_delete.assert_called_once_with(KEYRING_SERVICE, "openai_key")

    def test_remove_from_keyring_not_available(self, manager):
        """Test removing key when keyring not available."""
        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            # Should not raise
            result = manager.remove_api_key("openai")
            # Returns True because no error occurred
            assert result is True

    def test_remove_from_keyring_error(self, manager, mock_keyring_available):
        """Test removing key from keyring handles errors gracefully."""
        with patch(
            "core.secure_config.keyring.delete_password",
            side_effect=Exception("Delete failed"),
        ):
            # Should not raise
            result = manager.remove_api_key("openai")
            assert result is True

    def test_remove_from_encrypted_config(self, manager, mock_crypto_available):
        """Test removing key from encrypted config."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"openai": "sk", "other": "key"},
            ):
                with patch.object(manager, "_save_encrypted_config", return_value=True) as mock_save:
                    result = manager.remove_api_key("openai")
                    assert result is True
                    mock_save.assert_called_once_with({"other": "key"})

    def test_remove_from_encrypted_config_key_not_present(self, manager, mock_crypto_available):
        """Test removing key that's not in encrypted config - should not call save."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"other": "key"},
            ):
                with patch.object(manager, "_save_encrypted_config") as mock_save:
                    result = manager.remove_api_key("openai")
                    assert result is True
                    # When key is not present, save should NOT be called (optimization)
                    mock_save.assert_not_called()

    def test_remove_from_encrypted_config_save_fails(self, manager, mock_crypto_available):
        """Test removing key when encrypted save fails."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = True
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"openai": "sk"},
            ):
                with patch.object(manager, "_save_encrypted_config", return_value=False):
                    result = manager.remove_api_key("openai")
                    assert result is False

    def test_remove_from_encrypted_config_not_exists(self, manager):
        """Test removing key when encrypted config doesn't exist."""
        with patch.object(manager, "encrypted_config") as mock_encrypted:
            mock_encrypted.exists.return_value = False
            result = manager.remove_api_key("openai")
            assert result is True


# ============================================================================
# Tests for get_secure_config Singleton
# ============================================================================


class TestGetSecureConfig:
    """Test get_secure_config singleton function."""

    def test_returns_singleton(self):
        """Test that get_secure_config returns the same instance."""
        # Clear cache first
        get_secure_config.cache_clear()

        config1 = get_secure_config()
        config2 = get_secure_config()

        assert config1 is config2
        assert isinstance(config1, SecureConfigManager)

    def test_singleton_persists(self):
        """Test that singleton persists across multiple calls."""
        get_secure_config.cache_clear()

        config1 = get_secure_config()
        config3 = get_secure_config()
        config2 = get_secure_config()

        assert config1 is config2 is config3

    def test_cache_clear_works(self):
        """Test that cache clear creates new instance."""
        get_secure_config.cache_clear()
        config1 = get_secure_config()

        get_secure_config.cache_clear()
        config2 = get_secure_config()

        assert config1 is not config2
        assert isinstance(config1, SecureConfigManager)
        assert isinstance(config2, SecureConfigManager)


# ============================================================================
# Tests for migrate_plain_config
# ============================================================================


class TestMigratePlainConfig:
    """Test migrate_plain_config function."""

    def test_migrate_nonexistent_file(self, tmp_path):
        """Test migrating non-existent file returns False."""
        nonexistent = tmp_path / "nonexistent.json"
        result = migrate_plain_config(nonexistent)
        assert result is False

    def test_migrate_valid_config(self, tmp_path):
        """Test migrating valid config file."""
        config_file = tmp_path / "old_config.json"
        config_data = {
            "openai_key": "sk-openai",
            "anthropic_key": "sk-anthropic",
            "openrouter_key": "sk-openrouter",
            "github_token": "ghp_token",
            "shodan_key": "shodan_key",
            "other_setting": "ignored",  # Should be ignored
        }
        config_file.write_text(json.dumps(config_data))

        with patch("core.secure_config.get_secure_config") as mock_get:
            mock_manager = MagicMock()
            mock_manager.set_api_key.return_value = True
            mock_get.return_value = mock_manager

            result = migrate_plain_config(config_file)

            assert result is True
            assert mock_manager.set_api_key.call_count == 5

            # Verify each key was migrated
            calls = mock_manager.set_api_key.call_args_list
            providers_stored = {call.args[0] for call in calls}
            assert "openai" in providers_stored
            assert "anthropic" in providers_stored
            assert "openrouter" in providers_stored
            assert "github" in providers_stored
            assert "shodan" in providers_stored

    def test_migrate_creates_backup(self, tmp_path):
        """Test that migration creates backup of old config."""
        config_file = tmp_path / "old_config.json"
        config_file.write_text('{"openai_key": "sk-test"}')

        with patch("core.secure_config.get_secure_config") as mock_get:
            mock_manager = MagicMock()
            mock_manager.set_api_key.return_value = True
            mock_get.return_value = mock_manager

            migrate_plain_config(config_file)

            backup_path = config_file.with_suffix(".json.backup")
            assert backup_path.exists()
            assert json.loads(backup_path.read_text()) == {"openai_key": "sk-test"}
            assert not config_file.exists()

    def test_migrate_empty_config(self, tmp_path):
        """Test migrating empty config file."""
        config_file = tmp_path / "empty_config.json"
        config_file.write_text("{}")

        with patch("core.secure_config.get_secure_config") as mock_get:
            mock_manager = MagicMock()
            mock_manager.set_api_key.return_value = True
            mock_get.return_value = mock_manager

            result = migrate_plain_config(config_file)

            assert result is True
            # No API keys to migrate
            mock_manager.set_api_key.assert_not_called()

    def test_migrate_invalid_json(self, tmp_path, caplog):
        """Test migrating invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not valid json")

        with caplog.at_level("ERROR"):
            result = migrate_plain_config(config_file)
            assert result is False
            assert "Migration failed" in caplog.text

    def test_migrate_partial_keys(self, tmp_path):
        """Test migrating config with only some keys."""
        config_file = tmp_path / "partial.json"
        config_file.write_text('{"openai_key": "sk-test", "other": "value"}')

        with patch("core.secure_config.get_secure_config") as mock_get:
            mock_manager = MagicMock()
            mock_manager.set_api_key.return_value = True
            mock_get.return_value = mock_manager

            result = migrate_plain_config(config_file)

            assert result is True
            mock_manager.set_api_key.assert_called_once()
            assert mock_manager.set_api_key.call_args[0][0] == "openai"

    def test_migrate_storage_is_keyring(self, tmp_path):
        """Test that migrated keys are stored to keyring."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"openai_key": "sk-test"}')

        with patch("core.secure_config.get_secure_config") as mock_get:
            mock_manager = MagicMock()
            mock_manager.set_api_key.return_value = True
            mock_get.return_value = mock_manager

            migrate_plain_config(config_file)

            mock_manager.set_api_key.assert_called_once_with("openai", "sk-test", storage="keyring")


# ============================================================================
# Tests for Module Constants
# ============================================================================


class TestModuleConstants:
    """Test module-level constants."""

    def test_keyring_service_name(self):
        """Test KEYRING_SERVICE constant."""
        assert KEYRING_SERVICE == "zen-ai-pentest"

    def test_env_prefix(self):
        """Test ENV_PREFIX constant."""
        assert ENV_PREFIX == "ZEN_"

    def test_keyring_available_is_boolean(self):
        """Test KEYRING_AVAILABLE is a boolean."""
        assert isinstance(KEYRING_AVAILABLE, bool)

    def test_crypto_available_is_boolean(self):
        """Test CRYPTO_AVAILABLE is a boolean."""
        assert isinstance(CRYPTO_AVAILABLE, bool)


# ============================================================================
# Integration Tests
# ============================================================================


class TestEncryptedConfigBranches:
    """Test specific branches in encrypted config handling."""

    def test_get_api_key_crypto_not_available(self, manager, monkeypatch):
        """Test get_api_key skips encrypted when crypto not available."""
        monkeypatch.delenv("ZEN_OPENAI_KEY", raising=False)
        monkeypatch.delenv("OPENAI_KEY", raising=False)

        with patch("core.secure_config.CRYPTO_AVAILABLE", False):
            with patch("core.secure_config.KEYRING_AVAILABLE", False):
                with patch.object(manager, "encrypted_config") as mock_encrypted:
                    # Should not even check if encrypted config exists
                    mock_encrypted.exists.return_value = True
                    result = manager.get_api_key("openai")
                    assert result is None

    def test_get_api_key_encrypted_exists_but_provider_missing(self, manager, monkeypatch, mock_crypto_available):
        """Test get_api_key when encrypted config exists but provider not in it."""
        monkeypatch.delenv("ZEN_OPENAI_KEY", raising=False)
        monkeypatch.delenv("OPENAI_KEY", raising=False)

        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            with patch.object(manager, "encrypted_config") as mock_encrypted:
                mock_encrypted.exists.return_value = True
                # Encrypted config has other providers but not openai
                with patch.object(
                    manager,
                    "_load_encrypted_config",
                    return_value={"github": "ghp_token"},
                ):
                    result = manager.get_api_key("openai")
                    # Provider not in config, should return None
                    assert result is None

    def test_get_api_key_encrypted_load_returns_none(self, manager, monkeypatch, mock_crypto_available):
        """Test get_api_key when encrypted config load returns None."""
        monkeypatch.delenv("ZEN_OPENAI_KEY", raising=False)
        monkeypatch.delenv("OPENAI_KEY", raising=False)

        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            with patch.object(manager, "encrypted_config") as mock_encrypted:
                mock_encrypted.exists.return_value = True
                with patch.object(manager, "_load_encrypted_config", return_value=None):
                    result = manager.get_api_key("openai")
                    assert result is None


class TestImportErrorHandling:
    """Test handling of optional dependency import errors."""

    def test_keyring_import_error_sets_flag(self):
        """Test that ImportError for keyring sets KEYRING_AVAILABLE=False."""
        # We can't easily test the import-time exception handling without
        # complex module reloading, but we can verify the flag exists
        from core.secure_config import KEYRING_AVAILABLE

        assert isinstance(KEYRING_AVAILABLE, bool)

    def test_crypto_import_error_sets_flag(self):
        """Test that ImportError for cryptography sets CRYPTO_AVAILABLE=False."""
        from core.secure_config import CRYPTO_AVAILABLE

        assert isinstance(CRYPTO_AVAILABLE, bool)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_key_lifecycle(self, manager, mock_keyring_available):
        """Test full lifecycle: set, get, list, remove."""
        # Set key
        with patch.object(manager, "_set_keyring_password", return_value=True):
            assert manager.set_api_key("openai", "sk-lifecycle", storage="keyring") is True

        # Get key
        with patch.object(manager, "_get_keyring_password", return_value="sk-lifecycle"):
            assert manager.get_api_key("openai") == "sk-lifecycle"

        # List keys
        with patch.object(
            manager,
            "get_api_key",
            side_effect=lambda p: "key" if p == "openai" else None,
        ):
            keys = manager.list_configured_keys()
            assert "openai" in keys

    def test_priority_order(self, manager, monkeypatch, mock_keyring_available):
        """Test that priority order is respected: env > keyring > encrypted."""
        # Set up all three sources
        monkeypatch.setenv("ZEN_OPENAI_KEY", "from_env")

        with patch.object(manager, "_get_keyring_password", return_value="from_keyring"):
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"openai": "from_encrypted"},
            ):
                with patch.object(manager, "encrypted_config") as mock_encrypted:
                    mock_encrypted.exists.return_value = True

                    # Should get from env
                    result = manager.get_api_key("openai")
                    assert result == "from_env"

        # Clear env, should get from keyring
        monkeypatch.delenv("ZEN_OPENAI_KEY")
        with patch.object(manager, "_get_keyring_password", return_value="from_keyring"):
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"openai": "from_encrypted"},
            ):
                with patch.object(manager, "encrypted_config") as mock_encrypted:
                    mock_encrypted.exists.return_value = True

                    result = manager.get_api_key("openai")
                    assert result == "from_keyring"

        # Disable keyring, should get from encrypted
        with patch("core.secure_config.KEYRING_AVAILABLE", False):
            with patch.object(
                manager,
                "_load_encrypted_config",
                return_value={"openai": "from_encrypted"},
            ):
                with patch.object(manager, "encrypted_config") as mock_encrypted:
                    mock_encrypted.exists.return_value = True

                    result = manager.get_api_key("openai")
                    assert result == "from_encrypted"
