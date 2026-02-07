"""CrackMapExec Integration - SMB/WinRM/LDAP/MSSQL Swiss Army Knife"""

import subprocess
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CrackMapExec:
    """Windows Network Enumeration & Exploitation"""

    def __init__(self, cme_path: str = "crackmapexec"):
        self.cme_path = cme_path

    def smb_enum(self, target: str, username: str = None, password: str = None) -> Dict:
        """SMB Enumeration"""
        cmd = [self.cme_path, "smb", target]

        if username and password:
            cmd.extend(["-u", username, "-p", password])
        else:
            cmd.append('-u""-p""')  # Null session

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"target": target, "output": result.stdout, "accessible": "Pwn3d!" in result.stdout}
        except Exception as e:
            return {"error": str(e)}

    def ldap_enum(self, target: str, domain: str, username: str, password: str) -> Dict:
        """LDAP Enumeration (Users, Groups, etc.)"""
        cmd = [self.cme_path, "ldap", target, "-d", domain, "-u", username, "-p", password, "--users", "--groups"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {"output": result.stdout}
        except Exception as e:
            return {"error": str(e)}

    def mssql_exec(self, target: str, username: str, password: str, command: str) -> str:
        """Führt Befehl auf MSSQL aus"""
        cmd = [self.cme_path, "mssql", target, "-u", username, "-p", password, "-x", command]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout


from langchain_core.tools import tool


@tool
def cme_smb_check(target: str, username: str = "", password: str = "") -> str:
    """Check SMB Zugang mit CrackMapExec"""
    cme = CrackMapExec()
    result = cme.smb_enum(target, username or None, password or None)
    if result.get("accessible"):
        return f"SMB Access granted on {target}!"
    return f"No SMB access on {target}"
