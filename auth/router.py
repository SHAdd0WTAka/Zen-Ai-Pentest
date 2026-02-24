"""
Authentication Router
=====================

FastAPI router with all authentication endpoints:
- POST /auth/login
- POST /auth/register
- POST /auth/refresh
- POST /auth/logout
- POST /auth/mfa/setup
- POST /auth/mfa/verify
- GET /auth/me
- POST /auth/api-keys

Compliance: OWASP ASVS 2026 V2.1, V2.2, V2.3
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, validator

from .api_key_manager import get_api_key_manager
from .audit_logger import AuditEventType, AuditSeverity, get_audit_logger
from .config import get_config
from .jwt_handler import JWTHandler
from .mfa import get_mfa_manager
from .middleware import AuthContext, require_auth
from .password_hasher import PasswordStrengthError, get_password_hasher
from .rate_limiter import RateLimitType, get_rate_limiter
from .rbac import Role, get_rbac_manager
from .session_manager import get_session_manager

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============== Pydantic Models ==============


class UserRegisterRequest(BaseModel):
    """User registration request"""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=12)

    @validator("username")
    def validate_username(cls, v):
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError(
                "Username must be alphanumeric with optional underscores and hyphens"
            )
        return v


class UserLoginRequest(BaseModel):
    """User login request"""

    username: str
    password: str
    mfa_code: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    mfa_required: bool = False


class MFASetupRequest(BaseModel):
    """MFA setup request"""

    password: str


class MFASetupResponse(BaseModel):
    """MFA setup response"""

    secret: str
    qr_code_uri: str
    backup_codes: List[str]


class MFAVerifyRequest(BaseModel):
    """MFA verify request"""

    code: str = Field(..., min_length=6, max_length=8)


class MFAVerifyResponse(BaseModel):
    """MFA verify response"""

    success: bool
    method: str
    remaining_backup_codes: Optional[int] = None


class UserProfileResponse(BaseModel):
    """User profile response"""

    id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class APIKeyCreateRequest(BaseModel):
    """API key create request"""

    name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    permissions: Optional[List[str]] = None


class APIKeyResponse(BaseModel):
    """API key response"""

    id: str
    name: str
    key_preview: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    status: str


class APIKeyCreateResponse(APIKeyResponse):
    """API key create response (includes plain key)"""

    key: str  # Only shown once on creation


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request"""

    refresh_token: Optional[str] = None
    all_sessions: bool = False


class MessageResponse(BaseModel):
    """Generic message response"""

    message: str


# ============== In-Memory User Store (Replace with database in production) ==============


class UserStore:
    """Simple in-memory user store for demonstration"""

    def __init__(self):
        self._users: dict = {}
        self._user_id_counter = 0

    def create_user(
        self, username: str, email: str, password_hash: str
    ) -> dict:
        """Create a new user"""
        self._user_id_counter += 1
        user_id = str(self._user_id_counter)

        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "roles": [Role.USER.value],
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

        self._users[username] = user
        return user

    def get_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        return self._users.get(username)

    def get_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None

    def update_last_login(self, username: str) -> None:
        """Update last login time"""
        user = self._users.get(username)
        if user:
            user["last_login"] = datetime.now(timezone.utc)
            user["failed_login_attempts"] = 0

    def increment_failed_login(self, username: str) -> None:
        """Increment failed login attempts"""
        user = self._users.get(username)
        if user:
            user["failed_login_attempts"] += 1


# Global user store
user_store = UserStore()


# ============== Helper Functions ==============


def get_client_info(request: Request) -> tuple:
    """Get client IP and user agent from request"""
    # Get IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None

    # Get user agent
    user_agent = request.headers.get("User-Agent")

    return ip, user_agent


def get_user_permissions(user: dict) -> List[str]:
    """Get user permissions from roles"""
    rbac = get_rbac_manager()
    permissions = set()

    for role_str in user.get("roles", []):
        role = rbac.parse_role(role_str)
        if role:
            permissions.update(rbac.get_role_permissions(role))

    return [p.value for p in permissions]


