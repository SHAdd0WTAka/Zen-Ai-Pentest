"""
Zen-AI-Pentest API Server

FastAPI-basiertes Backend für das Pentesting-Framework.
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.schemas import (
    FindingCreate,
    FindingResponse,
    ReportCreate,
    ReportResponse,
    ScanCreate,
    ScanResponse,
    ScanUpdate,
    ScheduledScanCreate,
    ScheduledScanResponse,
    ScheduledScanUpdate,
    TokenResponse,
    ToolExecuteRequest,
    ToolExecuteResponse,
    UserLogin,
)
from database.crud import (
    create_finding,
    create_report,
    create_scan,
    get_findings,
    get_reports,
    get_scan,
    get_scans,
    update_scan_status,
)
from database.models import Report, SessionLocal, get_db, init_db

# Import new auth system
try:
    from auth import (
        AuthConfig,
        AuthMiddleware,
        JWTHandler,
        MFAHandler,
        PasswordHasher,
        Permission,
        RBACManager,
        Role,
        UserManager,
        get_user_manager,
    )
    from database.auth_models import get_auth_db, init_auth_db

    NEW_AUTH_AVAILABLE = True
except ImportError as e:
    print(f"Auth import error: {e}")
    NEW_AUTH_AVAILABLE = False

# Legacy auth as fallback
from api.auth_simple import authenticate_user as legacy_authenticate_user
from api.auth_simple import create_access_token as legacy_create_access_token
from api.auth_simple import verify_token as legacy_verify_token
from api.csrf_protection import csrf_protection, require_csrf
from api.rate_limiter import check_auth_rate_limit
from api.websocket import ConnectionManager
from api.websocket_manager import manager

# Import Agent v2 routes
try:
    from api.routes.agents_v2 import router as agents_v2_router
    from api.routes.agents_v2 import agent_websocket, agent_manager
    AGENTS_V2_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Agent v2 routes not available: {e}")
    AGENTS_V2_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize new auth components (after logger is defined)
_jwt_handler = None
_rbac_manager = None
_password_hasher = None
_user_manager = None

if NEW_AUTH_AVAILABLE:
    try:
        _jwt_handler = JWTHandler()
        _rbac_manager = RBACManager()
        _password_hasher = PasswordHasher()
        _user_manager = UserManager(_jwt_handler, _password_hasher)
        logger.info("✅ New auth system initialized with database support")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize new auth components: {e}")
        NEW_AUTH_AVAILABLE = False

# Security
security = HTTPBearer()


# Create unified verify_token that works with both systems
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token - uses new auth system if available, falls back to legacy
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try new auth system first
    if NEW_AUTH_AVAILABLE and _jwt_handler:
        try:
            from auth.jwt_handler import TokenExpiredError, TokenInvalidError

            payload = _jwt_handler.decode_token(credentials.credentials)
            return {
                "sub": payload.sub,
                "username": payload.sub,
                "role": payload.roles[0] if payload.roles else "user",
                "roles": payload.roles,
                "permissions": payload.permissions,
                "session_id": payload.session_id,
            }
        except TokenExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except TokenInvalidError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Fallback to legacy
    from api.auth_simple import verify_token as legacy_verify

    return legacy_verify(credentials)


# WebSocket Manager
ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up Zen-AI-Pentest API...")
    init_db()
    logger.info("Database initialized")

    # Initialize auth database
    if NEW_AUTH_AVAILABLE:
        try:
            init_auth_db()
            logger.info("Auth database initialized")

            # Create default admin user if not exists
            from database.auth_models import SessionLocal, UserRole, create_user, get_user_by_username

            db = SessionLocal()
            try:
                admin = get_user_by_username(db, "admin")
                if not admin:
                    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
                    create_user(
                        db,
                        username="admin",
                        email="admin@zen-pentest.local",
                        hashed_password=_password_hasher.hash_password(admin_pass),
                        role=UserRole.ADMIN,
                    )
                    logger.info("Default admin user created")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Could not initialize auth database: {e}")

    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Zen-AI-Pentest API", description="Professional Pentesting Framework API", version="2.2.0", lifespan=lifespan
)

# =============================================================================
# CORS Configuration
# =============================================================================
# Load allowed origins from environment variable
# Format: comma-separated list of origins
# Example: CORS_ORIGINS=https://domain.com,https://app.domain.com
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,  # 10 minutes cache for preflight
)

# Add new auth middleware if available
if NEW_AUTH_AVAILABLE:
    app.add_middleware(AuthMiddleware)

# ============================================================================
# AUTHENTICATION
# ============================================================================

# =============================================================================
# Secure Credential Store (In production: use database!)
# =============================================================================
# Load admin credentials from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    import warnings

    warnings.warn(
        "ADMIN_PASSWORD not set! Using insecure default for development only. "
        "Set ADMIN_PASSWORD environment variable for production!",
        RuntimeWarning,
    )
    ADMIN_PASSWORD = "admin"  # Only for development!


def verify_admin_credentials(username: str, password: str) -> bool:
    """Securely verify admin credentials using constant-time comparison"""
    import hmac

    return hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)


@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    """
    Login und JWT Token erhalten (Database-backed)

    - **username**: Username (min. 3 Zeichen)
    - **password**: Passwort (min. 6 Zeichen)

    Returns JWT Token für authentifizierte Requests
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "")
    check_auth_rate_limit(client_ip)

    # Use database-backed auth system if available
    if NEW_AUTH_AVAILABLE and _user_manager:
        from database.auth_models import SessionLocal

        db = SessionLocal()
        try:
            # Authenticate user against database
            user = _user_manager.authenticate_user(db, credentials.username, credentials.password, client_ip, user_agent)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create session with tokens
            session_data = _user_manager.create_session(db, user, client_ip, user_agent)

            return {
                "access_token": session_data["access_token"],
                "refresh_token": session_data["refresh_token"],
                "token_type": "bearer",
                "expires_in": 900,  # 15 minutes
                "username": user.username,
                "role": user.role.value,
            }
        finally:
            db.close()

    # Fallback to legacy auth
    user = legacy_authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = legacy_create_access_token(data={"sub": user["username"], "role": user["role"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 Stunden
        "username": user["username"],
        "role": user["role"],
    }


@app.get("/auth/me")
async def me(request: Request):
    """Get current user info"""
    # Try new auth system first
    if NEW_AUTH_AVAILABLE and _jwt_handler:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                from auth.jwt_handler import TokenExpiredError, TokenInvalidError

                payload = _jwt_handler.decode_token(token)
                return {
                    "sub": payload.sub,
                    "roles": payload.roles,
                    "permissions": payload.permissions,
                    "session_id": payload.session_id,
                }
            except (TokenExpiredError, TokenInvalidError):
                pass  # Fall through to legacy

    # Fallback to legacy
    return await legacy_verify_token(request)


@app.post("/auth/refresh")
async def refresh_token(request: Request):
    """
    Refresh access token using refresh token (Database-backed)

    Header: Authorization: Bearer <refresh_token>
    """
    if not NEW_AUTH_AVAILABLE or not _user_manager:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Token refresh not available with legacy auth")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_token = auth_header[7:]
    client_ip = request.client.host if request.client else "unknown"

    from database.auth_models import SessionLocal

    db = SessionLocal()
    try:
        # Use UserManager to refresh session
        result = _user_manager.refresh_session(db, refresh_token, client_ip)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "expires_in": result["expires_in"],
        }
    finally:
        db.close()


@app.get("/csrf-token")
async def get_csrf_token(response: Response):
    """
    Get CSRF Token for protected endpoints

    Returns CSRF token that must be included in X-CSRF-Token header
    for all POST/PUT/DELETE requests.
    """
    return csrf_protection.set_token(response)


@app.post("/auth/logout")
async def logout(request: Request, user: dict = Depends(verify_token)):
    """
    Logout - revoke current session (Database-backed)

    Requires valid access token.
    """
    if NEW_AUTH_AVAILABLE and _user_manager:
        from database.auth_models import SessionLocal

        # Get session_id from token payload
        session_id = user.get("session_id")
        if not session_id:
            # Try to get from request state (set by middleware)
            session_id = getattr(request.state, "session_id", None)

        if session_id:
            db = SessionLocal()
            try:
                _user_manager.revoke_session(db, session_id, "logout")
            finally:
                db.close()

    return {"message": "Logged out successfully"}


@app.post("/auth/logout-all")
async def logout_all_devices(request: Request, user: dict = Depends(verify_token)):
    """
    Logout from all devices - revoke all sessions (Database-backed)

    Requires valid access token.
    """
    if NEW_AUTH_AVAILABLE and _user_manager:
        from database.auth_models import SessionLocal

        user_id = user.get("sub")
        if user_id:
            db = SessionLocal()
            try:
                count = _user_manager.revoke_all_user_sessions(db, int(user_id), "logout_all")
                return {"message": f"Logged out from {count} device(s)"}
            finally:
                db.close()

    return {"message": "Logged out from all devices"}


# ============================================================================
# SCANS
# ============================================================================


@app.post("/scans", response_model=ScanResponse)
async def create_new_scan(
    request: Request,
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
    _: bool = Depends(require_csrf),
):
    """Create a new pentest scan"""
    db_scan = create_scan(
        db, name=scan.name, target=scan.target, scan_type=scan.scan_type, config=scan.config, user_id=user.get("sub")
    )

    # Start scan in background
    background_tasks.add_task(run_scan_task, db_scan.id, scan.dict())

    return db_scan


@app.get("/scans", response_model=List[ScanResponse])
async def list_scans(
    skip: int = 0, limit: int = 100, status: Optional[str] = None, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """List all scans with optional filtering"""
    scans = get_scans(db, skip=skip, limit=limit, status=status)
    return scans


@app.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_by_id(scan_id: int, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Get scan details by ID"""
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.patch("/scans/{scan_id}", response_model=ScanResponse)
async def update_scan(scan_id: int, update: ScanUpdate, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Update scan status or config"""
    scan = update_scan_status(db, scan_id, update.status, update.config)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.delete("/scans/{scan_id}")
async def delete_scan(scan_id: int, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Delete a scan"""
    # Implementation here
    return {"message": "Scan deleted"}


# ============================================================================
# FINDINGS
# ============================================================================


@app.get("/scans/{scan_id}/findings", response_model=List[FindingResponse])
async def get_scan_findings(
    scan_id: int, severity: Optional[str] = None, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Get all findings for a scan"""
    findings = get_findings(db, scan_id, severity)
    return findings


@app.post("/scans/{scan_id}/findings", response_model=FindingResponse)
async def add_finding(scan_id: int, finding: FindingCreate, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Add a finding to a scan"""
    db_finding = create_finding(
        db,
        scan_id=scan_id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        cvss_score=finding.cvss_score,
        evidence=finding.evidence,
        tool=finding.tool,
    )
    return db_finding


@app.patch("/findings/{finding_id}")
async def update_finding(finding_id: int, update: dict, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Update a finding"""
    from database.models import Finding

    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Update allowed fields
    allowed_fields = ["title", "description", "severity", "cvss_score", "evidence", "remediation", "verified"]

    for field, value in update.items():
        if field in allowed_fields and hasattr(finding, field):
            setattr(finding, field, value)

    db.commit()
    db.refresh(finding)

    return {
        "id": finding.id,
        "title": finding.title,
        "severity": finding.severity,
        "verified": finding.verified,
        "message": "Finding updated successfully",
    }


# ============================================================================
# TOOLS EXECUTION
# ============================================================================


@app.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest, background_tasks: BackgroundTasks, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Execute a pentesting tool"""
    # Create scan entry
    db_scan = create_scan(
        db,
        name=f"Tool: {request.tool_name}",
        target=request.target,
        scan_type="tool_execution",
        config=request.parameters,
        user_id=user.get("sub"),
    )

    # Execute in background
    background_tasks.add_task(execute_tool_task, db_scan.id, request.tool_name, request.target, request.parameters)

    return ToolExecuteResponse(scan_id=db_scan.id, status="started", message=f"Tool {request.tool_name} execution started")


@app.get("/tools")
async def list_tools(user: dict = Depends(verify_token)):
    """List available tools"""
    from tools import TOOL_REGISTRY

    tools = []
    for name, func in TOOL_REGISTRY.items():
        if func:
            tools.append({"name": name, "description": func.__doc__ or "No description", "category": get_tool_category(name)})

    return {"tools": tools}


def get_tool_category(tool_name: str) -> str:
    """Get tool category based on name"""
    categories = {
        "nmap": "network",
        "masscan": "network",
        "scapy": "network",
        "tshark": "network",
        "burp": "web",
        "sqlmap": "web",
        "gobuster": "web",
        "metasploit": "exploitation",
        "hydra": "brute_force",
        "amass": "recon",
        "bloodhound": "ad",
        "cme": "ad",
        "responder": "ad",
        "aircrack": "wireless",
    }

    for key, cat in categories.items():
        if key in tool_name.lower():
            return cat
    return "other"


# ============================================================================
# REPORTS
# ============================================================================


@app.post("/reports", response_model=ReportResponse)
async def generate_report(
    report: ReportCreate, background_tasks: BackgroundTasks, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Generate a report from scan findings"""
    db_report = create_report(
        db, scan_id=report.scan_id, format=report.format, template=report.template, user_id=user.get("sub")
    )

    # Generate in background
    background_tasks.add_task(generate_report_task, db_report.id, report.scan_id, report.format)

    return db_report


@app.get("/reports", response_model=List[ReportResponse])
async def list_reports(skip: int = 0, limit: int = 100, user: dict = Depends(verify_token), db=Depends(get_db)):
    """List all reports"""
    reports = get_reports(db, skip, limit)
    return reports


@app.get("/reports/{report_id}/download")
async def download_report(report_id: int, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Download a generated report"""
    from fastapi.responses import FileResponse

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(report.file_path, filename=f"report_{report_id}.{report.format}")


# ============================================================================
# WEBSOCKET
# ============================================================================


@app.websocket("/ws/scans/{scan_id}")
async def scan_websocket(websocket: WebSocket, scan_id: int):
    """WebSocket for real-time scan updates"""
    await ws_manager.connect(websocket, scan_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, scan_id)


@app.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """WebSocket for global notifications"""
    await ws_manager.connect(websocket, "global")
    try:
        while True:
            _ = await websocket.receive_text()
            # Handle incoming messages
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "global")


# ============================================================================
# BACKGROUND TASKS
# ============================================================================


async def run_scan_task(scan_id: int, scan_config: dict):
    """Background task for running a scan"""
    from agents.react_agent import ReActAgent, ReActAgentConfig

    db = SessionLocal()
    try:
        update_scan_status(db, scan_id, "running")

        # Notify via WebSocket
        await ws_manager.broadcast_to_scan(scan_id, {"type": "status", "status": "running", "message": "Scan started"})

        # Run agent
        config = ReActAgentConfig(max_iterations=10)
        agent = ReActAgent(config)

        result = agent.run(target=scan_config["target"], objective=scan_config.get("objective", "comprehensive scan"))

        # Save findings
        for finding_data in result.get("findings", []):
            create_finding(
                db,
                scan_id=scan_id,
                title=f"Finding from {finding_data.get('tool', 'unknown')}",
                description=str(finding_data.get("result", ""))[:500],
                severity="medium",
                tool=finding_data.get("tool"),
            )

        update_scan_status(
            db, scan_id, "completed", {"result": result.get("final_message", ""), "iterations": result.get("iterations", 0)}
        )

        # Notify completion
        await ws_manager.broadcast_to_scan(
            scan_id,
            {
                "type": "status",
                "status": "completed",
                "message": "Scan completed",
                "findings_count": len(result.get("findings", [])),
            },
        )

    except Exception as e:
        logger.error(f"Scan task error: {e}")
        update_scan_status(db, scan_id, "failed", {"error": str(e)})

        await ws_manager.broadcast_to_scan(scan_id, {"type": "error", "message": str(e)})
    finally:
        db.close()


async def execute_tool_task(scan_id: int, tool_name: str, target: str, parameters: dict):
    """Execute a single tool"""
    from tools import TOOL_REGISTRY

    db = SessionLocal()
    try:
        tool_func = TOOL_REGISTRY.get(tool_name)
        if not tool_func:
            raise ValueError(f"Tool {tool_name} not found")

        # Execute tool
        result = tool_func(target, **parameters)

        # Save finding
        create_finding(
            db, scan_id=scan_id, title=f"{tool_name} result", description=str(result)[:1000], severity="info", tool=tool_name
        )

        update_scan_status(db, scan_id, "completed")

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        update_scan_status(db, scan_id, "failed", {"error": str(e)})
    finally:
        db.close()


async def generate_report_task(report_id: int, scan_id: int, format: str):
    """Generate report in background"""
    from reports.generator import ReportGenerator

    db = SessionLocal()
    try:
        generator = ReportGenerator()

        if format == "pdf":
            file_path = generator.generate_pdf(scan_id)
        elif format == "html":
            file_path = generator.generate_html(scan_id)
        else:
            file_path = generator.generate_json(scan_id)

        # Update report
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.file_path = file_path
            report.status = "completed"
            db.commit()

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "failed"
            db.commit()
    finally:
        db.close()


# ============================================================================
# HEALTH & INFO
# ============================================================================


@app.get("/health")
async def health_check():
    """
    Health check endpoint für Docker und Monitoring
    Prüft alle wichtigen Services
    """
    import redis
    from sqlalchemy import text

    health_status = {"status": "healthy", "version": "2.2.0", "timestamp": datetime.utcnow().isoformat(), "services": {}}

    # Check Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["services"]["database"] = {"status": "ok", "type": "postgresql"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_connect_timeout=2)
        redis_client.ping()
        health_status["services"]["redis"] = {"status": "ok"}
    except Exception as e:
        health_status["services"]["redis"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check API selbst
    health_status["services"]["api"] = {"status": "ok", "port": 8000}

    return health_status


@app.get("/info")
async def api_info():
    """API information"""
    return {
        "name": "Zen-AI-Pentest API",
        "version": "2.0.0",
        "description": "Professional Pentesting Framework",
        "endpoints": {"scans": "/scans", "findings": "/scans/{id}/findings", "tools": "/tools", "reports": "/reports"},
    }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket Endpoint für Echtzeit-Updates

    Nutzung:
    - Verbinden: wscat -c ws://localhost:8000/ws/client123
    - Ping: {"type": "ping"}
    - Subscribe: {"type": "subscribe", "channel": "scans"}
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong", "timestamp": datetime.utcnow().isoformat()}, websocket)

            elif message.get("type") == "subscribe":
                channel = message.get("channel", "general")
                await manager.send_personal_message(
                    {"type": "subscribed", "channel": channel, "client_id": client_id}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)


# ============================================================================
# AGENT COMMUNICATION V2 WEBSOCKET
# ============================================================================

class SimpleAgentConnection:
    """Simple agent connection manager for basic messaging"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        logger.info(f"Agent {agent_id} connected via WebSocket")
    
    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            logger.info(f"Agent {agent_id} disconnected")
    
    async def send_to_agent(self, agent_id: str, message: dict):
        if agent_id in self.active_connections:
            await self.active_connections[agent_id].send_json(message)
    
    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        for agent_id, ws in self.active_connections.items():
            if agent_id != exclude:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to {agent_id}: {e}")


agent_connection_manager = SimpleAgentConnection()


@app.websocket("/agents/ws")
async def agent_websocket_endpoint(websocket: WebSocket):
    """
    Agent Communication WebSocket Endpoint
    
    Simple protocol for agent messaging:
    1. Connect and send: {"type": "auth", "agent_id": "..."}
    2. Server responds: {"type": "auth_success"}
    3. Send messages: {"type": "message", "recipient": "...", "payload": {...}}
    4. Receive broadcasts and direct messages
    5. Send heartbeat: {"type": "heartbeat"}
    
    Production Note: In production, implement full AgentAuthenticator
    with API key validation as shown in api/routes/agents_v2.py
    """
    agent_id: Optional[str] = None
    
    try:
        # Wait for auth message without accepting first
        await websocket.accept()
        
        # Receive auth message
        auth_data = await websocket.receive_json()
        
        if auth_data.get("type") != "auth":
            await websocket.send_json({
                "type": "auth_failed",
                "error": "Expected auth message with type 'auth'"
            })
            await websocket.close()
            return
        
        agent_id = auth_data.get("agent_id")
        if not agent_id:
            await websocket.send_json({
                "type": "auth_failed",
                "error": "agent_id required"
            })
            await websocket.close()
            return
        
        # Simple auth success (production: validate API key)
        await agent_connection_manager.connect(websocket, agent_id)
        
        await websocket.send_json({
            "type": "auth_success",
            "agent_id": agent_id,
            "message": "Connected to Zen-AI-Pentest Agent Network"
        })
        
        # Main message loop
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                
                if msg_type == "message":
                    recipient = data.get("recipient", "broadcast")
                    payload = data.get("payload", {})
                    
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "ack",
                        "message_id": data.get("message_id", "unknown"),
                        "status": "received",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Route message
                    if recipient == "broadcast":
                        await agent_connection_manager.broadcast({
                            "type": "message",
                            "sender": agent_id,
                            "payload": payload,
                            "timestamp": datetime.utcnow().isoformat()
                        }, exclude=agent_id)
                    else:
                        # Direct message
                        await agent_connection_manager.send_to_agent(recipient, {
                            "type": "message",
                            "sender": agent_id,
                            "payload": payload,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                
                elif msg_type == "heartbeat":
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif msg_type == "disconnect":
                    break
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info(f"Agent WebSocket disconnected")
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
    finally:
        if agent_id:
            agent_connection_manager.disconnect(agent_id)


# ============================================================================
# SCHEDULED SCANS
# ============================================================================

# In-memory storage for scheduled scans (in production: use database)
SCHEDULED_SCANS = []
SCHEDULE_ID_COUNTER = 1


@app.post("/schedules", response_model=ScheduledScanResponse)
async def create_schedule(schedule: ScheduledScanCreate, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Create a new scheduled scan"""
    global SCHEDULE_ID_COUNTER

    schedule_dict = {
        "id": SCHEDULE_ID_COUNTER,
        "name": schedule.name,
        "target": schedule.target,
        "scan_type": schedule.scan_type,
        "frequency": schedule.frequency.value,
        "schedule_time": schedule.schedule_time,
        "schedule_day": schedule.schedule_day,
        "enabled": schedule.enabled,
        "notification_email": schedule.notification_email,
        "notification_slack": schedule.notification_slack,
        "last_run_at": None,
        "last_run_status": None,
        "next_run_at": calculate_next_run(schedule.frequency.value, schedule.schedule_time, schedule.schedule_day),
        "created_at": datetime.utcnow(),
        "created_by": user.get("sub", "unknown"),
    }

    SCHEDULED_SCANS.append(schedule_dict)
    SCHEDULE_ID_COUNTER += 1

    return schedule_dict


@app.get("/schedules", response_model=List[ScheduledScanResponse])
async def list_schedules(user: dict = Depends(verify_token), db=Depends(get_db)):
    """List all scheduled scans"""
    return SCHEDULED_SCANS


@app.get("/schedules/{schedule_id}", response_model=ScheduledScanResponse)
async def get_schedule(schedule_id: int, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Get a specific scheduled scan"""
    for schedule in SCHEDULED_SCANS:
        if schedule["id"] == schedule_id:
            return schedule
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.patch("/schedules/{schedule_id}", response_model=ScheduledScanResponse)
async def update_schedule(
    schedule_id: int, update: ScheduledScanUpdate, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Update a scheduled scan"""
    for schedule in SCHEDULED_SCANS:
        if schedule["id"] == schedule_id:
            # Update fields
            for field, value in update.dict(exclude_unset=True).items():
                if value is not None:
                    schedule[field] = value

            # Recalculate next run if schedule changed
            if update.frequency or update.schedule_time or update.schedule_day is not None:
                schedule["next_run_at"] = calculate_next_run(
                    schedule["frequency"], schedule["schedule_time"], schedule["schedule_day"]
                )

            return schedule
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Delete a scheduled scan"""
    global SCHEDULED_SCANS
    for i, schedule in enumerate(SCHEDULED_SCANS):
        if schedule["id"] == schedule_id:
            SCHEDULED_SCANS.pop(i)
            return {"message": "Schedule deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.post("/schedules/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: int, background_tasks: BackgroundTasks, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Manually trigger a scheduled scan"""
    for schedule in SCHEDULED_SCANS:
        if schedule["id"] == schedule_id:
            background_tasks.add_task(execute_scheduled_scan, schedule, user.get("sub"))
            return {"message": "Scan triggered"}
    raise HTTPException(status_code=404, detail="Schedule not found")


def calculate_next_run(frequency: str, time_str: str, day: Optional[int] = None) -> datetime:
    """Calculate the next run time for a schedule"""
    from datetime import timedelta

    now = datetime.utcnow()
    hour, minute = map(int, time_str.split(":"))

    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if frequency == "once":
        if next_run <= now:
            next_run += timedelta(days=1)
    elif frequency == "daily":
        if next_run <= now:
            next_run += timedelta(days=1)
    elif frequency == "weekly":
        days_ahead = day - now.weekday() if day is not None else 0
        if days_ahead <= 0:
            days_ahead += 7
        next_run += timedelta(days=days_ahead)
    elif frequency == "monthly":
        # Simplified: run on the first of next month
        if now.day > 1 or (now.day == 1 and next_run <= now):
            next_run = next_run.replace(month=now.month + 1 if now.month < 12 else 1)
            if next_run.month == 1:
                next_run = next_run.replace(year=next_run.year + 1)

    return next_run


async def execute_scheduled_scan(schedule: dict, user_id: str):
    """Execute a scheduled scan"""
    from database.crud import create_scan, update_scan_status

    db = SessionLocal()
    try:
        # Update last run
        schedule["last_run_at"] = datetime.utcnow()
        schedule["last_run_status"] = "running"

        # Create scan
        scan_data = type(
            "obj",
            (object,),
            {
                "name": schedule["name"],
                "target": schedule["target"],
                "scan_type": schedule["scan_type"],
                "config": {},
                "user_id": user_id,
            },
        )

        db_scan = create_scan(db, scan_data)

        # Run scan
        update_scan_status(db, db_scan.id, "running")

        # TODO: Actually run the scan (simplified for now)
        import asyncio

        await asyncio.sleep(5)  # Simulate scan

        update_scan_status(db, db_scan.id, "completed")
        schedule["last_run_status"] = "completed"

        # Calculate next run
        schedule["next_run_at"] = calculate_next_run(
            schedule["frequency"], schedule["schedule_time"], schedule.get("schedule_day")
        )

        # Send notifications
        if schedule.get("notification_email"):
            await send_email_notification(schedule, db_scan.id)
        if schedule.get("notification_slack"):
            await send_slack_notification(schedule, db_scan.id)

    except Exception as e:
        schedule["last_run_status"] = "failed"
        logger.error(f"Scheduled scan error: {e}")
    finally:
        db.close()


async def send_email_notification(schedule: dict, scan_id: int):
    """Send email notification"""
    logger.info(f"Would send email to {schedule['notification_email']} for scan {scan_id}")


async def send_slack_notification(schedule: dict, scan_id: int):
    """Send Slack notification"""
    logger.info(f"Would send Slack notification for scan {scan_id}")


# ============================================================================
# STATS
# ============================================================================


@app.get("/stats/overview")
async def get_stats_overview(user: dict = Depends(verify_token), db=Depends(get_db)):
    """Get dashboard statistics overview"""
    from sqlalchemy import func

    from database.models import Finding, Scan

    # Basic counts
    total_scans = db.query(Scan).count()
    completed_scans = db.query(Scan).filter(Scan.status == "completed").count()
    running_scans = db.query(Scan).filter(Scan.status == "running").count()

    # Findings counts
    total_findings = db.query(Finding).count()

    # Severity distribution
    severity_counts = db.query(Finding.severity, func.count(Finding.id)).group_by(Finding.severity).all()

    severity_distribution = [
        {"name": sev.capitalize(), "value": count, "color": get_severity_color(sev)} for sev, count in severity_counts
    ]

    # Fill missing severities
    all_severities = ["critical", "high", "medium", "low", "info"]
    existing = {s["name"].lower(): s for s in severity_distribution}
    for sev in all_severities:
        if sev not in existing:
            severity_distribution.append({"name": sev.capitalize(), "value": 0, "color": get_severity_color(sev)})

    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "running_scans": running_scans,
        "total_findings": total_findings,
        "critical_findings": sum(1 for s in severity_counts if s[0] == "critical"),
        "severity_distribution": severity_distribution,
        "trends": [],  # TODO: Implement trends
        "tool_usage": [],  # TODO: Implement tool usage
    }


def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22c55e", "info": "#3b82f6"}
    return colors.get(severity.lower(), "#6b7280")


@app.get("/stats/trends")
async def get_stats_trends(days: int = 30, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Get scan trends for the last N days"""
    # TODO: Implement trend calculation
    return []


@app.get("/stats/severity")
async def get_severity_stats(user: dict = Depends(verify_token), db=Depends(get_db)):
    """Get findings by severity"""
    from sqlalchemy import func

    from database.models import Finding

    severity_counts = db.query(Finding.severity, func.count(Finding.id)).group_by(Finding.severity).all()

    return [{"severity": sev, "count": count} for sev, count in severity_counts]


@app.get("/stats/tools")
async def get_tool_usage(user: dict = Depends(verify_token), db=Depends(get_db)):
    """Get tool usage statistics"""
    # TODO: Implement tool usage tracking
    return []


# ============================================================================
# NOTIFICATIONS (SLACK)
# ============================================================================


def _validate_slack_webhook_url(webhook_url: str) -> str:
    """
    Validate that the provided webhook URL is a Slack webhook URL.

    This prevents server-side request forgery by restricting outbound
    requests to the official Slack webhook host.
    """
    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url is required")

    parsed = urlparse(webhook_url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid webhook URL scheme")

    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid webhook URL")

    # Restrict to official Slack incoming webhook host
    # See: https://api.slack.com/messaging/webhooks
    host = parsed.hostname or ""
    if host != "hooks.slack.com":
        raise HTTPException(status_code=400, detail="Webhook host is not allowed")

    return webhook_url


@app.post("/notifications/slack/test")
async def test_slack_notification(webhook_url: str, user: dict = Depends(verify_token)):
    """Test Slack webhook configuration"""
    try:
        from notifications.slack import SlackNotifier

        safe_webhook_url = _validate_slack_webhook_url(webhook_url)
        notifier = SlackNotifier(safe_webhook_url)
        success = notifier.send_message(
            f"Test notification from Zen AI Pentest\nUser: {user.get('sub', 'unknown')}\nTime: {datetime.utcnow().isoformat()}"
        )
        if success:
            return {"status": "success", "message": "Test notification sent"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send Slack notification")
    except HTTPException:
        # Re-raise validation errors without wrapping in 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/slack/scan-complete")
async def notify_slack_scan_complete(scan_id: int, webhook_url: str, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Send Slack notification for scan completion"""
    try:
        from database.models import Finding, Scan
        from notifications.slack import SlackNotifier

        # Get scan details
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        # Validate webhook URL to prevent SSRF
        safe_webhook_url = _validate_slack_webhook_url(webhook_url)

        # Count findings
        findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()
        findings_count = len(findings)
        critical_count = sum(1 for f in findings if f.severity == "critical")

        # Send notification
        notifier = SlackNotifier(safe_webhook_url)
        success = notifier.send_scan_completed(
            scan_id=scan_id, target=scan.target, findings_count=findings_count, critical_count=critical_count
        )

        if success:
            return {"status": "success", "message": "Notification sent"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send notification")
    except HTTPException:
        # Re-raise validation errors without wrapping in 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Store Slack webhook in memory (in production: use database)
SLACK_CONFIG = {"webhook_url": None, "enabled": False}


@app.get("/settings/slack")
async def get_slack_settings(user: dict = Depends(verify_token)):
    """Get Slack configuration (without sensitive data)"""
    return {"enabled": SLACK_CONFIG["enabled"], "configured": SLACK_CONFIG["webhook_url"] is not None}


@app.post("/settings/slack")
async def update_slack_settings(webhook_url: str, enabled: bool = True, user: dict = Depends(verify_token)):
    """Update Slack configuration"""
    global SLACK_CONFIG
    SLACK_CONFIG["webhook_url"] = webhook_url
    SLACK_CONFIG["enabled"] = enabled
    return {"status": "success", "message": "Slack settings updated"}


# ============================================================================
# JIRA INTEGRATION
# ============================================================================


@app.get("/settings/jira")
async def get_jira_settings(user: dict = Depends(verify_token)):
    """Get JIRA configuration (without sensitive data)"""
    from integrations.jira_client import JIRA_CONFIG

    return {
        "enabled": JIRA_CONFIG["enabled"],
        "configured": JIRA_CONFIG["base_url"] is not None,
        "base_url": JIRA_CONFIG["base_url"],
    }


@app.post("/settings/jira")
async def update_jira_settings(
    base_url: str, username: str, api_token: str, enabled: bool = True, user: dict = Depends(verify_token)
):
    """Update JIRA configuration"""
    from integrations.jira_client import JIRA_CONFIG

    JIRA_CONFIG["base_url"] = base_url
    JIRA_CONFIG["username"] = username
    JIRA_CONFIG["api_token"] = api_token
    JIRA_CONFIG["enabled"] = enabled
    return {"status": "success", "message": "JIRA settings updated"}


@app.post("/settings/jira/test")
async def test_jira_connection(user: dict = Depends(verify_token)):
    """Test JIRA connection"""
    from integrations.jira_client import get_jira_client

    client = get_jira_client()
    if not client:
        raise HTTPException(status_code=400, detail="JIRA not configured")

    if client.test_connection():
        return {"status": "success", "message": "Connection successful"}
    else:
        raise HTTPException(status_code=400, detail="Connection failed")


@app.get("/settings/jira/projects")
async def get_jira_projects(user: dict = Depends(verify_token)):
    """Get available JIRA projects"""
    from integrations.jira_client import get_jira_client

    client = get_jira_client()
    if not client:
        raise HTTPException(status_code=400, detail="JIRA not configured")

    projects = client.get_projects()
    return [{"key": p["key"], "name": p["name"]} for p in projects]


@app.post("/integrations/jira/create-ticket")
async def create_jira_ticket(finding_id: int, project_key: str, user: dict = Depends(verify_token), db=Depends(get_db)):
    """Create JIRA ticket from finding"""
    from database.models import Finding
    from integrations.jira_client import get_jira_client

    client = get_jira_client()
    if not client:
        raise HTTPException(status_code=400, detail="JIRA not configured")

    # Get finding
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Create ticket
    result = client.create_finding_ticket(
        project_key=project_key,
        finding={
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity,
            "target": finding.target,
            "tool": finding.tool,
        },
    )

    if result:
        return {
            "status": "success",
            "ticket_key": result.get("key"),
            "ticket_url": f"{client.base_url}/browse/{result.get('key')}",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to create ticket")


# ============================================================================
# API v1.0 (Q1 2026)
# ============================================================================

# Import v1 routers
try:
    from api.v1.siem import router as siem_v1_router

    app.include_router(siem_v1_router, prefix="/api/v1/siem", tags=["SIEM v1.0"])
    logger.info("API v1.0 SIEM endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load SIEM v1.0 endpoints: {e}")

try:
    from api.v1.dashboard import router as dashboard_v1_router

    app.include_router(dashboard_v1_router, prefix="/api/v1", tags=["Dashboard v1.0"])
    logger.info("API v1.0 Dashboard endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load Dashboard v1.0 endpoints: {e}")

try:
    from api.v1.scans_extended import router as scans_v1_router

    app.include_router(scans_v1_router, prefix="/api/v1/scans-extended", tags=["Scans v1.0"])
    logger.info("API v1.0 Scans endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load Scans v1.0 endpoints: {e}")

# Subdomain scanning routes
try:
    from api.routes.subdomain import router as subdomain_router

    app.include_router(subdomain_router, prefix="/api/v1/subdomain", tags=["Subdomain"])
    logger.info("Subdomain scanning endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load Subdomain endpoints: {e}")

# Agent Communication v2 routes
if AGENTS_V2_AVAILABLE:
    try:
        app.include_router(agents_v2_router, prefix="/api/v2")
        logger.info("✅ Agent Communication v2 endpoints loaded")
    except Exception as e:
        logger.warning(f"Could not load Agent v2 endpoints: {e}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
