#!/usr/bin/env python3
"""
Vulnerability Scanner Module
AI-powered vulnerability analysis and scanning
Author: SHAdd0WTAka
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger("ZenAI")


@dataclass
class Vulnerability:
    name: str
    severity: str  # Critical, High, Medium, Low, Info
    description: str
    evidence: str
    remediation: str
    cvss_score: Optional[float] = None
    cve_ids: List[str] = None


class VulnScannerModule:
    """
    Intelligent vulnerability scanner with LLM analysis
    """

    SEVERITY_ORDER = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Info": 1}

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.vulnerabilities = []

    async def analyze_nmap_output(self, nmap_output: str) -> List[Vulnerability]:
        """
        Analyze nmap scan results with LLM
        """
        prompt = f"""
Analyze this nmap scan output and identify vulnerabilities:

```
{nmap_output[:3000]}  # Truncate for token limits
```

For each vulnerability found, provide:
1. Name
2. Severity (Critical/High/Medium/Low/Info)
3. Description
4. Evidence from scan
5. Remediation steps
6. CVE IDs if applicable

Format each finding as:
[VULN]
Name: <name>
Severity: <severity>
Description: <desc>
Evidence: <evidence>
Remediation: <fix>
CVE: <cve_ids>
[/VULN]
"""

        response = await self.orchestrator.process(prompt)
        vulnerabilities = self._parse_vulnerabilities(response.content)

        logger.info(f"[VulnScanner] Found {len(vulnerabilities)} vulnerabilities in nmap output")
        return vulnerabilities

    async def analyze_web_headers(self, headers: Dict[str, str], url: str) -> List[Vulnerability]:
        """
        Analyze HTTP headers for security issues
        """
        headers_str = "\n".join([f"{k}: {v}" for k, v in headers.items()])

        prompt = f"""
Analyze these HTTP response headers for security vulnerabilities:
URL: {url}

```
{headers_str}
```

Check for:
- Missing security headers (HSTS, CSP, X-Frame-Options, etc.)
- Information disclosure (Server version, X-Powered-By)
- CORS misconfigurations
- Cookie security flags

List each finding with severity and remediation.
"""

        response = await self.orchestrator.process(prompt)
        return self._parse_vulnerabilities(response.content)

    async def analyze_web_page(self, html_content: str, url: str) -> List[Vulnerability]:
        """
        Analyze web page content for vulnerabilities
        """
        # Extract potentially interesting parts
        forms = re.findall(r"<form.*?</form>", html_content, re.DOTALL | re.IGNORECASE)
        scripts = re.findall(r"<script.*?</script>", html_content, re.DOTALL | re.IGNORECASE)
        comments = re.findall(r"<!--.*?-->", html_content, re.DOTALL)

        analysis_input = f"""
Forms found: {len(forms)}
Scripts found: {len(scripts)}
HTML comments: {len(comments)}

Sample forms:
{chr(10).join([f[:500] for f in forms[:3]])}

Sample comments (potential info disclosure):
{chr(10).join([c[:300] for c in comments[:5] if len(c) > 10])}
"""

        prompt = f"""
Analyze this web page content for vulnerabilities:
URL: {url}

{analysis_input}

Look for:
- Insecure form submissions (no CSRF tokens)
- Hardcoded credentials or API keys in comments
- Sensitive information in HTML comments
- Inline scripts (XSS potential)
- File upload forms without restrictions
- Autocomplete enabled on sensitive fields

Provide findings with severity and remediation.
"""

        response = await self.orchestrator.process(prompt)
        return self._parse_vulnerabilities(response.content)

    async def check_cve_database(self, service: str, version: str) -> List[Vulnerability]:
        """
        Query LLM for known CVEs for a service/version
        """
        prompt = f"""
List known vulnerabilities (CVEs) for:
Service: {service}
Version: {version}

For each CVE provide:
- CVE ID
- CVSS Score
- Severity
- Description
- Exploit availability

