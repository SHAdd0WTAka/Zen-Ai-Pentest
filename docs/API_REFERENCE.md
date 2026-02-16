# API Reference Documentation

**Project**: Zen-AI-Pentest  
**Version**: 2.3.9  
**Last Updated**: 2026-02-16

---

## Overview

Zen-AI-Pentest provides a comprehensive REST API for programmatic access to all penetration testing capabilities. This document serves as the **official reference documentation** for all external interfaces.

## Interactive API Documentation

### Swagger UI (OpenAPI)
When the API server is running, interactive documentation is available at:

```
http://localhost:8000/docs
```

This provides:
- ✅ Interactive endpoint testing
- ✅ Request/response schemas
- ✅ Authentication handling
- ✅ Auto-generated from code

### ReDoc (Alternative)
```
http://localhost:8000/redoc
```

---

## Base URLs

| Environment | URL | Protocol |
|-------------|-----|----------|
| Development | `http://localhost:8000` | HTTP |
| Docker | `http://localhost:8000` | HTTP |
| Production | `https://api.zen-pentest.local` | HTTPS |

---

## Authentication Interface

### Login Endpoint

**URL**: `POST /auth/login`

**Input:**
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Output (Success - 200):**
```json
{
  "access_token": "string (JWT)",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Output (Error - 401):**
```json
{
  "detail": "Invalid credentials"
}
```

### Using Authentication

All protected endpoints require the Authorization header:

```http
Authorization: Bearer <access_token>
```

---

## Core API Endpoints

### Health Check

**Purpose**: Check API availability

**URL**: `GET /health`

**Input**: None

**Output (200):**
```json
{
  "status": "healthy",
  "version": "2.3.9",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

---

### Scans Management

#### Create Scan

**URL**: `POST /api/v1/scans`

**Input:**
```json
{
  "target": "string (required, domain/IP)",
  "scan_type": "string (enum: quick, full, stealth)",
  "ports": [80, 443],
  "templates": ["string"],
  "timeout": 300,
  "concurrent": 5
}
```

**Output (201):**
```json
{
  "id": "uuid",
  "target": "example.com",
  "status": "pending",
  "created_at": "2026-02-16T12:00:00Z"
}
```

#### Get Scan Status

**URL**: `GET /api/v1/scans/{scan_id}`

**Input**: Path parameter `scan_id` (uuid)

**Output (200):**
```json
{
  "id": "uuid",
  "target": "example.com",
  "status": "running",
  "progress": 45,
  "findings_count": 3,
  "started_at": "2026-02-16T12:00:00Z",
  "estimated_completion": "2026-02-16T12:05:00Z"
}
```

#### List Scans

**URL**: `GET /api/v1/scans`

**Query Parameters**:
- `status` (optional): Filter by status
- `limit` (optional): Max results (default: 50)
- `offset` (optional): Pagination offset

**Output (200):**
```json
{
  "items": [...],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

---

### Findings Management

#### List Findings

**URL**: `GET /api/v1/findings`

**Query Parameters**:
- `severity` (optional): critical, high, medium, low, info
- `scan_id` (optional): Filter by scan
- `confirmed` (optional): boolean

**Output (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "SQL Injection",
      "severity": "critical",
      "description": "...",
      "remediation": "...",
      "cvss_score": 9.8,
      "confirmed": false,
      "created_at": "2026-02-16T12:00:00Z"
    }
  ],
  "total": 25
}
```

#### Get Finding Details

**URL**: `GET /api/v1/findings/{finding_id}`

**Output (200):** Full finding object with evidence

---

### Agent Management

#### List Agents

**URL**: `GET /api/v1/agents`

**Output (200):**
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "react-agent",
      "status": "idle",
      "capabilities": ["scan", "analyze"]
    }
  ]
}
```

#### Execute Agent

**URL**: `POST /api/v1/agents/{agent_id}/execute`

**Input:**
```json
{
  "task": "string",
  "parameters": {},
  "priority": "normal"
}
```

**Output (202):** Accepted, returns task ID

---

### WebSocket Interface

Real-time updates via WebSocket:

**URL**: `ws://localhost:8000/ws`

**Authentication**: Token via query parameter
```
ws://localhost:8000/ws?token=<access_token>
```

**Events**:
- `scan.update` - Scan progress updates
- `finding.new` - New finding discovered
- `agent.status` - Agent status changes

**Message Format:**
```json
{
  "event": "scan.update",
  "data": {
    "scan_id": "uuid",
    "progress": 75,
    "status": "running"
  }
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 422 | Validation Error | Input validation failed |
| 500 | Server Error | Internal server error |

---

## Rate Limiting

**Default Limits**:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

**Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645012800
```

---

## CLI Interface Reference

### Command Structure

```bash
zen-ai-pentest [command] [options]
```

### Available Commands

#### Scan Command
```bash
zen-ai-pentest scan [options]
```

**Options**:
- `--target, -t`: Target URL/IP (required)
- `--type, -T`: Scan type (quick|full|stealth)
- `--ports, -p`: Port range (e.g., 80,443,8080)
- `--output, -o`: Output format (json|html|pdf)
- `--verbose, -v`: Verbose output

**Example:**
```bash
zen-ai-pentest scan -t example.com -T full -p 80,443 -o json
```

#### Agent Command
```bash
zen-ai-pentest agent [subcommand]
```

**Subcommands**:
- `list`: List available agents
- `run <agent-id>`: Run specific agent
- `status`: Show agent status

---

## Python SDK Interface

### Installation

```bash
pip install zen-ai-pentest
```

### Usage

```python
from zen_ai_pentest import Client

# Initialize client
client = Client(
    base_url="http://localhost:8000",
    token="your-api-token"
)

# Create scan
scan = client.scans.create(
    target="example.com",
    scan_type="full"
)

# Wait for completion
scan.wait_for_completion()

# Get findings
findings = scan.get_findings()
for finding in findings:
    print(f"{finding.severity}: {finding.title}")
```

---

## Data Models

### Scan Model

```python
class Scan:
    id: UUID
    target: str
    status: ScanStatus
    scan_type: ScanType
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    findings_count: int
```

### Finding Model

```python
class Finding:
    id: UUID
    scan_id: UUID
    title: str
    description: str
    severity: Severity
    cvss_score: float
    evidence: dict
    remediation: str
    confirmed: bool
    created_at: datetime
```

---

## Additional Resources

- **Full API Guide**: [API.md](API.md)
- **Examples**: [API_EXAMPLES.md](API_EXAMPLES.md)
- **Postman Collection**: Available at `/docs/postman_collection.json`
- **OpenAPI Schema**: Available at `/openapi.json`

---

## Document Information

- **Type**: Reference Documentation
- **Audience**: Developers, API Users
- **Maintenance**: Auto-generated + Manual updates
- **Last Review**: 2026-02-16

---

*This document satisfies the OpenSSF Best Practices criterion [documentation_interface] by providing comprehensive reference documentation for all external interfaces.*
