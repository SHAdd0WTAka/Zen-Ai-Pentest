"""
Unit tests for Audit Logger

Tests the core audit logging functionality including:
- Log entry creation
- Integrity verification
- Signature validation
- Chain of custody
"""

from datetime import datetime

import pytest

# Import audit components
try:
    from audit import AuditLogEntry, AuditLogger
    from audit.config import AuditConfig, EventCategory, LogLevel
except ImportError:
    import sys

    sys.path.insert(0, "../../..")
    from audit import AuditLogEntry, AuditLogger
    from audit.config import AuditConfig, EventCategory, LogLevel


class TestAuditLogEntry:
    """Test AuditLogEntry class"""

    def test_entry_creation(self):
        """Test basic entry creation"""
        entry = AuditLogEntry(
            id="test-123",
            timestamp=datetime.utcnow(),
            level="info",
            category="system",
            event_type="test_event",
            message="Test message",
        )

        assert entry.id == "test-123"
        assert entry.level == "info"
        assert entry.hash is not None

    def test_hash_calculation(self):
        """Test hash is calculated correctly"""
        entry = AuditLogEntry(
            id="test-123",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            level="info",
            category="system",
            event_type="test_event",
            message="Test message",
        )

        # Hash should be deterministic
        hash1 = entry._calculate_hash()
        hash2 = entry._calculate_hash()
        assert hash1 == hash2

        # Hash should be 64 chars (SHA-256)
        assert len(entry.hash) == 64

    def test_signature_verification(self):
        """Test signing and verification"""
        entry = AuditLogEntry(
            id="test-123",
            timestamp=datetime.utcnow(),
            level="info",
            category="system",
            event_type="test_event",
            message="Test message",
        )

        secret = "my-secret-key"
        signature = entry.sign(secret)

        assert entry.signature is not None
        assert len(signature) == 64  # SHA-256 hex

        # Verify correct signature
        assert entry.verify(secret) is True

        # Verify with wrong secret
        assert entry.verify("wrong-secret") is False

    def test_chain_verification(self):
        """Test chain of custody verification"""
        entry1 = AuditLogEntry(
            id="test-1",
            timestamp=datetime.utcnow(),
            level="info",
            category="system",
            event_type="event1",
            message="First event",
        )

        entry2 = AuditLogEntry(
            id="test-2",
            timestamp=datetime.utcnow(),
            level="info",
            category="system",
            event_type="event2",
            message="Second event",
            previous_hash=entry1.hash,
        )

        # Valid chain
        assert entry2.verify_chain(entry1) is True

        # Invalid chain
        entry3 = AuditLogEntry(
            id="test-3",
            timestamp=datetime.utcnow(),
            level="info",
            category="system",
            event_type="event3",
            message="Third event",
            previous_hash="invalid-hash",
        )
        assert entry3.verify_chain(entry1) is False

        # First entry has no previous
        assert entry1.verify_chain(None) is True
        assert entry2.verify_chain(None) is False

    def test_to_dict(self):
        """Test serialization to dict"""
        entry = AuditLogEntry(
            id="test-123",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            level="info",
            category="system",
            event_type="test_event",
            message="Test message",
        )

        data = entry.to_dict()

        assert data["id"] == "test-123"
        assert data["timestamp"] == "2024-01-01T12:00:00"
        assert data["level"] == "info"

    def test_from_dict(self):
        """Test deserialization from dict"""
        data = {
            "id": "test-123",
            "timestamp": "2024-01-01T12:00:00",
            "level": "info",
            "category": "system",
            "event_type": "test_event",
            "message": "Test message",
            "hash": "abc123",
        }

        entry = AuditLogEntry.from_dict(data)

        assert entry.id == "test-123"
        assert entry.level == "info"
        assert entry.hash == "abc123"


