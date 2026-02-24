# System Architecture

Überblick über die Zen-AI-Pentest Architektur.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Web UI    │  │    CLI      │  │      Mobile App         │ │
│  │  (React)    │  │  (Python)   │  │      (Future)           │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘ │
└─────────┼────────────────┼───────────────────────────────────────┘
          │                │
          └────────┬───────┘
                   │ HTTPS/WSS
┌──────────────────┴──────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │   REST API  │  │  WebSocket  │  │   JWT/RBAC Auth │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Agent Orchestrator                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Workflow │ │   Task   │ │   Risk   │ │  State   │   │   │
│  │  │  Engine  │ │  Queue   │ │  Engine  │ │ Machine  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      AGENT LAYER                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Recon   │ │ Exploit  │ │ Analysis │ │  Report  │           │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Social  │ │  RedTeam │ │   Cloud  │ │   ICS    │           │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      TOOLS LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Tool Executor                            │   │
│  │       (Docker Sandbox / Local Execution)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │  Nmap  │ │ Nuclei │ │ SQLMap │ │  FFuF  │ │  Nikto │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Subfinder│ │ HTTPX  │ │ WAFW00F│ │ WhatWeb│ │  Hydra │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ PostgreSQL  │  │    Redis    │  │    File Storage         │  │
│  │  (Scans)    │  │  (Cache)    │  │    (Reports/Logs)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Komponenten Details

### 1. API Gateway

**FastAPI Server**
- Async Request Handling
- Automatic OpenAPI Documentation
- JWT Authentication
- Rate Limiting
- CORS Support

**WebSocket**
- Real-time Scan Updates
- Agent Communication
- Live Progress Streaming

### 2. Orchestrator

**Workflow Engine**
```python
class WorkflowEngine:
    def create_dag(self, phases: list) -> DAG:
        """Create execution graph."""

    def execute(self, dag: DAG) -> Results:
        """Execute workflow phases."""
```

**Task Queue (Celery + Redis)**
- Async Task Processing
- Retry Logic
- Priority Queues
- Result Backend

**Risk Engine**
- CVSS Scoring
- EPSS Integration
- False Positive Detection
- Business Impact Analysis

### 3. Agent System

**Base Agent**
```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, task: Task) -> Result:
        pass

    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        pass
```

**ReAct Pattern**
```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Thought │───▶│  Action │───▶│Observation│──▶│ Reflect │
└─────────┘    └─────────┘    └─────────┘    └────┬────┘
     ▲                                            │
     └────────────────────────────────────────────┘
```

### 4. Tool Integration

**Tool Interface**
```python
class BaseTool(ABC):
    name: str
    description: str
    safety_level: SafetyLevel

    @abstractmethod
    async def run(self, target: str, options: dict) -> Result:
        pass
```

**Docker Sandbox**
- Isolated Execution
- Resource Limits
- Network Isolation
- Read-Only Filesystem

### 5. Data Layer

**PostgreSQL Schema**
```sql
-- Scans Table
CREATE TABLE scans (
    id UUID PRIMARY KEY,
    target VARCHAR(255) NOT NULL,
    status scan_status DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    results JSONB
);

-- Agents Table
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    type agent_type NOT NULL,
    status agent_status DEFAULT 'idle',
    current_task UUID REFERENCES tasks(id)
);
```

**Redis Usage**
- Session Storage
- Rate Limiting
- Task Queue
- Cache Layer

## Data Flow

### 1. Scan Initiation

```
1. Client → POST /api/v1/scans
2. API → Validate Request
3. API → Create Scan Record (DB)
4. Orchestrator → Create Workflow
5. Task Queue → Distribute Tasks
6. Agents → Execute Tasks
7. Results → Store in DB
8. WebSocket → Notify Client
```

### 2. Agent Communication

```
1. Agent → Request Task (Redis)
2. Orchestrator → Assign Task
3. Agent → Execute (Docker)
4. Agent → Report Progress (WebSocket)
5. Agent → Submit Results (API)
6. Orchestrator → Update State
```

## Security Architecture

### Authentication Flow

```
┌────────┐         ┌────────┐         ┌────────┐
│ Client │────────▶│  API   │────────▶│  Auth  │
└────────┘         └────────┘         └────┬───┘
     │                    │                │
     │◀──── JWT Token ────┤◀───────────────┤
     │                    │                │
     │──── API Call + JWT──────────────────▶│
     │                    │                │
     │◀──── Response ─────┘                │
```

### Safety Controls

```
┌─────────────────────────────────────────┐
│           Safety Pipeline                │
├─────────────────────────────────────────┤
│ 1. Input Validation                     │
│    └─> Schema validation (Pydantic)    │
│                                         │
│ 2. Private IP Blocking                  │
│    └─> 10.0.0.0/8, 172.16.0.0/12       │
│       192.168.0.0/16, 127.0.0.0/8      │
│                                         │
│ 3. Risk Assessment                      │
│    └─> Level 0-3 Classification        │
│                                         │
│ 4. Execution Sandbox                    │
│    └─> Docker Container                │
│                                         │
│ 5. Output Sanitization                  │
│    └─> Remove sensitive data           │
└─────────────────────────────────────────┘
```

## Scalability

### Horizontal Scaling

```
┌─────────────┐
│   Load      │
│  Balancer   │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──┴──┐ ┌──┴──┐
│ API │ │ API │  ◀── Multiple API instances
│ #1  │ │ #2  │
└──┬──┘ └──┬──┘
   │       │
   └───┬───┘
       │
┌──────┴──────┐
│    Redis    │  ◀── Shared state
│   Cluster   │
└─────────────┘
```

### Worker Scaling

```yaml
# docker-compose.scale.yml
worker:
  deploy:
    replicas: 5
    resources:
      limits:
        cpus: '1'
        memory: 2G
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript |
| API | FastAPI, Python 3.12 |
| Agents | Python, AsyncIO |
| Queue | Celery, Redis |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Containers | Docker |
| Orchestration | Kubernetes (optional) |
| AI Models | Kimi, OpenAI, Anthropic |

## Deployment Patterns

### Development
```
Single Container
├─ API
├─ PostgreSQL
├─ Redis
└─ All Tools
```

### Production
```
Microservices
├─ API (x3 replicas)
├─ Worker (x5 replicas)
├─ PostgreSQL (managed)
├─ Redis (cluster)
└─ Tool Sandboxes (on-demand)
```

## Monitoring

### Metrics
- API Response Time
- Queue Length
- Agent Utilization
- Tool Execution Time
- Error Rate

### Logging
```python
{
    "timestamp": "2026-02-24T10:00:00Z",
    "level": "INFO",
    "component": "agent.recon",
    "scan_id": "uuid",
    "message": "Port scan completed",
    "metadata": {
        "target": "example.com",
        "ports_found": 3,
        "duration": 5.2
    }
}
```

## Future Architecture

### Planned Enhancements

1. **Event Sourcing**
   - Audit Trail
   - Replay Capability

2. **CQRS**
   - Separate Read/Write Models
   - Optimized Queries

3. **ML Pipeline**
   - Automated Vulnerability Classification
   - False Positive Prediction

4. **Federated Learning**
   - Cross-Organization Model Training
   - Privacy Preserving
