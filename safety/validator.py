"""
Output Validator - Structured validation against schemas
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ValidationResult:
    """Validation result with details"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    schema_type: str
    confidence_impact: float


class OutputValidator:
    """
    Validates AI outputs against expected schemas and formats.
    Detects structural hallucinations.
    """

    # Expected JSON schemas for common outputs
    SCHEMAS = {
        "vulnerability_report": {
            "required": ["cve_id", "severity", "description"],
            "optional": ["cvss_score", "affected_versions", "remediation"],
            "types": {
                "cve_id": str,
                "severity": str,
                "cvss_score": (int, float),
                "description": str,
            },
        },
        "port_scan": {
            "required": ["target", "open_ports"],
            "optional": ["scan_duration", "service_versions"],
            "types": {
                "target": str,
                "open_ports": list,
                "scan_duration": (int, float),
            },
        },
        "tool_output": {
            "required": ["tool_name", "command", "output"],
            "optional": ["return_code", "execution_time"],
            "types": {
                "tool_name": str,
                "command": str,
                "output": str,
                "return_code": int,
            },
        },
    }

    def __init__(self):
        self.validation_history: List[Dict] = []

    def validate_json(
        self, output: str, schema_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate JSON output against schema
        """
        errors = []
        warnings = []
        confidence_impact = 0.0

        # Try to parse JSON
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            confidence_impact = 0.8
            return ValidationResult(
                False,
                errors,
                warnings,
                schema_name or "unknown",
                confidence_impact,
            )

        # Validate against schema if specified
        if schema_name and schema_name in self.SCHEMAS:
            schema = self.SCHEMAS[schema_name]

            # Check required fields
            for field in schema["required"]:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
                    confidence_impact += 0.2

            # Check types
            for field, expected_type in schema["types"].items():
                if field in data:
                    actual_value = data[field]
                    if not isinstance(actual_value, expected_type):
                        errors.append(
                            f"Field '{field}' has wrong type: expected {expected_type}, got {type(actual_value)}"
                        )
                        confidence_impact += 0.15

            # Check for unexpected fields (possible hallucination)
            all_valid_fields = schema["required"] + schema["optional"]
            for field in data.keys():
                if field not in all_valid_fields:
                    warnings.append(f"Unexpected field: {field}")
                    confidence_impact += 0.1

        # Record validation
        self.validation_history.append(
            {
                "schema": schema_name,
                "valid": len(errors) == 0,
                "error_count": len(errors),
            }
        )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_type=schema_name or "unknown",
            confidence_impact=min(confidence_impact, 1.0),
        )

    def validate_command_output(
        self, output: str, expected_tool: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate that tool output looks legitimate
        """
        errors = []
        warnings = []
        confidence_impact = 0.0

        # Check for obviously fake outputs
        fake_indicators = [
            r"example\.com",  # Example domains
            r"192\.168\.x\.x",  # Placeholder IPs
            r"\[REDACTED\]",  # Common placeholder
            r"xxx\.xxx\.xxx",  # Masked data pattern
        ]

        for indicator in fake_indicators:
            if re.search(indicator, output, re.IGNORECASE):
                warnings.append(
                    f"Possible placeholder data detected: {indicator}"
                )
                confidence_impact += 0.15

        # Check output length (hallucinations often too verbose)
        lines = output.strip().splitlines()
        if len(lines) > 500:
            warnings.append(f"Unusually long output: {len(lines)} lines")
            confidence_impact += 0.1

        # Check for inconsistent formatting
        if expected_tool:
            format_issues = self._check_tool_format(output, expected_tool)
            warnings.extend(format_issues)
            confidence_impact += 0.05 * len(format_issues)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_type=(
                f"tool:{expected_tool}" if expected_tool else "generic"
            ),
            confidence_impact=min(confidence_impact, 1.0),
        )

    def _check_tool_format(self, output: str, tool_name: str) -> List[str]:
        """Check if output matches expected tool format"""
        issues = []

        # Tool-specific format checks
        format_patterns = {
            "nmap": r"(Nmap scan report|PORT\s+STATE\s+SERVICE)",
            "nikto": r"(Nikto|Target IP|Target Hostname)",
            "sqlmap": r"(sqlmap|Target|back-end DBMS)",
        }

        if tool_name in format_patterns:
            pattern = format_patterns[tool_name]
            if not re.search(pattern, output, re.IGNORECASE):
                issues.append(
                    f"Output doesn't match expected {tool_name} format"
                )

        return issues

    def validate_factual_consistency(
        self, new_output: str, memory_context: List[str]
    ) -> ValidationResult:
        """
        Check if new output contradicts previous known facts
        """
        errors = []
        warnings = []
        confidence_impact = 0.0

        # Extract potential facts from new output
        ip_pattern = r"(?:\d{1,3}\.){3}\d{1,3}"
        cve_pattern = r"CVE-\d{4}-\d{4,}"
        port_pattern = r"port\s+(\d{1,5})"

        new_cves = set(re.findall(cve_pattern, new_output, re.IGNORECASE))
        _ = re.findall(port_pattern, new_output, re.IGNORECASE)  # new_ports

        # Check against memory context
        for memory in memory_context:
            _ = re.findall(ip_pattern, memory)  # memory_ips
            memory_cves = set(re.findall(cve_pattern, memory, re.IGNORECASE))

            # Check for contradictory CVE claims
            for cve in new_cves:
                if cve.upper() in [c.upper() for c in memory_cves]:
                    # Same CVE mentioned - check for contradiction
                    if self._check_contradiction(new_output, memory, cve):
                        errors.append(f"Contradictory statements about {cve}")
                        confidence_impact += 0.3

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_type="consistency_check",
            confidence_impact=min(confidence_impact, 1.0),
        )

    def _check_contradiction(
        self, text1: str, text2: str, keyword: str
    ) -> bool:
        """Simple contradiction detection around keyword"""
        # Extract sentences containing keyword
        sentences1 = [
            s for s in text1.split(".") if keyword.lower() in s.lower()
        ]
        sentences2 = [
            s for s in text2.split(".") if keyword.lower() in s.lower()
        ]

        # Check for opposite sentiments (simplified)
        negations = ["not", "no", "false", "incorrect", "wrong"]

        for s1 in sentences1:
            s1_has_neg = any(n in s1.lower() for n in negations)
            for s2 in sentences2:
                s2_has_neg = any(n in s2.lower() for n in negations)
                if s1_has_neg != s2_has_neg:
                    return True

        return False
