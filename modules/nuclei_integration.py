#!/usr/bin/env python3
"""
Nuclei Integration Module
Template management and vulnerability scanning with Nuclei
Author: SHAdd0WTAka
"""

import asyncio
import json
import logging
import os

import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("ZenAI")


@dataclass
class NucleiTemplate:
    """Represents a Nuclei template"""

    id: str
    name: str
    severity: str
    description: str
    tags: List[str]
    author: str
    reference: List[str]
    classification: Dict
    template_path: str
    protocol: str
    cvss_score: Optional[float] = None
    cwe: List[str] = None
    cve: List[str] = None


@dataclass
class NucleiFinding:
    """Represents a Nuclei scan finding"""

    template_id: str
    template_name: str
    severity: str
    host: str
    matched_at: str
    extract_results: List[str]
    timestamp: str
    curl_command: Optional[str] = None
    request: Optional[str] = None
    response: Optional[str] = None


class NucleiIntegration:
    """
    Integration with ProjectDiscovery Nuclei scanner
    Manages templates and executes scans
    """

    SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}

    def __init__(self, orchestrator=None, nuclei_path: str = "nuclei"):
        self.orchestrator = orchestrator
        self.nuclei_path = nuclei_path
        self.templates_dir = "data/nuclei_templates"
        self.custom_templates = []
        self.scan_results = []

        # Ensure directories exist
        os.makedirs(self.templates_dir, exist_ok=True)

    async def check_nuclei_installed(self) -> bool:
        """Check if Nuclei is installed"""
        try:
            result = subprocess.run(
                [self.nuclei_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def update_templates(self) -> bool:
        """Update Nuclei templates from official repository"""
        try:
            logger.info("[Nuclei] Updating templates...")
            result = subprocess.run(
                [self.nuclei_path, "-update-templates"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            success = result.returncode == 0
            if success:
                logger.info("[Nuclei] Templates updated successfully")
            else:
                logger.error(f"[Nuclei] Update failed: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"[Nuclei] Update error: {e}")
            return False

    def get_template_categories(self) -> Dict[str, List[str]]:
        """Get available template categories"""
        categories = {
            "cves": [],
            "vulnerabilities": [],
            "misconfiguration": [],
            "exposures": [],
            "technologies": [],
            "token-spray": [],
            "default-logins": [],
            "dns": [],
            "fuzzing": [],
            "helpers": [],
            "headless": [],
        }

        # Get from nuclei if available
        try:
            result = subprocess.run([self.nuclei_path, "-tl"], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    for category in categories.keys():
                        if f"{category}/" in line.lower():
                            categories[category].append(line.strip())
        except Exception:
            pass

        return categories

    async def scan_target(
        self,
        target: str,
        severity: List[str] = None,
        tags: List[str] = None,
        templates: List[str] = None,
        rate_limit: int = 150,
    ) -> List[NucleiFinding]:
        """
        Run Nuclei scan against target
        """
        if not await self.check_nuclei_installed():
            logger.error("[Nuclei] Nuclei not installed. Install from: https://nuclei.projectdiscovery.io/")
            return []

        cmd = [
            self.nuclei_path,
            "-u",
            target,
            "-json",
            "-rate-limit",
            str(rate_limit),
            "-timeout",
            "10",
            "-retries",
            "2",
        ]

        # Add severity filter
        if severity:
            cmd.extend(["-severity", ",".join(severity)])

        # Add tags filter
        if tags:
            cmd.extend(["-tags", ",".join(tags)])

        # Add specific templates
        if templates:
            for tmpl in templates:
                cmd.extend(["-t", tmpl])

        logger.info(f"[Nuclei] Starting scan: {' '.join(cmd)}")

        findings = []
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                try:
                    data = json.loads(line.decode().strip())
                    finding = self._parse_nuclei_output(data)
                    if finding:
                        findings.append(finding)
                        logger.info(f"[Nuclei] Found: {finding.template_name} ({finding.severity})")
                except json.JSONDecodeError:
                    continue

            await process.wait()

        except Exception as e:
            logger.error(f"[Nuclei] Scan error: {e}")

        self.scan_results.extend(findings)
        return findings

    def _parse_nuclei_output(self, data: Dict) -> Optional[NucleiFinding]:
        """Parse Nuclei JSON output"""
        try:
            info = data.get("info", {})

            return NucleiFinding(
                template_id=info.get("id", "unknown"),
                template_name=info.get("name", "Unknown"),
                severity=info.get("severity", "info"),
                host=data.get("host", ""),
                matched_at=data.get("matched-at", ""),
                extract_results=data.get("extracted-results", []),
                timestamp=datetime.now().isoformat(),
                curl_command=data.get("curl-command"),
                request=data.get("request"),
                response=data.get("response"),
            )
        except Exception as e:
            logger.error(f"[Nuclei] Parse error: {e}")
            return None

    async def scan_with_ai_analysis(self, target: str) -> Dict:
        """
        Run Nuclei scan and analyze results with LLM
        """
        # Run the scan
        findings = await self.scan_target(target, severity=["critical", "high", "medium"])

        if not findings:
            return {"findings": [], "analysis": "No vulnerabilities found"}

        # Prepare data for LLM analysis
        findings_summary = "\n".join(
            [
                f"- [{f.severity.upper()}] {f.template_name} at {f.matched_at}"
                for f in findings[:20]  # Limit for token efficiency
            ]
        )

        if self.orchestrator:
            prompt = f"""
Analyze these Nuclei scan findings for {target}:

{findings_summary}

Provide:
1. Risk assessment summary
2. Prioritized remediation steps
3. Potential attack chains (how vulnerabilities might be combined)
4. Immediate actions required
"""
            analysis = await self.orchestrator.process(prompt)
            analysis_text = analysis.content
        else:
            analysis_text = "LLM analysis not available (no orchestrator)"

        return {
            "findings": findings,
            "analysis": analysis_text,
            "severity_summary": self._get_severity_summary(findings),
            "timestamp": datetime.now().isoformat(),
        }

    def _get_severity_summary(self, findings: List[NucleiFinding]) -> Dict[str, int]:
        """Get severity summary of findings"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.severity.lower()
            if sev in summary:
                summary[sev] += 1
        return summary

    def export_results(self, findings: List[NucleiFinding], filename: str = None) -> str:
        """Export findings to JSON"""
        if not filename:
            filename = f"logs/nuclei_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "scan_date": datetime.now().isoformat(),
            "total_findings": len(findings),
            "severity_summary": self._get_severity_summary(findings),
            "findings": [asdict(f) for f in findings],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"[Nuclei] Results exported: {filename}")
        return filename

    def get_critical_cves(self) -> List[Dict]:
        """Get list of critical CVE templates"""
        critical_cves = [
            {
                "id": "CVE-2024-XXXX",
                "name": "Placeholder for latest critical CVEs",
                "severity": "critical",
            },
            {
                "id": "CVE-2023-44487",
                "name": "HTTP/2 Rapid Reset",
                "severity": "critical",
            },
            {
                "id": "CVE-2023-38545",
                "name": "cURL SOCKS5 heap buffer overflow",
                "severity": "high",
            },
            {
                "id": "CVE-2023-29357",
                "name": "Microsoft SharePoint Privilege Escalation",
                "severity": "critical",
            },
            {
                "id": "CVE-2023-21716",
                "name": "Microsoft Word Remote Code Execution",
                "severity": "critical",
            },
            {
                "id": "CVE-2022-44877",
                "name": "CentOS Web Panel RCE",
                "severity": "critical",
            },
            {
                "id": "CVE-2022-42889",
                "name": "Apache Commons Text RCE (Text4Shell)",
                "severity": "critical",
            },
            {
                "id": "CVE-2022-41741",
                "name": "VMware Workspace ONE Access RCE",
                "severity": "critical",
            },
            {
                "id": "CVE-2022-26134",
                "name": "Atlassian Confluence OGNL Injection",
                "severity": "critical",
            },
            {
                "id": "CVE-2022-22965",
                "name": "Spring Framework RCE (Spring4Shell)",
                "severity": "critical",
            },
            {
                "id": "CVE-2022-22947",
                "name": "Spring Cloud Gateway RCE",
                "severity": "critical",
            },
            {
                "id": "CVE-2021-44228",
                "name": "Log4j RCE (Log4Shell)",
                "severity": "critical",
            },
            {
                "id": "CVE-2021-45046",
                "name": "Log4j Denial of Service",
                "severity": "critical",
            },
            {
                "id": "CVE-2021-41773",
                "name": "Apache Path Traversal",
                "severity": "critical",
            },
            {
                "id": "CVE-2021-3129",
                "name": "Laravel Ignition RCE",
                "severity": "critical",
            },
            {"id": "CVE-2020-1472", "name": "Zerologon", "severity": "critical"},
            {
                "id": "CVE-2020-14882",
                "name": "Oracle WebLogic RCE",
                "severity": "critical",
            },
            {
                "id": "CVE-2019-19781",
                "name": "Citrix ADC RCE (Shitrix)",
                "severity": "critical",
            },
            {
                "id": "CVE-2019-11510",
                "name": "Pulse Secure VPN Arbitrary File Reading",
                "severity": "critical",
            },
            {
                "id": "CVE-2018-13379",
                "name": "Fortinet VPN Path Traversal",
                "severity": "critical",
            },
            {
                "id": "CVE-2017-0144",
                "name": "EternalBlue (MS17-010)",
                "severity": "critical",
            },
            {
                "id": "CVE-2017-5638",
                "name": "Apache Struts RCE",
                "severity": "critical",
            },
        ]
        return critical_cves


class NucleiTemplateManager:
    """Manages custom Nuclei templates"""

    def __init__(self, templates_dir: str = "data/nuclei_templates"):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)

    def create_template(
        self,
        template_id: str,
        name: str,
        severity: str,
        request: Dict,
        matchers: List[Dict],
        description: str = "",
    ) -> str:
        """Create a new Nuclei template"""

        template = {
            "id": template_id,
            "info": {
                "name": name,
                "author": "zen-ai-pentest",
                "severity": severity,
                "description": description,
                "tags": ["custom", "autogenerated"],
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "tool": "zen-ai-pentest",
                },
            },
            "http": [
                {
                    "method": request.get("method", "GET"),
                    "path": request.get("path", ["/"]),
                    "headers": request.get("headers", {}),
                    "body": request.get("body", ""),
                    "matchers": matchers,
                    "extractors": request.get("extractors", []),
                }
            ],
        }

        filepath = os.path.join(self.templates_dir, f"{template_id}.yaml")

        import yaml

        with open(filepath, "w") as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)

        return filepath

    def list_templates(self) -> List[str]:
        """List all custom templates"""
        templates = []
        for f in os.listdir(self.templates_dir):
            if f.endswith(".yaml") or f.endswith(".yml"):
                templates.append(os.path.join(self.templates_dir, f))
        return templates
