# ============================================
# Kimi Device Authentication Bridge Router
# ============================================

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import bridge
sys.path.append(str(Path(__file__).parent.parent))
from kimi_bridge.bridge import AsyncKimiAuthBridge, KimiAuthBridge
from kimi_bridge.exceptions import KimiNotAuthenticatedError

router = APIRouter(prefix="/kimi-auth", tags=["kimi-auth"])

# Initialize bridge
kimi_bridge = KimiAuthBridge()


class KimiAuthStatus(BaseModel):
    authenticated: bool
    api_base: str
    model: str
    token_preview: Optional[str] = None


class KimiAuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/status", response_model=KimiAuthStatus)
async def get_kimi_status():
    """Get Kimi CLI authentication status"""
    try:
        is_auth = kimi_bridge.is_authenticated()

        return KimiAuthStatus(
            authenticated=is_auth,
            api_base=kimi_bridge.get_api_base(),
            model=kimi_bridge.get_default_model(),
            token_preview=kimi_bridge.get_token_preview() if is_auth else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token")
async def get_kimi_token():
    """Get Kimi access token (requires authentication)"""
    try:
        if not kimi_bridge.is_authenticated():
            raise HTTPException(
                status_code=401,
                detail="Not authenticated with Kimi CLI. Please run 'kimi login'",
            )

        kimi_bridge.get_access_token()
        headers = kimi_bridge.get_auth_headers()

        return {
            "token_preview": kimi_bridge.get_token_preview(),
            "api_base": kimi_bridge.get_api_base(),
            "user_agent": kimi_bridge.get_user_agent(),
            "headers": headers,
        }
    except KimiNotAuthenticatedError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=KimiAuthResponse)
async def trigger_kimi_login():
    """Trigger Kimi CLI login flow"""
    try:
        # Note: This requires kimi CLI to be installed on the server

        bridge = AsyncKimiAuthBridge()
        result = await bridge.login()

        return KimiAuthResponse(
            success=result,
            message="Login successful" if result else "Login failed",
            data={"authenticated": bridge.is_authenticated()},
        )
    except Exception as e:
        return KimiAuthResponse(success=False, message=f"Login error: {str(e)}")


@router.post("/logout", response_model=KimiAuthResponse)
async def trigger_kimi_logout():
    """Trigger Kimi CLI logout"""
    try:
        bridge = AsyncKimiAuthBridge()
        result = await bridge.logout()

        return KimiAuthResponse(
            success=result,
            message="Logout successful" if result else "Logout failed",
        )
    except Exception as e:
        return KimiAuthResponse(success=False, message=f"Logout error: {str(e)}")


@router.get("/headers")
async def get_auth_headers():
    """Get complete auth headers for API requests"""
    try:
        headers = kimi_bridge.get_auth_headers()
        return {"headers": headers, "api_base": kimi_bridge.get_api_base()}
    except KimiNotAuthenticatedError:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please run 'kimi login'",
        )
