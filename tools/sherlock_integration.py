"""
Sherlock Integration - Social Media OSINT
Findet Benutzernamen auf über 400 Social Media Plattformen
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SherlockResult:
    """Sherlock scan result"""
    username: str
    found_sites: List[Dict[str, str]] = field(default_factory=list)
    not_found_sites: List[str] = field(default_factory=list)
    total_sites: int = 0
    success: bool = False
    error: Optional[str] = None


class SherlockIntegration:
    """
    Sherlock Social Media OSINT Integration
    
    Unterstützt 400+ Plattformen:
    - Twitter/X, Instagram, Facebook, LinkedIn
    - GitHub, GitLab, Bitbucket
    - Reddit, TikTok, YouTube
    - Und viele mehr...
    """
    
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        
    async def search(self, username: str, sites: Optional[List[str]] = None) -> SherlockResult:
        """
        Search username across social media platforms
        
        Args:
            username: Username to search
            sites: Specific sites to check (None = all)
            
        Returns:
            SherlockResult with findings
        """
        cmd = ["sherlock", username, "--json", "-o", "-"]
        
        if sites:
            for site in sites:
                cmd.extend(["--site", site])
                
        logger.info(f"Starting Sherlock search: {' '.join(cmd)}")
        
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
            
            found_sites = []
            not_found_sites = []
            
            # Parse JSON output
            try:
                output = stdout.decode().strip()
                if output:
                    data = json.loads(output)
                    
                    for site_name, site_data in data.items():
                        if isinstance(site_data, dict):
                            status = site_data.get("status", {})
                            if status.get("status") == "FOUND":
                                found_sites.append({
                                    "site": site_name,
                                    "url": site_data.get("url_user", ""),
                                    "status": "found"
                                })
                            else:
                                not_found_sites.append(site_name)
                        elif site_data == "FOUND":
                            found_sites.append({
                                "site": site_name,
                                "url": f"https://{site_name}.com/{username}",
                                "status": "found"
                            })
                            
            except json.JSONDecodeError:
                # Fallback: parse line by line
                for line in stdout.decode().split('\n'):
                    if '[+]' in line and 'Found' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            site = parts[1].replace(':', '')
                            url = parts[-1]
                            found_sites.append({"site": site, "url": url, "status": "found"})
                            
            return SherlockResult(
                username=username,
                found_sites=found_sites,
                not_found_sites=not_found_sites,
                total_sites=len(found_sites) + len(not_found_sites),
                success=True
            )
            
        except asyncio.TimeoutError:
            logger.error("Sherlock search timed out")
            return SherlockResult(username=username, success=False, error="Timeout")
        except Exception as e:
            logger.error(f"Sherlock error: {e}")
            return SherlockResult(username=username, success=False, error=str(e))
            
    async def search_multiple(self, usernames: List[str]) -> Dict[str, SherlockResult]:
        """
        Search multiple usernames
        
        Args:
            usernames: List of usernames to search
            
        Returns:
            Dictionary with results for each username
        """
        results = {}
        for username in usernames:
            results[username] = await self.search(username)
        return results


# Sync wrapper
def search_sync(username: str) -> SherlockResult:
    """Synchronous wrapper for Sherlock search"""
    sherlock = SherlockIntegration()
    return asyncio.run(sherlock.search(username))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Sherlock Integration...")
    print("="*60)
    
    # Test with a common username
    result = search_sync("admin")
    
    print(f"Username: {result.username}")
    print(f"Success: {result.success}")
    print(f"Found on {len(result.found_sites)} sites:")
    for site in result.found_sites[:10]:
        print(f"  ✓ {site['site']}: {site['url']}")
