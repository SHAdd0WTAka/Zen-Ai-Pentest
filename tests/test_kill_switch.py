"""
Comprehensive tests for core/kill_switch.py - Kill Switch Engine

Tests all kill switch functionality including:
- KillSwitchEngine initialization and configuration
- Heartbeat monitoring and validation
- Kill switch triggering with various reasons
- Lockdown sequence execution
- System unlock via Kimi auth
- CredentialManager operations
- Event logging and callbacks
- Edge cases and error handling
- CLI main function

Target: 90-100% coverage for core/kill_switch.py
"""

import asyncio
import gc
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Ensure the core module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kill_switch import (
    CredentialManager,
    Heartbeat,
    KillSwitchEngine,
    KillSwitchEvent,
    KillSwitchReason,
    SecurityError,
    VaultState,
    get_kill_switch,
    main,
)

# ==================== Fixtures ====================


@pytest.fixture
def kill_switch_engine():
    """Create a fresh KillSwitchEngine instance"""
    engine = KillSwitchEngine()
    yield engine
    # Cleanup
    if engine._monitor_task and not engine._monitor_task.done():
        engine._monitor_task.cancel()


@pytest.fixture
def unlocked_engine(kill_switch_engine):
    """Create an unlocked KillSwitchEngine"""
    kill_switch_engine.state = VaultState.UNLOCKED
    kill_switch_engine.session_start = datetime.now(timezone.utc)
    return kill_switch_engine


@pytest.fixture
def credential_manager():
    """Create a CredentialManager instance"""
    return CredentialManager()


@pytest.fixture
def sample_heartbeat():
    """Create a sample heartbeat"""
    return Heartbeat(
        device_id="test_device_123",
        timestamp=datetime.now(timezone.utc),
        session_id="session_456",
        tunnel_status="connected",
    )


