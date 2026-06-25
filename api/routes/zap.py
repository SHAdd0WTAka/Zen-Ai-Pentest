"""
OWASP ZAP API Routes

Complete API endpoints for OWASP ZAP integration:
- Start ZAP scans (Spider, Active, Full)
- Check scan status
- Get alerts/findings
- Generate reports
- Manage authentication

Author: Zen-AI-Pentest Team
License: MIT
Version: 3.0.0
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

# Try to import auth dependencies
try:
    from api.auth_simple import get_current_user

    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

    def get_current_user():
        return None


# Import ZAP integration
try:
    from tools.zap_integration_enhanced import (
        ZAPAlert,
        ZAPAutomation,
        ZAPClient,
    )

    ZAP_AVAILABLE = True
except ImportError as e:
    ZAP_AVAILABLE = False
    logging.warning(f"ZAP integration not available: {e}")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools/zap", tags=["OWASP ZAP"])


class AuthType(str, Enum):
    """Authentication types"""

    NONE = "none"
    FORM = "form"
    JWT = "jwt"
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class ScanPolicy(str, Enum):
    """ZAP scan policies"""

    DEFAULT = "Default"
    API = "API Policy"
    FULL = "Full Policy"
    QUICK = "Quick Policy"


class ZAPAuthConfig(BaseModel):
    """ZAP authentication configuration"""

    type: AuthType = AuthType.NONE
    # Form-based auth
    login_url: Optional[str] = None
    username_field: Optional[str] = Field(default="username", alias="usernameField")
    password_field: Optional[str] = Field(default="password", alias="passwordField")
    username: Optional[str] = None
    password: Optional[str] = None
    # JWT/Bearer
    token: Optional[str] = None
    token_header: str = Field(default="Authorization", alias="tokenHeader")
    # API Key
    api_key: Optional[str] = Field(None, alias="apiKey")
    api_key_header: str = Field(default="X-API-Key", alias="apiKeyHeader")
    # Basic Auth
    basic_username: Optional[str] = Field(None, alias="basicUsername")
    basic_password: Optional[str] = Field(None, alias="basicPassword")
    # OAuth2
    oauth_token: Optional[str] = Field(None, alias="oauthToken")

    model_config = ConfigDict(populate_by_name=True)


class ZAPScanRequest(BaseModel):
    """ZAP scan request"""

    target: str = Field(..., description="Target URL to scan")
    policy: ScanPolicy = Field(default=ScanPolicy.DEFAULT, description="Scan policy")
    spider: bool = Field(default=True, description="Enable spider scan")
    ajax_spider: bool = Field(default=False, alias="ajaxSpider", description="Enable AJAX spider")
    active_scan: bool = Field(default=True, alias="activeScan", description="Enable active scan")
    auth: Optional[ZAPAuthConfig] = Field(None, description="Authentication configuration")
    max_depth: int = Field(default=5, ge=1, le=10, alias="maxDepth", description="Maximum crawl depth")
    timeout: int = Field(default=600, ge=60, le=3600, description="Scan timeout in seconds")
    zap_url: str = Field(default="http://localhost:8080", alias="zapUrl", description="ZAP API URL")
    zap_api_key: Optional[str] = Field(None, alias="zapApiKey", description="ZAP API key")

    model_config = ConfigDict(populate_by_name=True)


class ZAPQuickScanRequest(BaseModel):
    """ZAP quick scan request"""

    target: str = Field(..., description="Target URL to scan")
    zap_url: str = Field(default="http://localhost:8080", alias="zapUrl")
    zap_api_key: Optional[str] = Field(None, alias="zapApiKey")

    model_config = ConfigDict(populate_by_name=True)


class ZAPSpiderRequest(BaseModel):
    """ZAP spider request"""

    target: str = Field(..., description="Target URL to crawl")
    max_depth: int = Field(default=5, ge=1, le=10, alias="maxDepth")
    zap_url: str = Field(default="http://localhost:8080", alias="zapUrl")
    zap_api_key: Optional[str] = Field(None, alias="zapApiKey")

    model_config = ConfigDict(populate_by_name=True)


class ZAPAlertResponse(BaseModel):
    """ZAP alert response"""

    id: str = Field(..., alias="alertId")
    name: str
    risk: str
    confidence: str
    description: str
    solution: str
    url: str
    method: str
    param: Optional[str] = None
    attack: Optional[str] = None
    evidence: Optional[str] = None
    cwe_id: Optional[str] = Field(None, alias="cweId")
    wasc_id: Optional[str] = Field(None, alias="wascId")

    model_config = ConfigDict(populate_by_name=True)


class ZAPScanResponse(BaseModel):
    """ZAP scan response"""

    scan_id: str = Field(..., alias="scanId", description="Unique scan ID")
    target: str
    status: str = Field(..., description="Scan status (pending, running, completed, failed)")
    progress: int = Field(0, ge=0, le=100, description="Scan progress percentage")
    phase: str = Field("initializing", description="Current scan phase")
    message: Optional[str] = None
    urls_crawled: int = Field(0, alias="urlsCrawled")
    urls_audited: int = Field(0, alias="urlsAudited")
    alerts_count: int = Field(0, alias="alertsCount")
    risk_summary: Optional[Dict[str, int]] = Field(None, alias="riskSummary")
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    error: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ZAPAlertsResponse(BaseModel):
    """ZAP alerts list response"""

    target: Optional[str] = None
    total: int
    high: int
    medium: int
    low: int
    informational: int
    alerts: List[ZAPAlertResponse]


class ZAPReportRequest(BaseModel):
    """ZAP report generation request"""

    format: str = Field(default="json", pattern="^(html|json|xml|md)$")
    title: Optional[str] = None
    risk_filter: Optional[List[str]] = Field(None, alias="riskFilter")
    zap_url: str = Field(default="http://localhost:8080", alias="zapUrl")
    zap_api_key: Optional[str] = Field(None, alias="zapApiKey")

    model_config = ConfigDict(populate_by_name=True)


class ZAPReportResponse(BaseModel):
    """ZAP report response"""

    format: str
    generated_at: datetime = Field(..., alias="generatedAt")
    title: str
    content: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = Field(None, alias="downloadUrl")
    alert_count: int = Field(0, alias="alertCount")

    model_config = ConfigDict(populate_by_name=True)


class ZAPStatusResponse(BaseModel):
    """ZAP API status response"""

    connected: bool
    version: Optional[str] = None
    api_url: str = Field(..., alias="apiUrl")

    model_config = ConfigDict(populate_by_name=True)


# In-memory storage for active scans (use Redis/DB in production)
_active_scans: Dict[str, Dict[str, Any]] = {}


def _build_auth_config(auth: Optional[ZAPAuthConfig]) -> Optional[Dict[str, Any]]:
    """Build authentication config for ZAP"""
    if not auth or auth.type == AuthType.NONE:
        return None

    config = {"type": auth.type.value}

    if auth.type == AuthType.FORM:
        config.update(
            {
                "login_url": auth.login_url,
                "username_field": auth.username_field,
                "password_field": auth.password_field,
                "username": auth.username,
                "password": auth.password,
            }
        )
    elif auth.type in [AuthType.JWT, AuthType.OAUTH2]:
        config.update(
            {
                "token": auth.token or auth.oauth_token,
                "header": auth.token_header,
            }
        )
    elif auth.type == AuthType.API_KEY:
        config.update(
            {
                "api_key": auth.api_key,
                "header": auth.api_key_header,
            }
        )
    elif auth.type == AuthType.BASIC:
        config.update(
            {
                "basic_username": auth.basic_username or auth.username,
                "basic_password": auth.basic_password or auth.password,
            }
        )

    return config


def _alert_to_response(alert: ZAPAlert) -> ZAPAlertResponse:
    """Convert ZAPAlert to response model"""
    return ZAPAlertResponse(
        alertId=alert.alert_id,
        name=alert.name,
        risk=alert.risk,
        confidence=alert.confidence,
        description=alert.description,
        solution=alert.solution,
        url=alert.url,
        method=alert.method,
        param=alert.param or None,
        attack=alert.attack or None,
        evidence=alert.evidence or None,
        cweId=alert.cwe_id or None,
        wascId=alert.wasc_id or None,
    )


@router.get("/status", response_model=ZAPStatusResponse)
async def get_zap_status(
    zap_url: str = Query(default="http://localhost:8080", alias="zapUrl"),
    zap_api_key: Optional[str] = Query(default=None, alias="zapApiKey"),
):
    """
    Check ZAP API connectivity and version.

    Returns connection status and ZAP version if available.
    """
    if not ZAP_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ZAP integration not available",
        )

    try:
        client = ZAPClient(zap_url, zap_api_key)
        connected = await client.check_connection()
        version = client._version if connected else None
        await client.close()

        return ZAPStatusResponse(
            connected=connected,
            version=version,
            apiUrl=zap_url,
        )
    except Exception as e:
        logger.error(f"Failed to check ZAP status: {e}")
        return ZAPStatusResponse(
            connected=False,
            apiUrl=zap_url,
        )


@router.post("/scan", response_model=ZAPScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_zap_scan(
    request: ZAPScanRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Start a full ZAP security scan.

    This endpoint initiates a comprehensive security scan including:
    - Spider crawl
    - Passive scan analysis
    - Active vulnerability scanning

    The scan runs asynchronously. Use the returned scan_id to check status.

    **Authentication Types:**
    - `form`: Form-based authentication
    - `jwt`: JWT Bearer token
    - `api_key`: API Key in header
    - `basic`: HTTP Basic authentication
    - `oauth2`: OAuth2 Bearer token

    **Scan Policies:**
    - `Default`: Standard OWASP Top 10 coverage
    - `API`: REST/GraphQL specific tests
    - `Full`: All rules (comprehensive but slower)
    - `Quick`: High/Critical only (fast)
    """
    if not ZAP_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ZAP integration not available",
        )

    scan_id = f"zap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(request) % 10000}"

    # Initialize scan status
    _active_scans[scan_id] = {
        "scan_id": scan_id,
        "target": request.target,
        "status": "pending",
        "progress": 0,
        "phase": "initializing",
        "message": "Scan queued",
        "urls_crawled": 0,
        "urls_audited": 0,
        "alerts_count": 0,
        "risk_summary": {"High": 0, "Medium": 0, "Low": 0, "Informational": 0},
        "started_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "alerts": [],
    }

    # Start scan in background
    background_tasks.add_task(
        _run_zap_scan,
        scan_id,
        request,
    )

    return ZAPScanResponse(
        scanId=scan_id,
        target=request.target,
        status="pending",
        progress=0,
        phase="initializing",
        message="Scan queued",
    )


