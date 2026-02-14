# 🎉 Zen-Ai Kimi Personas - Demo

## ✅ System Status: ONLINE

Alle Komponenten wurden erfolgreich getestet und sind einsatzbereit!

```
┌─────────────────────────────────────────────────────────────────┐
│                    🛡️ SYSTEM STATUS                             │
├─────────────────────────────────────────────────────────────────┤
│  API Server        ✅ Running on http://127.0.0.1:5000          │
│  Web UI            ✅ Available at /                            │
│  11 Personas       ✅ All loaded                                │
│  CLI Tool          ✅ Functional                                │
│  API Client        ✅ Ready                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Schnell-Demo

### 1. CLI Tool (Schnell & Terminal-basiert)

```bash
# Aliase laden
source ~/Zen-Ai-Pentest/tools/setup_aliases.sh

# Personas anzeigen
khi --list

# Recon Anfrage
k-recon "Analysiere example.com - Subdomains und Ports"

# Exploit Development
k-exploit "Schreibe Python-Scanner für SQL Injection"

# Cloud Security
k-cloud "AWS S3 Bucket Enumeration mit pacu"

# Interaktiver Modus
k-chat
```

### 2. API Server (Integration & Web UI)

```bash
# Server starten
kimi-api-start
# oder
python3 ~/Zen-Ai-Pentest/api/kimi_personas_api.py --no-auth

# Web UI öffnen: http://127.0.0.1:5000
```

### 3. API Client (Programmatischer Zugriff)

```bash
# Health Check
kapi health

# Personas listen
kapi list

# Chat mit Kimi API
kapi chat recon "Analysiere Ziel" --complete

# Interaktiver Modus
kapi interactive --complete
```

### 4. cURL (Raw HTTP)

```bash
# Health
curl http://127.0.0.1:5000/api/v1/health

# Alle Personas
curl http://127.0.0.1:5000/api/v1/personas

# Admin Dashboard
curl http://127.0.0.1:5000/admin

# Chat
curl -X POST http://127.0.0.1:5000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"persona":"exploit","message":"Test"}'
```

## 🎭 Die 11 Personas im Überblick

| Emoji | Name | ID | Verwendung |
|-------|------|----|------------|
| 🔍 | Recon/OSINT Specialist | `recon` | Subdomain枚举, Port scanning |
| 💣 | Exploit Developer | `exploit` | Python coding, POC dev |
| 📝 | Technical Writer | `report` | CVSS scoring, Reports |
| 🔐 | Code Auditor | `audit` | Security review, OWASP |
| 🎭 | Social Engineering | `social` | Phishing analysis (Ethics!) |
| 🌐 | Network Pentester | `network` | AD, Lateral movement |
| 📱 | Mobile Security | `mobile` | Android, iOS, Frida |
| 🕵️ | Red Team Operator | `redteam` | APT TTPs, C2 ops |
| 🧪 | ICS/SCADA Specialist | `ics` | SCADA, Modbus, Safety |
| ☁️ | Cloud Security Expert | `cloud` | AWS, Azure, K8s |
| 🔬 | Cryptography Analyst | `crypto` | JWT, TLS, Crypto |

## 📊 Features Demo

### Request Logging
```bash
# Logs anzeigen
tail -f ~/Zen-Ai-Pentest/logs/api_requests.log

# Admin Dashboard
curl http://127.0.0.1:5000/admin/logs
```

### WebSocket Chat
```javascript
// Browser Console
const ws = new WebSocket('ws://127.0.0.1:5000/ws/chat');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({
  persona: 'recon',
  message: 'Analysiere example.com'
}));
```

### Batch Processing
```bash
curl -X POST http://127.0.0.1:5000/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {"persona": "recon", "message": "Scan target"},
      {"persona": "exploit", "message": "Write scanner"},
      {"persona": "report", "message": "Create report"}
    ]
  }'
```

## 🔧 Verfügbare Befehle

### CLI (kimi_helper.py)
```
khi --list                    # Personas anzeigen
khi -p <persona> "message"    # One-shot Anfrage
khi -i                        # Interaktiver Modus
khi -f file.txt               # Aus Datei lesen
```

### Aliase
```
k-recon, k-exploit, k-report, k-audit
k-social, k-network, k-mobile, k-redteam
k-ics, k-cloud, k-crypto
k-chat                        # Interaktiv
```

### API Client
```
kapi health                   # Status prüfen
kapi list                     # Personas listen
kapi chat <persona> <msg>     # Chat
kapi prompt <persona>         # System Prompt anzeigen
kapi admin                    # Dashboard
kapi interactive              # Interaktiver Modus
```

## 🌐 API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/` | GET | Web UI |
| `/api/v1/health` | GET | Health Check |
| `/api/v1/personas` | GET | Alle Personas |
| `/api/v1/personas/<id>` | GET | Details |
| `/api/v1/personas/<id>/prompt` | GET | System Prompt |
| `/api/v1/chat` | POST | Chat |
| `/api/v1/chat/complete` | POST | Mit Kimi API |
| `/api/v1/batch` | POST | Batch |
| `/admin` | GET | Dashboard |
| `/admin/logs` | GET | Logs |
| `/ws/chat` | WS | WebSocket |

## 🎉 Fertig!

Dein Zen-Ai Pentest Personas System ist vollständig eingerichtet und einsatzbereit!

### Nächste Schritte:
1. Wähle deine bevorzugte Schnittstelle (CLI, API, Web UI)
2. Beginne mit deiner ersten Pentest-Anfrage
3. Nutze verschiedene Personas für verschiedene Phasen

### Support:
- Dokumentation: `~/Zen-Ai-Pentest/KIMI_PERSONAS_SETUP.md`
- API Docs: `~/Zen-Ai-Pentest/api/README.md`
- Postman: `~/Zen-Ai-Pentest/api/postman_collection.json`

---
*System bereit für 48h Pentest-Sprints! 🚀*
