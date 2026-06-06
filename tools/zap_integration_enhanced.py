"""OWASP ZAP Enhanced Integration - Complete Web Application Security Scanner

This module provides a comprehensive OWASP ZAP integration with:
- ZAP API Client with full authentication support
- Multiple scan policies (Default, API, Full, Quick)
- Complete authentication support (Form, JWT, API Key, Basic Auth, OAuth2)
- Spider, AJAX Spider, Active and Passive scanning
- Context management with scope definition
- Report generation (HTML, XML, JSON, Markdown)
- Alert filtering and risk scoring
- ReAct Agent integration
- Async operations throughout

Author: Zen-AI-Pentest Team
License: MIT
Version: 3.0.0
"""

import asyncio
import base64
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class ZAPScanPolicy(Enum):
    """ZAP scan policies for active scanning"""

    DEFAULT = "Default Policy"  # Standard OWASP Top 10
    API = "API Policy"  # REST/GraphQL specific
    FULL = "Full Policy"  # All rules (longer time)
    QUICK = "Quick Policy"  # Only High/Critical (fast)
    SQL_INJECTION = "SQL Injection"
    XSS = "Cross Site Scripting"
    DIRECTORY_BROWSING = "Directory Browsing"
    CSRF = "Cross Site Request Forgery"
    COMMAND_INJECTION = "Command Injection"
    LDAP_INJECTION = "LDAP Injection"
    XPATH_INJECTION = "XPath Injection"
    XML_EXTERNAL_ENTITY = "XML External Entity Attack"
    PATH_TRAVERSAL = "Path Traversal"


class ZAPAuthType(Enum):
    """ZAP authentication types"""

    FORM_BASED = "formBasedAuthentication"
    SCRIPT_BASED = "scriptBasedAuthentication"
    HTTP = "httpAuthentication"
    MANUAL = "manualAuthentication"


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
    plugin_id: str = ""
    tags: List[str] = field(default_factory=list)
    is_false_positive: bool = False
    timestamp: Optional[datetime] = None


@dataclass
class ZAPAuthConfig:
    """Authentication configuration"""

    auth_type: ZAPAuthType
    # Form-based auth
    login_url: Optional[str] = None
    username_field: Optional[str] = None
    password_field: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    # JWT Bearer Token
    jwt_token: Optional[str] = None
    jwt_header: str = "Authorization"
    # API Key
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    # Basic Auth
    basic_username: Optional[str] = None
    basic_password: Optional[str] = None
    # OAuth2
    oauth_token: Optional[str] = None
    oauth_header: str = "Authorization"
    # Indicators
    logged_in_regex: str = ""
    logged_out_regex: str = ""
    # Session management
    session_mgmt: str = "cookieBasedSessionManagement"


@dataclass
class ZAPContext:
    """ZAP Context definition"""

    id: str
    name: str
    description: str = ""
    include_regexes: List[str] = field(default_factory=list)
    exclude_regexes: List[str] = field(default_factory=list)
    auth_config: Optional[ZAPAuthConfig] = None
    users: List[Dict[str, Any]] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)


@dataclass
class ZAPScanConfig:
    """ZAP scan configuration"""

    target: str
    scan_policy: ZAPScanPolicy = ZAPScanPolicy.DEFAULT
    max_depth: int = 5
    max_duration: int = 300  # seconds
    thread_count: int = 2
    delay_in_ms: int = 0
    timeout: int = 600
    exclude_urls: List[str] = field(default_factory=list)
    context_name: Optional[str] = None
    user_agent: Optional[str] = None
    handle_forms: bool = True
    follow_redirects: bool = True
    parse_robots: bool = True
    parse_sitemap: bool = True


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
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    risk_counts: Dict[str, int] = field(default_factory=dict)


