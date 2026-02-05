"""
Output Formatters Module for CI/CD Integration
==============================================
Provides formatters for various CI/CD platforms:
- SARIF (GitHub Security, GitLab Security Dashboard)
- JUnit XML (Jenkins, GitLab Test Reports)
- HTML (Human readable reports)

Version: 2.0.0
Author: Zen-AI-Pentest Team
"""

import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import html
import hashlib


@dataclass
class Finding:
    """Security finding data structure"""
    id: str
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    target: str
    category: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None
    references: Optional[List[str]] = None
    discovered_at: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None  # For SARIF location


@dataclass
class ScanSummary:
    """Scan summary data structure"""
    scan_id: str
    target: str
    scan_date: str
    duration: int  # seconds
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    risk_score: int
    tool_name: str = "Zen AI Pentest"
    tool_version: str = "2.0.0"


class SARIFFormatter:
    """
    SARIF (Static Analysis Results Interchange Format) formatter.
    
    SARIF is the standard format for GitHub Advanced Security and
    GitLab Security Dashboard integration.
    
    Spec: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
    """
    
    SARIF_VERSION = "2.1.0"
    SCHEMA_URI = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
    
    SEVERITY_LEVELS = {
        "critical": {"level": "error", "rank": 10},
        "high": {"level": "error", "rank": 8},
        "medium": {"level": "warning", "rank": 5},
        "low": {"level": "note", "rank": 3},
        "info": {"level": "none", "rank": 1}
    }
    
    def __init__(self, tool_name: str = "Zen AI Pentest", tool_version: str = "2.0.0"):
        self.tool_name = tool_name
        self.tool_version = tool_version
    
    def format(self, findings: List[Finding], summary: ScanSummary) -> Dict[str, Any]:
        """Convert findings to SARIF format"""
        
        sarif = {
            "$schema": self.SCHEMA_URI,
            "version": self.SARIF_VERSION,
            "runs": [{
                "tool": {
                    "driver": {
                        "name": self.tool_name,
                        "version": self.tool_version,
                        "informationUri": "https://github.com/zen-ai-pentest/zen-ai-pentest",
                        "rules": self._generate_rules(findings)
                    }
                },
                "results": self._generate_results(findings),
                "invocations": [{
                    "executionSuccessful": True,
                    "startTimeUtc": summary.scan_date,
                    "endTimeUtc": self._calculate_end_time(summary.scan_date, summary.duration)
                }],
                "properties": {
                    "scanId": summary.scan_id,
                    "target": summary.target,
                    "riskScore": summary.risk_score,
                    "summary": {
                        "critical": summary.critical,
                        "high": summary.high,
                        "medium": summary.medium,
                        "low": summary.low,
                        "info": summary.info
                    }
                }
            }]
        }
        
        return sarif
    
    def _generate_rules(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Generate SARIF rules from unique finding types"""
        rules = []
        seen_categories = set()
        
        for finding in findings:
            if finding.category in seen_categories:
                continue
            seen_categories.add(finding.category)
            
            rule = {
                "id": self._sanitize_rule_id(finding.category),
                "name": finding.category,
                "shortDescription": {
                    "text": finding.category
                },
                "fullDescription": {
                    "text": f"Security issue category: {finding.category}"
                },
                "defaultConfiguration": {
                    "level": self.SEVERITY_LEVELS.get(
                        finding.severity.lower(), {"level": "warning"}
                    )["level"]
                },
                "properties": {
                    "category": finding.category,
                    "severity": finding.severity
                }
            }
            rules.append(rule)
        
        return rules
    
    def _generate_results(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Generate SARIF results from findings"""
        results = []
        
        for idx, finding in enumerate(findings, 1):
            result = {
                "ruleId": self._sanitize_rule_id(finding.category),
                "ruleIndex": 0,
                "message": {
                    "text": finding.title,
                    "markdown": f"**{finding.title}**\n\n{finding.description}"
                },
                "locations": self._generate_locations(finding),
                "level": self.SEVERITY_LEVELS.get(
                    finding.severity.lower(), {"level": "warning"}
                )["level"],
                "rank": self.SEVERITY_LEVELS.get(
                    finding.severity.lower(), {"rank": 5}
                )["rank"],
                "properties": {
                    "findingId": finding.id,
                    "severity": finding.severity,
                    "target": finding.target,
                    "cveId": finding.cve_id,
                    "cvssScore": finding.cvss_score,
                    "discoveredAt": finding.discovered_at
                }
            }
            
            # Add remediation if available
            if finding.remediation:
                result["fixes"] = [{
                    "description": {
                        "text": finding.remediation
                    }
                }]
            
            # Add references if available
            if finding.references:
                result["relatedLocations"] = [
                    {
                        "id": i + 1,
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": ref,
                                "description": {
                                    "text": f"Reference {i + 1}"
                                }
                            }
                        }
                    }
                    for i, ref in enumerate(finding.references)
                ]
            
            results.append(result)
        
        return results
    
    def _generate_locations(self, finding: Finding) -> List[Dict[str, Any]]:
        """Generate SARIF location from finding"""
        locations = []
        
        # Primary location from target
        location = {
            "physicalLocation": {
                "artifactLocation": {
                    "uri": finding.target,
                    "description": {
                        "text": f"Target: {finding.target}"
                    }
                }
            }
        }
        
        # Add specific location if available
        if finding.location:
            if "uri" in finding.location:
                location["physicalLocation"]["artifactLocation"]["uri"] = finding.location["uri"]
            if "region" in finding.location:
                location["physicalLocation"]["region"] = finding.location["region"]
        
        locations.append(location)
        return locations
    
    def _sanitize_rule_id(self, category: str) -> str:
        """Convert category to valid SARIF rule ID"""
        return category.lower().replace(" ", "-").replace("_", "-")[:50]
    
    def _calculate_end_time(self, start_time: str, duration: int) -> str:
        """Calculate end time from start time and duration"""
        try:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = start.timestamp() + duration
            return datetime.fromtimestamp(end).isoformat()
        except:
            return start_time
    
    def write(self, findings: List[Finding], summary: ScanSummary, 
              output_path: Union[str, Path]) -> Path:
        """Write SARIF output to file"""
        output_path = Path(output_path)
        sarif_data = self.format(findings, summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sarif_data, f, indent=2, ensure_ascii=False)
        
        return output_path


