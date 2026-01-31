"""
Context Compressor - Uses small local LLM for fact extraction
Reduces noise before sending to expensive LLMs (GPT-4, Claude)
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Result of compression operation"""

    compressed_text: str
    original_length: int
    compressed_length: int
    compression_ratio: float
    method: str  # 'llm' or 'fallback'
    tokens_saved: int


class ContextCompressor:
    """
    Compresses tool output to relevant facts using small local LLM.
    Falls back to heuristics if LLM is unavailable.
    """

    # Strict system prompt for deterministic output
    SYSTEM_PROMPT = """You are a data compressor for security scan outputs.

TASK: Reduce input to facts relevant for penetration testing analysis.

RULES:
- REMOVE: timestamps, color codes, ASCII art, verbose banners, duplicate lines
- KEEP: ports, services, versions, error messages, HTTP status codes, file paths, vulnerabilities
- FORMAT: Bullet points, one fact per line
- MAXIMUM OUTPUT: 500 tokens
- BE CONCISE: Remove filler words, keep technical data

EXAMPLE INPUT:
```
Starting Nmap 7.94 ( https://nmap.org ) at 2024-01-15 10:30:45 UTC
Nmap scan report for 192.168.1.1
Host is up (0.0032s latency).
Not shown: 995 closed tcp ports (reset)
PORT    STATE SERVICE
22/tcp  open  ssh
80/tcp  open  http
443/tcp open  https
```

EXAMPLE OUTPUT:
- Target: 192.168.1.1 (up, 3.2ms latency)
- Open ports: 22/ssh, 80/http, 443/https
- 995 ports filtered
"""

    # Tool-specific extraction rules
    TOOL_PATTERNS = {
        "nmap": [
            r"Host is up",
            r"\d+/\w+\s+open",
            r"Service Info:",
            r"OS:",
            r"PORT\s+STATE\s+SERVICE",
        ],
        "nuclei": [
            r"\[.*?\]",
            r"\[.*?:.*\]",
        ],
        "sqlmap": [
            r"Parameter:",
            r"Type:",
            r"Title:",
            r"Payload:",
        ],
        "gobuster": [
            r"/\S+\s+\(Status:\s+\d+\)",
            r"\[\+\]",
        ],
    }

    # Keywords that indicate important lines
    IMPORTANT_KEYWORDS = [
        "open",
        "vulnerable",
        "vulnerability",
        "exploit",
        "error",
        "failed",
        "unauthorized",
        "forbidden",
        "200",
        "401",
        "403",
        "404",
        "500",
        "502",
        "503",
        "version",
        "server:",
        "x-powered-by",
        "set-cookie",
        "admin",
        "root",
        "password",
        "backup",
        "config",
        "critical",
        "high",
        "medium",
        "warning",
        "sql",
        "injection",
        "xss",
        "csrf",
        "rce",
    ]

    def __init__(self, small_llm_endpoint: str = "http://localhost:8001"):
        """
        Initialize compressor

        Args:
            small_llm_endpoint: URL of small local LLM (Phi-3, TinyLlama, etc.)
        """
        self.endpoint = small_llm_endpoint
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def compress(
        self,
        raw: str,
        source_tool: str = "unknown",
        max_output_tokens: int = 500,
        max_input_chars: int = 8000,
    ) -> CompressionResult:
        """
        Compress raw tool output

        Args:
            raw: Raw tool output
            source_tool: Name of source tool (nmap, nuclei, etc.)
            max_output_tokens: Maximum output tokens
            max_input_chars: Maximum input characters

        Returns:
            CompressionResult with compressed text and metadata
        """
        original_length = len(raw)

        # Hard limit on input
        if len(raw) > max_input_chars:
            raw = raw[:max_input_chars] + "\n... [truncated]"

        # Pre-clean: Remove obvious noise
        cleaned = self._pre_clean(raw)

        # Try small LLM first
        if await self._healthcheck():
            try:
                compressed = await self._llm_compress(cleaned, max_output_tokens)
                compressed_length = len(compressed)
                ratio = (
                    compressed_length / original_length if original_length > 0 else 1.0
                )

                # Estimate tokens saved (rough approximation)
                tokens_saved = (original_length - compressed_length) // 4

                return CompressionResult(
                    compressed_text=compressed,
                    original_length=original_length,
                    compressed_length=compressed_length,
                    compression_ratio=ratio,
                    method="llm",
                    tokens_saved=max(0, tokens_saved),
                )
            except Exception as e:
                logger.warning(f"LLM compression failed: {e}, using fallback")

        # Fallback to heuristic compression
        compressed = self._fallback_compress(cleaned, source_tool)
        compressed_length = len(compressed)
        ratio = compressed_length / original_length if original_length > 0 else 1.0
        tokens_saved = (original_length - compressed_length) // 4

        return CompressionResult(
            compressed_text=compressed,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=ratio,
            method="fallback",
            tokens_saved=max(0, tokens_saved),
        )

    def _pre_clean(self, text: str) -> str:
        """Remove obvious noise before compression"""
        # Remove ANSI color codes
        text = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)

        # Remove carriage returns
        text = text.replace("\r\n", "\n")

        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove progress bars (common pattern)
        text = re.sub(r"[=]+\s*\d+%\s*[=]+", "", text)

        # Remove spinner characters
        text = re.sub(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]", "", text)

        return text.strip()

    async def _llm_compress(self, text: str, max_tokens: int) -> str:
        """Use small local LLM for compression"""
        if not self.session:
            raise RuntimeError("Session not initialized")

        payload = {
            "model": "phi-3-mini",
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Input:\n{text}\n\nOutput:"},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,  # Deterministic
            "top_p": 0.1,
        }

        async with self.session.post(
            f"{self.endpoint}/v1/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"LLM returned {resp.status}")

            result = await resp.json()
            return result["choices"][0]["message"]["content"]

    def _fallback_compress(self, text: str, source_tool: str) -> str:
        """
        Heuristic compression when LLM is unavailable
        Simple but effective rule-based extraction
        """
        lines = text.split("\n")
        filtered = []

        # Get tool-specific patterns
        tool_patterns = self.TOOL_PATTERNS.get(source_tool.lower(), [])

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Keep lines matching important patterns
            if any(
                re.search(pattern, line, re.IGNORECASE) for pattern in tool_patterns
            ):
                filtered.append(line)
                continue

            # Keep lines with important keywords
            if any(keyword in line.lower() for keyword in self.IMPORTANT_KEYWORDS):
                filtered.append(line)
                continue

            # Keep lines that look like data (contain numbers, IPs, paths)
            if self._looks_like_data(line):
                filtered.append(line)

        # Hard cap on output
        if len(filtered) > 100:
            filtered = filtered[:100]
            filtered.append(f"... [{len(lines) - 100} more lines omitted]")

        return "\n".join(filtered)

    def _looks_like_data(self, line: str) -> bool:
        """Check if line looks like it contains useful data"""
        # Contains IP address
        if re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", line):
            return True

        # Contains URL/path
        if re.search(r"https?://|/\w+/", line):
            return True

        # Contains version numbers
        if re.search(r"\d+\.\d+(\.\d+)?", line):
            return True

        # Contains port numbers
        if re.search(r":\d{2,5}\b", line):
            return True

        return False

    async def _healthcheck(self) -> bool:
        """Check if small LLM is available"""
        if not self.session:
            return False

        try:
            async with self.session.get(
                f"{self.endpoint}/health", timeout=aiohttp.ClientTimeout(total=2)
            ) as resp:
                return resp.status == 200
        except Exception:
            return False