class ZAPClient:
    """
    Complete ZAP API Client with authentication support.

    Features:
    - Connection to ZAP API (http://localhost:8080)
    - API Key authentication
    - Session management
    - Retry logic with exponential backoff
    - Async context manager support
    """

    def __init__(
        self,
        zap_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize ZAP API Client.

        Args:
            zap_url: ZAP API URL
            api_key: ZAP API key for authentication
            timeout: Request timeout in seconds
        """
        self.zap_url = zap_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._version: Optional[str] = None
        self._max_retries = 3
        self._retry_delay = 1.0

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        return self._session

    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Make ZAP API request with retries.

        Args:
            endpoint: API endpoint (e.g., 'core/view/version')
            params: Request parameters
            method: HTTP method (GET or POST)

        Returns:
            JSON response as dictionary
        """
        url = f"{self.zap_url}/JSON/{endpoint}/"
        params = params or {}

        if self.api_key:
            params["apikey"] = self.api_key

        last_error = None
        for attempt in range(self._max_retries):
            try:
                session = await self._get_session()

                if method.upper() == "GET":
                    async with session.get(url, params=params) as response:
                        return await self._handle_response(response)
                else:
                    async with session.post(url, data=params) as response:
                        return await self._handle_response(response)

            except aiohttp.ClientError as e:
                last_error = e
                logger.warning(f"ZAP API request failed (attempt {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                    if self._session:
                        await self._session.close()
                        self._session = None
            except Exception as e:
                logger.error(f"Unexpected error in ZAP API request: {e}")
                raise

        raise RuntimeError(f"ZAP API request failed after {self._max_retries} attempts: {last_error}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response"""
        if response.status == 200:
            return await response.json()
        else:
            text = await response.text()
            raise RuntimeError(f"ZAP API error {response.status}: {text}")

    async def check_connection(self) -> bool:
        """Check if ZAP API is reachable"""
        try:
            result = await self._request("core/view/version")
            self._version = result.get("version", "unknown")
            return True
        except Exception as e:
            logger.error(f"ZAP API connection check failed: {e}")
            return False

    async def get_version(self) -> str:
        """Get ZAP version"""
        if self._version:
            return self._version
        result = await self._request("core/view/version")
        self._version = result.get("version", "unknown")
        return self._version

    def start_session(self, target: str) -> Dict[str, Any]:
        """
        Start a new scanning session.

        Args:
            target: Target URL

        Returns:
            Session information
        """
        # New session clears all previous data
        import asyncio

        try:
            asyncio.run(self._request("core/action/newSession", {"name": f"session_{int(time.time())}"}, "POST"))
            return {"success": True, "target": target, "message": "New session started"}
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return {"success": False, "error": str(e)}

    async def spider_scan(
        self,
        target: str,
        max_depth: int = 5,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        """
        Run spider scan to discover URLs.

        Args:
            target: Target URL
            max_depth: Maximum crawl depth
            progress_callback: Callback for progress updates (0-100)

        Returns:
            Scan ID
        """
        params = {
            "url": target,
            "maxChildren": 0,
            "recurse": str(max_depth),
        }

        result = await self._request("spider/action/scan", params, "POST")
        scan_id = result.get("scan")

        if not scan_id:
            raise RuntimeError("Failed to start spider scan")

        logger.info(f"Spider scan started: {scan_id}")

        # Wait for completion
        timeout = 600
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._request("spider/view/status", {"scanId": scan_id})
            progress = int(status.get("status", 0))

            if progress_callback:
                progress_callback(progress)

            if progress >= 100:
                break

            await asyncio.sleep(2)

        return scan_id

    async def ajax_spider(
        self,
        target: str,
        max_duration: int = 300,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        """
        Run AJAX spider for JavaScript-heavy applications.

        Args:
            target: Target URL
            max_duration: Maximum duration in seconds
            progress_callback: Callback for progress updates

        Returns:
            True if completed successfully
        """
        params = {"url": target}
        await self._request("ajaxSpider/action/scan", params, "POST")

        logger.info("AJAX Spider scan started")

        # Wait for completion
        start_time = time.time()

        while time.time() - start_time < max_duration:
            status = await self._request("ajaxSpider/view/status")
            is_running = status.get("status") == "running"

            if not is_running:
                if progress_callback:
                    progress_callback(100)
                return True

            if progress_callback:
                elapsed = time.time() - start_time
                estimated = min(int((elapsed / max_duration) * 100), 99)
                progress_callback(estimated)

            await asyncio.sleep(2)

        return False

    async def active_scan(
        self,
        target: str,
        scan_policy: str = "Default",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        """
        Run active security scan.

        Args:
            target: Target URL
            scan_policy: Scan policy name
            progress_callback: Callback for progress updates

        Returns:
            Scan ID
        """
        params = {
            "url": target,
            "recurse": "true",
            "inScopeOnly": "false",
            "scanPolicyName": scan_policy,
        }

        result = await self._request("ascan/action/scan", params, "POST")
        scan_id = result.get("scan")

        if not scan_id:
            raise RuntimeError("Failed to start active scan")

        logger.info(f"Active scan started: {scan_id}")

        # Wait for completion
        timeout = 600
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._request("ascan/view/status", {"scanId": scan_id})
            progress = int(status.get("status", 0))

            if progress_callback:
                progress_callback(progress)

            if progress >= 100:
                break

            await asyncio.sleep(2)

        return scan_id

    async def get_alerts(
        self,
        risk_levels: Optional[List[str]] = None,
        base_url: Optional[str] = None,
    ) -> List[ZAPAlert]:
        """
        Get alerts/findings from ZAP.

        Args:
            risk_levels: Filter by risk levels (High, Medium, Low, Informational)
            base_url: Filter by base URL

        Returns:
            List of ZAPAlert objects
        """
        params = {}
        if base_url:
            params["baseurl"] = base_url

        result = await self._request("core/view/alerts", params)
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
                plugin_id=str(alert_data.get("pluginId", "")),
                timestamp=datetime.now(),
            )

            # Filter by risk level if specified
            if risk_levels and alert.risk not in risk_levels:
                continue

            alerts.append(alert)

        return alerts

    async def generate_report(
        self,
        format: str = "html",
        output_path: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate ZAP report.

        Args:
            format: Report format (html, xml, json, md)
            output_path: Path to save report
            title: Report title

        Returns:
            Report content or file path
        """
        format_map = {
            "html": "traditional-html",
            "xml": "traditional-xml",
            "json": "traditional-json",
            "md": "traditional-md",
        }

        zap_format = format_map.get(format.lower(), "traditional-json")
        report_title = title or f"ZAP Scan Report - {int(time.time())}"

        try:
            result = await self._request(
                "reports/action/generate",
                {
                    "title": report_title,
                    "template": zap_format,
                    "reportFileName": output_path or f"zap_report_{int(time.time())}",
                },
                "POST",
            )

            if format == "json":
                # Return alerts as JSON
                alerts = await self.get_alerts()
                return {
                    "title": report_title,
                    "generated_at": datetime.now().isoformat(),
                    "alerts": [self._alert_to_dict(a) for a in alerts],
                }

            return result.get("generate", "")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {}

    def _alert_to_dict(self, alert: ZAPAlert) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": alert.alert_id,
            "name": alert.name,
            "risk": alert.risk,
            "confidence": alert.confidence,
            "description": alert.description,
            "solution": alert.solution,
            "url": alert.url,
            "method": alert.method,
            "param": alert.param,
            "evidence": alert.evidence,
            "cwe_id": alert.cwe_id,
            "wasc_id": alert.wasc_id,
        }


class ZAPAutomation:
    """
    Automated ZAP Security Testing with authentication support.

    Features:
    - Full automated scan workflow
    - Multiple authentication methods
    - Scan policies
    - Report generation
    - Progress tracking
    """

    def __init__(
        self,
        zap_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
    ):
        """
        Initialize ZAP Automation.

        Args:
            zap_url: ZAP API URL
            api_key: ZAP API key
        """
        self.client = ZAPClient(zap_url, api_key)
        self._scans: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.close()

    async def full_scan(
        self,
        target: str,
        auth: Optional[Dict[str, Any]] = None,
        policy: str = "Default",
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ZAPScanResult:
        """
        Run full automated scan with all phases.

        Args:
            target: Target URL
            auth: Authentication configuration dict
                {
                    "type": "form|jwt|api_key|basic|oauth2",
                    # Form-based
                    "login_url": "...",
                    "username_field": "username",
                    "password_field": "password",
                    "username": "...",
                    "password": "...",
                    # JWT/Bearer
                    "token": "...",
                    # API Key
                    "api_key": "...",
                    "api_key_header": "X-API-Key",
                    # Basic Auth
                    "basic_username": "...",
                    "basic_password": "...",
                    # OAuth2
                    "oauth_token": "...",
                }
            policy: Scan policy (Default, API, Full, Quick)
            progress_callback: Callback for progress updates

        Returns:
            ZAPScanResult with all findings
        """
        scan_id = str(uuid.uuid4())
        start_time = time.time()

        result = ZAPScanResult(
            success=True,
            target=target,
            scan_type="full",
            scan_id=scan_id,
            start_time=datetime.now(),
        )

        self._scans[scan_id] = {
            "status": "running",
            "progress": 0,
            "target": target,
            "phase": "initializing",
        }

        try:
            # Step 1: Context Setup
            if progress_callback:
                progress_callback({"phase": "context", "progress": 0, "message": "Setting up context"})

            context_name = f"context_{int(time.time())}"
            await self._create_context(context_name, target)

            # Step 2: Authentication (if provided)
            if auth:
                if progress_callback:
                    progress_callback({"phase": "auth", "progress": 0, "message": "Configuring authentication"})

                await self._configure_auth(context_name, target, auth)

                if progress_callback:
                    progress_callback({"phase": "auth", "progress": 100, "message": "Authentication configured"})

            # Step 3: Spider Scan
            if progress_callback:
                progress_callback({"phase": "spider", "progress": 0, "message": "Starting spider scan"})

            await self.client.spider_scan(
                target,
                max_depth=5,
                progress_callback=lambda p: (
                    progress_callback({"phase": "spider", "progress": p}) if progress_callback else None
                ),
            )

            # Get crawled URLs count
            urls_result = await self.client._request("core/view/urls")
            result.urls_crawled = len(urls_result.get("urls", []))

            # Step 4: Passive Scan
            if progress_callback:
                progress_callback({"phase": "passive", "progress": 0, "message": "Running passive scan"})

            await self._wait_for_passive_scan()

            if progress_callback:
                progress_callback({"phase": "passive", "progress": 100})

            # Step 5: Active Scan
            if progress_callback:
                progress_callback({"phase": "active", "progress": 0, "message": "Starting active scan"})

            await self.client.active_scan(
                target,
                scan_policy=policy,
                progress_callback=lambda p: (
                    progress_callback({"phase": "active", "progress": p}) if progress_callback else None
                ),
            )

            # Get audited count
            messages_result = await self.client._request("core/view/numberOfMessages")
            result.urls_audited = int(messages_result.get("numberOfMessages", 0))

            # Step 6: Get Alerts
            if progress_callback:
                progress_callback({"phase": "alerts", "progress": 0, "message": "Collecting alerts"})

            result.alerts = await self.client.get_alerts()
            result.risk_counts = self._calculate_risk_counts(result.alerts)

            if progress_callback:
                progress_callback({"phase": "alerts", "progress": 100})

            # Step 7: Report Generation
            if progress_callback:
                progress_callback({"phase": "report", "progress": 0, "message": "Generating report"})

            result.scan_time = time.time() - start_time
            result.end_time = datetime.now()
            result.progress = 100

            self._scans[scan_id]["status"] = "completed"
            self._scans[scan_id]["progress"] = 100

            if progress_callback:
                progress_callback({"phase": "completed", "progress": 100, "message": "Scan completed"})

        except Exception as e:
            logger.error(f"Full scan failed: {e}")
            result.success = False
            result.error = str(e)
            self._scans[scan_id]["status"] = "failed"
            self._scans[scan_id]["error"] = str(e)

            if progress_callback:
                progress_callback({"phase": "error", "progress": 0, "message": str(e)})

        return result

    async def _create_context(self, name: str, target: str) -> str:
        """Create a new ZAP context"""
        result = await self.client._request(
            "context/action/newContext",
            {"contextName": name},
            "POST",
        )
        context_id = result.get("contextId", "")

        # Include target in context
        await self.client._request(
            "context/action/includeInContext",
            {"contextName": name, "regex": f"\\Q{target}\\E.*"},
            "POST",
        )

        return context_id

    async def _configure_auth(
        self,
        context_name: str,
        target: str,
        auth: Dict[str, Any],
    ) -> bool:
        """
        Configure authentication for the scan.

        Supports:
        - Form-based: {type: "form", login_url, username_field, password_field, username, password}
        - JWT: {type: "jwt", token, header?}
        - API Key: {type: "api_key", api_key, header?}
        - Basic: {type: "basic", basic_username, basic_password}
        - OAuth2: {type: "oauth2", oauth_token, header?}
        """
        auth_type = auth.get("type", "").lower()

        if auth_type == "form":
            return await self._configure_form_auth(context_name, auth)
        elif auth_type in ["jwt", "bearer"]:
            return await self._configure_jwt_auth(auth)
        elif auth_type == "api_key":
            return await self._configure_api_key_auth(auth)
        elif auth_type == "basic":
            return await self._configure_basic_auth(auth)
        elif auth_type == "oauth2":
            return await self._configure_oauth2_auth(auth)
        else:
            logger.warning(f"Unknown auth type: {auth_type}")
            return False

    async def _configure_form_auth(self, context_name: str, auth: Dict[str, Any]) -> bool:
        """Configure form-based authentication"""
        try:
            login_url = auth.get("login_url", "")
            username_field = auth.get("username_field", "username")
            password_field = auth.get("password_field", "password")
            username = auth.get("username", "")
            password = auth.get("password", "")

            # Build auth config
            auth_config = f"loginUrl={login_url}&loginRequestData=username%3D%7B%7B{username_field}%7D%7D%26password%3D%7B%7B{password_field}%7D%7D"

            await self.client._request(
                "context/action/setAuthenticationMethod",
                {
                    "contextName": context_name,
                    "authMethodName": ZAPAuthType.FORM_BASED.value,
                    "authMethodConfigParams": auth_config,
                },
                "POST",
            )

            # Create user
            result = await self.client._request(
                "users/action/newUser",
                {"contextName": context_name, "userName": username},
                "POST",
            )
            user_id = result.get("userId", "")

            if user_id:
                # Set credentials
                creds = f"username={username}&password={password}"
                await self.client._request(
                    "users/action/setAuthenticationCredentials",
                    {
                        "contextName": context_name,
                        "userId": user_id,
                        "authCredentialsConfigParams": creds,
                    },
                    "POST",
                )

                # Enable user
                await self.client._request(
                    "users/action/setUserEnabled",
                    {"contextName": context_name, "userId": user_id, "enabled": "true"},
                    "POST",
                )

            logger.info(f"Form-based auth configured for context {context_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to configure form auth: {e}")
            return False

    async def _configure_jwt_auth(self, auth: Dict[str, Any]) -> bool:
        """Configure JWT Bearer token authentication"""
        try:
            token = auth.get("token") or auth.get("jwt_token", "")
            header = auth.get("header") or auth.get("jwt_header", "Authorization")

            # Add header to all requests via replacer
            await self.client._request(
                "replacer/action/addRule",
                {
                    "description": "JWT Auth",
                    "enabled": "true",
                    "matchType": "REQ_HEADER",
                    "matchString": header,
                    "replacement": f"Bearer {token}",
                    "initiators": "",
                },
                "POST",
            )

            logger.info("JWT authentication configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure JWT auth: {e}")
            return False

    async def _configure_api_key_auth(self, auth: Dict[str, Any]) -> bool:
        """Configure API Key authentication"""
        try:
            api_key = auth.get("api_key", "")
            header = auth.get("header") or auth.get("api_key_header", "X-API-Key")

            # Add header to all requests via replacer
            await self.client._request(
                "replacer/action/addRule",
                {
                    "description": "API Key Auth",
                    "enabled": "true",
                    "matchType": "REQ_HEADER",
                    "matchString": header,
                    "replacement": api_key,
                    "initiators": "",
                },
                "POST",
            )

            logger.info("API Key authentication configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure API key auth: {e}")
            return False

    async def _configure_basic_auth(self, auth: Dict[str, Any]) -> bool:
        """Configure Basic authentication"""
        try:
            username = auth.get("basic_username") or auth.get("username", "")
            password = auth.get("basic_password") or auth.get("password", "")

            # Create base64 encoded credentials
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

            # Add Authorization header via replacer
            await self.client._request(
                "replacer/action/addRule",
                {
                    "description": "Basic Auth",
                    "enabled": "true",
                    "matchType": "REQ_HEADER",
                    "matchString": "Authorization",
                    "replacement": f"Basic {credentials}",
                    "initiators": "",
                },
                "POST",
            )

            logger.info("Basic authentication configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure basic auth: {e}")
            return False

    async def _configure_oauth2_auth(self, auth: Dict[str, Any]) -> bool:
        """Configure OAuth2 authentication"""
        try:
            token = auth.get("oauth_token") or auth.get("token", "")
            header = auth.get("header") or auth.get("oauth_header", "Authorization")

            # Add header to all requests via replacer
            await self.client._request(
                "replacer/action/addRule",
                {
                    "description": "OAuth2 Auth",
                    "enabled": "true",
                    "matchType": "REQ_HEADER",
                    "matchString": header,
                    "replacement": f"Bearer {token}",
                    "initiators": "",
                },
                "POST",
            )

            logger.info("OAuth2 authentication configured")
            return True
        except Exception as e:
            logger.error(f"Failed to configure OAuth2 auth: {e}")
            return False

    async def _wait_for_passive_scan(self) -> None:
        """Wait for passive scan to complete"""
        # Enable all passive scanners
        await self.client._request("pscan/action/enableAllScanners", {}, "POST")

        # Wait for records to scan
        await asyncio.sleep(2)

        # Wait for completion
        max_wait = 60
        start = time.time()
        while time.time() - start < max_wait:
            result = await self.client._request("pscan/view/recordsToScan")
            remaining = int(result.get("recordsToScan", 0))
            if remaining == 0:
                break
            logger.debug(f"Passive scan: {remaining} records remaining")
            await asyncio.sleep(1)

    def _calculate_risk_counts(self, alerts: List[ZAPAlert]) -> Dict[str, int]:
        """Calculate risk level counts"""
        counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
        for alert in alerts:
            if alert.risk in counts:
                counts[alert.risk] += 1
        return counts

    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get scan status by ID"""
        return self._scans.get(scan_id, {"status": "unknown"})

    def normalize_findings(self, alerts: List[ZAPAlert]) -> List[Dict[str, Any]]:
        """
        Normalize ZAP alerts to standard finding format.

        Args:
            alerts: List of ZAPAlert objects

        Returns:
            List of normalized findings
        """
        findings = []
        severity_map = {
            "Informational": "info",
            "Low": "low",
            "Medium": "medium",
            "High": "high",
        }

        for alert in alerts:
            if alert.is_false_positive:
                continue

            finding = {
                "tool": "owasp_zap",
                "target": alert.url,
                "severity": severity_map.get(alert.risk, "info"),
                "title": alert.name,
                "description": alert.description,
                "evidence": {
                    "url": alert.url,
                    "method": alert.method,
                    "parameter": alert.param,
                    "attack": alert.attack,
                    "evidence": alert.evidence,
                },
                "remediation": alert.solution,
                "references": self._parse_references(alert.reference),
                "confidence": alert.confidence.lower(),
                "cwe_id": alert.cwe_id,
                "wasc_id": alert.wasc_id,
                "plugin_id": alert.plugin_id,
            }
            findings.append(finding)

        return findings

    def _parse_references(self, reference: str) -> List[str]:
        """Parse reference string into list of URLs"""
        if not reference:
            return []
        refs = [r.strip() for r in reference.replace("\n", " ").split() if r.strip().startswith(("http", "https"))]
        return refs if refs else [reference] if reference else []


# ReAct Agent Tool Integration
try:
    from langchain_core.tools import tool

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

    def tool(func=None, **kwargs):
        if func:
            return func
        return lambda f: f


@tool
def zap_full_scan(
    target: str,
    auth_type: str = "",
    auth_token: str = "",
    auth_username: str = "",
    auth_password: str = "",
    policy: str = "Default",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Execute full OWASP ZAP scan against a target.

    This tool performs a complete web application security scan including:
    - Spider crawling
    - Passive scanning
    - Active scanning
    - Report generation

    Args:
        target: Target URL to scan (e.g., "https://example.com")
        auth_type: Authentication type (form, jwt, api_key, basic, oauth2)
        auth_token: Token for JWT/API Key/OAuth2
        auth_username: Username for form/basic auth
        auth_password: Password for form/basic auth
        policy: Scan policy (Default, API, Full, Quick)
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Scan results summary with findings
    """
    import asyncio

    async def run_scan():
        async with ZAPAutomation(api_url, api_key or None) as automation:
            # Build auth config if provided
            auth = None
            if auth_type:
                auth = {"type": auth_type}
                if auth_token:
                    auth["token"] = auth_token
                if auth_username:
                    auth["username"] = auth_username
                if auth_password:
                    auth["password"] = auth_password

            result = await automation.full_scan(
                target=target,
                auth=auth,
                policy=policy,
            )
            return result

    result = asyncio.run(run_scan())

    if not result.success:
        return f"ZAP scan failed: {result.error}"

    # Format results
    lines = [
        "OWASP ZAP Full Scan completed",
        f"Target: {result.target}",
        f"Scan ID: {result.scan_id}",
        f"Duration: {result.scan_time:.2f}s",
        f"URLs Crawled: {result.urls_crawled}",
        f"URLs Audited: {result.urls_audited}",
        "",
        "Risk Summary:",
    ]

    for risk, count in result.risk_counts.items():
        lines.append(f"  {risk}: {count}")

    lines.extend(
        [
            "",
            "Top Findings:",
        ]
    )

    # Show top findings
    for risk in ["High", "Medium", "Low"]:
        alerts = [a for a in result.alerts if a.risk == risk][:3]
        for alert in alerts:
            lines.append(f"\n[{risk}] {alert.name}")
            lines.append(f"  URL: {alert.url}")
            lines.append(f"  Parameter: {alert.param or 'N/A'}")
            lines.append(f"  Description: {alert.description[:150]}...")

    return "\n".join(lines)


@tool
def zap_spider(
    target: str,
    max_depth: int = 5,
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Run ZAP spider to discover URLs on a target.

    Args:
        target: Target URL to crawl
        max_depth: Maximum crawl depth
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Spider results with discovered URLs
    """
    import asyncio

    async def run_spider():
        async with ZAPClient(api_url, api_key or None) as client:
            scan_id = await client.spider_scan(target, max_depth)

            # Get URLs
            urls_result = await client._request("core/view/urls")
            urls = urls_result.get("urls", [])

            return scan_id, urls

    try:
        scan_id, urls = asyncio.run(run_spider())
        return f"Spider completed (ID: {scan_id})\nDiscovered {len(urls)} URLs:\n" + "\n".join(
            [f"  - {url}" for url in urls[:20]]
        )
    except Exception as e:
        return f"Spider failed: {e}"


@tool
def zap_get_findings(
    target: str,
    min_risk: str = "Low",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Get security findings/alerts from ZAP.

    Args:
        target: Target URL (optional, for filtering)
        min_risk: Minimum risk level (Informational, Low, Medium, High)
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Formatted list of security findings
    """
    import asyncio

    async def get_alerts():
        async with ZAPClient(api_url, api_key or None) as client:
            risk_levels = ["High", "Medium", "Low", "Informational"]
            if min_risk in risk_levels:
                idx = risk_levels.index(min_risk)
                risk_levels = risk_levels[: idx + 1]

            alerts = await client.get_alerts(risk_levels=risk_levels, base_url=target or None)
            return alerts

    alerts = asyncio.run(get_alerts())

    if not alerts:
        return "No alerts found."

    lines = [f"Found {len(alerts)} security alerts:", ""]

    for alert in alerts:
        lines.append(f"[{alert.risk}] {alert.name}")
        lines.append(f"  Confidence: {alert.confidence}")
        lines.append(f"  URL: {alert.url}")
        lines.append(f"  Parameter: {alert.param or 'N/A'}")
        lines.append(f"  Description: {alert.description[:200]}...")
        lines.append("")

    return "\n".join(lines)


@tool
def zap_generate_report(
    format: str = "json",
    output_path: str = "",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Generate a ZAP security scan report.

    Args:
        format: Report format (html, json, xml, md)
        output_path: Path to save report (optional)
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Report generation result
    """
    import asyncio

    async def generate():
        async with ZAPClient(api_url, api_key or None) as client:
            report = await client.generate_report(
                format=format,
                output_path=output_path or None,
            )
            return report

    try:
        report = asyncio.run(generate())
        if isinstance(report, dict):
            alert_count = len(report.get("alerts", []))
            return f"Report generated with {alert_count} alerts in {format.upper()} format."
        return f"Report generated: {report}"
    except Exception as e:
        return f"Failed to generate report: {e}"


# Tool Registry Integration
try:
    from .tool_registry import ToolCategory, ToolSafetyLevel, registry

    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_zap_enhanced_tools():
    """Register ZAP enhanced tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        logger.warning("Cannot register ZAP enhanced tools: registry or langchain not available")
        return

    try:
        registry.register(
            tool=zap_full_scan,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["web", "vulnerability", "scanner", "owasp", "zap", "full-scan"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_spider,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "crawler", "spider", "owasp", "zap"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_get_findings,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "scanner", "findings", "alerts", "zap"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_generate_report,
            category=ToolCategory.REPORTING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "report", "zap", "documentation"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        logger.info("ZAP enhanced tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register ZAP enhanced tools: {e}")


# Auto-register on import
try:
    register_zap_enhanced_tools()
except Exception:
    pass


__all__ = [
    # Classes
    "ZAPClient",
    "ZAPAutomation",
    "ZAPAlert",
    "ZAPScanConfig",
    "ZAPScanResult",
    "ZAPAuthConfig",
    # Enums
    "ZAPScanPolicy",
    "ZAPAuthType",
    "ZAPAlertRisk",
    # Tools
    "zap_full_scan",
    "zap_spider",
    "zap_get_findings",
    "zap_generate_report",
    "register_zap_enhanced_tools",
]
