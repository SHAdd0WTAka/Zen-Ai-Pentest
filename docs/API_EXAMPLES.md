# API Examples

Comprehensive API examples for Zen AI Pentest using curl, Python, and JavaScript.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Scans](#scans)
3. [Findings](#findings)
4. [Tools](#tools)
5. [Reports](#reports)
6. [Agents](#agents)
7. [System](#system)
8. [WebSocket](#websocket)

---

## Base Configuration

```python
# Python configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "/api/v1"
```

```javascript
// JavaScript configuration
const BASE_URL = 'http://localhost:8000';
const API_VERSION = '/api/v1';
```

---

## Authentication

### Login

**cURL:**
```bash
# Login and store token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"
```

**Python:**
```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={
        "username": "admin",
        "password": "admin123"
    }
)

token = response.json()["access_token"]
print(f"Token: {token}")

# Create headers for subsequent requests
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

**JavaScript:**
```javascript
// Login
async function login(username, password) {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  });
  
  const data = await response.json();
  return data.access_token;
}

// Usage
const token = await login('admin', 'admin123');
console.log('Token:', token);
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

### Register User

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "pentester",
    "email": "pentester@example.com",
    "password": "secure_pass123",
    "full_name": "John Doe"
  }'
```

**Python:**
```python
response = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "username": "pentester",
        "email": "pentester@example.com",
        "password": "secure_pass123",
        "full_name": "John Doe"
    }
)
print(response.json())
```

**JavaScript:**
```javascript
async function register(userData) {
  const response = await fetch(`${BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  });
  return response.json();
}

await register({
  username: 'pentester',
  email: 'pentester@example.com',
  password: 'secure_pass123',
  full_name: 'John Doe'
});
```

---

## Scans

### Create Scan

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_type": "full",
    "name": "Comprehensive Security Scan",
    "description": "Full security assessment",
    "options": {
      "ports": "top1000",
      "aggressive": false,
      "tools": ["nmap", "nuclei", "sqlmap"]
    }
  }'
```

**Python:**
```python
response = requests.post(
    f"{BASE_URL}/api/v1/scans/",
    headers=headers,
    json={
        "target": "example.com",
        "scan_type": "full",
        "name": "Comprehensive Security Scan",
        "description": "Full security assessment",
        "options": {
            "ports": "top1000",
            "aggressive": False,
            "tools": ["nmap", "nuclei", "sqlmap"]
        }
    }
)

scan = response.json()
scan_id = scan["id"]
print(f"Scan created: {scan_id}")
```

**JavaScript:**
```javascript
async function createScan(token, scanData) {
  const response = await fetch(`${BASE_URL}/api/v1/scans/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(scanData)
  });
  return response.json();
}

const scan = await createScan(token, {
  target: 'example.com',
  scan_type: 'full',
  name: 'Comprehensive Security Scan',
  description: 'Full security assessment',
  options: {
    ports: 'top1000',
    aggressive: false,
    tools: ['nmap', 'nuclei', 'sqlmap']
  }
});
```

**Response:**
```json
{
  "id": "scan_abc123",
  "name": "Comprehensive Security Scan",
  "target": "example.com",
  "scan_type": "full",
  "status": "pending",
  "created_at": "2026-01-31T12:00:00Z",
  "created_by": "admin"
}
```

### List Scans

**cURL:**
```bash
# List all scans
curl -X GET "http://localhost:8000/api/v1/scans/?status=completed&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
# List scans with filters
response = requests.get(
    f"{BASE_URL}/api/v1/scans/",
    headers=headers,
    params={
        "status": "completed",
        "limit": 10,
        "skip": 0
    }
)

scans = response.json()
for scan in scans["scans"]:
    print(f"{scan['id']}: {scan['name']} - {scan['status']}")
```

**JavaScript:**
```javascript
async function listScans(token, filters = {}) {
  const queryParams = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}/api/v1/scans/?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}

const scans = await listScans(token, {
  status: 'completed',
  limit: 10
});
```

**Response:**
```json
{
  "scans": [
    {
      "id": "scan_abc123",
      "name": "Comprehensive Security Scan",
      "target": "example.com",
      "status": "completed",
      "progress": 100,
      "findings_count": 15,
      "created_at": "2026-01-31T12:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 10
}
```

### Get Scan Details

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/scans/scan_abc123 \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/scans/{scan_id}",
    headers=headers
)
scan_details = response.json()
print(f"Status: {scan_details['status']}")
print(f"Progress: {scan_details['progress']}%")
```

**JavaScript:**
```javascript
async function getScan(token, scanId) {
  const response = await fetch(`${BASE_URL}/api/v1/scans/${scanId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}

const scanDetails = await getScan(token, 'scan_abc123');
```

### Cancel Scan

**cURL:**
```bash
curl -X PATCH http://localhost:8000/api/v1/scans/scan_abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'
```

**Python:**
```python
response = requests.patch(
    f"{BASE_URL}/api/v1/scans/{scan_id}",
    headers=headers,
    json={"status": "cancelled"}
)
```

---

## Findings

### List Findings

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/findings/?severity=critical&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/findings/",
    headers=headers,
    params={
        "severity": "critical",
        "limit": 50
    }
)

findings = response.json()
for finding in findings["findings"]:
    print(f"[{finding['severity']}] {finding['title']}")
```

**JavaScript:**
```javascript
async function listFindings(token, filters = {}) {
  const queryParams = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}/api/v1/findings/?${queryParams}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}

const findings = await listFindings(token, { severity: 'critical' });
```

**Response:**
```json
{
  "findings": [
    {
      "id": "find_xyz789",
      "scan_id": "scan_abc123",
      "title": "SQL Injection in Login Form",
      "description": "The login form is vulnerable to SQL injection...",
      "severity": "critical",
      "cvss_score": 9.8,
      "status": "open",
      "tool": "sqlmap",
      "target": "https://example.com/login",
      "created_at": "2026-01-31T12:05:00Z"
    }
  ],
  "total": 15
}
```

### Get Findings Summary

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/findings/summary \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/findings/summary",
    headers=headers
)

summary = response.json()
print(f"Total findings: {summary['total']}")
print(f"Critical: {summary['by_severity']['critical']}")
print(f"High: {summary['by_severity']['high']}")
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

### Update Finding

**cURL:**
```bash
curl -X PATCH http://localhost:8000/api/v1/findings/find_xyz789 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "verified",
    "severity": "high",
    "notes": "Confirmed in production environment"
  }'
```

**Python:**
```python
response = requests.patch(
    f"{BASE_URL}/api/v1/findings/{finding_id}",
    headers=headers,
    json={
        "status": "verified",
        "severity": "high",
        "notes": "Confirmed in production environment"
    }
)
```

---

## Tools

### List Available Tools

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/tools/ \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/tools/",
    headers=headers
)

tools = response.json()
for category, tool_list in tools["tools"].items():
    print(f"\n{category.upper()}:")
    for tool in tool_list:
        print(f"  - {tool['name']}: {tool['description']}")
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
    ]
  }
}
```

### Execute Tool

**cURL:**
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

**Python:**
```python
response = requests.post(
    f"{BASE_URL}/api/v1/tools/execute",
    headers=headers,
    json={
        "tool_name": "nmap_scan",
        "target": "scanme.nmap.org",
        "parameters": {
            "ports": "22,80,443",
            "scan_type": "syn"
        },
        "timeout": 300
    }
)

result = response.json()
print(f"Execution ID: {result['execution_id']}")
print(f"Status: {result['status']}")
```

**JavaScript:**
```javascript
async function executeTool(token, toolData) {
  const response = await fetch(`${BASE_URL}/api/v1/tools/execute`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(toolData)
  });
  return response.json();
}

const result = await executeTool(token, {
  tool_name: 'nmap_scan',
  target: 'scanme.nmap.org',
  parameters: {
    ports: '22,80,443',
    scan_type: 'syn'
  },
  timeout: 300
});
```

**Response:**
```json
{
  "execution_id": "exec_def456",
  "tool_name": "nmap_scan",
  "status": "started",
  "message": "Tool execution started",
  "estimated_duration": 60
}
```

---

## Reports

### Generate Report

**cURL:**
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

**Python:**
```python
response = requests.post(
    f"{BASE_URL}/api/v1/reports/",
    headers=headers,
    json={
        "scan_id": "scan_abc123",
        "name": "Q1 Security Assessment",
        "format": "pdf",
        "template": "executive",
        "include_evidence": True
    }
)

report = response.json()
print(f"Report ID: {report['id']}")
print(f"Status: {report['status']}")
```

**Response:**
```json
{
  "id": "rep_ghi789",
  "scan_id": "scan_abc123",
  "name": "Q1 Security Assessment",
  "format": "pdf",
  "template": "executive",
  "status": "pending",
  "created_at": "2026-01-31T14:00:00Z"
}
```

### Download Report

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/reports/rep_ghi789/download \
  -H "Authorization: Bearer $TOKEN" \
  -o "security_report.pdf"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/reports/{report_id}/download",
    headers=headers,
    stream=True
)

with open("security_report.pdf", "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print("Report downloaded successfully")
```

**JavaScript:**
```javascript
async function downloadReport(token, reportId) {
  const response = await fetch(`${BASE_URL}/api/v1/reports/${reportId}/download`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'security_report.pdf';
  document.body.appendChild(a);
  a.click();
  a.remove();
}
```

---

## Agents

### List Agents

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/agents/ \
  -H "Authorization: Bearer $TOKEN"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/agents/",
    headers=headers
)

agents = response.json()
for agent in agents["agents"]:
    print(f"{agent['id']}: {agent['name']} ({agent['status']})")
```

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_recon_001",
      "name": "Reconnaissance Agent",
      "status": "idle",
      "type": "recon",
      "last_active": "2026-01-31T12:00:00Z"
    },
    {
      "id": "agent_vuln_001",
      "name": "Vulnerability Agent",
      "status": "busy",
      "type": "vulnerability",
      "current_task": "scan_abc123"
    }
  ]
}
```

### Assign Task to Agent

**cURL:**
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

**Python:**
```python
response = requests.post(
    f"{BASE_URL}/api/v1/agents/{agent_id}/task",
    headers=headers,
    json={
        "task_type": "recon",
        "parameters": {
            "target": "example.com",
            "depth": "medium"
        },
        "priority": 8
    }
)
```

---

## System

### Health Check

**cURL:**
```bash
curl -X GET http://localhost:8000/health
```

**Python:**
```python
response = requests.get(f"{BASE_URL}/health")
health = response.json()
print(f"Status: {health['status']}")
print(f"Version: {health['version']}")
```

**JavaScript:**
```javascript
async function healthCheck() {
  const response = await fetch(`${BASE_URL}/health`);
  return response.json();
}
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

### System Metrics (Admin)

**cURL:**
```bash
curl -X GET http://localhost:8000/api/v1/system/metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Python:**
```python
response = requests.get(
    f"{BASE_URL}/api/v1/system/metrics",
    headers=headers
)

metrics = response.json()
print(f"CPU: {metrics['cpu_percent']}%")
print(f"Memory: {metrics['memory_percent']}%")
print(f"Active scans: {metrics['active_scans']}")
```

**Response:**
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.5,
  "disk_percent": 34.0,
  "active_scans": 5,
  "queued_scans": 2,
  "active_agents": 8,
  "timestamp": "2026-01-31T12:00:00Z"
}
```

---

## WebSocket

### Real-Time Scan Updates

**JavaScript:**
```javascript
class ScanWebSocket {
  constructor(scanId, token) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/scans/${scanId}?token=${token}`);
    this.setupHandlers();
  }

  setupHandlers() {
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Auto-reconnect
      setTimeout(() => this.reconnect(), 5000);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'status':
        console.log(`Scan status: ${data.status}`);
        break;
      case 'progress':
        console.log(`Progress: ${data.percentage}%`);
        break;
      case 'finding':
        console.log(`New finding: ${data.finding.title}`);
        break;
      case 'log':
        console.log(`Log: ${data.message}`);
        break;
      case 'complete':
        console.log('Scan completed!');
        break;
      case 'error':
        console.error(`Error: ${data.message}`);
        break;
    }
  }

  reconnect() {
    console.log('Reconnecting...');
    this.ws = new WebSocket(this.ws.url);
    this.setupHandlers();
  }

  close() {
    this.ws.close();
  }
}

