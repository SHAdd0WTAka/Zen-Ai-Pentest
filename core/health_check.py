"""
Health Check System for Zen-AI-Pentest

Comprehensive health monitoring system that checks:
- Database connectivity and performance
- Security tool availability and versions
- API health and response times
- System resources (memory, CPU, disk)
- Security configuration validation

Usage:
    from core.health_check import HealthCheckRunner, HealthCheckConfig

    config = HealthCheckConfig()
    runner = HealthCheckRunner(config)
    report = runner.run_all_checks()

    # Or run specific checks
    db_status = runner.check_database()
    tool_status = runner.check_tools()

Author: Zen-AI-Pentest Team
License: MIT
Version: 1.0.0
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil
from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SKIPPED = "skipped"


class SeverityLevel(Enum):
    """Severity levels for health checks"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class HealthCheckResult:
    """Result of a single health check"""

    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.name,
            "remediation": self.remediation,
        }


@dataclass
class HealthReport:
    """Complete health check report"""

    overall_status: HealthStatus
    checks: List[HealthCheckResult]
    summary: Dict[str, int]
    metadata: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "overall_status": self.overall_status.value,
            "generated_at": self.generated_at.isoformat(),
            "duration_ms": round(self.duration_ms, 2),
            "summary": self.summary,
            "metadata": self.metadata,
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class HealthCheckConfig(BaseModel):
    """Configuration for health check system"""

    model_config = {"extra": "forbid"}

    # Database checks
    check_database: bool = Field(default=True, description="Enable database health checks")
    database_url: Optional[str] = Field(default=None, description="Database URL override")
    database_timeout: int = Field(default=5, ge=1, le=60, description="Database connection timeout")

    # Tool checks
    check_tools: bool = Field(default=True, description="Enable tool availability checks")
    required_tools: List[str] = Field(
        default_factory=lambda: ["nmap", "sqlmap", "nuclei"],
        description="List of required security tools",
    )
    optional_tools: List[str] = Field(
        default_factory=lambda: [
            "gobuster",
            "ffuf",
            "amass",
            "subfinder",
            "httpx",
            "masscan",
            "nikto",
            "whatweb",
        ],
        description="List of optional security tools",
    )

    # API checks
    check_api: bool = Field(default=True, description="Enable API health checks")
    api_base_url: str = Field(default="http://localhost:8000", description="API base URL")
    api_timeout: int = Field(default=10, ge=1, le=60, description="API request timeout")
    api_auth_token: Optional[str] = Field(default=None, description="API authentication token")

    # Resource checks
    check_resources: bool = Field(default=True, description="Enable resource checks")
    memory_warning_threshold: float = Field(default=80.0, ge=0, le=100, description="Memory warning threshold %")
    memory_critical_threshold: float = Field(default=95.0, ge=0, le=100, description="Memory critical threshold %")
    disk_warning_threshold: float = Field(default=85.0, ge=0, le=100, description="Disk warning threshold %")
    disk_critical_threshold: float = Field(default=95.0, ge=0, le=100, description="Disk critical threshold %")
    cpu_warning_threshold: float = Field(default=80.0, ge=0, le=100, description="CPU warning threshold %")
    cpu_critical_threshold: float = Field(default=95.0, ge=0, le=100, description="CPU critical threshold %")

    # Security checks
    check_security: bool = Field(default=True, description="Enable security checks")
    ssl_check_hosts: List[str] = Field(
        default_factory=lambda: ["localhost:8000"],
        description="Hosts to check SSL certificates",
    )
    required_env_vars: List[str] = Field(
        default_factory=lambda: ["KIMI_API_KEY"],
        description="Required environment variables",
    )
    secrets_scan_paths: List[str] = Field(
        default_factory=lambda: ["core", "agents", "api", "tools"],
        description="Paths to scan for secrets",
    )
    secrets_exclude_patterns: List[str] = Field(
        default_factory=lambda: ["test", "__pycache__", ".pyc"],
        description="Patterns to exclude from secrets scan",
    )

    # General settings
    parallel_checks: bool = Field(default=True, description="Run checks in parallel")
    max_concurrent_checks: int = Field(default=5, ge=1, le=20, description="Max concurrent checks")
    timeout_per_check: int = Field(default=30, ge=5, le=300, description="Timeout per check in seconds")

    @field_validator("required_tools", "optional_tools", mode="before")
    @classmethod
    def validate_tools(cls, v):
        """Validate tool names"""
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v


