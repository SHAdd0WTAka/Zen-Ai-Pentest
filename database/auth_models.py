"""
Auth Database Models
====================

Extended database models for the new authentication system.

Models:
- User: Extended user model with MFA support
- UserSession: Active sessions for token management
- APIKey: API key storage
- TokenBlacklist: Revoked tokens
- MFADevice: TOTP device storage
"""

import os
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class UserRole(str, PyEnum):
    """User roles aligned with auth.rbac.Role"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    USER = "user"
    VIEWER = "viewer"
    API_SERVICE = "api_service"


class TokenType(str, PyEnum):
    """Token types"""

    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class MFAType(str, PyEnum):
    """MFA types"""

    TOTP = "totp"
    BACKUP_CODES = "backup_codes"


class User(Base):
    """
    Extended User Model

    Supports:
    - Password authentication
    - MFA (TOTP)
    - Role-based access
    - Account status tracking
    """

    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Password
    hashed_password = Column(String(255), nullable=False)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    password_history = Column(JSON, default=list)  # Store last N password hashes

    # Role & Permissions
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    custom_permissions = Column(JSON, default=list)  # Additional permissions beyond role

    # Account Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verification
    is_mfa_enabled = Column(Boolean, default=False)

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("auth_users.id"), nullable=True)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    mfa_devices = relationship("MFADevice", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("UserAuditLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_mfa_enabled": self.is_mfa_enabled,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data["custom_permissions"] = self.custom_permissions
            data["failed_login_attempts"] = self.failed_login_attempts
        return data


class UserSession(Base):
    """
    User Session Model

    Tracks active sessions for:
    - Token refresh management
    - Session invalidation (logout)
    - Concurrent session limits
    - Audit trail
    """

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"), nullable=False, index=True)

    # Session identifiers
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token_jti = Column(String(255), unique=True, index=True, nullable=False)

    # Session metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSON, default=dict)  # Device fingerprinting

    # Status
    is_active = Column(Boolean, default=True)
    revoked = Column(Boolean, default=False)
    revoked_reason = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_sessions_user_active", "user_id", "is_active"),
        Index("idx_sessions_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    def is_expired(self):
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def touch(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.now(timezone.utc)


class APIKey(Base):
    """
    API Key Model

    Stores API keys for service-to-service authentication.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"), nullable=False, index=True)

    # Key data
    key_id = Column(String(100), unique=True, index=True, nullable=False)  # Public identifier
    key_hash = Column(String(255), nullable=False)  # Hashed key
    key_prefix = Column(String(20), nullable=False)  # First 8 chars for identification

    # Metadata
    name = Column(String(255), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)
    scopes = Column(JSON, default=list)  # Allowed scopes/permissions

    # Rate limiting
    rate_limit = Column(Integer, default=1000)  # Requests per hour

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Null = never expires

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_ip = Column(String(50), nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', active={self.is_active})>"

    def is_expired(self):
        """Check if API key is expired"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def record_usage(self):
        """Record API key usage"""
        self.use_count += 1
        self.last_used_at = datetime.now(timezone.utc)


class MFADevice(Base):
    """
    MFA Device Model

    Stores TOTP and backup code configurations.
    """

    __tablename__ = "mfa_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"), nullable=False, index=True)

    # Device info
    device_type = Column(Enum(MFAType), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "Google Authenticator"

    # TOTP data
    secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    backup_codes = Column(JSON, default=list)  # Hashed backup codes

    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Primary MFA device
    verified = Column(Boolean, default=False)  # Has been verified

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="mfa_devices")

    def __repr__(self):
        return f"<MFADevice(id={self.id}, type='{self.device_type.value}', active={self.is_active})>"


class TokenBlacklist(Base):
    """
    Token Blacklist Model

    Stores revoked tokens for immediate invalidation.
    """

    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)

    # Token info
    jti = Column(String(255), unique=True, index=True, nullable=False)
    token_type = Column(Enum(TokenType), nullable=False)

    # User reference (optional, for audit)
    user_id = Column(Integer, ForeignKey("auth_users.id"), nullable=True, index=True)

    # Reason
    reason = Column(String(100), default="logout")  # logout, compromise, expiry

    # Timestamps
    revoked_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # When token naturally expires

    __table_args__ = (Index("idx_blacklist_expires", "expires_at"),)

    def __repr__(self):
        return f"<TokenBlacklist(jti='{self.jti[:8]}...', reason='{self.reason}')>"


class UserAuditLog(Base):
    """
    User Audit Log Model

    Detailed audit trail for user actions.
    """

    __tablename__ = "user_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"), nullable=True, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)  # login, logout, password_change, etc.
    action_category = Column(String(50), nullable=True)  # auth, security, account

    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)

    # Details
    details = Column(JSON, default=dict)  # Additional context
    result = Column(String(50), nullable=True)  # success, failure, error
    failure_reason = Column(String(255), nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_timestamp", "timestamp"),
    )

    def __repr__(self):
        return f"<UserAuditLog(id={self.id}, action='{self.action}', result='{self.result}')>"


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

# Use same database as main models
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zen_pentest.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_auth_db():
    """Initialize auth database tables"""
    Base.metadata.create_all(bind=engine)


def get_auth_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# CRUD OPERATIONS
# ============================================================================


def create_user(db, username: str, email: str, hashed_password: str, role: UserRole = UserRole.USER):
    """Create new user"""
    user = User(username=username, email=email, hashed_password=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db, username: str):
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db, user_id: int):
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_session(
    db,
    user_id: int,
    session_id: str,
    refresh_token_jti: str,
    expires_at: datetime,
    ip_address: str = None,
    user_agent: str = None,
):
    """Create new user session"""
    session = UserSession(
        user_id=user_id,
        session_id=session_id,
        refresh_token_jti=refresh_token_jti,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_refresh_jti(db, refresh_token_jti: str):
    """Get session by refresh token JTI"""
    return db.query(UserSession).filter(UserSession.refresh_token_jti == refresh_token_jti, UserSession.is_active).first()


def revoke_session(db, session_id: str, reason: str = "logout"):
    """Revoke a session"""
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if session:
        session.is_active = False
        session.revoked = True
        session.revoked_reason = reason
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return session


def revoke_all_user_sessions(db, user_id: int, reason: str = "security"):
    """Revoke all sessions for a user"""
    sessions = db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.is_active).all()

    for session in sessions:
        session.is_active = False
        session.revoked = True
        session.revoked_reason = reason
        session.revoked_at = datetime.now(timezone.utc)

    db.commit()
    return len(sessions)


def blacklist_token(db, jti: str, token_type: TokenType, expires_at: datetime, user_id: int = None, reason: str = "logout"):
    """Add token to blacklist"""
    entry = TokenBlacklist(jti=jti, token_type=token_type, user_id=user_id, reason=reason, expires_at=expires_at)
    db.add(entry)
    db.commit()
    return entry


def is_token_blacklisted(db, jti: str):
    """Check if token is blacklisted"""
    return db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None


def create_audit_log(
    db,
    user_id: int = None,
    action: str = None,
    action_category: str = None,
    ip_address: str = None,
    user_agent: str = None,
    session_id: str = None,
    details: dict = None,
    result: str = None,
    failure_reason: str = None,
):
    """Create audit log entry"""
    log = UserAuditLog(
        user_id=user_id,
        action=action,
        action_category=action_category,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        details=details or {},
        result=result,
        failure_reason=failure_reason,
    )
    db.add(log)
    db.commit()
    return log


if __name__ == "__main__":
    init_auth_db()
    print("Auth database tables initialized")
