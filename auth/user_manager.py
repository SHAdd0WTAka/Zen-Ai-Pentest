"""
User Manager
============

Database-backed user management for the authentication system.

Features:
- User CRUD operations
- Session management
- Token blacklisting in database
- Audit logging
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.auth_models import TokenBlacklist
from database.auth_models import TokenType as DBTokenType
from database.auth_models import User, UserAuditLog, UserRole, UserSession

from .jwt_handler import JWTHandler, TokenType
from .password_hasher import PasswordHasher


class UserManager:
    """
    Database-backed user manager.

    Handles all user-related database operations including:
    - User authentication
    - Session management
    - Token blacklisting
    - Audit logging
    """

    def __init__(
        self,
        jwt_handler: Optional[JWTHandler] = None,
        password_hasher: Optional[PasswordHasher] = None,
    ):
        self.jwt = jwt_handler or JWTHandler()
        self.pwd = password_hasher or PasswordHasher()

    # ========================================================================
    # User Authentication
    # ========================================================================

    def authenticate_user(
        self,
        db: Session,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            db: Database session
            username: Username or email
            password: Plain text password
            ip_address: Client IP for audit
            user_agent: Client user agent for audit

        Returns:
            User object if authenticated, None otherwise
        """
        # Find user by username or email
        user = (
            db.query(User)
            .filter((User.username == username) | (User.email == username))
            .first()
        )

        if not user:
            # Log failed login attempt
            self._log_audit(
                db,
                None,
                "login",
                "auth",
                ip_address,
                user_agent,
                result="failure",
                failure_reason="user_not_found",
            )
            return None

        # Check if account is locked
        if (
            user.locked_until
            and datetime.now(timezone.utc) < user.locked_until
        ):
            self._log_audit(
                db,
                user.id,
                "login",
                "auth",
                ip_address,
                user_agent,
                result="failure",
                failure_reason="account_locked",
            )
            return None

        # Check if account is active
        if not user.is_active:
            self._log_audit(
                db,
                user.id,
                "login",
                "auth",
                ip_address,
                user_agent,
                result="failure",
                failure_reason="account_inactive",
            )
            return None

        # Verify password
        if not self.pwd.verify(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1

            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=30
                )

            db.commit()

            self._log_audit(
                db,
                user.id,
                "login",
                "auth",
                ip_address,
                user_agent,
                result="failure",
                failure_reason="invalid_password",
                details={"failed_attempts": user.failed_login_attempts},
            )
            return None

        # Successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        db.commit()

        self._log_audit(
            db,
            user.id,
            "login",
            "auth",
            ip_address,
            user_agent,
            result="success",
        )

        return user

    def create_user(
        self,
        db: Session,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
        created_by: int = None,
    ) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            username: Unique username
            email: Unique email
            password: Plain text password
            role: User role
            created_by: ID of user creating this account

        Returns:
            Created User object
        """
        # Hash password
        hashed = self.pwd.hash(password)

        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=hashed,
            role=role,
            created_by=created_by,
            password_changed_at=datetime.now(timezone.utc),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Log creation
        self._log_audit(
            db,
            created_by,
            "user_create",
            "account",
            details={"created_user_id": user.id, "role": role.value},
        )

        return user

    def change_password(
        self,
        db: Session,
        user_id: int,
        old_password: str,
        new_password: str,
        ip_address: str = None,
    ) -> bool:
        """
        Change user password.

        Args:
            db: Database session
            user_id: User ID
            old_password: Current password
            new_password: New password
            ip_address: Client IP for audit

        Returns:
            True if successful, False otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Verify old password
        if not self.pwd.verify(old_password, user.hashed_password):
            self._log_audit(
                db,
                user_id,
                "password_change",
                "security",
                ip_address,
                result="failure",
                failure_reason="invalid_old_password",
            )
            return False

        # Update password
        user.hashed_password = self.pwd.hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)

        # Add to history
        if user.password_history is None:
            user.password_history = []
        user.password_history.append(user.hashed_password)
        # Keep only last 5 passwords
        user.password_history = user.password_history[-5:]

        db.commit()

        # Revoke all sessions for security
        self.revoke_all_user_sessions(db, user_id, "password_change")

        self._log_audit(
            db,
            user_id,
            "password_change",
            "security",
            ip_address,
            result="success",
        )

        return True

    # ========================================================================
    # Session Management
    # ========================================================================

    def create_session(
        self,
        db: Session,
        user: User,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Dict[str, str]:
        """
        Create a new session with tokens.

        Args:
            db: Database session
            user: User object
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Dict with access_token, refresh_token, session_id
        """
        # Generate session ID
        session_id = str(uuid.uuid4())

        # Get user permissions
        from .rbac import RBACManager

        rbac = RBACManager()
        permissions = rbac.get_user_permissions(user.id)

        # Create tokens
        access_token = self.jwt.create_access_token(
            user_id=str(user.id),
            roles=[user.role.value],
            permissions=[p.value for p in permissions],
            mfa_verified=not user.is_mfa_enabled,  # Auto-verify if no MFA
        )

        refresh_token = self.jwt.create_refresh_token(
            user_id=str(user.id), session_id=session_id
        )

        # Decode refresh token to get JTI
        refresh_payload = self.jwt.decode_token(refresh_token)

        # Calculate expiry
        refresh_expiry = datetime.now(timezone.utc) + timedelta(days=7)

        # Store session in database
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            refresh_token_jti=refresh_payload.jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=refresh_expiry,
        )
        db.add(session)
        db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
            "token_type": "bearer",
            "expires_in": 900,  # 15 minutes
        }

    def refresh_session(
        self, db: Session, refresh_token: str, ip_address: str = None
    ) -> Optional[Dict[str, str]]:
        """
        Refresh access token using refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token string
            ip_address: Client IP

        Returns:
            New tokens dict or None if invalid
        """
        try:
            # Validate refresh token
            payload = self.jwt.decode_token(refresh_token)

            if payload.type != TokenType.REFRESH:
                return None

            # Check if blacklisted
            if self.is_token_blacklisted(db, payload.jti):
                return None

            # Get session
            session = (
                db.query(UserSession)
                .filter(
                    UserSession.refresh_token_jti == payload.jti,
                    UserSession.is_active,
                )
                .first()
            )

            if not session or session.is_expired():
                return None

            # Get user
            user = db.query(User).filter(User.id == int(payload.sub)).first()
            if not user or not user.is_active:
                return None

            # Create new access token
            from .rbac import RBACManager

            rbac = RBACManager()
            permissions = rbac.get_user_permissions(user.id)

            access_token = self.jwt.create_access_token(
                user_id=str(user.id),
                roles=[user.role.value],
                permissions=[p.value for p in permissions],
                session_id=session.session_id,
            )

            # Update session activity
            session.touch()
            db.commit()

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 900,
            }

        except Exception:
            return None

    def revoke_session(
        self, db: Session, session_id: str, reason: str = "logout"
    ) -> bool:
        """
        Revoke a session.

        Args:
            db: Database session
            session_id: Session ID
            reason: Reason for revocation

        Returns:
            True if successful
        """
        session = (
            db.query(UserSession)
            .filter(UserSession.session_id == session_id)
            .first()
        )

        if not session:
            return False

        # Blacklist the refresh token
        self.blacklist_token(
            db,
            session.refresh_token_jti,
            DBTokenType.REFRESH,
            session.expires_at,
            session.user_id,
            reason,
        )

        # Mark session as revoked
        session.is_active = False
        session.revoked = True
        session.revoked_reason = reason
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

        return True

    def revoke_all_user_sessions(
        self, db: Session, user_id: int, reason: str = "security"
    ) -> int:
        """
        Revoke all sessions for a user.

        Args:
            db: Database session
            user_id: User ID
            reason: Reason for revocation

        Returns:
            Number of sessions revoked
        """
        sessions = (
            db.query(UserSession)
            .filter(UserSession.user_id == user_id, UserSession.is_active)
            .all()
        )

        count = 0
        for session in sessions:
            # Blacklist token
            self.blacklist_token(
                db,
                session.refresh_token_jti,
                DBTokenType.REFRESH,
                session.expires_at,
                user_id,
                reason,
            )

            # Revoke session
            session.is_active = False
            session.revoked = True
            session.revoked_reason = reason
            session.revoked_at = datetime.now(timezone.utc)
            count += 1

        db.commit()
        return count

    def get_user_sessions(
        self, db: Session, user_id: int, active_only: bool = True
    ) -> List[UserSession]:
        """Get all sessions for a user"""
        query = db.query(UserSession).filter(UserSession.user_id == user_id)
        if active_only:
            query = query.filter(UserSession.is_active)
        return query.order_by(desc(UserSession.created_at)).all()

    # ========================================================================
    # Token Blacklisting
    # ========================================================================

    def blacklist_token(
        self,
        db: Session,
        jti: str,
        token_type: DBTokenType,
        expires_at: datetime,
        user_id: int = None,
        reason: str = "logout",
    ) -> TokenBlacklist:
        """Add token to blacklist"""
        entry = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            reason=reason,
            expires_at=expires_at,
        )
        db.add(entry)
        db.commit()
        return entry

    def is_token_blacklisted(self, db: Session, jti: str) -> bool:
        """Check if token is blacklisted"""
        return (
            db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
            is not None
        )

    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Remove expired tokens from blacklist.

        Returns:
            Number of tokens removed
        """
        expired = (
            db.query(TokenBlacklist)
            .filter(TokenBlacklist.expires_at < datetime.now(timezone.utc))
            .all()
        )

        count = len(expired)
        for entry in expired:
            db.delete(entry)

        db.commit()
        return count

    # ========================================================================
    # User Management
    # ========================================================================

    def deactivate_user(
        self, db: Session, user_id: int, reason: str = "admin_action"
    ) -> bool:
        """Deactivate user account and revoke all sessions"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        user.is_active = False
        db.commit()

        # Revoke all sessions
        self.revoke_all_user_sessions(db, user_id, reason)

        self._log_audit(
            db,
            user_id,
            "user_deactivate",
            "account",
            details={"reason": reason},
        )

        return True

    def update_user_role(
        self, db: Session, user_id: int, new_role: UserRole
    ) -> bool:
        """Update user role"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        old_role = user.role
        user.role = new_role
        db.commit()

        self._log_audit(
            db,
            user_id,
            "role_change",
            "account",
            details={"old_role": old_role.value, "new_role": new_role.value},
        )

        return True

    # ========================================================================
    # Audit Logging
    # ========================================================================

    def _log_audit(
        self,
        db: Session,
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

    def get_user_audit_logs(
        self, db: Session, user_id: int, limit: int = 100
    ) -> List[UserAuditLog]:
        """Get audit logs for a user"""
        return (
            db.query(UserAuditLog)
            .filter(UserAuditLog.user_id == user_id)
            .order_by(desc(UserAuditLog.timestamp))
            .limit(limit)
            .all()
        )


# Global instance
_user_manager = None


def get_user_manager(
    jwt_handler: Optional[JWTHandler] = None,
    password_hasher: Optional[PasswordHasher] = None,
) -> UserManager:
    """Get or create global UserManager instance"""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager(jwt_handler, password_hasher)
    return _user_manager
