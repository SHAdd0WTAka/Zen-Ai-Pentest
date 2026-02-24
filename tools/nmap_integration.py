"""Nmap Integration - Advanced Network Scanner for Zen-AI-Pentest

This module provides a comprehensive Nmap wrapper with:
- Async/await support
- XML output parsing
- Service detection
- OS detection
- NSE script scanning
- Proper error handling and input validation
- Integration with tool_registry and tool_orchestrator

Author: Zen-AI-Pentest Team
License: MIT
"""

import asyncio
import ipaddress
import logging
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ScanType(Enum):
    """Nmap scan types"""

    SYN = "-sS"  # TCP SYN scan (default, requires root)
    CONNECT = "-sT"  # TCP connect scan
    UDP = "-sU"  # UDP scan
    ACK = "-sA"  # TCP ACK scan
    WINDOW = "-sW"  # TCP Window scan
    MAIMON = "-sM"  # TCP Maimon scan
    FIN = "-sF"  # TCP FIN scan
    NULL = "-sN"  # TCP Null scan
    XMAS = "-sX"  # TCP Xmas scan
    PING = "-sn"  # Ping scan (no port scan)


class TimingTemplate(Enum):
    """Nmap timing templates (-T0 to -T5)"""

    PARANOID = "-T0"  # Slow, serial scan
    SNEAKY = "-T1"  # Slow, less intrusive
    POLITE = "-T2"  # Normal speed with pauses
    NORMAL = "-T3"  # Default
    AGGRESSIVE = "-T4"  # Fast, assumes good network
    INSANE = "-T5"  # Very fast, may lose accuracy


@dataclass
class NmapPort:
    """Represents a scanned port"""

    port: int
    protocol: str
    state: str
    service: str = ""
    version: str = ""
    banner: str = ""
    cpe: List[str] = field(default_factory=list)
    scripts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NmapHost:
    """Represents a scanned host"""

    ip: str
    hostname: str = ""
    status: str = ""
    os_match: str = ""
    os_accuracy: int = 0
    os_matches: List[Dict[str, Any]] = field(default_factory=list)
    ports: List[NmapPort] = field(default_factory=list)
    mac_address: str = ""
    vendor: str = ""
    host_scripts: Dict[str, Any] = field(default_factory=dict)
    trace: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class NmapResult:
    """Complete Nmap scan result"""

    success: bool
    hosts: List[NmapHost] = field(default_factory=list)
    command: str = ""
    scan_time: float = 0.0
    error: Optional[str] = None
    raw_xml: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)


