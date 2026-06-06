"""
PR Security Analysis für Zen-AI-Pentest.

Dieses Modul implementiert die tiefe Sicherheitsanalyse von PR-Änderungen
mit Fokus auf Secrets, verwundbare Code-Patterns und Dependency-Änderungen.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """
    Ein Security Finding aus der PR-Analyse.
    """

    file: str
    line: int
    severity: str  # critical, high, medium, low, info
    message: str
    remediation: str
    tool: str
    rule_id: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiere zu Dictionary."""
        return {
            "path": self.file,
            "line": self.line,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
            "tool": self.tool,
            "rule_id": self.rule_id,
            "code_snippet": self.code_snippet,
        }


class PRSecurityAnalyzer:
    """
    Security Analyzer für Pull Requests.

    Analysiert geänderte Dateien in PRs auf:
    - Hardcodierte Secrets
    - Verwundbare Code-Patterns
    - Unsichere Dependency-Änderungen
    - Sicherheitsrelevante Konfigurationsänderungen
    """

    # Patterns für Secret Detection
    SECRET_PATTERNS = {
        "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "aws_secret_key": re.compile(r"['\"][0-9a-zA-Z/+]{40}['\"]"),
        "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
        "slack_token": re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"),
        "generic_api_key": re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][a-z0-9]{16,}['\"]"),
        "private_key": re.compile(r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "password_in_code": re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        "database_url": re.compile(r"(?i)(postgres|mysql|mongodb)://[^:]+:[^@]+@"),
    }

    # Patterns für verwundbare Code-Patterns
    VULNERABLE_PATTERNS = {
        "python": {
            "eval_usage": re.compile(r"\beval\s*\("),
            "exec_usage": re.compile(r"\bexec\s*\("),
            "sql_string_format": re.compile(r"(?i)(execute|cursor\.execute).*%s"),
            "pickle_load": re.compile(r"pickle\.loads?\s*\("),
            "yaml_load": re.compile(r"yaml\.load\s*\([^,)]*\)"),
            "subprocess_shell": re.compile(r"subprocess\.\w+.*shell\s*=\s*True"),
            "hardcoded_ip": re.compile(
                r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
            ),
        },
        "javascript": {
            "eval_usage": re.compile(r"\beval\s*\("),
            "inner_html": re.compile(r"\.innerHTML\s*="),
            "document_write": re.compile(r"document\.write\s*\("),
            "set_timeout_string": re.compile(r"setTimeout\s*\(['\"]"),
            "set_interval_string": re.compile(r"setInterval\s*\(['\"]"),
        },
        "generic": {
            "todo_security": re.compile(r"(?i)#?\s*TODO.*(?:security|fix|hack|bypass)"),
            "disable_verify": re.compile(r"verify\s*=\s*False"),
            "insecure_http": re.compile(r"http://[^/\s]+"),
        },
    }

    # Kritische Dependencies
    CRITICAL_DEPENDENCIES = {
        "python": ["requests", "urllib3", "cryptography", "django", "flask", "fastapi"],
        "javascript": ["lodash", "jquery", "axios", "express", "next", "react"],
    }

    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"

    async def analyze_pr(self, pr_number: int) -> list[SecurityFinding]:
        """
        Deep security analysis of PR changes.

        Args:
            pr_number: Pull Request Nummer

        Returns:
            Liste von SecurityFindings
        """
        logger.info(f"Analyzing PR #{pr_number} for security issues")

        findings = []

        try:
            # Hole geänderte Dateien
            changed_files = await self._get_changed_files(pr_number)
            logger.info(f"Found {len(changed_files)} changed files in PR #{pr_number}")

            for file in changed_files:
                filename = file.get("filename", "")
                patch = file.get("patch", "")
                status = file.get("status", "")

                if status == "removed":
                    continue

                # Prüfe auf Secrets im Diff
                secrets = await self._check_secrets_in_diff(filename, patch)
                findings.extend(secrets)

                # Prüfe auf verwundbare Patterns
                vulns = await self._check_vulnerable_patterns(filename, patch)
                findings.extend(vulns)

                # Prüfe auf Dependency-Änderungen
                if self._is_dependency_file(filename):
                    deps = await self._check_dependency_changes(filename, patch)
                    findings.extend(deps)

                # Prüfe auf Konfigurationsänderungen
                if self._is_config_file(filename):
                    config_issues = await self._check_config_security(filename, patch)
                    findings.extend(config_issues)

            logger.info(f"PR #{pr_number} analysis complete: {len(findings)} findings")

        except Exception as e:
            logger.exception(f"Error analyzing PR #{pr_number}: {e}")

        return findings

    async def post_pr_review(self, pr_number: int, findings: list[SecurityFinding], event: str = "COMMENT") -> dict[str, Any]:
        """
        Post findings as PR review comments.

        Args:
            pr_number: Pull Request Nummer
            findings: Liste von SecurityFindings
            event: Review Event (COMMENT, REQUEST_CHANGES, APPROVE)

        Returns:
            API Response
        """
        if not findings:
            logger.info(f"No findings to post for PR #{pr_number}")
            return {"status": "no_findings"}

        # Gruppiere Findings nach Datei
        comments = []
        for finding in findings:
            comment = {
                "path": finding.file,
                "line": finding.line,
                "body": (
                    f"**[{finding.severity.upper()}]** {finding.message}\n\n"
                    f"**Tool:** {finding.tool}\n\n"
                    f"**Remediation:**\n{finding.remediation}"
                ),
                "side": "RIGHT",
            }
            comments.append(comment)

        # Hole PR Info für Commit SHA
        pr_url = f"{self.base_url}/pulls/{pr_number}"

        async with httpx.AsyncClient() as client:
            pr_response = await client.get(pr_url, headers=self.headers)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            head_sha = pr_data["head"]["sha"]

        # Erstelle Review
        review_url = f"{self.base_url}/pulls/{pr_number}/reviews"

        review_data = {
            "commit_id": head_sha,
            "body": self._generate_review_summary(findings),
            "event": event,
            "comments": comments[:50],  # Max 50 comments
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(review_url, headers=self.headers, json=review_data)
            response.raise_for_status()

        logger.info(f"Posted review for PR #{pr_number} with {len(comments)} comments")
        return response.json()

    async def create_or_update_comment(self, pr_number: int, findings: list[SecurityFinding]) -> dict[str, Any]:
        """
        Erstelle oder aktualisiere einen Summary Comment.

        Args:
            pr_number: Pull Request Nummer
            findings: Liste von SecurityFindings

        Returns:
            API Response
        """
        # Suche nach bestehendem Comment
        existing_id = await self._find_existing_comment(pr_number)

        body = self._generate_comment_body(findings)

        if existing_id:
            # Update bestehenden Comment
            url = f"{self.base_url}/issues/comments/{existing_id}"
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json={"body": body})
        else:
            # Erstelle neuen Comment
            url = f"{self.base_url}/issues/{pr_number}/comments"
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json={"body": body})

        response.raise_for_status()
        return response.json()

    async def _get_changed_files(self, pr_number: int) -> list[dict]:
        """Hole geänderte Dateien eines PR."""
        url = f"{self.base_url}/pulls/{pr_number}/files"

        files = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(url, headers=self.headers, params={"per_page": 100, "page": page})
                response.raise_for_status()
                page_files = response.json()

                if not page_files:
                    break

                files.extend(page_files)

                if len(page_files) < 100:
                    break

                page += 1

        return files

    async def _check_secrets_in_diff(self, filename: str, patch: str) -> list[SecurityFinding]:
        """Prüfe auf Secrets im Diff."""
        findings = []

        lines = patch.split("\n")
        line_number = 0

        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                # Neue Zeile im Diff
                line_number += 1
                content = line[1:]  # Entferne '+'

                for secret_type, pattern in self.SECRET_PATTERNS.items():
                    if pattern.search(content):
                        finding = SecurityFinding(
                            file=filename,
                            line=line_number,
                            severity="critical",
                            message=f"Potential {secret_type.replace('_', ' ').title()} detected",
                            remediation=(
                                "Remove hardcoded secrets from code. "
                                "Use environment variables or a secure secret management system. "
                                "If this is a real secret, rotate it immediately."
                            ),
                            tool="SecretScanner",
                            rule_id=secret_type,
                            code_snippet=content[:100],
                        )
                        findings.append(finding)
                        logger.warning(f"Secret detected in {filename}:{line_number}")
            elif line.startswith(" "):
                line_number += 1
            elif line.startswith("-"):
                # Alte Zeile, nicht zählen
                pass

        return findings

    async def _check_vulnerable_patterns(self, filename: str, patch: str) -> list[SecurityFinding]:
        """Prüfe auf verwundbare Code-Patterns."""
        findings = []

        # Bestimme Sprache
        language = self._detect_language(filename)
        patterns = self.VULNERABLE_PATTERNS.get(language, {})
        patterns.update(self.VULNERABLE_PATTERNS["generic"])

        lines = patch.split("\n")
        line_number = 0

        severity_map = {
            "eval_usage": "high",
            "exec_usage": "high",
            "sql_string_format": "critical",
            "pickle_load": "high",
            "yaml_load": "medium",
            "subprocess_shell": "high",
            "inner_html": "high",
            "document_write": "medium",
            "disable_verify": "medium",
            "insecure_http": "low",
            "hardcoded_ip": "low",
            "todo_security": "info",
        }

        remediation_map = {
            "eval_usage": "Avoid using eval(). Use ast.literal_eval() for safe evaluation or refactor to avoid dynamic code execution.",
            "exec_usage": "Avoid using exec(). Consider safer alternatives like importlib or configuration files.",
            "sql_string_format": "Use parameterized queries or ORM methods to prevent SQL injection.",
            "pickle_load": "Avoid unpickling untrusted data. Use JSON or safer serialization formats.",
            "yaml_load": "Use yaml.safe_load() instead of yaml.load() to prevent code execution.",
            "subprocess_shell": "Avoid shell=True. Pass command as list and use shell=False.",
            "inner_html": "Use textContent or createTextNode to prevent XSS attacks.",
            "document_write": "Avoid document.write() as it can lead to XSS. Use safer DOM manipulation methods.",
            "disable_verify": "Never disable SSL verification in production. Use proper certificates.",
            "insecure_http": "Use HTTPS instead of HTTP for secure communication.",
            "todo_security": "Address this TODO before merging.",
        }

        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                line_number += 1
                content = line[1:]

                for pattern_name, pattern in patterns.items():
                    if pattern.search(content):
                        finding = SecurityFinding(
                            file=filename,
                            line=line_number,
                            severity=severity_map.get(pattern_name, "medium"),
                            message=f"Vulnerable pattern: {pattern_name.replace('_', ' ').title()}",
                            remediation=remediation_map.get(pattern_name, "Review and fix this security issue."),
                            tool="VulnPatternScanner",
                            rule_id=pattern_name,
                            code_snippet=content[:100],
                        )
                        findings.append(finding)
            elif line.startswith(" "):
                line_number += 1

        return findings

    async def _check_dependency_changes(self, filename: str, patch: str) -> list[SecurityFinding]:
        """Prüfe Dependency-Änderungen auf Sicherheitsrisiken."""
        findings = []

        # Parse Requirements oder Package.json
        added_deps = self._parse_added_dependencies(filename, patch)

        for dep in added_deps:
            if self._is_critical_dependency(filename, dep["name"]):
                finding = SecurityFinding(
                    file=filename,
                    line=dep.get("line", 1),
                    severity="medium",
                    message=f"Critical dependency updated: {dep['name']}",
                    remediation=(
                        f"Verify that {dep['name']} version {dep.get('version', 'unknown')} "
                        f"does not introduce known vulnerabilities. "
                        f"Run 'pip-audit' or 'npm audit' to check."
                    ),
                    tool="DependencyScanner",
                    rule_id="critical_dep_update",
                )
                findings.append(finding)

        return findings

    async def _check_config_security(self, filename: str, patch: str) -> list[SecurityFinding]:
        """Prüfe Konfigurationsänderungen."""
        findings = []

        lines = patch.split("\n")
        line_number = 0

        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                line_number += 1
                content = line[1:].lower()

                # Prüfe auf unsichere Konfigurationen
                if "debug=true" in content or "debug: true" in content:
                    finding = SecurityFinding(
                        file=filename,
                        line=line_number,
                        severity="medium",
                        message="Debug mode enabled",
                        remediation="Ensure debug mode is disabled in production.",
                        tool="ConfigScanner",
                        rule_id="debug_enabled",
                    )
                    findings.append(finding)

                if "allow_origin: *" in content or "access-control-allow-origin: *" in content:
                    finding = SecurityFinding(
                        file=filename,
                        line=line_number,
                        severity="medium",
                        message="Wildcard CORS policy detected",
                        remediation="Specify explicit allowed origins instead of using wildcard.",
                        tool="ConfigScanner",
                        rule_id="wildcard_cors",
                    )
                    findings.append(finding)
            elif line.startswith(" "):
                line_number += 1

        return findings

    def _detect_language(self, filename: str) -> str:
        """Erkenne Programmiersprache anhand der Dateiendung."""
        if filename.endswith(".py"):
            return "python"
        elif filename.endswith((".js", "jsx", ".ts", ".tsx")):
            return "javascript"
        return "generic"

    def _is_dependency_file(self, filename: str) -> bool:
        """Prüfe ob Datei eine Dependency-Datei ist."""
        return filename in [
            "requirements.txt",
            "requirements-dev.txt",
            "package.json",
            "package-lock.json",
            "Pipfile",
            "poetry.lock",
            "Cargo.toml",
            "Cargo.lock",
            "Gemfile",
            "Gemfile.lock",
        ]

    def _is_config_file(self, filename: str) -> bool:
        """Prüfe ob Datei eine Konfigurationsdatei ist."""
        return any(
            filename.endswith(ext) for ext in [".yml", ".yaml", ".json", ".toml", ".ini", ".conf", ".config"]
        ) or filename in [".env.example", ".env.template"]

    def _is_critical_dependency(self, filename: str, dep_name: str) -> bool:
        """Prüfe ob Dependency kritisch ist."""
        if "requirements" in filename:
            language = "python"
        elif "package" in filename:
            language = "javascript"
        else:
            return False

        critical = self.CRITICAL_DEPENDENCIES.get(language, [])
        return any(crit in dep_name.lower() for crit in critical)

    def _parse_added_dependencies(self, filename: str, patch: str) -> list[dict]:
        """Parse hinzugefügte Dependencies aus Patch."""
        deps = []
        lines = patch.split("\n")
        line_number = 0

        for line in lines:
            if line.startswith("+") and not line.startswith("+++"):
                line_number += 1
                content = line[1:].strip()

                if "requirements" in filename:
                    # Python requirements.txt
                    if content and not content.startswith("#"):
                        dep_name = content.split("==")[0].split(">=")[0].strip()
                        version = content.split("==")[1] if "==" in content else ""
                        deps.append({"name": dep_name, "version": version, "line": line_number})

                elif "package.json" in filename:
                    # npm package.json
                    if '"' in content and (":" in content):
                        parts = content.split(":")
                        if len(parts) >= 2:
                            dep_name = parts[0].strip().strip('",')
                            version = parts[1].strip().strip('",')
                            deps.append({"name": dep_name, "version": version, "line": line_number})

        return deps

    async def _find_existing_comment(self, pr_number: int) -> Optional[int]:
        """Suche nach bestehendem Zen Comment."""
        url = f"{self.base_url}/issues/{pr_number}/comments"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            comments = response.json()

        for comment in comments:
            if "<!-- zen-ai-pentest -->" in comment.get("body", ""):
                return comment["id"]

        return None

    def _generate_comment_body(self, findings: list[SecurityFinding]) -> str:
        """Generiere Markdown Body für PR Comment."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for finding in findings:
            severity = finding.severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        total = sum(severity_counts.values())

        if severity_counts["critical"] > 0:
            status_badge = "🔴 **Action Required**"
        elif severity_counts["high"] > 0:
            status_badge = "🟠 **Review Recommended**"
        elif total > 0:
            status_badge = "🟡 **Informational**"
        else:
            status_badge = "🟢 **All Clear**"

        lines = [
            "<!-- zen-ai-pentest -->",
            "## 🔒 Zen AI Pentest Security Scan",
            "",
            f"{status_badge}",
            "",
            "### Summary",
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

        if findings:
            lines.extend(
                [
                    "### Top Findings",
                    "",
                ]
            )

            for finding in findings[:10]:
                severity = finding.severity.upper()
                lines.append(f"**[{severity}]** {finding.message}")
                lines.append(f"> {finding.remediation[:150]}...")
                lines.append(f"📁 `{finding.file}:{finding.line}`")
                lines.append("")

        lines.extend(
            [
                "---",
                "*Powered by [Zen-AI-Pentest](https://github.com/SHAdd0WTAka/zen-ai-pentest)*",
            ]
        )

        return "\n".join(lines)

    def _generate_review_summary(self, findings: list[SecurityFinding]) -> str:
        """Generiere Summary für PR Review."""
        critical = sum(1 for f in findings if f.severity == "critical")
        high = sum(1 for f in findings if f.severity == "high")

        if critical > 0:
            return f"🚨 {critical} Critical security issues found. Please address before merging."
        elif high > 0:
            return f"⚠️ {high} High severity issues found. Please review."
        else:
            return f"🔒 Security scan found {len(findings)} issue(s). Please review the comments."
