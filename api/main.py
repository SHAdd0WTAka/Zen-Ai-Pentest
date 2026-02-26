"""
Zen-AI-Pentest API Server

FastAPI-basiertes Backend für das Pentesting-Framework.
"""

import os
import sys
from pathlib import Path

# Windows Asyncio Fix (must be first)
if sys.platform == "win32":
    import warnings

    warnings.filterwarnings(
        "ignore", message="unclosed transport", category=ResourceWarning
    )

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
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
        AuthMiddleware,
        JWTHandler,
        PasswordHasher,
        RBACManager,
        UserManager,
    )
    from database.auth_models import init_auth_db

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
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
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
            from database.auth_models import (
                SessionLocal,
                UserRole,
                create_user,
                get_user_by_username,
            )

            db = SessionLocal()
            try:
                admin = get_user_by_username(db, "admin")
                if not admin:
                    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
                    create_user(
                        db,
                        username="admin",
                        email="admin@zen-pentest.local",
                        hashed_password=_password_hasher.hash_password(
                            admin_pass
                        ),
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


# Custom dark theme CSS for Swagger UI
SWAGGER_UI_DARK_CSS = """
    /* Zen Dark Theme for Swagger UI */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #14141f;
        --bg-card: #1a1a2e;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --accent: #06b6d4;
        --accent-hover: #0891b2;
        --border: #27273a;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
    }
    
    body { 
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    .swagger-ui {
        background: var(--bg-primary);
        color: var(--text-primary);
        filter: invert(1) hue-rotate(180deg);
    }
    
    .swagger-ui .topbar {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        border-bottom: 1px solid var(--border);
    }
    
    .swagger-ui .information-container {
        background: var(--bg-secondary) !important;
    }
    
    .swagger-ui .scheme-container {
        background: var(--bg-card) !important;
        border: 1px solid var(--border);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .swagger-ui .opblock {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .swagger-ui .opblock-tag {
        color: var(--text-primary) !important;
        border-bottom: 1px solid var(--border);
    }
    
    .swagger-ui .opblock .opblock-summary-method {
        background: var(--accent) !important;
        color: #000 !important;
        font-weight: 600;
    }
    
    .swagger-ui .opblock.opblock-get { border-color: var(--accent); }
    .swagger-ui .opblock.opblock-post { border-color: var(--success); }
    .swagger-ui .opblock.opblock-put { border-color: var(--warning); }
    .swagger-ui .opblock.opblock-delete { border-color: var(--error); }
    
    .swagger-ui .btn {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }
    
    .swagger-ui .btn.authorize {
        background: var(--success) !important;
        color: #000 !important;
    }
    
    .swagger-ui input[type=text],
    .swagger-ui textarea,
    .swagger-ui select {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }
    
    .swagger-ui .model-box {
        background: var(--bg-secondary) !important;
    }
    
    .swagger-ui table thead tr th {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border-bottom: 2px solid var(--border);
    }
    
    .swagger-ui .responses-inner h4,
    .swagger-ui .responses-inner h5 {
        color: var(--text-primary) !important;
    }
    
    .swagger-ui .response-col_status {
        color: var(--text-primary) !important;
    }
    
    /* Toggle Switch for Dark/Light Mode */
    .theme-toggle {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 30px;
        padding: 8px 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--text-primary);
        font-size: 14px;
        transition: all 0.3s ease;
    }
    
    .theme-toggle:hover {
        background: var(--accent);
        color: #000;
    }
"""

# ReDoc Dark Theme
REDOC_DARK_CSS = """
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #14141f;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --accent: #06b6d4;
    }
    
    body {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    .menu-content {
        background: var(--bg-secondary) !important;
        border-right: 1px solid #27273a;
    }
    
    .api-content {
        background: var(--bg-primary) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    
    p, span, div {
        color: var(--text-secondary) !important;
    }
    
    code {
        background: #1e1e2e !important;
        color: var(--accent) !important;
    }
    
    pre {
        background: #1e1e2e !important;
        border: 1px solid #27273a !important;
    }
"""

app = FastAPI(
    title="Zen-AI-Pentest API",
    description="""Professional Pentesting Framework API
    
## 🌓 API Documentation Dark Mode

Switch between **Swagger UI** (`/docs`) and **ReDoc** (`/redoc`) - both support dark themes.
    """,
    version="2.2.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs - we'll create custom
    redoc_url=None,  # Disable default redoc - we'll create custom
)

# =============================================================================
# CORS Configuration
# =============================================================================
# Load allowed origins from environment variable
# Format: comma-separated list of origins
# Example: CORS_ORIGINS=https://domain.com,https://app.domain.com
cors_origins_str = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"
)
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

# =============================================================================
# CUSTOM API DOCUMENTATION WITH DARK MODE
# =============================================================================
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse


