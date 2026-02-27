"""
Zen-AI-Pentest Report Generation Module

Professional penetration test reporting with:
- Executive Summary Reports
- Technical Detail Reports
- Compliance Reports (OWASP, ISO 27001, PCI DSS)
- Evidence Integration
- Multiple Export Formats (PDF, HTML, DOCX, JSON)

Usage:
    from reports import ReportGenerator
    
    generator = ReportGenerator()
    
    # Executive summary for C-Level
    pdf_path = generator.generate_executive_report(
        scan_id="scan-123",
        output_path="reports/exec_summary.pdf",
        company_name="ACME Corp",
        pentest_dates=("2026-02-01", "2026-02-07")
    )
    
    # Technical report for IT teams
    pdf_path = generator.generate_technical_report(
        scan_id="scan-123",
        output_path="reports/technical.pdf",
        include_evidence=True
    )
"""

from .generator import ReportGenerator
from .compliance import ComplianceMapper
from .export import PDFExporter, HTMLExporter, DOCXExporter
from .models import Report, ReportType, ReportStatus

__version__ = "1.0.0"
__all__ = [
    "ReportGenerator",
    "ComplianceMapper",
    "PDFExporter",
    "HTMLExporter", 
    "DOCXExporter",
    "Report",
    "ReportType",
    "ReportStatus",
]
