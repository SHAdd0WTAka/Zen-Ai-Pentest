# 🚀 Kimi Personas API

REST API & Web UI für Zen-Ai-Pentest Personas - 11 spezialisierte KI-Assistenten für Pentesting.

## ✨ Features

- 🎨 **Web UI** - Moderne Browser-Oberfläche
- 📡 **WebSocket** - Echtzeit-Chat
- 📝 **Request Logging** - Audit-Trail aller Anfragen
- 📊 **Admin Dashboard** - Statistiken & Monitoring
- 🔐 **API Key Auth** - Sichere Authentifizierung
- 🔄 **Batch Processing** - Mehrere Anfragen auf einmal

## 📦 Installation

```bash
cd ~/Zen-Ai-Pentest/api
pip install -r requirements-api.txt
```

## 🚀 Quick Start

```bash
# Server starten
python3 kimi_personas_api.py

# Oder mit dem Skript
kimi-api-start

# Oder mit Docker
docker-compose up -d
```

Öffne http://127.0.0.1:5000 im Browser für die Web UI!

## 🌐 Web UI

Die Web UI bietet:
- Alle 11 Personas auf einen Blick
- Echtzeit-Chat Interface
- Temperatur-Einstellung
- Message History
- Token-Tracking

![Web UI Preview](https://via.placeholder.com/800x500/1a1a2e/e94560?text=Zen-Ai+Kimi+Personas+Web+UI)

## 🔌 API Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/` | GET | **Web UI** |
| `/api/v1/health` | GET | Health Check |
| `/api/v1/personas` | GET | Alle Personas |
| `/api/v1/personas/<id>` | GET | Persona Details |
| `/api/v1/personas/<id>/prompt` | GET | System Prompt (plain text) |
| `/api/v1/personas/categories` | GET | Kategorien |
| `/api/v1/chat` | POST | Chat (Prompt Only) |
| `/api/v1/chat/complete` | POST | Chat mit Kimi API |
| `/api/v1/batch` | POST | Batch Processing |
| `/admin` | GET | **Admin Dashboard** |
| `/admin/logs` | GET | Request Logs |
| `/ws/chat` | WebSocket | Echtzeit-Chat |

## 💻 CLI Client

```bash
# Health Check
python3 cli_client.py health
kapi-health

# Personas listen
python3 cli_client.py list
kapi-list

# Chat
kapi chat recon "Analysiere example.com" --complete

# System Prompt anzeigen
kapi prompt exploit

# Admin Dashboard
kapi-admin
kapi admin --logs

# Interaktiver Modus
kapi interactive --complete
```

## 📋 cURL Beispiele

```bash
# Health Check
curl http://127.0.0.1:5000/api/v1/health

# Alle Personas
curl http://127.0.0.1:5000/api/v1/personas

# Chat mit Recon Persona
curl -X POST http://127.0.0.1:5000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dein-api-key" \
  -d '{
    "persona": "recon",
    "message": "Analysiere example.com"
  }'

# Chat mit Kimi API Integration (echte AI-Antwort)
curl -X POST http://127.0.0.1:5000/api/v1/chat/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dein-api-key" \
  -d '{
    "persona": "exploit",
    "message": "Schreibe SQLi Scanner",
    "temperature": 0.7
  }'

# Admin Stats
curl http://127.0.0.1:5000/admin

# Logs anzeigen
curl http://127.0.0.1:5000/admin/logs
```

## 🐍 Python Client

```python
from cli_client import KimiAPIClient

client = KimiAPIClient("http://127.0.0.1:5000", "dein-api-key")

# Liste Personas
personas = client.list_personas()
print(f"Verfügbar: {personas['count']} Personas")

# Chat
response = client.chat(
    persona="cloud",
    message="AWS S3 Bucket Enumeration",
    temperature=0.5,
    complete=True  # Nutzt echte Kimi API
)
print(response['response'])

# Admin Stats
stats = client.admin_stats()
print(f"Total Requests: {stats['stats']['total_requests']}")
```

## 🎭 Verfügbare Personas

| ID | Name | Kategorie |
|----|------|-----------|
| `recon` | 🔍 Recon/OSINT Specialist | core |
| `exploit` | 💣 Exploit Developer | core |
| `report` | 📝 Technical Writer | core |
| `audit` | 🔐 Code Auditor | core |
| `social` | 🎭 Social Engineering Specialist | extended |
| `network` | 🌐 Network Pentester | extended |
| `mobile` | 📱 Mobile Security Expert | extended |
| `redteam` | 🕵️ Red Team Operator | extended |
| `ics` | 🧪 ICS/SCADA Specialist | extended |
| `cloud` | ☁️ Cloud Security Expert | extended |
| `crypto` | 🔬 Cryptography Analyst | extended |

## 🔐 Authentifizierung

API Key kann über:
- Header: `X-API-Key: dein-key`
- Query: `?api_key=dein-key`
- Environment: `KIMI_API_KEY`

Der Key wird aus `config.json` (`api.api_key` oder `backends.kimi_api_key`) gelesen.

### Ohne Authentifizierung (DEV ONLY!)
```bash
python3 kimi_personas_api.py --no-auth
```

## 📁 Postman Collection

Importiere `postman_collection.json` in Postman. Setze die Variablen:
- `base_url`: `http://127.0.0.1:5000`
- `api_key`: Dein API Key

## 🐳 Docker

```bash
# Build
docker build -t kimi-personas-api .

# Run
docker run -p 5000:5000 \
  -v ~/.config/kimi:/root/.config/kimi:ro \
  -v ~/Zen-Ai-Pentest/config.json:/app/config.json:ro \
  kimi-personas-api

# Mit docker-compose
docker-compose up -d
```

## 🔄 CI/CD Integration

```yaml
# GitHub Actions Beispiel
- name: Security Review mit Kimi Audit
  run: |
    response=$(curl -s -X POST ${{ secrets.KIMI_API_URL }}/api/v1/chat/complete \
      -H "X-API-Key: ${{ secrets.KIMI_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{
        "persona": "audit",
        "message": "Reviewe diesen Code",
        "context": "'$(cat changed_files.py)'"
      }')
    echo "$response" | jq -r '.response'
```

## 📊 Monitoring

```bash
# Logs in Echtzeit
kimi-api-logs

# Oder manuell
tail -f ~/Zen-Ai-Pentest/logs/api_requests.log

# Admin Dashboard
curl http://127.0.0.1:5000/admin | jq
```

## 🔧 Troubleshooting

| Problem | Lösung |
|---------|--------|
| `ModuleNotFoundError: flask` | `pip install flask flask-cors flask-sock` |
| `API Key not configured` | Key in `config.json` oder `--no-auth` |
| `Persona not found` | `python3 tools/update_personas.py` ausführen |
| Web UI lädt nicht | Browser-Cache leeren, `/` aufrufen |

## 📝 Log Format

```
2024-02-07 12:34:56 | 127.0.0.1 | GET /api/v1/personas | Status: 200 | Duration: 0.012s | UA: Mozilla/5.0...
```
