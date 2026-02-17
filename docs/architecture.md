# Zen-AI-Pentest Architecture

## Overview

Zen-AI-Pentest is a modular, autonomous penetration testing framework built with Python and FastAPI. The architecture follows clean design principles with clear separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Web UI    │  │    CLI      │  │   Third-party Tools     │ │
│  │  (React)    │  │  (Python)   │  │   (Burp, Metasploit)    │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          └────────────────┴─────────────────────┘
                           │
                    HTTP / WebSocket
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                      API LAYER                                 │
│                    FastAPI Application                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │   REST API  │ │ WebSocket   │ │   Authentication        │  │
│  │  Endpoints  │ │   Server    │ │   (JWT/OAuth2)          │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                   CORE LAYER                                   │
│                                                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │  ZenOrchestrator│  │  Task Scheduler │  │   Dashboard    │ │
│  │   (3,441 LOC)   │  │   (2,218 LOC)   │  │   (1,829 LOC)  │ │
│  │                 │  │                 │  │                │ │
│  │ • Task Mgmt     │  │ • Cron Jobs     │  │ • Real-time    │ │
│  │ • Event Bus     │  │ • Recurring     │  │ • WebSocket    │ │
│  │ • State Mgmt    │  │ • Job Queue     │  │ • Metrics      │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────┘ │
│           │                    │                    │          │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼───────┐ │
│  │   Audit Logger  │  │  Secure Validator│  │   Analysis Bot │ │
│  │   (2,677 LOC)   │  │    (550 LOC)     │  │   (4,281 LOC)  │ │
│  │                 │  │                  │  │                │ │
│  │ • ISO 27001     │  │ • Input Valid.   │  │ • AI Analysis  │ │
│  │ • SIEM Integr.  │  │ • SSRF Prevent.  │  │ • Risk Scoring │ │
│  │ • Compliance    │  │ • SQL Injection  │  │ • Exploit Check│ │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Performance & Integration                    │ │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────────┐  │ │
│  │  │   Cache    │ │   Pools    │ │   App Factory        │  │ │
│  │  │  Manager   │ │  (Conn.)   │ │   (1,126 LOC)        │  │ │
│  │  └────────────┘ └────────────┘ └──────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. ZenOrchestrator (Core)

The central coordination hub that manages all system components.

**Responsibilities:**
- Task lifecycle management (submit, execute, monitor)
- Event propagation via EventBus
- State management across components
- Integration with Analysis Bot and Audit Logger

**Key Classes:**
- `ZenOrchestrator` - Main coordinator
- `StateManager` - Distributed state management
- `EventBus` - Async event publishing/subscribing
- `TaskManager` - Task execution with worker pools

### 2. Analysis Bot

AI-powered vulnerability analysis system.

**Responsibilities:**
- Vulnerability analysis and scoring
- Exploitability assessment
- Risk evaluation
- Remediation recommendations

**Key Components:**
- `VulnerabilityAnalyzer` - Identifies and classifies vulnerabilities
- `RiskScorer` - Calculates risk scores (CVSS, EPSS)
- `ExploitabilityChecker` - Determines exploit feasibility
- `RecommendationEngine` - Generates fix recommendations

### 3. Audit Logger

ISO 27001 compliant audit logging system.

**Responsibilities:**
- Tamper-proof log entries
- Chain of custody for logs
- SIEM integration (Splunk, ELK, QRadar)
- Compliance reporting (ISO 27001, GDPR, PCI DSS)

**Key Features:**
- Cryptographic signatures
- Automatic log integrity verification
- Multiple export formats (JSON, CSV, Syslog)

### 4. Secure Validator

Input validation and security hardening.

**Responsibilities:**
- URL validation (SSRF prevention)
- Command injection prevention
- SQL injection prevention
- XSS prevention
- Path traversal prevention

**Impact:** Reduces CVSS 7.5 vulnerabilities to CVSS 2.0

### 5. Task Scheduler

Job scheduling system for recurring tasks.

**Responsibilities:**
- Cron expression parsing
- Interval-based scheduling
- Job persistence
- Missed job recovery

**Presets:**
- `daily_vulnerability_scan()` - Daily at 2 AM
- `weekly_deep_scan()` - Weekly comprehensive scan
- `subdomain_monitoring()` - Every 4 hours

