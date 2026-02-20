# Zen-Ai-Pentest Framework - Finale System-Architektur

## Übersicht

**Framework:** Zen-Ai-Pentest
**Version:** 3.0.0
**Dokument:** FINALE ARCHITEKTUR-DOKUMENTATION
**Datum:** Februar 2026
**Status:** Produktionsreif

---

## 1. Executive Summary

Das Zen-Ai-Pentest Framework ist eine KI-gestützte Penetration-Testing-Plattform mit Multi-Agent-Architektur. Diese Dokumentation beschreibt die vollständige Systemarchitektur, alle Komponenten und deren Interaktionen.

### Kernmerkmale

| Feature | Beschreibung |
|---------|-------------|
| **Multi-Agent System** | Autonome AI-Agenten für verschiedene Pentest-Phasen |
| **Workflow Engine** | Event-gesteuerte Pentest-Automatisierung |
| **Plugin System** | Erweiterbare Scanner-, Exploit- und Report-Plugins |
| **RBAC** | Rollenbasierte Zugriffskontrolle mit ABAC-Erweiterungen |
| **State Machine** | Hierarchische Zustandsmaschine für Pentest-Phasen |
| **Message Broker** | ACP v1.1 kommunikationsprotokoll zwischen Agenten |
| **Safe Execution** | Sandbox-basierte Exploit-Ausführung |
| **Queue Management** | Prioritäts-Queues mit Retry- und DLQ-Handling |

---

## 2. System-Architektur-Übersicht

### 2.1 High-Level Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ZEN-AI-PENTEST FRAMEWORK                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API GATEWAY LAYER                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ REST API     │  │ WebSocket    │  │ GraphQL      │              │   │
│  │  │ (FastAPI)    │  │ (Real-time)  │  │ (Queries)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATION LAYER                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ ZenOrchestra │  │ Workflow     │  │ State        │              │   │
│  │  │ tor Core     │  │ Engine       │  │ Machine      │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        AGENT LAYER                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Agent        │  │ Message      │  │ Agent        │              │   │
│  │  │ Coordinator  │  │ Broker       │  │ Capabilities │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      EXECUTION LAYER                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ SafeExecutor │  │ Queue        │  │ Plugin       │              │   │
│  │  │ (Sandbox)    │  │ Manager      │  │ System       │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SECURITY LAYER                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ RBAC Manager │  │ Key Mgmt     │  │ Audit Log    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      DATA LAYER                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ PostgreSQL   │  │ Redis        │  │ File Store   │              │   │
│  │  │ (Primary)    │  │ (Cache)      │  │ (Artifacts)  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Komponenten-Übersicht

| Layer | Komponente | Zweck | Technologie |
|-------|-----------|-------|-------------|
| API | REST API | HTTP-Endpunkte | FastAPI |
| API | WebSocket | Real-time Events | FastAPI WebSockets |
| Orchestration | ZenOrchestrator | Hauptkoordination | Python Asyncio |
| Orchestration | Workflow Engine | Task-Ausführung | Python |
| Orchestration | State Machine | Zustandsverwaltung | Python |
| Agent | Agent Coordinator | Agent-Management | Python |
| Agent | Message Broker | Agent-Kommunikation | ACP v1.1 |
| Execution | SafeExecutor | Sandbox-Ausführung | Python + Linux |
| Execution | Queue Manager | Task-Queues | Redis/RabbitMQ |
| Execution | Plugin System | Erweiterungen | Python Plugins |
| Security | RBAC Manager | Zugriffskontrolle | Python |
| Security | Key Management | Schlüsselverwaltung | HashiCorp Vault |
| Data | PostgreSQL | Primärdatenbank | PostgreSQL 15+ |
| Data | Redis | Cache & Queues | Redis 7+ |
| Data | File Store | Artefakte | MinIO/S3 |

---

## 3. Detaillierte Komponenten-Beschreibung

### 3.1 ZenOrchestrator Core

**Datei:** `orchestrator_core.py`

Der ZenOrchestrator ist das Herzstück des Frameworks und koordiniert alle Subsysteme.

#### Features

- **Multi-Mode Betrieb**: STANDALONE, DISTRIBUTED, CLUSTER, CLOUD
- **Fault Tolerance**: Circuit Breaker, Retry-Logik, Self-Healing
- **Monitoring**: System-Metriken, Performance-Tracking, Alerting
- **Checkpointing**: Zustandspersistenz für Recovery

#### Architektur

