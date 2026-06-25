"""
Comprehensive Tests for Agent Models
Target: 90-100% Coverage

This module provides complete test coverage for models/agent_model.py including:
- AgentStatus, AgentRole, AgentPriority enums
- AgentCapabilities, AgentConfig models
- AgentState, AgentMessage models
- AgentRegistration, AgentHeartbeat models
- AgentTaskRequest, AgentTaskResult models
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest

# =============================================================================
# Enum Tests
# =============================================================================


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_all_enum_values_exist(self):
        """Test that all AgentStatus enum values are defined."""
        from models.agent_model import AgentStatus

        expected = {
            "IDLE",
            "INITIALIZING",
            "RUNNING",
            "PAUSED",
            "ERROR",
            "SHUTTING_DOWN",
            "TERMINATED",
        }
        actual = {e.name for e in AgentStatus}
        assert actual == expected

    def test_enum_values(self):
        """Test enum string values."""
        from models.agent_model import AgentStatus

        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.TERMINATED.value == "terminated"

    def test_enum_comparison(self):
        """Test enum value comparison."""
        from models.agent_model import AgentStatus

        assert AgentStatus.IDLE == AgentStatus.IDLE
        assert AgentStatus.IDLE != AgentStatus.RUNNING
        assert AgentStatus.IDLE.value == "idle"


class TestAgentRole:
    """Tests for AgentRole enum."""

    def test_all_enum_values_exist(self):
        """Test that all AgentRole enum values are defined."""
        from models.agent_model import AgentRole

        expected = {
            "RECON",
            "SCANNER",
            "EXPLOIT",
            "ANALYSIS",
            "REPORTER",
            "ORCHESTRATOR",
            "HYBRID",
        }
        actual = {e.name for e in AgentRole}
        assert actual == expected

    def test_enum_values(self):
        """Test enum string values."""
        from models.agent_model import AgentRole

        assert AgentRole.RECON.value == "recon"
        assert AgentRole.SCANNER.value == "scanner"
        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.HYBRID.value == "hybrid"


class TestAgentPriority:
    """Tests for AgentPriority enum."""

    def test_all_enum_values_exist(self):
        """Test that all AgentPriority enum values are defined."""
        from models.agent_model import AgentPriority

        expected = {"CRITICAL", "HIGH", "NORMAL", "LOW", "BACKGROUND"}
        actual = {e.name for e in AgentPriority}
        assert actual == expected

    def test_enum_values_are_integers(self):
        """Test that enum values are integers."""
        from models.agent_model import AgentPriority

        assert isinstance(AgentPriority.CRITICAL.value, int)
        assert AgentPriority.CRITICAL.value == 0
        assert AgentPriority.HIGH.value == 1
        assert AgentPriority.NORMAL.value == 2
        assert AgentPriority.LOW.value == 3
        assert AgentPriority.BACKGROUND.value == 4

    def test_priority_ordering(self):
        """Test that priorities can be compared."""
        from models.agent_model import AgentPriority

        assert AgentPriority.CRITICAL < AgentPriority.HIGH
        assert AgentPriority.HIGH < AgentPriority.NORMAL
        assert AgentPriority.NORMAL < AgentPriority.LOW
        assert AgentPriority.LOW < AgentPriority.BACKGROUND


# =============================================================================
# AgentCapabilities Tests
# =============================================================================


class TestAgentCapabilities:
    """Tests for AgentCapabilities model."""

    def test_default_values(self):
        """Test default capability values."""
        from models.agent_model import AgentCapabilities

        caps = AgentCapabilities()
        assert caps.web_scanning is False
        assert caps.network_scanning is False
        assert caps.exploit_execution is False
        assert caps.report_generation is False
        assert caps.osint_gathering is False
        assert caps.api_testing is False
        assert caps.cloud_scanning is False
        assert caps.wireless_testing is False

    def test_custom_values(self):
        """Test custom capability values."""
        from models.agent_model import AgentCapabilities

        caps = AgentCapabilities(
            web_scanning=True,
            network_scanning=True,
            report_generation=True,
        )
        assert caps.web_scanning is True
        assert caps.network_scanning is True
        assert caps.exploit_execution is False
        assert caps.report_generation is True

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        from models.agent_model import AgentCapabilities

        caps = AgentCapabilities(custom_capability=True)
        assert caps.custom_capability is True


# =============================================================================
# AgentConfig Tests
# =============================================================================


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_valid_config(self):
        """Test creating valid agent config."""
        from models.agent_model import AgentConfig, AgentRole

        config = AgentConfig(
            agent_id="test-agent-001",
            name="Test Agent",
            role=AgentRole.SCANNER,
        )
        assert config.agent_id == "test-agent-001"
        assert config.name == "Test Agent"
        assert config.role == AgentRole.SCANNER
        assert config.version == "1.0.0"

    def test_default_values(self):
        """Test default configuration values."""
        from models.agent_model import AgentConfig, AgentRole

        config = AgentConfig(
            agent_id="test-agent",
            name="Test",
            role=AgentRole.RECON,
        )
        assert config.max_concurrent_tasks == 3
        assert config.task_timeout_seconds == 300
        assert config.retry_attempts == 3
        assert config.auto_retry is True
        assert config.save_evidence is True
        assert config.notify_on_complete is False
        assert config.max_risk_level == "medium"
        assert config.allowed_targets == []
        assert config.blocked_targets == []

    def test_custom_values(self):
        """Test custom configuration values."""
        from models.agent_model import AgentConfig, AgentRole

        config = AgentConfig(
            agent_id="custom-agent",
            name="Custom Agent",
            role=AgentRole.EXPLOIT,
            version="2.1.0",
            max_concurrent_tasks=10,
            task_timeout_seconds=600,
            retry_attempts=5,
            auto_retry=False,
            save_evidence=False,
            notify_on_complete=True,
            max_risk_level="high",
            allowed_targets=["example.com", "test.com"],
            blocked_targets=["evil.com"],
        )
        assert config.version == "2.1.0"
        assert config.max_concurrent_tasks == 10
        assert config.task_timeout_seconds == 600
        assert config.retry_attempts == 5
        assert config.auto_retry is False
        assert config.max_risk_level == "high"
        assert "example.com" in config.allowed_targets

    def test_agent_id_validation_alphanumeric(self):
        """Test agent_id with valid characters."""
        from models.agent_model import AgentConfig, AgentRole

        valid_ids = [
            "agent123",
            "agent-123",
            "agent_123",
            "agent-123_test",
            "Agent123",
        ]

        for agent_id in valid_ids:
            config = AgentConfig(agent_id=agent_id, name="Test", role=AgentRole.RECON)
            assert config.agent_id == agent_id

    def test_agent_id_validation_invalid_characters(self):
        """Test agent_id with invalid characters."""
        from models.agent_model import AgentConfig, AgentRole

        invalid_ids = [
            "agent@123",
            "agent.123",
            "agent/123",
            "agent 123",
            "agent#123",
        ]

        for agent_id in invalid_ids:
            with pytest.raises(ValueError):
                AgentConfig(agent_id=agent_id, name="Test", role=AgentRole.RECON)

    def test_agent_id_min_length(self):
        """Test agent_id minimum length validation."""
        from models.agent_model import AgentConfig, AgentRole

        with pytest.raises(ValueError):
            AgentConfig(agent_id="ab", name="Test", role=AgentRole.RECON)

    def test_agent_id_max_length(self):
        """Test agent_id maximum length validation."""
        from models.agent_model import AgentConfig, AgentRole

        with pytest.raises(ValueError):
            AgentConfig(agent_id="x" * 65, name="Test", role=AgentRole.RECON)

    def test_name_min_length(self):
        """Test name minimum length validation."""
        from models.agent_model import AgentConfig, AgentRole

        with pytest.raises(ValueError):
            AgentConfig(agent_id="test-agent", name="", role=AgentRole.RECON)

    def test_version_pattern(self):
        """Test version pattern validation."""
        from models.agent_model import AgentConfig, AgentRole

        # Valid versions
        for version in ["1.0.0", "0.0.1", "10.20.30"]:
            config = AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                version=version,
            )
            assert config.version == version

        # Invalid versions
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                version="1.0",
            )

        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                version="invalid",
            )

    def test_max_concurrent_tasks_constraints(self):
        """Test max_concurrent_tasks constraints."""
        from models.agent_model import AgentConfig, AgentRole

        # Valid
        AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            max_concurrent_tasks=1,
        )
        AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            max_concurrent_tasks=20,
        )

        # Invalid
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                max_concurrent_tasks=0,
            )
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                max_concurrent_tasks=21,
            )

    def test_task_timeout_constraints(self):
        """Test task_timeout_seconds constraints."""
        from models.agent_model import AgentConfig, AgentRole

        # Valid
        AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            task_timeout_seconds=10,
        )
        AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            task_timeout_seconds=3600,
        )

        # Invalid
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                task_timeout_seconds=5,
            )
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                task_timeout_seconds=4000,
            )

    def test_retry_attempts_constraints(self):
        """Test retry_attempts constraints."""
        from models.agent_model import AgentConfig, AgentRole

        # Valid
        AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            retry_attempts=0,
        )
        AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            retry_attempts=10,
        )

        # Invalid
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                retry_attempts=-1,
            )
        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                retry_attempts=11,
            )

    def test_target_validation_invalid_chars(self):
        """Test target list validation with invalid characters."""
        from models.agent_model import AgentConfig, AgentRole

        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                allowed_targets=["example.com; rm -rf"],
            )

        with pytest.raises(ValueError):
            AgentConfig(
                agent_id="test",
                name="Test",
                role=AgentRole.RECON,
                blocked_targets=["example.com | cat /etc/passwd"],
            )

    def test_valid_target_list(self):
        """Test valid target lists."""
        from models.agent_model import AgentConfig, AgentRole

        config = AgentConfig(
            agent_id="test",
            name="Test",
            role=AgentRole.RECON,
            allowed_targets=["example.com", "192.168.1.1", "sub.test.com"],
            blocked_targets=["forbidden.com"],
        )
        assert len(config.allowed_targets) == 3
        assert len(config.blocked_targets) == 1


# =============================================================================
# AgentState Tests
# =============================================================================


class TestAgentState:
    """Tests for AgentState model."""

    def test_default_values(self):
        """Test default state values."""
        from models.agent_model import AgentState, AgentStatus

        state = AgentState()
        assert state.status == AgentStatus.IDLE
        assert state.current_task is None
        assert state.task_progress == 0
        assert state.tasks_completed == 0
        assert state.tasks_failed == 0
        assert state.total_runtime_seconds == 0
        assert state.started_at is None
        assert state.last_active_at is None
        assert state.memory_usage_mb is None
        assert state.cpu_percent is None

    def test_custom_values(self):
        """Test custom state values."""
        from models.agent_model import AgentState, AgentStatus

        now = datetime.now(timezone.utc)
        state = AgentState(
            status=AgentStatus.RUNNING,
            current_task="task-123",
            task_progress=50,
            tasks_completed=10,
            tasks_failed=2,
            total_runtime_seconds=3600,
            started_at=now,
            last_active_at=now,
            memory_usage_mb=512.5,
            cpu_percent=45.0,
        )
        assert state.status == AgentStatus.RUNNING
        assert state.current_task == "task-123"
        assert state.task_progress == 50
        assert state.tasks_completed == 10
        assert state.memory_usage_mb == 512.5
        assert state.cpu_percent == 45.0

    def test_task_progress_constraints(self):
        """Test task_progress constraints."""
        from models.agent_model import AgentState

        # Valid
        AgentState(task_progress=0)
        AgentState(task_progress=50)
        AgentState(task_progress=100)

        # Invalid
        with pytest.raises(ValueError):
            AgentState(task_progress=-1)
        with pytest.raises(ValueError):
            AgentState(task_progress=101)

    def test_cpu_percent_constraints(self):
        """Test cpu_percent constraints."""
        from models.agent_model import AgentState

        # Valid
        AgentState(cpu_percent=0)
        AgentState(cpu_percent=50)
        AgentState(cpu_percent=100)
        AgentState(cpu_percent=None)

        # Invalid
        with pytest.raises(ValueError):
            AgentState(cpu_percent=-1)
        with pytest.raises(ValueError):
            AgentState(cpu_percent=101)

    def test_metrics_constraints(self):
        """Test metrics non-negative constraints."""
        from models.agent_model import AgentState

        # Valid
        AgentState(tasks_completed=0, tasks_failed=0, total_runtime_seconds=0)

        # Invalid
        with pytest.raises(ValueError):
            AgentState(tasks_completed=-1)
        with pytest.raises(ValueError):
            AgentState(tasks_failed=-1)
        with pytest.raises(ValueError):
            AgentState(total_runtime_seconds=-1)

    def test_is_available(self):
        """Test is_available method."""
        from models.agent_model import AgentState, AgentStatus

        # Available states
        assert AgentState(status=AgentStatus.IDLE).is_available() is True
        assert AgentState(status=AgentStatus.RUNNING).is_available() is True

        # Unavailable states
        assert AgentState(status=AgentStatus.ERROR).is_available() is False
        assert AgentState(status=AgentStatus.TERMINATED).is_available() is False
        assert AgentState(status=AgentStatus.PAUSED).is_available() is False
        assert AgentState(status=AgentStatus.INITIALIZING).is_available() is False
        assert AgentState(status=AgentStatus.SHUTTING_DOWN).is_available() is False

    def test_update_activity(self):
        """Test update_activity method."""
        from models.agent_model import AgentState

        state = AgentState()
        assert state.last_active_at is None

        state.update_activity()
        assert state.last_active_at is not None
        # Should be very recent
        assert (datetime.now(timezone.utc) - state.last_active_at).total_seconds() < 1

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        from models.agent_model import AgentState

        state = AgentState(custom_metric=42)
        assert state.custom_metric == 42


# =============================================================================
# AgentMessage Tests
# =============================================================================


class TestAgentMessage:
    """Tests for AgentMessage model."""

    def test_valid_message(self):
        """Test creating valid agent message."""
        from models.agent_model import AgentMessage, AgentPriority

        msg = AgentMessage(
            message_id="msg-test-001",
            sender_id="agent-001",
            recipient_id="agent-002",
            message_type="task",
            priority=AgentPriority.HIGH,
            payload={"task": "scan", "target": "example.com"},
        )
        assert msg.message_id == "msg-test-001"
        assert msg.sender_id == "agent-001"
        assert msg.recipient_id == "agent-002"
        assert msg.message_type == "task"
        assert msg.priority == AgentPriority.HIGH
        assert msg.payload == {"task": "scan", "target": "example.com"}

    def test_default_values(self):
        """Test default message values."""
        from models.agent_model import AgentMessage, AgentPriority

        msg = AgentMessage(
            message_id="msg-test",
            sender_id="agent-001",
            message_type="status",
        )
        assert msg.priority == AgentPriority.NORMAL
        assert msg.payload == {}
        assert msg.recipient_id is None
        assert msg.correlation_id is None
        assert msg.ttl_seconds == 300
        assert msg.timestamp is not None

    def test_broadcast_message(self):
        """Test broadcast message (no recipient)."""
        from models.agent_model import AgentMessage

        msg = AgentMessage(
            message_id="msg-broadcast",
            sender_id="agent-001",
            recipient_id=None,
            message_type="control",
        )
        assert msg.recipient_id is None
        assert msg.is_broadcast() is True

    def test_message_id_constraints(self):
        """Test message_id constraints."""
        from models.agent_model import AgentMessage

        # Valid
        AgentMessage(message_id="x" * 8, sender_id="agent", message_type="task")
        AgentMessage(message_id="x" * 64, sender_id="agent", message_type="task")

        # Invalid - too short
        with pytest.raises(ValueError):
            AgentMessage(message_id="x" * 7, sender_id="agent", message_type="task")

        # Invalid - too long
        with pytest.raises(ValueError):
            AgentMessage(message_id="x" * 65, sender_id="agent", message_type="task")

    def test_sender_id_constraints(self):
        """Test sender_id constraints."""
        from models.agent_model import AgentMessage

        # Invalid - too short
        with pytest.raises(ValueError):
            AgentMessage(message_id="msg-test", sender_id="ab", message_type="task")

        # Invalid - too long
        with pytest.raises(ValueError):
            AgentMessage(message_id="msg-test", sender_id="x" * 65, message_type="task")

    def test_recipient_id_constraints(self):
        """Test recipient_id constraints."""
        from models.agent_model import AgentMessage

        # Invalid - too short
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg-test",
                sender_id="agent",
                recipient_id="ab",
                message_type="task",
            )

        # Invalid - too long
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg-test",
                sender_id="agent",
                recipient_id="x" * 65,
                message_type="task",
            )

    def test_message_type_validation(self):
        """Test message_type validation."""
        from models.agent_model import AgentMessage

        # Valid types
        for msg_type in ["task", "result", "status", "error", "control"]:
            AgentMessage(message_id="msg-test", sender_id="agent", message_type=msg_type)

        # Invalid type
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg-test",
                sender_id="agent",
                message_type="invalid",
            )

    def test_ttl_constraints(self):
        """Test ttl_seconds constraints."""
        from models.agent_model import AgentMessage

        # Valid
        AgentMessage(
            message_id="msg-test",
            sender_id="agent",
            message_type="task",
            ttl_seconds=0,
        )
        AgentMessage(
            message_id="msg-test",
            sender_id="agent",
            message_type="task",
            ttl_seconds=86400,
        )

        # Invalid - negative
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg-test",
                sender_id="agent",
                message_type="task",
                ttl_seconds=-1,
            )

        # Invalid - too large
        with pytest.raises(ValueError):
            AgentMessage(
                message_id="msg-test",
                sender_id="agent",
                message_type="task",
                ttl_seconds=86401,
            )

    def test_is_expired_with_zero_ttl(self):
        """Test is_expired with zero TTL (never expires)."""
        from models.agent_model import AgentMessage

        msg = AgentMessage(
            message_id="msg-test",
            sender_id="agent",
            message_type="task",
            ttl_seconds=0,
        )
        assert msg.is_expired() is False

    def test_is_expired_not_expired(self):
        """Test is_expired when not expired."""
        from models.agent_model import AgentMessage

        msg = AgentMessage(
            message_id="msg-test",
            sender_id="agent",
            message_type="task",
            ttl_seconds=300,
        )
        assert msg.is_expired() is False

    def test_is_expired_actually_expired(self):
        """Test is_expired when actually expired."""
        from models.agent_model import AgentMessage

        # Create message with timestamp in the past
        past_time = datetime.now(timezone.utc) - timedelta(seconds=400)
        msg = AgentMessage(
            message_id="msg-test",
            sender_id="agent",
            message_type="task",
            ttl_seconds=300,
            timestamp=past_time,
        )
        assert msg.is_expired() is True


# =============================================================================
# AgentRegistration Tests
# =============================================================================


class TestAgentRegistration:
    """Tests for AgentRegistration model."""

    def test_valid_registration(self):
        """Test creating valid agent registration."""
        from models.agent_model import (
            AgentCapabilities,
            AgentConfig,
            AgentRegistration,
            AgentRole,
            AgentState,
            AgentStatus,
        )

        registration = AgentRegistration(
            config=AgentConfig(
                agent_id="test-agent",
                name="Test Agent",
                role=AgentRole.SCANNER,
            ),
            capabilities=AgentCapabilities(web_scanning=True),
            state=AgentState(status=AgentStatus.IDLE),
            auth_token="x" * 32,
            hostname="test-host",
            ip_address="192.168.1.100",
            port=8080,
        )
        assert registration.config.agent_id == "test-agent"
        assert registration.capabilities.web_scanning is True
        assert registration.state.status == AgentStatus.IDLE
        assert registration.hostname == "test-host"
        assert registration.ip_address == "192.168.1.100"
        assert registration.port == 8080

    def test_default_values(self):
        """Test default registration values."""
        from models.agent_model import (
            AgentConfig,
            AgentRegistration,
            AgentRole,
        )

        registration = AgentRegistration(
            config=AgentConfig(
                agent_id="test-agent",
                name="Test Agent",
                role=AgentRole.RECON,
            ),
        )
        assert registration.capabilities is not None
        assert registration.state is not None
        assert registration.auth_token is None
        assert registration.hostname is None
        assert registration.ip_address is None
        assert registration.port is None

    def test_auth_token_min_length(self):
        """Test auth_token minimum length."""
        from models.agent_model import (
            AgentConfig,
            AgentRegistration,
            AgentRole,
        )

        # Valid - exactly 32 chars
        registration = AgentRegistration(
            config=AgentConfig(agent_id="test", name="Test", role=AgentRole.RECON),
            auth_token="x" * 32,
        )
        assert registration.auth_token is not None

        # Invalid - too short
        with pytest.raises(ValueError):
            AgentRegistration(
                config=AgentConfig(agent_id="test", name="Test", role=AgentRole.RECON),
                auth_token="x" * 31,
            )

    def test_port_constraints(self):
        """Test port constraints."""
        from models.agent_model import (
            AgentConfig,
            AgentRegistration,
            AgentRole,
        )

        # Valid
        AgentRegistration(
            config=AgentConfig(agent_id="test", name="Test", role=AgentRole.RECON),
            port=1,
        )
        AgentRegistration(
            config=AgentConfig(agent_id="test", name="Test", role=AgentRole.RECON),
            port=65535,
        )

        # Invalid
        with pytest.raises(ValueError):
            AgentRegistration(
                config=AgentConfig(agent_id="test", name="Test", role=AgentRole.RECON),
                port=0,
            )
        with pytest.raises(ValueError):
            AgentRegistration(
                config=AgentConfig(agent_id="test", name="Test", role=AgentRole.RECON),
                port=65536,
            )


# =============================================================================
# AgentHeartbeat Tests
# =============================================================================


class TestAgentHeartbeat:
    """Tests for AgentHeartbeat model."""

    def test_valid_heartbeat(self):
        """Test creating valid heartbeat."""
        from models.agent_model import AgentHeartbeat, AgentStatus

        heartbeat = AgentHeartbeat(
            agent_id="test-agent",
            status=AgentStatus.RUNNING,
            current_task="task-123",
            task_progress=75,
            healthy=True,
            message="All systems operational",
            memory_usage_mb=256.5,
            cpu_percent=30.0,
            disk_free_gb=100.0,
        )
        assert heartbeat.agent_id == "test-agent"
        assert heartbeat.status == AgentStatus.RUNNING
        assert heartbeat.task_progress == 75
        assert heartbeat.healthy is True
        assert heartbeat.memory_usage_mb == 256.5

    def test_default_values(self):
        """Test default heartbeat values."""
        from models.agent_model import AgentHeartbeat, AgentStatus

        heartbeat = AgentHeartbeat(
            agent_id="test-agent",
            status=AgentStatus.IDLE,
        )
        assert heartbeat.timestamp is not None
        assert heartbeat.current_task is None
        assert heartbeat.task_progress == 0
        assert heartbeat.healthy is True
        assert heartbeat.message is None
        assert heartbeat.memory_usage_mb is None
        assert heartbeat.cpu_percent is None
        assert heartbeat.disk_free_gb is None

    def test_task_progress_constraints(self):
        """Test task_progress constraints."""
        from models.agent_model import AgentHeartbeat, AgentStatus

        # Valid
        AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, task_progress=0)
        AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, task_progress=100)

        # Invalid
        with pytest.raises(ValueError):
            AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, task_progress=-1)
        with pytest.raises(ValueError):
            AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, task_progress=101)

    def test_cpu_percent_constraints(self):
        """Test cpu_percent constraints."""
        from models.agent_model import AgentHeartbeat, AgentStatus

        # Valid
        AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, cpu_percent=0)
        AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, cpu_percent=100)
        AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, cpu_percent=None)

        # Invalid
        with pytest.raises(ValueError):
            AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, cpu_percent=-1)
        with pytest.raises(ValueError):
            AgentHeartbeat(agent_id="test", status=AgentStatus.IDLE, cpu_percent=101)


# =============================================================================
# AgentTaskRequest Tests
# =============================================================================


class TestAgentTaskRequest:
    """Tests for AgentTaskRequest model."""

    def test_valid_task_request(self):
        """Test creating valid task request."""
        from models.agent_model import AgentPriority, AgentTaskRequest

        request = AgentTaskRequest(
            task_id="task-123",
            task_type="nmap_scan",
            target="example.com",
            parameters={"ports": "80,443", "flags": "-sV"},
            priority=AgentPriority.HIGH,
            timeout_seconds=600,
            depends_on=["task-001", "task-002"],
        )
        assert request.task_id == "task-123"
        assert request.task_type == "nmap_scan"
        assert request.target == "example.com"
        assert request.parameters == {"ports": "80,443", "flags": "-sV"}
        assert request.priority == AgentPriority.HIGH
        assert request.timeout_seconds == 600
        assert request.depends_on == ["task-001", "task-002"]

    def test_default_values(self):
        """Test default task request values."""
        from models.agent_model import AgentPriority, AgentTaskRequest

        request = AgentTaskRequest(
            task_id="task-123",
            task_type="scan",
        )
        assert request.target is None
        assert request.parameters == {}
        assert request.priority == AgentPriority.NORMAL
        assert request.timeout_seconds == 300
        assert request.depends_on == []

    def test_task_id_constraints(self):
        """Test task_id constraints."""
        from models.agent_model import AgentTaskRequest

        # Valid
        AgentTaskRequest(task_id="x" * 8, task_type="scan")
        AgentTaskRequest(task_id="x" * 64, task_type="scan")

        # Invalid - too short
        with pytest.raises(ValueError):
            AgentTaskRequest(task_id="x" * 7, task_type="scan")

        # Invalid - too long
        with pytest.raises(ValueError):
            AgentTaskRequest(task_id="x" * 65, task_type="scan")

    def test_task_type_constraints(self):
        """Test task_type constraints."""
        from models.agent_model import AgentTaskRequest

        # Valid
        AgentTaskRequest(task_id="task-valid", task_type="x" * 64)

        # Invalid - empty
        with pytest.raises(ValueError):
            AgentTaskRequest(task_id="task-valid", task_type="")

        # Invalid - too long
        with pytest.raises(ValueError):
            AgentTaskRequest(task_id="task-valid", task_type="x" * 65)

    def test_target_validation(self):
        """Test target validation."""
        from models.agent_model import AgentTaskRequest

        # Valid targets
        AgentTaskRequest(task_id="task-valid", task_type="scan", target="example.com")
        AgentTaskRequest(task_id="task-valid", task_type="scan", target="192.168.1.1")

        # Invalid - None is allowed
        AgentTaskRequest(task_id="task-valid", task_type="scan", target=None)

        # Invalid - dangerous characters
        with pytest.raises(ValueError):
            AgentTaskRequest(
                task_id="task-valid",
                task_type="scan",
                target="example.com; rm -rf",
            )
        with pytest.raises(ValueError):
            AgentTaskRequest(
                task_id="task-valid",
                task_type="scan",
                target="example.com | cat /etc/passwd",
            )
        with pytest.raises(ValueError):
            AgentTaskRequest(
                task_id="task-valid",
                task_type="scan",
                target="example.com & whoami",
            )
        with pytest.raises(ValueError):
            AgentTaskRequest(
                task_id="task-valid",
                task_type="scan",
                target="example.com$HOME",
            )

    def test_timeout_constraints(self):
        """Test timeout_seconds constraints."""
        from models.agent_model import AgentTaskRequest

        # Valid
        AgentTaskRequest(task_id="task-valid", task_type="scan", timeout_seconds=10)
        AgentTaskRequest(task_id="task-valid", task_type="scan", timeout_seconds=3600)

        # Invalid
        with pytest.raises(ValueError):
            AgentTaskRequest(task_id="task-valid", task_type="scan", timeout_seconds=5)
        with pytest.raises(ValueError):
            AgentTaskRequest(task_id="task-valid", task_type="scan", timeout_seconds=4000)


# =============================================================================
# AgentTaskResult Tests
# =============================================================================


class TestAgentTaskResult:
    """Tests for AgentTaskResult model."""

    def test_valid_task_result(self):
        """Test creating valid task result."""
        from models.agent_model import AgentTaskResult

        result = AgentTaskResult(
            task_id="task-123",
            agent_id="agent-001",
            success=True,
            status="completed",
            findings=[{"title": "Open port", "port": 80}],
            output="Scan completed successfully",
            execution_time_seconds=45.5,
            evidence_files=["/path/to/evidence.txt"],
            logs=["Starting scan...", "Scan complete"],
        )
        assert result.task_id == "task-123"
        assert result.agent_id == "agent-001"
        assert result.success is True
        assert result.status == "completed"
        assert len(result.findings) == 1
        assert result.output == "Scan completed successfully"

    def test_default_values(self):
        """Test default task result values."""
        from models.agent_model import AgentTaskResult

        result = AgentTaskResult(
            task_id="task-123",
            agent_id="agent-001",
            success=False,
            status="failed",
        )
        assert result.findings == []
        assert result.output is None
        assert result.error_message is None
        assert result.started_at is None
        assert result.execution_time_seconds is None
        assert result.evidence_files == []
        assert result.logs == []
        assert result.completed_at is not None

    def test_all_status_values(self):
        """Test all valid status values."""
        from models.agent_model import AgentTaskResult

        for status in ["completed", "failed", "cancelled", "timeout"]:
            result = AgentTaskResult(
                task_id="task",
                agent_id="agent",
                success=status == "completed",
                status=status,
            )
            assert result.status == status

    def test_invalid_status(self):
        """Test invalid status value."""
        from models.agent_model import AgentTaskResult

        with pytest.raises(ValueError):
            AgentTaskResult(
                task_id="task",
                agent_id="agent",
                success=True,
                status="invalid_status",
            )

    def test_calculate_duration(self):
        """Test calculate_duration method."""
        from models.agent_model import AgentTaskResult

        started = datetime.now(timezone.utc) - timedelta(seconds=60)
        completed = datetime.now(timezone.utc)

        result = AgentTaskResult(
            task_id="task",
            agent_id="agent",
            success=True,
            status="completed",
            started_at=started,
            completed_at=completed,
        )
        duration = result.calculate_duration()
        assert duration is not None
        assert pytest.approx(duration, abs=1) == 60.0

    def test_calculate_duration_no_started_at(self):
        """Test calculate_duration when started_at is None."""
        from models.agent_model import AgentTaskResult

        result = AgentTaskResult(
            task_id="task",
            agent_id="agent",
            success=True,
            status="completed",
            started_at=None,
        )
        duration = result.calculate_duration()
        assert duration is None

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed."""
        from models.agent_model import AgentTaskResult

        result = AgentTaskResult(
            task_id="task",
            agent_id="agent",
            success=True,
            status="completed",
            custom_field="custom_value",
        )
        assert result.custom_field == "custom_value"


