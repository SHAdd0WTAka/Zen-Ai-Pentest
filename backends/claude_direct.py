#!/usr/bin/env python3
"""
Claude Direct Backend (Reverse Engineered)
Uses internal API for Claude.ai
Requires session cookie extraction
"""

import logging
import os
import sys
from typing import Optional

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.async_fixes import safe_close_session

logger = logging.getLogger("ZenAI")


class ClaudeDirectBackend:
    """
    Direct Claude API Backend
    - Uses session key from browser
    - Optimized for long-form analysis
    - Good for code review and complex reasoning
    """

    def __init__(self, session_key: str = None):
        self.name = "Claude-Direct"
        self.priority = 3
        self.session_key = session_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await safe_close_session(self.session)

    async def chat(self, prompt: str, context: str = "") -> Optional[str]:
        """Send chat request to Claude"""
        if not self.session_key:
            logger.warning("[Claude-Direct] No session key provided")
            return None

        try:
            headers = {
                "Cookie": f"sessionKey={self.session_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/event-stream",
            }

            # Organization ID required for Claude
            org_id = await self._get_org_id()
            if not org_id:
                logger.error("[Claude-Direct] Could not get organization ID")
                return None

            payload = {
                "prompt": prompt,
                "model": "claude-3-5-sonnet-20241022",
                "timezone": "Europe/Berlin",
                "attachments": [],
            }

            logger.info("[Claude-Direct] Sending request...")

            async with self.session.post(
                f"https://claude.ai/api/organizations/{org_id}/chat_conversations",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 401:
                    logger.error("[Claude-Direct] Session expired")
                    return None
                elif resp.status != 200:
                    logger.error(f"[Claude-Direct] HTTP Error: {resp.status}")
                    return None

                # Claude uses SSE (Server-Sent Events)
                full_response = ""
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        try:
                            import json

                            data = json.loads(line[6:])
                            if data.get("completion"):
                                full_response += data["completion"]
                        except Exception:
                            continue

                return full_response

        except Exception as e:
            logger.error(f"[Claude-Direct] Error: {e}")
            return None

    async def _get_org_id(self) -> Optional[str]:
        """Get organization ID from session"""
        try:
            headers = {
                "Cookie": f"sessionKey={self.session_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            async with self.session.get("https://claude.ai/api/organizations", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and len(data) > 0:
                        return data[0].get("uuid")
                return None
        except Exception:
            return None

    async def health_check(self) -> bool:
        """Check if backend is available"""
        if not self.session_key:
            return False
        return await self._get_org_id() is not None
