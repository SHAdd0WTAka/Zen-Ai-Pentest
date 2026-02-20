"""
CSRF Protection für Zen-AI-Pentest API

Implementiert Double-Submit-Cookie Pattern:
1. Server setzt CSRF-Token als Cookie
2. Client muss Token im Header zurücksenden
3. Server vergleicht Cookie vs Header

Schützt vor:
- Cross-Site Request Forgery
- Session Riding
- Unautorisierte POST/PUT/DELETE Requests
"""

import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import Response

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "false").lower() == "true"
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
CSRF_TOKEN_EXPIRY = int(os.getenv("CSRF_TOKEN_EXPIRY", "86400"))  # 24 hours

# =============================================================================
# CSRF Token Management
# =============================================================================


class CSRFToken:
    """CSRF Token mit Zeitstempel und Validierung"""

    def __init__(self, token: str = None, timestamp: datetime = None):
        self.token = token or self._generate_token()
        self.timestamp = timestamp or datetime.utcnow()

    def _generate_token(self) -> str:
        """Generiert kryptographisch sicheres Token"""
        return secrets.token_urlsafe(32)

    def is_valid(self) -> bool:
        """Prüft ob Token noch gültig ist"""
        expiry = self.timestamp + timedelta(seconds=CSRF_TOKEN_EXPIRY)
        return datetime.utcnow() < expiry

    def to_cookie_value(self) -> str:
        """Formatiert Token für Cookie"""
        return f"{self.token}|{int(self.timestamp.timestamp())}"

    @classmethod
    def from_cookie_value(cls, cookie_value: str) -> Optional["CSRFToken"]:
        """Parst Token aus Cookie"""
        try:
            parts = cookie_value.split("|")
            if len(parts) != 2:
                return None
            token, timestamp = parts
            dt = datetime.fromtimestamp(int(timestamp))
            return cls(token, dt)
        except (ValueError, TypeError):
            return None


# =============================================================================
# CSRF Protection Middleware
# =============================================================================


class CSRFProtection:
    """
    CSRF Protection Middleware

    Usage:
        from api.csrf_protection import CSRFProtection
        csrf = CSRFProtection()

        @app.get("/csrf-token")
        async def get_csrf_token(response: Response):
            return csrf.set_token(response)

        @app.post("/api/action")
        async def protected_action(request: Request):
            csrf.validate(request)  # Wirft 403 falls ungültig
            return {"status": "ok"}
    """

    # Endpoints die kein CSRF benötigen (z.B. Login, API Keys)
    EXEMPT_ENDPOINTS = [
        "/auth/login",
        "/auth/logout",
        "/auth/refresh",
        "/api/webhook",  # Webhooks kommen von extern
        "/health",
        "/docs",
        "/openapi.json",
    ]

    # HTTP Methoden die CSRF-Schutz benötigen
    PROTECTED_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    def __init__(self):
        self.tokens: Dict[str, CSRFToken] = {}  # Session -> Token

    def set_token(self, response: Response, session_id: str = None) -> Dict:
        """
        Setzt neuen CSRF Token als Cookie

        Returns:
            Dict mit Token für Client
        """
        token = CSRFToken()

        # Cookie setzen
        cookie_value = token.to_cookie_value()
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=cookie_value,
            httponly=False,  # Muss von JavaScript lesbar sein
            secure=CSRF_COOKIE_SECURE,
            samesite=CSRF_COOKIE_SAMESITE,
            max_age=CSRF_TOKEN_EXPIRY,
            path="/",
        )

        # In Speicher merken (für Validierung)
        if session_id:
            self.tokens[session_id] = token

        logger.debug(f"CSRF Token gesetzt für Session: {session_id}")

        return {"csrf_token": token.token, "expires_in": CSRF_TOKEN_EXPIRY}

    def validate(self, request: Request) -> bool:
        """
        Validiert CSRF Token aus Request

        Raises:
            HTTPException: 403 falls Token ungültig/fehlt
        """
        # Prüfe ob Endpoint exempt ist
        path = request.url.path
        method = request.method

        if method not in self.PROTECTED_METHODS:
            return True  # GET, HEAD, OPTIONS, TRACE brauchen kein CSRF

        if any(path.startswith(exempt) for exempt in self.EXEMPT_ENDPOINTS):
            return True  # Exempt Endpoints

        # Token aus Cookie holen
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        if not cookie_token:
            logger.warning(f"CSRF Cookie fehlt: {path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing. Get a token from /csrf-token first."
            )

        # Token parsen und validieren
        csrf_token = CSRFToken.from_cookie_value(cookie_token)
        if not csrf_token or not csrf_token.is_valid():
            logger.warning(f"CSRF Token abgelaufen oder ungültig: {path}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token expired or invalid.")

        # Token aus Header holen
        header_token = request.headers.get(CSRF_HEADER_NAME)
        if not header_token:
            logger.warning(f"CSRF Header fehlt: {path}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"CSRF header '{CSRF_HEADER_NAME}' required.")

        # Tokens vergleichen (timing-safe)
        if not hmac.compare_digest(csrf_token.token, header_token):
            logger.warning(f"CSRF Token mismatch: {path}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token mismatch.")

        logger.debug(f"CSRF Token validiert: {path}")
        return True

    def rotate_token(self, response: Response, session_id: str = None) -> Dict:
        """
        Rotiert CSRF Token (nach Login oder periodisch)
        """
        # Altes Token entfernen
        if session_id and session_id in self.tokens:
            del self.tokens[session_id]

        # Neues Token setzen
        return self.set_token(response, session_id)

    def clear_token(self, response: Response, session_id: str = None):
        """
        Löscht CSRF Token (bei Logout)
        """
        response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")

        if session_id and session_id in self.tokens:
            del self.tokens[session_id]

        logger.debug(f"CSRF Token gelöscht für Session: {session_id}")


# =============================================================================
# FastAPI Dependency
# =============================================================================

csrf_protection = CSRFProtection()


async def require_csrf(request: Request):
    """
    FastAPI Dependency für CSRF-Schutz

    Usage:
        @app.post("/api/action")
        async def action(request: Request, _=Depends(require_csrf)):
            return {"status": "ok"}
    """
    csrf_protection.validate(request)
    return True


# =============================================================================
# Middleware für automatischen CSRF-Schutz
# =============================================================================


class CSRFMiddleware:
    """
    ASGI Middleware für automatischen CSRF-Schutz

    Usage:
        from api.csrf_protection import CSRFMiddleware
        app.add_middleware(CSRFMiddleware)
    """

    def __init__(self, app):
        self.app = app
        self.csrf = CSRFProtection()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Request prüfen
        request = Request(scope, receive)

        try:
            self.csrf.validate(request)
        except HTTPException as e:
            # Fehler direkt zurückgeben
            await send(
                {"type": "http.response.start", "status": e.status_code, "headers": [[b"content-type", b"application/json"]]}
            )
            await send({"type": "http.response.body", "body": f'"{e.detail}"'.encode()})
            return

        await self.app(scope, receive, send)
