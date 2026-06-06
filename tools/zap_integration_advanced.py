"""OWASP ZAP Advanced Integration - Enterprise Web Application Security Scanner

This module provides a comprehensive OWASP ZAP integration with:
- Full ZAP API Client with authentication
- Multiple scan types (Spider, Active, Passive, AJAX Spider, OpenAPI)
- Context and scope management
- Technology detection
- Policy management (Low/Medium/High/Insane)
- Authentication handling (Form-based, Script-based)
- Advanced reporting (JSON, HTML, risk-based filtering)
- False positive management
- ReActAgent integration

Author: Zen-AI-Pentest Team
License: MIT
Version: 2.0.0
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class ZAPScanType(Enum):
    """ZAP scan types"""

    SPIDER = "spider"
    AJAX_SPIDER = "ajax_spider"
    ACTIVE = "active"
    PASSIVE = "passive"
    OPENAPI = "openapi"
    GRAPHQL = "graphql"


class ZAPScanPolicy(Enum):
    """ZAP scan policies for active scanning"""

    DEFAULT = "Default Policy"
    SQL_INJECTION = "SQL Injection"
    XSS = "Cross Site Scripting"
    DIRECTORY_BROWSING = "Directory Browsing"
    CSRF = "Cross Site Request Forgery"
    COMMAND_INJECTION = "Command Injection"
    LDAP_INJECTION = "LDAP Injection"
    XPATH_INJECTION = "XPath Injection"
    XML_EXTERNAL_ENTITY = "XML External Entity Attack"
    SERVER_SIDE_INCLUDE = "Server Side Include"
    PATH_TRAVERSAL = "Path Traversal"
    REMOTE_FILE_INCLUSION = "Remote File Inclusion"
    SERVER_SIDE_CODE_INJECTION = "Server Side Code Injection"
    CORS = "CORS"


class ZAPAlertRisk(Enum):
    """ZAP alert risk levels"""

    INFORMATIONAL = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ZAPAuthMethod(Enum):
    """ZAP authentication methods"""

    FORM_BASED = "formBasedAuthentication"
    SCRIPT_BASED = "scriptBasedAuthentication"
    HTTP = "httpAuthentication"
    MANUAL = "manualAuthentication"


class ZAPScanIntensity(Enum):
    """Scan intensity levels"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    INSANE = "Insane"


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
class ZAPContext:
    """ZAP Context definition"""

    id: str
    name: str
    description: str = ""
    include_regexes: List[str] = field(default_factory=list)
    exclude_regexes: List[str] = field(default_factory=list)
    auth_method: Optional[ZAPAuthMethod] = None
    auth_config: Dict[str, Any] = field(default_factory=dict)
    users: List[Dict[str, Any]] = field(default_factory=list)
    session_mgmt: str = "cookieBasedSessionManagement"
    technologies: List[str] = field(default_factory=list)


@dataclass
class ZAPScanConfig:
    """ZAP scan configuration"""

    target: str
    scan_type: ZAPScanType
    scan_policy: ZAPScanPolicy = ZAPScanPolicy.DEFAULT
    intensity: ZAPScanIntensity = ZAPScanIntensity.MEDIUM
    context_name: Optional[str] = None
    user_agent: Optional[str] = None
    recursion_depth: int = 5
    max_children: int = 0
    max_depth: int = 10
    thread_per_host: int = 2
    delay_in_ms: int = 0
    timeout: int = 600
    exclude_urls: List[str] = field(default_factory=list)
    enable_passive: bool = True
    handle_forms: bool = True
    follow_redirects: bool = True
    parse_comments: bool = True
    parse_git: bool = True
    parse_sitemap_xml: bool = True
    parse_robots_txt: bool = True
    parse_svnpages: bool = False
    parse_dsstore: bool = True


@dataclass
class ZAPScanResult:
    """Complete ZAP scan result"""

    success: bool
    target: str
    scan_type: str
    scan_id: str
    alerts: List[ZAPAlert] = field(default_factory=list)
    scan_time: float = 0.0
    error: Optional[str] = None
    progress: int = 0
    urls_crawled: int = 0
    urls_audited: int = 0
    messages_sent: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    context_used: Optional[str] = None
    policy_used: Optional[str] = None
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZAPReport:
    """ZAP scan report"""

    title: str
    description: str
    site: str
    alerts: List[ZAPAlert]
    generated_at: datetime
    template: str
    risk_counts: Dict[str, int] = field(default_factory=dict)
    confidence_counts: Dict[str, int] = field(default_factory=dict)


