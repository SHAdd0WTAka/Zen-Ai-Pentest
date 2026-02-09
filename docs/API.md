# Zen-AI-Pentest API Documentation

Complete REST API reference for Zen-AI-Pentest with examples in curl, Python, and JavaScript.

---

## Overview

RESTful API for the Zen AI Pentest framework with:
- **Automatic Documentation** - Swagger UI at `/docs`
- **WebSocket Support** - Real-time updates
- **JWT Authentication** - Secure access control
- **Rate Limiting** - Protection against abuse
- **Multiple Output Formats** - JSON, PDF, HTML reports

---

## Base URL

```
Development: http://localhost:8000
Production:  https://api.zen-pentest.local
```

---

## Authentication

All endpoints (except `/health` and `/info`) require authentication.

### Login

**Endpoint:** `POST /api/v1/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include in all subsequent requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Register New User

**Endpoint:** `POST /api/v1/auth/register`

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pentester",
    "email": "pentester@example.com",
    "password": "secure_password123",
    "full_name": "John Doe"
  }'
```

---

## Endpoints

### Health & Info

#### Health Check

**Endpoint:** `GET /health`

No authentication required.

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-01-31T12:00:00Z",
  "services": {
    "database": "connected",
    "cache": "connected",
    "agents": "running"
  }
}
```

#### API Info

**Endpoint:** `GET /info`

```bash
curl -X GET http://localhost:8000/info
```

---

### Scans

#### List Scans

**Endpoint:** `GET /api/v1/scans/`

**Query Parameters:**
- `skip` (int): Offset for pagination (default: 0)
- `limit` (int): Max results per page (default: 100)
- `status` (string): Filter by status (pending, running, completed, failed)

```bash
curl -X GET "http://localhost:8000/api/v1/scans/?skip=0&limit=100&status=completed" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "scans": [
    {
      "id": "scan_abc123",
      "name": "Network Scan",
      "target": "192.168.1.0/24",
      "scan_type": "network",
      "status": "completed",
      "progress": 100,
      "findings_count": 15,
      "created_at": "2026-01-31T10:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 100
}
```

#### Create Scan

**Endpoint:** `POST /api/v1/scans/`

```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_type": "full",
    "name": "Weekly Security Scan",
    "description": "Comprehensive security assessment",
    "options": {
      "ports": "top1000",
      "aggressive": false,
      "tools": ["nmap", "nuclei", "sqlmap"]
    }
  }'
```

**Response:**
```json
{
  "id": "scan_abc123",
  "name": "Weekly Security Scan",
  "target": "example.com",
  "scan_type": "full",
  "status": "pending",
  "created_at": "2026-01-31T12:00:00Z"
}
```

#### Get Scan

**Endpoint:** `GET /api/v1/scans/{scan_id}`

```bash
curl -X GET http://localhost:8000/api/v1/scans/scan_abc123 \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "id": "scan_abc123",
  "name": "Network Scan",
  "target": "192.168.1.0/24",
  "scan_type": "network",
  "status": "completed",
  "config": {...},
  "result_summary": "Found 15 issues",
  "created_at": "2026-01-31T10:00:00Z",
  "started_at": "2026-01-31T10:00:05Z",
  "completed_at": "2026-01-31T10:15:30Z"
}
```

#### Update Scan

**Endpoint:** `PATCH /api/v1/scans/{scan_id}`

```bash
curl -X PATCH http://localhost:8000/api/v1/scans/scan_abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'
```

#### Delete Scan

**Endpoint:** `DELETE /api/v1/scans/{scan_id}`

```bash
curl -X DELETE http://localhost:8000/api/v1/scans/scan_abc123 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Findings

#### List Findings

**Endpoint:** `GET /api/v1/findings/`

**Query Parameters:**
- `scan_id` (string): Filter by scan
- `severity` (string): Filter by severity (critical, high, medium, low, info)
- `status` (string): Filter by status
- `limit` (int): Max results

