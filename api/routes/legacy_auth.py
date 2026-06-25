"""
Legacy authentication routes extracted from api/main.py.

Deprecated: Use /api/v1/auth/* endpoints instead.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from api.auth_deps import (
    NEW_AUTH_AVAILABLE,
    _jwt_handler,
    _user_manager,
    legacy_authenticate_user,
    legacy_create_access_token,
    legacy_verify_token,
    optional_auth,
    verify_token,
)
from api.csrf_protection import csrf_protection, require_csrf
from api.rate_limiter import check_auth_rate_limit
from api.schemas import TokenResponse, UserLogin

router = APIRouter(tags=["Legacy Auth"])


@router.post("/auth/login", response_model=TokenResponse, deprecated=True)
async def login(credentials: UserLogin, request: Request):
    """
    DEPRECATED: Use POST /api/v1/auth/login instead

    Login und JWT Token erhalten (Database-backed)

    - **username**: Username (min. 3 Zeichen)
    - **password**: Passwort (min. 6 Zeichen)

    Returns JWT Token für authentifizierte Requests

    Migration: Change endpoint from /auth/login to /api/v1/auth/login
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


@router.get("/auth/me", deprecated=True)
async def me(request: Request):
    """DEPRECATED: Use GET /api/v1/auth/me instead

    Get current user info
    """
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


@router.post("/auth/refresh", deprecated=True)
async def refresh_token(request: Request):
    """
    DEPRECATED: Use POST /api/v1/auth/refresh instead

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


@router.get("/csrf-token", deprecated=True)
async def get_csrf_token(response: Response):
    """
    DEPRECATED: Use GET /api/v1/csrf-token instead

    Get CSRF Token for protected endpoints

    Returns CSRF token that must be included in X-CSRF-Token header
    for all POST/PUT/DELETE requests.
    """
    return csrf_protection.set_token(response)


@router.post("/auth/logout", deprecated=True)
async def logout(request: Request, user: Any = Depends(verify_token)):
    """
    DEPRECATED: Use POST /api/v1/auth/logout instead

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


@router.post("/auth/logout-all", deprecated=True)
async def logout_all_devices(request: Request, user: Any = Depends(verify_token)):
    """
    DEPRECATED: Use POST /api/v1/auth/logout-all instead

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
