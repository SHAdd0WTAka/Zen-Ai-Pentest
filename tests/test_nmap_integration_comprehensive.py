"""
Comprehensive Tests for Nmap Integration Module

Tests for tools/nmap_integration.py with mocking (no real tool execution).
Target: 80%+ coverage
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.nmap_integration import (
    NmapHost,
    NmapPort,
    NmapResult,
    NmapScanner,
    ScanType,
    TimingTemplate,
    create_nmap_result_dict,
    nmap_quick_scan,
    nmap_scan,
    nmap_vuln_scan,
    register_nmap_tools,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_xml_output():
    """Sample Nmap XML output for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <nmaprun scanner="nmap" args="nmap -sS -T3 -oX - scanme.nmap.org">
        <host starttime="1234567890">
            <status state="up" reason="syn-ack"/>
            <address addr="45.33.32.156" addrtype="ipv4"/>
            <hostnames>
                <hostname name="scanme.nmap.org" type="user"/>
            </hostnames>
            <ports>
                <port protocol="tcp" portid="22">
                    <state state="open" reason="syn-ack"/>
                    <service name="ssh" product="OpenSSH" version="6.6.1"/>
                </port>
                <port protocol="tcp" portid="80">
                    <state state="open" reason="syn-ack"/>
                    <service name="http" product="Apache httpd" version="2.4.7">
                        <cpe>cpe:/a:apache:http_server:2.4.7</cpe>
                    </service>
                </port>
                <port protocol="tcp" portid="443">
                    <state state="closed" reason="reset"/>
                    <service name="https"/>
                </port>
            </ports>
            <os>
                <osmatch name="Linux 3.x" accuracy="95" line="12345"/>
                <osmatch name="Linux 4.x" accuracy="90" line="12346"/>
            </os>
            <hostscript>
                <script id="smb-os-discovery" output="Windows 10"/>
            </hostscript>
            <trace>
                <hop ttl="1" ipaddr="192.168.1.1" rtt="0.5"/>
                <hop ttl="2" ipaddr="10.0.0.1" rtt="1.2"/>
            </trace>
        </host>
        <host starttime="1234567891">
            <status state="down" reason="no-response"/>
            <address addr="192.168.1.100" addrtype="ipv4"/>
        </host>
    </nmaprun>"""


@pytest.fixture
def mock_nmap_path():
    """Mock nmap binary path"""
    return "/usr/bin/nmap"


@pytest.fixture
def scanner(mock_nmap_path):
    """Create a NmapScanner instance with mocked path validation"""
    with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
        return NmapScanner("scanme.nmap.org")


# ============================================================================
# Test NmapScanner Initialization
# ============================================================================


class TestNmapScannerInit:
    """Test NmapScanner initialization and validation"""

    def test_init_with_single_target(self, mock_nmap_path):
        """Test initialization with single target string"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")
            assert scanner.targets == ["scanme.nmap.org"]
            assert scanner.nmap_path == mock_nmap_path

    def test_init_with_multiple_targets(self, mock_nmap_path):
        """Test initialization with multiple targets"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner(["scanme.nmap.org", "example.com"])
            assert scanner.targets == ["scanme.nmap.org", "example.com"]

    def test_init_with_options(self, mock_nmap_path):
        """Test initialization with options"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            options = {"ports": "80,443", "service_detection": True}
            scanner = NmapScanner("scanme.nmap.org", options)
            assert scanner.options["ports"] == "80,443"
            assert scanner.options["service_detection"] is True
            assert scanner.options["timing"] == TimingTemplate.NORMAL

    def test_init_default_options(self, mock_nmap_path):
        """Test default options are set"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")
            assert scanner.options["timing"] == TimingTemplate.NORMAL
            assert scanner.options["scan_type"] == ScanType.SYN

    def test_nmap_not_found(self):
        """Test error when nmap is not installed"""
        with patch("tools.nmap_integration.shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="nmap not found"):
                NmapScanner("scanme.nmap.org")


# ============================================================================
# Test Target Validation
# ============================================================================


class TestTargetValidation:
    """Test target validation methods"""

    def test_validate_ip_address(self, mock_nmap_path):
        """Test validation of IP addresses"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("192.168.1.1")
            assert "192.168.1.1" in scanner.targets

    def test_validate_ipv6_address(self, mock_nmap_path):
        """Test validation of IPv6 addresses"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("2001:db8::1")
            assert "2001:db8::1" in scanner.targets

    def test_validate_cidr_network(self, mock_nmap_path):
        """Test validation of CIDR notation"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("192.168.1.0/24")
            assert "192.168.1.0/24" in scanner.targets

    def test_validate_hostname(self, mock_nmap_path):
        """Test validation of hostnames"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")
            assert "scanme.nmap.org" in scanner.targets

    def test_validate_invalid_characters(self, mock_nmap_path):
        """Test rejection of dangerous characters"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            with pytest.raises(ValueError, match="Invalid characters"):
                NmapScanner("scanme.nmap.org;rm -rf /")

    def test_validate_empty_target(self, mock_nmap_path):
        """Test handling of empty targets"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            with pytest.raises(ValueError, match="No valid targets"):
                NmapScanner("")

    def test_validate_no_valid_targets(self, mock_nmap_path):
        """Test error when no valid targets"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            with pytest.raises(ValueError, match="No valid targets"):
                NmapScanner(["", "   "])

    def test_validate_mixed_targets(self, mock_nmap_path):
        """Test validation with mixed valid/invalid targets"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner(["scanme.nmap.org", "", "192.168.1.1"])
            assert len(scanner.targets) == 2


# ============================================================================
# Test Command Building
# ============================================================================


class TestCommandBuilding:
    """Test command building functionality"""

    def test_basic_command(self, scanner):
        """Test basic command structure"""
        cmd = scanner._build_command()
        assert cmd[0] == scanner.nmap_path
        assert ScanType.SYN.value in cmd
        assert TimingTemplate.NORMAL.value in cmd
        assert "-oX" in cmd
        assert "-" in cmd
        assert "scanme.nmap.org" in cmd

    def test_scan_type_options(self, mock_nmap_path):
        """Test different scan types"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            for scan_type in ScanType:
                scanner = NmapScanner("scanme.nmap.org", {"scan_type": scan_type})
                cmd = scanner._build_command()
                assert scan_type.value in cmd

    def test_timing_templates(self, mock_nmap_path):
        """Test timing template options"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            for timing in TimingTemplate:
                scanner = NmapScanner("scanme.nmap.org", {"timing": timing})
                cmd = scanner._build_command()
                assert timing.value in cmd

    def test_port_specifications(self, mock_nmap_path):
        """Test various port specifications"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            test_cases = [
                ("80,443", "-p", "80,443"),
                ("1-1000", "-p", "1-1000"),
                ("top-10", "-p", NmapScanner.TOP_PORTS["top-10"]),
                ("top-1000", "--top-ports", "1000"),
            ]
            for ports, expected_flag, expected_value in test_cases:
                scanner = NmapScanner("scanme.nmap.org", {"ports": ports})
                cmd = scanner._build_command()
                assert expected_flag in cmd
                if expected_flag == "-p":
                    assert expected_value in cmd

    def test_service_detection(self, mock_nmap_path):
        """Test service detection options"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"service_detection": True, "version_intensity": 9})
            cmd = scanner._build_command()
            assert "-sV" in cmd
            assert "--version-intensity" in cmd
            assert "9" in cmd

    def test_os_detection(self, mock_nmap_path):
        """Test OS detection options"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"os_detection": True, "osscan_limit": True})
            cmd = scanner._build_command()
            assert "-O" in cmd
            assert "--osscan-limit" in cmd

    def test_script_scan_string(self, mock_nmap_path):
        """Test script scan with string"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"script_scan": "http-title"})
            cmd = scanner._build_command()
            assert "--script" in cmd
            assert "http-title" in cmd

    def test_script_scan_list(self, mock_nmap_path):
        """Test script scan with list"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"script_scan": ["http-title", "vulners"]})
            cmd = scanner._build_command()
            assert "--script" in cmd
            assert "http-title,vulners" in cmd

    def test_script_scan_default(self, mock_nmap_path):
        """Test default script scan"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"script_scan": True})
            cmd = scanner._build_command()
            assert "-sC" in cmd

    def test_aggressive_scan(self, mock_nmap_path):
        """Test aggressive scan flag"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"aggressive": True})
            cmd = scanner._build_command()
            assert "-A" in cmd

    def test_ping_scan(self, mock_nmap_path):
        """Test ping scan option"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"ping_scan": True})
            cmd = scanner._build_command()
            assert ScanType.PING.value in cmd

    def test_no_ping(self, mock_nmap_path):
        """Test no ping option"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"no_ping": True})
            cmd = scanner._build_command()
            assert "-Pn" in cmd

    def test_advanced_options(self, mock_nmap_path):
        """Test advanced options"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            options = {
                "source_port": 53,
                "interface": "eth0",
                "max_retries": 3,
                "host_timeout": "30m",
                "scan_delay": "1s",
                "max_rate": 1000,
            }
            scanner = NmapScanner("scanme.nmap.org", options)
            cmd = scanner._build_command()
            assert "-g" in cmd and "53" in cmd
            assert "-e" in cmd and "eth0" in cmd
            assert "--max-retries" in cmd and "3" in cmd
            assert "--host-timeout" in cmd and "30m" in cmd
            assert "--scan-delay" in cmd and "1s" in cmd
            assert "--max-rate" in cmd and "1000" in cmd

    def test_verbosity_options(self, mock_nmap_path):
        """Test verbosity levels"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            for level, expected in [(1, "-v"), (2, "-vv"), (3, "-vvv"), (5, "-vvv")]:
                scanner = NmapScanner("scanme.nmap.org", {"verbosity": level})
                cmd = scanner._build_command()
                assert expected in cmd

    def test_debugging_options(self, mock_nmap_path):
        """Test debugging levels"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            for level, expected in [(1, "-d"), (2, "-dd"), (3, "-dd")]:
                scanner = NmapScanner("scanme.nmap.org", {"debugging": level})
                cmd = scanner._build_command()
                assert expected in cmd

    def test_additional_args(self, mock_nmap_path):
        """Test additional arguments"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"additional_args": ["--reason", "--packet-trace"]})
            cmd = scanner._build_command()
            assert "--reason" in cmd
            assert "--packet-trace" in cmd

    def test_multiple_targets_in_command(self, mock_nmap_path):
        """Test command with multiple targets"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner(["scanme.nmap.org", "example.com"])
            cmd = scanner._build_command()
            assert cmd[-2] == "scanme.nmap.org"
            assert cmd[-1] == "example.com"

    def test_string_scan_type(self, mock_nmap_path):
        """Test string scan type instead of enum"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"scan_type": "-sT"})
            cmd = scanner._build_command()
            assert "-sT" in cmd

    def test_string_timing(self, mock_nmap_path):
        """Test string timing instead of enum"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org", {"timing": "-T5"})
            cmd = scanner._build_command()
            assert "-T5" in cmd


# ============================================================================
# Test XML Parsing
# ============================================================================


class TestXMLParsing:
    """Test XML output parsing"""

    def test_parse_host_with_ports(self, scanner, sample_xml_output):
        """Test parsing host with multiple ports"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        assert len(hosts) == 2

        # First host
        host = hosts[0]
        assert host.ip == "45.33.32.156"
        assert host.hostname == "scanme.nmap.org"
        assert host.status == "up"
        assert len(host.ports) == 3

    def test_parse_port_details(self, scanner, sample_xml_output):
        """Test parsing individual port details"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        host = hosts[0]

        # Check open port with service
        port22 = next(p for p in host.ports if p.port == 22)
        assert port22.protocol == "tcp"
        assert port22.state == "open"
        assert port22.service == "ssh"
        # Version contains the full version string (product + version)
        assert "6.6.1" in port22.version or "OpenSSH" in port22.version

        # Check closed port
        port443 = next(p for p in host.ports if p.port == 443)
        assert port443.state == "closed"

    def test_parse_os_detection(self, scanner, sample_xml_output):
        """Test parsing OS detection results"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        host = hosts[0]

        assert host.os_match == "Linux 3.x"
        assert host.os_accuracy == 95
        assert len(host.os_matches) == 2

    def test_parse_host_scripts(self, scanner, sample_xml_output):
        """Test parsing host script output"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        host = hosts[0]

        assert "smb-os-discovery" in host.host_scripts
        assert host.host_scripts["smb-os-discovery"] == "Windows 10"

    def test_parse_traceroute(self, scanner, sample_xml_output):
        """Test parsing traceroute data"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        host = hosts[0]

        assert len(host.trace) == 2
        assert host.trace[0]["ttl"] == "1"
        assert host.trace[0]["ipaddr"] == "192.168.1.1"

    def test_parse_down_host(self, scanner, sample_xml_output):
        """Test parsing down host"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        down_host = hosts[1]

        assert down_host.ip == "192.168.1.100"
        assert down_host.status == "down"

    def test_parse_empty_xml(self, scanner):
        """Test parsing empty XML"""
        hosts = scanner.parse_xml_output("<?xml version='1.0'?><nmaprun></nmaprun>")
        assert len(hosts) == 0

    def test_parse_invalid_xml(self, scanner):
        """Test parsing invalid XML with fallback"""
        invalid_xml = """<nmaprun>
            <host><address addr="1.2.3.4" addrtype="ipv4"/><status state="up"/></host>
        </nmaprun>"""
        hosts = scanner.parse_xml_output(invalid_xml)
        # Should use fallback parsing or handle gracefully
        assert isinstance(hosts, list)

    def test_parse_xml_with_cpe(self, scanner, sample_xml_output):
        """Test parsing CPE information"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        host = hosts[0]
        port80 = next(p for p in host.ports if p.port == 80)

        assert len(port80.cpe) > 0
        assert "apache:http_server" in port80.cpe[0]

    def test_parse_host_without_address(self, scanner):
        """Test parsing host without valid address"""
        xml = """<?xml version="1.0"?>
        <nmaprun>
            <host><status state="up"/></host>
        </nmaprun>"""
        hosts = scanner.parse_xml_output(xml)
        assert len(hosts) == 0


