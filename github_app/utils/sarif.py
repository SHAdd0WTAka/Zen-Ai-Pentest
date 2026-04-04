"""SARIF report generator for GitHub Security tab integration."""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """SARIF severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOTE = "note"
    NONE = "none"


# CWE to category mapping
CWE_CATEGORIES = {
    "CWE-79": {"name": "Cross-site Scripting (XSS)", "category": "security"},
    "CWE-89": {"name": "SQL Injection", "category": "security"},
    "CWE-94": {"name": "Code Injection", "category": "security"},
    "CWE-22": {"name": "Path Traversal", "category": "security"},
    "CWE-200": {"name": "Information Exposure", "category": "security"},
    "CWE-798": {"name": "Hardcoded Credentials", "category": "security"},
    "CWE-352": {"name": "CSRF", "category": "security"},
    "CWE-434": {"name": "Unrestricted File Upload", "category": "security"},
    "CWE-502": {"name": "Deserialization", "category": "security"},
    "CWE-918": {"name": "SSRF", "category": "security"},
    "CWE-611": {"name": "XXE", "category": "security"},
    "CWE-287": {"name": "Improper Authentication", "category": "security"},
    "CWE-306": {"name": "Missing Authentication", "category": "security"},
    "CWE-862": {"name": "Missing Authorization", "category": "security"},
    "CWE-863": {"name": "Incorrect Authorization", "category": "security"},
}


class Finding:
    """Security finding model."""

    def __init__(
        self,
        rule_id: str,
        message: str,
        file_path: str,
        line_number: int,
        severity: Severity,
        cwe: Optional[str] = None,
        description: Optional[str] = None,
        recommendation: Optional[str] = None,
        code_snippet: Optional[str] = None,
    ):
        self.rule_id = rule_id
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.severity = severity
        self.cwe = cwe
        self.description = description or message
        self.recommendation = recommendation
        self.code_snippet = code_snippet
        self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """Generate unique fingerprint for deduplication."""
        data = f"{self.rule_id}:{self.file_path}:{self.line_number}:{self.message}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class SARIFGenerator:
    """Generate SARIF reports for GitHub Security tab."""

    def __init__(self, tool_name: str = "Zen-AI-Pentest", tool_version: str = "1.0.0", organization: str = "Zen-AI-Security"):
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.organization = organization
        self.findings: List[Finding] = []

    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the report."""
        self.findings.append(finding)

    def add_findings(self, findings: List[Finding]) -> None:
        """Add multiple findings."""
        self.findings.extend(findings)

    def generate(self) -> Dict[str, Any]:
        """Generate SARIF report."""

        # Group findings by rule
        rules = {}
        results = []

        for finding in self.findings:
            # Create or get rule
            if finding.rule_id not in rules:
                rules[finding.rule_id] = self._create_rule(finding)

            # Create result
            result = self._create_result(finding)
            results.append(result)

        sarif_report = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.tool_name,
                            "version": self.tool_version,
                            "organization": self.organization,
                            "rules": list(rules.values()),
                        }
                    },
                    "results": results,
                    "automationDetails": {
                        "id": f"{self.tool_name.lower().replace(' ', '-')}/scan-{datetime.now(timezone.utc).isoformat()}"
                    },
                }
            ],
        }

        return sarif_report

    def generate_json(self, indent: int = 2) -> str:
        """Generate SARIF report as JSON string."""
        return json.dumps(self.generate(), indent=indent)

    def _create_rule(self, finding: Finding) -> Dict[str, Any]:
        """Create SARIF rule from finding."""
        rule = {
            "id": finding.rule_id,
            "name": finding.rule_id,
            "shortDescription": {"text": finding.message[:100] if len(finding.message) > 100 else finding.message},
            "fullDescription": {"text": finding.description},
            "defaultConfiguration": {"level": self._severity_to_level(finding.severity)},
            "properties": {"tags": ["security"], "precision": "high", "severity": finding.severity.value},
        }

        # Add CWE information
        if finding.cwe and finding.cwe in CWE_CATEGORIES:
            cwe_info = CWE_CATEGORIES[finding.cwe]
            rule["properties"]["tags"].append(cwe_info["category"])
            rule["properties"]["cwe"] = finding.cwe

            # Add CWE relationships
            rule["relationships"] = [
                {"target": {"id": finding.cwe, "toolComponent": {"name": "CWE", "index": 0}}, "kinds": ["relevant"]}
            ]

        # Add recommendation as help
        if finding.recommendation:
            rule["help"] = {"text": finding.recommendation, "markdown": finding.recommendation}

        return rule

    def _create_result(self, finding: Finding) -> Dict[str, Any]:
        """Create SARIF result from finding."""
        result = {
            "ruleId": finding.rule_id,
            "ruleIndex": 0,
            "level": self._severity_to_level(finding.severity),
            "message": {"text": finding.message},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.file_path, "uriBaseId": "%SRCROOT%"},
                        "region": {"startLine": finding.line_number, "endLine": finding.line_number},
                    }
                }
            ],
            "fingerprints": {"primary": finding.fingerprint},
            "properties": {"severity": finding.severity.value},
        }

        # Add code snippet if available
        if finding.code_snippet:
            result["locations"][0]["physicalLocation"]["region"]["snippet"] = {"text": finding.code_snippet}

        return result

    def _severity_to_level(self, severity: Severity) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.NOTE: "note",
            Severity.NONE: "none",
        }
        return mapping.get(severity, "warning")

    def get_summary(self) -> Dict[str, int]:
        """Get summary of findings by severity."""
        summary = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            summary[finding.severity.value] += 1
        return summary
