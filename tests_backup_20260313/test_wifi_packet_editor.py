"""
Tests für tools/wifi_packet_editor.py
Target: 90%+ Coverage
"""

import time
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestWiFiFrameInfo:
    """Test WiFiFrameInfo Dataclass"""

    def test_frame_info_creation(self):
        """Test WiFiFrameInfo kann erstellt werden"""
        from tools.wifi_packet_editor import WiFiFrameInfo

        info = WiFiFrameInfo(
            frame_type="Management",
            subtype="Beacon",
            src_mac="00:11:22:33:44:55",
            dst_mac="ff:ff:ff:ff:ff:ff",
            bssid="00:11:22:33:44:55",
            ssid="TestNetwork",
            channel=6,
            signal_dbm=-50,
        )

        assert info.frame_type == "Management"
        assert info.ssid == "TestNetwork"
        assert info.signal_dbm == -50


class TestWiFiSecurityError:
    """Test WiFiSecurityError Exception"""

    def test_exception_raised(self):
        """Test Exception kann geworfen werden"""
        from tools.wifi_packet_editor import WiFiSecurityError

        with pytest.raises(WiFiSecurityError):
            raise WiFiSecurityError("Test error")


class TestWiFiPacketEditorInit:
    """Test WiFiPacketEditor Initialisierung"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_init_defaults(self):
        """Test Standard-Initialisierung"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor()

        assert editor.interface == "wlan0mon"
        assert editor.safety_mode is True
        assert len(editor.allowed_networks) == 0

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_init_with_allowed_networks(self):
        """Test mit erlaubten Netzwerken"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        networks = ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
        editor = WiFiPacketEditor(allowed_networks=networks)

        assert editor.allowed_networks == set(networks)

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", False)
    def test_init_without_scapy(self):
        """Test ohne Scapy sollte fehlschlagen"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        with pytest.raises(RuntimeError):
            WiFiPacketEditor()


class TestIsAllowedBSSID:
    """Test BSSID-Validierung"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_allowed_bssid_true(self):
        """Test erlaubte BSSID wird erkannt"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(allowed_networks=["AA:BB:CC:DD:EE:FF"])

        assert (
            editor._is_allowed_bssid("aa:bb:cc:dd:ee:ff") is True
        )  # lowercase
        assert (
            editor._is_allowed_bssid("AA:BB:CC:DD:EE:FF") is True
        )  # uppercase

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_allowed_bssid_false(self):
        """Test nicht-erlaubte BSSID wird blockiert"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(allowed_networks=["AA:BB:CC:DD:EE:FF"])

        assert editor._is_allowed_bssid("00:11:22:33:44:55") is False

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_safety_mode_off(self):
        """Test ohne Safety Mode werden alle erlaubt"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)

        assert editor._is_allowed_bssid("00:11:22:33:44:55") is True


class TestParseFrame:
    """Test Frame-Parsing"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_parse_beacon_frame(self):
        """Test Beacon Frame Parsing"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        # Mock Frame erstellen - simuliere Scapy Frame
        mock_dot11_layer = MagicMock()
        mock_dot11_layer.type = 0  # Management
        mock_dot11_layer.subtype = 8  # Beacon
        mock_dot11_layer.addr1 = "ff:ff:ff:ff:ff:ff"
        mock_dot11_layer.addr2 = "00:11:22:33:44:55"
        mock_dot11_layer.addr3 = "00:11:22:33:44:55"

        mock_ssid_layer = MagicMock()
        mock_ssid_layer.ID = 0
        mock_ssid_layer.info = b"TestNetwork"

        # Frame mit haslayer und getlayer
        mock_frame = MagicMock()

        def mock_haslayer(layer):
            return layer.__name__ in ["Dot11", "Dot11Elt"]

        def mock_getlayer(layer):
            if layer.__name__ == "Dot11":
                return mock_dot11_layer
            elif layer.__name__ == "Dot11Elt":
                return mock_ssid_layer
            return None

        mock_frame.haslayer = mock_haslayer
        mock_frame.getlayer = mock_getlayer

        editor = WiFiPacketEditor(safety_mode=False)
        info = editor.parse_frame(mock_frame)

        assert info is not None
        assert info.subtype == "Beacon"
        assert info.frame_type == "Management"

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_parse_non_dot11_frame(self):
        """Test nicht-802.11 Frame wird ignoriert"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        mock_frame = MagicMock()
        mock_frame.haslayer.return_value = False

        editor = WiFiPacketEditor(safety_mode=False)
        info = editor.parse_frame(mock_frame)

        assert info is None


class TestCreateBeaconFrame:
    """Test Beacon Frame Erstellung"""

    def test_create_beacon_allowed(self):
        """Test Beacon Erstellung für erlaubtes Netzwerk"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(
            allowed_networks=["00:11:22:33:44:55"], safety_mode=True
        )

        # Einfacher Test - Frame wird erstellt
        frame = editor.create_beacon_frame(
            ssid="TestAP", bssid="00:11:22:33:44:55", channel=6
        )

        # Frame sollte erstellt worden sein (kein Error)
        assert frame is not None

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_create_beacon_not_allowed(self):
        """Test Beacon Erstellung für nicht-erlaubtes Netzwerk blockiert"""
        from tools.wifi_packet_editor import (
            WiFiPacketEditor,
            WiFiSecurityError,
        )

        editor = WiFiPacketEditor(
            allowed_networks=["00:11:22:33:44:55"], safety_mode=True
        )

        with pytest.raises(WiFiSecurityError):
            editor.create_beacon_frame(
                ssid="EvilAP",
                bssid="AA:BB:CC:DD:EE:FF",  # Nicht erlaubt
                channel=6,
            )