class JUnitXMLFormatter:
    """
    JUnit XML formatter for CI test result integration.
    
    Compatible with Jenkins, GitLab CI Test Reports, and most CI platforms.
    """
    
    SEVERITY_WEIGHTS = {
        "critical": 100,
        "high": 50,
        "medium": 20,
        "low": 5,
        "info": 1
    }
    
    def __init__(self, tool_name: str = "Zen AI Pentest"):
        self.tool_name = tool_name
    
    def format(self, findings: List[Finding], summary: ScanSummary) -> ET.Element:
        """Convert findings to JUnit XML format"""
        
        # Create root testsuites element
        testsuites = ET.Element("testsuites")
        testsuites.set("name", f"{self.tool_name} Security Scan")
        testsuites.set("tests", str(len(findings)))
        testsuites.set("failures", str(summary.critical + summary.high))
        testsuites.set("errors", "0")
        testsuites.set("time", str(summary.duration))
        
        # Create testsuite for the scan
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", f"Security Scan - {summary.target}")
        testsuite.set("tests", str(len(findings)))
        testsuite.set("failures", str(summary.critical + summary.high))
        testsuite.set("errors", "0")
        testsuite.set("time", str(summary.duration))
        testsuite.set("timestamp", summary.scan_date)
        testsuite.set("hostname", summary.target)
        
        # Add properties
        properties = ET.SubElement(testsuite, "properties")
        self._add_property(properties, "scan_id", summary.scan_id)
        self._add_property(properties, "target", summary.target)
        self._add_property(properties, "risk_score", str(summary.risk_score))
        self._add_property(properties, "tool_version", summary.tool_version)
        
        # Add test cases for each finding
        for finding in findings:
            testcase = self._create_testcase(testsuite, finding, summary)
        
        # Add summary test case
        summary_case = ET.SubElement(testsuite, "testcase")
        summary_case.set("name", "Scan Summary")
        summary_case.set("classname", "SecurityScan")
        summary_case.set("time", "0")
        
        system_out = ET.SubElement(summary_case, "system-out")
        system_out.text = self._generate_summary_text(summary)
        
        return testsuites
    
    def _add_property(self, properties: ET.Element, name: str, value: str):
        """Add a property to the testsuite"""
        prop = ET.SubElement(properties, "property")
        prop.set("name", name)
        prop.set("value", value)
    
    def _create_testcase(self, testsuite: ET.Element, finding: Finding, 
                         summary: ScanSummary) -> ET.Element:
        """Create a JUnit test case for a finding"""
        
        testcase = ET.SubElement(testsuite, "testcase")
        testcase.set("name", finding.title)
        testcase.set("classname", f"Security.{finding.category}")
        testcase.set("time", "0")
        
        # Add failure for critical/high findings
        if finding.severity.lower() in ["critical", "high"]:
            failure = ET.SubElement(testcase, "failure")
            failure.set("type", f"security.{finding.severity.lower()}")
            failure.set("message", f"[{finding.severity.upper()}] {finding.title}")
            
            # Build detailed failure text
            failure_text = self._generate_failure_text(finding)
            failure.text = failure_text
        
        # Add skipped for info findings (optional)
        elif finding.severity.lower() == "info":
            skipped = ET.SubElement(testcase, "skipped")
            skipped.set("message", "Informational finding")
        
        # Add system-out with finding details
        system_out = ET.SubElement(testcase, "system-out")
        system_out.text = self._generate_finding_text(finding)
        
        return testcase
    
    def _generate_failure_text(self, finding: Finding) -> str:
        """Generate detailed failure text for JUnit"""
        lines = [
            f"Finding ID: {finding.id}",
            f"Severity: {finding.severity.upper()}",
            f"Category: {finding.category}",
            f"Target: {finding.target}",
            "",
            "Description:",
            finding.description,
            ""
        ]
        
        if finding.cve_id:
            lines.extend([f"CVE: {finding.cve_id}", ""])
        
        if finding.cvss_score:
            lines.extend([f"CVSS Score: {finding.cvss_score}", ""])
        
        if finding.remediation:
            lines.extend([
                "Remediation:",
                finding.remediation,
                ""
            ])
        
        if finding.references:
            lines.extend(["References:"])
            lines.extend([f"  - {ref}" for ref in finding.references])
        
        return "\n".join(lines)
    
    def _generate_finding_text(self, finding: Finding) -> str:
        """Generate finding text for system-out"""
        return f"""Finding Details:
ID: {finding.id}
Title: {finding.title}
Severity: {finding.severity}
Target: {finding.target}
Category: {finding.category}
"""
    
    def _generate_summary_text(self, summary: ScanSummary) -> str:
        """Generate scan summary text"""
        return f"""Scan Summary
============
Target: {summary.target}
Scan ID: {summary.scan_id}
Duration: {summary.duration}s
Risk Score: {summary.risk_score}/100

Findings by Severity:
  Critical: {summary.critical}
  High: {summary.high}
  Medium: {summary.medium}
  Low: {summary.low}
  Info: {summary.info}
"""
    
    def to_string(self, element: ET.Element) -> str:
        """Convert XML element to formatted string"""
        # Convert to string
        rough_string = ET.tostring(element, encoding='unicode')
        
        # Pretty print
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def write(self, findings: List[Finding], summary: ScanSummary,
              output_path: Union[str, Path]) -> Path:
        """Write JUnit XML output to file"""
        output_path = Path(output_path)
        xml_element = self.format(findings, summary)
        xml_string = self.to_string(xml_element)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)
        
        return output_path