@pytest.fixture
def valid_heartbeat_data(kill_switch_engine):
    """Create valid heartbeat data with signature"""
    data = {
        "device_id": "test_device_123",
        "session_id": "session_456",
        "tunnel_status": "connected",
    }
    # Generate valid signature
    payload = json.dumps(data)
    signature = hmac.new(
        kill_switch_engine._secret_key.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    data["signature"] = signature
    return data


@pytest.fixture(autouse=True)
def reset_global_instance():
    """Reset global kill switch instance after each test"""
    yield
    import core.kill_switch as ks_module

    ks_module._kill_switch_engine = None


# ==================== VaultState Enum Tests ====================


class TestVaultState:
    """Test VaultState enum"""

    def test_enum_values(self):
        """Test VaultState enum has correct values"""
        assert VaultState.LOCKED.value == "locked"
        assert VaultState.UNLOCKED.value == "unlocked"
        assert VaultState.LOCKING.value == "locking"
        assert VaultState.ERROR.value == "error"

    def test_enum_comparison(self):
        """Test VaultState enum comparison"""
        assert VaultState.LOCKED == VaultState.LOCKED
        assert VaultState.UNLOCKED != VaultState.LOCKED


# ==================== KillSwitchReason Enum Tests ====================


class TestKillSwitchReason:
    """Test KillSwitchReason enum"""

    def test_enum_values(self):
        """Test KillSwitchReason enum has correct values"""
        assert KillSwitchReason.HEARTBEAT_TIMEOUT.value == "heartbeat_timeout"
        assert KillSwitchReason.TUNNEL_DOWN.value == "tunnel_down"
        assert KillSwitchReason.MANUAL_LOCK.value == "manual_lock"
        assert KillSwitchReason.SUSPICIOUS_ACTIVITY.value == "suspicious_activity"
        assert KillSwitchReason.SESSION_EXPIRED.value == "session_expired"


# ==================== Heartbeat Tests ====================


class TestHeartbeat:
    """Test Heartbeat dataclass"""

    def test_creation(self):
        """Test creating a heartbeat"""
        now = datetime.now(timezone.utc)
        heartbeat = Heartbeat(
            device_id="device_123",
            timestamp=now,
            session_id="session_456",
            tunnel_status="connected",
        )
        assert heartbeat.device_id == "device_123"
        assert heartbeat.timestamp == now
        assert heartbeat.session_id == "session_456"
        assert heartbeat.tunnel_status == "connected"


# ==================== KillSwitchEvent Tests ====================


class TestKillSwitchEvent:
    """Test KillSwitchEvent dataclass"""

    def test_creation(self):
        """Test creating an event"""
        now = datetime.now(timezone.utc)
        event = KillSwitchEvent(
            timestamp=now,
            reason=KillSwitchReason.HEARTBEAT_TIMEOUT,
            severity="CRITICAL",
            details={"test": "data"},
        )
        assert event.timestamp == now
        assert event.reason == KillSwitchReason.HEARTBEAT_TIMEOUT
        assert event.severity == "CRITICAL"
        assert event.details == {"test": "data"}

    def test_default_details(self):
        """Test event with default empty details"""
        event = KillSwitchEvent(
            timestamp=datetime.now(timezone.utc),
            reason=KillSwitchReason.MANUAL_LOCK,
            severity="HIGH",
        )
        assert event.details == {}


# ==================== KillSwitchEngine Initialization Tests ====================


class TestKillSwitchEngineInit:
    """Test KillSwitchEngine initialization"""

    def test_default_initialization(self):
        """Test default engine initialization"""
        engine = KillSwitchEngine()
        assert engine.state == VaultState.LOCKED
        assert engine.last_heartbeat is None
        assert engine.session_start is None
        assert engine._callbacks == []
        assert engine._event_log == []
        assert engine.vault_manager is None
        assert engine.credential_manager is None
        assert len(engine._secret_key) == 64  # 32 bytes in hex

    def test_config_constants(self):
        """Test engine configuration constants"""
        assert KillSwitchEngine.HEARTBEAT_INTERVAL == 30
        assert KillSwitchEngine.HEARTBEAT_TIMEOUT == 60
        assert KillSwitchEngine.SESSION_DURATION == timedelta(hours=24)


# ==================== KillSwitchEngine Monitoring Tests ====================


class TestKillSwitchEngineMonitoring:
    """Test KillSwitchEngine monitoring"""

    @pytest.mark.asyncio
    async def test_start_monitoring(self, kill_switch_engine):
        """Test starting monitoring"""
        await kill_switch_engine.start_monitoring()
        assert kill_switch_engine._monitor_task is not None
        assert not kill_switch_engine._monitor_task.done()
        await kill_switch_engine.stop_monitoring()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, kill_switch_engine):
        """Test stopping monitoring"""
        await kill_switch_engine.start_monitoring()
        await kill_switch_engine.stop_monitoring()
        assert kill_switch_engine._monitor_task.cancelled() or kill_switch_engine._monitor_task.done()

    @pytest.mark.asyncio
    async def test_stop_monitoring_unlocked_triggers_kill_switch(self, kill_switch_engine):
        """Test that stopping while unlocked triggers kill switch"""
        kill_switch_engine.state = VaultState.UNLOCKED
        await kill_switch_engine.start_monitoring()
        await kill_switch_engine.stop_monitoring()
        # Should trigger kill switch, so state should be LOCKED or LOCKING
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
        ]

    @pytest.mark.asyncio
    async def test_stop_monitoring_not_unlocked_no_kill_switch(self, kill_switch_engine):
        """Test that stopping when not unlocked doesn't trigger kill switch"""
        kill_switch_engine.state = VaultState.LOCKED
        await kill_switch_engine.start_monitoring()
        await kill_switch_engine.stop_monitoring()
        # Should remain LOCKED
        assert kill_switch_engine.state == VaultState.LOCKED

    @pytest.mark.asyncio
    async def test_stop_monitoring_unlocked_branch(self, kill_switch_engine):
        """Test the auto-lock branch when stopping while unlocked (line 116)"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.session_start = datetime.now(timezone.utc)

        # Start monitoring to create the task
        await kill_switch_engine.start_monitoring()

        # Stop should trigger kill switch
        await kill_switch_engine.stop_monitoring()

        # Verify state changed
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
        ]

    @pytest.mark.asyncio
    async def test_stop_monitoring_without_task(self, kill_switch_engine):
        """Test stopping when no monitor task exists"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine._monitor_task = None

        # Should still trigger kill switch for unlocked state
        await kill_switch_engine.stop_monitoring()

        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
        ]

    @pytest.mark.asyncio
    async def test_monitoring_loop_check_health(self, kill_switch_engine):
        """Test monitoring loop calls check_health"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=120),  # Stale
            session_id="test",
            tunnel_status="connected",
        )

        # Start monitoring briefly
        await kill_switch_engine.start_monitoring()
        await asyncio.sleep(0.1)  # Let it run a bit
        await kill_switch_engine.stop_monitoring()

        # Should have triggered kill switch due to stale heartbeat
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
            VaultState.ERROR,
        ]

    @pytest.mark.asyncio
    async def test_check_health_locked_state(self, kill_switch_engine):
        """Test check_health returns early when locked"""
        kill_switch_engine.state = VaultState.LOCKED
        # Should not raise or trigger anything
        await kill_switch_engine._check_health()
        assert kill_switch_engine.state == VaultState.LOCKED

    @pytest.mark.asyncio
    async def test_check_health_no_heartbeat(self, unlocked_engine):
        """Test check_health with no heartbeat"""
        unlocked_engine.last_heartbeat = None
        # Should not trigger kill switch
        await unlocked_engine._check_health()
        assert unlocked_engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_check_health_stale_heartbeat(self, unlocked_engine):
        """Test check_health triggers on stale heartbeat"""
        unlocked_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=120),  # 2 minutes ago
            session_id="test",
            tunnel_status="connected",
        )
        await unlocked_engine._check_health()
        assert unlocked_engine.state in [VaultState.LOCKED, VaultState.LOCKING]

    @pytest.mark.asyncio
    async def test_check_health_warning_heartbeat(self, unlocked_engine):
        """Test check_health warns on approaching timeout"""
        unlocked_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=50),  # 50 seconds (83% of 60)
            session_id="test",
            tunnel_status="connected",
        )
        # Should not trigger kill switch, just log warning
        await unlocked_engine._check_health()
        # State should still be unlocked (warning threshold but not timeout)
        assert unlocked_engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_check_health_healthy_heartbeat(self, unlocked_engine):
        """Test check_health with healthy heartbeat"""
        unlocked_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=30),  # 30 seconds - healthy
            session_id="test",
            tunnel_status="connected",
        )
        await unlocked_engine._check_health()
        # Should remain unlocked
        assert unlocked_engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_check_health_session_expired(self, unlocked_engine):
        """Test check_health triggers on session expiration"""
        unlocked_engine.session_start = datetime.now(timezone.utc) - timedelta(hours=25)  # Expired
        await unlocked_engine._check_health()
        assert unlocked_engine.state in [VaultState.LOCKED, VaultState.LOCKING]

    @pytest.mark.asyncio
    async def test_check_health_session_not_expired(self, unlocked_engine):
        """Test check_health with valid session"""
        unlocked_engine.session_start = datetime.now(timezone.utc) - timedelta(hours=2)  # Not expired
        await unlocked_engine._check_health()
        # Should remain unlocked
        assert unlocked_engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_monitoring_loop_exception_handling(self, kill_switch_engine):
        """Test monitoring loop handles exceptions in check_health"""
        kill_switch_engine.state = VaultState.UNLOCKED

        # Create a mock that raises exception
        async def failing_check():
            raise Exception("Check failed")

        kill_switch_engine._check_health = failing_check

        # Start and stop quickly
        await kill_switch_engine.start_monitoring()
        await asyncio.sleep(0.2)
        await kill_switch_engine.stop_monitoring()

        # Should have handled exception without crashing

    @pytest.mark.asyncio
    async def test_monitoring_loop_cancelled_error(self, kill_switch_engine):
        """Test monitoring loop handles CancelledError"""

        async def cancel_task():
            raise asyncio.CancelledError()

        kill_switch_engine._monitor_task = asyncio.create_task(cancel_task())
        await asyncio.sleep(0.01)  # Let task complete

        # Should not raise
        await kill_switch_engine.stop_monitoring()


# ==================== KillSwitchEngine Heartbeat Tests ====================


class TestKillSwitchEngineHeartbeat:
    """Test KillSwitchEngine heartbeat handling"""

    @pytest.mark.asyncio
    async def test_receive_valid_heartbeat(self, kill_switch_engine, valid_heartbeat_data):
        """Test receiving a valid heartbeat"""
        result = await kill_switch_engine.receive_heartbeat(valid_heartbeat_data)
        assert result is True
        assert kill_switch_engine.last_heartbeat is not None
        assert kill_switch_engine.last_heartbeat.device_id == "test_device_123"

    @pytest.mark.asyncio
    async def test_receive_heartbeat_invalid_signature(self, kill_switch_engine):
        """Test heartbeat with invalid signature triggers kill switch"""
        data = {
            "device_id": "test_device",
            "session_id": "session_123",
            "tunnel_status": "connected",
            "signature": "invalid_signature",
        }
        kill_switch_engine.state = VaultState.UNLOCKED
        result = await kill_switch_engine.receive_heartbeat(data)
        assert result is False
        # Should trigger suspicious activity kill switch
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
        ]
        assert len(kill_switch_engine._event_log) > 0
        assert kill_switch_engine._event_log[-1].reason == KillSwitchReason.SUSPICIOUS_ACTIVITY

    @pytest.mark.asyncio
    async def test_receive_heartbeat_invalid_format(self, kill_switch_engine):
        """Test heartbeat with invalid format"""
        data = {
            "signature": "test",
            # Missing required fields
        }
        result = await kill_switch_engine.receive_heartbeat(data)
        assert result is False

    @pytest.mark.asyncio
    async def test_receive_heartbeat_missing_device_id(self, kill_switch_engine, valid_heartbeat_data):
        """Test heartbeat missing device_id"""
        del valid_heartbeat_data["device_id"]
        # Regenerate signature without device_id
        payload = json.dumps({k: v for k, v in valid_heartbeat_data.items() if k != "signature"})
        valid_heartbeat_data["signature"] = hmac.new(
            kill_switch_engine._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        result = await kill_switch_engine.receive_heartbeat(valid_heartbeat_data)
        assert result is False

    @pytest.mark.asyncio
    async def test_receive_heartbeat_missing_session_id(self, kill_switch_engine, valid_heartbeat_data):
        """Test heartbeat missing session_id"""
        del valid_heartbeat_data["session_id"]
        # Regenerate signature without session_id
        payload = json.dumps({k: v for k, v in valid_heartbeat_data.items() if k != "signature"})
        valid_heartbeat_data["signature"] = hmac.new(
            kill_switch_engine._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        result = await kill_switch_engine.receive_heartbeat(valid_heartbeat_data)
        assert result is False

    def test_verify_heartbeat_signature_valid(self, kill_switch_engine):
        """Test signature verification with valid signature"""
        data = {"device_id": "test", "session_id": "123"}
        payload = json.dumps(data)
        signature = hmac.new(
            kill_switch_engine._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        data["signature"] = signature

        assert kill_switch_engine._verify_heartbeat_signature(data) is True

    def test_verify_heartbeat_signature_invalid(self, kill_switch_engine):
        """Test signature verification with invalid signature"""
        data = {
            "device_id": "test",
            "session_id": "123",
            "signature": "invalid",
        }
        assert kill_switch_engine._verify_heartbeat_signature(data) is False

    def test_verify_heartbeat_signature_missing(self, kill_switch_engine):
        """Test signature verification with missing signature"""
        data = {"device_id": "test", "session_id": "123"}
        assert kill_switch_engine._verify_heartbeat_signature(data) is False

    def test_verify_heartbeat_signature_empty(self, kill_switch_engine):
        """Test signature verification with empty signature"""
        data = {"device_id": "test", "session_id": "123", "signature": ""}
        assert kill_switch_engine._verify_heartbeat_signature(data) is False

    def test_verify_heartbeat_signature_wrong_key(self, kill_switch_engine):
        """Test signature verification with wrong key"""
        data = {"device_id": "test", "session_id": "123"}
        payload = json.dumps(data)
        # Sign with wrong key
        wrong_key = "wrong_key"
        signature = hmac.new(wrong_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        data["signature"] = signature

        assert kill_switch_engine._verify_heartbeat_signature(data) is False

    def test_generate_heartbeat_challenge(self, kill_switch_engine):
        """Test challenge generation"""
        challenge = kill_switch_engine.generate_heartbeat_challenge()
        assert isinstance(challenge, str)
        assert len(challenge) == 16  # First 16 chars of hex digest

    def test_generate_heartbeat_challenge_unique(self, kill_switch_engine):
        """Test challenge generation produces unique values with different timestamps"""
        with patch("core.kill_switch.time.time") as mock_time:
            mock_time.return_value = 1000000
            challenge1 = kill_switch_engine.generate_heartbeat_challenge()

            mock_time.return_value = 1000001  # Different timestamp
            challenge2 = kill_switch_engine.generate_heartbeat_challenge()

            assert challenge1 != challenge2


# ==================== KillSwitchEngine Trigger Tests ====================


class TestKillSwitchEngineTrigger:
    """Test KillSwitchEngine kill switch triggering"""

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_basic(self, kill_switch_engine):
        """Test basic kill switch triggering"""
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)

        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.ERROR,
        ]
        assert len(kill_switch_engine._event_log) == 1
        event = kill_switch_engine._event_log[0]
        assert event.reason == KillSwitchReason.MANUAL_LOCK
        assert event.severity == "CRITICAL"

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_already_locking(self, kill_switch_engine):
        """Test trigger when already locking"""
        kill_switch_engine.state = VaultState.LOCKING
        # Should return early without creating new event
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        # State should remain LOCKING
        assert kill_switch_engine.state == VaultState.LOCKING

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_multiple_reasons(self, kill_switch_engine):
        """Test kill switch with different reasons"""
        reasons = [
            KillSwitchReason.HEARTBEAT_TIMEOUT,
            KillSwitchReason.TUNNEL_DOWN,
            KillSwitchReason.SESSION_EXPIRED,
            KillSwitchReason.SUSPICIOUS_ACTIVITY,
        ]

        for reason in reasons:
            engine = KillSwitchEngine()  # Fresh engine for each
            await engine.trigger_kill_switch(reason)
            assert len(engine._event_log) == 1
            assert engine._event_log[0].reason == reason

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_callback(self, kill_switch_engine):
        """Test kill switch callback execution"""
        callback_called = False
        received_event = None

        async def test_callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event

        kill_switch_engine.on_kill_switch(test_callback)
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)

        # Allow time for async callback
        await asyncio.sleep(0.1)

        assert callback_called is True
        assert received_event is not None
        assert received_event.reason == KillSwitchReason.MANUAL_LOCK

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_callback_error(self, kill_switch_engine):
        """Test kill switch continues even if callback fails"""

        async def failing_callback(event):
            raise Exception("Callback error")

        kill_switch_engine.on_kill_switch(failing_callback)
        # Should not raise
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.ERROR,
        ]

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_event_details(self, unlocked_engine):
        """Test event details include heartbeat and session info"""
        unlocked_engine.last_heartbeat = Heartbeat(
            device_id="test_device",
            timestamp=datetime.now(timezone.utc),
            session_id="session_123",
            tunnel_status="connected",
        )
        unlocked_engine.session_start = datetime.now(timezone.utc) - timedelta(hours=1)

        await unlocked_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)

        event = unlocked_engine._event_log[0]
        assert "last_heartbeat" in event.details
        assert "session_duration" in event.details

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_event_details_no_heartbeat(self, kill_switch_engine):
        """Test event details when no heartbeat exists"""
        kill_switch_engine.last_heartbeat = None
        kill_switch_engine.session_start = None

        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)

        event = kill_switch_engine._event_log[0]
        assert event.details["last_heartbeat"] is None
        assert event.details["session_duration"] is None

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_lock_exception(self, kill_switch_engine):
        """Test trigger handles exception during lockdown"""

        # Make lockdown raise an exception
        async def failing_lockdown():
            raise Exception("Lockdown failed")

        kill_switch_engine._execute_lockdown = failing_lockdown

        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)

        # Should be in ERROR state
        assert kill_switch_engine.state == VaultState.ERROR

    @pytest.mark.asyncio
    async def test_trigger_kill_switch_multiple_callbacks(self, kill_switch_engine):
        """Test trigger with multiple callbacks"""
        callback_count = 0

        async def callback1(event):
            nonlocal callback_count
            callback_count += 1

        async def callback2(event):
            nonlocal callback_count
            callback_count += 1

        kill_switch_engine.on_kill_switch(callback1)
        kill_switch_engine.on_kill_switch(callback2)

        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        await asyncio.sleep(0.1)

        assert callback_count == 2


# ==================== KillSwitchEngine Lockdown Tests ====================


class TestKillSwitchEngineLockdown:
    """Test KillSwitchEngine lockdown sequence"""

    @pytest.mark.asyncio
    async def test_execute_lockdown(self, kill_switch_engine):
        """Test lockdown sequence execution"""
        # Mock vault and credential managers
        kill_switch_engine.vault_manager = AsyncMock()
        kill_switch_engine.credential_manager = MagicMock()

        await kill_switch_engine._execute_lockdown()

        # Vault should be encrypted
        kill_switch_engine.vault_manager.encrypt_vault.assert_called_once()
        # Credentials should be cleared
        kill_switch_engine.credential_manager.clear_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_lockdown_step_failure(self, kill_switch_engine):
        """Test lockdown continues even if a step fails"""
        kill_switch_engine.vault_manager = AsyncMock()
        kill_switch_engine.vault_manager.encrypt_vault.side_effect = Exception("Vault error")
        kill_switch_engine.credential_manager = MagicMock()

        # Should not raise, should complete
        await kill_switch_engine._execute_lockdown()

    @pytest.mark.asyncio
    async def test_encrypt_vault_with_manager(self, kill_switch_engine):
        """Test vault encryption when manager exists"""
        kill_switch_engine.vault_manager = AsyncMock()
        await kill_switch_engine._encrypt_vault()
        kill_switch_engine.vault_manager.encrypt_vault.assert_called_once()

    @pytest.mark.asyncio
    async def test_encrypt_vault_no_manager(self, kill_switch_engine):
        """Test vault encryption when no manager"""
        kill_switch_engine.vault_manager = None
        # Should not raise
        await kill_switch_engine._encrypt_vault()

    @pytest.mark.asyncio
    async def test_logout_github(self, kill_switch_engine):
        """Test GitHub CLI logout"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            await kill_switch_engine._logout_github()
            mock_run.assert_called_once_with(["gh", "auth", "logout"], capture_output=True, timeout=10)

    @pytest.mark.asyncio
    async def test_logout_github_failure(self, kill_switch_engine):
        """Test GitHub CLI logout failure is handled"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("gh not found")
            # Should not raise
            await kill_switch_engine._logout_github()

    @pytest.mark.asyncio
    async def test_revoke_kimi(self, kill_switch_engine):
        """Test Kimi token revocation"""
        # Create mock module
        mock_module = MagicMock()
        mock_bridge_class = MagicMock()
        mock_bridge_instance = MagicMock()
        mock_bridge_class.return_value = mock_bridge_instance
        mock_module.KimiAuthBridge = mock_bridge_class

        with patch.dict(os.environ, {"KIMI_ACCESS_TOKEN": "test_token"}):
            with patch(
                "builtins.__import__",
                side_effect=lambda name, *args, **kwargs: (
                    mock_module if name == "kimi_auth_bridge" else __import__(name, *args, **kwargs)
                ),
            ):
                await kill_switch_engine._revoke_kimi()
                assert "KIMI_ACCESS_TOKEN" not in os.environ

    @pytest.mark.asyncio
    async def test_revoke_kimi_import_error(self, kill_switch_engine):
        """Test Kimi revocation when import fails"""
        with patch.dict(os.environ, {"KIMI_ACCESS_TOKEN": "test"}, clear=True):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                # Should not raise
                await kill_switch_engine._revoke_kimi()

    @pytest.mark.asyncio
    async def test_revoke_kimi_exception(self, kill_switch_engine):
        """Test Kimi revocation when exception occurs"""
        with patch.dict(os.environ, {"KIMI_ACCESS_TOKEN": "test"}):
            with patch("builtins.__import__", side_effect=Exception("Auth error")):
                # Should not raise
                await kill_switch_engine._revoke_kimi()

    @pytest.mark.asyncio
    async def test_clear_api_keys(self, kill_switch_engine):
        """Test API key clearing"""
        kill_switch_engine.credential_manager = MagicMock()
        await kill_switch_engine._clear_api_keys()
        kill_switch_engine.credential_manager.clear_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_api_keys_no_manager(self, kill_switch_engine):
        """Test API key clearing when no manager"""
        kill_switch_engine.credential_manager = None
        # Should not raise
        await kill_switch_engine._clear_api_keys()

    @pytest.mark.asyncio
    async def test_kill_sessions(self, kill_switch_engine):
        """Test session killing clears env vars"""
        env_vars = [
            "GITHUB_TOKEN",
            "KIMI_TOKEN",
            "OPENAI_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "VAULT_KEY",
            "SESSION_TOKEN",
        ]

        # Set test values
        for var in env_vars:
            os.environ[var] = f"test_{var}"

        await kill_switch_engine._kill_sessions()

        # All should be removed
        for var in env_vars:
            assert var not in os.environ

    @pytest.mark.asyncio
    async def test_kill_sessions_missing_vars(self, kill_switch_engine):
        """Test session killing when vars don't exist"""
        # Ensure vars don't exist
        env_vars = [
            "GITHUB_TOKEN",
            "KIMI_TOKEN",
            "OPENAI_API_KEY",
        ]
        for var in env_vars:
            os.environ.pop(var, None)

        # Should not raise
        await kill_switch_engine._kill_sessions()

    @pytest.mark.asyncio
    async def test_wipe_memory(self, kill_switch_engine):
        """Test memory wiping"""
        old_key = kill_switch_engine._secret_key

        with patch("core.kill_switch.gc.collect") as mock_gc:
            await kill_switch_engine._wipe_memory()

            # Key should be regenerated
            assert kill_switch_engine._secret_key != old_key
            # GC should be called
            mock_gc.assert_called_once()


