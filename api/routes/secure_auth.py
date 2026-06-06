"""
🔐 Secure Authentication Routes for ZEN-ALPHA
Device Auth Bridge + LocalPortManager Integration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import hmac
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from auth.secure_auth_integration import get_secure_auth_manager

router = APIRouter(prefix="/auth", tags=["Secure Authentication"])


class LoginRequest(BaseModel):
    """Legacy login request (fallback)"""

    username: str
    password: str


class DeviceAuthStatus(BaseModel):
    """Device authentication status"""

    authenticated: bool
    device_id: str
    token_preview: Optional[str] = None
    login_url: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information"""

    session_id: str
    device_id: str
    created_at: str
    expires_at: str
    is_valid: bool


# Get auth manager
auth_manager = get_secure_auth_manager()


@router.get("/status", response_model=DeviceAuthStatus)
async def auth_status():
    """
    Check authentication status
    Returns device auth status and login URL if not authenticated
    """
    is_auth, preview = auth_manager.check_device_auth()

    response = {
        "authenticated": is_auth,
        "device_id": auth_manager.device_id,
        "token_preview": preview,
    }

    if not is_auth:
        # Generate browser login URL
        login_info = auth_manager.initiate_browser_login()
        response["login_url"] = login_info["auth_url"]
        response["login_data"] = {
            "callback_port": login_info["callback_port"],
            "state": login_info["state"],
        }

    return response


@router.get("/login")
async def login_page():
    """
    Initiate browser-based login
    Redirects user to Kimi OAuth page
    """
    login_info = auth_manager.initiate_browser_login()

    # Store state for callback verification
    # In production, store in Redis/session

    return {
        "message": "Please authenticate via browser",
        "auth_url": login_info["auth_url"],
        "device_id": login_info["device_id"],
        "instructions": [
            "1. Open the auth_url in your browser",
            "2. Login with your Kimi account",
            "3. You will be redirected back to complete authentication",
        ],
    }


@router.get("/callback")
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    OAuth callback from browser
    Exchanges code for access token
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Auth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code")

    # Verify state (prevent CSRF)
    # In production, verify against stored state

    # Exchange code for token via Device Auth Bridge
    try:
        # The Device Auth Bridge handles token exchange
        if auth_manager.auth_bridge.is_authenticated():
            token = auth_manager.auth_bridge.get_access_token()

            # Create session
            session = auth_manager.create_session(access_token=token, user_agent="ZEN-ALPHA Browser Client")

            # Set session cookie
            response = RedirectResponse(url="/")
            response.set_cookie(
                key="zen_session",
                value=session.session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=3600,
            )

            return response
        else:
            raise HTTPException(status_code=401, detail="Device not authenticated")

    except Exception:
        raise HTTPException(status_code=500, detail="Token exchange failed: Internal error")


@router.post("/token")
async def legacy_login(request: LoginRequest, response: Response):
    """
    Legacy username/password login (fallback)
    For development/testing only
    """
    # SECURITY: Never use hardcoded passwords. Require ADMIN_PASSWORD env var.
    _legacy_password = os.getenv("ADMIN_PASSWORD")
    if not _legacy_password:
        raise HTTPException(
            status_code=503,
            detail="Legacy login disabled: ADMIN_PASSWORD not configured",
        )
    if request.username == "admin" and hmac.compare_digest(request.password, _legacy_password):
        # Create session without Device Auth
        session = auth_manager.create_session(access_token="dev_token", user_agent="Legacy Client")

        response.set_cookie(
            key="zen_session",
            value=session.session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600,
        )

        return {
            "access_token": session.session_id,
            "token_type": "bearer",
            "expires_in": 3600,
            "message": "⚠️ Using legacy auth - setup Device Auth for production",
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and revoke session"""
    session_id = request.cookies.get("zen_session")

    if session_id:
        auth_manager.revoke_session(session_id)

    response.delete_cookie("zen_session")
    return {"message": "Logged out successfully"}


@router.get("/session", response_model=SessionInfo)
async def get_session(request: Request):
    """Get current session info"""
    session_id = request.cookies.get("zen_session")

    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")

    session = auth_manager.validate_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    return {
        "session_id": session.session_id,
        "device_id": session.device_id,
        "created_at": session.created_at.isoformat(),
        "expires_at": (session.expires_at.isoformat() if session.expires_at else None),
        "is_valid": True,
    }


@router.get("/sessions")
async def list_sessions(request: Request):
    """List all active sessions (admin only)"""
    # In production, check admin role
    return {
        "sessions": auth_manager.get_active_sessions(),
        "device_id": auth_manager.device_id,
    }


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, request: Request):
    """Revoke a specific session"""
    # In production, verify user owns session or is admin
    success = auth_manager.revoke_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session revoked"}


@router.get("/proxy-status")
async def proxy_status():
    """Get reverse proxy status"""
    try:
        services = auth_manager.port_manager.registry.list_services()
        return {
            "proxy_port": auth_manager.proxy_port,
            "api_port": auth_manager.api_port,
            "services": services,
            "device_id": auth_manager.device_id,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
