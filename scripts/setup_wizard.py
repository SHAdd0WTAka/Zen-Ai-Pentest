#!/usr/bin/env python3
"""
Zen-AI Pentest Setup Wizard
Konfiguriert API-Keys und Backends für Zen-AI Pentest.

Usage:
    python setup_wizard.py                    # Interaktiver Modus
    python setup_wizard.py --backend kimi --model kimi-k2.5 --key YOUR_KEY
    python setup_wizard.py --backend openai --model gpt-4o --key YOUR_KEY --test
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

BACKENDS = {
    "kimi": {
        "name": "Kimi (Moonshot AI)",
        "env_var": "KIMI_API_KEY",
        "url": "https://platform.moonshot.cn/",
        "models": ["kimi-k2.5", "kimi-k1.5", "kimi-latest"],
        "test_url": "https://api.moonshot.cn/v1/models",
    },
    "openrouter": {
        "name": "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/keys",
        "models": [
            "openrouter/auto",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "google/gemini-pro",
        ],
        "test_url": "https://openrouter.ai/api/v1/auth/key",
    },
    "openai": {
        "name": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "url": "https://platform.openai.com/api-keys",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "test_url": "https://api.openai.com/v1/models",
    },
}


def show_banner():
    console.print(
        Panel.fit(
            Text(
                "Zen-AI Pentest Configurator",
                justify="center",
                style="bold cyan",
            )
            + "\n"
            + Text(
                "Waehle dein AI-Backend und Modell",
                justify="center",
                style="dim",
            ),
            border_style="cyan",
        )
    )


def test_api_key(backend_key, api_key):
    backend = BACKENDS[backend_key]
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            backend["test_url"], headers=headers, timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False


def interactive_mode():
    """Interaktiver Modus mit questionary (wenn verfuegbar)"""
    try:
        import questionary
    except ImportError:
        console.print(
            "[red]questionary nicht installiert. Nutze CLI-Modus:[/red]"
        )
        console.print(
            "  python setup_wizard.py --backend kimi --model kimi-k2.5 --key YOUR_KEY"
        )
        return

    show_banner()

    choices = [
        questionary.Choice(title=v["name"], value=k)
        for k, v in BACKENDS.items()
    ] + [questionary.Choice(title="[X] Abbrechen", value=None)]

    backend_choice = questionary.select(
        "Waehle dein AI Backend:", choices=choices
    ).ask()

    if not backend_choice:
        console.print("[yellow]Abgebrochen.[/yellow]")
        return

    backend = BACKENDS[backend_choice]

    console.print(
        f"\n[blue]Verfuegbare Modelle fuer {backend['name']}:[/blue]"
    )
    model = questionary.select(
        "Waehle das Modell:",
        choices=backend["models"],
        default=backend["models"][0],
    ).ask()

    console.print(f"\n[dim]Hole deinen Key bei: {backend['url']}[/dim]")
    api_key = questionary.password("API Key eingeben:").ask()

    if not api_key or len(api_key) < 10:
        console.print("[red]Ungueltiger Key[/red]")
        return

    if questionary.confirm("Verbindung testen?", default=True).ask():
        with console.status("[cyan]Teste...[/cyan]"):
            if test_api_key(backend_choice, api_key):
                console.print("[green]Key valide![/green]")
            else:
                console.print("[yellow]Test fehlgeschlagen[/yellow]")
                if not questionary.confirm("Trotzdem speichern?").ask():
                    return

    save_config(backend_choice, model, api_key)


def cli_mode(backend, model, api_key, test=False):
    """CLI-Modus mit Argumenten"""
    if backend not in BACKENDS:
        console.print(f"[red]Ungueltiges Backend: {backend}[/red]")
        console.print(f"Verfuegbar: {', '.join(BACKENDS.keys())}")
        sys.exit(1)

    backend_data = BACKENDS[backend]

    if model not in backend_data["models"]:
        console.print(f"[red]Ungueltiges Modell: {model}[/red]")
        console.print(f"Verfuegbar: {', '.join(backend_data['models'])}")
        sys.exit(1)

    if not api_key or len(api_key) < 10:
        console.print("[red]Ungueltiger API Key[/red]")
        sys.exit(1)

    if test:
        console.print(f"[cyan]Teste {backend_data['name']}...[/cyan]")
        if test_api_key(backend, api_key):
            console.print("[green]Key valide![/green]")
        else:
            console.print(
                "[yellow]Test fehlgeschlagen - speichere trotzdem[/yellow]"
            )

    save_config(backend, model, api_key)


def save_config(backend_choice, model, api_key):
    """Speichert die Konfiguration in .env"""
    env_path = Path(__file__).parent.parent / ".env"
    backend = BACKENDS[backend_choice]

    if env_path.exists():
        backup = env_path.with_suffix(".env.backup")
        os.rename(env_path, backup)
        console.print(f"[dim]Backup: {backup}[/dim]")

    with open(env_path, "w") as f:
        f.write("# Zen-AI Pentest - API Konfiguration\n")
        f.write(f'export DEFAULT_BACKEND="{backend_choice}"\n')
        f.write(f'export DEFAULT_MODEL="{model}"\n')
        f.write(f"export {backend['env_var']}=\"{api_key}\"\n")
        f.write('export LOG_LEVEL="INFO"\n\n')
        f.write("# Alternative Backends (nicht konfiguriert)\n")
        for key, data in BACKENDS.items():
            if key != backend_choice:
                f.write(f"# export {data['env_var']}=\"\"\n")

    console.print(
        Panel(
            f"[green]Konfiguriert:[/green] {backend['name']} mit {model}\n\n"
            f"Nutzung:\n"
            f"  source .env\n"
            f"  python scripts/switch_model.py",
            title="Setup Complete",
            border_style="green",
        )
    )

    # Zeige verfuegbare Umgebungsvariablen
    console.print("\n[dim]Umgebungsvariablen (NICHT committen!):[/dim]")
    console.print(f"  DEFAULT_BACKEND={backend_choice}")
    console.print(f"  DEFAULT_MODEL={model}")
    console.print(f"  {backend['env_var']}=***")


def show_status():
    """Zeigt aktuelle Konfiguration"""
    env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        console.print("[yellow]Keine .env Datei gefunden[/yellow]")
        return

    with open(env_path, "r") as f:
        content = f.read()

    console.print(Panel(content, title="Aktuelle .env", border_style="blue"))


def main():
    parser = argparse.ArgumentParser(
        description="Zen-AI Pentest Setup Wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s                           # Interaktiver Modus
  %(prog)s --status                  # Zeige aktuelle Konfiguration
  %(prog)s -b kimi -m kimi-k2.5 -k KEY
  %(prog)s -b openai -m gpt-4o -k KEY --test
        """,
    )

    parser.add_argument(
        "-b",
        "--backend",
        choices=list(BACKENDS.keys()),
        help="Backend auswaehlen",
    )
    parser.add_argument("-m", "--model", help="Modell auswaehlen")
    parser.add_argument("-k", "--key", help="API Key")
    parser.add_argument(
        "-t", "--test", action="store_true", help="API Key testen"
    )
    parser.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Aktuelle Konfiguration anzeigen",
    )

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.backend and args.model and args.key:
        cli_mode(args.backend, args.model, args.key, args.test)
    elif args.backend or args.model or args.key:
        parser.error(
            "--backend, --model und --key muessen zusammen verwendet werden"
        )
    else:
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        sys.exit(0)
