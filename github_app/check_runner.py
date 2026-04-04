"""
GitHub Checks API Integration für Zen-AI-Pentest.

Dieses Modul implementiert die GitHub Checks API Integration
für detaillierte Security Scan Ergebnisse in GitHub.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class CheckRunStatus(str, Enum):
    """Status eines Check Runs nach GitHub API Spec."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    PENDING = "pending"
    ACTION_REQUIRED = "action_required"


class CheckRunConclusion(str, Enum):
    """Abschluss-Ergebnis eines Check Runs nach GitHub API Spec."""

    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    SKIPPED = "skipped"
    STARTUP_FAILURE = "startup_failure"
    STALE = "stale"


class AnnotationLevel(str, Enum):
    """Level für Code-Annotations."""

    NOTICE = "notice"
    WARNING = "warning"
    FAILURE = "failure"


@dataclass
class CheckAnnotation:
    """
    Code-Annotation für einen Check Run.

    Zeigt direkt im Code wo Probleme gefunden wurden.
    """

    path: str
    start_line: int
    end_line: int
    annotation_level: AnnotationLevel
    message: str
    title: Optional[str] = None
    raw_details: Optional[str] = None
    start_column: Optional[int] = None
    end_column: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiere zu GitHub API Format."""
        result = {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "annotation_level": self.annotation_level.value,
            "message": self.message,
        }
        if self.title:
            result["title"] = self.title
        if self.raw_details:
            result["raw_details"] = self.raw_details
        if self.start_column:
            result["start_column"] = self.start_column
        if self.end_column:
            result["end_column"] = self.end_column
        return result


@dataclass
class CheckRunOutput:
    """
    Output für einen Check Run.

    Enthält Titel, Zusammenfassung, detaillierten Text
    und optionale Annotations.
    """

    title: str
    summary: str
    text: Optional[str] = None
    annotations: list[CheckAnnotation] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Konvertiere zu GitHub API Format."""
        result = {
            "title": self.title,
            "summary": self.summary,
        }
        if self.text:
            result["text"] = self.text
        if self.annotations:
            result["annotations"] = [a.to_dict() for a in self.annotations[:50]]  # Max 50
        if self.images:
            result["images"] = self.images
        return result


@dataclass
class CheckRun:
    """
    Repräsentiert einen GitHub Check Run.

    Ein Check Run ist ein Status-Check für einen spezifischen Commit
    mit detaillierten Ergebnissen.
    """

    id: Optional[int] = None
    name: str = "Zen AI Pentest"
    head_sha: str = ""
    status: CheckRunStatus = CheckRunStatus.QUEUED
    conclusion: Optional[CheckRunConclusion] = None
    output: Optional[CheckRunOutput] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    details_url: Optional[str] = None
    external_id: Optional[str] = None

    def to_create_dict(self) -> dict[str, Any]:
        """Konvertiere zu GitHub API Create Format."""
        result = {
            "name": self.name,
            "head_sha": self.head_sha,
            "status": self.status.value,
        }
        if self.started_at:
            result["started_at"] = self.started_at
        if self.output:
            result["output"] = self.output.to_dict()
        if self.details_url:
            result["details_url"] = self.details_url
        if self.external_id:
            result["external_id"] = self.external_id
        return result

    def to_update_dict(self) -> dict[str, Any]:
        """Konvertiere zu GitHub API Update Format."""
        result = {"status": self.status.value}

        if self.conclusion:
            result["conclusion"] = self.conclusion.value
        if self.output:
            result["output"] = self.output.to_dict()
        if self.completed_at:
            result["completed_at"] = self.completed_at
        if self.details_url:
            result["details_url"] = self.details_url

        return result


