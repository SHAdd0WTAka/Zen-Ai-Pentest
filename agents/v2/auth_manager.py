"""
Agent Authentication Manager
============================

API key-based authentication for agents.

Features:
- API key generation with secure random tokens
- HMAC-based key verification
- Key rotation support
- Role-based permissions
- Database-backed storage
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from database.auth_models import APIKey as APIKeyModel
from database.auth_models import SessionLocal

from .secure_message import generate_keypair, generate_signing_keypair


class AgentRole(str, Enum):
    """Agent roles for permission control"""

    RESEARCHER = "researcher"  # Information gathering
    ANALYST = "analyst"  # Data analysis
    EXPLOIT = "exploit"  # Exploit development
    SCANNER = "scanner"  # Vulnerability scanning
    REPORTER = "reporter"  # Report generation
    COORDINATOR = "coordinator"  # Multi-agent coordination
    ADMIN = "admin"  # Administrative access


class AgentPermission(str, Enum):
    """Permissions for fine-grained access control"""

    # Messaging permissions
    MESSAGE_SEND = "message:send"
    MESSAGE_RECEIVE = "message:receive"
    MESSAGE_BROADCAST = "message:broadcast"

    # Task permissions
    TASK_CREATE = "task:create"
    TASK_EXECUTE = "task:execute"
    TASK_CANCEL = "task:cancel"

    # Channel permissions
    CHANNEL_JOIN = "channel:join"
    CHANNEL_LEAVE = "channel:leave"
    CHANNEL_CREATE = "channel:create"

    # System permissions
    AGENT_REGISTER = "agent:register"
    AGENT_UNREGISTER = "agent:unregister"
    AGENT_LIST = "agent:list"

    # Data permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[AgentRole, List[AgentPermission]] = {
    AgentRole.RESEARCHER: [
        AgentPermission.MESSAGE_SEND,
        AgentPermission.MESSAGE_RECEIVE,
        AgentPermission.TASK_CREATE,
        AgentPermission.TASK_EXECUTE,
        AgentPermission.CHANNEL_JOIN,
        AgentPermission.CHANNEL_LEAVE,
        AgentPermission.DATA_READ,
        AgentPermission.DATA_WRITE,
    ],
    AgentRole.ANALYST: [
        AgentPermission.MESSAGE_SEND,
        AgentPermission.MESSAGE_RECEIVE,
        AgentPermission.TASK_EXECUTE,
        AgentPermission.CHANNEL_JOIN,
        AgentPermission.CHANNEL_LEAVE,
        AgentPermission.DATA_READ,
        AgentPermission.DATA_WRITE,
    ],
    AgentRole.EXPLOIT: [
        AgentPermission.MESSAGE_SEND,
        AgentPermission.MESSAGE_RECEIVE,
        AgentPermission.TASK_CREATE,
        AgentPermission.TASK_EXECUTE,
        AgentPermission.CHANNEL_JOIN,
        AgentPermission.CHANNEL_LEAVE,
        AgentPermission.DATA_READ,
        AgentPermission.DATA_WRITE,
    ],
    AgentRole.SCANNER: [
        AgentPermission.MESSAGE_SEND,
        AgentPermission.MESSAGE_RECEIVE,
        AgentPermission.TASK_CREATE,
        AgentPermission.TASK_EXECUTE,
        AgentPermission.CHANNEL_JOIN,
        AgentPermission.CHANNEL_LEAVE,
        AgentPermission.DATA_READ,
        AgentPermission.DATA_WRITE,
    ],
    AgentRole.REPORTER: [
        AgentPermission.MESSAGE_RECEIVE,
        AgentPermission.TASK_EXECUTE,
        AgentPermission.CHANNEL_JOIN,
        AgentPermission.CHANNEL_LEAVE,
        AgentPermission.DATA_READ,
        AgentPermission.DATA_WRITE,
    ],
    AgentRole.COORDINATOR: [
        AgentPermission.MESSAGE_SEND,
        AgentPermission.MESSAGE_RECEIVE,
        AgentPermission.MESSAGE_BROADCAST,
        AgentPermission.TASK_CREATE,
        AgentPermission.TASK_EXECUTE,
        AgentPermission.TASK_CANCEL,
        AgentPermission.CHANNEL_JOIN,
        AgentPermission.CHANNEL_LEAVE,
        AgentPermission.CHANNEL_CREATE,
        AgentPermission.AGENT_LIST,
        AgentPermission.DATA_READ,
        AgentPermission.DATA_WRITE,
    ],
    AgentRole.ADMIN: list(AgentPermission),  # All permissions
}


@dataclass
class AgentCredentials:
    """Agent credentials container"""

    agent_id: str
    api_key: str
    api_secret: str  # Only shown once during creation
    public_key: bytes  # X25519 public key for encryption
    signing_key: bytes  # Ed25519 public key for signature verification
    role: AgentRole
    permissions: List[AgentPermission]
    created_at: datetime
    expires_at: Optional[datetime]


@dataclass
class AgentIdentity:
    """Authenticated agent identity"""

    agent_id: str
    role: AgentRole
    permissions: List[AgentPermission]
    is_active: bool
    last_seen: Optional[datetime]


class AgentAuthenticator:
    """
    Manages agent authentication and authorization

    Uses HMAC-SHA256 for API key verification.
    Keys are stored as hashes (like passwords) for security.
    """

    # API Key format: zen_{prefix}_{random}
    KEY_PREFIX = "zen"
    KEY_ENTROPY = 32  # bytes
    SECRET_ENTROPY = 48  # bytes

    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()

    def generate_api_key(
        self,
        role: AgentRole,
        name: str,
        description: Optional[str] = None,
        expires_days: Optional[int] = None,
        rate_limit: int = 1000,
    ) -> AgentCredentials:
        """
        Generate new agent credentials

        Args:
            role: Agent role for permissions
            name: Human-readable name
            description: Optional description
            expires_days: Days until expiration (None = never)
            rate_limit: Requests per hour limit

        Returns:
            AgentCredentials with API key and secret
        """
        # Generate IDs
        agent_id = f"agt_{uuid4().hex[:16]}"
        key_id = f"{self.KEY_PREFIX}_{secrets.token_urlsafe(8)}"

        # Generate keys
        api_secret = secrets.token_urlsafe(self.SECRET_ENTROPY)

        # Generate encryption keypair
        enc_private, enc_public = generate_keypair()

        # Generate signing keypair
        sign_private, sign_public = generate_signing_keypair()

        # Hash the secret for storage (like password hashing)
        secret_hash = self._hash_secret(api_secret)

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        # Store in database
        api_key_model = APIKeyModel(
            user_id=None,  # Agents are separate from users
            key_id=key_id,
            key_hash=secret_hash,
            key_prefix=key_id[:20],  # First 20 chars for identification
            name=name,
            description=description,
            scopes=[p.value for p in ROLE_PERMISSIONS[role]],
            rate_limit=rate_limit,
            is_active=True,
            expires_at=expires_at,
            created_by_ip=None,  # Set during registration
        )

        # Store agent metadata separately

        # Note: In production, create a proper Agent table
        # For now, store in API key metadata
        api_key_model.name = f"{name}|{agent_id}|{role.value}"

        self.db.add(api_key_model)
        self.db.commit()

        return AgentCredentials(
            agent_id=agent_id,
            api_key=key_id,
            api_secret=api_secret,
            public_key=enc_public,
            signing_key=sign_public,
            role=role,
            permissions=ROLE_PERMISSIONS[role],
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )

    def authenticate(self, api_key: str, api_secret: str) -> Optional[AgentIdentity]:
        """
        Authenticate agent with API key and secret

        Args:
            api_key: The API key ID
            api_secret: The API secret

        Returns:
            AgentIdentity if authenticated, None otherwise
        """
        # Find API key in database
        key_model = self.db.query(APIKeyModel).filter(APIKeyModel.key_id == api_key, APIKeyModel.is_active).first()

        if not key_model:
            return None

        # Check expiration
        if key_model.expires_at and datetime.utcnow() > key_model.expires_at:
            return None

        # Verify secret
        if not self._verify_secret(api_secret, key_model.key_hash):
            return None

        # Update last used
        key_model.record_usage()
        self.db.commit()

        # Parse agent info from name field (temporary solution)
        # Format: name|agent_id|role
        parts = key_model.name.split("|")
        if len(parts) >= 3:
            agent_id = parts[1]
            role = AgentRole(parts[2])
        else:
            agent_id = key_model.key_id
            role = AgentRole.SCANNER

        # Build permissions from scopes
        permissions = [AgentPermission(p) for p in key_model.scopes if p in AgentPermission._value2member_map_]

        return AgentIdentity(
            agent_id=agent_id, role=role, permissions=permissions, is_active=True, last_seen=key_model.last_used_at
        )

    def revoke_key(self, agent_id: str, reason: str = "admin_action") -> bool:
        """Revoke an agent's API key"""
        # Find by agent_id in name field
        key_models = self.db.query(APIKeyModel).filter(APIKeyModel.name.like(f"%{agent_id}%")).all()

        if not key_models:
            return False

        for key_model in key_models:
            key_model.is_active = False
            key_model.revoked_at = datetime.utcnow()
            key_model.revoked_reason = reason

        self.db.commit()
        return True

    def rotate_key(self, agent_id: str) -> Optional[AgentCredentials]:
        """
        Rotate an agent's API key

        Generates new credentials and invalidates old ones.
        """
        # Find existing key
        key_models = self.db.query(APIKeyModel).filter(APIKeyModel.name.like(f"%{agent_id}%"), APIKeyModel.is_active).all()

        if not key_models:
            return None

        # Parse role from existing key
        old_key = key_models[0]
        parts = old_key.name.split("|")
        role = AgentRole(parts[2]) if len(parts) >= 3 else AgentRole.SCANNER
        name = parts[0] if len(parts) >= 1 else "Agent"

        # Revoke old key
        for key_model in key_models:
            key_model.is_active = False
            key_model.revoked_at = datetime.utcnow()
            key_model.revoked_reason = "key_rotation"

        self.db.commit()

        # Generate new credentials
        return self.generate_api_key(role=role, name=name, expires_days=90 if old_key.expires_at else None)

    def check_permission(self, identity: AgentIdentity, permission: AgentPermission) -> bool:
        """Check if agent has specific permission"""
        return permission in identity.permissions

    def list_active_agents(self) -> List[AgentIdentity]:
        """List all active agents"""
        key_models = self.db.query(APIKeyModel).filter(APIKeyModel.is_active).all()

        agents = []
        for key_model in key_models:
            parts = key_model.name.split("|")
            if len(parts) >= 3:
                agent_id = parts[1]
                role = AgentRole(parts[2])
                permissions = [AgentPermission(p) for p in key_model.scopes if p in AgentPermission._value2member_map_]

                agents.append(
                    AgentIdentity(
                        agent_id=agent_id, role=role, permissions=permissions, is_active=True, last_seen=key_model.last_used_at
                    )
                )

        return agents

    def _hash_secret(self, secret: str) -> str:
        """Hash API secret using PBKDF2-like approach"""
        # Use HMAC with SHA-256 for hashing
        salt = secrets.token_hex(16)
        hash_value = hmac.new(salt.encode(), secret.encode(), hashlib.sha256).hexdigest()
        return f"{salt}${hash_value}"

    def _verify_secret(self, secret: str, hash_value: str) -> bool:
        """Verify API secret against hash"""
        try:
            salt, stored_hash = hash_value.split("$")
            computed_hash = hmac.new(salt.encode(), secret.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(computed_hash, stored_hash)
        except ValueError:
            return False


# ============================================================================
# Decorators for permission checking
# ============================================================================


def require_permission(permission: AgentPermission):
    """Decorator to require specific permission"""

    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, "identity") or not self.identity:
                raise PermissionError("Not authenticated")

            if permission not in self.identity.permissions:
                raise PermissionError(f"Missing permission: {permission.value}")

            return await func(self, *args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Test Functions
# ============================================================================


def test_agent_authentication():
    """Test agent authentication flow"""
    from database.auth_models import init_auth_db

    init_auth_db()

    auth = AgentAuthenticator()

    # Generate credentials
    creds = auth.generate_api_key(role=AgentRole.RESEARCHER, name="test-agent", expires_days=30)

    print(f"✅ Generated credentials for {creds.agent_id}")
    print(f"   API Key: {creds.api_key}")
    print(f"   Role: {creds.role.value}")
    print(f"   Permissions: {len(creds.permissions)}")

    # Authenticate
    identity = auth.authenticate(creds.api_key, creds.api_secret)
    assert identity is not None
    assert identity.agent_id == creds.agent_id
    assert identity.role == AgentRole.RESEARCHER

    print("✅ Authentication successful")

    # Check permissions
    assert auth.check_permission(identity, AgentPermission.MESSAGE_SEND)
    assert not auth.check_permission(identity, AgentPermission.AGENT_REGISTER)  # Admin only

    print("✅ Permission checking works")

    # Wrong secret
    identity = auth.authenticate(creds.api_key, "wrong_secret")
    assert identity is None

    print("✅ Wrong secret rejected")


def test_key_rotation():
    """Test key rotation"""
    from database.auth_models import init_auth_db

    init_auth_db()

    auth = AgentAuthenticator()

    # Generate initial credentials
    creds1 = auth.generate_api_key(role=AgentRole.ANALYST, name="rotation-test-agent")

    print(f"✅ Initial key: {creds1.api_key}")

    # Rotate key
    creds2 = auth.rotate_key(creds1.agent_id)
    assert creds2 is not None

    print(f"✅ Rotated key: {creds2.api_key}")

    # Old key should not work
    identity = auth.authenticate(creds1.api_key, creds1.api_secret)
    assert identity is None

    print("✅ Old key invalidated")

    # New key should work
    identity = auth.authenticate(creds2.api_key, creds2.api_secret)
    assert identity is not None

    print("✅ New key works")


if __name__ == "__main__":
    test_agent_authentication()
    test_key_rotation()
    print("\n✅ All tests passed!")
