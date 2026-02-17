"""
Nikto Integration - Web Vulnerability Scanner
Klassischer Web-Security-Scanner
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NiktoFinding:
    """Nikto vulnerability finding"""
    id: str
    method: str
    path: str
    description: str
    severity: str = "info"  # info, low, medium, high
    references: List[str] = field(default_factory=list)


@dataclass
class NiktoResult:
    """Nikto scan result"""
    success: bool
    target: str = ""
    findings: List[NiktoFinding] = field(default_factory=list)
    scan_info: Dict = field(default_factory=dict)
    error: Optional[str] = None
    duration: float = 0.0


class NiktoIntegration:
    """Nikto Web Vulnerability Scanner"""
    
    def __init__(self, timeout: int = 600):
        self.timeout = timeout
        
    async def scan(
        self,
        target: str,
        port: Optional[int] = None,
        ssl: bool = False,
        max_time: Optional[int] = None
    ) -> NiktoResult:
        """
        Scan a target with Nikto
        
        Args:
            target: Target host (e.g., example.com)
            port: Target port (default: 80/443)
            ssl: Use SSL/HTTPS
            max_time: Maximum scan time in seconds
            
        Returns:
            NiktoResult with vulnerabilities
        """
        import time
        start_time = time.time()
        
        cmd = ["nikto", "-h", target, "-Format", "json"]
        
        if port:
            cmd.extend(["-p", str(port)])
        if ssl:
            cmd.append("-ssl")
        if max_time:
            cmd.extend(["-maxtime", str(max_time)])
            
        logger.info(f"Starting Nikto scan: {' '.join(cmd)}")
        
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
            
            output = stdout.decode()
            
            # Try to parse JSON output
            try:
                data = json.loads(output)
                return self._parse_json_output(data, target, time.time() - start_time)
            except json.JSONDecodeError:
                # Fallback: parse text output
                return self._parse_text_output(output, target, time.time() - start_time)
                
        except asyncio.TimeoutError:
            logger.error("Nikto scan timed out")
            return NiktoResult(
                success=False,
                target=target,
                error="Scan timeout"
            )
        except Exception as e:
            logger.error(f"Nikto error: {e}")
            return NiktoResult(
                success=False,
                target=target,
                error=str(e)
            )
            
    def _parse_json_output(self, data: dict, target: str, duration: float) -> NiktoResult:
        """Parse Nikto JSON output"""
        findings = []
        
        vulnerabilities = data.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            finding = NiktoFinding(
                id=str(vuln.get("id", "")),
                method=vuln.get("method", "GET"),
                path=vuln.get("url", ""),
                description=vuln.get("msg", ""),
                severity=self._classify_severity(vuln.get("id", ""), vuln.get("msg", "")),
                references=vuln.get("references", [])
            )
            findings.append(finding)
            
        return NiktoResult(
            success=True,
            target=target,
            findings=findings,
            scan_info={
                "banner": data.get("banner", ""),
                "ip": data.get("ip", ""),
                "port": data.get("port", 0)
            },
            duration=duration
        )
        
    def _parse_text_output(self, output: str, target: str, duration: float) -> NiktoResult:
        """Parse Nikto text output as fallback"""
        findings = []
        
        # Pattern: + OSVDB-XXXX: Description
        pattern = r'\+\s*(OSVDB-\d+|Nikto-|CVE-[^:]+):\s*(.+)'
        matches = re.findall(pattern, output)
        
        for match in matches:
            finding_id = match[0]
            description = match[1]
            
            finding = NiktoFinding(
                id=finding_id,
                method="GET",
                path="/",
                description=description,
                severity=self._classify_severity(finding_id, description)
            )
            findings.append(finding)
            
        return NiktoResult(
            success=len(findings) > 0 or "No web server found" not in output,
            target=target,
            findings=findings,
            duration=duration,
            raw_output=output[:1000] if len(output) > 1000 else output
        )
        
    def _classify_severity(self, finding_id: str, description: str) -> str:
        """Classify finding severity"""
        desc_lower = description.lower()
        
        high_keywords = ["rce", "remote code", "sql injection", "xss", "csrf", "file inclusion"]
        medium_keywords = ["information disclosure", "directory listing", "debug", "backup"]
        
        for keyword in high_keywords:
            if keyword in desc_lower:
                return "high"
                
        for keyword in medium_keywords:
            if keyword in desc_lower:
                return "medium"
                
        return "info"


# Sync wrapper
def scan_sync(target: str, ssl: bool = False) -> NiktoResult:
    """Synchronous wrapper for Nikto scan"""
    nikto = NiktoIntegration()
    return asyncio.run(nikto.scan(target, ssl=ssl))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Nikto Integration...")
    print("="*60)
    
    result = scan_sync("scanme.nmap.org")
    
    print(f"Success: {result.success}")
    print(f"Target: {result.target}")
    print(f"Found {len(result.findings)} issues:")
    for finding in result.findings[:5]:
        print(f"  [{finding.severity.upper()}] {finding.id}: {finding.description[:60]}...")
