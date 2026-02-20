"""
Agent Communication Protocol (ACP) v1.1 - Pydantic Models
==========================================================

Dieses Modul definiert alle Pydantic-Modelle für das ACP v1.1 Protokoll.
Es bietet typsichere Message-Validierung, JSON Schema Enforcement und
Backward Compatibility zu ACP v1.0.

Autor: Zen-Ai-Pentest Team
Version: 1.1.0
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# =============================================================================
# Enums und Konstanten
# =============================================================================


class MessageType(str, Enum):
    """Alle unterstützten Message-Typen im ACP v1.1"""

    # Task Management
    TASK_CREATE = "task.create"
    TASK_UPDATE = "task.update"
    TASK_COMPLETE = "task.complete"
    TASK_CANCEL = "task.cancel"

    # Status Updates
    STATUS_UPDATE = "status.update"
    STATUS_REQUEST = "status.request"
    STATUS_RESPONSE = "status.response"

    # Communication
    MESSAGE = "message"
    BROADCAST = "broadcast"
    DIRECT = "direct"

    # Data Exchange
    DATA_REQUEST = "data.request"
    DATA_RESPONSE = "data.response"
    FILE_TRANSFER = "file.transfer"

    # Control
    HEARTBEAT = "control.heartbeat"
    REGISTER = "control.register"
    UNREGISTER = "control.unregister"
    SHUTDOWN = "control.shutdown"

    # Error Handling
    ERROR = "error"
    RETRY = "retry"
    RECOVERY = "recovery"

    # Security
    KEY_EXCHANGE = "security.key_exchange"
    AUTH_REQUEST = "security.auth_request"
    AUTH_RESPONSE = "security.auth_response"


class MessagePriority(IntEnum):
    """Message-Prioritäten für das Queue-Management"""

    CRITICAL = 0  # Sofortige Verarbeitung
    HIGH = 1  # Priorisierte Verarbeitung
    NORMAL = 2  # Standard-Verarbeitung
    LOW = 3  # Hintergrund-Verarbeitung
    BACKGROUND = 4  # Niedrigste Priorität


class TaskStatus(str, Enum):
    """Status-Werte für Tasks"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AgentRole(str, Enum):
    """Definierte Agent-Rollen im System"""

    CLI_KIMI = "cli_kimi"
    POWERSHELL_KIMI = "powershell_kimi"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    MONITOR = "monitor"
    REVIEWER = "reviewer"


class AgentStatus(str, Enum):
    """Agent-Status-Werte"""

    ONLINE = "online"
    BUSY = "busy"
    AWAY = "away"
    OFFLINE = "offline"
    ERROR = "error"


