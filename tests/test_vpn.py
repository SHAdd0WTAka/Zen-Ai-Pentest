"""
VPN Integration Tests
=====================

Tests for ProtonVPN integration and VPN detection.

Note: These tests work without actual VPN connection
by mocking or checking for VPN CLI availability.
"""

from unittest.mock import MagicMock, patch

import pytest

from vpn.protonvpn import GenericVPNDetector, ProtonVPNManager, VPNInfo, VPNManager, VPNStatus


class TestProtonVPNManager:
    """Test ProtonVPN CLI integration"""

    def test_initialization_without_cli(self):
        """Manager should work without ProtonVPN CLI"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("protonvpn-cli not found")

            vpn = ProtonVPNManager()
            assert vpn.cli_available is False

    def test_status_without_cli(self):
        """Status should return UNKNOWN without CLI"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("protonvpn-cli not found")

            vpn = ProtonVPNManager()
            status = vpn.get_status()

            assert status.status == VPNStatus.UNKNOWN
            assert "not installed" in status.error_message.lower()

    def test_status_connected(self):
        """Parse connected status correctly"""
        mock_output = """Status:       Connected
Server:       CH#1
IP:           10.0.0.1
Protocol:     UDP
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr="")

            vpn = ProtonVPNManager()
            vpn.cli_available = True
            status = vpn.get_status()

            assert status.status == VPNStatus.CONNECTED
            assert status.provider == "ProtonVPN"
            assert status.server == "CH#1"
            assert status.ip == "10.0.0.1"

    def test_status_disconnected(self):
        """Parse disconnected status correctly"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Disconnected", stderr="")

            vpn = ProtonVPNManager()
            vpn.cli_available = True
            status = vpn.get_status()

            assert status.status == VPNStatus.DISCONNECTED

    def test_is_connected_true(self):
        """is_connected returns True when connected"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Connected", stderr="")

            vpn = ProtonVPNManager()
            vpn.cli_available = True
            assert vpn.is_connected() is True

    def test_is_connected_false(self):
        """is_connected returns False when disconnected"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Disconnected", stderr="")

            vpn = ProtonVPNManager()
            vpn.cli_available = True
            assert vpn.is_connected() is False

    def test_connect_without_cli(self):
        """Connect returns False without CLI"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("protonvpn-cli not found")

            vpn = ProtonVPNManager()
            result = vpn.connect()

            assert result is False

    def test_disconnect_without_cli(self):
        """Disconnect returns False without CLI"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("protonvpn-cli not found")

            vpn = ProtonVPNManager()
            result = vpn.disconnect()

            assert result is False


class TestGenericVPNDetector:
    """Test generic VPN detection"""

    def test_detect_vpn_interface_linux(self):
        """Detect VPN via network interface on Linux"""
        mock_output = """1: lo: <LOOPBACK> mtu 65536
2: eth0: <BROADCAST> mtu 1500
3: tun0: <POINTOPOINT> mtu 1400
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr="")

            detector = GenericVPNDetector()
            status = detector.get_status()

            assert status.status == VPNStatus.CONNECTED

    def test_detect_vpn_process(self):
        """Detect VPN via running processes"""
        mock_output = """user 1234 0.0 openvpn --config vpn.conf