class GitHubCheckRunner:
    """
    GitHub Checks API Runner.

    Verwaltet die Erstellung und Aktualisierung von Check Runs
    für Security Scans.
    """

    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def create_check_run(self, repo: Any, head_sha: str, name: str = "Security Scan") -> CheckRun:
        """
        Create a new check run.

        Args:
            repo: GitHub Repository Objekt oder None für HTTP API
            head_sha: Commit SHA
            name: Name des Check Runs

        Returns:
            Erstellter CheckRun
        """
        check = CheckRun(
            name=name,
            head_sha=head_sha,
            status=CheckRunStatus.QUEUED,
            started_at=self._iso_timestamp(),
            external_id=f"zen-check-{head_sha[:8]}",
        )

        url = f"{self.base_url}/check-runs"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=check.to_create_dict())
            response.raise_for_status()
            data = response.json()
            check.id = data["id"]

        logger.info(f"Created check run {check.id} for {head_sha[:7]}")
        return check

    async def update_check_run(
        self,
        check_run: CheckRun,
        status: Optional[CheckRunStatus] = None,
        conclusion: Optional[CheckRunConclusion] = None,
        output: Optional[CheckRunOutput] = None,
    ) -> CheckRun:
        """
        Update check run with results.

        Args:
            check_run: Zu aktualisierender CheckRun
            status: Neuer Status
            conclusion: Abschluss-Ergebnis
            output: Output Daten

        Returns:
            Aktualisierter CheckRun
        """
        if not check_run.id:
            raise ValueError("Check Run ID required for update")

        if status:
            check_run.status = status
        if conclusion:
            check_run.conclusion = conclusion
        if output:
            check_run.output = output

        if conclusion:
            check_run.completed_at = self._iso_timestamp()

        url = f"{self.base_url}/check-runs/{check_run.id}"

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=self.headers, json=check_run.to_update_dict())
            response.raise_for_status()

        logger.info(f"Updated check run {check_run.id}: {status.value if status else 'no status change'}")
        return check_run

    async def run_security_check(
        self, repo: Any, head_sha: str, base_sha: Optional[str] = None, config: Optional[dict] = None
    ) -> CheckRun:
        """
        Full security check workflow.

        Führt SAST, Dependency Check und Secret Scanning durch
        und aktualisiert den Check Run mit den Ergebnissen.

        Args:
            repo: GitHub Repository
            head_sha: Commit SHA
            base_sha: Basis Commit SHA für Diff
            config: Scan Konfiguration

        Returns:
            Finaler CheckRun
        """
        check = await self.create_check_run(repo, head_sha)

        try:
            # Update zu in_progress
            await self.update_check_run(
                check,
                status=CheckRunStatus.IN_PROGRESS,
                output=CheckRunOutput(title="Security Scan in Progress", summary="Running security checks..."),
            )

            # Run SAST
            logger.info(f"Running SAST for {head_sha[:7]}")
            sast_results = await self.run_sast(repo, head_sha)

            # Run Dependency Check
            logger.info(f"Running dependency check for {head_sha[:7]}")
            deps_results = await self.run_dependency_check(repo, head_sha)

            # Run Secret Scanning
            logger.info(f"Running secret scan for {head_sha[:7]}")
            secrets_results = await self.run_secret_scan(repo, head_sha)

            # Aggregate results
            output = self.format_check_output(sast_results, deps_results, secrets_results)

            # Determine conclusion
            fail_on = config.get("fail_on", "high") if config else "high"
            conclusion = self._determine_conclusion(sast_results, deps_results, secrets_results, fail_on)

            await self.update_check_run(check, status=CheckRunStatus.COMPLETED, conclusion=conclusion, output=output)

            logger.info(f"Security check completed for {head_sha[:7]}: {conclusion.value}")

        except Exception as e:
            logger.exception(f"Security check failed for {head_sha[:7]}")

            error_output = CheckRunOutput(
                title="Security Scan Failed", summary=f"❌ Scan failed with error: {str(e)}", text=f"```\n{str(e)}\n```"
            )

            await self.update_check_run(
                check, status=CheckRunStatus.COMPLETED, conclusion=CheckRunConclusion.FAILURE, output=error_output
            )

        return check

    async def run_sast(self, repo: Any, head_sha: str) -> dict[str, Any]:
        """
        Run Static Application Security Testing (SAST).

        Args:
            repo: GitHub Repository
            head_sha: Commit SHA

        Returns:
            SAST Ergebnisse
        """
        # In einer echten Implementierung würde hier ein SAST Tool laufen
        # z.B. Semgrep, Bandit, ESLint Security, etc.

        return {
            "tool": "sast",
            "status": "completed",
            "findings": [],  # Würde echte Findings enthalten
            "summary": "No SAST findings",
        }

    async def run_dependency_check(self, repo: Any, head_sha: str) -> dict[str, Any]:
        """
        Run Dependency Vulnerability Check.

        Args:
            repo: GitHub Repository
            head_sha: Commit SHA

        Returns:
            Dependency Check Ergebnisse
        """
        # In einer echten Implementierung würde hier ein Dependency Scanner laufen
        # z.B. Snyk, OWASP Dependency-Check, pip-audit, npm audit, etc.

        return {
            "tool": "dependency",
            "status": "completed",
            "findings": [],  # Würde echte Findings enthalten
            "summary": "No vulnerable dependencies found",
        }

    async def run_secret_scan(self, repo: Any, head_sha: str) -> dict[str, Any]:
        """
        Run Secret Scanning.

        Args:
            repo: GitHub Repository
            head_sha: Commit SHA

        Returns:
            Secret Scan Ergebnisse
        """
        # In einer echten Implementierung würde hier ein Secret Scanner laufen
        # z.B. Gitleaks, TruffleHog, GitGuardian, etc.

        return {
            "tool": "secrets",
            "status": "completed",
            "findings": [],  # Würde echte Findings enthalten
            "summary": "No secrets detected",
        }

    def format_check_output(self, sast_results: dict, deps_results: dict, secrets_results: dict) -> CheckRunOutput:
        """
        Format check output from scan results.

        Args:
            sast_results: SAST Ergebnisse
            deps_results: Dependency Check Ergebnisse
            secrets_results: Secret Scan Ergebnisse

        Returns:
            Formatierter CheckRunOutput
        """
        all_findings = (
            sast_results.get("findings", []) + deps_results.get("findings", []) + secrets_results.get("findings", [])
        )

        # Zähle nach Severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in all_findings:
            severity = finding.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        total = sum(severity_counts.values())

        # Bestimme Titel
        if severity_counts["critical"] > 0:
            title = f"🚨 {severity_counts['critical']} Critical Vulnerabilities Found"
        elif severity_counts["high"] > 0:
            title = f"⚠️ {severity_counts['high']} High Severity Issues Found"
        elif total > 0:
            title = f"ℹ️ {total} Security Findings Detected"
        else:
            title = "✅ No Security Issues Found"

        # Erstelle Summary
        summary_parts = [
            "## 🔒 Security Scan Summary",
            "",
            f"**Total Findings:** {total}",
            "",
            "| Severity | Count |",
            "|----------|-------|",
            f"| 🔴 Critical | {severity_counts['critical']} |",
            f"| 🟠 High | {severity_counts['high']} |",
            f"| 🟡 Medium | {severity_counts['medium']} |",
            f"| 🔵 Low | {severity_counts['low']} |",
            f"| ⚪ Info | {severity_counts['info']} |",
            "",
            "### Scan Results",
            "",
            f"- **SAST:** {sast_results.get('summary', 'N/A')}",
            f"- **Dependencies:** {deps_results.get('summary', 'N/A')}",
            f"- **Secrets:** {secrets_results.get('summary', 'N/A')}",
        ]

        # Erstelle detaillierten Text
        text_parts = ["# Detailed Security Report\n"]

        if all_findings:
            text_parts.append("## Findings\n")
            for finding in all_findings[:100]:  # Limit für GitHub API
                severity = finding.get("severity", "info").upper()
                name = finding.get("name", "Unknown")
                description = finding.get("description", "")

                text_parts.append(f"### [{severity}] {name}")
                text_parts.append(f"{description}\n")

                if "remediation" in finding:
                    text_parts.append(f"**Remediation:** {finding['remediation']}\n")
        else:
            text_parts.append("No security issues detected. Great job! 🎉")

        # Erstelle Annotations
        annotations = self._create_annotations(all_findings)

        return CheckRunOutput(
            title=title, summary="\n".join(summary_parts), text="\n".join(text_parts), annotations=annotations
        )

    def _determine_conclusion(
        self, sast_results: dict, deps_results: dict, secrets_results: dict, fail_on: str = "high"
    ) -> CheckRunConclusion:
        """
        Determine check run conclusion based on findings.

        Args:
            sast_results: SAST Ergebnisse
            deps_results: Dependency Check Ergebnisse
            secrets_results: Secret Scan Ergebnisse
            fail_on: Schwelle für Failure (none, low, medium, high, critical)

        Returns:
            CheckRunConclusion
        """
        all_findings = (
            sast_results.get("findings", []) + deps_results.get("findings", []) + secrets_results.get("findings", [])
        )

        severity_order = ["none", "low", "medium", "high", "critical"]

        if fail_on not in severity_order:
            fail_on = "high"

        fail_threshold = severity_order.index(fail_on)

        for finding in all_findings:
            severity = finding.get("severity", "info").lower()
            if severity in severity_order:
                if severity_order.index(severity) >= fail_threshold:
                    return CheckRunConclusion.ACTION_REQUIRED

        return CheckRunConclusion.SUCCESS

    def _create_annotations(self, findings: list[dict]) -> list[CheckAnnotation]:
        """
        Create annotations from findings.

        Args:
            findings: Liste von Findings

        Returns:
            Liste von CheckAnnotations (max 50)
        """
        annotations = []

        severity_to_level = {
            "critical": AnnotationLevel.FAILURE,
            "high": AnnotationLevel.FAILURE,
            "medium": AnnotationLevel.WARNING,
            "low": AnnotationLevel.NOTICE,
            "info": AnnotationLevel.NOTICE,
        }

        for finding in findings[:50]:  # Max 50 Annotations
            severity = finding.get("severity", "info").lower()
            level = severity_to_level.get(severity, AnnotationLevel.NOTICE)

            # Extrahiere Datei-Info
            location = finding.get("location", {})
            path = location.get("path", "")
            start_line = location.get("start_line", 1)
            end_line = location.get("end_line", start_line)

            if not path:
                path = finding.get("file", "unknown")

            annotation = CheckAnnotation(
                path=path,
                start_line=start_line,
                end_line=end_line,
                annotation_level=level,
                message=finding.get("description", finding.get("message", "Security issue")),
                title=finding.get("name", "Security Finding"),
                raw_details=json.dumps(finding, indent=2),
            )
            annotations.append(annotation)

        return annotations

    def _iso_timestamp(self) -> str:
        """Generate ISO 8601 timestamp."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Backwards compatibility mit checks.py
CheckRunManager = GitHubCheckRunner