```bash
curl -X GET "http://localhost:8000/api/v1/findings/?severity=critical&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "findings": [
    {
      "id": "find_xyz789",
      "scan_id": "scan_abc123",
      "title": "SQL Injection in login form",
      "description": "The login form is vulnerable to SQL injection...",
      "severity": "critical",
      "cvss_score": 9.8,
      "tool": "sqlmap",
      "target": "https://example.com/login",
      "status": "open",
      "created_at": "2026-01-31T10:05:00Z"
    }
  ],
  "total": 25
}
```

#### Get Findings Summary

**Endpoint:** `GET /api/v1/findings/summary`

```bash
curl -X GET http://localhost:8000/api/v1/findings/summary \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total": 25,
  "by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 8
  },
  "by_status": {
    "open": 20,
    "verified": 3,
    "false_positive": 2
  }
}
```

#### Update Finding

**Endpoint:** `PATCH /api/v1/findings/{finding_id}`

```bash
curl -X PATCH http://localhost:8000/api/v1/findings/find_xyz789 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "verified",
    "severity": "high",
    "notes": "Confirmed SQL injection vulnerability"
  }'
```

---

### Tools

#### List Tools

**Endpoint:** `GET /api/v1/tools/`

```bash
curl -X GET http://localhost:8000/api/v1/tools/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "tools": {
    "network": [
      {"name": "nmap_scan", "description": "Port scanning with Nmap"},
      {"name": "masscan", "description": "Fast port scanner"}
    ],
    "web": [
      {"name": "sqlmap_scan", "description": "SQL Injection detection"},
      {"name": "nuclei_scan", "description": "Vulnerability scanner"}
    ],
    "exploitation": [
      {"name": "metasploit", "description": "Exploitation framework"}
    ]
  }
}
```

#### Execute Tool

**Endpoint:** `POST /api/v1/tools/execute`

```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "nmap_scan",
    "target": "scanme.nmap.org",
    "parameters": {
      "ports": "22,80,443",
      "scan_type": "syn"
    },
    "timeout": 300
  }'
```

**Response:**
```json
{
  "execution_id": "exec_def456",
  "scan_id": "scan_ghi789",
  "status": "started",
  "message": "Tool nmap_scan execution started",
  "estimated_duration": 60
}
```

---

### Reports

#### Generate Report

**Endpoint:** `POST /api/v1/reports/`

```bash
curl -X POST http://localhost:8000/api/v1/reports/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "scan_abc123",
    "name": "Q1 Security Assessment",
    "format": "pdf",
    "template": "executive",
    "include_evidence": true
  }'
```

**Response:**
```json
{
  "id": "rep_ghi789",
  "scan_id": "scan_abc123",
  "format": "pdf",
  "template": "executive",
  "status": "pending",
  "created_at": "2026-01-31T12:00:00Z"
}
```

#### List Reports

**Endpoint:** `GET /api/v1/reports/`

```bash
curl -X GET http://localhost:8000/api/v1/reports/ \
  -H "Authorization: Bearer $TOKEN"
```

#### Download Report

**Endpoint:** `GET /api/v1/reports/{report_id}/download`

```bash
curl -X GET http://localhost:8000/api/v1/reports/rep_ghi789/download \
  -H "Authorization: Bearer $TOKEN" \
  -o "security_report.pdf"
```

---

### VPN

#### Connect VPN

**Endpoint:** `POST /api/v1/vpn/connect`

```bash
curl -X POST http://localhost:8000/api/v1/vpn/connect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CH",
    "protocol": "wireguard",
    "security_level": "secure-core",
    "kill_switch": true
  }'
```

#### Get VPN Status

**Endpoint:** `GET /api/v1/vpn/status`

```bash
curl -X GET http://localhost:8000/api/v1/vpn/status \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
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

**Endpoint:** `POST /api/v1/vpn/rotate`

```bash
curl -X POST "http://localhost:8000/api/v1/vpn/rotate?country=NL" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Agents

