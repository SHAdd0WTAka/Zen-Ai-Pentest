# Postman Integration Guide

Vollständige Postman-Integration für Zen AI Pentest API mit Collection, Environments und Newman-Runner für CI/CD.

## 📦 Was ist enthalten?

| Datei | Beschreibung |
|-------|-------------|
| `Zen-AI-Pentest.postman_collection.json` | API Collection mit 30+ Endpoints |
| `Local.postman_environment.json` | Lokale Entwicklung |
| `Staging.postman_environment.json` | Staging Umgebung |
| `Production.postman_environment.json` | Produktion |
| `newman-runner.js` | CLI Runner für CI/CD |
| `.github/workflows/postman-tests.yml` | GitHub Action |

## 🚀 Quick Start

### 1. Postman importieren

```bash
# Collection importieren
curl -X POST https://api.getpostman.com/collections \
  -H "X-Api-Key: $POSTMAN_API_KEY" \
  -d @postman/Zen-AI-Pentest.postman_collection.json
```

Oder manuell:
1. Postman öffnen
2. File → Import
3. `postman/Zen-AI-Pentest.postman_collection.json` wählen

### 2. Environment konfigurieren

```bash
# Umgebung importieren
File → Import → postman/Local.postman_environment.json
```

Variablen anpassen:
- `base_url`: API URL (default: http://localhost:8000)
- `username`: Dein Username
- `password`: Dein Passwort

### 3. Ersten Request senden

```bash
# Health Check
GET {{base_url}}/health

# Login
POST {{base_url}}/auth/login
{
    "username": "{{username}}",
    "password": "{{password}}"
}
```

## 📁 Collection Struktur

```
Zen AI Pentest API
├── 🔍 Health & Status
│   ├── Health Check
│   └── System Status
│
├── 🔐 Authentication
│   ├── Login
│   ├── Refresh Token
│   └── Get Current User
│
├── 🔎 Scans
│   ├── List Scans
│   ├── Create Scan
│   ├── Get Scan
│   ├── Get Scan Status
│   └── Cancel Scan
│
├── 🚨 Findings
│   ├── List Findings
│   ├── Get Finding
│   └── Create Finding
│
├── 🌐 OSINT
│   ├── Harvest Emails
│   └── Domain Recon
│
├── 💾 Database
│   ├── Search CVE
│   ├── Get CVE by ID
│   └── List Ransomware Families
│
├── 🔧 Integration Bridge
│   ├── Run Nmap Scan
│   ├── Run Nuclei Scan
│   └── Get Tool Scan Status
│
├── 🛡️ Zen Shield
│   ├── Sanitize Data
│   └── Shield Health Check
│
└── 📄 Reports
    ├── Generate Report
    └── Download Report
```

## 🧪 Testing mit Newman

### Installation

```bash
cd postman
npm install
```

### Lokale Tests

```bash
# Alle Tests laufen lassen
npm test

# Health Checks only
npm run test:health

# Spezifischen Folder testen
npm run test:folder "Authentication"

# Mit Staging Umgebung
npm run test:staging
```

### CLI Usage

```bash
# Full collection
node newman-runner.js run local

# Health checks only
node newman-runner.js health local

# Specific folder
node newman-runner.js folder local "Scans"

# Available folders listen
node newman-runner.js list
```

### Mit Docker

```bash
# Newman Docker Image verwenden
docker run -v $(pwd)/postman:/etc/newman \
  postman/newman:latest \
  run Zen-AI-Pentest.postman_collection.json \
  -e Local.postman_environment.json \
  --reporters cli,htmlextra
```

## 🔧 Tests anpassen

### Pre-request Scripts

In Postman, unter dem "Pre-request Script" Tab:

```javascript
// Timestamp setzen
pm.environment.set("timestamp", new Date().toISOString());

// Random ID generieren
pm.environment.set("random_id", Math.random().toString(36).substring(7));
```

### Tests

Unter dem "Tests" Tab:

```javascript
// Status Code prüfen
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Response Time
pm.test("Response time < 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

// JSON Schema validieren
pm.test("Valid scan response", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('scan_id');
    pm.expect(jsonData).to.have.property('status');
});

// Variable speichern
pm.environment.set("scan_id", pm.response.json().scan_id);
```

## 🔄 CI/CD Integration

### GitHub Actions

Automatisch bei jedem Push:

```yaml
# .github/workflows/postman-tests.yml
# Bereits konfiguriert!
```

### Manuelles Triggern

```bash
# Über GitHub Web UI
Actions → Postman API Tests → Run workflow

# Environment wählen: local, staging, production
```

### Test Reports

Reports werden automatisch als Artifacts gespeichert:

- `report-{environment}-{timestamp}.html` - HTML Report
- `report-{environment}-{timestamp}.json` - JSON Report
- `report-{environment}-{timestamp}.xml` - JUnit XML
- `report-{environment}-{timestamp}-summary.json` - Summary

### Report ansehen

```bash
# Report Server starten
cd postman
npm run report:serve

# Öffne http://localhost:3000
```

## 🌐 Umgebungen verwalten

### Lokale Entwicklung

```json
{
  "base_url": "http://localhost:8000",
  "integration_bridge_url": "http://localhost:8080",
  "shield_url": "http://localhost:9000"
}
```

### Staging

```json
{
  "base_url": "https://api-staging.zen-pentest.example.com",
  "integration_bridge_url": "https://bridge-staging.zen-pentest.example.com",
  "shield_url": "https://shield-staging.zen-pentest.example.com"
}
```

### Produktion

```json
{
  "base_url": "https://api.zen-pentest.example.com",
  "integration_bridge_url": "https://bridge.zen-pentest.example.com",
  "shield_url": "https://shield.zen-pentest.example.com"
}
```

## 📊 Test Coverage

| Endpoint | Tests |
|----------|-------|
| Health | ✅ Status, Response Time |
| Auth | ✅ Login, Token, Refresh |
| Scans | ✅ CRUD, Status, Cancel |
| Findings | ✅ List, Get, Create |
| OSINT | ✅ Emails, Domain |
| Database | ✅ CVE, Ransomware |
| Integration | ✅ Nmap, Nuclei, Status |
| Shield | ✅ Sanitize, Health |
| Reports | ✅ Generate, Download |

## 🔐 Sicherheit

### Secrets in Postman

1. **Environment Variables**: Verwende `type: "secret"` für Passwörter
2. **Never commit**: `.postman_environment.json` mit echten Credentials
3. **Use Vault**: Für Produktion, verwende Postman Vault

### Pre-request Script für Auth

```javascript
// Automatisches Token Refresh
const token = pm.environment.get("access_token");
const tokenExpiry = pm.environment.get("token_expiry");

if (!token || Date.now() > tokenExpiry) {
    // Login und Token speichern
    pm.sendRequest({
        url: `${pm.environment.get("base_url")}/auth/login`,
        method: 'POST',
        body: {
            mode: 'raw',
            raw: JSON.stringify({
                username: pm.environment.get("username"),
                password: pm.environment.get("password")
            })
        }
    }, function (err, response) {
        const jsonData = response.json();
        pm.environment.set("access_token", jsonData.access_token);
        pm.environment.set("token_expiry", Date.now() + jsonData.expires_in * 1000);
    });
}
```

## 🐛 Troubleshooting

### Connection Refused

```bash
# Prüfe ob API läuft
curl http://localhost:8000/health

# Port prüfen
netstat -tlnp | grep 8000
```

### Authentication Failed

```bash
# Login manuell testen
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### Tests Failen

```bash
# Mit verbose output
newman run collection.json -e env.json --verbose

# Nur failed tests zeigen
newman run collection.json --reporters cli --bail false
```

## 📚 Weitere Ressourcen

- [Newman Documentation](https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/)
- [Postman Testing](https://learning.postman.com/docs/writing-scripts/test-scripts/)
- [API Documentation](API_DOCUMENTATION.md)

## 🤝 Contributing

Neue Endpoints zur Collection hinzufügen:

1. Endpoint in Postman erstellen
2. Pre-request Script hinzufügen (falls nötig)
3. Tests schreiben
4. Collection exportieren
5. PR erstellen