class ErrorSeverity(str, Enum):
    """Fehler-Schweregrade"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class EncryptionAlgorithm(str, Enum):
    """Unterstützte Verschlüsselungsalgorithmen"""

    NONE = "none"
    AES256_GCM = "aes256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"


# =============================================================================
# Basis-Modelle
# =============================================================================


class ACPBaseModel(BaseModel):
    """Basisklasse für alle ACP-Modelle mit gemeinsamer Konfiguration"""

    model_config = ConfigDict(
        extra="forbid",  # Keine zusätzlichen Felder erlaubt
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        json_schema_extra={"version": "1.1.0"},
    )


class TimestampMixin(BaseModel):
    """Mixin für Zeitstempel-Felder"""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Erstellungszeitpunkt der Nachricht"
    )
    updated_at: Optional[datetime] = Field(default=None, description="Letzter Aktualisierungszeitpunkt")
    expires_at: Optional[datetime] = Field(default=None, description="Ablaufzeitpunkt der Nachricht")


class MetadataMixin(BaseModel):
    """Mixin für Metadaten-Felder"""

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten", max_length=1000)
    tags: List[str] = Field(default_factory=list, description="Tags für Kategorisierung", max_length=50)


# =============================================================================
# Core Message Models
# =============================================================================


class AgentIdentity(ACPBaseModel):
    """Identifiziert einen Agenten eindeutig"""

    agent_id: str = Field(..., description="Eindeutige Agent-ID", min_length=1, max_length=128)
    role: AgentRole = Field(..., description="Rolle des Agenten")
    name: str = Field(..., description="Anzeigename des Agenten", min_length=1, max_length=256)
    version: str = Field(default="1.0.0", description="Agent-Version", pattern=r"^\d+\.\d+\.\d+")
    capabilities: List[str] = Field(default_factory=list, description="Fähigkeiten des Agenten")

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Validiert die Agent-ID Format"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Agent-ID darf nur alphanumerische Zeichen, Bindestriche und Unterstriche enthalten")
        return v


class MessageHeader(ACPBaseModel):
    """Header für alle ACP-Nachrichten"""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Eindeutige Message-ID")
    correlation_id: Optional[str] = Field(default=None, description="Korrelations-ID für Request-Response-Paare")
    message_type: MessageType = Field(..., description="Typ der Nachricht")
    version: str = Field(default="1.1.0", description="ACP-Protokollversion", pattern=r"^\d+\.\d+\.\d+$")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="Priorität der Nachricht")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Zeitstempel der Nachricht")
    ttl: int = Field(default=300, description="Time-to-Live in Sekunden", ge=0, le=86400)


class MessagePayload(ACPBaseModel):
    """Basis-Payload für alle Nachrichten"""

    data: Dict[str, Any] = Field(default_factory=dict, description="Payload-Daten")
    encoding: str = Field(default="json", description="Encoding der Daten", pattern=r"^(json|base64|binary|encrypted)$")
    compression: Optional[str] = Field(default=None, description="Kompressionsalgorithmus", pattern=r"^(gzip|zlib|lz4|none)$")

    @field_validator("data")
    @classmethod
    def validate_data_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validiert die Größe der Payload-Daten"""
        data_size = len(json.dumps(v))
        if data_size > 10 * 1024 * 1024:  # 10 MB Limit
            raise ValueError(f"Payload zu groß: {data_size} bytes (max 10 MB)")
        return v


class MessageSecurity(ACPBaseModel):
    """Sicherheitsinformationen für Nachrichten"""

    encryption: EncryptionAlgorithm = Field(default=EncryptionAlgorithm.NONE, description="Verwendete Verschlüsselung")
    signature: Optional[str] = Field(default=None, description="Digitale Signatur der Nachricht")
    auth_token: Optional[str] = Field(default=None, description="Authentifizierungs-Token")
    key_id: Optional[str] = Field(default=None, description="ID des verwendeten Schlüssels")


# =============================================================================
# Haupt-Message-Model
# =============================================================================


class ACPMessage(ACPBaseModel, TimestampMixin, MetadataMixin):
    """
    Haupt-Message-Modell für ACP v1.1

    Dies ist die zentrale Nachrichtenstruktur, die alle Kommunikation
    zwischen Agenten im Zen-Ai-Pentest Framework ermöglicht.
    """

    header: MessageHeader = Field(..., description="Message-Header mit Metadaten")
    sender: AgentIdentity = Field(..., description="Absender der Nachricht")
    recipient: Optional[AgentIdentity] = Field(default=None, description="Empfänger der Nachricht (None für Broadcast)")
    payload: MessagePayload = Field(..., description="Nutzerdaten der Nachricht")
    security: MessageSecurity = Field(default_factory=MessageSecurity, description="Sicherheitsinformationen")

    # Tracking-Felder
    delivery_attempts: int = Field(default=0, description="Anzahl der Zustellungsversuche", ge=0)
    last_error: Optional[str] = Field(default=None, description="Letzter Fehler bei der Zustellung")

    @model_validator(mode="after")
    def validate_message(self) -> "ACPMessage":
        """Validiert die vollständige Nachricht"""
        # Prüfe TTL
        if self.header.ttl <= 0:
            raise ValueError("TTL muss größer als 0 sein")

        # Prüfe Ablaufzeit
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            raise ValueError("Nachricht ist bereits abgelaufen")

        return self

    def is_expired(self) -> bool:
        """Prüft ob die Nachricht abgelaufen ist"""
        if self.expires_at:
            return self.expires_at < datetime.now(timezone.utc)
        age = (datetime.now(timezone.utc) - self.header.timestamp).total_seconds()
        return age > self.header.ttl

    def to_json(self, indent: Optional[int] = None) -> str:
        """Konvertiert die Nachricht zu JSON"""
        return self.model_dump_json(indent=indent)

    def compute_hash(self) -> str:
        """Berechnet einen Hash der Nachricht für Deduplizierung"""
        data = self.model_dump(exclude={"header": {"message_id"}})
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


