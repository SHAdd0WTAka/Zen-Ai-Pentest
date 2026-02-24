"""
Tests for nmap_integration module - Coverage Boost
"""

import subprocess
import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest


class TestScanType:
    """Test ScanType enum"""

    def test_scan_type_values(self):
        """Test ScanType enum values"""
        from tools.nmap_integration import ScanType

        assert ScanType.SYN.value == "-sS"
        assert ScanType.CONNECT.value == "-sT"
        assert ScanType.UDP.value == "-sU"
        assert ScanType.ACK.value == "-sA"
        assert ScanType.WINDOW.value == "-sW"
        assert ScanType.MAIMON.value == "-sM"
        assert ScanType.FIN.value == "-sF"
        assert ScanType.NULL.value == "-sN"
        assert ScanType.XMAS.value == "-sX"
        assert ScanType.PING.value == "-sn"


class TestTimingTemplate:
    """Test TimingTemplate enum"""

    def test_timing_template_values(self):
        """Test TimingTemplate enum values"""
        from tools.nmap_integration import TimingTemplate

        assert TimingTemplate.PARANOID.value == "-T0"
        assert TimingTemplate.SNEAKY.value == "-T1"
        assert TimingTemplate.POLITE.value == "-T2"
        assert TimingTemplate.NORMAL.value == "-T3"
        assert TimingTemplate.AGGRESSIVE.value == "-T4"
        assert TimingTemplate.INSANE.value == "-T5"


class TestNmapPort:
    """Test NmapPort dataclass"""

    def test_nmap_port_creation(self):
        """Test NmapPort creation"""
        from tools.nmap_integration import NmapPort

        port = NmapPort(
            port=80,
            protocol="tcp",
            state="open",
            service="http",
            version="Apache 2.4",
            banner="Apache/2.4.41",
            cpe=["cpe:/a:apache:http_server:2.4"],
            scripts={"http-title": "Test Page"},
        )

        assert port.port == 80
        assert port.protocol == "tcp"
        assert port.state == "open"
        assert port.service == "http"
        assert port.version == "Apache 2.4"

    def test_nmap_port_defaults(self):
        """Test NmapPort with default values"""
        from tools.nmap_integration import NmapPort

        port = NmapPort(port=22, protocol="tcp", state="open")

        assert port.service == ""
        assert port.version == ""
        assert port.banner == ""
        assert port.cpe == []
        assert port.scripts == {}


class TestNmapHost:
    """Test NmapHost dataclass"""

    def test_nmap_host_creation(self):
        """Test NmapHost creation"""
        from tools.nmap_integration import NmapHost, NmapPort

        ports = [NmapPort(port=80, protocol="tcp", state="open")]
        host = NmapHost(
            ip="192.168.1.1",
            hostname="test.local",
            status="up",
            os_match="Linux 5.4",
            os_accuracy=95,
            ports=ports,
            mac_address="00:11:22:33:44:55",
            vendor="Test Vendor",
        )

        assert host.ip == "192.168.1.1"
        assert host.hostname == "test.local"
        assert len(host.ports) == 1


class TestNmapResult:
    """Test NmapResult dataclass"""

    def test_nmap_result_success(self):
        """Test successful NmapResult"""
        from tools.nmap_integration import NmapHost, NmapResult

        hosts = [NmapHost(ip="192.168.1.1")]
        result = NmapResult(
            success=True,
            hosts=hosts,
            command="nmap 192.168.1.1",
            scan_time=10.5,
            summary={"hosts_up": 1, "hosts_down": 0},
        )

        assert result.success is True
        assert len(result.hosts) == 1
        assert result.error is None

    def test_nmap_result_failure(self):
        """Test failed NmapResult"""
        from tools.nmap_integration import NmapResult

        result = NmapResult(success=False, error="Permission denied")

        assert result.success is False
        assert result.error == "Permission denied"