```python
class ZenOrchestrator:
    """
    Hauptkomponente die alle Subsysteme koordiniert:
    - TaskScheduler: Aufgabenplanung und -ausführung
    - StateManager: Zustandsverwaltung und Persistenz
    - LoadBalancer: Lastverteilung zwischen Agents
    - AgentCoordinator: Agent-Management und -Kommunikation
    - FaultToleranceManager: Fehlertoleranz und Recovery
    - MonitoringService: Überwachung und Alerting
    """
```

#### Konfiguration

```python
@dataclass
class OrchestratorConfig:
    mode: OrchestratorMode = OrchestratorMode.STANDALONE
    max_concurrent_tasks: int = 50
    task_rate_limit: int = 1000
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    auto_recovery: bool = True
    checkpoint_interval: int = 300
```

### 3.2 Workflow Engine

**Datei:** `workflow_engine.py`

Flexible Workflow-Engine für Pentest-Automatisierung.

#### Features

- **Workflow-Definition**: YAML/JSON/Dict-basiert
- **State-Management**: Persistente Zustandsverwaltung
- **Conditional Logic**: Bedingte Task-Ausführung
- **Parallel Execution**: Parallele Task-Gruppen
- **Error Handling**: Retry-Logik mit Exponential Backoff

#### Task-Typen

| Task-Typ | Beschreibung |
|----------|-------------|
| `FunctionTask` | Führt Python-Funktion aus |
| `SubWorkflowTask` | Verschachtelte Workflows |
| `ScannerTask` | Sicherheits-Scan ausführen |
| `ExploitTask` | Exploit validieren/ausführen |

#### Beispiel-Workflow

```python
workflow = Workflow("Pentest Scan Workflow")

# Task 1: Ziel validieren
task1 = FunctionTask(
    name="target_validation",
    func=validate_target,
    metadata={"save_to_context": True, "context_key": "target_info"}
)

# Task 2: Port-Scan (abhängig von Task 1)
task2 = FunctionTask(
    name="port_scan",
    func=nmap_scan,
    dependencies=["target_validation"],
    timeout=300
)

workflow.add_tasks(task1, task2)
```

### 3.3 State Machine

**Datei:** `state_machine.py`

Hochmoderne State Machine für Pentest-Phasen-Management.

#### Features

- **Hierarchical States**: Composite & Sub-States
- **Guarded Transitions**: Komplexe Übergangsbedingungen
- **Event-Driven**: Asynchrone Event-Verarbeitung
- **History States**: Deep/Flat History
- **Auto-Recovery**: Automatische Fehlerbehebung

#### Pentest-States

```
┌─────────┐    start     ┌─────────────────┐
│  IDLE   │─────────────▶│ RECONNAISSANCE  │
└─────────┘              └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │Port Scan │  │ Service  │  │   OS     │
            │          │  │Detection │  │Fingerprint│
            └──────────┘  └──────────┘  └──────────┘
                                  │
                                  ▼ recon_complete
                    ┌─────────────────────────┐
                    │ VULNERABILITY_ASSESSMENT │
                    └────────────┬────────────┘
                                 │
                                 ▼ vulns_found
                         ┌──────────────┐
                         │ EXPLOITATION │
                         └──────┬───────┘
                                │
                                ▼ exploit_success
                         ┌──────────────┐
                         │POST_EXPLOIT  │
                         └──────┬───────┘
                                │
                                ▼ data_collected
                          ┌──────────┐
                          │REPORTING │
                          └────┬─────┘
                               │
                               ▼ report_generated
                          ┌──────────┐
                          │COMPLETED │
                          └──────────┘
```

### 3.4 Message Broker (ACP v1.1)

**Datei:** `message_broker.py`

Agent Communication Protocol v1.1 - Zentraler Message Broker.

#### Features

- **Queue-Management**: Prioritäts-Queues mit Deduplizierung
- **Routing**: Direkt, Broadcast, Topic-basiert
- **Error Recovery**: Retry, Redirect, Dead Letter Queue
- **Encryption**: Optionale Nachrichtenverschlüsselung
- **Pub/Sub**: Publish-Subscribe Integration

#### Nachrichten-Typen

| Typ | Beschreibung |
|-----|-------------|
| `TASK_CREATE` | Neue Task erstellen |
| `TASK_UPDATE` | Task-Status aktualisieren |
| `STATUS_UPDATE` | Agent-Status melden |
| `ERROR` | Fehler melden |
| `BROADCAST` | An alle Agenten |

#### Beispiel-Nutzung

```python
broker = MessageBroker(enable_encryption=True)
await broker.start()

# Agent registrieren
await broker.register_agent(agent, callback)

# Task senden
task = TaskPayload(title="Security Scan", ...)
message_id = await broker.send_task(sender, recipient, task, encrypt=True)
```