class TestSpoofMac:
    """Test MAC-Spoofing"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_spoof_mac_addresses(self):
        """Test MAC-Adressen werden geändert"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)

        # Mock Frame
        mock_frame = MagicMock()
        mock_frame.copy.return_value = MagicMock()
        mock_frame.addr1 = "ff:ff:ff:ff:ff:ff"
        mock_frame.addr2 = "00:11:22:33:44:55"
        mock_frame.addr3 = "00:11:22:33:44:55"

        modified = editor.spoof_mac(
            mock_frame,
            new_src="AA:BB:CC:DD:EE:FF",
            new_dst="11:22:33:44:55:66",
        )

        assert modified.addr2 == "AA:BB:CC:DD:EE:FF"
        assert modified.addr1 == "11:22:33:44:55:66"

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_spoof_mac_safety_block(self):
        """Test MAC-Spoofing wird bei unautorisiertem Netzwerk blockiert"""
        from tools.wifi_packet_editor import (
            WiFiPacketEditor,
            WiFiSecurityError,
        )

        editor = WiFiPacketEditor(
            allowed_networks=["00:11:22:33:44:55"], safety_mode=True
        )

        mock_frame = MagicMock()
        mock_frame.addr3 = "AA:BB:CC:DD:EE:FF"  # Nicht erlaubt

        with pytest.raises(WiFiSecurityError):
            editor.spoof_mac(mock_frame, new_src="11:22:33:44:55:66")


class TestCreateDeauthFrame:
    """Test Deauth Frame Erstellung"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_deauth_safety_mode_blocks(self):
        """Test Deauth wird im Safety Mode blockiert"""
        from tools.wifi_packet_editor import (
            WiFiPacketEditor,
            WiFiSecurityError,
        )

        editor = WiFiPacketEditor(safety_mode=True)

        with pytest.raises(WiFiSecurityError):
            editor.create_deauth_frame(
                src_mac="00:11:22:33:44:55",
                dst_mac="AA:BB:CC:DD:EE:FF",
                bssid="00:11:22:33:44:55",
            )

    def test_deauth_safety_mode_off(self):
        """Test Deauth Erstellung ohne Safety Mode"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)

        frame = editor.create_deauth_frame(
            src_mac="00:11:22:33:44:55",
            dst_mac="AA:BB:CC:DD:EE:FF",
            bssid="00:11:22:33:44:55",
            reason=7,
        )

        # Frame sollte erstellt worden sein
        assert frame is not None


