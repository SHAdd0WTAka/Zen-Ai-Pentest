"""Semgrep Integration - Static Analysis for Code Security for Zen-AI-Pentest

This module provides a comprehensive Semgrep wrapper with:
- Custom rule support
- OWASP/CWE coverage
- Multiple language support
- CI/CD integration
- Rule configuration
- JSON output parsing
- Finding categorization
- False positive handling

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


class SemgrepSeverity(Enum):
    """Semgrep severity levels"""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class SemgrepConfidence(Enum):
    """Semgrep confidence levels"""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class SemgrepFinding:
    """Represents a Semgrep finding"""

    check_id: str
    path: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    message: str
    severity: str
    confidence: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    code_snippet: str = ""
    fix: str = ""
    fix_regex: Dict[str, str] = field(default_factory=dict)


@dataclass
class SemgrepResult:
    """Complete Semgrep scan result"""

    success: bool
    target: str
    findings: List[SemgrepFinding] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scan_time: float = 0.0
    error: Optional[str] = None
    stats: Dict[str, Any] = field(default_factory=dict)


class SemgrepScanner:
    """
    Advanced Semgrep scanner for static code analysis.

    Features:
    - Custom rule support
    - OWASP/CWE coverage
    - Multiple language support
    - CI/CD integration
    - Rule configuration
    - JSON output parsing
    - Finding categorization
    - False positive handling
    """

    SEVERITY_MAP = {
        "ERROR": "high",
        "WARNING": "medium",
        "INFO": "low",
    }

    DEFAULT_RULES = [
        "p/security-audit",
        "p/owasp-top-ten",
        "p/cwe-top-25",
        "p/secrets",
    ]

    LANGUAGE_EXTENSIONS = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "go": [".go"],
        "ruby": [".rb"],
        "php": [".php"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
        "c": [".c", ".h"],
        "swift": [".swift"],
        "kotlin": [".kt", ".kts"],
        "scala": [".scala"],
        "rust": [".rs"],
    }

    def __init__(
        self,
        semgrep_path: str = "semgrep",
        config: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        max_memory: int = 0,
        max_target_bytes: int = 1000000,
        num_jobs: int = 4,
        timeout: int = 300,
        timeout_threshold: int = 3,
        autofix: bool = False,
        dry_run: bool = True,
        strict: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize Semgrep scanner.

        Args:
            semgrep_path: Path to semgrep binary
            config: List of rules/configs to use
            exclude_patterns: Patterns to exclude from scanning
            include_patterns: Patterns to include in scanning
            max_memory: Maximum memory to use in MB (0 = unlimited)
            max_target_bytes: Maximum file size to scan
            num_jobs: Number of parallel jobs
            timeout: Timeout for semgrep in seconds
            timeout_threshold: Number of times a rule can timeout
            autofix: Apply autofixes
            dry_run: Run in dry-run mode
            strict: Exit with error on warnings
            verbose: Verbose output
        """
        self.semgrep_path = self._validate_installation(semgrep_path)
        self.config = config or self.DEFAULT_RULES.copy()
        self.exclude_patterns = exclude_patterns or [
            "node_modules",
            "vendor",
            ".git",
            "__pycache__",
            "*.min.js",
            "*.min.css",
            "dist",
            "build",
            ".tox",
            ".venv",
            "venv",
        ]
        self.include_patterns = include_patterns or []
        self.max_memory = max_memory
        self.max_target_bytes = max_target_bytes
        self.num_jobs = num_jobs
        self.timeout = timeout
        self.timeout_threshold = timeout_threshold
        self.autofix = autofix
        self.dry_run = dry_run
        self.strict = strict
        self.verbose = verbose

    def _validate_installation(self, path: str) -> str:
        """Validate semgrep binary exists"""
        semgrep_path = shutil.which(path)
        if not semgrep_path:
            raise RuntimeError(
                f"semgrep not found at '{path}'. Install with: pip install semgrep"
            )
        return semgrep_path

    def _get_version(self) -> str:
        """Get Semgrep version"""
        try:
            result = subprocess.run(
                [self.semgrep_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _build_command(self, target: str, output_file: Optional[str] = None) -> List[str]:
        """Build semgrep command"""
        cmd = [self.semgrep_path, "--json"]

        # Add configs/rules
        for config in self.config:
            cmd.extend(["--config", config])

        # Exclude patterns
        for pattern in self.exclude_patterns:
            cmd.extend(["--exclude", pattern])

        # Include patterns
        if self.include_patterns:
            for pattern in self.include_patterns:
                cmd.extend(["--include", pattern])

        # Performance options
        if self.max_memory > 0:
            cmd.extend(["--max-memory", str(self.max_memory)])

        cmd.extend(["--max-target-bytes", str(self.max_target_bytes)])
        cmd.extend(["--jobs", str(self.num_jobs)])
        cmd.extend(["--timeout", str(self.timeout)])
        cmd.extend(["--timeout-threshold", str(self.timeout_threshold)])

        # Behavior options
        if self.autofix:
            cmd.append("--autofix")

        if self.dry_run:
            cmd.append("--dryrun")

        if self.strict:
            cmd.append("--strict")

        if self.verbose:
            cmd.append("--verbose")

        # Add target
        cmd.append(target)

        # Output file
        if output_file:
            cmd.extend(["--output", output_file])

        return cmd

    def _parse_findings(self, data: Dict[str, Any]) -> List[SemgrepFinding]:
        """
        Parse Semgrep JSON output into findings.

        Args:
            data: Parsed JSON data

        Returns:
            List of SemgrepFinding objects
        """
        findings = []

        results = data.get("results", [])
        for result in results:
            # Get location
            location = result.get("start", {})
            end_location = result.get("end", {})

            # Get metadata
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})

            # Extract fix information
            fix = extra.get("fix", "")
            fix_regex = extra.get("fix_regex", {})

            # Get code snippet
            lines = extra.get("lines", "")

            finding = SemgrepFinding(
                check_id=result.get("check_id", ""),
                path=result.get("path", ""),
                start_line=location.get("line", 0),
                end_line=end_location.get("line", 0),
                start_col=location.get("col", 0),
                end_col=end_location.get("col", 0),
                message=extra.get("message", ""),
                severity=extra.get("severity", "WARNING"),
                confidence=metadata.get("confidence", "MEDIUM"),
                metadata=metadata,
                code_snippet=lines,
                fix=fix,
                fix_regex=fix_regex,
            )
            findings.append(finding)

        return findings

    def _extract_errors(self, data: Dict[str, Any]) -> List[str]:
        """Extract errors from Semgrep output"""
        errors = data.get("errors", [])
        return [error.get("message", "Unknown error") for error in errors]

    def _extract_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract statistics from Semgrep output"""
        stats = {}

        # Extract engine stats if available
        engine_requested = data.get("engine_requested", "OS")
        stats["engine"] = engine_requested

        # Extract version
        stats["version"] = data.get("version", "unknown")

        # Count findings by severity
        results = data.get("results", [])
        severity_counts = {}
        for result in results:
            severity = result.get("extra", {}).get("severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        stats["severity_counts"] = severity_counts

        return stats

    async def scan(
        self,
        target: str,
        custom_config: Optional[List[str]] = None,
    ) -> SemgrepResult:
        """
        Run Semgrep scan.

        Args:
            target: Path or target to scan
            custom_config: Optional custom config to override default

        Returns:
            SemgrepResult with scan results
        """
        start_time = asyncio.get_event_loop().time()

        # Validate target
        target_path = Path(target)
        if not target_path.exists():
            return SemgrepResult(
                success=False,
                target=target,
                error=f"Target does not exist: {target}",
            )

        # Use custom config if provided
        original_config = self.config
        if custom_config:
            self.config = custom_config

        cmd = self._build_command(target)

        logger.info(f"Starting Semgrep scan: {target}")

        try:
            # Run semgrep in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._run_subprocess, cmd)

            scan_time = asyncio.get_event_loop().time() - start_time

            # Parse JSON output
            try:
                output_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                # Restore original config
                self.config = original_config
                return SemgrepResult(
                    success=False,
                    target=target,
                    error=f"Failed to parse output: {e}",
                    scan_time=scan_time,
                )

            # Extract findings
            findings = self._parse_findings(output_data)
            errors = self._extract_errors(output_data)
            stats = self._extract_stats(output_data)

            # Restore original config
            self.config = original_config

            success = result.returncode == 0 or (result.returncode == 1 and findings)

            return SemgrepResult(
                success=success,
                target=target,
                findings=findings,
                errors=errors,
                scan_time=scan_time,
                stats=stats,
            )

        except asyncio.TimeoutError:
            scan_time = asyncio.get_event_loop().time() - start_time
            # Restore original config
            self.config = original_config
            logger.error(f"Semgrep scan timed out after {self.timeout}s")
            return SemgrepResult(
                success=False,
                target=target,
                error=f"Scan timed out after {self.timeout} seconds",
                scan_time=scan_time,
            )

        except Exception as e:
            scan_time = asyncio.get_event_loop().time() - start_time
            # Restore original config
            self.config = original_config
            logger.error(f"Semgrep scan error: {e}")
            return SemgrepResult(
                success=False,
                target=target,
                error=str(e),
                scan_time=scan_time,
            )

    def _run_subprocess(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Run subprocess (sync, to be called in executor)"""
        return subprocess.run(cmd, capture_output=True, text=True)

    def parse_output(self, result: SemgrepResult) -> List[Dict[str, Any]]:
        """
        Parse Semgrep result into standardized format.

        Args:
            result: SemgrepResult object

        Returns:
            List of standardized finding dictionaries
        """
        findings = []

        for finding in result.findings:
            # Extract CWE IDs from metadata
            cwe = finding.metadata.get("cwe", [])
            cwe_ids = [str(c) for c in cwe] if isinstance(cwe, list) else [str(cwe)]

            # Extract OWASP categories
            owasp = finding.metadata.get("owasp", [])
            owasp_ids = owasp if isinstance(owasp, list) else [owasp]

            # Extract references
            references = finding.metadata.get("references", [])
            if not isinstance(references, list):
                references = [references]

            # Extract technology/languages
            technology = finding.metadata.get("technology", [])
            languages = technology if isinstance(technology, list) else [technology]

            parsed = {
                "tool": "semgrep",
                "check_id": finding.check_id,
                "path": finding.path,
                "line": finding.start_line,
                "column": finding.start_col,
                "message": finding.message,
                "severity": self.SEVERITY_MAP.get(finding.severity, "medium"),
                "confidence": finding.confidence.lower(),
                "cwe_ids": cwe_ids,
                "owasp": owasp_ids,
                "languages": languages,
                "references": references,
                "code": finding.code_snippet,
                "fix": finding.fix,
                "category": finding.metadata.get("category", "security"),
                "subcategory": finding.metadata.get("subcategory", []),
                "likelihood": finding.metadata.get("likelihood", "LOW"),
                "impact": finding.metadata.get("impact", "LOW"),
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
            # Build remediation
            remediation = finding.get("fix", "")
            if not remediation:
                remediation = (
                    "Review the code and fix the security issue. "
                    "Refer to the provided references for guidance."
                )

            # Build evidence
            evidence = {
                "file": finding.get("path"),
                "line": finding.get("line"),
                "column": finding.get("column"),
                "code": finding.get("code", ""),
                "check_id": finding.get("check_id"),
            }

            # Build references
            references = finding.get("references", [])
            if finding.get("cwe_ids"):
                for cwe_id in finding.get("cwe_ids", []):
                    if cwe_id.startswith("CWE-"):
                        references.append(f"https://cwe.mitre.org/data/definitions/{cwe_id[4:]}.html")

            normalized_finding = {
                "tool": "semgrep",
                "target": finding.get("path", ""),
                "severity": finding.get("severity", "medium").lower(),
                "title": finding.get("message", "Code Security Issue")[:100],
                "description": finding.get("message", ""),
                "evidence": evidence,
                "remediation": remediation,
                "references": references,
                "cwe_ids": finding.get("cwe_ids", []),
                "owasp": finding.get("owasp", []),
                "confidence": finding.get("confidence", "medium"),
                "languages": finding.get("languages", []),
            }
            normalized.append(normalized_finding)

        return normalized

    def get_version(self) -> str:
        """Get Semgrep version"""
        return self._get_version()

    def add_owasp_rules(self) -> None:
        """Add OWASP rules to configuration"""
        if "p/owasp-top-ten" not in self.config:
            self.config.append("p/owasp-top-ten")

    def add_cwe_rules(self) -> None:
        """Add CWE Top 25 rules to configuration"""
        if "p/cwe-top-25" not in self.config:
            self.config.append("p/cwe-top-25")

    def add_security_audit_rules(self) -> None:
        """Add security audit rules to configuration"""
        if "p/security-audit" not in self.config:
            self.config.append("p/security-audit")

    def add_secrets_rules(self) -> None:
        """Add secrets detection rules"""
        if "p/secrets" not in self.config:
            self.config.append("p/secrets")

    def filter_false_positives(
        self,
        findings: List[SemgrepFinding],
        false_positive_patterns: Optional[List[str]] = None,
    ) -> List[SemgrepFinding]:
        """
        Filter out potential false positives.

        Args:
            findings: List of findings
            false_positive_patterns: Regex patterns for false positives

        Returns:
            Filtered findings
        """
        if not false_positive_patterns:
            # Default patterns
            false_positive_patterns = [
                r"test_",  # Test files
                r"_test\.",  # Test files
                r"spec\.",  # Spec files
                r"mock",  # Mock objects
                r"example",  # Example code
                r"fixtures",  # Test fixtures
            ]

        import re
        filtered = []

        for finding in findings:
            is_fp = False
            for pattern in false_positive_patterns:
                if re.search(pattern, finding.path, re.IGNORECASE):
                    is_fp = True
                    break

                # Check if code contains false positive indicators
                if re.search(pattern, finding.code_snippet, re.IGNORECASE):
                    is_fp = True
                    break

            if not is_fp:
                filtered.append(finding)

        return filtered


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
def semgrep_scan_code(path: str, rules: str = "") -> str:
    """
    Scan code for security issues using Semgrep.

    Args:
        path: Path to code to scan
        rules: Comma-separated list of rules (default: security-audit, owasp, cwe)

    Returns:
        Security findings
    """
    import asyncio

    # Parse rules
    if rules:
        rule_list = [r.strip() for r in rules.split(",")]
    else:
        rule_list = ["p/security-audit", "p/owasp-top-ten", "p/cwe-top-25"]

    scanner = SemgrepScanner(config=rule_list)
    result = asyncio.run(scanner.scan(path))

    if not result.success:
        return f"Semgrep scan failed: {result.error}"

    # Format results
    lines = [
        f"Semgrep Scan: {path}",
        f"Rules: {', '.join(rule_list)}",
        f"Findings: {len(result.findings)}",
        f"Scan Time: {result.scan_time:.2f}s",
        "",
    ]

    # Group by severity
    severity_groups = {"high": [], "medium": [], "low": []}
    for finding in result.findings:
        sev = scanner.SEVERITY_MAP.get(finding.severity, "medium")
        severity_groups[sev].append(finding)

    for sev in ["high", "medium"]:
        if severity_groups[sev]:
            lines.append(f"\n{sev.upper()} Severity ({len(severity_groups[sev])}):")
            for finding in severity_groups[sev][:5]:
                lines.append(f"  - {finding.check_id}")
                lines.append(f"    File: {finding.path}:{finding.start_line}")
                lines.append(f"    {finding.message[:80]}...")

    return "\n".join(lines)


@tool
def semgrep_scan_owasp(path: str) -> str:
    """
    Scan code for OWASP Top 10 vulnerabilities.

    Args:
        path: Path to code to scan

    Returns:
        OWASP findings
    """
    import asyncio

    scanner = SemgrepScanner(config=["p/owasp-top-ten"])
    result = asyncio.run(scanner.scan(path))

    if not result.success:
        return f"OWASP scan failed: {result.error}"

    owasp_count = sum(
        1 for f in result.findings
        if f.metadata.get("owasp")
    )

    return (
        f"OWASP Top 10 Scan: {path}\n"
        f"  Findings: {len(result.findings)}\n"
        f"  OWASP-related: {owasp_count}\n"
        f"  Duration: {result.scan_time:.2f}s"
    )


@tool
def semgrep_scan_secrets(path: str) -> str:
    """
    Scan code for secrets and credentials.

    Args:
        path: Path to code to scan

    Returns:
        Secret findings
    """
    import asyncio

    scanner = SemgrepScanner(
        config=["p/secrets"],
        exclude_patterns=["node_modules", "vendor", ".git"],
    )
    result = asyncio.run(scanner.scan(path))

    if not result.success:
        return f"Secrets scan failed: {result.error}"

    return (
        f"Secrets Scan: {path}\n"
        f"  Potential secrets found: {len(result.findings)}\n"
        f"  Review findings carefully - some may be false positives"
    )


@tool
def semgrep_scan_ci(path: str) -> str:
    """
    CI/CD optimized Semgrep scan with essential rules.

    Args:
        path: Path to code to scan

    Returns:
        Security summary for CI/CD
    """
    import asyncio

    scanner = SemgrepScanner(
        config=[
            "p/security-audit",
            "p/secrets",
            "p/cwe-top-25",
        ],
        strict=True,
    )

    result = asyncio.run(scanner.scan(path))

    if not result.success:
        return f"CI scan failed: {result.error}"

    high = sum(1 for f in result.findings if f.severity == "ERROR")

    return (
        f"CI Security Scan: {path}\n"
        f"  High Severity: {high}\n"
        f"  Total Issues: {len(result.findings)}\n"
        f"  Status: {'PASS' if high == 0 else 'FAIL'}"
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


def register_semgrep_tools():
    """Register Semgrep tools with the tool registry"""
    if not TOOL_REGISTRY_AVAILABLE or not LANGCHAIN_AVAILABLE:
        return

    try:
        registry.register(
            tool=semgrep_scan_code,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["sast", "code", "security", "semgrep"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=semgrep_scan_owasp,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["sast", "owasp", "code", "semgrep"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=semgrep_scan_secrets,
            category=ToolCategory.RECONNAISSANCE,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["secrets", "sast", "code", "semgrep"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        registry.register(
            tool=semgrep_scan_ci,
            category=ToolCategory.SCANNING,
            safety_level=ToolSafetyLevel.SAFE,
            tags=["sast", "ci-cd", "code", "semgrep"],
            author="Zen-AI-Pentest Team",
            version="1.0.0",
        )

        logger.info("Semgrep tools registered successfully")
    except Exception as e:
        logger.warning(f"Could not register Semgrep tools: {e}")


# Auto-register on import
try:
    register_semgrep_tools()
except Exception:
    pass


__all__ = [
    "SemgrepScanner",
    "SemgrepFinding",
    "SemgrepResult",
    "SemgrepSeverity",
    "SemgrepConfidence",
    "semgrep_scan_code",
    "semgrep_scan_owasp",
    "semgrep_scan_secrets",
    "semgrep_scan_ci",
    "register_semgrep_tools",
]
