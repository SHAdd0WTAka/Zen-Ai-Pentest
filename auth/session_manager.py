"""
Session Management Module
=========================

Secure session management with:
- Session creation and validation
- Timeout handling
- Concurrent session limiting
- Session termination
- Activity tracking

Compliance: OWASP ASVS 2026 V3.2, V3.3
"""

import uuid
import hashlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from .config import get_config, SessionConfig


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"


@dataclass
class Session:
    """Session data structure"""
    id: str
    user_id: str
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    absolute_expires_at: datetime
    status: SessionStatus
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None
    mfa_verified: bool = False
    metadata: Dict = field(default_factory=dict)


class SessionError(Exception):
    """Base session error"""
    pass


class SessionNotFoundError(SessionError):
    """Session not found"""
    pass


class SessionExpiredError(SessionError):
    """Session has expired"""
    pass


class SessionLimitExceededError(SessionError):
    """Maximum number of sessions exceeded"""
    pass


class SessionManager:
    """
    Session Manager
    
    Manages user sessions with:
    - Session lifecycle
    - Timeout handling
    - Concurrent session limits
    - Activity tracking
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or get_config().session
        self._sessions: Dict[str, Session] = {}  # session_id -> Session
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
    
    def create_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None,
        mfa_verified: bool = False,
        metadata: Optional[Dict] = None
    ) -> Session:
        """
        Create a new session for a user
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            device_info: Device information
            mfa_verified: Whether MFA was verified
            metadata: Additional metadata
            
        Returns:
            New session object
            
        Raises:
            SessionLimitExceededError: If user has too many sessions
        """
        # Check session limit
        user_session_count = len(self._user_sessions.get(user_id, set()))
        if user_session_count >= self.config.max_sessions_per_user:
            # Remove oldest session
            self._remove_oldest_session(user_id)
        
        now = datetime.now(timezone.utc)
        
        # Create session
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(minutes=self.config.session_timeout_minutes),
            absolute_expires_at=now + timedelta(hours=self.config.absolute_timeout_hours),
            status=SessionStatus.ACTIVE,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            mfa_verified=mfa_verified,
            metadata=metadata or {},
        )
        
        # Store session
        self._sessions[session.id] = session
        
        # Add to user's sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(session.id)
        
        return session
    
    def validate_session(self, session_id: str) -> Optional[Session]:
        """
        Validate a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session if valid, None otherwise
            
        Raises:
            SessionExpiredError: If session has expired
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        now = datetime.now(timezone.utc)
        
        # Check if terminated
        if session.status == SessionStatus.TERMINATED:
            return None
        
        # Check absolute timeout
        if now > session.absolute_expires_at:
            session.status = SessionStatus.EXPIRED
            raise SessionExpiredError("Session has exceeded absolute timeout")
        
        # Check idle timeout
        if now > session.expires_at:
            session.status = SessionStatus.EXPIRED
            raise SessionExpiredError("Session has expired due to inactivity")
        
        return session
    
    def update_activity(self, session_id: str) -> bool:
        """
        Update session last activity time
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was updated
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if session.status != SessionStatus.ACTIVE:
            return False
        
        now = datetime.now(timezone.utc)
        session.last_activity_at = now
        session.expires_at = now + timedelta(minutes=self.config.session_timeout_minutes)
        
        return True
    
    def terminate_session(self, session_id: str, reason: str = "logout") -> bool:
        """
        Terminate a session
        
        Args:
            session_id: Session identifier
            reason: Reason for termination
            
        Returns:
            True if session was terminated
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.TERMINATED
        session.metadata["terminated_at"] = datetime.now(timezone.utc).isoformat()
        session.metadata["termination_reason"] = reason
        
        return True
    
    def terminate_all_user_sessions(
        self,
        user_id: str,
        exclude_session_id: Optional[str] = None,
        reason: str = "security"
    ) -> int:
        """
        Terminate all sessions for a user
        
        Args:
            user_id: User identifier
            exclude_session_id: Optional session ID to exclude
            reason: Reason for termination
            
        Returns:
            Number of sessions terminated
        """
        count = 0
        for session_id in self._user_sessions.get(user_id, set()):
            if exclude_session_id and session_id == exclude_session_id:
                continue
            
            if self.terminate_session(session_id, reason):
                count += 1
        
        return count
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session or None
        """
        return self._sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of sessions
        """
        sessions = []
        for session_id in self._user_sessions.get(user_id, set()):
            session = self._sessions.get(session_id)
            if session:
                sessions.append(session)
        
        return sorted(sessions, key=lambda s: s.last_activity_at, reverse=True)
    
    def get_active_sessions(self, user_id: str) -> List[Session]:
        """
        Get active sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active sessions
        """
        return [s for s in self.get_user_sessions(user_id) if s.status == SessionStatus.ACTIVE]
    
    def _remove_oldest_session(self, user_id: str) -> bool:
        """
        Remove the oldest session for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            True if a session was removed
        """
        sessions = self.get_user_sessions(user_id)
        if not sessions:
            return False
        
        # Find oldest session
        oldest = min(sessions, key=lambda s: s.last_activity_at)
        
        # Terminate it
        return self.terminate_session(oldest.id, "session_limit")
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now(timezone.utc)
        count = 0
        
        for session in list(self._sessions.values()):
            if session.status == SessionStatus.ACTIVE:
                if now > session.absolute_expires_at or now > session.expires_at:
                    session.status = SessionStatus.EXPIRED
                    count += 1
        
        return count
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session information (safe for display)
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information dictionary
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            "id": session.id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "status": session.status.value,
            "ip_address": self._mask_ip(session.ip_address),
            "user_agent": session.user_agent,
            "device_info": session.device_info,
            "mfa_verified": session.mfa_verified,
        }
    
    def _mask_ip(self, ip: Optional[str]) -> Optional[str]:
        """Mask IP address for privacy"""
        if not ip:
            return None
        
        # For IPv4
        if '.' in ip:
            parts = ip.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.*.*"
        
        # For IPv6
        if ':' in ip:
            parts = ip.split(':')
            if len(parts) >= 4:
                return ':'.join(parts[:2]) + ":*"
        
        return ip
    
    def is_session_valid(self, session_id: str) -> bool:
        """
        Quick check if session is valid
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is valid
        """
        try:
            session = self.validate_session(session_id)
            return session is not None
        except SessionExpiredError:
            return False
    
    def get_session_count(self, user_id: str) -> int:
        """
        Get number of sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions
        """
        return len(self._user_sessions.get(user_id, set()))
    
    def get_active_session_count(self, user_id: str) -> int:
        """
        Get number of active sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of active sessions
        """
        return len(self.get_active_sessions(user_id))
    
    def suspend_session(self, session_id: str) -> bool:
        """
        Suspend a session (temporary disable)
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was suspended
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if session.status == SessionStatus.ACTIVE:
            session.status = SessionStatus.SUSPENDED
            return True
        
        return False
    
    def reactivate_session(self, session_id: str) -> bool:
        """
        Reactivate a suspended session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was reactivated
        """
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if session.status == SessionStatus.SUSPENDED:
            # Check if not expired
            now = datetime.now(timezone.utc)
            if now > session.absolute_expires_at or now > session.expires_at:
                session.status = SessionStatus.EXPIRED
                return False
            
            session.status = SessionStatus.ACTIVE
            return True
        
        return False


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get singleton session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
