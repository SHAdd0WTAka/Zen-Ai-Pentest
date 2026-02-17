# Zen-AI-Pentest API Reference

Complete API reference for the authentication and agent communication systems.

## Base URL

```
Production: https://api.zen-pentest.local
Development: http://localhost:8000
```

## Authentication

All API endpoints (except login/register) require authentication via Bearer token.

```http
Authorization: Bearer <access_token>
```

## Endpoints

### Authentication

#### POST `/auth/login`
Authenticate user and get access token.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "username": "admin",
  "role": "admin"
}
```

#### POST `/auth/refresh`
Refresh access token using refresh token.

**Headers:**
```http
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### POST `/auth/logout`
Revoke current session.

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

#### POST `/auth/logout-all`
Revoke all user sessions.

**Response:**
```json
{
  "message": "Logged out from 3 device(s)"
}
```

#### GET `/auth/me`
Get current user info.

**Response:**
```json
{
  "sub": "admin",
  "roles": ["admin"],
  "permissions": [],
  "session_id": "..."
}
```

---

### Agent Management v2

#### POST `/api/v2/agents/register`
Register a new agent. Requires `agent:register` permission.

**Request:**
```json
{
  "name": "research-agent-1",
  "role": "researcher",
  "description": "Network reconnaissance agent",
  "expires_days": 90,
  "rate_limit": 1000
}
```

**Response:**
```json
{
  "agent_id": "agt_abc123def456",
  "api_key": "zen_xyz789uvw123",
  "api_secret": "sec_abc123xyz789",
  "role": "researcher",
  "permissions": [
    "message:send",
    "message:receive",
    "task:create",
    "task:execute"
  ],
  "created_at": "2026-02-17T16:30:00Z",
  "expires_at": "2026-05-18T16:30:00Z",
  "warning": "Store the api_secret securely - it will not be shown again!"
}
```

**Roles:**
- `researcher` - Information gathering
- `analyst` - Data analysis
- `exploit` - Exploit development
- `scanner` - Vulnerability scanning
- `reporter` - Report generation
- `coordinator` - Multi-agent coordination
- `admin` - Full access

#### POST `/api/v2/agents/{agent_id}/revoke`
Revoke agent credentials. Requires `agent:unregister` permission.

**Request:**
```json
{
  "reason": "security_breach"
}
```

**Response:**
```json
{
  "message": "Agent agt_abc123def456 revoked successfully",
  "reason": "security_breach"
}
```

#### POST `/api/v2/agents/{agent_id}/rotate`
Rotate agent API key. Requires `agent:register` permission.

**Response:**
```json
{
  "agent_id": "agt_abc123def456",
  "api_key": "zen_new789uvw456",
  "api_secret": "sec_new456abc789",
  "role": "researcher",
  "expires_at": "2026-05-18T16:30:00Z",
  "warning": "Store the api_secret securely - it will not be shown again!"
}
```