# =============================================================================
# Spezialisierte Payload-Modelle
# =============================================================================


class TaskPayload(ACPBaseModel):
    """Payload für Task-bezogene Nachrichten"""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Eindeutige Task-ID")
    title: str = Field(..., description="Task-Titel", min_length=1, max_length=512)
    description: str = Field(default="", description="Task-Beschreibung", max_length=10000)
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Aktueller Task-Status")
    assigned_to: Optional[str] = Field(default=None, description="Zugewiesener Agent")
    parent_task_id: Optional[str] = Field(default=None, description="ID der übergeordneten Task")
    dependencies: List[str] = Field(default_factory=list, description="Abhängige Task-IDs")
    instructions: str = Field(default="", description="Ausführungsanweisungen", max_length=50000)
    expected_result: Optional[str] = Field(default=None, description="Erwartetes Ergebnis")
    deadline: Optional[datetime] = Field(default=None, description="Deadline für die Task")
    progress: int = Field(default=0, description="Fortschritt in Prozent", ge=0, le=100)
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task-Ergebnis")
    error_message: Optional[str] = Field(default=None, description="Fehlermeldung bei Fehlschlag")


class StatusPayload(ACPBaseModel):
    """Payload für Status-Updates"""

    agent_status: AgentStatus = Field(..., description="Status des Agenten")
    current_task_id: Optional[str] = Field(default=None, description="ID der aktuellen Task")
    queue_size: int = Field(default=0, description="Größe der Message-Queue", ge=0)
    memory_usage: Optional[float] = Field(default=None, description="Speichernutzung in MB", ge=0)
    cpu_usage: Optional[float] = Field(default=None, description="CPU-Nutzung in Prozent", ge=0, le=100)
    active_connections: int = Field(default=0, description="Anzahl aktiver Verbindungen", ge=0)
    last_activity: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Zeitpunkt der letzten Aktivität"
    )
    capabilities_available: List[str] = Field(default_factory=list, description="Verfügbare Fähigkeiten")


class ErrorPayload(ACPBaseModel):
    """Payload für Fehlernachrichten"""

    error_code: str = Field(..., description="Fehlercode", min_length=1, max_length=64)
    severity: ErrorSeverity = Field(default=ErrorSeverity.ERROR, description="Schweregrad des Fehlers")
    message: str = Field(..., description="Fehlermeldung", max_length=10000)
    details: Optional[Dict[str, Any]] = Field(default=None, description="Zusätzliche Fehlerdetails")
    stack_trace: Optional[str] = Field(default=None, description="Stack-Trace (nur bei internen Fehlern)")
    recoverable: bool = Field(default=True, description="Ob der Fehler behebbar ist")
    retry_count: int = Field(default=0, description="Anzahl der Wiederholungsversuche", ge=0)
    max_retries: int = Field(default=3, description="Maximale Anzahl der Wiederholungsversuche", ge=0)


class FileTransferPayload(ACPBaseModel):
    """Payload für Dateiübertragungen"""

    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Eindeutige Datei-ID")
    filename: str = Field(..., description="Dateiname", max_length=512)
    file_size: int = Field(..., description="Dateigröße in Bytes", ge=0)
    mime_type: str = Field(..., description="MIME-Typ der Datei")
    checksum: str = Field(..., description="SHA-256 Prüfsumme der Datei")
    chunk_index: int = Field(default=0, description="Index des aktuellen Chunks", ge=0)
    total_chunks: int = Field(default=1, description="Gesamtanzahl der Chunks", ge=1)
    chunk_data: Optional[str] = Field(default=None, description="Base64-kodierte Chunk-Daten")
    compression: Optional[str] = Field(default=None, description="Kompressionsalgorithmus")


class DataRequestPayload(ACPBaseModel):
    """Payload für Datenanfragen"""

    query: str = Field(..., description="Suchanfrage", min_length=1, max_length=10000)
    data_type: str = Field(..., description="Typ der angeforderten Daten")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filterkriterien")
    limit: int = Field(default=100, description="Maximale Anzahl der Ergebnisse", ge=1, le=10000)
    offset: int = Field(default=0, description="Offset für Paginierung", ge=0)
    sort_by: Optional[str] = Field(default=None, description="Sortierfeld")
    sort_order: str = Field(default="asc", description="Sortierreihenfolge", pattern=r"^(asc|desc)$")


