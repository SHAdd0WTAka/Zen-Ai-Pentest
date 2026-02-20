# Zen-AI-Pentest API Guide

> **Complete API reference for developers**

---

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Endpoints Overview](#endpoints-overview)
- [Core Endpoints](#core-endpoints)
- [WebSocket Usage](#websocket-usage)
- [Error Handling](#error-handling)
- [SDK Examples](#sdk-examples)
- [Best Practices](#best-practices)

---

## Getting Started

### Base URLs

| Environment | URL |
|-------------|-----|
| Local Development | `http://localhost:8000` |
| Docker | `http://localhost:8000` |
| Production | `https://api.zen-pentest.local` |

### Interactive Documentation

Once the server is running, access interactive docs:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Quick Start

```bash
# Start the server
uvicorn api.main:app --reload

# Test with curl
curl http://localhost:8000/health
```

---

## Authentication

Zen-AI-Pentest uses **JWT (JSON Web Tokens)** for authentication.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
}
```

### Using the Token

Include the token in the `Authorization` header:

```http
GET /scans
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

### Token Refresh

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
}
```

### API Keys (Alternative)

For service-to-service communication:

```http
GET /scans
X-API-Key: your-api-key-here
```

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse.

### Limits

| User Type | Limit | Window |
|-----------|-------|--------|
| Anonymous | 100 requests | 1 hour |
| Authenticated | 1000 requests | 1 hour |
| Admin | 5000 requests | 1 hour |
| Scan Execution | 10 concurrent | - |

### Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705315800
X-RateLimit-Retry-After: 3600
```

### Handling Rate Limits

```python
import time
import requests

def make_request_with_retry(url, headers):
    """Make request with rate limit handling."""
    response = requests.get(url, headers=headers)
    
    if response.status_code == 429:
        # Get retry after
        retry_after = int(response.headers.get('X-RateLimit-Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return make_request_with_retry(url, headers)
    
    return response
```

---

## Endpoints Overview

### Endpoint Categories

| Category | Base Path | Description |
|----------|-----------|-------------|
| Authentication | `/auth/*` | Login, logout, token management |
| Scans | `/scans/*` | Scan management |
| Findings | `/findings/*` | Vulnerability findings |
| Tools | `/tools/*` | Security tool execution |
| Reports | `/reports/*` | Report generation |
| Agents | `/agents/*` | AI agent management |
| Orchestrator | `/api/v1/orchestrator/*` | Task orchestration |
| Scheduler | `/api/v1/scheduler/*` | Job scheduling |
| Dashboard | `/api/v1/dashboard/*` | Dashboard data |
| Audit | `/api/v1/audit/*` | Audit logging |
| Health | `/health` | Health checks |

---

## Core Endpoints

### Health & Info

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2026-02-20T10:00:00Z",
  "checks": {
    "database": {"healthy": true, "latency_ms": 5},
    "redis": {"healthy": true, "latency_ms": 2},
    "disk": {"healthy": true, "usage_percent": 45}
  }
}
```

#### API Information

```http
GET /info
```

**Response:**
```json
{
  "name": "Zen-AI-Pentest API",
  "version": "3.0.0",
  "environment": "production",
  "features": ["scans", "findings", "reports", "agents", "websocket"]
}
```

---

### Scans

#### List Scans

```http
GET /scans?skip=0&limit=100&status=completed&sort=-created_at
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `skip` | integer | Number of records to skip (default: 0) |
| `limit` | integer | Max records per page (default: 20, max: 100) |
| `status` | string | Filter by status (pending, running, completed, failed) |
| `scan_type` | string | Filter by type (network, web, api) |
| `sort` | string | Sort field (+field for asc, -field for desc) |

**Response:**
```json
{
  "data": [
    {
      "id": "scan-123",
      "name": "Network Scan",
      "target": "192.168.1.0/24",
      "scan_type": "network",
      "status": "completed",
      "progress": 100,
      "findings_count": 15,
      "created_at": "2026-02-20T10:00:00Z",
      "started_at": "2026-02-20T10:00:05Z",
      "completed_at": "2026-02-20T10:15:30Z"
    }
  ],
  "pagination": {
    "total": 150,
    "skip": 0,
    "limit": 20,
    "has_more": true
  }
}
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
  "description": "Comprehensive security assessment",
  "config": {
    "tools": ["nmap", "nuclei", "sqlmap"],
    "ports": "80,443,8080",
    "intensity": "high",
    "timeout": 3600,
    "risk_level": 1
  },
  "schedule": {
    "enabled": false
  }
}
```

**Config Options:**

| Option | Type | Description |
|--------|------|-------------|
| `tools` | array | Tools to use for scan |
| `ports` | string | Ports to scan (e.g., "80,443" or "top-100") |
| `intensity` | string | Scan intensity (low, medium, high) |
| `timeout` | integer | Max scan duration in seconds |
| `risk_level` | integer | Risk level 0-3 (0=safe, 3=aggressive) |
| `wordlist` | string | Custom wordlist for fuzzing |
| `exclude_paths` | array | Paths to exclude |

**Response:**
```json
{
  "id": "scan-456",
  "name": "Web Application Scan",
  "target": "https://example.com",
  "scan_type": "web",
  "status": "pending",
  "created_at": "2026-02-20T10:30:00Z",
  "estimated_duration": 1800,
  "webhook_url": "https://api.example.com/webhooks/scan"
}
```

#### Get Scan Details

```http
GET /scans/{scan_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "scan-456",
  "name": "Web Application Scan",
  "target": "https://example.com",
  "scan_type": "web",
  "status": "running",
  "progress": 65,
  "config": {...},
  "results_summary": {
    "total_findings": 12,
    "by_severity": {
      "critical": 1,
      "high": 3,
      "medium": 5,
      "low": 3
    }
  },
  "created_at": "2026-02-20T10:30:00Z",
  "started_at": "2026-02-20T10:30:05Z",
  "estimated_completion": "2026-02-20T11:00:00Z"
}
```

#### Update Scan

```http
PATCH /scans/{scan_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Scan Name",
  "status": "cancelled"
}
```

#### Delete Scan

```http
DELETE /scans/{scan_id}
Authorization: Bearer <token>
```

#### Get Scan Findings

```http
GET /scans/{scan_id}/findings?severity=high&limit=50
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "finding-789",
      "scan_id": "scan-456",
      "title": "SQL Injection in Login Form",
      "description": "The login form is vulnerable to SQL injection...",
      "severity": "critical",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "tool": "sqlmap",
      "target": "https://example.com/login",
      "evidence": {
        "request": "POST /login HTTP/1.1...",
        "response": "HTTP/1.1 200 OK...",
        "payload": "' OR '1'='1"
      },
      "remediation": "Use parameterized queries...",
      "references": ["https://owasp.org/...", "https://cwe.mitre.org/..."],
      "created_at": "2026-02-20T10:35:00Z"
    }
  ],
  "pagination": {...}
}
```

---

### Findings

#### List All Findings

```http
GET /findings?severity=critical,high&tool=sqlmap&limit=100
Authorization: Bearer <token>
```

#### Get Finding Details

```http
GET /findings/{finding_id}
Authorization: Bearer <token>
```

#### Update Finding

```http
PATCH /findings/{finding_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "severity": "medium",
  "status": "confirmed",
  "notes": "Verified manually - confirmed vulnerability"
}
```

#### Export Findings

```http
POST /findings/export
Authorization: Bearer <token>
Content-Type: application/json

{
  "format": "pdf",
  "findings": ["finding-1", "finding-2"],
  "template": "executive"
}
```

---

### Tools

#### List Available Tools

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
      "description": "Network port scanner",
      "category": "network",
      "safety_level": 1,
      "parameters": {
        "target": {"type": "string", "required": true},
        "ports": {"type": "string", "default": "top-1000"},
        "options": {"type": "string", "default": "-sV"}
      }
    },
    {
      "name": "sqlmap_scan",
      "description": "SQL injection scanner",
      "category": "web",
      "safety_level": 2,
      "parameters": {
        "target": {"type": "string", "required": true},
        "level": {"type": "integer", "default": 1, "min": 1, "max": 5},
        "risk": {"type": "integer", "default": 1, "min": 1, "max": 3}
      }
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
    "ports": "22,80,443",
    "options": "-sV --script=http-title"
  },
  "timeout": 300,
  "async": true
}
```

**Response (async):**
```json
{
  "task_id": "task-abc123",
  "status": "queued",
  "message": "Tool execution queued",
  "estimated_duration": 60,
  "webhook_url": "https://api.example.com/webhooks/task-abc123"
}
```

**Response (sync):**
```json
{
  "success": true,
  "data": {
    "ports": [
      {"port": 22, "state": "open", "service": "ssh", "version": "OpenSSH 8.2"},
      {"port": 80, "state": "open", "service": "http", "version": "nginx 1.18"}
    ]
  },
  "execution_time": 45.2
}
```

#### Get Tool Result

```http
GET /tools/execute/{task_id}
Authorization: Bearer <token>
```

---

### Reports

#### Generate Report

```http
POST /reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "scan_id": "scan-456",
  "format": "pdf",
  "template": "executive",
  "options": {
    "include_evidence": true,
    "include_remediation": true,
    "severity_filter": ["critical", "high"]
  }
}
```

**Templates:**
- `executive` - High-level summary for management
- `technical` - Detailed technical report
- `compliance` - Compliance-focused report (ISO27001, PCI-DSS)
- `developer` - Developer-friendly remediation guide

**Formats:**
- `pdf` - PDF document
- `html` - HTML report
- `json` - Machine-readable JSON
- `csv` - CSV for spreadsheets
- `xml` - XML (SARIF for CI/CD)

#### List Reports

```http
GET /reports?scan_id=scan-456&limit=20
Authorization: Bearer <token>
```

#### Download Report

```http
GET /reports/{report_id}/download
Authorization: Bearer <token>
```

---

### Agents

#### List Agents

```http
GET /agents
Authorization: Bearer <token>
```

#### Create Agent

```http
POST /agents
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Recon Agent",
  "type": "reconnaissance",
  "config": {
    "max_iterations": 10,
    "risk_level": 1,
    "tools": ["nmap", "subfinder", "httpx"]
  }
}
```

#### Run Agent

```http
POST /agents/{agent_id}/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "objective": "Perform comprehensive reconnaissance on example.com",
  "target": "example.com",
  "context": {
    "previous_findings": [],
    "scope": "*.example.com"
  }
}
```

---

### Orchestrator

#### Submit Task

```http
POST /api/v1/orchestrator/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "vulnerability_scan",
  "target": "example.com",
  "options": {
    "ports": "80,443",
    "scan_type": "quick"
  },
  "priority": "high",
  "dependencies": []
}
```

#### Get Task Status

```http
GET /api/v1/orchestrator/tasks/{task_id}
Authorization: Bearer <token>
```

#### List Tasks

```http
GET /api/v1/orchestrator/tasks?status=running&limit=100
Authorization: Bearer <token>
```

---

### Scheduler

#### Schedule Job

```http
POST /api/v1/scheduler/jobs
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Daily Security Scan",
  "description": "Automated daily vulnerability scan",
  "task_type": "vulnerability_scan",
  "task_data": {
    "target": "production.example.com"
  },
  "cron": "0 2 * * *",
  "timezone": "UTC",
  "enabled": true,
  "max_retries": 3
}
```

#### Schedule with Interval

```http
POST /api/v1/scheduler/jobs
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Subdomain Monitor",
  "task_type": "subdomain_enum",
  "task_data": {"domain": "example.com"},
  "interval": 3600,
  "timezone": "UTC"
}
```

---

### Dashboard

#### Get Dashboard Data

```http
GET /api/v1/dashboard/data
Authorization: Bearer <token>
```

**Response:**
```json
{
  "system_status": {
    "status": "healthy",
    "api": "running",
    "database": "running",
    "scheduler": "running"
  },
  "current_metrics": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 60.1,
    "tasks_running": 5,
    "tasks_queued": 2
  },
  "scan_statistics": {
    "total_scans": 150,
    "completed_today": 12,
    "failed_today": 1,
    "avg_duration": 1200
  },
  "recent_findings": [...],
  "recent_events": [...]
}
```

---

## WebSocket Usage

### Connecting

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans/scan-456?token=YOUR_TOKEN');

ws.onopen = () => {
  console.log('Connected to scan updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### Event Types

| Event Type | Description | Payload |
|------------|-------------|---------|
| `scan.status` | Scan status changed | `{ status: "running", progress: 50 }` |
| `scan.progress` | Progress update | `{ progress: 50, message: "Scanning ports..." }` |
| `scan.finding` | New finding discovered | `{ finding: {...} }` |
| `scan.complete` | Scan completed | `{ status: "completed", findings_count: 12 }` |
| `scan.error` | Error occurred | `{ error: "Timeout", message: "..." }` |
| `system.metrics` | System metrics | `{ cpu: 25, memory: 45 }` |

### Subscribe to Events

```javascript
// After connecting, subscribe to specific events
ws.send(JSON.stringify({
  action: 'subscribe',
  event_types: ['scan.status', 'scan.finding']
}));

