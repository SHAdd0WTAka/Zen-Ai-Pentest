#!/usr/bin/env python3
"""
GitHub Actions Workflow Validator
Validates workflow files for syntax errors, invalid references, and common issues.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

# Configure logging
logger = logging.getLogger(__name__)

# GitHub-hosted runners (as of 2026)
SUPPORTED_RUNNERS: Set[str] = {
    "ubuntu-latest",
    "ubuntu-24.04",
    "ubuntu-22.04",
    "ubuntu-20.04",
    "windows-latest",
    "windows-2022",
    "windows-2019",
    "macos-latest",
    "macos-15",
    "macos-14",
    "macos-13",
    "macos-12",
}

# Required top-level fields for workflow files
REQUIRED_WORKFLOW_FIELDS: Set[str] = {"name", "on"}

# Valid 'on' triggers (from GitHub Actions documentation)
VALID_TRIGGERS: Set[str] = {
    "push",
    "pull_request",
    "pull_request_target",
    "workflow_dispatch",
    "schedule",
    "release",
    "workflow_call",
    "workflow_run",
    "repository_dispatch",
    "issues",
    "issue_comment",
    "create",
    "delete",
    "deployment",
    "deployment_status",
    "fork",
    "gollum",
    "label",
    "member",
    "milestone",
    "page_build",
    "project",
    "project_card",
    "project_column",
    "public",
    "registry_package",
    "status",
    "watch",
    "discussion",
    "discussion_comment",
    "merge_group",
    # Additional valid triggers
    "pull_request_review",
    "pull_request_review_comment",
    "check_suite",
    "branch_protection_rule",
    "check_run",
}


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a workflow file."""

    level: str  # error, warning, info
    message: str
    location: str = ""  # e.g., "jobs.build.steps[0]"


@dataclass
class WorkflowValidationResult:
    """Result of validating a single workflow file."""

    file_path: str
    is_valid_yaml: bool
    yaml_error: Optional[str]
    issues: List[ValidationIssue]
    runner_types: List[str]
    referenced_actions: List[str]
    referenced_files: List[str]
    missing_files: List[str]


