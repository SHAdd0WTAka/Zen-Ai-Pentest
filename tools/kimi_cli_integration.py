#!/usr/bin/env python3
"""
Kimi CLI Integration für Zen-Ai-Pentest
Nutzt die lokale kimi CLI mit Session-Auth
"""

import subprocess
import sys
import os
from pathlib import Path

PERSONAS = {
    "recon": "🔍 OSINT Specialist - Fokus auf Reconnaissance, Subdomains, Ports",
    "exploit": "💣 Exploit Developer - Fokus auf Python-Exploits, POCs",
    "report": "📝 Technical Writer - Fokus auf CVSS, Remediation, Reports",
    "audit": "🔐 Code Auditor - Fokus auf Security Review, Bug Bounty",
    "network": "🌐 Network Pentester - Infrastruktur, AD, Lateral Movement",
    "redteam": "🕵️ Red Team Operator - Adversary Simulation, APT TTPs"
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
    # Prüfe ob .kimi Verzeichnis existiert (Session-Daten)
    kimi_dir = Path.home() / ".kimi"
    return kimi_dir.exists()

def start_kimi_with_context(persona, context=""):
    """Startet kimi mit Persona-Context"""
    
    # Prompt vorbereiten
    if persona in PERSONAS:
        system_prompt = f"Du bist ein {PERSONAS[persona]}. "
        full_prompt = f"{system_prompt}\n\n{context}"
    else:
        full_prompt = context
    
    print(f"🧠 Starte Kimi mit Persona: {persona}")
    print(f"💡 Tipp: Nutze /help für Commands, /exit zum Beenden\n")
    
    # kimi starten (interaktiv)
    try:
        subprocess.run(["kimi"], input=full_prompt + "\n", text=True)
    except KeyboardInterrupt:
        pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Kimi CLI Integration")
    parser.add_argument("context", nargs="?", help="Initialer Prompt/Context")
    parser.add_argument("-p", "--persona", choices=list(PERSONAS.keys()), 
                       default="recon", help="Pentest Persona")
    parser.add_argument("--login", action="store_true", help="Login durchführen")
    parser.add_argument("--check", action="store_true", help="Status prüfen")
    
    args = parser.parse_args()
    
    # Check Installation
    if not check_kimi_installed():
        print("❌ kimi CLI nicht installiert!")
        print("Installiere: pip install kimi-cli")
        print("Dann: kimi login")
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
        else:
            print("⚠️  Keine Session gefunden. Führe aus:")
            print("   kimi login")
            print("   Oder: python3 tools/kimi_cli_integration.py --login")
        return
    
    if not check_kimi_logged_in():
        print("⚠️  Nicht eingeloggt!")
        print("Führe zuerst aus: python3 tools/kimi_cli_integration.py --login")
        sys.exit(1)
    
    # Kimi starten
    start_kimi_with_context(args.persona, args.context or "")

if __name__ == "__main__":
    main()
