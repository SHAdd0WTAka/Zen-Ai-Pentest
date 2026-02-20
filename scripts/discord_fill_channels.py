#!/usr/bin/env python3
"""
Discord Server - Channels mit Inhalt füllen
Postet Willkommensnachrichten, Regeln und Informationen
"""

import os

import requests

# Konfiguration
GUILD_ID = "1467204311355363485"
API_BASE = "https://discord.com/api/v10"

# Inhalte für verschiedene Channels
CHANNEL_CONTENT = {
    "rules": """# 📜 Server Rules - Zen-Ai Community

Willkommen in der Zen-AI-Pentest Community! 🛡️

## Grundregeln

1. **Respektvoller Umgang** - Behandle alle Mitglieder fair und höflich
2. **Kein Spam** - Keine unerwünschte Werbung oder wiederholte Nachrichten
3. **Keine illegalen Aktivitäten** - Dies ist ein Framework für **autorisierte** Security-Tests
4. **Hilfe & Support** - Frag ruhig, aber nutze die richtigen Channels
5. **Datenschutz** - Teile keine persönlichen Daten oder sensible Informationen

## Projekt-Info

**Zen-AI-Pentest** ist ein Open-Source Framework für:
- Automated Penetration Testing
- Vulnerability Scanning
- AI-powered Security Analysis
- Compliance Reporting (ISO 27001, GDPR)

🔗 GitHub: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest
📦 PyPI: https://pypi.org/project/zen-ai-pentest/

## Support

- 💬 **#💬-general** - Allgemeine Diskussionen
- 🆘 **#🆘-support** - Technische Hilfe
- 🐛 **#🐛-bug-reports** - Fehler melden
- 💡 **#💡-feature-requests** - Ideen vorschlagen

**Viel Spaß in der Community!** 🚀
""",
    "announcements": """# 📢 Willkommen bei Zen-Ai!

🎉 **Der Discord Server ist jetzt live!**

## Was ist Zen-AI-Pentest?

Ein professionelles, KI-gestütztes Penetration Testing Framework für:
- Security Professionals
- Bug Bounty Hunter
- Enterprise Security Teams
- Red Teams

## 🌟 Highlights

✅ **Autonomous AI Agent** - ReAct Pattern für intelligente Entscheidungen
✅ **20+ Security Tools** - Nmap, SQLMap, Metasploit, BurpSuite Integration
✅ **Risk Engine** - CVSS/EPSS Scoring mit False-Positive Reduktion
✅ **Zero Telemetry** - 100% Privacy, keine Datenweitergabe
✅ **ISO 27001 Ready** - Compliance-Dokumentation inklusive

## 📅 Aktuelles

- **v2.3.9** ist auf PyPI verfügbar
- Discord-Integration für CI/CD Notifications
- ISO 27001 Compliance-Dokumentation veröffentlicht

## 🔗 Links

- 🌐 **GitHub**: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest
- 💬 **Discord**: https://discord.gg/zJZUJwK9AC
- 📦 **PyPI**: https://pypi.org/project/zen-ai-pentest/

**Bleib dran für Updates!** 🔔
""",
    "general": """# 💬 Willkommen im General Chat!

Hier kannst du:
- 👋 Dich vorstellen
- 💬 Über Security-Themen diskutieren
- 🤝 Mit anderen vernetzen
- 📅 Über Events abstimmen

**Wer bist du?** Sag hallo und erzähl uns:
- Was ist dein Hintergrund? (Dev, Sec, Ops, ...)
- Was machst du mit Zen-AI-Pentest?
- Woher kommst du?

**Viel Spaß!** 🎉
""",
    "introductions": """# 👋 Stell dich vor!

Neu im Server? Hier ist der perfekte Ort um dich vorzustellen!

**Template (kannst du kopieren und anpassen):**

```
👤 **Name/Handle:**
🌍 **Location:**
💼 **Role:** (Security Researcher, Developer, Student, ...)
🛠️ **Experience:** (Junior, Mid, Senior)
🎯 **Interests:** (Pentesting, Bug Bounty, AI, ...)
🔧 **Tools I use:** (Nmap, Burp, Custom scripts, ...)
📖 **Currently learning:**
💡 **Why Zen-AI-Pentest?:**
```

Wir freuen uns dich kennenzulernen! 🎉
""",
    "knowledge-base": """# 📚 Knowledge Base

Hier sammeln wir nützliche Ressourcen!

## 📖 Offizielle Dokumentation

- [GitHub Repository](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest)
- [Installation Guide](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/INSTALLATION.md)
- [API Dokumentation](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/API.md)
- [Architecture](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/docs/ARCHITECTURE.md)

## 🎓 Lernressourcen

### Penetration Testing
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Hack The Box](https://www.hackthebox.com/)
- [TryHackMe](https://tryhackme.com/)

### KI & Security
- [LangChain Dokumentation](https://python.langchain.com/)
- [OpenAI API Guide](https://platform.openai.com/docs)

## 🛠️ Tools

| Kategorie | Tools |
|-----------|-------|
| **Network** | Nmap, Masscan, Scapy |
| **Web** | BurpSuite, SQLMap, Nuclei |
| **Exploitation** | Metasploit, SearchSploit |
| **AD** | BloodHound, CrackMapExec |

**Hast du eine Ressource die fehlt?** Poste sie hier! 💡
""",
    "tools-automation": """# 🤖 Tools & Automation

Diskutiere über Pentesting-Tools und Automatisierung!

## 🛠️ Integrierte Tools in Zen-AI-Pentest

### Network Scanning
- `nmap` - Port scanning & service detection
- `masscan` - High-speed port scanning
- `scapy` - Packet manipulation

### Web Application Testing
- `sqlmap` - SQL injection automation
- `gobuster` - Directory/file brute-forcing
- `nuclei` - Vulnerability scanning
- `burpsuite` - Web proxy & testing

### Exploitation
- `metasploit` - Exploitation framework
- `searchsploit` - Exploit database

## 💬 Diskussionsthemen

- Welche Tools nutzt du am häufigsten?
- Automation vs. Manual Testing?
- Custom Scripts & Workflows?
- Tool-Integration in CI/CD?

**Zeig her deine Setups!** 🔧
""",
    "security-research": """# 🔒 Security Research

Für tiefgreifende Security-Diskussionen!

## 🎯 Aktuelle Themen

### AI in Cybersecurity
- Autonomous penetration testing
- AI-powered vulnerability detection
- Ethical considerations
- Red Team AI vs Blue Team AI

### Framework & Methodology
- PTES (Penetration Testing Execution Standard)
- OWASP Testing Guide
- NIST Cybersecurity Framework
- ISO 27001 Controls

### Research Topics
- Zero-day discovery
- Exploit development
- Threat modeling
- Attack surface analysis

## 📊 CVE & Exploits

Teile interessante CVEs oder Exploits hier!

**Format:**
```
CVE-XXXX-XXXX
Severity: CVSS Score
Summary: Brief description
Mitigation: How to fix
Reference: Link
```

**Disclaimer:** Nur für autorisierte Tests und Research! 🛡️
""",
    "ai-ml-discussion": """# 🧠 AI & Machine Learning

KI-Themen rund um Security!

## 🤖 Zen-AI-Pentest AI Features

### ReAct Agent
- Reasoning → Acting → Observing
- Autonome Entscheidungsfindung
- Tool-Auswahl basierend auf Context

### Unterstützte Modelle
- Kimi AI (Moonshot)
- OpenAI GPT-4/3.5
- Anthropic Claude
- Local LLMs (Ollama)

## 💡 Diskussionsthemen

### Prompt Engineering
- System prompts für Security Tasks
- Context window optimization
- Few-shot prompting

### AI Safety & Ethics
- Responsible disclosure
- AI red teaming
- Privacy preservation
- Hallucination handling

### Model Performance
- Vergleich verschiedener LLMs
- Cost vs. Performance
- Local vs. Cloud

**Was ist deine Meinung zu AI in Security?** 🤔
""",
    "bug-reports": """# 🐛 Bug Reports

Hier können Bugs gemeldet werden!

## 📝 Wie man einen Bug reportet

**Nutze dieses Template:**

```markdown
**Bug Beschreibung:**
Kurze Beschreibung des Problems

**Reproduzieren:**
1. Schritt 1
2. Schritt 2
3. ...

**Erwartetes Verhalten:**
Was sollte passieren?

**Tatsächliches Verhalten:**
Was passiert stattdessen?

**Screenshots:**
Falls zutreffend

**Umgebung:**
- OS: [z.B. Windows 11, Ubuntu 22.04]
- Python Version: [z.B. 3.11]
- Zen-AI-Pentest Version: [z.B. 2.3.9]
- Installation: [pip, docker, source]

**Logs:**
```
Fehler-Logs hier einfügen
```

**Zusätzlicher Kontext:**
Weitere Informationen
```

## 🏷️ Labels

Ein Moderator wird das Issue labeln:
- `bug` - Bestätigter Bug
- `duplicate` - Bereits gemeldet
- `wontfix` - Wird nicht behoben
- `help wanted` - Community-Hilfe benötigt

**Danke für deine Hilfe!** 🙏
""",
    "feature-requests": """# 💡 Feature Requests

Hast du eine Idee für ein neues Feature?

## 📝 Template für Feature Requests

```markdown
**Feature Beschreibung:**
Kurze Beschreibung des gewünschten Features

**Problem:**
Welches Problem löst dieses Feature?

**Lösung:**
Wie sollte es funktionieren?

**Alternativen:**
Gibt es andere Lösungsansätze?

**Zusätzlicher Kontext:**
Mockups, Beispiele, Referenzen
```

## 🎯 Feature Kategorien

- 🛠️ **Tool Integration** - Neues Security Tool
- 🤖 **AI Features** - Verbesserungen am Agent
- 📊 **Reporting** - Neue Report-Formate
- 🌐 **API** - REST API Erweiterungen
- 💻 **UI/UX** - Dashboard oder CLI Verbesserungen
- 🔧 **Config** - Einstellungen & Workflows

## 🗳️ Voting

Reagiere auf Feature-Requests mit:
- 👍 - Ich will das auch!
- 👎 - Nicht notwendig
- 🚀 - High Priority

**Community-Wünsche werden priorisiert!** 📈
""",
    "support": """# 🆘 Support & Help

Hilfe bei Problemen mit Zen-AI-Pentest!

## 🔧 Häufige Probleme

### Installation
```bash
# Virtual Environment empfohlen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\\Scripts\\activate  # Windows

pip install zen-ai-pentest
```

### API Keys konfigurieren
```bash
# .env Datei erstellen
KIMI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

### Tests laufen nicht
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

**Wir helfen gerne!** 💪
""",
}


