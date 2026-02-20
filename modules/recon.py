#!/usr/bin/env python3
"""
Reconnaissance Module
Intelligent target reconnaissance using LLM analysis
Author: SHAdd0WTAka
"""

import logging
import socket
import subprocess
from typing import Dict, List

# Import subdomain scanner
try:
    from modules.subdomain_scanner import SubdomainScanner
    from modules.subdomain_scanner_advanced import AdvancedSubdomainScanner

    SUBDOMAIN_SCANNER_AVAILABLE = True
except ImportError:
    SUBDOMAIN_SCANNER_AVAILABLE = False

logger = logging.getLogger("ZenAI")


class ReconModule:
    """
    Automated reconnaissance with LLM-powered analysis
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.results = {}

    async def analyze_target(self, target: str) -> Dict:
        """
        Perform comprehensive target analysis
        """
        logger.info(f"[Recon] Starting analysis of {target}")

        # Gather basic info
        target_info = {
            "target": target,
            "ip": await self._resolve_ip(target),
            "dns_records": await self._get_dns_records(target),
            "whois": await self._get_whois(target),
        }

        # Use LLM to analyze and suggest next steps
        prompt = f"""
Analyze this target for penetration testing:
Target: {target}
IP: {target_info["ip"]}
DNS Records: {target_info["dns_records"]}

Provide a structured reconnaissance plan including:
1. Potential attack vectors
2. Suggested tools (nmap, gobuster, etc.)
3. Likely vulnerabilities based on common patterns
4. OSINT sources to check
"""

        llm_response = await self.orchestrator.process(prompt)

        target_info["llm_analysis"] = llm_response.content
        target_info["attack_vectors"] = self._parse_attack_vectors(llm_response.content)

        self.results[target] = target_info
        return target_info

    async def _resolve_ip(self, target: str) -> str:
        """Resolve target to IP address"""
        try:
            ip = socket.gethostbyname(target)
            return ip
        except Exception:
            return "Could not resolve"

    async def _get_dns_records(self, target: str) -> List[str]:
        """Get DNS records for target"""
        records = []
        record_types = ["A", "MX", "NS", "TXT", "CNAME"]

        for rtype in record_types:
            try:
                result = subprocess.run(
                    ["nslookup", "-type=" + rtype, target],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    records.append(f"{rtype}: {result.stdout[:200]}...")
            except (subprocess.SubprocessError, OSError):
                continue

        return records if records else ["No DNS records found"]

    async def _get_whois(self, target: str) -> str:
        """Get WHOIS information"""
        try:
            result = subprocess.run(["whois", target], capture_output=True, text=True, timeout=15)
            # Return first 500 chars of relevant info
            return result.stdout[:500] if result.returncode == 0 else "WHOIS failed"
        except (subprocess.SubprocessError, OSError):
            return "WHOIS not available"

    def _parse_attack_vectors(self, llm_content: str) -> List[str]:
        """Extract attack vectors from LLM response"""
        vectors = []
        lines = llm_content.split("\n")
        for line in lines:
            if any(keyword in line.lower() for keyword in ["vector", "attack", "exploit", "vulnerability"]):
                vectors.append(line.strip())
        return vectors[:10]  # Limit to top 10

    async def generate_nmap_command(self, target: str, intensity: str = "normal") -> str:
        """
        Generate optimized nmap command based on target analysis
        """
        prompt = f"""
Generate an nmap command for target {target} with {intensity} intensity.
Consider:
- Stealth vs speed requirements
- Most common ports for web services
- Version detection
- Script scanning for vulnerabilities

Return ONLY the nmap command, nothing else.
"""

        response = await self.orchestrator.process(prompt)
        # Extract command from response
        cmd = response.content.strip()

        # Basic validation
        if not cmd.startswith("nmap"):
            # Fallback to default
            cmd = f"nmap -sV -sC -O {target}"

        return cmd

    async def subdomain_enum(self, domain: str, wordlist: str = "common") -> List[str]:
        """
        LLM-assisted subdomain enumeration
        """
        prompt = f"""
Generate a list of likely subdomains for {domain}.
Include common patterns like:
- admin, api, dev, staging, test
- mail, ftp, vpn, remote
- www, blog, shop, app