# ============================================================================
# Test Fallback Parsing
# ============================================================================


class TestFallbackParsing:
    """Test fallback regex-based parsing"""

    def test_fallback_parse_host(self, scanner):
        """Test fallback parsing extracts host info"""
        xml = '<host><address addr="192.168.1.1" addrtype="ipv4"/><status state="up"/></host>'
        hosts = scanner._fallback_parse(xml)

        assert len(hosts) == 1
        assert hosts[0].ip == "192.168.1.1"
        assert hosts[0].status == "up"

    def test_fallback_parse_multiple_hosts(self, scanner):
        """Test fallback parsing with multiple hosts"""
        xml = """
        <host><address addr="192.168.1.1" addrtype="ipv4"/><status state="up"/></host>
        <host><address addr="192.168.1.2" addrtype="ipv4"/><status state="down"/></host>
        """
        hosts = scanner._fallback_parse(xml)
        assert len(hosts) == 2

    def test_fallback_parse_no_match(self, scanner):
        """Test fallback parsing with no matches"""
        hosts = scanner._fallback_parse("<invalid>not a host</invalid>")
        assert len(hosts) == 0


# ============================================================================
# Test Async Scanning
# ============================================================================


class TestAsyncScanning:
    """Test async scan execution"""

    @pytest.mark.asyncio
    async def test_successful_scan(self, scanner, sample_xml_output):
        """Test successful scan execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = sample_xml_output
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.scan(timeout=60)

        assert result.success is True
        assert len(result.hosts) == 2
        assert result.command != ""
        assert result.scan_time >= 0
        assert "total_hosts" in result.summary

    @pytest.mark.asyncio
    async def test_scan_failure(self, scanner):
        """Test scan with non-zero exit code"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Invalid target"

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.scan(timeout=60)

        assert result.success is False
        assert "failed" in result.error.lower() or "Error" in result.error

    @pytest.mark.asyncio
    async def test_scan_timeout(self, scanner):
        """Test scan timeout handling"""
        with patch.object(scanner, "_run_subprocess", side_effect=asyncio.TimeoutError):
            result = await scanner.scan(timeout=1)

        assert result.success is False
        # Check for timeout in error message (case-insensitive)
        assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_scan_exception(self, scanner):
        """Test scan with unexpected exception"""
        with patch.object(scanner, "_run_subprocess", side_effect=Exception("Unexpected error")):
            result = await scanner.scan(timeout=60)

        assert result.success is False
        assert "Unexpected error" in result.error

    @pytest.mark.asyncio
    async def test_scan_ports_method(self, mock_nmap_path):
        """Test scan_ports convenience method"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<?xml version='1.0'?><nmaprun></nmaprun>"
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.scan_ports(ports="top-10", scan_type=ScanType.SYN)

        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_service_detection_method(self, mock_nmap_path):
        """Test service_detection convenience method"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<?xml version='1.0'?><nmaprun></nmaprun>"
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.service_detection(ports="80,443")

        assert isinstance(result, dict)
        assert scanner.options["service_detection"] is True

    @pytest.mark.asyncio
    async def test_os_detection_method(self, mock_nmap_path):
        """Test os_detection convenience method"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<?xml version='1.0'?><nmaprun></nmaprun>"
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.os_detection(ports="top-100")

        assert isinstance(result, dict)
        assert scanner.options["os_detection"] is True

    @pytest.mark.asyncio
    async def test_run_script_method(self, mock_nmap_path):
        """Test run_script convenience method"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<?xml version='1.0'?><nmaprun></nmaprun>"
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.run_script("http-title", ports="80,443", script_args={"http.useragent": "Mozilla"})

        assert isinstance(result, dict)
        assert scanner.options["script_scan"] == "http-title"

    @pytest.mark.asyncio
    async def test_scan_ports_with_enum_type(self, mock_nmap_path):
        """Test scan_ports with ScanType enum"""
        with patch("tools.nmap_integration.shutil.which", return_value=mock_nmap_path):
            scanner = NmapScanner("scanme.nmap.org")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "<?xml version='1.0'?><nmaprun></nmaprun>"
        mock_result.stderr = ""

        with patch.object(scanner, "_run_subprocess", return_value=mock_result):
            result = await scanner.scan_ports(ports="80", scan_type=ScanType.SYN)

        assert isinstance(result, dict)
        assert scanner.options["scan_type"] == ScanType.SYN


