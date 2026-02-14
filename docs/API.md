# Zen-AI-Pentest API Documentation

Complete REST API reference for Zen-AI-Pentest.

## Base URL

```
Local:   http://localhost:8000
Docker:  http://localhost:8000
Prod:    https://api.zen-pentest.local
```

## Authentication

All endpoints (except `/health` and `/info`) require authentication.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using Token

```http
GET /scans
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

## Endpoints

### Health & Info

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-01-31T12:00:00"
}
```

#### API Info
```http
GET /info
```

### Scans

#### List Scans
```http
GET /scans?skip=0&limit=100&status=completed
```

**Query Parameters:**
- `skip` (int): Offset for pagination
- `limit` (int): Max results per page
- `status` (string): Filter by status (pending, running, completed, failed)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Network Scan",
    "target": "192.168.1.0/24",
    "scan_type": "network",
    "status": "completed",
    "created_at": "2026-01-31T10:00:00",
    "findings_count": 15
  }
]
```

#### Create Scan
```http
POST /scans
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Web Application Scan",
  "target": "https://example.com",
  "scan_type": "web",
  "config": {
    "tools": ["nmap", "sqlmap", "nuclei"],
    "ports": "80,443",
    "intensity": "high"
  }
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Web Application Scan",
  "target": "https://example.com",
  "scan_type": "web",
  "status": "pending",
  "created_at": "2026-01-31T12:00:00"
}
```

#### Get Scan
```http
GET /scans/{scan_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "name": "Network Scan",
  "target": "192.168.1.0/24",
  "scan_type": "network",
  "status": "completed",
  "config": {...},
  "result_summary": "Found 15 issues",
  "created_at": "2026-01-31T10:00:00",
  "started_at": "2026-01-31T10:00:05",
  "completed_at": "2026-01-31T10:15:30"
}
```

#### Update Scan
```http
PATCH /scans/{scan_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "cancelled"
}
```

#### Delete Scan
```http
DELETE /scans/{scan_id}
Authorization: Bearer <token>
```

### Findings

#### List Findings
```http
GET /scans/{scan_id}/findings?severity=critical
Authorization: Bearer <token>
```

**Query Parameters:**
- `severity`: Filter by severity (critical, high, medium, low, info)

**Response:**
```json
[
  {
    "id": 1,
    "scan_id": 1,
    "title": "SQL Injection in login form",
    "description": "The login form is vulnerable to SQL injection...",
    "severity": "critical",
    "cvss_score": 9.8,
    "tool": "sqlmap",
    "target": "https://example.com/login",
    "created_at": "2026-01-31T10:05:00"
  }
]
```

#### Add Finding
```http
POST /scans/{scan_id}/findings
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Missing Security Headers",
  "description": "X-Frame-Options header not set",
  "severity": "medium",
  "tool": "nuclei",
  "target": "https://example.com"
}
```

### Tools

#### List Tools
```http
GET /tools
Authorization: Bearer <token>
```

**Response:**
```json
{
  "tools": [
    {
      "name": "nmap_scan",
      "description": "Port scanning with Nmap",
      "category": "network"
    },
    {
      "name": "sqlmap_scan",
      "description": "SQL Injection detection",
      "category": "web"
    }
  ]
}
```

#### Execute Tool
```http
POST /tools/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "tool_name": "nmap_scan",
  "target": "scanme.nmap.org",
  "parameters": {
    "ports": "22,80,443"
  },
  "timeout": 300
}
```

**Response:**
```json
{
  "scan_id": 3,
  "status": "started",
  "message": "Tool nmap_scan execution started",
  "estimated_duration": 60
}
```

### Reports

#### Generate Report
```http
POST /reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "scan_id": 1,
  "format": "pdf",
  "template": "executive"
}
```

**Response:**
```json
{
  "id": 1,
  "scan_id": 1,
  "format": "pdf",
  "status": "pending",
  "created_at": "2026-01-31T12:00:00"
}
```

#### List Reports
```http
GET /reports
Authorization: Bearer <token>
```

#### Download Report
```http
GET /reports/{report_id}/download
Authorization: Bearer <token>
```

Returns the report file (PDF/HTML/JSON).

### WebSocket

#### Real-Time Scan Updates
```
WS /ws/scans/{scan_id}
```

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans/1');

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
- `log`: Tool execution log
- `finding`: New finding discovered
- `error`: Error occurred
- `complete`: Scan completed

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
| 500 | Server Error - Internal error |

## Rate Limiting

Default limits:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643640000
```

## Pagination

List endpoints support pagination:

```http
GET /scans?skip=0&limit=20
```

**Response Headers:**
```
X-Total-Count: 100
X-Page-Count: 5
```

## Error Format

```json
{
  "detail": "Error message",
  "code": "error_code",
  "timestamp": "2026-01-31T12:00:00"
}
```

## SDK Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"
token = "your-jwt-token"

# Create scan
response = requests.post(
    f"{API_URL}/scans",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "My Scan",
        "target": "example.com",
        "scan_type": "web"
    }
)
scan_id = response.json()["id"]

# Poll for results
import time
while True:
    scan = requests.get(
        f"{API_URL}/scans/{scan_id}",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    if scan["status"] in ["completed", "failed"]:
        break
    
    time.sleep(5)

# Get findings
findings = requests.get(
    f"{API_URL}/scans/{scan_id}/findings",
    headers={"Authorization": f"Bearer {token}"}
).json()

print(f"Found {len(findings)} issues")
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000';
const token = 'your-jwt-token';

// Create scan
const createScan = async () => {
  const response = await fetch(`${API_URL}/scans`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'My Scan',
      target: 'example.com',
      scan_type: 'web'
    })
  });
  return response.json();
};

// WebSocket connection
const connectWebSocket = (scanId) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/scans/${scanId}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
  };
  
  return ws;
};
```

## Changelog

### v2.0.0 (2026-01-31)
- Initial API release
- REST endpoints for scans, findings, reports
- WebSocket support
- JWT authentication