#### GET `/api/v2/agents`
List active agents. Requires `agent:list` permission.

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "agt_abc123def456",
      "role": "researcher",
      "permissions": ["message:send", "task:create"],
      "is_active": true,
      "last_seen": "2026-02-17T16:30:00Z"
    }
  ],
  "count": 1
}
```

#### GET `/api/v2/agents/{agent_id}`
Get agent details. Requires `agent:list` permission.

**Response:**
```json
{
  "agent_id": "agt_abc123def456",
  "role": "researcher",
  "permissions": ["message:send", "task:create"],
  "is_active": true,
  "last_seen": "2026-02-17T16:30:00Z"
}
```

---

### WebSocket Agent Communication

#### WS `/agents/stream`
Real-time agent communication endpoint.

**Protocol:**

1. **Connect** to WebSocket
2. **Authenticate** within 10 seconds:
```json
{
  "type": "auth",
  "api_key": "zen_xyz789uvw123",
  "api_secret": "sec_abc123xyz789"
}
```

3. **Receive auth success**:
```json
{
  "type": "auth_success",
  "agent_id": "agt_abc123def456",
  "role": "researcher",
  "permissions": ["message:send", "task:create"]
}
```

4. **Send message**:
```json
{
  "type": "message",
  "recipient": "agt_target789",  // or "broadcast"
  "payload": {
    "task": "scan",
    "target": "example.com",
    "options": {...}
  }
}
```

5. **Receive acknowledgment**:
```json
{
  "type": "ack",
  "message_id": "msg_123",
  "status": "delivered",
  "timestamp": "2026-02-17T16:30:00Z"
}
```

6. **Receive message**:
```json
{
  "type": "message",
  "sender": "agt_source456",
  "payload": {
    "result": "scan_complete",
    "findings": [...]
  }
}
```

7. **Send heartbeat** (every 30s):
```json
{
  "type": "heartbeat",
  "timestamp": "2026-02-17T16:30:00Z"
}
```

---

### Scans

#### POST `/scans`
Create a new scan.

**Request:**
```json
{
  "name": "Network Scan - DMZ",
  "target": "192.168.1.0/24",
  "scan_type": "network",
  "config": {
    "ports": "1-65535",
    "threads": 100
  }
}
```

**Headers:**
```http
X-CSRF-Token: <csrf_token>
```

**Response:**
```json
{
  "id": 1,
  "name": "Network Scan - DMZ",
  "target": "192.168.1.0/24",
  "scan_type": "network",
  "status": "pending",
  "config": {"ports": "1-65535", "threads": 100},
  "user_id": "admin",
  "created_at": "2026-02-17T16:30:00Z"
}
```

#### GET `/scans`
List scans.

**Query Parameters:**
- `skip`: Offset (default: 0)
- `limit`: Max results (default: 100)
- `status`: Filter by status (pending, running, completed, failed)

**Response:**
```json
{
  "scans": [...],
  "total": 50
}
```

#### GET `/scans/{scan_id}`
Get scan details.

#### DELETE `/scans/{scan_id}`
Delete a scan.

---

### Findings

#### GET `/scans/{scan_id}/findings`
Get findings for a scan.

**Query Parameters:**
- `severity`: Filter by severity (critical, high, medium, low, info)

#### POST `/scans/{scan_id}/findings`
Add finding to scan.

**Request:**
```json
{
  "title": "SQL Injection",
  "description": "UNION-based SQL injection in search parameter",
  "severity": "critical",
  "cvss_score": 9.8,
  "evidence": "...",
  "remediation": "Use parameterized queries"
}
```

---

### Reports

#### POST `/reports`
Generate report.

**Request:**
```json
{
  "scan_id": 1,
  "format": "pdf",
  "template": "executive"
}
```

#### GET `/reports`
List reports.

#### GET `/reports/{report_id}/download`
Download report file.

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Permission denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5 requests/minute |
| `/auth/*` | 20 requests/minute |
| `/api/v2/agents/*` | 100 requests/minute |
| `/scans` | 100 requests/minute |
| `/agents/stream` | 1000 messages/minute |

---

## SDK Examples

### Python

```python
import requests

# Login
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
tokens = response.json()
access_token = tokens["access_token"]

# Create scan
response = requests.post(
    "http://localhost:8000/scans",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "name": "Test Scan",
        "target": "scanme.nmap.org",
        "scan_type": "network"
    }
)
scan = response.json()
print(f"Scan created: {scan['id']}")
```

### Agent Client

```python
from agents.v2 import AgentClient

agent = AgentClient(
    agent_id="agt_xxx",
    api_key="zen_xxx",
    api_secret="sec_xxx"
)

await agent.connect()

# Send message
await agent.send_message(
    recipient="agt_target",
    payload={"task": "scan", "target": "example.com"}
)

# Receive messages
async for msg in agent.receive_messages():
    print(f"Received: {msg.payload}")
```

---

## Security

- All requests must use HTTPS in production
- Tokens expire after 15 minutes (access) or 7 days (refresh)
- API keys should be rotated every 90 days
- Messages between agents are end-to-end encrypted
- All authentication events are logged for audit

---

## Changelog

### v2.0.0
- Added Agent Communication v2 with end-to-end encryption
- Added API key authentication for agents
- Added WebSocket real-time messaging
- Added message queue with delivery guarantees
