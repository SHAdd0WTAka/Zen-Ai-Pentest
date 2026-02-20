#!/usr/bin/env python3
"""
Zen-AI Pentest Model Switcher
Wechselt zwischen konfigurierten Backends und Modellen.

Usage:
    python switch_model.py              # Interaktiver Modus
    python switch_model.py --list       # Zeigt verfuegbare Backends
    python switch_model.py --status     # Zeigt aktuelle Konfiguration
    python switch_model.py -b openai -m gpt-4o
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None

    def print_msg(msg, style=None):
        print(msg)

else:

    def print_msg(msg, style=None):
        if style:
            console.print(msg, style=style)
        else:
            console.print(msg)


# Bekannte Backends und ihre Keys
BACKENDS = {
    "kimi": {"name": "Kimi", "key_var": "KIMI_API_KEY", "models": ["kimi-k2.5", "kimi-k1.5", "kimi-latest"]},
    "openrouter": {
        "name": "OpenRouter",
        "key_var": "OPENROUTER_API_KEY",
        "models": ["openrouter/auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-pro"],
    },
    "openai": {"name": "OpenAI", "key_var": "OPENAI_API_KEY", "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]},
}


def parse_env(env_path):
    """Liest .env und extrahiert Konfiguration"""
    config = {"current_backend": None, "current_model": None, "available": {}}

    if not env_path.exists():
        return config

    with open(env_path, "r") as f:
        content = f.read()

    # Aktuelles Backend/Modell finden
    backend_match = re.search(r'export DEFAULT_BACKEND="([^"]+)"', content)
    model_match = re.search(r'export DEFAULT_MODEL="([^"]+)"', content)

    if backend_match:
        config["current_backend"] = backend_match.group(1)
    if model_match:
        config["current_model"] = model_match.group(1)

    # Verfuegbare Keys suchen
    for key, data in BACKENDS.items():
        key_match = re.search(rf'export {data["key_var"]}="([^"]+)"', content)
        if key_match and len(key_match.group(1)) > 10:
            config["available"][key] = key_match.group(1)

    return config


def show_status(config, env_path):
    """Zeigt aktuelle Konfiguration"""
    if RICH_AVAILABLE:
        table = Table(title="Zen-AI Aktuelle Konfiguration", show_header=True, header_style="bold cyan")
        table.add_column("Einstellung", style="dim")
        table.add_column("Wert", style="green")

        current_backend = config.get("current_backend", "Nicht gesetzt")
        current_model = config.get("current_model", "Nicht gesetzt")

        table.add_row("Backend", current_backend)
        table.add_row("Modell", current_model)
        table.add_row("Verfuegbare Keys", ", ".join(config["available"].keys()) or "Keine")

        console.print(table)
    else:
        print("\n=== Zen-AI Konfiguration ===")
        print(f"Backend: {config.get('current_backend', 'Nicht gesetzt')}")
        print(f"Modell: {config.get('current_model', 'Nicht gesetzt')}")
        print(f"Verfuegbare Keys: {', '.join(config['available'].keys()) or 'Keine'}")
        print(f"Env-Datei: {env_path}")
        print("===========================\n")


def list_backends(config):
    """Listet alle verfuegbaren Backends"""
    if RICH_AVAILABLE:
        table = Table(title="Verfuegbare Backends", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name")
        table.add_column("Env-Variable")
        table.add_column("Modelle")
        table.add_column("Status")

        for key, data in BACKENDS.items():
            status = "[green]Konfiguriert[/green]" if key in config["available"] else "[yellow]Nicht konfiguriert[/yellow]"
            current = " [blue]<- Aktiv[/blue]" if config.get("current_backend") == key else ""
            table.add_row(key, data["name"], data["key_var"], ", ".join(data["models"]), status + current)

        console.print(table)
    else:
        print("\n=== Verfuegbare Backends ===")
        for key, data in BACKENDS.items():
            status = "Konfiguriert" if key in config["available"] else "Nicht konfiguriert"
            current = " <- Aktiv" if config.get("current_backend") == key else ""
            print(f"\n{key}: {data['name']} ({status}){current}")
            print(f"  Env: {data['key_var']}")
            print(f"  Modelle: {', '.join(data['models'])}")
        print("\n===========================\n")


def switch_backend(config, env_path, new_backend, new_model=None):
    """Wechselt zu einem anderen Backend"""
    if new_backend not in BACKENDS:
        print_msg(f"[red]Ungueltiges Backend: {new_backend}[/red]")
        return False

    if new_backend not in config["available"]:
        print_msg(f"[yellow]Warnung: {new_backend} ist nicht konfiguriert (kein API Key)[/yellow]")

    backend_data = BACKENDS[new_backend]

    # Modell bestimmen
    if new_model:
        if new_model not in backend_data["models"]:
            print_msg(f"[red]Ungueltiges Modell '{new_model}' fuer {new_backend}[/red]")
            print_msg(f"Verfuegbar: {', '.join(backend_data['models'])}")
            return False
    else:
        # Aktuelles Modell beibehalten wenn moeglich
        current_model = config.get("current_model", "")
        if current_model in backend_data["models"]:
            new_model = current_model
        else:
            new_model = backend_data["models"][0]

    update_env(env_path, new_backend, new_model)
    print_msg(f"[green]Gewechselt zu:[/green] {backend_data['name']} mit {new_model}")
    return True


def switch_model(config, env_path, new_model):
    """Wechselt das Modell fuer das aktuelle Backend"""
    current_backend = config.get("current_backend")

    if not current_backend:
        print_msg("[red]Kein Backend konfiguriert. Nutze --backend um eines zu waehlen.[/red]")
        return False

    backend_data = BACKENDS.get(current_backend)
    if not backend_data:
        print_msg(f"[red]Unbekanntes Backend: {current_backend}[/red]")
        return False

    if new_model not in backend_data["models"]:
        print_msg(f"[red]Ungueltiges Modell '{new_model}' fuer {current_backend}[/red]")
        print_msg(f"Verfuegbar: {', '.join(backend_data['models'])}")
        return False

    update_env(env_path, current_backend, new_model)
    print_msg(f"[green]Modell gewechselt zu:[/green] {new_model}")
    return True


def update_env(env_path, backend, model):
    """Aktualisiert die .env Datei"""
    if not env_path.exists():
        print_msg(f"[red].env nicht gefunden: {env_path}[/red]")
        return

    with open(env_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("export DEFAULT_BACKEND="):
            new_lines.append(f'export DEFAULT_BACKEND="{backend}"\n')
        elif line.startswith("export DEFAULT_MODEL="):
            new_lines.append(f'export DEFAULT_MODEL="{model}"\n')
        else:
            new_lines.append(line)

    with open(env_path, "w") as f:
        f.writelines(new_lines)


def interactive_mode(config, env_path):
    """Interaktiver Modus mit questionary"""
    try:
        import questionary
    except ImportError:
        print_msg("[red]questionary nicht installiert. Nutze CLI-Modus:[/red]")
        print("  python switch_model.py --list")
        print("  python switch_model.py -b openai -m gpt-4o")
        return

    if not config["available"]:
        if RICH_AVAILABLE:
            console.print(
                Panel.fit(
                    "[red]Keine API Keys gefunden![/red]\n\n" "Fuehre zuerst aus:\n" "[cyan]python3 setup_wizard.py[/cyan]",
                    title="Zen-AI Switch",
                    border_style="red",
                )
            )
        else:
            print("\nKeine API Keys gefunden!")
            print("Fuehre zuerst aus: python setup_wizard.py")
        sys.exit(1)

    show_status(config, env_path)

    action = questionary.select(
        "Was moechtest du tun?",
        choices=[
            questionary.Choice("Backend & Modell wechseln", value="full"),
            questionary.Choice("Nur Backend wechseln", value="backend"),
            questionary.Choice("Nur Modell wechseln", value="model"),
            questionary.Choice("Beenden", value="exit"),
        ],
    ).ask()

    if action == "full":
        # Backend auswaehlen
        choices = []
        for key in config["available"].keys():
            backend_info = BACKENDS[key]
            is_active = "(Aktiv) " if config["current_backend"] == key else ""
            choices.append(questionary.Choice(title=f"{is_active}{backend_info['name']}", value=key))

        new_backend = questionary.select("Waehle Backend:", choices=choices).ask()
        if not new_backend:
            return

        # Modell auswaehlen
        backend_data = BACKENDS[new_backend]
        current_model = config.get("current_model", "")
        default_model = current_model if current_model in backend_data["models"] else backend_data["models"][0]

        new_model = questionary.select(
            f"Modell fuer {backend_data['name']}:", choices=backend_data["models"], default=default_model
        ).ask()

        switch_backend(config, env_path, new_backend, new_model)

    elif action == "backend":
        choices = [questionary.Choice(title=BACKENDS[k]["name"], value=k) for k in config["available"].keys()]
        new_backend = questionary.select("Waehle Backend:", choices=choices).ask()
        if new_backend:
            switch_backend(config, env_path, new_backend)

    elif action == "model":
        current_backend = config.get("current_backend")
        if not current_backend:
            print_msg("[red]Kein Backend aktiv[/red]")
            return

        backend_data = BACKENDS[current_backend]
        new_model = questionary.select(
            "Waehle Modell:", choices=backend_data["models"], default=config.get("current_model", backend_data["models"][0])
        ).ask()

        if new_model:
            switch_model(config, env_path, new_model)
    else:
        print_msg("[dim]Tschuess![/dim]")


def main():
    env_path = Path(__file__).parent.parent / ".env"
    config = parse_env(env_path)

    parser = argparse.ArgumentParser(
        description="Zen-AI Pentest Model Switcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s                    # Interaktiver Modus
  %(prog)s --list             # Zeige verfuegbare Backends
  %(prog)s --status           # Zeige aktuelle Konfiguration
  %(prog)s -b openai          # Wechsle zu OpenAI (automatisches Modell)
  %(prog)s -b openai -m gpt-4o  # Wechsle zu OpenAI mit GPT-4o
  %(prog)s -m gpt-4o-mini     # Wechsle nur das Modell
        """,
    )

    parser.add_argument("-b", "--backend", choices=list(BACKENDS.keys()), help="Zu Backend wechseln")
    parser.add_argument("-m", "--model", help="Zu Modell wechseln")
    parser.add_argument("-l", "--list", action="store_true", help="Verfuegbare Backends anzeigen")
    parser.add_argument("-s", "--status", action="store_true", help="Aktuelle Konfiguration anzeigen")

    args = parser.parse_args()

    if args.list:
        list_backends(config)
    elif args.status:
        show_status(config, env_path)
    elif args.backend:
        switch_backend(config, env_path, args.backend, args.model)
    elif args.model:
        switch_model(config, env_path, args.model)
    else:
        interactive_mode(config, env_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]Abgebrochen.[/yellow]")
        else:
            print("\nAbgebrochen.")
        sys.exit(0)
