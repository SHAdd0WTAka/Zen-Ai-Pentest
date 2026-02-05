#!/usr/bin/env python3
"""
DuckDuckGo AI Backend
Free, no authentication required
Supports GPT-4o-mini, Claude-3-haiku, Llama-3.1-70B
"""

import logging
import os
import sys
from typing import Optional

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.async_fixes import safe_close_session

logger = logging.getLogger("ZenAI")


class DuckDuckGoBackend:
    """
    DuckDuckGo AI Chat Backend
    - No API key required
    - ~50-100 requests per day limit
    - Automatic model rotation on rate limit
    """

    def __init__(self):
        self.name = "DuckDuckGo"
        self.priority = 1  # Highest priority (free, fast)
        self.vqd_token = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.models = [
            "gpt-4o-mini",
            "claude-3-haiku",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        ]
        self.current_model = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await safe_close_session(self.session)

    async def _get_vqd_token(self):
        """Get anti-CSRF token from DDG"""
        if self.vqd_token:
            return

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        }

        try:
            async with self.session.get(
                "https://duckduckgo.com/?q=DuckDuckGo+AI+Chat&ia=chat", headers=headers
            ) as resp:
                text = await resp.text()
                if 'vqd="' in text:
                    self.vqd_token = text.split('vqd="')[1].split('"')[0]
                    logger.info(f"[DDG] VQD Token acquired: {self.vqd_token[:10]}...")
        except Exception as e:
            logger.error(f"[DDG] Token acquisition failed: {e}")

    async def chat(self, prompt: str, context: str = "") -> Optional[str]:
        """Send chat request to DuckDuckGo AI"""
        try:
            await self._get_vqd_token()

            if not self.vqd_token:
                return None

            model = self.models[self.current_model % len(self.models)]

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }

            headers = {
                "X-Vqd-4": self.vqd_token,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://duckduckgo.com/",
            }

            logger.info(f"[DDG] Sending to {model}...")

            async with self.session.post(
                "https://duckduckgo.com/duckchat/v1/chat", json=payload, headers=headers
            ) as resp:
                if resp.status == 429:
                    logger.warning("[DDG] Rate limited, rotating model...")
                    self.current_model += 1
                    return None

                if resp.status == 418:
                    logger.warning("[DDG] Teapot error (rate limit or invalid token)")
                    self.vqd_token = None  # Force token refresh
                    return None

                if resp.status != 200:
                    logger.error(f"[DDG] HTTP Error: {resp.status}")
                    return None

                # DDG streams JSON Lines
                full_response = ""
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        try:
                            import json

                            data = json.loads(line[6:])
                            if "message" in data:
                                full_response += data["message"]
                        except Exception:
                            continue

                return full_response

        except Exception as e:
            logger.error(f"[DDG] Error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if backend is available"""
        try:
            await self._get_vqd_token()
            return self.vqd_token is not None
        except Exception:
            return False
