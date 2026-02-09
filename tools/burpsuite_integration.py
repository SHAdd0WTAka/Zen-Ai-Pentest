"""BurpSuite Integration"""

import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BurpSuiteAPI:
    """BurpSuite Enterprise/Professional API Integration"""

    def __init__(self, api_url: str, api_key: str, verify_ssl: Optional[bool] = None, ca_bundle: Optional[str] = None):
        """
        Initialize BurpSuite API client.
        
        Args:
            api_url: BurpSuite API URL
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificates (default: True, use env BURP_VERIFY_SSL to override)
            ca_bundle: Path to CA bundle for SSL verification
        """
        import requests
        
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Authorization": api_key, "Content-Type": "application/json"}
        
        # SSL verification - default to True, allow override via environment
        env_verify = os.getenv("BURP_VERIFY_SSL", "").lower()
        if verify_ssl is not None:
            self.verify_ssl = verify_ssl
        elif env_verify in ("false", "0", "no", "off"):
            logger.warning("SSL verification disabled via BURP_VERIFY_SSL environment variable - NOT RECOMMENDED")
            self.verify_ssl = False
        else:
            self.verify_ssl = True
            
        self.ca_bundle = ca_bundle or os.getenv("BURP_CA_BUNDLE")

    def get_sites(self) -> List[Dict]:
        """Listet konfigurierte Sites"""
        import requests
        try:
            resp = requests.get(
                f"{self.api_url}/v1/sites", 
                headers=self.headers, 
                verify=self.ca_bundle if self.ca_bundle else self.verify_ssl
            )
            resp.raise_for_status()
            return resp.json().get("sites", [])
        except Exception as e:
            logger.error(f"Burp API Fehler: {e}")
            return []

    def start_scan(self, site_id: str, scan_configuration: str = "Crawl and Audit") -> str:
        """Startet Scan auf Site"""
        import requests
        try:
            data = {"site_id": site_id, "scan_configuration": scan_configuration}
            resp = requests.post(
                f"{self.api_url}/v1/scans", 
                headers=self.headers, 
                json=data, 
                verify=self.ca_bundle if self.ca_bundle else self.verify_ssl
            )
            resp.raise_for_status()
            return resp.json().get("scan_id", "")
        except Exception as e:
            logger.error(f"Scan Start Fehler: {e}")
            return ""

    def get_scan_results(self, scan_id: str) -> Dict:
        """Holt Scan-Ergebnisse"""
        import requests
        try:
            resp = requests.get(
                f"{self.api_url}/v1/scans/{scan_id}/issues", 
                headers=self.headers, 
                verify=self.ca_bundle if self.ca_bundle else self.verify_ssl
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}


class BurpSuiteHeadless:
    """Headless BurpSuite für CI/CD"""

    def __init__(self, burp_jar: str = "/usr/share/burpsuite/burpsuite.jar"):
        self.burp_jar = burp_jar

    def run_scan(self, target_url: str, config_file: str = None) -> Dict:
        """Führt headless Scan durch"""
        import subprocess

        cmd = [
            "java",
            "-jar",
            self.burp_jar,
            "--project-file=/tmp/burp_project.tmp",
            "--config-file=" + (config_file or ""),
            "--unpause-spider-and-scanner",
            target_url,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            return {"success": result.returncode == 0, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}


# LangChain Tool
from langchain_core.tools import tool


@tool
def burp_scan_url(url: str) -> str:
    """Scannt URL mit BurpSuite (Enterprise API)"""
    # Konfiguration aus Umgebung
    import os

    api_url = os.getenv("BURP_API_URL", "http://localhost:8080")
    api_key = os.getenv("BURP_API_KEY", "")

    if not api_key:
        return "BurpSuite API Key nicht konfiguriert"

    burp = BurpSuiteAPI(api_url, api_key)
    sites = burp.get_sites()
    return f"Found {len(sites)} sites in BurpSuite"