def get_zen_swagger_html() -> str:
    """Generate custom Swagger UI HTML with dark theme"""
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zen-AI-Pentest API - Swagger UI</title>
    <link rel="shortcut icon" href="/favicon.ico">
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
    <style>
        /* Zen Dark Theme Base */
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #14141f;
            --bg-card: #1a1a2e;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --accent: #06b6d4;
            --accent-hover: #0891b2;
            --border: #27273a;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }}
        
        * {{
            scrollbar-width: thin;
            scrollbar-color: #27273a #0a0a0f;
        }}
        
        body {{
            background: var(--bg-primary) !important;
            margin: 0;
            padding: 0;
        }}
        
        /* Swagger UI Dark Overrides */
        .swagger-ui {{
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .topbar {{
            background: linear-gradient(135deg, #1a1a2e 0%, #0f172a 100%) !important;
            border-bottom: 1px solid var(--border);
            padding: 15px 0;
        }}
        
        .swagger-ui .topbar .download-url-wrapper input[type=text] {{
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 6px;
            padding: 8px 12px;
        }}
        
        .swagger-ui .topbar .download-url-wrapper .download-url-button {{
            background: var(--accent) !important;
            color: #000 !important;
            font-weight: 600;
            border-radius: 6px;
        }}
        
        /* Info Section */
        .swagger-ui .information-container {{
            background: var(--bg-secondary) !important;
            padding: 30px 0;
        }}
        
        .swagger-ui .info {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        .swagger-ui .info .title {{
            color: var(--accent) !important;
            font-size: 2.8em;
            font-weight: 700;
            text-shadow: 0 0 40px rgba(6,182,212,0.3);
            margin-bottom: 10px;
        }}
        
        .swagger-ui .info .version {{
            background: var(--accent) !important;
            color: #000 !important;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 600;
            vertical-align: middle;
        }}
        
        .swagger-ui .info .description {{
            color: var(--text-secondary) !important;
            font-size: 1.1em;
            line-height: 1.6;
        }}
        
        .swagger-ui .info .description h2 {{
            color: var(--text-primary) !important;
            margin-top: 20px;
        }}
        
        /* Scheme Container */
        .swagger-ui .scheme-container {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            margin: 20px;
            padding: 20px;
        }}
        
        .swagger-ui .schemes-title {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .scheme-container .schemes > label {{
            color: var(--text-secondary) !important;
        }}
        
        /* Operation Blocks */
        .swagger-ui .opblock-tag {{
            font-size: 1.3em;
            color: var(--text-primary) !important;
            border-bottom: 2px solid var(--border);
            padding: 20px 0;
            margin: 0 20px;
        }}
        
        .swagger-ui .opblock-tag small {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .opblock {{
            background: var(--bg-card) !important;
            border-radius: 12px;
            margin: 15px 20px;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        .swagger-ui .opblock-summary {{
            padding: 15px 20px;
        }}
        
        .swagger-ui .opblock .opblock-summary-method {{
            border-radius: 6px;
            font-weight: 600;
            min-width: 70px;
            text-align: center;
        }}
        
        .swagger-ui .opblock.opblock-get .opblock-summary-method {{
            background: var(--accent) !important;
            color: #000 !important;
        }}
        
        .swagger-ui .opblock.opblock-post .opblock-summary-method {{
            background: var(--success) !important;
            color: #000 !important;
        }}
        
        .swagger-ui .opblock.opblock-put .opblock-summary-method {{
            background: var(--warning) !important;
            color: #000 !important;
        }}
        
        .swagger-ui .opblock.opblock-delete .opblock-summary-method {{
            background: var(--error) !important;
            color: #fff !important;
        }}
        
        .swagger-ui .opblock .opblock-summary-path {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .opblock .opblock-summary-description {{
            color: var(--text-secondary) !important;
        }}
        
        /* Parameters */
        .swagger-ui .parameter__name {{
            color: var(--accent) !important;
            font-weight: 600;
        }}
        
        .swagger-ui .parameter__type {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .parameter__in {{
            color: var(--text-secondary) !important;
            font-style: italic;
        }}
        
        /* Tables */
        .swagger-ui table thead tr th {{
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            border-bottom: 2px solid var(--border);
            padding: 12px;
        }}
        
        .swagger-ui table tbody tr td {{
            background: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border-bottom: 1px solid var(--border);
            padding: 12px;
        }}
        
        /* Models */
        .swagger-ui .model-box {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 15px;
        }}
        
        .swagger-ui .model-title {{
            color: var(--accent) !important;
        }}
        
        .swagger-ui .prop-type {{
            color: var(--success) !important;
        }}
        
        /* Response Section */
        .swagger-ui .responses-inner h4,
        .swagger-ui .responses-inner h5 {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .response-col_status {{
            color: var(--text-primary) !important;
            font-weight: 600;
        }}
        
        .swagger-ui .response-col_description {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .responses-table td.response-col_status {{
            color: var(--text-primary) !important;
        }}
        
        /* Input Fields */
        .swagger-ui input[type=text],
        .swagger-ui input[type=password],
        .swagger-ui input[type=email],
        .swagger-ui input[type=url],
        .swagger-ui input[type=number],
        .swagger-ui textarea,
        .swagger-ui select {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
            border-radius: 6px;
            padding: 8px 12px;
        }}
        
        .swagger-ui input:focus,
        .swagger-ui textarea:focus,
        .swagger-ui select:focus {{
            border-color: var(--accent) !important;
            outline: none;
            box-shadow: 0 0 0 3px rgba(6,182,212,0.1);
        }}
        
        .swagger-ui .response-content-type {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
        }}
        
        /* Buttons */
        .swagger-ui .btn {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
            border-radius: 6px;
            padding: 8px 16px;
            transition: all 0.2s ease;
        }}
        
        .swagger-ui .btn:hover {{
            background: var(--accent) !important;
            color: #000 !important;
            border-color: var(--accent) !important;
        }}
        
        .swagger-ui .btn.authorize {{
            background: var(--success) !important;
            color: #000 !important;
            border-color: var(--success) !important;
        }}
        
        .swagger-ui .btn.execute {{
            background: var(--accent) !important;
            color: #000 !important;
            border-color: var(--accent) !important;
        }}
        
        /* Auth */
        .swagger-ui .auth-container {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px;
            padding: 20px;
        }}
        
        .swagger-ui .auth-container .errors {{
            background: rgba(239,68,68,0.1) !important;
            border: 1px solid var(--error) !important;
            border-radius: 6px;
        }}
        
        /* Dialogs */
        .swagger-ui .dialog-ux .backdrop-ux {{
            background: rgba(0,0,0,0.8) !important;
        }}
        
        .swagger-ui .dialog-ux .modal-ux {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        
        .swagger-ui .dialog-ux .modal-ux-content h4 {{
            color: var(--text-primary) !important;
        }}
        
        /* Code */
        .swagger-ui code {{
            background: var(--bg-secondary) !important;
            color: var(--accent) !important;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        
        .swagger-ui pre {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 15px;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-primary);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--accent);
        }}
        
        /* Links */
        .swagger-ui a {{
            color: var(--accent) !important;
            transition: color 0.2s ease;
        }}
        
        .swagger-ui a:hover {{
            color: var(--accent-hover) !important;
        }}
        
        /* Highlight */
        .swagger-ui .highlight-code {{
            background: var(--bg-secondary) !important;
        }}
        
        /* Loading */
        .swagger-ui .loading-container {{
            background: var(--bg-primary) !important;
        }}
        
        .swagger-ui .loading-container .loading::after {{
            border-color: var(--accent) !important;
        }}
        
        /* Error */
        .swagger-ui .errors-wrapper {{
            background: rgba(239,68,68,0.1) !important;
            border: 1px solid var(--error) !important;
            border-radius: 8px;
        }}
        
        .swagger-ui .errors-wrapper .errors h4 {{
            color: var(--error) !important;
        }}
        
        /* Curl Command */
        .swagger-ui .curl {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 15px;
        }}
        
        .swagger-ui .curl .curl-command {{
            color: var(--text-primary) !important;
        }}
        
        /* Try-it-out section */
        .swagger-ui .try-out {{
            margin-top: 10px;
        }}
        
        .swagger-ui .try-out__btn {{
            background: var(--accent) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: 600;
        }}
        
        /* Copy button */
        .swagger-ui .copy-to-clipboard {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px;
        }}
        
        .swagger-ui .copy-to-clipboard:hover {{
            background: var(--accent) !important;
        }}
        
        /* Filter */
        .swagger-ui .filter .filter-input {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
            border-radius: 6px;
            padding: 8px 12px;
        }}
        
        /* Servers */
        .swagger-ui .servers > label {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .servers {{
            background: var(--bg-secondary) !important;
            border-radius: 8px;
            padding: 15px;
        }}
        
        /* SCHEMAS SECTION - Fix white backgrounds */
        .swagger-ui section.models {{
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px;
            margin: 20px;
        }}
        
        .swagger-ui section.models.is-open {{
            background: var(--bg-card) !important;
        }}
        
        .swagger-ui section.models h4 {{
            color: var(--text-primary) !important;
            background: var(--bg-secondary) !important;
            padding: 15px 20px;
            margin: 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .swagger-ui section.models h4 span {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui section.models .model-container {{
            background: var(--bg-card) !important;
            border-bottom: 1px solid var(--border) !important;
        }}
        
        .swagger-ui .model-box {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 15px;
        }}
        
        .swagger-ui .model {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .model .property {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .model .property-name {{
            color: var(--accent) !important;
            font-weight: 600;
        }}
        
        .swagger-ui .model .property-type {{
            color: var(--success) !important;
        }}
        
        .swagger-ui .model .property.primitive {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .model .model-box .model-box {{
            background: var(--bg-card) !important;
        }}
        
        .swagger-ui .model-title {{
            color: var(--text-primary) !important;
            font-weight: 600;
        }}
        
        .swagger-ui .model-title__text {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .model-toggle {{
            color: var(--accent) !important;
            background: var(--bg-secondary) !important;
            border-radius: 4px;
            padding: 2px 6px;
        }}
        
        .swagger-ui .model-toggle:hover {{
            background: var(--accent) !important;
            color: #000 !important;
        }}
        
        .swagger-ui .model-toggle.collapsed {{
            color: var(--accent) !important;
        }}
        
        .swagger-ui .model-toggle::after {{
            background: var(--accent) !important;
        }}
        
        .swagger-ui .brace-open, 
        .swagger-ui .brace-close {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .inner-object {{
            background: var(--bg-card) !important;
            border-left: 2px solid var(--border) !important;
            padding-left: 15px;
            margin-left: 10px;
        }}
        
        .swagger-ui .prop-type {{
            color: var(--success) !important;
        }}
        
        .swagger-ui .prop-format {{
            color: var(--text-secondary) !important;
        }}
        
        .swagger-ui .prop-enum {{
            color: var(--warning) !important;
        }}
        
        .swagger-ui .prop-readonly {{
            color: var(--error) !important;
            font-weight: 600;
        }}
        
        .swagger-ui .prop-keyword {{
            color: var(--accent) !important;
        }}
        
        /* Model collapse/expand button */
        .swagger-ui .model-box-control {{
            color: var(--accent) !important;
        }}
        
        /* Array items styling */
        .swagger-ui .model-box .items {{
            color: var(--text-secondary) !important;
        }}
        
        /* Table in models */
        .swagger-ui .model-box table {{
            background: transparent !important;
        }}
        
        .swagger-ui .model-box table tr {{
            background: transparent !important;
            border-bottom: 1px solid var(--border) !important;
        }}
        
        .swagger-ui .model-box table tr:last-child {{
            border-bottom: none !important;
        }}
        
        .swagger-ui .model-box table td {{
            background: transparent !important;
            color: var(--text-primary) !important;
            border: none !important;
        }}
        
        .swagger-ui .model-box table .header-row {{
            background: var(--bg-secondary) !important;
        }}
        
        /* Additional schema containers */
        .swagger-ui .json-schema-2020-12 {{
            background: var(--bg-secondary) !important;
        }}
        
        .swagger-ui .json-schema-2020-12-property {{
            color: var(--text-primary) !important;
        }}
        
        .swagger-ui .json-schema-2020-12__title {{
            color: var(--text-primary) !important;
        }}
        
        /* Schema accordion */
        .swagger-ui .model-deprecated-warning {{
            background: rgba(239,68,68,0.1) !important;
            border: 1px solid var(--error) !important;
            color: var(--error) !important;
            border-radius: 6px;
            padding: 10px;
        }}
        
        /* Content type selection */
        .swagger-ui .content-type {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
        }}
        
        /* Response samples */
        .swagger-ui .example {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
        }}
        
        .swagger-ui .example .example__section-header {{
            color: var(--text-primary) !important;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }}
        
        /* Code samples */
        .swagger-ui .microlight {{
            color: var(--text-primary) !important;
        }}
        
        /* Execute button area */
        .swagger-ui .execute-wrapper {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px;
            padding: 15px;
        }}
        
        /* Clear button */
        .swagger-ui .btn-clear {{
            background: transparent !important;
            border: 1px solid var(--error) !important;
            color: var(--error) !important;
        }}
        
        .swagger-ui .btn-clear:hover {{
            background: var(--error) !important;
            color: #fff !important;
        }}
        
        /* Schema Buttons (Expand/Collapse) */
        .swagger-ui .model-box-control {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-primary) !important;
            border-radius: 6px;
            padding: 4px 12px !important;
            font-size: 0.85em;
            font-weight: 500;
            transition: all 0.2s ease;
        }}
        
        .swagger-ui .model-box-control:hover {{
            background: var(--accent) !important;
            color: #000 !important;
            border-color: var(--accent) !important;
        }}
        
        .swagger-ui .model-box-control:focus {{
            outline: none;
            box-shadow: 0 0 0 2px rgba(6,182,212,0.3);
        }}
        
        /* Section controls (Expand all / Collapse all) */
        .swagger-ui section.models .model-box-control {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-secondary) !important;
            margin-left: 10px;
        }}
        
        .swagger-ui section.models .model-box-control:hover {{
            background: var(--accent) !important;
            color: #000 !important;
        }}
        
        /* Model control arrows */
        .swagger-ui .model-box-control .pointer {{
            color: var(--accent) !important;
        }}
        
        /* Schema header buttons container */
        .swagger-ui section.models .models-control {{
            display: flex;
            gap: 10px;
        }}
        
        /* Theme Toggle Button */
        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 50px;
            padding: 10px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-primary);
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        
        .theme-toggle:hover {{
            background: var(--accent);
            color: #000;
            border-color: var(--accent);
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(6,182,212,0.3);
        }}
        
        .theme-toggle:active {{
            transform: translateY(0);
        }}
        
        .theme-toggle .icon {{
            font-size: 16px;
        }}
        
        /* Light Theme Variables */
        body[data-theme="light"] {{
            --bg-primary: #f8fafc;
            --bg-secondary: #f1f5f9;
            --bg-card: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
        }}
        
        body[data-theme="light"] .swagger-ui {{
            background: #f8fafc !important;
        }}
        
        body[data-theme="light"] .swagger-ui .topbar {{
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%) !important;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        body[data-theme="light"] .swagger-ui .info {{
            background: linear-gradient(135deg, rgba(6,182,212,0.05) 0%, transparent 100%);
            border: 1px solid rgba(6,182,212,0.15);
        }}
        
        body[data-theme="light"] .swagger-ui .info .title {{
            color: #0891b2 !important;
            text-shadow: none;
        }}
        
        body[data-theme="light"] .swagger-ui .opblock {{
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        body[data-theme="light"] .theme-toggle {{
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <!-- Theme Toggle Button -->
    <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()">
        <span class="icon" id="themeIcon">🌙</span>
        <span id="themeText">Dark</span>
    </button>
    
    <div id="swagger-ui"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        // Theme Management
        const THEME_KEY = 'zen-api-theme';
        
        function getPreferredTheme() {{
            const savedTheme = localStorage.getItem(THEME_KEY);
            if (savedTheme) return savedTheme;
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }}
        
        function applyTheme(theme) {{
            document.body.setAttribute('data-theme', theme);
            const icon = document.getElementById('themeIcon');
            const text = document.getElementById('themeText');
            
            if (theme === 'dark') {{
                icon.textContent = '☀️';
                text.textContent = 'Light';
            }} else {{
                icon.textContent = '🌙';
                text.textContent = 'Dark';
            }}
        }}
        
        function toggleTheme() {{
            const currentTheme = document.body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            localStorage.setItem(THEME_KEY, newTheme);
            applyTheme(newTheme);
        }}
        
        // Initialize theme
        document.addEventListener('DOMContentLoaded', function() {{
            const theme = getPreferredTheme();
            applyTheme(theme);
        }});
        
        // Initialize Swagger UI
        const ui = SwaggerUIBundle({{
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "BaseLayout",
            validatorUrl: null,
            tryItOutEnabled: true,
            supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
        }});
    </script>
</body>
</html>'''
    return html_template


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    """Swagger UI with Dark Mode support"""
    return HTMLResponse(content=get_zen_swagger_html())


def get_zen_redoc_html() -> str:
    """Generate custom ReDoc HTML with dark theme"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zen-AI-Pentest API - ReDoc</title>
    <link rel="shortcut icon" href="/favicon.ico">
    <meta name="description" content="Zen-AI-Pentest API Documentation">
    <style>
        /* Zen Dark Theme for ReDoc */
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #14141f;
            --bg-card: #1a1a2e;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --accent: #06b6d4;
            --accent-hover: #0891b2;
            --border: #27273a;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        
        * {
            scrollbar-width: thin;
            scrollbar-color: #27273a #0a0a0f;
        }
        
        body {
            background: var(--bg-primary) !important;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }
        
        /* Menu / Sidebar */
        .menu-content {
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border) !important;
        }
        
        .menu-item {
            color: var(--text-secondary) !important;
            transition: all 0.2s ease;
        }
        
        .menu-item:hover {
            color: var(--text-primary) !important;
            background: rgba(6,182,212,0.1) !important;
        }
        
        .menu-item.active {
            color: var(--accent) !important;
            background: rgba(6,182,212,0.15) !important;
            border-left: 3px solid var(--accent);
        }
        
        .menu-item-title {
            font-weight: 500;
        }
        
        /* API Info Header */
        .api-info {
            background: linear-gradient(135deg, rgba(6,182,212,0.1) 0%, transparent 100%) !important;
            padding: 40px !important;
            border-bottom: 1px solid var(--border) !important;
        }
        
        .api-info h1 {
            color: var(--accent) !important;
            font-size: 2.8em !important;
            font-weight: 700 !important;
            text-shadow: 0 0 40px rgba(6,182,212,0.3);
            margin-bottom: 10px !important;
        }
        
        .api-info p {
            color: var(--text-secondary) !important;
            font-size: 1.1em;
            line-height: 1.6;
        }
        
        .api-info a {
            color: var(--accent) !important;
        }
        
        /* Content Area */
        .api-content {
            background: var(--bg-primary) !important;
            padding: 40px !important;
        }
        
        /* Section Headers */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
        }
        
        h2 {
            border-bottom: 2px solid var(--border) !important;
            padding-bottom: 15px;
        }
        
        h3 {
            color: var(--accent) !important;
        }
        
        /* Operation Labels */
        .http-verb {
            border-radius: 6px !important;
            font-weight: 600 !important;
            padding: 4px 10px !important;
        }
        
        .http-verb.get {
            background: rgba(6,182,212,0.2) !important;
            color: var(--accent) !important;
            border: 1px solid rgba(6,182,212,0.3) !important;
        }
        
        .http-verb.post {
            background: rgba(16,185,129,0.2) !important;
            color: var(--success) !important;
            border: 1px solid rgba(16,185,129,0.3) !important;
        }
        
        .http-verb.put {
            background: rgba(245,158,11,0.2) !important;
            color: var(--warning) !important;
            border: 1px solid rgba(245,158,11,0.3) !important;
        }
        
        .http-verb.delete {
            background: rgba(239,68,68,0.2) !important;
            color: var(--error) !important;
            border: 1px solid rgba(239,68,68,0.3) !important;
        }
        
        .http-verb.patch {
            background: rgba(139,92,246,0.2) !important;
            color: #8b5cf6 !important;
            border: 1px solid rgba(139,92,246,0.3) !important;
        }
        
        /* Code Blocks */
        code {
            background: var(--bg-secondary) !important;
            color: var(--accent) !important;
            padding: 2px 8px !important;
            border-radius: 4px !important;
            font-family: 'JetBrains Mono', 'Fira Code', Monaco, Consolas, monospace !important;
        }
        
        pre {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            padding: 20px !important;
        }
        
        pre code {
            background: transparent !important;
            color: var(--text-primary) !important;
        }
        
        /* JSON Viewer */
        .redoc-json {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }
        
        .redoc-json .string {
            color: var(--success) !important;
        }
        
        .redoc-json .number {
            color: var(--accent) !important;
        }
        
        .redoc-json .boolean {
            color: var(--warning) !important;
        }
        
        .redoc-json .null {
            color: var(--error) !important;
        }
        
        .redoc-json .key {
            color: var(--text-primary) !important;
        }
        
        /* Schema Tables */
        table {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            overflow: hidden;
        }
        
        table tr {
            border-bottom: 1px solid var(--border) !important;
        }
        
        table th {
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            font-weight: 600;
            padding: 12px !important;
        }
        
        table td {
            color: var(--text-secondary) !important;
            padding: 12px !important;
        }
        
        /* Property Types */
        .property-type {
            color: var(--success) !important;
        }
        
        .property-name {
            color: var(--accent) !important;
        }
        
        /* Required Badge */
        .required {
            color: var(--error) !important;
            font-size: 0.85em;
        }
        
        /* Pattern / Constraints */
        .pattern, .constraints {
            color: var(--text-secondary) !important;
            font-size: 0.9em;
        }
        
        /* Description */
        .property-description {
            color: var(--text-secondary) !important;
        }
        
        /* Default Value */
        .default-value {
            color: var(--warning) !important;
        }
        
        /* Enum Values */
        .enum-value {
            background: var(--bg-secondary) !important;
            color: var(--accent) !important;
            padding: 2px 8px !important;
            border-radius: 4px !important;
            margin: 2px !important;
        }
        
        /* Collapsible Sections */
        .collapsible {
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            background: var(--bg-card) !important;
            margin: 10px 0 !important;
        }
        
        .collapsible-header {
            background: var(--bg-secondary) !important;
            padding: 15px !important;
            border-radius: 8px 8px 0 0 !important;
        }
        
        .collapsible-body {
            padding: 15px !important;
        }
        
        /* Tabs */
        .react-tabs__tab-list {
            border-bottom: 2px solid var(--border) !important;
        }
        
        .react-tabs__tab {
            color: var(--text-secondary) !important;
            padding: 12px 20px !important;
        }
        
        .react-tabs__tab--selected {
            color: var(--accent) !important;
            border-bottom: 2px solid var(--accent) !important;
            background: rgba(6,182,212,0.1) !important;
        }
        
        /* Try It Button */
        .try-it {
            background: var(--accent) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 8px 20px !important;
            font-weight: 600 !important;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .try-it:hover {
            background: var(--accent-hover) !important;
        }
        
        /* Response Samples */
        .samples {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }
        
        .samples-header {
            background: var(--bg-secondary) !important;
            padding: 15px !important;
            border-radius: 8px 8px 0 0 !important;
            color: var(--text-primary) !important;
        }
        
        /* Copy Button */
        .copy-button {
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text-secondary) !important;
            border-radius: 4px !important;
            padding: 4px 8px !important;
        }
        
        .copy-button:hover {
            background: var(--accent) !important;
            color: #000 !important;
        }
        
        /* Links */
        a {
            color: var(--accent) !important;
            text-decoration: none !important;
            transition: color 0.2s ease;
        }
        
        a:hover {
            color: var(--accent-hover) !important;
            text-decoration: underline !important;
        }
        
        /* Loading */
        .loading {
            color: var(--text-secondary) !important;
        }
        
        /* Errors */
        .error {
            background: rgba(239,68,68,0.1) !important;
            border: 1px solid var(--error) !important;
            border-radius: 8px !important;
            color: var(--error) !important;
            padding: 15px !important;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent);
        }
        
        /* Left Sidebar Scrollbar */
        .menu-content::-webkit-scrollbar {
            width: 6px;
        }
        
        /* Version Badge */
        .version {
            background: var(--accent) !important;
            color: #000 !important;
            border-radius: 4px !important;
            padding: 4px 12px !important;
            font-weight: 600 !important;
            font-size: 0.9em !important;
        }
        
        /* Download Button */
        .download-button {
            background: var(--accent) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .download-button:hover {
            background: var(--accent-hover) !important;
        }
        
        /* Search Box */
        .search-box {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            padding: 10px 15px !important;
        }
        
        .search-box::placeholder {
            color: var(--text-secondary) !important;
        }
        
        .search-box:focus {
            border-color: var(--accent) !important;
            outline: none;
        }
        
        /* Security Badge */
        .security-badge {
            background: rgba(16,185,129,0.2) !important;
            color: var(--success) !important;
            border: 1px solid rgba(16,185,129,0.3) !important;
            border-radius: 4px !important;
            padding: 2px 8px !important;
            font-size: 0.85em !important;
        }
        
        /* Callback Badge */
        .callback-badge {
            background: rgba(139,92,246,0.2) !important;
            color: #8b5cf6 !important;
            border: 1px solid rgba(139,92,246,0.3) !important;
            border-radius: 4px !important;
            padding: 2px 8px !important;
            font-size: 0.85em !important;
        }
        
        /* Deprecated */
        .deprecated {
            opacity: 0.6;
        }
        
        .deprecated-badge {
            background: rgba(239,68,68,0.2) !important;
            color: var(--error) !important;
            border: 1px solid rgba(239,68,68,0.3) !important;
            border-radius: 4px !important;
            padding: 2px 8px !important;
            font-size: 0.85em !important;
        }
        
        /* External Docs */
        .external-docs {
            color: var(--text-secondary) !important;
        }
        
        .external-docs a {
            color: var(--accent) !important;
        }
        
        /* Tag Description */
        .tag-description {
            color: var(--text-secondary) !important;
            margin: 10px 0 !important;
        }
    </style>
</head>
<body>
    <redoc spec-url="/openapi.json"></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"></script>
</body>
</html>'''


@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html() -> HTMLResponse:
    """ReDoc with Dark Mode support"""
    return HTMLResponse(content=get_zen_redoc_html())


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to docs"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Custom Zen favicon"""
    from fastapi.responses import Response
    
    # Zen-themed SVG favicon (cyan shield)
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="32" height="32">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#06b6d4;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#0891b2;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="100" height="100" rx="20" fill="#0a0a0f"/>
      <path d="M50 10 L80 25 L80 50 C80 70 50 90 50 90 C50 90 20 70 20 50 L20 25 Z" 
            fill="url(#grad)" stroke="#06b6d4" stroke-width="2"/>
      <path d="M35 45 L45 55 L65 35" fill="none" stroke="#0a0a0f" stroke-width="4" stroke-linecap="round"/>
    </svg>'''
    
    return Response(content=svg.encode(), media_type="image/svg+xml")


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

    return hmac.compare_digest(
        username, ADMIN_USERNAME
    ) and hmac.compare_digest(password, ADMIN_PASSWORD)


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
            user = _user_manager.authenticate_user(
                db,
                credentials.username,
                credentials.password,
                client_ip,
                user_agent,
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create session with tokens
            session_data = _user_manager.create_session(
                db, user, client_ip, user_agent
            )

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

    access_token = legacy_create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

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
                from auth.jwt_handler import (
                    TokenExpiredError,
                    TokenInvalidError,
                )

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
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Token refresh not available with legacy auth",
        )

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
async def logout_all_devices(
    request: Request, user: dict = Depends(verify_token)
):
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
                count = _user_manager.revoke_all_user_sessions(
                    db, int(user_id), "logout_all"
                )
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
        db,
        name=scan.name,
        target=scan.target,
        scan_type=scan.scan_type,
        config=scan.config,
        user_id=user.get("sub"),
    )

    # Start scan in background
    background_tasks.add_task(run_scan_task, db_scan.id, scan.dict())

    return db_scan


@app.get("/scans", response_model=List[ScanResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """List all scans with optional filtering"""
    scans = get_scans(db, skip=skip, limit=limit, status=status)
    return scans


@app.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_by_id(
    scan_id: int, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Get scan details by ID"""
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.patch("/scans/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: int,
    update: ScanUpdate,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """Update scan status or config"""
    scan = update_scan_status(db, scan_id, update.status, update.config)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@app.delete("/scans/{scan_id}")
async def delete_scan(
    scan_id: int, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Delete a scan"""
    # Implementation here
    return {"message": "Scan deleted"}


# ============================================================================
# FINDINGS
# ============================================================================


@app.get("/scans/{scan_id}/findings", response_model=List[FindingResponse])
async def get_scan_findings(
    scan_id: int,
    severity: Optional[str] = None,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """Get all findings for a scan"""
    findings = get_findings(db, scan_id, severity)
    return findings


@app.post("/scans/{scan_id}/findings", response_model=FindingResponse)
async def add_finding(
    scan_id: int,
    finding: FindingCreate,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
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
async def update_finding(
    finding_id: int,
    update: dict,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """Update a finding"""
    from database.models import Finding

    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Update allowed fields
    allowed_fields = [
        "title",
        "description",
        "severity",
        "cvss_score",
        "evidence",
        "remediation",
        "verified",
    ]

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
    request: ToolExecuteRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
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
    background_tasks.add_task(
        execute_tool_task,
        db_scan.id,
        request.tool_name,
        request.target,
        request.parameters,
    )

    return ToolExecuteResponse(
        scan_id=db_scan.id,
        status="started",
        message=f"Tool {request.tool_name} execution started",
    )


@app.get("/tools")
async def list_tools(user: dict = Depends(verify_token)):
    """List available tools"""
    from tools import TOOL_REGISTRY

    tools = []
    for name, func in TOOL_REGISTRY.items():
        if func:
            tools.append(
                {
                    "name": name,
                    "description": func.__doc__ or "No description",
                    "category": get_tool_category(name),
                }
            )

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
    report: ReportCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """Generate a report from scan findings"""
    db_report = create_report(
        db,
        scan_id=report.scan_id,
        format=report.format,
        template=report.template,
        user_id=user.get("sub"),
    )

    # Generate in background
    background_tasks.add_task(
        generate_report_task, db_report.id, report.scan_id, report.format
    )

    return db_report


@app.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """List all reports"""
    reports = get_reports(db, skip, limit)
    return reports


@app.get("/reports/{report_id}/download")
async def download_report(
    report_id: int, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Download a generated report"""
    from fastapi.responses import FileResponse

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report.file_path, filename=f"report_{report_id}.{report.format}"
    )


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
        await ws_manager.broadcast_to_scan(
            scan_id,
            {"type": "status", "status": "running", "message": "Scan started"},
        )

        # Run agent
        config = ReActAgentConfig(max_iterations=10)
        agent = ReActAgent(config)

        result = agent.run(
            target=scan_config["target"],
            objective=scan_config.get("objective", "comprehensive scan"),
        )

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
            db,
            scan_id,
            "completed",
            {
                "result": result.get("final_message", ""),
                "iterations": result.get("iterations", 0),
            },
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

        await ws_manager.broadcast_to_scan(
            scan_id, {"type": "error", "message": str(e)}
        )
    finally:
        db.close()


async def execute_tool_task(
    scan_id: int, tool_name: str, target: str, parameters: dict
):
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
            db,
            scan_id=scan_id,
            title=f"{tool_name} result",
            description=str(result)[:1000],
            severity="info",
            tool=tool_name,
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

    health_status = {
        "status": "healthy",
        "version": "2.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    # Check Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["services"]["database"] = {
            "status": "ok",
            "type": "postgresql",
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "error",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            socket_connect_timeout=2,
        )
        redis_client.ping()
        health_status["services"]["redis"] = {"status": "ok"}
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e),
        }
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
        "endpoints": {
            "scans": "/scans",
            "findings": "/scans/{id}/findings",
            "tools": "/tools",
            "reports": "/reports",
        },
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
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    websocket,
                )

            elif message.get("type") == "subscribe":
                channel = message.get("channel", "general")
                await manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "channel": channel,
                        "client_id": client_id,
                    },
                    websocket,
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
    """Simple agent connection manager with task support"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.agent_info: dict[str, dict] = (
            {}
        )  # agent_id -> {api_key, connected_at, ...}

    async def connect(
        self, websocket: WebSocket, agent_id: str, api_key: str = None
    ):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.agent_info[agent_id] = {
            "api_key": api_key,
            "connected_at": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
        }
        logger.info(f"✅ Agent {agent_id} connected via WebSocket")

    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in self.agent_info:
            del self.agent_info[agent_id]
        logger.info(f"🔌 Agent {agent_id} disconnected")

    async def send_to_agent(self, agent_id: str, message: dict) -> bool:
        """Send message to specific agent. Returns True if sent."""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
                self.agent_info[agent_id][
                    "last_seen"
                ] = datetime.utcnow().isoformat()
                return True
            except Exception as e:
                logger.error(f"❌ Failed to send to {agent_id}: {e}")
                return False
        return False

    async def send_task(self, agent_id: str, task: dict) -> bool:
        """Send task to agent"""
        return await self.send_to_agent(
            agent_id,
            {
                "type": "task",
                "task": task,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        for agent_id, ws in self.active_connections.items():
            if agent_id != exclude:
                try:
                    await ws.send_json(message)
                    self.agent_info[agent_id][
                        "last_seen"
                    ] = datetime.utcnow().isoformat()
                except Exception as e:
                    logger.error(f"❌ Failed to send to {agent_id}: {e}")

    def get_connected_agents(self) -> list:
        """Get list of connected agent IDs"""
        return list(self.active_connections.keys())

    def is_agent_connected(self, agent_id: str) -> bool:
        """Check if agent is connected"""
        return agent_id in self.active_connections


agent_connection_manager = SimpleAgentConnection()


@app.websocket("/agents/ws")
async def agent_websocket_endpoint(websocket: WebSocket):
    """
    Agent Communication WebSocket Endpoint with API Key Auth

    Protocol:
    1. Auth: {"type": "auth", "agent_id": "...", "api_key": "...", "api_secret": "..."}
    2. Receive: {"type": "auth_success", "agent_id": "..."}
    3. Receive tasks: {"type": "task", "task": {...}}
    4. Send results: {"type": "task_result", "task_id": "...", "result": {...}}
    5. Heartbeat: {"type": "heartbeat"} every 30s
    """
    agent_id: Optional[str] = None
    api_key: Optional[str] = None

    try:
        await websocket.accept()

        # Receive auth message
        auth_data = await websocket.receive_json()

        if auth_data.get("type") != "auth":
            await websocket.send_json(
                {
                    "type": "auth_failed",
                    "error": "Expected auth message with type 'auth'",
                }
            )
            await websocket.close()
            return

        agent_id = auth_data.get("agent_id")
        api_key = auth_data.get("api_key")
        auth_data.get("api_secret")

        if not agent_id:
            await websocket.send_json(
                {"type": "auth_failed", "error": "agent_id required"}
            )
            await websocket.close()
            return

        # Validate API Key (simple check for now)
        # In production: Use AgentAuthenticator to validate
        if not api_key or not api_key.startswith("zen_"):
            await websocket.send_json(
                {"type": "auth_failed", "error": "Invalid API key format"}
            )
            await websocket.close()
            return

        # Connect agent
        await agent_connection_manager.connect(websocket, agent_id, api_key)

        await websocket.send_json(
            {
                "type": "auth_success",
                "agent_id": agent_id,
                "message": "Connected to Zen-AI-Pentest Agent Network",
            }
        )

        from utils.security import mask_api_key, sanitize_log_id

        logger.info(
            f"🔌 Agent {sanitize_log_id(agent_id)} authenticated "
            f"with API key {mask_api_key(api_key)}"
        )

        # Main message loop
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "task_result":
                    # Receive task result from agent
                    task_id = data.get("task_id")
                    result = data.get("result", {})

                    logger.info(
                        f"✅ Task result received from "
                        f"{sanitize_log_id(agent_id)}: {sanitize_log_id(task_id)}"
                    )

                    # Forward to workflow orchestrator
                    try:
                        from agents.workflows.orchestrator import (
                            get_workflow_orchestrator,
                        )

                        orchestrator = get_workflow_orchestrator()
                        await orchestrator.submit_task_result(task_id, result)

                        await websocket.send_json(
                            {
                                "type": "ack",
                                "message_id": task_id,
                                "status": "result_received",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to process task result: {e}")

                elif msg_type == "task_ack":
                    # Agent acknowledged task receipt
                    task_id = data.get("task_id")
                    logger.debug(
                        f"📋 Task {sanitize_log_id(task_id)} acknowledged by "
                        f"{sanitize_log_id(agent_id)}"
                    )

                elif msg_type == "message":
                    # Agent-to-agent messaging
                    recipient = data.get("recipient", "broadcast")
                    payload = data.get("payload", {})

                    await websocket.send_json(
                        {
                            "type": "ack",
                            "message_id": data.get("message_id", "unknown"),
                            "status": "received",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    if recipient == "broadcast":
                        await agent_connection_manager.broadcast(
                            {
                                "type": "message",
                                "sender": agent_id,
                                "payload": payload,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                            exclude=agent_id,
                        )
                    else:
                        # Direct message
                        await agent_connection_manager.send_to_agent(
                            recipient,
                            {
                                "type": "message",
                                "sender": agent_id,
                                "payload": payload,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        )

                elif msg_type == "heartbeat":
                    await websocket.send_json(
                        {
                            "type": "heartbeat_ack",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                elif msg_type == "disconnect":
                    break

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "error": "Invalid JSON"}
                )
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json({"type": "error", "error": str(e)})

    except WebSocketDisconnect:
        logger.info("Agent WebSocket disconnected")
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
async def create_schedule(
    schedule: ScheduledScanCreate,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
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
        "next_run_at": calculate_next_run(
            schedule.frequency.value,
            schedule.schedule_time,
            schedule.schedule_day,
        ),
        "created_at": datetime.utcnow(),
        "created_by": user.get("sub", "unknown"),
    }

    SCHEDULED_SCANS.append(schedule_dict)
    SCHEDULE_ID_COUNTER += 1

    return schedule_dict


@app.get("/schedules", response_model=List[ScheduledScanResponse])
async def list_schedules(
    user: dict = Depends(verify_token), db=Depends(get_db)
):
    """List all scheduled scans"""
    return SCHEDULED_SCANS


@app.get("/schedules/{schedule_id}", response_model=ScheduledScanResponse)
async def get_schedule(
    schedule_id: int, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Get a specific scheduled scan"""
    for schedule in SCHEDULED_SCANS:
        if schedule["id"] == schedule_id:
            return schedule
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.patch("/schedules/{schedule_id}", response_model=ScheduledScanResponse)
async def update_schedule(
    schedule_id: int,
    update: ScheduledScanUpdate,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """Update a scheduled scan"""
    for schedule in SCHEDULED_SCANS:
        if schedule["id"] == schedule_id:
            # Update fields
            for field, value in update.dict(exclude_unset=True).items():
                if value is not None:
                    schedule[field] = value

            # Recalculate next run if schedule changed
            if (
                update.frequency
                or update.schedule_time
                or update.schedule_day is not None
            ):
                schedule["next_run_at"] = calculate_next_run(
                    schedule["frequency"],
                    schedule["schedule_time"],
                    schedule["schedule_day"],
                )

            return schedule
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Delete a scheduled scan"""
    global SCHEDULED_SCANS
    for i, schedule in enumerate(SCHEDULED_SCANS):
        if schedule["id"] == schedule_id:
            SCHEDULED_SCANS.pop(i)
            return {"message": "Schedule deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


@app.post("/schedules/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
    """Manually trigger a scheduled scan"""
    for schedule in SCHEDULED_SCANS:
        if schedule["id"] == schedule_id:
            background_tasks.add_task(
                execute_scheduled_scan, schedule, user.get("sub")
            )
            return {"message": "Scan triggered"}
    raise HTTPException(status_code=404, detail="Schedule not found")


def calculate_next_run(
    frequency: str, time_str: str, day: Optional[int] = None
) -> datetime:
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
            next_run = next_run.replace(
                month=now.month + 1 if now.month < 12 else 1
            )
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
            schedule["frequency"],
            schedule["schedule_time"],
            schedule.get("schedule_day"),
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
    logger.info(
        f"Would send email to {schedule['notification_email']} for scan {scan_id}"
    )


async def send_slack_notification(schedule: dict, scan_id: int):
    """Send Slack notification"""
    logger.info(f"Would send Slack notification for scan {scan_id}")


# ============================================================================
# STATS
# ============================================================================


@app.get("/stats/overview")
async def get_stats_overview(
    user: dict = Depends(verify_token), db=Depends(get_db)
):
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
    severity_counts = (
        db.query(Finding.severity, func.count(Finding.id))
        .group_by(Finding.severity)
        .all()
    )

    severity_distribution = [
        {
            "name": sev.capitalize(),
            "value": count,
            "color": get_severity_color(sev),
        }
        for sev, count in severity_counts
    ]

    # Fill missing severities
    all_severities = ["critical", "high", "medium", "low", "info"]
    existing = {s["name"].lower(): s for s in severity_distribution}
    for sev in all_severities:
        if sev not in existing:
            severity_distribution.append(
                {
                    "name": sev.capitalize(),
                    "value": 0,
                    "color": get_severity_color(sev),
                }
            )

    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "running_scans": running_scans,
        "total_findings": total_findings,
        "critical_findings": sum(
            1 for s in severity_counts if s[0] == "critical"
        ),
        "severity_distribution": severity_distribution,
        "trends": [],  # TODO: Implement trends
        "tool_usage": [],  # TODO: Implement tool usage
    }


def get_severity_color(severity: str) -> str:
    """Get color for severity level"""
    colors = {
        "critical": "#ef4444",
        "high": "#f97316",
        "medium": "#eab308",
        "low": "#22c55e",
        "info": "#3b82f6",
    }
    return colors.get(severity.lower(), "#6b7280")


@app.get("/stats/trends")
async def get_stats_trends(
    days: int = 30, user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Get scan trends for the last N days"""
    # TODO: Implement trend calculation
    return []


@app.get("/stats/severity")
async def get_severity_stats(
    user: dict = Depends(verify_token), db=Depends(get_db)
):
    """Get findings by severity"""
    from sqlalchemy import func

    from database.models import Finding

    severity_counts = (
        db.query(Finding.severity, func.count(Finding.id))
        .group_by(Finding.severity)
        .all()
    )

    return [
        {"severity": sev, "count": count} for sev, count in severity_counts
    ]


@app.get("/stats/tools")
async def get_tool_usage(
    user: dict = Depends(verify_token), db=Depends(get_db)
):
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

    try:
        # Reuse centralized validation logic from notifications.slack
        from notifications.slack import (
            _validate_slack_webhook_url as _core_validate_slack_webhook_url,
        )

        return _core_validate_slack_webhook_url(webhook_url)
    except ValueError as e:
        # Map validation errors to HTTP 400 responses
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/notifications/slack/test")
async def test_slack_notification(
    webhook_url: str, user: dict = Depends(verify_token)
):
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
            raise HTTPException(
                status_code=400, detail="Failed to send Slack notification"
            )
    except HTTPException:
        # Re-raise validation errors without wrapping in 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/slack/scan-complete")
async def notify_slack_scan_complete(
    scan_id: int,
    webhook_url: str,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
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
            scan_id=scan_id,
            target=scan.target,
            findings_count=findings_count,
            critical_count=critical_count,
        )

        if success:
            return {"status": "success", "message": "Notification sent"}
        else:
            raise HTTPException(
                status_code=400, detail="Failed to send notification"
            )
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
    return {
        "enabled": SLACK_CONFIG["enabled"],
        "configured": SLACK_CONFIG["webhook_url"] is not None,
    }


@app.post("/settings/slack")
async def update_slack_settings(
    webhook_url: str, enabled: bool = True, user: dict = Depends(verify_token)
):
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
    base_url: str,
    username: str,
    api_token: str,
    enabled: bool = True,
    user: dict = Depends(verify_token),
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
async def create_jira_ticket(
    finding_id: int,
    project_key: str,
    user: dict = Depends(verify_token),
    db=Depends(get_db),
):
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

    app.include_router(
        siem_v1_router, prefix="/api/v1/siem", tags=["SIEM v1.0"]
    )
    logger.info("API v1.0 SIEM endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load SIEM v1.0 endpoints: {e}")

try:
    from api.v1.dashboard import router as dashboard_v1_router

    app.include_router(
        dashboard_v1_router, prefix="/api/v1", tags=["Dashboard v1.0"]
    )
    logger.info("API v1.0 Dashboard endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load Dashboard v1.0 endpoints: {e}")

try:
    from api.v1.scans_extended import router as scans_v1_router

    app.include_router(
        scans_v1_router, prefix="/api/v1/scans-extended", tags=["Scans v1.0"]
    )
    logger.info("API v1.0 Scans endpoints loaded")
except ImportError as e:
    logger.warning(f"Could not load Scans v1.0 endpoints: {e}")

# Subdomain scanning routes
try:
    from api.routes.subdomain import router as subdomain_router

    app.include_router(
        subdomain_router, prefix="/api/v1/subdomain", tags=["Subdomain"]
    )
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

# Workflow routes - import directly to avoid circular imports
try:
    import importlib.util
    import sys
    from pathlib import Path

    workflows_path = Path(__file__).parent / "routes" / "workflows.py"
    spec = importlib.util.spec_from_file_location("workflows", workflows_path)
    workflows_module = importlib.util.module_from_spec(spec)
    sys.modules["workflows"] = workflows_module
    spec.loader.exec_module(workflows_module)

    app.include_router(workflows_module.router)
    logger.info("✅ Workflow endpoints loaded")
except Exception as e:
    logger.warning(f"Could not load Workflow endpoints: {e}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104
