"""Aircrack-ng Integration - Wireless Security Testing"""

import logging
import subprocess
from typing import Dict, List

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
            # Stop interfering processes
            subprocess.run(
                [self.tools["airmon-ng"], "check", "kill"], capture_output=True
            )

            # Start monitor mode
            subprocess.run(
                [self.tools["airmon-ng"], "start", interface],
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Monitor mode enabled on {interface}"
        except Exception as e:
            return f"Error: {str(e)}"

    def scan_networks(self, interface: str, duration: int = 30) -> List[Dict]:
        """Scannt nach WLAN-Netzwerken"""
        output_file = "/tmp/airodump_scan"

        cmd = [
            self.tools["airodump-ng"],
            "-w",
            output_file,
            "--output-format",
            "csv",
            interface,
        ]

        try:
            # Run for specified duration
            subprocess.run(cmd, timeout=duration, capture_output=True)

            # Parse CSV
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
        output: str = "/tmp/capture",
    ) -> str:
        """Capture WPA Handshake"""
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

    def crack_wpa(self, capture_file: str, wordlist: str) -> str:
        """Crackt WPA mit Wordlist"""
        cmd = [
            self.tools["aircrack-ng"],
            "-w",
            wordlist,
            "-b",
            "",  # BSSID
            capture_file,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600
            )
            if "KEY FOUND" in result.stdout:
                return "Password found!"
            return "Password not in wordlist"
        except Exception as e:
            return f"Error: {str(e)}"


from langchain_core.tools import tool


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