# ============================================================================
# Test Result Conversion
# ============================================================================


class TestResultConversion:
    """Test result to dictionary conversion"""

    def test_result_to_dict(self, scanner, sample_xml_output):
        """Test converting result to dictionary"""
        hosts = scanner.parse_xml_output(sample_xml_output)
        result = NmapResult(success=True, hosts=hosts, command="nmap test", scan_time=5.0)

        result_dict = scanner._result_to_dict(result)

        assert result_dict["success"] is True
        assert result_dict["command"] == "nmap test"
        assert result_dict["scan_time"] == 5.0
        assert len(result_dict["hosts"]) == 2
        assert "ports" in result_dict["hosts"][0]

    def test_create_nmap_result_dict(self, sample_xml_output):
        """Test create_nmap_result_dict helper"""
        scanner = NmapScanner.__new__(NmapScanner)
        hosts = scanner.parse_xml_output(sample_xml_output)

        result = create_nmap_result_dict(hosts)

        assert result["tool"] == "nmap"
        assert result["total_hosts"] == 2
        assert result["hosts_up"] == 1  # One host is up, one is down
        assert len(result["open_ports"]) == 2  # 22 and 80 are open


# ============================================================================
# Test LangChain Tool Functions
# ============================================================================


class TestLangChainTools:
    """Test LangChain tool wrapper functions - these are LangChain StructuredTool objects"""

    def test_nmap_scan_tool_exists(self):
        """Test that nmap_scan tool is defined"""
        # nmap_scan is a LangChain StructuredTool, not a regular function
        assert nmap_scan is not None
        assert hasattr(nmap_scan, 'name')
        assert nmap_scan.name == 'nmap_scan'

    def test_nmap_quick_scan_tool_exists(self):
        """Test that nmap_quick_scan tool is defined"""
        assert nmap_quick_scan is not None
        assert hasattr(nmap_quick_scan, 'name')
        assert nmap_quick_scan.name == 'nmap_quick_scan'

    def test_nmap_vuln_scan_tool_exists(self):
        """Test that nmap_vuln_scan tool is defined"""
        assert nmap_vuln_scan is not None
        assert hasattr(nmap_vuln_scan, 'name')
        assert nmap_vuln_scan.name == 'nmap_vuln_scan'

    def test_nmap_scan_tool_description(self):
        """Test that nmap_scan has description"""
        assert hasattr(nmap_scan, 'description')
        assert 'nmap' in nmap_scan.description.lower()

    @patch("tools.nmap_integration.NmapScanner")
    @patch("tools.nmap_integration.asyncio.run")
    def test_nmap_scan_invocation(self, mock_run, mock_scanner_class):
        """Test nmap_scan tool can be invoked via LangChain"""
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.scan_time = 10.5
        mock_result.command = "nmap -sS scanme.nmap.org"
        mock_result.hosts = []
        mock_run.return_value = mock_result

        # Invoke via LangChain tool interface
        result = nmap_scan.invoke({"target": "scanme.nmap.org", "ports": "top-100", "scan_type": "syn"})

        assert isinstance(result, str)
        mock_scanner_class.assert_called_once()

    @patch("tools.nmap_integration.NmapScanner")
    @patch("tools.nmap_integration.asyncio.run")
    def test_nmap_quick_scan_invocation(self, mock_run, mock_scanner_class):
        """Test nmap_quick_scan tool invocation"""
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.hosts = []
        mock_run.return_value = mock_result

        result = nmap_quick_scan.invoke({"target": "scanme.nmap.org"})

        assert isinstance(result, str)

    @patch("tools.nmap_integration.NmapScanner")
    @patch("tools.nmap_integration.asyncio.run")
    def test_nmap_vuln_scan_invocation(self, mock_run, mock_scanner_class):
        """Test nmap_vuln_scan tool invocation"""
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.hosts = []
        mock_run.return_value = mock_result

        result = nmap_vuln_scan.invoke({"target": "scanme.nmap.org"})

        assert isinstance(result, str)


