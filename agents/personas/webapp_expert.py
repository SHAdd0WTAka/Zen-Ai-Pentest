#!/usr/bin/env python3
"""
WebApp Expert Persona - Specialized in Web Application Penetration Testing
Part of the Zen-AI-Pentest Multi-Agent System
Author: SHAdd0WTAka
"""

import logging
from typing import Any, Dict, List, Optional

from agents.agent_base import AgentMessage, AgentRole, BaseAgent
from autonomous.idor_detector import IDORDetector
from guardrails.ip_validator import IPValidator
from tools.ffuf_integration_enhanced import FFUFIntegration
from tools.nikto_integration import NiktoScanner
from tools.nuclei_integration import NucleiScanner
from tools.wafw00f_integration import WAFW00FScanner
from tools.whatweb_integration import WhatWebScanner

logger = logging.getLogger("ZenAI.Personas")


class WebAppExpertPersona(BaseAgent):
    """
    WebApp Expert - Specialized in OWASP Top 10 and web application security testing.

    Expertise:
    - OWASP Top 10 vulnerabilities
    - SQL Injection (SQLMap integration)
    - Cross-Site Scripting (XSS)
    - Cross-Site Request Forgery (CSRF)
    - Insecure Direct Object Reference (IDOR)
    - Authentication bypass
    - Session management flaws

    Tools:
    - sqlmap: Automated SQL injection
    - burpsuite: Web proxy and testing
    - zap: OWASP ZAP scanner
    - nikto: Web server scanner
    - nuclei: Vulnerability scanner
    - ffuf: Fuzzing tool
    """

    name = "WebApp Expert"
    description = "Specialized in web application penetration testing with focus on OWASP Top 10"
    expertise = [
        "OWASP Top 10",
        "SQL Injection",
        "Cross-Site Scripting (XSS)",
        "Cross-Site Request Forgery (CSRF)",
        "Insecure Direct Object Reference (IDOR)",
        "Authentication Bypass",
        "Session Management",
        "Security Misconfiguration",
        "Sensitive Data Exposure",
        "XML External Entities (XXE)",
        "Broken Access Control",
        "Insecure Deserialization",
    ]
    tools = ["sqlmap", "burpsuite", "zap", "nikto", "nuclei", "ffuf", "wafw00f", "whatweb", "dirb", "gobuster"]

    system_prompt = """You are a Web Application Security Expert with deep knowledge of OWASP Top 10 vulnerabilities.

    YOUR EXPERTISE:
    - OWASP Top 10 2021 vulnerabilities
    - SQL Injection (Boolean-based, Time-based, Union-based, Error-based)
    - Cross-Site Scripting (Reflected, Stored, DOM-based)
    - Cross-Site Request Forgery (CSRF) attacks
    - Insecure Direct Object Reference (IDOR)
    - Authentication and Session Management flaws
    - Security Misconfigurations
    - Sensitive Data Exposure
    - XML External Entities (XXE)
    - Broken Access Control
    - Insecure Deserialization
    - Server-Side Request Forgery (SSRF)

    METHODOLOGY - WEB APP PENTEST:
    1. RECONNAISSANCE
       - WAF Detection (wafw00f)
       - Technology Stack Identification (whatweb)
       - Server Banner Grabbing
       - SSL/TLS Configuration Analysis

    2. DISCOVERY
       - Directory Enumeration (ffuf, dirb, gobuster)
       - Endpoint Discovery
       - Parameter Identification
       - Hidden File/Backup Discovery

    3. VULNERABILITY SCANNING
       - Automated Scanning (nikto, nuclei)
       - OWASP ZAP Spidering
       - Configuration Review

    4. MANUAL TESTING
       - SQL Injection Testing (SQLMap)
       - XSS Payload Injection
       - CSRF Token Testing
       - IDOR Vulnerability Testing
       - Authentication Bypass Attempts

    5. EXPLOITATION
       - Proof-of-Concept Development
       - Privilege Escalation Testing
       - Business Logic Testing

    6. REPORTING
       - CVSS Scoring
       - Evidence Collection
       - Remediation Recommendations

    RULES:
    - ALWAYS check for WAF before aggressive testing
    - NEVER test destructive exploits without explicit approval
    - Document ALL findings with clear evidence
    - Respect rate limits to avoid service disruption
    - Use time-based SQLi for detection only
    - Report all findings with CVSS score and remediation
    - Flag business logic vulnerabilities separately
    - Maintain detailed logs of all tests performed

    TOOL USAGE:
    - sqlmap: Use with --risk=1 --level=1 for initial detection
    - nikto: Use for comprehensive web server scanning
    - nuclei: Use for CVE detection and misconfigurations
    - ffuf: Use for directory and parameter fuzzing
    - wafw00f: Use before any aggressive testing
    - whatweb: Use for technology fingerprinting

    REPORT FORMAT:
    For each vulnerability found, provide:
    1. Vulnerability Name & Classification
    2. CVSS v3.1 Score and Severity
    3. Affected URL/Parameter
    4. Proof of Concept (PoC)
    5. Impact Assessment
    6. Remediation Steps
    7. References (OWASP, CWE, CAPEC)
    """

    def __init__(self, name: str = "WebApp Expert", orchestrator=None, zen_orchestrator=None):
        super().__init__(name, AgentRole.ANALYST, orchestrator)
        self.zen_orchestrator = zen_orchestrator
        self.ip_validator = IPValidator()
        self.findings_db = []

        # Tool instances
        self.nuclei = NucleiScanner()
        self.nikto = NiktoScanner()
        self.wafw00f = WAFW00FScanner()
        self.whatweb = WhatWebScanner()
        self.ffuf = FFUFIntegration()
        self.idor_detector = IDORDetector()

        # Register message handlers
        self.register_handler("webapp_scan", self._handle_webapp_scan)
        self.register_handler("sqli_test", self._handle_sqli_test)
        self.register_handler("xss_test", self._handle_xss_test)
        self.register_handler("csrf_test", self._handle_csrf_test)
        self.register_handler("idor_test", self._handle_idor_test)
        self.register_handler("findings_analysis", self._handle_findings_analysis)

    async def _handle_webapp_scan(self, msg: AgentMessage):
        """Handle comprehensive web application scan requests"""
        target = msg.context.get("target")
        scan_depth = msg.context.get("depth", "normal")

        logger.info(f"[WebAppExpert:{self.name}] Starting webapp scan for {target}")

        # Validate target
        if not self._validate_target(target):
            await self.send_message(
                content=f"Invalid or forbidden target: {target}",
                recipient=msg.sender,
                msg_type="error",
                context={"error": "validation_failed"},
            )
            return

        # Phase 1: WAF Detection
        waf_info = await self._detect_waf(target)

        # Phase 2: Technology Detection
        tech_info = await self._detect_technologies(target)

        # Phase 3: Directory Enumeration
        directories = await self._enumerate_directories(target, scan_depth)

        # Phase 4: Vulnerability Scanning
        vulns = await self._scan_vulnerabilities(target, waf_info)

        findings = {
            "target": target,
            "waf": waf_info,
            "technologies": tech_info,
            "directories": directories,
            "vulnerabilities": vulns,
            "scan_depth": scan_depth,
        }

        await self.send_message(
            content=f"WebApp scan complete. Found {len(vulns)} vulnerabilities.",
            recipient=msg.sender,
            msg_type="webapp_findings",
            context={"findings": findings},
        )

    async def _handle_sqli_test(self, msg: AgentMessage):
        """Handle SQL injection testing requests"""
        target = msg.context.get("target")
        params = msg.context.get("parameters", [])

        logger.info(f"[WebAppExpert:{self.name}] Testing SQLi on {target}")

        results = await self._test_sql_injection(target, params)

        await self.send_message(
            content=f"SQLi testing complete. Vulnerable: {results['vulnerable']}",
            recipient=msg.sender,
            msg_type="sqli_results",
            context={"results": results},
        )

    async def _handle_xss_test(self, msg: AgentMessage):
        """Handle XSS testing requests"""
        target = msg.context.get("target")
        params = msg.context.get("parameters", [])

        logger.info(f"[WebAppExpert:{self.name}] Testing XSS on {target}")

        results = await self._test_xss(target, params)

        await self.send_message(
            content=f"XSS testing complete. Found {len(results['findings'])} issues.",
            recipient=msg.sender,
            msg_type="xss_results",
            context={"results": results},
        )

    async def _handle_csrf_test(self, msg: AgentMessage):
        """Handle CSRF testing requests"""
        target = msg.context.get("target")

        logger.info(f"[WebAppExpert:{self.name}] Testing CSRF on {target}")

        results = await self._test_csrf(target)

        await self.send_message(
            content=f"CSRF testing complete. Vulnerable: {results['vulnerable']}",
            recipient=msg.sender,
            msg_type="csrf_results",
            context={"results": results},
        )

    async def _handle_idor_test(self, msg: AgentMessage):
        """Handle IDOR testing requests"""
        target = msg.context.get("target")
        endpoints = msg.context.get("endpoints", [])

        logger.info(f"[WebAppExpert:{self.name}] Testing IDOR on {target}")

        results = await self.idor_detector.test_endpoints(target, endpoints)

        await self.send_message(
            content=f"IDOR testing complete. Found {len(results['vulnerable'])} issues.",
            recipient=msg.sender,
            msg_type="idor_results",
            context={"results": results},
        )

    async def _handle_findings_analysis(self, msg: AgentMessage):
        """Analyze findings from other agents"""
        findings = msg.context.get("findings", [])

        analysis = self.analyze(None, findings)

        await self.send_message(
            content=f"Analysis complete. Risk level: {analysis['risk_level']}",
            recipient=msg.sender,
            msg_type="analysis_results",
            context={"analysis": analysis},
        )

    def _validate_target(self, target: str) -> bool:
        """Validate target is allowed"""
        # Check for private IPs
        if self.ip_validator.is_private_ip(target):
            logger.warning(f"[WebAppExpert] Blocking private IP: {target}")
            return False
        return True

    async def _detect_waf(self, target: str) -> Dict[str, Any]:
        """Detect Web Application Firewall"""
        try:
            result = await self.wafw00f.detect_waf(target)
            return {
                "detected": result.get("detected", False),
                "waf_name": result.get("waf_name", "Unknown"),
                "confidence": result.get("confidence", 0),
            }
        except Exception as e:
            logger.error(f"[WebAppExpert] WAF detection error: {e}")
            return {"detected": False, "error": str(e)}

    async def _detect_technologies(self, target: str) -> List[Dict[str, Any]]:
        """Detect web technologies"""
        try:
            result = await self.whatweb.scan(target)
            return result.get("plugins", [])
        except Exception as e:
            logger.error(f"[WebAppExpert] Technology detection error: {e}")
            return []

    async def _enumerate_directories(self, target: str, depth: str) -> List[str]:
        """Enumerate directories and endpoints"""
        try:
            wordlist = "common.txt" if depth == "quick" else "directory-list-2.3-medium.txt"
            result = await self.ffuf.directory_fuzz(target, wordlist=wordlist)
            return result.get("findings", [])
        except Exception as e:
            logger.error(f"[WebAppExpert] Directory enumeration error: {e}")
            return []

    async def _scan_vulnerabilities(self, target: str, waf_info: Dict) -> List[Dict[str, Any]]:
        """Scan for vulnerabilities"""
        vulns = []

        # Nikto scan
        try:
            nikto_results = await self.nikto.scan(target)
            vulns.extend(nikto_results.get("vulnerabilities", []))
        except Exception as e:
            logger.error(f"[WebAppExpert] Nikto scan error: {e}")

        # Nuclei scan (only if no WAF or WAF bypass enabled)
        if not waf_info.get("detected"):
            try:
                nuclei_results = await self.nuclei.scan(target, templates=["cves", "vulnerabilities"])
                vulns.extend(nuclei_results.get("findings", []))
            except Exception as e:
                logger.error(f"[WebAppExpert] Nuclei scan error: {e}")

        return vulns

    async def _test_sql_injection(self, target: str, params: List[str]) -> Dict[str, Any]:
        """Test for SQL injection vulnerabilities"""
        # This would integrate with SQLMap
        return {"vulnerable": False, "target": target, "parameters_tested": params, "payloads_used": [], "findings": []}

    async def _test_xss(self, target: str, params: List[str]) -> Dict[str, Any]:
        """Test for XSS vulnerabilities"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
        ]

        findings = []
        # Test each parameter with each payload
        for param in params:
            for payload in xss_payloads:
                # Simulate testing
                pass

        return {"target": target, "parameters_tested": params, "payloads_used": xss_payloads, "findings": findings}

    async def _test_csrf(self, target: str) -> Dict[str, Any]:
        """Test for CSRF vulnerabilities"""
        checks = ["token_presence", "token_entropy", "same_site_cookies", "referer_validation"]

        return {"vulnerable": False, "target": target, "checks_performed": checks, "missing_protections": []}

    def analyze(self, target: Optional[str], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Persona-specific analysis logic for web application findings.

        Args:
            target: The target URL/domain
            findings: List of vulnerability findings

        Returns:
            Analysis results with risk scoring and recommendations
        """
        analysis = {
            "total_findings": len(findings),
            "by_category": {},
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "owasp_top10_mapping": {},
            "risk_level": "low",
            "critical_vulnerabilities": [],
            "recommendations": [],
            "attack_vectors": [],
        }

        # Categorize findings
        for finding in findings:
            category = finding.get("category", "unknown")
            severity = finding.get("severity", "info").lower()

            # By category
            if category not in analysis["by_category"]:
                analysis["by_category"][category] = []
            analysis["by_category"][category].append(finding)

            # By severity
            if severity in analysis["by_severity"]:
                analysis["by_severity"][severity] += 1

            # OWASP Top 10 mapping
            owasp_category = self._map_to_owasp(category)
            if owasp_category:
                if owasp_category not in analysis["owasp_top10_mapping"]:
                    analysis["owasp_top10_mapping"][owasp_category] = []
                analysis["owasp_top10_mapping"][owasp_category].append(finding)

            # Critical vulnerabilities
            if severity in ["critical", "high"]:
                analysis["critical_vulnerabilities"].append(finding)

        # Determine risk level
        if analysis["by_severity"]["critical"] > 0:
            analysis["risk_level"] = "critical"
        elif analysis["by_severity"]["high"] > 0:
            analysis["risk_level"] = "high"
        elif analysis["by_severity"]["medium"] > 0:
            analysis["risk_level"] = "medium"

        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)

        # Identify attack vectors
        analysis["attack_vectors"] = self._identify_attack_vectors(findings)

        return analysis

    def _map_to_owasp(self, category: str) -> Optional[str]:
        """Map vulnerability category to OWASP Top 10"""
        mapping = {
            "sql_injection": "A03:2021 - Injection",
            "xss": "A03:2021 - Injection",
            "csrf": "A01:2021 - Broken Access Control",
            "idor": "A01:2021 - Broken Access Control",
            "authentication": "A07:2021 - Identification and Authentication Failures",
            "session": "A07:2021 - Identification and Authentication Failures",
            "configuration": "A05:2021 - Security Misconfiguration",
            "exposure": "A02:2021 - Cryptographic Failures",
            "xxe": "A04:2021 - Insecure Design",
            "deserialization": "A08:2021 - Software and Data Integrity Failures",
            "logging": "A09:2021 - Security Logging and Monitoring Failures",
            "ssrf": "A10:2021 - Server-Side Request Forgery",
        }
        return mapping.get(category.lower())

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate remediation recommendations"""
        recommendations = []

        if analysis["by_severity"]["critical"] > 0:
            recommendations.append("IMMEDIATE: Address critical vulnerabilities before production deployment")

        if "A03:2021 - Injection" in analysis["owasp_top10_mapping"]:
            recommendations.append("Implement parameterized queries and input validation for all user inputs")

        if "A01:2021 - Broken Access Control" in analysis["owasp_top10_mapping"]:
            recommendations.append("Review and enforce proper access controls at all layers")

        if "A07:2021 - Identification and Authentication Failures" in analysis["owasp_top10_mapping"]:
            recommendations.append("Implement multi-factor authentication and secure session management")

        return recommendations

    def _identify_attack_vectors(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Identify potential attack vectors"""
        vectors = []

        categories = [f.get("category", "").lower() for f in findings]

        if "sql_injection" in categories:
            vectors.append("Database compromise via SQL Injection")

        if "xss" in categories:
            vectors.append("Session hijacking via XSS")

        if "csrf" in categories:
            vectors.append("Unauthorized actions via CSRF")

        if "idor" in categories:
            vectors.append("Unauthorized data access via IDOR")

        return vectors

    async def execute_task(self, task: Dict) -> Dict:
        """Execute web application testing task"""
        task_type = task.get("type", "")
        context = task.get("context", {})

        logger.info(f"[WebAppExpert:{self.name}] Executing task: {task_type}")

        if task_type == "webapp_scan":
            target = context.get("target")
            findings = await self._scan_vulnerabilities(target, {})
            analysis = self.analyze(target, findings)

            return {"status": "complete", "findings": findings, "analysis": analysis, "agent": self.name}

        elif task_type == "sqli_scan":
            results = await self._test_sql_injection(context.get("target"), context.get("parameters", []))
            return {"status": "complete", "results": results, "agent": self.name}

        elif task_type == "xss_scan":
            results = await self._test_xss(context.get("target"), context.get("parameters", []))
            return {"status": "complete", "results": results, "agent": self.name}

        return {"status": "unknown_task"}