// Set minimum priority filter
ws.send(JSON.stringify({
  action: 'set_priority',
  min_priority: 3
}));
```

### Python WebSocket Client

```python
import asyncio
import websockets
import json

async def scan_websocket(scan_id, token):
    uri = f"ws://localhost:8000/ws/scans/{scan_id}?token={token}"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data['type'] == 'scan.progress':
                print(f"Progress: {data['progress']}%")
            elif data['type'] == 'scan.complete':
                print("Scan complete!")
                break

asyncio.run(scan_websocket("scan-456", "your-token"))
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Valid token, insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Valid JSON, invalid values |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request validation failed",
    "details": [
      {
        "field": "target",
        "message": "Invalid URL format"
      }
    ],
    "timestamp": "2026-02-20T10:00:00Z",
    "request_id": "req-abc123",
    "documentation_url": "https://docs.zen-pentest.dev/errors/VALIDATION_ERROR"
  }
}
```

### Common Errors

#### Authentication Error (401)

```json
{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Invalid or expired token",
    "resolution": "Please login again to obtain a new token"
  }
}
```

#### Rate Limit Error (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 3600,
    "limit": 1000,
    "window": "1 hour"
  }
}
```

#### Validation Error (422)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "target",
        "message": "Target must be a valid URL or IP address",
        "received": "not-a-valid-target"
      },
      {
        "field": "scan_type",
        "message": "Invalid scan type",
        "allowed": ["network", "web", "api", "mobile"],
        "received": "invalid"
      }
    ]
  }
}
```

---

## SDK Examples

### Python SDK

```python
from zen_aipentest import Client

