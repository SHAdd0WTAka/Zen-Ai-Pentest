"""
TShark Integration - Network Traffic Analysis
Wireshark CLI für automatisierte Netzwerk-Analyse
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TSharkHost:
    """Discovered host"""
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    ports: List[int] = field(default_factory=list)


@dataclass
class TSharkProtocol:
    """Protocol statistics"""
    name: str
    count: int
    percentage: float


@dataclass
class TSharkResult:
    """TShark analysis result"""
    success: bool
    capture_file: str = ""
    hosts: List[TSharkHost] = field(default_factory=list)
    protocols: List[TSharkProtocol] = field(default_factory=list)
    statistics: Dict = field(default_factory=dict)
    error: Optional[str] = None


class TSharkIntegration:
    """
    TShark Network Analysis Integration

    Features:
    - PCAP file analysis
    - Live capture (short duration)
    - Protocol statistics
    - Host discovery
    - Traffic analysis
    """

    def __init__(self, interface: Optional[str] = None):
        self.interface = interface or "eth0"

    async def analyze_pcap(self, pcap_file: str) -> TSharkResult:
        """
        Analyze existing PCAP file

        Args:
            pcap_file: Path to PCAP file

        Returns:
            TSharkResult with analysis
        """
        if not Path(pcap_file).exists():
            return TSharkResult(
                success=False,
                error=f"PCAP file not found: {pcap_file}"
            )

        # Get protocol statistics
        stats_cmd = [
            "tshark", "-r", pcap_file,
            "-q", "-z", "io,phs"
        ]

        # Get unique hosts
        hosts_cmd = [
            "tshark", "-r", pcap_file,
            "-T", "fields", "-e", "ip.src", "-e", "ip.dst",
            "-E", "header=y"
        ]

        try:
            # Run statistics
            stats_process = await asyncio.create_subprocess_exec(
                *stats_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stats_stdout, _ = await asyncio.wait_for(
                stats_process.communicate(), timeout=60
            )

            # Run host extraction
            hosts_process = await asyncio.create_subprocess_exec(
                *hosts_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            hosts_stdout, _ = await asyncio.wait_for(
                hosts_process.communicate(), timeout=60
            )

            # Parse results
            protocols = self._parse_protocols(stats_stdout.decode())
            hosts = self._parse_hosts(hosts_stdout.decode())

            return TSharkResult(
                success=True,
                capture_file=pcap_file,
                hosts=hosts,
                protocols=protocols,
                statistics={
                    "total_hosts": len(hosts),
                    "total_protocols": len(protocols),
                    "file_size": Path(pcap_file).stat().st_size
                }
            )

        except asyncio.TimeoutError:
            logger.error("TShark analysis timed out")
            return TSharkResult(success=False, error="Timeout")
        except Exception as e:
            logger.error(f"TShark error: {e}")
            return TSharkResult(success=False, error=str(e))

    async def capture_live(
        self,
        duration: int = 60,
        filter_expr: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> TSharkResult:
        """
        Perform live network capture

        Args:
            duration: Capture duration in seconds
            filter_expr: BPF filter expression
            output_file: Output PCAP file path

        Returns:
            TSharkResult with capture results
        """
        if output_file is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/tmp/capture_{timestamp}.pcap"

        cmd = [
            "tshark",
            "-i", self.interface,
            "-a", f"duration:{duration}",
            "-w", output_file
        ]

        if filter_expr:
            cmd.extend(["-f", filter_expr])

        logger.info(f"Starting live capture for {duration}s on {self.interface}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=duration + 30
            )

            if process.returncode != 0:
                error = stderr.decode().strip()
                logger.error(f"TShark capture failed: {error}")
                return TSharkResult(success=False, error=error)

            # Analyze captured file
            return await self.analyze_pcap(output_file)

        except asyncio.TimeoutError:
            logger.error("TShark capture timed out")
            return TSharkResult(success=False, error="Capture timeout")
        except Exception as e:
            logger.error(f"TShark capture error: {e}")
            return TSharkResult(success=False, error=str(e))

    def _parse_protocols(self, output: str) -> List[TSharkProtocol]:
        """Parse protocol hierarchy statistics"""
        protocols = []
        lines = output.split('\n')

        for line in lines:
            # Look for protocol lines like "  tcp: packets: 100 bytes: 5000"
            match = re.search(r'^\s+(\w+):\s+packets:\s+(\d+)', line)
            if match:
                protocols.append(TSharkProtocol(
                    name=match.group(1),
                    count=int(match.group(2)),
                    percentage=0.0  # Would need total for percentage
                ))

        return protocols

    def _parse_hosts(self, output: str) -> List[TSharkHost]:
        """Parse unique hosts from output"""
        hosts = {}
        lines = output.strip().split('\n')

        for line in lines[1:]:  # Skip header
            if not line:
                continue
            parts = line.split('\t')
            for ip in parts:
                ip = ip.strip()
                if ip and ip not in hosts:
                    hosts[ip] = TSharkHost(ip=ip)

        return list(hosts.values())


# Sync wrappers
def analyze_pcap_sync(pcap_file: str) -> TSharkResult:
    """Synchronous wrapper for PCAP analysis"""
    tshark = TSharkIntegration()
    return asyncio.run(tshark.analyze_pcap(pcap_file))


def capture_live_sync(
    duration: int = 60,
    interface: str = "eth0",
    output_file: Optional[str] = None
) -> TSharkResult:
    """Synchronous wrapper for live capture"""
    tshark = TSharkIntegration(interface=interface)
    return asyncio.run(tshark.capture_live(duration, output_file=output_file))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Testing TShark Integration...")
    print("="*60)
    print("Note: Requires root privileges for live capture")
    print("="*60)

    # Test with sample PCAP if available
    sample_pcap = "/tmp/test.pcap"
    if Path(sample_pcap).exists():
        result = analyze_pcap_sync(sample_pcap)
        print(f"\nAnalyzed: {result.capture_file}")
        print(f"Hosts found: {len(result.hosts)}")
        print(f"Protocols: {[p.name for p in result.protocols]}")
    else:
        print("TShark integration ready (no test pcap available)")
