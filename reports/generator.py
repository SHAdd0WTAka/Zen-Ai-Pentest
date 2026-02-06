"""
Report Generator für Zen-AI-Pentest

Erstellt professionelle PDF, HTML und JSON Reports.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from jinja2 import Template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generiert Pentest-Reports in verschiedenen Formaten"""
    
    def __init__(self, output_dir: str = "/tmp/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Report-Templates
        self.html_template = self._get_html_template()
    
    def generate_pdf(self, scan_id: int, findings: List[Dict], 
                     scan_info: Dict, template: str = "default") -> str:
        """Generiert PDF-Report"""
        if not WEASYPRINT_AVAILABLE:
            logger.warning("WeasyPrint nicht verfügbar, erstelle HTML stattdessen")
            return self.generate_html(scan_id, findings, scan_info)
        
        try:
            # HTML erstellen
            html_content = self._render_html(scan_id, findings, scan_info)
            
            # PDF generieren
            output_file = self.output_dir / f"report_{scan_id}_{int(datetime.now().timestamp())}.pdf"
            HTML(string=html_content).write_pdf(str(output_file))
            
            logger.info(f"PDF Report erstellt: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"PDF Generierung fehlgeschlagen: {e}")
            # Fallback zu HTML
            return self.generate_html(scan_id, findings, scan_info)
    
    def generate_html(self, scan_id: int, findings: List[Dict],
                      scan_info: Dict, template: str = "default") -> str:
        """Generiert HTML-Report"""
        html_content = self._render_html(scan_id, findings, scan_info)
        
        output_file = self.output_dir / f"report_{scan_id}_{int(datetime.now().timestamp())}.html"
        output_file.write_text(html_content, encoding='utf-8')
        
        logger.info(f"HTML Report erstellt: {output_file}")
        return str(output_file)
    
    def generate_json(self, scan_id: int, findings: List[Dict],
                      scan_info: Dict) -> str:
        """Generiert JSON-Report (für API/Integrationen)"""
        report_data = {
            "report_metadata": {
                "scan_id": scan_id,
                "generated_at": datetime.utcnow().isoformat(),
                "generator": "Zen-AI-Pentest v2.0",
                "format": "json"
            },
            "scan_info": scan_info,
            "summary": {
                "total_findings": len(findings),
                "severity_counts": self._count_by_severity(findings),
                "tool_counts": self._count_by_tool(findings)
            },
            "findings": findings
        }
        
        output_file = self.output_dir / f"report_{scan_id}_{int(datetime.now().timestamp())}.json"
        output_file.write_text(json.dumps(report_data, indent=2), encoding='utf-8')
        
        logger.info(f"JSON Report erstellt: {output_file}")
        return str(output_file)
    
    def generate_xml(self, scan_id: int, findings: List[Dict],
                     scan_info: Dict) -> str:
        """Generiert XML-Report (für Import in andere Tools)"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("pentest_report")
        root.set("generated", datetime.utcnow().isoformat())
        
        # Metadata
        meta = ET.SubElement(root, "metadata")
        ET.SubElement(meta, "scan_id").text = str(scan_id)
        ET.SubElement(meta, "target").text = scan_info.get("target", "")
        ET.SubElement(meta, "scan_type").text = scan_info.get("scan_type", "")
        
        # Findings
        findings_elem = ET.SubElement(root, "findings")
        findings_elem.set("count", str(len(findings)))
        
        for finding in findings:
            f_elem = ET.SubElement(findings_elem, "finding")
            f_elem.set("id", str(finding.get("id", "")))
            ET.SubElement(f_elem, "title").text = finding.get("title", "")
            ET.SubElement(f_elem, "severity").text = finding.get("severity", "")
            ET.SubElement(f_elem, "description").text = finding.get("description", "")
            ET.SubElement(f_elem, "tool").text = finding.get("tool", "")
        
        # Write to file
        output_file = self.output_dir / f"report_{scan_id}_{int(datetime.now().timestamp())}.xml"
        tree = ET.ElementTree(root)
        tree.write(str(output_file), encoding='utf-8', xml_declaration=True)
        
        logger.info(f"XML Report erstellt: {output_file}")
        return str(output_file)
    
    def generate_markdown(self, scan_id: int, findings: List[Dict],
                          scan_info: Dict) -> str:
        """Generiert Markdown-Report"""
        md_content = f"""# Pentest Report

**Scan ID:** {scan_id}  
**Target:** {scan_info.get('target', 'N/A')}  
**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}  
**Type:** {scan_info.get('scan_type', 'N/A')}

---

## Summary

- **Total Findings:** {len(findings)}
- **Critical:** {sum(1 for f in findings if f.get('severity') == 'critical')}
- **High:** {sum(1 for f in findings if f.get('severity') == 'high')}
- **Medium:** {sum(1 for f in findings if f.get('severity') == 'medium')}
- **Low:** {sum(1 for f in findings if f.get('severity') == 'low')}

---

## Findings

"""
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_findings = sorted(findings, key=lambda x: severity_order.get(x.get('severity', 'info'), 5))
        
        for finding in sorted_findings:
            md_content += f"""### {finding.get('title', 'Untitled')}

- **Severity:** {finding.get('severity', 'unknown').upper()}
- **Tool:** {finding.get('tool', 'unknown')}
- **Target:** {finding.get('target', 'N/A')}

{finding.get('description', 'No description available.')}

---

"""
        
        output_file = self.output_dir / f"report_{scan_id}_{int(datetime.now().timestamp())}.md"
        output_file.write_text(md_content, encoding='utf-8')
        
        logger.info(f"Markdown Report erstellt: {output_file}")
        return str(output_file)
    
    def _render_html(self, scan_id: int, findings: List[Dict],
                     scan_info: Dict) -> str:
        """Rendert HTML-Template"""
        template = Template(self.html_template)
        
        # Sort findings by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_findings = sorted(findings, key=lambda x: severity_order.get(x.get('severity', 'info'), 5))
        
        # Count by severity
        severity_counts = self._count_by_severity(findings)
        
        return template.render(
            scan_id=scan_id,
            scan_info=scan_info,
            findings=sorted_findings,
            severity_counts=severity_counts,
            generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            total_findings=len(findings)
        )
    
    def _count_by_severity(self, findings: List[Dict]) -> Dict[str, int]:
        """Zählt Befunde nach Schweregrad"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for f in findings:
            sev = f.get('severity', 'info').lower()
            if sev in counts:
                counts[sev] += 1
        return counts
    
    def _count_by_tool(self, findings: List[Dict]) -> Dict[str, int]:
        """Zählt Befunde nach Tool"""
        counts = {}
        for f in findings:
            tool = f.get('tool', 'unknown')
            counts[tool] = counts.get(tool, 0) + 1
        return counts
    
    def _get_html_template(self) -> str:
        """Gibt HTML-Template zurück"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pentest Report - {{ scan_info.get('target', 'Unknown') }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f6f8fa;
            color: #24292e;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        
        header {
            background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        h1 { font-size: 32px; margin-bottom: 10px; }
        .meta { opacity: 0.9; font-size: 14px; }
        .meta span { margin-right: 20px; }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .summary-card h3 { font-size: 14px; color: #586069; margin-bottom: 10px; }
        .summary-card .number { font-size: 36px; font-weight: bold; }
        .critical { color: #d32f2f; }
        .high { color: #f57c00; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
        .info { color: #1976d2; }
        
        .findings { background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .findings h2 { margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e1e4e8; }
        
        .finding {
            margin-bottom: 25px;
            padding: 20px;
            background: #f6f8fa;
            border-radius: 8px;
            border-left: 4px solid #ccc;
        }
        .finding.critical { border-left-color: #d32f2f; }
        .finding.high { border-left-color: #f57c00; }
        .finding.medium { border-left-color: #fbc02d; }
        .finding.low { border-left-color: #388e3c; }
        
        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .finding-title { font-size: 18px; font-weight: 600; }
        .severity-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }
        .severity-critical { background: #d32f2f; }
        .severity-high { background: #f57c00; }
        .severity-medium { background: #fbc02d; color: #333; }
        .severity-low { background: #388e3c; }
        .severity-info { background: #1976d2; }
        
        .finding-meta { font-size: 12px; color: #586069; margin-bottom: 10px; }
        .finding-meta span { margin-right: 15px; }
        
        .finding-description { color: #444; }
        
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e1e4e8;
            text-align: center;
            color: #586069;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Security Assessment Report</h1>
            <div class="meta">
                <span>Target: {{ scan_info.get('target', 'Unknown') }}</span>
                <span>Scan Type: {{ scan_info.get('scan_type', 'Unknown') }}</span>
                <span>Generated: {{ generated_at }}</span>
            </div>
        </header>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Findings</h3>
                <div class="number">{{ total_findings }}</div>
            </div>
            <div class="summary-card">
                <h3>Critical</h3>
                <div class="number critical">{{ severity_counts.critical }}</div>
            </div>
            <div class="summary-card">
                <h3>High</h3>
                <div class="number high">{{ severity_counts.high }}</div>
            </div>
            <div class="summary-card">
                <h3>Medium</h3>
                <div class="number medium">{{ severity_counts.medium }}</div>
            </div>
            <div class="summary-card">
                <h3>Low</h3>
                <div class="number low">{{ severity_counts.low }}</div>
            </div>
        </div>
        
        <div class="findings">
            <h2>Detailed Findings</h2>
            
            {% for finding in findings %}
            <div class="finding {{ finding.get('severity', 'info') }}">
                <div class="finding-header">
                    <div class="finding-title">{{ finding.get('title', 'Untitled') }}</div>
                    <span class="severity-badge severity-{{ finding.get('severity', 'info') }}">
                        {{ finding.get('severity', 'info').upper() }}
                    </span>
                </div>
                <div class="finding-meta">
                    <span>Tool: {{ finding.get('tool', 'Unknown') }}</span>
                    <span>Target: {{ finding.get('target', 'N/A') }}</span>
                    {% if finding.get('cvss_score') %}
                    <span>CVSS: {{ finding.get('cvss_score') }}</span>
                    {% endif %}
                </div>
                <div class="finding-description">
                    {{ finding.get('description', 'No description available.') }}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <footer>
            <p>Generated by Zen-AI-Pentest v2.0</p>
            <p>Confidential - For authorized use only</p>
        </footer>
    </div>
</body>
</html>
        """


if __name__ == "__main__":
    # Test
    generator = ReportGenerator()
    
    # Test data
    findings = [
        {
            "id": 1,
            "title": "SQL Injection in login form",
            "description": "The login form is vulnerable to SQL injection attacks.",
            "severity": "critical",
            "tool": "sqlmap",
            "target": "http://example.com/login",
            "cvss_score": 9.8
        },
        {
            "id": 2,
            "title": "Outdated Apache Version",
            "description": "Apache 2.4.29 detected, multiple CVEs applicable.",
            "severity": "high",
            "tool": "nmap",
            "target": "192.168.1.1",
            "cvss_score": 7.5
        },
        {
            "id": 3,
            "title": "Missing Security Headers",
            "description": "X-Frame-Options header not set.",
            "severity": "medium",
            "tool": "nuclei",
            "target": "http://example.com"
        }
    ]
    
    scan_info = {
        "target": "example.com",
        "scan_type": "comprehensive"
    }
    
    # Generate reports
    pdf_path = generator.generate_pdf(123, findings, scan_info)
    html_path = generator.generate_html(123, findings, scan_info)
    json_path = generator.generate_json(123, findings, scan_info)
    
    print("Reports generated:")
    print(f"  PDF: {pdf_path}")
    print(f"  HTML: {html_path}")
    print(f"  JSON: {json_path}")
