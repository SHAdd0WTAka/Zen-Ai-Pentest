# API Documentation

Zen-AI-Pentest bietet eine RESTful API basierend auf FastAPI.

## Base URL

```
# Lokal
http://localhost:8000

# Production
https://zen-ai-pentest.workers.dev
```

## Authentication

Alle Endpunkte benötigen JWT-Authentication.

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "[YOUR_PASSWORD_HERE]"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...[EXAMPLE_TOKEN]",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Authenticated Request

```bash
curl http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer [YOUR_JWT_TOKEN_HERE]"
```

## Endpoints

### Scans

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/scans` | Alle Scans listen |
| POST | `/api/v1/scans` | Neuen Scan starten |
| GET | `/api/v1/scans/{id}` | Scan-Details |
| DELETE | `/api/v1/scans/{id}` | Scan löschen |

**Scan starten:**
```bash
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer [YOUR_JWT_TOKEN_HERE]" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_type": "recon",
    "tools": ["nmap", "subfinder"]
  }'
```

### Agents

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/agents` | Alle Agents listen |
| POST | `/api/v1/agents` | Agent erstellen |
| GET | `/api/v1/agents/{id}` | Agent-Details |
| POST | `/api/v1/agents/{id}/execute` | Task ausführen |

### Tools

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/tools` | Verfügbare Tools |
| POST | `/api/v1/tools/execute` | Tool ausführen |

**Tool ausführen:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Authorization: Bearer [YOUR_JWT_TOKEN_HERE]" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "nmap",
    "target": "example.com",
    "options": ["-sV", "-p", "80,443"]
  }'
```

## WebSocket

Realtime-Updates für laufende Scans.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Scan update:', data);
};
```

## Fehler-Codes

| Code | Bedeutung | Lösung |
|------|-----------|--------|
| 401 | Unauthorized | Token erneuern |
| 403 | Forbidden | Berechtigungen prüfen |
| 404 | Not Found | Ressource existiert nicht |
| 422 | Validation Error | Request-Format prüfen |
| 500 | Server Error | Logs prüfen |

## Rate Limiting

- **Limit:** 100 Requests/Minute
- **Header:** `X-RateLimit-Remaining`

## OpenAPI/Swagger

API-Dokumentation ist verfügbar unter:

```
http://localhost:8000/docs
http://localhost:8000/redoc
```