# Initialize client
client = Client(
    base_url="http://localhost:8000",
    token="your-api-token"
)

# Create a scan
scan = client.scans.create(
    name="Production Scan",
    target="https://example.com",
    scan_type="web",
    config={
        "tools": ["nmap", "nuclei", "sqlmap"],
        "intensity": "high"
    }
)

# Wait for completion with progress updates
for update in scan.wait_for_completion(timeout=3600):
    print(f"Progress: {update.progress}% - {update.message}")

# Get findings
findings = client.findings.list(
    scan_id=scan.id,
    severity=["critical", "high"]
)

for finding in findings:
    print(f"[{finding.severity}] {finding.title}")

# Generate report
report = client.reports.generate(
    scan_id=scan.id,
    format="pdf",
    template="executive"
)

# Download report
report.download("scan-report.pdf")
```

### JavaScript/TypeScript SDK

```typescript
import { ZenClient } from '@zen-ai-pentest/sdk';

const client = new ZenClient({
  baseURL: 'http://localhost:8000',
  token: 'your-api-token'
});

// Create scan
const scan = await client.scans.create({
  name: 'Production Scan',
  target: 'https://example.com',
  scanType: 'web',
  config: {
    tools: ['nmap', 'nuclei'],
    intensity: 'high'
  }
});

