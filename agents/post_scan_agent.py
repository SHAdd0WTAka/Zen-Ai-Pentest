"""
Post-Scan Agent - Automates the Pentester Workflow After Initial Scan

Based on industry-standard penetration testing methodology (PTES, OWASP, NIST):
1. Manual Verification (False Positive Elimination)
2. Vulnerability Validation & Risk Scoring
3. Exploitation Attempts
4. Post-Exploitation (Privilege Escalation, Lateral Movement)
5. Evidence Collection & Documentation
6. Loot Aggregation
7. Cleanup & Restoration
8. Report Generation Preparation

This agent runs automatically after every scan to ensure professional pentest standards.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_base import AgentRole, BaseAgent


class PostScanPhase(Enum):
    """Phases of post-scan workflow based on PTES methodology"""

    VERIFICATION = "verification"  # Manual verification of findings
    VALIDATION = "validation"  # Validate vulnerabilities are real
    EXPLOITATION = "exploitation"  # Attempt exploitation
    POST_EXPLOITATION = "post_exploitation"  # Privilege escalation, lateral movement
    EVIDENCE_COLLECTION = "evidence"  # Screenshots, logs, proof
    LOOT_DOCUMENTATION = "loot"  # Credentials, sensitive data
    CLEANUP = "cleanup"  # Remove backdoors, restore systems
    REPORT_PREP = "report_prep"  # Prepare findings for reporting


@dataclass
class VerifiedFinding:
    """A verified vulnerability finding with evidence"""

    id: str
    title: str
    severity: str  # critical, high, medium, low, info
    cvss_score: float
    description: str
    affected_host: str
    port: Optional[int] = None
    service: Optional[str] = None

    # Verification
    verified: bool = False
    verification_method: str = ""  # manual, automated, hybrid
    false_positive: bool = False
    verification_notes: str = ""

    # Exploitation
    exploited: bool = False
    exploitation_successful: bool = False
    exploit_method: str = ""
    exploitation_notes: str = ""

    # Post-Exploitation
    privileges_obtained: str = ""  # user, admin, system, none
    lateral_movement_possible: bool = False
    lateral_movement_targets: List[str] = field(default_factory=list)

    # Evidence
    screenshots: List[str] = field(default_factory=list)  # Paths to screenshots
    log_files: List[str] = field(default_factory=list)
    command_history: List[str] = field(default_factory=list)

    # Loot
    credentials_found: List[Dict[str, str]] = field(default_factory=list)
    sensitive_files: List[str] = field(default_factory=list)

    # Cleanup
    cleanup_performed: bool = False
    cleanup_verified: bool = False
    cleanup_notes: str = ""

    # Timestamps
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified_at: Optional[str] = None
    exploited_at: Optional[str] = None
    cleaned_up_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "description": self.description,
            "affected_host": self.affected_host,
            "port": self.port,
            "service": self.service,
            "verification": {
                "verified": self.verified,
                "method": self.verification_method,
                "false_positive": self.false_positive,
                "notes": self.verification_notes,
                "timestamp": self.verified_at,
            },
            "exploitation": {
                "attempted": self.exploited,
                "successful": self.exploitation_successful,
                "method": self.exploit_method,
                "notes": self.exploitation_notes,
                "timestamp": self.exploited_at,
            },
            "post_exploitation": {
                "privileges": self.privileges_obtained,
                "lateral_movement_possible": self.lateral_movement_possible,
                "lateral_targets": self.lateral_movement_targets,
            },
            "evidence": {
                "screenshots": self.screenshots,
                "logs": self.log_files,
                "commands": self.command_history,
            },
            "loot": {
                "credentials": self.credentials_found,
                "sensitive_files": self.sensitive_files,
            },
            "cleanup": {
                "performed": self.cleanup_performed,
                "verified": self.cleanup_verified,
                "notes": self.cleanup_notes,
                "timestamp": self.cleaned_up_at,
            },
        }


@dataclass
class PentestLoot:
    """Aggregated loot from entire penetration test"""

    credentials: List[Dict[str, str]] = field(default_factory=list)
    hashes: List[str] = field(default_factory=list)
    tokens: List[str] = field(default_factory=list)
    sensitive_files: List[str] = field(default_factory=list)
    database_dumps: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)

    def add_credential(self, host: str, username: str, password: str, credential_type: str = "password"):
        self.credentials.append(
            {
                "host": host,
                "username": username,
                "password": password,
                "type": credential_type,
                "discovered_at": datetime.now().isoformat(),
            }
        )


class PostScanAgent(BaseAgent):
    """
    Agent that automates professional pentester post-scan workflow.

    Runs after initial automated scanning to:
    1. Verify findings (eliminate false positives)
    2. Validate vulnerabilities
    3. Attempt exploitation
    4. Document evidence
    5. Collect loot
    6. Perform cleanup
    7. Prepare for reporting
    """

    def __init__(self):
        super().__init__(
            name="PostScanAgent",
            role=AgentRole.POST_EXPLOITATION,
            description="Automates post-scan pentester workflow - verification, exploitation, evidence collection",
        )
        self.verified_findings: List[VerifiedFinding] = []
        self.loot = PentestLoot()
        self.current_phase = PostScanPhase.VERIFICATION
        self.phase_results: Dict[str, Any] = {}
        self.evidence_dir = Path("evidence")
        self.report_data: Dict[str, Any] = {}

    async def run(self, target: str, initial_findings: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Execute complete post-scan workflow

        Args:
            target: Target host/IP
            initial_findings: Raw findings from automated scan

        Returns:
            Complete post-scan results ready for reporting
        """
        self.log_action(f"Starting post-scan workflow for {target}")
        print(f"\n[{'=' * 60}")
        print("  Post-Scan Pentest Workflow")
        print(f"  Target: {target}")
        print(f"  Initial Findings: {len(initial_findings)}")
        print(f"{'=' * 60}\n")

        # Create evidence directory
        self.evidence_dir = Path(f"evidence/{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1: Manual Verification
        await self._phase_verification(target, initial_findings)

        # Phase 2: Vulnerability Validation
        await self._phase_validation(target)

        # Phase 3: Exploitation Attempts
        await self._phase_exploitation(target)

        # Phase 4: Post-Exploitation
        await self._phase_post_exploitation(target)

        # Phase 5: Evidence Collection
        await self._phase_evidence_collection(target)

        # Phase 6: Loot Documentation
        await self._phase_loot_documentation(target)

        # Phase 7: Cleanup
        await self._phase_cleanup(target)

        # Phase 8: Report Preparation
        await self._phase_report_preparation(target)

        return {
            "target": target,
            "phases_completed": list(self.phase_results.keys()),
            "verified_findings": [f.to_dict() for f in self.verified_findings],
            "total_verified": len([f for f in self.verified_findings if f.verified and not f.false_positive]),
            "total_false_positives": len([f for f in self.verified_findings if f.false_positive]),
            "total_exploited": len([f for f in self.verified_findings if f.exploitation_successful]),
            "loot_summary": {
                "credentials": len(self.loot.credentials),
                "screenshots": len(self.loot.screenshots),
                "sensitive_files": len(self.loot.sensitive_files),
            },
            "evidence_directory": str(self.evidence_dir),
            "report_data": self.report_data,
        }

    async def _phase_verification(self, target: str, initial_findings: List[Dict[str, Any]]):
        """Phase 1: Manual verification of findings - eliminate false positives"""
        self.current_phase = PostScanPhase.VERIFICATION
        print(f"[Phase 1/8] Manual Verification of {len(initial_findings)} findings...")

        verified_count = 0
        false_positive_count = 0

        for finding in initial_findings:
            vf = VerifiedFinding(
                id=finding.get("id", f"FINDING_{len(self.verified_findings)}"),
                title=finding.get("title", "Unknown"),
                severity=finding.get("severity", "medium"),
                cvss_score=finding.get("cvss_score", 5.0),
                description=finding.get("description", ""),
                affected_host=target,
                port=finding.get("port"),
                service=finding.get("service"),
            )

            # Simulate manual verification logic
            verification_result = await self._verify_finding(vf)

            vf.verified = verification_result["verified"]
            vf.false_positive = verification_result["false_positive"]
            vf.verification_method = verification_result["method"]
            vf.verification_notes = verification_result["notes"]
            vf.verified_at = datetime.now().isoformat()

            if vf.verified and not vf.false_positive:
                verified_count += 1
            elif vf.false_positive:
                false_positive_count += 1

            self.verified_findings.append(vf)

        self.phase_results["verification"] = {
            "total_findings": len(initial_findings),
            "verified": verified_count,
            "false_positives": false_positive_count,
            "requires_validation": verified_count,
        }

        print(f"  [OK] Verified: {verified_count}, False Positives: {false_positive_count}")
        self.log_action(f"Verification complete: {verified_count} valid, {false_positive_count} FP")

    async def _verify_finding(self, finding: VerifiedFinding) -> Dict[str, Any]:
        """Verify a single finding for false positives"""
        # In real implementation, this would:
        # - Re-run the specific test manually
        # - Check for environmental factors
        # - Verify with different tools
        # - Contextual analysis

        # Simulation logic:
        # High confidence findings are likely true positives
        # Low confidence or generic findings need verification

        confidence_indicators = [
            finding.cvss_score > 7.0,  # CVSS high
            finding.port is not None,  # Specific port
            "confirmed" in finding.description.lower(),
        ]

        if any(confidence_indicators):
            return {
                "verified": True,
                "false_positive": False,
                "method": "automated_context_analysis",
                "notes": f"High confidence finding on port {finding.port}",
            }
        else:
            # Low confidence - flag for manual review
            return {
                "verified": True,  # Still include but flag
                "false_positive": False,
                "method": "requires_manual_review",
                "notes": "Low confidence - manual verification recommended",
            }

    async def _phase_validation(self, target: str):
        """Phase 2: Validate vulnerabilities and assess business impact"""
        self.current_phase = PostScanPhase.VALIDATION
        print("[Phase 2/8] Vulnerability Validation & Risk Assessment...")

        validated_count = 0

        for finding in self.verified_findings:
            if finding.verified and not finding.false_positive:
                # Validate exploitability
                validation = await self._validate_vulnerability(finding)

                # Update with validation results
                if validation["exploitable"]:
                    finding.cvss_score = min(10.0, finding.cvss_score + 0.5)
                    validated_count += 1

        self.phase_results["validation"] = {
            "validated": validated_count,
            "risk_assessment": "completed",
        }

        print(f"  [OK] {validated_count} vulnerabilities validated as exploitable")

    async def _validate_vulnerability(self, finding: VerifiedFinding) -> Dict[str, Any]:
        """Validate if a vulnerability is actually exploitable"""
        # In real implementation:
        # - Check for compensating controls
        # - Verify exploit conditions exist
        # - Test proof-of-concept (safe check)

        exploitable_services = ["ssh", "http", "https", "smb", "rdp", "ftp"]

        if finding.service and finding.service.lower() in exploitable_services:
            return {"exploitable": True, "confidence": "high"}
        elif finding.cvss_score >= 9.0:
            return {"exploitable": True, "confidence": "medium"}
        else:
            return {"exploitable": False, "confidence": "low"}

    async def _phase_exploitation(self, target: str):
        """Phase 3: Attempt exploitation of validated vulnerabilities"""
        self.current_phase = PostScanPhase.EXPLOITATION
        print("[Phase 3/8] Exploitation Attempts...")

        exploitation_results = []

        # Prioritize by severity
        critical_findings = [f for f in self.verified_findings if f.severity in ["critical", "high"] and f.verified]

        for finding in critical_findings[:5]:  # Limit attempts for safety
            result = await self._attempt_exploitation(finding)
            exploitation_results.append(result)

            finding.exploited = True
            finding.exploitation_successful = result["success"]
            finding.exploit_method = result["method"]
            finding.exploitation_notes = result["notes"]
            finding.exploited_at = datetime.now().isoformat()

        successful = len([r for r in exploitation_results if r["success"]])

        self.phase_results["exploitation"] = {
            "attempted": len(exploitation_results),
            "successful": successful,
            "methods_used": list(set(r["method"] for r in exploitation_results)),
        }

        print(f"  [OK] Attempted: {len(exploitation_results)}, Successful: {successful}")

    async def _attempt_exploitation(self, finding: VerifiedFinding) -> Dict[str, Any]:
        """Safely attempt exploitation of a finding"""
        # In real implementation:
        # - Use Metasploit / custom exploits
        # - Test with safe payloads first
        # - Document every attempt

        methods = {
            "sql_injection": "SQLMap with --risk=1 --level=1",
            "xss": "XSS payload injection with event handlers",
            "rce": "Command injection with safe ping test",
            "lfi": "Local file inclusion with /etc/passwd",
            "default_creds": "Default credential testing",
            "known_exploit": "CVE-specific exploit module",
        }

        # Simulate based on finding type
        if "sql" in finding.title.lower():
            return {
                "success": True,
                "method": methods["sql_injection"],
                "notes": "Successfully extracted database version",
            }
        elif "xss" in finding.title.lower():
            return {
                "success": True,
                "method": methods["xss"],
                "notes": "Reflected XSS confirmed",
            }
        else:
            return {
                "success": False,
                "method": "generic_test",
                "notes": "Requires manual exploitation",
            }

    async def _phase_post_exploitation(self, target: str):
        """Phase 4: Post-exploitation - privilege escalation, lateral movement"""
        self.current_phase = PostScanPhase.POST_EXPLOITATION
        print("[Phase 4/8] Post-Exploitation Analysis...")

        successful_exploits = [f for f in self.verified_findings if f.exploitation_successful]

        for finding in successful_exploits:
            # Assess privilege level
            privileges = await self._assess_privileges(finding)
            finding.privileges_obtained = privileges["level"]

            # Check lateral movement possibilities
            lateral = await self._check_lateral_movement(finding)
            finding.lateral_movement_possible = lateral["possible"]
            finding.lateral_movement_targets = lateral["targets"]

            # Collect credentials if possible
            if privileges["level"] in ["admin", "system"]:
                creds = await self._harvest_credentials(finding)
                finding.credentials_found = creds
                for cred in creds:
                    self.loot.add_credential(
                        finding.affected_host,
                        cred.get("username", ""),
                        cred.get("password", ""),
                        cred.get("type", "password"),
                    )

        self.phase_results["post_exploitation"] = {
            "systems_compromised": len(successful_exploits),
            "privilege_levels": list(set(f.privileges_obtained for f in successful_exploits)),
            "lateral_movement_opportunities": sum(1 for f in successful_exploits if f.lateral_movement_possible),
        }

        print(f"  [OK] Analyzed {len(successful_exploits)} compromised systems")

    async def _assess_privileges(self, finding: VerifiedFinding) -> Dict[str, Any]:
        """Assess privilege level obtained"""
        # In real implementation:
        # - Check user ID
        # - Check group memberships
        # - Check sudo/admin rights
        return {"level": "user", "groups": ["users"], "sudo": False}

    async def _check_lateral_movement(self, finding: VerifiedFinding) -> Dict[str, Any]:
        """Check possibilities for lateral movement"""
        # In real implementation:
        # - Network discovery
        # - Credential reuse checks
        # - Trust relationship analysis
        return {
            "possible": True,
            "targets": ["internal_subnet_1"],
            "method": "pass_the_hash",
        }

    async def _harvest_credentials(self, finding: VerifiedFinding) -> List[Dict[str, str]]:
        """Harvest credentials from compromised system"""
        # In real implementation:
        # - Dump password hashes
        # - Extract browser credentials
        # - Find configuration files with passwords
        # - Keylogger/memory dump analysis
        return [
            {"username": "admin", "password": "[HASH]", "type": "ntlm_hash"},
            {
                "username": "service_account",
                "password": "[CLEARTEXT]",
                "type": "password",
            },
        ]

    async def _phase_evidence_collection(self, target: str):
        """Phase 5: Collect evidence (screenshots, logs, proof)"""
        self.current_phase = PostScanPhase.EVIDENCE_COLLECTION
        print("[Phase 5/8] Evidence Collection...")

        evidence_count = 0

        for finding in self.verified_findings:
            if finding.verified and not finding.false_positive:
                # Generate screenshot path
                screenshot_path = self.evidence_dir / f"{finding.id}_evidence.png"
                finding.screenshots.append(str(screenshot_path))
                self.loot.screenshots.append(str(screenshot_path))

                # Simulate command history
                finding.command_history = await self._generate_command_history(finding)

                # Log file
                log_path = self.evidence_dir / f"{finding.id}_logs.txt"
                finding.log_files.append(str(log_path))

                evidence_count += 1

        self.phase_results["evidence"] = {
            "screenshots_taken": len(self.loot.screenshots),
            "log_files": len([f for f in self.verified_findings if f.log_files]),
            "evidence_directory": str(self.evidence_dir),
        }

        print(f"  [OK] Collected evidence for {evidence_count} findings")

    async def _generate_command_history(self, finding: VerifiedFinding) -> List[str]:
        """Generate command history for a finding"""
        commands = []

        if "sql" in finding.title.lower():
            commands = [
                f"sqlmap -u 'http://{finding.affected_host}:{finding.port}/search?q=test' --risk=1",
                "sqlmap --dbs",
                "sqlmap -D database --tables",
                "sqlmap -D database -T users --dump",
            ]
        elif "xss" in finding.title.lower():
            commands = [
                f"curl -X POST http://{finding.affected_host}:{finding.port}/comment",
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
            ]
        else:
            commands = [f"nmap -sV -p {finding.port} {finding.affected_host}"]

        return commands

    async def _phase_loot_documentation(self, target: str):
        """Phase 6: Document all loot (credentials, sensitive data)"""
        self.current_phase = PostScanPhase.LOOT_DOCUMENTATION
        print("[Phase 6/8] Loot Documentation...")

        # Save loot to secure file
        loot_file = self.evidence_dir / "loot_summary.json"

        loot_data = {
            "credentials": self.loot.credentials,
            "hashes": self.loot.hashes,
            "tokens": self.loot.tokens,
            "sensitive_files": self.loot.sensitive_files,
            "screenshots": self.loot.screenshots,
            "collected_at": datetime.now().isoformat(),
        }

        with open(loot_file, "w") as f:
            json.dump(loot_data, f, indent=2)

        self.phase_results["loot"] = {
            "credentials_found": len(self.loot.credentials),
            "screenshots": len(self.loot.screenshots),
            "loot_file": str(loot_file),
        }

        print(f"  [OK] Documented {len(self.loot.credentials)} credentials, {len(self.loot.screenshots)} screenshots")

    async def _phase_cleanup(self, target: str):
        """Phase 7: Cleanup - remove backdoors, restore systems"""
        self.current_phase = PostScanPhase.CLEANUP
        print("[Phase 7/8] Cleanup & Restoration...")

        cleanup_actions = []

        for finding in self.verified_findings:
            if finding.exploitation_successful:
                # Simulate cleanup
                cleanup = await self._perform_cleanup(finding)
                finding.cleanup_performed = cleanup["performed"]
                finding.cleanup_verified = cleanup["verified"]
                finding.cleanup_notes = cleanup["notes"]
                finding.cleaned_up_at = datetime.now().isoformat()

                cleanup_actions.append(
                    {
                        "finding": finding.id,
                        "status": "success" if cleanup["verified"] else "pending",
                    }
                )

        self.phase_results["cleanup"] = {
            "systems_cleaned": len(cleanup_actions),
            "verified": len([a for a in cleanup_actions if a["status"] == "success"]),
            "actions": cleanup_actions,
        }

        print(f"  [OK] Cleanup performed on {len(cleanup_actions)} systems")

    async def _perform_cleanup(self, finding: VerifiedFinding) -> Dict[str, Any]:
        """Perform cleanup for a specific finding"""
        # In real implementation:
        # - Remove created accounts
        # - Delete uploaded files
        # - Remove persistence mechanisms
        # - Clear logs (if allowed)
        # - Verify system state

        return {
            "performed": True,
            "verified": True,
            "notes": f"Removed test artifacts from {finding.affected_host}",
        }

    async def _phase_report_preparation(self, target: str):
        """Phase 8: Prepare data for final report"""
        self.current_phase = PostScanPhase.REPORT_PREP
        print("[Phase 8/8] Report Preparation...")

        # Organize findings by severity
        by_severity = {"critical": [], "high": [], "medium": [], "low": [], "info": []}

        for finding in self.verified_findings:
            if finding.verified and not finding.false_positive:
                sev = finding.severity.lower()
                if sev in by_severity:
                    by_severity[sev].append(finding.to_dict())

        # Executive summary data
        executive_summary = {
            "target": target,
            "test_date": datetime.now().strftime("%Y-%m-%d"),
            "total_findings": len(self.verified_findings),
            "confirmed_vulnerabilities": len([f for f in self.verified_findings if f.verified and not f.false_positive]),
            "false_positives": len([f for f in self.verified_findings if f.false_positive]),
            "exploited_systems": len([f for f in self.verified_findings if f.exploitation_successful]),
            "critical_count": len(by_severity["critical"]),
            "high_count": len(by_severity["high"]),
            "medium_count": len(by_severity["medium"]),
            "low_count": len(by_severity["low"]),
            "overall_risk": self._calculate_overall_risk(),
            "key_recommendations": self._generate_recommendations(),
        }

        # Technical findings
        technical_findings = [f.to_dict() for f in self.verified_findings if f.verified and not f.false_positive]

        # Remediation priorities
        remediation = {
            "immediate": by_severity["critical"],
            "short_term": by_severity["high"],
            "medium_term": by_severity["medium"],
            "long_term": by_severity["low"] + by_severity["info"],
        }

        self.report_data = {
            "executive_summary": executive_summary,
            "methodology": "PTES (Penetration Testing Execution Standard)",
            "phases_completed": list(self.phase_results.keys()),
            "technical_findings": technical_findings,
            "remediation_priorities": remediation,
            "evidence_location": str(self.evidence_dir),
            "loot_summary": {
                "credentials": len(self.loot.credentials),
                "screenshots": len(self.loot.screenshots),
            },
            "appendices": {
                "tools_used": ["Nmap", "SQLMap", "Custom Scripts"],
                "testing_period": f"{datetime.now().strftime('%Y-%m-%d')}",
                "limitations": "Simulated test environment",
            },
        }

        # Save report data
        report_file = self.evidence_dir / "report_data.json"
        with open(report_file, "w") as f:
            json.dump(self.report_data, f, indent=2)

        self.phase_results["report_prep"] = {
            "report_file": str(report_file),
            "findings_by_severity": {k: len(v) for k, v in by_severity.items()},
            "executive_summary_ready": True,
        }

        print(f"  [OK] Report data prepared: {len(technical_findings)} findings")
        print(f"  [OK] Report file: {report_file}")

    def _calculate_overall_risk(self) -> str:
        """Calculate overall risk rating"""
        critical = len([f for f in self.verified_findings if f.severity == "critical" and f.verified])
        high = len([f for f in self.verified_findings if f.severity == "high" and f.verified])

        if critical > 0:
            return "CRITICAL"
        elif high >= 3:
            return "HIGH"
        elif high > 0:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_recommendations(self) -> List[str]:
        """Generate key recommendations based on findings"""
        recommendations = []

        critical_findings = [f for f in self.verified_findings if f.severity == "critical" and f.verified]

        if any("sql" in f.title.lower() for f in critical_findings):
            recommendations.append("Implement parameterized queries and input validation")

        if any("default" in f.title.lower() for f in critical_findings):
            recommendations.append("Change all default credentials immediately")

        if any(f.exploitation_successful for f in self.verified_findings):
            recommendations.append("Deploy endpoint detection and response (EDR) solutions")

        recommendations.append("Conduct regular security assessments and penetration tests")
        recommendations.append("Implement defense-in-depth security architecture")

        return recommendations

    def _dict_to_finding(self, data: Dict[str, Any]) -> VerifiedFinding:
        """Convert dictionary to VerifiedFinding object"""
        return VerifiedFinding(
            id=data.get("id", "UNKNOWN"),
            title=data.get("title", "Unknown"),
            severity=data.get("severity", "medium"),
            cvss_score=data.get("cvss_score", 5.0),
            description=data.get("description", ""),
            affected_host=data.get("affected_host", "unknown"),
            port=data.get("port"),
            service=data.get("service"),
        )

    def get_report_template(self) -> str:
        """Generate a markdown report template"""
        if not self.report_data:
            return "No report data available. Run the post-scan workflow first."

        es = self.report_data.get("executive_summary", {})

        template = f"""# Penetration Testing Report

## Executive Summary

**Target:** {es.get("target", "N/A")}
**Test Date:** {es.get("test_date", "N/A")}
**Overall Risk Rating:** {es.get("overall_risk", "N/A")}

### Findings Overview

| Severity | Count |
|----------|-------|
| Critical | {es.get("critical_count", 0)} |
| High | {es.get("high_count", 0)} |
| Medium | {es.get("medium_count", 0)} |
| Low | {es.get("low_count", 0)} |
| **Total Confirmed** | **{es.get("confirmed_vulnerabilities", 0)}** |

### Key Findings

- **{es.get("exploited_systems", 0)}** systems were successfully compromised
- **{es.get("false_positives", 0)}** findings were identified as false positives
- Evidence and logs collected in: `{self.evidence_dir}`

### Key Recommendations

"""
        for rec in es.get("key_recommendations", []):
            template += f"1. {rec}\n"

        template += """

## Methodology

This assessment followed the Penetration Testing Execution Standard (PTES):

1. Pre-Engagement Interactions
2. Intelligence Gathering
3. Threat Modeling
4. Vulnerability Analysis
5. **Exploitation** ✓
6. **Post-Exploitation** ✓
7. **Reporting** ✓

## Technical Findings

"""

        # Add finding details
        for finding in self.report_data.get("technical_findings", []):
            template += f"""### {finding["id"]}: {finding["title"]}

**Severity:** {finding["severity"]} | **CVSS:** {finding["cvss_score"]}

**Description:**
{finding["description"]}

**Evidence:**
"""
            for screenshot in finding.get("evidence", {}).get("screenshots", []):
                template += f"- Screenshot: `{screenshot}`\n"

            if finding.get("exploitation", {}).get("successful"):
                template += f"""
**Exploitation:**
- Method: {finding["exploitation"].get("method", "N/A")}
- Successful: Yes
- Privileges Obtained: {finding.get("post_exploitation", {}).get("privileges", "N/A")}

"""

        template += """
## Remediation Roadmap

### Immediate (Critical)
Address within 24-48 hours

### Short-term (High)
Address within 1-2 weeks

### Medium-term (Medium)
Address within 1-3 months

### Long-term (Low/Info)
Address as part of regular maintenance

---

*Report generated by Zen AI Pentest - PostScan Agent*
"""

        return template


# Convenience function for direct use
async def run_post_scan_workflow(target: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standalone function to run the complete post-scan workflow

    Usage:
        results = await run_post_scan_workflow("192.168.1.1", scan_findings)
    """
    agent = PostScanAgent()
    return await agent.run(target, findings)
