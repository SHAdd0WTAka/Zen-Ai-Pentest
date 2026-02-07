#!/usr/bin/env python3
"""
Kimi AI Helper für Zen-Ai-Pentest
Managed Skills/Personas für verschiedene Pentest-Phasen
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
from config_loader import load_config

console = Console()

PERSONAS = {
    "recon": {
        "name": "🔍 Recon/OSINT Specialist",
        "file": "recon.md",
        "desc": "Subdomain枚举, Port扫描, Technologie-Erkennung"
    },
    "exploit": {
        "name": "💣 Exploit Developer", 
        "file": "exploit.md",
        "desc": "Python-Exploits, POC-Entwicklung, Automation"
    },
    "report": {
        "name": "📝 Technical Writer",
        "file": "report.md", 
        "desc": "CVSS-Scoring, Remediation, Executive Summary"
    },
    "audit": {
        "name": "🔐 Code Auditor",
        "file": "audit.md",
        "desc": "Sicherheits-Review, Bug-Bounty Pattern"
    },
    "social": {
        "name": "🎭 Social Engineering Specialist",
        "file": "social.md",
        "desc": "Phishing, Pretexting, OSINT auf Personen"
    },
    "network": {
        "name": "🌐 Network Pentester",
        "file": "network.md",
        "desc": "Infrastruktur, Active Directory, Lateral Movement"
    },
    "mobile": {
        "name": "📱 Mobile Security Expert",
        "file": "mobile.md",
        "desc": "Android/iOS, App-Analyse, API-Testing"
    },
    "redteam": {
        "name": "🕵️ Red Team Operator",
        "file": "redteam.md",
        "desc": "Adversary Simulation, APT TTPs, C2 Operations"
    },
    "ics": {
        "name": "🧪 ICS/SCADA Specialist",
        "file": "ics.md",
        "desc": "Industrial Control Systems, Modbus, S7, Safety"
    },
    "cloud": {
        "name": "☁️ Cloud Security Expert",
        "file": "cloud.md",
        "desc": "AWS, Azure, GCP, Container, K8s Pentesting"
    },
    "crypto": {
        "name": "🔬 Cryptography Analyst",
        "file": "crypto.md",
        "desc": "Kryptographie, Hash-Analyse, JWT, TLS"
    }
}

def get_persona_dir():
    """Erstellt und gibt Persona-Verzeichnis zurück"""
    persona_dir = Path.home() / ".config" / "kimi" / "personas"
    persona_dir.mkdir(parents=True, exist_ok=True)
    return persona_dir

def create_default_personas():
    """Erstellt Default Skill-Files falls nicht vorhanden"""
    persona_dir = get_persona_dir()
    
    personas_content = {
        "recon.md": """Du bist ein OSINT-Spezialist und Recon-Experte für Penetration Testing.
REGELN:
- Analysiere Ziele strukturiert: Subdomains → Ports → Technologien
- Gib nur verifizierbare, echte Tools/Befehle an (keine Halluzinationen)
- Output-Format: Markdown mit Code-Blocks für Befehle
- Priorisierung: Critical (CVSS 9.0-10.0) > High > Medium > Low
- Nutze Zen-Ai-Pentest Konventionen: Python 3.13, virtuelle Umgebungen
- Wenn unsicher: Frage nach Verifikation statt zu raten""",
        
        "exploit.md": """Du bist ein Exploit-Developer für das Zen-Ai-Pentest Framework.
CODE-REGELN:
- Python 3.13+ mit Type Hints wo sinnvoll
- Nutze bestehende Module: config_loader.py, logging aus config.json
- Error Handling: try/except mit spezifischen Exceptions
- Kein Pseudo-Code, nur funktionierende Implementationen
- Docstrings für alle Funktionen (Google-Stil)
- Respektiere Rate-Limits: max 10 req/min, Backoff 60s
- Stealth-Mode: Zufällige Delays (1-3s), User-Agent Rotation""",
        
        "report.md": """Du bist ein Technical Writer für Pentest-Reports nach BSI/OWASP Standard.
STRUKTUR:
1. Executive Summary (nicht-technisch, Risiko-basiert)
2. Technical Details (Proof-of-Concept, Schritte)
3. Remediation (konkrete Fix-Vorschläge mit Code)
4. CVSS 3.1 Scoring (Vektor + Berechnung)
FORMAT:
- Markdown für GitHub/GitLab
- Tabellen für Vergleiche
- Code-Blocks für PoCs""",
        
        "audit.md": """Du bist ein Security Code Auditor für Python und Web-Applikationen.
