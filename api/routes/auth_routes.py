"""
Authentication Routes für Zen-AI-Pentest API

Endpoints:
- POST /auth/login - Username/Password → JWT Token
- POST /auth/register - Neuen Benutzer erstellen
- GET /auth/me - Aktuellen Benutzer abrufen (protected)
- POST /auth/refresh - Token erneuern
- POST /auth/logout - Ausloggen (Token blacklist)

Integration mit:
- JWTHandler für Token-Management
- PasswordHasher für bcrypt-Passwort-Hashing
- SQLAlchemy Auth Models für User-Datenbank
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from api.auth import (
    get_auth_service,
    get_current_user,
    get_jwt_handler,
    require_admin,
)
from database.auth_models import (
    User,
    create_audit_log,
    get_auth_db,
    get_user_by_username,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# =============================================================================
# Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """Login Request Schema"""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """Registration Request Schema"""

    username: str = Field(
        ..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", description="Username (alphanumeric and underscore only)"
    )
    email: EmailStr
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")
    full_name: Optional[str] = Field(None, max_length=100)


class TokenResponse(BaseModel):
    """Token Response Schema"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class TokenPairResponse(BaseModel):
    """Token Pair Response with Refresh Token"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    """User Response Schema"""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: Optional[str] = None


class RefreshRequest(BaseModel):
    """Token Refresh Request"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout Request"""

    refresh_token: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic Message Response"""

    message: str


# =============================================================================
# Helper Functions
# =============================================================================


def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _user_to_dict(user: User) -> dict:
    """Convert User model to dictionary"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_mfa_enabled": user.is_mfa_enabled,
    }


# =============================================================================
# Routes
# =============================================================================


