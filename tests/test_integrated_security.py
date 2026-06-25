"""
Comprehensive tests for core/integrated_security.py - Integrated Security Manager

Tests all integrated security functionality including:
- IntegratedSecurityManager initialization
- Security component coordination (kill switch, temporal CA, vault)
- P2P connection handling
- Credential lifecycle management
- Emergency lockdown procedures
- Security status reporting

Target: 90-100% coverage for core/integrated_security.py
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest

# Ensure the core module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock P2PConnection before importing
sys.modules["p2p"] = MagicMock()
sys.modules["p2p.connection"] = MagicMock()
sys.modules["p2p.connection"].P2PConnection = MagicMock()

# Mock other potentially missing imports
sys.modules["kimi_auth_bridge"] = MagicMock()
sys.modules["core.credential_lifecycle"] = MagicMock()
sys.modules["core.vault_manager"] = MagicMock()
sys.modules["core.ssh_key_manager"] = MagicMock()

# Setup CredentialStatus for proper comparison
CredentialStatusMock = MagicMock()
CredentialStatusMock.ACTIVE = "ACTIVE"
CredentialStatusMock.REVOKED = "REVOKED"
sys.modules["core.credential_lifecycle"].CredentialStatus = CredentialStatusMock

from core.integrated_security import (
    IntegratedSecurityManager,
    SecurityError,
    SecurityStatus,
    get_security_manager,
)
from core.kill_switch import KillSwitchEvent, KillSwitchReason

# ==================== Mock Fixtures ====================


@pytest.fixture
def mock_kill_switch():
    """Create a mock KillSwitchEngine"""
    mock = MagicMock()
    mock.state = MagicMock()
    mock.state.value = "locked"
    mock.start_monitoring = AsyncMock()
    mock.stop_monitoring = AsyncMock()
    mock.trigger_kill_switch = AsyncMock()
    mock.get_status = MagicMock(
        return_value={
            "last_heartbeat": {"seconds_ago": 10},
            "session": {"age_hours": 1.5},
        }
    )
    mock.on_kill_switch = MagicMock()
    mock.receive_heartbeat = AsyncMock(return_value=True)
    mock.unlock_system = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_temporal_ca():
    """Create a mock KimiTemporalCA"""
    mock = MagicMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.issue_credential = AsyncMock(
        return_value=MagicMock(
            id="cred_123",
            value="secret_value",
            status=MagicMock(value="active"),
        )
    )
    mock.revoke_all = AsyncMock()
    mock.get_active = AsyncMock(return_value=[])
    mock.rotate_credential = AsyncMock()
    mock._credentials = {}
    return mock


@pytest.fixture
def mock_vault_manager():
    """Create a mock SecureVaultManager"""
    mock = MagicMock()
    mock.encrypt_vault = AsyncMock()
    mock.decrypt_vault = AsyncMock(return_value=True)
    mock.is_unlocked = MagicMock(return_value=False)
    mock.get_credential = MagicMock(return_value="secret_value")
    mock.setup_github_cli = AsyncMock()
    return mock


@pytest.fixture
def mock_p2p_connection():
    """Create a mock P2PConnection"""
    mock = MagicMock()
    mock.is_connected = MagicMock(return_value=True)
    mock.close = AsyncMock()
    mock.create_offer = AsyncMock(return_value={"sdp": "test_sdp_offer"})
    mock.on_connect = MagicMock()
    mock.on_disconnect = MagicMock()
    return mock


@pytest.fixture
def mock_ssh_manager():
    """Create a mock SSH manager"""
    mock = MagicMock()
    mock.get_key = MagicMock(return_value=MagicMock(id="key_123"))
    mock.deploy_to_github = AsyncMock()
    mock.add_to_ssh_agent = AsyncMock()
    return mock


@pytest.fixture
def security_manager(mock_kill_switch, mock_temporal_ca, mock_vault_manager):
    """Create an IntegratedSecurityManager with mocked dependencies"""
    with patch(
        "core.integrated_security.KillSwitchEngine",
        return_value=mock_kill_switch,
    ):
        with patch(
            "core.integrated_security.KimiTemporalCA",
            return_value=mock_temporal_ca,
        ):
            with patch(
                "core.integrated_security.SecureVaultManager",
                return_value=mock_vault_manager,
            ):
                manager = IntegratedSecurityManager()
                yield manager


# ==================== SecurityStatus Tests ====================


class TestSecurityStatus:
    """Test SecurityStatus dataclass"""

    def test_creation(self):
        """Test creating SecurityStatus"""
        status = SecurityStatus(
            kill_switch_armed=True,
            p2p_connected=True,
            vault_unlocked=True,
            active_credentials=5,
            last_heartbeat=30.0,
            session_duration="2h 30m",
        )
        assert status.kill_switch_armed is True
        assert status.p2p_connected is True
        assert status.vault_unlocked is True
        assert status.active_credentials == 5
        assert status.last_heartbeat == 30.0
        assert status.session_duration == "2h 30m"

    def test_creation_with_none(self):
        """Test creating SecurityStatus with None values"""
        status = SecurityStatus(
            kill_switch_armed=False,
            p2p_connected=False,
            vault_unlocked=False,
            active_credentials=0,
            last_heartbeat=None,
            session_duration=None,
        )
        assert status.last_heartbeat is None
        assert status.session_duration is None


# ==================== IntegratedSecurityManager Init Tests ====================


class TestIntegratedSecurityManagerInit:
    """Test IntegratedSecurityManager initialization"""

    def test_initialization(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test manager initialization"""
        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    manager = IntegratedSecurityManager()

                    assert manager.kill_switch is mock_kill_switch
                    assert manager.temporal_ca is mock_temporal_ca
                    assert manager.vault_manager is mock_vault_manager
                    assert manager.p2p is None
                    # Callback should be registered
                    mock_kill_switch.on_kill_switch.assert_called_once()

    def test_setup_kill_switch_callbacks(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test kill switch callback setup"""
        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    manager = IntegratedSecurityManager()

                    # Get the registered callback
                    callback = mock_kill_switch.on_kill_switch.call_args[0][0]
                    assert callable(callback)


# ==================== IntegratedSecurityManager Start/Stop Tests ====================


class TestIntegratedSecurityManagerLifecycle:
    """Test IntegratedSecurityManager start/stop operations"""

    @pytest.mark.asyncio
    async def test_start(self, security_manager):
        """Test starting security system"""
        await security_manager.start()

        security_manager.temporal_ca.start.assert_awaited_once()
        security_manager.kill_switch.start_monitoring.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop(self, security_manager):
        """Test stopping security system"""
        await security_manager.stop()

        # Should trigger kill switch
        security_manager.kill_switch.trigger_kill_switch.assert_awaited_once()
        security_manager.temporal_ca.stop.assert_awaited_once()
        security_manager.kill_switch.stop_monitoring.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_triggers_manual_lock(self, security_manager):
        """Test stop triggers manual lock kill switch"""
        from core.integrated_security import KillSwitchReason

        await security_manager.stop()

        call_args = security_manager.kill_switch.trigger_kill_switch.call_args
        assert call_args[0][0] == KillSwitchReason.MANUAL_LOCK


# ==================== P2P Connection Tests ====================


class TestP2PConnection:
    """Test P2P connection handling"""

    @pytest.mark.asyncio
    async def test_establish_p2p_connection(self, security_manager, mock_p2p_connection):
        """Test establishing P2P connection"""
        with patch(
            "core.integrated_security.P2PConnection",
            return_value=mock_p2p_connection,
        ):
            result = await security_manager.establish_p2p_connection()

            assert result is True
            assert security_manager.p2p is mock_p2p_connection
            mock_p2p_connection.create_offer.assert_awaited_once()
            mock_p2p_connection.on_connect.assert_called_once()
            mock_p2p_connection.on_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_p2p_connect(self, security_manager, mock_p2p_connection):
        """Test P2P connect handler"""
        with patch(
            "core.integrated_security.P2PConnection",
            return_value=mock_p2p_connection,
        ):
            await security_manager.establish_p2p_connection()

            # Get the connect callback
            connect_callback = mock_p2p_connection.on_connect.call_args[0][0]

            # Mock the credential issuance
            with patch.object(
                security_manager,
                "_issue_session_credentials",
                new_callable=AsyncMock,
            ) as mock_issue:
                mock_issue.return_value = {
                    MagicMock(value="VAULT_KEY"): MagicMock(value="vault_key_value"),
                    MagicMock(value="KIMI_TEMP"): MagicMock(id="kimi_id"),
                }

                # Call the callback (it's wrapped in asyncio.create_task in real code)
                await connect_callback()

                # Credentials should be issued
                mock_issue.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_on_p2p_disconnect(self, security_manager, mock_p2p_connection):
        """Test P2P disconnect handler"""
        from core.integrated_security import KillSwitchReason

        with patch(
            "core.integrated_security.P2PConnection",
            return_value=mock_p2p_connection,
        ):
            await security_manager.establish_p2p_connection()

            # Get the disconnect callback
            disconnect_callback = mock_p2p_connection.on_disconnect.call_args[0][0]

            # Call the callback
            await disconnect_callback()

            # Should trigger tunnel down kill switch
            security_manager.kill_switch.trigger_kill_switch.assert_awaited_with(KillSwitchReason.TUNNEL_DOWN)


# ==================== Credential Management Tests ====================


class TestCredentialManagement:
    """Test credential lifecycle management"""

    @pytest.mark.asyncio
    async def test_issue_session_credentials(self, security_manager):
        """Test issuing session credentials"""
        # Mock SSH manager
        with patch("core.ssh_key_manager.get_ssh_manager") as mock_get_ssh:
            mock_ssh = MagicMock()
            mock_ssh.get_key = MagicMock(return_value=MagicMock(id="key_123"))
            mock_ssh.deploy_to_github = AsyncMock()
            mock_ssh.add_to_ssh_agent = AsyncMock()
            mock_get_ssh.return_value = mock_ssh

            credentials = await security_manager._issue_session_credentials()

            # Should issue all credential types (5 credentials)
            assert security_manager.temporal_ca.issue_credential.await_count == 5
            # Should get 5 credentials back
            assert len(credentials) == 5

    @pytest.mark.asyncio
    async def test_get_credential_success(self, security_manager):
        """Test getting credential when unlocked"""
        security_manager.vault_manager.is_unlocked.return_value = True

        result = await security_manager.get_credential("api_key")

        assert result == "secret_value"
        security_manager.vault_manager.get_credential.assert_called_once_with("api_key")

    @pytest.mark.asyncio
    async def test_get_credential_locked(self, security_manager):
        """Test getting credential when locked raises error"""
        security_manager.vault_manager.is_unlocked.return_value = False

        with pytest.raises(SecurityError, match="System locked"):
            await security_manager.get_credential("api_key")


# ==================== Security Status Tests ====================


class TestSecurityStatusReporting:
    """Test security status reporting"""

    def test_get_status(self, security_manager):
        """Test getting complete security status"""
        CredentialStatus = sys.modules["core.credential_lifecycle"].CredentialStatus

        # Create mock credentials that compare properly with CredentialStatus.ACTIVE
        cred_active = MagicMock()
        cred_active.status = CredentialStatus.ACTIVE
        cred_revoked = MagicMock()
        cred_revoked.status = CredentialStatus.REVOKED

        security_manager.temporal_ca._credentials = {
            "cred1": cred_active,
            "cred2": cred_active,
            "cred3": cred_revoked,
        }
        security_manager.p2p = MagicMock()
        security_manager.p2p.is_connected.return_value = True
        security_manager.vault_manager.is_unlocked.return_value = True

        status = security_manager.get_status()

        assert isinstance(status, SecurityStatus)
        assert status.kill_switch_armed is True
        assert status.p2p_connected is True
        assert status.vault_unlocked is True
        assert status.active_credentials == 2
        assert status.last_heartbeat == 10.0
        assert status.session_duration == 1.5  # Numeric value from mock

    def test_get_status_no_p2p(self, security_manager):
        """Test status when P2P is not connected"""
        security_manager.p2p = None
        security_manager.temporal_ca._credentials = {}

        status = security_manager.get_status()

        assert status.p2p_connected is False
        assert status.active_credentials == 0


# ==================== Credential Rotation Tests ====================


class TestCredentialRotation:
    """Test credential rotation functionality"""

    @pytest.mark.asyncio
    async def test_rotate_all_credentials(self, security_manager):
        """Test rotating all active credentials"""
        mock_creds = [
            MagicMock(id="cred1"),
            MagicMock(id="cred2"),
            MagicMock(id="cred3"),
        ]
        security_manager.temporal_ca.get_active = AsyncMock(return_value=mock_creds)
        security_manager.temporal_ca.rotate_credential = AsyncMock()

        await security_manager.rotate_all_credentials()

        assert security_manager.temporal_ca.rotate_credential.await_count == 3
        security_manager.temporal_ca.rotate_credential.assert_has_awaits(
            [
                call("cred1"),
                call("cred2"),
                call("cred3"),
            ]
        )

    @pytest.mark.asyncio
    async def test_rotate_no_active_credentials(self, security_manager):
        """Test rotation with no active credentials"""
        security_manager.temporal_ca.get_active = AsyncMock(return_value=[])

        await security_manager.rotate_all_credentials()

        security_manager.temporal_ca.rotate_credential.assert_not_awaited()


# ==================== Emergency Lockdown Tests ====================


class TestEmergencyLockdown:
    """Test emergency lockdown functionality"""

    @pytest.mark.asyncio
    async def test_emergency_lockdown(self, security_manager, mock_p2p_connection):
        """Test emergency lockdown"""
        security_manager.p2p = mock_p2p_connection

        await security_manager.emergency_lockdown()

        security_manager.temporal_ca.revoke_all.assert_awaited_once()
        security_manager.vault_manager.encrypt_vault.assert_awaited_once()
        mock_p2p_connection.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_emergency_lockdown_no_p2p(self, security_manager):
        """Test emergency lockdown without P2P"""
        security_manager.p2p = None

        await security_manager.emergency_lockdown()

        security_manager.temporal_ca.revoke_all.assert_awaited_once()
        security_manager.vault_manager.encrypt_vault.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_emergency_lockdown_partial_failure(self, security_manager, mock_p2p_connection):
        """Test lockdown continues even if some operations fail"""
        security_manager.p2p = mock_p2p_connection
        security_manager.temporal_ca.revoke_all.side_effect = Exception("Revoke failed")

        # Should not raise
        await security_manager.emergency_lockdown()


# ==================== Kill Switch Callback Tests ====================


class TestKillSwitchCallback:
    """Test kill switch callback behavior"""

    @pytest.mark.asyncio
    async def test_on_kill_switch_callback(self, security_manager, mock_p2p_connection):
        """Test kill switch callback purges credentials"""
        security_manager.p2p = mock_p2p_connection

        # Get the registered callback
        callback = security_manager.kill_switch.on_kill_switch.call_args[0][0]

        # Create a mock event
        event = MagicMock()
        event.reason = KillSwitchReason.HEARTBEAT_TIMEOUT

        # Call the callback
        await callback(event)

        # Should purge all credentials
        security_manager.temporal_ca.revoke_all.assert_awaited_once()
        security_manager.vault_manager.encrypt_vault.assert_awaited_once()
        mock_p2p_connection.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_on_kill_switch_no_p2p(self, security_manager):
        """Test kill switch callback without P2P"""
        security_manager.p2p = None

        # Get the registered callback
        callback = security_manager.kill_switch.on_kill_switch.call_args[0][0]

        # Should not raise
        await callback(MagicMock())


# ==================== Global Instance Tests ====================


class TestGlobalInstance:
    """Test global security manager instance"""

    def test_get_security_manager_singleton(self):
        """Test get_security_manager returns singleton"""
        # Reset global instance
        import core.integrated_security as is_module

        original = is_module._security_manager
        is_module._security_manager = None

        try:
            with patch("core.integrated_security.KillSwitchEngine"):
                with patch("core.integrated_security.KimiTemporalCA"):
                    with patch("core.integrated_security.SecureVaultManager"):
                        sm1 = get_security_manager()
                        sm2 = get_security_manager()
                        assert sm1 is sm2
        finally:
            is_module._security_manager = original

    def test_get_security_manager_creates_instance(self):
        """Test get_security_manager creates instance if none exists"""
        import core.integrated_security as is_module

        original = is_module._security_manager
        is_module._security_manager = None

        try:
            with patch("core.integrated_security.KillSwitchEngine"):
                with patch("core.integrated_security.KimiTemporalCA"):
                    with patch("core.integrated_security.SecureVaultManager"):
                        sm = get_security_manager()
                        assert sm is not None
                        assert isinstance(sm, IntegratedSecurityManager)
        finally:
            is_module._security_manager = original


# ==================== Integration Tests ====================


@pytest.mark.integration
class TestIntegratedSecurityIntegration:
    """Integration tests for integrated security system"""

    @pytest.mark.asyncio
    async def test_full_security_lifecycle(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test complete security lifecycle"""
        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    manager = IntegratedSecurityManager()

                    # Start
                    await manager.start()
                    mock_temporal_ca.start.assert_awaited_once()
                    mock_kill_switch.start_monitoring.assert_awaited_once()

                    # Get status
                    status = manager.get_status()
                    assert isinstance(status, SecurityStatus)

                    # Stop
                    await manager.stop()
                    mock_kill_switch.trigger_kill_switch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_p2p_connect_disconnect_flow(
        self,
        mock_kill_switch,
        mock_temporal_ca,
        mock_vault_manager,
        mock_p2p_connection,
    ):
        """Test P2P connect and disconnect flow"""
        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    with patch(
                        "core.integrated_security.P2PConnection",
                        return_value=mock_p2p_connection,
                    ):
                        manager = IntegratedSecurityManager()

                        # Establish connection
                        await manager.establish_p2p_connection()
                        assert manager.p2p is mock_p2p_connection

                        # Simulate disconnect
                        disconnect_callback = mock_p2p_connection.on_disconnect.call_args[0][0]
                        await disconnect_callback()

                        # Should trigger kill switch
                        mock_kill_switch.trigger_kill_switch.assert_awaited()


# ==================== Edge Case Tests ====================


class TestIntegratedSecurityEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_issue_credentials_with_ssh_failure(self, security_manager):
        """Test credential issuance when SSH deployment fails"""
        with patch("core.ssh_key_manager.get_ssh_manager") as mock_get_ssh:
            mock_ssh = MagicMock()
            mock_ssh.get_key = MagicMock(return_value=None)  # No key returned
            mock_ssh.deploy_to_github = AsyncMock()
            mock_get_ssh.return_value = mock_ssh

            # Should not raise
            credentials = await security_manager._issue_session_credentials()

            # SSH deployment should not be called if no key
            mock_ssh.deploy_to_github.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_with_component_failure(self, security_manager):
        """Test start when a component fails"""
        security_manager.temporal_ca.start.side_effect = Exception("Start failed")

        # Should raise the exception
        with pytest.raises(Exception, match="Start failed"):
            await security_manager.start()

    @pytest.mark.asyncio
    async def test_p2p_connect_vault_decrypt_fails(self, security_manager, mock_p2p_connection):
        """Test P2P connect when vault decryption fails"""
        with patch(
            "core.integrated_security.P2PConnection",
            return_value=mock_p2p_connection,
        ):
            await security_manager.establish_p2p_connection()

            # Get connect callback
            connect_callback = mock_p2p_connection.on_connect.call_args[0][0]

            # Mock credentials with vault key
            with patch.object(
                security_manager,
                "_issue_session_credentials",
                new_callable=AsyncMock,
            ) as mock_issue:
                mock_cred = MagicMock()
                mock_cred.value = "vault_key_value"

                # Use a simple approach - mock the credential type lookup
                creds_dict = {mock_cred: mock_cred}
                mock_issue.return_value = creds_dict

                # Should not raise
                await connect_callback()

    @pytest.mark.asyncio
    async def test_on_p2p_connect_no_vault_key(self, security_manager, mock_p2p_connection):
        """Test P2P connect when no vault key in credentials"""
        with patch(
            "core.integrated_security.P2PConnection",
            return_value=mock_p2p_connection,
        ):
            await security_manager.establish_p2p_connection()

            connect_callback = mock_p2p_connection.on_connect.call_args[0][0]

            # Return credentials without vault key
            with patch.object(
                security_manager,
                "_issue_session_credentials",
                new_callable=AsyncMock,
            ) as mock_issue:
                mock_issue.return_value = {}  # No vault key

                # Should not raise
                await connect_callback()


# ==================== CLI Tests ====================


class TestCLI:
    """Test CLI main function"""

    @pytest.mark.asyncio
    async def test_cli_start(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test CLI start command"""
        import core.integrated_security as is_module

        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    # Reset singleton
                    is_module._security_manager = None

                    from core.integrated_security import main

                    with patch("sys.argv", ["integrated_security", "start"]):
                        with patch("asyncio.sleep", side_effect=KeyboardInterrupt()):
                            await main()

                            mock_temporal_ca.start.assert_awaited_once()
                            mock_kill_switch.start_monitoring.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cli_stop(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test CLI stop command"""
        import core.integrated_security as is_module

        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    # Reset singleton
                    is_module._security_manager = None

                    from core.integrated_security import main

                    with patch("sys.argv", ["integrated_security", "stop"]):
                        await main()

                        mock_kill_switch.trigger_kill_switch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cli_status(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test CLI status command"""
        import core.integrated_security as is_module

        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    # Reset singleton
                    is_module._security_manager = None

                    from core.integrated_security import main

                    with patch("sys.argv", ["integrated_security", "status"]):
                        with patch("builtins.print") as mock_print:
                            await main()

                            # Should print status
                            mock_print.assert_called()

    @pytest.mark.asyncio
    async def test_cli_lockdown(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test CLI lockdown command"""
        import core.integrated_security as is_module

        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    # Reset singleton
                    is_module._security_manager = None

                    from core.integrated_security import main

                    with patch("sys.argv", ["integrated_security", "lockdown"]):
                        await main()

                        # Should trigger emergency lockdown
                        mock_temporal_ca.revoke_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cli_rotate(self, mock_kill_switch, mock_temporal_ca, mock_vault_manager):
        """Test CLI rotate command"""
        import core.integrated_security as is_module

        with patch(
            "core.integrated_security.KillSwitchEngine",
            return_value=mock_kill_switch,
        ):
            with patch(
                "core.integrated_security.KimiTemporalCA",
                return_value=mock_temporal_ca,
            ):
                with patch(
                    "core.integrated_security.SecureVaultManager",
                    return_value=mock_vault_manager,
                ):
                    # Reset singleton
                    is_module._security_manager = None

                    from core.integrated_security import main

                    with patch("sys.argv", ["integrated_security", "rotate"]):
                        await main()

                        # Should rotate credentials
                        mock_temporal_ca.get_active.assert_awaited_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
