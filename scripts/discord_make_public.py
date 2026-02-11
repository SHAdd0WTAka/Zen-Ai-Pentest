#!/usr/bin/env python3
"""
Discord Server - Make Public
Setzt den Discord-Server auf oeffentlich sichtbar
"""

import requests
import json
import sys
import getpass

# === KONFIGURATION ===
GUILD_ID = "1470531751595086017"
API_BASE = "https://discord.com/api/v10"

# === FUNKTIONEN ===

def update_server_settings(token):
    """Aktualisiert die Server-Einstellungen fuer oeffentliche Sichtbarkeit"""
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    print("[INFO] Aktualisiere Server-Einstellungen...")
    
    # 1. Server-Details abrufen
    url = f"{API_BASE}/guilds/{GUILD_ID}"
    
    # Community-Features aktivieren
    community_settings = {
        "features": ["COMMUNITY"],
        "default_message_notifications": 0,  # Nur @mentions
        "verification_level": 1,  # E-Mail-Verifizierung erforderlich
        "explicit_content_filter": 2,  # Für alle scanen
    }
    
    response = requests.patch(url, headers=headers, json=community_settings)
    
    if response.status_code == 200:
        print("[OK] Community-Features aktiviert")
    else:
        print(f"[WARN] Community-Features: {response.status_code}")
        print(response.text)
    
    # 2. Community-Status aktivieren (für Discoverable)
    community_url = f"{API_BASE}/guilds/{GUILD_ID}/community"
    
    community_payload = {
        "enabled": True,
        "default_channel_id": None,  # Wird automatisch gesetzt
        "description": "Professional AI-Powered Penetration Testing Framework - Community",
        "preferred_locale": "en-US"
    }
    
    response = requests.put(community_url, headers=headers, json=community_payload)
    
    if response.status_code == 200:
        print("[OK] Community-Status aktiviert")
    else:
        print(f"[WARN] Community-Status: {response.status_code}")
        print(response.text)
    
    # 3. Vanity URL prüfen/aktualisieren
    vanity_url = f"{API_BASE}/guilds/{GUILD_ID}/vanity-url"
    
    response = requests.get(vanity_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        current_code = data.get('code', 'N/A')
        print(f"[OK] Vanity URL: discord.gg/{current_code}")
    else:
        print(f"[WARN] Vanity URL konnte nicht geprueft werden: {response.status_code}")
    
    return True


def create_invite(token, max_age=0, max_uses=0):
    """Erstellt einen permanenten Einladungslink"""
    
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    # Ersten Text-Channel finden
    channels_url = f"{API_BASE}/guilds/{GUILD_ID}/channels"
    response = requests.get(channels_url, headers=headers)
    
    if response.status_code != 200:
        print(f"[ERROR] Fehler beim Abrufen der Channels: {response.status_code}")
        return None
    
    channels = response.json()
    text_channel = None
    
    for channel in channels:
        if channel['type'] == 0:  # Text channel
            text_channel = channel['id']
            break
    
    if not text_channel:
        print("[ERROR] Kein Text-Channel gefunden")
        return None
    
    # Einladung erstellen
    invite_url = f"{API_BASE}/channels/{text_channel}/invites"
    
    payload = {
        "max_age": max_age,  # 0 = nie ablaufen
        "max_uses": max_uses,  # 0 = unbegrenzt
        "temporary": False,
        "unique": False
    }
    
    response = requests.post(invite_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        invite_code = data['code']
        print(f"[OK] Einladungslink erstellt: https://discord.gg/{invite_code}")
        return invite_code
    else:
        print(f"[ERROR] Fehler beim Erstellen der Einladung: {response.status_code}")
        print(response.text)
        return None


def main():
    print("=" * 60)
    print(">> Discord Server - Oeffentlich machen")
    print("=" * 60)
    print()
    
    # Token eingeben
    token = getpass.getpass("Bot Token eingeben: ")
    
    if not token:
        print("[ERROR] Kein Token eingegeben")
        sys.exit(1)
    
    print()
    print("[INFO] Starte Konfiguration...")
    print()
    
    try:
        # Server-Einstellungen aktualisieren
        update_server_settings(token)
        
        print()
        
        # Permanenten Einladungslink erstellen
        print("[INFO] Erstelle permanenten Einladungslink...")
        invite_code = create_invite(token, max_age=0, max_uses=0)
        
        print()
        print("=" * 60)
        print("[OK] API-Konfiguration abgeschlossen!")
        print("=" * 60)
        print()
        
        if invite_code:
            print(f"[INFO] Neuer Einladungslink: https://discord.gg/{invite_code}")
        
        print()
        print("[WARN] WICHTIG - Manuelle Schritte erforderlich:")
        print("   1. Discord öffnen → Server auswählen")
        print("   2. Server-Einstellungen → Community")
        print("   3. 'Server Discovery' aktivieren")
        print("   4. Kategorie & Tags setzen")
        print("   5. Speichern")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
