#!/usr/bin/env python3
"""
Kimi CLI Integration für Zen-Ai-Pentest
Nutzt die lokale kimi CLI mit Session-Auth
"""

import subprocess
import sys
from pathlib import Path

PERSONAS = {
    "recon": "🔍 OSINT Specialist - Fokus auf Reconnaissance, Subdomains, Ports",
    "exploit": "💣 Exploit Developer - Fokus auf Python-Exploits, POCs",
    "report": "📝 Technical Writer - Fokus auf CVSS, Remediation, Reports",
    "audit": "🔐 Code Auditor - Fokus auf Security Review, Bug Bounty",
    "network": "🌐 Network Pentester - Infrastruktur, AD, Lateral Movement",
    "redteam": "🕵️ Red Team Operator - Adversary Simulation, APT TTPs",
}


def check_kimi_installed():
    """Prüft ob kimi CLI installiert ist"""
    try:
        subprocess.run(["kimi", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_kimi_logged_in():
    """Prüft ob Session existiert (via kimi status oder einfacher Test)"""
    kimi_dir = Path.home() / ".kimi"
    return kimi_dir.exists()


def start_kimi_with_persona(persona, context=""):
    """Startet kimi mit Persona-Context"""

    if persona not in PERSONAS:
        persona = "recon"

    persona_desc = PERSONAS[persona]

    print(f"""
{'='*60}
🧠 ZEN-KIMI PENTEST CLI
{'='*60}
Persona: {persona_desc}
{'='*60}
💡 Befehle: /help - Hilfe | /exit - Beenden | /clear - Clear
{'='*60}
""")

    # Erste Nachricht vorbereiten (Persona als Kontext)
    if context:
        initial_message = f"[Als {persona}] {context}"
    else:
        initial_message = f"Ich bin bereit als {persona_desc}. Was möchtest du tun?"

    # kimi starten (interaktiv) mit initialer Nachricht
    try:
        subprocess.run(["kimi"], input=initial_message + "\n", text=True)
    except KeyboardInterrupt:
        print("\n👋 Beendet.")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Zen-Kimi Pentest CLI - Kimi CLI mit Pentest-Personas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  zen-kimi -p recon "Scanne example.com"     # One-shot mit Prompt
  zen-kimi -p exploit                         # Interaktiver Chat
  zlogin                                      # Bei kimi einloggen
        """,
    )
    parser.add_argument("context", nargs="?", help="Initialer Prompt/Context")
    parser.add_argument(
        "-p", "--persona", choices=list(PERSONAS.keys()), default="recon", help="Pentest Persona (default: recon)"
    )
    parser.add_argument("--login", action="store_true", help="Login durchführen")
    parser.add_argument("--check", action="store_true", help="Status prüfen")
    parser.add_argument("--list-personas", action="store_true", help="Zeige alle Personas")

    args = parser.parse_args()

    # Zeige Personas
    if args.list_personas:
        print("🎭 Verfügbare Personas:")
        for key, desc in PERSONAS.items():
            print(f"  -p {key:<10} {desc}")
        return

    # Check Installation
    if not check_kimi_installed():
        print("❌ kimi CLI nicht installiert!")
        print("📦 Installiere: pip install kimi-cli")
        print("🔐 Dann: kimi login  oder  zlogin")
        sys.exit(1)

    # Login Check
    if args.login:
        print("🔐 Starte kimi Login...")
        subprocess.run(["kimi", "login"])
        return

    if args.check:
        if check_kimi_logged_in():
            print("✅ Kimi CLI ist installiert und konfiguriert")
            print("📁 Session-Daten gefunden in ~/.kimi")
            print("\n🎭 Verfügbare Personas:")
            for key, desc in PERSONAS.items():
                print(f"   {key:<10} - {desc.split(' - ')[1]}")
        else:
            print("⚠️  Keine Session gefunden.")
            print("   Führe aus: zlogin")
        return

    if not check_kimi_logged_in():
        print("⚠️  Nicht eingeloggt!")
        print("   Führe zuerst aus: zlogin")
        sys.exit(1)

    # Kimi starten
    start_kimi_with_persona(args.persona, args.context or "")


if __name__ == "__main__":
    main()
