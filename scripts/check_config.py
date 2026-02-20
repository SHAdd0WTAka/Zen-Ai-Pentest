#!/usr/bin/env python3
"""
Prüft ob Zen-AI Pentest korrekt konfiguriert ist
Jeder Benutzer muss seine eigenen API Keys konfigurieren!
"""

import re
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check_config():
    env_path = Path(__file__).parent.parent / ".env"

    console.print(Panel.fit("Zen-AI Pentest - Konfigurations-Check", title="Setup", border_style="cyan"))

    # Prüfe ob .env existiert
    if not env_path.exists():
        console.print("[yellow].env Datei nicht gefunden![/yellow]")
        console.print("\n[bold]Erstmalige Einrichtung:[/bold]")
        console.print("  python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k YOUR_KEY")
        return False

    with open(env_path, "r") as f:
        content = f.read()

    # Extrahiere Konfiguration
    config = {}
    for match in re.finditer(r'export (\w+)="([^"]*)"', content):
        config[match.group(1)] = match.group(2)

    # Erstelle Status-Tabelle
    table = Table(title="API Konfiguration", show_header=True)
    table.add_column("Backend", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Modell", style="dim")

    backends = [
        ("Kimi", "KIMI_API_KEY", "DEFAULT_BACKEND", "kimi"),
        ("OpenRouter", "OPENROUTER_API_KEY", "DEFAULT_BACKEND", "openrouter"),
        ("OpenAI", "OPENAI_API_KEY", "DEFAULT_BACKEND", "openai"),
    ]

    has_valid_key = False
    default_backend = config.get("DEFAULT_BACKEND", "")
    default_model = config.get("DEFAULT_MODEL", "nicht gesetzt")

    for name, key_var, _, backend_id in backends:
        key = config.get(key_var, "")
        is_default = default_backend == backend_id

        # Prüfe ob Key valide aussieht (nicht leer, nicht dummy)
        is_dummy = key in ["", "test-key-12345", "your-api-key", "xxx", "sk-xxx"]

        if key and not is_dummy and len(key) > 20:
            status = "[green]Konfiguriert"
            if is_default:
                status += " [blue](Standard)"
            has_valid_key = True
        elif is_dummy:
            status = "[red]Dummy-Key"
        else:
            status = "[dim]Nicht konfiguriert"

        table.add_row(name, status, default_model if is_default else "-")

    console.print(table)
    console.print()

    # Hinweise
    if not has_valid_key:
        console.print(
            Panel(
                "[bold]Kein gültiger API Key gefunden![/bold]\n\n"
                "Jeder Benutzer muss seine eigenen API Keys konfigurieren.\n\n"
                "[cyan]Einrichtung:[/cyan]\n"
                "  python scripts/setup_wizard.py\n\n"
                "[cyan]Schnell-Setup:[/cyan]\n"
                '  python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "sk-..."',
                title="Aktion erforderlich",
                border_style="yellow",
            )
        )
        return False
    else:
        console.print(
            Panel(
                f"[green]Backend:[/green] {default_backend}\n"
                f"[green]Modell:[/green] {default_model}\n\n"
                "[cyan]Nutzung:[/cyan]\n"
                '  python tools/kimi_helper.py -p recon "Scan target.com"\n'
                "  python tools/kimi_helper.py -i  (interaktiv)",
                title="Bereit",
                border_style="green",
            )
        )
        return True


if __name__ == "__main__":
    import sys

    success = check_config()
    sys.exit(0 if success else 1)
