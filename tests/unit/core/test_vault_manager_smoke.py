"""Smoke tests for core/vault_manager.py"""

from pathlib import Path

import pytest

from core.vault_manager import SecureVaultManager, SecurityError, VaultConfig, get_vault_manager


class TestVaultConfig:
    def test_defaults(self):
        config = VaultConfig()
        assert "obsidian-vault" in str(config.vault_path)
        assert ".secure" in str(config.encrypted_vault_path)
        assert ".config/gh" in str(config.github_config_path)

    def test_custom(self):
        config = VaultConfig(vault_path=Path("/tmp/custom-vault"))
        assert config.vault_path == Path("/tmp/custom-vault")


class TestSecureVaultManager:
    def test_init(self):
        vm = SecureVaultManager()
        assert vm._master_key is None
        assert vm._fernet is None
        assert vm._is_unlocked is False

    def test_is_unlocked_false(self):
        vm = SecureVaultManager()
        assert vm.is_unlocked() is False

    def test_get_credential_raises_when_locked(self):
        vm = SecureVaultManager()
        with pytest.raises(SecurityError, match="Vault is locked"):
            vm.get_credential("test_key")

    def test_store_credential_raises_when_locked(self):
        vm = SecureVaultManager()
        with pytest.raises(SecurityError, match="Vault is locked"):
            vm.store_credential("test_key", "test_value")


class TestGetVaultManager:
    def test_returns_singleton(self):
        vm1 = get_vault_manager()
        vm2 = get_vault_manager()
        assert vm1 is vm2

    def test_returns_secure_vault_manager(self):
        vm = get_vault_manager()
        assert isinstance(vm, SecureVaultManager)