user 5678 0.0 chrome
"""
        # First check interfaces (no VPN), then processes
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="1: lo:", stderr=""),  # ip link
                MagicMock(returncode=0, stdout="1: lo:", stderr=""),  # ifconfig
                MagicMock(returncode=0, stdout=mock_output, stderr=""),  # ps aux
            ]

            detector = GenericVPNDetector()
            status = detector.get_status()

            assert status.status == VPNStatus.CONNECTED

    def test_no_vpn_detected(self):
        """Return DISCONNECTED when no VPN found"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="1: lo:", stderr=""),
                MagicMock(returncode=0, stdout="1: lo:", stderr=""),
                MagicMock(returncode=0, stdout="user 1234 chrome", stderr=""),
            ]

            detector = GenericVPNDetector()
            status = detector.get_status()

            assert status.status == VPNStatus.DISCONNECTED

    def test_detect_provider_proton(self):
        """Detect ProtonVPN from interface name"""
        detector = GenericVPNDetector()
        provider = detector._detect_provider_from_interface("proton0")
        assert provider == "ProtonVPN"

    def test_detect_provider_wireguard(self):
        """Detect WireGuard from interface name"""
        detector = GenericVPNDetector()
        provider = detector._detect_provider_from_interface("wg0")
        assert provider == "WireGuard"

    def test_detect_provider_openvpn(self):
        """Detect OpenVPN from interface name"""
        detector = GenericVPNDetector()
        provider = detector._detect_provider_from_interface("tun0")
        assert provider == "OpenVPN"


class TestVPNManager:
    """Test high-level VPN manager"""

    def test_get_status_uses_proton_when_available(self):
        """Manager prefers ProtonVPN when CLI available"""
        mock_output = "Status: Connected\nServer: CH#1"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output, stderr="")

            manager = VPNManager()
            status = manager.get_status()

            assert status.status == VPNStatus.CONNECTED
            assert status.provider == "ProtonVPN"

    def test_get_status_fallback_to_generic(self):
        """Manager falls back to generic detection"""
        with patch("subprocess.run") as mock_run:
            # First call (ProtonVPN) fails
            # Second call (generic) succeeds
            mock_run.side_effect = [
                FileNotFoundError("protonvpn-cli not found"),
                MagicMock(returncode=0, stdout="3: tun0:", stderr=""),
                MagicMock(returncode=0, stdout="", stderr=""),  # ifconfig fallback
            ]

            manager = VPNManager()
            status = manager.get_status()

            assert status.status == VPNStatus.CONNECTED

    def test_is_connected_true(self):
        """is_connected returns True when VPN active"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Connected", stderr="")

            manager = VPNManager()
            manager.proton.cli_available = True
            assert manager.is_connected() is True

    def test_is_connected_false(self):
        """is_connected returns False when VPN inactive"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Disconnected", stderr="")

            manager = VPNManager()
            manager.proton.cli_available = True
            assert manager.is_connected() is False

    def test_check_before_scan_connected(self):
        """Check before scan when VPN connected"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Connected\nServer: CH#1", stderr="")

            manager = VPNManager()
            manager.proton.cli_available = True
            result = manager.check_before_scan("scanme.nmap.org")

            assert result["allowed"] is True
            assert result["warning"] is None
            assert "✅ VPN active" in result["recommendation"]

    def test_check_before_scan_disconnected(self):
        """Check before scan when VPN disconnected - shows warning"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("protonvpn-cli not found")

            manager = VPNManager()
            result = manager.check_before_scan("scanme.nmap.org")

            assert result["allowed"] is True  # Not blocked, just warned
            assert result["warning"] is not None
            assert "WARNING" in result["warning"]
            assert "ProtonVPN" in result["recommendation"]

    def test_strict_mode_blocks_scan(self):
        """Strict mode blocks scans without VPN"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("protonvpn-cli not found")

            manager = VPNManager()
            manager.set_strict_mode(True)
            result = manager.check_before_scan("scanme.nmap.org")

            assert result["allowed"] is False
            assert "SCAN BLOCKED" in result["warning"]

    def test_strict_mode_allows_with_vpn(self):
        """Strict mode allows scans with VPN connected"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Status: Connected", stderr="")

            manager = VPNManager()
            manager.set_strict_mode(True)
            manager.proton.cli_available = True
            result = manager.check_before_scan("scanme.nmap.org")

            assert result["allowed"] is True

    def test_disable_recommendations(self):
        """Can disable VPN recommendations"""
        manager = VPNManager()
        manager.set_recommendations(False)

        result = manager.check_before_scan("scanme.nmap.org")
        assert result["warning"] is None
        assert result["recommendation"] is None

    def test_status_callback(self):
        """Status change callbacks work"""
        callbacks = []

        def callback(status):
            callbacks.append(status)

        manager = VPNManager()
        manager.on_status_change(callback)

        # Manually trigger callback
        test_status = VPNInfo(status=VPNStatus.CONNECTED)
        for cb in manager._status_callbacks:
            cb(test_status)

        assert len(callbacks) == 1
        assert callbacks[0].status == VPNStatus.CONNECTED


