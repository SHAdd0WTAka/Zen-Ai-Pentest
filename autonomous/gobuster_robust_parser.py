"""
Gobuster Robust Parser Module

Provides robust parsing for Gobuster output with multiple format support
and error handling. Uses ToolExecutor for external tool execution.
"""

import asyncio
import json
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
class GobusterResult:
    """Result of Gobuster scan."""

    success: bool
    findings: List[Dict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    target: str = ""
    mode: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class GobusterRobustParser:
    """
    Robust parser for Gobuster output.

    Supports multiple output formats and handles edge cases.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse(self, output: str, mode: str = "dir") -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Parse Gobuster output.

        Args:
            output: Raw Gobuster output
            mode: Scan mode (dir, dns, fuzz, vhost)

        Returns:
            Tuple of (findings, summary)
        """
        if not output or not output.strip():
            return [], {"total": 0, "error": "Empty output"}

        # Try JSON parsing first
        try:
            return self._parse_json(output)
        except (json.JSONDecodeError, ValueError):
            pass

        # Fall back to text parsing
        if mode == "dir":
            return self._parse_dir_output(output)
        elif mode == "dns":
            return self._parse_dns_output(output)
        elif mode == "fuzz":
            return self._parse_fuzz_output(output)
        elif mode == "vhost":
            return self._parse_vhost_output(output)
        else:
            return self._parse_generic_output(output)

    def _parse_json(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse JSON format output."""
        data = json.loads(output)
        findings = []

        if isinstance(data, list):
            for item in data:
                finding = self._extract_finding_from_dict(item)
                if finding:
                    findings.append(finding)
        elif isinstance(data, dict):
            # Handle nested structures
            if "results" in data:
                for item in data["results"]:
                    finding = self._extract_finding_from_dict(item)
                    if finding:
                        findings.append(finding)
            else:
                finding = self._extract_finding_from_dict(data)
                if finding:
                    findings.append(finding)

        summary = self._generate_summary(findings)
        return findings, summary

    def _parse_dir_output(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse directory scan output."""
        findings = []

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse standard Gobuster dir output
            # Format: /path (Status: XXX) [Size: YYY]
            match = re.match(r"(/[^\s]*)\s*\(Status:\s*(\d+)\)\s*\[Size:\s*(\d+)\]", line)
            if match:
                findings.append(
                    {
                        "path": match.group(1),
                        "status": int(match.group(2)),
                        "size": int(match.group(3)),
                        "raw": line,
                    }
                )
            else:
                # Try alternative formats
                alt_match = re.match(r"(/[^\s]*)\s+(\d+)\s+(\d+)", line)
                if alt_match:
                    findings.append(
                        {
                            "path": alt_match.group(1),
                            "status": int(alt_match.group(2)),
                            "size": int(alt_match.group(3)),
                            "raw": line,
                        }
                    )

        summary = self._generate_summary(findings)
        return findings, summary

    def _parse_dns_output(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse DNS scan output."""
        findings = []

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse DNS output
            # Format: subdomain.domain.com [IP1,IP2]
            match = re.match(r"([^\s]+)\s*\[([^\]]+)\]", line)
            if match:
                subdomain = match.group(1)
                ips = [ip.strip() for ip in match.group(2).split(",")]
                findings.append({"subdomain": subdomain, "ips": ips, "raw": line})
            else:
                # Simple subdomain format
                if "." in line and not line.startswith("["):
                    subdomain = line.split()[0]
                    findings.append({"subdomain": subdomain, "ips": [], "raw": line})

        summary = {
            "total": len(findings),
            "unique_subdomains": len(set(f.get("subdomain", "") for f in findings)),
        }
        return findings, summary

    def _parse_fuzz_output(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse fuzz scan output."""
        findings = []

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse fuzz output similar to dir
            match = re.match(r"([^\s]+)\s*\(Status:\s*(\d+)\)\s*\[Size:\s*(\d+)\]", line)
            if match:
                findings.append(
                    {
                        "input": match.group(1),
                        "status": int(match.group(2)),
                        "size": int(match.group(3)),
                        "raw": line,
                    }
                )

        summary = self._generate_summary(findings)
        return findings, summary

    def _parse_vhost_output(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse vhost scan output."""
        findings = []

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse vhost output
            match = re.match(r"([^\s]+)\s*\(Status:\s*(\d+)\)", line)
            if match:
                findings.append(
                    {
                        "vhost": match.group(1),
                        "status": int(match.group(2)),
                        "raw": line,
                    }
                )

        summary = self._generate_summary(findings)
        return findings, summary

    def _parse_generic_output(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse generic output format."""
        findings = []

        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Try to extract any useful information
            finding = {"raw": line}

            # Look for status codes
            status_match = re.search(r"Status:\s*(\d+)", line, re.IGNORECASE)
            if status_match:
                finding["status"] = int(status_match.group(1))

            # Look for sizes
            size_match = re.search(r"Size:\s*(\d+)", line, re.IGNORECASE)
            if size_match:
                finding["size"] = int(size_match.group(1))

            # Look for paths/URLs
            path_match = re.search(r"(/[^\s\[]+)", line)
            if path_match:
                finding["path"] = path_match.group(1)

            findings.append(finding)

        summary = self._generate_summary(findings)
        return findings, summary

    def _extract_finding_from_dict(self, data: Dict) -> Optional[Dict]:
        """Extract finding from dictionary."""
        if not isinstance(data, dict):
            return None

        finding = {}

        # Map common fields
        field_mappings = {
            "url": ["url", "Url", "URL"],
            "path": ["path", "Path", "location", "Location"],
            "status": ["status", "Status", "statusCode", "StatusCode"],
            "size": ["size", "Size", "length", "Length"],
            "subdomain": ["subdomain", "Subdomain", "host", "Host"],
        }

        for key, possible_names in field_mappings.items():
            for name in possible_names:
                if name in data:
                    finding[key] = data[name]
                    break

        # Keep raw data
        finding["_raw"] = data

        return finding if finding else None

    def _generate_summary(self, findings: List[Dict]) -> Dict[str, Any]:
        """Generate summary from findings."""
        summary = {
            "total": len(findings),
            "status_codes": {},
            "size_ranges": {"small": 0, "medium": 0, "large": 0},
        }

        for finding in findings:
            # Count status codes
            status = finding.get("status")
            if status:
                status_str = str(status)
                summary["status_codes"][status_str] = summary["status_codes"].get(status_str, 0) + 1

            # Categorize sizes
            size = finding.get("size", 0)
            if size:
                if size < 1000:
                    summary["size_ranges"]["small"] += 1
                elif size < 10000:
                    summary["size_ranges"]["medium"] += 1
                else:
                    summary["size_ranges"]["large"] += 1

        return summary


class GobusterRobustScanner:
    """
    Gobuster scanner with robust parsing.

    Safety Level: NON_DESTRUCTIVE (active but safe scanning)
    """

    def __init__(
        self,
        timeout: int = 300,
        threads: int = 10,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    ):
        """
        Initialize Gobuster scanner.

        Args:
            timeout: Maximum execution time in seconds
            threads: Number of concurrent threads
            wordlist: Default wordlist path
        """
        self.timeout = timeout
        self.threads = threads
        self.wordlist = wordlist
        self.logger = logging.getLogger(__name__)
        self.executor = ToolExecutor(safety_level=SafetyLevel.NON_DESTRUCTIVE)
        self.parser = GobusterRobustParser()

    async def directory_scan(
        self,
        target_url: str,
        wordlist: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        status_codes: Optional[List[int]] = None,
    ) -> GobusterResult:
        """
        Scan for directories.

        Args:
            target_url: Target URL
            wordlist: Custom wordlist path
            extensions: File extensions to test
            status_codes: Status codes to match

        Returns:
            GobusterResult with findings
        """
        start_time = datetime.now()

        # Validate target
        valid, error = self._validate_target(target_url)
        if not valid:
            return GobusterResult(
                success=False,
                target=target_url,
                mode="dir",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build Gobuster command
            cmd = [
                "gobuster",
                "dir",
                "-u",
                target_url,
                "-w",
                wordlist or self.wordlist,
                "-t",
                str(self.threads),
                "-o",
                (lambda fd, path: (os.close(fd), path)[1])(*tempfile.mkstemp(suffix=".txt")),
            ]

            # Add extensions
            if extensions:
                cmd.extend(["-x", ",".join(extensions)])

            # Add status codes
            if status_codes:
                cmd.extend(["-s", ",".join(map(str, status_codes))])

            self.logger.info(f"[REAL] Executing Gobuster: {' '.join(cmd)}")

            # Execute Gobuster
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
                return GobusterResult(
                    success=False,
                    target=target_url,
                    mode="dir",
                    error_message=f"Gobuster timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            findings, summary = self.parser.parse(output, mode="dir")

            return GobusterResult(
                success=len(findings) > 0,
                target=target_url,
                mode="dir",
                findings=findings,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "wordlist": wordlist or self.wordlist,
                    "extensions": extensions,
                    "threads": self.threads,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return GobusterResult(
                success=False,
                target=target_url,
                mode="dir",
                error_message="Gobuster not found. Install: https://github.com/OJ/gobuster",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"Gobuster execution failed: {e}")
            return GobusterResult(
                success=False,
                target=target_url,
                mode="dir",
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


class GobusterTool:
    """Tool wrapper for Gobuster integration in agent loop."""

    def __init__(self):
        self.scanner = GobusterRobustScanner()

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gobuster scan and return standardized result."""
        target = parameters.get("target")
        mode = parameters.get("mode", "dir")

        if mode == "dir":
            result = await self.scanner.directory_scan(
                target,
                wordlist=parameters.get("wordlist"),
                extensions=parameters.get("extensions"),
                status_codes=parameters.get("status_codes"),
            )
        else:
            return {
                "tool": "gobuster",
                "success": False,
                "error": f"Unknown mode: {mode}",
            }

        return {
            "tool": "gobuster",
            "success": result.success,
            "target": result.target,
            "mode": result.mode,
            "findings": result.findings,
            "finding_count": len(result.findings),
            "summary": result.summary,
            "execution_time": result.execution_time,
            "error": result.error_message,
            "metadata": result.metadata,
        }


if __name__ == "__main__":

    async def test():
        scanner = GobusterRobustScanner(timeout=60)

        # Test directory scan
        result = await scanner.directory_scan("http://testphp.vulnweb.com", extensions=[".php", ".html"])

        print(f"Success: {result.success}")
        print(f"Target: {result.target}")
        print(f"Findings: {len(result.findings)}")
        print(f"Summary: {result.summary}")

    asyncio.run(test())
