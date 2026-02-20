"""
Report Export Module
Q2 2026 - PDF & CSV Export
"""

import csv
import io
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

try:
    from weasyprint import HTML  # CSS not used directly
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ReportData:
    """Report data structure"""
    title: str
    scan_date: datetime
    target: str
    findings: List[Dict[str, Any]]
    summary: Dict[str, int]
    recommendations: List[str]


class ReportExporter:
    """Export reports to various formats"""

    def __init__(self):
        self.templates = {
            "executive": self._executive_template,
            "technical": self._technical_template,
            "compliance": self._compliance_template
        }

    def export_csv(self, findings: List[Dict], filename: str = None) -> bytes:
        """Export findings to CSV"""
        if not filename:
            filename = f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Severity", "Title", "Description", "Target",
            "CVE", "CVSS", "Status", "Discovered"
        ])

        # Data
        for finding in findings:
            writer.writerow([
                finding.get("id", ""),
                finding.get("severity", ""),
                finding.get("title", ""),
                finding.get("description", ""),
                finding.get("target", ""),
                finding.get("cve_id", ""),
                finding.get("cvss_score", ""),
                finding.get("status", "open"),
                finding.get("discovered_at", "")
            ])

        return output.getvalue().encode('utf-8')

    def export_pdf(self, report: ReportData, template: str = "executive") -> bytes:
        """Export report to PDF"""
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint not available. Install: pip install weasyprint")
            raise RuntimeError("PDF generation requires WeasyPrint")

        html_content = self.templates.get(template, self._executive_template)(report)

        pdf = HTML(string=html_content).write_pdf()
        return pdf

    def _executive_template(self, report: ReportData) -> str:
        """Executive summary template"""
        findings_html = ""
        for f in report.findings[:10]:  # Top 10
            severity_color = {
                "critical": "#dc2626",
                "high": "#ea580c",
                "medium": "#ca8a04",
                "low": "#16a34a"
            }.get(f.get("severity", "low"), "#6b7280")

            findings_html += f"""
            <div style="margin: 10px 0; padding: 10px; border-left: 4px solid {severity_color}; background: #f9fafb;">
                <strong>{f.get('title', 'Unknown')}</strong>
                <span style="color: {severity_color}; text-transform: uppercase; font-size: 0.8em;">
                    {f.get('severity', 'unknown')}
                </span>
                <p style="margin: 5px 0; color: #4b5563;">{f.get('description', '')[:200]}...</p>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #111827; border-bottom: 2px solid #059669; padding-bottom: 10px; }}
                .summary {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #059669; }}
                .metric-label {{ color: #6b7280; font-size: 0.9em; }}
                .findings {{ margin-top: 30px; }}
            </style>
        </head>
        <body>
            <h1>{report.title}</h1>
            <p><strong>Target:</strong> {report.target}</p>
            <p><strong>Scan Date:</strong> {report.scan_date.strftime('%Y-%m-%d %H:%M')}</p>

            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">
                    <div class="metric-value">{report.summary.get('critical', 0)}</div>
                    <div class="metric-label">Critical</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{report.summary.get('high', 0)}</div>
                    <div class="metric-label">High</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{report.summary.get('medium', 0)}</div>
                    <div class="metric-label">Medium</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{report.summary.get('low', 0)}</div>
                    <div class="metric-label">Low</div>
                </div>
            </div>

            <div class="findings">
                <h2>Top Findings</h2>
                {findings_html}
            </div>

            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.9em;">
                <p>Generated by Zen AI Pentest v2.1.0</p>
                <p>Confidential - For authorized eyes only</p>
            </div>
        </body>
        </html>
        """

    def _technical_template(self, report: ReportData) -> str:
        """Technical detailed template"""
        # Similar to executive but with more technical details
        return self._executive_template(report)  # Simplified for now

    def _compliance_template(self, report: ReportData) -> str:
        """Compliance-focused template"""
        # For compliance reporting (PCI-DSS, GDPR, etc.)
        return self._executive_template(report)  # Simplified for now

    def export_json(self, findings: List[Dict]) -> str:
        """Export findings to JSON"""
        import json
        return json.dumps(findings, indent=2)

    def get_export_formats(self) -> List[str]:
        """List available export formats"""
        formats = ["csv", "json"]
        if WEASYPRINT_AVAILABLE:
            formats.append("pdf")
        return formats


# Convenience function
def export_findings(findings: List[Dict], format: str = "csv") -> bytes:
    """Quick export function"""
    exporter = ReportExporter()

    if format == "csv":
        return exporter.export_csv(findings)
    elif format == "json":
        return exporter.export_json(findings).encode('utf-8')
    elif format == "pdf":
        report = ReportData(
            title="Security Assessment Report",
            scan_date=datetime.now(),
            target="Multiple Targets",
            findings=findings,
            summary={
                "critical": len([f for f in findings if f.get("severity") == "critical"]),
                "high": len([f for f in findings if f.get("severity") == "high"]),
                "medium": len([f for f in findings if f.get("severity") == "medium"]),
                "low": len([f for f in findings if f.get("severity") == "low"])
            },
            recommendations=[]
        )
        return exporter.export_pdf(report)
    else:
        raise ValueError(f"Unsupported format: {format}")