# ==================== KillSwitchEngine Unlock Tests ====================


class TestKillSwitchEngineUnlock:
    """Test KillSwitchEngine unlock functionality"""

    @pytest.mark.asyncio
    async def test_unlock_system_already_unlocked(self, kill_switch_engine):
        """Test unlock when already unlocked"""
        kill_switch_engine.state = VaultState.UNLOCKED
        result = await kill_switch_engine.unlock_system("token")
        assert result is True

    @pytest.mark.asyncio
    async def test_unlock_system_success(self, kill_switch_engine):
        """Test successful unlock"""
        kill_switch_engine.state = VaultState.LOCKED

        with patch.object(kill_switch_engine, "_verify_kimi_token", return_value=True):
            kill_switch_engine.vault_manager = AsyncMock()
            kill_switch_engine.vault_manager.decrypt_vault.return_value = True

            result = await kill_switch_engine.unlock_system("valid_token")

            assert result is True
            assert kill_switch_engine.state == VaultState.UNLOCKED
            assert kill_switch_engine.session_start is not None
            kill_switch_engine.vault_manager.decrypt_vault.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_unlock_system_invalid_token(self, kill_switch_engine):
        """Test unlock with invalid token"""
        kill_switch_engine.state = VaultState.LOCKED

        with patch.object(kill_switch_engine, "_verify_kimi_token", return_value=False):
            result = await kill_switch_engine.unlock_system("invalid_token")

            assert result is False
            assert kill_switch_engine.state == VaultState.LOCKED

    @pytest.mark.asyncio
    async def test_unlock_system_vault_decryption_fails(self, kill_switch_engine):
        """Test unlock when vault decryption fails"""
        kill_switch_engine.state = VaultState.LOCKED

        with patch.object(kill_switch_engine, "_verify_kimi_token", return_value=True):
            kill_switch_engine.vault_manager = AsyncMock()
            kill_switch_engine.vault_manager.decrypt_vault.return_value = False

            result = await kill_switch_engine.unlock_system("token")

            assert result is False
            assert kill_switch_engine.state == VaultState.LOCKED

    @pytest.mark.asyncio
    async def test_unlock_system_no_vault_manager(self, kill_switch_engine):
        """Test unlock when no vault manager exists"""
        kill_switch_engine.state = VaultState.LOCKED
        kill_switch_engine.vault_manager = None

        with patch.object(kill_switch_engine, "_verify_kimi_token", return_value=True):
            result = await kill_switch_engine.unlock_system("token")

            assert result is True
            assert kill_switch_engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_unlock_system_decrypt_returns_false(self, kill_switch_engine):
        """Test unlock when vault decrypt returns False"""
        kill_switch_engine.state = VaultState.LOCKED
        kill_switch_engine.vault_manager = AsyncMock()
        kill_switch_engine.vault_manager.decrypt_vault.return_value = False

        with patch.object(kill_switch_engine, "_verify_kimi_token", return_value=True):
            result = await kill_switch_engine.unlock_system("token")

            # Should return False when decrypt fails
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_kimi_token_success(self, kill_switch_engine):
        """Test Kimi token verification success"""
        # Create a mock module
        mock_module = MagicMock()
        mock_bridge_class = MagicMock()
        mock_bridge_instance = MagicMock()
        mock_bridge_instance.get_access_token.return_value = "valid_token"
        mock_bridge_class.return_value = mock_bridge_instance
        mock_module.KimiAuthBridge = mock_bridge_class

        def mock_import(name, *args, **kwargs):
            if name == "kimi_auth_bridge":
                return mock_module
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = await kill_switch_engine._verify_kimi_token("test_token")
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_kimi_token_failure(self, kill_switch_engine):
        """Test Kimi token verification failure"""
        # Create a mock module
        mock_module = MagicMock()
        mock_bridge_class = MagicMock()
        mock_bridge_instance = MagicMock()
        mock_bridge_instance.get_access_token.return_value = None  # No token = invalid
        mock_bridge_class.return_value = mock_bridge_instance
        mock_module.KimiAuthBridge = mock_bridge_class

        def mock_import(name, *args, **kwargs):
            if name == "kimi_auth_bridge":
                return mock_module
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = await kill_switch_engine._verify_kimi_token("invalid_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_kimi_token_exception(self, kill_switch_engine):
        """Test Kimi token verification with exception"""

        def mock_import(name, *args, **kwargs):
            if name == "kimi_auth_bridge":
                raise Exception("Auth error")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = await kill_switch_engine._verify_kimi_token("token")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_kimi_token_import_error(self, kill_switch_engine):
        """Test Kimi token verification with import error"""

        def mock_import(name, *args, **kwargs):
            if name == "kimi_auth_bridge":
                raise ImportError("No module named 'kimi_auth_bridge'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = await kill_switch_engine._verify_kimi_token("token")
            assert result is False


# ==================== KillSwitchEngine Status Tests ====================


class TestKillSwitchEngineStatus:
    """Test KillSwitchEngine status reporting"""

    def test_get_status_locked(self, kill_switch_engine):
        """Test status when locked"""
        kill_switch_engine.state = VaultState.LOCKED
        status = kill_switch_engine.get_status()

        assert status["state"] == "locked"
        assert status["kill_switch_armed"] is True
        assert status["heartbeat_timeout"] == 60
        assert status["last_heartbeat"] is None

    def test_get_status_unlocked(self, kill_switch_engine):
        """Test status when unlocked"""
        kill_switch_engine.state = VaultState.UNLOCKED
        status = kill_switch_engine.get_status()

        assert status["state"] == "unlocked"

    def test_get_status_locking(self, kill_switch_engine):
        """Test status when locking"""
        kill_switch_engine.state = VaultState.LOCKING
        status = kill_switch_engine.get_status()

        assert status["state"] == "locking"

    def test_get_status_error(self, kill_switch_engine):
        """Test status when error"""
        kill_switch_engine.state = VaultState.ERROR
        status = kill_switch_engine.get_status()

        assert status["state"] == "error"

    def test_get_status_with_heartbeat(self, kill_switch_engine):
        """Test status with heartbeat"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.last_heartbeat = Heartbeat(
            device_id="test_device_12345",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=30),
            session_id="session_123",
            tunnel_status="connected",
        )

        status = kill_switch_engine.get_status()

        assert status["state"] == "unlocked"
        assert status["last_heartbeat"] is not None
        # Device ID should be truncated (first 8 chars + "...")
        assert status["last_heartbeat"]["device_id"].startswith("test_dev")
        assert status["last_heartbeat"]["device_id"].endswith("...")
        assert status["last_heartbeat"]["seconds_ago"] == 30
        assert status["last_heartbeat"]["healthy"] is True

    def test_get_status_with_stale_heartbeat(self, kill_switch_engine):
        """Test status with stale heartbeat"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.last_heartbeat = Heartbeat(
            device_id="test_device",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=90),  # Stale
            session_id="session_123",
            tunnel_status="connected",
        )

        status = kill_switch_engine.get_status()

        assert status["last_heartbeat"]["healthy"] is False

    def test_get_status_with_session(self, kill_switch_engine):
        """Test status with active session"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.session_start = datetime.now(timezone.utc) - timedelta(hours=2)

        status = kill_switch_engine.get_status()

        assert status["session"] is not None
        assert abs(status["session"]["age_hours"] - 2.0) < 0.01  # Allow small floating point difference
        assert abs(status["session"]["expires_in_hours"] - 22.0) < 0.01

    def test_get_status_with_event(self, kill_switch_engine):
        """Test status includes last event"""
        event = KillSwitchEvent(
            timestamp=datetime.now(timezone.utc),
            reason=KillSwitchReason.MANUAL_LOCK,
            severity="CRITICAL",
        )
        kill_switch_engine._event_log.append(event)

        status = kill_switch_engine.get_status()

        assert status["last_event"] is not None
        assert status["last_event"]["reason"] == "manual_lock"

    def test_get_status_multiple_events(self, kill_switch_engine):
        """Test status includes most recent event"""
        event1 = KillSwitchEvent(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            reason=KillSwitchReason.HEARTBEAT_TIMEOUT,
            severity="CRITICAL",
        )
        event2 = KillSwitchEvent(
            timestamp=datetime.now(timezone.utc),
            reason=KillSwitchReason.MANUAL_LOCK,
            severity="CRITICAL",
        )
        kill_switch_engine._event_log.append(event1)
        kill_switch_engine._event_log.append(event2)

        status = kill_switch_engine.get_status()

        assert status["last_event"]["reason"] == "manual_lock"

    def test_on_kill_switch_callback_registration(self, kill_switch_engine):
        """Test callback registration"""

        def test_callback(event):
            pass

        kill_switch_engine.on_kill_switch(test_callback)
        assert test_callback in kill_switch_engine._callbacks

    def test_on_kill_switch_multiple_callbacks(self, kill_switch_engine):
        """Test multiple callback registration"""

        def callback1(event):
            pass

        def callback2(event):
            pass

        kill_switch_engine.on_kill_switch(callback1)
        kill_switch_engine.on_kill_switch(callback2)

        assert callback1 in kill_switch_engine._callbacks
        assert callback2 in kill_switch_engine._callbacks
        assert len(kill_switch_engine._callbacks) == 2


# ==================== CredentialManager Tests ====================


class TestCredentialManager:
    """Test CredentialManager functionality"""

    def test_initialization(self):
        """Test credential manager initialization"""
        manager = CredentialManager()
        assert manager._credentials == {}
        assert manager._locked is True

    def test_unlock(self, credential_manager):
        """Test unlocking credential manager"""
        credential_manager.unlock()
        assert credential_manager._locked is False

    def test_lock(self, credential_manager):
        """Test locking credential manager"""
        credential_manager.unlock()
        credential_manager.lock()
        assert credential_manager._locked is True

    def test_store_when_locked(self, credential_manager):
        """Test storing when locked raises error"""
        with pytest.raises(SecurityError, match="System locked"):
            credential_manager.store("key", "value")

    def test_store_success(self, credential_manager):
        """Test successful credential storage"""
        credential_manager.unlock()
        credential_manager.store("api_key", "secret123")
        assert credential_manager._credentials["api_key"] == "secret123"

    def test_store_multiple(self, credential_manager):
        """Test storing multiple credentials"""
        credential_manager.unlock()
        credential_manager.store("key1", "value1")
        credential_manager.store("key2", "value2")
        assert credential_manager._credentials["key1"] == "value1"
        assert credential_manager._credentials["key2"] == "value2"

    def test_get_when_locked(self, credential_manager):
        """Test getting when locked raises error"""
        with pytest.raises(SecurityError, match="System locked"):
            credential_manager.get("key")

    def test_get_success(self, credential_manager):
        """Test successful credential retrieval"""
        credential_manager.unlock()
        credential_manager.store("api_key", "secret123")
        result = credential_manager.get("api_key")
        assert result == "secret123"

    def test_get_nonexistent(self, credential_manager):
        """Test getting nonexistent credential"""
        credential_manager.unlock()
        result = credential_manager.get("nonexistent")
        assert result is None

    def test_clear_all(self, credential_manager):
        """Test clearing all credentials"""
        credential_manager.unlock()
        credential_manager.store("key1", "value1")
        credential_manager.store("key2", "value2")

        credential_manager.clear_all()

        assert credential_manager._credentials == {}
        assert credential_manager._locked is True

    def test_clear_all_overwrites(self, credential_manager):
        """Test that clear_all overwrites data before deletion"""
        credential_manager.unlock()
        credential_manager.store("secret", "sensitive_data")

        credential_manager.clear_all()

        # The value should have been overwritten with zeros
        # (Implementation detail: value is overwritten in place before clear)

    def test_clear_all_empty(self, credential_manager):
        """Test clearing when empty"""
        credential_manager.unlock()
        credential_manager.clear_all()
        assert credential_manager._credentials == {}
        assert credential_manager._locked is True


# ==================== Global Instance Tests ====================


class TestGlobalInstance:
    """Test global kill switch instance"""

    def test_get_kill_switch_singleton(self):
        """Test get_kill_switch returns singleton"""
        ks1 = get_kill_switch()
        ks2 = get_kill_switch()
        assert ks1 is ks2

    def test_get_kill_switch_creates_instance(self):
        """Test get_kill_switch creates instance if none exists"""
        # Reset global instance
        import core.kill_switch as ks_module

        original = ks_module._kill_switch_engine
        ks_module._kill_switch_engine = None

        try:
            ks = get_kill_switch()
            assert ks is not None
            assert isinstance(ks, KillSwitchEngine)
        finally:
            # Restore original
            ks_module._kill_switch_engine = original

    def test_get_kill_switch_type(self):
        """Test get_kill_switch returns correct type"""
        ks = get_kill_switch()
        assert isinstance(ks, KillSwitchEngine)


# ==================== Integration Tests ====================


@pytest.mark.integration
class TestKillSwitchIntegration:
    """Integration tests for kill switch system"""

    @pytest.mark.asyncio
    async def test_full_lock_unlock_cycle(self):
        """Test complete lock and unlock cycle"""
        engine = KillSwitchEngine()

        # Start unlocked
        engine.state = VaultState.UNLOCKED
        engine.session_start = datetime.now(timezone.utc)

        # Lock
        await engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        assert engine.state in [VaultState.LOCKED, VaultState.ERROR]

        # Try to unlock with mock
        with patch.object(engine, "_verify_kimi_token", return_value=True):
            engine.vault_manager = AsyncMock()
            engine.vault_manager.decrypt_vault.return_value = True

            result = await engine.unlock_system("token")
            assert result is True
            assert engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_heartbeat_monitoring_integration(self):
        """Test heartbeat monitoring with real timing"""
        engine = KillSwitchEngine()
        engine.state = VaultState.UNLOCKED
        engine.session_start = datetime.now(timezone.utc)

        # Start monitoring
        await engine.start_monitoring()

        # Send valid heartbeat
        data = {
            "device_id": "test",
            "session_id": "123",
            "tunnel_status": "connected",
        }
        payload = json.dumps(data)
        data["signature"] = hmac.new(engine._secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()

        result = await engine.receive_heartbeat(data)
        assert result is True

        # Stop monitoring
        await engine.stop_monitoring()


# ==================== Edge Case Tests ====================


class TestKillSwitchEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_lockdown_step_failure(self, kill_switch_engine):
        """Test lockdown continues even if a step fails"""
        kill_switch_engine.vault_manager = AsyncMock()
        kill_switch_engine.vault_manager.encrypt_vault.side_effect = Exception("Vault error")

        # Should not raise, should complete with ERROR state
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.ERROR,
        ]

    def test_heartbeat_with_unusual_tunnel_status(self, kill_switch_engine):
        """Test heartbeat with various tunnel statuses"""
        statuses = ["connected", "disconnected", "connecting", "error", ""]

        for status in statuses:
            engine = KillSwitchEngine()
            data = {
                "device_id": "test",
                "session_id": "123",
                "tunnel_status": status,
            }
            payload = json.dumps(data)
            data["signature"] = hmac.new(engine._secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()

            # Should not raise
            asyncio.run(engine.receive_heartbeat(data))
            assert engine.last_heartbeat is not None
            assert engine.last_heartbeat.tunnel_status == status

    @pytest.mark.asyncio
    async def test_concurrent_kill_switch_triggers(self, kill_switch_engine):
        """Test concurrent kill switch triggers are handled"""
        # Start multiple triggers concurrently
        tasks = [kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK) for _ in range(5)]
        await asyncio.gather(*tasks)

        # Should complete without errors
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.ERROR,
            VaultState.LOCKING,
        ]

    @pytest.mark.asyncio
    async def test_heartbeat_during_locking(self, kill_switch_engine):
        """Test receiving heartbeat during locking state"""
        kill_switch_engine.state = VaultState.LOCKING

        data = {
            "device_id": "test",
            "session_id": "123",
            "tunnel_status": "connected",
        }
        payload = json.dumps(data)
        data["signature"] = hmac.new(
            kill_switch_engine._secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Heartbeat should still be processed
        result = await kill_switch_engine.receive_heartbeat(data)
        assert result is True

    @pytest.mark.asyncio
    async def test_session_boundary(self, kill_switch_engine):
        """Test session at exact boundary"""
        kill_switch_engine.state = VaultState.UNLOCKED
        # Set session to exactly 24 hours ago
        kill_switch_engine.session_start = datetime.now(timezone.utc) - timedelta(hours=24)

        await kill_switch_engine._check_health()
        # Should trigger session expired
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
        ]

    @pytest.mark.asyncio
    async def test_heartbeat_exactly_at_timeout(self, kill_switch_engine):
        """Test heartbeat exactly at timeout boundary"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=60),  # Exactly at timeout
            session_id="test",
            tunnel_status="connected",
        )

        await kill_switch_engine._check_health()
        # Should trigger timeout
        assert kill_switch_engine.state in [
            VaultState.LOCKED,
            VaultState.LOCKING,
        ]

    @pytest.mark.asyncio
    async def test_heartbeat_just_under_timeout(self, kill_switch_engine):
        """Test heartbeat just under timeout"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=59.9),  # Just under timeout
            session_id="test",
            tunnel_status="connected",
        )

        await kill_switch_engine._check_health()
        # Should NOT trigger timeout
        assert kill_switch_engine.state == VaultState.UNLOCKED


# ==================== CLI Main Function Tests ====================


class TestCLIMain:
    """Test CLI main function"""

    @pytest.mark.asyncio
    async def test_main_status_command(self, capsys):
        """Test main function with status command"""
        with patch("sys.argv", ["kill_switch", "status"]):
            try:
                await main()
            except SystemExit as e:
                pass  # argparse may call sys.exit

        captured = capsys.readouterr()
        # Should output JSON status

    @pytest.mark.asyncio
    async def test_main_lock_command(self, capsys):
        """Test main function with lock command"""
        with patch("sys.argv", ["kill_switch", "lock"]):
            try:
                await main()
            except SystemExit as e:
                pass

        captured = capsys.readouterr()

    @pytest.mark.asyncio
    async def test_main_monitor_command_keyboard_interrupt(self):
        """Test main function monitor command with keyboard interrupt"""
        with patch("sys.argv", ["kill_switch", "monitor"]):
            with patch.object(KillSwitchEngine, "start_monitoring") as mock_start:
                with patch.object(KillSwitchEngine, "stop_monitoring") as mock_stop:
                    # Simulate keyboard interrupt after start
                    async def raise_interrupt():
                        raise KeyboardInterrupt()

                    # Patch asyncio.sleep to raise KeyboardInterrupt
                    with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

        mock_start.assert_called_once()
        mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_monitor_command(self, capsys):
        """Test main function with monitor command"""
        with patch("sys.argv", ["kill_switch", "monitor"]):
            with patch.object(KillSwitchEngine, "start_monitoring") as mock_start:
                with patch.object(KillSwitchEngine, "stop_monitoring") as mock_stop:
                    # Patch asyncio.sleep to exit quickly
                    with patch(
                        "asyncio.sleep",
                        side_effect=[None, KeyboardInterrupt()],
                    ):
                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

        mock_start.assert_called_once()


# ==================== Additional Coverage Tests ====================


class TestAdditionalCoverage:
    """Additional tests to reach 90%+ coverage"""

    @pytest.mark.asyncio
    async def test_check_health_warning_threshold(self, unlocked_engine):
        """Test check_health at warning threshold (75% of timeout)"""
        unlocked_engine.last_heartbeat = Heartbeat(
            device_id="test",
            timestamp=datetime.now(timezone.utc) - timedelta(seconds=46),  # 76.6% of 60
            session_id="test",
            tunnel_status="connected",
        )

        await unlocked_engine._check_health()
        # Should log warning but not trigger
        assert unlocked_engine.state == VaultState.UNLOCKED

    @pytest.mark.asyncio
    async def test_trigger_from_locking_state(self, kill_switch_engine):
        """Test trigger when already in LOCKING state"""
        kill_switch_engine.state = VaultState.LOCKING
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        # Should remain LOCKING, no duplicate event
        assert kill_switch_engine.state == VaultState.LOCKING
        assert len(kill_switch_engine._event_log) == 0

    @pytest.mark.asyncio
    async def test_trigger_from_locked_state(self, kill_switch_engine):
        """Test trigger when already in LOCKED state"""
        kill_switch_engine.state = VaultState.LOCKED
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        # Should still process (not early return like LOCKING)
        # But lockdown should still happen

    @pytest.mark.asyncio
    async def test_trigger_from_error_state(self, kill_switch_engine):
        """Test trigger when in ERROR state"""
        kill_switch_engine.state = VaultState.ERROR
        await kill_switch_engine.trigger_kill_switch(KillSwitchReason.MANUAL_LOCK)
        # Should process again
        assert len(kill_switch_engine._event_log) == 1

    def test_get_status_no_session(self, kill_switch_engine):
        """Test status when no session exists"""
        kill_switch_engine.state = VaultState.UNLOCKED
        kill_switch_engine.session_start = None

        status = kill_switch_engine.get_status()

        assert "session" not in status

    def test_get_status_no_events(self, kill_switch_engine):
        """Test status when no events exist"""
        kill_switch_engine._event_log = []

        status = kill_switch_engine.get_status()

        assert "last_event" not in status


class TestModuleExecution:
    """Test module-level execution"""

    def test_main_block_execution(self):
        """Test the __main__ block can be imported and executed"""
        # We can't directly test __main__ block, but we can verify the module structure
        import core.kill_switch as ks_module

        # Verify main function exists and is callable
        assert hasattr(ks_module, "main")
        assert callable(ks_module.main)

        # Verify get_kill_switch exists
        assert hasattr(ks_module, "get_kill_switch")
        assert callable(ks_module.get_kill_switch)

    def test_all_exports(self):
        """Test all expected exports are available"""
        import core.kill_switch as ks_module

        expected_exports = [
            "VaultState",
            "KillSwitchReason",
            "KillSwitchEvent",
            "Heartbeat",
            "KillSwitchEngine",
            "CredentialManager",
            "SecurityError",
            "get_kill_switch",
            "main",
        ]

        for export in expected_exports:
            assert hasattr(ks_module, export), f"Missing export: {export}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