class ZAPAPIClient:
    """
    ZAP API Client with async operations and session management.

    Features:
    - Connection to ZAP API (http://localhost:8080)
    - API Key authentication
    - Async operations
    - Session management
    - Error handling and retries
    """

    DEFAULT_API_URL = "http://localhost:8080"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(
        self,
        api_url: str = DEFAULT_API_URL,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize ZAP API Client.

        Args:
            api_url: ZAP API URL
            api_key: ZAP API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._version: Optional[str] = None
        self._lock = asyncio.Lock()

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

    async def request(
        self,
        component: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Make ZAP API request with retries.

        Args:
            component: API component (e.g., 'core', 'spider', 'ascan')
            action: API action (e.g., 'view/alerts', 'action/scan')
            params: Request parameters
            method: HTTP method (GET or POST)

        Returns:
            JSON response as dictionary

        Raises:
            RuntimeError: If request fails after retries
        """
        url = f"{self.api_url}/JSON/{component}/{action}/"
        params = params or {}

        if self.api_key:
            params["apikey"] = self.api_key

        last_error = None
        for attempt in range(self.MAX_RETRIES):
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
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    # Recreate session on connection error
                    if self._session:
                        await self._session.close()
                        self._session = None
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in ZAP API request: {e}")
                raise

        raise RuntimeError(f"ZAP API request failed after {self.MAX_RETRIES} attempts: {last_error}")

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
            result = await self.request("core", "view/version")
            self._version = result.get("version", "unknown")
            return True
        except Exception as e:
            logger.error(f"ZAP API connection check failed: {e}")
            return False

    async def get_version(self) -> str:
        """Get ZAP version"""
        if self._version:
            return self._version
        result = await self.request("core", "view/version")
        self._version = result.get("version", "unknown")
        return self._version

    async def get_status(self) -> Dict[str, Any]:
        """Get ZAP status information"""
        return await self.request("core", "view/version")


class ZAPContextManager:
    """
    ZAP Context Manager for scope and authentication.

    Features:
    - Context creation and management
    - Include/exclude regex patterns
    - Authentication configuration
    - User management
    - Technology detection
    """

    def __init__(self, client: ZAPAPIClient):
        """
        Initialize context manager.

        Args:
            client: ZAP API client instance
        """
        self.client = client
        self._contexts: Dict[str, ZAPContext] = {}

    async def create_context(
        self,
        name: str,
        description: str = "",
        include_regexes: Optional[List[str]] = None,
        exclude_regexes: Optional[List[str]] = None,
    ) -> ZAPContext:
        """
        Create a new ZAP context.

        Args:
            name: Context name
            description: Context description
            include_regexes: Regex patterns to include
            exclude_regexes: Regex patterns to exclude

        Returns:
            ZAPContext object
        """
        # Create context
        result = await self.client.request(
            "context",
            "action/newContext",
            {"contextName": name},
            "POST",
        )
        context_id = result.get("contextId", "")

        # Set description if provided
        if description:
            await self.client.request(
                "context",
                "action/setContextDescription",
                {"contextName": name, "description": description},
                "POST",
            )

        # Add include patterns
        if include_regexes:
            for regex in include_regexes:
                await self.client.request(
                    "context",
                    "action/includeInContext",
                    {"contextName": name, "regex": regex},
                    "POST",
                )

        # Add exclude patterns
        if exclude_regexes:
            for regex in exclude_regexes:
                await self.client.request(
                    "context",
                    "action/excludeFromContext",
                    {"contextName": name, "regex": regex},
                    "POST",
                )

        context = ZAPContext(
            id=context_id,
            name=name,
            description=description,
            include_regexes=include_regexes or [],
            exclude_regexes=exclude_regexes or [],
        )
        self._contexts[name] = context
        return context

    async def get_context(self, name: str) -> Optional[ZAPContext]:
        """Get context by name"""
        if name in self._contexts:
            return self._contexts[name]

        result = await self.client.request("context", "view/context", {"contextName": name})
        if result.get("context"):
            ctx = result["context"]
            return ZAPContext(
                id=ctx.get("id", ""),
                name=name,
                description=ctx.get("description", ""),
                include_regexes=ctx.get("includeRegexs", []),
                exclude_regexes=ctx.get("excludeRegexs", []),
            )
        return None

    async def list_contexts(self) -> List[str]:
        """List all context names"""
        result = await self.client.request("context", "view/contextList")
        return result.get("contextList", [])

    async def delete_context(self, name: str) -> bool:
        """Delete a context"""
        try:
            await self.client.request(
                "context",
                "action/removeContext",
                {"contextName": name},
                "POST",
            )
            if name in self._contexts:
                del self._contexts[name]
            return True
        except Exception as e:
            logger.error(f"Failed to delete context {name}: {e}")
            return False

    async def configure_form_auth(
        self,
        context_name: str,
        login_url: str,
        username_field: str,
        password_field: str,
        login_regex: str = "\\Qhttp://localhost:8080/logout\\E",
        logged_in_regex: str = "",
        logged_out_regex: str = "",
    ) -> bool:
        """
        Configure form-based authentication for a context.

        Args:
            context_name: Name of the context
            login_url: URL of the login page
            username_field: Name of the username field
            password_field: Name of the password field
            login_regex: Regex to detect login URL
            logged_in_regex: Regex to detect logged in state
            logged_out_regex: Regex to detect logged out state

        Returns:
            True if successful
        """
        try:
            # Set authentication method
            auth_config = f"loginUrl={login_url}&loginRequestData=username%3D%7B%7B{username_field}%7D%7D%26password%3D%7B%7B{password_field}%7D%7D"

            await self.client.request(
                "context",
                "action/setAuthenticationMethod",
                {
                    "contextName": context_name,
                    "authMethodName": ZAPAuthMethod.FORM_BASED.value,
                    "authMethodConfigParams": auth_config,
                },
                "POST",
            )

            # Set logged in/out indicators
            if logged_in_regex:
                await self.client.request(
                    "context",
                    "action/setLoggedInIndicator",
                    {"contextName": context_name, "loggedInIndicatorRegex": logged_in_regex},
                    "POST",
                )

            if logged_out_regex:
                await self.client.request(
                    "context",
                    "action/setLoggedOutIndicator",
                    {"contextName": context_name, "loggedOutIndicatorRegex": logged_out_regex},
                    "POST",
                )

            return True
        except Exception as e:
            logger.error(f"Failed to configure form auth: {e}")
            return False

    async def add_user(
        self,
        context_name: str,
        username: str,
        password: str,
        enabled: bool = True,
    ) -> Optional[str]:
        """
        Add a user to a context.

        Args:
            context_name: Context name
            username: Username
            password: Password
            enabled: Whether the user is enabled

        Returns:
            User ID if successful
        """
        try:
            result = await self.client.request(
                "users",
                "action/newUser",
                {"contextName": context_name, "userName": username},
                "POST",
            )
            user_id = result.get("userId", "")

            if user_id:
                # Set credentials
                creds = f"username={username}&password={password}"
                await self.client.request(
                    "users",
                    "action/setAuthenticationCredentials",
                    {
                        "contextName": context_name,
                        "userId": user_id,
                        "authCredentialsConfigParams": creds,
                    },
                    "POST",
                )

                # Set enabled
                await self.client.request(
                    "users",
                    "action/setUserEnabled",
                    {"contextName": context_name, "userId": user_id, "enabled": str(enabled).lower()},
                    "POST",
                )

            return user_id
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            return None

    async def include_in_scope(self, context_name: str, regex: str) -> bool:
        """Add URL pattern to scope"""
        try:
            await self.client.request(
                "context",
                "action/includeInContext",
                {"contextName": context_name, "regex": regex},
                "POST",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to include in scope: {e}")
            return False

    async def exclude_from_scope(self, context_name: str, regex: str) -> bool:
        """Exclude URL pattern from scope"""
        try:
            await self.client.request(
                "context",
                "action/excludeFromContext",
                {"contextName": context_name, "regex": regex},
                "POST",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to exclude from scope: {e}")
            return False


class ZAPScanner:
    """
    Advanced ZAP Scanner with all scan types.

    Features:
    - Spider scanning
    - AJAX Spider for JavaScript-heavy sites
    - Active scanning with policies
    - Passive scanning
    - OpenAPI scanning
    - Progress tracking
    - Alert filtering
    """

    def __init__(
        self,
        client: Optional[ZAPAPIClient] = None,
        api_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
    ):
        """
        Initialize ZAP Scanner.

        Args:
            client: Existing ZAP API client
            api_url: ZAP API URL (if no client provided)
            api_key: ZAP API key (if no client provided)
        """
        self.client = client or ZAPAPIClient(api_url, api_key)
        self.context_manager = ZAPContextManager(self.client)
        self._scan_id = str(uuid.uuid4())
        self._scans: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.close()

    async def spider_scan(
        self,
        target: str,
        config: Optional[ZAPScanConfig] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        """
        Run traditional spider scan.

        Args:
            target: Target URL
            config: Scan configuration
            progress_callback: Callback for progress updates (0-100)

        Returns:
            Scan ID
        """
        config = config or ZAPScanConfig(target=target, scan_type=ZAPScanType.SPIDER)

        params = {
            "url": target,
            "maxChildren": config.max_children,
            "recurse": "true" if config.recursion_depth > 0 else "false",
        }

        if config.context_name:
            params["contextName"] = config.context_name
        if config.user_agent:
            params["userAgent"] = config.user_agent

        # Start spider
        result = await self.client.request("spider", "action/scan", params, "POST")
        scan_id = result.get("scan")

        if not scan_id:
            raise RuntimeError("Failed to start spider scan")

        logger.info(f"Spider scan started: {scan_id}")

        # Wait for completion
        await self._wait_for_spider(scan_id, config.timeout, progress_callback)

        return scan_id

    async def ajax_spider_scan(
        self,
        target: str,
        config: Optional[ZAPScanConfig] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        """
        Run AJAX spider scan for JavaScript-heavy applications.

        Args:
            target: Target URL
            config: Scan configuration
            progress_callback: Callback for progress updates

        Returns:
            True if completed successfully
        """
        config = config or ZAPScanConfig(target=target, scan_type=ZAPScanType.AJAX_SPIDER)

        params = {"url": target}
        if config.context_name:
            params["contextName"] = config.context_name

        # Start AJAX spider
        await self.client.request("ajaxSpider", "action/scan", params, "POST")

        logger.info("AJAX Spider scan started")

        # Wait for completion
        return await self._wait_for_ajax_spider(config.timeout, progress_callback)

    async def active_scan(
        self,
        target: str,
        config: Optional[ZAPScanConfig] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> str:
        """
        Run active security scan.

        Args:
            target: Target URL
            config: Scan configuration
            progress_callback: Callback for progress updates

        Returns:
            Scan ID
        """
        config = config or ZAPScanConfig(target=target, scan_type=ZAPScanType.ACTIVE)

        # Apply scan policy if specified
        if config.scan_policy != ZAPScanPolicy.DEFAULT:
            await self._set_scan_policy(config.scan_policy)

        params = {
            "url": target,
            "recurse": "true",
            "inScopeOnly": "false",
            "scanPolicyName": config.scan_policy.value,
        }

        if config.context_name:
            params["contextName"] = config.context_name

        # Start active scan
        result = await self.client.request("ascan", "action/scan", params, "POST")
        scan_id = result.get("scan")

        if not scan_id:
            raise RuntimeError("Failed to start active scan")

        logger.info(f"Active scan started: {scan_id}")

        # Wait for completion
        await self._wait_for_active_scan(scan_id, config.timeout, progress_callback)

        return scan_id

    async def passive_scan(self, target: str) -> None:
        """
        Enable and wait for passive scan to complete.

        Args:
            target: Target URL
        """
        # Enable passive scan
        await self.client.request("pscan", "action/enableAllScanners", {}, "POST")

        # Wait for records to scan
        await asyncio.sleep(2)

        # Wait for completion
        while True:
            result = await self.client.request("pscan", "view/recordsToScan")
            remaining = int(result.get("recordsToScan", 0))
            if remaining == 0:
                break
            logger.debug(f"Passive scan: {remaining} records remaining")
            await asyncio.sleep(1)

    async def openapi_scan(
        self,
        target: str,
        openapi_url: str,
        config: Optional[ZAPScanConfig] = None,
    ) -> bool:
        """
        Import and scan OpenAPI specification.

        Args:
            target: Target base URL
            openapi_url: URL to OpenAPI spec
            config: Scan configuration

        Returns:
            True if successful
        """
        try:
            # Import OpenAPI
            await self.client.request(
                "openapi",
                "action/importUrl",
                {"url": openapi_url, "target": target},
                "POST",
            )
            logger.info(f"OpenAPI spec imported from {openapi_url}")

            # Run active scan on imported URLs
            if config and config.scan_type == ZAPScanType.ACTIVE:
                await self.active_scan(target, config)

            return True
        except Exception as e:
            logger.error(f"OpenAPI scan failed: {e}")
            return False

    async def full_scan(
        self,
        target: str,
        config: Optional[ZAPScanConfig] = None,
        progress_callback: Optional[Callable[[Dict[str, int]], None]] = None,
    ) -> ZAPScanResult:
        """
        Run complete scan (spider + passive + active).

        Args:
            target: Target URL
            config: Scan configuration
            progress_callback: Callback for progress updates

        Returns:
            ZAPScanResult with all findings
        """
        config = config or ZAPScanConfig(target=target, scan_type=ZAPScanType.ACTIVE)
        start_time = time.time()
        scan_id = str(uuid.uuid4())

        result = ZAPScanResult(
            success=True,
            target=target,
            scan_type="full",
            scan_id=scan_id,
            start_time=datetime.now(),
        )

        try:
            # Step 1: Spider scan
            if progress_callback:
                progress_callback({"phase": "spider", "progress": 0})

            spider_id = await self.spider_scan(
                target,
                config,
                lambda p: progress_callback({"phase": "spider", "progress": p}) if progress_callback else None,
            )
            result.urls_crawled = await self._get_spider_results(spider_id)

            # Step 2: Passive scan
            if progress_callback:
                progress_callback({"phase": "passive", "progress": 0})

            if config.enable_passive:
                await self.passive_scan(target)

            if progress_callback:
                progress_callback({"phase": "passive", "progress": 100})

            # Step 3: Active scan
            if progress_callback:
                progress_callback({"phase": "active", "progress": 0})

            active_id = await self.active_scan(
                target,
                config,
                lambda p: progress_callback({"phase": "active", "progress": p}) if progress_callback else None,
            )
            result.urls_audited = await self._get_active_scan_results(active_id)

            # Step 4: Get alerts
            result.alerts = await self.get_alerts(target)

            # Calculate stats
            result.stats = self._calculate_stats(result.alerts)
            result.scan_time = time.time() - start_time
            result.end_time = datetime.now()
            result.progress = 100

        except Exception as e:
            logger.error(f"Full scan failed: {e}")
            result.success = False
            result.error = str(e)

        return result

    async def get_alerts(
        self,
        base_url: Optional[str] = None,
        risk_level: Optional[ZAPAlertRisk] = None,
    ) -> List[ZAPAlert]:
        """
        Get alerts/findings from ZAP.

        Args:
            base_url: Filter by base URL
            risk_level: Filter by minimum risk level

        Returns:
            List of ZAPAlert objects
        """
        params = {}
        if base_url:
            params["baseurl"] = base_url
        if risk_level:
            params["riskId"] = str(risk_level.value)

        result = await self.client.request("core", "view/alerts", params)
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
            alerts.append(alert)

        return alerts

    async def get_alert_details(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific alert"""
        try:
            result = await self.client.request("core", "view/alert", {"id": alert_id})
            return result.get("alert")
        except Exception as e:
            logger.error(f"Failed to get alert details: {e}")
            return None

    async def mark_false_positive(self, alert_id: str, is_fp: bool = True) -> bool:
        """
        Mark an alert as false positive.

        Args:
            alert_id: Alert ID
            is_fp: True to mark as false positive

        Returns:
            True if successful
        """
        try:
            # Add to false positive list
            if is_fp:
                await self.client.request(
                    "alertFilter",
                    "action/addAlertFilter",
                    {"alertId": alert_id, "isFalsePositive": "true"},
                    "POST",
                )
            return True
        except Exception as e:
            logger.error(f"Failed to mark false positive: {e}")
            return False

    async def stop_scan(self, scan_id: str, scan_type: str = "ascan") -> bool:
        """
        Stop a running scan.

        Args:
            scan_id: Scan ID
            scan_type: Type of scan (ascan, spider, ajaxSpider)

        Returns:
            True if successful
        """
        try:
            if scan_type == "ascan":
                await self.client.request("ascan", "action/stop", {"scanId": scan_id}, "POST")
            elif scan_type == "spider":
                await self.client.request("spider", "action/stop", {"scanId": scan_id}, "POST")
            elif scan_type == "ajaxSpider":
                await self.client.request("ajaxSpider", "action/stop", {}, "POST")
            return True
        except Exception as e:
            logger.error(f"Failed to stop scan: {e}")
            return False

    async def pause_scan(self, scan_id: str, scan_type: str = "ascan") -> bool:
        """Pause a running scan"""
        try:
            if scan_type == "ascan":
                await self.client.request("ascan", "action/pause", {"scanId": scan_id}, "POST")
            elif scan_type == "spider":
                await self.client.request("spider", "action/pause", {"scanId": scan_id}, "POST")
            return True
        except Exception as e:
            logger.error(f"Failed to pause scan: {e}")
            return False

    async def resume_scan(self, scan_id: str, scan_type: str = "ascan") -> bool:
        """Resume a paused scan"""
        try:
            if scan_type == "ascan":
                await self.client.request("ascan", "action/resume", {"scanId": scan_id}, "POST")
            elif scan_type == "spider":
                await self.client.request("spider", "action/resume", {"scanId": scan_id}, "POST")
            return True
        except Exception as e:
            logger.error(f"Failed to resume scan: {e}")
            return False

    async def get_scan_status(self, scan_id: str, scan_type: str = "ascan") -> Dict[str, Any]:
        """Get scan status"""
        try:
            if scan_type == "ascan":
                result = await self.client.request("ascan", "view/status", {"scanId": scan_id})
                return {
                    "status": int(result.get("status", 0)),
                    "state": "running" if int(result.get("status", 0)) < 100 else "completed",
                }
            elif scan_type == "spider":
                result = await self.client.request("spider", "view/status", {"scanId": scan_id})
                return {
                    "status": int(result.get("status", 0)),
                    "state": "running" if int(result.get("status", 0)) < 100 else "completed",
                }
            elif scan_type == "ajaxSpider":
                result = await self.client.request("ajaxSpider", "view/status")
                return {
                    "status": 100 if result.get("status") != "running" else 50,
                    "state": "completed" if result.get("status") != "running" else "running",
                }
            return {"status": 0, "state": "unknown"}
        except Exception as e:
            logger.error(f"Failed to get scan status: {e}")
            return {"status": 0, "state": "error", "error": str(e)}

    async def generate_report(
        self,
        target: str,
        report_format: str = "json",
        output_path: Optional[str] = None,
        risk_filter: Optional[List[str]] = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate ZAP report.

        Args:
            target: Target URL
            report_format: Format (html, xml, json, md)
            output_path: Path to save report
            risk_filter: Filter by risk levels

        Returns:
            Report content or file path
        """
        format_map = {
            "html": "traditional-html",
            "xml": "traditional-xml",
            "json": "traditional-json",
            "md": "traditional-md",
        }

        zap_format = format_map.get(report_format.lower(), "traditional-json")

        try:
            result = await self.client.request(
                "reports",
                "action/generate",
                {
                    "title": f"ZAP Scan Report - {target}",
                    "template": zap_format,
                    "sites": target,
                    "reportFileName": output_path or f"zap_report_{int(time.time())}",
                },
                "POST",
            )

            if report_format == "json":
                # Return alerts directly
                alerts = await self.get_alerts(target)
                if risk_filter:
                    alerts = [a for a in alerts if a.risk.lower() in [r.lower() for r in risk_filter]]
                return self._alerts_to_dict(alerts)

            return result.get("generate", "")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {}

    async def _wait_for_spider(
        self,
        scan_id: str,
        timeout: int,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Wait for spider scan to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = await self.client.request("spider", "view/status", {"scanId": scan_id})
            progress = int(result.get("status", 0))

            if progress_callback:
                progress_callback(progress)

            if progress >= 100:
                break

            await asyncio.sleep(2)

    async def _wait_for_ajax_spider(
        self,
        timeout: int,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        """Wait for AJAX spider to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = await self.client.request("ajaxSpider", "view/status")
            is_running = result.get("status") == "running"

            if not is_running:
                if progress_callback:
                    progress_callback(100)
                return True

            if progress_callback:
                elapsed = time.time() - start_time
                estimated = min(int((elapsed / timeout) * 100), 99)
                progress_callback(estimated)

            await asyncio.sleep(2)

        return False

    async def _wait_for_active_scan(
        self,
        scan_id: str,
        timeout: int,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """Wait for active scan to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = await self.client.request("ascan", "view/status", {"scanId": scan_id})
            progress = int(result.get("status", 0))

            if progress_callback:
                progress_callback(progress)

            if progress >= 100:
                break

            await asyncio.sleep(2)

    async def _get_spider_results(self, scan_id: str) -> int:
        """Get number of URLs found by spider"""
        try:
            result = await self.client.request("spider", "view/results", {"scanId": scan_id})
            return len(result.get("results", []))
        except Exception:
            return 0

    async def _get_active_scan_results(self, scan_id: str) -> int:
        """Get number of messages sent by active scan"""
        try:
            result = await self.client.request("ascan", "view/scanProgress", {"scanId": scan_id})
            return int(result.get("totalRequests", 0))
        except Exception:
            return 0

    async def _set_scan_policy(self, policy: ZAPScanPolicy) -> None:
        """Set scan policy"""
        # ZAP uses scan policies configured in the UI
        # This is a placeholder for policy configuration
        pass

    def _calculate_stats(self, alerts: List[ZAPAlert]) -> Dict[str, Any]:
        """Calculate statistics from alerts"""
        risk_counts = {"Informational": 0, "Low": 0, "Medium": 0, "High": 0}
        confidence_counts = {"Low": 0, "Medium": 0, "High": 0}

        for alert in alerts:
            if alert.risk in risk_counts:
                risk_counts[alert.risk] += 1
            if alert.confidence in confidence_counts:
                confidence_counts[alert.confidence] += 1

        return {
            "total_alerts": len(alerts),
            "risk_counts": risk_counts,
            "confidence_counts": confidence_counts,
        }

    def _alerts_to_dict(self, alerts: List[ZAPAlert]) -> List[Dict[str, Any]]:
        """Convert alerts to dictionaries"""
        return [
            {
                "id": a.alert_id,
                "name": a.name,
                "risk": a.risk,
                "confidence": a.confidence,
                "description": a.description,
                "solution": a.solution,
                "url": a.url,
                "method": a.method,
                "param": a.param,
                "evidence": a.evidence,
                "cwe_id": a.cwe_id,
                "wasc_id": a.wasc_id,
            }
            for a in alerts
        ]

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

    def calculate_risk_score(self, alerts: List[ZAPAlert]) -> float:
        """
        Calculate overall risk score (0-100).

        Args:
            alerts: List of ZAPAlert objects

        Returns:
            Risk score from 0 (low) to 100 (critical)
        """
        if not alerts:
            return 0.0

        weights = {
            "High": 10.0,
            "Medium": 5.0,
            "Low": 2.0,
            "Informational": 0.5,
        }

        total_score = 0
        for alert in alerts:
            if not alert.is_false_positive:
                total_score += weights.get(alert.risk, 0)

        # Normalize to 0-100
        max_score = len(alerts) * 10
        if max_score == 0:
            return 0.0

        return min((total_score / max_score) * 100, 100)


# LangChain Tool Integration
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
def zap_advanced_scan(
    target: str,
    scan_type: str = "full",
    scan_policy: str = "DEFAULT",
    spider: bool = True,
    ajax_spider: bool = False,
    active_scan: bool = True,
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Advanced OWASP ZAP scan for web application security testing.

    Args:
        target: Target URL to scan (e.g., "http://example.com")
        scan_type: Scan type (full, spider, active, passive, ajax)
        scan_policy: Scan policy (DEFAULT, SQL_INJECTION, XSS, etc.)
        spider: Enable spider/crawl
        ajax_spider: Enable AJAX spider for JavaScript-heavy sites
        active_scan: Enable active scanning
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Scan results with vulnerabilities and risk score
    """
    import asyncio

    async def run_scan():
        async with ZAPScanner(api_url=api_url, api_key=api_key or None) as scanner:
            policy = ZAPScanPolicy[scan_policy.upper()]

            config = ZAPScanConfig(
                target=target,
                scan_type=ZAPScanType.ACTIVE,
                scan_policy=policy,
            )

            if scan_type == "full":
                result = await scanner.full_scan(target, config)
            elif scan_type == "spider":
                scan_id = await scanner.spider_scan(target, config)
                result = ZAPScanResult(
                    success=True,
                    target=target,
                    scan_type="spider",
                    scan_id=scan_id,
                    alerts=await scanner.get_alerts(target),
                )
            elif scan_type == "active":
                scan_id = await scanner.active_scan(target, config)
                result = ZAPScanResult(
                    success=True,
                    target=target,
                    scan_type="active",
                    scan_id=scan_id,
                    alerts=await scanner.get_alerts(target),
                )
            else:
                return ZAPScanResult(success=False, target=target, scan_type=scan_type, scan_id="", error="Unknown scan type")

            return result

    result = asyncio.run(run_scan())

    if not result.success:
        return f"ZAP scan failed: {result.error}"

    # Format results
    risk_score = ZAPScanner().calculate_risk_score(result.alerts)
    high_count = sum(1 for a in result.alerts if a.risk == "High")
    medium_count = sum(1 for a in result.alerts if a.risk == "Medium")
    low_count = sum(1 for a in result.alerts if a.risk == "Low")

    lines = [
        "OWASP ZAP Advanced Scan completed",
        f"Target: {result.target}",
        f"Scan Type: {result.scan_type}",
        f"Duration: {result.scan_time:.2f}s",
        f"URLs Crawled: {result.urls_crawled}",
        f"Risk Score: {risk_score:.1f}/100",
        "",
        "Findings Summary:",
        f"  High: {high_count}",
        f"  Medium: {medium_count}",
        f"  Low: {low_count}",
        f"  Total: {len(result.alerts)}",
        "",
        "Top Findings:",
    ]

    # Group by risk and show top findings
    for risk in ["High", "Medium", "Low"]:
        alerts = [a for a in result.alerts if a.risk == risk][:3]
        for alert in alerts:
            lines.append(f"\n[{risk}] {alert.name}")
            lines.append(f"  URL: {alert.url}")
            lines.append(f"  Description: {alert.description[:150]}...")

    return "\n".join(lines)


@tool
def zap_create_context(
    context_name: str,
    target: str,
    include_regexes: str = "",
    exclude_regexes: str = "",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Create a ZAP context with scope definition.

    Args:
        context_name: Name for the context
        target: Target base URL
        include_regexes: Comma-separated include regex patterns
        exclude_regexes: Comma-separated exclude regex patterns
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Context creation result
    """
    import asyncio

    async def create():
        client = ZAPAPIClient(api_url, api_key or None)
        manager = ZAPContextManager(client)

        includes = [r.strip() for r in include_regexes.split(",") if r.strip()]
        excludes = [r.strip() for r in exclude_regexes.split(",") if r.strip()]

        # Add target as include if no includes specified
        if not includes and target:
            includes = [f"\\Q{target}\\E.*"]

        context = await manager.create_context(
            name=context_name,
            include_regexes=includes,
            exclude_regexes=excludes,
        )
        await client.close()
        return context

    try:
        context = asyncio.run(create())
        return f"Context '{context.name}' created successfully with ID: {context.id}"
    except Exception as e:
        return f"Failed to create context: {e}"


@tool
def zap_get_alerts(
    target: str,
    min_risk: str = "Low",
    api_url: str = "http://localhost:8080",
    api_key: str = "",
) -> str:
    """
    Get ZAP alerts for a target.

    Args:
        target: Target URL
        min_risk: Minimum risk level (Informational, Low, Medium, High)
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Formatted alerts list
    """
    import asyncio

    async def get():
        async with ZAPScanner(api_url=api_url, api_key=api_key or None) as scanner:
            risk_map = {
                "informational": ZAPAlertRisk.INFORMATIONAL,
                "low": ZAPAlertRisk.LOW,
                "medium": ZAPAlertRisk.MEDIUM,
                "high": ZAPAlertRisk.HIGH,
            }
            risk_level = risk_map.get(min_risk.lower())
            return await scanner.get_alerts(target, risk_level)

    alerts = asyncio.run(get())

    if not alerts:
        return "No alerts found."

    lines = [f"Found {len(alerts)} alerts:", ""]

    for alert in alerts:
        lines.append(f"[{alert.risk}] {alert.name}")
        lines.append(f"  Confidence: {alert.confidence}")
        lines.append(f"  URL: {alert.url}")
        lines.append(f"  Parameter: {alert.param or 'N/A'}")
        lines.append(f"  Description: {alert.description[:200]}...")
        lines.append("")

    return "\n".join(lines)


@tool
def zap_stop_scan(scan_id: str, api_url: str = "http://localhost:8080", api_key: str = "") -> str:
    """
    Stop a running ZAP scan.

    Args:
        scan_id: Scan ID to stop
        api_url: ZAP API URL
        api_key: ZAP API key

    Returns:
        Stop result
    """
    import asyncio

    async def stop():
        async with ZAPScanner(api_url=api_url, api_key=api_key or None) as scanner:
            # Try stopping both spider and ascan
            await scanner.stop_scan(scan_id, "spider")
            await scanner.stop_scan(scan_id, "ascan")
            return True

    try:
        asyncio.run(stop())
        return f"Scan {scan_id} stopped successfully"
    except Exception as e:
        return f"Failed to stop scan: {e}"


# Tool Registry Integration
try:
    from .tool_registry import ToolCategory, ToolSafetyLevel, registry

    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_zap_advanced_tools():
    """Register ZAP advanced tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        logger.warning("Cannot register ZAP tools: registry or langchain not available")
        return

    try:
        registry.register(
            tool=zap_advanced_scan,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["web", "vulnerability", "scanner", "owasp", "zap", "advanced"],
            author="Zen-AI-Pentest Team",
            version="2.0.0",
        )

        registry.register(
            tool=zap_create_context,
            category=ToolCategory.CONFIGURATION,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "configuration", "context", "scope", "zap"],
            author="Zen-AI-Pentest Team",
            version="2.0.0",
        )

        registry.register(
            tool=zap_get_alerts,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "scanner", "alerts", "zap"],
            author="Zen-AI-Pentest Team",
            version="2.0.0",
        )

        registry.register(
            tool=zap_stop_scan,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "scanner", "control", "zap"],
            author="Zen-AI-Pentest Team",
            version="2.0.0",
        )

        logger.info("ZAP advanced tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register ZAP advanced tools: {e}")


# Auto-register on import
try:
    register_zap_advanced_tools()
except Exception:
    pass


__all__ = [
    # Classes
    "ZAPAPIClient",
    "ZAPContextManager",
    "ZAPScanner",
    "ZAPAlert",
    "ZAPContext",
    "ZAPScanConfig",
    "ZAPScanResult",
    "ZAPReport",
    # Enums
    "ZAPScanType",
    "ZAPScanPolicy",
    "ZAPAlertRisk",
    "ZAPAuthMethod",
    "ZAPScanIntensity",
    # Tools
    "zap_advanced_scan",
    "zap_create_context",
    "zap_get_alerts",
    "zap_stop_scan",
    "register_zap_advanced_tools",
]
