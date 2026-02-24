#!/usr/bin/env python3
"""
OpenRouter Backend
One API key, many free models
Supports multiple LLMs through unified API
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


class OpenRouterBackend:
    """
    OpenRouter API Backend
    - Single key access to multiple models
    - Generous free tier with rate limits
    - Automatic model rotation
    """

    def __init__(self, api_key: str = None):
        self.name = "OpenRouter"
        self.priority = 2  # Medium priority (requires key)
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

        # Free tier models
        self.models = [
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemini-flash-1.5:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "nvidia/llama-3.1-nemotron-70b-instruct:free",
        ]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await safe_close_session(self.session)

    async def chat(self, prompt: str, context: str = "") -> Optional[str]:
        """Send chat request to OpenRouter"""
        if not self.api_key:
            logger.warning("[OpenRouter] No API key provided")
            return None

        try:
            model = random.choice(self.models)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost",
                "X-Title": "ZenAI-Pentest",
            }

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert and penetration testing assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }

            logger.info(f"[OpenRouter] Using {model}...")

            async with self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status == 429:
                    logger.warning("[OpenRouter] Rate limit hit")
                    return None
                elif resp.status == 401:
                    logger.error("[OpenRouter] Invalid API key")
                    return None
                elif resp.status != 200:
                    logger.error(f"[OpenRouter] HTTP Error: {resp.status}")
                    return None

                data = await resp.json()

                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]

                return None

        except Exception as e:
            logger.error(f"[OpenRouter] Error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if backend is available"""
        if not self.api_key:
            return False
        try:
            # Try a simple request
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with self.session.get(
                "https://openrouter.ai/api/v1/auth/key", headers=headers
            ) as resp:
                return resp.status == 200
        except Exception:
            return False
