"""
OAuth2 Authentication Integration
=================================

Supports:
- Google OAuth2
- GitHub OAuth
- Microsoft/Azure AD
- Generic OAuth2 providers

Author: SHAdd0WTAka
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status


class OAuthProvider(str, Enum):
    """Supported OAuth providers"""

    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    CUSTOM = "custom"


@dataclass
class OAuthConfig:
    """OAuth provider configuration"""

    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    redirect_uri: str
    scope: str
    provider: OAuthProvider


class OAuthManager:
    """Manages OAuth2 authentication flows"""

    PROVIDER_CONFIGS = {
        OAuthProvider.GOOGLE: {
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scope": "openid email profile",
        },
        OAuthProvider.GITHUB: {
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scope": "read:user user:email",
        },
        OAuthProvider.MICROSOFT: {
            "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scope": "openid email profile User.Read",
        },
    }

    def __init__(self, provider: OAuthProvider):
        self.provider = provider
        self.config = self._load_config()

    def _load_config(self) -> OAuthConfig:
        """Load OAuth configuration from environment"""
        prefix = f"OAUTH_{self.provider.value.upper()}_"

        client_id = os.getenv(f"{prefix}CLIENT_ID")
        client_secret = os.getenv(f"{prefix}CLIENT_SECRET")
        redirect_uri = os.getenv(
            f"{prefix}REDIRECT_URI",
            "http://localhost:8000/auth/oauth/callback",
        )

        if not client_id or not client_secret:
            raise ValueError(f"OAuth configuration missing for {self.provider.value}")

        provider_config = self.PROVIDER_CONFIGS.get(self.provider, {})

        return OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url=provider_config.get("authorize_url", ""),
            token_url=provider_config.get("token_url", ""),
            userinfo_url=provider_config.get("userinfo_url", ""),
            redirect_uri=redirect_uri,
            scope=provider_config.get("scope", "openid email profile"),
            provider=self.provider,
        )

    def get_authorize_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": self.config.scope,
        }

        if state:
            params["state"] = state

        # Add provider-specific parameters
        if self.provider == OAuthProvider.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.authorize_url}?{query}"

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "authorization_code",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "redirect_uri": self.config.redirect_uri,
            }

            headers = {"Accept": "application/json"}

            try:
                response = await client.post(self.config.token_url, data=data, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"OAuth token exchange failed: {str(e)}",
                )

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}

            try:
                response = await client.get(self.config.userinfo_url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to get user info: {str(e)}",
                )

    def normalize_user_info(self, raw_info: Dict[str, Any]) -> Dict[str, str]:
        """Normalize user info from different providers"""
        if self.provider == OAuthProvider.GOOGLE:
            return {
                "email": raw_info.get("email", ""),
                "name": raw_info.get("name", ""),
                "picture": raw_info.get("picture", ""),
                "provider_id": raw_info.get("id", ""),
            }
        elif self.provider == OAuthProvider.GITHUB:
            return {
                "email": raw_info.get("email", ""),
                "name": raw_info.get("name", ""),
                "picture": raw_info.get("avatar_url", ""),
                "provider_id": str(raw_info.get("id", "")),
            }
        elif self.provider == OAuthProvider.MICROSOFT:
            return {
                "email": raw_info.get("mail", raw_info.get("userPrincipalName", "")),
                "name": raw_info.get("displayName", ""),
                "picture": "",
                "provider_id": raw_info.get("id", ""),
            }
        else:
            return {
                "email": raw_info.get("email", ""),
                "name": raw_info.get("name", ""),
                "picture": raw_info.get("picture", ""),
                "provider_id": str(raw_info.get("id", "")),
            }


class OAuthUserManager:
    """Manages OAuth users in the database"""

    def __init__(self, db_session):
        self.db = db_session

    async def get_or_create_oauth_user(
        self,
        provider: OAuthProvider,
        provider_id: str,
        email: str,
        name: str,
        picture: str = "",
    ):
        """Get existing OAuth user or create new one"""
        from database.models import User

        # Try to find existing OAuth user
        user = (
            self.db.query(User)
            .filter(
                User.oauth_provider == provider.value,
                User.oauth_provider_id == provider_id,
            )
            .first()
        )

        if user:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            self.db.commit()
            return user

        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            # Link OAuth to existing account
            existing_user.oauth_provider = provider.value
            existing_user.oauth_provider_id = provider_id
            self.db.commit()
            return existing_user

        # Create new OAuth user
        new_user = User(
            username=email.split("@")[0],
            email=email,
            full_name=name,
            oauth_provider=provider.value,
            oauth_provider_id=provider_id,
            profile_picture=picture,
            is_active=True,
            role="operator",  # Default role for OAuth users
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user


# Factory function
def get_oauth_manager(provider: str) -> OAuthManager:
    """Get OAuth manager for specified provider"""
    try:
        provider_enum = OAuthProvider(provider.lower())
        return OAuthManager(provider_enum)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )


# Environment check
def is_oauth_configured(provider: OAuthProvider) -> bool:
    """Check if OAuth provider is properly configured"""
    prefix = f"OAUTH_{provider.value.upper()}_"
    return bool(os.getenv(f"{prefix}CLIENT_ID") and os.getenv(f"{prefix}CLIENT_SECRET"))


# List available providers
def get_available_providers() -> Dict[str, bool]:
    """Get list of configured OAuth providers"""
    return {provider.value: is_oauth_configured(provider) for provider in OAuthProvider}
