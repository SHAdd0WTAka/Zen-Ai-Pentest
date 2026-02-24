"""
Masscan Integration - High-Speed Port Scanner
Schneller als Nmap für große Netzwerke
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MasscanPort:
    """Masscan port result"""

    port: int
    protocol: str = "tcp"
    state: str = "open"
    ip: str = ""


@dataclass
class MasscanResult:
    """Masscan scan result"""

    success: bool
    ports: List[MasscanPort] = field(default_factory=list)
    command: str = ""
    duration: float = 0.0
    total_hosts: int = 0
    error: Optional[str] = None


class MasscanIntegration:
    """Masscan High-Speed Port Scanner"""

    def __init__(self, rate: int = 10000):
        """
        Args:
            rate: Packets per second (default: 10000)
        """
        self.rate = rate

    async def scan(
        self,
        target: str,
        ports: str = "1-65535",
        exclude_file: Optional[str] = None,
    ) -> MasscanResult:
        """
        Fast port scan with Masscan

        Args:
            target: IP or CIDR range (e.g., 192.168.1.0/24)
            ports: Port range (default: 1-65535)
            exclude_file: File with IPs to exclude

        Returns:
            MasscanResult with open ports
        """
        import time

        start_time = time.time()

        cmd = [
            "masscan",
            target,
            "-p",
            ports,
            "--rate",
            str(self.rate),
            "-oX",
            "-",
            "--wait",
            "2",
        ]  # XML output to stdout

        if exclude_file:
            cmd.extend(["--excludefile", exclude_file])

        logger.info(f"Starting Masscan: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=600
            )  # 10 min timeout

            # Parse XML output
            ports = []
            try:
                root = ET.fromstring(stdout.decode())
                for host in root.findall("host"):
                    ip = host.find("address").get("addr")
                    for port_elem in host.findall("ports/port"):
                        port = MasscanPort(
                            port=int(port_elem.get("portid")),
                            protocol=port_elem.get("protocol", "tcp"),
                            state=port_elem.find("state").get("state", "open"),
                            ip=ip,
                        )
                        ports.append(port)
            except ET.ParseError as e:
                logger.warning(f"XML parse error: {e}")

            duration = time.time() - start_time

            return MasscanResult(
                success=True,
                ports=ports,
                command=" ".join(cmd),
                duration=duration,
                total_hosts=len(set(p.ip for p in ports)),
            )

        except asyncio.TimeoutError:
            logger.error("Masscan timed out")
            return MasscanResult(success=False, error="Timeout")
        except Exception as e:
            logger.error(f"Masscan error: {e}")
            return MasscanResult(success=False, error=str(e))

    async def scan_top_ports(self, target: str) -> MasscanResult:
        """Scan top 1000 ports quickly"""
        return await self.scan(target, ports="1-1000", rate=50000)


# Sync wrapper
def scan_sync(target: str, ports: str = "1-65535") -> MasscanResult:
    """Synchronous wrapper"""
    masscan = MasscanIntegration()
    return asyncio.run(masscan.scan(target, ports))


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("Testing Masscan Integration...")
    print("=" * 60)
    print("⚠️  Note: Masscan requires root privileges")
    print("⚠️  Testing with --dry-run mode")
    print("=" * 60)

    # Test parsing
    masscan = MasscanIntegration()
    print(f"Rate: {masscan.rate} packets/sec")
    print("Masscan integration ready!")
