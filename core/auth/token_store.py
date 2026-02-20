#!/usr/bin/env python3
"""
Secure token storage for Zen-AI-Pentest
Stores credentials in OS-specific secure locations
"""

import json
import os
import stat
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


class TokenStore:
    """Secure storage for authentication tokens"""

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.credentials_file = self.config_dir / "credentials.json"
        self._ensure_config_dir()

    def _get_config_dir(self) -> Path:
        """Get OS-specific config directory"""
        if os.name == "nt":  # Windows
            config_root = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
            config_dir = config_root / "zen-ai-pentest"
        else:  # Linux/macOS
            config_root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
            config_dir = config_root / "zen-ai-pentest"

        return config_dir

    def _ensure_config_dir(self):
        """Create config directory with secure permissions"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions (owner only)
        if os.name != "nt":
            os.chmod(self.config_dir, stat.S_IRWXU)  # 700

    def save_credentials(
        self, access_token: str, refresh_token: Optional[str] = None, expires_in: Optional[int] = None, provider: str = "kimi"
    ):
        """
        Save credentials securely

        Args:
            access_token: The access token
            refresh_token: Optional refresh token
            expires_in: Token expiration time in seconds
            provider: The authentication provider
        """
        expires_at = None
        if expires_in:
            expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

        credentials = {
            "version": 1,
            "provider": provider,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Write with restricted permissions
        temp_file = self.credentials_file.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(credentials, f, indent=2)

        # Set restrictive permissions before moving
        if os.name != "nt":
            os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)  # 600

        # Atomic move
        temp_file.replace(self.credentials_file)

    def load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load stored credentials"""
        if not self.credentials_file.exists():
            return None

        try:
            with open(self.credentials_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def get_access_token(self) -> Optional[str]:
        """Get current access token if valid"""
        creds = self.load_credentials()
        if not creds:
            return None

        # Check if token is expired
        expires_at = creds.get("expires_at")
        if expires_at:
            expiry = datetime.fromisoformat(expires_at)
            # Refresh if expires in less than 5 minutes
            if datetime.utcnow() > expiry - timedelta(minutes=5):
                return None  # Signal to refresh

        return creds.get("access_token")

    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token"""
        creds = self.load_credentials()
        if creds:
            return creds.get("refresh_token")
        return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get_access_token() is not None

    def clear_credentials(self):
        """Remove stored credentials (logout)"""
        if self.credentials_file.exists():
            self.credentials_file.unlink()

    def get_auth_headers(self) -> Dict[str, str]:
        """Get HTTP headers for authenticated requests"""
        token = self.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def get_credential_path(self) -> str:
        """Get path to credentials file (for display)"""
        return str(self.credentials_file)


# Helper functions for CLI


def get_stored_token() -> Optional[str]:
    """Get token from store (convenience function)"""
    store = TokenStore()
    return store.get_access_token()


def is_logged_in() -> bool:
    """Check if user is logged in (convenience function)"""
    store = TokenStore()
    return store.is_authenticated()


def require_auth(func):
    """Decorator to require authentication for CLI commands"""

    def wrapper(*args, **kwargs):
        if not is_logged_in():
            print("❌ Not authenticated. Please run: zen auth login")
            return 1
        return func(*args, **kwargs)

    return wrapper
