#!/usr/bin/env python3
import re
import sys
from pathlib import Path
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Bekannte Backends und ihre Keys
BACKENDS = {
    "kimi": {"name": "🌙 Kimi", "key_var": "KIMI_API_KEY", "models": ["kimi-k2.5", "kimi-k1.5", "kimi-latest"]},
    "openrouter": {"name": "🔀 OpenRouter", "key_var": "OPENROUTER_API_KEY", "models": ["openrouter/auto", "anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-pro"]},
    "openai": {"name": "🤖 OpenAI", "key_var": "OPENAI_API_KEY", "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]}
}

def parse_env(env_path):
    """Liest .env und extrahiert Konfiguration"""
    config = {
        "current_backend": None,
        "current_model": None,
        "available": {}
    }

    if not env_path.exists():
        return config

    with open(env_path, 'r') as f:
        content = f.read()

    # Aktuelles Backend/Modell finden
    backend_match = re.search(r'export DEFAULT_BACKEND="([^"]+)"', content)
    model_match = re.search(r'export DEFAULT_MODEL="([^"]+)"', content)

    if backend_match:
        config["current_backend"] = backend_match.group(1)
    if model_match:
        config["current_model"] = model_match.group(1)

    # Verfügbare Keys suchen
    for key, data in BACKENDS.items():
        key_match = re.search(rf'export {data["key_var"]}="([^"]+)"', content)
        if key_match and len(key_match.group(1)) > 10:
            config["available"][key] = key_match.group(1)

    return config

def show_status(config):
    """Zeigt aktuelle Konfiguration"""
    table = Table(title="🧠 Zen-AI Aktuelle Konfiguration", show_header=True, header_style="bold cyan")
    table.add_column("Einstellung", style="dim")
    table.add_column("Wert", style="green")

    current_backend = config.get("current_backend", "Nicht gesetzt")
    current_model = config.get("current_model", "Nicht gesetzt")

    table.add_row("Backend", current_backend)
    table.add_row("Modell", current_model)
    table.add_row("Verfügbare Keys", ", ".join(config["available"].keys()) or "Keine")

    console.print(table)

def switch_backend(config, env_path):
    """Wechselt zwischen konfigurierten Backends"""
    available = config["available"]

    if not available:
        console.print("[red]❌ Keine Backends konfiguriert. Führe zuerst setup_wizard.py aus![/red]")
        return

    choices = []
    for key in available.keys():
        backend_info = BACKENDS[key]
        is_active = "✓ " if config["current_backend"] == key else "  "
        choices.append(questionary.Choice(
            title=f"{is_active}{backend_info['name']}",
            value=key
        ))

    choices.append(questionary.Choice(title="❌ Abbrechen", value=None))

    new_backend = questionary.select(
        "Wähle Backend:",
        choices=choices,
        instruction="(✓ = Aktiv)"
    ).ask()

    if not new_backend:
        return

    # Modell auswählen
    backend_data = BACKENDS[new_backend]
    current_model = config.get("current_model", "")

    # Prüfen ob aktuelles Modell zu neuem Backend passt, sonst default
    if current_model in backend_data["models"]:
        default_model = current_model
    else:
        default_model = backend_data["models"][0]

    new_model = questionary.select(
        f"Modell für {backend_data['name']}:",
        choices=backend_data["models"],
        default=default_model
    ).ask()

    update_env(env_path, new_backend, new_model)
    console.print(f"[green]✅ Gewechselt zu:[/green] {backend_data['name']} mit {new_model}")

def update_env(env_path, backend, model):
    """Aktualisiert die .env Datei"""
    if not env_path.exists():
        console.print("[red]❌ .env nicht gefunden![/red]")
        return

    with open(env_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("export DEFAULT_BACKEND="):
            new_lines.append(f'export DEFAULT_BACKEND="{backend}"\n')
        elif line.startswith("export DEFAULT_MODEL="):
            new_lines.append(f'export DEFAULT_MODEL="{model}"\n')
        else:
            new_lines.append(line)

    with open(env_path, 'w') as f:
        f.writelines(new_lines)

def quick_switch(config, env_path):
    """Schneller Wechsel zwischen nur den verfügbaren Backends"""
    available = list(config["available"].keys())

    if len(available) < 2:
        console.print("[yellow]⚠️  Nur ein Backend konfiguriert. Nutze 'Modell wechseln' für Details.[/yellow]")
        return

    # Zeige nur Optionen mit aktivem Marker
    for key in available:
        marker = "→ " if config["current_backend"] == key else "  "
        console.print(f"{marker}{BACKENDS[key]['name']}")

    choice = questionary.select(
        "Schnellwechsel:",
        choices=[(BACKENDS[k]['name'], k) for k in available] + [("❌ Abbrechen", None)]
    ).ask()

    if choice:
        # Behalte Modell bei wenn möglich, sonst erstes
        current_model = config.get("current_model", "")
        if current_model not in BACKENDS[choice]["models"]:
            current_model = BACKENDS[choice]["models"][0]
        update_env(env_path, choice, current_model)
        console.print(f"[green]✅ Aktiv:[/green] {BACKENDS[choice]['name']}")

def main():
    env_path = Path(__file__).parent / ".env"
    config = parse_env(env_path)

    if not config["available"]:
        console.print(Panel.fit(
            "[red]Keine API Keys gefunden![/red]\n\n"
            "Führe zuerst aus:\n"
            "[cyan]python3 setup_wizard.py[/cyan]",
            title="Zen-AI Switch",
            border_style="red"
        ))
        sys.exit(1)

    show_status(config)

    action = questionary.select(
        "Was möchtest du tun?",
        choices=[
            questionary.Choice("🔄 Backend & Modell wechseln", value="full"),
            questionary.Choice("⚡ Schnellwechsel (nur Backend)", value="quick"),
            questionary.Choice("❌ Beenden", value="exit")
        ]
    ).ask()

    if action == "full":
        switch_backend(config, env_path)
    elif action == "quick":
        quick_switch(config, env_path)
    else:
        console.print("[dim]Tschüss![/dim]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        sys.exit(0)
