# Zen-AI-Pentest API Guide

## Quick Start

```bash
# Start the server
python -m uvicorn api.main:app --reload

# API is available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

## Authentication

All API endpoints (except health checks) require authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/orchestrator/tasks
```

## Core Endpoints

### 1. Orchestrator API

#### Submit Task

```http
POST /api/v1/orchestrator/tasks
Content-Type: application/json

{
  "type": "vulnerability_scan",
  "target": "example.com",
  "options": {
    "ports": "80,443",
    "scan_type": "quick"
  },
  "priority": "high"
}
```

**Response:**
```json
{
  "task_id": "task-abc123",
  "status": "submitted",
  "submitted_at": "2024-01-15T10:30:00Z"
}
```

#### Get Task Status

```http
GET /api/v1/orchestrator/tasks/{task_id}
```

**Response:**
```json
{
  "id": "task-abc123",
  "type": "vulnerability_scan",
  "state": "running",
  "priority": "high",
  "progress": 45.5,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z"
}
```

#### List Tasks

```http
GET /api/v1/orchestrator/tasks?status=running&limit=100
```

### 2. Scheduler API

#### Schedule Job

```http
POST /api/v1/scheduler/jobs
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
  "max_retries": 3
}
```

**Response:**
```json
{
  "job_id": "job-xyz789",
  "status": "scheduled",
  "scheduled_at": "2024-01-15T10:30:00Z"
}
```

#### Schedule with Interval

```http
POST /api/v1/scheduler/jobs
Content-Type: application/json

{
  "name": "Subdomain Monitor",
  "task_type": "subdomain_enum",
  "task_data": {"domain": "example.com"},
  "interval": 240
}
```

#### List Jobs

```http
GET /api/v1/scheduler/jobs?enabled_only=true
```

#### Pause/Resume Job

```http
POST /api/v1/scheduler/jobs/{job_id}/pause
POST /api/v1/scheduler/jobs/{job_id}/resume
```

### 3. Dashboard API

#### Get Dashboard Data

```http
GET /api/v1/dashboard/data
```

**Response:**
```json
{
  "system_status": {
    "status": "healthy",
    "dashboard": "running",
    "websocket": "running"
  },
  "current_metrics": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "tasks_running": 5
  },
  "recent_events": [...]
}
```

#### Get Recent Events

```http
GET /api/v1/dashboard/events/recent?limit=50&event_type=task.progress
```

#### Send Notification

```http
POST /api/v1/dashboard/notify?title=Scan%20Complete&message=All%20tasks%20finished&level=success
```

### 4. Audit API

#### Query Audit Logs

```http
GET /api/v1/audit/logs?start_time=2024-01-01T00:00:00Z&level=error&limit=100
```

**Response:**
```json
{
  "logs": [
    {
      "id": "log-123",
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "error",
      "category": "security",
      "event_type": "failed_login",
      "message": "Failed login attempt",
      "user_id": "user@example.com",
      "ip_address": "192.168.1.1"
    }
  ]
}
```

#### Verify Log Integrity

```http
GET /api/v1/audit/integrity
```

**Response:**
```json
{
  "total_entries": 1500,
  "valid_signatures": 1500,
  "invalid_signatures": 0,
  "chain_breaks": 0,
  "is_valid": true
}
```

#### Generate Compliance Report

```http
POST /api/v1/audit/compliance/report
Content-Type: application/json

{
  "standard": "iso27001",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "format": "json"
}
```

### 5. Analysis API

#### Analyze Results

```http
POST /api/v1/analysis
Content-Type: application/json

{
  "vulnerabilities": [
    {
      "id": "CVE-2024-1234",
      "title": "SQL Injection",
      "severity": "high"
    }
  ],
  "config": {
    "risk_threshold": 7.0,
    "include_remediation": true
  }
}
```

**Response:**
```json
{
  "analysis_id": "analysis-456",
  "risk_score": 8.5,
  "findings": [...],
  "recommendations": [...]
}
```

## WebSocket API

### Connect to Dashboard

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/dashboard/ws?token=YOUR_TOKEN');

