#!/usr/bin/env python3
"""
ChatGPT Direct Backend (Reverse Engineered)
Uses internal WebSocket/HTTP API with session token
Requires manual token extraction once
"""

import logging
import os
import random
import sys
from typing import Optional

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.async_fixes import safe_close_session

logger = logging.getLogger("ZenAI")


class ChatGPTDirectBackend:
    """
    Direct ChatGPT API Backend
    - Uses access token from browser session
    - No browser automation overhead
    - Requires token renewal every 2-4 weeks
    """

    def __init__(self, access_token: str = None):
        self.name = "ChatGPT-Direct"
        self.priority = 3  # Lower priority (requires manual setup)
        self.access_token = access_token
        self.refresh_token = None
        self.conversation_id = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await safe_close_session(self.session)

    async def chat(self, prompt: str, context: str = "") -> Optional[str]:
        """Send chat request via direct API"""
        if not self.access_token:
            logger.warning("[ChatGPT-Direct] No access token provided")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            # Generate unique IDs
            msg_id = str(random.randint(1000000000, 9999999999))
            parent_id = str(random.randint(1000000000, 9999999999))

            payload = {
                "action": "next",
                "messages": [
                    {
                        "id": msg_id,
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [prompt]},
                    }
                ],
                "conversation_id": self.conversation_id,
                "parent_message_id": parent_id,
                "model": "text-davinci-002-render-sha",
                "timezone_offset_min": -120,
                "history_and_training_disabled": False,
            }

            logger.info("[ChatGPT-Direct] Sending request...")

            async with self.session.post(
                "https://chat.openai.com/backend-api/conversation",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 401:
                    logger.error("[ChatGPT-Direct] Token expired!")
                    return None
                elif resp.status == 429:
                    logger.warning("[ChatGPT-Direct] Rate limited")
                    return None
                elif resp.status != 200:
                    logger.error(f"[ChatGPT-Direct] HTTP Error: {resp.status}")
                    return None

                # ChatGPT streams events
                text = await resp.text()
                lines = text.split("\n")

                full_response = ""
                for line in lines:
                    if line.startswith("data: "):
                        try:
                            import json

                            data = json.loads(line[6:])
                            if data.get("message") and data["message"].get("content"):
                                full_response = data["message"]["content"]["parts"][0]
                            # Update conversation ID for context
                            if data.get("conversation_id"):
                                self.conversation_id = data["conversation_id"]
                        except Exception:
                            continue

                return full_response

        except Exception as e:
            logger.error(f"[ChatGPT-Direct] Error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if backend is available"""
        if not self.access_token:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get("https://chat.openai.com/backend-api/models", headers=headers) as resp:
                return resp.status == 200
        except Exception:
            return False
