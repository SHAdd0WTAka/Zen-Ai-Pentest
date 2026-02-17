#!/usr/bin/env python3
"""
Kimi Personas API CLI Client
Kommandozeilen-Tool für die API
"""

import os
import sys
import argparse
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

DEFAULT_API_URL = "http://127.0.0.1:5000"

class KimiAPIClient:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url or os.getenv('KIMI_API_URL', DEFAULT_API_URL)
        self.api_key = api_key or os.getenv('KIMI_API_KEY', '')
        self.session = requests.Session()

    def _headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def health(self):
        """Health Check"""
        r = self.session.get(f"{self.base_url}/api/v1/health")
        return r.json() if r.ok else None

    def list_personas(self, category=None):
        """Liste alle Personas"""
        url = f"{self.base_url}/api/v1/personas"
        if category:
            url += f"?category={category}"
        r = self.session.get(url)
        return r.json() if r.ok else None

    def get_persona(self, persona_id, include_prompt=False):
        """Hole Persona Details"""
        url = f"{self.base_url}/api/v1/personas/{persona_id}"
        if include_prompt:
            url += "?include_prompt=true"
        r = self.session.get(url)
        return r.json() if r.ok else None

    def get_prompt(self, persona_id):
        """Hole System Prompt"""
        url = f"{self.base_url}/api/v1/personas/{persona_id}/prompt"
        r = self.session.get(url)
        return r.text if r.ok else None

    def chat(self, persona, message, temperature=0.7, context=None, complete=False):
        """Chat mit Persona"""
        endpoint = "/api/v1/chat/complete" if complete else "/api/v1/chat"
        url = f"{self.base_url}{endpoint}"

        data = {
            "persona": persona,
            "message": message,
            "temperature": temperature
        }
        if context:
            data["context"] = context

        r = self.session.post(url, headers=self._headers(), json=data)
        return r.json() if r.ok else None

    def admin_stats(self):
        """Admin Dashboard Stats"""
        url = f"{self.base_url}/admin"
        r = self.session.get(url)
        return r.json() if r.ok else None

    def admin_logs(self):
        """Admin Logs"""
        url = f"{self.base_url}/admin/logs"
        r = self.session.get(url)
        return r.json() if r.ok else None

def cmd_health(args):
    client = KimiAPIClient(args.url, args.key)
    data = client.health()

    if not data:
        console.print("[red]❌ API nicht erreichbar[/red]")
        return 1

    console.print(Panel.fit(
        f"[green]✓ API Online[/green]\n"
        f"Version: {data.get('version', 'unknown')}\n"
        f"Personas: {data.get('personas_available', 0)}\n"
        f"Timestamp: {data.get('timestamp', 'unknown')}",
        title="Health Check", border_style="green"
    ))

def cmd_list(args):
    client = KimiAPIClient(args.url, args.key)
    data = client.list_personas(args.category)

    if not data:
        console.print("[red]❌ Fehler beim Laden[/red]")
        return 1

    table = Table(title=f"Personas ({data.get('count', 0)} total)")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Description")

    for pid, pdata in data.get('personas', {}).items():
        table.add_row(
            pid,
            pdata.get('name', ''),
            pdata.get('category', ''),
            pdata.get('description', '')[:50] + "..."
        )

    console.print(table)

def cmd_chat(args):
    client = KimiAPIClient(args.url, args.key)

    console.print(Panel(f"[bold]{args.persona}[/bold] | Temp: {args.temperature}", border_style="cyan"))
    console.print(f"[dim]You:[/dim] {args.message}")
    console.print()

    with console.status("[cyan]Frage Kimi...[/cyan]"):
        data = client.chat(
            args.persona,
            args.message,
            args.temperature,
            args.context,
            complete=args.complete
        )

    if not data:
        console.print("[red]❌ Fehler bei der Anfrage[/red]")
        return 1

    if data.get('status') == 'success':
        if args.complete:
            console.print(Markdown(data['response']))
            if 'usage' in data:
                console.print(f"\n[dim]Tokens: {data['usage']}\nModel: {data.get('model', 'unknown')}[/dim]")
        else:
            console.print("[green]✓ Anfrage akzeptiert[/green]")
            console.print(f"Prompt Länge: {data.get('system_prompt_length', 0)} chars")
    else:
        console.print(f"[red]❌ Fehler: {data.get('error', 'Unknown')}[/red]")

def cmd_prompt(args):
    client = KimiAPIClient(args.url, args.key)
    prompt = client.get_prompt(args.persona)

    if not prompt:
        console.print("[red]❌ Persona nicht gefunden[/red]")
        return 1

    console.print(Panel(prompt, title=f"System Prompt: {args.persona}", border_style="blue"))

