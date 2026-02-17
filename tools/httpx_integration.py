"""
HTTPX Integration - Fast HTTP Prober
Schneller HTTP/HTTPS Prober für Subdomains und URLs
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HTTPXHost:
    """HTTPX host result"""
    url: str
    status_code: int = 0
    title: str = ""
    webserver: str = ""
    content_type: str = ""
    content_length: int = 0
    response_time: str = ""
    technologies: List[str] = field(default_factory=list)
    ip: str = ""
    port: int = 0
    scheme: str = ""


@dataclass
class HTTPXResult:
    """HTTPX scan result"""
    success: bool
    hosts: List[HTTPXHost] = field(default_factory=list)
    count: int = 0
    error: Optional[str] = None
    duration: float = 0.0


class HTTPXIntegration:
    """HTTPX Fast HTTP Prober"""
    
    def __init__(self, timeout: int = 10, threads: int = 50):
        self.timeout = timeout
        self.threads = threads
        
    async def probe(
        self,
        targets: List[str],
        probe_all_ips: bool = False,
        follow_redirects: bool = True
    ) -> HTTPXResult:
        """
        Probe targets for HTTP/HTTPS
        
        Args:
            targets: List of domains, IPs, or URLs
            probe_all_ips: Probe all IPs for a domain
            follow_redirects: Follow HTTP redirects
            
        Returns:
            HTTPXResult with host information
        """
        import time
        from tempfile import NamedTemporaryFile
        
        start_time = time.time()
        
        # Write targets to temp file
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for target in targets:
                f.write(target + '\n')
            temp_file = f.name
            
        cmd = [
            "httpx",
            "-l", temp_file,
            "-json",
            "-timeout", str(self.timeout),
            "-threads", str(self.threads),
        ]
        
        if probe_all_ips:
            cmd.append("-probe-all-ips")
        if not follow_redirects:
            cmd.append("-no-follow-redirects")
            
        logger.info(f"Starting HTTPX probe: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout * 2
            )
            
            hosts = []
            
            # Parse JSON output
            for line in stdout.decode().strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    host = HTTPXHost(
                        url=data.get("url", ""),
                        status_code=data.get("status_code", 0),
                        title=data.get("title", ""),
                        webserver=data.get("webserver", ""),
                        content_type=data.get("content_type", ""),
                        content_length=data.get("content_length", 0),
                        response_time=data.get("response_time", ""),
                        technologies=data.get("tech", []),
                        ip=data.get("host", ""),
                        port=data.get("port", 0),
                        scheme=data.get("scheme", "")
                    )
                    hosts.append(host)
                except json.JSONDecodeError:
                    continue
                    
            duration = time.time() - start_time
            
            # Cleanup temp file
            import os
            os.unlink(temp_file)
            
            return HTTPXResult(
                success=True,
                hosts=hosts,
                count=len(hosts),
                duration=duration
            )
            
        except asyncio.TimeoutError:
            logger.error("HTTPX probe timed out")
            return HTTPXResult(success=False, error="Timeout")
        except Exception as e:
            logger.error(f"HTTPX error: {e}")
            return HTTPXResult(success=False, error=str(e))
            
    async def probe_single(self, target: str) -> Optional[HTTPXHost]:
        """Probe a single target"""
        result = await self.probe([target])
        if result.success and result.hosts:
            return result.hosts[0]
        return None


# Sync wrappers
def probe_sync(targets: List[str]) -> HTTPXResult:
    """Synchronous wrapper for HTTP probing"""
    httpx = HTTPXIntegration()
    return asyncio.run(httpx.probe(targets))


def probe_single_sync(target: str) -> Optional[HTTPXHost]:
    """Synchronous wrapper for single target"""
    httpx = HTTPXIntegration()
    return asyncio.run(httpx.probe_single(target))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing HTTPX Integration...")
    print("="*60)
    
    result = probe_sync(["scanme.nmap.org", "http://scanme.nmap.org"])
    
    print(f"Success: {result.success}")
    print(f"Found {result.count} live hosts:")
    for host in result.hosts:
        print(f"  • {host.url}")
        print(f"    Status: {host.status_code}")
        print(f"    Title: {host.title}")
        print(f"    Server: {host.webserver}")
        print(f"    Response Time: {host.response_time}")