### 3.5 RBAC Manager

**Datei:** `rbac_manager.py`

Role-Based Access Control mit ABAC-Erweiterungen.

#### Features

- **Rollen-Hierarchie**: Vererbung von Berechtigungen
- **ABAC**: Attribute-Based Access Control
- **Resource Policies**: Ressourcen-spezifische Policies
- **MFA-Integration**: Multi-Faktor-Authentifizierung
- **Impersonation**: Benutzer-Impersonation mit Prüfung

#### System-Rollen

| Rolle | Level | Beschreibung |
|-------|-------|-------------|
| `super_admin` | 100 | Vollständiger Systemzugriff |
| `admin` | 90 | System-Administration |
| `manager` | 70 | Team-Management |
| `pentester` | 50 | Penetration Tester |
| `analyst` | 40 | Sicherheitsanalyst |
| `guest` | 20 | Gastbenutzer |
| `api` | 40 | API-Zugriff |

#### Berechtigungen (Auszug)

```python
class Permission(str, Enum):
    # Pentest Operations
    PENTEST_READ = "pentest:read"
    PENTEST_CREATE = "pentest:create"
    PENTEST_EXECUTE = "pentest:execute"

    # Scan Operations
    SCAN_READ = "scan:read"
    SCAN_EXECUTE = "scan:execute"
    SCAN_STOP = "scan:stop"

    # Vulnerability Management
    VULN_READ = "vuln:read"
    VULN_VERIFY = "vuln:verify"
```

### 3.6 Safe Executor

**Datei:** `safe_executor.py`

Sandbox-basierte sichere Exploit-Ausführung.

#### Features

- **Sandbox-Isolation**: Isolierte Ausführungsumgebung
- **Ressourcen-Limitierung**: CPU, Memory, File-Size Limits
- **Netzwerk-Isolation**: Eingeschränkte Netzwerkzugriffe
- **Audit-Logging**: Vollständige Audit-Trails
- **Safety-Violation Detection**: Automatische Erkennung

#### Sicherheitsstufen

| Level | Beschreibung |
|-------|-------------|
| `STRICT` | Maximale Einschränkungen |
| `MODERATE` | Ausgewogene Sicherheit |
| `PERMISSIVE` | Für vertrauenswürdige Umgebungen |

#### Ressourcen-Limits

```python
@dataclass
class ResourceLimits:
    max_cpu_time: int = 60           # Sekunden
    max_memory_mb: int = 512         # MB
    max_file_size_mb: int = 100      # MB
    max_processes: int = 10
    max_open_files: int = 50
    max_network_connections: int = 5
```

### 3.7 Queue Manager

**Datei:** `queue_manager.py`

Erweiterter Queue-Manager mit Worker-Management.

#### Features

- **Worker-Management**: Dynamische Worker-Steuerung
- **Retry-Logik**: Exponential Backoff
- **Dead-Letter-Queue**: Fehlgeschlagene Messages
- **Batch-Processing**: Effiziente Batch-Verarbeitung
- **Message Persistence**: Persistente Message-Speicherung

#### Queue-Backends

| Backend | Beschreibung |
|---------|-------------|
| `InMemory` | Für Entwicklung/Tests |
| `Redis` | Produktions-Backend |
| `RabbitMQ` | Enterprise-Backend |

### 3.8 Plugin API

**Datei:** `plugin_api.py`

Erweiterbares Plugin-System für Scanner, Exploits und Reports.

#### Plugin-Typen

| Typ | Interface | Zweck |
|-----|-----------|-------|
| `ScannerPlugin` | Scanner-Interface | Sicherheits-Scanner |
| `ExploitPlugin` | Exploit-Interface | Exploit-Module |
| `ReporterPlugin` | Reporter-Interface | Report-Generierung |
| `AnalyzerPlugin` | Analyzer-Interface | Datenanalyse |
| `IntegrationPlugin` | Integration-Interface | Externe Systeme |

#### Beispiel-Plugin

```python
@scanner(protocols=["http", "https"], ports=[80, 443])
class ExampleScanner(ScannerPlugin):
    NAME = "example_scanner"
    VERSION = "1.0.0"

    async def scan(self, target: Target, options: Dict = None) -> ScanResult:
        # Scan-Logik hier
        pass
```

---

## 4. Datenmodelle