# =============================================================================
# Integration Tests
# =============================================================================


class TestAgentModelIntegration:
    """Integration tests for agent models working together."""

    def test_full_agent_lifecycle(self):
        """Test a full agent lifecycle from registration to task completion."""
        from models.agent_model import (
            AgentCapabilities,
            AgentConfig,
            AgentMessage,
            AgentPriority,
            AgentRegistration,
            AgentRole,
            AgentState,
            AgentStatus,
            AgentTaskRequest,
            AgentTaskResult,
        )

        # 1. Create agent config
        config = AgentConfig(
            agent_id="scanner-001",
            name="Port Scanner Agent",
            role=AgentRole.SCANNER,
            max_concurrent_tasks=5,
        )

        # 2. Create capabilities
        capabilities = AgentCapabilities(
            network_scanning=True,
            web_scanning=True,
        )

        # 3. Create initial state
        state = AgentState(status=AgentStatus.IDLE)

        # 4. Register agent
        registration = AgentRegistration(
            config=config,
            capabilities=capabilities,
            state=state,
            hostname="scanner-host-01",
        )

        assert registration.config.agent_id == "scanner-001"
        assert registration.capabilities.network_scanning is True
        assert registration.state.is_available() is True

        # 5. Receive task assignment message
        assignment_msg = AgentMessage(
            message_id="msg-assign-001",
            sender_id="orchestrator",
            recipient_id="scanner-001",
            message_type="task",
            priority=AgentPriority.HIGH,
            payload={"task_id": "task-123"},
        )

        assert assignment_msg.recipient_id == "scanner-001"
        assert not assignment_msg.is_broadcast()

        # 6. Create task request
        task_request = AgentTaskRequest(
            task_id="task-123",
            task_type="nmap_scan",
            target="example.com",
            priority=AgentPriority.HIGH,
            timeout_seconds=600,
        )

        assert task_request.task_type == "nmap_scan"

        # 7. Update state to running
        state.status = AgentStatus.RUNNING
        state.current_task = "task-123"
        state.task_progress = 50
        state.update_activity()

        assert state.status == AgentStatus.RUNNING
        assert state.last_active_at is not None

        # 8. Complete task with result
        result = AgentTaskResult(
            task_id="task-123",
            agent_id="scanner-001",
            success=True,
            status="completed",
            findings=[{"port": 80, "service": "http"}],
            started_at=datetime.now(timezone.utc) - timedelta(seconds=120),
        )

        assert result.success is True
        assert len(result.findings) == 1
        assert result.calculate_duration() is not None

        # 9. Return to idle
        state.status = AgentStatus.IDLE
        state.current_task = None
        state.task_progress = 0
        state.tasks_completed += 1

        assert state.status == AgentStatus.IDLE
        assert state.tasks_completed == 1

    def test_agent_communication_flow(self):
        """Test agent communication message flow."""
        from models.agent_model import (
            AgentHeartbeat,
            AgentMessage,
            AgentPriority,
            AgentStatus,
        )

        # Status request (broadcast)
        status_request = AgentMessage(
            message_id="msg-status-req",
            sender_id="orchestrator",
            recipient_id=None,  # Broadcast
            message_type="status",
            priority=AgentPriority.NORMAL,
        )

        assert status_request.is_broadcast() is True

        # Status response
        status_response = AgentMessage(
            message_id="msg-status-resp",
            sender_id="agent-001",
            recipient_id="orchestrator",
            message_type="status",
            payload={"status": "idle", "tasks_completed": 10},
        )

        assert status_response.is_broadcast() is False

        # Heartbeat
        heartbeat = AgentHeartbeat(
            agent_id="agent-001",
            status=AgentStatus.IDLE,
            healthy=True,
            task_progress=0,
        )

        assert heartbeat.healthy is True

    def test_message_ttl_expiration(self):
        """Test message TTL expiration in communication flow."""
        from models.agent_model import AgentMessage

        # Old message
        old_msg = AgentMessage(
            message_id="msg-old-msg",
            sender_id="agent-001",
            recipient_id="agent-002",
            message_type="task",
            ttl_seconds=60,
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=120),
        )

        assert old_msg.is_expired() is True

        # Fresh message
        fresh_msg = AgentMessage(
            message_id="msg-fresh",
            sender_id="agent-001",
            recipient_id="agent-002",
            message_type="task",
            ttl_seconds=300,
        )

        assert fresh_msg.is_expired() is False
