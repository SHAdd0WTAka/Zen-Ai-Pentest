"""
ProtonVPN Integration
=====================

Manages ProtonVPN connection status and provides
security recommendations for penetration testing.

This module is completely optional - the system works
without VPN, but warnings are issued for safety.
"""

import asyncio
import logging
import socket
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("zen.vpn")


class VPNStatus(Enum):
    """VPN connection status"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class VPNInfo:
    """VPN connection information"""

    status: VPNStatus
    provider: Optional[str] = None
    server: Optional[str] = None
    ip: Optional[str] = None
    country: Optional[str] = None
    protocol: Optional[str] = None
    error_message: Optional[str] = None


class ProtonVPNManager:
    """
    Manages ProtonVPN connection via CLI.

    Requires ProtonVPN CLI to be installed:
        pip install protonvpn-cli  # or protonvpn-gui

    Commands used:
    - protonvpn-cli status
    - protonvpn-cli connect
    - protonvpn-cli disconnect
    """

    def __init__(self):
        self.cli_command = "protonvpn-cli"
        self._check_cli_available()

    def _check_cli_available(self) -> bool:
        """Check if ProtonVPN CLI is installed"""
        try:
            result = subprocess.run([self.cli_command, "--version"], capture_output=True, text=True, timeout=5)
            self.cli_available = result.returncode == 0
            if self.cli_available:
                logger.info(f"✅ ProtonVPN CLI found: {result.stdout.strip()}")
            return self.cli_available
        except (subprocess.SubprocessError, FileNotFoundError):
            self.cli_available = False
            logger.debug("ProtonVPN CLI not found - VPN features disabled")
            return False

    def get_status(self) -> VPNInfo:
        """
        Get current ProtonVPN connection status.

        Returns:
            VPNInfo with connection details
        """
        if not self.cli_available:
            return VPNInfo(status=VPNStatus.UNKNOWN, error_message="ProtonVPN CLI not installed")

        try:
            result = subprocess.run([self.cli_command, "status"], capture_output=True, text=True, timeout=10)

            output = result.stdout.lower()

            # Parse status output
            if "connected" in output and "disconnected" not in output:
                return self._parse_connected_status(result.stdout)
            elif "disconnected" in output:
                return VPNInfo(status=VPNStatus.DISCONNECTED, provider="ProtonVPN")
            else:
                return VPNInfo(status=VPNStatus.UNKNOWN, provider="ProtonVPN")

        except subprocess.TimeoutExpired:
            return VPNInfo(status=VPNStatus.ERROR, error_message="Timeout checking VPN status")
        except Exception as e:
            return VPNInfo(status=VPNStatus.ERROR, error_message=f"Error checking VPN: {str(e)}")

    def _parse_connected_status(self, output: str) -> VPNInfo:
        """Parse connected status output"""
        info = VPNInfo(status=VPNStatus.CONNECTED, provider="ProtonVPN")

        lines = output.strip().split("\n")
        for line in lines:
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "server" in key:
                    info.server = value
                elif "ip" in key and "country" not in key:
                    info.ip = value
                elif "country" in key:
                    info.country = value
                elif "protocol" in key:
                    info.protocol = value

        return info

    def connect(self, server: Optional[str] = None) -> bool:
        """
        Connect to ProtonVPN.

        Args:
            server: Optional server to connect to (e.g., "CH#1")

        Returns:
            True if connection successful
        """
        if not self.cli_available:
            logger.error("❌ Cannot connect: ProtonVPN CLI not installed")
            return False

        try:
            cmd = [self.cli_command, "connect"]
            if server:
                cmd.append(server)

            logger.info(f"🔌 Connecting to ProtonVPN{' (' + server + ')' if server else ''}...")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                logger.info("✅ Connected to ProtonVPN")
                return True
            else:
                logger.error(f"❌ Failed to connect: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from ProtonVPN.

        Returns:
            True if disconnection successful
        """
        if not self.cli_available:
            return False

        try:
            result = subprocess.run([self.cli_command, "disconnect"], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                logger.info("🔌 Disconnected from ProtonVPN")
                return True
            else:
                logger.error(f"❌ Failed to disconnect: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Disconnection error: {e}")
            return False

    def is_connected(self) -> bool:
        """Quick check if VPN is connected"""
        info = self.get_status()
        return info.status == VPNStatus.CONNECTED


class GenericVPNDetector:
    """
    Generic VPN detection that works with any VPN provider.

    Detects VPN by:
    - Checking for VPN interfaces (tun0, wg0, etc.)
    - Checking public IP against known VPN ranges
    - Looking for VPN processes
    """

    # Common VPN interface names
    VPN_INTERFACES = ["tun0", "tun1", "wg0", "wg1", "ppp0", "proton0"]

    # Known VPN indicators in public IP ranges
    # These are examples - in production, use a proper IP database
    VPN_ASN_PATTERNS = ["proton", "nordvpn", "expressvpn", "mullvad"]

    def get_status(self) -> VPNInfo:
        """Detect VPN status using generic methods"""

        # Check for VPN interfaces
        vpn_interface = self._check_vpn_interfaces()
        if vpn_interface:
            return VPNInfo(
                status=VPNStatus.CONNECTED, provider=self._detect_provider_from_interface(vpn_interface), server=vpn_interface
            )

        # Check for VPN processes
        if self._check_vpn_processes():
            return VPNInfo(status=VPNStatus.CONNECTED, provider="Unknown (detected via process)")

        return VPNInfo(status=VPNStatus.DISCONNECTED)

    def _check_vpn_interfaces(self) -> Optional[str]:
        """Check for VPN network interfaces"""
        try:
            result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True, timeout=5)

            output = result.stdout.lower()
            for interface in self.VPN_INTERFACES:
                if interface in output:
                    return interface

            # macOS alternative
            result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()
            for interface in self.VPN_INTERFACES:
                if interface in output:
                    return interface

        except Exception:
            pass

        return None

    def _check_vpn_processes(self) -> bool:
        """Check for running VPN processes"""
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)

            output = result.stdout.lower()
            vpn_processes = ["openvpn", "wireguard", "wg", "protonvpn", "nordvpn", "expressvpn", "mullvad"]

            for proc in vpn_processes:
                if proc in output:
                    return True

        except Exception:
            pass

        return False

    def _detect_provider_from_interface(self, interface: str) -> Optional[str]:
        """Try to detect provider from interface name"""
        if "proton" in interface:
            return "ProtonVPN"
        elif "wg" in interface:
            return "WireGuard"
        elif "tun" in interface:
            return "OpenVPN"
        return "Unknown"


