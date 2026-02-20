"""Trivy Integration - Container and Filesystem Vulnerability Scanner for Zen-AI-Pentest

This module provides a comprehensive Trivy wrapper with:
- Container image scanning
- Filesystem scanning
- SBOM generation
- CVE detection
- Misconfiguration detection
- JSON output parsing
- Severity filtering
- Cache integration

Author: Zen-AI-Pentest Team
License: MIT
"""

import asyncio
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TrivyScanTarget(Enum):
    """Trivy scan target types"""

    IMAGE = "image"
    FILESYSTEM = "filesystem"
    ROOTFS = "rootfs"
    REPOSITORY = "repository"
    VIRTUAL_MACHINE = "vm"
    SBOM = "sbom"


class TrivyScannerType(Enum):
    """Trivy scanner types"""

    VULNERABILITY = "vuln"
    MISCONFIGURATION = "config"
    SECRET = "secret"
    LICENSE = "license"


@dataclass
class TrivyVulnerability:
    """Represents a Trivy vulnerability finding"""

    vulnerability_id: str
    pkg_name: str
    installed_version: str
    fixed_version: str
    severity: str
    title: str
    description: str
    references: List[str] = field(default_factory=list)
    cvss_score: Optional[float] = None
    cvss_vector: str = ""
    primary_url: str = ""
    published_date: str = ""
    last_modified_date: str = ""


@dataclass
class TrivyMisconfiguration:
    """Represents a Trivy misconfiguration finding"""

    id: str
    type: str
    title: str
    description: str
    severity: str
    message: str
    resolution: str
    references: List[str] = field(default_factory=list)
    file_path: str = ""


@dataclass
class TrivySecret:
    """Represents a Trivy secret finding"""

    rule_id: str
    category: str
    severity: str
    title: str
    match: str
    file_path: str = ""
    start_line: int = 0
    end_line: int = 0


@dataclass
class TrivyResult:
    """Complete Trivy scan result"""

    success: bool
    target: str
    scan_type: str
    vulnerabilities: List[TrivyVulnerability] = field(default_factory=list)
    misconfigurations: List[TrivyMisconfiguration] = field(default_factory=list)
    secrets: List[TrivySecret] = field(default_factory=list)
    scan_time: float = 0.0
    error: Optional[str] = None
    os_info: Optional[Dict[str, Any]] = None
    artifact_name: str = ""
    artifact_type: str = ""