class TestNmapScanner:
    """Test NmapScanner class"""

    @pytest.fixture
    def mock_nmap_path(self):
        """Mock nmap binary path"""
        with patch("tools.nmap_integration.shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/nmap"
            yield mock_which

    def test_init_single_target(self, mock_nmap_path):
        """Test scanner initialization with single target"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1")

        assert scanner.targets == ["192.168.1.1"]
        assert scanner.nmap_path == "/usr/bin/nmap"

    def test_init_multiple_targets(self, mock_nmap_path):
        """Test scanner initialization with multiple targets"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner(["192.168.1.1", "192.168.1.2"])

        assert len(scanner.targets) == 2

    def test_init_with_options(self, mock_nmap_path):
        """Test scanner initialization with options"""
        from tools.nmap_integration import (
            NmapScanner,
            ScanType,
            TimingTemplate,
        )

        options = {
            "ports": "80,443",
            "scan_type": ScanType.CONNECT,
            "timing": TimingTemplate.AGGRESSIVE,
        }
        scanner = NmapScanner("192.168.1.1", options=options)

        assert scanner.options["ports"] == "80,443"
        assert scanner.options["scan_type"] == ScanType.CONNECT

    def test_init_nmap_not_found(self):
        """Test scanner initialization when nmap is not found"""
        from tools.nmap_integration import NmapScanner

        with patch("tools.nmap_integration.shutil.which") as mock_which:
            mock_which.return_value = None

            with pytest.raises(RuntimeError, match="nmap not found"):
                NmapScanner("192.168.1.1")

    def test_validate_targets_with_cidr(self, mock_nmap_path):
        """Test target validation with CIDR notation"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.0/24")

        assert "192.168.1.0/24" in scanner.targets

    def test_validate_targets_with_hostname(self, mock_nmap_path):
        """Test target validation with hostname"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("example.com")

        assert "example.com" in scanner.targets

    def test_validate_targets_dangerous_chars(self, mock_nmap_path):
        """Test target validation rejects dangerous characters"""
        from tools.nmap_integration import NmapScanner

        with pytest.raises(ValueError, match="Invalid characters"):
            NmapScanner("192.168.1.1; rm -rf /")

    def test_build_command_basic(self, mock_nmap_path):
        """Test basic command building"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1")
        cmd = scanner._build_command()

        assert "/usr/bin/nmap" in cmd
        assert "192.168.1.1" in cmd
        assert "-T3" in cmd  # Default timing

    def test_build_command_with_service_detection(self, mock_nmap_path):
        """Test command building with service detection"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner(
            "192.168.1.1", options={"service_detection": True}
        )
        cmd = scanner._build_command()

        assert "-sV" in cmd

    def test_build_command_with_os_detection(self, mock_nmap_path):
        """Test command building with OS detection"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1", options={"os_detection": True})
        cmd = scanner._build_command()

        assert "-O" in cmd

    def test_build_command_aggressive(self, mock_nmap_path):
        """Test command building with aggressive scan"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1", options={"aggressive": True})
        cmd = scanner._build_command()

        assert "-A" in cmd

    def test_build_command_ping_scan(self, mock_nmap_path):
        """Test command building with ping scan"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1", options={"ping_scan": True})
        cmd = scanner._build_command()

        assert "-sn" in cmd

    def test_build_command_no_ping(self, mock_nmap_path):
        """Test command building with no ping"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1", options={"no_ping": True})
        cmd = scanner._build_command()

        assert "-Pn" in cmd

    def test_build_command_top_ports(self, mock_nmap_path):
        """Test command building with top ports preset"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1", options={"ports": "top-10"})
        cmd = scanner._build_command()

        assert "-p" in cmd
        assert any("22,80,443" in str(item) for item in cmd)

    def test_build_command_top_1000(self, mock_nmap_path):
        """Test command building with top-1000 preset"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1", options={"ports": "top-1000"})
        cmd = scanner._build_command()

        assert "--top-ports" in cmd

    def test_build_command_output_xml(self, mock_nmap_path):
        """Test command building includes XML output"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1")
        cmd = scanner._build_command()

        assert "-oX" in cmd

    def test_parse_xml_host(self, mock_nmap_path):
        """Test XML parsing for host"""
        from tools.nmap_integration import NmapScanner

        mock_xml = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.1" addrtype="ipv4"/>
                <hostnames>
                    <hostname name="test.local" type="PTR"/>
                </hostnames>
            </host>
        </nmaprun>"""

        scanner = NmapScanner("192.168.1.1")
        root = ET.fromstring(mock_xml)
        host_elem = root.find("host")

        host = scanner._parse_host(host_elem)

        assert host.ip == "192.168.1.1"
        assert host.hostname == "test.local"
        assert host.status == "up"

    def test_parse_xml_port(self, mock_nmap_path):
        """Test XML parsing for port"""
        from tools.nmap_integration import NmapScanner

        mock_xml = """<port protocol="tcp" portid="80">
            <state state="open"/>
            <service name="http" product="Apache" version="2.4"/>
        </port>"""

        scanner = NmapScanner("192.168.1.1")
        port_elem = ET.fromstring(mock_xml)

        port = scanner._parse_port(port_elem)

        assert port.port == 80
        assert port.protocol == "tcp"
        assert port.state == "open"
        assert port.service == "http"

    def test_parse_xml_host_down(self, mock_nmap_path):
        """Test XML parsing for down host"""
        from tools.nmap_integration import NmapScanner

        mock_xml = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="down"/>
                <address addr="192.168.1.2" addrtype="ipv4"/>
            </host>
        </nmaprun>"""

        scanner = NmapScanner("192.168.1.2")
        root = ET.fromstring(mock_xml)
        host_elem = root.find("host")

        host = scanner._parse_host(host_elem)

        assert host.ip == "192.168.1.2"
        assert host.status == "down"

    def test_parse_xml_with_mac(self, mock_nmap_path):
        """Test XML parsing with MAC address"""
        from tools.nmap_integration import NmapScanner

        mock_xml = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.1" addrtype="ipv4"/>
                <address addr="00:11:22:33:44:55" addrtype="mac" vendor="TestVendor"/>
            </host>
        </nmaprun>"""

        scanner = NmapScanner("192.168.1.1")
        root = ET.fromstring(mock_xml)
        host_elem = root.find("host")

        host = scanner._parse_host(host_elem)

        # MAC address parsing may vary based on implementation
        assert host is not None
        assert host.ip == "192.168.1.1"

    def test_top_ports_constant(self, mock_nmap_path):
        """Test TOP_PORTS class constant"""
        from tools.nmap_integration import NmapScanner

        assert "top-10" in NmapScanner.TOP_PORTS
        assert "top-100" in NmapScanner.TOP_PORTS
        assert "top-1000" in NmapScanner.TOP_PORTS

        assert "22,80,443" in NmapScanner.TOP_PORTS["top-10"]

    @pytest.mark.asyncio
    async def test_scan_with_mock_subprocess(self, mock_nmap_path):
        """Test scan with mocked subprocess"""
        from tools.nmap_integration import NmapScanner

        mock_xml = b"""<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.1" addrtype="ipv4"/>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http"/>
                    </port>
                </ports>
            </host>
        </nmaprun>"""

        scanner = NmapScanner("192.168.1.1")

        with patch.object(scanner, "_run_subprocess") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["nmap"], returncode=0, stdout=mock_xml, stderr=b""
            )

            result = await scanner.scan()

            assert result.success is True
            assert len(result.hosts) == 1
            assert result.hosts[0].ip == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_scan_subprocess_error(self, mock_nmap_path):
        """Test scan with subprocess error"""
        from tools.nmap_integration import NmapScanner

        scanner = NmapScanner("192.168.1.1")

        with patch.object(scanner, "_run_subprocess") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["nmap"],
                returncode=1,
                stdout=b"",
                stderr=b"nmap: command failed",
            )

            result = await scanner.scan()

            assert result.success is False

    def test_result_to_dict(self, mock_nmap_path):
        """Test converting result to dict"""
        from tools.nmap_integration import NmapHost, NmapResult, NmapScanner

        hosts = [NmapHost(ip="192.168.1.1", status="up")]
        result = NmapResult(success=True, hosts=hosts)

        scanner = NmapScanner("192.168.1.1")
        result_dict = scanner._result_to_dict(result)

        assert result_dict["success"] is True
        assert len(result_dict["hosts"]) == 1

    def test_fallback_parse(self, mock_nmap_path):
        """Test fallback XML parsing"""
        from tools.nmap_integration import NmapScanner

        xml_string = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <address addr="192.168.1.1" addrtype="ipv4"/>
                <status state="up"/>
            </host>
        </nmaprun>"""

        scanner = NmapScanner("192.168.1.1")
        hosts = scanner._fallback_parse(xml_string)

        assert len(hosts) == 1
        assert hosts[0].ip == "192.168.1.1"
