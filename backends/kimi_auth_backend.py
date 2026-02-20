#!/usr/bin/env python3
"""
Kimi AI Backend with OAuth Token Support
Uses stored credentials from 'zen auth login'
"""

import logging
import os
import sys
from typing import AsyncGenerator, Optional

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth.device_flow import DeviceCodeFlow
from core.auth.token_store import TokenStore, get_stored_token

logger = logging.getLogger("ZenAI.Kimi")


class KimiAuthBackend:
    """
    Kimi AI Backend with automatic OAuth token handling
    - Uses stored token from 'zen auth login'
    - Auto-refreshes expired tokens
    - Falls back to API key if available
    """

    API_BASE = "https://api.moonshot.cn/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.name = "Kimi"
        self.priority = 2  # High priority (good quality)
        self.session: Optional[aiohttp.ClientSession] = None
        self.token_store = TokenStore()
        self._api_key = api_key

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_auth_token(self) -> Optional[str]:
        """Get authentication token from store or env"""
        # Priority: 1. Env var, 2. Stored token, 3. Constructor param
        env_key = os.environ.get("KIMI_API_KEY")
        if env_key:
            return env_key

        stored = get_stored_token()
        if stored:
            return stored

        return self._api_key

    async def _refresh_token_if_needed(self) -> bool:
        """Refresh token if expired"""
        refresh_token = self.token_store.get_refresh_token()
        if not refresh_token:
            return False

        try:
            async with DeviceCodeFlow() as flow:
                new_tokens = await flow.refresh_access_token(refresh_token)

                self.token_store.save_credentials(
                    access_token=new_tokens["access_token"],
                    refresh_token=new_tokens.get("refresh_token", refresh_token),
                    expires_in=new_tokens.get("expires_in"),
                    provider="kimi",
                )
                logger.info("Token refreshed successfully")
                return True
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            return False

    async def chat(self, message: str, model: str = "kimi-k2-07132k-preview") -> str:
        """
        Send chat message to Kimi AI

        Args:
            message: User message
            model: Model to use

        Returns:
            AI response text
        """
        token = self._get_auth_token()

        if not token:
            raise AuthenticationRequiredError("Not authenticated. Please run 'zen auth login' or set KIMI_API_KEY")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        payload = {"model": model, "messages": [{"role": "user", "content": message}], "temperature": 0.7, "max_tokens": 4096}

        try:
            async with self.session.post(f"{self.API_BASE}/chat/completions", headers=headers, json=payload) as response:
                if response.status == 401:
                    # Token expired, try refresh
                    if await self._refresh_token_if_needed():
                        # Retry with new token
                        return await self.chat(message, model)
                    else:
                        raise AuthenticationRequiredError("Token expired. Please run 'zen auth login' again.")

                response.raise_for_status()
                data = await response.json()
                return data["choices"][0]["message"]["content"]

        except aiohttp.ClientError as e:
            logger.error(f"Kimi API error: {e}")
            raise

    async def chat_stream(self, message: str, model: str = "kimi-k2-07132k-preview") -> AsyncGenerator[str, None]:
        """Stream chat response from Kimi AI"""
        token = self._get_auth_token()

        if not token:
            raise AuthenticationRequiredError("Not authenticated. Please run 'zen auth login'")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        payload = {"model": model, "messages": [{"role": "user", "content": message}], "stream": True, "temperature": 0.7}

        try:
            async with self.session.post(f"{self.API_BASE}/chat/completions", headers=headers, json=payload) as response:
                if response.status == 401:
                    if await self._refresh_token_if_needed():
                        async for chunk in self.chat_stream(message, model):
                            yield chunk
                        return
                    else:
                        raise AuthenticationRequiredError("Token expired")

                response.raise_for_status()

                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json

                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError):
                            continue

        except aiohttp.ClientError as e:
            logger.error(f"Kimi streaming error: {e}")
            raise

    def is_configured(self) -> bool:
        """Check if backend is properly configured"""
        return self._get_auth_token() is not None


class AuthenticationRequiredError(Exception):
    """Raised when authentication is required but not available"""

    pass


# Convenience function for quick usage
def create_kimi_backend():
    """Create Kimi backend with stored credentials"""
    return KimiAuthBackend()
