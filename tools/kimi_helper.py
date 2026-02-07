#!/usr/bin/env python3
"""
Kimi AI Helper für Zen-AI-Pentest
Unified Tool: Unterstützt sowohl API-Mode als auch CLI-Mode

Usage:
    # API Mode (Standard)
    python tools/kimi_helper.py -p recon "Scan target.com"
    
    # CLI Mode (lokale kimi CLI)
    python tools/kimi_helper.py --cli -p recon
    
    # Interaktiv
    python tools/kimi_helper.py -i
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

console = Console()

# Personas mit detaillierten System-Prompts
PERSONAS = {
    "recon": {
        "name": "[Recon] OSINT Specialist",
        "emoji": "🔍",
        "desc": "Subdomain-Enum, Port-Scanning, Technologie-Erkennung",
        "prompt": """Du bist ein OSINT-Spezialist und Recon-Experte für Penetration Testing.
REGELN:
- Analysiere Ziele strukturiert: Subdomains → Ports → Technologien
- Gib nur verifizierbare, echte Tools/Befehle an (keine Halluzinationen)
- Output-Format: Markdown mit Code-Blocks für Befehle
- Priorisierung: Critical (CVSS 9.0-10.0) > High > Medium > Low
- Nutze Zen-AI-Pentest Konventionen: Python 3.13, virtuelle Umgebungen
- Wenn unsicher: Frage nach Verifikation statt zu raten"""
    },
    "exploit": {
        "name": "[Exploit] Developer",
        "emoji": "💣", 
        "desc": "Python-Exploits, POC-Entwicklung, Automation",
        "prompt": """Du bist ein Exploit-Developer für das Zen-AI-Pentest Framework.
CODE-REGELN:
- Python 3.13+ mit Type Hints wo sinnvoll
- Nutze bestehende Module: config_loader.py, logging aus config.json
- Error Handling: try/except mit spezifischen Exceptions
- Kein Pseudo-Code, nur funktionierende Implementationen
- Docstrings für alle Funktionen (Google-Stil)
- Respektiere Rate-Limits: max 10 req/min, Backoff 60s
- Stealth-Mode: Zufällige Delays (1-3s), User-Agent Rotation"""
    },
    "report": {
        "name": "[Report] Technical Writer",
        "emoji": "📝",
        "desc": "CVSS-Scoring, Remediation, Executive Summary",
        "prompt": """Du bist ein Technical Writer für Pentest-Reports nach BSI/OWASP Standard.
STRUKTUR:
1. Executive Summary (nicht-technisch, Risiko-basiert)
2. Technical Details (Proof-of-Concept, Schritte)
3. Remediation (konkrete Fix-Vorschläge mit Code)
4. CVSS 3.1 Scoring (Vektor + Berechnung)
FORMAT:
- Markdown für GitHub/GitLab
- Tabellen für Vergleiche
- Code-Blocks für PoCs"""
    },
    "audit": {
        "name": "[Audit] Code Auditor",
        "emoji": "🔐",
        "desc": "Sicherheits-Review, Bug-Bounty Pattern",
        "prompt": """Du bist ein Security Code Auditor für Python und Web-Applikationen.
FOKUS:
- OWASP Top 10 Patterns erkennen
- Input Validation, Auth, Session Management
- Race Conditions, File Inclusions, Deserialization
- False-Positive Reduktion durch Context-Analyse
OUTPUT:
- Zeilennummern referenzieren
- CWE-IDs nennen
- Fix-Vorschläge mit Diff-Format"""
    },
    "network": {
        "name": "[Network] Pentester", 
        "emoji": "🌐",
        "desc": "Infrastruktur, AD, Lateral Movement",
        "prompt": """Du bist ein Network Penetration Tester mit Fokus auf Active Directory und Infrastruktur.
SPEZIALISIERUNG:
- Active Directory Enumeration und Angriffe
- Lateral Movement Techniken
- Network Protocol Analysis
- Pivoting und Tunneling
TOOLS:
- impacket, bloodhound, crackmapexec
- nmap, responder, mitm6
- chisel, ligolo-ng, sshuttle"""
    },
    "redteam": {
        "name": "[RedTeam] Operator",
        "emoji": "🕵️",
        "desc": "Adversary Simulation, APT TTPs",
        "prompt": """Du bist ein Red Team Operator für Adversary Simulation.
