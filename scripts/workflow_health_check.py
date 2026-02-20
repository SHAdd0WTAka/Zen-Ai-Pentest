#!/usr/bin/env python3
"""
GitHub Actions Workflow Health Check Script

This script analyzes GitHub Actions workflow files for common issues:
- Deprecated action versions
- Missing permissions
- Missing concurrency settings
- Missing timeout-minutes
- YAML syntax errors
- Hardcoded secrets

Usage:
    python scripts/workflow_health_check.py
    python scripts/workflow_health_check.py --verbose
    python scripts/workflow_health_check.py --fix-suggestions
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Installing...")
    os.system("pip install pyyaml")
    import yaml


class WorkflowHealthChecker:
    """Analyzes GitHub Actions workflow files for common issues."""

    # Latest stable versions of common actions
    LATEST_ACTIONS = {
        "actions/checkout": "v4",
        "actions/setup-python": "v5",
        "actions/upload-artifact": "v4",
        "actions/download-artifact": "v4",
        "actions/cache": "v4",
        "actions/github-script": "v7",
        "actions/setup-node": "v4",
        "actions/labeler": "v5",
        "actions/stale": "v9",
        "actions/dependency-review-action": "v4",
        "github/codeql-action/init": "v3",
        "github/codeql-action/autobuild": "v3",
        "github/codeql-action/analyze": "v3",
        "github/codeql-action/upload-sarif": "v3",
        "docker/setup-buildx-action": "v3",
        "docker/login-action": "v3",
        "docker/build-push-action": "v6",
        "docker/metadata-action": "v5",
        "softprops/action-gh-release": "v2",
        "release-drafter/release-drafter": "v6",
        "peter-evans/create-pull-request": "v7",
        "aquasecurity/trivy-action": "master",
        "gitleaks/gitleaks-action": "v2",
        "trufflesecurity/trufflehog": "main",
        "ossf/scorecard-action": "v2.3.1",
        "dependabot/fetch-metadata": "v2",
        "8398a7/action-slack": "v3",
        "Ilshidur/action-discord": "master",
        "sarisia/actions-status-discord": "v1.12.0",
        "micnncim/action-label-syncer": "v1",
        "actions/upload-pages-artifact": "v3",
        "actions/deploy-pages": "v4",
        "actions/labeler": "v5",
        "lewagon/wait-on-check-action": "v1.3.4",
        "PyCQA/bandit": "main",
    }

    # Deprecated patterns to check for
    DEPRECATED_PATTERNS = {
        r"actions/checkout@v[12]\b": "Update to actions/checkout@v4",
        r"actions/setup-python@v[1234]\b": "Update to actions/setup-python@v5",
        r"actions/upload-artifact@v[123]\b": "Update to actions/upload-artifact@v4",
        r"actions/download-artifact@v[123]\b": "Update to actions/download-artifact@v4",
        r"actions/cache@v[123]\b": "Update to actions/cache@v4",
        r"actions/github-script@v[456]\b": "Update to actions/github-script@v7",
        r"actions/setup-node@v[123]\b": "Update to actions/setup-node@v4",
        r"node-version.*['\"](12|14|16|18)['\"]": "Update to Node.js 20",
        r"python-version.*['\"](3\.[6789])['\"]": "Consider updating Python version",
    }

    # Secret patterns to check for (only actual hardcoded values)
    SECRET_PATTERNS = {
        # AWS Access Key ID
        r"AKIA[0-9A-Z]{16}": "AWS Access Key ID detected",
        # GitHub Personal Access Token (classic)
        r"ghp_[a-zA-Z0-9]{36}": "GitHub token detected",
        # OpenAI API key
        r"sk-[a-zA-Z0-9]{20,}": "OpenAI/API key detected",
        # Private keys
        r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----": "Private key detected",
        # Hardcoded passwords (not GitHub secrets)
        r"password:\s*[\"'][^${][^\"']{3,}[\"']": "Hardcoded password detected",
        r"passwd:\s*[\"'][^${][^\"']{3,}[\"']": "Hardcoded password detected",
    }
    
    # Lines to ignore (GitHub expressions, env vars, etc.)
    IGNORE_PATTERNS = [
        r"secrets\.",  # GitHub secrets reference
        r"env\.",  # Environment variables
        r"^\s*#",  # Comments
        r"^[\s]*$",  # Empty lines
        r"example",  # Example values
        r"your_",  # Placeholders like your_token
        r"<",  # Template placeholders
    ]

    def __init__(self, workflows_dir: str = ".github/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.issues: list[dict[str, Any]] = []
        self.summary = {
            "total_workflows": 0,
            "workflows_with_issues": 0,
            "total_issues": 0,
            "issues_by_type": {},
            "issues_by_severity": {"error": 0, "warning": 0, "info": 0},
        }

    def add_issue(
        self, workflow: str, issue_type: str, message: str, severity: str = "warning", line: int = None
    ):
        """Add an issue to the report."""
        issue = {
            "workflow": workflow,
            "type": issue_type,
            "message": message,
            "severity": severity,
            "line": line,
        }
        self.issues.append(issue)
        self.summary["total_issues"] += 1
        self.summary["issues_by_type"][issue_type] = (
            self.summary["issues_by_type"].get(issue_type, 0) + 1
        )
        self.summary["issues_by_severity"][severity] += 1

    def check_yaml_syntax(self, workflow_path: Path) -> dict | None:
        """Check YAML syntax and return parsed content."""
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                content = f.read()
                return yaml.safe_load(content)
        except yaml.scanner.ScannerError as e:
            # Only report real YAML errors, not heredoc parsing issues
            error_msg = str(e)
            # Skip errors that are likely from heredoc content
            if "could not find expected ':'" in error_msg and "import " in error_msg:
                # This is likely a heredoc with Python code, try to parse anyway
                try:
                    # Try parsing by preprocessing
                    lines = content.split('\n')
                    processed_lines = []
                    in_heredoc = False
                    for line in lines:
                        if '<<' in line and ('PYEOF' in line or 'EOF' in line):
                            in_heredoc = not in_heredoc
                            processed_lines.append(line)
                        elif in_heredoc:
                            # Comment out heredoc content for parsing
                            processed_lines.append('# ' + line)
                        else:
                            processed_lines.append(line)
                    return yaml.safe_load('\n'.join(processed_lines))
                except:
                    pass
            self.add_issue(
                workflow_path.name,
                "yaml_syntax",
                f"YAML syntax error: {e}",
                "error",
            )
            return None
        except Exception as e:
            self.add_issue(
                workflow_path.name,
                "file_read",
                f"Failed to read file: {e}",
                "error",
            )
            return None

    def check_action_versions(self, workflow_path: Path, content: dict):
        """Check for deprecated action versions."""
        with open(workflow_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Check for deprecated patterns
            for pattern, message in self.DEPRECATED_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    self.add_issue(
                        workflow_path.name,
                        "deprecated_action",
                        f"Line {line_num}: {message}",
                        "warning",
                        line_num,
                    )

            # Check for actions that could be updated
            match = re.search(r"uses:\s+([^@]+)@(\S+)", line)
            if match:
                action_name = match.group(1)
                current_version = match.group(2)
                if action_name in self.LATEST_ACTIONS:
                    latest = self.LATEST_ACTIONS[action_name]
                    if current_version != latest and not current_version.startswith(latest):
                        self.add_issue(
                            workflow_path.name,
                            "outdated_action",
                            f"Line {line_num}: {action_name}@{current_version} could be updated to {latest}",
                            "info",
                            line_num,
                        )

    def check_permissions(self, workflow_path: Path, content: dict):
        """Check for missing or minimal permissions."""
        if not content:
            return

        # Check workflow-level permissions
        if "permissions" not in content:
            self.add_issue(
                workflow_path.name,
                "missing_permissions",
                "Workflow missing permissions block. Add 'permissions: contents: read' at minimum",
                "warning",
            )

        # Check job-level permissions
        jobs = content.get("jobs", {})
        for job_name, job_config in jobs.items():
            if isinstance(job_config, dict):
                if "permissions" not in job_config and "permissions" not in content:
                    self.add_issue(
                        workflow_path.name,
                        "missing_job_permissions",
                        f"Job '{job_name}' missing permissions. Consider adding job-level permissions",
                        "info",
                    )

    def check_concurrency(self, workflow_path: Path, content: dict):
        """Check for missing concurrency settings."""
        if not content:
            return

        if "concurrency" not in content:
            self.add_issue(
                workflow_path.name,
                "missing_concurrency",
                "Missing concurrency settings. Consider adding:\n"
                "  concurrency:\n"
                "    group: ${{ github.workflow }}-${{ github.ref }}\n"
                "    cancel-in-progress: true",
                "info",
            )

    def check_timeout(self, workflow_path: Path, content: dict):
        """Check for missing timeout-minutes."""
        if not content:
            return

        jobs = content.get("jobs", {})
        for job_name, job_config in jobs.items():
            if isinstance(job_config, dict) and "timeout-minutes" not in job_config:
                self.add_issue(
                    workflow_path.name,
                    "missing_timeout",
                    f"Job '{job_name}' missing timeout-minutes. Consider adding timeout to prevent hanging jobs",
                    "info",
                )

    def check_hardcoded_secrets(self, workflow_path: Path):
        """Check for hardcoded secrets."""
        with open(workflow_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Skip lines that match ignore patterns
            should_ignore = any(
                re.search(pattern, line, re.IGNORECASE) 
                for pattern in self.IGNORE_PATTERNS
            )
            if should_ignore:
                continue
                
            for pattern, message in self.SECRET_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    self.add_issue(
                        workflow_path.name,
                        "potential_secret",
                        f"Line {line_num}: {message}",
                        "error",
                        line_num,
                    )

    def check_on_triggers(self, workflow_path: Path, content: dict):
        """Check for workflow triggers."""
        if not content:
            return

        # Handle 'on' key which YAML may parse as True
        on_config = content.get("on")
        if on_config is None:
            on_config = content.get(True)  # YAML parses 'on' as True
        
        # Valid triggers include push, pull_request, schedule, workflow_dispatch, etc.
        if not on_config or on_config is True:
            self.add_issue(
                workflow_path.name,
                "no_triggers",
                "Workflow has no trigger events defined",
                "error",
            )

    def check_name(self, workflow_path: Path, content: dict):
        """Check for workflow name."""
        if not content:
            return

        if "name" not in content:
            self.add_issue(
                workflow_path.name,
                "missing_name",
                "Workflow missing name. Add a descriptive name for better visibility",
                "info",
            )

    def analyze_workflow(self, workflow_path: Path) -> bool:
        """Analyze a single workflow file. Returns True if issues found."""
        print(f"  [CHECK] {workflow_path.name}")
        
        content = self.check_yaml_syntax(workflow_path)
        if content is None:
            return True

        initial_issue_count = len(self.issues)
        
        self.check_action_versions(workflow_path, content)
        self.check_permissions(workflow_path, content)
        self.check_concurrency(workflow_path, content)
        self.check_timeout(workflow_path, content)
        self.check_hardcoded_secrets(workflow_path)
        self.check_on_triggers(workflow_path, content)
        self.check_name(workflow_path, content)

        return len(self.issues) > initial_issue_count

    def run(self) -> dict:
        """Run the health check on all workflows."""
        if not self.workflows_dir.exists():
            print(f"Error: Workflows directory not found: {self.workflows_dir}")
            sys.exit(1)

        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(
            self.workflows_dir.glob("*.yaml")
        )
        
        # Filter out disabled workflows
        workflow_files = [w for w in workflow_files if ".disabled" not in w.name]

        self.summary["total_workflows"] = len(workflow_files)

        print(f"\n[SCAN] Analyzing {len(workflow_files)} workflow files...\n")

        for workflow_path in sorted(workflow_files):
            has_issues = self.analyze_workflow(workflow_path)
            if has_issues:
                self.summary["workflows_with_issues"] += 1

        return self.summary

    def print_report(self, verbose: bool = False, fix_suggestions: bool = False):
        """Print the health check report."""
        print("\n" + "=" * 80)
        print("WORKFLOW HEALTH CHECK REPORT")
        print("=" * 80)

        print(f"\n[SUMMARY] Total Workflows: {self.summary['total_workflows']}")
        print(f"[WARN] Workflows with Issues: {self.summary['workflows_with_issues']}")
        print(f"[INFO] Total Issues Found: {self.summary['total_issues']}")

        print("\n[BY SEVERITY] Issues by Severity:")
        for severity, count in self.summary["issues_by_severity"].items():
            prefix = {"error": "[ERR]", "warning": "[WARN]", "info": "[INFO]"}.get(severity, "[?]")
            print(f"  {prefix} {severity.capitalize()}: {count}")

        if self.summary["issues_by_type"]:
            print("\n[BY TYPE] Issues by Type:")
            for issue_type, count in sorted(
                self.summary["issues_by_type"].items(), key=lambda x: -x[1]
            ):
                print(f"  - {issue_type}: {count}")

        if verbose and self.issues:
            print("\n" + "-" * 80)
            print("[DETAILS] DETAILED ISSUES")
            print("-" * 80)

            current_workflow = None
            for issue in self.issues:
                if issue["workflow"] != current_workflow:
                    current_workflow = issue["workflow"]
                    print(f"\n[FILE] {current_workflow}")
                
                prefix = {
                    "error": "[ERR]",
                    "warning": "[WARN]",
                    "info": "[INFO]",
                }.get(issue["severity"], "[?]")
                
                line_info = f" (line {issue['line']})" if issue["line"] else ""
                print(f"  {prefix} [{issue['type']}]{line_info}: {issue['message']}")

        if fix_suggestions and self.issues:
            print("\n" + "-" * 80)
            print("[FIXES] FIX SUGGESTIONS")
            print("-" * 80)
            print("\nCommon fixes:")
            print("  1. Add concurrency settings to prevent redundant runs")
            print("  2. Add permissions block for least-privilege access")
            print("  3. Add timeout-minutes to all jobs")
            print("  4. Update deprecated action versions")
            print("\nExample minimal configuration:")
            print("""