### 4.1 Core Entities

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     USER        │     │    PENTEST      │     │     SCAN        │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id: UUID        │────▶│ id: UUID        │────▶│ id: UUID        │
│ username: str   │     │ name: str       │     │ target: str     │
│ email: str      │     │ status: Enum    │     │ type: Enum      │
│ roles: List     │     │ owner_id: UUID  │     │ status: Enum    │
│ org_id: UUID    │     │ started_at: dt  │     │ progress: int   │
└─────────────────┘     │ completed_at: dt│     │ findings: int   │
                        └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │    FINDING      │
                                                ├─────────────────┤
                                                │ id: UUID        │
                                                │ title: str      │
                                                │ severity: Enum  │
                                                │ cvss_score: flt │
                                                │ cve_id: str     │
                                                │ evidence: JSON  │
                                                └─────────────────┘
```

### 4.2 Agent Communication

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  ACPMessage     │         │  AgentIdentity  │         │  TaskPayload    │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ header          │         │ agent_id: str   │         │ title: str      │
│ sender          │◄────────│ role: Enum      │         │ description: str│
│ recipient       │         │ name: str       │         │ instructions:str│
│ payload         │         │ capabilities    │         │ parameters: JSON│
│ metadata        │         │ metadata        │         │ priority: Enum  │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

## 5. API-Design

### 5.1 REST API Endpunkte

| Methode | Endpoint | Beschreibung | Auth |
|---------|----------|--------------|------|
| POST | `/v1/auth/login` | Login | Nein |
| POST | `/v1/auth/logout` | Logout | Ja |
| GET | `/v1/scans` | Alle Scans | Ja |
| POST | `/v1/scans` | Scan erstellen | Ja |
| GET | `/v1/scans/{id}` | Scan-Details | Ja |
| DELETE | `/v1/scans/{id}` | Scan löschen | Ja |
| GET | `/v1/agents` | Alle Agents | Ja |
| POST | `/v1/agents` | Agent erstellen | Admin |
| GET | `/v1/findings` | Alle Findings | Ja |
| GET | `/v1/reports` | Alle Reports | Ja |
| POST | `/v1/reports` | Report generieren | Ja |

### 5.2 WebSocket Events

| Event | Beschreibung |
|-------|-------------|
| `scan.progress` | Scan-Fortschritt |
| `scan.finding` | Neues Finding |
| `scan.complete` | Scan abgeschlossen |
| `agent.status` | Agent-Status-Änderung |
| `agent.message` | Agent-Nachricht |

---

## 6. Sicherheitsarchitektur

### 6.1 ISO 27001 Compliance

| Anforderung | Implementierung | Status |
|-------------|-----------------|--------|
| A.9.4.1 (Passwort-Management) | Keycloak Integration | ✅ |
| A.9.4.2 (Zugriffskontrolle) | RBAC Manager | ✅ |
| A.10.1.1 (Kryptographie) | Vault Integration | ✅ |
| A.12.3.1 (Logging) | Zentrale Log-Aggregation | ✅ |
| A.12.4.1 (Event-Logging) | Audit-Log | ✅ |
| A.14.1.1 (Sichere Entwicklung) | SAST/DAST Pipeline | ✅ |
| A.16.1.1 (Incident Management) | Alerting System | ✅ |

### 6.2 Sicherheitsmaßnahmen

| Maßnahme | Implementierung |
|----------|-----------------|
| **Authentifizierung** | JWT mit kurzer Lebensdauer |
| **Autorisierung** | RBAC + ABAC |
| **Input Validation** | Pydantic Schemas |
| **Output Encoding** | JSON/HTML Escaping |
| **Transport Security** | TLS 1.3 |
| **Sandboxing** | SafeExecutor |
| **Audit Logging** | Vollständige Trails |

---

## 7. Deployment-Architektur

### 7.1 Docker-Compose

```yaml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379

  orchestrator:
    build: ./orchestrator
    environment:
      - MODE=cluster

  agent-pool:
    build: ./agents
    replicas: 5

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7

  minio:
    image: minio/minio
    command: server /data
```

### 7.2 Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zen-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    spec:
      containers:
      - name: orchestrator
        image: zen-ai-pentest/orchestrator:latest
        env:
        - name: MODE
          value: "cluster"
```

---

## 8. Monitoring & Observability

### 8.1 Metriken

| Metrik | Beschreibung | Ziel |
|--------|-------------|------|
| API Response Time | p95 Latenz | < 200ms |
| Task Throughput | Tasks/Sekunde | > 100 |
| Error Rate | Fehlerquote | < 1% |
| Agent Utilization | Agent-Auslastung | 70-90% |
| Queue Depth | Queue-Größe | < 1000 |