class BaseHealthCheck:
    """Base class for health checks"""

    name: str = "base_check"
    description: str = "Base health check"
    severity: SeverityLevel = SeverityLevel.MEDIUM

    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> HealthCheckResult:
        """Run the health check - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run()")

    def _create_result(
        self,
        status: HealthStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        remediation: Optional[str] = None,
    ) -> HealthCheckResult:
        """Create a health check result"""
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=message,
            details=details or {},
            duration_ms=duration_ms,
            severity=self.severity,
            remediation=remediation,
        )

    def _run_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Run a synchronous function safely"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
            raise

    async def _run_async(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function with timeout"""
        try:
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, functools.partial(func, *args, **kwargs)),
                timeout=self.config.timeout_per_check,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Check {self.name} timed out after {self.config.timeout_per_check}s")
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {e}")
            raise


class DatabaseHealthCheck(BaseHealthCheck):
    """Check database connectivity and performance"""

    name = "database"
    description = "Database connectivity and performance check"
    severity = SeverityLevel.CRITICAL

    async def run(self) -> HealthCheckResult:
        """Run database health check"""
        start_time = time.time()

        if not self.config.check_database:
            return self._create_result(
                HealthStatus.SKIPPED, "Database checks disabled", duration_ms=(time.time() - start_time) * 1000
            )

        try:
            results = await self._run_async(self._check_database)
            duration_ms = (time.time() - start_time) * 1000

            # Determine overall status
            if results["connection"] == "error":
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Database connection failed: {results.get('error', 'Unknown error')}",
                    results,
                    duration_ms,
                    remediation="Check database URL, credentials, and network connectivity",
                )

            if results["query_performance"] == "slow":
                return self._create_result(
                    HealthStatus.WARNING,
                    "Database query performance is slow",
                    results,
                    duration_ms,
                    remediation="Consider optimizing queries or scaling database resources",
                )

            return self._create_result(HealthStatus.OK, "Database is healthy", results, duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.ERROR,
                f"Database check failed: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                duration_ms,
                remediation="Check database configuration and connectivity",
            )

    def _check_database(self) -> Dict[str, Any]:
        """Check database health"""
        results = {
            "connection": "unknown",
            "type": None,
            "query_performance": "unknown",
            "size_mb": None,
            "tables": [],
        }

        # Get database URL
        db_url = self.config.database_url or os.getenv("DATABASE_URL", "sqlite:///./zen_pentest.db")
        results["type"] = "postgresql" if "postgresql" in db_url.lower() else "sqlite"

        try:
            if results["type"] == "postgresql":
                import psycopg2

                conn = psycopg2.connect(db_url, connect_timeout=self.config.database_timeout)
                cursor = conn.cursor()

                # Test connection
                cursor.execute("SELECT 1")
                cursor.fetchone()
                results["connection"] = "ok"

                # Check query performance
                perf_start = time.time()
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables")
                perf_duration = (time.time() - perf_start) * 1000
                results["query_performance"] = "slow" if perf_duration > 1000 else "ok"
                results["query_time_ms"] = round(perf_duration, 2)

                # Get database size
                cursor.execute("SELECT pg_database_size(current_database()) / 1024 / 1024")
                results["size_mb"] = cursor.fetchone()[0]

                # Get table list
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                results["tables"] = [row[0] for row in cursor.fetchall()]

                conn.close()

            else:  # SQLite
                import sqlite3

                # Extract database path from URL
                db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
                conn = sqlite3.connect(db_path, timeout=self.config.database_timeout)
                cursor = conn.cursor()

                # Test connection
                cursor.execute("SELECT 1")
                cursor.fetchone()
                results["connection"] = "ok"

                # Check query performance
                perf_start = time.time()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                perf_duration = (time.time() - perf_start) * 1000
                results["query_performance"] = "slow" if perf_duration > 1000 else "ok"
                results["query_time_ms"] = round(perf_duration, 2)

                # Get database size
                if os.path.exists(db_path):
                    results["size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)

                results["tables"] = [row[0] for row in cursor.fetchall()]

                conn.close()

        except ImportError as e:
            results["connection"] = "error"
            results["error"] = f"Database driver not installed: {e}"
        except Exception as e:
            results["connection"] = "error"
            results["error"] = str(e)

        return results


class ToolsHealthCheck(BaseHealthCheck):
    """Check security tool availability and versions"""

    name = "tools"
    description = "Security tool availability and version check"
    severity = SeverityLevel.HIGH

    # Tool version extraction commands
    VERSION_COMMANDS = {
        "nmap": ("nmap --version", r"Nmap version ([\d.]+)"),
        "sqlmap": ("sqlmap --version", r"([\d.]+)"),
        "nuclei": ("nuclei --version", r"([\d.]+)"),
        "gobuster": ("gobuster version", r"Version\s+([\d.]+)"),
        "ffuf": ("ffuf -V", r"([\d.]+)"),
        "amass": ("amass -version", r"v?([\d.]+)"),
        "subfinder": ("subfinder -version", r"([\d.]+)"),
        "httpx": ("httpx -version", r"([\d.]+)"),
        "masscan": ("masscan --version", r"([\d.]+)"),
        "nikto": ("nikto -Version", r"([\d.]+)"),
        "whatweb": ("whatweb --version", r"([\d.]+)"),
    }

    async def run(self) -> HealthCheckResult:
        """Run tools health check"""
        start_time = time.time()

        if not self.config.check_tools:
            return self._create_result(
                HealthStatus.SKIPPED, "Tool checks disabled", duration_ms=(time.time() - start_time) * 1000
            )

        try:
            results = await self._run_async(self._check_tools)
            duration_ms = (time.time() - start_time) * 1000

            # Determine overall status
            required_missing = [t for t in results["required"] if not results["required"][t]["available"]]
            optional_missing = [t for t in results["optional"] if not results["optional"][t]["available"]]

            if required_missing:
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Required tools missing: {', '.join(required_missing)}",
                    results,
                    duration_ms,
                    remediation=f"Install missing tools: {', '.join(required_missing)}",
                )

            if len(optional_missing) > len(self.config.optional_tools) / 2:
                return self._create_result(
                    HealthStatus.WARNING,
                    f"Many optional tools missing: {', '.join(optional_missing[:3])}...",
                    results,
                    duration_ms,
                    remediation="Consider installing optional tools for full functionality",
                )

            return self._create_result(HealthStatus.OK, "All required tools available", results, duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.ERROR,
                f"Tool check failed: {str(e)}",
                {"error": str(e)},
                duration_ms,
                remediation="Check tool installations and PATH configuration",
            )

    def _check_tools(self) -> Dict[str, Any]:
        """Check tool availability"""
        results = {"required": {}, "optional": {}, "total_available": 0, "total_missing": 0}

        for tool in self.config.required_tools:
            tool_info = self._check_tool(tool)
            results["required"][tool] = tool_info
            if tool_info["available"]:
                results["total_available"] += 1
            else:
                results["total_missing"] += 1

        for tool in self.config.optional_tools:
            tool_info = self._check_tool(tool)
            results["optional"][tool] = tool_info
            if tool_info["available"]:
                results["total_available"] += 1

        return results

    def _check_tool(self, tool_name: str) -> Dict[str, Any]:
        """Check a single tool"""
        result = {"available": False, "path": None, "version": None}

        # Check if tool exists in PATH
        tool_path = shutil.which(tool_name)
        if tool_path:
            result["available"] = True
            result["path"] = tool_path

            # Try to get version
            if tool_name in self.VERSION_COMMANDS:
                cmd, pattern = self.VERSION_COMMANDS[tool_name]
                try:
                    output = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    match = re.search(pattern, output.stdout + output.stderr)
                    if match:
                        result["version"] = match.group(1)
                except Exception:
                    pass

        return result


