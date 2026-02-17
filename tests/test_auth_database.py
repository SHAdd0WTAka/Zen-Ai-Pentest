"""
Auth Database Layer Tests
=========================

Tests for the database-backed authentication system.
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

# Set up environment
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt-32-bytes!"
os.environ["DATABASE_URL"] = "sqlite:///./test_auth_db.db"

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from auth.jwt_handler import JWTHandler
from auth.password_hasher import PasswordHasher
from auth.user_manager import UserManager
from database.auth_models import (
    APIKey,
    Base,
    MFADevice,
    TokenBlacklist,
    TokenType,
    User,
    UserAuditLog,
    UserRole,
    UserSession,
    blacklist_token,
    create_session,
    create_user,
    get_user_by_email,
    get_user_by_username,
    is_token_blacklisted,
    revoke_session,
)

# Create test database
engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_manager():
    """Create UserManager instance"""
    jwt_handler = JWTHandler()
    pwd_hasher = PasswordHasher()
    return UserManager(jwt_handler, pwd_hasher)


class TestUserModel:
    """Test User database model"""

    def test_create_user(self, db):
        """Test creating a user"""
        user = User(username="testuser", email="test@example.com", hashed_password="hashed_password_here", role=UserRole.USER)
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_to_dict(self, db):
        """Test user serialization"""
        user = User(username="testuser", email="test@example.com", hashed_password="hashed", role=UserRole.ADMIN)
        db.add(user)
        db.commit()

        data = user.to_dict()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "password" not in data  # Sensitive data excluded

    def test_get_user_by_username(self, db):
        """Test retrieving user by username"""
        create_user(db, "testuser", "test@example.com", "hashed_pass_hash", UserRole.USER)

        user = get_user_by_username(db, "testuser")
        assert user is not None
        assert user.username == "testuser"

    def test_get_user_by_email(self, db):
        """Test retrieving user by email"""
        create_user(db, "testuser", "test@example.com", "hashed_pass_hash", UserRole.USER)

        user = get_user_by_email(db, "test@example.com")
        assert user is not None
        assert user.email == "test@example.com"


class TestUserSession:
    """Test UserSession database model"""

    def test_create_session(self, db):
        """Test creating a user session"""
        user = create_user(db, "testuser", "test@example.com", "hashed", UserRole.USER)

        session = create_session(
            db,
            user.id,
            "session_123",
            "jti_456",
            datetime.utcnow() + timedelta(days=7),
            ip_address="192.168.1.1",
            user_agent="TestAgent",
        )

        assert session.id is not None
        assert session.session_id == "session_123"
        assert session.user_id == user.id
        assert session.is_active is True

    def test_session_expiration(self, db):
        """Test session expiration check"""
        user = create_user(db, "testuser", "test@example.com", "hashed", UserRole.USER)

        # Create expired session
        expired_session = create_session(
            db,
            user.id,
            "expired_session",
            "jti_expired",
            datetime.utcnow() - timedelta(days=1),  # Expired
            ip_address="192.168.1.1",
        )

        assert expired_session.is_expired() is True

        # Create active session
        active_session = create_session(
            db, user.id, "active_session", "jti_active", datetime.utcnow() + timedelta(days=7), ip_address="192.168.1.1"
        )

        assert active_session.is_expired() is False

    def test_revoke_session(self, db):
        """Test revoking a session"""
        user = create_user(db, "testuser", "test@example.com", "hashed", UserRole.USER)
        session = create_session(db, user.id, "session_123", "jti_456", datetime.utcnow() + timedelta(days=7))

        revoked = revoke_session(db, "session_123", "logout")

        assert revoked is not None
        assert revoked.is_active is False
        assert revoked.revoked is True
        assert revoked.revoked_reason == "logout"


class TestTokenBlacklist:
    """Test TokenBlacklist database model"""

    def test_blacklist_token(self, db):
        """Test adding token to blacklist"""
        user = create_user(db, "testuser", "test@example.com", "hashed", UserRole.USER)

        entry = blacklist_token(db, "jti_123", TokenType.ACCESS, datetime.utcnow() + timedelta(minutes=15), user.id, "logout")

        assert entry.id is not None
        assert entry.jti == "jti_123"
        assert entry.token_type == TokenType.ACCESS
        assert entry.reason == "logout"

    def test_is_token_blacklisted(self, db):
        """Test checking if token is blacklisted"""
        user = create_user(db, "testuser", "test@example.com", "hashed", UserRole.USER)

        # Initially not blacklisted
        assert is_token_blacklisted(db, "jti_123") is False

        # Add to blacklist
        blacklist_token(db, "jti_123", TokenType.ACCESS, datetime.utcnow() + timedelta(minutes=15), user.id, "logout")

        # Now blacklisted
        assert is_token_blacklisted(db, "jti_123") is True


class TestUserManager:
    """Test UserManager with database"""

    def test_authenticate_user_success(self, db, user_manager):
        """Test successful authentication"""
        # Create user with hashed password
        password = "securepassword123"
        hashed = user_manager.pwd.hash(password)
        user = create_user(db, "testuser", "test@example.com", hashed, UserRole.USER)

        # Authenticate
        auth_user = user_manager.authenticate_user(db, "testuser", password)

        assert auth_user is not None
        assert auth_user.id == user.id
        assert auth_user.last_login_at is not None

    def test_authenticate_user_wrong_password(self, db, user_manager):
        """Test authentication with wrong password"""
        password = "securepassword123"
        hashed = user_manager.pwd.hash(password)
        create_user(db, "testuser", "test@example.com", hashed, UserRole.USER)

        # Try wrong password
        auth_user = user_manager.authenticate_user(db, "testuser", "wrongpassword")

        assert auth_user is None

    def test_authenticate_user_not_found(self, db, user_manager):
        """Test authentication for non-existent user"""
        auth_user = user_manager.authenticate_user(db, "nonexistent", "password")
        assert auth_user is None

    def test_create_session_with_tokens(self, db, user_manager):
        """Test creating session with JWT tokens"""
        password = "securepassword123"
        hashed = user_manager.pwd.hash(password)
        user = create_user(db, "testuser", "test@example.com", hashed, UserRole.USER)

        # Create session
        result = user_manager.create_session(db, user, "192.168.1.1", "TestAgent")

        assert "access_token" in result
        assert "refresh_token" in result
        assert "session_id" in result
        assert result["token_type"] == "bearer"

        # Verify session was stored in DB
        session = db.query(UserSession).filter(UserSession.session_id == result["session_id"]).first()

        assert session is not None
        assert session.user_id == user.id
        assert session.is_active is True

    def test_refresh_session(self, db, user_manager):
        """Test refreshing access token"""
        password = "securepassword123"
        hashed = user_manager.pwd.hash(password)
        user = create_user(db, "testuser", "test@example.com", hashed, UserRole.USER)

        # Create initial session
        session_data = user_manager.create_session(db, user)
        refresh_token = session_data["refresh_token"]

        # Refresh
        result = user_manager.refresh_session(db, refresh_token)

        assert result is not None
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_revoke_all_user_sessions(self, db, user_manager):
        """Test revoking all user sessions"""
        password = "securepassword123"
        hashed = user_manager.pwd.hash(password)
        user = create_user(db, "testuser", "test@example.com", hashed, UserRole.USER)

        # Create multiple sessions
        user_manager.create_session(db, user, "192.168.1.1")
        user_manager.create_session(db, user, "192.168.1.2")
        user_manager.create_session(db, user, "192.168.1.3")

        # Revoke all
        count = user_manager.revoke_all_user_sessions(db, user.id, "security")

        assert count == 3

        # Check all revoked
        active_sessions = db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.is_active == True).count()

        assert active_sessions == 0

    def test_change_password(self, db, user_manager):
        """Test password change"""
        old_password = "oldpassword123"
        hashed = user_manager.pwd.hash(old_password)
        user = create_user(db, "testuser", "test@example.com", hashed, UserRole.USER)

        # Change password
        new_password = "newpassword123"
        result = user_manager.change_password(db, user.id, old_password, new_password)

        assert result is True

        # Verify old password no longer works
        auth_user = user_manager.authenticate_user(db, "testuser", old_password)
        assert auth_user is None

        # Verify new password works
        auth_user = user_manager.authenticate_user(db, "testuser", new_password)
        assert auth_user is not None


class TestUserAuditLog:
    """Test audit logging"""

    def test_create_audit_log(self, db, user_manager):
        """Test creating audit log entries"""
        user = create_user(db, "testuser", "test@example.com", "hashed", UserRole.USER)

        # Authenticate to generate audit log
        user_manager.authenticate_user(db, "testuser", "wrongpassword")

        # Check audit log
        logs = db.query(UserAuditLog).filter(UserAuditLog.user_id == user.id).all()

        assert len(logs) >= 1
        assert logs[0].action == "login"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
