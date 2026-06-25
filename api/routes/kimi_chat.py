"""
🤖 Kimi Chat API - Direkte Chat-Integration mit Kimi
Nutzt die Moonshot AI API für Chat-Funktionalität
"""

import logging

logger = logging.getLogger(__name__)

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from api.auth_simple import verify_token

router = APIRouter(prefix="/kimi", tags=["Kimi Chat"])
security = HTTPBearer(auto_error=False)


class ChatMessage(BaseModel):
    """Eine Chat-Nachricht"""

    role: str  # "user" oder "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat Request"""

    message: str
    history: List[ChatMessage] = []
    model: str = "kimi-k2.5"


class ChatResponse(BaseModel):
    """Chat Response"""

    response: str
    model: str
    usage: Optional[Dict[str, Any]] = None


def get_local_kimi_token() -> Optional[str]:
    """Lese lokalen Kimi Token"""
    try:
        home = Path.home()
        credential_paths = [
            home / ".kimi" / "credentials" / "kimi-code.json",
        ]

        for cred_path in credential_paths:
            if cred_path.exists():
                with open(cred_path, "r") as f:
                    data = json.load(f)
                    token = data.get("access_token") or data.get("token")
                    if token:
                        return token

        return os.getenv("KIMI_ACCESS_TOKEN")
    except Exception:
        return None


@router.post("/chat", response_model=ChatResponse)
async def kimi_chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Chat mit Kimi AI
    Nutzt die Moonshot AI API
    """
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)

    # Get Kimi token
    token = get_local_kimi_token()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Kimi nicht authentifiziert. Bitte 'kimi login' ausführen.",
        )

    # Build messages
    messages = []
    for msg in request.history[-10:]:  # Keep last 10 messages for context
        messages.append({"role": msg.role, "content": msg.content})

    # Add current message
    messages.append({"role": "user", "content": request.message})

    try:
        # Call Moonshot AI API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": request.model,
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 4000,
                },
            )

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Kimi Chat API Error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Kimi API Error: {error_text}",
                )

            data = response.json()

            # Extract response
            content = data["choices"][0]["message"]["content"]

            return ChatResponse(response=content, model=request.model, usage=data.get("usage"))

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Kimi API Timeout")
    except Exception as e:
        logger.exception(f"Kimi Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def kimi_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Prüfe Kimi Status"""
    # SECURITY: Verify valid JWT token (not just presence)
    verify_token(credentials)

    token = get_local_kimi_token()

    return {
        "installed": True,
        "authenticated": token is not None,
        "message": "Kimi Chat bereit" if token else "Bitte einloggen",
    }
