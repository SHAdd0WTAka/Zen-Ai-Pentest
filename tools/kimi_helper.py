#!/usr/bin/env python3
"""
Kimi AI Helper fuer Zen-Ai-Pentest
Managed Skills/Personas fuer verschiedene Pentest-Phasen
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import requests

# Add parent to path for config_loader
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from config_loader import load_config
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False

console = Console()

PERSONAS = {
    "recon": {
        "name": "[Recon] OSINT Specialist",
        "file": "recon.md",
        "desc": "Subdomain-Enum, Port-Scanning, Technologie-Erkennung"
    },
    "exploit": {
        "name": "[Exploit] Developer", 
        "file": "exploit.md",
        "desc": "Python-Exploits, POC-Entwicklung, Automation"
    },
    "report": {
        "name": "[Report] Technical Writer",
        "file": "report.md", 
        "desc": "CVSS-Scoring, Remediation, Executive Summary"
    },
    "audit": {
        "name": "[Audit] Code Auditor",
        "file": "audit.md",
        "desc": "Sicherheits-Review, Bug-Bounty Pattern"
    }
}

def get_persona_dir():
    """Erstellt und gibt Persona-Verzeichnis zurueck"""
    persona_dir = Path.home() / ".config" / "kimi" / "personas"
    persona_dir.mkdir(parents=True, exist_ok=True)
    return persona_dir

def create_default_personas():
    """Erstellt Default Skill-Files falls nicht vorhanden"""
    persona_dir = get_persona_dir()
    
    personas_content = {
        "recon.md": """Du bist ein OSINT-Spezialist und Recon-Experte fuer Penetration Testing.
REGELN:
- Analysiere Ziele strukturiert: Subdomains -> Ports -> Technologien
- Gib nur verifizierbare, echte Tools/Befehle an (keine Halluzinationen)
- Output-Format: Markdown mit Code-Blocks fuer Befehle
- Priorisierung: Critical (CVSS 9.0-10.0) > High > Medium > Low
- Nutze Zen-Ai-Pentest Konventionen: Python 3.13, virtuelle Umgebungen
- Wenn unsicher: Frage nach Verifikation statt zu raten""",
        
        "exploit.md": """Du bist ein Exploit-Developer fuer das Zen-Ai-Pentest Framework.
CODE-REGELN:
- Python 3.13+ mit Type Hints wo sinnvoll
- Nutze bestehende Module: config_loader.py, logging aus config.json
- Error Handling: try/except mit spezifischen Exceptions
- Kein Pseudo-Code, nur funktionierende Implementationen
- Docstrings fuer alle Funktionen (Google-Stil)
- Respektiere Rate-Limits: max 10 req/min, Backoff 60s
- Stealth-Mode: Zufaellige Delays (1-3s), User-Agent Rotation""",
        
        "report.md": """Du bist ein Technical Writer fuer Pentest-Reports nach BSI/OWASP Standard.
STRUKTUR:
1. Executive Summary (nicht-technisch, Risiko-basiert)
2. Technical Details (Proof-of-Concept, Schritte)
3. Remediation (konkrete Fix-Vorschlaege mit Code)
4. CVSS 3.1 Scoring (Vektor + Berechnung)
FORMAT:
- Markdown fuer GitHub/GitLab
- Tabellen fuer Vergleiche
- Code-Blocks fuer PoCs""",
        
        "audit.md": """Du bist ein Security Code Auditor fuer Python und Web-Applikationen.