class NmapScanner:
    """
    Advanced Nmap scanner with async support, XML parsing, and comprehensive features.

    Features:
    - Multiple scan types (SYN, Connect, UDP, etc.)
    - Service and version detection
    - OS fingerprinting
    - NSE script scanning
    - Timing templates
    - XML output parsing
    - Input validation
    - Error handling
    """

    # Common port presets
    TOP_PORTS = {
        "top-10": "22,80,443,21,25,53,110,143,3306,3389",
        "top-100": "80,443,22,21,25,53,110,143,3306,5432,3389,5900,8080,8443,8888,3000,5000,8000,"
        "1433,1521,27017,6379,9200,11211,2049,445,139,135,111,33060,5560,5433,5901,"
        "5001,102,2222,3333,4444,5555,6666,7777,9999,10000,10001,10002,1099,1194,1434,1524,1720,1723,1812,2082,2083,2095,2096,2302,2483,2484,30000,3020,3071,3077,3268,3269,3333,4444,5000,5001,5009,5050,5051,5060,5101,5190,5357,5432,5631,5666,5800,5900,6000,6001,6646,7000,7001,7019,7070,7937,7938,8000,8001,8008,8014,8042,8069,8080,8081,8083,8088,8090,8091,8118,8123,8172,8222,8243,8280,8281,8333,8334,8443,8500,8800,8834,8880,8888,8983,9000,9001,9043,9060,9080,9090,9091,9200,9443,9502,9800,9981,9999,10000,10000,10001",
        "top-1000": "top-1000",  # Use nmap's built-in top 1000
    }

    def __init__(
        self,
        target: Union[str, List[str]],
        options: Optional[Dict[str, Any]] = None,
        nmap_path: str = "nmap",
    ):
        """
        Initialize Nmap scanner.

        Args:
            target: Target(s) to scan (IP, hostname, CIDR, or list of targets)
            options: Scan options dictionary
            nmap_path: Path to nmap binary

        Options:
            - ports: Port specification (e.g., "80,443", "1-1000", "top-100")
            - scan_type: ScanType enum value
            - timing: TimingTemplate enum value (default: T3)
            - service_detection: Enable service version detection (-sV)
            - os_detection: Enable OS detection (-O)
            - script_scan: Run NSE scripts (-sC or specific scripts)
            - aggressive: Enable aggressive scan (-A)
            - ping_scan: Ping scan only (-sn)
            - no_ping: Skip host discovery (-Pn)
            - source_port: Set source port (-g)
            - interface: Network interface (-e)
            - max_retries: Maximum retries (--max-retries)
            - host_timeout: Host timeout (--host-timeout)
            - scan_delay: Delay between probes (--scan-delay)
            - max_rate: Maximum packets per second (--max-rate)
            - verbosity: Verbosity level (-v, -vv, -vvv)
            - debugging: Debugging level (-d, -dd)
            - output_file: Output file path
            - additional_args: List of additional nmap arguments
        """
        self.nmap_path = self._validate_nmap_path(nmap_path)
        self.targets = self._validate_targets(target)
        self.options = options or {}

        # Set defaults
        self.options.setdefault("timing", TimingTemplate.NORMAL)
        self.options.setdefault("scan_type", ScanType.SYN)

    def _validate_nmap_path(self, path: str) -> str:
        """Validate nmap binary exists"""
        nmap_path = shutil.which(path)
        if not nmap_path:
            raise RuntimeError(
                f"nmap not found at '{path}'. Please install nmap: "
                "https://nmap.org/download.html"
            )
        return nmap_path

    def _validate_targets(self, targets: Union[str, List[str]]) -> List[str]:
        """Validate and normalize target specifications"""
        if isinstance(targets, str):
            targets = [targets]

        validated = []
        for target in targets:
            target = target.strip()
            if not target:
                continue

            # Check for invalid characters that could lead to command injection
            dangerous_chars = [
                ";",
                "&&",
                "||",
                "|",
                "`",
                "$",
                "(",
                ")",
                "{",
                "}",
                "<",
                ">",
            ]
            if any(char in target for char in dangerous_chars):
                raise ValueError(f"Invalid characters in target: {target}")

            # Validate target format
            try:
                # Try as IP address
                ipaddress.ip_address(target)
                validated.append(target)
                continue
            except ValueError:
                pass

            try:
                # Try as CIDR network
                ipaddress.ip_network(target, strict=False)
                validated.append(target)
                continue
            except ValueError:
                pass

            # Check if it looks like a valid hostname
            hostname_pattern = re.compile(
                r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
            )
            if hostname_pattern.match(target):
                validated.append(target)
            else:
                logger.warning(
                    f"Target '{target}' doesn't look like a valid hostname or IP, but accepting anyway"
                )
                validated.append(target)

        if not validated:
            raise ValueError("No valid targets specified")

        return validated

    def _build_command(self) -> List[str]:
        """Build nmap command from options"""
        cmd = [self.nmap_path]

        # Scan type
        scan_type = self.options.get("scan_type", ScanType.SYN)
        if isinstance(scan_type, ScanType):
            cmd.append(scan_type.value)
        else:
            cmd.append(scan_type)

        # Timing template
        timing = self.options.get("timing", TimingTemplate.NORMAL)
        if isinstance(timing, TimingTemplate):
            cmd.append(timing.value)
        else:
            cmd.append(timing)

        # Ping/no ping
        if self.options.get("ping_scan"):
            cmd.append(ScanType.PING.value)
        elif self.options.get("no_ping"):
            cmd.append("-Pn")

        # Ports
        ports = self.options.get("ports", "")
        if ports:
            if ports in self.TOP_PORTS:
                if ports == "top-1000":
                    cmd.append("--top-ports")
                    cmd.append("1000")
                else:
                    cmd.extend(["-p", self.TOP_PORTS[ports]])
            else:
                cmd.extend(["-p", ports])

        # Service detection
        if self.options.get("service_detection"):
            cmd.append("-sV")
            version_intensity = self.options.get("version_intensity", 7)
            cmd.extend(["--version-intensity", str(version_intensity)])

        # OS detection
        if self.options.get("os_detection"):
            cmd.append("-O")
            osscan_limit = self.options.get("osscan_limit", True)
            if osscan_limit:
                cmd.append("--osscan-limit")

        # Script scanning
        script_scan = self.options.get("script_scan")
        if script_scan:
            if script_scan is True or script_scan == "default":
                cmd.append("-sC")
            elif isinstance(script_scan, str):
                cmd.extend(["--script", script_scan])
            elif isinstance(script_scan, list):
                cmd.extend(["--script", ",".join(script_scan)])

        # Aggressive scan
        if self.options.get("aggressive"):
            cmd.append("-A")

        # Source port
        source_port = self.options.get("source_port")
        if source_port:
            cmd.extend(["-g", str(source_port)])

        # Interface
        interface = self.options.get("interface")
        if interface:
            cmd.extend(["-e", interface])

        # Advanced options
        if "max_retries" in self.options:
            cmd.extend(["--max-retries", str(self.options["max_retries"])])

        if "host_timeout" in self.options:
            cmd.extend(["--host-timeout", str(self.options["host_timeout"])])

        if "scan_delay" in self.options:
            cmd.extend(["--scan-delay", str(self.options["scan_delay"])])

        if "max_rate" in self.options:
            cmd.extend(["--max-rate", str(self.options["max_rate"])])

        # Verbosity and debugging
        verbosity = self.options.get("verbosity", 0)
        if verbosity > 0:
            cmd.append("-" + "v" * min(verbosity, 3))

        debugging = self.options.get("debugging", 0)
        if debugging > 0:
            cmd.append("-" + "d" * min(debugging, 2))

        # XML output (we always use XML for parsing)
        cmd.extend(["-oX", "-"])

        # Additional args
        additional = self.options.get("additional_args", [])
        if additional:
            cmd.extend(additional)

        # Add targets last
        cmd.extend(self.targets)

        return cmd

    def parse_xml_output(self, xml_string: str) -> List[NmapHost]:
        """
        Parse Nmap XML output into structured data.

        Args:
            xml_string: Nmap XML output string

        Returns:
            List of NmapHost objects
        """
        hosts = []

        try:
            root = ET.fromstring(xml_string)

            for host_elem in root.findall(".//host"):
                host = self._parse_host(host_elem)
                if host:
                    hosts.append(host)

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            # Try to extract basic info with regex as fallback
            hosts = self._fallback_parse(xml_string)

        return hosts

    def _parse_host(self, host_elem: ET.Element) -> Optional[NmapHost]:
        """Parse a single host element"""
        try:
            # Get IP address
            ip = ""
            for addr in host_elem.findall("address"):
                if addr.get("addrtype") == "ipv4":
                    ip = addr.get("addr", "")
                elif addr.get("addrtype") == "mac":
                    # MAC address and vendor detected but not used in this version
                    pass

            if not ip:
                return None

            host = NmapHost(ip=ip)

            # Get hostname
            hostnames_elem = host_elem.find("hostnames")
            if hostnames_elem is not None:
                hostname = hostnames_elem.find("hostname")
                if hostname is not None:
                    host.hostname = hostname.get("name", "")

            # Get status
            status = host_elem.find("status")
            if status is not None:
                host.status = status.get("state", "")

            # Get ports
            ports_elem = host_elem.find("ports")
            if ports_elem is not None:
                for port_elem in ports_elem.findall("port"):
                    port = self._parse_port(port_elem)
                    if port:
                        host.ports.append(port)

            # Get OS info
            os_elem = host_elem.find("os")
            if os_elem is not None:
                osmatch = os_elem.find("osmatch")
                if osmatch is not None:
                    host.os_match = osmatch.get("name", "")
                    host.os_accuracy = int(osmatch.get("accuracy", 0))

                # Get all OS matches
                for osmatch in os_elem.findall("osmatch"):
                    host.os_matches.append(
                        {
                            "name": osmatch.get("name", ""),
                            "accuracy": int(osmatch.get("accuracy", 0)),
                            "line": osmatch.get("line", ""),
                        }
                    )

            # Get host scripts
            hostscripts = host_elem.find("hostscript")
            if hostscripts is not None:
                for script in hostscripts.findall("script"):
                    script_id = script.get("id", "")
                    script_output = script.get("output", "")
                    host.host_scripts[script_id] = script_output

            # Get traceroute
            trace = host_elem.find("trace")
            if trace is not None:
                for hop in trace.findall("hop"):
                    host.trace.append(
                        {
                            "ttl": hop.get("ttl", ""),
                            "ipaddr": hop.get("ipaddr", ""),
                            "rtt": hop.get("rtt", ""),
                        }
                    )

            return host

        except Exception as e:
            logger.error(f"Error parsing host: {e}")
            return None

    def _parse_port(self, port_elem: ET.Element) -> Optional[NmapPort]:
        """Parse a single port element"""
        try:
            port_id = int(port_elem.get("portid", 0))
            protocol = port_elem.get("protocol", "tcp")

            state_elem = port_elem.find("state")
            state = (
                state_elem.get("state", "")
                if state_elem is not None
                else "unknown"
            )

            port = NmapPort(port=port_id, protocol=protocol, state=state)

            # Get service info
            service = port_elem.find("service")
            if service is not None:
                port.service = service.get("name", "")
                port.version = service.get("version", "")
                if not port.version and service.get("product"):
                    port.version = service.get("product", "")
                    if service.get("version"):
                        port.version += " " + service.get("version", "")

                # Get CPE
                for cpe in service.findall("cpe"):
                    if cpe.text:
                        port.cpe.append(cpe.text)

            # Get script results
            for script in port_elem.findall("script"):
                script_id = script.get("id", "")
                script_output = script.get("output", "")
                port.scripts[script_id] = script_output

            return port

        except Exception as e:
            logger.error(f"Error parsing port: {e}")
            return None

    def _fallback_parse(self, xml_string: str) -> List[NmapHost]:
        """Fallback regex-based parsing for malformed XML"""
        hosts = []

        # Try to find host elements with regex
        host_pattern = re.compile(r"<host[^>]*>.*?</host>", re.DOTALL)
        for match in host_pattern.finditer(xml_string):
            try:
                host_xml = match.group(0)

                # Extract IP
                ip_match = re.search(
                    r'addr="([^"]+)"\s+addrtype="ipv4"', host_xml
                )
                if ip_match:
                    host = NmapHost(ip=ip_match.group(1))

                    # Extract status
                    status_match = re.search(r'state="([^"]+)"', host_xml)
                    if status_match:
                        host.status = status_match.group(1)

                    hosts.append(host)
            except Exception as e:
                logger.warning(f"Fallback parsing error: {e}")

        return hosts

    async def scan(self, timeout: int = 600) -> NmapResult:
        """
        Execute nmap scan asynchronously.

        Args:
            timeout: Maximum execution time in seconds

        Returns:
            NmapResult with scan results
        """
        import time

        start_time = time.time()
        cmd = self._build_command()
        cmd_str = " ".join(cmd)

        logger.info(f"Starting nmap scan: {cmd_str}")

        try:
            # Run nmap in executor to make it async
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._run_subprocess, cmd),
                timeout=timeout,
            )

            scan_time = time.time() - start_time

            if result.returncode != 0 and not result.stdout:
                return NmapResult(
                    success=False,
                    command=cmd_str,
                    scan_time=scan_time,
                    error=f"nmap failed with code {result.returncode}: {result.stderr}",
                    raw_xml=result.stderr,
                )

            # Parse XML output
            hosts = self.parse_xml_output(result.stdout)

            # Build summary
            summary = {
                "total_hosts": len(hosts),
                "up_hosts": sum(1 for h in hosts if h.status == "up"),
                "total_ports": sum(len(h.ports) for h in hosts),
                "open_ports": sum(
                    1 for h in hosts for p in h.ports if p.state == "open"
                ),
            }

            return NmapResult(
                success=True,
                hosts=hosts,
                command=cmd_str,
                scan_time=scan_time,
                raw_xml=result.stdout,
                summary=summary,
            )

        except asyncio.TimeoutError:
            scan_time = time.time() - start_time
            logger.error(f"Nmap scan timed out after {timeout}s")
            return NmapResult(
                success=False,
                command=cmd_str,
                scan_time=scan_time,
                error=f"Scan timed out after {timeout} seconds",
            )

        except Exception as e:
            scan_time = time.time() - start_time
            logger.error(f"Nmap scan error: {e}")
            return NmapResult(
                success=False,
                command=cmd_str,
                scan_time=scan_time,
                error=str(e),
            )

    def _run_subprocess(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run subprocess (sync, to be called in executor)"""
        return subprocess.run(cmd, capture_output=True, text=True)

    async def scan_ports(
        self,
        ports: str = "top-100",
        scan_type: Union[ScanType, str] = ScanType.SYN,
    ) -> Dict[str, Any]:
        """
        Simple port scan.

        Args:
            ports: Port specification or preset (top-10, top-100, top-1000)
            scan_type: Type of scan to perform

        Returns:
            Dictionary with scan results
        """
        self.options["ports"] = ports
        if isinstance(scan_type, str):
            scan_type = ScanType(scan_type.upper())
        self.options["scan_type"] = scan_type

        result = await self.scan()
        return self._result_to_dict(result)

    async def service_detection(
        self,
        ports: str = "top-100",
        version_intensity: int = 7,
    ) -> Dict[str, Any]:
        """
        Service and version detection scan.

        Args:
            ports: Port specification
            version_intensity: Version detection intensity (0-9)

        Returns:
            Dictionary with scan results
        """
        self.options["ports"] = ports
        self.options["service_detection"] = True
        self.options["version_intensity"] = version_intensity

        result = await self.scan()
        return self._result_to_dict(result)

    async def os_detection(self, ports: str = "top-100") -> Dict[str, Any]:
        """
        OS detection scan.

        Args:
            ports: Port specification

        Returns:
            Dictionary with scan results
        """
        self.options["ports"] = ports
        self.options["os_detection"] = True

        result = await self.scan()
        return self._result_to_dict(result)

    async def run_script(
        self,
        script_name: Union[str, List[str]],
        ports: str = "top-100",
        script_args: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run NSE scripts.

        Args:
            script_name: NSE script name(s)
            ports: Port specification
            script_args: Arguments for scripts (--script-args)

        Returns:
            Dictionary with scan results
        """
        self.options["ports"] = ports
        self.options["script_scan"] = script_name

        if script_args:
            args_str = ",".join(f"{k}={v}" for k, v in script_args.items())
            if "additional_args" not in self.options:
                self.options["additional_args"] = []
            self.options["additional_args"].extend(["--script-args", args_str])

        result = await self.scan()
        return self._result_to_dict(result)

    def _result_to_dict(self, result: NmapResult) -> Dict[str, Any]:
        """Convert NmapResult to dictionary"""
        return {
            "success": result.success,
            "command": result.command,
            "scan_time": result.scan_time,
            "error": result.error,
            "summary": result.summary,
            "hosts": [
                {
                    "ip": h.ip,
                    "hostname": h.hostname,
                    "status": h.status,
                    "os_match": h.os_match,
                    "os_accuracy": h.os_accuracy,
                    "mac_address": h.mac_address,
                    "vendor": h.vendor,
                    "ports": [
                        {
                            "port": p.port,
                            "protocol": p.protocol,
                            "state": p.state,
                            "service": p.service,
                            "version": p.version,
                            "banner": p.banner,
                            "cpe": p.cpe,
                            "scripts": p.scripts,
                        }
                        for p in h.ports
                    ],
                    "host_scripts": h.host_scripts,
                    "trace": h.trace,
                }
                for h in result.hosts
            ],
        }


# Convenience functions for LangChain integration


def create_nmap_result_dict(hosts: List[NmapHost]) -> Dict[str, Any]:
    """Create standardized result dictionary"""
    open_ports = []
    for host in hosts:
        for port in host.ports:
            if port.state == "open":
                open_ports.append(
                    {
                        "host": host.ip,
                        "port": port.port,
                        "protocol": port.protocol,
                        "service": port.service,
                        "version": port.version,
                    }
                )

    return {
        "tool": "nmap",
        "open_ports": open_ports,
        "total_hosts": len(hosts),
        "hosts_up": sum(1 for h in hosts if h.status == "up"),
    }


# LangChain Tool integration
try:
    from langchain_core.tools import tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

    # Define a dummy decorator if langchain is not available
    def tool(func=None, **kwargs):
        if func:
            return func
        return lambda f: f


@tool
def nmap_scan(
    target: str,
    ports: str = "top-100",
    scan_type: str = "syn",
    service_detection: bool = True,
    os_detection: bool = False,
    script_scan: str = "",
) -> str:
    """
    Scan network ports and services using Nmap.

    Args:
        target: Target IP, hostname, or network (e.g., "192.168.1.1", "scanme.nmap.org")
        ports: Port specification - "top-10", "top-100", "top-1000", or custom like "80,443,8080"
        scan_type: Type of scan - "syn" (default), "connect", "udp", "ack", "fin", "null", "xmas"
        service_detection: Enable service version detection
        os_detection: Enable OS fingerprinting (requires privileged access)
        script_scan: Run NSE scripts - "default" for common scripts, or specific like "http-title,vulners"

    Returns:
        Scan results with open ports, services, and OS information
    """
    import asyncio

    options = {
        "ports": ports,
        "scan_type": scan_type.upper(),
        "service_detection": service_detection,
        "os_detection": os_detection,
    }

    if script_scan:
        options["script_scan"] = script_scan

    scanner = NmapScanner(target, options)
    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"Scan failed: {result.error}"

    # Format results
    lines = [
        f"Nmap scan completed in {result.scan_time:.2f}s",
        f"Command: {result.command}",
        "",
    ]

    for host in result.hosts:
        lines.append(f"Host: {host.ip} ({host.hostname})")
        lines.append(f"Status: {host.status}")

        if host.os_match:
            lines.append(
                f"OS: {host.os_match} ({host.os_accuracy}% confidence)"
            )

        lines.append("")
        lines.append("Open Ports:")

        for port in host.ports:
            if port.state == "open":
                service_info = port.service
                if port.version:
                    service_info += f" ({port.version})"
                lines.append(f"  {port.port}/{port.protocol}: {service_info}")

                if port.scripts:
                    for script_id, output in port.scripts.items():
                        lines.append(
                            f"    Script ({script_id}): {output[:100]}"
                        )

        lines.append("")

    return "\n".join(lines)


@tool
def nmap_quick_scan(target: str, ports: str = "top-100") -> str:
    """
    Quick port scan with default options.

    Args:
        target: Target to scan
        ports: Port specification

    Returns:
        Summary of open ports
    """
    import asyncio

    scanner = NmapScanner(target, {"ports": ports, "timing": "-T4"})
    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"Scan failed: {result.error}"

    open_count = sum(
        1 for h in result.hosts for p in h.ports if p.state == "open"
    )

    if open_count == 0:
        return f"No open ports found on {target}"

    return f"Found {open_count} open ports on {target}"


@tool
def nmap_vuln_scan(target: str, ports: str = "top-100") -> str:
    """
    Vulnerability scan using NSE scripts.

    Args:
        target: Target to scan
        ports: Port specification

    Returns:
        Vulnerability scan results
    """
    import asyncio

    options = {
        "ports": ports,
        "script_scan": "vulners,vuln",
        "service_detection": True,
    }

    scanner = NmapScanner(target, options)
    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"Vulnerability scan failed: {result.error}"

    findings = []
    for host in result.hosts:
        for port in host.ports:
            for script_id, output in port.scripts.items():
                if "vuln" in script_id.lower() or "cve" in output.lower():
                    findings.append(
                        f"Port {port.port}: [{script_id}] {output[:200]}"
                    )

    if not findings:
        return f"No obvious vulnerabilities found on {target}"

    return "Potential vulnerabilities found:\n" + "\n".join(findings[:10])


# Tool Registry integration
try:
    from .tool_registry import ToolCategory, ToolSafetyLevel, registry

    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_nmap_tools():
    """Register nmap tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=nmap_scan,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network", "port-scan", "reconnaissance", "nmap"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=nmap_quick_scan,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["network", "port-scan", "quick", "nmap"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=nmap_vuln_scan,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.NORMAL,
            tags=["network", "vulnerability", "nse", "nmap"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        logger.info("Nmap tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register nmap tools: {e}")


# Auto-register on import
try:
    register_nmap_tools()
except Exception:
    pass


__all__ = [
    "NmapScanner",
    "NmapPort",
    "NmapHost",
    "NmapResult",
    "ScanType",
    "TimingTemplate",
    "nmap_scan",
    "nmap_quick_scan",
    "nmap_vuln_scan",
    "register_nmap_tools",
]