@router.post(
    "/login",
    response_model=TokenPairResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with username and password",
    description="Authenticate user and return JWT access and refresh tokens",
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "User account deactivated"},
    },
)
async def login(
    request: LoginRequest,
    req: Request,
    db=Depends(get_auth_db),
):
    """
    Login mit Username und Password

    Returns:
        - access_token: JWT Access Token (kurzlebig)
        - refresh_token: JWT Refresh Token (langlebig)
        - expires_in: Ablaufzeit in Sekunden
        - user: Benutzerinformationen
    """
    auth_service = get_auth_service()
    jwt_handler = get_jwt_handler()
    client_info = get_client_info(req)

    # Authenticate user
    user_data = auth_service.authenticate_user(db, request.username, request.password)

    if not user_data:
        # Log failed login attempt
        create_audit_log(
            db,
            action="login",
            action_category="auth",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            result="failure",
            failure_reason="Invalid credentials",
            details={"username": request.username},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get full user object
    user = get_user_by_username(db, user_data["username"])

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = client_info.get("ip_address")
    db.commit()

    # Create token pair
    tokens = jwt_handler.create_token_pair(
        user_id=str(user.id),
        roles=[user.role.value if hasattr(user.role, "value") else str(user.role)],
        permissions=[],  # Will be calculated from role
        ip_address=client_info.get("ip_address"),
        user_agent=client_info.get("user_agent"),
    )

    # Log successful login
    create_audit_log(
        db,
        user_id=user.id,
        action="login",
        action_category="auth",
        ip_address=client_info.get("ip_address"),
        user_agent=client_info.get("user_agent"),
        result="success",
        details={"method": "password"},
    )

    return TokenPairResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=_user_to_dict(user),
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with username, email and password",
    responses={
        400: {"description": "Username or email already exists"},
        422: {"description": "Invalid input data"},
    },
)
async def register(
    request: RegisterRequest,
    req: Request,
    db=Depends(get_auth_db),
):
    """
    Neuen Benutzer registrieren

    Password requirements:
    - Mindestens 12 Zeichen
    - Mindestens ein Großbuchstabe
    - Mindestens ein Kleinbuchstabe
    - Mindestens eine Zahl
    - Mindestens ein Sonderzeichen

    Returns:
        User object without sensitive data
    """
    auth_service = get_auth_service()
    client_info = get_client_info(req)

    # Check if username exists
    existing_user = get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    from database.auth_models import get_user_by_email

    existing_email = get_user_by_email(db, request.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    try:
        user_data = auth_service.create_user(
            db,
            username=request.username,
            email=request.email,
            password=request.password,
            role="user",
        )

        # Log registration
        create_audit_log(
            db,
            user_id=user_data["id"],
            action="register",
            action_category="auth",
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            result="success",
            details={"username": request.username},
        )

        return UserResponse(**user_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=dict,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    user: dict = Depends(get_current_user),
    db=Depends(get_auth_db),
):
    """
    Aktuellen Benutzer abrufen

    Returns:
        User object with id, username, email, role
    """
    # Get fresh user data from database
    from database.auth_models import get_user_by_id

    db_user = get_user_by_id(db, int(user.get("user_id", 0)))

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role),
        "is_active": db_user.is_active,
        "is_verified": db_user.is_verified,
        "is_mfa_enabled": db_user.is_mfa_enabled,
        "last_login_at": db_user.last_login_at.isoformat() if db_user.last_login_at else None,
        "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: RefreshRequest,
    req: Request,
    db=Depends(get_auth_db),
):
    """
    Access Token erneuern

    Args:
        refresh_token: Valid refresh token

    Returns:
        New access token
    """
    jwt_handler = get_jwt_handler()
    client_info = get_client_info(req)

    try:
        # Verify refresh token and rotate
        token_data = jwt_handler.rotate_refresh_token(
            request.refresh_token,
            roles=[],  # Will be extracted from old token
            permissions=[],
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
        )

        # Get user info from new token
        payload = jwt_handler.decode_token(token_data["access_token"])
        from database.auth_models import get_user_by_id

        user = get_user_by_id(db, int(payload.sub))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data.get("expires_in", 3600),
            user=_user_to_dict(user),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Invalidate the current access token and optionally refresh token",
)
async def logout(
    request: LogoutRequest,
    user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_auth_db),
):
    """
    Ausloggen und Token invalidieren

    Blacklists the current access token and optionally the refresh token.
    """
    jwt_handler = get_jwt_handler()

    # Get JTI from current token and blacklist it
    try:
        payload = jwt_handler.decode_token(credentials.credentials)
        jwt_handler.blacklist_token(payload.jti, "logout")

        # Also blacklist refresh token if provided
        if request.refresh_token:
            refresh_payload = jwt_handler.verify_refresh_token(request.refresh_token)
            jwt_handler.blacklist_token(refresh_payload.jti, "logout")

        # Log logout
        create_audit_log(
            db,
            user_id=int(user.get("user_id", 0)),
            action="logout",
            action_category="auth",
            result="success",
        )

        return MessageResponse(message="Logged out successfully")

    except Exception:
        # Still return success even if token was already expired
        return MessageResponse(message="Logged out")


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password",
)
async def change_password(
    old_password: str = Body(..., min_length=1),
    new_password: str = Body(..., min_length=12),
    user: dict = Depends(get_current_user),
    db=Depends(get_auth_db),
):
    """
    Passwort ändern

    Args:
        old_password: Current password
        new_password: New password (min 12 chars)
    """
    from auth import PasswordHasher
    from database.auth_models import get_user_by_id

    user_id = int(user.get("user_id", 0))
    db_user = get_user_by_id(db, user_id)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    hasher = PasswordHasher()

    # Verify old password
    if not hasher.verify(old_password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    is_valid, error = hasher.validate_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"New password too weak: {error}",
        )

    # Hash and set new password
    db_user.hashed_password = hasher.hash(new_password)
    db_user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    # Log password change
    create_audit_log(
        db,
        user_id=user_id,
        action="password_change",
        action_category="security",
        result="success",
    )

    return MessageResponse(message="Password changed successfully")


# =============================================================================
# Admin Routes
# =============================================================================


@router.get(
    "/users",
    response_model=list,
    summary="List all users (admin only)",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_auth_db),
):
    """Liste aller Benutzer (nur Admin)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [_user_to_dict(u) for u in users]


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Delete user (admin only)",
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_auth_db),
):
    """Benutzer löschen (nur Admin)"""
    # Prevent self-deletion
    if int(current_user.get("user_id", 0)) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    from database.auth_models import get_user_by_id

    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()

    return MessageResponse(message=f"User {user_id} deleted")