// Poll for completion
const result = await scan.waitForCompletion({
  onProgress: (progress) => {
    console.log(`Progress: ${progress.percentage}%`);
  }
});

// Get findings
const findings = await client.findings.list({
  scanId: scan.id,
  severity: ['critical', 'high']
});
```

### cURL Examples

```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Create scan
SCAN_ID=$(curl -s -X POST http://localhost:8000/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test Scan",
    "target": "scanme.nmap.org",
    "scan_type": "network"
  }' | jq -r '.id')

# Get scan status
curl -s http://localhost:8000/scans/$SCAN_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.status'

# Get findings
curl -s http://localhost:8000/scans/$SCAN_ID/findings \
  -H "Authorization: Bearer $TOKEN" | jq '.data[] | {title: .title, severity: .severity}'
```

---

## Best Practices

### 1. Use WebSockets for Real-Time Updates

Instead of polling, use WebSockets for scan progress:

```python
# Good: WebSocket connection
ws = client.websocket.connect(f"/ws/scans/{scan_id}")
for message in ws:
    if message.type == "complete":
        break

# Bad: Polling
while True:
    status = client.scans.get(scan_id).status
    if status == "completed":
        break
    time.sleep(5)
```

### 2. Handle Rate Limits

Implement exponential backoff:

```python
import time
import random

def make_request_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
```

### 3. Validate Inputs

Always validate inputs before sending:

```python
from urllib.parse import urlparse

def validate_target(target):
    parsed = urlparse(target)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid target URL")
    return target
```

### 4. Use Async for Multiple Operations

```python
import asyncio

async def run_multiple_scans(targets):
    tasks = [
        client.scans.create_async(target=t, name=f"Scan {t}")
        for t in targets
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 5. Secure Token Storage

```python
import os
from keyring import get_password, set_password

# Store token securely
set_password("zen-pentest", "api_token", token)

# Retrieve token
token = get_password("zen-pentest", "api_token")
```

---

<p align="center">
  <b>Build secure applications with Zen-AI-Pentest API! 🔒</b><br>
  <sub>For more examples, see <a href="API_EXAMPLES.md">API_EXAMPLES.md</a></sub>
</p>