@router.get("/scan/{scan_id}", response_model=ZAPScanResponse)
async def get_scan_status(
    scan_id: str,
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Get the status of a running or completed ZAP scan.

    Returns current progress, phase, and results summary.
    """
    if scan_id not in _active_scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )

    scan = _active_scans[scan_id]

    return ZAPScanResponse(
        scanId=scan["scan_id"],
        target=scan["target"],
        status=scan["status"],
        progress=scan["progress"],
        phase=scan["phase"],
        message=scan.get("message"),
        urlsCrawled=scan["urls_crawled"],
        urlsAudited=scan["urls_audited"],
        alertsCount=scan["alerts_count"],
        riskSummary=scan["risk_summary"],
        startedAt=scan["started_at"],
        completedAt=scan.get("completed_at"),
        error=scan.get("error"),
    )


@router.get("/scans", response_model=List[ZAPScanResponse])
async def list_scans(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    List all ZAP scans with optional status filtering.

    Returns a list of scan summaries.
    """
    scans = list(_active_scans.values())

    if status:
        scans = [s for s in scans if s["status"] == status]

    # Sort by start time (newest first)
    scans.sort(key=lambda x: x["started_at"], reverse=True)

    return [
        ZAPScanResponse(
            scanId=s["scan_id"],
            target=s["target"],
            status=s["status"],
            progress=s["progress"],
            phase=s["phase"],
            message=s.get("message"),
            urlsCrawled=s["urls_crawled"],
            urlsAudited=s["urls_audited"],
            alertsCount=s["alerts_count"],
            riskSummary=s["risk_summary"],
            startedAt=s["started_at"],
            completedAt=s.get("completed_at"),
            error=s.get("error"),
        )
        for s in scans
    ]


@router.post("/spider", response_model=ZAPScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_spider_scan(
    request: ZAPSpiderRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Start a ZAP spider crawl only (no active scanning).

    Discovers URLs on the target without sending attack payloads.
    """
    if not ZAP_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ZAP integration not available",
        )

    scan_id = f"spider_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(request) % 10000}"

    _active_scans[scan_id] = {
        "scan_id": scan_id,
        "target": request.target,
        "status": "pending",
        "progress": 0,
        "phase": "spider",
        "message": "Spider scan queued",
        "urls_crawled": 0,
        "urls_audited": 0,
        "alerts_count": 0,
        "risk_summary": {"High": 0, "Medium": 0, "Low": 0, "Informational": 0},
        "started_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "alerts": [],
    }

    background_tasks.add_task(
        _run_spider_scan,
        scan_id,
        request,
    )

    return ZAPScanResponse(
        scanId=scan_id,
        target=request.target,
        status="pending",
        progress=0,
        phase="spider",
        message="Spider scan queued",
    )


@router.get("/alerts", response_model=ZAPAlertsResponse)
async def get_alerts(
    target: Optional[str] = Query(None, description="Filter by target URL"),
    min_risk: str = Query(default="Low", alias="minRisk", description="Minimum risk level"),
    zap_url: str = Query(default="http://localhost:8080", alias="zapUrl"),
    zap_api_key: Optional[str] = Query(default=None, alias="zapApiKey"),
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Get security alerts/findings from ZAP.

    Returns a list of discovered vulnerabilities with details.
    """
    if not ZAP_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ZAP integration not available",
        )

    try:
        # Map risk levels
        risk_levels = ["High", "Medium", "Low", "Informational"]
        if min_risk in risk_levels:
            idx = risk_levels.index(min_risk)
            risk_levels = risk_levels[: idx + 1]

        client = ZAPClient(zap_url, zap_api_key)
        alerts = await client.get_alerts(
            risk_levels=risk_levels,
            base_url=target,
        )
        await client.close()

        # Calculate counts
        counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
        for alert in alerts:
            if alert.risk in counts:
                counts[alert.risk] += 1

        return ZAPAlertsResponse(
            target=target,
            total=len(alerts),
            high=counts["High"],
            medium=counts["Medium"],
            low=counts["Low"],
            informational=counts["Informational"],
            alerts=[_alert_to_response(a) for a in alerts],
        )
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}",
        )


