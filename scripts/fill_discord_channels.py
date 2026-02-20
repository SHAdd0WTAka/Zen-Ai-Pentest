#!/usr/bin/env python3
"""
Discord Channel Content Filler
Füllt die 4 fehlenden Channels mit Content aus dem Repo
"""

import os
import sys

import requests

GUILD_ID = "1467204311355363485"
BASE_URL = "https://discord.com/api/v10"

# Channel Content aus DISCORD_MISSING_CONTENT.md
CHANNELS_CONTENT = {
    "introductions": """# 👋 Stell dich vor!

Neu im Server? Hier ist der perfekte Ort um dich vorzustellen!

**Template (kannst du kopieren und anpassen):**

👤 **Name/Handle:**
🌍 **Location:**
💼 **Role:** (Security Researcher, Developer, Student, ...)
🛠️ **Experience:** (Junior, Mid, Senior)
🎯 **Interests:** (Pentesting, Bug Bounty, AI, ...)
🔧 **Tools I use:** (Nmap, Burp, Custom scripts, ...)
📖 **Currently learning:**
💡 **Why Zen-AI-Pentest?:**

Wir freuen uns dich kennenzulernen! 🎉

---
*Pinne diesen Post für das Template!* 📌""",
    "knowledge-base": """# 📚 Knowledge Base

Hier sammeln wir nützliche Ressourcen!

## 📖 Offizielle Dokumentation

- [GitHub Repository](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest)
- [Installation Guide](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/INSTALLATION.md)
- [API Dokumentation](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/API.md)
- [Architecture](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/ARCHITECTURE.md)

## 🎓 Lernressourcen

**Penetration Testing:**
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Hack The Box](https://www.hackthebox.com/)
- [TryHackMe](https://tryhackme.com/)

**KI & Security:**
- [LangChain Dokumentation](https://python.langchain.com/)
- [OpenAI API Guide](https://platform.openai.com/docs)

## 🛠️ Integrierte Tools

| Kategorie | Tools |
|-----------|-------|
| **Network** | Nmap, Masscan, Scapy |
| **Web** | BurpSuite, SQLMap, Nuclei |
| **Exploitation** | Metasploit, SearchSploit |
| **AD** | BloodHound, CrackMapExec |

**Hast du eine Ressource die fehlt?** Poste sie hier! 💡""",
    "tools-automation": """# 🤖 Tools & Automation

Diskutiere über Pentesting-Tools und Automatisierung!

## 🛠️ Integrierte Tools in Zen-AI-Pentest

**Network Scanning:**
- `nmap` - Port scanning & service detection
- `masscan` - High-speed port scanning
- `scapy` - Packet manipulation

**Web Application Testing:**
- `sqlmap` - SQL injection automation
- `gobuster` - Directory/file brute-forcing
- `nuclei` - Vulnerability scanning
- `burpsuite` - Web proxy & testing

**Exploitation:**
- `metasploit` - Exploitation framework
- `searchsploit` - Exploit database

## 💬 Diskussionsthemen

- Welche Tools nutzt du am häufigsten?
- Automation vs. Manual Testing?
- Custom Scripts & Workflows?
- Tool-Integration in CI/CD?

**Zeig her deine Setups!** 🔧""",
    "support": """# 🆘 Support & Help

Hilfe bei Problemen mit Zen-AI-Pentest!

## 🔧 Häufige Probleme

**Installation:**
```bash
# Virtual Environment empfohlen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\\Scripts\\activate  # Windows

pip install zen-ai-pentest
```

**API Keys konfigurieren:**
```bash
# .env Datei erstellen
KIMI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

**Tests laufen nicht:**
```bash
# SECRET_KEY setzen
export SECRET_KEY="your-secret-key-min-32-chars"
pytest
```

## 📝 Support Template

```markdown
**Problem:**
Beschreibung des Fehlers

**Was hast du versucht:**
1. Schritt 1
2. Schritt 2

**Fehlermeldung:**
```
Fehler-Log hier
```

**Umgebung:**
- OS:
- Python:
- Version:
```

## 📚 Ressourcen

- [Troubleshooting Guide](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/TROUBLESHOOTING.md)
- [FAQ](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/FAQ.md)

**Wir helfen gerne!** 💪""",
}


def find_channel_by_name(guild_id, channel_name, headers):
    """Findet Channel-ID anhand des Namens"""
    url = f"{BASE_URL}/guilds/{guild_id}/channels"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        channels = response.json()
        for channel in channels:
            if channel["name"] == channel_name:
                return channel["id"]
    return None


def post_message(channel_id, content, headers):
    """Postet eine Nachricht in einen Channel"""
    url = f"{BASE_URL}/channels/{channel_id}/messages"

    # Discord hat 2000 Zeichen Limit pro Nachricht
    if len(content) > 2000:
        # Teile in mehrere Nachrichten
        parts = []
        current = ""
        for line in content.split("\n"):
            if len(current) + len(line) + 1 > 1900:
                parts.append(current)
                current = line
            else:
                current += "\n" + line if current else line
        if current:
            parts.append(current)

        # Poste erste Nachricht
        data = {"content": parts[0]}
        r = requests.post(url, json=data, headers=headers)

        # Poste Rest als Thread oder separate Nachrichten
        for part in parts[1:]:
            data = {"content": part}
            requests.post(url, json=data, headers=headers)

        return r.status_code == 200
    else:
        data = {"content": content}
        response = requests.post(url, json=data, headers=headers)
        return response.status_code == 200


def main():
    print("🎮 Discord Channel Content Filler")
    print("=" * 50)

    # Bot Token
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if not bot_token:
        print("\nBitte DISCORD_BOT_TOKEN als Environment Variable setzen:")
        print("set DISCORD_BOT_TOKEN=dein-token")
        sys.exit(1)

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}

    print(f"\n🏰 Guild ID: {GUILD_ID}")
    print("⏳ Suche Channels und poste Content...\n")

    success_count = 0
    fail_count = 0

    for channel_name, content in CHANNELS_CONTENT.items():
        print(f"🔍 Suche #{channel_name}...")
        channel_id = find_channel_by_name(GUILD_ID, channel_name, headers)

        if channel_id:
            print(f"   ✅ Gefunden (ID: {channel_id})")
            print("   ⏳ Poste Content...")

            if post_message(channel_id, content, headers):
                print("   ✅ Erfolgreich gepostet!\n")
                success_count += 1
            else:
                print("   ❌ Fehler beim Posten\n")
                fail_count += 1
        else:
            print("   ❌ Channel nicht gefunden\n")
            fail_count += 1

    print("=" * 50)
    print(f"📊 Ergebnis: {success_count} erfolgreich, {fail_count} fehlgeschlagen")

    if success_count == len(CHANNELS_CONTENT):
        print("🎉 Alle Channels wurden gefüllt!")
    else:
        print("⚠️  Einige Channels konnten nicht gefüllt werden")


if __name__ == "__main__":
    main()
