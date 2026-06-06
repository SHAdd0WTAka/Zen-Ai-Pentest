"""
Enhanced FFUF Integration for Web Fuzzing

This module provides advanced FFUF (Fuzz Faster U Fool) execution
capabilities with multiple modes and output parsing.
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
class FFUFResult:
    """Result of FFUF fuzzing."""

    success: bool
    findings: List[Dict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    target: str = ""
    mode: str = ""
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FFUFEnhancedScanner:
    """
    Enhanced web fuzzer using FFUF.

    Safety Level: NON_DESTRUCTIVE (active but safe fuzzing)
    """

    def __init__(
        self,
        timeout: int = 300,
        threads: int = 40,
        wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    ):
        """
        Initialize FFUF scanner.

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

    async def directory_scan(
        self,
        target_url: str,
        wordlist: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        match_codes: Optional[List[int]] = None,
        filter_codes: Optional[List[int]] = None,
    ) -> FFUFResult:
        """
        Scan for directories and files.

        Args:
            target_url: Target URL with FUZZ keyword
            wordlist: Custom wordlist path
            extensions: File extensions to test
            match_codes: HTTP codes to match
            filter_codes: HTTP codes to filter out

        Returns:
            FFUFResult with findings
        """
        start_time = datetime.now()

        # Validate target
        valid, error = self._validate_target(target_url)
        if not valid:
            return FFUFResult(
                success=False,
                target=target_url,
                mode="directory",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build FFUF command
            cmd = [
                "ffuf",
                "-u",
                target_url,
                "-w",
                wordlist or self.wordlist,
                "-t",
                str(self.threads),
                "-o",
                (lambda fd, path: (os.close(fd), path)[1])(*tempfile.mkstemp(suffix=".json")),
                "-of",
                "json",
                "-s",
            ]

            # Add extensions
            if extensions:
                cmd.extend(["-e", ",".join(extensions)])

            # Add match codes
            if match_codes:
                cmd.extend(["-mc", ",".join(map(str, match_codes))])

            # Add filter codes
            if filter_codes:
                cmd.extend(["-fc", ",".join(map(str, filter_codes))])

            self.logger.info(f"[REAL] Executing FFUF: {' '.join(cmd)}")

            # Execute FFUF
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
                return FFUFResult(
                    success=False,
                    target=target_url,
                    mode="directory",
                    error_message=f"FFUF timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            findings, summary = self._parse_ffuf_json(output)

            return FFUFResult(
                success=True,
                target=target_url,
                mode="directory",
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
            return FFUFResult(
                success=False,
                target=target_url,
                mode="directory",
                error_message="FFUF not found. Install: https://github.com/ffuf/ffuf",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"FFUF execution failed: {e}")
            return FFUFResult(
                success=False,
                target=target_url,
                mode="directory",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def vhost_scan(self, target_ip: str, domain: str, wordlist: Optional[str] = None) -> FFUFResult:
        """
        Scan for virtual hosts.

        Args:
            target_ip: Target IP address
            domain: Base domain
            wordlist: Custom wordlist path

        Returns:
            FFUFResult with findings
        """
        start_time = datetime.now()

        # Validate inputs
        valid, error = self._validate_vhost_inputs(target_ip, domain)
        if not valid:
            return FFUFResult(
                success=False,
                target=f"{target_ip}/{domain}",
                mode="vhost",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build FFUF vhost command
            cmd = [
                "ffuf",
                "-u",
                f"http://{target_ip}/",
                "-H",
                f"Host: FUZZ.{domain}",
                "-w",
                wordlist or self.wordlist,
                "-t",
                str(self.threads),
                "-fs",
                "0",  # Filter by size (customize as needed)
                "-o",
                (lambda fd, path: (os.close(fd), path)[1])(*tempfile.mkstemp(suffix=".json")),
                "-of",
                "json",
            ]

            self.logger.info(f"[REAL] Executing FFUF VHost: {' '.join(cmd)}")

            # Execute FFUF
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
                return FFUFResult(
                    success=False,
                    target=f"{target_ip}/{domain}",
                    mode="vhost",
                    error_message=f"FFUF timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            findings, summary = self._parse_ffuf_json(output)

            return FFUFResult(
                success=True,
                target=f"{target_ip}/{domain}",
                mode="vhost",
                findings=findings,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "wordlist": wordlist or self.wordlist,
                    "threads": self.threads,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return FFUFResult(
                success=False,
                target=f"{target_ip}/{domain}",
                mode="vhost",
                error_message="FFUF not found. Install: https://github.com/ffuf/ffuf",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"FFUF execution failed: {e}")
            return FFUFResult(
                success=False,
                target=f"{target_ip}/{domain}",
                mode="vhost",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def parameter_fuzz(
        self,
        target_url: str,
        parameter: str,
        wordlist: Optional[str] = None,
        method: str = "GET",
    ) -> FFUFResult:
        """
        Fuzz URL parameters.

        Args:
            target_url: Target URL with FUZZ keyword
            parameter: Parameter name to fuzz
            wordlist: Custom wordlist path
            method: HTTP method

        Returns:
            FFUFResult with findings
        """
        start_time = datetime.now()

        # Validate target
        valid, error = self._validate_target(target_url)
        if not valid:
            return FFUFResult(
                success=False,
                target=target_url,
                mode="parameter",
                error_message=f"Validation failed: {error}",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

        try:
            # Build FFUF parameter fuzz command
            cmd = [
                "ffuf",
                "-u",
                target_url,
                "-X",
                method,
                "-d",
                f"{parameter}=FUZZ",
                "-w",
                wordlist or self.wordlist,
                "-t",
                str(self.threads),
                "-o",
                (lambda fd, path: (os.close(fd), path)[1])(*tempfile.mkstemp(suffix=".json")),
                "-of",
                "json",
            ]

            self.logger.info(f"[REAL] Executing FFUF Parameter: {' '.join(cmd)}")

            # Execute FFUF
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
                return FFUFResult(
                    success=False,
                    target=target_url,
                    mode="parameter",
                    error_message=f"FFUF timeout after {self.timeout}s",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Parse results
            findings, summary = self._parse_ffuf_json(output)

            return FFUFResult(
                success=True,
                target=target_url,
                mode="parameter",
                findings=findings,
                summary=summary,
                error_message=stderr_text if stderr_text else None,
                execution_time=execution_time,
                metadata={
                    "parameter": parameter,
                    "method": method,
                    "wordlist": wordlist or self.wordlist,
                    "threads": self.threads,
                    "real_execution": True,
                },
            )

        except FileNotFoundError:
            return FFUFResult(
                success=False,
                target=target_url,
                mode="parameter",
                error_message="FFUF not found. Install: https://github.com/ffuf/ffuf",
                execution_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            self.logger.error(f"FFUF execution failed: {e}")
            return FFUFResult(
                success=False,
                target=target_url,
                mode="parameter",
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    def _validate_target(self, target: str) -> Tuple[bool, str]:
        """Validate target URL."""
        if not target:
            return False, "Target cannot be empty"

        # Check for FUZZ keyword
        if "FUZZ" not in target:
            return False, "Target must contain FUZZ keyword"

        # Check for dangerous characters
        if re.search(r"[;&|<>$`]", target):
            return False, "Invalid characters in target"

        return True, ""

    def _validate_vhost_inputs(self, target_ip: str, domain: str) -> Tuple[bool, str]:
        """Validate vhost scan inputs."""
        if not target_ip:
            return False, "Target IP cannot be empty"

        if not domain:
            return False, "Domain cannot be empty"

        # Validate IP format
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", target_ip):
            return False, "Invalid IP address format"

        return True, ""

    def _parse_ffuf_json(self, output: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Parse FFUF JSON output."""
        findings = []
        summary = {"total": 0, "status_codes": {}}

        try:
            # Try to parse as JSON
            data = json.loads(output)

            if isinstance(data, dict) and "results" in data:
                for result in data["results"]:
                    finding = {
                        "url": result.get("url", ""),
                        "status": result.get("status", 0),
                        "length": result.get("length", 0),
                        "words": result.get("words", 0),
                        "lines": result.get("lines", 0),
                        "redirectlocation": result.get("redirectlocation", ""),
                        "resultfile": result.get("resultfile", ""),
                    }
                    findings.append(finding)

                    # Update summary
                    status = str(finding["status"])
                    summary["status_codes"][status] = summary["status_codes"].get(status, 0) + 1

            summary["total"] = len(findings)

        except json.JSONDecodeError:
            # Parse plain text output
            for line in output.split("\n"):
                if line.strip() and "Status:" in line:
                    # Parse text output format
                    match = re.search(r"Status:\s*(\d+)", line)
                    if match:
                        status = int(match.group(1))
                        findings.append({"status": status, "raw": line.strip()})
                        summary["status_codes"][str(status)] = summary["status_codes"].get(str(status), 0) + 1

            summary["total"] = len(findings)

        return findings, summary


class FFUFTool:
    """Tool wrapper for FFUF integration in agent loop."""

    def __init__(self):
        self.scanner = FFUFEnhancedScanner()

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute FFUF scan and return standardized result."""
        target = parameters.get("target")
        mode = parameters.get("mode", "directory")

        if mode == "directory":
            result = await self.scanner.directory_scan(
                target,
                wordlist=parameters.get("wordlist"),
                extensions=parameters.get("extensions"),
                match_codes=parameters.get("match_codes"),
                filter_codes=parameters.get("filter_codes"),
            )
        elif mode == "vhost":
            result = await self.scanner.vhost_scan(
                parameters.get("target_ip", target),
                parameters.get("domain", ""),
                wordlist=parameters.get("wordlist"),
            )
        elif mode == "parameter":
            result = await self.scanner.parameter_fuzz(
                target,
                parameters.get("parameter", ""),
                wordlist=parameters.get("wordlist"),
                method=parameters.get("method", "GET"),
            )
        else:
            return {
                "tool": "ffuf",
                "success": False,
                "error": f"Unknown mode: {mode}",
            }

        return {
            "tool": "ffuf",
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
        scanner = FFUFEnhancedScanner(timeout=60)

        # Test directory scan
        result = await scanner.directory_scan("http://testphp.vulnweb.com/FUZZ", extensions=[".php", ".html"])

        print(f"Success: {result.success}")
        print(f"Target: {result.target}")
        print(f"Findings: {len(result.findings)}")
        print(f"Summary: {result.summary}")

    asyncio.run(test())
