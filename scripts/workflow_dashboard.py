#!/usr/bin/env python3
"""
GitHub Actions Workflow Status Dashboard

Displays real-time status of all workflows in the repository.
Can be run locally to check workflow health.

Usage:
    python scripts/workflow_dashboard.py
    python scripts/workflow_dashboard.py --watch
    python scripts/workflow_dashboard.py --failed-only
    python scripts/workflow_dashboard.py --save-report workflow_report.json

Environment Variables:
    GITHUB_TOKEN - GitHub personal access token (for private repos)
    GITHUB_REPOSITORY - Repository name (default: auto-detected from git)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Optional: Try to import rich for better formatting
try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


class WorkflowDashboard:
    """Dashboard for monitoring GitHub Actions workflow status."""

    STATUS_ICONS = {
        "success": "✅",
        "failure": "❌",
        "cancelled": "🚫",
        "skipped": "⏭️",
        "in_progress": "🔄",
        "queued": "⏳",
        "waiting": "⏸️",
        "pending": "⏸️",
        "completed": "✓",
        "action_required": "⚠️",
        "neutral": "⚪",
        "stale": "🕐",
        "timed_out": "⏰",
        "unknown": "❓",
    }

    STATUS_COLORS = {
        "success": "green",
        "failure": "red",
        "cancelled": "yellow",
        "skipped": "dim",
        "in_progress": "blue",
        "queued": "cyan",
        "waiting": "yellow",
        "pending": "yellow",
        "completed": "green",
        "action_required": "red",
        "neutral": "white",
        "stale": "dim",
        "timed_out": "red",
        "unknown": "white",
    }

    def __init__(
        self, repo: Optional[str] = None, token: Optional[str] = None
    ):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or self._detect_repo()
        self.workflows_dir = Path(".github/workflows")
        self.workflow_files: list[Path] = []
        self.workflow_status: dict[str, Any] = {}
        self.health_checker = None

    def _detect_repo(self) -> Optional[str]:
        """Detect repository from git remote."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
            # Handle both HTTPS and SSH URLs
            if url.startswith("https://github.com/"):
                return url.replace("https://github.com/", "").replace(
                    ".git", ""
                )
            elif url.startswith("git@github.com:"):
                return url.replace("git@github.com:", "").replace(".git", "")
        except Exception:
            pass
        return os.environ.get("GITHUB_REPOSITORY")

    def _run_gh_command(self, args: list[str]) -> Optional[dict]:
        """Run a GitHub CLI command and return JSON output."""
        try:
            cmd = ["gh"] + args
            env = os.environ.copy()
            if self.token:
                env["GITHUB_TOKEN"] = self.token

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                check=True,
            )
            return json.loads(result.stdout) if result.stdout else {}
        except subprocess.CalledProcessError as e:
            if "gh" in str(e).lower() or "not found" in str(e).lower():
                print(
                    "⚠️ GitHub CLI (gh) not found. Install it from: https://cli.github.com/"
                )
            return None
        except json.JSONDecodeError:
            return None
        except FileNotFoundError:
            print(
                "⚠️ GitHub CLI (gh) not found. Install it from: https://cli.github.com/"
            )
            return None

    def list_workflows(self) -> list[dict]:
        """List all workflows in the repository."""
        if not self.repo:
            print(
                "⚠️ Repository not detected. Set GITHUB_REPOSITORY or run from a git repo."
            )
            return []

        result = self._run_gh_command(
            [
                "api",
                f"/repos/{self.repo}/actions/workflows",
                "--jq",
                ".workflows",
            ]
        )
        return result if result else []

    def get_workflow_runs(
        self, workflow_id: str, limit: int = 5
    ) -> list[dict]:
        """Get recent runs for a workflow."""
        if not self.repo:
            return []

        result = self._run_gh_command(
            [
                "api",
                f"/repos/{self.repo}/actions/workflows/{workflow_id}/runs?per_page={limit}",
                "--jq",
                ".workflow_runs",
            ]
        )
        return result if result else []

    def get_latest_run(self, workflow_id: str) -> Optional[dict]:
        """Get the latest run for a workflow."""
        runs = self.get_workflow_runs(workflow_id, limit=1)
        return runs[0] if runs else None

    def scan_local_workflows(self) -> list[Path]:
        """Scan for workflow files locally."""
        if not self.workflows_dir.exists():
            return []

        self.workflow_files = sorted(
            list(self.workflows_dir.glob("*.yml"))
            + list(self.workflows_dir.glob("*.yaml"))
        )
        return self.workflow_files

    def check_health(self) -> dict:
        """Run health check on workflows."""
        try:
            # Import the health checker
            sys.path.insert(0, str(Path(__file__).parent))
            from workflow_health_check import WorkflowHealthChecker

            checker = WorkflowHealthChecker(str(self.workflows_dir))
            summary = checker.run()

            return {
                "summary": summary,
                "issues": checker.issues,
                "issues_by_workflow": self._group_issues_by_workflow(
                    checker.issues
                ),
            }
        except Exception as e:
            print(f"⚠️ Could not run health check: {e}")
            return {}

    def _group_issues_by_workflow(self, issues: list) -> dict:
        """Group issues by workflow name."""
        grouped = {}
        for issue in issues:
            workflow = issue.get("workflow", "unknown")
            if workflow not in grouped:
                grouped[workflow] = []
            grouped[workflow].append(issue)
        return grouped

    def format_timestamp(self, ts: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60}m ago"
            else:
                return "just now"
        except Exception:
            return ts

    def display_dashboard(
        self, failed_only: bool = False, show_health: bool = True
    ):
        """Display the workflow dashboard."""
        workflows = self.list_workflows()
        local_workflows = self.scan_local_workflows()

        if not workflows and not local_workflows:
            print("⚠️ No workflows found.")
            return

        # Get health check data
        health_data = self.check_health() if show_health else {}
        issues_by_workflow = health_data.get("issues_by_workflow", {})

        if RICH_AVAILABLE:
            self._display_rich_dashboard(
                workflows, local_workflows, issues_by_workflow, failed_only
            )
        else:
            self._display_simple_dashboard(
                workflows, local_workflows, issues_by_workflow, failed_only
            )

    def _display_rich_dashboard(
        self,
        workflows: list,
        local_workflows: list,
        issues_by_workflow: dict,
        failed_only: bool,
    ):
        """Display dashboard using rich formatting."""
        # Header
        console.print()
        console.print(
            Panel.fit(
                f"[bold cyan]GitHub Actions Workflow Dashboard[/bold cyan]\n"
                f"[dim]Repository: {self.repo or 'N/A'}[/dim]",
                border_style="cyan",
            )
        )
        console.print()

        # Summary table
        summary_table = Table(box=box.ROUNDED, title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")

        total_workflows = len(workflows) if workflows else len(local_workflows)
        active_workflows = sum(
            1 for w in workflows if w.get("state") == "active"
        )

        summary_table.add_row("Total Workflows", str(total_workflows))
        summary_table.add_row("Active Workflows", str(active_workflows))
        if health_data := self.check_health():
            summary = health_data.get("summary", {})
            summary_table.add_row(
                "Workflows with Issues",
                str(summary.get("workflows_with_issues", 0)),
            )
            summary_table.add_row(
                "Total Issues", str(summary.get("total_issues", 0))
            )

        console.print(summary_table)
        console.print()

        # Workflows table
        table = Table(box=box.ROUNDED, title="Workflow Status")
        table.add_column("Workflow", style="cyan", min_width=25)
        table.add_column("Status", style="white", width=12)
        table.add_column("Conclusion", style="white", width=12)
        table.add_column("Last Run", style="dim", width=12)
        table.add_column("Branch", style="dim", width=15)
        table.add_column("Health", style="white", width=10)

        for workflow in workflows:
            name = workflow.get("name", workflow.get("path", "Unknown"))
            state = workflow.get("state", "unknown")

            # Get latest run
            latest_run = self.get_latest_run(str(workflow.get("id")))

            if latest_run:
                status = latest_run.get("status", "unknown")
                conclusion = latest_run.get("conclusion", "unknown")
                updated_at = self.format_timestamp(
                    latest_run.get("updated_at", "")
                )
                branch = latest_run.get("head_branch", "-")

                # Skip if filtering for failed only
                if failed_only and conclusion != "failure":
                    continue
            else:
                status = state
                conclusion = "-"
                updated_at = "-"
                branch = "-"

            # Get health status
            workflow_file = Path(workflow.get("path", "")).name
            issues = issues_by_workflow.get(workflow_file, [])
            if issues:
                error_count = sum(
                    1 for i in issues if i.get("severity") == "error"
                )
                warning_count = sum(
                    1 for i in issues if i.get("severity") == "warning"
                )
                health = (
                    f"[red]{error_count}E[/red]/[yellow]{warning_count}W[/yellow]"
                    if error_count
                    else f"[yellow]{warning_count}W[/yellow]"
                )
            else:
                health = "[green]✓[/green]"

            # Format status with icon
            status_icon = self.STATUS_ICONS.get(status, "❓")
            status_color = self.STATUS_COLORS.get(status, "white")
            conclusion_icon = self.STATUS_ICONS.get(conclusion, "")
            conclusion_color = self.STATUS_COLORS.get(conclusion, "white")

            table.add_row(
                name,
                f"[{status_color}]{status_icon} {status}[/{status_color}]",
                (
                    f"[{conclusion_color}]{conclusion_icon} {conclusion}[/{conclusion_color}]"
                    if conclusion != "-"
                    else "-"
                ),
                updated_at,
                branch,
                health,
            )

        console.print(table)
        console.print()

        # Legend
        console.print(
            "[dim]Legend: ✅ Success | ❌ Failure | 🔄 In Progress | ⏳ Queued | 🚫 Cancelled | ⏭️ Skipped[/dim]"
        )
        console.print()

    def _display_simple_dashboard(
        self,
        workflows: list,
        local_workflows: list,
        issues_by_workflow: dict,
        failed_only: bool,
    ):
        """Display dashboard using simple formatting."""
        print("\n" + "=" * 80)
        print("GitHub Actions Workflow Dashboard")
        print(f"Repository: {self.repo or 'N/A'}")
        print("=" * 80)

        total_workflows = len(workflows) if workflows else len(local_workflows)
        print(f"\nTotal Workflows: {total_workflows}")

        if health_data := self.check_health():
            summary = health_data.get("summary", {})
            print(
                f"Workflows with Issues: {summary.get('workflows_with_issues', 0)}"
            )
            print(f"Total Issues: {summary.get('total_issues', 0)}")

        print("\n" + "-" * 80)
        print(
            f"{'Workflow':<30} {'Status':<15} {'Conclusion':<12} {'Last Run':<12} {'Health':<10}"
        )
        print("-" * 80)

        for workflow in workflows:
            name = workflow.get("name", "Unknown")[:28]

            latest_run = self.get_latest_run(str(workflow.get("id")))

            if latest_run:
                status = latest_run.get("status", "unknown")
                conclusion = latest_run.get("conclusion", "-")
                updated_at = self.format_timestamp(
                    latest_run.get("updated_at", "")
                )

                if failed_only and conclusion != "failure":
                    continue
            else:
                status = workflow.get("state", "unknown")
                conclusion = "-"
                updated_at = "-"

            workflow_file = Path(workflow.get("path", "")).name
            issues = issues_by_workflow.get(workflow_file, [])
            if issues:
                error_count = sum(
                    1 for i in issues if i.get("severity") == "error"
                )
                warning_count = sum(
                    1 for i in issues if i.get("severity") == "warning"
                )
                health = f"{error_count}E/{warning_count}W"
            else:
                health = "OK"

            icon = self.STATUS_ICONS.get(
                conclusion if conclusion != "-" else status, "?"
            )
            print(
                f"{icon} {name:<28} {status:<15} {conclusion:<12} {updated_at:<12} {health:<10}"
            )

        print("-" * 80)
        print(
            "\nLegend: ✅ Success | ❌ Failure | 🔄 In Progress | ⏳ Queued | 🚫 Cancelled"
        )

    def generate_report(self) -> dict:
        """Generate a JSON report of workflow status."""
        workflows = self.list_workflows()
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repository": self.repo,
            "workflows": [],
        }

        for workflow in workflows:
            workflow_report = {
                "id": workflow.get("id"),
                "name": workflow.get("name"),
                "path": workflow.get("path"),
                "state": workflow.get("state"),
            }

            latest_run = self.get_latest_run(str(workflow.get("id")))
            if latest_run:
                workflow_report["latest_run"] = {
                    "id": latest_run.get("id"),
                    "status": latest_run.get("status"),
                    "conclusion": latest_run.get("conclusion"),
                    "branch": latest_run.get("head_branch"),
                    "started_at": latest_run.get("run_started_at"),
                    "updated_at": latest_run.get("updated_at"),
                    "url": latest_run.get("html_url"),
                }

            report["workflows"].append(workflow_report)

        # Add health check
        health_data = self.check_health()
        if health_data:
            report["health_check"] = health_data.get("summary", {})
            report["issues"] = health_data.get("issues", [])

        return report

    def watch_mode(self, interval: int = 30):
        """Run dashboard in watch mode."""
        import time

        if not RICH_AVAILABLE:
            print(
                "Watch mode requires 'rich' package. Install with: pip install rich"
            )
            return

        try:
            with console.screen():
                while True:
                    console.clear()
                    self.display_dashboard()
                    console.print(
                        f"\n[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Press Ctrl+C to exit[/dim]"
                    )
                    time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[dim]Exiting watch mode...[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Actions Workflow Status Dashboard"
    )
    parser.add_argument(
        "--repo",
        "-r",
        help="Repository name (owner/repo). Auto-detected if not provided.",
    )
    parser.add_argument(
        "--token",
        "-t",
        help="GitHub token. Can also use GITHUB_TOKEN env var.",
    )
    parser.add_argument(
        "--failed-only",
        "-f",
        action="store_true",
        help="Show only failing workflows",
    )
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Watch mode - auto-refresh every 30 seconds",
    )
    parser.add_argument("--save-report", "-o", help="Save JSON report to file")
    parser.add_argument(
        "--no-health", action="store_true", help="Skip health check (faster)"
    )

    args = parser.parse_args()

    dashboard = WorkflowDashboard(repo=args.repo, token=args.token)

    if args.watch:
        dashboard.watch_mode()
    elif args.save_report:
        report = dashboard.generate_report()
        with open(args.save_report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to {args.save_report}")
    else:
        dashboard.display_dashboard(
            failed_only=args.failed_only, show_health=not args.no_health
        )


if __name__ == "__main__":
    main()
