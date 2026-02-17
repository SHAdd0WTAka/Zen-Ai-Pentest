"""
Compliance Reporting Module

Generates compliance reports for various standards:
- ISO 27001
- SOC 2
- GDPR
- PCI DSS
- NIST Cybersecurity Framework
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .logger import AuditLogEntry, EventCategory


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    ISO27001 = "iso27001"
    SOC2 = "soc2"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"
    HIPAA = "hipaa"


@dataclass
class ComplianceControl:
    """Individual compliance control"""
    control_id: str
    standard: ComplianceStandard
    description: str
    requirement: str
    evidence_required: List[str]
    verification_method: str


@dataclass
class ComplianceFinding:
    """Compliance finding (pass/fail)"""
    control_id: str
    status: str  # "pass", "fail", "partial", "not_applicable"
    evidence_count: int
    findings: List[str]
    recommendations: List[str]
    severity: Optional[str] = None


class ComplianceReporter:
    """
    Generates compliance reports from audit logs

    Maps audit events to compliance controls and generates
    evidence packages for auditors.
    """

    # Control mappings for ISO 27001
    ISO27001_CONTROLS = {
        "A.9.1.2": ComplianceControl(
            control_id="A.9.1.2",
            standard=ComplianceStandard.ISO27001,
            description="Access to networks and network services",
            requirement="Users shall only be provided with access to the network and network services that they have been specifically authorized to use.",
            evidence_required=["authentication_logs", "authorization_logs"],
            verification_method="review_logs"
        ),
        "A.9.2.1": ComplianceControl(
            control_id="A.9.2.1",
            standard=ComplianceStandard.ISO27001,
            description="User registration and de-registration",
            requirement="A formal user registration and de-registration process shall be implemented.",
            evidence_required=["user_registration_logs", "user_deactivation_logs"],
            verification_method="review_logs"
        ),
        "A.9.4.1": ComplianceControl(
            control_id="A.9.4.1",
            standard=ComplianceStandard.ISO27001,
            description="Restriction of access to information",
            requirement="Access to information and application system functions shall be restricted in accordance with the access control policy.",
            evidence_required=["access_logs", "authorization_failures"],
            verification_method="review_logs"
        ),
        "A.9.4.2": ComplianceControl(
            control_id="A.9.4.2",
            standard=ComplianceStandard.ISO27001,
            description="Secure log-on procedures",
            requirement="Where required by the access control policy, access to systems and applications shall be controlled by a secure log-on procedure.",
            evidence_required=["authentication_logs", "failed_login_attempts"],
            verification_method="review_logs"
        ),
        "A.12.4.1": ComplianceControl(
            control_id="A.12.4.1",
            standard=ComplianceStandard.ISO27001,
            description="Event logging",
            requirement="Event logs recording user activities, exceptions, and information security events shall be produced and kept.",
            evidence_required=["audit_logs", "log_integrity_verification"],
            verification_method="review_logs"
        ),
        "A.12.4.2": ComplianceControl(
            control_id="A.12.4.2",
            standard=ComplianceStandard.ISO27001,
            description="Protection of log information",
            requirement="Logging facilities and log information shall be protected against tampering and unauthorized access.",
            evidence_required=["log_signatures", "access_control_logs"],
            verification_method="verify_integrity"
        ),
        "A.12.4.3": ComplianceControl(
            control_id="A.12.4.3",
            standard=ComplianceStandard.ISO27001,
            description="Administrator and operator logs",
            requirement="System administrator and system operator activities shall be logged.",
            evidence_required=["admin_logs", "privileged_access_logs"],
            verification_method="review_logs"
        ),
        "A.12.6.1": ComplianceControl(
            control_id="A.12.6.1",
            standard=ComplianceStandard.ISO27001,
            description="Management of technical vulnerabilities",
            requirement="Information about technical vulnerabilities of information systems being used shall be obtained, the organization's exposure to such vulnerabilities evaluated, and appropriate measures taken.",
            evidence_required=["vulnerability_scans", "remediation_logs"],
            verification_method="review_evidence"
        ),
        "A.16.1.1": ComplianceControl(
            control_id="A.16.1.1",
            standard=ComplianceStandard.ISO27001,
            description="Responsibilities and procedures",
            requirement="Management responsibilities and procedures shall be established to ensure a quick, effective, and orderly response to information security incidents.",
            evidence_required=["incident_logs", "response_procedures"],
            verification_method="review_evidence"
        ),
        "A.16.1.4": ComplianceControl(
            control_id="A.16.1.4",
            standard=ComplianceStandard.ISO27001,
            description="Assessment of and decision on information security events",
            requirement="Information security events shall be assessed and decisions made on how they should be classified and handled.",
            evidence_required=["security_event_logs", "incident_classification"],
            verification_method="review_logs"
        ),
    }

    # GDPR Article mappings
    GDPR_CONTROLS = {
        "Art.5": ComplianceControl(
            control_id="Art.5",
            standard=ComplianceStandard.GDPR,
            description="Principles relating to processing of personal data",
            requirement="Personal data shall be processed lawfully, fairly and transparently.",
            evidence_required=["data_access_logs", "consent_logs"],
            verification_method="review_logs"
        ),
        "Art.17": ComplianceControl(
            control_id="Art.17",
            standard=ComplianceStandard.GDPR,
            description="Right to erasure ('right to be forgotten')",
            requirement="Data subject rights for erasure must be honored.",
            evidence_required=["deletion_logs", "verification_logs"],
            verification_method="review_logs"
        ),
        "Art.32": ComplianceControl(
            control_id="Art.32",
            standard=ComplianceStandard.GDPR,
            description="Security of processing",
            requirement="Appropriate technical and organizational measures to ensure security.",
            evidence_required=["security_logs", "access_controls", "encryption_logs"],
            verification_method="review_evidence"
        ),
        "Art.33": ComplianceControl(
            control_id="Art.33",
            standard=ComplianceStandard.GDPR,
            description="Notification of personal data breach",
            requirement="Breach notification within 72 hours.",
            evidence_required=["breach_logs", "notification_logs"],
            verification_method="review_logs"
        ),
    }

    # PCI DSS Requirements
    PCI_DSS_CONTROLS = {
        "Req.10.1": ComplianceControl(
            control_id="Req.10.1",
            standard=ComplianceStandard.PCI_DSS,
            description="Audit trails linking access to system components",
            requirement="Implement audit trails linking all access to system components to each individual user.",
            evidence_required=["access_logs", "user_identification"],
            verification_method="review_logs"
        ),
        "Req.10.2": ComplianceControl(
            control_id="Req.10.2",
            standard=ComplianceStandard.PCI_DSS,
            description="Audit trail entries",
            requirement="Implement automated audit trails for all system components.",
            evidence_required=["audit_logs", "log_completeness"],
            verification_method="review_logs"
        ),
        "Req.10.3": ComplianceControl(
            control_id="Req.10.3",
            standard=ComplianceStandard.PCI_DSS,
            description="Record audit trail entries",
            requirement="Record specific data elements for each event.",
            evidence_required=["audit_logs", "data_elements"],
            verification_method="review_logs"
        ),
        "Req.10.5": ComplianceControl(
            control_id="Req.10.5",
            standard=ComplianceStandard.PCI_DSS,
            description="Secure audit trails so they cannot be altered",
            requirement="Protect audit trail files from unauthorized modifications.",
            evidence_required=["log_integrity", "access_controls"],
            verification_method="verify_integrity"
        ),
    }

    def __init__(self, audit_logger):
        self.audit_logger = audit_logger
        self.all_controls = {
            **self.ISO27001_CONTROLS,
            **self.GDPR_CONTROLS,
            **self.PCI_DSS_CONTROLS,
        }

    async def generate_report(
        self,
        standard: ComplianceStandard,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **filters
    ) -> Dict[str, Any]:
        """
        Generate compliance report for a specific standard

        Args:
            standard: Compliance standard to report on
            start_date: Report period start
            end_date: Report period end
            **filters: Additional filters

        Returns:
            Compliance report dictionary
        """
        # Default to last 90 days
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # Get controls for this standard
        controls = self._get_controls_for_standard(standard)

        # Get audit logs for period
        logs = await self.audit_logger.query(
            start_time=start_date,
            end_time=end_date,
            limit=10000
        )

        # Evaluate each control
        findings = []
        for control in controls:
            finding = await self._evaluate_control(control, logs)
            findings.append(finding)

        # Calculate metrics
        total = len(findings)
        passed = sum(1 for f in findings if f.status == "pass")
        failed = sum(1 for f in findings if f.status == "fail")
        partial = sum(1 for f in findings if f.status == "partial")

        # Generate report
        report = {
            "report_id": f"COMPLIANCE-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "standard": standard.value,
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_controls": total,
                "passed": passed,
                "failed": failed,
                "partial": partial,
                "compliance_rate": (passed / total * 100) if total > 0 else 0
            },
            "findings": [self._finding_to_dict(f) for f in findings],
            "evidence_package": await self._generate_evidence_package(
                standard, logs, findings
            )
        }

        return report

    def _get_controls_for_standard(self, standard: ComplianceStandard) -> List[ComplianceControl]:
        """Get all controls for a compliance standard"""
        return [
            control for control in self.all_controls.values()
            if control.standard == standard
        ]

    async def _evaluate_control(
        self,
        control: ComplianceControl,
        logs: List[AuditLogEntry]
    ) -> ComplianceFinding:
        """Evaluate a single control against audit logs"""

        # Filter logs for this control's evidence
        relevant_logs = self._filter_logs_for_control(control, logs)

        # Check based on verification method
        if control.verification_method == "review_logs":
            return self._evaluate_log_review(control, relevant_logs)
        elif control.verification_method == "verify_integrity":
            return await self._evaluate_integrity(control, relevant_logs)
        elif control.verification_method == "review_evidence":
            return self._evaluate_evidence(control, relevant_logs)

        return ComplianceFinding(
            control_id=control.control_id,
            status="not_applicable",
            evidence_count=len(relevant_logs),
            findings=["Unknown verification method"],
            recommendations=["Configure verification method"]
        )

    def _filter_logs_for_control(
        self,
        control: ComplianceControl,
        logs: List[AuditLogEntry]
    ) -> List[AuditLogEntry]:
        """Filter logs relevant to a control"""
        relevant = []

        for log in logs:
            # Match by category
            if log.category == EventCategory.AUTHENTICATION.value:
                if "authentication" in control.evidence_required:
                    relevant.append(log)
            elif log.category == EventCategory.AUTHORIZATION.value:
                if "authorization" in control.evidence_required:
                    relevant.append(log)
            elif log.category == EventCategory.DATA_ACCESS.value:
                if "access" in control.evidence_required:
                    relevant.append(log)
            elif log.category == EventCategory.SECURITY.value:
                if "security" in control.evidence_required:
                    relevant.append(log)
            elif log.category == EventCategory.SYSTEM.value:
                if "admin" in control.evidence_required:
                    relevant.append(log)

        return relevant

    def _evaluate_log_review(
        self,
        control: ComplianceControl,
        logs: List[AuditLogEntry]
    ) -> ComplianceFinding:
        """Evaluate control based on log review"""
        findings = []
        recommendations = []

        if not logs:
            return ComplianceFinding(
                control_id=control.control_id,
                status="fail",
                evidence_count=0,
                findings=["No audit logs found for this control"],
                recommendations=["Enable logging for this control area"],
                severity="high"
            )

        # Check for required evidence
        evidence_found = set()
        for log in logs:
            if log.category == EventCategory.AUTHENTICATION.value:
                evidence_found.add("authentication_logs")
            elif log.category == EventCategory.AUTHORIZATION.value:
                evidence_found.add("authorization_logs")
            elif log.category == EventCategory.DATA_ACCESS.value:
                evidence_found.add("access_logs")

        missing_evidence = set(control.evidence_required) - evidence_found

        if missing_evidence:
            findings.append(f"Missing evidence: {', '.join(missing_evidence)}")
            recommendations.append(f"Collect: {', '.join(missing_evidence)}")

        # Determine status
        if len(missing_evidence) == 0:
            status = "pass"
        elif len(missing_evidence) < len(control.evidence_required) / 2:
            status = "partial"
        else:
            status = "fail"

        return ComplianceFinding(
            control_id=control.control_id,
            status=status,
            evidence_count=len(logs),
            findings=findings,
            recommendations=recommendations,
            severity="medium" if status == "fail" else None
        )

    async def _evaluate_integrity(
        self,
        control: ComplianceControl,
        logs: List[AuditLogEntry]
    ) -> ComplianceFinding:
        """Evaluate log integrity"""
        findings = []
        recommendations = []

        if not logs:
            return ComplianceFinding(
                control_id=control.control_id,
                status="fail",
                evidence_count=0,
                findings=["No logs to verify"],
                recommendations=["Enable logging"],
                severity="high"
            )

        # Check for signatures
        unsigned = sum(1 for log in logs if not log.signature)
        if unsigned > 0:
            findings.append(f"{unsigned} logs without signatures")
            recommendations.append("Enable log signing")

        # Verify chain integrity
        integrity_result = await self.audit_logger.verify_integrity()
        if integrity_result.get("chain_breaks", 0) > 0:
            findings.append(f"{integrity_result['chain_breaks']} chain breaks detected")
            recommendations.append("Investigate log tampering")

        if integrity_result.get("invalid_signatures", 0) > 0:
            findings.append(f"{integrity_result['invalid_signatures']} invalid signatures")
            recommendations.append("Review signing keys and process")

        status = "pass" if not findings else "fail"

        return ComplianceFinding(
            control_id=control.control_id,
            status=status,
            evidence_count=len(logs),
            findings=findings,
            recommendations=recommendations,
            severity="critical" if status == "fail" else None
        )

    def _evaluate_evidence(
        self,
        control: ComplianceControl,
        logs: List[AuditLogEntry]
    ) -> ComplianceFinding:
        """Evaluate control based on evidence"""
        # Simplified evidence evaluation
        if logs:
            return ComplianceFinding(
                control_id=control.control_id,
                status="pass",
                evidence_count=len(logs),
                findings=[],
                recommendations=[]
            )
        else:
            return ComplianceFinding(
                control_id=control.control_id,
                status="fail",
                evidence_count=0,
                findings=["No evidence found"],
                recommendations=["Collect required evidence"],
                severity="medium"
            )

    def _finding_to_dict(self, finding: ComplianceFinding) -> Dict[str, Any]:
        """Convert finding to dictionary"""
        return {
            "control_id": finding.control_id,
            "status": finding.status,
            "evidence_count": finding.evidence_count,
            "findings": finding.findings,
            "recommendations": finding.recommendations,
            "severity": finding.severity
        }

    async def _generate_evidence_package(
        self,
        standard: ComplianceStandard,
        logs: List[AuditLogEntry],
        findings: List[ComplianceFinding]
    ) -> Dict[str, Any]:
        """Generate evidence package for auditors"""
        return {
            "log_summary": {
                "total_events": len(logs),
                "by_category": self._summarize_by_category(logs),
                "by_level": self._summarize_by_level(logs),
            },
            "integrity_verification": await self.audit_logger.verify_integrity(),
            "sample_logs": [log.to_dict() for log in logs[:10]],
            "control_mapping": {
                f.control_id: {
                    "status": f.status,
                    "evidence_count": f.evidence_count
                }
                for f in findings
            }
        }

    def _summarize_by_category(self, logs: List[AuditLogEntry]) -> Dict[str, int]:
        """Summarize logs by category"""
        summary = {}
        for log in logs:
            summary[log.category] = summary.get(log.category, 0) + 1
        return summary

    def _summarize_by_level(self, logs: List[AuditLogEntry]) -> Dict[str, int]:
        """Summarize logs by level"""
        summary = {}
        for log in logs:
            summary[log.level] = summary.get(log.level, 0) + 1
        return summary

    async def export_report(
        self,
        report: Dict[str, Any],
        format: str = "json"
    ) -> str:
        """Export report to various formats"""
        if format == "json":
            return json.dumps(report, indent=2, default=str)

        elif format == "markdown":
            return self._to_markdown(report)

        elif format == "csv":
            return self._to_csv(report)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report to Markdown"""
        md = f"""# Compliance Report

**Standard:** {report['standard']}
**Generated:** {report['generated_at']}
**Period:** {report['period']['start']} to {report['period']['end']}

## Summary

| Metric | Value |
|--------|-------|
| Total Controls | {report['summary']['total_controls']} |
| Passed | {report['summary']['passed']} ✅ |
| Failed | {report['summary']['failed']} ❌ |
| Partial | {report['summary']['partial']} ⚠️ |
| **Compliance Rate** | **{report['summary']['compliance_rate']:.1f}%** |

## Findings

| Control | Status | Evidence | Findings |
|---------|--------|----------|----------|
"""
        for finding in report['findings']:
            status_icon = "✅" if finding['status'] == "pass" else "❌" if finding['status'] == "fail" else "⚠️"
            md += f"| {finding['control_id']} | {status_icon} {finding['status']} | {finding['evidence_count']} | {len(finding['findings'])} |\n"

        md += "\n## Detailed Findings\n\n"
        for finding in report['findings']:
            if finding['findings']:
                md += f"### {finding['control_id']}\n\n"
                md += f"**Status:** {finding['status']}\n\n"
                md += "**Findings:**\n"
                for f in finding['findings']:
                    md += f"- {f}\n"
                md += "\n**Recommendations:**\n"
                for r in finding['recommendations']:
                    md += f"- {r}\n"
                md += "\n"

        return md

    def _to_csv(self, report: Dict[str, Any]) -> str:
        """Convert report to CSV"""
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "control_id", "status", "evidence_count", "findings", "recommendations", "severity"
        ])

        # Data
        for finding in report['findings']:
            writer.writerow([
                finding['control_id'],
                finding['status'],
                finding['evidence_count'],
                "; ".join(finding['findings']),
                "; ".join(finding['recommendations']),
                finding.get('severity', '')
            ])

        return output.getvalue()
