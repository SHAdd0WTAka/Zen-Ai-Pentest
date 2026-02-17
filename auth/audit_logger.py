"""
Audit Logging Module
====================

Comprehensive audit logging for security events with:
- Structured logging
- Sensitive data masking
- Log rotation
- Tamper resistance

Compliance: OWASP ASVS 2026 V7.1, ISO 27001 A.12.4
"""

import json
import hashlib
import logging
import logging.handlers
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
import threading
import os

from .config import get_config, AuditConfig


class AuditEventType(Enum):
    """Audit event types"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    
    # Registration events
    USER_REGISTERED = "user_registered"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # MFA events
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"
    MFA_BACKUP_USED = "mfa_backup_used"
    
    # Password events
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    
    # API key events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_USED = "api_key_used"
    
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"
    SESSION_EXPIRED = "session_expired"
    
    # RBAC events
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCESS_DENIED = "access_denied"
    
    # Configuration events
    CONFIG_CHANGED = "config_changed"


class AuditSeverity(Enum):
    """Audit event severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    severity: AuditSeverity
    message: str
    details: Dict[str, Any]
    event_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "event_hash": self.event_hash,
        }


class AuditLogger:
    """
    Audit Logger
    
    Provides comprehensive security audit logging with:
    - Structured JSON logs
    - Sensitive data masking
    - Log rotation
    - Chain hashing for tamper detection
    """
    
    def __init__(self, config: Optional[AuditConfig] = None):
        self.config = config or get_config().audit
        self._logger = self._setup_logger()
        self._previous_hash: Optional[str] = None
        self._lock = threading.Lock()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup the audit logger"""
        logger = logging.getLogger("zen_audit")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        
        # File handler with rotation
        if self.config.log_file_path:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config.log_file_path), exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                self.config.log_file_path,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Console handler
        if self.config.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive fields in data
        
        Args:
            data: Data dictionary
            
        Returns:
            Masked data dictionary
        """
        masked = {}
        
        for key, value in data.items():
            # Check if field is sensitive
            is_sensitive = any(
                sensitive in key.lower()
                for sensitive in self.config.sensitive_fields
            )
            
            if is_sensitive:
                if isinstance(value, str):
                    if len(value) > 8:
                        masked[key] = value[:4] + "****" + value[-4:]
                    else:
                        masked[key] = "****"
                else:
                    masked[key] = "[REDACTED]"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        
        return masked
    
    def _calculate_hash(self, event: AuditEvent) -> str:
        """
        Calculate event hash for tamper detection
        
        Args:
            event: Audit event
            
        Returns:
            Hash string
        """
        # Create hash data
        hash_data = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "session_id": event.session_id,
            "message": event.message,
            "details": event.details,
            "previous_hash": self._previous_hash,
        }
        
        # Calculate hash
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def log_event(
        self,
        event_type: AuditEventType,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            message: Event message
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            severity: Event severity
            details: Additional details
            
        Returns:
            Logged audit event
        """
        with self._lock:
            # Mask sensitive data
            masked_details = self._mask_sensitive_data(details or {})
            
            # Create event
            event = AuditEvent(
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                message=message,
                details=masked_details,
            )
            
            # Calculate hash
            event.event_hash = self._calculate_hash(event)
            self._previous_hash = event.event_hash
            
            # Log event
            self._logger.info(json.dumps(event.to_dict()))
            
            return event
    
    def log_login_success(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        mfa_used: bool = False,
    ) -> AuditEvent:
        """Log successful login"""
        return self.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            message="User logged in successfully",
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.INFO,
            details={"mfa_used": mfa_used},
        )
    
    def log_login_failure(
        self,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: str = "invalid_credentials",
    ) -> AuditEvent:
        """Log failed login"""
        return self.log_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            message=f"Login failed: {reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            severity=AuditSeverity.WARNING,
            details={"username": username, "reason": reason},
        )
    
    def log_logout(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log logout"""
        return self.log_event(
            event_type=AuditEventType.LOGOUT,
            message="User logged out",
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
        )
    
    def log_mfa_enabled(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log MFA enabled"""
        return self.log_event(
            event_type=AuditEventType.MFA_ENABLED,
            message="MFA enabled for user",
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
        )
    
    def log_mfa_disabled(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        reason: str = "user_request",
    ) -> AuditEvent:
        """Log MFA disabled"""
        return self.log_event(
            event_type=AuditEventType.MFA_DISABLED,
            message=f"MFA disabled: {reason}",
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditSeverity.WARNING,
            details={"reason": reason},
        )
    
    def log_password_changed(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditEvent:
        """Log password change"""
        return self.log_event(
            event_type=AuditEventType.PASSWORD_CHANGED,
            message="User changed password",
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
        )
    
    def log_api_key_created(
        self,
        user_id: str,
        key_id: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log API key creation"""
        return self.log_event(
            event_type=AuditEventType.API_KEY_CREATED,
            message="API key created",
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
            details={"key_id": key_id},
        )
    
    def log_api_key_revoked(
        self,
        user_id: str,
        key_id: str,
        ip_address: Optional[str] = None,
        reason: str = "user_request",
    ) -> AuditEvent:
        """Log API key revocation"""
        return self.log_event(
            event_type=AuditEventType.API_KEY_REVOKED,
            message=f"API key revoked: {reason}",
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
            details={"key_id": key_id, "reason": reason},
        )
    
    def log_rate_limit_exceeded(
        self,
        identifier: str,
        limit_type: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log rate limit exceeded"""
        return self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded: {limit_type}",
            ip_address=ip_address,
            severity=AuditSeverity.WARNING,
            details={"identifier": identifier, "limit_type": limit_type},
        )
    
    def log_access_denied(
        self,
        user_id: str,
        resource: str,
        permission: str,
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log access denied"""
        return self.log_event(
            event_type=AuditEventType.ACCESS_DENIED,
            message=f"Access denied to {resource}",
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditSeverity.WARNING,
            details={"resource": resource, "permission": permission},
        )
    
    def log_suspicious_activity(
        self,
        message: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> AuditEvent:
        """Log suspicious activity"""
        return self.log_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            severity=AuditSeverity.ERROR,
            details=details or {},
        )
    
    def log_role_change(
        self,
        admin_id: str,
        target_user_id: str,
        role: str,
        action: str,  # "assigned" or "revoked"
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log role change"""
        event_type = (
            AuditEventType.ROLE_ASSIGNED
            if action == "assigned"
            else AuditEventType.ROLE_REVOKED
        )
        
        return self.log_event(
            event_type=event_type,
            message=f"Role {action}: {role}",
            user_id=admin_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
            details={"target_user_id": target_user_id, "role": role},
        )
    
    def log_session_terminated(
        self,
        user_id: str,
        session_id: str,
        reason: str = "logout",
        ip_address: Optional[str] = None,
    ) -> AuditEvent:
        """Log session termination"""
        return self.log_event(
            event_type=AuditEventType.SESSION_TERMINATED,
            message=f"Session terminated: {reason}",
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            severity=AuditSeverity.INFO,
            details={"reason": reason},
        )
    
    def verify_log_integrity(self, log_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify log file integrity using chain hashing
        
        Args:
            log_file_path: Path to log file (uses config default if not specified)
            
        Returns:
            Verification result
        """
        log_file = log_file_path or self.config.log_file_path
        
        if not log_file or not os.path.exists(log_file):
            return {"valid": False, "error": "Log file not found"}
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            previous_hash = None
            invalid_entries = []
            
            for i, line in enumerate(lines):
                try:
                    event_data = json.loads(line.strip())
                    stored_hash = event_data.pop("event_hash", None)
                    
                    # Recalculate hash
                    hash_data = {
                        **event_data,
                        "previous_hash": previous_hash,
                    }
                    hash_string = json.dumps(hash_data, sort_keys=True)
                    calculated_hash = hashlib.sha256(hash_string.encode()).hexdigest()
                    
                    if calculated_hash != stored_hash:
                        invalid_entries.append({
                            "line": i + 1,
                            "expected": calculated_hash,
                            "stored": stored_hash,
                        })
                    
                    previous_hash = stored_hash
                    
                except json.JSONDecodeError:
                    invalid_entries.append({"line": i + 1, "error": "Invalid JSON"})
            
            return {
                "valid": len(invalid_entries) == 0,
                "total_entries": len(lines),
                "invalid_entries": invalid_entries,
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get singleton audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
