#!/usr/bin/env python3
"""
Health Check CLI for Zen-AI-Pentest

Command-line tool for running health checks and monitoring system health.
Supports multiple output formats and CI/CD integration.

Usage:
    python scripts/health_check_cli.py                    # Run all checks
    python scripts/health_check_cli.py --check database   # Run database check only
    python scripts/health_check_cli.py --format json      # Output as JSON
    python scripts/health_check_cli.py --ci               # CI/CD mode (exit non-zero on issues)
    python scripts/health_check_cli.py --config config.yml # Use custom config

Exit Codes:
    0 - All checks passed (OK)
    1 - Some checks failed (WARNING/ERROR/CRITICAL)
    2 - CLI error or exception

Author: Zen-AI-Pentest Team
License: MIT
Version: 1.0.0
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.health_check import (
    HealthCheckConfig,
    HealthCheckRunner,
    HealthReport,
    HealthStatus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("health_check_cli")


class Colors:
    """Terminal colors for output"""

    OK = "\033[92m"  # Green
    WARNING = "\033[93m"  # Yellow
    ERROR = "\033[91m"  # Red
    CRITICAL = "\033[91m\033[1m"  # Bold Red
    INFO = "\033[94m"  # Blue
    RESET = "\033[0m"  # Reset
    BOLD = "\033[1m"
    DIM = "\033[2m"


class HealthCheckCLI:
    """Health Check CLI Application"""

    # Status to color mapping
    STATUS_COLORS = {
        HealthStatus.OK: Colors.OK,
        HealthStatus.WARNING: Colors.WARNING,
        HealthStatus.ERROR: Colors.ERROR,
        HealthStatus.CRITICAL: Colors.CRITICAL,
        HealthStatus.SKIPPED: Colors.DIM,
    }

    # Status to icon mapping
    STATUS_ICONS = {
        HealthStatus.OK: "✓",
        HealthStatus.WARNING: "⚠",
        HealthStatus.ERROR: "✗",
        HealthStatus.CRITICAL: "✗",
        HealthStatus.SKIPPED: "○",
    }

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors and sys.stdout.isatty()

    def colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if self.use_colors:
            return f"{color}{text}{Colors.RESET}"
        return text

    def print_banner(self):
        """Print CLI banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║              🔍 Zen-AI-Pentest Health Check 🔍               ║
