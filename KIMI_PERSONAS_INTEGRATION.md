# 🔗 Kimi Personas Integration

Dieses Dokument beschreibt die Integration des **Kimi Personas Systems** in das Zen-Ai-Pentest Repository.

## 📦 Was wurde hinzugefügt

### 🎭 11 Pentest-Personas
```
~/.config/kimi/personas/
├── recon.md      # 🔍 OSINT & Reconnaissance
├── exploit.md    # 💣 Exploit Development
├── report.md     # 📝 Technical Writing
├── audit.md      # 🔐 Code Auditing
├── social.md     # 🎭 Social Engineering
├── network.md    # 🌐 Network Pentesting
├── mobile.md     # 📱 Mobile Security
├── redteam.md    # 🕵️ Red Team Operations
├── ics.md        # 🧪 ICS/SCADA
├── cloud.md      # ☁️ Cloud Security
└── crypto.md     # 🔬 Cryptography
```

### 🛠️ Tools (neu)
```
tools/
├── kimi_helper.py         # CLI Tool mit 11 Personas
├── update_personas.py     # Persona-Verwaltung
└── setup_aliases.sh       # Bash Aliase
```

### 🌐 API Server (neu)
```
api/
├── kimi_personas_api.py      # Flask REST API + WebSocket
├── cli_client.py             # API CLI Client
├── templates/
│   └── index.html            # Web UI mit Screenshot-Support
├── add_screenshot.py         # Screenshot Manager
├── manage.sh                 # Server Management
├── status.sh                 # Status-Anzeige
├── diagnose.sh               # Diagnose-Tool
├── QUICK_TEST.sh             # Schnelltest
├── QUICKSTART.sh             # Automatisches Setup
├── postman_collection.json   # Postman Import
├── docker-compose.yml        # Docker Setup
├── Dockerfile                # Container Image
├── requirements-api.txt      # Dependencies
└── README.md                 # API Dokumentation
```

### 📸 Screenshots (neu)
```
screenshots/              # Screenshot-Verzeichnis
└── README.txt
```

## 🚀 Quick Start

### 1. Repository klonen & Setup
```bash
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Dependencies installieren
pip install flask flask-cors flask-sock rich requests

# Aliase laden
source tools/setup_aliases.sh

# Personas erstellen
python3 tools/update_personas.py
```

### 2. CLI Tool nutzen
```bash
# Interaktiver Modus
khi -i

# One-Shot Anfragen
k-recon "Analysiere example.com"
k-exploit "Schreibe SQLi Scanner"
k-cloud "AWS S3 Enumeration"
```

### 3. API Server starten
```bash
# Server starten
kimi-api-start

# oder
python3 api/kimi_personas_api.py --no-auth

# Web UI: http://127.0.0.1:5000
```

### 4. API Client nutzen
```bash
# Health Check
kapi health

# Chat
kapi chat recon "Analysiere Ziel" --complete

# Interaktiver Modus
kapi interactive
```

## 🔌 API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | Web UI |
| `/api/v1/health` | GET | Health Check |
| `/api/v1/personas` | GET | Alle 11 Personas |
| `/api/v1/personas/<id>` | GET | Persona Details |
| `/api/v1/personas/<id>/prompt` | GET | System Prompt |
| `/api/v1/chat` | POST | Chat |
| `/api/v1/chat/complete` | POST | Chat mit Kimi API |
| `/api/v1/batch` | POST | Batch Processing |
| `/api/v1/screenshots` | GET/POST | Screenshots verwalten |
| `/static/screenshots/<file>` | GET | Screenshot anzeigen |
| `/admin` | GET | Admin Dashboard |
| `/admin/logs` | GET | Request Logs |
| `/ws/chat` | WS | WebSocket Chat |

## 🎭 Verfügbare Personas

