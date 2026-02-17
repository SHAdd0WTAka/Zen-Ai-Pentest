"""OWASP ZAP Integration - Web Application Security Scanner for Zen-AI-Pentest

This module provides a comprehensive OWASP ZAP wrapper with:
- Spider/crawl functionality
- Active scan with various policies
- Passive scan
- AJAX spider
- API scan support
- Report generation (HTML, XML, JSON)
- Async scanning support
- Progress callbacks
- Findings normalization

Author: Zen-AI-Pentest Team
License: MIT
"""

import asyncio
import logging
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ZAPScanPolicy(Enum):
    """ZAP scan policies for active scanning"""

    DEFAULT = "Default Policy"
    SQL_INJECTION = "SQL Injection"
    XSS = "Cross Site Scripting (Reflected)"
    DIRECTORY_BROWSING = "Directory Browsing"
    CSRF = "Cross Site Request Forgery"
    COMMAND_INJECTION = "Command Injection"
    LDAP_INJECTION = "LDAP Injection"
    XPATH_INJECTION = "XPath Injection"
    XML_EXTERNAL_ENTITY = "XML External Entity Attack"
    SERVER_SIDE_INCLUDE = "Server Side Include"
    PATH_TRAVERSAL = "Path Traversal"


class ZAPAlertRisk(Enum):
    """ZAP alert risk levels"""

    INFORMATIONAL = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class ZAPAlert:
    """Represents a ZAP security alert/finding"""

    alert_id: str
    name: str
    risk: str
    confidence: str
    description: str
    solution: str
    reference: str
    cwe_id: str = ""
    wasc_id: str = ""
    sourceid: str = ""
    url: str = ""
    method: str = ""
    attack: str = ""
    evidence: str = ""
    other_info: str = ""
    param: str = ""


@dataclass
class ZAPScanResult:
    """Complete ZAP scan result"""

    success: bool
    target: str
    scan_type: str
    alerts: List[ZAPAlert] = field(default_factory=list)
    scan_time: float = 0.0
    error: Optional[str] = None
    scan_id: Optional[str] = None
    progress: int = 0
    urls_crawled: int = 0
    urls_audited: int = 0


