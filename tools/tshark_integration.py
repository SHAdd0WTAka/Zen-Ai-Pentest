"""Tshark/Wireshark Integration für Zen-AI-Pentest"""

import subprocess
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TsharkAnalyzer:
    """Headless Wireshark für Traffic-Analyse"""

    def __init__(self):
        self.tshark_path = self._find_tshark()

    def _find_tshark(self) -> str:
        """Findet tshark binary"""
        import shutil

        path = shutil.which("tshark")
        if not path:
            raise RuntimeError("tshark nicht gefunden. Installieren: apt install tshark")
        return path

    def capture_to_pcap(self, interface: str, duration: int, output_file: str) -> bool:
        """Captures Traffic zu PCAP Datei"""
        try:
            cmd = [self.tshark_path, "-i", interface, "-a", f"duration:{duration}", "-w", output_file]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"Capture Fehler: {e}")
            return False

    def analyze_pcap(self, pcap_file: str, display_filter: str = "") -> List[Dict]:
        """Analysiert PCAP Datei"""
        try:
            cmd = [self.tshark_path, "-r", pcap_file, "-T", "json"]
            if display_filter:
                cmd.extend(["-Y", display_filter])

            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.loads(result.stdout) if result.stdout else []
        except Exception as e:
            logger.error(f"Analyse Fehler: {e}")
            return []

    def extract_http_requests(self, pcap_file: str) -> List[Dict]:
        """Extrahiert HTTP Requests aus PCAP"""
        packets = self.analyze_pcap(pcap_file, "http.request")
        requests = []
        for pkt in packets:
            try:
                http = pkt.get("_source", {}).get("layers", {}).get("http", {})
                requests.append(
                    {
                        "method": http.get("http.request.method"),
                        "uri": http.get("http.request.uri"),
                        "host": http.get("http.host"),
                    }
                )
            except Exception:
                pass
        return requests

    def get_statistics(self, pcap_file: str) -> Dict:
        """Gibt Traffic-Statistiken"""
        try:
            # Protocol Hierarchy
            cmd = [self.tshark_path, "-r", pcap_file, "-q", "-z", "io,phs"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            return {"pcap_file": pcap_file, "statistics": result.stdout}
        except Exception as e:
            logger.error(f"Stats Fehler: {e}")
            return {}


# LangChain Tool
from langchain_core.tools import tool


@tool
def tshark_capture(interface: str, duration: int, output: str) -> str:
    """Capture Network Traffic zu PCAP"""
    analyzer = TsharkAnalyzer()
    success = analyzer.capture_to_pcap(interface, duration, output)
    return f"Capture {'successful' if success else 'failed'}: {output}"


@tool
def tshark_analyze_pcap(pcap_file: str, filter_expr: str = "") -> str:
    """Analysiert PCAP Datei"""
    analyzer = TsharkAnalyzer()
    packets = analyzer.analyze_pcap(pcap_file, filter_expr)
    return f"Analyzed {len(packets)} packets"
