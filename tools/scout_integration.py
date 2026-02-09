"""ScoutSuite Integration - Cloud Security Posture Assessment for Zen-AI-Pentest

This module provides a comprehensive ScoutSuite wrapper with:
- AWS, Azure, GCP support
- Compliance checking
- Security rule evaluation
- Report parsing
- Finding normalization
- Risk scoring integration

Author: Zen-AI-Pentest Team
License: MIT
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud providers"""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ALIBABA = "aliyun"
    ORACLE = "oracle"


@dataclass
class ScoutFinding:
    """Represents a ScoutSuite security finding"""

    rule_id: str
    description: str
    severity: str
    provider: str
    service: str
    resource_type: str
    resource_path: str
    remediation: str
    compliance: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    enabled: bool = True
    flagged_items: int = 0
    checked_items: int = 0


@dataclass
class ScoutResult:
    """Complete ScoutSuite scan result"""

    success: bool
    provider: str
    findings: List[ScoutFinding] = field(default_factory=list)
    scan_time: float = 0.0
    error: Optional[str] = None
    report_path: Optional[str] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    compliance_summary: Dict[str, Any] = field(default_factory=dict)


class ScoutSuiteScanner:
    """
    Advanced ScoutSuite scanner for cloud security posture assessment.

    Features:
    - AWS, Azure, GCP support
    - Compliance checking (CIS, PCI-DSS, HIPAA, etc.)
    - Security rule evaluation
    - Report parsing
    - Finding normalization
    - Risk scoring integration
    """

    SEVERITY_MAP = {
        "danger": "critical",
        "critical": "critical",
        "high": "high",
        "warning": "medium",
        "medium": "medium",
        "low": "low",
        "info": "info",
    }

    COMPLIANCE_FRAMEWORKS = {
        "aws": ["cis", "pci-dss", "hipaa", "gdpr", "soc2", "nist"],
        "azure": ["cis", "pci-dss", "hipaa", "gdpr"],
        "gcp": ["cis", "pci-dss", "hipaa", "gdpr"],
    }

    def __init__(
        self,
        provider: Union[CloudProvider, str],
        scout_path: str = "scout",
        profile: Optional[str] = None,
        regions: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        compliance: Optional[List[str]] = None,
        output_dir: str = "./scout-reports",
        skip_prompt: bool = True,
        thread_config: int = 5,
    ):
        """
        Initialize ScoutSuite scanner.

        Args:
            provider: Cloud provider (aws, azure, gcp)
            scout_path: Path to ScoutSuite executable
            profile: AWS profile name (for AWS provider)
            regions: List of regions to scan
            services: List of services to scan
            compliance: List of compliance frameworks to check
            output_dir: Directory for output reports
            skip_prompt: Skip confirmation prompts
            thread_config: Number of threads to use
        """
        self.scout_path = self._validate_installation(scout_path)
        self.provider = provider.value if isinstance(provider, CloudProvider) else provider
        self.profile = profile
        self.regions = regions or []
        self.services = services or []
        self.compliance = compliance or []
        self.output_dir = output_dir
        self.skip_prompt = skip_prompt
        self.thread_config = thread_config

        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _validate_installation(self, path: str) -> str:
        """Validate ScoutSuite installation"""
        scout_path = shutil.which(path)
        if not scout_path:
            # Try alternative names
            for alt_name in ["scout", "scoutsuite", "ScoutSuite"]:
                scout_path = shutil.which(alt_name)
                if scout_path:
                    break

        if not scout_path:
            raise RuntimeError(
                f"ScoutSuite not found. Install with: pip install scoutsuite"
            )
        return scout_path

    def _get_version(self) -> str:
        """Get ScoutSuite version"""
        try:
            result = subprocess.run(
                [self.scout_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _build_command(self) -> List[str]:
        """Build ScoutSuite command"""
        cmd = [
            self.scout_path,
            self.provider,
            "--report-dir", self.output_dir,
            "--thread-config", str(self.thread_config),
        ]

        if self.skip_prompt:
            cmd.append("--no-browser")

        if self.profile and self.provider == "aws":
            cmd.extend(["--profile", self.profile])

        if self.regions:
            cmd.extend(["--regions", ",".join(self.regions)])

        if self.services:
            cmd.extend(["--services", ",".join(self.services)])

        if self.compliance:
            cmd.extend(["--compliance", ",".join(self.compliance)])

        return cmd

    def _find_latest_report(self) -> Optional[str]:
        """Find the most recent ScoutSuite report"""
        output_path = Path(self.output_dir)
        if not output_path.exists():
            return None

        # Look for JSON result files
        json_files = list(output_path.glob("*-*-*.json"))
        if not json_files:
            return None

        # Sort by modification time (newest first)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return str(json_files[0])

    def _parse_report(self, report_path: str) -> Dict[str, Any]:
        """
        Parse ScoutSuite JSON report.

        Args:
            report_path: Path to JSON report file

        Returns:
            Parsed report data
        """
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse report: {e}")
            return {}

    def _extract_findings(self, report_data: Dict[str, Any]) -> List[ScoutFinding]:
        """
        Extract findings from parsed report.

        Args:
            report_data: Parsed report data

        Returns:
            List of ScoutFinding objects
        """
        findings = []

        # Get findings from services
        services = report_data.get("services", {})

        for service_name, service_data in services.items():
            if not isinstance(service_data, dict):
                continue

            findings_data = service_data.get("findings", {})

            for rule_id, rule_data in findings_data.items():
                if not isinstance(rule_data, dict):
                    continue

                # Skip disabled checks
                if not rule_data.get("enabled", True):
                    continue

                # Get severity
                level = rule_data.get("level", "warning")
                severity = self.SEVERITY_MAP.get(level.lower(), "medium")

                # Get compliance frameworks
                compliance = rule_data.get("compliance", [])
                if isinstance(compliance, dict):
                    compliance = list(compliance.keys())

                finding = ScoutFinding(
                    rule_id=rule_id,
                    description=rule_data.get("description", ""),
                    severity=severity,
                    provider=self.provider,
                    service=service_name,
                    resource_type=rule_data.get("resource_type", "Unknown"),
                    resource_path="",
                    remediation=rule_data.get("remediation", ""),
                    compliance=compliance,
                    references=rule_data.get("references", []),
                    enabled=rule_data.get("enabled", True),
                    flagged_items=rule_data.get("flagged_items", 0),
                    checked_items=rule_data.get("checked_items", 0),
                )
                findings.append(finding)

        return findings

    def _generate_summary(self, findings: List[ScoutFinding]) -> Dict[str, Any]:
        """Generate summary statistics"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        service_counts = {}
        total_flagged = 0
        total_checked = 0

        for finding in findings:
            severity = finding.severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

            service = finding.service
            service_counts[service] = service_counts.get(service, 0) + 1

            total_flagged += finding.flagged_items
            total_checked += finding.checked_items

        return {
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "service_counts": service_counts,
            "total_flagged_items": total_flagged,
            "total_checked_items": total_checked,
        }

    async def scan(
        self,
        timeout: int = 3600,
        progress_callback: Optional[callable] = None,
    ) -> ScoutResult:
        """
        Run ScoutSuite scan.

        Args:
            timeout: Maximum scan time in seconds
            progress_callback: Callback function for progress updates

        Returns:
            ScoutResult with scan results
        """
        start_time = asyncio.get_event_loop().time()
        cmd = self._build_command()

        logger.info(f"Starting ScoutSuite scan for {self.provider}")

        try:
            # Check credentials before scanning
            if not self._check_credentials():
                return ScoutResult(
                    success=False,
                    provider=self.provider,
                    error=f"No valid credentials found for {self.provider}. Please configure credentials.",
                )

            # Run ScoutSuite
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._run_subprocess, cmd),
                timeout=timeout,
            )

            scan_time = asyncio.get_event_loop().time() - start_time

            if result.returncode != 0 and "error" in result.stderr.lower():
                return ScoutResult(
                    success=False,
                    provider=self.provider,
                    error=f"ScoutSuite failed: {result.stderr[:500]}",
                    scan_time=scan_time,
                )

            # Find and parse report
            report_path = self._find_latest_report()
            if not report_path:
                return ScoutResult(
                    success=False,
                    provider=self.provider,
                    error="No report generated",
                    scan_time=scan_time,
                )

            report_data = self._parse_report(report_path)
            findings = self._extract_findings(report_data)
            summary = self._generate_summary(findings)

            return ScoutResult(
                success=True,
                provider=self.provider,
                findings=findings,
                scan_time=scan_time,
                report_path=report_path,
                summary=summary,
            )

        except asyncio.TimeoutError:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"ScoutSuite scan timed out after {timeout}s")
            return ScoutResult(
                success=False,
                provider=self.provider,
                error=f"Scan timed out after {timeout} seconds",
                scan_time=scan_time,
            )

        except Exception as e:
            scan_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"ScoutSuite scan error: {e}")
            return ScoutResult(
                success=False,
                provider=self.provider,
                error=str(e),
                scan_time=scan_time,
            )

    def _check_credentials(self) -> bool:
        """Check if cloud provider credentials are configured"""
        if self.provider == "aws":
            return self._check_aws_credentials()
        elif self.provider == "azure":
            return self._check_azure_credentials()
        elif self.provider == "gcp":
            return self._check_gcp_credentials()
        return True

    def _check_aws_credentials(self) -> bool:
        """Check AWS credentials"""
        # Check environment variables
        if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
            return True
        if os.environ.get("AWS_PROFILE"):
            return True

        # Check AWS credentials file
        creds_path = Path.home() / ".aws" / "credentials"
        if creds_path.exists():
            return True

        # Check if using IAM role (EC2 instance profile)
        try:
            import subprocess
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            pass

        return False

    def _check_azure_credentials(self) -> bool:
        """Check Azure credentials"""
        # Check environment variables
        if os.environ.get("AZURE_CLIENT_ID") and os.environ.get("AZURE_CLIENT_SECRET"):
            return True
        if os.environ.get("AZURE_TENANT_ID"):
            return True

        # Check Azure CLI login
        try:
            result = subprocess.run(
                ["az", "account", "show"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            pass

        return False

    def _check_gcp_credentials(self) -> bool:
        """Check GCP credentials"""
        # Check environment variable
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            return True

        # Check gcloud credentials
        gcloud_creds = Path.home() / ".config" / "gcloud" / "credentials.db"
        if gcloud_creds.exists():
            return True

        # Check application_default_credentials
        adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        if adc_path.exists():
            return True

        return False

    def _run_subprocess(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run subprocess (sync, to be called in executor)"""
        return subprocess.run(cmd, capture_output=True, text=True)

    def parse_output(self, result: ScoutResult) -> List[Dict[str, Any]]:
        """
        Parse ScoutSuite result into standardized format.

        Args:
            result: ScoutResult object

        Returns:
            List of standardized finding dictionaries
        """
        findings = []
        for finding in result.findings:
            parsed = {
                "tool": "scoutsuite",
                "rule_id": finding.rule_id,
                "description": finding.description,
                "severity": finding.severity,
                "provider": finding.provider,
                "service": finding.service,
                "resource_type": finding.resource_type,
                "remediation": finding.remediation,
                "compliance": finding.compliance,
                "references": finding.references,
                "flagged_items": finding.flagged_items,
                "checked_items": finding.checked_items,
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
            normalized_finding = {
                "tool": "scoutsuite",
                "target": f"{finding.get('provider', 'cloud')}:{finding.get('service', 'unknown')}",
                "severity": finding.get("severity", "medium").lower(),
                "title": finding.get("rule_id", "Unknown Issue").replace("-", " ").title(),
                "description": finding.get("description", ""),
                "evidence": {
                    "provider": finding.get("provider"),
                    "service": finding.get("service"),
                    "resource_type": finding.get("resource_type"),
                    "flagged_items": finding.get("flagged_items", 0),
                    "checked_items": finding.get("checked_items", 0),
                },
                "remediation": finding.get("remediation", ""),
                "references": finding.get("references", []),
                "compliance": finding.get("compliance", []),
            }
            normalized.append(normalized_finding)

        return normalized

    def get_version(self) -> str:
        """Get ScoutSuite version"""
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
def scoutsuite_scan_aws(
    profile: str = "",
    regions: str = "",
    services: str = "",
) -> str:
    """
    Scan AWS infrastructure using ScoutSuite.

    Args:
        profile: AWS profile name (uses default if empty)
        regions: Comma-separated list of regions (scans all if empty)
        services: Comma-separated list of services (scans all if empty)

    Returns:
        Cloud security posture assessment results
    """
    import asyncio

    regions_list = [r.strip() for r in regions.split(",")] if regions else []
    services_list = [s.strip() for s in services.split(",")] if services else []

    scanner = ScoutSuiteScanner(
        provider=CloudProvider.AWS,
        profile=profile if profile else None,
        regions=regions_list,
        services=services_list,
    )

    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"ScoutSuite AWS scan failed: {result.error}"

    # Format results
    summary = result.summary
    severity = summary.get("severity_counts", {})

    lines = [
        f"ScoutSuite AWS Scan Complete",
        f"Duration: {result.scan_time:.2f}s",
        f"Report: {result.report_path}",
        "",
        "Findings Summary:",
        f"  Critical: {severity.get('critical', 0)}",
        f"  High: {severity.get('high', 0)}",
        f"  Medium: {severity.get('medium', 0)}",
        f"  Low: {severity.get('low', 0)}",
        f"  Total: {summary.get('total_findings', 0)}",
    ]

    return "\n".join(lines)


@tool
def scoutsuite_scan_azure() -> str:
    """
    Scan Azure infrastructure using ScoutSuite.

    Returns:
        Azure security posture assessment results
    """
    import asyncio

    scanner = ScoutSuiteScanner(provider=CloudProvider.AZURE)
    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"ScoutSuite Azure scan failed: {result.error}"

    return (
        f"Azure Scan Complete:\n"
        f"  Findings: {len(result.findings)}\n"
        f"  Report: {result.report_path}"
    )


@tool
def scoutsuite_scan_gcp(project_id: str = "") -> str:
    """
    Scan GCP infrastructure using ScoutSuite.

    Args:
        project_id: GCP Project ID (uses default if empty)

    Returns:
        GCP security posture assessment results
    """
    import asyncio

    # Set project if provided
    if project_id:
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

    scanner = ScoutSuiteScanner(provider=CloudProvider.GCP)
    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"ScoutSuite GCP scan failed: {result.error}"

    return (
        f"GCP Scan Complete for {project_id or 'default project'}:\n"
        f"  Findings: {len(result.findings)}\n"
        f"  Report: {result.report_path}"
    )


@tool
def scoutsuite_quick_scan(provider: str) -> str:
    """
    Quick security scan of cloud provider.

    Args:
        provider: Cloud provider (aws, azure, gcp)

    Returns:
        Quick security summary
    """
    import asyncio

    provider_map = {
        "aws": CloudProvider.AWS,
        "azure": CloudProvider.AZURE,
        "gcp": CloudProvider.GCP,
    }

    cloud = provider_map.get(provider.lower())
    if not cloud:
        return f"Unknown provider: {provider}. Use: aws, azure, or gcp"

    scanner = ScoutSuiteScanner(
        provider=cloud,
        services=["iam", "storage", "compute"],  # Focus on key services
    )

    result = asyncio.run(scanner.scan())

    if not result.success:
        return f"Scan failed: {result.error}"

    high_critical = sum(
        1 for f in result.findings
        if f.severity in ["critical", "high"]
    )

    return (
        f"{provider.upper()} Quick Scan Results:\n"
        f"  High/Critical Issues: {high_critical}\n"
        f"  Total Findings: {len(result.findings)}\n"
        f"  Full report: {result.report_path}"
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


def register_scout_tools():
    """Register ScoutSuite tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=scoutsuite_scan_aws,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["cloud", "aws", "security", "compliance", "scoutsuite"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=scoutsuite_scan_azure,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["cloud", "azure", "security", "compliance", "scoutsuite"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=scoutsuite_scan_gcp,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["cloud", "gcp", "security", "compliance", "scoutsuite"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=scoutsuite_quick_scan,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["cloud", "security", "quick", "scoutsuite"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        logger.info("ScoutSuite tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register ScoutSuite tools: {e}")


# Auto-register on import
try:
    register_scout_tools()
except Exception:
    pass


__all__ = [
    "ScoutSuiteScanner",
    "ScoutFinding",
    "ScoutResult",
    "CloudProvider",
    "scoutsuite_scan_aws",
    "scoutsuite_scan_azure",
    "scoutsuite_scan_gcp",
    "scoutsuite_quick_scan",
    "register_scout_tools",
]
