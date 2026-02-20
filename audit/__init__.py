"""
Audit Logging System for Zen-AI-Pentest

ISO 27001 compliant audit logging with:
- Tamper-proof log entries
- SIEM integration
- Compliance reporting
- Real-time alerting
"""

from .compliance import ComplianceReporter
from .config import AuditConfig, LogLevel
from .logger import AuditLogEntry, AuditLogger
from .siem import SIEMIntegration

__all__ = [
    "AuditLogger",
    "AuditLogEntry",
    "AuditConfig",
    "LogLevel",
    "SIEMIntegration",
    "ComplianceReporter",
]

__version__ = "1.0.0"
