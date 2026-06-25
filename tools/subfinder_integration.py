"""
Subfinder Integration - Subdomain Discovery
Schnelle Subdomain-Enumeration mit Subfinder
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SubfinderResult:
    """Subfinder scan result"""

    success: bool
    domain: str = ""
    subdomains: List[str] = field(default_factory=list)
    count: int = 0
    error: Optional[str] = None
    duration: float = 0.0


class SubfinderIntegration:
    """Subfinder Subdomain Discovery"""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    async def enumerate(self, domain: str, recursive: bool = False) -> SubfinderResult:
        """
        Enumerate subdomains for a domain

        Args:
            domain: Target domain (e.g., example.com)
            recursive: Enable recursive subdomain discovery

        Returns:
            SubfinderResult with found subdomains
        """
        import time

        start_time = time.time()

        cmd = ["subfinder", "-d", domain, "-json", "-silent"]

        if recursive:
            cmd.append("-recursive")

        logger.info(f"Starting Subfinder enumeration: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            subdomains = []

            # Parse JSON output (one JSON object per line)
            for line in stdout.decode().strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    host = data.get("host", "")
                    if host:
                        subdomains.append(host)
                except json.JSONDecodeError:
                    # Fallback: treat as plain text; skip log lines starting with [
                    stripped = line.strip()
                    if stripped and not stripped.startswith("["):
                        subdomains.append(stripped)

            duration = time.time() - start_time
            unique_subdomains = sorted(set(subdomains))

            return SubfinderResult(
                success=True,
                domain=domain,
                subdomains=unique_subdomains,
                count=len(unique_subdomains),
                duration=duration,
            )

        except asyncio.TimeoutError:
            logger.error("Subfinder enumeration timed out")
            return SubfinderResult(success=False, domain=domain, error="Timeout")
        except Exception as e:
            logger.error(f"Subfinder error: {e}")
            return SubfinderResult(success=False, domain=domain, error=str(e))


# Sync wrapper
def enumerate_sync(domain: str, recursive: bool = False) -> SubfinderResult:
    """Synchronous wrapper for subdomain enumeration"""
    subfinder = SubfinderIntegration()
    return asyncio.run(subfinder.enumerate(domain, recursive))


# Alias for tool registry compatibility
subfinder_scan = enumerate_sync


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    logger.info("Testing Subfinder Integration...")
    logger.info("=" * 60)

    result = enumerate_sync("scanme.nmap.org")

    logger.info(f"Success: {result.success}")
    logger.info(f"Domain: {result.domain}")
    logger.info(f"Found {result.count} subdomains:")
    for subdomain in result.subdomains[:10]:
        logger.info(f"  • {subdomain}")
    if len(result.subdomains) > 10:
        logger.info(f"  ... and {len(result.subdomains) - 10} more")