### 6. Live Dashboard

Real-time monitoring and visualization.

**Responsibilities:**
- WebSocket event streaming
- System metrics collection
- Live task progress tracking
- Security alert notifications

## Data Flow

### Task Execution Flow

```
1. Client submits task via API
        ↓
2. Secure Validator checks input
        ↓
3. ZenOrchestrator queues task
        ↓
4. TaskManager assigns to worker
        ↓
5. Audit Logger records execution
        ↓
6. Dashboard broadcasts progress
        ↓
7. Results stored / Analysis Bot processes
        ↓
8. Client receives completion event
```

### Scheduled Job Flow

```
1. Job scheduled via Scheduler API
        ↓
2. Scheduler persists job
        ↓
3. Scheduler loop checks due jobs
        ↓
4. Due job triggers execution
        ↓
5. Task submitted to Orchestrator
        ↓
6. Normal task execution flow
```

## Security Architecture

### Defense in Depth

1. **Input Validation** - Secure Validator at entry points
2. **Authentication** - JWT tokens with role-based access
3. **Audit Logging** - All actions logged with integrity protection
4. **Rate Limiting** - API endpoint protection
5. **Circuit Breakers** - Fault tolerance

### Security Features by Module

| Module | Security Feature |
|--------|-----------------|
| Secure Validator | SSRF, SQLi, Command Injection prevention |
| Audit Logger | Tamper-proof logs, chain of custody |
| Analysis Bot | False positive reduction, confidence scoring |
| Orchestrator | Input validation, secure task isolation |

## Performance Architecture

### Caching Strategy

- **Memory Cache**: LRU cache for hot data
- **TTL**: Configurable expiration per entry
- **Decorator**: `@cache.cached(ttl=300)` for easy caching

### Connection Pooling

- Min/Max connection limits
- Automatic validation on borrow
- Idle connection cleanup

### Async Optimizations

- Semaphore-based concurrency limiting
- Batch processing for bulk operations
- Rate limiting with token bucket
- Thread pool for sync operations

## Deployment Architecture

### Docker Compose Setup

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
  
  worker:
    build: .
    command: celery worker
  
  redis:
    image: redis:alpine
  
  postgres:
    image: postgres:15
```

### Kubernetes Ready

- Health checks: `/health`, `/ready`, `/live`
- Graceful shutdown handling
- Horizontal Pod Autoscaling ready

## API Design

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/orchestrator/tasks` | POST | Submit new task |
| `/api/v1/scheduler/jobs` | POST | Schedule job |
| `/api/v1/dashboard/data` | GET | Get dashboard data |
| `/api/v1/audit/logs` | GET | Query audit logs |

### WebSocket Events

| Event Type | Description |
|------------|-------------|
| `task.progress` | Task progress update |
| `system.metrics` | System metrics broadcast |
| `security.alert` | Security alert notification |

## Testing Strategy

### Test Pyramid

```
       /\
      /  \    E2E Tests (API)
     /____\
    /      \   Integration Tests
   /________\
  /          \  Unit Tests
 /____________\
```

### Coverage Areas

- **Unit Tests**: Individual components
- **Integration Tests**: Component interactions
- **E2E Tests**: Full API workflows

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Database | PostgreSQL / SQLite |
| Cache | In-Memory / Redis |
| Message Queue | Redis / In-Memory |
| Task Queue | Celery (optional) |
| Frontend | React (separate) |
| Deployment | Docker / Kubernetes |

## Future Extensions

### Planned Features

- [ ] Kubernetes Operator
- [ ] Multi-tenant support
- [ ] Advanced AI models (GPT-4, Claude)
- [ ] Cloud provider integrations (AWS, Azure, GCP)
- [ ] Advanced reporting (PDF, HTML)

### Plugin System

The architecture supports plugins via:

```python
class PentestPlugin:
    def register(self, orchestrator):
        orchestrator.register_tool(self)
    
    async def execute(self, target, options):
        # Plugin logic
        pass
```

## Conclusion

The modular architecture allows for:
- **Independent scaling** of components
- **Easy testing** with clear interfaces
- **Future extensibility** via plugin system
- **Operational visibility** through comprehensive logging

Total: **18,384 lines** of production-ready code.
