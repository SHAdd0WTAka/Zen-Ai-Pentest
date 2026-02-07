# Zen AI Pentest

**AI-Powered Multi-LLM Penetration Testing Framework**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen)](../.github/workflows/ci.yml)

---

## 🚀 Features

### AI Integration
- **🌙 Kimi Support** (Moonshot AI) - Beste Preis/Leistung
- **🔄 OpenRouter** - Multi-Provider (50+ Modelle)
- **🤖 OpenAI** - GPT-4o Support
- **🎭 6 Pentest Personas** für spezialisierte Aufgaben

### Pentest Personas

| Persona | Fokus |
|---------|-------|
| 🔍 **Recon** | OSINT, Subdomains, Ports |
| 💣 **Exploit** | Python-Exploits, POCs |
| 📝 **Report** | CVSS, Remediation |
| 🔐 **Audit** | Code Review, Security |
| 🌐 **Network** | AD, Lateral Movement |
| 🕵️ **RedTeam** | APT Simulation |

---

## 📦 Schnellstart

### Installation

```bash
# Repository klonen
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Abhängigkeiten installieren
pip install -r requirements.txt

# API Keys konfigurieren (jeder Benutzer!)
python scripts/setup_wizard.py
```

### Nutzung

```bash
# Mit Persona arbeiten
python tools/kimi_helper.py -p recon "Scan target.com"
python tools/kimi_helper.py -p exploit "SQLi Scanner schreiben"
python tools/kimi_helper.py -p report "CVSS-Bericht erstellen"

# Interaktiver Modus
python tools/kimi_helper.py -i

# Oder mit Aliasen
zrecon "Finde Subdomains"
zexploit "Buffer Overflow PoC"
```

---

## 🛠️ Tools & Scripts

| Tool | Zweck |
|------|-------|
| `kimi_helper.py` | AI Assistant mit Personas |
| `setup_wizard.py` | API Key Konfiguration |
| `check_config.py` | Konfigurations-Check |
| `switch_model.py` | Backend wechseln |

---

## 📚 Dokumentation

- [KIMI_PERSONAS.md](KIMI_PERSONAS.md) - Persona Details
- [ALIASES.md](ALIASES.md) - Schnellzugriff Aliase
- [README_USER_SETUP.md](../README_USER_SETUP.md) - Setup Anleitung
- [API.md](API.md) - API Dokumentation

---

## 🔒 Security

- API Keys werden **nie committed**
- Jeder Benutzer konfiguriert eigene Keys
- Automatische Key-Rotation verfügbar

---

## 🤝 Contributing

Siehe [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📄 License

MIT License - Siehe [LICENSE](../LICENSE)
