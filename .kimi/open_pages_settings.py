#!/usr/bin/env python3
"""Open GitHub Pages settings for manual configuration"""

import webbrowser
import os
import sys

REPO_OWNER = "SHAdd0WTAka"
REPO_NAME = "Zen-Ai-Pentest"

# Direct link to Pages settings
pages_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/settings/pages"

print("=" * 70)
print(" GITHUB PAGES MANUAL CONFIGURATION REQUIRED")
print("=" * 70)
print()
print(f"Opening: {pages_url}")
print()
print("=" * 70)
print(" ANLEITUNG (3 Schritte):")
print("=" * 70)
print()
print("1. Unter 'Build and deployment' > 'Source'")
print("   Klicke auf das Dropdown (aktuell: 'master')")
print()
print("2. Wähle aus:")
print("   Branch: main")
print("   Folder: /docs")
print()
print("3. Klicke den blauen 'Save' Button")
print()
print("=" * 70)
print(" Danach: Warte 2-3 Minuten für den Build")
print(" Teste:  https://shadd0wtaka.github.io/Zen-Ai-Pentest/")
print("=" * 70)

# Open browser
try:
    webbrowser.open(pages_url)
    print("\n✅ Browser wurde geöffnet!")
except Exception as e:
    print(f"\n⚠️  Browser konnte nicht automatisch geöffnet werden.")
    print(f"   Bitte öffne die URL manuell.")