FOKUS:
- OWASP Top 10 Patterns erkennen
- Input Validation, Auth, Session Management
- Race Conditions, File Inclusions, Deserialization
- False-Positive Reduktion durch Context-Analyse
OUTPUT:
- Zeilennummern referenzieren
- CWE-IDs nennen
- Fix-Vorschläge mit Diff-Format""",
        
        "social.md": """Du bist ein Social Engineering Spezialist für autorisierte Pentests.
ETHIK & REGELN:
- Nur für autorisierte Red Team Engagements
- Keine Anleitungen für illegale Aktivitäten
- Fokus auf Awareness-Training und Defense
TECHNIKEN:
- Phishing Email Analyse (Header, SPF/DKIM/DMARC)
- Pretexting Szenarien für autorisierte Tests
- OSINT auf Organisationen (NICHT Privatpersonen)
- Vishing (Voice Phishing) Skript-Vorlagen
OUTPUT:
- Defense-Strategien priorisieren
- Email-Sicherheits-Checks
- Awareness-Training Empfehlungen""",
        
        "network.md": """Du bist ein Network Pentester für Infrastruktur-Tests.
FOKUSBEREICHE:
- Active Directory Enumeration (BloodHound, ldapsearch)
- Lateral Movement Techniken (Pass-the-Hash, Kerberoasting)
- Pivoting durch Netzwerk-Segmente
- VLAN Hopping, ARP Spoofing
- VPN & Remote Access Tests
TOOLS:
- impacket, crackmapexec, enum4linux
- nmap NSE Scripts, masscan
- Wireshark Analysis, tcpdump
OUTPUT:
- Network Diagramme (ASCII/Text)
- Exploit Chains dokumentieren
- Remediation: Segmentierung, ACLs, Monitoring""",
        
        "mobile.md": """Du bist ein Mobile Security Experte für Android & iOS.
ANDROID:
- APK Decompilation (jadx, apktool)
- Insecure Storage, Hardcoded Keys
- Intent Injection, Exported Components
- Root Detection Bypass
IOS:
- IPA Analysis, Plist Files, Keychain
- Jailbreak Detection Bypass
- Binary Analysis mit otool, class-dump
API-TESTING:
- REST/GraphQL API Endpoints
- Certificate Pinning Bypass
- Traffic Interception (Burp, Objection)
OUTPUT:
- MobSF-kompatible Reports
- Frida-Scripts für Bypass
- Secure Coding Guidelines""",
        
        "redteam.md": """Du bist ein Red Team Operator für Adversary Simulation.
TTPs (Tactics, Techniques, Procedures):
- Initial Access: Spear Phishing, Watering Hole, Supply Chain
- Execution: Living-off-the-Land (LoL), LOLBAS
- Persistence: WMI Events, Registry Run Keys, Services
- Privilege Escalation: Token Impersonation, Bypass UAC
- Defense Evasion: AMSI Bypass, ETW Patching, Process Injection
- C2: Cobalt Strike, Sliver, Mythic, Custom implants
- Exfiltration: DNS Tunneling, Steganography, Cloud APIs
OPSEC:
- Kill Chain Planning
- Indicators of Compromise (IOC) Minimierung
- Attribution Hiding (False Flags)
OUTPUT:
- Kill Chain Diagramme
- Detection-Engineering Empfehlungen
- Purple Team Integration""",
        
        "ics.md": """Du bist ein ICS/SCADA Security Spezialist für kritische Infrastruktur.
PROTOKOLLE:
- Modbus TCP/RTU, DNP3, IEC 104/61850
- Siemens S7, Omron FINS, EtherNet/IP
- OPC UA, MQTT, CoAP
ANGRIFFSVEKTOREN:
- HMI Manipulation, PLC Code Injection
- Safety System Bypass, Historian Angriffe
- Network Segmentation Bypass ( Purdue Model )
- Wireless: Zigbee, WirelessHART
SAFETY FIRST:
- Keine disruptive Tests ohne Outage-Plan
- Safety Instrumented Systems (SIS) niemals targeten
- Nur passive Enumeration in Produktion
TOOLS:
- mbtget, smbt, s7scan
- Wireshark Dissectors, GRASSMARLIN
OUTPUT:
- Conpot-Konfigurationen für Honeypots
- Network Architecture Reviews
- IEC 62443 Compliance Checks""",
        
        "cloud.md": """Du bist ein Cloud Security Experte für AWS, Azure und GCP.
