#!/usr/bin/env python3
"""
Zen Pentest Integration CLI
Command-line interface for orchestrating classic pentesting tools
"""

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.tool_orchestrator import PENTEST_TOOLS, ToolOrchestrator

console = Console()


@click.group()
@click.option(
    "--bridge", default="http://localhost:8080", help="Integration Bridge URL"
)
@click.pass_context
def cli(ctx, bridge):
    """Zen Pentest Integration CLI - Orchestrate classic tools"""
    ctx.ensure_object(dict)
    ctx.obj["bridge_url"] = bridge


@cli.command()
@click.pass_context
def tools(ctx):
    """List available tools"""
    console.print(Panel.fit("[bold cyan]Available Pentesting Tools[/]"))

    for name, config in PENTEST_TOOLS.items():
        console.print(f"\n[bold green]{name}[/]")
        console.print(f"  [dim]{config.description}[/]")
        console.print(f"  Endpoint: {config.bridge_endpoint}")
        console.print(f"  Duration: ~{config.typical_duration}s")


@cli.command()
@click.argument("target")
@click.option(
    "--type",
    "scan_type",
    default="tcp_syn",
    type=click.Choice(["tcp_syn", "tcp_connect", "udp", "comprehensive"]),
)
@click.option("--ports", default="top-1000", help="Port specification")
@click.option("--wait/--no-wait", default=True, help="Wait for completion")
@click.pass_context
def nmap(ctx, target, scan_type, ports, wait):
    """Run Nmap port scan"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            console.print(
                f"[bold]Starting Nmap {scan_type} scan against {target}...[/]"
            )

            result = await orch.scan_with_nmap(
                target, scan_type=scan_type, ports=ports
            )
            scan_id = result["scan_id"]

            console.print(f"Scan ID: [cyan]{scan_id}[/]")

            if wait:
                console.print("Waiting for completion...")
                status = await orch.wait_for_scan(scan_id)
                console.print(f"Status: [green]{status['status']}[/]")

                if status["status"] == "completed":
                    results = await orch.get_scan_results(scan_id)
                    console.print(JSON(json.dumps(results, indent=2)))

    asyncio.run(run())


@cli.command()
@click.argument("url")
@click.option("--level", default=1, type=int, help="Test level (1-5)")
@click.option("--risk", default=1, type=int, help="Risk level (1-3)")
@click.option("--wait/--no-wait", default=True, help="Wait for completion")
@click.pass_context
def sqlmap(ctx, url, level, risk, wait):
    """Run SQLMap scan"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            console.print(f"[bold]Starting SQLMap scan against {url}...[/]")

            result = await orch.scan_with_sqlmap(url, level=level, risk=risk)
            scan_id = result["scan_id"]

            console.print(f"Scan ID: [cyan]{scan_id}[/]")

            if wait:
                console.print(
                    "Waiting for completion... (this may take a while)"
                )
                status = await orch.wait_for_scan(scan_id, timeout=7200)
                console.print(f"Status: [green]{status['status']}[/]")

    asyncio.run(run())


@cli.command()
@click.argument("target")
@click.option(
    "--severity", help="Filter by severity (info, low, medium, high, critical)"
)
@click.option("--wait/--no-wait", default=True, help="Wait for completion")
@click.pass_context
def nuclei(ctx, target, severity, wait):
    """Run Nuclei vulnerability scan"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            console.print(f"[bold]Starting Nuclei scan against {target}...[/]")

            result = await orch.scan_with_nuclei(target, severity=severity)
            scan_id = result["scan_id"]

            console.print(f"Scan ID: [cyan]{scan_id}[/]")

            if wait:
                console.print("Waiting for completion...")
                status = await orch.wait_for_scan(scan_id, timeout=1800)
                console.print(f"Status: [green]{status['status']}[/]")

                if status["status"] == "completed":
                    results = await orch.get_scan_results(scan_id)
                    console.print(JSON(json.dumps(results, indent=2)))

    asyncio.run(run())


@cli.command()
@click.argument("url")
@click.option(
    "--wordlist", default="/wordlists/dirb/common.txt", help="Wordlist path"
)
@click.option("--extensions", help="File extensions (e.g., php,txt,html)")
@click.pass_context
def gobuster(ctx, url, wordlist, extensions):
    """Run Gobuster directory scan"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            console.print(f"[bold]Starting Gobuster scan against {url}...[/]")

            result = await orch.scan_with_gobuster(
                url, wordlist=wordlist, extensions=extensions
            )
            scan_id = result["scan_id"]

            console.print(f"Scan ID: [cyan]{scan_id}[/]")
            console.print("Waiting for completion...")

            status = await orch.wait_for_scan(scan_id, timeout=600)
            console.print(f"Status: [green]{status['status']}[/]")

    asyncio.run(run())


@cli.command()
@click.argument("domain")
@click.option(
    "--active/--passive", default=False, help="Active reconnaissance"
)
@click.pass_context
def amass(ctx, domain, active):
    """Enumerate subdomains with Amass"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            mode = "active" if active else "passive"
            console.print(
                f"[bold]Starting Amass {mode} enumeration for {domain}...[/]"
            )

            result = await orch.enumerate_subdomains(domain, active=active)
            scan_id = result["scan_id"]

            console.print(f"Scan ID: [cyan]{scan_id}[/]")
            console.print(
                "Waiting for completion... (this may take several minutes)"
            )

            status = await orch.wait_for_scan(scan_id, timeout=3600)
            console.print(f"Status: [green]{status['status']}[/]")

            if status["status"] == "completed":
                results = await orch.get_scan_results(scan_id)
                subdomains = results.get("results", [])
                console.print(
                    f"\n[bold]Found {len(subdomains)} subdomains:[/]"
                )
                for subdomain in subdomains[:20]:  # Show first 20
                    console.print(f"  • {subdomain}")
                if len(subdomains) > 20:
                    console.print(f"  ... and {len(subdomains) - 20} more")

    asyncio.run(run())


@cli.command()
@click.argument("target")
@click.option(
    "--type",
    "scan_type",
    default="web",
    type=click.Choice(["web", "network", "full"]),
)
@click.pass_context
def comprehensive(ctx, target, scan_type):
    """Run comprehensive multi-tool scan"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            results = await orch.run_comprehensive_scan(target, scan_type)
            orch.display_scan_summary(results)

            # Save results
            output_file = (
                f"scan_results_{target.replace('/', '_')}_{scan_type}.json"
            )
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"\n[green]Results saved to: {output_file}[/]")

    asyncio.run(run())


@cli.command()
@click.argument("scan_id")
@click.pass_context
def status(ctx, scan_id):
    """Check scan status"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            status = await orch.get_scan_status(scan_id)
            console.print(JSON(json.dumps(status, indent=2, default=str)))

    asyncio.run(run())


@cli.command()
@click.argument("scan_id")
@click.pass_context
def results(ctx, scan_id):
    """Get scan results"""
    bridge_url = ctx.obj["bridge_url"]

    async def run():
        async with ToolOrchestrator(bridge_url) as orch:
            scan_results = await orch.get_scan_results(scan_id)
            console.print(
                JSON(json.dumps(scan_results, indent=2, default=str))
            )

    asyncio.run(run())


if __name__ == "__main__":
    cli()
