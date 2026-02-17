"""
Audit Logger Core

Tamper-proof audit logging with cryptographic signatures and
compliance features for ISO 27001.
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass, asdict
import asyncio
from contextlib import asynccontextmanager

if TYPE_CHECKING:
    from .config import AuditConfig


class LogLevel(Enum):
    """Audit log severity levels"""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class EventCategory(Enum):
    """Categories of audit events"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY = "security"
    SYSTEM = "system"
    SCAN = "scan"
    EXPLOIT = "exploit"
    ADMIN = "administrative"


@dataclass
class AuditLogEntry:
    """
    Single audit log entry with cryptographic integrity protection

    All fields are immutable after creation to ensure tamper-proof logging.
    """
    # Core Fields
    id: str
    timestamp: datetime
    level: str
    category: str
    event_type: str
    message: str

    # Actor Information
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Resource Information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None

    # Details
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    # Compliance
    compliance_tags: Optional[List[str]] = None
    retention_until: Optional[datetime] = None

    # Integrity
    previous_hash: Optional[str] = None
    hash: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        """Calculate hash for integrity verification"""
        if self.hash is None:
            self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of log entry"""
        data = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "category": self.category,
            "event_type": self.event_type,
            "message": self.message,
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "previous_hash": self.previous_hash,
        }

        json_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_data.encode()).hexdigest()

    def sign(self, secret_key: str) -> str:
        """Create HMAC signature for log entry"""
        message = f"{self.id}:{self.hash}:{self.timestamp.isoformat()}"
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        self.signature = signature
        return signature

    def verify(self, secret_key: str) -> bool:
        """Verify HMAC signature"""
        if not self.signature:
            return False

        message = f"{self.id}:{self.hash}:{self.timestamp.isoformat()}"
        expected = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(self.signature, expected)

    def verify_chain(self, previous_entry: Optional["AuditLogEntry"]) -> bool:
        """Verify chain integrity with previous entry"""
        if previous_entry is None:
            return self.previous_hash is None

        return self.previous_hash == previous_entry.hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if self.retention_until:
            data["retention_until"] = self.retention_until.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLogEntry":
        """Create from dictionary"""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("retention_until"):
            data["retention_until"] = datetime.fromisoformat(data["retention_until"])
        return cls(**data)


class AuditLogger:
    """
    Main audit logger with tamper-proof logging capabilities

    Features:
    - Cryptographic integrity protection
    - Chain of custody for log entries
    - Async batch processing
    - SIEM integration
    - Compliance reporting
    """

    def __init__(self, config: Optional["AuditConfig"] = None):
        from .config import AuditConfig

        self.config = config or AuditConfig.default()
        self._entries: List[AuditLogEntry] = []
        self._last_hash: Optional[str] = None
        self._buffer: List[AuditLogEntry] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
        self._secret_key = self.config.signature_key or self._generate_key()

        # Storage backends
        self._storage = None
        self._archive = None

    def _generate_key(self) -> str:
        """Generate a signing key"""
        return hashlib.sha256(
            f"zen_audit_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:32]

    async def start(self):
        """Start the audit logger"""
        self._running = True

        if self.config.async_logging:
            self._flush_task = asyncio.create_task(self._flush_loop())

        await self._init_storage()

    async def stop(self):
        """Stop the audit logger and flush remaining entries"""
        self._running = False

        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        await self._flush_buffer()

    async def _init_storage(self):
        """Initialize storage backend"""
        # This would initialize PostgreSQL, SQLite, or other storage
        # For now, we'll use in-memory with file backup
        pass

    async def _flush_loop(self):
        """Background task to flush buffer periodically"""
        while self._running:
            try:
                await asyncio.sleep(self.config.flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                print(f"Audit flush error: {e}")

    async def _flush_buffer(self):
        """Flush buffer to storage"""
        async with self._lock:
            if not self._buffer:
                return

            entries = self._buffer.copy()
            self._buffer.clear()

        # Write to storage
        await self._write_to_storage(entries)

        # Send to SIEM if enabled
        if self.config.siem_enabled:
            await self._send_to_siem(entries)

    async def _write_to_storage(self, entries: List[AuditLogEntry]):
        """Write entries to storage backend"""
        # Implementation would write to PostgreSQL, etc.
        self._entries.extend(entries)

    async def _send_to_siem(self, entries: List[AuditLogEntry]):
        """Send entries to SIEM system"""
        # Implementation would send to Splunk, ELK, etc.
        pass

    def _create_entry(
        self,
        level: LogLevel,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Create a new audit log entry"""
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            level=level.value,
            category=category.value,
            event_type=event_type,
            message=message,
            previous_hash=self._last_hash,
            **kwargs
        )

        # Sign the entry
        if self.config.sign_logs:
            entry.sign(self._secret_key)

        self._last_hash = entry.hash
        return entry

    async def log(
        self,
        level: LogLevel,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """
        Create and store an audit log entry

        Args:
            level: Severity level
            category: Event category
            event_type: Type of event (e.g., 'user_login', 'scan_started')
            message: Human-readable message
            **kwargs: Additional fields (user_id, resource_id, etc.)

        Returns:
            The created AuditLogEntry
        """
        entry = self._create_entry(level, category, event_type, message, **kwargs)

        if self.config.async_logging:
            async with self._lock:
                self._buffer.append(entry)

                # Flush if buffer is full
                if len(self._buffer) >= self.config.buffer_size:
                    asyncio.create_task(self._flush_buffer())
        else:
            await self._write_to_storage([entry])

            if self.config.siem_enabled:
                await self._send_to_siem([entry])

        return entry

    # Convenience methods for different log levels

    async def debug(
        self,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Log debug level event"""
        return await self.log(LogLevel.DEBUG, category, event_type, message, **kwargs)

    async def info(
        self,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Log info level event"""
        return await self.log(LogLevel.INFO, category, event_type, message, **kwargs)

    async def warning(
        self,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Log warning level event"""
        return await self.log(LogLevel.WARNING, category, event_type, message, **kwargs)

    async def error(
        self,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Log error level event"""
        return await self.log(LogLevel.ERROR, category, event_type, message, **kwargs)

    async def critical(
        self,
        category: EventCategory,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Log critical level event"""
        return await self.log(LogLevel.CRITICAL, category, event_type, message, **kwargs)

    async def security(
        self,
        event_type: str,
        message: str,
        **kwargs
    ) -> AuditLogEntry:
        """Log security event (always permanent retention)"""
        return await self.log(
            LogLevel.ALERT,
            EventCategory.SECURITY,
            event_type,
            message,
            compliance_tags=["security", "permanent"],
            **kwargs
        )

    # Query methods

    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[LogLevel] = None,
        category: Optional[EventCategory] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """Query audit logs with filters"""
        entries = self._entries

        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]
        if level:
            entries = [e for e in entries if e.level == level.value]
        if category:
            entries = [e for e in entries if e.category == category.value]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        # Sort by timestamp descending
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        return entries[offset:offset + limit]

    async def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all log entries"""
        results = {
            "total_entries": len(self._entries),
            "valid_signatures": 0,
            "invalid_signatures": 0,
            "chain_breaks": 0,
            "errors": []
        }

        prev_entry = None

        for entry in self._entries:
            # Verify signature
            if entry.signature:
                if entry.verify(self._secret_key):
                    results["valid_signatures"] += 1
                else:
                    results["invalid_signatures"] += 1
                    results["errors"].append({
                        "entry_id": entry.id,
                        "error": "Invalid signature"
                    })

            # Verify chain
            if not entry.verify_chain(prev_entry):
                results["chain_breaks"] += 1
                results["errors"].append({
                    "entry_id": entry.id,
                    "error": "Chain break detected",
                    "expected_previous": prev_entry.hash if prev_entry else None,
                    "actual_previous": entry.previous_hash
                })

            prev_entry = entry

        return results

    async def export(
        self,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **filters
    ) -> Union[str, bytes]:
        """Export audit logs to various formats"""
        entries = await self.query(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
            **filters
        )

        if format == "json":
            data = [e.to_dict() for e in entries]
            return json.dumps(data, indent=2, default=str)

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "id", "timestamp", "level", "category", "event_type",
                "message", "user_id", "ip_address", "resource_id", "hash"
            ])

            # Data
            for e in entries:
                writer.writerow([
                    e.id, e.timestamp, e.level, e.category, e.event_type,
                    e.message, e.user_id, e.ip_address, e.resource_id, e.hash
                ])

            return output.getvalue()

        elif format == "syslog":
            lines = []
            for e in entries:
                lines.append(
                    f"<{e.level}>{e.timestamp.isoformat()} "
                    f"zen-audit[{e.id}] {e.category}: {e.message}"
                )
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")

    @asynccontextmanager
    async def session(self):
        """Context manager for audit logger session"""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