class APIHealthCheck(BaseHealthCheck):
    """Check API health and response times"""

    name = "api"
    description = "API health and connectivity check"
    severity = SeverityLevel.CRITICAL

    async def run(self) -> HealthCheckResult:
        """Run API health check"""
        start_time = time.time()

        if not self.config.check_api:
            return self._create_result(
                HealthStatus.SKIPPED, "API checks disabled", duration_ms=(time.time() - start_time) * 1000
            )

        try:
            results = await self._run_async(self._check_api)
            duration_ms = (time.time() - start_time) * 1000

            # Determine overall status
            if results["health_endpoint"]["status"] == "error":
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"API health check failed: {results['health_endpoint'].get('error', 'Unknown error')}",
                    results,
                    duration_ms,
                    remediation="Check if API server is running and accessible",
                )

            if results["health_endpoint"].get("response_time_ms", 0) > 5000:
                return self._create_result(
                    HealthStatus.WARNING,
                    "API response time is slow",
                    results,
                    duration_ms,
                    remediation="Consider optimizing API performance or checking network latency",
                )

            if results["auth_status"] == "error":
                return self._create_result(
                    HealthStatus.WARNING,
                    "API authentication check failed",
                    results,
                    duration_ms,
                    remediation="Check API authentication configuration",
                )

            return self._create_result(HealthStatus.OK, "API is healthy", results, duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.ERROR,
                f"API check failed: {str(e)}",
                {"error": str(e)},
                duration_ms,
                remediation="Check API configuration and network connectivity",
            )

    def _check_api(self) -> Dict[str, Any]:
        """Check API health"""
        import urllib.request
        from urllib.error import HTTPError, URLError

        results = {
            "base_url": self.config.api_base_url,
            "health_endpoint": {"status": "unknown", "response_time_ms": 0},
            "auth_status": "unknown",
        }

        # Check health endpoint
        health_url = f"{self.config.api_base_url}/health"
        try:
            start_time = time.time()
            req = urllib.request.Request(health_url, method="GET")
            req.add_header("Accept", "application/json")

            with urllib.request.urlopen(req, timeout=self.config.api_timeout) as response:
                response_time = (time.time() - start_time) * 1000
                results["health_endpoint"]["status"] = "ok"
                results["health_endpoint"]["response_time_ms"] = round(response_time, 2)
                results["health_endpoint"]["status_code"] = response.getcode()

                try:
                    body = response.read().decode("utf-8")
                    results["health_endpoint"]["response"] = json.loads(body)
                except Exception:
                    pass

        except HTTPError as e:
            results["health_endpoint"]["status"] = "error"
            results["health_endpoint"]["error"] = f"HTTP {e.code}: {e.reason}"
        except URLError as e:
            results["health_endpoint"]["status"] = "error"
            results["health_endpoint"]["error"] = str(e.reason)
        except Exception as e:
            results["health_endpoint"]["status"] = "error"
            results["health_endpoint"]["error"] = str(e)

        # Check auth if token provided
        if self.config.api_auth_token:
            me_url = f"{self.config.api_base_url}/auth/me"
            try:
                req = urllib.request.Request(me_url, method="GET")
                req.add_header("Authorization", f"Bearer {self.config.api_auth_token}")
                req.add_header("Accept", "application/json")

                with urllib.request.urlopen(req, timeout=self.config.api_timeout) as response:
                    results["auth_status"] = "ok"
                    results["auth_status_code"] = response.getcode()

            except HTTPError as e:
                if e.code == 401:
                    results["auth_status"] = "unauthorized"
                else:
                    results["auth_status"] = "error"
                    results["auth_error"] = f"HTTP {e.code}: {e.reason}"
            except Exception as e:
                results["auth_status"] = "error"
                results["auth_error"] = str(e)

        return results


