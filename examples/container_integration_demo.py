#!/usr/bin/env python3
"""
Zen AI Pentest - Container Integration Demo
Demonstrates orchestration of classic pentesting tools
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from modules.tool_orchestrator import ToolOrchestrator

console = Console()


async def demo_integration():
    """
    Demonstrate integration with classic pentesting tools
    """
    bridge_url = "http://localhost:8080"

    console.print(
        Panel.fit(
            "[bold cyan]Zen AI Pentest - Container Integration Demo[/]\n"
            "[dim]Orchestrating classic pentesting tools via Integration Bridge[/]",
            border_style="cyan",
        )
    )

    async with ToolOrchestrator(bridge_url) as orch:
        # Check bridge health
        console.print("\n[bold]1. Checking Integration Bridge...[/]")
        healthy = await orch.health_check()
        if not healthy:
            console.print("[red]✗ Bridge not available![/]")
            console.print(
                "[dim]Make sure to run: docker-compose -f docker-compose.pentest.yml up -d[/]"
            )
            return
        console.print("[green]✓ Bridge is healthy[/]")

        # Example target (use a test target)
        target = "scanme.nmap.org"  # Nmap's official scan target

        console.print(f"\n[bold]2. Target: {target}[/]")
        console.print(
            "[yellow]⚠ Using scanme.nmap.org as safe demo target[/]\n"
        )

        # Run Nmap scan
        console.print("[bold]3. Running Nmap port scan...[/]")
        nmap_result = await orch.scan_with_nmap(
            target=target, scan_type="tcp_syn", ports="top-100"
        )
        console.print(f"   Scan ID: [cyan]{nmap_result['scan_id']}[/]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Scanning ports...", total=None)
            nmap_status = await orch.wait_for_scan(nmap_result["scan_id"])
            progress.update(task, completed=True)

        console.print(f"   Status: [green]{nmap_status['status']}[/]")

        if nmap_status["status"] == "completed":
            nmap_results = await orch.get_scan_results(nmap_result["scan_id"])
            hosts = nmap_results.get("results", {}).get("hosts", [])
            console.print(f"   Found [yellow]{len(hosts)}[/] host(s)")

            for host in hosts[:1]:  # Show first host
                ports = host.get("ports", [])
                open_ports = [p for p in ports if p.get("state") == "open"]
                console.print(f"   Open ports: [green]{len(open_ports)}[/]")
                for port in open_ports[:5]:  # Show first 5
                    console.print(
                        f"     • Port {port['port']}/{port['protocol']}: {port.get('service', 'unknown')}"
                    )

        # Run subdomain enumeration (different target)
        console.print("\n[bold]4. Running Amass subdomain enumeration...[/]")
        domain = "example.com"  # Safe example domain
        amass_result = await orch.enumerate_subdomains(domain, active=False)
        console.print(f"   Scan ID: [cyan]{amass_result['scan_id']}[/]")
        console.print("   [dim](Passive enumeration only)[/]")

        # Web scanning demo
        console.print("\n[bold]5. Running Nuclei vulnerability scan...[/]")
        web_target = (
            "http://testphp.vulnweb.com"  # Intentionally vulnerable test site
        )
        console.print(f"   Target: [dim]{web_target}[/]")

        nuclei_result = await orch.scan_with_nuclei(
            target=web_target, severity="high,critical"
        )
        console.print(f"   Scan ID: [cyan]{nuclei_result['scan_id']}[/]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Scanning for vulnerabilities...", total=None
            )
            nuclei_status = await orch.wait_for_scan(
                nuclei_result["scan_id"], timeout=600
            )
            progress.update(task, completed=True)

        console.print(f"   Status: [green]{nuclei_status['status']}[/]")

        if nuclei_status["status"] == "completed":
            nuclei_results = await orch.get_scan_results(
                nuclei_result["scan_id"]
            )
            findings = nuclei_results.get("results", [])
            console.print(
                f"   Found [yellow]{len(findings)}[/] vulnerability template(s)"
            )

            for finding in findings[:3]:  # Show first 3
                severity = finding.get("info", {}).get("severity", "unknown")
                name = finding.get("info", {}).get("name", "Unknown")
                color = {
                    "critical": "red",
                    "high": "orange3",
                    "medium": "yellow",
                    "low": "blue",
                }.get(severity, "white")
                console.print(f"     [{color}]• {name} ({severity})[/{color}]")

        # Summary table
        console.print("\n[bold]6. Scan Summary[/]")
        table = Table()
        table.add_column("Tool", style="cyan")
        table.add_column("Target", style="white")
        table.add_column("Status", style="green")
        table.add_column("Scan ID", style="dim")

        table.add_row(
            "Nmap", target, nmap_status["status"], nmap_result["scan_id"][:8]
        )
        table.add_row(
            "Amass", domain, "triggered", amass_result["scan_id"][:8]
        )
        table.add_row(
            "Nuclei",
            web_target,
            nuclei_status["status"],
            nuclei_result["scan_id"][:8],
        )

        console.print(table)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"container_demo_results_{timestamp}.json"

        all_results = {
            "timestamp": timestamp,
            "scans": {
                "nmap": {
                    "scan_id": nmap_result["scan_id"],
                    "status": nmap_status["status"],
                    "results": (
                        nmap_results.get("results", {})
                        if nmap_status["status"] == "completed"
                        else None
                    ),
                },
                "nuclei": {
                    "scan_id": nuclei_result["scan_id"],
                    "status": nuclei_status["status"],
                    "results": (
                        nuclei_results.get("results", [])
                        if nuclei_status["status"] == "completed"
                        else None
                    ),
                },
            },
        }

        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2, default=str)

        console.print(f"\n[green]✓ Results saved to: {results_file}[/]")

        console.print(
            Panel.fit(
                "[bold green]Demo completed successfully![/]\n"
                "[dim]To view full results, check the shared volumes or API responses[/]",
                border_style="green",
            )
        )


async def demo_comprehensive_scan():
    """
    Demonstrate comprehensive multi-tool scan
    """
    bridge_url = "http://localhost:8080"

    console.print(
        Panel.fit(
            "[bold cyan]Comprehensive Multi-Tool Scan Demo[/]",
            border_style="cyan",
        )
    )

    target = "scanme.nmap.org"

    async with ToolOrchestrator(bridge_url) as orch:
        console.print(
            f"\n[bold]Running comprehensive network scan against {target}...[/]\n"
        )

        results = await orch.run_comprehensive_scan(
            target=target, scan_type="network"
        )

        orch.display_scan_summary(results)

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = (
            f"comprehensive_scan_{target.replace('.', '_')}_{timestamp}.json"
        )

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        console.print(f"\n[green]✓ Detailed results saved to: {filename}[/]")


def print_usage():
    """Print usage instructions"""
    console.print(
        Panel.fit(
            """