@router.get("/scan/{scan_id}/alerts", response_model=ZAPAlertsResponse)
async def get_scan_alerts(
    scan_id: str,
    min_risk: str = Query(default="Low", alias="minRisk"),
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Get alerts for a specific scan.

    Returns findings discovered during the specified scan.
    """
    if scan_id not in _active_scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )

    scan = _active_scans[scan_id]
    alerts = scan.get("alerts", [])

    # Filter by risk
    risk_map = {
        "Informational": 0,
        "Low": 1,
        "Medium": 2,
        "High": 3,
    }
    min_risk_level = risk_map.get(min_risk, 0)
    filtered_alerts = [a for a in alerts if risk_map.get(a.risk, 0) >= min_risk_level]

    return ZAPAlertsResponse(
        target=scan["target"],
        total=len(filtered_alerts),
        high=sum(1 for a in filtered_alerts if a.risk == "High"),
        medium=sum(1 for a in filtered_alerts if a.risk == "Medium"),
        low=sum(1 for a in filtered_alerts if a.risk == "Low"),
        informational=sum(1 for a in filtered_alerts if a.risk == "Informational"),
        alerts=[_alert_to_response(a) for a in filtered_alerts],
    )


@router.post("/report", response_model=ZAPReportResponse)
async def generate_report(
    request: ZAPReportRequest,
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Generate a security report from ZAP findings.

    Supports HTML, JSON, XML, and Markdown formats.
    """
    if not ZAP_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ZAP integration not available",
        )

    try:
        client = ZAPClient(request.zap_url, request.zap_api_key)
        report = await client.generate_report(
            format=request.format,
            title=request.title,
        )
        await client.close()

        alert_count = 0
        if isinstance(report, dict):
            alert_count = len(report.get("alerts", []))

        return ZAPReportResponse(
            format=request.format,
            generatedAt=datetime.now(),
            title=request.title or f"ZAP Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=report if isinstance(report, dict) else None,
            alertCount=alert_count,
        )
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.delete("/scan/{scan_id}", status_code=status.HTTP_200_OK)
async def delete_scan(
    scan_id: str,
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Delete a scan record.

    Removes the scan from the active scans list.
    """
    if scan_id not in _active_scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )

    del _active_scans[scan_id]

    return {"message": f"Scan {scan_id} deleted"}


@router.post("/scan/{scan_id}/stop", response_model=ZAPScanResponse)
async def stop_scan(
    scan_id: str,
    current_user: Optional[Any] = Depends(get_current_user) if AUTH_AVAILABLE else None,
):
    """
    Stop a running ZAP scan.

    Attempts to stop the scan gracefully.
    """
    if scan_id not in _active_scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )

    scan = _active_scans[scan_id]

    if scan["status"] not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scan cannot be stopped (status: {scan['status']})",
        )

    scan["status"] = "stopped"
    scan["message"] = "Scan stopped by user"
    scan["completed_at"] = datetime.now()

    return ZAPScanResponse(
        scanId=scan["scan_id"],
        target=scan["target"],
        status="stopped",
        progress=scan["progress"],
        phase=scan["phase"],
        message="Scan stopped by user",
    )


# Background task functions
async def _run_zap_scan(scan_id: str, request: ZAPScanRequest):
    """Run ZAP scan in background"""
    scan = _active_scans.get(scan_id)
    if not scan:
        return

    scan["status"] = "running"
    scan["phase"] = "initializing"
    scan["message"] = "Starting ZAP scan"

    try:
        # Build auth config
        auth = _build_auth_config(request.auth)

        # Create automation instance
        automation = ZAPAutomation(
            zap_url=request.zap_url,
            api_key=request.zap_api_key,
        )

        async with automation:

            def progress_callback(update: Dict[str, Any]):
                scan["phase"] = update.get("phase", scan["phase"])
                scan["message"] = update.get("message", "")
                if "progress" in update:
                    scan["progress"] = update["progress"]

            result = await automation.full_scan(
                target=request.target,
                auth=auth,
                policy=request.policy.value,
                progress_callback=progress_callback,
            )

            # Update scan with results
            scan["status"] = "completed" if result.success else "failed"
            scan["progress"] = 100
            scan["urls_crawled"] = result.urls_crawled
            scan["urls_audited"] = result.urls_audited
            scan["alerts_count"] = len(result.alerts)
            scan["alerts"] = result.alerts
            scan["risk_summary"] = result.risk_counts
            scan["completed_at"] = datetime.now()

            if not result.success:
                scan["error"] = result.error
                scan["message"] = f"Scan failed: {result.error}"
            else:
                scan["message"] = f"Scan completed. Found {len(result.alerts)} alerts."

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        scan["status"] = "failed"
        scan["error"] = str(e)
        scan["message"] = f"Scan failed: {str(e)}"
        scan["completed_at"] = datetime.now()


async def _run_spider_scan(scan_id: str, request: ZAPSpiderRequest):
    """Run spider scan in background"""
    scan = _active_scans.get(scan_id)
    if not scan:
        return

    scan["status"] = "running"
    scan["message"] = "Starting spider scan"

    try:
        client = ZAPClient(request.zap_url, request.zap_api_key)

        async with client:

            def progress_callback(progress: int):
                scan["progress"] = progress
                scan["message"] = f"Spider crawling... {progress}%"

            await client.spider_scan(
                target=request.target,
                max_depth=request.max_depth,
                progress_callback=progress_callback,
            )

            # Get URLs
            urls_result = await client._request("core/view/urls")
            urls = urls_result.get("urls", [])

            scan["status"] = "completed"
            scan["progress"] = 100
            scan["urls_crawled"] = len(urls)
            scan["completed_at"] = datetime.now()
            scan["message"] = f"Spider completed. Discovered {len(urls)} URLs."

    except Exception as e:
        logger.error(f"Spider scan {scan_id} failed: {e}")
        scan["status"] = "failed"
        scan["error"] = str(e)
        scan["message"] = f"Spider failed: {str(e)}"
        scan["completed_at"] = datetime.now()


# ReAct Agent tool integration
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
def zap_api_start_scan(
    target: str,
    policy: str = "Default",
    auth_type: str = "",
    zap_url: str = "http://localhost:8080",
) -> str:
    """
    Start a ZAP security scan via API.

    This tool initiates a full security scan against a web target using
    the OWASP ZAP scanner through the API.

    Args:
        target: Target URL to scan (e.g., "https://example.com")
        policy: Scan policy (Default, API, Full, Quick)
        auth_type: Authentication type if needed (form, jwt, basic, oauth2)
        zap_url: ZAP API URL

    Returns:
        Scan ID and initial status
    """
    import httpx

    try:
        response = httpx.post(
            f"{zap_url}/tools/zap/scan",
            json={
                "target": target,
                "policy": policy,
                "auth": {"type": auth_type} if auth_type else None,
            },
            timeout=10.0,
        )

        if response.status_code == 202:
            data = response.json()
            return f"ZAP scan started successfully!\nScan ID: {data.get('scanId')}\nTarget: {data.get('target')}\nStatus: {data.get('status')}"
        else:
            return f"Failed to start scan: {response.text}"

    except Exception as e:
        return f"Error starting ZAP scan: {e}"


@tool
def zap_api_check_status(
    scan_id: str,
    api_url: str = "http://localhost:8000",
) -> str:
    """
    Check the status of a ZAP scan.

    Args:
        scan_id: The scan ID returned from start_scan
        api_url: The API base URL

    Returns:
        Current scan status and progress
    """
    import httpx

    try:
        response = httpx.get(
            f"{api_url}/tools/zap/scan/{scan_id}",
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            lines = [
                f"Scan Status: {data.get('status')}",
                f"Target: {data.get('target')}",
                f"Progress: {data.get('progress')}%",
                f"Phase: {data.get('phase')}",
            ]

            if data.get("riskSummary"):
                lines.extend(
                    [
                        "",
                        "Findings:",
                        f"  High: {data['riskSummary'].get('High', 0)}",
                        f"  Medium: {data['riskSummary'].get('Medium', 0)}",
                        f"  Low: {data['riskSummary'].get('Low', 0)}",
                    ]
                )

            return "\n".join(lines)
        else:
            return f"Failed to get status: {response.text}"

    except Exception as e:
        return f"Error checking scan status: {e}"


@tool
def zap_api_get_alerts(
    target: Optional[str] = None,
    min_risk: str = "Low",
    api_url: str = "http://localhost:8000",
) -> str:
    """
    Get security alerts from ZAP via API.

    Args:
        target: Optional target URL filter
        min_risk: Minimum risk level (Informational, Low, Medium, High)
        api_url: The API base URL

    Returns:
        List of security findings
    """
    import httpx

    try:
        params = {"minRisk": min_risk}
        if target:
            params["target"] = target

        response = httpx.get(
            f"{api_url}/tools/zap/alerts",
            params=params,
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            lines = [
                f"Total Alerts: {data.get('total')}",
                f"High: {data.get('high')}",
                f"Medium: {data.get('medium')}",
                f"Low: {data.get('low')}",
                "",
                "Top Findings:",
            ]

            for alert in data.get("alerts", [])[:10]:
                lines.append(f"\n[{alert.get('risk')}] {alert.get('name')}")
                lines.append(f"  URL: {alert.get('url')}")
                lines.append(f"  Parameter: {alert.get('param') or 'N/A'}")

            return "\n".join(lines)
        else:
            return f"Failed to get alerts: {response.text}"

    except Exception as e:
        return f"Error getting alerts: {e}"


@tool
def zap_api_generate_report(
    format: str = "json",
    api_url: str = "http://localhost:8000",
) -> str:
    """
    Generate a ZAP security report via API.

    Args:
        format: Report format (html, json, xml, md)
        api_url: The API base URL

    Returns:
        Report generation status
    """
    import httpx

    try:
        response = httpx.post(
            f"{api_url}/tools/zap/report",
            json={"format": format},
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            return f"Report generated!\nFormat: {data.get('format')}\nTitle: {data.get('title')}\nAlerts: {data.get('alertCount')}"
        else:
            return f"Failed to generate report: {response.text}"

    except Exception as e:
        return f"Error generating report: {e}"


# Tool Registry Integration
try:
    from tools.tool_registry import ToolCategory, ToolSafetyLevel, registry

    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_zap_api_tools():
    """Register ZAP API tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=zap_api_start_scan,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.DANGEROUS,
            requires_approval=True,
            tags=["web", "vulnerability", "scanner", "owasp", "zap", "api"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_api_check_status,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "scanner", "status", "zap", "api"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_api_get_alerts,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "scanner", "alerts", "findings", "zap", "api"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        registry.register(
            tool=zap_api_generate_report,
            category=ToolCategory.REPORTING,
            safety_level=ToolSafetyLevel.SAFE,
            requires_approval=False,
            tags=["web", "report", "zap", "documentation", "api"],
            author="Zen-AI-Pentest Team",
            version="3.0.0",
        )

        logger.info("ZAP API tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register ZAP API tools: {e}")


# Auto-register on import
try:
    register_zap_api_tools()
except Exception:
    pass
