"""
Trivy Integration for Container and Filesystem Vulnerability Scanning

This module provides Trivy execution capabilities for detecting
vulnerabilities in containers, filesystems, and repositories.
"""

import asyncio
import json
import logging
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from autonomous.tool_executor import SafetyLevel, ToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class TrivyResult:
    """Result of Trivy scan."""

    success: bool
    vulnerabilities: List[Dict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    target: str = ""
    scan_type: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrivyScanner:
    """
    Vulnerability scanner using Trivy.

    Safety Level: READ_ONLY (only reads, doesn't modify)
    """

    SEVERITY_ORDER = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
        "UNKNOWN": 0,
    }

    def __init__(self, timeout: int = 600, severity: Optional[List[str]] = None):
        """
        Initialize Trivy scanner.

        Args:
            timeout: Maximum execution time in seconds
            severity: Severity levels to report (default: all)
        """
        self.timeout = timeout
        self.severity = severity or [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
            "UNKNOWN",
        ]
        self.logger = logging.getLogger(__name__)
        self.executor = ToolExecutor(safety_level=SafetyLevel.READ_ONLY)

    async def scan_image(
        self,
        image_name: str,
        scan_vuln: bool = True,
        scan_config: bool = True,
        scan_secret: bool = False,
    ) -> TrivyResult:
        """
        Scan a container image for vulnerabilities.

        Args:
            image_name: Container image name (e.g., "nginx:latest")
            scan_vuln: Scan for vulnerabilities
            scan_config: Scan for misconfigurations
            scan_secret: Scan for secrets

        Returns:
            TrivyResult with findings
        """
        start_time = datetime.now()

        # Validate image name
        valid, error = self._validate_image_name(image_name)
        if not valid:
            return TrivyResult(
                success=False,
                target=image_name,
                scan_type="image",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build Trivy command
            scanners = []
            if scan_vuln:
                scanners.append("vuln")
            if scan_config:
                scanners.append("config")
            if scan_secret:
                scanners.append("secret")

            if not scanners:
                scanners = ["vuln"]

            severity_str = ",".join(self.severity)

            cmd = [
                "trivy",
                "image",
                "--format",
                "json",
                "--severity",
                severity_str,
                "--scanners",
                ",".join(scanners),
                "--timeout",
                f"{self.timeout}s",
                image_name,
            ]

            self.logger.info(f"[REAL] Executing Trivy: {' '.join(cmd)}")

            # Execute Trivy
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
                return TrivyResult(
                    success=False,
                    target=image_name,
                    scan_type="image",
                    error_message=f"Trivy timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            vulnerabilities, summary = self._parse_trivy_json(output)

            return TrivyResult(
                success=True,
                target=image_name,
                scan_type="image",
                vulnerabilities=vulnerabilities,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "scanners": scanners,
                    "severity_levels": self.severity,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return TrivyResult(
                success=False,
                target=image_name,
                scan_type="image",
                error_message="Trivy not found. Install: https://aquasecurity.github.io/trivy/",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"Trivy execution failed: {e}")
            return TrivyResult(
                success=False,
                target=image_name,
                scan_type="image",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def scan_filesystem(
        self,
        path: str,
        scan_vuln: bool = True,
        scan_config: bool = True,
        scan_secret: bool = True,
    ) -> TrivyResult:
        """
        Scan a filesystem path for vulnerabilities.

        Args:
            path: Filesystem path to scan
            scan_vuln: Scan for vulnerabilities
            scan_config: Scan for misconfigurations
            scan_secret: Scan for secrets

        Returns:
            TrivyResult with findings
        """
        start_time = datetime.now()

        # Validate path
        valid, error = self._validate_path(path)
        if not valid:
            return TrivyResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build Trivy command
            scanners = []
            if scan_vuln:
                scanners.append("vuln")
            if scan_config:
                scanners.append("config")
            if scan_secret:
                scanners.append("secret")

            if not scanners:
                scanners = ["vuln", "config", "secret"]

            severity_str = ",".join(self.severity)

            cmd = [
                "trivy",
                "filesystem",
                "--format",
                "json",
                "--severity",
                severity_str,
                "--scanners",
                ",".join(scanners),
                "--timeout",
                f"{self.timeout}s",
                path,
            ]

            self.logger.info(f"[REAL] Executing Trivy FS: {' '.join(cmd)}")

            # Execute Trivy
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
                return TrivyResult(
                    success=False,
                    target=path,
                    scan_type="filesystem",
                    error_message=f"Trivy timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            vulnerabilities, summary = self._parse_trivy_json(output)

            return TrivyResult(
                success=True,
                target=path,
                scan_type="filesystem",
                vulnerabilities=vulnerabilities,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "scanners": scanners,
                    "severity_levels": self.severity,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return TrivyResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error_message="Trivy not found. Install: https://aquasecurity.github.io/trivy/",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"Trivy execution failed: {e}")
            return TrivyResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def _validate_image_name(self, image_name: str) -> Tuple[bool, str]:
        """Validate container image name."""
        if not image_name:
            return False, "Image name cannot be empty"

        # Check for dangerous characters
        if re.search(r"[;&|<>$`]", image_name):
            return False, "Invalid characters in image name"

        return True, ""

    def _validate_path(self, path: str) -> Tuple[bool, str]:
        """Validate filesystem path."""
        if not path:
            return False, "Path cannot be empty"

        # Check for dangerous characters
        if re.search(r"[;&|<>$`]", path):
            return False, "Invalid characters in path"

        # Prevent path traversal
        if ".." in path:
            return False, "Path traversal not allowed"

        return True, ""

    def _parse_trivy_json(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse Trivy JSON output."""
        vulnerabilities = []
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        }

        try:
            data = json.loads(output)

            if not isinstance(data, dict):
                return vulnerabilities, summary

            # Parse Results
            results = data.get("Results", [])

            for result in results:
                vulns = result.get("Vulnerabilities", [])
                for vuln in vulns:
                    vuln_info = {
                        "vulnerability_id": vuln.get("VulnerabilityID", "UNKNOWN"),
                        "pkg_name": vuln.get("PkgName", ""),
                        "installed_version": vuln.get("InstalledVersion", ""),
                        "fixed_version": vuln.get("FixedVersion", ""),
                        "severity": vuln.get("Severity", "UNKNOWN").upper(),
                        "title": vuln.get("Title", ""),
                        "description": vuln.get("Description", ""),
                        "references": vuln.get("References", []),
                        "primary_url": vuln.get("PrimaryURL", ""),
                        "target": result.get("Target", ""),
                    }

                    vulnerabilities.append(vuln_info)

                    # Update summary
                    severity = vuln_info["severity"].lower()
                    if severity in summary:
                        summary[severity] += 1

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Trivy JSON: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing Trivy output: {e}")

        return vulnerabilities, summary


class TrivyTool:
    """Tool wrapper for Trivy integration in agent loop."""

    def __init__(self):
        self.scanner = TrivyScanner()

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Trivy scan and return standardized result."""
        target = parameters.get("target")
        scan_type = parameters.get("scan_type", "image")

        if scan_type == "image":
            result = await self.scanner.scan_image(target)
        elif scan_type == "filesystem":
            result = await self.scanner.scan_filesystem(target)
        else:
            return {
                "tool": "trivy",
                "success": False,
                "error": f"Unknown scan type: {scan_type}",
            }

        return {
            "tool": "trivy",
            "success": result.success,
            "target": result.target,
            "scan_type": result.scan_type,
            "vulnerabilities": result.vulnerabilities,
            "summary": result.summary,
            "vuln_count": len(result.vulnerabilities),
            "execution_time": result.execution_time,
            "error": result.error_message,
            "metadata": result.metadata,
        }


if __name__ == "__main__":

    async def test():
        scanner = TrivyScanner(timeout=60)

        # Test filesystem scan
        scan_dir = tempfile.mkdtemp()
        result = await scanner.scan_filesystem(scan_dir, scan_vuln=False, scan_config=True)

        print(f"Success: {result.success}")
        print(f"Target: {result.target}")
        print(f"Vulnerabilities: {len(result.vulnerabilities)}")
        print(f"Summary: {result.summary}")

    asyncio.run(test())