class VPNManager:
    """
    High-level VPN manager that combines multiple detection methods.

    Provides:
    - VPN status checking (ProtonVPN + generic)
    - Security recommendations
    - Warning generation
    - Graceful degradation (works without VPN)
    """

    def __init__(self):
        self.proton = ProtonVPNManager()
        self.generic = GenericVPNDetector()
        self._status_callbacks: List[Callable] = []

        # Configuration
        self.recommend_vpn = True  # Issue warnings when VPN not connected
        self.strict_mode = False  # If True, block scans without VPN

    def get_status(self) -> VPNInfo:
        """
        Get VPN status using best available method.

        Priority:
        1. ProtonVPN CLI (most detailed)
        2. Generic detection (any VPN)
        3. Unknown status
        """
        # Try ProtonVPN first
        if self.proton.cli_available:
            status = self.proton.get_status()
            if status.status != VPNStatus.UNKNOWN:
                return status

        # Fall back to generic detection
        return self.generic.get_status()

    def is_connected(self) -> bool:
        """Check if any VPN is connected"""
        return self.get_status().status == VPNStatus.CONNECTED

    def check_before_scan(self, target: str) -> Dict:
        """
        Check VPN status before scanning and return recommendation.

        Args:
            target: Target being scanned

        Returns:
            Dict with:
            - allowed: Whether scan should proceed
            - warning: Optional warning message
            - recommendation: Security recommendation
            - vpn_status: Current VPN status
        """
        status = self.get_status()
        result = {
            "allowed": True,
            "warning": None,
            "recommendation": None,
            "vpn_status": status,
        }

        # If VPN is connected, everything is good
        if status.status == VPNStatus.CONNECTED:
            result["recommendation"] = (
                f"✅ VPN active ({status.provider}) - " f"Server: {status.server or 'unknown'}, " f"IP: {status.ip or 'hidden'}"
            )
            return result

        # VPN not connected - issue warning
        if self.recommend_vpn:
            result["warning"] = (
                "⚠️  WARNING: Scanning without VPN protection!\n"
                "Your real IP address may be exposed to the target.\n"
                "Consider using ProtonVPN: https://protonvpn.com"
            )
            result["recommendation"] = (
                "💡 Recommendation: Connect to ProtonVPN before scanning:\n"
                "   1. Install: pip install protonvpn-cli\n"
                "   2. Login: protonvpn-cli login\n"
                "   3. Connect: protonvpn-cli connect"
            )

        # Strict mode blocks scans without VPN
        if self.strict_mode:
            result["allowed"] = False
            result["warning"] = "❌ SCAN BLOCKED: VPN required in strict mode.\n" "Connect to a VPN before scanning."

        return result

    def set_strict_mode(self, enabled: bool):
        """Enable/disable strict mode (require VPN)"""
        self.strict_mode = enabled
        logger.info(f"🔒 VPN strict mode: {'enabled' if enabled else 'disabled'}")

    def set_recommendations(self, enabled: bool):
        """Enable/disable VPN recommendations"""
        self.recommend_vpn = enabled

    def on_status_change(self, callback: Callable):
        """Register callback for VPN status changes"""
        self._status_callbacks.append(callback)

    async def monitor_connection(self, interval: int = 30):
        """
        Monitor VPN connection status periodically.

        Args:
            interval: Check interval in seconds
        """
        last_status = None

        while True:
            current_status = self.get_status()

            # Notify on status change
            if last_status is None or last_status.status != current_status.status:
                for callback in self._status_callbacks:
                    try:
                        callback(current_status)
                    except Exception as e:
                        logger.error(f"Error in VPN status callback: {e}")

                if current_status.status == VPNStatus.CONNECTED:
                    logger.info(f"🔒 VPN connected: {current_status.provider}")
                elif last_status and last_status.status == VPNStatus.CONNECTED:
                    logger.warning("🔓 VPN disconnected!")

            last_status = current_status
            await asyncio.sleep(interval)


# Convenience functions
def get_vpn_status() -> VPNInfo:
    """Get current VPN status"""
    from vpn import get_vpn_manager

    return get_vpn_manager().get_status()


def is_vpn_connected() -> bool:
    """Check if VPN is connected"""
    from vpn import get_vpn_manager

    return get_vpn_manager().is_connected()


def check_vpn_before_scan(target: str) -> Dict:
    """Check VPN status before scanning"""
    from vpn import get_vpn_manager

    return get_vpn_manager().check_before_scan(target)
