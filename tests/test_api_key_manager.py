"""Tests for API Key Manager module"""

import os
import tempfile

import pytest

from modules.api_key_manager import APIKeyManager, KeyStatus


class TestAPIKeyManager:
    """Test API Key Manager functionality"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary key manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "api_keys.json")
            manager = APIKeyManager(storage_path=db_path)
            yield manager

    def test_init(self, temp_manager):
        """Test initialization"""
        assert temp_manager.name == "api_key_manager"
        assert temp_manager.version == "1.0.0"
        assert os.path.exists(temp_manager.storage_path.parent)

    def test_generate_key(self, temp_manager):
        """Test key generation"""
        key_id, plain_key = temp_manager.generate_key(name="Test Key", permissions=["read", "write"], created_by="test_user")

        assert key_id.startswith("zen_")
        assert plain_key.startswith("zen_")
        assert len(plain_key) > len(key_id)

        # Verify key was stored
        keys = temp_manager._load_keys()
        assert key_id in keys
        assert keys[key_id]["name"] == "Test Key"

    def test_validate_key_success(self, temp_manager):
        """Test successful key validation"""
        key_id, plain_key = temp_manager.generate_key(name="Test Key", permissions=["read", "write"])

        result = temp_manager.validate_key(plain_key)
        assert result is not None
        assert result.key_id == key_id
        assert "read" in result.permissions

    def test_validate_key_invalid(self, temp_manager):
        """Test invalid key validation"""
        result = temp_manager.validate_key("invalid_key_12345")
        assert result is None

    def test_validate_key_wrong_permission(self, temp_manager):
        """Test key validation with wrong permission"""
        key_id, plain_key = temp_manager.generate_key(name="Read Only Key", permissions=["read"])

        # Should fail - key only has "read", not "write"
        result = temp_manager.validate_key(plain_key, required_permission="write")
        assert result is None

    def test_revoke_key(self, temp_manager):
        """Test key revocation"""
        key_id, plain_key = temp_manager.generate_key(name="Key to Revoke", permissions=["read"])

        # Revoke
        assert temp_manager.revoke_key(key_id, "admin") is True

        # Should not validate anymore
        result = temp_manager.validate_key(plain_key)
        assert result is None

        # Verify status
        key = temp_manager._get_key_by_id(key_id)
        assert key.status == KeyStatus.REVOKED.value

    def test_revoke_nonexistent_key(self, temp_manager):
        """Test revoking non-existent key"""
        result = temp_manager.revoke_key("nonexistent_key", "admin")
        assert result is False

    def test_rotate_key(self, temp_manager):
        """Test key rotation"""
        old_key_id, old_plain_key = temp_manager.generate_key(name="Key to Rotate", permissions=["read", "admin"])

        # Rotate
        result = temp_manager.rotate_key(old_key_id, "admin")
        assert result is not None

        new_key_id, new_plain_key = result
        assert new_key_id != old_key_id
        assert new_plain_key != old_plain_key

        # Old key should be invalid
        assert temp_manager.validate_key(old_plain_key) is None

        # New key should work
        new_key_data = temp_manager.validate_key(new_plain_key)
        assert new_key_data is not None
        assert new_key_data.key_id == new_key_id

    def test_rotate_nonexistent_key(self, temp_manager):
        """Test rotating non-existent key"""
        result = temp_manager.rotate_key("nonexistent", "admin")
        assert result is None

    def test_list_keys(self, temp_manager):
        """Test listing keys"""
        # Create some keys
        temp_manager.generate_key("Key 1", ["read"])
        temp_manager.generate_key("Key 2", ["write"])
        temp_manager.generate_key("Key 3", ["admin"])

        keys = temp_manager.list_keys()
        assert len(keys) == 3

        # Check filtering by status
        active_keys = temp_manager.list_keys(status=KeyStatus.ACTIVE.value)
        assert len(active_keys) == 3

    def test_key_expiration(self, temp_manager):
        """Test key expiration"""
        # Create key that expires immediately
        key_id, plain_key = temp_manager.generate_key(
            name="Expiring Key",
            permissions=["read"],
            expires_days=-1,  # Already expired
        )

        # Should be invalid due to expiration
        result = temp_manager.validate_key(plain_key)
        assert result is None

        # Check status was updated
        key = temp_manager._get_key_by_id(key_id)
        assert key.status == KeyStatus.EXPIRED.value

    def test_audit_logging(self, temp_manager):
        """Test audit logging"""
        # Generate key (creates audit entry)
        key_id, plain_key = temp_manager.generate_key(name="Audited Key", permissions=["read"])

        # Validate key (creates audit entry)
        temp_manager.validate_key(plain_key)

        # Check audit log
        logs = temp_manager.get_audit_log(key_id=key_id)
        assert len(logs) >= 2  # create + validate

        # Check latest entry
        latest = logs[0]
        assert latest.action in ["key_created", "key_validated"]
        assert latest.key_id == key_id

    def test_cleanup_expired_keys(self, temp_manager):
        """Test cleanup of old expired keys"""
        # Create expired key
        key_id, _ = temp_manager.generate_key(
            name="Old Expired Key",
            permissions=["read"],
            expires_days=-60,  # Expired 60 days ago
        )

        # Manually set status to expired
        key = temp_manager._get_key_by_id(key_id)
        key.status = KeyStatus.EXPIRED.value
        temp_manager._save_key(key)

        # Cleanup
        removed = temp_manager.cleanup_expired_keys()
        assert removed == 1

        # Key should be gone
        assert temp_manager._get_key_by_id(key_id) is None

    def test_key_permissions(self, temp_manager):
        """Test various permissions"""
        key_id, plain_key = temp_manager.generate_key(name="Multi Permission Key", permissions=["read", "write", "delete"])

        # Should validate for each permission
        for perm in ["read", "write", "delete"]:
            result = temp_manager.validate_key(plain_key, required_permission=perm)
            assert result is not None, f"Failed for permission: {perm}"

        # Should fail for admin (not granted)
        result = temp_manager.validate_key(plain_key, required_permission="admin")
        assert result is None

    def test_key_metadata(self, temp_manager):
        """Test key metadata handling"""
        metadata = {"project": "test", "environment": "dev"}
        key_id, _ = temp_manager.generate_key(name="Metadata Key", permissions=["read"], metadata=metadata)

        key = temp_manager._get_key_by_id(key_id)
        assert key.metadata["project"] == "test"
        assert key.metadata["environment"] == "dev"

    def test_encryption_fallback(self, temp_manager):
        """Test encryption/decryption"""
        test_data = "sensitive_api_key_12345"

        encrypted = temp_manager._encrypt(test_data)
        decrypted = temp_manager._decrypt(encrypted)

        assert decrypted == test_data
        assert encrypted != test_data

    def test_hash_consistency(self, temp_manager):
        """Test key hashing is consistent"""
        key = "test_key_123"
        hash1 = temp_manager._hash_key(key)
        hash2 = temp_manager._hash_key(key)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_get_info(self, temp_manager):
        """Test module info"""
        info = temp_manager.get_info()
        assert info["name"] == "api_key_manager"
        assert "encryption" in info
        assert "version" in info