[bold cyan]Container Integration Usage[/]

[bold]1. Start the infrastructure:[/]
   docker-compose -f docker-compose.pentest.yml up -d

[bold]2. Check service health:[/]
   docker-compose -f docker-compose.pentest.yml ps

[bold]3. Run this demo:[/]
   python examples/container_integration_demo.py

[bold]4. Use the CLI:[/]
   python integration/cli.py --help
   python integration/cli.py nmap scanme.nmap.org
   python integration/cli.py amass example.com

[bold]5. Access results:[/]
   - API: http://localhost:8080
   - Web UI: http://localhost:8081
   - Shared volume: ./shared/scans/

[bold]Available Tools:[/]
   • Nmap - Port scanning
   • SQLMap - SQL injection testing
   • Metasploit - Exploitation
   • Nuclei - Vulnerability scanning
   • Gobuster - Directory enumeration
   • Amass - Subdomain discovery
   • WPScan - WordPress scanning
   • Nikto - Web server scanning
    """,
            border_style="blue",
        )
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Zen Container Integration Demo"
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "comprehensive", "usage"],
        default="demo",
        help="Demo mode",
    )

    args = parser.parse_args()

    if args.mode == "usage":
        print_usage()
    elif args.mode == "comprehensive":
        asyncio.run(demo_comprehensive_scan())
    else:
        asyncio.run(demo_integration())
