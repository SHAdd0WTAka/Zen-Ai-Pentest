"""
Tool Orchestrator - Integration with Classic Pentesting Tools
Connects Zen AI Pentest with containerized classic tools via Integration Bridge
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ToolConfig:
    """Configuration for a pentesting tool"""

    name: str
    bridge_endpoint: str
    description: str
    typical_duration: int  # seconds


# Tool registry
PENTEST_TOOLS = {
    "nmap": ToolConfig(
        name="nmap",
        bridge_endpoint="/api/v1/scan/nmap",
        description="Network port scanner with NSE scripting",
        typical_duration=300,
    ),
    "sqlmap": ToolConfig(
        name="sqlmap",
        bridge_endpoint="/api/v1/scan/sqlmap",
        description="Automated SQL injection scanner",
        typical_duration=600,
    ),
    "metasploit": ToolConfig(
        name="metasploit",
        bridge_endpoint="/api/v1/scan/metasploit",
        description="Exploitation framework",
        typical_duration=300,
    ),
    "nuclei": ToolConfig(
        name="nuclei",
        bridge_endpoint="/api/v1/scan/nuclei",
        description="Fast vulnerability scanner",
        typical_duration=600,
    ),
    "gobuster": ToolConfig(
        name="gobuster",
        bridge_endpoint="/api/v1/scan/gobuster",
        description="Directory/file bruteforcer",
        typical_duration=180,
    ),
    "amass": ToolConfig(
        name="amass",
        bridge_endpoint="/api/v1/scan/amass",
        description="Subdomain enumeration",
        typical_duration=300,
    ),
    "wpscan": ToolConfig(
        name="wpscan",
        bridge_endpoint="/api/v1/scan/wpscan",
        description="WordPress vulnerability scanner",
        typical_duration=300,
    ),
    "nikto": ToolConfig(
        name="nikto",
        bridge_endpoint="/api/v1/scan/nikto",
        description="Web server scanner",
        typical_duration=600,
    ),
}


class ToolOrchestrator:
    """
    Orchestrates classic pentesting tools through the Integration Bridge
    """

    def __init__(self, bridge_url: str = "http://integration-bridge:8080"):
        self.bridge_url = bridge_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.active_scans: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if integration bridge is available"""
        try:
            async with self.session.get(f"{self.bridge_url}/health") as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Bridge health check failed: {e}")
            return False

    async def scan_with_nmap(
        self,
        target: str,
        scan_type: str = "tcp_syn",
        ports: str = "top-1000",
        scripts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run Nmap scan against target

        Args:
            target: Target IP/hostname
            scan_type: tcp_syn, tcp_connect, udp, comprehensive
            ports: Port specification (top-1000, all, or specific range)
            scripts: List of NSE scripts to run
        """
        payload = {
            "target": target,
            "scan_type": scan_type,
            "ports": ports,
            "scripts": scripts or [],
        }

        return await self._trigger_scan("nmap", payload)

    async def scan_with_sqlmap(
        self,
        url: str,
        method: str = "GET",
        data: Optional[str] = None,
        level: int = 1,
        risk: int = 1,
    ) -> Dict[str, Any]:
        """
        Run SQLMap scan against URL

        Args:
            url: Target URL
            method: HTTP method
            data: POST data
            level: Test level (1-5)
            risk: Risk level (1-3)
        """
        payload = {
            "target": url,
            "url": url,
            "method": method,
            "data": data,
            "level": level,
            "risk": risk,
        }

        return await self._trigger_scan("sqlmap", payload)

    async def scan_with_nuclei(
        self,
        target: str,
        severity: Optional[str] = None,
        templates: Optional[List[str]] = None,
        concurrency: int = 50,
    ) -> Dict[str, Any]:
        """
        Run Nuclei vulnerability scan

        Args:
            target: Target URL
            severity: Filter by severity (info, low, medium, high, critical)
            templates: Specific templates to run
            concurrency: Number of concurrent requests
        """
        payload = {
            "target": target,
            "options": {
                "severity": severity,
                "templates": templates or [],
                "concurrency": concurrency,
            },
        }

        return await self._trigger_scan("nuclei", payload)

    async def scan_with_gobuster(
        self,
        target: str,
        mode: str = "dir",
        wordlist: str = "/wordlists/dirb/common.txt",
        extensions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run Gobuster directory scan

        Args:
            target: Target URL
            mode: dir, dns, fuzz
            wordlist: Wordlist path
            extensions: File extensions to search
        """
        payload = {
            "target": target,
            "options": {"mode": mode, "wordlist": wordlist, "extensions": extensions},
        }

        return await self._trigger_scan("gobuster", payload)

    async def enumerate_subdomains(
        self, domain: str, active: bool = False
    ) -> Dict[str, Any]:
        """
        Enumerate subdomains with Amass

        Args:
            domain: Target domain
            active: Enable active reconnaissance
        """
        payload = {"target": domain, "options": {"active": active}}

        return await self._trigger_scan("amass", payload)

    async def scan_wordpress(
        self, url: str, enumerate_plugins: bool = True
    ) -> Dict[str, Any]:
        """
        Scan WordPress site with WPScan

        Args:
            url: WordPress site URL
            enumerate_plugins: Enumerate plugins/themes
        """
        payload = {"target": url, "options": {"enumerate": enumerate_plugins}}

        return await self._trigger_scan("wpscan", payload)

    async def run_msf_module(
        self,
        module: str,
        rhosts: str,
        rport: int = 443,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run Metasploit module

        Args:
            module: Metasploit module path
            rhosts: Target hosts
            rport: Target port
            options: Additional module options
        """
        payload = {
            "module": module,
            "rhosts": rhosts,
            "rport": rport,
            "options": options or {},
        }

        return await self._trigger_scan("metasploit", payload)

    async def _trigger_scan(self, tool: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger scan via integration bridge"""
        tool_config = PENTEST_TOOLS.get(tool)
        if not tool_config:
            raise ValueError(f"Unknown tool: {tool}")

        url = f"{self.bridge_url}{tool_config.bridge_endpoint}"

        logger.info(f"Triggering {tool} scan: {payload.get('target', 'N/A')}")

        try:
            async with self.session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(f"Bridge returned {resp.status}: {error_text}")

                result = await resp.json()
                self.active_scans[result["scan_id"]] = {
                    "tool": tool,
                    "target": payload.get("target", "N/A"),
                    "status": "triggered",
                    "start_time": datetime.utcnow(),
                }
                return result

        except Exception as e:
            logger.error(f"Failed to trigger {tool} scan: {e}")
            raise

    async def wait_for_scan(
        self, scan_id: str, poll_interval: int = 10, timeout: int = 3600
    ) -> Dict[str, Any]:
        """
        Wait for scan to complete

        Args:
            scan_id: Scan ID to wait for
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds
        """
        start_time = datetime.utcnow()

        while True:
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout:
                raise TimeoutError(f"Scan {scan_id} timed out after {timeout}s")

            # Get status
            status = await self.get_scan_status(scan_id)
            current_status = status.get("status", "unknown")

            if current_status in ("completed", "failed", "cancelled"):
                return status

            logger.debug(f"Scan {scan_id} status: {current_status}, waiting...")
            await asyncio.sleep(poll_interval)

    async def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get scan status from bridge"""
        url = f"{self.bridge_url}/api/v1/scan/{scan_id}"

        async with self.session.get(url) as resp:
            if resp.status == 404:
                return {"status": "not_found"}
            resp.raise_for_status()
            return await resp.json()

    async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """Get parsed scan results"""
        url = f"{self.bridge_url}/api/v1/scan/{scan_id}/results"

        async with self.session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def run_comprehensive_scan(
        self, target: str, scan_type: str = "web", tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive multi-tool scan

        Args:
            target: Target host/URL
            scan_type: web, network, full
            tools: Specific tools to use (None = auto-select)
        """
        results = {
            "target": target,
            "scan_type": scan_type,
            "start_time": datetime.utcnow().isoformat(),
            "scans": {},
        }

        # Auto-select tools based on scan type
        if not tools:
            if scan_type == "web":
                tools = ["nmap", "nuclei", "gobuster", "nikto"]
            elif scan_type == "network":
                tools = ["nmap", "amass"]
            elif scan_type == "full":
                tools = ["nmap", "nuclei", "gobuster", "amass", "nikto"]

        console.print(
            f"[bold green]Starting comprehensive {scan_type} scan against {target}[/]"
        )
        console.print(f"[dim]Tools: {', '.join(tools)}[/]\n")

        # Run scans concurrently
        scan_tasks = []
        for tool in tools:
            if tool in PENTEST_TOOLS:
                task = self._run_tool_with_progress(tool, target)
                scan_tasks.append((tool, task))

        # Execute all scans
        for tool, task in scan_tasks:
            try:
                scan_result = await task
                results["scans"][tool] = scan_result
                console.print(f"[green]✓[/] {tool} completed")
            except Exception as e:
                console.print(f"[red]✗[/] {tool} failed: {e}")
                results["scans"][tool] = {"error": str(e)}

        results["end_time"] = datetime.utcnow().isoformat()

        return results

    async def _run_tool_with_progress(self, tool: str, target: str) -> Dict[str, Any]:
        """Run tool with progress indication"""
        config = PENTEST_TOOLS[tool]

        with console.status(f"[bold cyan]Running {tool}...[/]"):
            # Trigger scan
            if tool == "nmap":
                result = await self.scan_with_nmap(target)
            elif tool == "nuclei":
                result = await self.scan_with_nuclei(target)
            elif tool == "gobuster":
                result = await self.scan_with_gobuster(target)
            elif tool == "amass":
                result = await self.enumerate_subdomains(target)
            elif tool == "wpscan":
                result = await self.scan_wordpress(target)
            else:
                raise ValueError(f"Tool {tool} not implemented")

            scan_id = result["scan_id"]

            # Wait for completion
            final_status = await self.wait_for_scan(
                scan_id, poll_interval=5, timeout=config.typical_duration * 2
            )

            # Get results
            try:
                scan_results = await self.get_scan_results(scan_id)
            except Exception:
                scan_results = {
                    "status": "completed",
                    "raw": final_status.get("raw_output", ""),
                }

            return {
                "scan_id": scan_id,
                "status": final_status.get("status"),
                "results": scan_results,
                "duration": config.typical_duration,
            }

    def display_scan_summary(self, results: Dict[str, Any]):
        """Display scan results in formatted table"""
        table = Table(title=f"Scan Results: {results['target']}")
        table.add_column("Tool", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Findings", style="yellow")
        table.add_column("Duration", style="dim")

        for tool, result in results.get("scans", {}).items():
            status = result.get("status", "unknown")
            status_emoji = (
                "✓" if status == "completed" else "✗" if "error" in result else "⏳"
            )

            # Count findings if available
            findings = "N/A"
            if "results" in result:
                if isinstance(result["results"], list):
                    findings = str(len(result["results"]))
                elif isinstance(result["results"], dict):
                    findings = str(len(result["results"].get("hosts", [])))

            duration = str(result.get("duration", "N/A"))

            table.add_row(tool, f"{status_emoji} {status}", findings, f"{duration}s")

        console.print(table)


# Convenience functions for direct usage
async def quick_nmap_scan(
    target: str, bridge_url: str = "http://localhost:8080"
) -> Dict[str, Any]:
    """Quick Nmap scan wrapper"""
    async with ToolOrchestrator(bridge_url) as orch:
        result = await orch.scan_with_nmap(target, scan_type="quick")
        return await orch.wait_for_scan(result["scan_id"])


async def quick_web_scan(
    url: str, bridge_url: str = "http://localhost:8080"
) -> Dict[str, Any]:
    """Quick web vulnerability scan with Nuclei"""
    async with ToolOrchestrator(bridge_url) as orch:
        result = await orch.scan_with_nuclei(url)
        return await orch.wait_for_scan(result["scan_id"])


async def find_subdomains(
    domain: str, bridge_url: str = "http://localhost:8080"
) -> List[str]:
    """Enumerate subdomains with Amass"""
    async with ToolOrchestrator(bridge_url) as orch:
        result = await orch.enumerate_subdomains(domain, active=False)
        status = await orch.wait_for_scan(result["scan_id"])

        # Parse results
        results = await orch.get_scan_results(result["scan_id"])
        return results.get("results", [])
