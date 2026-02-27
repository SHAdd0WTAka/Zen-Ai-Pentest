"""
Compliance Mapping Module

Maps findings to various compliance frameworks:
- OWASP Top 10
- OWASP ASVS
- ISO 27001
- PCI DSS
- NIST Cybersecurity Framework
- CIS Controls
- BSI Grundschutz (Germany)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ComplianceMapping:
    """Single compliance control mapping."""
    framework: str
    control_id: str
    control_name: str
    description: str
    severity: str
    remediation: str


class ComplianceMapper:
    """
    Maps security findings to compliance frameworks.
    
    Usage:
        mapper = ComplianceMapper()
        
        # Map a finding to OWASP Top 10
        mappings = mapper.map_to_owasp_top_10("SQL Injection")
        
        # Get all frameworks for a finding
        all_mappings = mapper.map_finding("SQL Injection")
    """
    
    def __init__(self):
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, Dict[str, ComplianceMapping]]:
        """Load all compliance mappings."""
        return {
            "owasp_top_10": {
                "sql_injection": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A03:2021",
                    control_name="Injection",
                    description="SQL Injection allows attackers to execute malicious SQL commands",
                    severity="Critical",
                    remediation="Use parameterized queries and prepared statements"
                ),
                "xss": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A03:2021",
                    control_name="Injection",
                    description="Cross-Site Scripting (XSS) allows injection of malicious scripts",
                    severity="High",
                    remediation="Implement proper output encoding and Content Security Policy"
                ),
                "broken_auth": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A07:2021",
                    control_name="Identification and Authentication Failures",
                    description="Weak authentication mechanisms allow credential-based attacks",
                    severity="Critical",
                    remediation="Implement MFA, strong password policies, and session management"
                ),
                "sensitive_data_exposure": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A02:2021",
                    control_name="Cryptographic Failures",
                    description="Sensitive data exposed without proper encryption",
                    severity="High",
                    remediation="Encrypt data at rest and in transit with strong algorithms"
                ),
                "xxe": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A05:2021",
                    control_name="Security Misconfiguration",
                    description="XML External Entity (XXE) processing allows server-side request forgery",
                    severity="High",
                    remediation="Disable XML external entity processing"
                ),
                "broken_access_control": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A01:2021",
                    control_name="Broken Access Control",
                    description="Improper access control allows unauthorized resource access",
                    severity="Critical",
                    remediation="Implement proper authorization checks on all endpoints"
                ),
                "security_misconfiguration": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A05:2021",
                    control_name="Security Misconfiguration",
                    description="Insecure default configurations or incomplete configurations",
                    severity="Medium",
                    remediation="Implement secure configuration baselines and hardening"
                ),
                "csrf": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A01:2021",
                    control_name="Broken Access Control",
                    description="Cross-Site Request Forgery forces users to perform unintended actions",
                    severity="Medium",
                    remediation="Implement anti-CSRF tokens and SameSite cookies"
                ),
                "insecure_deserialization": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A08:2021",
                    control_name="Software and Data Integrity Failures",
                    description="Insecure deserialization leads to remote code execution",
                    severity="Critical",
                    remediation="Implement integrity checks and avoid deserializing untrusted data"
                ),
                "insufficient_logging": ComplianceMapping(
                    framework="OWASP Top 10",
                    control_id="A09:2021",
                    control_name="Security Logging and Monitoring Failures",
                    description="Insufficient logging prevents detection and response to attacks",
                    severity="Medium",
                    remediation="Implement comprehensive logging and monitoring"
                ),
            },
            "iso_27001": {
                "sql_injection": ComplianceMapping(
                    framework="ISO 27001:2022",
                    control_id="A.8.26",
                    control_name="Application Security Requirements",
                    description="SQL injection indicates insufficient input validation",
                    severity="Critical",
                    remediation="Implement secure coding practices and input validation"
                ),
                "xss": ComplianceMapping(
                    framework="ISO 27001:2022",
                    control_id="A.8.26",
                    control_name="Application Security Requirements",
                    description="XSS indicates insufficient output encoding",
                    severity="High",
                    remediation="Implement secure coding practices and output encoding"
                ),
                "broken_auth": ComplianceMapping(
                    framework="ISO 27001:2022",
                    control_id="A.5.17",
                    control_name="Authentication Information",
                    description="Weak authentication violates password management requirements",
                    severity="Critical",
                    remediation="Implement strong authentication mechanisms per A.5.17"
                ),
                "sensitive_data_exposure": ComplianceMapping(
                    framework="ISO 27001:2022",
                    control_id="A.8.24",
                    control_name="Use of Cryptography",
                    description="Sensitive data exposure violates cryptographic protection requirements",
                    severity="High",
                    remediation="Implement encryption for sensitive data per A.8.24"
                ),
                "insufficient_logging": ComplianceMapping(
                    framework="ISO 27001:2022",
                    control_id="A.8.15",
                    control_name="Logging",
                    description="Insufficient logging violates activity logging requirements",
                    severity="Medium",
                    remediation="Implement comprehensive logging per A.8.15"
                ),
            },
            "pci_dss": {
                "sql_injection": ComplianceMapping(
                    framework="PCI DSS 4.0",
                    control_id="Req 6.5.1",
                    control_name="Injection Flaws",
                    description="SQL injection is a prohibited injection flaw",
                    severity="Critical",
                    remediation="Implement parameterized queries and input validation"
                ),
                "xss": ComplianceMapping(
                    framework="PCI DSS 4.0",
                    control_id="Req 6.5.7",
                    control_name="Cross-Site Scripting (XSS)",
                    description="XSS attacks must be prevented in web applications",
                    severity="High",
                    remediation="Implement output encoding and input validation"
                ),
                "broken_auth": ComplianceMapping(
                    framework="PCI DSS 4.0",
                    control_id="Req 8.3",
                    control_name="Multi-Factor Authentication",
                    description="Weak authentication violates MFA requirements",
                    severity="Critical",
                    remediation="Implement MFA for all access to cardholder data environment"
                ),
                "sensitive_data_exposure": ComplianceMapping(
                    framework="PCI DSS 4.0",
                    control_id="Req 3.4",
                    control_name="PAN Storage",
                    description="Exposed sensitive data violates PAN protection requirements",
                    severity="Critical",
                    remediation="Render PAN unreadable using strong cryptography"
                ),
                "unencrypted_transmission": ComplianceMapping(
                    framework="PCI DSS 4.0",
                    control_id="Req 4.2",
                    control_name="Strong Cryptography",
                    description="Unencrypted transmission violates data protection requirements",
                    severity="High",
                    remediation="Use strong cryptography and security protocols (TLS 1.2+)"
                ),
            },
            "nist_csf": {
                "sql_injection": ComplianceMapping(
                    framework="NIST CSF 2.0",
                    control_id="PR.PS-01",
                    control_name="Secure Software Development",
                    description="SQL injection indicates insufficient secure coding practices",
                    severity="Critical",
                    remediation="Implement secure software development lifecycle (SSDLC)"
                ),
                "xss": ComplianceMapping(
                    framework="NIST CSF 2.0",
                    control_id="PR.PS-01",
                    control_name="Secure Software Development",
                    description="XSS indicates insufficient secure coding practices",
                    severity="High",
                    remediation="Implement secure coding practices and security testing"
                ),
                "broken_auth": ComplianceMapping(
                    framework="NIST CSF 2.0",
                    control_id="PR.AA-01",
                    control_name="Identities and Credentials",
                    description="Weak authentication violates identity management requirements",
                    severity="Critical",
                    remediation="Implement strong authentication mechanisms per PR.AA-01"
                ),
                "sensitive_data_exposure": ComplianceMapping(
                    framework="NIST CSF 2.0",
                    control_id="PR.DS-01",
                    control_name="Data-at-Rest Protection",
                    description="Data exposure violates data protection requirements",
                    severity="High",
                    remediation="Implement encryption and data loss prevention"
                ),
                "insufficient_logging": ComplianceMapping(
                    framework="NIST CSF 2.0",
                    control_id="DE.CM-01",
                    control_name="Continuous Monitoring",
                    description="Insufficient logging violates monitoring requirements",
                    severity="Medium",
                    remediation="Implement comprehensive monitoring and logging"
                ),
            },
        }
    
    def map_finding(self, vulnerability_type: str) -> Dict[str, ComplianceMapping]:
        """
        Map a finding to all supported compliance frameworks.
        
        Args:
            vulnerability_type: Type of vulnerability (e.g., "SQL Injection")
            
        Returns:
            Dict of framework -> ComplianceMapping
        """
        # Normalize the vulnerability type
        normalized = self._normalize_vulnerability(vulnerability_type)
        
        results = {}
        for framework, mappings in self.mappings.items():
            if normalized in mappings:
                results[framework] = mappings[normalized]
        
        return results
    
    def map_to_framework(
        self,
        vulnerability_type: str,
        framework: str
    ) -> Optional[ComplianceMapping]:
        """
        Map a finding to a specific framework.
        
        Args:
            vulnerability_type: Type of vulnerability
            framework: Target framework (owasp_top_10, iso_27001, etc.)
            
        Returns:
            ComplianceMapping or None
        """
        normalized = self._normalize_vulnerability(vulnerability_type)
        framework_lower = framework.lower().replace(" ", "_").replace("-", "_")
        
        if framework_lower in self.mappings:
            return self.mappings[framework_lower].get(normalized)
        
        return None
    
    def get_frameworks(self) -> List[str]:
        """Get list of supported compliance frameworks."""
        return [
            "OWASP Top 10 (2021)",
            "OWASP ASVS 4.0",
            "ISO 27001:2022",
            "PCI DSS 4.0",
            "NIST CSF 2.0",
            "CIS Controls v8",
            "BSI Grundschutz",
        ]
    
    def _normalize_vulnerability(self, vuln_type: str) -> str:
        """Normalize vulnerability type for matching."""
        vuln_lower = vuln_type.lower()
        
        # Common normalization mappings
        mappings = {
            "sql injection": "sql_injection",
            "sqli": "sql_injection",
            "sql_injection": "sql_injection",
            "xss": "xss",
            "cross-site scripting": "xss",
            "cross site scripting": "xss",
            "broken authentication": "broken_auth",
            "weak authentication": "broken_auth",
            "authentication failure": "broken_auth",
            "sensitive data exposure": "sensitive_data_exposure",
            "information disclosure": "sensitive_data_exposure",
            "data exposure": "sensitive_data_exposure",
            "xxe": "xxe",
            "xml external entity": "xxe",
            "broken access control": "broken_access_control",
            "access control": "broken_access_control",
            "idOR": "broken_access_control",
            "security misconfiguration": "security_misconfiguration",
            "misconfiguration": "security_misconfiguration",
            "csrf": "csrf",
            "cross-site request forgery": "csrf",
            "insecure deserialization": "insecure_deserialization",
            "deserialization": "insecure_deserialization",
            "insufficient logging": "insufficient_logging",
            "missing logging": "insufficient_logging",
            "unencrypted transmission": "unencrypted_transmission",
            "cleartext": "unencrypted_transmission",
        }
        
        return mappings.get(vuln_lower, vuln_lower.replace(" ", "_"))
    
    def generate_compliance_summary(
        self,
        findings: List[Dict],
        framework: str
    ) -> Dict:
        """
        Generate compliance summary for a list of findings.
        
        Args:
            findings: List of finding dictionaries
            framework: Target compliance framework
            
        Returns:
            Compliance summary with gaps and recommendations
        """
        mapped_findings = []
        unmapped_findings = []
        
        for finding in findings:
            mapping = self.map_to_framework(finding.get("vulnerability_type", ""), framework)
            if mapping:
                mapped_findings.append({
                    "finding": finding,
                    "mapping": mapping,
                })
            else:
                unmapped_findings.append(finding)
        
        # Calculate statistics
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for item in mapped_findings:
            severity = item["mapping"].severity
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Get unique controls
        controls = {}
        for item in mapped_findings:
            control_id = item["mapping"].control_id
            if control_id not in controls:
                controls[control_id] = {
                    "control_name": item["mapping"].control_name,
                    "findings": [],
                }
            controls[control_id]["findings"].append(item["finding"])
        
        return {
            "framework": framework,
            "summary": {
                "total_findings": len(findings),
                "mapped_findings": len(mapped_findings),
                "unmapped_findings": len(unmapped_findings),
                "severity_distribution": severity_counts,
                "affected_controls": len(controls),
            },
            "controls": controls,
            "unmapped": unmapped_findings,
            "compliance_gaps": [
                {
                    "control_id": control_id,
                    "control_name": info["control_name"],
                    "finding_count": len(info["findings"]),
                }
                for control_id, info in controls.items()
            ],
        }
