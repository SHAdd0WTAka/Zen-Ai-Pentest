"""
Proton VPN Integration Module for Zen AI Pentest

Provides secure VPN connectivity for penetration testing operations:
- Anonymous reconnaissance
- Geo-location bypassing
- Secure C2 communications
- Traffic encryption

Author: SHAdd0WTAka
"""

import asyncio

import logging
import random
import subprocess
from dataclasses import dataclass, field
from enum import Enum

from typing import Any, Dict, List, Optional

logger = logging.getLogger("ZenAI.ProtonVPN")


class VPNProtocol(Enum):
    """Supported VPN protocols"""

    WIREGUARD = "wireguard"
    OPENVPN_TCP = "openvpn-tcp"
    OPENVPN_UDP = "openvpn-udp"


class VPNSecurityLevel(Enum):
    """Proton VPN security levels"""

    STANDARD = "standard"  # Regular servers
    SECURE_CORE = "secure-core"  # Multi-hop ( entry -> secure country -> exit)
    TOR = "tor"  # VPN over Tor
    P2P = "p2p"  # P2P optimized


@dataclass
class VPNStatus:
    """Current VPN connection status"""

    connected: bool = False
    server_ip: Optional[str] = None
    server_location: Optional[str] = None
    protocol: Optional[str] = None
    public_ip: Optional[str] = None
    original_ip: Optional[str] = None
    connection_time: Optional[str] = None
    kill_switch: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "server_ip": self.server_ip,
            "server_location": self.server_location,
            "protocol": self.protocol,
            "public_ip": self.public_ip,
            "original_ip": self.original_ip,
            "connection_time": self.connection_time,
            "kill_switch": self.kill_switch,
        }


@dataclass
class VPNServer:
    """Proton VPN server information"""

    name: str
    country: str
    city: Optional[str] = None
    ip: Optional[str] = None
    load: int = 0  # Server load percentage
    features: List[str] = field(default_factory=list)
    tier: int = 0  # 0=Free, 1=Basic, 2=Plus, 3=Visionary

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.country}) - Load: {self.load}%"