FOKUS:
- OWASP Top 10 Patterns erkennen
- Input Validation, Auth, Session Management
- Race Conditions, File Inclusions, Deserialization
- False-Positive Reduktion durch Context-Analyse
OUTPUT:
- Zeilennummern referenzieren
- CWE-IDs nennen
- Fix-Vorschlaege mit Diff-Format"""
    }
    
    created = []
    for filename, content in personas_content.items():
        filepath = persona_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding='utf-8')
            created.append(filename)
    
    if created:
        console.print(f"[green]Created personas:[/green] {', '.join(created)}")

def load_persona(persona_name):
    """Laedt System Prompt aus Persona-File"""
    persona_dir = get_persona_dir()
    
    if persona_name not in PERSONAS:
        available = ", ".join(PERSONAS.keys())
        console.print(f"[red]Unbekannte Persona: {persona_name}[/red]")
        console.print(f"[dim]Verfuegbar: {available}[/dim]")
        return None
        
    persona_file = persona_dir / PERSONAS[persona_name]["file"]
    
    if not persona_file.exists():
        create_default_personas()
        
    return persona_file.read_text(encoding='utf-8')

def get_api_key():
    """Holt API Key aus Config oder Umgebungsvariable"""
    # Versuche zuerst Umgebungsvariable
    api_key = os.environ.get('KIMI_API_KEY')
    if api_key:
        return api_key
    
    # Dann Config-Loader
    if CONFIG_LOADER_AVAILABLE:
        try:
            config = load_config()
            api_key = config.get('backends', {}).get('kimi_api_key')
            if api_key:
                return api_key
        except:
            pass
    
    # Dann .env Datei
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        content = env_path.read_text()
        import re
        match = re.search(r'export KIMI_API_KEY="([^"]+)"', content)
        if match:
            return match.group(1)
    
    return None

def query_kimi(prompt, system_prompt, model="kimi-k2.5", temperature=0.7):
    """Sendet Query an Kimi API"""
    api_key = get_api_key()
    
    if not api_key:
        console.print("[red]KIMI_API_KEY nicht gesetzt![/red]")
        console.print("Fuehre aus: python setup_wizard.py")
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

def interactive_mode():
    """Interaktiver Modus mit Context-Erhaltung"""
    console.print(Panel.fit(
        "Zen-Ai Kimi Helper - Interactive Mode\n"
        "Befehle: /recon, /exploit, /report, /audit, /clear, /exit",
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
                elif cmd in PERSONAS:
                    current_persona = cmd
                    console.print(f"[green]Gewechselt zu:[/green] {PERSONAS[cmd]['name']}")
                else:
                    console.print("[red]Unbekannter Befehl[/red]")
                continue
            
            if not user_input:
                continue
                
            # Fuege History hinzu fuer Context
            context = "\n".join(history[-3:]) if history else ""
            full_prompt = f"Context:\n{context}\n\nNeue Anfrage:\n{user_input}" if context else user_input
            
            system_prompt = load_persona(current_persona)
            if system_prompt:
                response = query_kimi(full_prompt, system_prompt)
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
        description="Kimi AI Helper fuer Zen-Ai-Pentest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s -p recon "Analysiere example.com"
  %(prog)s -p exploit -f request.txt
  %(prog)s -i                    # Interaktiver Modus
        """
    )
    
    parser.add_argument("prompt", nargs="?", help="Die Anfrage/Prompt")
    parser.add_argument("-p", "--persona", choices=PERSONAS.keys(), 
                       default="recon", help="Skill/Persona (default: recon)")
    parser.add_argument("-f", "--file", type=Path, 
                       help="Lese Prompt aus Datei")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Interaktiver Modus")
    parser.add_argument("-t", "--temperature", type=float, default=0.7,
                       help="Temperature 0.0-1.0 (default: 0.7)")
    parser.add_argument("-m", "--model", default="kimi-k2.5",
                       help="Model (default: kimi-k2.5)")
    parser.add_argument("--list", action="store_true",
                       help="Zeige verfuegbare Personas")
    
    args = parser.parse_args()
    
    # Initialisiere Personas
    create_default_personas()
    
    if args.list:
        console.print("[bold]Verfuegbare Personas:[/bold]")
        for key, data in PERSONAS.items():
            console.print(f"  [cyan]{key:10}[/cyan] {data['name']} - {data['desc']}")
        return
    
    if args.interactive:
        interactive_mode()
        return
    
    # Normaler One-Shot Modus
    if args.file:
        prompt = args.file.read_text(encoding='utf-8')
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        return
    
    system_prompt = load_persona(args.persona)
    if not system_prompt:
        return
        
    console.print(Panel(f"[bold]{PERSONAS[args.persona]['name']}[/bold]", 
                       border_style="cyan"))
    
    response = query_kimi(prompt, system_prompt, model=args.model, temperature=args.temperature)
    
    if response:
        console.print(Markdown(response))

if __name__ == "__main__":
    main()