def get_channels(guild_id, token):
    """Holt alle Channels vom Server"""
    url = f"{API_BASE}/guilds/{guild_id}/channels"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[ERROR] Konnte Channels nicht abrufen: {response.status_code}")
        print(response.text)
        return []


def send_message(channel_id, content, token):
    """Sendet eine Nachricht in einen Channel"""
    url = f"{API_BASE}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    # Discord hat ein Limit von 2000 Zeichen pro Nachricht
    # Lange Nachrichten müssen aufgeteilt werden
    max_length = 1900

    if len(content) <= max_length:
        payload = {"content": content}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("[OK] Nachricht gesendet")
            return True
        else:
            print(f"[ERROR] Konnte Nachricht nicht senden: {response.status_code}")
            print(response.text)
            return False
    else:
        # Nachricht aufteilen
        parts = []
        current_part = ""
        for line in content.split("\n"):
            if len(current_part) + len(line) + 1 > max_length:
                parts.append(current_part)
                current_part = line
            else:
                current_part += "\n" + line if current_part else line
        if current_part:
            parts.append(current_part)

        for i, part in enumerate(parts):
            payload = {"content": part}
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"[OK] Nachricht Teil {i+1}/{len(parts)} gesendet")
            else:
                print(f"[ERROR] Teil {i+1} fehlgeschlagen: {response.status_code}")
                return False
        return True