class ResourcesHealthCheck(BaseHealthCheck):
    """Check system resources (memory, CPU, disk)"""

    name = "resources"
    description = "System resource usage check"
    severity = SeverityLevel.HIGH

    async def run(self) -> HealthCheckResult:
        """Run resource health check"""
        start_time = time.time()

        if not self.config.check_resources:
            return self._create_result(
                HealthStatus.SKIPPED, "Resource checks disabled", duration_ms=(time.time() - start_time) * 1000
            )

        try:
            results = await self._run_async(self._check_resources)
            duration_ms = (time.time() - start_time) * 1000

            # Determine overall status
            critical_issues = []
            warning_issues = []

            # Memory check
            if results["memory"]["percent"] >= self.config.memory_critical_threshold:
                critical_issues.append(f"Memory usage at {results['memory']['percent']:.1f}%")
            elif results["memory"]["percent"] >= self.config.memory_warning_threshold:
                warning_issues.append(f"Memory usage at {results['memory']['percent']:.1f}%")

            # Disk check
            for disk in results["disks"]:
                if disk["percent"] >= self.config.disk_critical_threshold:
                    critical_issues.append(f"Disk {disk['mountpoint']} at {disk['percent']:.1f}%")
                elif disk["percent"] >= self.config.disk_warning_threshold:
                    warning_issues.append(f"Disk {disk['mountpoint']} at {disk['percent']:.1f}%")

            # CPU check
            if results["cpu"]["percent"] >= self.config.cpu_critical_threshold:
                critical_issues.append(f"CPU usage at {results['cpu']['percent']:.1f}%")
            elif results["cpu"]["percent"] >= self.config.cpu_warning_threshold:
                warning_issues.append(f"CPU usage at {results['cpu']['percent']:.1f}%")

            if critical_issues:
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Critical resource issues: {'; '.join(critical_issues)}",
                    results,
                    duration_ms,
                    remediation="Free up system resources or scale up infrastructure",
                )

            if warning_issues:
                return self._create_result(
                    HealthStatus.WARNING,
                    f"Resource warnings: {'; '.join(warning_issues)}",
                    results,
                    duration_ms,
                    remediation="Monitor resource usage and consider optimization",
                )

            return self._create_result(HealthStatus.OK, "System resources are healthy", results, duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.ERROR,
                f"Resource check failed: {str(e)}",
                {"error": str(e)},
                duration_ms,
                remediation="Check system resource monitoring capabilities",
            )

    def _check_resources(self) -> Dict[str, Any]:
        """Check system resources"""
        results = {
            "memory": {},
            "cpu": {},
            "disks": [],
            "load_average": None,
        }

        # Memory
        memory = psutil.virtual_memory()
        results["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent,
        }

        # CPU
        results["cpu"] = {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        }

        # Disk
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                results["disks"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent,
                })
            except PermissionError:
                continue

        # Load average (Unix only)
        if hasattr(os, "getloadavg"):
            load1, load5, load15 = os.getloadavg()
            results["load_average"] = {
                "1min": round(load1, 2),
                "5min": round(load5, 2),
                "15min": round(load15, 2),
            }

        return results