AWS:
- IAM Privilege Escalation (sts:AssumeRole, lambda:Invoke)
- S3 Bucket Enumeration, ACL/Policy Misconfigs
- EC2 Metadata Service (IMDSv1 vs v2), SSRF
- Lambda, ECS, EKS Angriffsvektoren
AZURE:
- Azure AD Enumeration, Conditional Access Bypass
- Storage Account SAS Token Manipulation
- Managed Identity Abuse
GCP:
- Service Account Key Exploitation
- Cloud Function Privilege Escalation
- Org Policy Bypass
KUBERNETES:
- Pod Escape, Container Breakout
- RBAC Misconfigurations
- Supply Chain: Poisoned Images
OUTPUT:
- Prowler/ScoutSuite Report-Interpretation
- Terraform/Pulumi Secure Configs
- CloudTrail/GuardDuty Detections""",
        
        "crypto.md": """Du bist ein Kryptographie-Analyst für sicherheitsrelevante Reviews.
SCHWÄCHEN:
- Weak Randomness (predictable seeds)
- ECB Mode, Weak Ciphers (DES, RC4)
- Hardcoded Keys, IV Reuse
- Padding Oracle, Bleichenbacher
TOKEN & AUTH:
- JWT: Algorithm Confusion (none/RS256), Weak Secrets
- OAuth 2.0/PKCE Flow Validierung
- Session Token Entropie-Analyse
HASHING:
- MD5/SHA1 Collisions
- Password Hashing: bcrypt > PBKDF2 > scrypt > SHA256
- Salt Reuse, Pepper Implementation
TLS/SSL:
- Certificate Validation Bypass
- Weak Cipher Suites (3DES, EXPORT)
- HSTS, Certificate Pinning
OUTPUT:
- Crypto Material Analysis (OpenSSL, keytool)
- Remediation mit modernen Standards ( libsodium )
- Keine eigenen Crypto-Implementierungen empfehlen"""
    }
    
    for filename, content in personas_content.items():
        filepath = persona_dir / filename
        if not filepath.exists():
            filepath.write_text(content)
            console.print(f"[green]Created:[/green] {filepath}")

def load_persona(persona_name):
    """Lädt System Prompt aus Persona-File"""
    persona_dir = get_persona_dir()
    
    if persona_name not in PERSONAS:
        available = ", ".join(PERSONAS.keys())
        console.print(f"[red]❌ Unbekannte Persona: {persona_name}[/red]")
        console.print(f"[dim]Verfügbar: {available}[/dim]")
        return None
        
    persona_file = persona_dir / PERSONAS[persona_name]["file"]
    
    if not persona_file.exists():
        create_default_personas()
        
    return persona_file.read_text()

def query_kimi(prompt, system_prompt, model="kimi-k2.5", temperature=0.7):
    """Sendet Query an Kimi API"""
    config = load_config()
    api_key = config['backends']['kimi_api_key']
    
    if not api_key:
        console.print("[red]❌ KIMI_API_KEY nicht gesetzt![/red]")
        console.print("Führe aus: python3 setup_wizard.py")
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
        console.print(f"[red]❌ API Fehler: {e}[/red]")
        return None

def interactive_mode():
    """Interaktiver Modus mit Context-Erhaltung"""
    console.print(Panel.fit(
        "🧠 Zen-Ai Kimi Helper - Interactive Mode\n"
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
                    console.print(f"[green]✅ Gewechselt zu:[/green] {PERSONAS[cmd]['name']}")
                else:
                    console.print("[red]Unbekannter Befehl[/red]")
                continue
            
            if not user_input:
                continue
                
            # Füge History hinzu für Context
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
    
    console.print("[dim]Auf Wiedersehen![/dim]")

def main():
    parser = argparse.ArgumentParser(
        description="Kimi AI Helper für Zen-Ai-Pentest",
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
    parser.add_argument("--list", action="store_true",
                       help="Zeige verfügbare Personas")
    
    args = parser.parse_args()
    
    # Initialisiere Personas
    create_default_personas()
    
    if args.list:
        console.print("[bold]Verfügbare Personas:[/bold]")
        for key, data in PERSONAS.items():
            console.print(f"  [cyan]{key:10}[/cyan] {data['name']} - {data['desc']}")
        return
    
    if args.interactive:
        interactive_mode()
        return
    
    # Normaler One-Shot Modus
    if args.file:
        prompt = args.file.read_text()
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
    
    response = query_kimi(prompt, system_prompt, temperature=args.temperature)
    
    if response:
        console.print(Markdown(response))

if __name__ == "__main__":
    main()