# ============== Endpoints ==============


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(request: Request, data: UserRegisterRequest):
    """
    Register a new user

    Creates a new user account with the provided credentials.
    """
    config = get_config()

    # Check if registration is allowed
    if not config.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled",
        )

    # Rate limiting
    ip, _ = get_client_info(request)
    rate_limiter = get_rate_limiter()
    rate_result = rate_limiter.check_rate_limit(
        ip or "unknown", RateLimitType.REGISTRATION
    )

    if not rate_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_result.message,
        )

    # Check if username exists
    if user_store.get_by_username(data.username):
        rate_limiter.record_attempt(
            ip or "unknown", RateLimitType.REGISTRATION
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # Validate password strength
    password_hasher = get_password_hasher()
    try:
        password_hasher.validate_password_or_raise(data.password)
    except PasswordStrengthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Hash password
    password_hash = password_hasher.hash_password(data.password)

    # Create user
    user = user_store.create_user(
        username=data.username, email=data.email, password_hash=password_hash
    )

    # Assign default role in RBAC
    rbac = get_rbac_manager()
    rbac.assign_role(user["id"], Role.USER)

    # Log event
    audit_logger = get_audit_logger()
    audit_logger.log_event(
        event_type=AuditEventType.USER_REGISTERED,
        message="User registered",
        user_id=user["id"],
        ip_address=ip,
        details={"username": data.username},
    )

    return MessageResponse(message="User registered successfully")


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, data: UserLoginRequest):
    """
    Authenticate and receive tokens

    Authenticates a user and returns access and refresh tokens.
    If MFA is enabled, requires MFA code.
    """
    ip, user_agent = get_client_info(request)
    identifier = data.username

    # Rate limiting
    rate_limiter = get_rate_limiter()
    rate_result = rate_limiter.check_rate_limit(
        identifier, RateLimitType.LOGIN
    )

    if not rate_result.allowed:
        # Log rate limit
        audit_logger = get_audit_logger()
        audit_logger.log_rate_limit_exceeded(
            identifier=identifier, limit_type="login", ip_address=ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_result.message,
        )

    # Get user
    user = user_store.get_by_username(data.username)

    if not user:
        rate_limiter.record_attempt(identifier, RateLimitType.LOGIN)
        audit_logger = get_audit_logger()
        audit_logger.log_login_failure(
            username=data.username,
            ip_address=ip,
            user_agent=user_agent,
            reason="user_not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    password_hasher = get_password_hasher()
    if not password_hasher.verify_password(
        data.password, user["password_hash"]
    ):
        rate_limiter.record_attempt(identifier, RateLimitType.LOGIN)
        user_store.increment_failed_login(data.username)

        audit_logger = get_audit_logger()
        audit_logger.log_login_failure(
            username=data.username,
            ip_address=ip,
            user_agent=user_agent,
            reason="invalid_password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check MFA
    mfa_manager = get_mfa_manager()
    mfa_enabled = mfa_manager.is_mfa_enabled(user["id"])

    if mfa_enabled:
        if not data.mfa_code:
            # MFA required but no code provided
            return TokenResponse(
                access_token="",
                refresh_token="",
                token_type="bearer",
                expires_in=0,
                mfa_required=True,
            )

        # Verify MFA code
        mfa_result = mfa_manager.verify(user["id"], data.mfa_code)
        if not mfa_result.success:
            rate_limiter.record_attempt(identifier, RateLimitType.LOGIN)

            audit_logger = get_audit_logger()
            audit_logger.log_event(
                event_type=AuditEventType.MFA_FAILED,
                message="MFA verification failed",
                user_id=user["id"],
                ip_address=ip,
                severity=AuditSeverity.WARNING,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code",
            )

    # Create session
    session_manager = get_session_manager()
    session = session_manager.create_session(
        user_id=user["id"],
        ip_address=ip,
        user_agent=user_agent,
        mfa_verified=mfa_enabled,
    )

    # Get user permissions
    permissions = get_user_permissions(user)

    # Create tokens
    jwt_handler = JWTHandler()
    tokens = jwt_handler.create_token_pair(
        user_id=user["id"],
        roles=user["roles"],
        permissions=permissions,
        session_id=session.id,
        mfa_verified=mfa_enabled or not get_config().require_mfa,
        ip_address=ip,
        user_agent=user_agent,
    )

    # Update last login
    user_store.update_last_login(data.username)

    # Record successful login
    rate_limiter.record_attempt(identifier, RateLimitType.LOGIN, success=True)

    # Log event
    audit_logger = get_audit_logger()
    audit_logger.log_login_success(
        user_id=user["id"],
        session_id=session.id,
        ip_address=ip,
        user_agent=user_agent,
        mfa_used=mfa_enabled,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        mfa_required=False,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, data: RefreshTokenRequest):
    """
    Refresh access token

    Uses a refresh token to obtain a new access token.
    """
    ip, user_agent = get_client_info(request)

    try:
        jwt_handler = JWTHandler()

        # Get user for permissions
        payload = jwt_handler.verify_refresh_token(data.refresh_token)
        user = user_store.get_by_id(payload.sub)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        permissions = get_user_permissions(user)

        # Rotate tokens
        tokens = jwt_handler.rotate_refresh_token(
            refresh_token=data.refresh_token,
            roles=user["roles"],
            permissions=permissions,
            ip_address=ip,
            user_agent=user_agent,
        )

        # Log event
        audit_logger = get_audit_logger()
        audit_logger.log_event(
            event_type=AuditEventType.TOKEN_REFRESH,
            message="Token refreshed",
            user_id=user["id"],
            ip_address=ip,
        )

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=get_config().jwt.access_token_expire_minutes * 60,
            mfa_required=False,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    data: LogoutRequest,
    auth: AuthContext = Depends(require_auth),
):
    """
    Logout user

    Invalidates the current session and optionally all sessions.
    """
    ip, _ = get_client_info(request)

    # Blacklist refresh token if provided
    if data.refresh_token:
        jwt_handler = JWTHandler()
        try:
            payload = jwt_handler.verify_refresh_token(data.refresh_token)
            jwt_handler.blacklist_token(payload.jti, "logout")
        except Exception:
            pass

    # Terminate session
    if auth.session_id:
        session_manager = get_session_manager()
        session_manager.terminate_session(auth.session_id, "logout")

    # Terminate all sessions if requested
    if data.all_sessions:
        session_manager = get_session_manager()
        session_manager.terminate_all_user_sessions(
            auth.user_id, exclude_session_id=auth.session_id
        )

        # Blacklist all tokens
        jwt_handler = JWTHandler()
        jwt_handler.blacklist_user_tokens(auth.user_id, "logout_all")

    # Log event
    audit_logger = get_audit_logger()
    audit_logger.log_logout(
        user_id=auth.user_id, session_id=auth.session_id or "", ip_address=ip
    )

    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user(auth: AuthContext = Depends(require_auth)):
    """
    Get current user profile

    Returns the profile of the currently authenticated user.
    """
    user = user_store.get_by_id(auth.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    mfa_manager = get_mfa_manager()

    return UserProfileResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        roles=user["roles"],
        permissions=auth.permissions,
        mfa_enabled=mfa_manager.is_mfa_enabled(user["id"]),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
    )


# ============== MFA Endpoints ==============


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    request: Request,
    data: MFASetupRequest,
    auth: AuthContext = Depends(require_auth),
):
    """
    Setup MFA for user

    Generates MFA secret and backup codes.
    """
    user = user_store.get_by_id(auth.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify password
    password_hasher = get_password_hasher()
    if not password_hasher.verify_password(
        data.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    # Setup MFA
    mfa_manager = get_mfa_manager()

    try:
        result = mfa_manager.setup_mfa(auth.user_id, user["username"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return MFASetupResponse(
        secret=result.secret,
        qr_code_uri=result.qr_code_uri,
        backup_codes=result.backup_codes,
    )


@router.post("/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: Request,
    data: MFAVerifyRequest,
    auth: AuthContext = Depends(require_auth),
):
    """
    Verify MFA setup

    Verifies the MFA code and enables MFA for the user.
    """
    mfa_manager = get_mfa_manager()

    result = mfa_manager.verify_setup(auth.user_id, data.code)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
        )

    # Log event
    ip, _ = get_client_info(request)
    audit_logger = get_audit_logger()
    audit_logger.log_mfa_enabled(user_id=auth.user_id, ip_address=ip)

    return MFAVerifyResponse(
        success=True,
        method="totp",
        remaining_backup_codes=mfa_manager.get_remaining_backup_codes(
            auth.user_id
        ),
    )


@router.post("/mfa/disable", response_model=MessageResponse)
async def disable_mfa(
    request: Request,
    data: MFASetupRequest,
    auth: AuthContext = Depends(require_auth),
):
    """
    Disable MFA for user

    Disables MFA after password verification.
    """
    user = user_store.get_by_id(auth.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify password
    password_hasher = get_password_hasher()
    if not password_hasher.verify_password(
        data.password, user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    # Disable MFA
    mfa_manager = get_mfa_manager()
    result = mfa_manager.disable_mfa(auth.user_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled",
        )

    # Log event
    ip, _ = get_client_info(request)
    audit_logger = get_audit_logger()
    audit_logger.log_mfa_disabled(
        user_id=auth.user_id, ip_address=ip, reason="user_request"
    )

    return MessageResponse(message="MFA disabled successfully")


# ============== API Key Endpoints ==============


@router.post(
    "/api-keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: Request,
    data: APIKeyCreateRequest,
    auth: AuthContext = Depends(require_auth),
):
    """
    Create API key

    Creates a new API key for the authenticated user.
    """
    ip, _ = get_client_info(request)

    api_key_manager = get_api_key_manager()

    try:
        result = api_key_manager.create_api_key(
            user_id=auth.user_id,
            name=data.name,
            expires_in_days=data.expires_in_days,
            permissions=data.permissions,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    # Log event
    audit_logger = get_audit_logger()
    audit_logger.log_api_key_created(
        user_id=auth.user_id, key_id=result.api_key.id, ip_address=ip
    )

    return APIKeyCreateResponse(
        id=result.api_key.id,
        name=result.api_key.name,
        key=result.plain_key,  # Only shown once!
        key_preview=result.api_key.key_preview,
        created_at=result.api_key.created_at,
        expires_at=result.api_key.expires_at,
        last_used_at=result.api_key.last_used_at,
        usage_count=result.api_key.usage_count,
        status=result.api_key.status.value,
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(auth: AuthContext = Depends(require_auth)):
    """
    List API keys

    Returns all API keys for the authenticated user.
    """
    api_key_manager = get_api_key_manager()
    keys = api_key_manager.get_user_api_keys(auth.user_id)

    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key_preview=key.key_preview,
            created_at=key.created_at,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            status=key.status.value,
        )
        for key in keys
    ]


@router.delete("/api-keys/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    request: Request, key_id: str, auth: AuthContext = Depends(require_auth)
):
    """
    Revoke API key

    Revokes an API key by ID.
    """
    ip, _ = get_client_info(request)

    api_key_manager = get_api_key_manager()
    result = api_key_manager.revoke_api_key(auth.user_id, key_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # Log event
    audit_logger = get_audit_logger()
    audit_logger.log_api_key_revoked(
        user_id=auth.user_id,
        key_id=key_id,
        ip_address=ip,
        reason="user_request",
    )

    return MessageResponse(message="API key revoked successfully")