class SecurityHealthCheck(BaseHealthCheck):
    """Check security configuration"""

    name = "security"
    description = "Security configuration check"
    severity = SeverityLevel.CRITICAL

    # Patterns to detect potential secrets
    SECRET_PATTERNS = {
        "api_key": re.compile(r"api[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", re.IGNORECASE),
        "secret_key": re.compile(r"secret[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", re.IGNORECASE),
        "password": re.compile(r"password\s*[=:]\s*['\"][^'\"\s]{8,}['\"]", re.IGNORECASE),
        "token": re.compile(r"token\s*[=:]\s*['\"][a-zA-Z0-9_-]{16,}['\"]", re.IGNORECASE),
        "private_key": re.compile(r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", re.IGNORECASE),
        "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
        "slack_token": re.compile(r"xox[baprs]-[0-9a-zA-Z-]+"),
    }

    async def run(self) -> HealthCheckResult:
        """Run security health check"""
        start_time = time.time()

        if not self.config.check_security:
            return self._create_result(
                HealthStatus.SKIPPED, "Security checks disabled", duration_ms=(time.time() - start_time) * 1000
            )

        try:
            results = await self._run_async(self._check_security)
            duration_ms = (time.time() - start_time) * 1000

            # Determine overall status
            if results["secrets_found"]:
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Potential secrets found in {len(results['secrets_found'])} files",
                    results,
                    duration_ms,
                    remediation="Remove hardcoded secrets and use environment variables or secure vaults",
                )

            missing_env_vars = [v for v in self.config.required_env_vars if not results["env_vars"].get(v, False)]
            if missing_env_vars:
                return self._create_result(
                    HealthStatus.WARNING,
                    f"Missing required environment variables: {', '.join(missing_env_vars)}",
                    results,
                    duration_ms,
                    remediation=f"Set the following environment variables: {', '.join(missing_env_vars)}",
                )

            expired_certs = [h for h in results["ssl_certs"] if h.get("expired", False)]
            if expired_certs:
                return self._create_result(
                    HealthStatus.CRITICAL,
                    f"Expired SSL certificates: {', '.join(h['host'] for h in expired_certs)}",
                    results,
                    duration_ms,
                    remediation="Renew SSL certificates immediately",
                )

            return self._create_result(HealthStatus.OK, "Security configuration is healthy", results, duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.ERROR,
                f"Security check failed: {str(e)}",
                {"error": str(e)},
                duration_ms,
                remediation="Check security configuration",
            )

    def _check_security(self) -> Dict[str, Any]:
        """Check security configuration"""
        results = {
            "env_vars": {},
            "ssl_certs": [],
            "secrets_found": [],
        }

        # Check environment variables
        for var in self.config.required_env_vars:
            results["env_vars"][var] = bool(os.getenv(var))

        # Check SSL certificates
        for host in self.config.ssl_check_hosts:
            cert_info = self._check_ssl_cert(host)
            results["ssl_certs"].append(cert_info)

        # Scan for secrets
        for path in self.config.secrets_scan_paths:
            secrets = self._scan_for_secrets(path)
            results["secrets_found"].extend(secrets)

        return results

    def _check_ssl_cert(self, host: str) -> Dict[str, Any]:
        """Check SSL certificate for a host"""
        result = {"host": host, "status": "unknown"}

        try:
            # Parse host:port
            if ":" in host:
                hostname, port = host.rsplit(":", 1)
                port = int(port)
            else:
                hostname = host
                port = 443

            context = ssl.create_default_context()
            with context.wrap_socket(ssl.socket(), server_hostname=hostname) as sock:
                sock.settimeout(10)
                sock.connect((hostname, port))
                cert = sock.getpeercert()

                # Parse expiry
                not_after = cert.get("notAfter")
                if not_after:
                    expiry_date = ssl.cert_time_to_seconds(not_after)
                    days_until_expiry = (expiry_date - time.time()) / 86400
                    result["days_until_expiry"] = round(days_until_expiry, 1)
                    result["expired"] = days_until_expiry < 0
                    result["expiring_soon"] = days_until_expiry < 30

                result["subject"] = cert.get("subject")
                result["issuer"] = cert.get("issuer")
                result["status"] = "ok"

        except ssl.SSLError as e:
            result["status"] = "error"
            result["error"] = f"SSL Error: {str(e)}"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _scan_for_secrets(self, path: str) -> List[Dict[str, Any]]:
        """Scan a directory for potential secrets"""
        secrets = []
        base_path = Path(path)

        if not base_path.exists():
            return secrets

        for file_path in base_path.rglob("*.py"):
            # Skip excluded patterns
            if any(pattern in str(file_path) for pattern in self.config.secrets_exclude_patterns):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                for secret_type, pattern in self.SECRET_PATTERNS.items():
                    for match in pattern.finditer(content):
                        # Get line number
                        line_num = content[: match.start()].count("\n") + 1

                        secrets.append({
                            "file": str(file_path),
                            "line": line_num,
                            "type": secret_type,
                            "snippet": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                        })

            except Exception:
                continue

        return secrets