def cmd_admin(args):
    client = KimiAPIClient(args.url, args.key)

    if args.logs:
        data = client.admin_logs()
        if data:
            console.print(Panel(
                "\n".join(data.get('logs', [])[-20:]),
                title=f"Recent Logs ({data.get('count', 0)} entries)",
                border_style="dim"
            ))
    else:
        data = client.admin_stats()
        if not data:
            console.print("[red]❌ Admin API nicht erreichbar[/red]")
            return 1

        stats = data.get('stats', {})

        console.print(Panel.fit(
            f"[bold]Uptime:[/bold] {data.get('uptime_formatted', 'unknown')}\n"
            f"[bold]Total Requests:[/bold] {stats.get('total_requests', 0)}\n"
            f"[bold]Personas:[/bold] {data.get('personas_loaded', 0)}",
            title="Admin Dashboard", border_style="magenta"
        ))

        if stats.get('requests_by_persona'):
            table = Table(title="Requests by Persona")
            table.add_column("Persona", style="cyan")
            table.add_column("Count", style="green")
            for persona, count in stats['requests_by_persona'].items():
                table.add_row(persona, str(count))
            console.print(table)

def cmd_interactive(args):
    """Interaktiver Modus"""
    client = KimiAPIClient(args.url, args.key)

    console.print(Panel.fit(
        "[bold]Kimi Personas API Client[/bold]\n"
        "Befehle: /persona <name>, /temp <0.0-1.0>, /quit",
        title="Interactive Mode", border_style="green"
    ))

    current_persona = args.persona or 'recon'
    current_temp = 0.7

    while True:
        try:
            user_input = console.input(f"[bold cyan]{current_persona}({current_temp})>[/bold cyan] ").strip()

            if not user_input:
                continue

            if user_input.startswith('/'):
                parts = user_input[1:].split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'persona':
                    if arg in ['recon', 'exploit', 'report', 'audit', 'social', 'network', 'mobile', 'redteam', 'ics', 'cloud', 'crypto']:
                        current_persona = arg
                        console.print(f"[green]✓ Gewechselt zu:[/green] {arg}")
                    else:
                        console.print("[red]Unbekannte Persona[/red]")
                elif cmd == 'temp':
                    try:
                        current_temp = float(arg)
                        console.print(f"[green]✓ Temperature:[/green] {current_temp}")
                    except:
                        console.print("[red]Ungültige Temperatur[/red]")
                elif cmd == 'prompt':
                    prompt = client.get_prompt(current_persona)
                    if prompt:
                        console.print(Panel(prompt[:500] + "...", title="System Prompt"))
                else:
                    console.print("[dim]Befehle: /persona, /temp, /prompt, /quit[/dim]")
                continue

            # Send message
            with console.status("[cyan]Frage...[/cyan]"):
                data = client.chat(current_persona, user_input, current_temp, complete=args.complete)

            if data and data.get('status') == 'success' and args.complete:
                console.print(Markdown(data['response']))
            elif data:
                console.print(f"[dim]{data}[/dim]")
            else:
                console.print("[red]Fehler[/red]")

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")

    console.print("[dim]Auf Wiedersehen![/dim]")

def main():
    parser = argparse.ArgumentParser(
        description="Kimi Personas API CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Umgebungsvariablen:
  KIMI_API_URL    API Base URL (default: http://127.0.0.1:5000)
  KIMI_API_KEY    API Key für Authentifizierung

Beispiele:
  %(prog)s health
  %(prog)s list
  %(prog)s chat recon "Analysiere example.com"
  %(prog)s prompt exploit
  %(prog)s admin
  %(prog)s interactive --complete
        """
    )

    parser.add_argument('--url', default=os.getenv('KIMI_API_URL', DEFAULT_API_URL),
                       help='API Base URL')
    parser.add_argument('--key', default=os.getenv('KIMI_API_KEY', ''),
                       help='API Key')

    subparsers = parser.add_subparsers(dest='command', help='Befehle')

    # Health
    subparsers.add_parser('health', help='Health Check')

    # List
    p_list = subparsers.add_parser('list', help='Liste Personas')
    p_list.add_argument('--category', choices=['core', 'extended'],
                       help='Filter nach Kategorie')

    # Chat
    p_chat = subparsers.add_parser('chat', help='Chat mit Persona')
    p_chat.add_argument('persona', help='Persona ID')
    p_chat.add_argument('message', help='Nachricht')
    p_chat.add_argument('-t', '--temperature', type=float, default=0.7)
    p_chat.add_argument('-c', '--context', help='Kontext')
    p_chat.add_argument('--complete', action='store_true',
                       help='Kimi API Integration nutzen')

    # Prompt
    p_prompt = subparsers.add_parser('prompt', help='Zeige System Prompt')
    p_prompt.add_argument('persona', help='Persona ID')

    # Admin
    p_admin = subparsers.add_parser('admin', help='Admin Dashboard')
    p_admin.add_argument('--logs', action='store_true', help='Zeige Logs')

    # Interactive
    p_interactive = subparsers.add_parser('interactive', help='Interaktiver Modus')
    p_interactive.add_argument('--persona', default='recon', help='Start-Persona')
    p_interactive.add_argument('--complete', action='store_true',
                              help='Kimi API Integration')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'health': cmd_health,
        'list': cmd_list,
        'chat': cmd_chat,
        'prompt': cmd_prompt,
        'admin': cmd_admin,
        'interactive': cmd_interactive
    }

    return commands[args.command](args) or 0

if __name__ == '__main__':
    sys.exit(main())
