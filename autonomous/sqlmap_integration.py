"""
SQLMap Integration for REAL SQL Injection Testing

This module provides real SQLMap execution capabilities for
detecting and testing SQL injection vulnerabilities.

NO SIMULATIONS - Only real tool execution with safety controls.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SQLMapResult:
    """Result of SQLMap execution."""

    success: bool
    vulnerable: bool
    dbms: Optional[str] = None
    payload: Optional[str] = None
    parameters: List[Dict] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)
    raw_output: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SQLMapScanner:
    """
    SQL Injection Scanner using REAL SQLMap execution.

    Safety Level: DESTRUCTIVE (can modify database)
    Only use with explicit permission and in safe environments.
    """

    def __init__(self, timeout: int = 600, level: int = 1, risk: int = 1):
        """
        Initialize SQLMap scanner.

        Args:
            timeout: Maximum execution time in seconds
            level: Detection level (1-5, higher = more thorough)
            risk: Risk level (1-3, higher = more aggressive)
        """
        self.timeout = timeout
        self.level = min(max(level, 1), 5)  # Clamp 1-5
        self.risk = min(max(risk, 1), 3)  # Clamp 1-3
        self.logger = logging.getLogger(__name__)

    async def scan_target(
        self,
        target_url: str,
        method: str = "GET",
        data: Optional[str] = None,
        cookies: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> SQLMapResult:
        """
        Scan a target URL for SQL injection vulnerabilities.

        Args:
            target_url: URL to scan (e.g., "http://example.com/page.php?id=1")
            method: HTTP method (GET or POST)
            data: POST data if method is POST
            cookies: Cookie string
            headers: Additional HTTP headers

        Returns:
            SQLMapResult with findings
        """
        import asyncio.subprocess

        start_time = datetime.now()

        # Safety checks
        valid, error = self._validate_target(target_url)
        if not valid:
            return SQLMapResult(
                success=False,
                vulnerable=False,
                error_message=f"Safety check failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build SQLMap command
            cmd = [
                "sqlmap",
                "-u",
                target_url,
                "--batch",  # Non-interactive mode
                "--level",
                str(self.level),
                "--risk",
                str(self.risk),
                "--json",  # JSON output
                "--tamper=space2comment",  # Basic tamper
                "--random-agent",  # Rotate user agents
                "--timeout",
                str(self.timeout),
                "--retries",
                "2",
            ]

            if method.upper() == "POST" and data:
                cmd.extend(["--data", data])

            if cookies:
                cmd.extend(["--cookie", cookies])

            if headers:
                for key, value in headers.items():
                    cmd.extend(["--header", f"{key}: {value}"])

            # CRITICAL SAFETY: Disable destructive operations by default
            cmd.append("--no-union")  # No UNION-based injection tests
            cmd.append("--no-exploit")  # No exploitation
            cmd.append("--no-stored")  # No stored procedure tests

            self.logger.info(f"[REAL] Executing SQLMap: {' '.join(cmd)}")

            # Execute SQLMap
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return SQLMapResult(
                    success=False,
                    vulnerable=False,
                    error_message=f"SQLMap timeout after {self.timeout}s",
                    execution_time=(
                        datetime.now() - start_time
                    ).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            vulnerable, dbms, payload, parameters = self._parse_sqlmap_output(
                output
            )

            findings = []
            if vulnerable:
                findings.append(
                    {
                        "type": "sql_injection",
                        "severity": "critical",
                        "dbms": dbms,
                        "payload": payload,
                        "parameters": parameters,
                        "description": f"SQL Injection vulnerability detected in {target_url}",
                    }
                )

            return SQLMapResult(
                success=True,
                vulnerable=vulnerable,
                dbms=dbms,
                payload=payload,
                parameters=parameters,
                findings=findings,
                raw_output=output,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "target": target_url,
                    "method": method,
                    "level": self.level,
                    "risk": self.risk,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return SQLMapResult(
                success=False,
                vulnerable=False,
                error_message="SQLMap not found. Install: https://sqlmap.org/",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"SQLMap execution failed: {e}")
            return SQLMapResult(
                success=False,
                vulnerable=False,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def _validate_target(self, target: str) -> Tuple[bool, str]:
        """Validate target for safety."""
        import ipaddress

        # Check URL format
        if not re.match(r"^https?://", target):
            return False, "Target must start with http:// or https://"

        # Extract host
        try:
            from urllib.parse import urlparse

            parsed = urlparse(target)
            host = parsed.hostname

            # Check if private IP
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private and not ip.is_loopback:
                    return False, f"Private IP {host} blocked"
            except ValueError:
                pass  # Not an IP, probably a domain

        except Exception as e:
            return False, f"Invalid URL: {e}"

        # Check for dangerous characters
        if re.search(r"[;&|<>$`]", target):
            return False, "Invalid characters in target"

        return True, ""

    def _parse_sqlmap_output(
        self, output: str
    ) -> Tuple[bool, Optional[str], Optional[str], List[Dict]]:
        """
        Parse SQLMap output to extract vulnerability information.

        Returns:
            Tuple of (vulnerable, dbms, payload, parameters)
        """
        vulnerable = False
        dbms = None
        payload = None
        parameters = []

        lines = output.split("\n")

        for line in lines:
            # Check for vulnerability detection
            if "is vulnerable" in line.lower() or "injectable" in line.lower():
                vulnerable = True

            # Extract DBMS
            if "back-end DBMS:" in line:
                match = re.search(
                    r"back-end DBMS:\s*(.+)", line, re.IGNORECASE
                )
                if match:
                    dbms = match.group(1).strip()

            # Extract payload
            if "payload:" in line.lower():
                match = re.search(r"[Pp]ayload:\s*(.+)", line)
                if match:
                    payload = match.group(1).strip()

            # Extract parameter info
            if "parameter" in line.lower() and (
                "get" in line.lower() or "post" in line.lower()
            ):
                match = re.search(
                    r"(\w+)\s+parameter\s+\'([^\']+)\'", line, re.IGNORECASE
                )
                if match:
                    param_type = match.group(1).upper()
                    param_name = match.group(2)
                    parameters.append({"type": param_type, "name": param_name})

        return vulnerable, dbms, payload, parameters


# Tool integration for agent_loop.py
class SQLMapTool:
    """Tool wrapper for SQLMap integration in agent loop."""

    def __init__(self):
        self.scanner = SQLMapScanner()

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQLMap scan and return standardized result."""
        target = parameters.get("target")
        method = parameters.get("method", "GET")
        data = parameters.get("data")

        result = await self.scanner.scan_target(
            target, method=method, data=data
        )

        return {
            "tool": "sqlmap",
            "success": result.success,
            "vulnerable": result.vulnerable,
            "findings": result.findings,
            "dbms": result.dbms,
            "execution_time": result.execution_time,
            "error": result.error_message,
            "metadata": result.metadata,
        }


if __name__ == "__main__":
    # Test
    async def test():
        scanner = SQLMapScanner(timeout=60, level=1, risk=1)

        # Test against deliberately vulnerable test target
        # Note: Only test against targets you own or have permission to test
        result = await scanner.scan_target(
            "http://testphp.vulnweb.com/artists.php?artist=1"
        )

        print(f"Success: {result.success}")
        print(f"Vulnerable: {result.vulnerable}")
        if result.vulnerable:
            print(f"DBMS: {result.dbms}")
            print(f"Payload: {result.payload}")
        print(f"Execution time: {result.execution_time:.2f}s")

    asyncio.run(test())
