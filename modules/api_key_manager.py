"""API Key Management System

Secure storage and management of API keys with:
- Encrypted storage using Fernet
- Role-based permissions
- Key rotation
- Audit logging
- OS keyring integration
"""

import json
import secrets
import hashlib
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

try:
    from cryptography.fernet import Fernet

    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class Permission(Enum):
    """API Key permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class KeyStatus(Enum):
    """Key status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"


@dataclass
class APIKey:
    """API Key structure"""
    key_id: str
    name: str
    hashed_key: str
    permissions: List[str]
    created_at: str
    expires_at: Optional[str]
    last_used: Optional[str]
    status: str
    created_by: str
    metadata: Dict


@dataclass
class AuditEntry:
    """Audit log entry"""
    timestamp: str
    action: str
    key_id: str
    user: str
    ip_address: Optional[str]
    success: bool
    details: str


class APIKeyManager:
    """Secure API Key Management"""

    name = "api_key_manager"
    version = "1.0.0"

    # Default key expiration (90 days)
    DEFAULT_EXPIRY_DAYS = 90

    def __init__(self, storage_path: str = "data/api_keys.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_log_path = Path(storage_path.replace(".json", "_audit.json"))
        self._encryption_key: Optional[bytes] = None
        self._fernet: Optional['Fernet'] = None

        if CRYPTO_AVAILABLE:
            self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption"""
        # Try to get encryption key from keyring
        if KEYRING_AVAILABLE:
            self._encryption_key = keyring.get_password(
                "zen-ai-pentest", "api_key_encryption"
            )
        
        # Generate new key if not exists
        if not self._encryption_key:
            self._encryption_key = Fernet.generate_key().decode()
            if KEYRING_AVAILABLE:
                keyring.set_password(
                    "zen-ai-pentest",
                    "api_key_encryption",
                    self._encryption_key
                )
            else:
                # Fallback: store in file (less secure)
                key_file = self.storage_path.parent / ".encryption_key"
                key_file.write_text(self._encryption_key)
                key_file.chmod(0o600)  # Owner read/write only
        
        self._fernet = Fernet(self._encryption_key.encode())

    def _encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not CRYPTO_AVAILABLE or not self._fernet:
            # Fallback: base64 encode (not secure, but functional)
            import base64
            return base64.b64encode(data.encode()).decode()
        return self._fernet.encrypt(data.encode()).decode()

    def _decrypt(self, data: str) -> str:
        """Decrypt string data"""
        if not CRYPTO_AVAILABLE or not self._fernet:
            import base64
            return base64.b64decode(data.encode()).decode()
        return self._fernet.decrypt(data.encode()).decode()

    def _hash_key(self, key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()

    def generate_key(
        self,
        name: str,
        permissions: List[str],
        created_by: str = "system",
        expires_days: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> tuple[str, str]:
        """
        Generate new API key
        Returns: (key_id, plain_key)
        """
        # Generate secure random key
        key_id = f"zen_{secrets.token_urlsafe(16)}"
        plain_key = f"zen_{secrets.token_urlsafe(32)}"
        
        # Calculate expiration
        created_at = datetime.utcnow()
        if expires_days is not None:
            expires_at = (created_at + timedelta(days=expires_days)).isoformat()
        else:
            expires_at = (created_at + timedelta(days=self.DEFAULT_EXPIRY_DAYS)).isoformat()
        
        # Create key record
        api_key = APIKey(
            key_id=key_id,
            name=name,
            hashed_key=self._hash_key(plain_key),
            permissions=permissions,
            created_at=created_at.isoformat(),
            expires_at=expires_at,
            last_used=None,
            status=KeyStatus.ACTIVE.value,
            created_by=created_by,
            metadata=metadata or {}
        )
        
        # Store
        self._save_key(api_key)
        
        # Audit log
        self._log_audit(
            action="key_created",
            key_id=key_id,
            user=created_by,
            success=True,
            details=f"Key '{name}' created with permissions: {permissions}"
        )
        
        return key_id, plain_key

    def validate_key(self, plain_key: str, required_permission: Optional[str] = None) -> Optional[APIKey]:
        """
        Validate API key and check permissions
        """
        key_hash = self._hash_key(plain_key)
        keys = self._load_keys()
        
        for key_data in keys.values():
            if key_data["hashed_key"] == key_hash:
                key = APIKey(**key_data)
                
                # Check status
                if key.status != KeyStatus.ACTIVE.value:
                    self._log_audit(
                        action="key_validation_failed",
                        key_id=key.key_id,
                        user="system",
                        success=False,
                        details=f"Key status: {key.status}"
                    )
                    return None
                
                # Check expiration
                if key.expires_at:
                    expires = datetime.fromisoformat(key.expires_at)
                    if datetime.utcnow() > expires:
                        key.status = KeyStatus.EXPIRED.value
                        self._save_key(key)
                        self._log_audit(
                            action="key_expired",
                            key_id=key.key_id,
                            user="system",
                            success=False,
                            details="Key expired"
                        )
                        return None
                
                # Check permission
                if required_permission and required_permission not in key.permissions:
                    self._log_audit(
                        action="key_permission_denied",
                        key_id=key.key_id,
                        user="system",
                        success=False,
                        details=f"Required: {required_permission}, Has: {key.permissions}"
                    )
                    return None
                
                # Update last used
                key.last_used = datetime.utcnow().isoformat()
                self._save_key(key)
                
                self._log_audit(
                    action="key_validated",
                    key_id=key.key_id,
                    user="system",
                    success=True,
                    details=f"Permission checked: {required_permission}"
                )
                
                return key
        
        return None

    def revoke_key(self, key_id: str, revoked_by: str) -> bool:
        """Revoke API key"""
        key = self._get_key_by_id(key_id)
        if not key:
            return False
        
        key.status = KeyStatus.REVOKED.value
        self._save_key(key)
        
        self._log_audit(
            action="key_revoked",
            key_id=key_id,
            user=revoked_by,
            success=True,
            details="Key revoked"
        )
        
        return True

    def rotate_key(self, key_id: str, rotated_by: str) -> Optional[tuple[str, str]]:
        """
        Rotate API key (create new, invalidate old)
        Returns: (new_key_id, new_plain_key) or None
        """
        old_key = self._get_key_by_id(key_id)
        if not old_key:
            return None
        
        # Mark old key as rotated
        old_key.status = KeyStatus.ROTATED.value
        old_key.metadata["rotated_to"] = "pending"
        old_key.metadata["rotated_at"] = datetime.utcnow().isoformat()
        self._save_key(old_key)
        
        # Generate new key with same permissions
        new_key_id, new_plain_key = self.generate_key(
            name=f"{old_key.name} (rotated)",
            permissions=old_key.permissions,
            created_by=rotated_by,
            expires_days=self.DEFAULT_EXPIRY_DAYS,
            metadata={"rotated_from": old_key.key_id}
        )
        
        # Update old key with rotation info
        old_key.metadata["rotated_to"] = new_key_id
        self._save_key(old_key)
        
        self._log_audit(
            action="key_rotated",
            key_id=key_id,
            user=rotated_by,
            success=True,
            details=f"Rotated to: {new_key_id}"
        )
        
        return new_key_id, new_plain_key

    def list_keys(self, status: Optional[str] = None) -> List[APIKey]:
        """List all API keys (without sensitive data)"""
        keys = self._load_keys()
        result = []
        
        for key_data in keys.values():
            if status is None or key_data["status"] == status:
                result.append(APIKey(**key_data))
        
        return result

    def get_audit_log(self, key_id: Optional[str] = None, limit: int = 100) -> List[AuditEntry]:
        """Get audit log entries"""
        logs = self._load_audit_log()
        
        if key_id:
            logs = [log for log in logs if log["key_id"] == key_id]
        
        # Sort by timestamp (newest first) and limit
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return [AuditEntry(**log) for log in logs[:limit]]

    def cleanup_expired_keys(self) -> int:
        """Remove expired keys older than 30 days"""
        keys = self._load_keys()
        removed = 0
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        for key_id, key_data in list(keys.items()):
            if key_data["status"] == KeyStatus.EXPIRED.value:
                expires_at = datetime.fromisoformat(key_data["expires_at"])
                if expires_at < cutoff:
                    del keys[key_id]
                    removed += 1
        
        self._save_keys(keys)
        return removed

    def _load_keys(self) -> Dict:
        """Load keys from storage"""
        if not self.storage_path.exists():
            return {}
        
        try:
            data = self.storage_path.read_text()
            decrypted = self._decrypt(data)
            return json.loads(decrypted)
        except Exception as e:
            logging.error(f"Failed to load keys: {e}")
            return {}

    def _save_key(self, key: APIKey):
        """Save single key"""
        keys = self._load_keys()
        keys[key.key_id] = asdict(key)
        self._save_keys(keys)

    def _save_keys(self, keys: Dict):
        """Save all keys"""
        data = json.dumps(keys, indent=2)
        encrypted = self._encrypt(data)
        self.storage_path.write_text(encrypted)
        self.storage_path.chmod(0o600)  # Owner only

    def _get_key_by_id(self, key_id: str) -> Optional[APIKey]:
        """Get key by ID"""
        keys = self._load_keys()
        if key_id in keys:
            return APIKey(**keys[key_id])
        return None

    def _log_audit(self, action: str, key_id: str, user: str, success: bool, details: str):
        """Add audit log entry"""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            key_id=key_id,
            user=user,
            ip_address=None,
            success=success,
            details=details
        )
        
        logs = self._load_audit_log()
        logs.append(asdict(entry))
        
        # Keep only last 10000 entries
        if len(logs) > 10000:
            logs = logs[-10000:]
        
        self._save_audit_log(logs)

    def _load_audit_log(self) -> List[Dict]:
        """Load audit log"""
        if not self.audit_log_path.exists():
            return []
        
        try:
            data = self.audit_log_path.read_text()
            return json.loads(data)
        except Exception:
            return []

    def _save_audit_log(self, logs: List[Dict]):
        """Save audit log"""
        self.audit_log_path.write_text(json.dumps(logs, indent=2))
        self.audit_log_path.chmod(0o600)

    def get_info(self) -> Dict:
        """Get module info"""
        return {
            "name": self.name,
            "version": self.version,
            "encryption": "Fernet (AES-128)" if CRYPTO_AVAILABLE else "Base64 (fallback)",
            "storage": str(self.storage_path),
            "keyring_available": KEYRING_AVAILABLE,
            "crypto_available": CRYPTO_AVAILABLE
        }


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="API Key Management")
    parser.add_argument("action", choices=["create", "list", "revoke", "rotate", "audit", "cleanup"])
    parser.add_argument("--name", help="Key name")
    parser.add_argument("--permissions", nargs="+", default=["read"], help="Permissions")
    parser.add_argument("--key-id", help="Key ID for operations")
    parser.add_argument("--user", default="cli", help="User performing action")
    
    args = parser.parse_args()
    
    manager = APIKeyManager()
    
    if args.action == "create":
        if not args.name:
            print("Error: --name required")
            exit(1)
        key_id, plain_key = manager.generate_key(
            name=args.name,
            permissions=args.permissions,
            created_by=args.user
        )
        print(f"Key ID: {key_id}")
        print(f"API Key: {plain_key}")
        print("WARNING: Save this key now - it won't be shown again!")
    
    elif args.action == "list":
        keys = manager.list_keys()
        print(f"{'Key ID':<30} {'Name':<20} {'Status':<10} {'Permissions'}")
        print("-" * 80)
        for key in keys:
            perms = ", ".join(key.permissions)
            print(f"{key.key_id:<30} {key.name:<20} {key.status:<10} {perms}")
    
    elif args.action == "revoke":
        if not args.key_id:
            print("Error: --key-id required")
            exit(1)
        if manager.revoke_key(args.key_id, args.user):
            print(f"Key {args.key_id} revoked")
        else:
            print(f"Key {args.key_id} not found")
    
    elif args.action == "rotate":
        if not args.key_id:
            print("Error: --key-id required")
            exit(1)
        result = manager.rotate_key(args.key_id, args.user)
        if result:
            print(f"Key rotated. New Key ID: {result[0]}")
            print(f"New API Key: {result[1]}")
        else:
            print(f"Key {args.key_id} not found")
    
    elif args.action == "audit":
        logs = manager.get_audit_log(args.key_id)
        print(f"{'Timestamp':<25} {'Action':<20} {'Key ID':<15} {'Success'}")
        print("-" * 70)
        for log in logs[:20]:
            status = "✓" if log.success else "✗"
            print(f"{log.timestamp:<25} {log.action:<20} {log.key_id:<15} {status}")
    
    elif args.action == "cleanup":
        removed = manager.cleanup_expired_keys()
        print(f"Removed {removed} expired keys")