// Usage
const ws = new ScanWebSocket('scan_abc123', token);
```

### Agent Updates WebSocket

**JavaScript:**
```javascript
class AgentWebSocket {
  constructor(token) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/agents?token=${token}`);
    this.setupHandlers();
  }

  setupHandlers() {
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Agent update:', data);
      
      if (data.type === 'agent_status') {
        console.log(`Agent ${data.agent_id} is now ${data.status}`);
      } else if (data.type === 'task_complete') {
        console.log(`Task completed by agent ${data.agent_id}`);
      }
    };
  }
}

// Usage
const agentWs = new AgentWebSocket(token);
```

### Python WebSocket Client

```python
import asyncio
import websockets
import json

async def scan_websocket(scan_id, token):
    uri = f"ws://localhost:8000/ws/scans/{scan_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data["type"] == "status":
                    print(f"Status: {data['status']}")
                elif data["type"] == "progress":
                    print(f"Progress: {data['percentage']}%")
                elif data["type"] == "complete":
                    print("Scan completed!")
                    break
                    
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

# Run
asyncio.run(scan_websocket("scan_abc123", token))
```

---

## Complete Workflow Example

**Python - Full Scan Workflow:**

```python
import requests
import time

BASE_URL = "http://localhost:8000"

class ZenPentestClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def login(self, username, password):
        """Authenticate and get token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        return self.token
    
    def create_scan(self, target, name, scan_type="full"):
        """Create a new scan"""
        response = requests.post(
            f"{self.base_url}/api/v1/scans/",
            headers=self.headers,
            json={
                "target": target,
                "name": name,
                "scan_type": scan_type,
                "options": {"ports": "top1000"}
            }
        )
        return response.json()
    
    def wait_for_scan(self, scan_id, timeout=3600):
        """Poll scan status until complete"""
        start = time.time()
        while time.time() - start < timeout:
            response = requests.get(
                f"{self.base_url}/api/v1/scans/{scan_id}",
                headers=self.headers
            )
            scan = response.json()
            
            if scan["status"] in ["completed", "failed", "cancelled"]:
                return scan
            
            print(f"Status: {scan['status']}, Progress: {scan.get('progress', 0)}%")
            time.sleep(5)
        
        raise TimeoutError("Scan did not complete within timeout")
    
    def get_findings(self, scan_id):
        """Get findings for a scan"""
        response = requests.get(
            f"{self.base_url}/api/v1/findings/",
            headers=self.headers,
            params={"scan_id": scan_id}
        )
        return response.json()
    
    def generate_report(self, scan_id, format="pdf"):
        """Generate and download report"""
        # Create report
        response = requests.post(
            f"{self.base_url}/api/v1/reports/",
            headers=self.headers,
            json={
                "scan_id": scan_id,
                "format": format,
                "template": "executive"
            }
        )
        report = response.json()
        
        # Wait for report generation
        while True:
            response = requests.get(
                f"{self.base_url}/api/v1/reports/{report['id']}",
                headers=self.headers
            )
            r = response.json()
            if r["status"] == "completed":
                break
            time.sleep(2)
        
        # Download report
        response = requests.get(
            f"{self.base_url}/api/v1/reports/{report['id']}/download",
            headers=self.headers,
            stream=True
        )
        
        filename = f"report_{scan_id}.{format}"
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filename

# Usage
client = ZenPentestClient("http://localhost:8000")
client.login("admin", "admin123")

# Create and run scan
scan = client.create_scan("example.com", "Security Assessment")
print(f"Created scan: {scan['id']}")

# Wait for completion
result = client.wait_for_scan(scan['id'])
print(f"Scan completed with status: {result['status']}")

# Get findings
findings = client.get_findings(scan['id'])
print(f"Found {findings['total']} findings")
for f in findings['findings'][:5]:
    print(f"  [{f['severity']}] {f['title']}")

# Generate report
report_file = client.generate_report(scan['id'])
print(f"Report saved to: {report_file}")
```

---

<p align="center">
  <b>For more details, see <a href="API.md">API.md</a></b><br>
  <sub>For support, see <a href="../SUPPORT.md">SUPPORT.md</a></sub>
</p>
