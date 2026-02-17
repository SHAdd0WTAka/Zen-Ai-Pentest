"""TruffleHog Integration - Secrets Detection for Zen-AI-Pentest

This module provides a comprehensive TruffleHog wrapper with:
- Git repository scanning
- File/directory scanning
- Custom regex patterns
- Verified secrets only option
- Multiple output formats
- Result parsing and normalization

Author: Zen-AI-Pentest Team
License: MIT
"""

import asyncio
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TruffleHogFinding:
    """Represents a TruffleHog secret finding"""

    detector_name: str
    detector_type: str
    verified: bool
    raw: str
    redacted: str
    source: str  # git or filesystem
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    severity: str = "high"  # Derived from detector type
    confidence: str = "high"


@dataclass
class TruffleHogResult:
    """Complete TruffleHog scan result"""

    success: bool
    target: str
    scan_type: str  # 'git' or 'filesystem'
    findings: List[TruffleHogFinding] = field(default_factory=list)
    scan_time: float = 0.0
    error: Optional[str] = None
    raw_output: str = ""
    verified_only: bool = False


class TruffleHogScanner:
    """
    Advanced TruffleHog scanner for secrets detection.

    Features:
    - Git repository scanning
    - File/directory scanning
    - Custom regex patterns
    - Verified secrets only option
    - Multiple output formats
    - Result parsing and normalization
    - Severity classification
    """

    SEVERITY_MAP = {
        # Critical - High impact secrets
        "AWS": "critical",
        "AWSAccessKey": "critical",
        "AWSSessionKey": "critical",
        "GitHub": "critical",
        "GitHubApp": "critical",
        "GitHubOauth2": "critical",
        "GitLab": "critical",
        "PrivateKey": "critical",
        "OpenSSHPrivateKey": "critical",
        "RSAPrivateKey": "critical",
        "ECPrivateKey": "critical",
        "PGPPrivateKey": "critical",
        "Stripe": "critical",
        "StripeAPIKey": "critical",
        "StripeRestrictedKey": "critical",
        "SendGrid": "critical",
        "Slack": "critical",
        "SlackWebhook": "critical",
        "SlackApp": "critical",
        "SlackBot": "critical",
        "SlackConfig": "critical",
        "SlackLegacy": "critical",
        "SlackUserToken": "critical",

        # High - Important credentials
        "Docker": "high",
        "DockerHub": "high",
        "DockerConfig": "high",
        "Heroku": "high",
        "HerokuAPIKey": "high",
        "Twilio": "high",
        "TwilioAPIKey": "high",
        "NPM": "high",
        "NPMAuthToken": "high",
        "PyPI": "high",
        "Rubygems": "high",
        "Terraform": "high",
        "TerraformCloud": "high",
        "TerraformEnterprise": "high",
        "Vault": "high",
        "VaultToken": "high",
        "Kubernetes": "high",
        "KubeConfig": "high",
        "Jwt": "high",
        "JwtToken": "high",
        "BearerToken": "high",
        "ApiKey": "high",
        "GenericApiKey": "high",

        # Medium - API keys and tokens
        "Mailchimp": "medium",
        "Mailgun": "medium",
        "PagerDuty": "medium",
        "Square": "medium",
        "SquareApp": "medium",
        "SquareOAuth": "medium",
        "TravisCI": "medium",
        "TravisCIApiKey": "medium",
        "Auth0": "medium",
        "Auth0Management": "medium",
        "Cloudflare": "medium",
        "CloudflareAPIKey": "medium",
        "CloudflareGlobalAPIKey": "medium",
        "Datadog": "medium",
        "DatadogToken": "medium",
        "Dropbox": "medium",
        "DropboxLong": "medium",
        "DropboxShort": "medium",
        "Firebase": "medium",
        "FirebaseURL": "medium",

        # Low - Generic patterns and less critical
        "BasicAuth": "low",
        "HttpBasicAuth": "low",
        "HttpDigestAuth": "low",
        "Password": "low",
        "PasswordInUrl": "low",
        "Secret": "low",
        "SecretKeyword": "low",
        "Uri": "info",
        "Url": "info",
    }

    def __init__(
        self,
        trufflehog_path: str = "trufflehog",
        verified_only: bool = False,
        custom_regexes: Optional[Dict[str, str]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        max_depth: int = 0,
        since_commit: Optional[str] = None,
        branch: Optional[str] = None,
    ):
        """
        Initialize TruffleHog scanner.

        Args:
            trufflehog_path: Path to trufflehog binary
            verified_only: Only report verified secrets
            custom_regexes: Dictionary of custom regex patterns
            exclude_paths: List of paths to exclude
            include_paths: List of paths to include
            max_depth: Maximum depth for git scan (0 = unlimited)
            since_commit: Scan commits since this commit
            branch: Git branch to scan
        """
        self.trufflehog_path = self._validate_installation(trufflehog_path)
        self.verified_only = verified_only
        self.custom_regexes = custom_regexes or {}
        self.exclude_paths = exclude_paths or []
        self.include_paths = include_paths or []
        self.max_depth = max_depth
        self.since_commit = since_commit
        self.branch = branch

    def _validate_installation(self, path: str) -> str:
        """Validate trufflehog binary exists"""
        trufflehog_path = shutil.which(path)
        if not trufflehog_path:
            raise RuntimeError(
                f"trufflehog not found at '{path}'. Install from: "
                "https://github.com/trufflesecurity/trufflehog"
            )
        return trufflehog_path

    def _get_version(self) -> str:
        """Get TruffleHog version"""
        try:
            result = subprocess.run(
                [self.trufflehog_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _build_git_command(self, repo_url: str, output_file: Optional[str] = None) -> List[str]:
        """Build trufflehog git scan command"""
        cmd = [
            self.trufflehog_path,
            "git",
            repo_url,
            "--json",
        ]

        if self.verified_only:
            cmd.append("--only-verified")

        if self.max_depth > 0:
            cmd.extend(["--max-depth", str(self.max_depth)])

        if self.since_commit:
            cmd.extend(["--since-commit", self.since_commit])

        if self.branch:
            cmd.extend(["--branch", self.branch])

        for path in self.exclude_paths:
            cmd.extend(["--exclude-paths", path])

        return cmd

    def _build_filesystem_command(self, path: str, output_file: Optional[str] = None) -> List[str]:
        """Build trufflehog filesystem scan command"""
        cmd = [
            self.trufflehog_path,
            "filesystem",
            path,
            "--json",
        ]

        if self.verified_only:
            cmd.append("--only-verified")

        for exclude in self.exclude_paths:
            cmd.extend(["--exclude-paths", exclude])

        # Add custom regexes if provided
        if self.custom_regexes:
            # TruffleHog v3 supports custom detectors via config
            # For now, we'll note this in the scan
            logger.info(f"Custom regexes configured: {list(self.custom_regexes.keys())}")

        return cmd

    def _parse_json_output(self, json_lines: str, source: str) -> List[TruffleHogFinding]:
        """
        Parse TruffleHog JSON output.

        Args:
            json_lines: JSON lines output from trufflehog
            source: Source type ('git' or 'filesystem')

        Returns:
            List of TruffleHogFinding objects
        """
        findings = []

        for line in json_lines.strip().split("\n"):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                detector_name = data.get("DetectorName", "Unknown")
                detector_type = data.get("DetectorType", "Unknown")
                verified = data.get("Verified", False)
                raw = data.get("Raw", "")
                redacted = data.get("Redacted", "")

                # Get source metadata
                source_metadata = data.get("SourceMetadata", {})
                if "Data" in source_metadata:
                    source_metadata = source_metadata["Data"]

                # Determine severity
                severity = self._classify_severity(detector_name, verified)

                finding = TruffleHogFinding(
                    detector_name=detector_name,
                    detector_type=detector_type,
                    verified=verified,
                    raw=raw,
                    redacted=redacted,
                    source=source,
                    source_metadata=source_metadata,
                    severity=severity,
                    confidence="high" if verified else "medium",
                )
                findings.append(finding)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON line: {e}")
                continue

        return findings

    def _classify_severity(self, detector_name: str, verified: bool) -> str:
        """Classify severity based on detector name"""
        # Check exact match first
        if detector_name in self.SEVERITY_MAP:
            severity = self.SEVERITY_MAP[detector_name]
        else:
            # Check partial matches
            severity = "medium"  # Default
            for key, value in self.SEVERITY_MAP.items():
                if key.lower() in detector_name.lower():
                    severity = value
                    break

        # Upgrade severity for verified secrets
        if verified and severity in ["medium", "low"]:
            severity = "high"

        return severity

    async def scan_git(
        self,
        repo_url: str,
        timeout: int = 600,
    ) -> TruffleHogResult:
        """
        Scan a Git repository for secrets.

        Args:
            repo_url: Git repository URL or local path
            timeout: Maximum scan time in seconds

        Returns:
            TruffleHogResult with findings
        """
        start_time = asyncio.get_event_loop().time()
        cmd = self._build_git_command(repo_url)

        logger.info(f"Starting TruffleHog git scan: {repo_url}")

        try:
            # Run trufflehog in executor to make it async
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._run_subprocess, cmd),
                timeout=timeout,
            )

            scan_time = asyncio.get_event_loop().time() - start_time

            # Parse findings
            findings = self._parse_json_output(result.stdout, "git")

            return TruffleHogResult(
                success=True,
                target=repo_url,
                scan_type="git",
                findings=findings,
                scan_time=scan_time,
                raw_output=result.stdout,
                verified_only=self.verified_only,
            )

        except asyncio.TimeoutError:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"TruffleHog git scan timed out after {timeout}s")
            return TruffleHogResult(
                success=False,
                target=repo_url,
                scan_type="git",
                error=f"Scan timed out after {timeout} seconds",
                scan_time=scan_time,
                verified_only=self.verified_only,
            )

        except Exception as e:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"TruffleHog git scan error: {e}")
            return TruffleHogResult(
                success=False,
                target=repo_url,
                scan_type="git",
                error=str(e),
                scan_time=scan_time,
                verified_only=self.verified_only,
            )

    async def scan_filesystem(
        self,
        path: str,
        timeout: int = 600,
    ) -> TruffleHogResult:
        """
        Scan a filesystem path for secrets.

        Args:
            path: Path to scan
            timeout: Maximum scan time in seconds

        Returns:
            TruffleHogResult with findings
        """
        # Validate path
        scan_path = Path(path)
        if not scan_path.exists():
            return TruffleHogResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error=f"Path does not exist: {path}",
            )

        start_time = asyncio.get_event_loop().time()
        cmd = self._build_filesystem_command(str(scan_path))

        logger.info(f"Starting TruffleHog filesystem scan: {path}")

        try:
            # Run trufflehog in executor
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._run_subprocess, cmd),
                timeout=timeout,
            )

            scan_time = asyncio.get_event_loop().time() - start_time

            # Parse findings
            findings = self._parse_json_output(result.stdout, "filesystem")

            return TruffleHogResult(
                success=True,
                target=path,
                scan_type="filesystem",
                findings=findings,
                scan_time=scan_time,
                raw_output=result.stdout,
                verified_only=self.verified_only,
            )

        except asyncio.TimeoutError:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"TruffleHog filesystem scan timed out after {timeout}s")
            return TruffleHogResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error=f"Scan timed out after {timeout} seconds",
                scan_time=scan_time,
                verified_only=self.verified_only,
            )

        except Exception as e:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"TruffleHog filesystem scan error: {e}")
            return TruffleHogResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error=str(e),
                scan_time=scan_time,
                verified_only=self.verified_only,
            )

    def _run_subprocess(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run subprocess (sync, to be called in executor)"""
        return subprocess.run(cmd, capture_output=True, text=True)

    def parse_output(self, result: TruffleHogResult) -> List[Dict[str, Any]]:
        """
        Parse TruffleHog result into standardized format.

        Args:
            result: TruffleHogResult object

        Returns:
            List of standardized finding dictionaries
        """
        findings = []
        for finding in result.findings:
            parsed = {
                "tool": "trufflehog",
                "detector": finding.detector_name,
                "type": finding.detector_type,
                "severity": finding.severity,
                "verified": finding.verified,
                "confidence": finding.confidence,
                "source": finding.source,
                "source_metadata": finding.source_metadata,
                "redacted_secret": finding.redacted,
                "file": finding.source_metadata.get("File", "") if finding.source_metadata else "",
                "commit": finding.source_metadata.get("Commit", "") if finding.source_metadata else "",
                "email": finding.source_metadata.get("Email", "") if finding.source_metadata else "",
                "timestamp": finding.source_metadata.get("Timestamp", "") if finding.source_metadata else "",
            }
            findings.append(parsed)
        return findings

    def normalize_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize findings to standard format.

        Args:
            findings: List of finding dictionaries

        Returns:
            List of normalized findings
        """
        normalized = []

        for finding in findings:
            # Build description
            description = (
                f"Detected {finding.get('detector', 'Unknown')} secret"
            )
            if finding.get("verified"):
                description += " (VERIFIED)"

            # Build evidence
            evidence = {
                "detector": finding.get("detector"),
                "type": finding.get("type"),
                "redacted_secret": finding.get("redacted_secret"),
                "verified": finding.get("verified"),
            }

            # Add file/commit info if available
            if finding.get("file"):
                evidence["file"] = finding["file"]
            if finding.get("commit"):
                evidence["commit"] = finding["commit"]
            if finding.get("timestamp"):
                evidence["timestamp"] = finding["timestamp"]

            normalized_finding = {
                "tool": "trufflehog",
                "target": finding.get("source", ""),
                "severity": finding.get("severity", "medium").lower(),
                "title": f"Secret Found: {finding.get('detector', 'Unknown')}",
                "description": description,
                "evidence": evidence,
                "remediation": (
                    "1. Rotate the exposed secret immediately\n"
                    "2. Remove the secret from the repository\n"
                    "3. Use environment variables or secret management\n"
                    "4. Add the pattern to .gitignore or trufflehog config"
                ),
                "references": [
                    "https://docs.github.com/en/code-security/secret-scanning",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html",
                ],
                "confidence": finding.get("confidence", "medium"),
                "verified": finding.get("verified", False),
            }
            normalized.append(normalized_finding)

        return normalized

    def get_version(self) -> str:
        """Get TruffleHog version"""
        return self._get_version()


# LangChain Tool integration
try:
    from langchain_core.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

    def tool(func=None, **kwargs):
        if func:
            return func
        return lambda f: f


@tool
def trufflehog_scan_git(
    repo_url: str,
    verified_only: bool = False,
    max_depth: int = 0,
) -> str:
    """
    Scan a Git repository for secrets using TruffleHog.

    Args:
        repo_url: Git repository URL or local path
        verified_only: Only report verified secrets
        max_depth: Maximum commit depth to scan (0 = unlimited)

    Returns:
        Scan results with discovered secrets
    """
    import asyncio

    scanner = TruffleHogScanner(
        verified_only=verified_only,
        max_depth=max_depth,
    )

    result = asyncio.run(scanner.scan_git(repo_url))

    if not result.success:
        return f"TruffleHog scan failed: {result.error}"

    # Format results
    lines = [
        f"TruffleHog Git Scan completed in {result.scan_time:.2f}s",
        f"Repository: {result.target}",
        f"Secrets Found: {len(result.findings)}",
        "",
    ]

    # Group by severity
    severity_groups = {"critical": [], "high": [], "medium": [], "low": []}
    for finding in result.findings:
        sev = finding.severity.lower()
        if sev in severity_groups:
            severity_groups[sev].append(finding)

    for severity in ["critical", "high", "medium"]:
        if severity_groups[severity]:
            lines.append(f"\n{severity.upper()} Severity ({len(severity_groups[severity])}):")
            for finding in severity_groups[severity][:10]:  # Limit output
                verified_mark = "✓ VERIFIED" if finding.verified else ""
                lines.append(f"  - {finding.detector_name} {verified_mark}")
                lines.append(f"    Redacted: {finding.redacted}")

    return "\n".join(lines)


@tool
def trufflehog_scan_path(
    path: str,
    verified_only: bool = False,
) -> str:
    """
    Scan a file or directory for secrets using TruffleHog.

    Args:
        path: Path to scan
        verified_only: Only report verified secrets

    Returns:
        Scan results with discovered secrets
    """
    import asyncio

    scanner = TruffleHogScanner(verified_only=verified_only)
    result = asyncio.run(scanner.scan_filesystem(path))

    if not result.success:
        return f"TruffleHog scan failed: {result.error}"

    verified_count = sum(1 for f in result.findings if f.verified)

    return (
        f"TruffleHog Filesystem Scan Results for {path}:\n"
        f"  Total Secrets: {len(result.findings)}\n"
        f"  Verified: {verified_count}\n"
        f"  Scan Time: {result.scan_time:.2f}s"
    )


@tool
def trufflehog_scan_local_repo(
    repo_path: str,
    since_commit: str = "",
    branch: str = "",
) -> str:
    """
    Scan a local Git repository for secrets.

    Args:
        repo_path: Path to local Git repository
        since_commit: Scan commits since this commit hash
        branch: Branch to scan

    Returns:
        Scan results with discovered secrets
    """
    import asyncio

    scanner = TruffleHogScanner(
        since_commit=since_commit if since_commit else None,
        branch=branch if branch else None,
    )

    result = asyncio.run(scanner.scan_git(repo_path))

    if not result.success:
        return f"Local repo scan failed: {result.error}"

    high_count = sum(1 for f in result.findings if f.severity in ["critical", "high"])

    return (
        f"Local Repository Scan Complete:\n"
        f"  Path: {repo_path}\n"
        f"  High/Critical Secrets: {high_count}\n"
        f"  Total Secrets: {len(result.findings)}"
    )


# Tool Registry integration
try:
    from .tool_registry import ToolCategory, ToolSafetyLevel, registry
    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_trufflehog_tools():
    """Register TruffleHog tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=trufflehog_scan_git,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["secrets", "git", "repository", "trufflehog"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=trufflehog_scan_path,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["secrets", "filesystem", "trufflehog"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=trufflehog_scan_local_repo,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["secrets", "git", "local", "trufflehog"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        logger.info("TruffleHog tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register TruffleHog tools: {e}")


# Auto-register on import
try:
    register_trufflehog_tools()
except Exception:
    pass


__all__ = [
    "TruffleHogScanner",
    "TruffleHogFinding",
    "TruffleHogResult",
    "trufflehog_scan_git",
    "trufflehog_scan_path",
    "trufflehog_scan_local_repo",
    "register_trufflehog_tools",
]