class TestDetectDeauthAttack:
    """Test Deauth-Angriffserkennung"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_no_attack_detected(self):
        """Test keine Angriff bei wenigen Deauth-Frames"""
        from tools.wifi_packet_editor import WiFiFrameInfo, WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)

        frames = [
            WiFiFrameInfo(
                "Management",
                "Beacon",
                "00:11:22:33:44:55",
                "ff:ff:ff:ff:ff:ff",
                "00:11:22:33:44:55",
            ),
            WiFiFrameInfo(
                "Management",
                "Beacon",
                "00:11:22:33:44:55",
                "ff:ff:ff:ff:ff:ff",
                "00:11:22:33:44:55",
            ),
            WiFiFrameInfo(
                "Management",
                "Deauth",
                "00:11:22:33:44:55",
                "AA:BB:CC:DD:EE:FF",
                "00:11:22:33:44:55",
            ),
        ]

        report = editor.detect_deauth_attack(frames)

        assert report["attack_detected"] is False
        assert report["deauth_frames"] == 1

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_attack_detected(self):
        """Test Angriffserkennung bei vielen Deauth-Frames"""
        from tools.wifi_packet_editor import WiFiFrameInfo, WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)

        # Erstelle 15 Deauth-Frames (Threshold > 10)
        frames = [
            WiFiFrameInfo(
                "Management",
                "Deauth",
                "00:11:22:33:44:55",
                f"AA:BB:CC:DD:EE:{i:02X}",
                "00:11:22:33:44:55",
            )
            for i in range(15)
        ]

        report = editor.detect_deauth_attack(frames)

        assert report["attack_detected"] is True
        assert len(report["recommendations"]) > 0


class TestExportImport:
    """Test PCAP Export/Import"""

    @patch("tools.wifi_packet_editor.wrpcap")
    def test_export_to_pcap(self, mock_wrpcap):
        """Test Export zu PCAP"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)
        editor._captured_frames = [MagicMock(), MagicMock()]

        result = editor.export_to_pcap("/tmp/test.pcap")

        assert result is True
        mock_wrpcap.assert_called_once()

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    def test_export_no_frames(self):
        """Test Export ohne Frames"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        editor = WiFiPacketEditor(safety_mode=False)

        result = editor.export_to_pcap("/tmp/test.pcap")

        assert result is False

    @patch("tools.wifi_packet_editor.rdpcap")
    def test_import_from_pcap(self, mock_rdpcap):
        """Test Import aus PCAP"""
        from tools.wifi_packet_editor import WiFiPacketEditor

        # Mock Pakete
        mock_pkt = MagicMock()
        mock_pkt.haslayer.return_value = False  # Einfacher Test
        mock_rdpcap.return_value = [mock_pkt, mock_pkt]

        editor = WiFiPacketEditor(safety_mode=False)
        result = editor.import_from_pcap("/tmp/test.pcap")

        mock_rdpcap.assert_called_once_with("/tmp/test.pcap")


class TestCheckMonitorModeCapability:
    """Test System-Check"""

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", True)
    @patch("scapy.all.get_if_list")
    def test_check_with_scapy(self, mock_get_if_list):
        """Test System-Check mit Scapy"""
        from tools.wifi_packet_editor import check_monitor_mode_capability

        mock_get_if_list.return_value = ["eth0", "wlan0", "wlan0mon"]

        result = check_monitor_mode_capability("wlan0")

        assert result["scapy_available"] is True
        assert "wlan0" in result["available_interfaces"]
        assert len(result["recommendations"]) > 0

    @patch("tools.wifi_packet_editor.SCAPY_AVAILABLE", False)
    def test_check_without_scapy(self):
        """Test System-Check ohne Scapy"""
        from tools.wifi_packet_editor import check_monitor_mode_capability

        result = check_monitor_mode_capability()

        assert result["scapy_available"] is False
        assert any("pip install" in r for r in result["recommendations"])


class TestQuickScan:
    """Test Convenience-Funktion quick_scan"""

    @patch("tools.wifi_packet_editor.WiFiPacketEditor")
    def test_quick_scan(self, mock_editor_class):
        """Test quick_scan Funktion"""
        from tools.wifi_packet_editor import quick_scan

        mock_instance = MagicMock()
        mock_instance.capture_frames.return_value = []
        mock_editor_class.return_value = mock_instance

        result = quick_scan(duration=10, interface="wlan0mon")

        mock_editor_class.assert_called_once_with(
            interface="wlan0mon", safety_mode=True, allowed_networks=[]
        )
        mock_instance.capture_frames.assert_called_once_with(duration=10)


class TestWiFiFrameTypeEnum:
    """Test WiFiFrameType Enum"""

    def test_frame_types(self):
        """Test Frame-Typen Werte"""
        from tools.wifi_packet_editor import WiFiFrameType

        assert WiFiFrameType.MANAGEMENT.value == 0
        assert WiFiFrameType.CONTROL.value == 1
        assert WiFiFrameType.DATA.value == 2


class TestWiFiSubTypeEnum:
    """Test WiFiSubType Enum"""

    def test_subtypes(self):
        """Test Subtyp-Werte"""
        from tools.wifi_packet_editor import WiFiSubType

        assert WiFiSubType.BEACON.value == 8
        assert WiFiSubType.DEAUTHENTICATION.value == 12
        assert WiFiSubType.PROBE_REQUEST.value == 4
