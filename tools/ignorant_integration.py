"""
Ignorant Integration - Email OSINT
Überprüft Email-Adressen auf 120+ Plattformen
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IgnorantCheck:
    """Single platform check result"""
    platform: str
    exists: bool
    url: str = ""
    error: Optional[str] = None


@dataclass
class IgnorantResult:
    """Ignorant email check result"""
    email: str
    username: str
    domain: str
    found_platforms: List[IgnorantCheck] = field(default_factory=list)
    not_found_platforms: List[str] = field(default_factory=list)
    total_checked: int = 0
    success: bool = False
    error: Optional[str] = None


class IgnorantIntegration:
    """
    Ignorant Email OSINT Integration

    Unterstützt 120+ Plattformen:
    - Instagram, Twitter, Snapchat
    - GitHub, GitLab
    - Spotify, Netflix
    - Und viele mehr...
    """

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    async def check_email(self, email: str) -> IgnorantResult:
        """
        Check email address across platforms

        Args:
            email: Email address to check

        Returns:
            IgnorantResult with findings
        """
        # Parse email
        if '@' not in email:
            return IgnorantResult(
                email=email,
                username=email,
                domain="",
                success=False,
                error="Invalid email format"
            )

        username, domain = email.rsplit('@', 1)

        cmd = ["ignorant", email, "--json"]

        logger.info(f"Starting Ignorant check for: {email}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            found_platforms = []
            not_found_platforms = []

            # Parse JSON output
            try:
                output = stdout.decode().strip()
                if output:
                    lines = output.split('\n')
                    for line in lines:
                        if not line:
                            continue
                        try:
                            data = json.loads(line)

                            if data.get("exists") is True:
                                found_platforms.append(IgnorantCheck(
                                    platform=data.get("name", "Unknown"),
                                    exists=True,
                                    url=data.get("url", "")
                                ))
                            else:
                                not_found_platforms.append(data.get("name", "Unknown"))
                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.warning(f"Parse error: {e}")

            return IgnorantResult(
                email=email,
                username=username,
                domain=domain,
                found_platforms=found_platforms,
                not_found_platforms=not_found_platforms,
                total_checked=len(found_platforms) + len(not_found_platforms),
                success=True
            )

        except asyncio.TimeoutError:
            logger.error("Ignorant check timed out")
            return IgnorantResult(
                email=email,
                username=username,
                domain=domain,
                success=False,
                error="Timeout"
            )
        except Exception as e:
            logger.error(f"Ignorant error: {e}")
            return IgnorantResult(
                email=email,
                username=username,
                domain=domain,
                success=False,
                error=str(e)
            )

    async def check_emails(self, emails: List[str]) -> Dict[str, IgnorantResult]:
        """
        Check multiple email addresses

        Args:
            emails: List of email addresses

        Returns:
            Dictionary with results for each email
        """
        results = {}
        for email in emails:
            results[email] = await self.check_email(email)
        return results


# Sync wrapper
def check_email_sync(email: str) -> IgnorantResult:
    """Synchronous wrapper for email check"""
    ignorant = IgnorantIntegration()
    return asyncio.run(ignorant.check_email(email))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Testing Ignorant Integration...")
    print("="*60)

    # Test with a sample email
    result = check_email_sync("test@example.com")

    print(f"Email: {result.email}")
    print(f"Username: {result.username}")
    print(f"Domain: {result.domain}")
    print(f"Success: {result.success}")
    print(f"Found on {len(result.found_platforms)} platforms")
    for platform in result.found_platforms[:5]:
        print(f"  ✓ {platform.platform}: {platform.url}")
