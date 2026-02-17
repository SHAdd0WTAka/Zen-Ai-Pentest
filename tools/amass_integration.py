"""
Amass Integration - Advanced Subdomain Enumeration
Die umfassendste Subdomain-Enumeration
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AmassResult:
    """Amass enumeration result"""
    success: bool
    domain: str = ""
    subdomains: List[str] = field(default_factory=list)
    count: int = 0
    error: Optional[str] = None
    duration: float = 0.0


class AmassIntegration:
    """Amass Advanced Subdomain Enumeration"""
    
    def __init__(self, timeout: int = 600):
        self.timeout = timeout
        
    async def enumerate(
        self,
        domain: str,
        passive: bool = True,
        brute: bool = False
    ) -> AmassResult:
        """
        Enumerate subdomains with Amass
        
        Args:
            domain: Target domain
            passive: Use passive sources only (no DNS resolution)
            brute: Enable DNS brute-forcing
            
        Returns:
            AmassResult with subdomains
        """
        import time
        start_time = time.time()
        
        cmd = ["amass", "enum", "-d", domain, "-json", "-o", "-"]
        
        if passive:
            cmd.append("-passive")
        if brute:
            cmd.append("-brute")
            
        logger.info(f"Starting Amass: {' '.join(cmd)}")
        
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
            
            subdomains = []
            
            # Parse JSON output (one JSON object per line)
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Amass JSON format varies by version
                    if isinstance(data, dict):
                        name = data.get("name", "")
                        if name:
                            subdomains.append(name)
                except json.JSONDecodeError:
                    # Try plain text fallback
                    if line and not line.startswith('['):
                        subdomains.append(line.strip())
                        
            # Remove duplicates and sort
            subdomains = sorted(set(subdomains))
            duration = time.time() - start_time
            
            return AmassResult(
                success=True,
                domain=domain,
                subdomains=subdomains,
                count=len(subdomains),
                duration=duration
            )
            
        except asyncio.TimeoutError:
            logger.error("Amass timed out")
            return AmassResult(success=False, domain=domain, error="Timeout")
        except Exception as e:
            logger.error(f"Amass error: {e}")
            return AmassResult(success=False, domain=domain, error=str(e))
            
    async def intel(self, domain: str) -> dict:
        """
        Gather intelligence about a domain
        
        Args:
            domain: Target domain
            
        Returns:
            Dictionary with intelligence data
        """
        cmd = ["amass", "intel", "-d", domain, "-whois"]
        
        logger.info(f"Starting Amass intel: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300
            )
            
            results = stdout.decode().strip().split('\n')
            
            return {
                "success": True,
                "domain": domain,
                "related_domains": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Amass intel error: {e}")
            return {"success": False, "error": str(e)}


# Sync wrappers
def enumerate_sync(domain: str, passive: bool = True) -> AmassResult:
    """Synchronous wrapper"""
    amass = AmassIntegration()
    return asyncio.run(amass.enumerate(domain, passive))


def intel_sync(domain: str) -> dict:
    """Synchronous intel wrapper"""
    amass = AmassIntegration()
    return asyncio.run(amass.intel(domain))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Amass Integration...")
    print("="*60)
    
    result = enumerate_sync("scanme.nmap.org", passive=True)
    
    print(f"Success: {result.success}")
    print(f"Domain: {result.domain}")
    print(f"Found {result.count} subdomains:")
    for subdomain in result.subdomains[:10]:
        print(f"  • {subdomain}")