║              System Health & Readiness Monitor               ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(self.colorize(banner, Colors.INFO))

    def print_status_line(
        self, name: str, status: HealthStatus, message: str, duration_ms: float
    ):
        """Print a formatted status line"""
        color = self.STATUS_COLORS.get(status, Colors.RESET)
        icon = self.STATUS_ICONS.get(status, "?")
        status_text = status.value.upper()

        name_padded = name.ljust(15)
        status_padded = self.colorize(f"{icon} {status_text}", color).ljust(20)
        duration_str = f"({duration_ms:.0f}ms)" if duration_ms > 0 else ""

        print(
            f"  {name_padded} {status_padded} {message} {Colors.DIM}{duration_str}{Colors.RESET}"
        )

    def print_check_details(self, check, verbose: bool = False):
        """Print detailed check information"""
        if not verbose and check.status == HealthStatus.OK:
            return

        # Print details if available
        if check.details:
            if "error" in check.details:
                print(
                    f"    {self.colorize('Error:', Colors.ERROR)} {check.details['error']}"
                )

            # Tool check details
            if "required" in check.details and "optional" in check.details:
                for tool_name, tool_info in check.details["required"].items():
                    status = "✓" if tool_info["available"] else "✗"
                    tool_color = (
                        Colors.OK if tool_info["available"] else Colors.ERROR
                    )
                    version = (
                        f"v{tool_info['version']}"
                        if tool_info.get("version")
                        else ""
                    )
                    print(
                        f"      {self.colorize(status, tool_color)} {tool_name} {Colors.DIM}{version}{Colors.RESET}"
                    )

            # Resource check details
            if "memory" in check.details:
                mem = check.details["memory"]
                used = mem.get("used_gb", 0)
                total = mem.get("total_gb", 0)
                pct = mem.get("percent", 0)
                print(f"    Memory: {used:.1f}GB / {total:.1f}GB ({pct:.0f}%)")

            if "cpu" in check.details:
                cpu = check.details["cpu"]
                print(f"    CPU: {cpu.get('percent', 0):.0f}%")

            if "disks" in check.details:
                for disk in check.details["disks"]:
                    mount = disk.get("mountpoint", "unknown")
                    pct = disk.get("percent", 0)
                    print(f"    Disk {mount}: {pct:.0f}% used")

            # Security check details
            if check.name == "security":
                if check.details.get("secrets_found"):
                    print(
                        f"    {self.colorize('⚠ Secrets found:', Colors.WARNING)}"
                    )
                    for secret in check.details["secrets_found"][
                        :5
                    ]:  # Show first 5
                        file = secret.get("file", "unknown")
                        line = secret.get("line", 0)
                        secret_type = secret.get("type", "unknown")
                        print(f"      - {file}:{line} ({secret_type})")

                if check.details.get("env_vars"):
                    missing = [
                        k
                        for k, v in check.details["env_vars"].items()
                        if not v
                    ]
                    if missing:
                        print(
                            f"    {self.colorize('Missing env vars:', Colors.WARNING)} {', '.join(missing)}"
                        )

        # Print remediation if available
        if check.remediation and check.status != HealthStatus.OK:
            print(
                f"    {self.colorize('💡 Remediation:', Colors.INFO)} {check.remediation}"
            )

        print()

    def print_summary(self, report: HealthReport):
        """Print report summary"""
        print("\n" + "=" * 60)
        print(self.colorize("SUMMARY", Colors.BOLD))
        print("=" * 60)

        summary = report.summary
        status_color = self.STATUS_COLORS.get(
            report.overall_status, Colors.RESET
        )

        print(
            f"\nOverall Status: {self.colorize(report.overall_status.value.upper(), status_color)}"
        )
        print("\nChecks:")
        print(f"  Total:     {summary['total']}")
        print(f"  {self.colorize('OK:', Colors.OK)}        {summary['ok']}")
        print(
            f"  {self.colorize('Warning:', Colors.WARNING)}  {summary['warning']}"
        )
        print(
            f"  {self.colorize('Error:', Colors.ERROR)}     {summary['error']}"
        )
        print(
            f"  {self.colorize('Critical:', Colors.CRITICAL)} {summary['critical']}"
        )
        print(
            f"  {self.colorize('Skipped:', Colors.DIM)}   {summary['skipped']}"
        )

        print(f"\nDuration: {report.duration_ms:.0f}ms")
        print(
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def print_json(self, report: HealthReport, pretty: bool = True):
        """Print report as JSON"""
        indent = 2 if pretty else None
        print(report.to_json(indent=indent))

    def print_markdown(self, report: HealthReport):
        """Print report as Markdown"""
        print("# Zen-AI-Pentest Health Check Report\n")
        print(
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"**Overall Status:** {report.overall_status.value.upper()}\n")

        print("## Summary\n")
        print("| Status | Count |")
        print("|--------|-------|")
        print(f"| OK | {report.summary['ok']} |")
        print(f"| Warning | {report.summary['warning']} |")
        print(f"| Error | {report.summary['error']} |")
        print(f"| Critical | {report.summary['critical']} |")
        print(f"| Skipped | {report.summary['skipped']} |")
        print(f"| **Total** | **{report.summary['total']}** |\n")

        print("## Checks\n")
        for check in report.checks:
            icon = self.STATUS_ICONS.get(check.status, "?")
            print(f"### {icon} {check.name}\n")
            print(f"- **Status:** {check.status.value.upper()}")
            print(f"- **Message:** {check.message}")
            print(f"- **Duration:** {check.duration_ms:.0f}ms")

            if check.remediation:
                print(f"- **Remediation:** {check.remediation}")

            if check.details:
                print("\n**Details:**")
                print("```json")
                print(json.dumps(check.details, indent=2, default=str))
                print("```")

            print()

    def print_csv(self, report: HealthReport):
        """Print report as CSV"""
        print("name,status,message,duration_ms,severity,timestamp")
        for check in report.checks:
            print(
                f'{check.name},{check.status.value},"{check.message}",{check.duration_ms},{check.severity.name},{check.timestamp.isoformat()}'
            )

    def run(
        self,
        checks: Optional[List[str]] = None,
        config: Optional[HealthCheckConfig] = None,
        format_type: str = "text",
        verbose: bool = False,
        quiet: bool = False,
    ) -> int:
        """
        Run health checks and display results

        Args:
            checks: List of specific checks to run (None = all)
            config: Health check configuration
            format_type: Output format (text, json, markdown, csv)
            verbose: Show verbose output
            quiet: Suppress non-essential output

        Returns:
            Exit code (0 for OK, 1 for issues, 2 for errors)
        """
        import asyncio

        config = config or HealthCheckConfig()
        runner = HealthCheckRunner(config)

        try:
            if not quiet and format_type == "text":
                self.print_banner()
                print("Running health checks...\n")

            # Run checks
            report = asyncio.run(runner.run_all_checks(checks))

            if not quiet and format_type == "text":
                print(f"Completed in {report.duration_ms:.0f}ms\n")
                print("=" * 60)
                print(self.colorize("CHECK RESULTS", Colors.BOLD))
                print("=" * 60 + "\n")

                for check in report.checks:
                    self.print_status_line(
                        check.name,
                        check.status,
                        check.message,
                        check.duration_ms,
                    )
                    self.print_check_details(check, verbose)

                self.print_summary(report)

            elif format_type == "json":
                self.print_json(report, pretty=not quiet)

            elif format_type == "markdown":
                self.print_markdown(report)

            elif format_type == "csv":
                self.print_csv(report)

            # Determine exit code
            if report.overall_status == HealthStatus.OK:
                return 0
            else:
                return 1

        except KeyboardInterrupt:
            if not quiet:
                print("\n\nInterrupted by user")
            return 130
        except Exception as e:
            if not quiet:
                print(f"\n{self.colorize('Error:', Colors.ERROR)} {e}")
            logger.exception("Health check failed")
            return 2


def load_config_from_file(config_path: str) -> HealthCheckConfig:
    """Load configuration from a JSON or YAML file"""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    content = path.read_text()

    # Try JSON first
    try:
        data = json.loads(content)
        return HealthCheckConfig(**data)
    except json.JSONDecodeError:
        pass

    # Try YAML
    try:
        import yaml

        data = yaml.safe_load(content)
        return HealthCheckConfig(**data)
    except ImportError:
        raise ValueError("YAML config requires PyYAML: pip install pyyaml")
    except Exception as e:
        raise ValueError(f"Failed to parse config file: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog="health_check_cli.py",
        description="Zen-AI-Pentest Health Check System - Monitor system health and readiness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all health checks
  python scripts/health_check_cli.py

  # Run specific checks only
  python scripts/health_check_cli.py --check database --check tools

  # Output as JSON for CI/CD integration
  python scripts/health_check_cli.py --format json --ci

  # Check API health at specific URL
  python scripts/health_check_cli.py --check api --api-url http://api.example.com:8000

  # Use custom configuration
  python scripts/health_check_cli.py --config myconfig.json

  # Quiet mode for scripts
  python scripts/health_check_cli.py --format json --quiet

Exit Codes:
  0  - All checks passed
  1  - Some checks failed (WARNING/ERROR/CRITICAL)
  2  - CLI error or exception
        """,
    )

    # Check selection
    parser.add_argument(
        "--check",
        "-c",
        action="append",
        choices=["database", "tools", "api", "resources", "security"],
        help="Specific check to run (can be specified multiple times)",
    )

    # Output options
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "markdown", "csv"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output including check details",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress non-essential output",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    # CI/CD options
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD mode: exit non-zero on any issues, output JSON",
    )

    # Configuration options
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON or YAML)",
    )

    # Database options
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database URL override",
    )

    parser.add_argument(
        "--skip-database",
        action="store_true",
        help="Skip database health checks",
    )

    # Tool options
    parser.add_argument(
        "--skip-tools",
        action="store_true",
        help="Skip tool availability checks",
    )

    # API options
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip API health checks",
    )

    # Resource options
    parser.add_argument(
        "--skip-resources",
        action="store_true",
        help="Skip resource usage checks",
    )

    # Security options
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip security configuration checks",
    )

    # Other options
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per check in seconds (default: 30)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    return parser


def main() -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # CI mode overrides
    if args.ci:
        args.format = "json"
        args.quiet = True

    # Load or create config
    if args.config:
        try:
            config = load_config_from_file(args.config)
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return 2
    else:
        config = HealthCheckConfig(
            check_database=not args.skip_database,
            check_tools=not args.skip_tools,
            check_api=not args.skip_api,
            api_base_url=args.api_url,
            check_resources=not args.skip_resources,
            check_security=not args.skip_security,
            database_url=args.database_url,
            timeout_per_check=args.timeout,
        )

    # Create CLI and run
    cli = HealthCheckCLI(use_colors=not args.no_color)
    exit_code = cli.run(
        checks=args.check,
        config=config,
        format_type=args.format,
        verbose=args.verbose,
        quiet=args.quiet,
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