class TrivyScanner:
    """
    Advanced Trivy scanner for container and filesystem vulnerabilities.

    Features:
    - Container image scanning
    - Filesystem scanning
    - SBOM generation
    - CVE detection
    - Misconfiguration detection
    - JSON output parsing
    - Severity filtering
    - Cache integration
    """

    SEVERITY_ORDER = ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def __init__(
        self,
        trivy_path: str = "trivy",
        cache_dir: Optional[str] = None,
        severity: Optional[List[str]] = None,
        scanners: Optional[List[TrivyScannerType]] = None,
        skip_db_update: bool = False,
        offline_scan: bool = False,
        timeout: int = 3600,
    ):
        """
        Initialize Trivy scanner.

        Args:
            trivy_path: Path to trivy binary
            cache_dir: Cache directory for vulnerability DB
            severity: List of severities to include (UNKNOWN, LOW, MEDIUM, HIGH, CRITICAL)
            scanners: List of scanners to enable
            skip_db_update: Skip vulnerability database update
            offline_scan: Run in offline mode
            timeout: Scan timeout in seconds
        """
        self.trivy_path = self._validate_installation(trivy_path)
        self.cache_dir = cache_dir
        self.severity = severity or ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        self.scanners = scanners or [TrivyScannerType.VULNERABILITY]
        self.skip_db_update = skip_db_update
        self.offline_scan = offline_scan
        self.timeout = timeout

    def _validate_installation(self, path: str) -> str:
        """Validate trivy binary exists"""
        trivy_path = shutil.which(path)
        if not trivy_path:
            raise RuntimeError(f"trivy not found at '{path}'. Install from: https://aquasecurity.github.io/trivy/")
        return trivy_path

    def _get_version(self) -> str:
        """Get Trivy version"""
        try:
            result = subprocess.run(
                [self.trivy_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _build_command(
        self,
        target_type: TrivyScanTarget,
        target: str,
        output_format: str = "json",
        output_file: Optional[str] = None,
    ) -> List[str]:
        """Build trivy command"""
        cmd = [self.trivy_path, target_type.value]

        # Scanner types
        scanner_list = [s.value for s in self.scanners]
        cmd.extend(["--scanners", ",".join(scanner_list)])

        # Severity filter
        cmd.extend(["--severity", ",".join(self.severity)])

        # Output format
        cmd.extend(["--format", output_format])

        # Output file
        if output_file:
            cmd.extend(["--output", output_file])

        # Cache directory
        if self.cache_dir:
            cmd.extend(["--cache-dir", self.cache_dir])

        # Skip DB update
        if self.skip_db_update:
            cmd.append("--skip-db-update")

        # Offline mode
        if self.offline_scan:
            cmd.append("--offline-scan")

        # Timeout
        if self.timeout:
            cmd.extend(["--timeout", f"{self.timeout}s"])

        # Add target
        cmd.append(target)

        return cmd

    def _parse_vulnerabilities(self, results: List[Dict]) -> List[TrivyVulnerability]:
        """Parse vulnerability findings from Trivy output"""
        vulnerabilities = []

        for result in results:
            vuln_list = result.get("Vulnerabilities", [])

            for vuln_data in vuln_list:
                vuln = TrivyVulnerability(
                    vulnerability_id=vuln_data.get("VulnerabilityID", ""),
                    pkg_name=vuln_data.get("PkgName", ""),
                    installed_version=vuln_data.get("InstalledVersion", ""),
                    fixed_version=vuln_data.get("FixedVersion", ""),
                    severity=vuln_data.get("Severity", "UNKNOWN"),
                    title=vuln_data.get("Title", ""),
                    description=vuln_data.get("Description", ""),
                    references=vuln_data.get("References", []),
                    cvss_score=self._extract_cvss_score(vuln_data.get("CVSS", {})),
                    primary_url=vuln_data.get("PrimaryURL", ""),
                    published_date=vuln_data.get("PublishedDate", ""),
                    last_modified_date=vuln_data.get("LastModifiedDate", ""),
                )
                vulnerabilities.append(vuln)

        return vulnerabilities

    def _extract_cvss_score(self, cvss_data: Dict) -> Optional[float]:
        """Extract CVSS score from CVSS data"""
        if not cvss_data:
            return None

        # Try to get NVD score first
        nvd = cvss_data.get("nvd", {})
        if nvd:
            return nvd.get("V3Score") or nvd.get("V2Score")

        # Try vendor score
        for key, value in cvss_data.items():
            if isinstance(value, dict):
                score = value.get("V3Score") or value.get("V2Score")
                if score:
                    return score

        return None

    def _parse_misconfigurations(self, results: List[Dict]) -> List[TrivyMisconfiguration]:
        """Parse misconfiguration findings from Trivy output"""
        misconfigurations = []

        for result in results:
            misconf_list = result.get("Misconfigurations", [])

            for misconf_data in misconf_list:
                misconf = TrivyMisconfiguration(
                    id=misconf_data.get("ID", ""),
                    type=misconf_data.get("Type", ""),
                    title=misconf_data.get("Title", ""),
                    description=misconf_data.get("Description", ""),
                    severity=misconf_data.get("Severity", "UNKNOWN"),
                    message=misconf_data.get("Message", ""),
                    resolution=misconf_data.get("Resolution", ""),
                    references=misconf_data.get("References", []),
                )
                misconfigurations.append(misconf)

        return misconfigurations

    def _parse_secrets(self, results: List[Dict]) -> List[TrivySecret]:
        """Parse secret findings from Trivy output"""
        secrets = []

        for result in results:
            secret_list = result.get("Secrets", [])

            for secret_data in secret_list:
                secret = TrivySecret(
                    rule_id=secret_data.get("RuleID", ""),
                    category=secret_data.get("Category", ""),
                    severity=secret_data.get("Severity", "HIGH"),
                    title=secret_data.get("Title", ""),
                    match=secret_data.get("Match", ""),
                    file_path=result.get("Target", ""),
                )
                secrets.append(secret)

        return secrets

    async def scan_image(
        self,
        image: str,
        timeout: Optional[int] = None,
    ) -> TrivyResult:
        """
        Scan a container image.

        Args:
            image: Container image name (e.g., "nginx:latest")
            timeout: Scan timeout in seconds

        Returns:
            TrivyResult with scan results
        """
        return await self._scan(
            target_type=TrivyScanTarget.IMAGE,
            target=image,
            timeout=timeout,
        )

    async def scan_filesystem(
        self,
        path: str,
        timeout: Optional[int] = None,
    ) -> TrivyResult:
        """
        Scan a filesystem path.

        Args:
            path: Path to scan
            timeout: Scan timeout in seconds

        Returns:
            TrivyResult with scan results
        """
        # Validate path
        scan_path = Path(path)
        if not scan_path.exists():
            return TrivyResult(
                success=False,
                target=path,
                scan_type="filesystem",
                error=f"Path does not exist: {path}",
            )

        return await self._scan(
            target_type=TrivyScanTarget.FILESYSTEM,
            target=str(scan_path),
            timeout=timeout,
        )

    async def scan_repository(
        self,
        repo_url: str,
        timeout: Optional[int] = None,
    ) -> TrivyResult:
        """
        Scan a remote repository.

        Args:
            repo_url: Repository URL
            timeout: Scan timeout in seconds

        Returns:
            TrivyResult with scan results
        """
        return await self._scan(
            target_type=TrivyScanTarget.REPOSITORY,
            target=repo_url,
            timeout=timeout,
        )

    async def _scan(
        self,
        target_type: TrivyScanTarget,
        target: str,
        timeout: Optional[int] = None,
    ) -> TrivyResult:
        """
        Internal scan method.

        Args:
            target_type: Type of target to scan
            target: Target to scan
            timeout: Scan timeout

        Returns:
            TrivyResult with scan results
        """
        start_time = asyncio.get_event_loop().time()
        scan_timeout = timeout or self.timeout

        cmd = self._build_command(target_type, target)

        logger.info(f"Starting Trivy {target_type.value} scan: {target}")

        try:
            # Run trivy in executor
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._run_subprocess, cmd),
                timeout=scan_timeout,
            )

            scan_time = asyncio.get_event_loop().time() - start_time

            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                return TrivyResult(
                    success=False,
                    target=target,
                    scan_type=target_type.value,
                    error=f"Trivy failed: {error_msg}",
                    scan_time=scan_time,
                )

            # Parse JSON output
            try:
                output_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return TrivyResult(
                    success=False,
                    target=target,
                    scan_type=target_type.value,
                    error=f"Failed to parse output: {e}",
                    scan_time=scan_time,
                )

            # Extract findings
            results = output_data.get("Results", [])

            vulnerabilities = self._parse_vulnerabilities(results)
            misconfigurations = self._parse_misconfigurations(results)
            secrets = self._parse_secrets(results)

            # Get metadata
            metadata = output_data.get("Metadata", {})
            os_info = metadata.get("OS", {})

            return TrivyResult(
                success=True,
                target=target,
                scan_type=target_type.value,
                vulnerabilities=vulnerabilities,
                misconfigurations=misconfigurations,
                secrets=secrets,
                scan_time=scan_time,
                os_info=os_info,
                artifact_name=output_data.get("ArtifactName", target),
                artifact_type=output_data.get("ArtifactType", ""),
            )

        except asyncio.TimeoutError:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Trivy scan timed out after {scan_timeout}s")
            return TrivyResult(
                success=False,
                target=target,
                scan_type=target_type.value,
                error=f"Scan timed out after {scan_timeout} seconds",
                scan_time=scan_time,
            )

        except Exception as e:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Trivy scan error: {e}")
            return TrivyResult(
                success=False,
                target=target,
                scan_type=target_type.value,
                error=str(e),
                scan_time=scan_time,
            )

    def _run_subprocess(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run subprocess (sync, to be called in executor)"""
        return subprocess.run(cmd, capture_output=True, text=True)

    async def generate_sbom(
        self,
        target: str,
        target_type: TrivyScanTarget = TrivyScanTarget.IMAGE,
        sbom_format: str = "cyclonedx",
    ) -> str:
        """
        Generate SBOM for target.

        Args:
            target: Target to scan
            target_type: Type of target
            sbom_format: SBOM format (cyclonedx, spdx, spdx-json)

        Returns:
            SBOM content
        """
        cmd = [
            self.trivy_path,
            "sbom",
            target,
            "--format",
            sbom_format,
        ]

        if self.cache_dir:
            cmd.extend(["--cache-dir", self.cache_dir])

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._run_subprocess, cmd)

            if result.returncode == 0:
                return result.stdout
            else:
                return f"SBOM generation failed: {result.stderr}"

        except Exception as e:
            return f"SBOM generation error: {e}"

    def parse_output(self, result: TrivyResult) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse Trivy result into standardized format.

        Args:
            result: TrivyResult object

        Returns:
            Dictionary with parsed vulnerabilities, misconfigurations, and secrets
        """
        parsed = {
            "vulnerabilities": [],
            "misconfigurations": [],
            "secrets": [],
        }

        # Parse vulnerabilities
        for vuln in result.vulnerabilities:
            parsed["vulnerabilities"].append(
                {
                    "tool": "trivy",
                    "type": "vulnerability",
                    "id": vuln.vulnerability_id,
                    "package": vuln.pkg_name,
                    "installed_version": vuln.installed_version,
                    "fixed_version": vuln.fixed_version,
                    "severity": vuln.severity.lower(),
                    "title": vuln.title,
                    "description": vuln.description,
                    "cvss_score": vuln.cvss_score,
                    "references": vuln.references,
                    "primary_url": vuln.primary_url,
                }
            )

        # Parse misconfigurations
        for misconf in result.misconfigurations:
            parsed["misconfigurations"].append(
                {
                    "tool": "trivy",
                    "type": "misconfiguration",
                    "id": misconf.id,
                    "misconfiguration_type": misconf.type,
                    "severity": misconf.severity.lower(),
                    "title": misconf.title,
                    "description": misconf.description,
                    "message": misconf.message,
                    "resolution": misconf.resolution,
                    "references": misconf.references,
                }
            )

        # Parse secrets
        for secret in result.secrets:
            parsed["secrets"].append(
                {
                    "tool": "trivy",
                    "type": "secret",
                    "rule_id": secret.rule_id,
                    "category": secret.category,
                    "severity": secret.severity.lower(),
                    "title": secret.title,
                }
            )

        return parsed

    def normalize_findings(self, result: TrivyResult) -> List[Dict[str, Any]]:
        """
        Normalize findings to standard format.

        Args:
            result: TrivyResult object

        Returns:
            List of normalized findings
        """
        normalized = []

        # Normalize vulnerabilities
        for vuln in result.vulnerabilities:
            normalized.append(
                {
                    "tool": "trivy",
                    "target": result.target,
                    "severity": vuln.severity.lower(),
                    "title": vuln.title or vuln.vulnerability_id,
                    "description": vuln.description,
                    "evidence": {
                        "package": vuln.pkg_name,
                        "installed_version": vuln.installed_version,
                        "fixed_version": vuln.fixed_version,
                        "vulnerability_id": vuln.vulnerability_id,
                    },
                    "remediation": (
                        f"Update {vuln.pkg_name} to version {vuln.fixed_version}"
                        if vuln.fixed_version
                        else "Check vendor advisory for remediation"
                    ),
                    "references": [vuln.primary_url] + vuln.references if vuln.primary_url else vuln.references,
                    "cvss_score": vuln.cvss_score,
                }
            )

        # Normalize misconfigurations
        for misconf in result.misconfigurations:
            normalized.append(
                {
                    "tool": "trivy",
                    "target": result.target,
                    "severity": misconf.severity.lower(),
                    "title": misconf.title,
                    "description": misconf.description,
                    "evidence": {
                        "type": misconf.type,
                        "message": misconf.message,
                    },
                    "remediation": misconf.resolution,
                    "references": misconf.references,
                }
            )

        # Normalize secrets
        for secret in result.secrets:
            normalized.append(
                {
                    "tool": "trivy",
                    "target": result.target,
                    "severity": secret.severity.lower(),
                    "title": f"Secret Found: {secret.title}",
                    "description": f"Detected {secret.category} secret in code",
                    "evidence": {
                        "category": secret.category,
                        "file": secret.file_path,
                        "match": secret.match,
                    },
                    "remediation": (
                        "1. Remove the secret from the code\n"
                        "2. Rotate the exposed secret\n"
                        "3. Use environment variables or secret management"
                    ),
                    "references": [],
                }
            )

        return normalized

    def get_version(self) -> str:
        """Get Trivy version"""
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
def trivy_scan_image(image: str, severity: str = "HIGH,CRITICAL") -> str:
    """
    Scan a container image for vulnerabilities using Trivy.

    Args:
        image: Container image name (e.g., "nginx:latest", "python:3.9-slim")
        severity: Comma-separated severity levels to report

    Returns:
        Vulnerability scan results
    """
    import asyncio

    severity_list = [s.strip() for s in severity.split(",")]

    scanner = TrivyScanner(
        severity=severity_list,
        scanners=[TrivyScannerType.VULNERABILITY],
    )

    result = asyncio.run(scanner.scan_image(image))

    if not result.success:
        return f"Trivy scan failed: {result.error}"

    # Format results
    lines = [
        f"Trivy Image Scan: {image}",
        f"Scan Time: {result.scan_time:.2f}s",
        f"OS: {result.os_info.get('Family', 'Unknown')} {result.os_info.get('Name', '')}",
        "",
        "Vulnerabilities:",
    ]

    # Group by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for vuln in result.vulnerabilities:
        sev = vuln.severity.upper()
        if sev in severity_counts:
            severity_counts[sev] += 1

    for sev, count in severity_counts.items():
        if count > 0:
            lines.append(f"  {sev}: {count}")

    # Show top vulnerabilities
    critical_high = [v for v in result.vulnerabilities if v.severity in ["CRITICAL", "HIGH"]]
    if critical_high:
        lines.append("\nTop Issues:")
        for vuln in critical_high[:5]:
            lines.append(f"  - {vuln.vulnerability_id}: {vuln.title[:60]}")
            if vuln.fixed_version:
                lines.append(f"    Fix: Update to {vuln.fixed_version}")

    return "\n".join(lines)


@tool
def trivy_scan_filesystem(path: str) -> str:
    """
    Scan a filesystem path for vulnerabilities and misconfigurations.

    Args:
        path: Path to scan

    Returns:
        Scan results with vulnerabilities and misconfigurations
    """
    import asyncio

    scanner = TrivyScanner(
        scanners=[TrivyScannerType.VULNERABILITY, TrivyScannerType.MISCONFIGURATION],
    )

    result = asyncio.run(scanner.scan_filesystem(path))

    if not result.success:
        return f"Filesystem scan failed: {result.error}"

    vuln_count = len(result.vulnerabilities)
    misconf_count = len(result.misconfigurations)

    return (
        f"Trivy Filesystem Scan: {path}\n"
        f"  Vulnerabilities: {vuln_count}\n"
        f"  Misconfigurations: {misconf_count}\n"
        f"  Scan Time: {result.scan_time:.2f}s"
    )


@tool
def trivy_scan_dockerfile(dockerfile_path: str) -> str:
    """
    Scan a Dockerfile for misconfigurations.

    Args:
        dockerfile_path: Path to Dockerfile

    Returns:
        Misconfiguration findings
    """
    import asyncio

    scanner = TrivyScanner(
        scanners=[TrivyScannerType.MISCONFIGURATION],
    )

    result = asyncio.run(scanner.scan_filesystem(dockerfile_path))

    if not result.success:
        return f"Dockerfile scan failed: {result.error}"

    lines = [
        f"Dockerfile Scan: {dockerfile_path}",
        f"Misconfigurations: {len(result.misconfigurations)}",
        "",
    ]

    for misconf in result.misconfigurations[:10]:
        lines.append(f"- {misconf.title}")
        lines.append(f"  Severity: {misconf.severity}")
        lines.append(f"  Resolution: {misconf.resolution[:100]}")

    return "\n".join(lines)


@tool
def trivy_generate_sbom(image: str) -> str:
    """
    Generate SBOM for a container image.

    Args:
        image: Container image name

    Returns:
        SBOM generation result
    """
    import asyncio

    scanner = TrivyScanner()
    sbom = asyncio.run(scanner.generate_sbom(image))

    if "failed" in sbom.lower() or "error" in sbom.lower():
        return sbom

    return f"SBOM generated for {image}\nLength: {len(sbom)} characters"


# Tool Registry integration
try:
    from .tool_registry import ToolCategory, ToolSafetyLevel, registry

    TOOL_REGISTRY_AVAILABLE = True
except ImportError:
    TOOL_REGISTRY_AVAILABLE = False
    registry = None
    ToolCategory = None
    ToolSafetyLevel = None


def register_trivy_tools():
    """Register Trivy tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=trivy_scan_image,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["container", "vulnerability", "scanner", "trivy"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=trivy_scan_filesystem,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["filesystem", "vulnerability", "scanner", "trivy"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=trivy_scan_dockerfile,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["dockerfile", "misconfiguration", "trivy"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=trivy_generate_sbom,
            category=ToolCategory.UTILITY,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["container", "sbom", "trivy"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        logger.info("Trivy tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register Trivy tools: {e}")


# Auto-register on import
try:
    register_trivy_tools()
except Exception:
    pass


__all__ = [
    "TrivyScanner",
    "TrivyVulnerability",
    "TrivyMisconfiguration",
    "TrivySecret",
    "TrivyResult",
    "TrivyScanTarget",
    "TrivyScannerType",
    "trivy_scan_image",
    "trivy_scan_filesystem",
    "trivy_scan_dockerfile",
    "trivy_generate_sbom",
    "register_trivy_tools",
]
