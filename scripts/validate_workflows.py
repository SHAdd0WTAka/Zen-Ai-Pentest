#!/usr/bin/env python3
"""
Validate GitHub Actions workflows for common issues.

Usage: python scripts/validate_workflows.py
"""

import glob
import re
import sys
from pathlib import Path


def validate_workflow_file(filepath: str) -> list[dict]:
    """Validate a single workflow file and return list of issues."""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{"line": 0, "message": f"Failed to read file: {e}", "severity": "error"}]
    
    # Check 1: Using secrets in job-level 'if' condition (GitHub Actions limitation)
    job_if_pattern = r'^\s+if:\s*.*secrets\.'
    for i, line in enumerate(lines, 1):
        if re.match(job_if_pattern, line):
            issues.append({
                "line": i,
                "message": "Using 'secrets' in job-level 'if' condition is not allowed in GitHub Actions",
                "severity": "error",
                "fix": "Move the secret check to a step-level condition instead"
            })
    
    # Check 2: Missing continue-on-error for external service calls
    if 'discord' in filepath.lower() or 'webhook' in filepath.lower() or 'notify' in filepath.lower():
        if 'continue-on-error' not in content and 'if: steps.check-secret' not in content:
            issues.append({
                "line": 0,
                "message": "Notification workflow may fail if webhook is not configured",
                "severity": "warning",
                "fix": "Add 'continue-on-error: true' or a secret check step"
            })
    
    # Check 3: Shell JSON escaping issues
    json_payload_patterns = [
        r'sanitize_json\(\)',
        r'python3?\s*<<.*EOF.*json',
        r'python3?\s+-c.*json'
    ]
    has_proper_json_handling = any(re.search(p, content, re.IGNORECASE) for p in json_payload_patterns)
    
    if 'json' in content.lower() and not has_proper_json_handling and 'curl' in content:
        # Check for naive sed-based JSON escaping
        if 'sed.*\\\\' in content or 'sed.*\\"' in content:
            issues.append({
                "line": 0,
                "message": "Using sed for JSON escaping may fail with special characters",
                "severity": "warning",
                "fix": "Use Python or jq for proper JSON handling"
            })
    
    # Check 4: Timeout settings
    if 'timeout-minutes' not in content and 'jobs:' in content:
        issues.append({
            "line": 0,
            "message": "No timeout-minutes set for jobs",
            "severity": "warning",
            "fix": "Add 'timeout-minutes: 5' (or appropriate value) to prevent hung jobs"
        })
    
    # Check 5: Concurrency settings (prevents parallel run issues)
    if 'concurrency:' not in content:
        issues.append({
            "line": 0,
            "message": "No concurrency settings found",
            "severity": "info",
            "fix": "Add concurrency settings to prevent multiple simultaneous runs"
        })
    
    # Check 6: Permissions (security best practice)
    if 'permissions:' not in content:
        issues.append({
            "line": 0,
            "message": "No permissions specified",
            "severity": "info",
            "fix": "Add minimal permissions (e.g., 'permissions: contents: read')"
        })
    
    # Check 7: Using deprecated action versions
    deprecated_patterns = [
        (r'@master\s*$', 'Use specific version tag instead of @master'),
        (r'@v0\s*$', 'Consider using a more recent version'),
    ]
    for i, line in enumerate(lines, 1):
        for pattern, message in deprecated_patterns:
            if re.search(pattern, line) and 'uses:' in line:
                issues.append({
                    "line": i,
                    "message": message,
                    "severity": "warning",
                    "fix": "Pin to a specific version like @v1.12.0"
                })
    
    return issues


def print_validation_results(filepath: str, issues: list[dict]):
    """Print validation results for a file."""
    if not issues:
        print(f"[OK] {filepath}")
        return
    
    error_count = sum(1 for i in issues if i['severity'] == 'error')
    warning_count = sum(1 for i in issues if i['severity'] == 'warning')
    info_count = sum(1 for i in issues if i['severity'] == 'info')
    
    status = "[ERR]" if error_count > 0 else "[WARN]" if warning_count > 0 else "[INFO]"
    print(f"{status} {filepath} ({error_count} errors, {warning_count} warnings, {info_count} info)")
    
    for issue in issues:
        severity_icon = {"error": "[ERR]", "warning": "[WARN]", "info": "[INFO]"}.get(issue['severity'], "[*]")
        line_info = f"line {issue['line']}" if issue['line'] > 0 else "general"
        print(f"   {severity_icon} [{line_info}] {issue['message']}")
        if 'fix' in issue:
            print(f"      Fix: {issue['fix']}")


def main():
    """Main validation function."""
    print("=" * 70)
    print("GitHub Actions Workflow Validator")
    print("=" * 70)
    
    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print(f"❌ Workflow directory not found: {workflow_dir}")
        return 1
    
    workflow_files = list(workflow_dir.glob("*.yml"))
    if not workflow_files:
        print("No workflow files found")
        return 0
    
    total_errors = 0
    total_warnings = 0
    
    for filepath in sorted(workflow_files):
        issues = validate_workflow_file(str(filepath))
        print_validation_results(str(filepath), issues)
        total_errors += sum(1 for i in issues if i['severity'] == 'error')
        total_warnings += sum(1 for i in issues if i['severity'] == 'warning')
    
    print("\n" + "=" * 70)
    print(f"Summary: {total_errors} errors, {total_warnings} warnings")
    print("=" * 70)
    
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