class TestAuditLogger:
    """Test AuditLogger class"""

    @pytest.fixture
    async def logger(self):
        """Create test logger"""
        config = AuditConfig(async_logging=False, sign_logs=True)  # Synchronous for tests
        logger = AuditLogger(config)
        await logger.start()
        yield logger
        await logger.stop()

    @pytest.mark.asyncio
    async def test_log_creation(self, logger):
        """Test creating log entries"""
        entry = await logger.log(
            level=LogLevel.INFO,
            category=EventCategory.SYSTEM,
            event_type="test_event",
            message="Test message",
            user_id="user123",
        )

        assert entry.level == "info"
        assert entry.category == "system"
        assert entry.user_id == "user123"
        assert entry.signature is not None

    @pytest.mark.asyncio
    async def test_convenience_methods(self, logger):
        """Test convenience logging methods"""
        # Test all levels
        debug_entry = await logger.debug(EventCategory.SYSTEM, "debug_test", "Debug message")
        assert debug_entry.level == "debug"

        info_entry = await logger.info(EventCategory.SYSTEM, "info_test", "Info message")
        assert info_entry.level == "info"

        warning_entry = await logger.warning(EventCategory.SYSTEM, "warning_test", "Warning message")
        assert warning_entry.level == "warning"

        error_entry = await logger.error(EventCategory.SYSTEM, "error_test", "Error message")
        assert error_entry.level == "error"

        critical_entry = await logger.critical(EventCategory.SYSTEM, "critical_test", "Critical message")
        assert critical_entry.level == "critical"

        security_entry = await logger.security("security_test", "Security message")
        assert security_entry.level == "alert"
        assert security_entry.category == "security"

    @pytest.mark.asyncio
    async def test_query_logs(self, logger):
        """Test querying logs"""
        # Create some entries
        await logger.info(EventCategory.SYSTEM, "test1", "Message 1", user_id="user1")
        await logger.info(EventCategory.SYSTEM, "test2", "Message 2", user_id="user2")
        await logger.warning(EventCategory.SECURITY, "test3", "Message 3")

        # Query all
        all_logs = await logger.query(limit=10)
        assert len(all_logs) == 3

        # Query by level
        info_logs = await logger.query(level=LogLevel.INFO)
        assert len(info_logs) == 2

        # Query by user
        user1_logs = await logger.query(user_id="user1")
        assert len(user1_logs) == 1
        assert user1_logs[0].user_id == "user1"

    @pytest.mark.asyncio
    async def test_integrity_verification(self, logger):
        """Test integrity verification"""
        # Create entries
        await logger.info(EventCategory.SYSTEM, "test1", "Message 1")
        await logger.info(EventCategory.SYSTEM, "test2", "Message 2")

        result = await logger.verify_integrity()

        assert result["total_entries"] == 2
        assert result["valid_signatures"] == 2
        assert result["invalid_signatures"] == 0
        assert result["chain_breaks"] == 0

    @pytest.mark.asyncio
    async def test_export_json(self, logger):
        """Test JSON export"""
        await logger.info(EventCategory.SYSTEM, "test", "Test message")

        json_data = await logger.export(format="json")

        assert "test" in json_data
        assert "info" in json_data
        assert "Test message" in json_data

    @pytest.mark.asyncio
    async def test_export_csv(self, logger):
        """Test CSV export"""
        await logger.info(EventCategory.SYSTEM, "test", "Test message")

        csv_data = await logger.export(format="csv")

        assert "id,timestamp,level" in csv_data
        assert "info" in csv_data
        assert "system" in csv_data

    @pytest.mark.asyncio
    async def test_chain_integrity(self, logger):
        """Test chain of custody is maintained"""
        entry1 = await logger.info(EventCategory.SYSTEM, "test1", "Message 1")
        entry2 = await logger.info(EventCategory.SYSTEM, "test2", "Message 2")
        entry3 = await logger.info(EventCategory.SYSTEM, "test3", "Message 3")

        # Verify chain
        assert entry2.previous_hash == entry1.hash
        assert entry3.previous_hash == entry2.hash

        # Verify chain integrity
        assert entry2.verify_chain(entry1)
        assert entry3.verify_chain(entry2)


class TestAuditConfig:
    """Test AuditConfig class"""

    def test_default_config(self):
        """Test default configuration"""
        config = AuditConfig.default()

        assert config.sign_logs is True
        assert config.async_logging is True
        assert config.hash_algorithm == "sha256"
        assert config.buffer_size == 1000

    def test_strict_config(self):
        """Test strict compliance configuration"""
        config = AuditConfig.strict()

        assert config.async_logging is False  # Synchronous for strict
        assert config.sign_logs is True
        assert config.encrypt_sensitive is True
        assert config.compliance_mode == "strict"
        assert config.include_pii is False

    def test_retention_policies(self):
        """Test retention policy configuration"""
        config = AuditConfig.default()

        from audit.config import RetentionPolicy

        # Critical logs should be permanent
        assert config.retention_policies[LogLevel.CRITICAL] == RetentionPolicy.PERMANENT

        # Debug logs should be short
        assert config.retention_policies[LogLevel.DEBUG] == RetentionPolicy.SHORT


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