class WorkflowValidator:
    """Validates GitHub Actions workflow files."""

    def __init__(self, workflows_dir: str) -> None:
        """Initialize the validator.

        Args:
            workflows_dir: Path to the directory containing workflow files.
        """
        self.workflows_dir = Path(workflows_dir)
        self.project_root = self.workflows_dir.parent.parent
        self.results: List[WorkflowValidationResult] = []

    def validate_all(self) -> None:
        """Validate all workflow files in the workflows directory."""
        workflow_files = sorted(self.workflows_dir.glob("*.yml"))

        logger.info("Found %d workflow files to validate", len(workflow_files))
        print(f"Found {len(workflow_files)} workflow files to validate\n")

        for workflow_file in workflow_files:
            result = self.validate_workflow(workflow_file)
            self.results.append(result)

    def validate_workflow(self, file_path: Path) -> WorkflowValidationResult:
        """Validate a single workflow file.

        Args:
            file_path: Path to the workflow file.

        Returns:
            Validation result containing any issues found.
        """
        issues: List[ValidationIssue] = []
        runner_types: List[str] = []
        referenced_actions: List[str] = []
        referenced_files: List[str] = []
        missing_files: List[str] = []

        # Try to parse YAML
        workflow_data, is_valid_yaml, yaml_error = self._parse_yaml(file_path, issues)

        if not is_valid_yaml:
            return self._create_error_result(file_path, yaml_error, issues, "YAML Syntax Error")

        if workflow_data is None:
            return self._create_error_result(file_path, "Workflow file is empty", issues, "Empty File")

        # Validate workflow structure
        self._validate_structure(workflow_data, issues)

        # Validate triggers
        on_triggers = workflow_data.get("on") or workflow_data.get(True, {})
        if on_triggers:
            self._validate_triggers(on_triggers, issues)

        # Validate jobs
        jobs = workflow_data.get("jobs", {})
        if jobs and isinstance(jobs, dict):
            self._validate_jobs(jobs, issues, runner_types, referenced_actions, referenced_files, missing_files)
            self._check_duplicate_job_names(jobs, issues)

        return WorkflowValidationResult(
            file_path=str(file_path),
            is_valid_yaml=True,
            yaml_error=None,
            issues=issues,
            runner_types=list(set(runner_types)),
            referenced_actions=list(set(referenced_actions)),
            referenced_files=list(set(referenced_files)),
            missing_files=list(set(missing_files)),
        )

    def _parse_yaml(
        self, file_path: Path, issues: List[ValidationIssue]
    ) -> Tuple[Optional[Dict[str, Any]], bool, Optional[str]]:
        """Parse YAML file and return data or error information.

        Args:
            file_path: Path to the YAML file.
            issues: List to append validation issues to.

        Returns:
            Tuple of (workflow_data, is_valid, error_message).
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            workflow_data = yaml.safe_load(content)
            return workflow_data, True, None
        except yaml.YAMLError as e:
            error_msg = str(e)
            issues.append(ValidationIssue("error", f"YAML Syntax Error: {error_msg}"))
            return None, False, error_msg
        except Exception as e:
            error_msg = str(e)
            issues.append(ValidationIssue("error", f"File Read Error: {error_msg}"))
            return None, False, error_msg

    def _create_error_result(
        self, file_path: Path, error: str, issues: List[ValidationIssue], error_type: str = "Error"
    ) -> WorkflowValidationResult:
        """Create an error result for a workflow file.

        Args:
            file_path: Path to the workflow file.
            error: Error message.
            issues: List of validation issues.
            error_type: Type of error for logging.

        Returns:
            Validation result with error information.
        """
        logger.error("%s in %s: %s", error_type, file_path, error)
        return WorkflowValidationResult(
            file_path=str(file_path),
            is_valid_yaml=False,
            yaml_error=error,
            issues=issues,
            runner_types=[],
            referenced_actions=[],
            referenced_files=[],
            missing_files=[],
        )

    def _validate_structure(self, workflow_data: Dict[str, Any], issues: List[ValidationIssue]) -> None:
        """Validate the top-level structure of a workflow.

        Args:
            workflow_data: Parsed workflow data.
            issues: List to append validation issues to.
        """
        workflow_keys = set(workflow_data.keys())
        has_on_trigger = "on" in workflow_keys or True in workflow_keys

        missing_fields: Set[str] = set()
        if "name" not in workflow_keys:
            missing_fields.add("name")
        if not has_on_trigger:
            missing_fields.add("on")

        for field in missing_fields:
            issues.append(ValidationIssue("error", f"Missing required field: '{field}'"))

    def _validate_jobs(
        self,
        jobs: Dict[str, Any],
        issues: List[ValidationIssue],
        runner_types: List[str],
        referenced_actions: List[str],
        referenced_files: List[str],
        missing_files: List[str],
    ) -> None:
        """Validate all jobs in a workflow.

        Args:
            jobs: Dictionary of job configurations.
            issues: List to append validation issues to.
            runner_types: List to collect runner types.
            referenced_actions: List to collect action references.
            referenced_files: List to collect file references.
            missing_files: List to collect missing files.
        """
        for job_name, job_config in jobs.items():
            if not isinstance(job_config, dict):
                issues.append(
                    ValidationIssue(
                        "error",
                        f"Job '{job_name}' has invalid configuration",
                    )
                )
                continue

            self._validate_job_runner(job_name, job_config, issues, runner_types)
            self._validate_job_steps(job_name, job_config, issues, referenced_actions, referenced_files, missing_files)

    def _validate_job_runner(
        self, job_name: str, job_config: Dict[str, Any], issues: List[ValidationIssue], runner_types: List[str]
    ) -> None:
        """Validate the runner configuration for a job.

        Args:
            job_name: Name of the job.
            job_config: Job configuration dictionary.
            issues: List to append validation issues to.
            runner_types: List to collect runner types.
        """
        runs_on = job_config.get("runs-on")
        if runs_on:
            if isinstance(runs_on, str):
                runner_types.append(runs_on)
                self._validate_runner_string(job_name, runs_on, issues)
            elif isinstance(runs_on, list):
                runner_types.extend(runs_on)
            # matrix or group configuration is allowed as dict
        else:
            issues.append(
                ValidationIssue(
                    "error",
                    f"Job '{job_name}' is missing 'runs-on' field",
                )
            )

    def _validate_runner_string(self, job_name: str, runs_on: str, issues: List[ValidationIssue]) -> None:
        """Validate a runner string.

        Args:
            job_name: Name of the job.
            runs_on: Runner string to validate.
            issues: List to append validation issues to.
        """
        if runs_on.startswith("$"):
            return  # Allow expressions

        if runs_on not in SUPPORTED_RUNNERS:
            if not any(label in runs_on.lower() for label in ["self-hosted", "ubuntu", "windows", "macos"]):
                issues.append(
                    ValidationIssue(
                        "warning",
                        f"Job '{job_name}' uses potentially unsupported runner: '{runs_on}'",
                    )
                )

    def _validate_job_steps(
        self,
        job_name: str,
        job_config: Dict[str, Any],
        issues: List[ValidationIssue],
        referenced_actions: List[str],
        referenced_files: List[str],
        missing_files: List[str],
    ) -> None:
        """Validate the steps in a job.

        Args:
            job_name: Name of the job.
            job_config: Job configuration dictionary.
            issues: List to append validation issues to.
            referenced_actions: List to collect action references.
            referenced_files: List to collect file references.
            missing_files: List to collect missing files.
        """
        steps = job_config.get("steps", [])
        if not steps or not isinstance(steps, list):
            return

        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            # Check for 'uses' (action reference)
            self._validate_step_uses(job_name, idx, step, issues, referenced_actions)

            # Check for 'run' with file references
            self._validate_step_run(job_name, idx, step, issues, referenced_files, missing_files)

            # Check working-directory
            working_dir = step.get("working-directory")
            if working_dir:
                referenced_files.append(working_dir)

    def _validate_step_uses(
        self, job_name: str, step_idx: int, step: Dict[str, Any], issues: List[ValidationIssue], referenced_actions: List[str]
    ) -> None:
        """Validate the 'uses' directive in a step.

        Args:
            job_name: Name of the job.
            step_idx: Index of the step.
            step: Step configuration dictionary.
            issues: List to append validation issues to.
            referenced_actions: List to collect action references.
        """
        uses = step.get("uses")
        if not uses:
            return

        referenced_actions.append(uses)
        action_issue = self._validate_action_reference(uses)
        if action_issue:
            issues.append(
                ValidationIssue(
                    "warning",
                    action_issue,
                    f"jobs.{job_name}.steps[{step_idx}]",
                )
            )

    def _validate_step_run(
        self,
        job_name: str,
        step_idx: int,
        step: Dict[str, Any],
        issues: List[ValidationIssue],
        referenced_files: List[str],
        missing_files: List[str],
    ) -> None:
        """Validate the 'run' directive in a step.

        Args:
            job_name: Name of the job.
            step_idx: Index of the step.
            step: Step configuration dictionary.
            issues: List to append validation issues to.
            referenced_files: List to collect file references.
            missing_files: List to collect missing files.
        """
        run_cmd = step.get("run")
        if not run_cmd or not isinstance(run_cmd, str):
            return

        files = self._extract_file_references(run_cmd)
        for file_ref in files:
            referenced_files.append(file_ref)
            if not self._file_exists(file_ref):
                missing_files.append(file_ref)
                issues.append(
                    ValidationIssue(
                        "error",
                        f"Referenced file does not exist: '{file_ref}'",
                        f"jobs.{job_name}.steps[{step_idx}]",
                    )
                )

    def _check_duplicate_job_names(self, jobs: Dict[str, Any], issues: List[ValidationIssue]) -> None:
        """Check for duplicate job names in a workflow.

        Args:
            jobs: Dictionary of job configurations.
            issues: List to append validation issues to.
        """
        job_names = list(jobs.keys())
        seen = set()
        duplicates = set()

        for name in job_names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)

        for dup in duplicates:
            issues.append(ValidationIssue("error", f"Duplicate job name: '{dup}'"))

    def _validate_triggers(self, on_triggers: Any, issues: List[ValidationIssue]) -> None:
        """Validate the 'on' triggers configuration.

        Args:
            on_triggers: The triggers configuration (can be list, dict, or string).
            issues: List to append validation issues to.
        """
        triggers: List[str] = []

        if isinstance(on_triggers, list):
            triggers = on_triggers
        elif isinstance(on_triggers, dict):
            triggers = list(on_triggers.keys())
        elif isinstance(on_triggers, str):
            triggers = [on_triggers]
        else:
            return

        for trigger in triggers:
            if trigger not in VALID_TRIGGERS:
                issues.append(
                    ValidationIssue(
                        "warning",
                        f"Potentially invalid trigger: '{trigger}'",
                    )
                )

    def _validate_action_reference(self, action_ref: str) -> Optional[str]:
        """Validate an action reference.

        Args:
            action_ref: The action reference string.

        Returns:
            Error message if invalid, None if valid.
        """
        # Skip expressions
        if action_ref.startswith("${{"):
            return None

        # Docker references
        if action_ref.startswith("docker://"):
            return None

        # Local paths
        if action_ref.startswith("./") or action_ref.startswith("../"):
            return self._validate_local_action(action_ref)

        # GitHub action references: owner/repo@ref
        return self._validate_github_action(action_ref)

    def _validate_local_action(self, action_ref: str) -> Optional[str]:
        """Validate a local action reference.

        Args:
            action_ref: The local action reference string.

        Returns:
            Error message if invalid, None if valid.
        """
        path = action_ref.lstrip("./")
        full_path = self.project_root / ".github" / "actions" / path
        if not full_path.exists():
            return f"Local action path may not exist: '{action_ref}'"
        return None

    def _validate_github_action(self, action_ref: str) -> Optional[str]:
        """Validate a GitHub action reference.

        Args:
            action_ref: The GitHub action reference string.

        Returns:
            Error message if invalid, None if valid.
        """
        parts = action_ref.split("@")
        if len(parts) != 2:
            return f"Invalid action reference format (missing @version): '{action_ref}'"

        repo_part, version = parts
        if "/" not in repo_part:
            return f"Invalid action reference format (should be owner/repo): '{action_ref}'"

        # Check for semantic version or commit SHA
        is_semver = bool(re.match(r"^v?\d+(\.\d+)*$", version))
        is_sha = bool(re.match(r"^[a-f0-9]{40}$", version))

        if not (is_semver or is_sha):
            # Branch names are not recommended but allowed
            if version in ["main", "master", "develop"]:
                return f"Action references branch '{version}' instead of specific version (not recommended)"

        return None

    def _extract_file_references(self, command: str) -> List[str]:
        """Extract potential file references from a shell command.

        Args:
            command: The shell command to parse.

        Returns:
            List of potential file references.
        """
        files: List[str] = []

        # Common patterns that reference files
        patterns = [
            r"python\s+(\S+\.py)",  # python script.py
            r"python3?\s+[-m]\s+(\S+)",  # python -m module
            r"pip\s+install\s+-r\s+(\S+)",  # pip install -r requirements.txt
            r"bash\s+(\S+\.sh)",  # bash script.sh
            r"\.\/(\S+\.sh)",  # ./script.sh
            r"\.\/(\S+\.py)",  # ./script.py
            r"source\s+(\S+)",  # source file
            r"cat\s+(\S+)",  # cat file
            r"chmod\s+[+x-]+\s+(\S+)",  # chmod +x file
        ]

        for pattern in patterns:
            matches = re.findall(pattern, command)
            files.extend(matches)

        # Filter out common non-file strings
        filtered: List[str] = []
        for f in files:
            if not f.startswith("$") and not f.startswith("-") and ("/" in f or "." in f):
                filtered.append(f)

        return filtered

    def _file_exists(self, file_path: str) -> bool:
        """Check if a file exists relative to the project root.

        Args:
            file_path: Path to check.

        Returns:
            True if file exists or should be skipped, False otherwise.
        """
        # Skip variables and URLs
        if file_path.startswith("$") or file_path.startswith("http"):
            return True

        # Skip paths that are likely generated at runtime
        runtime_patterns = [
            "/tmp/",  # nosec B108
            "/var/tmp/",  # nosec B108
            "$(",
            "${",
            "*.",
            "~",
            "\\\n",
            "|",
            ">",
            "<",
            "&",
            ";",
            "`",
            '"',
            "'",
        ]
        if any(pattern in file_path for pattern in runtime_patterns):
            return True

        # Skip generated files with common patterns
        if self._is_generated_file(file_path):
            return True

        # Clean up the path
        clean_path = file_path.strip().strip('"').strip("'")
        if not clean_path or clean_path.startswith("-"):
            return True

        return self._check_file_in_locations(clean_path)

    def _is_generated_file(self, file_path: str) -> bool:
        """Check if a file is likely a generated/temporary file.

        Args:
            file_path: Path to check.

        Returns:
            True if file is likely generated.
        """
        if not file_path.endswith((".json", ".txt", ".md", ".log")):
            return False

        generated_indicators = ["report", "result", "output", "tmp", "cache"]
        return any(indicator in file_path for indicator in generated_indicators)

    def _check_file_in_locations(self, clean_path: str) -> bool:
        """Check if a file exists in various locations.

        Args:
            clean_path: Cleaned file path.

        Returns:
            True if file exists, False otherwise.
        """
        full_path = self.project_root / clean_path
        if full_path.exists():
            return True

        # Check with common extensions
        for ext in [".py", ".sh", ".yml", ".yaml", ".json"]:
            if full_path.with_suffix(ext).exists():
                return True

        # Check in common directories
        for subdir in [
            "scripts",
            "benchmarks",
            "tools",
            "tests",
            "examples",
            "docs",
            "web_ui",
        ]:
            alt_path = self.project_root / subdir / clean_path
            if alt_path.exists():
                return True
            for ext in [".py", ".sh"]:
                if alt_path.with_suffix(ext).exists():
                    return True
        return False

    def generate_report(self) -> str:
        """Generate a validation report.

        Returns:
            Formatted validation report as a string.
        """
        lines: List[str] = []
        lines.extend(self._generate_report_header())
        lines.extend(self._generate_summary_section())
        lines.extend(self._generate_yaml_errors_section())
        lines.extend(self._generate_errors_section())
        lines.extend(self._generate_warnings_section())
        lines.extend(self._generate_valid_files_section())
        lines.extend(self._generate_runners_section())
        lines.extend(self._generate_actions_section())
        lines.extend(self._generate_report_footer())

        return "\n".join(lines)

    def _generate_report_header(self) -> List[str]:
        """Generate the report header.

        Returns:
            List of header lines.
        """
        return [
            "=" * 80,
            "GITHUB ACTIONS WORKFLOW VALIDATION REPORT",
            "=" * 80,
            "",
        ]

    def _generate_summary_section(self) -> List[str]:
        """Generate the summary section of the report.

        Returns:
            List of summary lines.
        """
        total_files = len(self.results)
        valid_yaml_count = sum(1 for r in self.results if r.is_valid_yaml)
        error_count = sum(1 for r in self.results for i in r.issues if i.level == "error")
        warning_count = sum(1 for r in self.results for i in r.issues if i.level == "warning")

        return [
            f"Total Workflow Files: {total_files}",
            f"Valid YAML Syntax: {valid_yaml_count}/{total_files}",
            f"Total Errors: {error_count}",
            f"Total Warnings: {warning_count}",
            "",
        ]

    def _generate_yaml_errors_section(self) -> List[str]:
        """Generate the YAML errors section of the report.

        Returns:
            List of YAML error lines.
        """
        yaml_errors = [r for r in self.results if not r.is_valid_yaml]
        if not yaml_errors:
            return []

        lines = [
            "-" * 80,
            "🚨 YAML SYNTAX ERRORS (CRITICAL)",
            "-" * 80,
        ]
        for result in yaml_errors:
            lines.append(f"\n❌ {result.file_path}")
            lines.append(f"   Error: {result.yaml_error}")
        lines.append("")
        return lines

    def _generate_errors_section(self) -> List[str]:
        """Generate the errors section of the report.

        Returns:
            List of error section lines.
        """
        files_with_errors = [r for r in self.results if any(i.level == "error" for i in r.issues)]
        if not files_with_errors:
            return []

        lines = [
            "-" * 80,
            "❌ FILES WITH ERRORS",
            "-" * 80,
        ]
        for result in files_with_errors:
            error_issues = [i for i in result.issues if i.level == "error"]
            if error_issues:
                lines.append(f"\n📄 {result.file_path}")
                for issue in error_issues:
                    loc = f" [{issue.location}]" if issue.location else ""
                    lines.append(f"   ❌ {issue.message}{loc}")
        lines.append("")
        return lines

    def _generate_warnings_section(self) -> List[str]:
        """Generate the warnings section of the report.

        Returns:
            List of warning section lines.
        """
        files_with_warnings = [r for r in self.results if any(i.level == "warning" for i in r.issues)]
        if not files_with_warnings:
            return []

        lines = [
            "-" * 80,
            "⚠️ FILES WITH WARNINGS",
            "-" * 80,
        ]
        for result in files_with_warnings:
            warning_issues = [i for i in result.issues if i.level == "warning"]
            if warning_issues:
                lines.append(f"\n📄 {result.file_path}")
                for issue in warning_issues:
                    loc = f" [{issue.location}]" if issue.location else ""
                    lines.append(f"   ⚠️ {issue.message}{loc}")
        lines.append("")
        return lines

    def _generate_valid_files_section(self) -> List[str]:
        """Generate the valid files section of the report.

        Returns:
            List of valid files section lines.
        """
        valid_files = [
            r for r in self.results if r.is_valid_yaml and not any(i.level in ["error", "warning"] for i in r.issues)
        ]
        if not valid_files:
            return []

        lines = [
            "-" * 80,
            "✅ VALID WORKFLOW FILES",
            "-" * 80,
        ]
        for result in valid_files:
            lines.append(f"   ✅ {Path(result.file_path).name}")
        lines.append("")
        return lines

    def _generate_runners_section(self) -> List[str]:
        """Generate the runners section of the report.

        Returns:
            List of runners section lines.
        """
        all_runners: Set[str] = set()
        for result in self.results:
            all_runners.update(result.runner_types)
        if not all_runners:
            return []

        lines = [
            "-" * 80,
            "🏃 RUNNER TYPES USED",
            "-" * 80,
        ]
        for runner in sorted(all_runners):
            supported = "✅" if runner in SUPPORTED_RUNNERS or runner.startswith("$") else "⚠️"
            lines.append(f"   {supported} {runner}")
        lines.append("")
        return lines

    def _generate_actions_section(self) -> List[str]:
        """Generate the actions section of the report.

        Returns:
            List of actions section lines.
        """
        all_actions: Set[str] = set()
        for result in self.results:
            all_actions.update(result.referenced_actions)
        if not all_actions:
            return []

        lines = [
            "-" * 80,
            "📦 EXTERNAL ACTIONS REFERENCED",
            "-" * 80,
        ]
        for action in sorted(all_actions):
            if not action.startswith("./") and not action.startswith("$"):
                lines.append(f"   • {action}")
        lines.append("")
        return lines

    def _generate_report_footer(self) -> List[str]:
        """Generate the report footer.

        Returns:
            List of footer lines.
        """
        return [
            "=" * 80,
            "END OF VALIDATION REPORT",
            "=" * 80,
        ]


def main() -> int:
    """Main entry point for the workflow validator.

    Returns:
        Exit code (0 for success).
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    workflows_dir = "/workspaces/Zen-Ai-Pentest/.github/workflows"

    validator = WorkflowValidator(workflows_dir)
    validator.validate_all()

    report = validator.generate_report()
    print(report)

    # Save report to file
    report_path = "/workspaces/Zen-Ai-Pentest/workflow_validation_report.txt"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_path}")
    except IOError as e:
        logger.error("Failed to save report: %s", e)

    return 0


if __name__ == "__main__":
    exit(main())
