"""Amass Integration - Attack Surface Management"""

import subprocess
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class AmassRecon:
    """Subdomain Enumeration & Network Mapping"""

    def __init__(self, amass_path: str = "amass"):
        self.amass_path = amass_path

    def enum_subdomains(self, domain: str, passive: bool = True, timeout: int = 30) -> List[str]:
        """Enumerate Subdomains"""
        mode = "passive" if passive else "active"
        output_file = f"/tmp/amass_{domain}.txt"

        cmd = [self.amass_path, mode, "-d", domain, "-o", output_file, "-timeout", str(timeout)]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)

            with open(output_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Amass Fehler: {e}")
            return []

    def intel(self, domain: str) -> Dict:
        """Sammelt Intelligence über Organisation"""
        cmd = [self.amass_path, "intel", "-d", domain, "-whois"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"domain": domain, "intel": result.stdout.split("\\n")}
        except Exception as e:
            return {"error": str(e)}


from langchain_core.tools import tool


@tool
def amass_enum(domain: str) -> str:
    """Subdomain Enumeration mit Amass"""
    amass = AmassRecon()
    results = amass.enum_subdomains(domain)
    return f"Found {len(results)} subdomains for {domain}"