If version is unknown or 'latest', focus on recent high-profile CVEs.
"""

        response = await self.orchestrator.process(prompt)

        # Parse CVE information
        vulns = []
        cve_pattern = r"(CVE-\d{4}-\d{4,})"
        cves = re.findall(cve_pattern, response.content)

        for cve in cves[:5]:  # Limit results
            vulns.append(
                Vulnerability(
                    name=f"{service} - {cve}",
                    severity="Unknown",  # Would need actual CVSS lookup
                    description=f"Known vulnerability in {service} {version}",
                    evidence=f"CVE ID: {cve}",
                    remediation="Update to latest version or apply security patches",
                    cve_ids=[cve],
                )
            )

        return vulns

    async def ssl_tls_analysis(self, cert_info: str) -> List[Vulnerability]:
        """
        Analyze SSL/TLS configuration
        """
        prompt = f"""
Analyze this SSL/TLS certificate and configuration:

```
{cert_info[:2000]}
```

Check for:
- Weak cipher suites
- Expired or soon-expiring certificates
- Self-signed certificates in production
- Weak protocols (SSLv2, SSLv3, TLS 1.0)
- Certificate chain issues
- Wildcard certificate usage

List findings with severity and remediation.
"""

        response = await self.orchestrator.process(prompt)
        return self._parse_vulnerabilities(response.content)

    def _parse_vulnerabilities(self, content: str) -> List[Vulnerability]:
        """Parse vulnerability blocks from LLM response"""
        vulns = []

        # Look for [VULN] blocks
        vuln_blocks = re.findall(r"\[VULN\](.*?)\[/VULN\]", content, re.DOTALL)

        if not vuln_blocks:
            # Try alternate parsing (numbered lists)
            sections = content.split("\n\n")
            for section in sections:
                if any(s in section.lower() for s in ["severity:", "vulnerability:", "risk:"]):
                    vulns.append(self._create_vuln_from_text(section))
        else:
            for block in vuln_blocks:
                vulns.append(self._create_vuln_from_text(block))

        return vulns

    def _create_vuln_from_text(self, text: str) -> Vulnerability:
        """Create Vulnerability object from text block"""

        # Extract fields using regex
        name_match = re.search(r"Name:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        severity_match = re.search(r"Severity:\s*(\w+)", text, re.IGNORECASE)
        desc_match = re.search(r"Description:\s*(.+?)(?:\n\w+:|$)", text, re.DOTALL | re.IGNORECASE)
        evidence_match = re.search(r"Evidence:\s*(.+?)(?:\n\w+:|$)", text, re.DOTALL | re.IGNORECASE)
        remediation_match = re.search(r"Remediation:\s*(.+?)(?:\n\w+:|$)", text, re.DOTALL | re.IGNORECASE)
        cve_match = re.findall(r"(CVE-\d{4}-\d{4,})", text)

        # Validate severity
        severity = severity_match.group(1).capitalize() if severity_match else "Info"
        if severity not in self.SEVERITY_ORDER:
            severity = "Info"

        return Vulnerability(
            name=name_match.group(1).strip() if name_match else "Unknown Vulnerability",
            severity=severity,
            description=desc_match.group(1).strip()[:500] if desc_match else text[:300],
            evidence=evidence_match.group(1).strip()[:300] if evidence_match else "N/A",
            remediation=(remediation_match.group(1).strip()[:500] if remediation_match else "Review and fix"),
            cve_ids=cve_match if cve_match else [],
        )

    def get_severity_summary(self, vulnerabilities: List[Vulnerability]) -> Dict[str, int]:
        """Get summary of vulnerabilities by severity"""
        summary = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
        for v in vulnerabilities:
            if v.severity in summary:
                summary[v.severity] += 1
        return summary

    def sort_by_severity(self, vulnerabilities: List[Vulnerability]) -> List[Vulnerability]:
        """Sort vulnerabilities by severity (highest first)"""
        return sorted(
            vulnerabilities,
            key=lambda x: self.SEVERITY_ORDER.get(x.severity, 0),
            reverse=True,
        )