#### List Agents

**Endpoint:** `GET /api/v1/agents/`

```bash
curl -X GET http://localhost:8000/api/v1/agents/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_recon_001",
      "name": "Reconnaissance Agent",
      "status": "idle",
      "type": "recon"
    },
    {
      "id": "agent_vuln_001",
      "name": "Vulnerability Agent",
      "status": "busy",
      "type": "vulnerability"
    }
  ]
}
```

#### Assign Task

**Endpoint:** `POST /api/v1/agents/{agent_id}/task`

```bash
curl -X POST http://localhost:8000/api/v1/agents/agent_recon_001/task \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "recon",
    "parameters": {
      "target": "example.com",
      "depth": "medium"
    },
    "priority": 8
  }'
```

---

### System

#### System Metrics (Admin)

**Endpoint:** `GET /api/v1/system/metrics`

Requires admin token.

```bash
curl -X GET http://localhost:8000/api/v1/system/metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Response:**
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.5,
  "disk_percent": 34.0,
  "active_scans": 5,
  "queued_scans": 2,
  "active_agents": 8
}
```

---

## WebSocket

### Real-Time Scan Updates

**Connection:** `WS /ws/scans/{scan_id}`

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans/scan_abc123');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
  // { type: "status", status: "running", message: "Scan in progress" }
};
```

**Message Types:**
- `status`: Scan status update
- `progress`: Progress percentage
- `log`: Tool execution log
- `finding`: New finding discovered
- `error`: Error occurred
- `complete`: Scan completed

### Agent Updates

**Connection:** `WS /ws/agents`

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agents');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent update:', data);
};
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data |
| 429 | Too Many Requests - Rate limited |
| 500 | Server Error - Internal error |

---

## Rate Limiting

Default limits:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643640000
```

---

## Pagination

List endpoints support pagination:

```http
GET /api/v1/scans?skip=0&limit=20
```

**Response Headers:**
```
X-Total-Count: 100
X-Page-Count: 5
```

---

## Error Format

```json
{
  "detail": "Error message",
  "code": "error_code",
  "timestamp": "2026-01-31T12:00:00Z"
}
```

---

## SDK Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"

# Login
response = requests.post(
    f"{API_URL}/api/v1/auth/login",
    data={"username": "admin", "password": "admin"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create scan
response = requests.post(
    f"{API_URL}/api/v1/scans/",
    headers=headers,
    json={
        "target": "example.com",
        "scan_type": "full",
        "name": "My Scan"
    }
)
scan_id = response.json()["id"]

# Poll for results
import time
while True:
    scan = requests.get(
        f"{API_URL}/api/v1/scans/{scan_id}",
        headers=headers
    ).json()
    
    if scan["status"] in ["completed", "failed"]:
        break
    
    time.sleep(5)
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000';

// Login
const login = async () => {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: 'username=admin&password=admin'
  });
  const data = await response.json();
  return data.access_token;
};

// Create scan
const createScan = async (token, target) => {
  const response = await fetch(`${API_URL}/api/v1/scans/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      target: target,
      scan_type: 'full',
      name: 'My Scan'
    })
  });
  return response.json();
};
```

### cURL

```bash
# Login and store token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin" | jq -r '.access_token')

# Create scan
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "scan_type": "full"}'
```

---

## Testing

### Using Swagger UI

Visit `/docs` for interactive API documentation and testing.

### Using ReDoc

Visit `/redoc` for alternative API documentation.

---

## More Examples

For comprehensive examples in multiple languages, see **[API_EXAMPLES.md](API_EXAMPLES.md)**.

---

<p align="center">
  <b>For support, see <a href="../SUPPORT.md">SUPPORT.md</a></b><br>
  <sub>© 2026 Zen AI Pentest. All rights reserved.</sub>
</p>
