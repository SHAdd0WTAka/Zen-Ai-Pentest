#!/usr/bin/env python3
"""
OAuth2 Device Code Flow for Kimi AI Authentication
Similar to 'gh auth login'
"""

import asyncio
import time
import webbrowser
from typing import Any, Dict, Optional

import aiohttp


class DeviceCodeFlow:
    """OAuth2 Device Authorization Grant implementation"""

    # Kimi AI OAuth endpoints (placeholder - update with actual endpoints when available)
    DEVICE_AUTHORIZATION_ENDPOINT = "https://api.moonshot.cn/v1/oauth/device/code"
    TOKEN_ENDPOINT = "https://api.moonshot.cn/v1/oauth/token"

    def __init__(self, client_id: str = "zen-ai-pentest-cli"):
        self.client_id = client_id
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def initiate_device_flow(self) -> Dict[str, Any]:
        """
        Step 1: Request device code from authorization server

        Returns:
            Dict containing device_code, user_code, verification_uri, etc.
        """
        payload = {"client_id": self.client_id, "scope": "api offline_access"}  # offline_access for refresh token

        try:
            async with self.session.post(
                self.DEVICE_AUTHORIZATION_ENDPOINT, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise AuthenticationError(f"Device code request failed: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error: {e}")

    async def poll_for_token(self, device_code: str, interval: int = 5, timeout: int = 600) -> Dict[str, Any]:
        """
        Step 2: Poll token endpoint until user authorizes

        Args:
            device_code: The device code from step 1
            interval: Polling interval in seconds
            timeout: Maximum time to wait in seconds

        Returns:
            Dict containing access_token, refresh_token, etc.
        """
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self.client_id,
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                async with self.session.post(
                    self.TOKEN_ENDPOINT, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    data = await response.json()

                    if response.status == 200:
                        return data

                    error = data.get("error", "")

                    if error == "authorization_pending":
                        # User hasn't authorized yet, continue polling
                        await asyncio.sleep(interval)
                        continue
                    elif error == "slow_down":
                        # Server requests slower polling
                        interval += 5
                        await asyncio.sleep(interval)
                        continue
                    elif error == "expired_token":
                        raise AuthenticationError("Device code expired. Please run 'zen auth login' again.")
                    elif error == "access_denied":
                        raise AuthenticationError("Access denied by user.")
                    else:
                        raise AuthenticationError(f"Token request failed: {error}")

            except aiohttp.ClientError as e:
                raise AuthenticationError(f"Network error during polling: {e}")

        raise AuthenticationError("Authentication timed out. Please try again.")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token

        Args:
            refresh_token: The refresh token

        Returns:
            Dict containing new access_token and refresh_token
        """
        payload = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": self.client_id}

        try:
            async with self.session.post(
                self.TOKEN_ENDPOINT, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise AuthenticationError(f"Token refresh failed: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error during refresh: {e}")

    def open_browser(self, url: str) -> bool:
        """Open browser for user to authorize"""
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False


class AuthenticationError(Exception):
    """Authentication-related errors"""

    pass


# Fallback: API Key authentication for providers without OAuth
class APIKeyAuth:
    """Simple API Key authentication as fallback"""

    @staticmethod
    def validate_key(key: str, provider: str = "kimi") -> bool:
        """Validate API key format"""
        if not key or len(key) < 10:
            return False

        if provider == "kimi":
            # Kimi keys start with specific prefixes
            return key.startswith(("sk-", "Bearer "))

        return True