class HealthCheckRunner:
    """Runner for executing health checks"""

    # Registry of available health checks
    CHECKS = {
        "database": DatabaseHealthCheck,
        "tools": ToolsHealthCheck,
        "api": APIHealthCheck,
        "resources": ResourcesHealthCheck,
        "security": SecurityHealthCheck,
    }

    def __init__(self, config: Optional[HealthCheckConfig] = None):
        self.config = config or HealthCheckConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run_all_checks(self, check_names: Optional[List[str]] = None) -> HealthReport:
        """Run all or selected health checks"""
        start_time = time.time()

        # Determine which checks to run
        checks_to_run = check_names or list(self.CHECKS.keys())
        check_classes = {name: self.CHECKS[name] for name in checks_to_run if name in self.CHECKS}

        # Run checks
        results = []
        if self.config.parallel_checks:
            results = await self._run_parallel(check_classes)
        else:
            results = await self._run_sequential(check_classes)

        # Calculate summary
        summary = {"total": len(results), "ok": 0, "warning": 0, "error": 0, "critical": 0, "skipped": 0}

        for result in results:
            summary[result.status.value] += 1

        # Determine overall status
        if summary["critical"] > 0:
            overall_status = HealthStatus.CRITICAL
        elif summary["error"] > 0:
            overall_status = HealthStatus.ERROR
        elif summary["warning"] > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.OK

        duration_ms = (time.time() - start_time) * 1000

        # Build metadata
        metadata = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "runner_version": "1.0.0",
            "config": {
                "check_database": self.config.check_database,
                "check_tools": self.config.check_tools,
                "check_api": self.config.check_api,
                "check_resources": self.config.check_resources,
                "check_security": self.config.check_security,
            },
        }

        return HealthReport(
            overall_status=overall_status,
            checks=results,
            summary=summary,
            metadata=metadata,
            duration_ms=duration_ms,
        )

    async def _run_parallel(self, check_classes: Dict[str, Any]) -> List[HealthCheckResult]:
        """Run checks in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_checks)

        async def run_with_limit(name: str, check_class: Any) -> HealthCheckResult:
            async with semaphore:
                check = check_class(self.config)
                return await check.run()

        tasks = [run_with_limit(name, cls) for name, cls in check_classes.items()]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_sequential(self, check_classes: Dict[str, Any]) -> List[HealthCheckResult]:
        """Run checks sequentially"""
        results = []
        for name, check_class in check_classes.items():
            check = check_class(self.config)
            result = await check.run()
            results.append(result)
        return results

    def run_check(self, check_name: str) -> HealthCheckResult:
        """Run a single health check by name (synchronous wrapper)"""
        if check_name not in self.CHECKS:
            raise ValueError(f"Unknown check: {check_name}")

        check_class = self.CHECKS[check_name]
        check = check_class(self.config)

        try:
            return asyncio.run(check.run())
        except Exception as e:
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.ERROR,
                message=f"Check execution failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                severity=SeverityLevel.CRITICAL,
            )


# Convenience functions for simple usage
def run_health_check(
    config: Optional[HealthCheckConfig] = None,
    check_names: Optional[List[str]] = None,
    json_output: bool = False,
) -> Union[HealthReport, str]:
    """
    Run health checks with optional JSON output

    Args:
        config: Health check configuration
        check_names: List of check names to run (None = all)
        json_output: Return JSON string instead of HealthReport

    Returns:
        HealthReport object or JSON string
    """
    runner = HealthCheckRunner(config)
    report = asyncio.run(runner.run_all_checks(check_names))

    if json_output:
        return report.to_json()
    return report


def check_database(
    database_url: Optional[str] = None, timeout: int = 5
) -> HealthCheckResult:
    """Quick database health check"""
    config = HealthCheckConfig(
        check_database=True,
        database_url=database_url,
        database_timeout=timeout,
        check_tools=False,
        check_api=False,
        check_resources=False,
        check_security=False,
    )
    runner = HealthCheckRunner(config)
    return runner.run_check("database")


def check_tools(required_tools: Optional[List[str]] = None) -> HealthCheckResult:
    """Quick tools health check"""
    config = HealthCheckConfig(
        check_database=False,
        check_tools=True,
        required_tools=required_tools or ["nmap", "sqlmap", "nuclei"],
        check_api=False,
        check_resources=False,
        check_security=False,
    )
    runner = HealthCheckRunner(config)
    return runner.run_check("tools")


def check_api_health(base_url: str = "http://localhost:8000", timeout: int = 10) -> HealthCheckResult:
    """Quick API health check"""
    config = HealthCheckConfig(
        check_database=False,
        check_tools=False,
        check_api=True,
        api_base_url=base_url,
        api_timeout=timeout,
        check_resources=False,
        check_security=False,
    )
    runner = HealthCheckRunner(config)
    return runner.run_check("api")


def check_resources() -> HealthCheckResult:
    """Quick resources health check"""
    config = HealthCheckConfig(
        check_database=False,
        check_tools=False,
        check_api=False,
        check_resources=True,
        check_security=False,
    )
    runner = HealthCheckRunner(config)
    return runner.run_check("resources")


def check_security_config() -> HealthCheckResult:
    """Quick security configuration check"""
    config = HealthCheckConfig(
        check_database=False,
        check_tools=False,
        check_api=False,
        check_resources=False,
        check_security=True,
    )
    runner = HealthCheckRunner(config)
    return runner.run_check("security")


# Exports
__all__ = [
    # Enums
    "HealthStatus",
    "SeverityLevel",
    # Data classes
    "HealthCheckResult",
    "HealthReport",
    # Config
    "HealthCheckConfig",
    # Base class
    "BaseHealthCheck",
    # Specific checks
    "DatabaseHealthCheck",
    "ToolsHealthCheck",
    "APIHealthCheck",
    "ResourcesHealthCheck",
    "SecurityHealthCheck",
    # Runner
    "HealthCheckRunner",
    # Convenience functions
    "run_health_check",
    "check_database",
    "check_tools",
    "check_api_health",
    "check_resources",
    "check_security_config",
]
