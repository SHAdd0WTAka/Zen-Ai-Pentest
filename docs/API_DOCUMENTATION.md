# Zen AI Pentest API Documentation

## Overview

RESTful API for the Zen AI Pentest framework with:
- **Automatic Documentation** - Swagger UI at `/docs`
- **WebSocket Support** - Real-time updates
- **JWT Authentication** - Secure access control
- **Rate Limiting** - Protection against abuse
- **Multiple Output Formats** - JSON, PDF, HTML reports

## Base URL

```
Development: http://localhost:8080
Production: https://your-domain.com
```

## Authentication

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include in all subsequent requests:

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Register New User

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "pentester",
  "email": "pentester@example.com",
  "password": "secure_password123",
  "full_name": "John Doe"
}
```

## Endpoints

### Scans

#### Create Scan

```bash
POST /api/v1/scans/
Authorization: Bearer <token>
Content-Type: application/json

{
  "target": "example.com",
  "scan_type": "full",
  "name": "Weekly Security Scan",
  "description": "Comprehensive security assessment",
  "options": {
    "ports": "top1000",
    "aggressive": false
  }
}
```

#### List Scans

```bash
GET /api/v1/scans/?status=running&limit=20
Authorization: Bearer <token>
```

Response:
```json
{
  "scans": [
    {
      "id": "scan_123",
      "name": "Weekly Security Scan",
      "target": "example.com",
      "status": "running",
      "progress": 45,
      "findings_count": 3
    }
  ]
}
```

#### Get Scan Details

```bash
GET /api/v1/scans/{scan_id}
Authorization: Bearer <token>
```

### Findings

#### List Findings

```bash
GET /api/v1/findings/?severity=critical&limit=50
Authorization: Bearer <token>
```

#### Update Finding

```bash
PATCH /api/v1/findings/{finding_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "verified",
  "severity": "high",
  "notes": "Confirmed SQL injection vulnerability"
}
```

#### Get Findings Summary

```bash
GET /api/v1/findings/summary
Authorization: Bearer <token>
```

Response:
```json
{
  "total": 25,
  "by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 8
  }
}
```

### Reports

#### Generate Report

```bash
POST /api/v1/reports/
Authorization: Bearer <token>
Content-Type: application/json

{
  "scan_id": "scan_123",
  "name": "Q1 Security Assessment",
  "format": "pdf",
  "template": "executive",
  "include_evidence": true
}
```

#### Download Report

```bash
GET /api/v1/reports/{report_id}/download
Authorization: Bearer <token>
```

### VPN

#### Connect VPN

```bash
POST /api/v1/vpn/connect
Authorization: Bearer <token>
Content-Type: application/json

{
  "country": "CH",
  "protocol": "wireguard",
  "security_level": "secure-core",
  "kill_switch": true
}
```

#### Get VPN Status

```bash
GET /api/v1/vpn/status
Authorization: Bearer <token>
```

Response:
```json
{
  "connected": true,
  "server_location": "Zurich, CH",
  "public_ip": "185.159.158.XXX",
  "protocol": "wireguard",
  "kill_switch": true
}
```

#### Rotate IP

```bash
POST /api/v1/vpn/rotate?country=NL
Authorization: Bearer <token>
```

### Agents

#### List Agents

```bash
GET /api/v1/agents/
Authorization: Bearer <token>
```

#### Assign Task

```bash
POST /api/v1/agents/{agent_id}/task
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_type": "recon",
  "parameters": {
    "target": "example.com",
    "depth": "medium"
  },
  "priority": 8
}
```

### System

#### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "cache": "connected",
    "agents": "running"
  }
}
```

#### System Metrics (Admin)

```bash
GET /api/v1/system/metrics
Authorization: Bearer <admin_token>
```

## WebSocket

### Connect to Scan Updates

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/scans/{scan_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Scan update:', data);
};
```

### Connect to Agent Updates

```javascript
const ws = new WebSocket('ws://localhost:8080/ws/agents');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent update:', data);
};
```

## Rate Limits

| User Type | Limit |
|-----------|-------|
| Anonymous | 10 requests/minute |
| Authenticated | 100 requests/minute |
| Admin | 1000 requests/minute |

## Error Responses

### 400 Bad Request

```json
{
  "error": "Bad request",
  "message": "Invalid parameters",
  "details": {
    "target": ["Target is required"]
  }
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

### 429 Too Many Requests

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

## Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8080/api/v1/auth/login",
    data={"username": "user", "password": "pass"}
)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Create scan
scan = requests.post(
    "http://localhost:8080/api/v1/scans/",
    headers=headers,
    json={"target": "example.com", "scan_type": "full"}
).json()

print(f"Scan created: {scan['id']}")
```

### JavaScript

```javascript
// Using fetch
const login = async () => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const { access_token } = await response.json();
  return access_token;
};

const createScan = async (token, target) => {
  const response = await fetch('/api/v1/scans/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ target, scan_type: 'full' })
  });
  return response.json();
};
```

### cURL

```bash
# Login and store token
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -d "username=pentester&password=secret" | jq -r '.access_token')

# Create scan
curl -X POST http://localhost:8080/api/v1/scans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "scan_type": "full"}'

# Check scan status
curl http://localhost:8080/api/v1/scans/scan_123 \
  -H "Authorization: Bearer $TOKEN"
```

## Testing

### Using Swagger UI

Visit `/docs` for interactive API documentation and testing.

### Using ReDoc

Visit `/redoc` for alternative API documentation.

## SDKs

### Python SDK (Coming Soon)

```python
from zen_ai_pentest import Client

client = Client("http://localhost:8080", token="your_token")

# Create scan
scan = client.scans.create(target="example.com")

# Wait for completion
scan.wait_for_completion()

# Get findings
findings = client.findings.list(scan_id=scan.id)
```

---

*For more information, visit the [GitHub repository](https://github.com/SHAdd0WTAka/zen-ai-pentest)*