name: Workflow Name

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  job-name:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
""")

        print("\n" + "=" * 80)
        
        # Return exit code based on errors
        if self.summary["issues_by_severity"]["error"] > 0:
            print("[FAIL] Health check completed with ERRORS")
            return 1
        elif self.summary["issues_by_severity"]["warning"] > 0:
            print("[WARN] Health check completed with WARNINGS")
            return 0
        else:
            print("[PASS] Health check completed successfully")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Actions Workflow Health Checker"
    )
    parser.add_argument(
        "--workflows-dir",
        default=".github/workflows",
        help="Path to workflows directory",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed issue information"
    )
    parser.add_argument(
        "--fix-suggestions",
        action="store_true",
        help="Show fix suggestions and examples",
    )
    parser.add_argument(
        "--json", "-j", action="store_true", help="Output report as JSON"
    )
    parser.add_argument(
        "--output", "-o", help="Save report to file"
    )

    args = parser.parse_args()

    checker = WorkflowHealthChecker(args.workflows_dir)
    summary = checker.run()

    if args.json:
        report = {
            "summary": summary,
            "issues": checker.issues,
        }
        output = json.dumps(report, indent=2)
        if args.output:
            with open(args.output, "w", encoding='utf-8') as f:
                f.write(output)
            print(f"\n[SAVE] Report saved to {args.output}")
        else:
            print(output)
    else:
        exit_code = checker.print_report(args.verbose, args.fix_suggestions)
        
        if args.output:
            report = {
                "summary": summary,
                "issues": checker.issues,
            }
            with open(args.output, "w", encoding='utf-8') as f:
                json.dump(report, indent=2, fp=f)
            print(f"[SAVE] JSON report saved to {args.output}")
        
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