class TestVPNInfo:
    """Test VPNInfo dataclass"""

    def test_vpn_info_creation(self):
        """Create VPNInfo with all fields"""
        info = VPNInfo(
            status=VPNStatus.CONNECTED,
            provider="ProtonVPN",
            server="CH#1",
            ip="10.0.0.1",
            country="Switzerland",
            protocol="UDP",
        )

        assert info.status == VPNStatus.CONNECTED
        assert info.provider == "ProtonVPN"
        assert info.server == "CH#1"
        assert info.ip == "10.0.0.1"
        assert info.country == "Switzerland"
        assert info.protocol == "UDP"

    def test_vpn_info_defaults(self):
        """VPNInfo with default values"""
        info = VPNInfo(status=VPNStatus.DISCONNECTED)

        assert info.status == VPNStatus.DISCONNECTED
        assert info.provider is None
        assert info.server is None


class TestVPNConvenienceFunctions:
    """Test convenience module functions"""

    @patch("vpn.get_vpn_manager")
    def test_get_vpn_status(self, mock_get_manager):
        """get_vpn_status convenience function"""
        mock_manager = MagicMock()
        mock_manager.get_status.return_value = VPNInfo(status=VPNStatus.CONNECTED)
        mock_get_manager.return_value = mock_manager

        from vpn.protonvpn import get_vpn_status

        status = get_vpn_status()

        assert status.status == VPNStatus.CONNECTED

    @patch("vpn.get_vpn_manager")
    def test_is_vpn_connected(self, mock_get_manager):
        """is_vpn_connected convenience function"""
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_get_manager.return_value = mock_manager

        from vpn.protonvpn import is_vpn_connected

        result = is_vpn_connected()

        assert result is True

    @patch("vpn.get_vpn_manager")
    def test_check_vpn_before_scan(self, mock_get_manager):
        """check_vpn_before_scan convenience function"""
        mock_manager = MagicMock()
        mock_manager.check_before_scan.return_value = {"allowed": True}
        mock_get_manager.return_value = mock_manager

        from vpn.protonvpn import check_vpn_before_scan

        result = check_vpn_before_scan("target.com")

        assert result["allowed"] is True


class TestVPNIntegrationWithOrchestrator:
    """Test VPN integration with workflow orchestrator"""

    @pytest.mark.asyncio
    async def test_orchestrator_shows_vpn_warning(self):
        """Orchestrator shows VPN warning when not connected"""
        from agents.workflows.orchestrator import WorkflowOrchestrator

        with patch("vpn.get_vpn_manager") as mock_get_vpn:
            mock_vpn = MagicMock()
            mock_vpn.check_before_scan.return_value = {
                "allowed": True,
                "warning": "⚠️ WARNING: No VPN",
                "recommendation": "💡 Use ProtonVPN",
            }
            mock_get_vpn.return_value = mock_vpn

            orchestrator = WorkflowOrchestrator(step_timeout=1)
            orchestrator.guardrails_enabled = False

            # Should not raise, just log warning
            workflow_id = await orchestrator.start_workflow(
                workflow_type="network_recon", target="scanme.nmap.org", agents=["agent-1"]
            )

            assert workflow_id is not None

    @pytest.mark.asyncio
    async def test_workflow_proceeds_without_vpn(self):
        """Workflow proceeds even without VPN (optional)"""
        from agents.workflows.orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(step_timeout=1)
        orchestrator.guardrails_enabled = False

        # Should work without VPN
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="scanme.nmap.org", agents=["agent-1"]
        )

        assert workflow_id.startswith("wf_")