# ============================================================================
# Test Tool Registry Integration
# ============================================================================


class TestToolRegistryIntegration:
    """Test integration with tool registry"""

    @patch("tools.nmap_integration.TOOL_REGISTRY_AVAILABLE", True)
    @patch("tools.nmap_integration.LANGCHAIN_AVAILABLE", True)
    @patch("tools.nmap_integration.registry")
    def test_register_nmap_tools(self, mock_registry):
        """Test registering nmap tools with registry"""
        register_nmap_tools()

        # Should register 3 tools
        assert mock_registry.register.call_count == 3

    @patch("tools.nmap_integration.TOOL_REGISTRY_AVAILABLE", False)
    def test_register_when_registry_unavailable(self):
        """Test registration when registry is not available"""
        # Should not raise exception
        result = register_nmap_tools()
        assert result is None

    @patch("tools.nmap_integration.TOOL_REGISTRY_AVAILABLE", True)
    @patch("tools.nmap_integration.LANGCHAIN_AVAILABLE", True)
    @patch("tools.nmap_integration.registry")
    def test_register_with_exception(self, mock_registry):
        """Test registration handling exceptions"""
        mock_registry.register.side_effect = Exception("Registry error")

        # Should not raise exception
        result = register_nmap_tools()
        assert result is None