class ZAPScanner:
    """
    Advanced OWASP ZAP scanner with async support and comprehensive features.

    Features:
    - Spider/crawl functionality
    - Active scan with various policies
    - Passive scan
    - AJAX spider for modern web apps
    - API scan support
    - Report generation (HTML, XML, JSON)
    - Async scanning support
    - Progress callbacks
    - Findings normalization
    """

    DEFAULT_API_PORT = 8080
    DEFAULT_DAEMON_PORT = 8080

    def __init__(
        self,
        target: str,
        api_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        zap_path: str = "zap",
        use_docker: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ZAP scanner.

        Args:
            target: Target URL to scan
            api_url: ZAP API URL (default: http://localhost:8080)
            api_key: ZAP API key for authentication
            zap_path: Path to ZAP executable
            use_docker: Use Docker to run ZAP
            options: Scan options dictionary

        Options:
            - spider: Enable spider scan (default: True)
            - ajax_spider: Enable AJAX spider (default: False)
            - active_scan: Enable active scan (default: True)
            - scan_policy: Scan policy for active scan
            - recursion_depth: Spider recursion depth (default: 5)
            - context_name: ZAP context name
            - user_agent: Custom user agent
            - max_children: Maximum children to crawl
            - excluded_urls: List of URLs to exclude
            - scan_timeout: Scan timeout in seconds (default: 600)
            - progress_callback: Callback function for progress updates
        """
        self.target = target
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.zap_path = zap_path
        self.use_docker = use_docker
        self.options = options or {}

        # Set defaults
        self.options.setdefault("spider", True)
        self.options.setdefault("ajax_spider", False)
        self.options.setdefault("active_scan", True)
        self.options.setdefault("recursion_depth", 5)
        self.options.setdefault("scan_timeout", 600)

        self._session: Optional[aiohttp.ClientSession] = None
        self._docker_container: Optional[str] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _api_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = "GET"
    ) -> Dict[str, Any]:
        """Make ZAP API request"""
        session = await self._get_session()
        url = f"{self.api_url}/JSON/{endpoint}"

        params = params or {}
        if self.api_key:
            params["apikey"] = self.api_key

        try:
            if method.upper() == "GET":
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        raise RuntimeError(f"ZAP API error {response.status}: {text}")
            elif method.upper() == "POST":
                async with session.post(url, data=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        text = await response.text()
                        raise RuntimeError(f"ZAP API error {response.status}: {text}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Failed to connect to ZAP API: {e}")

    def _check_zap_installed(self) -> bool:
        """Check if ZAP is installed"""
        if self.use_docker:
            return shutil.which("docker") is not None
        return shutil.which(self.zap_path) is not None

    async def start_daemon(self, port: int = 8080) -> bool:
        """Start ZAP daemon"""
        if not self._check_zap_installed():
            raise RuntimeError(
                "ZAP not found. Install ZAP from: https://www.zaproxy.org/download/"
            )

        if self.use_docker:
            return await self._start_docker_daemon(port)
        else:
            return await self._start_local_daemon(port)

    async def _start_local_daemon(self, port: int) -> bool:
        """Start local ZAP daemon"""
        import subprocess

        cmd = [
            self.zap_path,
            "-daemon",
            "-port", str(port),
            "-config", "api.disablekey=true",
            "-config", "api.addrs.addr.regex=true",
            "-config", "api.addrs.addr.name=.*",
        ]

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            # Wait for ZAP to start
            await asyncio.sleep(10)
            return True
        except Exception as e:
            logger.error(f"Failed to start ZAP daemon: {e}")
            return False

    async def _start_docker_daemon(self, port: int) -> bool:
        """Start ZAP in Docker"""
        import subprocess

        cmd = [
            "docker", "run", "-d",
            "-p", f"{port}:{port}",
            "--name", f"zap_daemon_{port}",
            "ghcr.io/zaproxy/zaproxy:stable",
            "zap.sh", "-daemon",
            "-port", str(port),
            "-config", "api.disablekey=true",
            "-config", "api.addrs.addr.regex=true",
            "-config", "api.addrs.addr.name=.*",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self._docker_container = result.stdout.strip()
                # Wait for ZAP to start
                await asyncio.sleep(15)
                return True
            else:
                logger.error(f"Docker error: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to start ZAP docker: {e}")
            return False

    async def stop_daemon(self) -> None:
        """Stop ZAP daemon"""
        if self._docker_container:
            import subprocess
            subprocess.run(
                ["docker", "stop", self._docker_container],
                capture_output=True,
            )
            subprocess.run(
                ["docker", "rm", self._docker_container],
                capture_output=True,
            )
            self._docker_container = None

        if self._session and not self._session.closed:
            await self._session.close()

    async def spider_scan(self, progress_callback: Optional[Callable[[int], None]] = None) -> str:
        """
        Run spider scan.

        Returns:
            Scan ID
        """
        params = {
            "url": self.target,
            "maxChildren": self.options.get("max_children", 0),
            "recurse": str(self.options.get("recursion_depth", 5)),
        }

        if self.options.get("context_name"):
            params["contextName"] = self.options["context_name"]

        if self.options.get("user_agent"):
            params["userAgent"] = self.options["user_agent"]

        # Start spider
        result = await self._api_request("spider/action/scan/", params, "POST")
        scan_id = result.get("scan")

        if not scan_id:
            raise RuntimeError("Failed to start spider scan")

        # Wait for completion
        timeout = self.options.get("scan_timeout", 600)
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._api_request("spider/view/status/", {"scanId": scan_id})
            progress = int(status.get("status", 0))

            if progress_callback:
                progress_callback(progress)

            if progress >= 100:
                break

            await asyncio.sleep(2)

        return scan_id

    async def ajax_spider_scan(self, progress_callback: Optional[Callable[[int], None]] = None) -> bool:
        """
        Run AJAX spider scan for modern web applications.

        Returns:
            True if completed successfully
        """
        params = {
            "url": self.target,
        }

        if self.options.get("context_name"):
            params["contextName"] = self.options["context_name"]

        # Start AJAX spider
        await self._api_request("ajaxSpider/action/scan/", params, "POST")

        # Wait for completion
        timeout = self.options.get("scan_timeout", 600)
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._api_request("ajaxSpider/view/status/")
            is_running = status.get("status") == "running"

            if not is_running:
                if progress_callback:
                    progress_callback(100)
                return True

            if progress_callback:
                # Estimate progress based on time
                elapsed = time.time() - start_time
                estimated_progress = min(int((elapsed / timeout) * 100), 99)
                progress_callback(estimated_progress)

            await asyncio.sleep(2)

        return False

    async def active_scan(self, progress_callback: Optional[Callable[[int], None]] = None) -> str:
        """
        Run active scan.

        Returns:
            Scan ID
        """
        # Get context and user if configured
        context_id = ""
        if self.options.get("context_name"):
            contexts = await self._api_request("context/view/contextList/")
            if self.options["context_name"] in contexts.get("contextList", []):
                context_id = self.options["context_name"]

        params = {
            "url": self.target,
            "recurse": "true",
            "inScopeOnly": "false",
            "scanPolicyName": self.options.get("scan_policy", ""),
            "method": "",
            "postData": "",
        }

        if context_id:
            params["contextId"] = context_id

        # Start active scan
        result = await self._api_request("ascan/action/scan/", params, "POST")
        scan_id = result.get("scan")

        if not scan_id:
            raise RuntimeError("Failed to start active scan")

        # Wait for completion
        timeout = self.options.get("scan_timeout", 600)
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._api_request("ascan/view/status/", {"scanId": scan_id})
            progress = int(status.get("status", 0))

            if progress_callback:
                progress_callback(progress)

            if progress >= 100:
                break

            await asyncio.sleep(2)

        return scan_id

    async def get_alerts(self, base_url: Optional[str] = None) -> List[ZAPAlert]:
        """
        Get all alerts/findings from ZAP.

        Args:
            base_url: Filter alerts by base URL

        Returns:
            List of ZAPAlert objects
        """
        params = {}
        if base_url:
            params["baseurl"] = base_url

        result = await self._api_request("core/view/alerts/", params)
        alerts_data = result.get("alerts", [])

        alerts = []
        for alert_data in alerts_data:
            alert = ZAPAlert(
                alert_id=str(alert_data.get("alertId", "")),
                name=alert_data.get("name", ""),
                risk=alert_data.get("risk", ""),
                confidence=alert_data.get("confidence", ""),
                description=alert_data.get("description", ""),
                solution=alert_data.get("solution", ""),
                reference=alert_data.get("reference", ""),
                cwe_id=str(alert_data.get("cweid", "")),
                wasc_id=str(alert_data.get("wascid", "")),
                sourceid=str(alert_data.get("sourceid", "")),
                url=alert_data.get("url", ""),
                method=alert_data.get("method", ""),
                attack=alert_data.get("attack", ""),
                evidence=alert_data.get("evidence", ""),
                other_info=alert_data.get("otherinfo", ""),
                param=alert_data.get("param", ""),
            )
            alerts.append(alert)

        return alerts

    async def scan(self) -> ZAPScanResult:
        """
        Run complete ZAP scan based on options.

        Returns:
            ZAPScanResult with scan results
        """
        start_time = time.time()
        progress_callback = self.options.get("progress_callback")

        try:
            # Spider scan
            if self.options.get("spider", True):
                logger.info(f"Starting spider scan for {self.target}")
                await self.spider_scan(
                    progress_callback=lambda p: progress_callback({"spider": p}) if progress_callback else None
                )

            # AJAX spider scan
            if self.options.get("ajax_spider", False):
                logger.info(f"Starting AJAX spider scan for {self.target}")
                await self.ajax_spider_scan(
                    progress_callback=lambda p: progress_callback({"ajax_spider": p}) if progress_callback else None
                )

            # Active scan
            if self.options.get("active_scan", True):
                logger.info(f"Starting active scan for {self.target}")
                await self.active_scan(
                    progress_callback=lambda p: progress_callback({"active_scan": p}) if progress_callback else None
                )

            # Get alerts
            alerts = await self.get_alerts(self.target)

            # Get scan statistics
            urls = await self._api_request("core/view/urls/")
            num_urls = len(urls.get("urls", []))

            scan_time = time.time() - start_time

            return ZAPScanResult(
                success=True,
                target=self.target,
                scan_type="full",
                alerts=alerts,
                scan_time=scan_time,
                urls_crawled=num_urls,
                urls_audited=num_urls,
            )

        except Exception as e:
            logger.error(f"ZAP scan error: {e}")
            return ZAPScanResult(
                success=False,
                target=self.target,
                scan_type="full",
                error=str(e),
                scan_time=time.time() - start_time,
            )

    def parse_output(self, alerts: List[ZAPAlert]) -> List[Dict[str, Any]]:
        """
        Parse ZAP alerts into standardized format.

        Args:
            alerts: List of ZAPAlert objects

        Returns:
            List of standardized finding dictionaries
        """
        findings = []
        for alert in alerts:
            finding = {
                "tool": "zap",
                "name": alert.name,
                "severity": self._risk_to_severity(alert.risk),
                "confidence": alert.confidence.lower(),
                "description": alert.description,
                "solution": alert.solution,
                "references": self._parse_references(alert.reference),
                "evidence": {
                    "url": alert.url,
                    "method": alert.method,
                    "parameter": alert.param,
                    "attack": alert.attack,
                    "evidence": alert.evidence,
                },
                "cwe_id": alert.cwe_id,
                "wasc_id": alert.wasc_id,
            }
            findings.append(finding)
        return findings

    def normalize_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize findings to standard format.

        Args:
            findings: List of finding dictionaries

        Returns:
            List of normalized findings
        """
        normalized = []
        severity_map = {
            "informational": "info",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "critical",
        }

        for finding in findings:
            normalized_finding = {
                "tool": "owasp_zap",
                "target": self.target,
                "severity": severity_map.get(finding.get("severity", "").lower(), "info"),
                "title": finding.get("name", "Unknown"),
                "description": finding.get("description", ""),
                "evidence": finding.get("evidence", {}),
                "remediation": finding.get("solution", ""),
                "references": finding.get("references", []),
                "confidence": finding.get("confidence", "medium"),
                "cwe_id": finding.get("cwe_id", ""),
                "wasc_id": finding.get("wasc_id", ""),
            }
            normalized.append(normalized_finding)

        return normalized

    def _risk_to_severity(self, risk: str) -> str:
        """Convert ZAP risk level to severity"""
        risk_map = {
            "Informational": "info",
            "Low": "low",
            "Medium": "medium",
            "High": "high",
        }
        return risk_map.get(risk, "info")

    def _parse_references(self, reference: str) -> List[str]:
        """Parse reference string into list of URLs"""
        if not reference:
            return []
        # Split by common delimiters
        refs = [r.strip() for r in reference.replace("\n", " ").split() if r.strip().startswith("http")]
        return refs if refs else [reference]

    async def generate_report(self, report_format: str = "json", output_path: Optional[str] = None) -> str:
        """
        Generate ZAP report.

        Args:
            report_format: Report format (html, xml, json, md)
            output_path: Path to save report

        Returns:
            Report content or path to saved report
        """
        format_map = {
            "html": "traditional-html",
            "xml": "traditional-xml",
            "json": "traditional-json",
            "md": "traditional-md",
        }

        zap_format = format_map.get(report_format.lower(), "traditional-json")

        result = await self._api_request(
            "reports/action/generate/",
            {
                "title": f"ZAP Scan Report - {self.target}",
                "template": zap_format,
                "sites": self.target,
                "reportFileName": output_path or "zap_report",
            },
            "POST",
        )

        return result.get("generate", "")

    def get_version(self) -> str:
        """Get ZAP version"""
        try:
            import asyncio
            result = asyncio.run(self._api_request("core/view/version/"))
            return result.get("version", "unknown")
        except Exception:
            return "unknown"


# LangChain Tool integration
try:
    from langchain_core.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Define a dummy decorator if langchain is not available
    def tool(func=None, **kwargs):
        if func:
            return func
        return lambda f: f


@tool
def zap_scan_url(
    target: str,
    spider: bool = True,
    active_scan: bool = True,
    ajax_spider: bool = False,
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Scan a web application using OWASP ZAP.

    Args:
        target: Target URL to scan (e.g., "http://example.com")
        spider: Enable spider/crawl functionality
        active_scan: Enable active scanning
        ajax_spider: Enable AJAX spider for modern web apps
        api_url: ZAP API URL (default: http://localhost:8080)
        api_key: ZAP API key

    Returns:
        Scan results with discovered vulnerabilities
    """
    import asyncio

    options = {
        "spider": spider,
        "active_scan": active_scan,
        "ajax_spider": ajax_spider,
    }

    scanner = ZAPScanner(
        target=target,
        api_url=api_url,
        api_key=api_key if api_key else None,
        options=options,
    )

    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"ZAP scan failed: {result.error}"

    # Format results
    lines = [
        f"OWASP ZAP Scan completed in {result.scan_time:.2f}s",
        f"Target: {result.target}",
        f"URLs Crawled: {result.urls_crawled}",
        f"Alerts Found: {len(result.alerts)}",
        "",
        "Findings:",
    ]

    # Group alerts by risk
    risk_groups = {"High": [], "Medium": [], "Low": [], "Informational": []}
    for alert in result.alerts:
        risk = alert.risk if alert.risk in risk_groups else "Informational"
        risk_groups[risk].append(alert)

    for risk in ["High", "Medium", "Low"]:
        if risk_groups[risk]:
            lines.append(f"\n{risk} Risk Findings:")
            for alert in risk_groups[risk][:5]:  # Limit to 5 per category
                lines.append(f"  - {alert.name}")
                lines.append(f"    URL: {alert.url}")
                lines.append(f"    Description: {alert.description[:100]}...")

    return "\n".join(lines)


@tool
def zap_quick_scan(target: str, api_url: str = "http://localhost:8080") -> str:
    """
    Quick ZAP scan with spider and basic active scanning.

    Args:
        target: Target URL to scan
        api_url: ZAP API URL

    Returns:
        Summary of findings
    """
    import asyncio

    scanner = ZAPScanner(
        target=target,
        api_url=api_url,
        options={"spider": True, "active_scan": True, "scan_timeout": 300},
    )

    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"Quick scan failed: {result.error}"

    high_count = sum(1 for a in result.alerts if a.risk == "High")
    medium_count = sum(1 for a in result.alerts if a.risk == "Medium")
    low_count = sum(1 for a in result.alerts if a.risk == "Low")

    return (
        f"ZAP Quick Scan Results for {target}:\n"
        f"  High: {high_count}\n"
        f"  Medium: {medium_count}\n"
        f"  Low: {low_count}\n"
        f"  Total Alerts: {len(result.alerts)}"
    )


@tool
def zap_spider_only(target: str, api_url: str = "http://localhost:8080") -> str:
    """
    Run only ZAP spider/crawler without active scanning.

    Args:
        target: Target URL to crawl
        api_url: ZAP API URL

    Returns:
        Discovered URLs
    """
    import asyncio

    scanner = ZAPScanner(
        target=target,
        api_url=api_url,
        options={"spider": True, "active_scan": False, "ajax_spider": False},
    )

    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"Spider failed: {result.error}"

    return f"Spider completed. Crawled {result.urls_crawled} URLs from {target}"


# Tool Registry integration
try:
    from .tool_registry import ToolCategory, ToolSafetyLevel, registry
    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_zap_tools():
    """Register ZAP tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=zap_scan_url,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["web", "vulnerability", "scanner", "owasp", "zap"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=zap_quick_scan,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["web", "vulnerability", "quick", "owasp", "zap"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=zap_spider_only,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["web", "crawler", "spider", "owasp", "zap"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        logger.info("ZAP tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register ZAP tools: {e}")


# Auto-register on import
try:
    register_zap_tools()
except Exception:
    pass


__all__ = [
    "ZAPScanner",
    "ZAPAlert",
    "ZAPScanResult",
    "ZAPScanPolicy",
    "ZAPAlertRisk",
    "zap_scan_url",
    "zap_quick_scan",
    "zap_spider_only",
    "register_zap_tools",
]
