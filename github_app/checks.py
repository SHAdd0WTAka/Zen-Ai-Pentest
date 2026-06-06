"""
GitHub Check Runs Management für Zen-AI-Pentest.

Dieses Modul verwaltet die Erstellung und Aktualisierung von GitHub Check Runs
für Security Scan Ergebnisse.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import httpx


class CheckRunStatus(str, Enum):
    """Status eines Check Runs."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    PENDING = "pending"
    ACTION_REQUIRED = "action_required"


class CheckRunConclusion(str, Enum):
    """Abschluss-Ergebnis eines Check Runs."""

    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    SKIPPED = "skipped"


class AnnotationLevel(str, Enum):
    """Level für Code-Annotations."""

    NOTICE = "notice"
    WARNING = "warning"
    FAILURE = "failure"


@dataclass
class CheckAnnotation:
    """Code-Annotation für einen Check Run."""

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
    """Output für einen Check Run."""

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
            result["annotations"] = [a.to_dict() for a in self.annotations]
        if self.images:
            result["images"] = self.images
        return result


@dataclass
class CheckRun:
    """Repräsentiert einen GitHub Check Run."""

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


class CheckRunManager:
    """Manager für GitHub Check Runs."""

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

    async def create_check_run(self, check_run: CheckRun) -> CheckRun:
        """Erstelle einen neuen Check Run."""
        url = f"{self.base_url}/check-runs"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=check_run.to_create_dict())
            response.raise_for_status()
            data = response.json()

        check_run.id = data["id"]
        return check_run

    async def update_check_run(self, check_run: CheckRun) -> CheckRun:
        """Aktualisiere einen bestehenden Check Run."""
        if not check_run.id:
            raise ValueError("Check Run ID ist erforderlich für Update")

        url = f"{self.base_url}/check-runs/{check_run.id}"

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=self.headers, json=check_run.to_update_dict())
            response.raise_for_status()

        return check_run

    async def get_check_run(self, check_run_id: int) -> CheckRun:
        """Hole einen Check Run per ID."""
        url = f"{self.base_url}/check-runs/{check_run_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

        return CheckRun(
            id=data["id"],
            name=data["name"],
            head_sha=data["head_sha"],
            status=CheckRunStatus(data["status"]),
            conclusion=CheckRunConclusion(data["conclusion"]) if data.get("conclusion") else None,
            details_url=data.get("details_url"),
            external_id=data.get("external_id"),
        )

    def create_findings_annotations(self, findings: list[dict], max_annotations: int = 50) -> list[CheckAnnotation]:
        """Erstelle Annotations aus Security Findings."""
        annotations = []

        severity_to_level = {
            "critical": AnnotationLevel.FAILURE,
            "high": AnnotationLevel.FAILURE,
            "medium": AnnotationLevel.WARNING,
            "low": AnnotationLevel.NOTICE,
            "info": AnnotationLevel.NOTICE,
        }

        for finding in findings[:max_annotations]:
            severity = finding.get("severity", "info").lower()
            level = severity_to_level.get(severity, AnnotationLevel.NOTICE)

            # Extrahiere Dateipfad und Zeile aus dem Finding
            location = finding.get("location", {})
            path = location.get("path", "")
            start_line = location.get("start_line", 1)
            end_line = location.get("end_line", start_line)

            # Wenn kein Pfad, versuche aus URL zu extrahieren
            if not path:
                url = finding.get("url", "")
                # Einfache Extraktion - in Produktion könnte man Repository-Mapping nutzen
                path = self._extract_path_from_url(url) or "unknown"

            annotation = CheckAnnotation(
                path=path,
                start_line=start_line,
                end_line=end_line,
                annotation_level=level,
                message=f"[{severity.upper()}] {finding.get('description', finding.get('name', 'Unbekanntes Finding'))}",
                title=finding.get("name", "Security Finding"),
                raw_details=json.dumps(finding, indent=2),
            )
            annotations.append(annotation)

        return annotations

    def _extract_path_from_url(self, url: str) -> Optional[str]:
        """Versuche einen Dateipfad aus einer URL zu extrahieren."""
        # Einfache Heuristik - kann erweitert werden
        import urllib.parse

        try:
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.lstrip("/")
            # Entferne Query-Parameter und Fragment
            if "." in path.split("/")[-1]:
                return path
        except Exception:
            pass
        return None

    def create_scan_summary(self, scan_results: list[dict], scan_config: dict) -> CheckRunOutput:
        """Erstelle einen Summary Report für den Check Run."""

        # Zähle Findings nach Severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        all_findings = []

        for result in scan_results:
            findings = result.get("findings", [])
            all_findings.extend(findings)
            for finding in findings:
                severity = finding.get("severity", "info").lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1

        total = sum(severity_counts.values())

        # Erstelle Markdown Summary
        summary_parts = [
            "## 🔒 Zen AI Pentest Security Scan Results",
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
        ]

        # Erstelle detaillierten Text
        text_parts = [
            "# Detailed Security Scan Report",
            "",
            "**Scan Configuration:**",
            f"```yaml\n{json.dumps(scan_config, indent=2)}\n```",
            "",
            "## Findings Details",
            "",
        ]

        for finding in all_findings[:100]:  # Limit für GitHub API
            severity = finding.get("severity", "info").upper()
            name = finding.get("name", "Unknown")
            description = finding.get("description", "No description available")

            text_parts.append(f"### [{severity}] {name}")
            text_parts.append(f"{description}")
            text_parts.append("")

            if "remediation" in finding:
                text_parts.append(f"**Remediation:** {finding['remediation']}")
                text_parts.append("")

            if "reference" in finding:
                text_parts.append(f"**Reference:** {finding['reference']}")
                text_parts.append("")

        # Erstelle Annotations (max 50)
        annotations = self.create_findings_annotations(all_findings)

        # Bestimme Titel basierend auf Severity
        if severity_counts["critical"] > 0:
            title = f"🚨 {severity_counts['critical']} Critical Vulnerabilities Found"
        elif severity_counts["high"] > 0:
            title = f"⚠️ {severity_counts['high']} High Severity Issues Found"
        elif total > 0:
            title = f"ℹ️ {total} Security Findings Detected"
        else:
            title = "✅ No Security Issues Found"

        return CheckRunOutput(
            title=title,
            summary="\n".join(summary_parts),
            text="\n".join(text_parts) if all_findings else None,
            annotations=annotations,
        )

    def determine_conclusion(self, scan_results: list[dict], fail_on: str = "high") -> CheckRunConclusion:
        """Bestimme den Check Run Conclusion basierend auf Findings."""

        severity_order = ["none", "low", "medium", "high", "critical"]
        fail_threshold = severity_order.index(fail_on.lower())

        for result in scan_results:
            for finding in result.get("findings", []):
                severity = finding.get("severity", "info").lower()
                if severity in severity_order:
                    if severity_order.index(severity) >= fail_threshold:
                        return CheckRunConclusion.ACTION_REQUIRED

        return CheckRunConclusion.SUCCESS
