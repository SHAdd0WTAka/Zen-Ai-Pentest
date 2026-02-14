"""
Report Generator mit Template Support
"""
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from typing import List, Dict
import os


class ReportGenerator:
    """Generiert Pentest Reports in verschiedenen Formaten"""
    
    def __init__(self, template_dir: str = "templates/reports"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def count_severities(self, findings: List[Dict]) -> Dict:
        """Zählt Findings nach Severity"""
        counts = {
            "critical": 0,
            "high": 0, 
            "medium": 0,
            "low": 0,
            "info": 0
        }
        for finding in findings:
            sev = finding.get("severity", "").lower()
            if sev in counts:
                counts[sev] += 1
        return counts
    
    def generate_html(self, scan: Dict, findings: List[Dict], template: str = "default") -> str:
        """Generiert HTML Report"""
        template_file = f"{template}.html"
        template_obj = self.env.get_template(template_file)
        
        html_content = template_obj.render(
            scan=scan,
            findings=findings,
            counts=self.count_severities(findings),
            generated_at=datetime.now()
        )
        
        return html_content
    
    def generate_pdf(self, scan: Dict, findings: List[Dict], template: str = "default", output_path: str = None) -> str:
        """Generiert PDF Report (benötigt WeasyPrint oder pdfkit)"""
        try:
            import pdfkit
            
            html_content = self.generate_html(scan, findings, template)
            
            if not output_path:
                output_path = f"reports/report_{scan.get('id', 'unknown')}.pdf"
            
            # Verzeichnis erstellen
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            pdfkit.from_string(html_content, output_path)
            return output_path
            
        except ImportError:
            print("pdfkit nicht installiert. Verwende HTML Report.")
            return self.save_html(scan, findings, template)
    
    def save_html(self, scan: Dict, findings: List[Dict], template: str = "default", output_path: str = None) -> str:
        """Speichert HTML Report in Datei"""
        html_content = self.generate_html(scan, findings, template)
        
        if not output_path:
            output_path = f"reports/report_{scan.get('id', 'unknown')}.html"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def generate_json(self, scan: Dict, findings: List[Dict]) -> Dict:
        """Generiert JSON Report"""
        import json
        
        report = {
            "scan": scan,
            "findings": findings,
            "summary": {
                "total": len(findings),
                "severity_counts": self.count_severities(findings)
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return report
