# 🛡️ Zen-Ai Kimi Personas - Komplettes Setup

Dieses Setup bietet **11 spezialisierte KI-Assistenten** für Pentesting über CLI, API und Web UI.

## 📁 Struktur

```
~/Zen-Ai-Pentest/
├── tools/
│   ├── kimi_helper.py          # CLI Tool mit 11 Personas
│   ├── update_personas.py      # Persona Verwaltung
│   └── setup_aliases.sh        # Bash Aliase
│
├── api/
│   ├── kimi_personas_api.py    # Flask REST API + WebSocket
│   ├── cli_client.py           # API CLI Client
│   ├── templates/
│   │   └── index.html          # Web UI
│   ├── start_server.sh         # Server Starter
│   ├── test_api.sh             # API Tests
│   ├── postman_collection.json # Postman Import
│   ├── docker-compose.yml      # Docker Setup
│   └── README.md               # API Dokumentation
│
└── ~/.config/kimi/personas/    # Persona Definitionen
    ├── recon.md
    ├── exploit.md
    ├── report.md
    ├── audit.md
    ├── social.md
    ├── network.md
    ├── mobile.md
    ├── redteam.md
    ├── ics.md
    ├── cloud.md
    └── crypto.md
```

## 🚀 Schnellstart

### 1. Aliase laden

```bash
source ~/Zen-Ai-Pentest/tools/setup_aliases.sh
```

### 2. CLI Tool nutzen

```bash
# Interaktiver Modus
khi -i

# One-Shot
k-recon "Analysiere example.com"
k-exploit "Schreibe SQLi Scanner"
k-cloud "AWS S3 Enumeration"
```

### 3. API Server starten

```bash
kimi-api-start
# oder
python3 ~/Zen-Ai-Pentest/api/kimi_personas_api.py
```

### 4. Web UI öffnen

http://127.0.0.1:5000

### 5. API Client nutzen

```bash
kapi-health
kapi-list
kapi chat redteam "Kill Chain Design"
kapi interactive --complete
```

## 🎭 Die 11 Personas

| Persona | Alias | Verwendung |
|---------|-------|------------|
| **🔍 recon** | `k-recon` | OSINT, Subdomains, Ports |
| **💣 exploit** | `k-exploit` | Exploit Development, Python |
| **📝 report** | `k-report` | CVSS, Remediation, Reports |
| **🔐 audit** | `k-audit` | Code Review, OWASP |
| **🎭 social** | `k-social` | Phishing Analyse (Ethik!) |
| **🌐 network** | `k-network` | AD, Lateral Movement |
| **📱 mobile** | `k-mobile` | Android, iOS, Frida |
| **🕵️ redteam** | `k-redteam` | APT TTPs, C2 Ops |
| **🧪 ics** | `k-ics` | SCADA, Modbus, Safety |
| **☁️ cloud** | `k-cloud` | AWS, Azure, K8s |
| **🔬 crypto** | `k-crypto` | JWT, TLS, Krypto |

## 🌐 API Endpoints

```bash
GET  /                          # Web UI
GET  /api/v1/health             # Health Check
GET  /api/v1/personas           # Liste Personas
GET  /api/v1/personas/<id>      # Persona Details
GET  /api/v1/personas/<id>/prompt  # System Prompt
POST /api/v1/chat               # Chat
POST /api/v1/chat/complete      # Chat mit Kimi API
POST /api/v1/batch              # Batch Processing
GET  /admin                     # Admin Dashboard
GET  /admin/logs                # Request Logs
WS   /ws/chat                   # WebSocket Chat
```

## 🔧 Konfiguration

### API Key setzen

```bash
# In config.json
{
  "backends": {
    "kimi_api_key": "dein-key-hier"
  }
}

# Oder als Environment Variable
export KIMI_API_KEY="dein-key"
```

### Ohne Authentifizierung (nur lokal!)

```bash
python3 ~/Zen-Ai-Pentest/api/kimi_personas_api.py --no-auth
```

## 📊 Features im Überblick

| Feature | CLI | API | Web UI |
|---------|-----|-----|--------|
| 11 Personas | ✅ | ✅ | ✅ |
| Interaktiver Modus | ✅ | ✅ | ✅ |
| Chat mit Kimi API | ✅ | ✅ | ✅ |
| Request Logging | ❌ | ✅ | ❌ |
| Admin Dashboard | ❌ | ✅ | ❌ |
| WebSocket | ❌ | ✅ | ✅ |
| Batch Processing | ❌ | ✅ | ❌ |
| Token Tracking | ✅ | ✅ | ✅ |

## 🐳 Docker

```bash
cd ~/Zen-Ai-Pentest/api
docker-compose up -d
```

## 🔄 Updates

```bash
# Personas aktualisieren
python3 ~/Zen-Ai-Pentest/tools/update_personas.py

# Neue Persona hinzufügen
# 1. Datei in ~/.config/kimi/personas/ erstellen
# 2. kimi_helper.py und kimi_personas_api.py aktualisieren
```

## 📝 Beispiel-Workflow

```bash
# 1. Recon
k-recon "Analysiere testphp.vulnweb.com"

# 2. Exploit basierend auf Recon
k-exploit "Schreibe SQLi Scanner für MySQL mit UNION-based extraction"

# 3. Code Review
k-audit -f scanner.py

# 4. Report
k-report "SQLi auf login.php, CVSS 9.8"

# 5. Oder alles über die Web UI/API
kimi-api-start
# -> Browser: http://127.0.0.1:5000
```

## 🆘 Troubleshooting

| Problem | Lösung |
|---------|--------|
| `No module named 'flask'` | `pip install flask flask-cors flask-sock` |
| `No module named 'rich'` | `pip install rich requests` |
| `Persona not found` | `python3 tools/update_personas.py` |
| `API Key not configured` | Key in config.json oder `--no-auth` |
| Web UI zeigt nichts | Browser-Cache leeren, `/` aufrufen |

## 📚 Dokumentation

- `api/README.md` - API Dokumentation
- `tools/kimi_helper.py --help` - CLI Hilfe
- `api/cli_client.py --help` - API Client Hilfe

## 🎉 Fertig!

Dein Zen-Ai Pentest Personas System ist bereit. Wähle deinen Modus:
- **CLI**: Schnell, terminal-basiert
- **API**: Für Integrationen, CI/CD
- **Web UI**: Visuell, benutzerfreundlich