ws.onopen = () => {
  // Subscribe to events
  ws.send(JSON.stringify({
    action: 'subscribe',
    event_types: ['task.progress', 'system.metrics', 'security.alert']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Event Types

| Event Type | Description | Priority |
|------------|-------------|----------|
| `task.progress` | Task progress update | 3 |
| `task.completed` | Task completion | 3 |
| `system.metrics` | System metrics | 2 |
| `security.alert` | Security alert | 5 |
| `schedule.triggered` | Scheduled job triggered | 3 |

### WebSocket Actions

```javascript
// Subscribe to events
{
  "action": "subscribe",
  "event_types": ["task.progress", "system.metrics"]
}

// Set minimum priority filter
{
  "action": "set_priority",
  "min_priority": 3
}

// Ping/Pong
{
  "action": "ping"
}
```

## Health Check Endpoints

### Basic Health

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "orchestrator": {"healthy": true},
    "scheduler": {"healthy": true},
    "dashboard": {"healthy": true}
  }
}
```

### Kubernetes Probes

```http
GET /ready    # Readiness probe
GET /live     # Liveness probe
```

## Common Patterns

### 1. Submit and Monitor Task

```python
import requests
import time

# Submit task
response = requests.post(
    'http://localhost:8000/api/v1/orchestrator/tasks',
    json={
        'type': 'vulnerability_scan',
        'target': 'example.com',
        'priority': 'high'
    },
    headers={'Authorization': 'Bearer TOKEN'}
)
task_id = response.json()['task_id']

# Poll for completion
while True:
    status = requests.get(
        f'http://localhost:8000/api/v1/orchestrator/tasks/{task_id}'
    ).json()
    
    if status['state'] in ['completed', 'failed']:
        break
    
    print(f"Progress: {status.get('progress', 0)}%")
    time.sleep(5)

# Get results
results = requests.get(
    f'http://localhost:8000/api/v1/orchestrator/tasks/{task_id}/results'
).json()
```

### 2. Schedule Recurring Job

```python
import requests

# Schedule daily scan
response = requests.post(
    'http://localhost:8000/api/v1/scheduler/jobs',
    json={
        'name': 'Daily Production Scan',
        'task_type': 'vulnerability_scan',
        'task_data': {
            'target': 'production.example.com',
            'options': {'deep_scan': True}
        },
        'cron': '0 2 * * *',  # Daily at 2 AM
        'timezone': 'UTC'
    }
)

job_id = response.json()['job_id']
print(f"Job scheduled: {job_id}")
```

### 3. Query Audit Logs

```python
import requests
from datetime import datetime, timedelta

# Get logs from last 24 hours
start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()

response = requests.get(
    'http://localhost:8000/api/v1/audit/logs',
    params={
        'start_time': start_time,
        'level': 'error',
        'limit': 100
    }
)

logs = response.json()['logs']
for log in logs:
    print(f"[{log['timestamp']}] {log['level']}: {log['message']}")
```

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

API endpoints are rate-limited:

- **Authenticated**: 1000 requests/hour
- **Unauthenticated**: 100 requests/hour

Headers returned:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705315800
```

## SDK Examples

### Python SDK

```python
from zen_aipentest import Client

client = Client(
    base_url="http://localhost:8000",
    token="YOUR_TOKEN"
)

# Submit task
task = client.tasks.submit(
    type="vulnerability_scan",
    target="example.com",
    priority="high"
)

# Wait for completion
result = task.wait_for_completion(timeout=3600)
print(result.findings)
```

### cURL Examples

```bash
# Submit task
curl -X POST http://localhost:8000/api/v1/orchestrator/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "type": "vulnerability_scan",
    "target": "example.com",
    "priority": "high"
  }'

# Get status
curl http://localhost:8000/api/v1/orchestrator/tasks/task-abc123 \
  -H "Authorization: Bearer TOKEN"

# Export audit logs
curl http://localhost:8000/api/v1/audit/logs/export \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"format": "csv", "start_time": "2024-01-01T00:00:00Z"}' \
  --output audit_logs.csv
```

## Best Practices

1. **Use WebSockets** for real-time updates instead of polling
2. **Set appropriate priorities** for tasks (critical/high/normal/low)
3. **Handle rate limits** with exponential backoff
4. **Validate inputs** before submission
5. **Monitor task progress** via events or polling
6. **Export audit logs** regularly for compliance