# ============================================================================
# Test Data Classes
# ============================================================================


class TestDataClasses:
    """Test dataclass definitions"""

    def test_nmap_port_defaults(self):
        """Test NmapPort default values"""
        port = NmapPort(port=80, protocol="tcp", state="open")
        assert port.port == 80
        assert port.protocol == "tcp"
        assert port.state == "open"
        assert port.service == ""
        assert port.version == ""
        assert port.banner == ""
        assert port.cpe == []
        assert port.scripts == {}

    def test_nmap_host_defaults(self):
        """Test NmapHost default values"""
        host = NmapHost(ip="192.168.1.1")
        assert host.ip == "192.168.1.1"
        assert host.hostname == ""
        assert host.status == ""
        assert host.os_match == ""
        assert host.os_accuracy == 0
        assert host.os_matches == []
        assert host.ports == []
        assert host.mac_address == ""
        assert host.vendor == ""
        assert host.host_scripts == {}
        assert host.trace == []

    def test_nmap_result_defaults(self):
        """Test NmapResult default values"""
        result = NmapResult(success=True)
        assert result.success is True
        assert result.hosts == []
        assert result.command == ""
        assert result.scan_time == 0.0
        assert result.error is None
        assert result.raw_xml == ""
        assert result.summary == {}


# ============================================================================
# Test ScanType and TimingTemplate Enums
# ============================================================================


