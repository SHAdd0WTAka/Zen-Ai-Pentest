"""
OWASP ZAP Integration for Web Application Security Scanning

This module provides ZAP (Zed Attack Proxy) execution capabilities
for automated web application security testing.
"""

import asyncio
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from autonomous.tool_executor import SafetyLevel, ToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class ZAPResult:
    """Result of ZAP scan."""

    success: bool
    alerts: List[Dict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    target: str = ""
    scan_type: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ZAPScanner:
    """
    Web application scanner using OWASP ZAP.

    Safety Level: NON_DESTRUCTIVE (active scanning but safe)
    """

    RISK_LEVELS = {"Informational": 0, "Low": 1, "Medium": 2, "High": 3}

    def __init__(
        self,
        timeout: int = 600,
        zap_path: str = "zap.sh",
        api_url: str = "http://localhost:8080",
    ):
        """
        Initialize ZAP scanner.

        Args:
            timeout: Maximum execution time in seconds
            zap_path: Path to ZAP executable
            api_url: ZAP API URL (for daemon mode)
        """
        self.timeout = timeout
        self.zap_path = zap_path
        self.api_url = api_url
        self.logger = logging.getLogger(__name__)
        self.executor = ToolExecutor(safety_level=SafetyLevel.NON_DESTRUCTIVE)

    async def quick_scan(
        self,
        target_url: str,
        spider: bool = True,
        ajax_spider: bool = False,
        active_scan: bool = True,
    ) -> ZAPResult:
        """
        Perform a quick scan of a target URL.

        Args:
            target_url: URL to scan
            spider: Run traditional spider
            ajax_spider: Run AJAX spider
            active_scan: Run active scanner

        Returns:
            ZAPResult with findings
        """
        start_time = datetime.now()

        # Validate target
        valid, error = self._validate_target(target_url)
        if not valid:
            return ZAPResult(
                success=False,
                target=target_url,
                scan_type="quick",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build ZAP command
            cmd = [
                self.zap_path,
                "-cmd",
                "-quickurl",
                target_url,
                "-quickprogress",
                "-quickout",
                (lambda fd, path: (os.close(fd), path)[1])(*tempfile.mkstemp(suffix=".json")),
            ]

            # Add scan options
            if not spider:
                cmd.extend(["-spider", "false"])
            if ajax_spider:
                cmd.append("-ajaxSpider")
            if not active_scan:
                cmd.extend(["-activeScan", "false"])

            self.logger.info(f"[REAL] Executing ZAP: {' '.join(cmd)}")

            # Execute ZAP
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ZAPResult(
                    success=False,
                    target=target_url,
                    scan_type="quick",
                    error_message=f"ZAP timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results from output
            alerts, summary = self._parse_zap_output(output)

            return ZAPResult(
                success=True,
                target=target_url,
                scan_type="quick",
                alerts=alerts,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "spider": spider,
                    "ajax_spider": ajax_spider,
                    "active_scan": active_scan,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return ZAPResult(
                success=False,
                target=target_url,
                scan_type="quick",
                error_message="ZAP not found. Install: https://www.zaproxy.org/download/",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"ZAP execution failed: {e}")
            return ZAPResult(
                success=False,
                target=target_url,
                scan_type="quick",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def baseline_scan(self, target_url: str, context_file: Optional[str] = None) -> ZAPResult:
        """
        Perform a baseline scan (spider + passive scan only).

        Args:
            target_url: URL to scan
            context_file: Optional ZAP context file

        Returns:
            ZAPResult with findings
        """
        start_time = datetime.now()

        # Validate target
        valid, error = self._validate_target(target_url)
        if not valid:
            return ZAPResult(
                success=False,
                target=target_url,
                scan_type="baseline",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build ZAP baseline command
            cmd = [self.zap_path, "-cmd", "-baseline", target_url]

            if context_file:
                cmd.extend(["-context", context_file])

            self.logger.info(f"[REAL] Executing ZAP Baseline: {' '.join(cmd)}")

            # Execute ZAP
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ZAPResult(
                    success=False,
                    target=target_url,
                    scan_type="baseline",
                    error_message=f"ZAP timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            alerts, summary = self._parse_zap_output(output)

            return ZAPResult(
                success=True,
                target=target_url,
                scan_type="baseline",
                alerts=alerts,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "context_file": context_file,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return ZAPResult(
                success=False,
                target=target_url,
                scan_type="baseline",
                error_message="ZAP not found. Install: https://www.zaproxy.org/download/",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"ZAP execution failed: {e}")
            return ZAPResult(
                success=False,
                target=target_url,
                scan_type="baseline",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def _validate_target(self, target: str) -> Tuple[bool, str]:
        """Validate target URL."""
        if not target:
            return False, "Target cannot be empty"

        # Check URL format
        if not re.match(r"^https?://", target):
            return False, "Target must start with http:// or https://"

        # Check for dangerous characters
        if re.search(r"[;&|<>$`]", target):
            return False, "Invalid characters in target"

        return True, ""

    def _parse_zap_output(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse ZAP output to extract alerts."""
        alerts = []
        summary = {"informational": 0, "low": 0, "medium": 0, "high": 0}

        lines = output.split("\n")
        current_alert = None

        for line in lines:
            line = line.strip()

            # Parse alert lines
            if line.startswith("[WARN]") or line.startswith("[INFO]"):
                # Extract alert information
                alert_match = re.search(r"\[(\w+)\]\s+(.+?)\s*\[(\d+)\]", line)
                if alert_match:
                    level = alert_match.group(1)
                    name = alert_match.group(2)
                    plugin_id = alert_match.group(3)

                    risk_level = "Informational"
                    if level == "WARN":
                        risk_level = "Medium"

                    alert = {
                        "name": name,
                        "risk": risk_level,
                        "confidence": "Medium",
                        "plugin_id": plugin_id,
                        "description": "",
                        "solution": "",
                        "reference": "",
                        "instances": [],
                    }
                    alerts.append(alert)
                    current_alert = alert

                    # Update summary
                    risk_key = risk_level.lower()
                    if risk_key in summary:
                        summary[risk_key] += 1

            # Parse alert details
            if current_alert:
                if line.startswith("Description:"):
                    current_alert["description"] = line.replace("Description:", "").strip()
                elif line.startswith("Solution:"):
                    current_alert["solution"] = line.replace("Solution:", "").strip()
                elif line.startswith("Reference:"):
                    current_alert["reference"] = line.replace("Reference:", "").strip()

        return alerts, summary


class ZAPTool:
    """Tool wrapper for ZAP integration in agent loop."""

    def __init__(self):
        self.scanner = ZAPScanner()

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ZAP scan and return standardized result."""
        target = parameters.get("target")
        scan_type = parameters.get("scan_type", "quick")

        if scan_type == "quick":
            result = await self.scanner.quick_scan(
                target,
                spider=parameters.get("spider", True),
                ajax_spider=parameters.get("ajax_spider", False),
                active_scan=parameters.get("active_scan", True),
            )
        elif scan_type == "baseline":
            result = await self.scanner.baseline_scan(target, context_file=parameters.get("context_file"))
        else:
            return {
                "tool": "zap",
                "success": False,
                "error": f"Unknown scan type: {scan_type}",
            }

        return {
            "tool": "zap",
            "success": result.success,
            "target": result.target,
            "scan_type": result.scan_type,
            "alerts": result.alerts,
            "alert_count": len(result.alerts),
            "summary": result.summary,
            "execution_time": result.execution_time,
            "error": result.error_message,
            "metadata": result.metadata,
        }


if __name__ == "__main__":

    async def test():
        scanner = ZAPScanner(timeout=60)

        # Test baseline scan
        result = await scanner.baseline_scan("http://testphp.vulnweb.com")

        print(f"Success: {result.success}")
        print(f"Target: {result.target}")
        print(f"Alerts: {len(result.alerts)}")
        print(f"Summary: {result.summary}")

    asyncio.run(test())
