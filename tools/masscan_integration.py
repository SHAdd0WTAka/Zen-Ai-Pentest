"""Masscan Integration - Ultra-schneller Port Scanner"""

import subprocess
import logging
import json
from typing import List, Dict

logger = logging.getLogger(__name__)


class MasscanScanner:
    """Async Port Scanner (schneller als Nmap)"""

    def __init__(self, masscan_path: str = "masscan"):
        self.masscan_path = masscan_path

    def scan(self, targets: str, ports: str = "0-65535", rate: int = 10000, interface: str = None) -> List[Dict]:
        """
        Schneller Port Scan.

        Args:
            targets: IP oder Netzwerk (z.B. "10.0.0.0/8")
            ports: Port-Range (z.B. "80,443" oder "0-65535")
            rate: Packets pro Sekunde (höher = schneller, aber lauter)
        """
        output_file = "/tmp/masscan_output.json"

        cmd = [self.masscan_path, targets, "-p", ports, "--rate", str(rate), "-oJ", output_file, "--wait", "0"]

        if interface:
            cmd.extend(["--adapter", interface])

        try:
            logger.info(f"Starte Masscan Scan auf {targets}")
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            # Parse JSON Output
            with open(output_file, "r") as f:
                results = json.load(f)

            return [
                {
                    "ip": r.get("ip", "unknown"),
                    "port": r.get("ports", [{}])[0].get("port", 0),
                    "proto": r.get("ports", [{}])[0].get("proto", "tcp"),
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Masscan Fehler: {e}")
            return []


from langchain_core.tools import tool


@tool
def masscan_quick_scan(target: str, ports: str = "top-100") -> str:
    """Ultra-schneller Port Scan mit Masscan"""
    scanner = MasscanScanner()
    port_range = "80,443,22,21,25,53,110,143,3306,5432,3389,5900,8080" if ports == "top-100" else ports
    results = scanner.scan(target, port_range, rate=1000)
    return f"Found {len(results)} open ports: " + ", ".join([str(r["port"]) for r in results[:20]])