| ID | Name | Kategorie | Verwendung |
|----|------|-----------|------------|
| `recon` | 🔍 Recon/OSINT | Core | Subdomains, Ports, OSINT |
| `exploit` | 💣 Exploit Dev | Core | Python, POCs, Automation |
| `report` | 📝 Technical Writer | Core | CVSS, Remediation |
| `audit` | 🔐 Code Auditor | Core | Security Review, OWASP |
| `social` | 🎭 Social Engineering | Extended | Phishing, Awareness |
| `network` | 🌐 Network Pentester | Extended | AD, Lateral Movement |
| `mobile` | 📱 Mobile Security | Extended | Android, iOS, Frida |
| `redteam` | 🕵️ Red Team Operator | Extended | APT TTPs, C2 |
| `ics` | 🧪 ICS/SCADA | Extended | Modbus, Safety Systems |
| `cloud` | ☁️ Cloud Security | Extended | AWS, Azure, K8s |
| `crypto` | 🔬 Cryptography | Extended | JWT, TLS, Crypto |

## 📸 Screenshot-Feature

### Screenshots hinzufügen
```bash
# Aus Downloads suchen
kss downloads

# Manuell hinzufügen
kss add ~/Downloads/screenshot.png

# Verzeichnis öffnen
kss open
```

### In Web UI analysieren
1. http://127.0.0.1:5000 öffnen
2. Tab "Screenshots" wählen
3. Bild hochladen oder aus Gallery wählen
4. "Mit Persona analysieren" klicken

## 🔧 Management

```bash
# Server Status
bash api/manage.sh status

# Server starten/stoppen/restarten
bash api/manage.sh start
bash api/manage.sh stop
bash api/manage.sh restart

# Logs anzeigen
bash api/manage.sh logs

# API testen
bash api/manage.sh test

# Diagnose
bash api/manage.sh diagnose
```

## 🐳 Docker

```bash
cd api
docker-compose up -d
```

## 📝 Konfiguration

### API Key (optional)
```json
{
  "backends": {
    "kimi_api_key": "your-kimi-api-key"
  }
}
```

Ohne API Key läuft das System im Demo-Modus mit simulierten Antworten.

## 🔗 GitHub Integration

### Änderungen pushen
```bash
# Status prüfen
git status

# Neue Dateien hinzufügen
git add tools/kimi_helper.py
git add tools/update_personas.py
git add tools/setup_aliases.sh
git add api/
git add screenshots/
git add KIMI_PERSONAS_INTEGRATION.md

# Commit
git commit -m "feat: Add Kimi Personas System with 11 Pentest AI assistants

- Add 11 specialized pentest personas (recon, exploit, report, audit, etc.)
- Add CLI tool (kimi_helper.py) with interactive mode
- Add Flask REST API with WebSocket support
- Add Web UI with screenshot analysis
- Add API CLI client
- Add screenshot management
- Add Docker support
- Add Postman collection
- Add comprehensive documentation"

# Push
git push origin main
```

## 📚 Dokumentation

- `KIMI_PERSONAS_SETUP.md` - Komplettes Setup
- `api/README.md` - API Dokumentation
- `DEMO.md` - Demo & Beispiele
- `KIMI_PERSONAS_INTEGRATION.md` - Dieses Dokument

## 🎯 Workflow Beispiel

```bash
# 1. Terminal 1: Server starten
bash api/manage.sh start

# 2. Terminal 2: CLI nutzen
source tools/setup_aliases.sh
k-recon "Analysiere target.com"

# 3. Browser: Web UI öffnen
# http://127.0.0.1:5000

# 4. Screenshot hinzufügen
kss add ~/Downloads/target_recon.png

# 5. In Web UI analysieren
# Tab "Screenshots" → Bild wählen → Analysieren
```

## ✅ Fertig!

Das Kimi Personas System ist jetzt vollständig in dein Zen-Ai-Pentest Repository integriert!

---
*Erstellt: 2026-02-07*
*Version: 1.0.0*
