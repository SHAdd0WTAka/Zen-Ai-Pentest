#!/usr/bin/env python3
"""
Telegram Bot Test Script
Testet die Telegram-Integration und sendet Testnachrichten
"""

import os
import sys

import requests


def test_connection(token, chat_id):
    """Testet die Verbindung zum Telegram Bot"""
    print("=" * 60)
    print(">> Telegram Bot Connection Test")
    print("=" * 60)
    print()

    # Test 1: Bot Info abrufen
    print("[INFO] Prüfe Bot-Informationen...")
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            bot_info = data["result"]
            print("[OK] Bot gefunden:")
            print(f"     Name: {bot_info.get('first_name')}")
            print(f"     Username: @{bot_info.get('username')}")
            print(f"     ID: {bot_info.get('id')}")
        else:
            print(f"[ERROR] Bot-Fehler: {data.get('description')}")
            return False
    else:
        print(f"[ERROR] HTTP {response.status_code}: Ungültiger Token")
        return False

    print()

    # Test 2: Testnachricht senden
    print("[INFO] Sende Testnachricht...")
    message = (
        "🧪 <b>Telegram Integration Test</b>\n\n"
        "Dies ist eine Testnachricht von Zen-AI-Pentest.\n\n"
        "<b>Repository:</b> SHAdd0WTAka/Zen-Ai-Pentest\n"
        "<b>Status:</b> ✅ Integration funktioniert!\n\n"
        "Du erhältst jetzt Benachrichtigungen für:\n"
        "• Workflow-Status\n"
        "• Issues & PRs\n"
        "• Releases"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("[OK] Testnachricht gesendet!")
            print(f"     Message ID: {data['result'].get('message_id')}")
            print(
                f"     Chat: {data['result']['chat'].get('title', data['result']['chat'].get('first_name'))}"
            )
        else:
            print(f"[ERROR] Senden fehlgeschlagen: {data.get('description')}")
            return False
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(f"Response: {response.text}")
        return False

    print()
    print("=" * 60)
    print("[OK] Alle Tests erfolgreich!")
    print("=" * 60)
    return True


def get_chat_id(token):
    """Holt die Chat ID aus den letzten Updates"""
    print("[INFO] Suche nach Chat ID...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("ok") and data.get("result"):
            updates = data["result"]
            print(f"[INFO] {len(updates)} Updates gefunden")

            for update in updates:
                if "message" in update:
                    chat = update["message"]["chat"]
                    chat_id = chat["id"]
                    chat_type = chat["type"]
                    chat_name = chat.get(
                        "title", chat.get("first_name", "Unknown")
                    )
                    print(f"\n[FOUND] Chat ID: {chat_id}")
                    print(f"        Type: {chat_type}")
                    print(f"        Name: {chat_name}")
                    return str(chat_id)
        else:
            print("[WARN] Keine Updates gefunden.")
            print("       Schreibe eine Nachricht an den Bot zuerst!")
    else:
        print(f"[ERROR] HTTP {response.status_code}")

    return None


def main():
    print()

    # Token aus Umgebungsvariable oder Eingabe
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN nicht gesetzt")
        print("Nutze: $env:TELEGRAM_BOT_TOKEN='dein-token'")
        print()
        print("ODER starte den GitHub Actions Workflow:")
        print(
            "https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/actions/workflows/telegram-notifications.yml"
        )
        return

    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not chat_id:
        print("[INFO] TELEGRAM_CHAT_ID nicht gesetzt")
        print("[INFO] Versuche Chat ID automatisch zu ermitteln...")
        chat_id = get_chat_id(token)

        if chat_id:
            print(f"\n[INFO] Gefundene Chat ID: {chat_id}")
            print("[INFO] Speichere diese als TELEGRAM_CHAT_ID")
        else:
            print("\n[ERROR] Chat ID konnte nicht ermittelt werden")
            print("Schreibe zuerst eine Nachricht an den Bot!")
            return

    print()
    print(f"[INFO] Verwende Chat ID: {chat_id}")
    print()

    # Verbindung testen
    if test_connection(token, chat_id):
        print()
        print("🎉 Telegram Integration ist bereit!")
        print("Du wirst jetzt Benachrichtigungen erhalten.")
    else:
        print()
        print("❌ Tests fehlgeschlagen")
        print("Prüfe Token und Chat ID")
        sys.exit(1)


if __name__ == "__main__":
    main()
