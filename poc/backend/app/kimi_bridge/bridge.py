"""
Main implementation of Kimi Authentication Bridge
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from .config import KimiConfig
from .exceptions import (
    KimiAuthError,
    KimiNotAuthenticatedError,
    KimiCredentialsNotFoundError,
    KimiInvalidCredentialsError,
    KimiCLINotFoundError,
)


class KimiAuthBridge:
    """
    Synchronous authentication bridge for Kimi CLI
    
    Reads OAuth tokens from Kimi CLI's secure storage and provides
them for use in other applications.
    
    Example:
        >>> bridge = KimiAuthBridge()
        >>> if bridge.is_authenticated():
        ...     headers = bridge.get_auth_headers()
        ...     # Use headers with requests library
    
    Args:
        config: Optional KimiConfig instance for custom configuration
    """
    
    def __init__(self, config: Optional[KimiConfig] = None):
        self.config = config or KimiConfig()
    
    def _load_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Load credentials from Kimi CLI storage
        
        Returns:
            Dict containing credentials or None if not found
            
        Raises:
            KimiCredentialsNotFoundError: If credentials file doesn't exist
            KimiInvalidCredentialsError: If credentials file is invalid JSON
        """
        creds_path = self.config.credentials_path
        
        if not creds_path or not creds_path.exists():
            return None
        
        try:
            with open(creds_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise KimiInvalidCredentialsError(f"Invalid JSON in credentials file: {e}")
        except IOError as e:
            raise KimiCredentialsNotFoundError(str(creds_path))
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated with Kimi CLI
        
        Returns:
            True if valid credentials exist, False otherwise
        """
        try:
            creds = self._load_credentials()
            if not creds:
                return False
            
            # Check if access_token exists and is not empty
            access_token = creds.get('access_token')
            return access_token is not None and len(access_token) > 0
        except (KimiCredentialsNotFoundError, KimiInvalidCredentialsError):
            return False
    
    def get_access_token(self) -> Optional[str]:
        """
        Get the current access token
        
        Returns:
            Access token string or None if not authenticated
            
        Example:
            >>> bridge = KimiAuthBridge()
            >>> token = bridge.get_access_token()
            >>> if token:
            ...     headers = {"Authorization": f"Bearer {token}"}
        """
        try:
            creds = self._load_credentials()
            if not creds:
                return None
            return creds.get('access_token')
        except (KimiCredentialsNotFoundError, KimiInvalidCredentialsError):
            return None
    
    def get_token_preview(self, length: int = 20) -> Optional[str]:
        """
        Get a truncated version of the token for display purposes
        
        Args:
            length: Number of characters to show
            
        Returns:
            Truncated token string ending with "..." or None
            
        Example:
            >>> bridge.get_token_preview(10)
            'eyJhbGciOi...'
        """
        token = self.get_access_token()
        if token and len(token) > length:
            return f"{token[:length]}..."
        return token
    
    def get_refresh_token(self) -> Optional[str]:
        """
        Get the refresh token if available
        
        Returns:
            Refresh token string or None
        """
        try:
            creds = self._load_credentials()
            if not creds:
                return None
            return creds.get('refresh_token')
        except (KimiCredentialsNotFoundError, KimiInvalidCredentialsError):
            return None
    
    def get_api_base(self) -> str:
        """
        Get the Kimi API base URL
        
        Returns:
            API base URL string
        """
        return self.config.api_base
    
    def get_default_model(self) -> str:
        """
        Get the default model name
        
        Returns:
            Model name string
        """
        return self.config.model
    
    def get_user_agent(self) -> str:
        """
        Get the User-Agent header required for API requests
        
        Returns:
            User-Agent string
        """
        return self.config.user_agent
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get complete authentication headers for API requests
        
        Returns:
            Dictionary with Authorization and User-Agent headers
            
        Raises:
            KimiNotAuthenticatedError: If user is not authenticated
            
        Example:
            >>> headers = bridge.get_auth_headers()
            >>> requests.post(url, headers=headers, json=data)
        """
        token = self.get_access_token()
        
        if not token:
            raise KimiNotAuthenticatedError()
        
        return {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.config.user_agent,
            "Content-Type": "application/json",
        }
    
    def require_auth(self, func):
        """
        Decorator to require authentication for a function
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function that checks auth before execution
            
        Example:
            >>> @bridge.require_auth
            ... def make_api_call():
            ...     # This will only run if authenticated
            ...     pass
        """
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                raise KimiNotAuthenticatedError()
            return func(*args, **kwargs)
        return wrapper


class AsyncKimiAuthBridge(KimiAuthBridge):
    """
    Asynchronous authentication bridge for Kimi CLI
    
    Same functionality as KimiAuthBridge but with async support
    for non-blocking operations.
    
    Example:
        >>> bridge = AsyncKimiAuthBridge()
        >>> if await bridge.is_authenticated():
        ...     token = await bridge.get_access_token()
    """
    
    async def is_authenticated(self) -> bool:
        """Async version of is_authenticated"""
        return super().is_authenticated()
    
    async def get_access_token(self) -> Optional[str]:
        """Async version of get_access_token"""
        return super().get_access_token()
    
    async def get_token_preview(self, length: int = 20) -> Optional[str]:
        """Async version of get_token_preview"""
        return super().get_token_preview(length)
    
    async def get_refresh_token(self) -> Optional[str]:
        """Async version of get_refresh_token"""
        return super().get_refresh_token()
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Async version of get_auth_headers"""
        creds = self._load_credentials()
        if not creds:
            raise KimiNotAuthenticatedError("Not authenticated. Please run 'kimi login' first.")
        return {"Authorization": f"Bearer {creds.get('access_token', '')}"}
    
    async def login(self) -> bool:
        """
        Trigger Kimi CLI login flow
        
        Returns:
            True if login was successful, False otherwise
            
        Raises:
            KimiCLINotFoundError: If kimi CLI is not installed
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "kimi", "login",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise KimiAuthError(f"Login failed: {error_msg}")
                
        except FileNotFoundError:
            raise KimiCLINotFoundError()
    
    async def logout(self) -> bool:
        """
        Trigger Kimi CLI logout
        
        Returns:
            True if logout was successful, False otherwise
            
        Raises:
            KimiCLINotFoundError: If kimi CLI is not installed
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "kimi", "logout",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            return proc.returncode == 0
            
        except FileNotFoundError:
            raise KimiCLINotFoundError()
