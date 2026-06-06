"""SQLMap Integration für automatisierte SQL Injection Tests"""

import logging
import subprocess
import tempfile
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SQLMapScanner:
    """Wrapper für SQLMap SQL Injection Scanner"""

    def __init__(self, sqlmap_path: str = "sqlmap"):
        self.sqlmap_path = sqlmap_path
        self.check_installation()

    def check_installation(self):
        """Prüft ob sqlmap installiert ist"""
        try:
            result = subprocess.run([self.sqlmap_path, "--version"], capture_output=True, text=True)
            logger.info(f"SQLMap verfügbar: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError("sqlmap nicht gefunden. Installieren: pip install sqlmap")

    def scan_url(
        self,
        url: str,
        risk: int = 1,
        level: int = 1,
        batch: bool = True,
        dump: bool = False,
    ) -> Dict:
        """
        Scannt URL auf SQL Injection.

        Args:
            url: Ziel-URL mit Parametern
            risk: 1-3 (höher = riskanter)
            level: 1-5 (höher = gründlicher)
            batch: Keine User-Interaktion
            dump: Daten dumpen (nur autorisiert!)
        """
        cmd = [
            self.sqlmap_path,
            "-u",
            url,
            "--risk",
            str(risk),
            "--level",
            str(level),
            "--batch" if batch else "",
            "--dump" if dump else "",
            "--output-dir",
            tempfile.mkdtemp(prefix="sqlmap_"),
            "--format",
            "json",
        ]

        # Leere Strings entfernen
        cmd = [c for c in cmd if c]

        try:
            logger.info(f"Starte SQLMap Scan: {url}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Parse Output
            output = {
                "url": url,
                "vulnerable": "sqlmap identified" in result.stdout.lower(),
                "stdout": (result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout),
                "stderr": result.stderr,
            }

            return output

        except subprocess.TimeoutExpired:
            return {"url": url, "error": "Timeout after 300s"}
        except Exception as e:
            return {"url": url, "error": str(e)}

    def scan_form(self, url: str, data: str, risk: int = 1, level: int = 1) -> Dict:
        """Scannt POST Form auf SQL Injection"""
        cmd = [
            self.sqlmap_path,
            "-u",
            url,
            "--data",
            data,
            "--risk",
            str(risk),
            "--level",
            str(level),
            "--batch",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "url": url,
                "vulnerable": "sqlmap identified" in result.stdout.lower(),
                "output": result.stdout[-3000:],
            }
        except Exception as e:
            return {"url": url, "error": str(e)}

    def get_databases(self, url: str) -> List[str]:
        """Listet Datenbanken auf (nur autorisiert!)"""
        cmd = [self.sqlmap_path, "-u", url, "--dbs", "--batch"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            # Parse databases from output
            databases = []
            for line in result.stdout.split("\n"):
                if "available databases" in line.lower():
                    # Nächste Zeilen enthalten DB-Namen
                    pass
            return databases
        except Exception as e:
            logger.error(f"Fehler: {e}")
            return []


# LangChain Tool
try:
    from langchain_core.tools import tool
except ImportError:

    class _FunctionTool:
        """Minimal LangChain tool shim."""

        def __init__(self, func):
            self._func = func
            self.name = func.__name__
            self.__doc__ = func.__doc__
            self.__name__ = func.__name__

        def __call__(self, *args, **kwargs):
            return self._func(*args, **kwargs)

        def invoke(self, input_dict: dict):
            return self._func(**input_dict)

    def tool(func=None, **kwargs):
        if func:
            return _FunctionTool(func)
        return lambda f: _FunctionTool(f)


@tool
def sqlmap_scan(url: str, risk: int = 1, level: int = 1) -> str:
    """
    Scannt URL auf SQL Injection Vulnerabilities.

    Args:
        url: Ziel-URL (z.B. "http://target.com/page.php?id=1")
        risk: 1-3 (höher = aggressiver)
        level: 1-5 (höher = gründlicher)
    """
    scanner = SQLMapScanner()
    result = scanner.scan_url(url, risk=risk, level=level, dump=False)

    if result.get("vulnerable"):
        return f"SQL Injection gefunden in {url}!"
    elif "error" in result:
        return f"Fehler: {result['error']}"
    else:
        return f"Keine SQL Injection in {url} gefunden."


@tool
def sqlmap_scan_form(url: str, data: str) -> str:
    """Scannt POST Form auf SQL Injection"""
    scanner = SQLMapScanner()
    result = scanner.scan_form(url, data)
    return "Vulnerable" if result.get("vulnerable") else "Not vulnerable"


async def run_sqlmap(url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Async sqlmap runner - can be patched in tests."""
    scanner = SQLMapScanner()
    return scanner.scan_url(url, **(options or {}))


async def run_sqlmap_form(url: str, data: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Async sqlmap form runner - can be patched in tests."""
    scanner = SQLMapScanner()
    return scanner.scan_form(url, data)
