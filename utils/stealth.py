#!/usr/bin/env python3
"""
Stealth and evasion utilities
Author: SHAdd0WTAka
"""

import random
import time


class StealthManager:
    """
    Manage stealth techniques for penetration testing
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]

    REFERERS = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://duckduckgo.com/",
        "https://search.yahoo.com/",
        "https://www.reddit.com/",
    ]

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.delay_min = self.config.get("delay_min", 1)
        self.delay_max = self.config.get("delay_max", 3)
        self.use_random_ua = self.config.get("random_user_agent", True)

    def get_headers(self, custom_headers: dict = None) -> dict:
        """Generate stealthy HTTP headers"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

        if self.use_random_ua:
            headers["User-Agent"] = random.choice(self.USER_AGENTS)

        headers["Referer"] = random.choice(self.REFERERS)

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def delay(self, min_seconds: float = None, max_seconds: float = None):
        """Add random delay between requests"""
        min_sec = min_seconds or self.delay_min
        max_sec = max_seconds or self.delay_max
        time.sleep(random.uniform(min_sec, max_sec))

    def get_random_user_agent(self) -> str:
        """Get random user agent string"""
        return random.choice(self.USER_AGENTS)

    def jitter_delay(self, base_delay: float = 1.0, jitter: float = 0.5):
        """Add jittered delay (base +/- jitter)"""
        delay = base_delay + random.uniform(-jitter, jitter)
        if delay > 0:
            time.sleep(delay)

    def exponential_backoff(self, attempt: int, base_delay: float = 1.0):
        """Exponential backoff for retries"""
        delay = base_delay * (2**attempt) + random.uniform(0, 1)
        time.sleep(delay)