Return as a comma-separated list.
"""

        response = await self.orchestrator.process(prompt)

        # Parse subdomains from response
        subdomains = []
        for line in response.content.split("\n"):
            for item in line.split(","):
                item = item.strip().lower()
                if item and "." not in item:
                    subdomains.append(f"{item}.{domain}")

        return list(set(subdomains))[:20]  # Return unique, limited

    async def comprehensive_subdomain_scan(
        self,
        domain: str,
        advanced: bool = False,
        check_http: bool = True,
        max_workers: int = 50,
    ) -> Dict:
        """
        Comprehensive subdomain enumeration using SubdomainScanner

        Args:
            domain: Target domain
            advanced: Use advanced scanning techniques
            check_http: Check HTTP/HTTPS availability
            max_workers: Concurrent workers

        Returns:
            Dictionary with scan results and metadata
        """
        if not SUBDOMAIN_SCANNER_AVAILABLE:
            logger.warning("[Recon] SubdomainScanner not available, falling back to basic enumeration")
            return {
                "domain": domain,
                "subdomains": await self.subdomain_enum(domain),
                "method": "basic_llm",
            }

        logger.info(f"[Recon] Starting comprehensive subdomain scan for {domain}")

        if advanced:
            scanner = AdvancedSubdomainScanner(orchestrator=self.orchestrator, max_workers=max_workers)
            results = await scanner.scan_advanced(domain=domain, check_http=check_http)
        else:
            scanner = SubdomainScanner(orchestrator=self.orchestrator, max_workers=max_workers)
            results = await scanner.scan(domain=domain, check_http=check_http)

        # Build comprehensive result
        live_hosts = [r for r in results.values() if r.is_alive]
        dns_only = [r for r in results.values() if not r.is_alive]

        scan_result = {
            "domain": domain,
            "total_discovered": len(results),
            "live_hosts": len(live_hosts),
            "dns_only": len(dns_only),
            "subdomains": {
                sub: {
                    "ip_addresses": r.ip_addresses,
                    "status_code": r.status_code,
                    "server_header": r.server_header,
                    "technologies": r.technologies,
                    "is_alive": r.is_alive,
                }
                for sub, r in results.items()
            },
            "method": "advanced_scan" if advanced else "standard_scan",
        }

        logger.info(f"[Recon] Subdomain scan complete: {len(results)} found ({len(live_hosts)} live)")
        return scan_result

    async def discover_attack_surface(self, domain: str) -> Dict:
        """
        Complete attack surface discovery for a domain

        Combines:
        - Subdomain enumeration
        - DNS record analysis
        - Technology fingerprinting
        - Service discovery
        """
        logger.info(f"[Recon] Discovering attack surface for {domain}")

        # Run subdomain scan
        subdomain_data = await self.comprehensive_subdomain_scan(domain=domain, advanced=True, check_http=True)

        # Get basic target info
        target_info = {
            "ip": await self._resolve_ip(domain),
            "dns_records": await self._get_dns_records(domain),
            "whois": await self._get_whois(domain),
        }

        # Use LLM to analyze attack surface
        live_subdomains = [sub for sub, data in subdomain_data["subdomains"].items() if data.get("is_alive")]

        prompt = f"""
Analyze the attack surface for penetration testing:

Target Domain: {domain}
IP Address: {target_info["ip"]}
Total Subdomains Discovered: {subdomain_data["total_discovered"]}
Live Hosts: {subdomain_data["live_hosts"]}

Live Subdomains:
{chr(10).join(f"- {sub}" for sub in live_subdomains[:20])}

DNS Records:
{chr(10).join(target_info["dns_records"][:5])}

Provide:
1. Priority targets for penetration testing
2. Potential entry points
3. Likely vulnerability areas based on discovered services
4. Recommended next steps (specific tools and techniques)
"""

        try:
            llm_response = await self.orchestrator.process(prompt)
            analysis = llm_response.content
        except Exception as e:
            logger.warning(f"[Recon] LLM analysis failed: {e}")
            analysis = "LLM analysis not available"

        return {
            "domain": domain,
            "target_info": target_info,
            "subdomain_data": subdomain_data,
            "analysis": analysis,
            "recommended_targets": live_subdomains[:10] if live_subdomains else [domain],
        }