FOKUS:
- APT Tactics, Techniques, Procedures (TTPs)
- OPSEC und Anti-Forensics
- Command & Control Infrastruktur
- Social Engineering und Phishing
FRAMEWORKS:
- MITRE ATT&CK Mapping
- Cyber Kill Chain
- Unified Kill Chain"""
    }
}

def check_kimi_cli():
    """Prüft ob kimi CLI installiert ist"""
    try:
        subprocess.run(["kimi", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_kimi_logged_in():
    """Prüft ob Session existiert"""
    kimi_dir = Path.home() / ".kimi"
    return kimi_dir.exists()

def get_api_key():
    """Holt API Key aus Umgebungsvariable oder .env"""
    api_key = os.environ.get('KIMI_API_KEY')
    if api_key:
        return api_key
    
    # Versuche .env Datei
    env_paths = [
        Path(__file__).parent.parent / ".env",
        Path.cwd() / ".env"
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            content = env_path.read_text()
            import re
            match = re.search(r'export KIMI_API_KEY="([^"]+)"', content)
            if match:
                return match.group(1)
    
    return None

def query_kimi_api(prompt, system_prompt, model="kimi-k2.5", temperature=0.7):
    """Sendet Query an Kimi API"""
    if not REQUESTS_AVAILABLE:
        console.print("[red]requests nicht installiert. Installiere: pip install requests[/red]")
        return None
    
    api_key = get_api_key()
    if not api_key:
        console.print("[red]KIMI_API_KEY nicht gesetzt![/red]")
        console.print("[dim]Führe aus: python scripts/setup_wizard.py[/dim]")
        return None
    
    url = "https://api.moonshot.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 4096
    }
    
    try:
        with console.status("[cyan]Frage Kimi...[/cyan]"):
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        console.print(f"[red]API Fehler: {e}[/red]")
        return None

def query_kimi_cli(prompt, persona):
    """Nutzt lokale kimi CLI"""
    if not check_kimi_cli():
        console.print("[red]kimi CLI nicht installiert![/red]")
        console.print("[dim]Installiere: pip install kimi-cli[/dim]")
        return None
    
    if not check_kimi_logged_in():
        console.print("[red]Nicht bei kimi CLI eingeloggt![/red]")
        console.print("[dim]Führe aus: kimi login[/dim]")
        return None
    
    system_prompt = PERSONAS.get(persona, {}).get("prompt", "")
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    
    try:
        result = subprocess.run(
            ["kimi", "ask"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        console.print("[red]Timeout - Kimi CLI hat nicht rechtzeitig geantwortet[/red]")
        return None
    except Exception as e:
        console.print(f"[red]CLI Fehler: {e}[/red]")
        return None

def interactive_mode(use_cli=False):
    """Interaktiver Modus mit Context-Erhaltung"""
    console.print(Panel.fit(
        f"Zen-AI Kimi Helper - Interactive Mode\n"
        f"Mode: {'CLI' if use_cli else 'API'}\n"
        "Befehle: /recon, /exploit, /report, /audit, /network, /red, /clear, /exit",
        title="Interactive", border_style="cyan"
    ))
    
    current_persona = "recon"
    history = []
    
    while True:
        try:
            user_input = console.input(f"[bold cyan]{current_persona}>[/bold cyan] ").strip()
            
            if user_input.startswith("/"):
                cmd = user_input[1:].lower()
                
                if cmd == "exit":
                    break
                elif cmd == "clear":
                    history.clear()
                    console.clear()
                    continue
                elif cmd in PERSONAS:
                    current_persona = cmd
                    console.print(f"[green]Gewechselt zu:[/green] {PERSONAS[cmd]['emoji']} {PERSONAS[cmd]['name']}")
                    continue
                else:
                    console.print("[red]Unbekannter Befehl[/red]")
                    continue
            
            if not user_input:
                continue
            
            # Füge History hinzu für Context
            context = "\n".join(history[-3:]) if history else ""
            full_prompt = f"Context:\n{context}\n\nNeue Anfrage:\n{user_input}" if context else user_input
            
            system_prompt = PERSONAS[current_persona]["prompt"]
            
            if use_cli:
                response = query_kimi_cli(full_prompt, current_persona)
            else:
                response = query_kimi_api(full_prompt, system_prompt)
            
            if response:
                console.print(Markdown(response))
                history.append(f"Q: {user_input}\nA: {response[:200]}...")
                    
        except KeyboardInterrupt:
            break
        except EOFError:
            break
    
    console.print("[dim]Auf Wiedersehen![/dim]")

def main():
    parser = argparse.ArgumentParser(
        description="Kimi AI Helper für Zen-AI-Pentest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # API Mode (Standard)
  %(prog)s -p recon "Analysiere example.com"
  %(prog)s -p exploit "SQLi-Scanner schreiben"
  %(prog)s -p report "CVSS-Bericht erstellen"
  
  # CLI Mode (lokale kimi CLI)
  %(prog)s --cli -p recon
  
  # Interaktiver Modus
  %(prog)s -i
  %(prog)s --cli -i
        """
    )
    
    parser.add_argument("prompt", nargs="?", help="Die Anfrage/Prompt")
    parser.add_argument("-p", "--persona", choices=list(PERSONAS.keys()), 
                       default="recon", help="Pentest Persona (default: recon)")
    parser.add_argument("--cli", action="store_true",
                       help="Nutze lokale kimi CLI statt API")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Interaktiver Modus")
    parser.add_argument("-t", "--temperature", type=float, default=0.7,
                       help="Temperature 0.0-1.0 (default: 0.7)")
    parser.add_argument("-m", "--model", default="kimi-k2.5",
                       help="Model für API Mode (default: kimi-k2.5)")
    parser.add_argument("--login", action="store_true",
                       help="Bei kimi CLI einloggen")
    parser.add_argument("--check", action="store_true",
                       help="Status prüfen")
    parser.add_argument("--list", action="store_true",
                       help="Personas auflisten")
    
    args = parser.parse_args()
    
    # Login
    if args.login:
        if check_kimi_cli():
            console.print("🔐 Starte kimi login...")
            subprocess.run(["kimi", "login"])
        else:
            console.print("[red]kimi CLI nicht installiert: pip install kimi-cli[/red]")
        return
    
    # Check
    if args.check:
        console.print(Panel("Kimi Status Check", border_style="cyan"))
        
        # CLI Status
        if check_kimi_cli():
            console.print("[green]OK[/green] Kimi CLI installiert")
            if check_kimi_logged_in():
                console.print("[green]OK[/green] Kimi CLI eingeloggt")
            else:
                console.print("[yellow]WARN[/yellow] Kimi CLI nicht eingeloggt")
        else:
            console.print("[red]ERR[/red] Kimi CLI nicht installiert")
        
        # API Status
        api_key = get_api_key()
        if api_key:
            console.print("[green]OK[/green] API Key konfiguriert")
        else:
            console.print("[red]ERR[/red] API Key nicht konfiguriert")
            console.print("[dim]  Führe aus: python scripts/setup_wizard.py[/dim]")
        return
    
    # List
    if args.list:
        console.print("[bold]Verfügbare Personas:[/bold]")
        for key, data in PERSONAS.items():
            console.print(f"  {data['emoji']} [cyan]{key:10}[/cyan] {data['name']} - {data['desc']}")
        return
    
    # Interaktiver Modus
    if args.interactive:
        interactive_mode(use_cli=args.cli)
        return
    
    # Normaler One-Shot Modus
    if not args.prompt:
        parser.print_help()
        return
    
    system_prompt = PERSONAS[args.persona]["prompt"]
    
    console.print(Panel(
        f"{PERSONAS[args.persona]['emoji']} [bold]{PERSONAS[args.persona]['name']}[/bold]\n"
        f"Mode: {'CLI' if args.cli else 'API'}",
        border_style="cyan"
    ))
    
    if args.cli:
        response = query_kimi_cli(args.prompt, args.persona)
    else:
        response = query_kimi_api(args.prompt, system_prompt, model=args.model, temperature=args.temperature)
    
    if response:
        console.print(Markdown(response))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Abgebrochen.[/dim]")
        sys.exit(0)