def find_channel_by_name(channels, name_part):
    """Findet einen Channel anhand eines Namensteils"""
    for channel in channels:
        # Entferne Emojis und suche nach Namensteil
        clean_name = "".join(c for c in channel["name"] if c.isalnum() or c in "-_").lower()
        if name_part.lower() in clean_name or name_part.lower() in channel["name"].lower():
            return channel["id"]
    return None


def main():
    print("=" * 60)
    print(">> Discord Channels mit Inhalt fuellen")
    print("=" * 60)
    print()

    # Token aus Umgebungsvariable oder Datei
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("[ERROR] DISCORD_BOT_TOKEN nicht gesetzt")
        print("Nutze: $env:DISCORD_BOT_TOKEN='dein-token'")
        return

    print("[INFO] Lade Channels...")
    channels = get_channels(GUILD_ID, token)

    if not channels:
        print("[ERROR] Keine Channels gefunden")
        return

    print(f"[INFO] {len(channels)} Channels gefunden")
    print()

    # Mapping: Content-Key -> Channel-Name-Suchbegriffe
    channel_mapping = {
        "rules": ["rules", "regeln"],
        "announcements": ["announcements", "announce", "news", "updates"],
        "general": ["general", "allgemein", "chat"],
        "introductions": ["introductions", "intro", "vorstellung"],
        "knowledge-base": ["knowledge", "wiki", "docs", "resources"],
        "tools-automation": ["tools", "automation", "scripting"],
        "security-research": ["security", "research", "cve"],
        "ai-ml-discussion": ["ai", "ml", "machine-learning", "ki"],
        "bug-reports": ["bug", "bugs", "issue", "issues"],
        "feature-requests": ["feature", "features", "request"],
        "support": ["support", "help", "hilfe"],
    }

    success_count = 0

    for content_key, search_terms in channel_mapping.items():
        if content_key not in CHANNEL_CONTENT:
            continue

        # Suche nach passendem Channel
        channel_id = None
        for term in search_terms:
            channel_id = find_channel_by_name(channels, term)
            if channel_id:
                break

        if not channel_id:
            print(f"[WARN] Kein Channel gefunden fuer: {content_key}")
            continue

        print(f"[INFO] Fuelle Channel '{content_key}'...")
        content = CHANNEL_CONTENT[content_key]

        if send_message(channel_id, content, token):
            success_count += 1
            print(f"[OK] {content_key} erfolgreich gefuellt")
        else:
            print(f"[ERROR] {content_key} fehlgeschlagen")

        print()

    print("=" * 60)
    print(f"[OK] {success_count}/{len(CHANNEL_CONTENT)} Channels gefuellt")
    print("=" * 60)


if __name__ == "__main__":
    main()
