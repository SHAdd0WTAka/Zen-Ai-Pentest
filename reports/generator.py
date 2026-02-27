"""
Report Generator

Main class for generating penetration test reports.

Usage:
    generator = ReportGenerator()
    
    # Generate executive summary
    report = generator.generate_executive_report(
        scan_id="scan-123",
        company_name="ACME Corp",
        output_path="reports/executive.pdf"
    )
    
    # Generate technical report
    report = generator.generate_technical_report(
        scan_id="scan-123",
        output_path="reports/technical.pdf",
        include_evidence=True
    )
"""

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from database.models import SessionLocal
from evidence.models import Evidence
from reports.compliance import ComplianceMapper
from reports.export import DOCXExporter, HTMLExporter, JSONExporter, PDFExporter
from reports.models import Report, ReportFormat, ReportStatus, ReportType


class ReportGenerator:
    """
    Main report generator class.
    
    Handles all aspects of report generation:
    - Data collection
    - Template rendering
    - Export to multiple formats
    - Report tracking
    """
    
    def __init__(self, templates_dir: str = "reports/templates"):
        self.templates_dir = Path(templates_dir)
        self.pdf_exporter = PDFExporter(templates_dir)
        self.html_exporter = HTMLExporter(templates_dir)
        self.docx_exporter = DOCXExporter()
        self.json_exporter = JSONExporter()
        self.compliance_mapper = ComplianceMapper()
    
    def generate_executive_report(
        self,
        scan_id: str,
        output_path: str,
        company_name: str = "Unknown Company",
        pentest_start: Optional[str] = None,
        pentest_end: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict:
        """
        Generate an executive summary report.
        
        Args:
            scan_id: The scan ID to generate report for
            output_path: Where to save the report
            company_name: Client company name
            pentest_start: Pentest start date (ISO format)
            pentest_end: Pentest end date (ISO format)
            db: Database session
            
        Returns:
            Report metadata dict
        """
        if db is None:
            db = SessionLocal()
        
        try:
            # Collect data
            findings = self._collect_findings(db, scan_id)
            evidence = self._collect_evidence(db, scan_id)
            
            # Calculate statistics
            stats = self._calculate_statistics(findings)
            
            # Prepare template data
            data = {
                "title": f"Penetration Test Report - {company_name}",
                "company_name": company_name,
                "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "pentest_start": pentest_start or datetime.utcnow().strftime("%Y-%m-%d"),
                "pentest_end": pentest_end or datetime.utcnow().strftime("%Y-%m-%d"),
                "report_version": "1.0",
                "executive_summary": self._generate_executive_summary(stats, company_name),
                "scope_included": "Web applications, APIs, Network infrastructure",
                "scope_excluded": "Physical security, Social engineering, Denial of Service",
                "overall_risk": stats["overall_risk"],
                "risk_summary": {
                    "total": stats["total"],
                    "critical": stats["critical"],
                    "high": stats["high"],
                    "medium": stats["medium"],
                    "low": stats["low"],
                    "info": stats["info"],
                },
                "top_findings": self._get_top_findings(findings, 10),
                "immediate_recommendations": self._get_recommendations(findings, "immediate"),
                "short_term_recommendations": self._get_recommendations(findings, "short"),
                "long_term_recommendations": self._get_recommendations(findings, "long"),
                "compliance_gaps": self._get_compliance_gaps(findings),
            }
            
            # Generate report
            format = self._detect_format(output_path)
            
            if format == "pdf":
                self.pdf_exporter.export(data, "executive_report", output_path)
            elif format == "html":
                self.html_exporter.export(data, "executive_report", output_path)
            elif format == "docx":
                self.docx_exporter.export(data, output_path)
            elif format == "json":
                self.json_exporter.export(data, output_path)
            
            # Create report record
            report_record = self._create_report_record(
                scan_id=scan_id,
                report_type=ReportType.EXECUTIVE,
                format=format,
                output_path=output_path,
                stats=stats,
                company_name=company_name,
                db=db,
            )
            
            return {
                "success": True,
                "report_id": report_record.id,
                "file_path": output_path,
                "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                "statistics": stats,
            }
            
        finally:
            if db:
                db.close()
    
    def generate_technical_report(
        self,
        scan_id: str,
        output_path: str,
        include_evidence: bool = True,
        include_remediation: bool = True,
        db: Optional[Session] = None,
    ) -> Dict:
        """
        Generate a detailed technical report.
        
        Args:
            scan_id: The scan ID
            output_path: Output file path
            include_evidence: Include screenshots and evidence
            include_remediation: Include remediation steps
            db: Database session
            
        Returns:
            Report metadata
        """
        if db is None:
            db = SessionLocal()
        
        try:
            findings = self._collect_findings(db, scan_id)
            evidence = self._collect_evidence(db, scan_id) if include_evidence else []
            
            stats = self._calculate_statistics(findings)
            
            data = {
                "title": "Technical Penetration Test Report",
                "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "scan_id": scan_id,
                "findings": findings,
                "evidence": [e.to_dict() for e in evidence],
                "statistics": stats,
                "include_remediation": include_remediation,
            }
            
            format = self._detect_format(output_path)
            
            if format == "pdf":
                self.pdf_exporter.export(data, "technical_report", output_path)
            elif format == "html":
                self.html_exporter.export(data, "technical_report", output_path)
            elif format == "docx":
                self.docx_exporter.export(data, output_path)
            elif format == "json":
                self.json_exporter.export(data, output_path)
            
            report_record = self._create_report_record(
                scan_id=scan_id,
                report_type=ReportType.TECHNICAL,
                format=format,
                output_path=output_path,
                stats=stats,
                db=db,
            )
            
            return {
                "success": True,
                "report_id": report_record.id,
                "file_path": output_path,
                "statistics": stats,
            }
            
        finally:
            if db:
                db.close()
    
    def generate_compliance_report(
        self,
        scan_id: str,
        output_path: str,
        framework: str,
        db: Optional[Session] = None,
    ) -> Dict:
        """
        Generate a compliance-focused report.
        
        Args:
            scan_id: The scan ID
            output_path: Output file path
            framework: Compliance framework (owasp, iso27001, pci_dss)
            db: Database session
            
        Returns:
            Report metadata
        """
        if db is None:
            db = SessionLocal()
        
        try:
            findings = self._collect_findings(db, scan_id)
            
            # Generate compliance mapping
            compliance_summary = self.compliance_mapper.generate_compliance_summary(
                findings, framework
            )
            
            data = {
                "title": f"{framework.upper()} Compliance Assessment Report",
                "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "framework": framework,
                "compliance_summary": compliance_summary,
                "findings": findings,
            }
            
            format = self._detect_format(output_path)
            
            if format == "pdf":
                self.pdf_exporter.export(data, "compliance_report", output_path)
            elif format == "html":
                self.html_exporter.export(data, "compliance_report", output_path)
            elif format == "json":
                self.json_exporter.export(data, output_path)
            
            report_record = self._create_report_record(
                scan_id=scan_id,
                report_type=ReportType.COMPLIANCE,
                format=format,
                output_path=output_path,
                stats=self._calculate_statistics(findings),
                compliance_framework=framework,
                db=db,
            )
            
            return {
                "success": True,
                "report_id": report_record.id,
                "file_path": output_path,
                "compliance_summary": compliance_summary,
            }
            
        finally:
            if db:
                db.close()
    
    def list_reports(
        self,
        scan_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict]:
        """List all generated reports."""
        if db is None:
            db = SessionLocal()
        
        try:
            query = db.query(Report)
            if scan_id:
                query = query.filter(Report.scan_id == scan_id)
            
            reports = query.order_by(Report.generated_at.desc()).all()
            return [r.to_dict() for r in reports]
            
        finally:
            if db:
                db.close()
    
    def get_report(self, report_id: str, db: Optional[Session] = None) -> Optional[Dict]:
        """Get a specific report by ID."""
        if db is None:
            db = SessionLocal()
        
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            return report.to_dict() if report else None
            
        finally:
            if db:
                db.close()
    
    def _collect_findings(self, db: Session, scan_id: str) -> List[Dict]:
        """Collect findings from database."""
        # This would integrate with your findings database
        # For now, return mock data
        return [
            {
                "id": "1",
                "title": "SQL Injection in Login Form",
                "severity": "critical",
                "vulnerability_type": "SQL Injection",
                "description": "The login form is vulnerable to SQL injection attacks.",
                "proof_of_concept": "' OR 1=1 --",
                "remediation": "Use parameterized queries",
                "cvss_score": "9.8",
                "target": "https://example.com/login",
            },
            {
                "id": "2",
                "title": "Cross-Site Scripting (XSS)",
                "severity": "high",
                "vulnerability_type": "XSS",
                "description": "Reflected XSS in search parameter",
                "proof_of_concept": "<script>alert('XSS')</script>",
                "remediation": "Implement output encoding",
                "cvss_score": "7.5",
                "target": "https://example.com/search",
            },
        ]
    
    def _collect_evidence(self, db: Session, scan_id: str) -> List[Evidence]:
        """Collect evidence from database."""
        return db.query(Evidence).filter(Evidence.scan_id == scan_id).all()
    
    def _calculate_statistics(self, findings: List[Dict]) -> Dict:
        """Calculate finding statistics."""
        stats = {
            "total": len(findings),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "overall_risk": "LOW",
        }
        
        cvss_scores = []
        
        for f in findings:
            severity = f.get("severity", "info").lower()
            if severity in stats:
                stats[severity] += 1
            
            # Collect CVSS scores
            cvss = f.get("cvss_score")
            if cvss:
                try:
                    cvss_scores.append(float(cvss))
                except ValueError:
                    pass
        
        # Calculate overall risk
        if stats["critical"] > 0:
            stats["overall_risk"] = "CRITICAL"
        elif stats["high"] > 0:
            stats["overall_risk"] = "HIGH"
        elif stats["medium"] > 0:
            stats["overall_risk"] = "MEDIUM"
        elif stats["low"] > 0:
            stats["overall_risk"] = "LOW"
        
        # CVSS statistics
        if cvss_scores:
            stats["avg_cvss"] = round(sum(cvss_scores) / len(cvss_scores), 1)
            stats["max_cvss"] = max(cvss_scores)
        
        return stats
    
    def _generate_executive_summary(self, stats: Dict, company_name: str) -> str:
        """Generate executive summary text."""
        risk = stats["overall_risk"]
        
        summaries = {
            "CRITICAL": f"""
The penetration test of {company_name}'s infrastructure revealed CRITICAL security vulnerabilities 
that require immediate attention. A total of {stats['total']} findings were identified, including 
{stats['critical']} critical and {stats['high']} high-severity issues. These vulnerabilities 
present significant risk to the organization's data and operations. Immediate remediation is strongly 
recommended.
""",
            "HIGH": f"""
The penetration test of {company_name}'s infrastructure identified HIGH-risk security vulnerabilities. 
A total of {stats['total']} findings were discovered, including {stats['high']} high-severity issues. 
These vulnerabilities could lead to unauthorized access and data exposure. Prompt remediation is recommended.
""",
            "MEDIUM": f"""
The penetration test of {company_name}'s infrastructure revealed MODERATE security risks. 
{stats['total']} findings were identified, primarily medium and low severity. While no critical 
issues were found, addressing these findings will improve the overall security posture.
""",
            "LOW": f"""
The penetration test of {company_name}'s infrastructure found LOW overall risk. {stats['total']} 
minor findings were identified, primarily informational. The security posture is generally good, 
though implementing the recommended improvements will further strengthen defenses.
""",
        }
        
        return summaries.get(risk, summaries["LOW"])
    
    def _get_top_findings(self, findings: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top findings by severity."""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        
        sorted_findings = sorted(
            findings,
            key=lambda x: severity_order.get(x.get("severity", "info").lower(), 5)
        )
        
        return sorted_findings[:limit]
    
    def _get_recommendations(self, findings: List[Dict], timeframe: str) -> List[Dict]:
        """Get recommendations based on timeframe."""
        recommendations = {
            "immediate": [
                {"title": "Address Critical SQL Injection", "description": "Patch SQL injection vulnerability in login form immediately"},
                {"title": "Enable WAF Rules", "description": "Deploy Web Application Firewall with SQLi/XSS protection"},
            ],
            "short": [
                {"title": "Security Training", "description": "Conduct secure coding training for development team"},
                {"title": "Implement Input Validation", "description": "Add comprehensive input validation across all forms"},
            ],
            "long": [
                {"title": "DevSecOps Integration", "description": "Integrate security testing into CI/CD pipeline"},
                {"title": "Bug Bounty Program", "description": "Consider establishing a bug bounty program"},
            ],
        }
        
        return recommendations.get(timeframe, [])
    
    def _get_compliance_gaps(self, findings: List[Dict]) -> List[Dict]:
        """Get compliance gaps from findings."""
        return [
            {
                "framework": "OWASP Top 10",
                "control": "A03:2021 - Injection",
                "description": "SQL Injection vulnerability found",
                "priority": "critical",
            },
            {
                "framework": "ISO 27001",
                "control": "A.8.26 - Application Security",
                "description": "Input validation insufficient",
                "priority": "high",
            },
        ]
    
    def _detect_format(self, output_path: str) -> str:
        """Detect format from file extension."""
        ext = Path(output_path).suffix.lower()
        
        format_map = {
            ".pdf": "pdf",
            ".html": "html",
            ".docx": "docx",
            ".json": "json",
        }
        
        return format_map.get(ext, "pdf")
    
    def _create_report_record(
        self,
        scan_id: str,
        report_type: ReportType,
        format: str,
        output_path: str,
        stats: Dict,
        company_name: str = None,
        compliance_framework: str = None,
        db: Session = None,
    ) -> Report:
        """Create a report database record."""
        report = Report(
            id=str(uuid.uuid4()),
            scan_id=scan_id,
            report_type=report_type,
            report_format=ReportFormat(format),
            status=ReportStatus.COMPLETED,
            title=f"{report_type.value.title()} Report",
            company_name=company_name,
            total_findings=stats.get("total", 0),
            critical_count=stats.get("critical", 0),
            high_count=stats.get("high", 0),
            medium_count=stats.get("medium", 0),
            low_count=stats.get("low", 0),
            info_count=stats.get("info", 0),
            file_path=output_path,
            file_size=os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            generated_at=datetime.utcnow(),
        )
        
        if compliance_framework:
            from reports.models import ComplianceFramework
            report.compliance_framework = ComplianceFramework(compliance_framework)
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report
