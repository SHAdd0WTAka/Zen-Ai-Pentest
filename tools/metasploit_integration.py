"""Metasploit Framework Integration"""

import subprocess
import logging
import time
from typing import Dict, List

logger = logging.getLogger(__name__)


class MetasploitManager:
    """Wrapper für Metasploit RPC/API"""

    def __init__(self, rpc_host: str = "127.0.0.1", rpc_port: int = 55553):
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.rpc_user = "msf"
        self.rpc_pass = None
        self.client = None

    def start_rpc_server(self, password: str = "zen_pentest") -> bool:
        """Startet Metasploit RPC Server"""
        try:
            # Prüfe ob RPC läuft
            subprocess.run(
                ["msfrpcd", "-P", password, "-S", "-a", self.rpc_host, "-p", str(self.rpc_port)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.rpc_pass = password
            time.sleep(3)  # Warte auf Start
            return True
        except Exception as e:
            logger.error(f"RPC Start Fehler: {e}")
            return False

    def connect_rpc(self) -> bool:
        """Verbindet zu Metasploit RPC"""
        try:
            # pymetasploit3 verwenden falls verfügbar
            from pymetasploit3.msfrpc import MsfRpcClient

            self.client = MsfRpcClient(self.rpc_pass, server=self.rpc_host, port=self.rpc_port)
            logger.info("Metasploit RPC verbunden")
            return True
        except ImportError:
            logger.error("pymetasploit3 nicht installiert: pip install pymetasploit3")
            return False
        except Exception as e:
            logger.error(f"RPC Connect Fehler: {e}")
            return False

    def search_exploits(self, keyword: str) -> List[Dict]:
        """Sucht nach Exploits"""
        if not self.client:
            return []

        try:
            results = self.client.modules.search(keyword)
            return [{"name": r["fullname"], "type": r["type"], "description": r["description"][:100]} for r in results[:10]]
        except Exception as e:
            logger.error(f"Search Fehler: {e}")
            return []

    def execute_exploit(self, exploit_path: str, target: str, payload: str = None, options: Dict = None) -> Dict:
        """
        Führt Exploit aus.

        WARNUNG: Nur für autorisierte Tests!
        """
        if not self.client:
            return {"error": "Not connected to RPC"}

        try:
            # Exploit laden
            exploit = self.client.modules.use("exploit", exploit_path)

            # Optionen setzen
            exploit["RHOSTS"] = target
            if options:
                for key, value in options.items():
                    exploit[key] = value

            # Payload setzen
            if payload:
                exploit.execute(payload=payload)
            else:
                exploit.execute()

            return {"status": "executed", "exploit": exploit_path, "target": target}

        except Exception as e:
            logger.error(f"Exploit Fehler: {e}")
            return {"error": str(e)}

    def run_auxiliary(self, module_path: str, options: Dict) -> Dict:
        """Führt Auxiliary-Modul aus (Scanner etc.)"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            aux = self.client.modules.use("auxiliary", module_path)
            for key, value in options.items():
                aux[key] = value

            result = aux.execute()
            return {"status": "completed", "result": result}
        except Exception as e:
            return {"error": str(e)}

    def get_sessions(self) -> List[Dict]:
        """Listet aktive Meterpreter-Sessions"""
        if not self.client:
            return []

        try:
            sessions = []
            for s in self.client.sessions.list:
                sessions.append({"id": s["session_id"], "type": s["type"], "target": s["session_host"]})
            return sessions
        except Exception:
            return []


# CLI Wrapper für einfache Befehle
class MetasploitCLI:
    """Einfache CLI-Wrapper für msfconsole"""

    @staticmethod
    def run_command(commands: List[str], timeout: int = 60) -> str:
        """Führt msfconsole Befehle aus"""
        rc_file = "/tmp/msf_commands.rc"
        with open(rc_file, "w") as f:
            f.write("\\n".join(commands))

        try:
            result = subprocess.run(["msfconsole", "-r", rc_file, "-q"], capture_output=True, text=True, timeout=timeout)
            return result.stdout
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def generate_payload(payload_type: str, lhost: str, lport: int, format: str = "exe") -> str:
        """Generiert Payload mit msfvenom"""
        output_file = f"/tmp/payload_{int(time.time())}.{format}"

        try:
            result = subprocess.run(
                ["msfvenom", "-p", payload_type, f"LHOST={lhost}", f"LPORT={lport}", "-f", format, "-o", output_file],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return output_file
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"


# LangChain Tools
from langchain_core.tools import tool


@tool
def metasploit_search(keyword: str) -> str:
    """Sucht nach Metasploit Exploits"""
    msf = MetasploitManager()
    if msf.connect_rpc():
        results = msf.search_exploits(keyword)
        return "\\n".join([f"{r['name']}: {r['description']}" for r in results[:5]])
    return "Metasploit RPC nicht verfügbar"


@tool
def msfvenom_generate(payload: str, lhost: str, lport: int) -> str:
    """Generiert Payload mit msfvenom"""
    result = MetasploitCLI.generate_payload(payload, lhost, lport)
    return f"Payload generiert: {result}" if not result.startswith("Error") else result
