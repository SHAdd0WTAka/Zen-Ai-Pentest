# Agent Communication Protocol (ACP) v1.1 Spezifikation

**Version:** 1.1.0
**Datum:** 2026-02-11
**Autor:** Zen-Ai-Pentest Team
**Status:** Final

---

## Inhaltsverzeichnis

1. [Überblick](#1-überblick)
2. [Änderungen von v1.0 zu v1.1](#2-änderungen-von-v10-zu-v11)
3. [Architektur](#3-architektur)
4. [Message-Format](#4-message-format)
5. [Message-Types](#5-message-types)
6. [Pub/Sub-System](#6-pubsub-system)
7. [Verschlüsselung](#7-verschlüsselung)
8. [Error Recovery](#8-error-recovery)
9. [JSON Schema](#9-json-schema)
10. [Implementierungsdetails](#10-implementierungsdetails)

---

## 1. Überblick

Das Agent Communication Protocol (ACP) v1.1 ist ein typsicheres, skalierbares Kommunikationsprotokoll für den Nachrichtenaustausch zwischen Agenten im Zen-Ai-Pentest Framework. Es baut auf ACP v1.0 auf und fügt wichtige Features hinzu:

- **Pydantic-basierte Validierung** mit JSON Schema Enforcement
- **Publish/Subscribe-System** für dezentrale Kommunikation
- **Ende-zu-Ende-Verschlüsselung** mit AES-256-GCM und ChaCha20-Poly1305
- **Automatische Fehlerbehebung** mit Retry-Mechanismen
- **Message Broker** mit Queue-Management und Routing

### Design-Prinzipien

1. **Typsicherheit:** Alle Nachrichten werden durch Pydantic-Modelle validiert
2. **Skalierbarkeit:** Pub/Sub-Architektur ermöglicht horizontale Skalierung
3. **Sicherheit:** E2E-Verschlüsselung für alle sensiblen Daten
4. **Zuverlässigkeit:** Automatische Wiederholung und Fehlerbehebung
5. **Backward Compatibility:** Volle Kompatibilität zu ACP v1.0

---

## 2. Änderungen von v1.0 zu v1.1

### 2.1 Neue Features

| Feature | ACP v1.0 | ACP v1.1 |
|---------|----------|----------|
| Message-Format | Markdown/Text | JSON/Pydantic |
| Validierung | Manuell | Automatisch (Pydantic) |
| Verschlüsselung | ❌ | ✅ AES-256-GCM, ChaCha20-Poly1305 |
| Pub/Sub | ❌ | ✅ Topic-basiert |
| Message Broker | ❌ | ✅ Mit Queue-Management |
| Error Recovery | ❌ | ✅ Automatisch |
| JSON Schema | ❌ | ✅ Vollständig |
| Backward Compat. | - | ✅ Konverter eingebaut |

### 2.2 Breaking Changes

- Keine Breaking Changes für existierende Workflows
- ACP v1.0 Nachrichten werden automatisch konvertiert

---

## 3. Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        ACP v1.1 Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Agent 1   │    │   Agent 2   │    │   Agent N   │         │
│  │ (CLI-Kimi)  │    │(PowerShell) │    │  (Worker)   │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                │
│         └──────────────────┼──────────────────┘                │
│                            │                                    │
│                   ┌────────▼────────┐                          │
│                   │  Message Broker │                          │
│                   │  ├─ Router      │                          │
│                   │  ├─ Queue       │                          │
│                   │  ├─ Validator   │                          │
│                   │  └─ Recovery    │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         │                  │                  │                │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐         │
│  │   Pub/Sub   │    │ Encryption  │    │   Storage   │         │
│  │   Engine    │    │    Layer    │    │   (Opt.)    │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 Komponenten

#### Message Broker
- Zentrale Koordinationskomponente
- Verwaltet Message-Queues
- Routet Nachrichten zu den richtigen Empfängern
- Integriert Error Recovery

#### Pub/Sub Engine
- Topic-basiertes Messaging
- Wildcard-Unterstützung (`*`, `#`)
- Prioritäts-basierte Verarbeitung
- Filter-Kriterien

#### Encryption Layer
- Transparente E2E-Verschlüsselung
- Schlüsselmanagement
- ECDH-Schlüsselaustausch
- Signatur-Validierung

---

## 4. Message-Format

### 4.1 Haupt-Message-Struktur (ACPMessage)

```json
{
  "header": {
    "message_id": "uuid-v4",
    "correlation_id": "optional-uuid",
    "message_type": "task.create",
    "version": "1.1.0",
    "priority": 2,
    "timestamp": "2026-02-11T12:00:00Z",
    "ttl": 300
  },
  "sender": {
    "agent_id": "cli_kimi_001",
    "role": "cli_kimi",
    "name": "CLI-Kimi",
    "version": "1.0.0",
    "capabilities": ["analysis", "planning"]
  },
  "recipient": {
    "agent_id": "powershell_kimi_001",
    "role": "powershell_kimi",
    "name": "PowerShell-Kimi",
    "version": "1.0.0",
    "capabilities": ["execution", "debugging"]
  },
  "payload": {
    "data": { },
    "encoding": "json",
    "compression": null
  },
  "security": {
    "encryption": "aes256_gcm",
    "signature": "base64-signature",
    "auth_token": "optional-token",
    "key_id": "key-uuid"
  },
  "metadata": {},
  "tags": ["github-actions", "webhook"],
  "created_at": "2026-02-11T12:00:00Z",
  "updated_at": null,
  "expires_at": null,
  "delivery_attempts": 0,
  "last_error": null
}
```

### 4.2 Header-Felder

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| message_id | string | Ja | Eindeutige UUID v4 |
| correlation_id | string | Nein | Für Request-Response-Paare |
| message_type | enum | Ja | Typ der Nachricht |
| version | string | Ja | ACP-Version (z.B. "1.1.0") |
| priority | int | Nein | 0=Kritisch, 4=Background |
| timestamp | datetime | Ja | ISO 8601 Zeitstempel |
| ttl | int | Nein | Time-to-Live in Sekunden |

### 4.3 AgentIdentity

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| agent_id | string | Ja | Eindeutige Agent-ID |
| role | enum | Ja | Agent-Rolle |
| name | string | Ja | Anzeigename |
| version | string | Nein | Agent-Version |
| capabilities | list | Nein | Fähigkeiten des Agenten |

---

## 5. Message-Types

### 5.1 Task Management

#### TASK_CREATE
Erstellt eine neue Task.

```json
{
  "header": { "message_type": "task.create" },
  "payload": {
    "data": {
      "task_id": "uuid",
      "title": "Task Title",
      "description": "Task Description",
      "status": "pending",
      "instructions": "Step-by-step instructions",
      "expected_result": "Expected outcome",
      "deadline": "2026-02-11T18:00:00Z",
      "priority": 1
    }
  }
}
```

#### TASK_UPDATE
Aktualisiert den Status einer Task.

```json
{
  "header": { "message_type": "task.update" },
  "payload": {
    "data": {
      "task_id": "uuid",
      "status": "in_progress",
      "progress": 50,
      "message": "Current status message"
    }
  }
}
```

#### TASK_COMPLETE
Markiert eine Task als abgeschlossen.

```json
{
  "header": { "message_type": "task.complete" },
  "payload": {
    "data": {
      "task_id": "uuid",
      "status": "completed",
      "result": { },
      "completed_at": "2026-02-11T14:00:00Z"
    }
  }
}
```

### 5.2 Status Updates

#### STATUS_UPDATE
Sendet einen Status-Update.

```json
{
  "header": { "message_type": "status.update" },
  "payload": {
    "data": {
      "agent_status": "online",
      "current_task_id": "uuid",
      "queue_size": 5,
      "memory_usage": 128.5,
      "cpu_usage": 25.0,
      "active_connections": 3
    }
  }
}
```

### 5.3 Error Handling

#### ERROR
Meldet einen Fehler.

```json
{
  "header": { "message_type": "error" },
  "payload": {
    "data": {
      "error_code": "DELIVERY_FAILED",
      "severity": "error",
      "message": "Failed to deliver message",
      "details": { },
      "recoverable": true,
      "retry_count": 1,
      "max_retries": 3
    }
  }
}
```

### 5.4 Security

#### KEY_EXCHANGE
Tauscht kryptographische Schlüssel aus.

```json
{
  "header": { "message_type": "security.key_exchange" },
  "payload": {
    "data": {
      "public_key": "-----BEGIN PUBLIC KEY-----\n...",
      "key_algorithm": "ECDH",
      "key_id": "uuid",
      "expires_at": "2026-02-11T13:00:00Z"
    }
  }
}
```

---

## 6. Pub/Sub-System

### 6.1 Topic-Format

Topics folgen einer hierarchischen Struktur:

```
agent/{agent_id}/status
agent/{agent_id}/tasks
task/{task_id}/updates
broadcast/all
broadcast/role/{role}
system/events
system/errors
logs/{agent_id}
```

### 6.2 Wildcards

- `*` - Ein einzelnes Topic-Level
  - `agent/*/status` matcht `agent/001/status`, `agent/002/status`

- `#` - Mehrere Topic-Level (nur am Ende)
  - `agent/#` matcht `agent/001`, `agent/001/status`, `agent/001/tasks/123`

### 6.3 Subscription-Beispiel

```python
# Abonniere alle Status-Updates
subscription_id = pubsub.subscribe(
    subscriber_id="monitor_agent",
    topic_pattern="agent/+/status",
    callback=status_handler,
    priority=MessagePriority.HIGH,
    filter_criteria={
        "min_priority": MessagePriority.NORMAL,
        "tags": ["important"]
    }
)
```

---

## 7. Verschlüsselung

### 7.1 Unterstützte Algorithmen

| Algorithmus | Schlüssellänge | Modus | Empfohlen |
|-------------|----------------|-------|-----------|
| AES-256-GCM | 256 Bit | GCM | ✅ Ja |
| ChaCha20-Poly1305 | 256 Bit | AEAD | ✅ Ja |
| None | - | - | Nur für Tests |

### 7.2 Schlüsselaustausch

Verwendet ECDH (Elliptic Curve Diffie-Hellman) mit secp384r1:

1. Agent A generiert ECDH-Schlüsselpaar
2. Agent A sendet öffentlichen Schlüssel an Agent B
3. Agent B generiert eigenes Schlüsselpaar
4. Beide Agenten leiten gemeinsamen Session-Schlüssel ab
5. Session-Schlüssel wird für symmetrische Verschlüsselung verwendet

### 7.3 Verschlüsselungs-Beispiel

```python
# Initialisiere Verschlüsselung
encryption = MessageEncryption()

# Verschlüssele Nachricht
encrypted_message = encryption.encrypt_message(message, key_id="session_key_001")

# Entschlüssele Nachricht
decrypted_message = encryption.decrypt_message(encrypted_message)
```

---

## 8. Error Recovery

### 8.1 Wiederherstellungsstrategien

| Strategie | Beschreibung | Anwendungsfall |
|-----------|--------------|----------------|
| RETRY | Nachricht erneut senden | Timeout, temporärer Fehler |
| REDIRECT | An anderen Agenten senden | Agent nicht verfügbar |
| ESCALATE | An Supervisor melden | Kritischer Fehler |
| DEAD_LETTER | In DLQ speichern | Max Retries überschritten |
| DROP | Nachricht verwerfen | Nicht behebbarer Fehler |

### 8.2 Retry-Konfiguration

```python
RecoveryAction(
    strategy=ErrorRecoveryStrategy.RETRY,
    delay=5,           # Sekunden vor Wiederholung
    max_attempts=3,    # Maximale Versuche
    reason="Connection timeout"
)
```

### 8.3 Dead Letter Queue

Nachrichten, die nach maximalen Wiederholungsversuchen nicht zugestellt werden können,
werden in die Dead Letter Queue (DLQ) verschoben. Sie können später:
- Manuell überprüft werden
- Erneut versendet werden
- Für Analyse exportiert werden

---

## 9. JSON Schema

### 9.1 Schema-Export

Alle Pydantic-Modelle können als JSON Schema exportiert werden:

```python
from acp_models import export_json_schemas

# Exportiere alle Schemas
schema_paths = export_json_schemas("./schemas")
```

### 9.2 Verfügbare Schemas

- `acp_message_schema.json` - Haupt-Message-Schema
- `message_header_schema.json` - Header-Schema
- `agent_identity_schema.json` - Agent-Schema
- `task_payload_schema.json` - Task-Payload
- `status_payload_schema.json` - Status-Payload
- `error_payload_schema.json` - Error-Payload
- `file_transfer_payload_schema.json` - File-Transfer
- `data_request_payload_schema.json` - Data-Request
- `data_response_payload_schema.json` - Data-Response
- `key_exchange_payload_schema.json` - Key-Exchange
- `auth_payload_schema.json` - Auth-Payload

---

## 10. Implementierungsdetails

### 10.1 Abhängigkeiten

```
pydantic >= 2.0.0
cryptography >= 41.0.0
```

### 10.2 Performance-Kennzahlen

| Metrik | Zielwert |
|--------|----------|
| Nachrichten/Seconde | > 10.000 |
| Latenz (P50) | < 10 ms |
| Latenz (P99) | < 100 ms |
| Queue-Größe | 10.000 Nachrichten |
| Max. Payload | 10 MB |

### 10.3 Sicherheitsanforderungen

1. **Verschlüsselung:** Alle sensiblen Daten müssen verschlüsselt werden
2. **Authentifizierung:** Agenten müssen sich authentifizieren
3. **Autorisierung:** Rollenbasierte Zugriffskontrolle
4. **Audit-Logging:** Alle Nachrichten müssen protokolliert werden
5. **Schlüsselrotation:** Schlüssel müssen regelmäßig rotiert werden

---

## Anhang A: Enum-Werte

### MessageType
```python
task.create, task.update, task.complete, task.cancel
status.update, status.request, status.response
message, broadcast, direct
data.request, data.response, file.transfer
control.heartbeat, control.register, control.unregister, control.shutdown
error, retry, recovery
security.key_exchange, security.auth_request, security.auth_response
```

### MessagePriority
```python
CRITICAL = 0
HIGH = 1
NORMAL = 2
LOW = 3
BACKGROUND = 4
```

### TaskStatus
```python
pending, assigned, in_progress, completed, failed, cancelled, retrying
```

### AgentRole
```python
cli_kimi, powershell_kimi, orchestrator, worker, monitor, reviewer
```

### ErrorSeverity
```python
debug, info, warning, error, critical, fatal
```

---

## Anhang B: Beispiel-Workflow

### Szenario: Task-Zuweisung und Ausführung

```
1. CLI-Kimi erstellt Task
   → send_message(TASK_CREATE)
   → Message Broker routet zu PowerShell-Kimi

2. PowerShell-Kimi empfängt Task
   → send_message(STATUS_UPDATE, "in_progress")
   → Führt Task aus

3. PowerShell-Kimi sendet Updates
   → send_message(TASK_UPDATE, progress=50%)

4. PowerShell-Kimi schließt Task ab
   → send_message(TASK_COMPLETE, result={...})

5. CLI-Kimi empfängt Abschluss
   → send_message(MESSAGE, "Task completed successfully")
```

---

**Ende der Spezifikation**
