"""Aircrack-ng Integration - Wireless Security Testing"""

import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AircrackSuite:
    """WiFi Security Testing Tools"""

    def __init__(self):
        self.tools = {
            "airmon-ng": "airmon-ng",
            "airodump-ng": "airodump-ng",
            "aireplay-ng": "aireplay-ng",
            "aircrack-ng": "aircrack-ng",
        }

    def set_monitor_mode(self, interface: str) -> str:
        """Aktiviert Monitor Mode auf Interface"""
        try:
            subprocess.run([self.tools["airmon-ng"], "check", "kill"], capture_output=True)
            subprocess.run(
                [self.tools["airmon-ng"], "start", interface],
                capture_output=True,
                text=True,
                check=True,
            )
            return f"Monitor mode enabled on {interface}"
        except Exception as e:
            return f"Error: {str(e)}"

    def stop_monitor_mode(self, interface: str) -> str:
        """Stops monitor mode on interface"""
        try:
            result = subprocess.run(
                [self.tools["airmon-ng"], "stop", interface],
                capture_output=True,
                text=True,
            )
            return f"Monitor mode stopped: {interface}\n{result.stdout}"
        except Exception as e:
            return f"Error: {str(e)}"

    def scan_networks(self, interface: str, duration: int = 30) -> List[Dict]:
        """Scannt nach WLAN-Netzwerken"""
        fd, output_file = tempfile.mkstemp(prefix="airodump_scan_")
        os.close(fd)
        cmd = [
            self.tools["airodump-ng"],
            "-w",
            output_file,
            "--output-format",
            "csv",
            interface,
        ]
        try:
            subprocess.run(cmd, timeout=duration, capture_output=True)
            networks = []
            csv_file = f"{output_file}-01.csv"
            with open(csv_file, "r") as f:
                for line in f:
                    if "," in line and "BSSID" not in line:
                        parts = line.split(",")
                        if len(parts) >= 14:
                            networks.append(
                                {
                                    "bssid": parts[0].strip(),
                                    "channel": parts[3].strip(),
                                    "encryption": parts[5].strip(),
                                    "ssid": parts[13].strip(),
                                }
                            )
            return networks
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return []

    def capture_handshake(
        self,
        bssid: str,
        channel: str,
        interface: str,
        output: str = None,
    ) -> str:
        """Capture WPA Handshake"""
        if output is None:
            fd, output = tempfile.mkstemp(prefix="capture_")
            os.close(fd)
        cmd = [
            self.tools["airodump-ng"],
            "-c",
            channel,
            "--bssid",
            bssid,
            "-w",
            output,
            interface,
        ]
        return f"Start capture: {' '.join(cmd)} (Run manually)"

    def deauth_attack(
        self,
        bssid: str,
        client: str,
        interface: str,
        count: int = 10,
    ) -> str:
        """Send deauthentication packets"""
        cmd = [
            self.tools["aireplay-ng"],
            "-0",
            str(count),
            "-a",
            bssid,
            "-c",
            client,
            interface,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return f"Deauth sent: {count} packets to {client}\n{result.stdout}"
        except subprocess.TimeoutExpired:
            return "Error: Deauth timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def fake_auth(
        self,
        bssid: str,
        interface: str,
        delay: int = 30000,
    ) -> str:
        """Perform fake authentication against AP"""
        cmd = [
            self.tools["aireplay-ng"],
            "-1",
            str(delay),
            "-a",
            bssid,
            interface,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if "Association successful" in result.stdout:
                return f"Fake auth successful: {bssid}\n{result.stdout}"
            return f"Fake auth attempted: {bssid}\n{result.stdout}"
        except subprocess.TimeoutExpired:
            return "Error: Fake auth timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def arp_replay(
        self,
        bssid: str,
        interface: str,
        client: Optional[str] = None,
    ) -> str:
        """ARP replay attack (returns command string without executing)"""
        cmd = [
            self.tools["aireplay-ng"],
            "-3",
            f"-b {bssid}",
        ]
        if client:
            cmd.append(f"-h {client}")
        cmd.append(interface)
        return f"Start ARP replay: {' '.join(cmd)}"

    def crack_wpa(
        self,
        capture_file: str,
        wordlist: str,
        bssid: Optional[str] = None,
    ) -> str:
        """Crackt WPA mit Wordlist"""
        cmd = [self.tools["aircrack-ng"], "-w", wordlist]
        if bssid:
            cmd += ["-b", bssid]
        cmd.append(capture_file)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if "KEY FOUND" in result.stdout:
                return "Password found!"
            return "Password not in wordlist"
        except subprocess.TimeoutExpired:
            return "Error: Cracking timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def crack_wep(
        self,
        capture_file: str,
        key_length: int = 128,
        fudge: int = 2,
    ) -> str:
        """Crack WEP key from capture file"""
        key_bytes = key_length // 8
        cmd = [
            self.tools["aircrack-ng"],
            "-n",
            str(key_bytes),
            "-f",
            str(fudge),
            capture_file,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            if "KEY FOUND!" in result.stdout:
                # Extract key from output line like: KEY FOUND! [ 12:34:56:78:9A ]
                for line in result.stdout.splitlines():
                    if "KEY FOUND!" in line:
                        key = line.split("[")[-1].split("]")[0].strip()
                        return f"WEP Key found: {key}"
                return "WEP Key found!"
            return "Key not found - need more IVs"
        except subprocess.TimeoutExpired:
            return "Error: WEP cracking timeout"
        except Exception as e:
            return f"Error: {str(e)}"

    def crack_pmkid(
        self,
        pmkid_file: str,
        wordlist: str,
    ) -> str:
        """Crack PMKID using hashcat (fallback to aircrack-ng)"""
        # Try hashcat first
        try:
            hashcat_cmd = [
                "hashcat",
                "-m",
                "22000",
                pmkid_file,
                wordlist,
                "--quiet",
            ]
            result = subprocess.run(hashcat_cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0 and ":" in result.stdout:
                return f"PMKID cracked!: {result.stdout.strip()}"
            # Fall through to aircrack fallback on non-zero returncode
        except FileNotFoundError:
            pass  # hashcat not found, fall back to aircrack

        # Fallback: aircrack-ng
        aircrack_cmd = [
            self.tools["aircrack-ng"],
            "-w",
            wordlist,
            pmkid_file,
        ]
        try:
            result = subprocess.run(aircrack_cmd, capture_output=True, text=True, timeout=3600)
            if "KEY FOUND" in result.stdout:
                return "Password found!"
            return "Password not in wordlist"
        except Exception as e:
            return f"Error: {str(e)}"


# LangChain tool decorator with fallback
try:
    from langchain_core.tools import tool
except ImportError:

    class _FunctionTool:
        """Minimal LangChain tool shim."""

        def __init__(self, func):
            self._func = func
            self.name = func.__name__
            self.__doc__ = func.__doc__
            self.__name__ = func.__name__
            self.func = func

        def __call__(self, *args, **kwargs):
            return self._func(*args, **kwargs)

        def invoke(self, input_dict: dict):
            return self._func(**input_dict)

    def tool(func=None, **kwargs):
        if func:
            return _FunctionTool(func)
        return lambda f: _FunctionTool(f)


@tool
def airodump_scan(interface: str = "wlan0mon") -> str:
    """Scannt nach WiFi-Netzwerken"""
    aircrack = AircrackSuite()
    networks = aircrack.scan_networks(interface, duration=30)
    return f"Found {len(networks)} networks"


@tool
def aircrack_wpa(capture_file: str, wordlist: str) -> str:
    """Crackt WPA-Handshake mit Wordlist"""
    aircrack = AircrackSuite()
    return aircrack.crack_wpa(capture_file, wordlist)


@tool
def aireplay_deauth(bssid: str, client: str, interface: str, count: int = 10) -> str:
    """Send deauthentication packets to disconnect a client from AP"""
    suite = AircrackSuite()
    return suite.deauth_attack(bssid, client, interface, count)


@tool
def aireplay_fakeauth(bssid: str, interface: str, delay: int = 30000) -> str:
    """Perform fake authentication against a WEP access point"""
    suite = AircrackSuite()
    return suite.fake_auth(bssid, interface, delay)


@tool
def aireplay_arpreplay(bssid: str, interface: str, client: str = None) -> str:
    """Start ARP replay attack to generate WEP IVs"""
    suite = AircrackSuite()
    return suite.arp_replay(bssid, interface, client)


@tool
def aircrack_wep(capture_file: str, key_length: int = 128, fudge: int = 2) -> str:
    """Crack WEP encryption key from capture file"""
    suite = AircrackSuite()
    return suite.crack_wep(capture_file, key_length, fudge)


@tool
def aircrack_pmkid(pmkid_file: str, wordlist: str) -> str:
    """Crack PMKID hash using hashcat or aircrack-ng"""
    suite = AircrackSuite()
    return suite.crack_pmkid(pmkid_file, wordlist)


@tool
def airmon_stop(interface: str) -> str:
    """Stop monitor mode on wireless interface"""
    suite = AircrackSuite()
    return suite.stop_monitor_mode(interface)


# Alias for tool registry compatibility
aircrack_scan = airodump_scan


if __name__ == "__main__":
    print("Aircrack Integration")
    print("=" * 60)
    print("Available functions:")
    print("  - airodump_scan(interface)")
    print("  - aircrack_wpa(capture_file, wordlist)")
    print("  - aireplay_deauth(bssid, client, interface, count)")
    print("  - aireplay_fakeauth(bssid, interface, delay)")
    print("  - aireplay_arpreplay(bssid, interface, client)")
    print("  - aircrack_wep(capture_file, key_length, fudge)")
    print("  - aircrack_pmkid(pmkid_file, wordlist)")
    print("  - airmon_stop(interface)")
