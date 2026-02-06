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
IP: {target_info['ip']}
DNS Records: {target_info['dns_records']}

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
            except Exception:
                continue

        return records if records else ["No DNS records found"]

    async def _get_whois(self, target: str) -> str:
        """Get WHOIS information"""
        try:
            result = subprocess.run(
                ["whois", target], capture_output=True, text=True, timeout=15
            )
            # Return first 500 chars of relevant info
            return result.stdout[:500] if result.returncode == 0 else "WHOIS failed"
        except:
            return "WHOIS not available"

    def _parse_attack_vectors(self, llm_content: str) -> List[str]:
        """Extract attack vectors from LLM response"""
        vectors = []
        lines = llm_content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in ["vector", "attack", "exploit", "vulnerability"]
            ):
                vectors.append(line.strip())
        return vectors[:10]  # Limit to top 10

    async def generate_nmap_command(
        self, target: str, intensity: str = "normal"
    ) -> str:
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
