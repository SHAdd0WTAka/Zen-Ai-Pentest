"""
Rich TUI - Enhanced terminal interface
Provides beautiful, interactive CLI experience
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.table import Table

console = Console()


@dataclass
class ScanTask:
    """Represents a scanning task"""

    id: str
    name: str
    target: str
    status: str
    progress: float
    start_time: float
    findings: int = 0


class ZenTUI:
    """
    Rich-based Terminal User Interface
    """

    def __init__(self):
        self.console = Console()
        self.tasks: Dict[str, ScanTask] = {}
        self.live: Optional[Live] = None
        self._running = False

    def print_banner(self):
        """Display application banner"""
        banner = """
[bold cyan]        ███████╗███████╗███╗   ██╗[/]
[bold cyan]        ╚══███╔╝██╔════╝████╗  ██║[/]
[bold cyan]          ███╔╝ █████╗  ██╔██╗ ██║[/]  [bold]AI-Powered Penetration Testing[/]
[bold cyan]         ███╔╝  ██╔══╝  ██║╚██╗██║[/]  [dim]Multi-LLM Security Framework[/]
[bold cyan]        ███████╗███████╗██║ ╚████║[/]
[bold cyan]        ╚══════╝╚══════╝╚═╝  ╚═══╝[/]  [dim]v1.0.0 | github.com/SHAdd0WTAka/zen-ai-pentest[/]
        """
        self.console.print(banner)
        self.console.print()

    def show_main_menu(self) -> str:
        """Display main menu and get selection"""
        menu = Table(title="[bold green]Main Menu[/]", box=box.ROUNDED, show_header=False)
        menu.add_column("Option", style="cyan", justify="center")
        menu.add_column("Description", style="white")

        options = [
            ("1", "🎯  New Scan", "Start a new penetration test"),
            ("2", "📊  View Results", "Browse previous scan results"),
            ("3", "🔍  OSINT Tools", "Email/domain reconnaissance"),
            ("4", "⚙️   Configuration", "Settings and API keys"),
            ("5", "📚  Database", "CVE and ransomware lookup"),
            ("6", "🔌  Plugins", "Manage plugin modules"),
            ("7", "❓  Help", "Documentation and examples"),
            ("q", "🚪  Quit", "Exit application"),
        ]

        for opt, label, desc in options:
            menu.add_row(f"[{opt}]", f"{label}\n[dim]{desc}[/]")

        self.console.print(menu)
        self.console.print()

        choice = Prompt.ask(
            "Select option",
            choices=["1", "2", "3", "4", "5", "6", "7", "q"],
            default="1",
        )
        return choice

    def scan_config_wizard(self) -> Dict[str, Any]:
        """Interactive scan configuration wizard"""
        self.console.print(Panel.fit("[bold]New Scan Configuration[/]", border_style="green"))

        # Target input with validation
        while True:
            target = Prompt.ask("[cyan]Target domain/IP[/]")
            if target and "." in target:
                break
            self.console.print("[red]Please enter a valid target[/]")

        # Scan type
        scan_type = Prompt.ask("[cyan]Scan type[/]", choices=["quick", "full", "stealth"], default="quick")

        # Port selection
        port_choice = Prompt.ask(
            "[cyan]Port selection[/]",
            choices=["common", "full", "custom"],
            default="common",
        )

        ports = [80, 443]
        if port_choice == "full":
            ports = list(range(1, 65536))
        elif port_choice == "custom":
            custom = Prompt.ask("Enter ports (comma-separated)")
            ports = [int(p.strip()) for p in custom.split(",") if p.strip().isdigit()]

        # Options
        nuclei = Confirm.ask("[cyan]Run Nuclei vulnerability scan?[/]", default=True)
        osint = Confirm.ask("[cyan]Run OSINT reconnaissance?[/]", default=False)

        config = {
            "target": target,
            "scan_type": scan_type,
            "ports": ports,
            "nuclei": nuclei,
            "osint": osint,
        }

        # Summary
        self.console.print("\n[bold]Configuration Summary:[/]")
        summary = Table(show_header=False, box=box.SIMPLE)
        summary.add_column("Setting", style="cyan")
        summary.add_column("Value", style="white")
        for key, value in config.items():
            summary.add_row(key, str(value))
        self.console.print(summary)

        if Confirm.ask("\nStart scan?", default=True):
            return config
        return None

    def create_progress_bar(self, description: str = "Working..."):
        """Create rich progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            transient=True,
        )

    async def run_scan_with_progress(self, scan_func: Callable, *args, **kwargs) -> Any:
        """Run scan with live progress display"""
        with self.create_progress_bar() as progress:
            task = progress.add_task("[cyan]Initializing scan...", total=None)

            # Update progress messages
            stages = [
                "[cyan]Resolving target...",
                "[yellow]Running port scan...",
                "[yellow]Detecting services...",
                "[yellow]Running vulnerability checks...",
                "[green]Analyzing results...",
                "[green]Generating report...",
            ]

            result = None
            scan_task = asyncio.create_task(scan_func(*args, **kwargs))

            stage_idx = 0
            while not scan_task.done():
                if stage_idx < len(stages):
                    progress.update(task, description=stages[stage_idx])
                    stage_idx += 1
                await asyncio.sleep(2)

            try:
                result = await scan_task
                progress.update(task, description="[bold green]✓ Scan complete!")
            except Exception as e:
                progress.update(task, description=f"[bold red]✗ Error: {e}")
                raise

            return result

    def display_scan_results(self, result: Dict[str, Any]):
        """Display scan results in formatted table"""
        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold]Scan Results: {result.get('target', 'Unknown')}[/]",
                border_style="blue",
            )
        )

        # Summary stats
        stats = result.get("stats", {})
        stats_table = Table(title="Summary", box=box.ROUNDED)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Duration", f"{stats.get('duration', 0):.1f}s")
        stats_table.add_row("Hosts Scanned", str(stats.get("hosts", 0)))
        stats_table.add_row("Services Found", str(stats.get("services", 0)))
        stats_table.add_row("Total Findings", str(stats.get("findings", 0)))

        self.console.print(stats_table)

        # Findings by severity
        findings = result.get("findings", [])
        if findings:
            self.console.print()
            sev_table = Table(title="Findings by Severity", box=box.ROUNDED)
            sev_table.add_column("Severity", style="bold")
            sev_table.add_column("Count", justify="right")

            severity_order = ["critical", "high", "medium", "low", "info"]
            severity_colors = {
                "critical": "red",
                "high": "orange3",
                "medium": "yellow",
                "low": "blue",
                "info": "dim",
            }

            counts = {}
            for f in findings:
                sev = f.get("severity", "info").lower()
                counts[sev] = counts.get(sev, 0) + 1

            for sev in severity_order:
                if sev in counts:
                    color = severity_colors.get(sev, "white")
                    sev_table.add_row(f"[{color}]{sev.upper()}[/{color}]", str(counts[sev]))

            self.console.print(sev_table)

            # Show critical/high findings
            critical = [f for f in findings if f.get("severity") in ["critical", "high"]]
            if critical:
                self.console.print()
                self.console.print("[bold red]Critical/High Findings:[/]")
                for finding in critical[:5]:  # Show first 5
                    self.console.print(
                        Panel(
                            f"[bold]{finding.get('title', 'Unknown')}[/]\n[dim]{finding.get('description', '')[:200]}...[/]",
                            border_style="red",
                        )
                    )

    def confirm(self, message: str, default: bool = False) -> bool:
        """Show confirmation prompt"""
        return Confirm.ask(message, default=default)

    def error(self, message: str):
        """Display error message"""
        self.console.print(f"[bold red]Error:[/] {message}")

    def success(self, message: str):
        """Display success message"""
        self.console.print(f"[bold green]✓[/] {message}")

    def warning(self, message: str):
        """Display warning message"""
        self.console.print(f"[bold yellow]⚠[/] {message}")

    def info(self, message: str):
        """Display info message"""
        self.console.print(f"[dim]ℹ[/] {message}")

    def status_spinner(self, message: str):
        """Get status spinner context manager"""
        return Status(message, console=self.console, spinner="dots")


# Global TUI instance
tui = ZenTUI()
