"""
Pydantic schemas for authentication.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TokenPayload(BaseModel):
    """Token payload schema."""

    user_id: str


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class UserData(BaseModel):
    """User data schema."""

    id: str
    email: str
    username: str
    full_name: str
    avatar: Optional[str] = None
    role: str
    is_active: bool
    last_login: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TokenData(BaseModel):
    """Token data schema."""

    access_token: str
    refresh_token: str
    token_type: str
    user: UserData


class LoginResponse(BaseModel):
    """Login response schema."""

    success: bool
    data: TokenData


class UserResponse(BaseModel):
    """User response schema."""

    success: bool
    data: UserData


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirm schema."""

    token: str
    new_password: str = Field(..., min_length=8)