class HTMLFormatter:
    """
    HTML formatter for human-readable security reports.
    
    Generates professional HTML reports with:
    - Executive summary with charts
    - Detailed findings with filtering
    - Remediation guidance
    - Export options
    """
    
    SEVERITY_COLORS = {
        "critical": {"bg": "#dc2626", "text": "#ffffff", "light": "#fee2e2"},
        "high": {"bg": "#ea580c", "text": "#ffffff", "light": "#ffedd5"},
        "medium": {"bg": "#ca8a04", "text": "#ffffff", "light": "#fef3c7"},
        "low": {"bg": "#16a34a", "text": "#ffffff", "light": "#dcfce7"},
        "info": {"bg": "#6b7280", "text": "#ffffff", "light": "#f3f4f6"}
    }
    
    def __init__(self, tool_name: str = "Zen AI Pentest", tool_version: str = "2.0.0"):
        self.tool_name = tool_name
        self.tool_version = tool_version
    
    def format(self, findings: List[Finding], summary: ScanSummary) -> str:
        """Generate HTML report"""
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Scan Report - {html.escape(summary.target)}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    {self._generate_header(summary)}
    {self._generate_summary(summary)}
    {self._generate_findings(findings)}
    {self._generate_footer(summary)}
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _get_css(self) -> str:
        """Get CSS styles for the report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                         'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header-meta {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 4px solid;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        
        .summary-card.critical {{ border-left-color: #dc2626; }}
        .summary-card.high {{ border-left-color: #ea580c; }}
        .summary-card.medium {{ border-left-color: #ca8a04; }}
        .summary-card.low {{ border-left-color: #16a34a; }}
        .summary-card.info {{ border-left-color: #6b7280; }}
        
        .summary-card .count {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .summary-card.critical .count {{ color: #dc2626; }}
        .summary-card.high .count {{ color: #ea580c; }}
        .summary-card.medium .count {{ color: #ca8a04; }}
        .summary-card.low .count {{ color: #16a34a; }}
        .summary-card.info .count {{ color: #6b7280; }}
        
        .summary-card .label {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            font-weight: 600;
        }
        
        .risk-score {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .risk-score h2 {
            margin-bottom: 20px;
            color: #1f2937;
        }
        
        .risk-indicator {
            display: flex;
            align-items: center;
            gap: 30px;
        }
        
        .risk-value {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
        }
        
        .risk-low {{ background: linear-gradient(135deg, #16a34a, #22c55e); }}
        .risk-medium {{ background: linear-gradient(135deg, #ca8a04, #eab308); }}
        .risk-high {{ background: linear-gradient(135deg, #ea580c, #f97316); }}
        .risk-critical {{ background: linear-gradient(135deg, #dc2626, #ef4444); }}
        
        .findings-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .findings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .filter-btn:hover, .filter-btn.active {
            border-color: #059669;
            color: #059669;
        }
        
        .finding-item {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 16px;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }
        
        .finding-item:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .finding-header {
            padding: 16px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .finding-title {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .severity-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .finding-content {
            padding: 20px;
            border-top: 1px solid #e5e7eb;
            display: none;
        }
        
        .finding-content.expanded {
            display: block;
        }
        
        .finding-content h4 {
            margin-bottom: 8px;
            color: #374151;
        }
        
        .finding-content p, .finding-content ul {
            margin-bottom: 16px;
            color: #4b5563;
        }
        
        .remediation {
            background: #f0fdf4;
            border-left: 4px solid #16a34a;
            padding: 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 16px;
        }
        
        .footer {
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        @media print {
            .filter-buttons {{ display: none; }}
            .finding-content {{ display: block !important; }}
        }
        """
    
    def _generate_header(self, summary: ScanSummary) -> str:
        """Generate report header"""
        scan_date = datetime.fromisoformat(summary.scan_date.replace('Z', '+00:00'))
        formatted_date = scan_date.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return f"""
        <div class="header">
            <div class="container">
                <h1>🔒 Security Scan Report</h1>
                <div class="header-meta">
                    <p><strong>Target:</strong> {html.escape(summary.target)}</p>
                    <p><strong>Scan Date:</strong> {formatted_date}</p>
                    <p><strong>Scan ID:</strong> {html.escape(summary.scan_id)}</p>
                    <p><strong>Duration:</strong> {summary.duration} seconds</p>
                </div>
            </div>
        </div>
        """
    
    def _generate_summary(self, summary: ScanSummary) -> str:
        """Generate summary section with cards"""
        
        total = summary.critical + summary.high + summary.medium + summary.low + summary.info
        
        # Determine risk class
        if summary.risk_score >= 80:
            risk_class = "risk-critical"
            risk_label = "Critical Risk"
        elif summary.risk_score >= 60:
            risk_class = "risk-high"
            risk_label = "High Risk"
        elif summary.risk_score >= 40:
            risk_class = "risk-medium"
            risk_label = "Medium Risk"
        else:
            risk_class = "risk-low"
            risk_label = "Low Risk"
        
        return f"""
        <div class="container">
            <div class="summary-cards">
                <div class="summary-card critical">
                    <div class="count">{summary.critical}</div>
                    <div class="label">Critical</div>
                </div>
                <div class="summary-card high">
                    <div class="count">{summary.high}</div>
                    <div class="label">High</div>
                </div>
                <div class="summary-card medium">
                    <div class="count">{summary.medium}</div>
                    <div class="label">Medium</div>
                </div>
                <div class="summary-card low">
                    <div class="count">{summary.low}</div>
                    <div class="label">Low</div>
                </div>
                <div class="summary-card info">
                    <div class="count">{summary.info}</div>
                    <div class="label">Info</div>
                </div>
            </div>
            
            <div class="risk-score">
                <h2>Risk Assessment</h2>
                <div class="risk-indicator">
                    <div class="risk-value {risk_class}">{summary.risk_score}</div>
                    <div>
                        <h3>{risk_label}</h3>
                        <p>Overall risk score based on {total} findings</p>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_findings(self, findings: List[Finding]) -> str:
        """Generate findings section"""
        
        findings_html = []
        for i, finding in enumerate(findings, 1):
            severity = finding.severity.lower()
            colors = self.SEVERITY_COLORS.get(severity, self.SEVERITY_COLORS["info"])
            
            finding_html = f"""
            <div class="finding-item" data-severity="{severity}">
                <div class="finding-header" onclick="toggleFinding({i})">
                    <div class="finding-title">{html.escape(finding.title)}</div>
                    <span class="severity-badge" style="background: {colors['bg']}; color: {colors['text']};">
                        {severity.upper()}
                    </span>
                </div>
                <div class="finding-content" id="finding-{i}">
                    <h4>🔍 Description</h4>
                    <p>{html.escape(finding.description)}</p>
                    
                    <h4>📍 Target</h4>
                    <p>{html.escape(finding.target)}</p>
            """
            
            if finding.cve_id:
                finding_html += f"""
                    <h4>🐛 CVE Reference</h4>
                    <p><a href="https://nvd.nist.gov/vuln/detail/{finding.cve_id}" target="_blank">{finding.cve_id}</a></p>
                """
            
            if finding.cvss_score:
                finding_html += f"""
                    <h4>📊 CVSS Score</h4>
                    <p>{finding.cvss_score}</p>
                """
            
            if finding.remediation:
                finding_html += f"""
                    <h4>🛠️ Remediation</h4>
                    <div class="remediation">
                        <p>{html.escape(finding.remediation)}</p>
                    </div>
                """
            
            if finding.references:
                finding_html += """
                    <h4>📚 References</h4>
                    <ul>
                """
                for ref in finding.references:
                    finding_html += f'<li><a href="{html.escape(ref)}" target="_blank">{html.escape(ref)}</a></li>'
                finding_html += "</ul>"
            
            finding_html += f"""
                    <p style="margin-top: 20px; font-size: 0.875rem; color: #6b7280;">
                        Finding ID: {finding.id} | Category: {finding.category}
                    </p>
                </div>
            </div>
            """
            
            findings_html.append(finding_html)
        
        return f"""
        <div class="container">
            <div class="findings-section">
                <div class="findings-header">
                    <h2>Detailed Findings ({len(findings)})</h2>
                    <div class="filter-buttons">
                        <button class="filter-btn active" onclick="filterFindings('all')">All</button>
                        <button class="filter-btn" onclick="filterFindings('critical')">Critical</button>
                        <button class="filter-btn" onclick="filterFindings('high')">High</button>
                        <button class="filter-btn" onclick="filterFindings('medium')">Medium</button>
                        <button class="filter-btn" onclick="filterFindings('low')">Low</button>
                    </div>
                </div>
                {''.join(findings_html)}
            </div>
        </div>
        """
    
    def _generate_footer(self, summary: ScanSummary) -> str:
        """Generate report footer"""
        return f"""
        <div class="footer">
            <p>Generated by {self.tool_name} v{self.tool_version}</p>
            <p>This report contains sensitive security information. Handle with care.</p>
        </div>
        """
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactivity"""
        return """
        function toggleFinding(id) {
            const content = document.getElementById('finding-' + id);
            content.classList.toggle('expanded');
        }
        
        function filterFindings(severity) {
            const items = document.querySelectorAll('.finding-item');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // Update active button
            buttons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.toLowerCase() === severity || 
                    (severity === 'all' && btn.textContent === 'All')) {
                    btn.classList.add('active');
                }
            });
            
            // Filter items
            items.forEach(item => {
                if (severity === 'all' || item.dataset.severity === severity) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        }
        """
    
    def write(self, findings: List[Finding], summary: ScanSummary,
              output_path: Union[str, Path]) -> Path:
        """Write HTML report to file"""
        output_path = Path(output_path)
        html_content = self.format(findings, summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path


# =============================================================================
# Utility Functions
# =============================================================================

def convert_findings(raw_findings: List[Dict[str, Any]]) -> List[Finding]:
    """Convert raw dictionary findings to Finding objects"""
    findings = []
    for f in raw_findings:
        finding = Finding(
            id=f.get('id', str(hashlib.md5(str(f).encode()).hexdigest()[:8])),
            title=f.get('title', 'Unknown'),
            description=f.get('description', ''),
            severity=f.get('severity', 'info').lower(),
            target=f.get('target', ''),
            category=f.get('category', 'general'),
            cve_id=f.get('cve_id'),
            cvss_score=f.get('cvss_score'),
            remediation=f.get('remediation'),
            references=f.get('references', []),
            discovered_at=f.get('discovered_at', datetime.utcnow().isoformat()),
            evidence=f.get('evidence'),
            location=f.get('location')
        )
        findings.append(finding)
    return findings


def create_summary(findings: List[Finding], scan_id: str, target: str,
                   duration: int = 0) -> ScanSummary:
    """Create scan summary from findings"""
    
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.severity.lower()
        if sev in counts:
            counts[sev] += 1
    
    # Calculate risk score (simple algorithm)
    risk_score = min(100, (
        counts["critical"] * 20 +
        counts["high"] * 10 +
        counts["medium"] * 5 +
        counts["low"] * 1
    ))
    
    return ScanSummary(
        scan_id=scan_id,
        target=target,
        scan_date=datetime.utcnow().isoformat() + "Z",
        duration=duration,
        total_findings=len(findings),
        critical=counts["critical"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        info=counts["info"],
        risk_score=risk_score
    )


def export_all_formats(findings: List[Finding], summary: ScanSummary,
                       output_dir: Union[str, Path],
                       prefix: str = "scan") -> Dict[str, Path]:
    """Export findings to all supported formats"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # SARIF
    sarif_formatter = SARIFFormatter()
    results['sarif'] = sarif_formatter.write(
        findings, summary, output_dir / f"{prefix}.sarif"
    )
    
    # JUnit XML
    junit_formatter = JUnitXMLFormatter()
    results['junit'] = junit_formatter.write(
        findings, summary, output_dir / f"{prefix}.xml"
    )
    
    # HTML
    html_formatter = HTMLFormatter()
    results['html'] = html_formatter.write(
        findings, summary, output_dir / f"{prefix}.html"
    )
    
    # JSON
    json_path = output_dir / f"{prefix}.json"
    with open(json_path, 'w') as f:
        json.dump({
            'summary': asdict(summary),
            'findings': [asdict(f) for f in findings]
        }, f, indent=2, default=str)
    results['json'] = json_path
    
    return results


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Example usage
    example_findings = [
        Finding(
            id="FIND-001",
            title="SQL Injection Vulnerability",
            description="The application is vulnerable to SQL injection attacks through the login form.",
            severity="critical",
            target="https://example.com/login",
            category="injection",
            cve_id="CVE-2023-1234",
            cvss_score=9.8,
            remediation="Use parameterized queries and input validation.",
            references=["https://owasp.org/www-community/attacks/SQL_Injection"]
        ),
        Finding(
            id="FIND-002",
            title="Missing Security Headers",
            description="The application is missing important security headers.",
            severity="medium",
            target="https://example.com",
            category="configuration",
            remediation="Add X-Frame-Options, CSP, and HSTS headers."
        ),
        Finding(
            id="FIND-003",
            title="Information Disclosure",
            description="Server version is exposed in HTTP headers.",
            severity="low",
            target="https://example.com",
            category="information-disclosure",
            remediation="Configure server to hide version information."
        )
    ]
    
    summary = create_summary(example_findings, "scan-001", "https://example.com", 120)
    
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "./output"
    
    results = export_all_formats(example_findings, summary, output_dir)
    
    print("Exported to:")
    for fmt, path in results.items():
        print(f"  {fmt}: {path}")