class DataResponsePayload(ACPBaseModel):
    """Payload für Datenantworten"""

    request_id: str = Field(..., description="ID der ursprünglichen Anfrage")
    total_count: int = Field(default=0, description="Gesamtanzahl der verfügbaren Ergebnisse", ge=0)
    returned_count: int = Field(default=0, description="Anzahl der zurückgegebenen Ergebnisse", ge=0)
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Ergebnisdaten")
    has_more: bool = Field(default=False, description="Ob weitere Ergebnisse verfügbar sind")


class KeyExchangePayload(ACPBaseModel):
    """Payload für Schlüsselaustausch"""

    public_key: str = Field(..., description="Öffentlicher Schlüssel (Base64)")
    key_algorithm: str = Field(default="ECDH", description="Schlüsselaustausch-Algorithmus")
    key_id: str = Field(..., description="Eindeutige Schlüssel-ID")
    expires_at: datetime = Field(..., description="Ablaufzeitpunkt des Schlüssels")


class AuthPayload(ACPBaseModel):
    """Payload für Authentifizierung"""

    credentials: Dict[str, str] = Field(..., description="Authentifizierungsdaten")
    auth_method: str = Field(
        default="token", description="Authentifizierungsmethode", pattern=r"^(token|certificate|oauth|api_key)$"
    )
    session_id: Optional[str] = Field(default=None, description="Session-ID bei erfolgreicher Authentifizierung")
    permissions: List[str] = Field(default_factory=list, description="Gewährte Berechtigungen")
    expires_at: Optional[datetime] = Field(default=None, description="Ablaufzeitpunkt der Session")


# =============================================================================
# Response-Modelle
# =============================================================================


class MessageAcknowledgment(ACPBaseModel):
    """Bestätigung für empfangene Nachrichten"""

    message_id: str = Field(..., description="ID der bestätigten Nachricht")
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Empfangszeitpunkt")
    status: str = Field(
        default="received", description="Status der Bestätigung", pattern=r"^(received|processing|completed|failed)$"
    )
    error: Optional[str] = Field(default=None, description="Fehlermeldung")


class ValidationResult(ACPBaseModel):
    """Ergebnis einer Nachrichtenvalidierung"""

    is_valid: bool = Field(..., description="Ob die Nachricht gültig ist")
    errors: List[str] = Field(default_factory=list, description="Validierungsfehler")
    warnings: List[str] = Field(default_factory=list, description="Warnungen")
    message_hash: Optional[str] = Field(default=None, description="Hash der Nachricht")


# =============================================================================
# Backward Compatibility
# =============================================================================


