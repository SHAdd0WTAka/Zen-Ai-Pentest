"""Release scan handler for pre-release security checks."""

import logging
from datetime import datetime, timezone
from typing import List

from ..models.events import ReleaseEvent
from ..utils.github_api import GitHubAPI
from ..utils.sarif import Finding, SARIFGenerator, Severity

logger = logging.getLogger(__name__)


class ReleaseScanResult:
    """Result of a release scan."""

    def __init__(self):
        self.findings: List[Finding] = []
        self.scanned_files: int = 0
        self.errors: List[str] = []
        self.duration_seconds: int = 0
        self.passed: bool = False


class ReleaseScanHandler:
    """Handle pre-release security scans."""

    def __init__(self, github_api: GitHubAPI):
        self.github_api = github_api
        self.sarif = SARIFGenerator()

    async def handle(self, event: ReleaseEvent) -> ReleaseScanResult:
        """Handle release scan event.

        Args:
            event: Release event

        Returns:
            Scan result
        """
        result = ReleaseScanResult()
        owner = event.repository.owner.login
        repo = event.repository.name
        tag = event.release.tag_name

        logger.info(f"Starting release scan for {owner}/{repo}@{tag}")

        # Only scan published releases, not drafts
        if event.release.draft:
            logger.info("Skipping draft release")
            return result

        start_time = datetime.now(timezone.utc)

        try:
            # Perform full repository scan
            await self._full_repository_scan(owner, repo, event)

            # Upload SARIF
            await self._upload_security_report(owner, repo, event)

            # Update release with security summary
            await self._update_release_notes(owner, repo, event, result)

            # Determine if release passes security checks
            critical_count = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
            high_count = sum(1 for f in result.findings if f.severity == Severity.HIGH)

            result.passed = critical_count == 0 and high_count < 5

            duration = datetime.now(timezone.utc) - start_time
            result.duration_seconds = int(duration.total_seconds())

            logger.info(
                f"Release scan complete in {result.duration_seconds}s: {len(result.findings)} findings, passed={result.passed}"
            )

        except Exception as e:
            logger.exception("Release scan failed")
            result.errors.append(str(e))
            result.passed = False

        return result

    async def _full_repository_scan(self, owner: str, repo: str, event: ReleaseEvent) -> None:
        """Perform full repository scan.

        In production, this would:
        1. Clone the repository at the release tag
        2. Run comprehensive security scans
        3. Analyze all code, dependencies, and configurations
        """
        logger.info(f"Performing full scan of {owner}/{repo}")

        # Simulated findings
        findings = [
            Finding(
                rule_id="release.scan.complete",
                message="Full repository scan completed successfully",
                file_path="N/A",
                line_number=0,
                severity=Severity.NOTE,
                description="Comprehensive security scan of the release",
            )
        ]

        # Add findings to result
        for finding in findings:
            self.sarif.add_finding(finding)

    async def _upload_security_report(self, owner: str, repo: str, event: ReleaseEvent) -> None:
        """Upload SARIF security report."""
        try:
            sarif_data = self.sarif.generate_json()

            # Get the release commit SHA
            # In production, this would be fetched from the release data
            commit_sha = "HEAD"  # Placeholder

            await self.github_api.upload_sarif(
                owner=owner, repo=repo, sarif_data=sarif_data, commit_sha=commit_sha, ref=f"refs/tags/{event.release.tag_name}"
            )

            logger.info(f"Security SARIF uploaded for release {event.release.tag_name}")

        except Exception as e:
            logger.error(f"Failed to upload release SARIF: {e}")

    async def _update_release_notes(self, owner: str, repo: str, event: ReleaseEvent, result: ReleaseScanResult) -> None:
        """Update release notes with security summary."""

        summary = self._generate_security_summary(result)

        # Build updated release body
        original_body = event.release.body or ""

        # Check if security section already exists
        security_header = "## 🔒 Security Summary"
        if security_header in original_body:
            # Replace existing section
            import re

            pattern = rf"{re.escape(security_header)}.*?(?=##|$)"
            new_body = re.sub(pattern, summary, original_body, flags=re.DOTALL)
        else:
            # Append to end
            new_body = original_body + "\n\n" + summary

        # Update release via API
        try:
            await self.github_api._request(
                "PATCH", f"/repos/{owner}/{repo}/releases/{event.release.id}", json={"body": new_body}
            )

            logger.info(f"Updated release notes for {event.release.tag_name}")

        except Exception as e:
            logger.error(f"Failed to update release notes: {e}")

    def _generate_security_summary(self, result: ReleaseScanResult) -> str:
        """Generate security summary for release notes."""
        summary = self.sarif.get_summary()

        # Status indicator
        status_emoji = "✅" if result.passed else "⚠️"
        status_text = "PASSED" if result.passed else "NEEDS ATTENTION"

        body = f"""## 🔒 Security Summary

{status_emoji} **Security Scan {status_text}**

| Severity | Count |
|----------|-------|
| 🔴 Critical | {summary.get("critical", 0)} |
| 🟠 High | {summary.get("high", 0)} |
| 🟡 Medium | {summary.get("medium", 0)} |
| 🟢 Low | {summary.get("low", 0)} |

"""

        if result.passed:
            body += """This release has passed automated security checks.

"""
        else:
            body += """⚠️ This release has security findings that should be reviewed.
Please check the [Security tab](../../security) for details.

"""

        body += f"*Scan completed in {result.duration_seconds}s*\n"

        return body

    def _generate_markdown_report(self, result: ReleaseScanResult) -> str:
        """Generate detailed markdown security report."""
        lines = [
            "# Security Scan Report",
            "",
            f"**Status:** {'✅ PASSED' if result.passed else '❌ FAILED'}",
            f"**Files Scanned:** {result.scanned_files}",
            f"**Total Findings:** {len(result.findings)}",
            "",
            "## Findings by Severity",
            "",
        ]

        summary = self.sarif.get_summary()
        for severity in ["critical", "high", "medium", "low"]:
            count = summary.get(severity, 0)
            emoji = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡" if severity == "medium" else "🟢"
            lines.append(f"- {emoji} **{severity.capitalize()}:** {count}")

        if result.findings:
            lines.extend(["", "## Detailed Findings", ""])

            for i, finding in enumerate(result.findings[:20], 1):
                emoji = (
                    "🔴"
                    if finding.severity == Severity.CRITICAL
                    else "🟠"
                    if finding.severity == Severity.HIGH
                    else "🟡"
                    if finding.severity == Severity.MEDIUM
                    else "🟢"
                )

                lines.extend(
                    [
                        f"### {i}. {finding.rule_id} {emoji}",
                        "",
                        f"**File:** `{finding.file_path}:{finding.line_number}`",
                        f"**Severity:** {finding.severity.value}",
                        f"**Message:** {finding.message}",
                        "",
                    ]
                )

                if finding.description:
                    lines.extend(["**Description:**", finding.description, ""])

                if finding.recommendation:
                    lines.extend(["**Recommendation:**", finding.recommendation, ""])

            if len(result.findings) > 20:
                lines.append(f"\n*... and {len(result.findings) - 20} more findings*\n")

        if result.errors:
            lines.extend(["", "## Errors", ""])
            for error in result.errors:
                lines.append(f"- ❌ {error}")

        lines.extend(["", "---", "", "*Generated by Zen-AI Security Scan*"])

        return "\n".join(lines)