### 8.2 Logging

```python
# Strukturiertes Logging
{
    "timestamp": "2026-02-15T10:30:00Z",
    "level": "INFO",
    "component": "ZenOrchestrator",
    "event": "task_completed",
    "task_id": "task_123",
    "duration_ms": 150,
    "trace_id": "trace_abc123"
}
```

### 8.3 Tracing

- **Distributed Tracing**: OpenTelemetry
- **Trace-ID**: Über alle Komponenten hinweg
- **Span-Kontext**: Request-Flow-Visualisierung

---

## 9. Performance-Kennzahlen

### 9.1 Ziel-KPIs

| KPI | Aktuell | Ziel |
|-----|---------|------|
| API Response (p95) | ~500ms | < 200ms |
| LLM Routing Latenz | ~200ms | < 100ms |
| DB Queries | ~100ms | < 50ms |
| Concurrent Requests | ~50 | > 500 |
| Task Throughput | ~50/s | > 100/s |

### 9.2 Optimierungen

- **Caching**: Redis für häufige Abfragen
- **Connection Pooling**: DB-Connection-Pool
- **Async Processing**: Asyncio für I/O-Operationen
- **Batch Processing**: Batch-Insert/Update

---

## 10. Erweiterbarkeit

### 10.1 Plugin-Entwicklung

```python
# Neues Scanner-Plugin
from plugin_api import ScannerPlugin, scanner, Target, ScanResult

@scanner(protocols=["tcp"], ports=[22, 80, 443])
class CustomScanner(ScannerPlugin):
    NAME = "custom_scanner"
    VERSION = "1.0.0"

    async def scan(self, target: Target, options: dict = None) -> ScanResult:
        # Implementierung
        pass
```

### 10.2 Workflow-Erweiterung

```python
# Custom Task
class CustomTask(Task):
    async def execute(self, context: Dict[str, Any]) -> TaskResult:
        # Implementierung
        return TaskResult(success=True, data={"result": "ok"})
```

---

## 11. Fehlerbehandlung

### 11.1 Error Codes

| Code | Beschreibung |
|------|-------------|
| `AUTH_INVALID_CREDENTIALS` | 1001 |
| `AUTH_TOKEN_EXPIRED` | 1002 |
| `VALIDATION_ERROR` | 2001 |
| `RESOURCE_NOT_FOUND` | 3001 |
| `SCAN_TIMEOUT` | 4004 |
| `AGENT_NOT_AVAILABLE` | 5001 |
| `RATE_LIMIT_EXCEEDED` | 9001 |

### 11.2 Retry-Strategien

| Fehler-Typ | Strategie | Max Retries |
|------------|-----------|-------------|
| Timeout | Exponential Backoff | 3 |
| Connection Error | Linear Backoff | 5 |
| Rate Limit | Exponential Backoff | 10 |

---

## 12. Zusammenfassung

Das Zen-Ai-Pentest Framework ist eine moderne, skalierbare und sichere Penetration-Testing-Plattform mit folgenden Kernstärken:

1. **Multi-Agent Architektur**: Autonome AI-Agenten für alle Pentest-Phasen
2. **Workflow-Automatisierung**: Event-gesteuerte Pentest-Automatisierung
3. **Erweiterbarkeit**: Plugin-System für Scanner, Exploits und Reports
4. **Sicherheit**: RBAC, Sandbox-Ausführung, Audit-Logging
5. **Skalierbarkeit**: Horizontal skalierbare Microservices-Architektur
6. **Observability**: Umfassendes Monitoring, Logging und Tracing

---

## Anhänge

### A. Datei-Struktur

```
/mnt/okcomputer/output/
├── orchestrator_core.py      # Haupt-Orchestrator
├── workflow_engine.py        # Workflow-Engine
├── state_machine.py          # State Machine
├── message_broker.py         # ACP Message Broker
├── rbac_manager.py           # RBAC Manager
├── safe_executor.py          # Safe Executor
├── queue_manager.py          # Queue Manager
├── plugin_api.py             # Plugin API
├── api_design.md             # API Design
├── FINAL_ARCHITECTURE.md     # Dieses Dokument
└── system_overview.mmd       # Mermaid-Diagramm
```

### B. Abhängigkeiten

```
Python 3.11+
FastAPI 0.104+
SQLAlchemy 2.0+
Redis 7+
PostgreSQL 15+
```

### C. Lizenz

Zen-Ai-Pentest - Educational Purpose Only

---

*Diese Dokumentation wurde automatisch generiert und sollte regelmäßig aktualisiert werden.*