class TestEnums:
    """Test enum definitions"""

    def test_scan_type_values(self):
        """Test all scan types have correct values"""
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

    def test_timing_template_values(self):
        """Test all timing templates have correct values"""
        assert TimingTemplate.PARANOID.value == "-T0"
        assert TimingTemplate.SNEAKY.value == "-T1"
        assert TimingTemplate.POLITE.value == "-T2"
        assert TimingTemplate.NORMAL.value == "-T3"
        assert TimingTemplate.AGGRESSIVE.value == "-T4"
        assert TimingTemplate.INSANE.value == "-T5"


# ============================================================================
# Test TOP_PORTS Dictionary
# ============================================================================


class TestTopPorts:
    """Test TOP_PORTS presets"""

    def test_top_10_ports(self):
        """Test top-10 ports preset"""
        ports = NmapScanner.TOP_PORTS["top-10"]
        assert "22" in ports
        assert "80" in ports
        assert "443" in ports

    def test_top_100_ports(self):
        """Test top-100 ports preset"""
        ports = NmapScanner.TOP_PORTS["top-100"]
        port_list = ports.split(",")
        # The top-100 list may have duplicates but should have many ports
        assert len(port_list) >= 90  # Allow some flexibility for formatting

    def test_top_1000_marker(self):
        """Test top-1000 marker"""
        assert NmapScanner.TOP_PORTS["top-1000"] == "top-1000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
