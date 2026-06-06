#!/usr/bin/env python3
"""
Zen AI Pentest - Interactive TUI
Rich-based interface for real penetration testing workflow
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List

from rich import box

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

console = Console()


class ZenTUI:
    """Interactive Zen AI Pentest TUI"""

    def __init__(self):
        self.target = None
        self.services = []
        self.exploits = []
        self.sessions = []
        self.history = []

    def clear(self):
        """Clear screen"""
        console.clear()

    def banner(self):
        """Show main banner"""
        banner_text = """
        ███████╗███████╗███╗   ██╗    █████╗ ███████╗
        ╚══███╔╝██╔════╝████╗  ██║   ██╔══██╗██╔════╝
          ███╔╝ █████╗  ██╔██╗ ██║   ███████║███████╗
         ███╔╝  ██╔══╝  ██║╚██╗██║   ██╔══██║╚════██║
        ███████╗███████╗██║ ╚████║   ██║  ██║███████║
        ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝  ╚═╝╚══════╝

        🎯 AI-Powered Penetration Testing Platform 🎯
        """
        console.print(Panel(banner_text, style="bold cyan", border_style="cyan"))

    def main_menu(self) -> str:
        """Show main menu and get choice"""
        console.print("\n[bold yellow]Hauptmenü[/bold yellow]\n")

        menu = Table(box=box.ROUNDED, show_header=False)
        menu.add_column("#", style="cyan", justify="center")
        menu.add_column("Aktion", style="green")
        menu.add_column("Beschreibung", style="dim")

        options = [
            (
                "1",
                "🎯 Quick Scan",
                "Ziel scannen → Exploits finden → Analysieren",
            ),
            ("2", "🔍 Service Analyse", "Bekannte Services analysieren"),
            ("3", "💥 Auto-Exploit", "Gefundene Schwachstellen ausnutzen"),
            ("4", "📊 Sessions", "Aktive Sessions verwalten"),
            ("5", "🗂️  History", "Vergangene Scans anzeigen"),
            ("6", "🔧 Werkzeuge", "SearchSploit, CVE Lookup, etc."),
            ("0", "❌ Beenden", "Programm beenden"),
        ]

        for num, action, desc in options:
            menu.add_row(num, action, desc)

        console.print(menu)

        choice = Prompt.ask(
            "\n[bold cyan]Wähle eine Option[/bold cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="1",
        )
        return choice

    def quick_scan(self):
        """Quick scan workflow: Scan → Analyze → Report"""
        self.clear()
        self.banner()
        console.print(
            Panel(
                "[bold yellow]🎯 Quick Scan Workflow[/bold yellow]",
                border_style="yellow",
            )
        )

        # Step 1: Get target
        target = Prompt.ask(
            "[bold green]Ziel-IP oder Hostname[/bold green]",
            default="192.168.1.245",
        )
        self.target = target

        if not Confirm.ask(f"[yellow]Scanne {target}?[/yellow]", default=True):
            return

        # Step 2: Run nmap
        console.print(f"\n[bold cyan]🔍 Starte Portscan auf {target}...[/bold cyan]")

        import tempfile

        xml_fd, xml_file = tempfile.mkstemp(suffix=".xml", prefix="zen_scan_")
        os.close(xml_fd)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Scanne Ports mit nmap...", total=None)

            try:
                subprocess.run(
                    [
                        "nmap",
                        "-sV",
                        "-O",
                        "--top-ports",
                        "100",
                        "-oX",
                        xml_file,
                        target,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]❌ Scan fehlgeschlagen: {e}[/red]")
                return

        # Step 3: Parse results
        console.print("[bold green]✅ Scan abgeschlossen![/bold green]")

        # Parse nmap XML
        services = self._parse_nmap_xml(xml_file)

        if not services:
            console.print("[yellow]⚠️ Keine Services gefunden[/yellow]")
            return

        self.services = services

        # Display results
        self._show_services_table(services)

        # Step 4: Analyze with Zen-AI
        if Confirm.ask(
            "\n[bold yellow]Mit Zen-AI auf Exploits analysieren?[/bold yellow]",
            default=True,
        ):
            self._analyze_services(services)

    def _parse_nmap_xml(self, xml_file: str) -> List[Dict]:
        """Parse nmap XML output"""
        services = []

        try:
            import xml.etree.ElementTree as ET

            # nosec B314: Using defusedxml for safe XML parsing when available
            try:
                from defusedxml import ElementTree as DefusedET

                tree = DefusedET.parse(xml_file)
            except ImportError:
                tree = ET.parse(xml_file)  # nosec B314: Fallback when defusedxml not available
            root = tree.getroot()

            for host in root.findall("host"):
                host_ip = host.find("address").get("addr", "unknown")

                ports_elem = host.find("ports")
                if ports_elem is None:
                    continue

                for port in ports_elem.findall("port"):
                    port_num = int(port.get("portid", 0))
                    protocol = port.get("protocol", "tcp")
                    state = port.find("state")

                    if state is not None and state.get("state") == "open":
                        service_elem = port.find("service")
                        if service_elem is not None:
                            services.append(
                                {
                                    "name": service_elem.get("name", "unknown"),
                                    "port": port_num,
                                    "protocol": protocol,
                                    "version": service_elem.get("version", ""),
                                    "product": service_elem.get("product", ""),
                                    "host": host_ip,
                                }
                            )
        except Exception as e:
            console.print(f"[red]Fehler beim Parsen: {e}[/red]")

        return services

    def _show_services_table(self, services: List[Dict]):
        """Display services in a table"""
        table = Table(title="Gefundene Services", box=box.ROUNDED)
        table.add_column("Port", style="cyan", justify="right")
        table.add_column("Protokoll", style="dim")
        table.add_column("Service", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Produkt", style="blue")

        for svc in services:
            table.add_row(
                str(svc["port"]),
                svc["protocol"],
                svc["name"],
                svc.get("version", "-"),
                svc.get("product", "-")[:30],
            )

        console.print(table)

    def _analyze_services(self, services: List[Dict]):
        """Analyze services with Zen-AI"""
        console.print("\n[bold cyan]🧠 Analysiere Services mit Zen-AI...[/bold cyan]")

        # Save to JSON for processing
        json_fd, json_file = tempfile.mkstemp(suffix=".json", prefix="zen_services_")
        os.close(json_fd)
        with open(json_file, "w") as f:
            json.dump(services, f, indent=2)

        # Run zen_ai_pentest analysis
        try:
            subprocess.run(
                [
                    "python3",
                    "zen_ai_pentest.py",
                    "--analyze-services",
                    json_file,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd="/home/atakan/Zen-Ai-Pentest",
            )

            # Show results
            console.print("[bold green]✅ Analyse abgeschlossen![/bold green]")

            # Parse and display high-confidence matches
            vuln_file = "/home/atakan/Zen-Ai-Pentest/vulnerability_mapping.json"
            if os.path.exists(vuln_file):
                self._show_vulnerability_report(vuln_file)

                if Confirm.ask(
                    "\n[bold red]💥 Auto-Exploit starten?[/bold red]",
                    default=False,
                ):
                    self._auto_exploit(vuln_file)

        except Exception as e:
            console.print(f"[red]❌ Analyse fehlgeschlagen: {e}[/red]")

    def _show_vulnerability_report(self, vuln_file: str):
        """Show vulnerability analysis results"""
        try:
            with open(vuln_file, "r") as f:
                data = json.load(f)

            high_conf = [m for m in data.get("mappings", []) if m.get("confidence_score", 0) >= 0.7]

            if high_conf:
                console.print(f"\n[bold red]🔴 {len(high_conf)} High-Confidence Exploits gefunden![/bold red]")

                table = Table(title="Kritische Schwachstellen", box=box.ROUNDED)
                table.add_column("Port", style="cyan")
                table.add_column("Service", style="green")
                table.add_column("Confidence", style="red")
                table.add_column("Exploits", style="yellow")
                table.add_column("Top Exploit", style="dim")

                for m in high_conf[:10]:
                    svc = m["service"]
                    exploits = m.get("exploits", [])
                    top = exploits[0]["title"][:40] + "..." if exploits else "-"

                    table.add_row(
                        f"{svc['port']}/{svc['protocol']}",
                        f"{svc['name']} {svc.get('version', '')}",
                        f"{m['confidence_score']:.0%}",
                        str(len(exploits)),
                        top,
                    )

                console.print(table)
            else:
                console.print("[yellow]⚠️ Keine high-confidence Exploits gefunden[/yellow]")

        except Exception as e:
            console.print(f"[red]Fehler beim Lesen des Reports: {e}[/red]")

    def _auto_exploit(self, vuln_file: str):
        """Run auto-exploit"""
        console.print("\n[bold red]💥 Starte Auto-Exploit...[/bold red]")
        console.print("[yellow]⚠️  Dry-Run Modus (zeigt nur was passieren würde)[/yellow]\n")

        try:
            result = subprocess.run(
                [
                    "python3",
                    "zen_ai_pentest.py",
                    "--msf-auto",
                    f"{self.target}:{vuln_file}",
                    "--msf-dry-run",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd="/home/atakan/Zen-Ai-Pentest",
            )

            # Parse and show results
            output = result.stdout + result.stderr

            # Show successful exploits
            if "Would execute" in output:
                console.print("[bold green]✅ Folgende Exploits würden ausgeführt:[/bold green]\n")

                for line in output.split("\n"):
                    if "Would execute" in line:
                        exploit = line.split("Would execute:")[1].strip()
                        console.print(f"  [cyan]→[/cyan] {exploit}")

            if Confirm.ask(
                "\n[bold red]🔴 LIVE ausführen? (Achtung: Nur auf autorisierten Systemen!)[/bold red]",
                default=False,
            ):
                console.print("[bold red]🔥 Führe Exploits LIVE aus...[/bold red]")

                # Run without dry-run
                result = subprocess.run(
                    [
                        "python3",
                        "zen_ai_pentest.py",
                        "--msf-auto",
                        f"{self.target}:{vuln_file}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd="/home/atakan/Zen-Ai-Pentest",
                )

                console.print(result.stdout)

        except Exception as e:
            console.print(f"[red]❌ Exploit fehlgeschlagen: {e}[/red]")

    def service_analysis(self):
        """Manual service analysis"""
        self.clear()
        self.banner()
        console.print(
            Panel(
                "[bold yellow]🔍 Service Analyse[/bold yellow]",
                border_style="yellow",
            )
        )

        # Manual service input
        console.print("[cyan]Gib Services ein (Format: name:port:version)[/cyan]")
        console.print("[dim]Beispiel: vsftpd:21:2.3.4[/dim]")
        console.print("[dim]Leere Zeile = Fertig[/dim]\n")

        services = []
        while True:
            line = Prompt.ask("[green]Service[/green]", default="")
            if not line:
                break

            parts = line.split(":")
            if len(parts) >= 2:
                services.append(
                    {
                        "name": parts[0],
                        "port": int(parts[1]),
                        "version": parts[2] if len(parts) > 2 else "",
                        "protocol": "tcp",
                    }
                )

        if services:
            self._show_services_table(services)
            self._analyze_services(services)

    def tools_menu(self):
        """Tools submenu"""
        self.clear()
        self.banner()
        console.print(
            Panel(
                "[bold yellow]🔧 Werkzeuge[/bold yellow]",
                border_style="yellow",
            )
        )

        tools = Table(box=box.ROUNDED)
        tools.add_column("#", style="cyan")
        tools.add_column("Tool", style="green")
        tools.add_column("Beschreibung", style="dim")

        tools.add_row("1", "SearchSploit", "Exploit-DB durchsuchen")
        tools.add_row("2", "CVE Lookup", "Exploits zu CVE finden")
        tools.add_row("3", "Metasploit Sessions", "Aktive Sessions anzeigen")
        tools.add_row("4", "Nmap Quick", "Schneller Portscan")
        tools.add_row("0", "Zurück", "Hauptmenü")

        console.print(tools)

        choice = Prompt.ask(
            "[bold cyan]Tool wählen[/bold cyan]",
            choices=["0", "1", "2", "3", "4"],
        )

        if choice == "1":
            query = Prompt.ask("[green]Suchbegriff[/green]", default="wordpress sql injection")
            self._run_searchsploit(query)
        elif choice == "2":
            cve = Prompt.ask("[green]CVE[/green]", default="CVE-2011-2523")
            self._run_cve_lookup(cve)
        elif choice == "3":
            self._show_sessions()
        elif choice == "4":
            target = Prompt.ask("[green]Ziel[/green]", default=self.target or "192.168.1.245")
            self._quick_nmap(target)

    def _run_searchsploit(self, query: str):
        """Run SearchSploit query"""
        console.print(f"\n[bold cyan]🔍 Suche nach: {query}[/bold cyan]")

        try:
            result = subprocess.run(
                ["python3", "zen_ai_pentest.py", "--search-exploit", query],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/home/atakan/Zen-Ai-Pentest",
            )

            # Parse and show results
            output = result.stdout + result.stderr

            # Extract exploits
            exploits = []
            for line in output.split("\n"):
                if "EDB-" in line and "Found" not in line:
                    exploits.append(line.strip())

            if exploits:
                console.print(f"[bold green]✅ {len(exploits)} Exploits gefunden[/bold green]\n")
                for exp in exploits[:10]:
                    console.print(f"  [yellow]{exp}[/yellow]")
            else:
                console.print(output)

        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")

    def _run_cve_lookup(self, cve: str):
        """Run CVE lookup"""
        console.print(f"\n[bold cyan]🔍 Suche nach: {cve}[/bold cyan]")

        try:
            result = subprocess.run(
                ["python3", "zen_ai_pentest.py", "--search-cve", cve],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/home/atakan/Zen-Ai-Pentest",
            )

            output = result.stdout + result.stderr

            if "Found" in output:
                for line in output.split("\n"):
                    if "EDB-" in line or "Verified" in line:
                        console.print(f"[green]{line}[/green]")
            else:
                console.print("[yellow]Keine Exploits gefunden[/yellow]")

        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")

    def _show_sessions(self):
        """Show Metasploit sessions"""
        console.print("\n[bold cyan]📊 Metasploit Sessions[/bold cyan]")

        try:
            result = subprocess.run(
                ["python3", "zen_ai_pentest.py", "--msf-sessions"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/home/atakan/Zen-Ai-Pentest",
            )

            console.print(result.stdout)

        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")

    def _quick_nmap(self, target: str):
        """Quick nmap scan"""
        console.print(f"\n[bold cyan]🔍 Quick Scan: {target}[/bold cyan]")

        try:
            result = subprocess.run(
                ["nmap", "-F", target],
                capture_output=True,
                text=True,
                timeout=60,
            )

            console.print(Syntax(result.stdout, "bash", theme="monokai"))

        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")

    def show_history(self):
        """Show scan history"""
        self.clear()
        self.banner()
        console.print(
            Panel(
                "[bold yellow]🗂️  Scan History[/bold yellow]",
                border_style="yellow",
            )
        )

        # Look for previous scan files
        scan_files = list(Path("/tmp").glob("zen_*_*.*"))  # nosec B108: Searching for existing temp files only

        if scan_files:
            table = Table(box=box.ROUNDED)
            table.add_column("Datum", style="cyan")
            table.add_column("Datei", style="green")
            table.add_column("Typ", style="yellow")

            for f in sorted(scan_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
                ftype = "XML" if f.suffix == ".xml" else "JSON"
                table.add_row(mtime, f.name, ftype)

            console.print(table)
        else:
            console.print("[yellow]Keine History gefunden[/yellow]")

    def run(self):
        """Main TUI loop"""
        try:
            while True:
                self.clear()
                self.banner()

                # Show current status
                if self.target:
                    status = f"[bold green]Target: {self.target}[/bold green]"
                    if self.services:
                        status += f" | [bold yellow]{len(self.services)} Services[/bold yellow]"
                    console.print(Panel(status, border_style="green"))

                choice = self.main_menu()

                if choice == "0":
                    console.print("\n[bold cyan]👋 Auf Wiedersehen![/bold cyan]")
                    break
                elif choice == "1":
                    self.quick_scan()
                    Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")
                elif choice == "2":
                    self.service_analysis()
                    Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")
                elif choice == "3":
                    vuln_file = "/home/atakan/Zen-Ai-Pentest/vulnerability_mapping.json"
                    if os.path.exists(vuln_file):
                        self._auto_exploit(vuln_file)
                    else:
                        console.print("[red]❌ Keine Analyse gefunden. Bitte zuerst scannen.[/red]")
                    Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")
                elif choice == "4":
                    self._show_sessions()
                    Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")
                elif choice == "5":
                    self.show_history()
                    Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")
                elif choice == "6":
                    self.tools_menu()
                    Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")

        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]👋 Auf Wiedersehen![/bold cyan]")


def main():
    """Entry point"""
    tui = ZenTUI()
    tui.run()


if __name__ == "__main__":
    main()