class LegacyMessageConverter:
    """
    Konvertiert ACP v1.0 Nachrichten zu ACP v1.1

    ACP v1.0 verwendete ein einfaches Markdown-Format:
    ## [FROM-AGENT] → [TO-AGENT]
    **Task:** ...
    **Status:** ...
    """

    @staticmethod
    def parse_legacy_message(content: str) -> Dict[str, Any]:
        """Parst eine ACP v1.0 Nachricht"""
        import re

        result = {"sender": None, "recipient": None, "message_type": MessageType.MESSAGE, "content": {}}

        # Parse Header: ## [FROM] → [TO]
        header_match = re.search(r"##\s*\[([^\]]+)\]\s*→\s*\[([^\]]+)\]", content)
        if header_match:
            result["sender"] = {"name": header_match.group(1), "role": AgentRole.WORKER}
            result["recipient"] = {"name": header_match.group(2), "role": AgentRole.WORKER}

        # Parse Status-Emojis
        if "🆕" in content:
            result["message_type"] = MessageType.TASK_CREATE
        elif "🔄" in content:
            result["message_type"] = MessageType.STATUS_UPDATE
        elif "✅" in content:
            result["message_type"] = MessageType.TASK_COMPLETE
        elif "❌" in content:
            result["message_type"] = MessageType.ERROR

        # Parse Key-Value Paare
        kv_pattern = r"\*\*([^:]+):\*\*\s*(.+?)(?=\*\*|$)"
        for match in re.finditer(kv_pattern, content, re.DOTALL):
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            result["content"][key] = value

        # Parse Code-Blöcke
        code_pattern = r"```(\w+)?\n(.*?)```"
        code_blocks = re.findall(code_pattern, content, re.DOTALL)
        if code_blocks:
            result["content"]["code_blocks"] = [
                {"language": lang or "text", "code": code.strip()} for lang, code in code_blocks
            ]

        return result

    @staticmethod
    def convert_to_v1_1(legacy_content: str) -> ACPMessage:
        """Konvertiert eine ACP v1.0 Nachricht zu ACP v1.1"""
        parsed = LegacyMessageConverter.parse_legacy_message(legacy_content)

        sender = AgentIdentity(
            agent_id=parsed.get("sender", {}).get("name", "unknown").lower().replace(" ", "_"),
            role=parsed.get("sender", {}).get("role", AgentRole.WORKER),
            name=parsed.get("sender", {}).get("name", "Unknown"),
        )

        recipient = None
        if parsed.get("recipient"):
            recipient = AgentIdentity(
                agent_id=parsed["recipient"]["name"].lower().replace(" ", "_"),
                role=parsed["recipient"].get("role", AgentRole.WORKER),
                name=parsed["recipient"]["name"],
            )

        header = MessageHeader(message_type=parsed.get("message_type", MessageType.MESSAGE))

        payload = MessagePayload(data=parsed.get("content", {}))

        return ACPMessage(header=header, sender=sender, recipient=recipient, payload=payload)


# =============================================================================
# JSON Schema Export
# =============================================================================


def export_json_schemas(output_dir: str = ".") -> Dict[str, str]:
    """Exportiert alle JSON Schemas für die Modelle"""
    from pathlib import Path

    schemas = {
        "acp_message": ACPMessage.model_json_schema(),
        "message_header": MessageHeader.model_json_schema(),
        "agent_identity": AgentIdentity.model_json_schema(),
        "task_payload": TaskPayload.model_json_schema(),
        "status_payload": StatusPayload.model_json_schema(),
        "error_payload": ErrorPayload.model_json_schema(),
        "file_transfer_payload": FileTransferPayload.model_json_schema(),
        "data_request_payload": DataRequestPayload.model_json_schema(),
        "data_response_payload": DataResponsePayload.model_json_schema(),
        "key_exchange_payload": KeyExchangePayload.model_json_schema(),
        "auth_payload": AuthPayload.model_json_schema(),
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for name, schema in schemas.items():
        file_path = output_path / f"{name}_schema.json"
        with open(file_path, "w") as f:
            json.dump(schema, f, indent=2)

    return {name: str(output_path / f"{name}_schema.json") for name in schemas}


# =============================================================================
# Beispiel-Nutzung
# =============================================================================

if __name__ == "__main__":
    # Beispiel: Erstelle eine Task-Message
    sender = AgentIdentity(
        agent_id="cli_kimi_001", role=AgentRole.CLI_KIMI, name="CLI-Kimi", capabilities=["analysis", "planning", "review"]
    )

    recipient = AgentIdentity(
        agent_id="powershell_kimi_001",
        role=AgentRole.POWERSHELL_KIMI,
        name="PowerShell-Kimi",
        capabilities=["execution", "debugging", "windows"],
    )

    task_payload = TaskPayload(
        title="Fix Telegram Webhook",
        description="Der Telegram Webhook in GitHub Actions funktioniert nicht",
        instructions="""
        1. Analysiere den Fehler im Workflow
        2. Fix die Webhook URL
        3. Erstelle einen PR
        """,
        expected_result="PR erstellt mit dem Fix",
    )

    message = ACPMessage(
        header=MessageHeader(message_type=MessageType.TASK_CREATE, priority=MessagePriority.HIGH),
        sender=sender,
        recipient=recipient,
        payload=MessagePayload(data=task_payload.model_dump()),
        tags=["github-actions", "telegram", "webhook"],
    )

    print("ACP v1.1 Message Example:")
    print(message.model_dump_json(indent=2))

    # Exportiere Schemas
    schema_paths = export_json_schemas("/mnt/okcomputer/output/schemas")
    print("\nJSON Schemas exported to:")
    for name, path in schema_paths.items():
        print(f"  - {name}: {path}")