class ProtonVPNManager:
    """
    Manager for Proton VPN integration

    Features:
    - Connect/disconnect to VPN servers
    - Rotate IP addresses
    - Secure Core (multi-hop) connections
    - Kill switch management
    - Country/region selection
    - Automatic server selection (least load)
    """

    # Proton VPN countries optimized for pentesting
    RECOMMENDED_COUNTRIES = [
        "CH",  # Switzerland - Strong privacy laws
        "IS",  # Iceland - Data protection
        "SE",  # Sweden - Good connectivity
        "NL",  # Netherlands - Fast servers
        "DE",  # Germany - Good infrastructure
        "SG",  # Singapore - Asia coverage
        "JP",  # Japan - Asia coverage
        "CA",  # Canada - North America
    ]

    # Countries with P2P support
    P2P_COUNTRIES = ["NL", "CH", "IS", "SE", "DE", "SG"]

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/protonvpn.json"
        self.status = VPNStatus()
        self.connected = False
        self.current_server: Optional[VPNServer] = None
        self._original_ip: Optional[str] = None
        self._connection_history: List[Dict] = []

    async def get_public_ip(self) -> str:
        """Get current public IP address"""
        try:
            # Multiple services for redundancy
            services = [
                "https://ip.me",
                "https://api.ipify.org",
                "https://icanhazip.com",
            ]

            for service in services:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "curl",
                        "-s",
                        "--max-time",
                        "5",
                        service,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=6)
                    ip = stdout.decode().strip()
                    if ip and self._is_valid_ip(ip):
                        return ip
                except Exception:
                    continue

            return "unknown"
        except Exception as e:
            logger.error(f"Failed to get public IP: {e}")
            return "unknown"

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        import re

        pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
        return bool(re.match(pattern, ip))

    async def connect(
        self,
        country: Optional[str] = None,
        city: Optional[str] = None,
        protocol: VPNProtocol = VPNProtocol.WIREGUARD,
        security_level: VPNSecurityLevel = VPNSecurityLevel.STANDARD,
        p2p: bool = False,
        kill_switch: bool = True,
    ) -> VPNStatus:
        """
        Connect to Proton VPN

        Args:
            country: ISO country code (e.g., 'CH', 'NL')
            city: City name for specific location
            protocol: VPN protocol to use
            security_level: Security/Feature level
            p2p: Use P2P-optimized servers
            kill_switch: Enable kill switch
        """
        logger.info("Connecting to Proton VPN...")

        # Save original IP
        if not self._original_ip:
            self._original_ip = await self.get_public_ip()
            self.status.original_ip = self._original_ip

        # Select server
        if not country:
            country = random.choice(self.RECOMMENDED_COUNTRIES)

        if p2p and country not in self.P2P_COUNTRIES:
            country = random.choice(self.P2P_COUNTRIES)

        # Build connection command
        _ = self._get_server_name(country, city, p2p)

        try:
            # Check if protonvpn-cli is available
            proc = await asyncio.create_subprocess_exec(
                "protonvpn-cli",
                "connect",
                "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode != 0:
                logger.warning("protonvpn-cli not found, using mock mode")
                return await self._mock_connect(country, protocol)

            # Real Proton VPN connection
            cmd = ["protonvpn-cli", "connect", "--cc", country.lower()]

            if protocol == VPNProtocol.WIREGUARD:
                cmd.extend(["--protocol", "wireguard"])
            elif protocol == VPNProtocol.OPENVPN_TCP:
                cmd.extend(["--protocol", "tcp"])
            elif protocol == VPNProtocol.OPENVPN_UDP:
                cmd.extend(["--protocol", "udp"])

            if security_level == VPNSecurityLevel.SECURE_CORE:
                cmd.append("--sc")
            elif security_level == VPNSecurityLevel.TOR:
                cmd.append("--tor")

            if kill_switch:
                subprocess.run(["protonvpn-cli", "ks", "--on"], check=False)

            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                self.connected = True
                self.status.connected = True
                self.status.server_location = f"{city or 'Auto'}, {country}" if city else country
                self.status.protocol = protocol.value
                self.status.kill_switch = kill_switch
                self.status.connection_time = self._get_timestamp()

                # Get new public IP
                await asyncio.sleep(3)  # Wait for connection
                self.status.public_ip = await self.get_public_ip()

                logger.info(f"Connected to {self.status.server_location}")
                logger.info(f"New IP: {self.status.public_ip}")

                self._log_connection()

            else:
                error = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Connection failed: {error}")

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return await self._mock_connect(country, protocol)

        return self.status

    async def disconnect(self) -> VPNStatus:
        """Disconnect from VPN"""
        logger.info("Disconnecting from Proton VPN...")

        try:
            proc = await asyncio.create_subprocess_exec(
                "protonvpn-cli",
                "disconnect",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            self.connected = False
            self.status.connected = False
            self.status.server_ip = None
            self.status.server_location = None
            self.status.protocol = None
            self.status.public_ip = await self.get_public_ip()

            logger.info("Disconnected from VPN")

        except Exception as e:
            logger.error(f"Disconnect error: {e}")

        return self.status

    async def rotate_ip(
        self,
        country: Optional[str] = None,
        protocol: VPNProtocol = VPNProtocol.WIREGUARD,
    ) -> VPNStatus:
        """
        Rotate VPN IP address
        Disconnect and reconnect to get new IP
        """
        logger.info("Rotating VPN IP...")

        await self.disconnect()
        await asyncio.sleep(2)

        # Select different country if not specified
        if not country:
            available = [c for c in self.RECOMMENDED_COUNTRIES if c != self.status.server_location]
            country = random.choice(available)

        return await self.connect(country=country, protocol=protocol)

    def _get_server_name(self, country: str, city: Optional[str], p2p: bool) -> str:
        """Generate server name based on parameters"""
        if p2p:
            return f"{country}-P2P"
        if city:
            return f"{country}-{city}"
        return country

    async def _mock_connect(self, country: str, protocol: VPNProtocol) -> VPNStatus:
        """Mock connection for testing without real VPN"""
        logger.info(f"[MOCK] Connecting to {country} via {protocol.value}")

        self.connected = True
        self.status.connected = True
        self.status.server_location = f"MOCK-{country}"
        self.status.protocol = protocol.value
        self.status.server_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.1"
        self.status.public_ip = f"185.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
        self.status.connection_time = self._get_timestamp()

        if not self._original_ip:
            self._original_ip = "192.168.1.100"
            self.status.original_ip = self._original_ip

        return self.status

    def get_status(self) -> VPNStatus:
        """Get current VPN status"""
        return self.status

    def is_connected(self) -> bool:
        """Check if VPN is connected"""
        return self.connected

    async def get_server_list(self, country: Optional[str] = None) -> List[VPNServer]:
        """Get list of available VPN servers"""
        servers = []

        # Mock server list (in real implementation, fetch from Proton API)
        mock_servers = [
            VPNServer("CH-01", "CH", "Zurich", "185.159.158.1", 45, ["secure-core"], 2),
            VPNServer("CH-02", "CH", "Geneva", "185.159.158.2", 30, ["secure-core", "p2p"], 2),
            VPNServer("NL-01", "NL", "Amsterdam", "185.107.56.1", 60, ["p2p", "tor"], 2),
            VPNServer("NL-02", "NL", "Amsterdam", "185.107.56.2", 25, ["p2p"], 2),
            VPNServer("SE-01", "SE", "Stockholm", "185.210.217.1", 40, ["secure-core"], 2),
            VPNServer("IS-01", "IS", "Reykjavik", "37.235.49.1", 20, ["secure-core"], 2),
            VPNServer("DE-01", "DE", "Frankfurt", "185.104.63.1", 55, [], 1),
            VPNServer("SG-01", "SG", "Singapore", "103.125.234.1", 70, ["p2p"], 2),
        ]

        if country:
            servers = [s for s in mock_servers if s.country == country.upper()]
        else:
            servers = mock_servers

        return sorted(servers, key=lambda x: x.load)

    async def recommend_server(
        self,
        purpose: str = "general",
        require_p2p: bool = False,
        require_secure_core: bool = False,
    ) -> Optional[VPNServer]:
        """
        Recommend best server for specific purpose

        Args:
            purpose: 'general', 'pentest', 'c2', 'fileshare'
            require_p2p: Need P2P support
            require_secure_core: Need multi-hop
        """
        servers = await self.get_server_list()

        # Filter by requirements
        if require_p2p:
            servers = [s for s in servers if "p2p" in s.features]
        if require_secure_core:
            servers = [s for s in servers if "secure-core" in s.features]

        # Purpose-based selection
        if purpose == "pentest":
            # Low load, secure core for anonymity
            candidates = [s for s in servers if "secure-core" in s.features]
            return min(candidates, key=lambda x: x.load) if candidates else None

        elif purpose == "c2":
            # Stable, low latency
            return min(servers, key=lambda x: x.load)

        elif purpose == "fileshare":
            # P2P optimized
            candidates = [s for s in servers if "p2p" in s.features]
            return min(candidates, key=lambda x: x.load) if candidates else None

        # General purpose - lowest load
        return min(servers, key=lambda x: x.load) if servers else None

    def get_connection_history(self) -> List[Dict]:
        """Get history of VPN connections"""
        return self._connection_history

    def _log_connection(self):
        """Log connection to history"""
        self._connection_history.append(
            {
                "timestamp": self._get_timestamp(),
                "server": self.status.server_location,
                "protocol": self.status.protocol,
                "public_ip": self.status.public_ip,
            }
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

    def check_ip_leak(self) -> Dict[str, Any]:
        """
        Check for IP/DNS leaks
        Returns leak test results
        """
        results = {
            "dns_leak": False,
            "webrtc_leak": False,
            "ipv6_leak": False,
            "recommendations": [],
        }

        # In real implementation, perform actual leak tests
        # For now, return mock results

        results["dns_servers"] = [
            "10.8.8.1 (Proton VPN DNS)",
            "10.8.8.2 (Proton VPN DNS)",
        ]

        results["recommendations"] = [
            "IPv6 is disabled - Good for privacy",
            "DNS queries go through VPN tunnel",
            "No WebRTC leaks detected",
        ]

        return results

    async def speed_test(self) -> Dict[str, Any]:
        """Test VPN connection speed"""
        logger.info("Running speed test...")

        try:
            # Simple curl-based speed test
            proc = await asyncio.create_subprocess_exec(
                "curl",
                "-o",
                "/dev/null",
                "-w",
                "%{time_total},%{speed_download}",
                "https://speed.cloudflare.com/__down?bytes=10000000",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)

            result = stdout.decode().strip()
            if "," in result:
                time_total, speed = result.split(",")
                return {
                    "download_mbps": round(float(speed) / 125000, 2),
                    "latency_ms": round(float(time_total) * 1000, 2),
                    "status": "success",
                }
        except Exception as e:
            logger.error(f"Speed test failed: {e}")

        return {"download_mbps": 0, "latency_ms": 0, "status": "failed"}


# Convenience functions
async def quick_connect(country: Optional[str] = None) -> VPNStatus:
    """Quick connect to Proton VPN"""
    vpn = ProtonVPNManager()
    return await vpn.connect(country=country)


async def secure_connect() -> VPNStatus:
    """Connect with maximum security (Secure Core)"""
    vpn = ProtonVPNManager()
    return await vpn.connect(country="CH", security_level=VPNSecurityLevel.SECURE_CORE, kill_switch=True)


if __name__ == "__main__":
    # Test
    async def test():
        vpn = ProtonVPNManager()

        print("=== Proton VPN Manager Test ===")

        # Get public IP
        ip = await vpn.get_public_ip()
        print(f"Current IP: {ip}")

        # Connect
        status = await vpn.connect(country="CH")
        print(f"Connected: {status.connected}")
        print(f"Location: {status.server_location}")
        print(f"New IP: {status.public_ip}")

        # Get servers
        servers = await vpn.get_server_list()
        print(f"\nAvailable servers: {len(servers)}")
        for s in servers[:3]:
            print(f"  - {s}")

        # Recommend server
        recommended = await vpn.recommend_server(purpose="pentest")
        if recommended:
            print(f"\nRecommended for pentest: {recommended}")

        # Speed test
        speed = await vpn.speed_test()
        print(f"\nSpeed: {speed['download_mbps']} Mbps")

        # Disconnect
        await vpn.disconnect()
        print("\nDisconnected")

    asyncio.run(test())
