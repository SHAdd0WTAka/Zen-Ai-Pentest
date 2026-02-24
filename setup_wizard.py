#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import questionary
import requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

BACKENDS = {
    "kimi": {
        "name": "🌙 Kimi (Moonshot AI)",
        "env_var": "KIMI_API_KEY",
        "url": "https://platform.moonshot.cn/",
        "models": ["kimi-k2.5", "kimi-k1.5", "kimi-latest"],
        "test_url": "https://api.moonshot.cn/v1/models",
    },
    "openrouter": {
        "name": "🔀 OpenRouter",
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
        "name": "🤖 OpenAI",
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
                "🧠 Zen-AI Pentest Configurator",
                justify="center",
                style="bold cyan",
            )
            + "\n"
            + Text(
                "Wähle dein AI-Backend und Modell",
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


def main():
    show_banner()

    # FIX: questionary.Choice verwenden statt Tupel
    choices = [
        questionary.Choice(title=v["name"], value=k)
        for k, v in BACKENDS.items()
    ] + [questionary.Choice(title="❌ Abbrechen", value=None)]

    backend_choice = questionary.select(
        "Wähle dein AI Backend:", choices=choices
    ).ask()

    if not backend_choice:
        console.print("[yellow]Abgebrochen.[/yellow]")
        return

    backend = BACKENDS[backend_choice]

    console.print(f"\n[blue]Verfügbare Modelle für {backend['name']}:[/blue]")
    model = questionary.select(
        "Wähle das Modell:",
        choices=backend["models"],
        default=backend["models"][0],
    ).ask()

    console.print(f"\n[dim]Hole deinen Key bei: {backend['url']}[/dim]")
    api_key = questionary.password("API Key eingeben:").ask()

    if not api_key or len(api_key) < 10:
        console.print("[red]❌ Ungültiger Key[/red]")
        return

    if questionary.confirm("🔍 Verbindung testen?", default=True).ask():
        with console.status("[cyan]Teste...[/cyan]"):
            if test_api_key(backend_choice, api_key):
                console.print("[green]✅ Key valide![/green]")
            else:
                console.print("[yellow]⚠️ Test fehlgeschlagen[/yellow]")
                if not questionary.confirm("Trotzdem speichern?").ask():
                    return

    # Speichern
    env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        backup = env_path.with_suffix(".env.backup")
        os.rename(env_path, backup)
        console.print(f"[dim]💾 Backup: {backup}[/dim]")

    with open(env_path, "w") as f:
        f.write("# 🧠 Zen-AI Pentest - API Konfiguration\n")
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
            f"[green]✅ Konfiguriert:[/green] {backend['name']} mit {model}\n\n"
            f"🚀 Nutzung:\n"
            f"  source .env\n"
            f"  python3 switch_model.py",
            title="Setup Complete",
            border_style="green",
        )
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen.[/yellow]")
        sys.exit(0)
