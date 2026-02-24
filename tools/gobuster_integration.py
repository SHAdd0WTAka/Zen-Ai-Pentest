"""Gobuster Integration - Directory/File/DNS/VHost Busting"""

import logging
import subprocess
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class GobusterResult:
    url: str
    status_code: int
    size: int
    found: bool


class GobusterScanner:
    def __init__(self, gobuster_path: str = "gobuster"):
        self.gobuster_path = gobuster_path

    def dir_scan(
        self,
        url: str,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
        extensions: str = "php,html,js,txt",
        threads: int = 50,
    ) -> List[GobusterResult]:
        """Directory/File Busting"""
        cmd = [
            self.gobuster_path,
            "dir",
            "-u",
            url,
            "-w",
            wordlist,
            "-x",
            extensions,
            "-t",
            str(threads),
            "-q",  # Quiet mode
            "-o",
            "/tmp/gobuster_output.txt",
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Parse Output
            results = []
            with open("/tmp/gobuster_output.txt", "r") as f:
                for line in f:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            results.append(
                                GobusterResult(
                                    url=parts[0],
                                    status_code=(
                                        int(parts[1])
                                        if parts[1].isdigit()
                                        else 0
                                    ),
                                    size=(
                                        int(parts[2])
                                        if len(parts) > 2
                                        and parts[2].isdigit()
                                        else 0
                                    ),
                                    found=True,
                                )
                            )
            return results
        except Exception as e:
            logger.error(f"Gobuster Fehler: {e}")
            return []

    def dns_scan(
        self,
        domain: str,
        wordlist: str = "/usr/share/wordlists/dnsrecon/subdomains-top1mil.txt",
    ) -> List[str]:
        """DNS Subdomain Enumeration"""
        cmd = [self.gobuster_path, "dns", "-d", domain, "-w", wordlist, "-q"]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            return [
                line.strip()
                for line in result.stdout.split("\\n")
                if line.strip()
            ]
        except Exception as e:
            logger.error(f"DNS Scan Fehler: {e}")
            return []


from langchain_core.tools import tool


@tool
def gobuster_dir_scan(
    url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt"
) -> str:
    """Directory Busting mit Gobuster"""
    scanner = GobusterScanner()
    results = scanner.dir_scan(url, wordlist)
    if results:
        return f"Found {len(results)} directories/files:\\n" + "\\n".join(
            [r.url for r in results[:10]]
        )
    return "No directories found"


@tool
def gobuster_dns_scan(domain: str) -> str:
    """DNS Subdomain Enumeration"""
    scanner = GobusterScanner()
    results = scanner.dns_scan(domain)
    return (
        f"Found {len(results)} subdomains"
        if results
        else "No subdomains found"
    )
