"""
Security Tests: Authentication
=============================

Tests for authentication security:
- JWT token validation
- Password hashing
- RBAC permissions
- API key validation
"""

import pytest
import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Set
from unittest.mock import Mock, patch, MagicMock


def get_utc_now():
    """Helper function to get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class JWTHandler:
    """JWT token handler with security validations."""
    
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm
        self.blacklist: Set[str] = set()
    
    def generate_token(
        self, 
        user_id: str, 
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict] = None
    ) -> str:
        """Generate a JWT token."""
        import base64
        import json
        
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": self.algorithm, "typ": "JWT"}).encode()
        ).rstrip(b'=').decode()
        
        now = get_utc_now()
        exp = now + (expires_delta or timedelta(minutes=15))
        
        payload = {
            "sub": user_id,
            "iat": now.timestamp(),
            "exp": exp.timestamp(),
            "jti": secrets.token_hex(16),
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).rstrip(b'=').decode()
        
        signature = hmac.new(
            self.secret.encode(),
            f"{header}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        
        return f"{header}.{payload_b64}.{sig_b64}"
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode a JWT token."""
        import base64
        import json
        
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid token format")
            
            # Verify signature
            message = f"{parts[0]}.{parts[1]}".encode()
            expected_sig = hmac.new(
                self.secret.encode(),
                message,
                hashlib.sha256
            ).digest()
            
            # Decode actual signature from base64url
            actual_sig_b64 = parts[2]
            # Add padding if needed
            padding_needed = 4 - len(actual_sig_b64) % 4
            if padding_needed != 4:
                actual_sig_b64 += '=' * padding_needed
            actual_sig = base64.urlsafe_b64decode(actual_sig_b64)
            
            if not hmac.compare_digest(expected_sig, actual_sig):
                raise ValueError("Invalid signature")
            
            # Decode payload
            payload_b64 = parts[1]
            while len(payload_b64) % 4:
                payload_b64 += '='
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Check expiration
            if payload.get("jti") in self.blacklist:
                raise ValueError("Token has been revoked")
            
            exp = payload.get("exp")
            if exp and get_utc_now().timestamp() > exp:
                raise ValueError("Token has expired")
            
            return payload
            
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")
    
    def blacklist_token(self, jti: str):
        """Add token JTI to blacklist."""
        self.blacklist.add(jti)


class PasswordHasher:
    """Secure password hashing utility."""
    
    SALT_LENGTH = 32
    ITERATIONS = 100000
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password with salt using PBKDF2."""
        salt = secrets.token_hex(cls.SALT_LENGTH)
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('ascii'),
            cls.ITERATIONS
        )
        return f"pbkdf2:sha256:{cls.ITERATIONS}${salt}${pwdhash.hex()}"
    
    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            parts = hashed.split('$')
            if len(parts) != 3:
                return False
            
            algo_info = parts[0].split(':')
            if len(algo_info) != 3:
                return False
            
            iterations = int(algo_info[2])
            salt = parts[1]
            stored_hash = parts[2]
            
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('ascii'),
                iterations
            ).hex()
            
            return hmac.compare_digest(stored_hash, computed_hash)
        except Exception:
            return False
    
    @classmethod
    def check_password_strength(cls, password: str) -> Dict[str, any]:
        """Check password strength and return detailed analysis."""
        result = {
            "strong": False,
            "length": len(password),
            "has_upper": bool(re.search(r'[A-Z]', password)),
            "has_lower": bool(re.search(r'[a-z]', password)),
            "has_digit": bool(re.search(r'\d', password)),
            "has_special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            "score": 0,
        }
        
        # Calculate score
        if result["length"] >= 8:
            result["score"] += 1
        if result["length"] >= 12:
            result["score"] += 1
        if result["has_upper"]:
            result["score"] += 1
        if result["has_lower"]:
            result["score"] += 1
        if result["has_digit"]:
            result["score"] += 1
        if result["has_special"]:
            result["score"] += 1
        
        result["strong"] = result["score"] >= 4 and result["length"] >= 8
        return result


class APIKeyValidator:
    """API key validation utility."""
    
    KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{32,128}$')
    
    def __init__(self):
        self.valid_keys: Dict[str, Dict] = {}
    
    def generate_key(self, name: str, permissions: List[str]) -> str:
        """Generate a new API key."""
        key = f"zen_{secrets.token_urlsafe(32)}"
        self.valid_keys[key] = {
            "name": name,
            "permissions": set(permissions),
            "created_at": get_utc_now(),
            "last_used": None,
            "usage_count": 0,
        }
        return key
    
    def validate_key(self, key: str, required_permission: Optional[str] = None) -> bool:
        """Validate an API key and optionally check permission."""
        if not self.KEY_PATTERN.match(key):
            return False
        
        key_data = self.valid_keys.get(key)
        if not key_data:
            return False
        
        # Update usage stats
        key_data["last_used"] = get_utc_now()
        key_data["usage_count"] += 1
        
        if required_permission:
            return required_permission in key_data["permissions"]
        
        return True
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        if key in self.valid_keys:
            del self.valid_keys[key]
            return True
        return False


class RBACManager:
    """Role-Based Access Control manager."""
    
    ROLES = {
        "admin": {"*"},  # All permissions
        "operator": {
            "scan:read", "scan:write", "scan:execute",
            "report:read", "report:write",
            "target:read", "target:write",
        },
        "viewer": {
            "scan:read",
            "report:read",
            "target:read",
        },
        "auditor": {
            "scan:read",
            "report:read",
            "audit:read", "audit:write",
        },
    }
    
    def __init__(self):
        self.user_roles: Dict[str, Set[str]] = {}
    
    def assign_role(self, user_id: str, role: str):
        """Assign role to user."""
        if role not in self.ROLES:
            raise ValueError(f"Invalid role: {role}")
        self.user_roles[user_id] = self.ROLES[role]
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission."""
        user_perms = self.user_roles.get(user_id, set())
        return "*" in user_perms or permission in user_perms
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user."""
        return self.user_roles.get(user_id, set())


# ============== JWT Tests ==============

class TestJWTValidation:
    """Test cases for JWT token validation."""
    
    @pytest.fixture
    def jwt_handler(self):
        return JWTHandler(secret="test_secret_key_32_bytes_long!!")
    
    def test_token_generation(self, jwt_handler):
        """Test JWT token generation."""
        token = jwt_handler.generate_token("user123")
        assert token is not None
        assert len(token.split('.')) == 3
    
    def test_token_verification(self, jwt_handler):
        """Test JWT token verification."""
        token = jwt_handler.generate_token("user123")
        payload = jwt_handler.verify_token(token)
        assert payload["sub"] == "user123"
        assert "exp" in payload
        assert "jti" in payload
    
    def test_token_expiration(self, jwt_handler):
        """Test expired token detection."""
        # Generate token that expires immediately
        token = jwt_handler.generate_token("user123", expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(ValueError, match="expired"):
            jwt_handler.verify_token(token)
    
    def test_token_signature_validation(self, jwt_handler):
        """Test token signature validation."""
        import base64
        import json
        
        token = jwt_handler.generate_token("user123")
        parts = token.split('.')
        
        # Tamper with payload
        tampered_payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "attacker"}).encode()
        ).rstrip(b'=').decode()
        
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
        
        with pytest.raises(ValueError):
            jwt_handler.verify_token(tampered_token)
    
    def test_token_blacklist(self, jwt_handler):
        """Test token blacklisting."""
        token = jwt_handler.generate_token("user123")
        payload = jwt_handler.verify_token(token)
        
        # Blacklist the token
        jwt_handler.blacklist_token(payload["jti"])
        
        # Verify blacklisted token fails
        with pytest.raises(ValueError, match="revoked"):
            jwt_handler.verify_token(token)
    
    def test_invalid_token_format(self, jwt_handler):
        """Test handling of malformed tokens."""
        invalid_tokens = [
            "invalid",
            "only.two.parts",
            "too.many.parts.here.extra",
            "",
        ]
        
        for token in invalid_tokens:
            with pytest.raises(ValueError):
                jwt_handler.verify_token(token)
    
    def test_additional_claims(self, jwt_handler):
        """Test token with additional claims."""
        claims = {"role": "admin", "org": "acme"}
        token = jwt_handler.generate_token("user123", additional_claims=claims)
        payload = jwt_handler.verify_token(token)
        
        assert payload["role"] == "admin"
        assert payload["org"] == "acme"


# ============== Password Hashing Tests ==============

class TestPasswordHashing:
    """Test cases for password hashing."""
    
    def test_password_hashing(self):
        """Test password hashing produces valid hash."""
        password = "MySecureP@ssw0rd"
        hashed = PasswordHasher.hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert "$" in hashed
        assert "pbkdf2:sha256" in hashed
    
    def test_password_verification(self):
        """Test password verification."""
        password = "MySecureP@ssw0rd"
        hashed = PasswordHasher.hash_password(password)
        
        assert PasswordHasher.verify_password(password, hashed) is True
        assert PasswordHasher.verify_password("WrongPassword", hashed) is False
    
    def test_different_salts(self):
        """Test that same password produces different hashes."""
        password = "SamePassword123!"
        hash1 = PasswordHasher.hash_password(password)
        hash2 = PasswordHasher.hash_password(password)
        
        assert hash1 != hash2  # Different salts
        assert PasswordHasher.verify_password(password, hash1)
        assert PasswordHasher.verify_password(password, hash2)
    
    @pytest.mark.parametrize("password,expected_strong", [
        ("short", False),
        ("password", False),  # Common word, no variety
        ("Password1!", True),  # Meets all criteria
        ("MyV3ryStr0ng!P@ss", True),  # Strong
        ("12345678", False),  # Only digits
    ])
    def test_password_strength(self, password: str, expected_strong: bool):
        """Test password strength checker."""
        result = PasswordHasher.check_password_strength(password)
        assert result["strong"] == expected_strong
    
    def test_password_strength_details(self):
        """Test password strength provides detailed analysis."""
        password = "Test123!"
        result = PasswordHasher.check_password_strength(password)
        
        assert "length" in result
        assert "has_upper" in result
        assert "has_lower" in result
        assert "has_digit" in result
        assert "has_special" in result
        assert "score" in result
        
        assert result["has_upper"] is True
        assert result["has_lower"] is True
        assert result["has_digit"] is True
        assert result["has_special"] is True
    
    def test_verify_malformed_hash(self):
        """Test verification handles malformed hashes gracefully."""
        assert PasswordHasher.verify_password("password", "invalid_hash") is False
        assert PasswordHasher.verify_password("password", "") is False


# ============== RBAC Tests ==============

class TestRBACPermissions:
    """Test cases for RBAC permission system."""
    
    @pytest.fixture
    def rbac(self):
        rbac = RBACManager()
        rbac.assign_role("admin_user", "admin")
        rbac.assign_role("operator_user", "operator")
        rbac.assign_role("viewer_user", "viewer")
        rbac.assign_role("auditor_user", "auditor")
        return rbac
    
    def test_admin_has_all_permissions(self, rbac):
        """Test admin role has all permissions."""
        assert rbac.check_permission("admin_user", "scan:read")
        assert rbac.check_permission("admin_user", "scan:write")
        assert rbac.check_permission("admin_user", "scan:delete")
        assert rbac.check_permission("admin_user", "user:admin")
        assert rbac.check_permission("admin_user", "any:permission")
    
    def test_operator_permissions(self, rbac):
        """Test operator role has appropriate permissions."""
        assert rbac.check_permission("operator_user", "scan:read")
        assert rbac.check_permission("operator_user", "scan:write")
        assert rbac.check_permission("operator_user", "scan:execute")
        assert not rbac.check_permission("operator_user", "user:admin")
        assert not rbac.check_permission("operator_user", "scan:delete")
    
    def test_viewer_permissions(self, rbac):
        """Test viewer role has read-only permissions."""
        assert rbac.check_permission("viewer_user", "scan:read")
        assert rbac.check_permission("viewer_user", "report:read")
        assert not rbac.check_permission("viewer_user", "scan:write")
        assert not rbac.check_permission("viewer_user", "scan:execute")
    
    def test_auditor_permissions(self, rbac):
        """Test auditor role has audit permissions."""
        assert rbac.check_permission("auditor_user", "scan:read")
        assert rbac.check_permission("auditor_user", "audit:read")
        assert rbac.check_permission("auditor_user", "audit:write")
        assert not rbac.check_permission("auditor_user", "scan:write")
    
    def test_unknown_user_has_no_permissions(self, rbac):
        """Test unknown users have no permissions."""
        assert not rbac.check_permission("unknown_user", "scan:read")
        assert not rbac.check_permission("unknown_user", "any:permission")
    
    def test_invalid_role_raises_error(self, rbac):
        """Test that invalid role assignment raises error."""
        with pytest.raises(ValueError, match="Invalid role"):
            rbac.assign_role("user", "invalid_role")
    
    def test_get_user_permissions(self, rbac):
        """Test getting all permissions for a user."""
        perms = rbac.get_user_permissions("viewer_user")
        assert "scan:read" in perms
        assert "report:read" in perms
        assert "target:read" in perms


# ============== API Key Tests ==============

class TestAPIKeyValidation:
    """Test cases for API key validation."""
    
    @pytest.fixture
    def api_validator(self):
        return APIKeyValidator()
    
    def test_key_generation(self, api_validator):
        """Test API key generation."""
        key = api_validator.generate_key("test-app", ["read", "write"])
        
        assert key is not None
        assert key.startswith("zen_")
        assert len(key) > 32
    
    def test_key_validation(self, api_validator):
        """Test API key validation."""
        key = api_validator.generate_key("test-app", ["read"])
        
        assert api_validator.validate_key(key) is True
        assert api_validator.validate_key(key, "read") is True
        assert api_validator.validate_key(key, "write") is False
    
    def test_invalid_key_rejection(self, api_validator):
        """Test rejection of invalid keys."""
        invalid_keys = [
            "",  # Empty
            "short",  # Too short
            "invalid!chars",  # Invalid characters
            "a" * 200,  # Too long
        ]
        
        for key in invalid_keys:
            assert api_validator.validate_key(key) is False
    
    def test_key_usage_tracking(self, api_validator):
        """Test API key usage tracking."""
        key = api_validator.generate_key("test-app", ["read"])
        
        # Initial state
        key_data = api_validator.valid_keys[key]
        assert key_data["usage_count"] == 0
        assert key_data["last_used"] is None
        
        # After use
        api_validator.validate_key(key)
        assert key_data["usage_count"] == 1
        assert key_data["last_used"] is not None
    
    def test_key_revocation(self, api_validator):
        """Test API key revocation."""
        key = api_validator.generate_key("test-app", ["read"])
        
        assert api_validator.validate_key(key) is True
        
        api_validator.revoke_key(key)
        
        assert api_validator.validate_key(key) is False
    
    def test_revoke_nonexistent_key(self, api_validator):
        """Test revoking non-existent key returns False."""
        assert api_validator.revoke_key("nonexistent_key") is False
    
    def test_multiple_keys_isolation(self, api_validator):
        """Test that API keys are properly isolated."""
        key1 = api_validator.generate_key("app1", ["read"])
        key2 = api_validator.generate_key("app2", ["write"])
        
        assert api_validator.validate_key(key1, "read") is True
        assert api_validator.validate_key(key1, "write") is False
        
        assert api_validator.validate_key(key2, "write") is True
        assert api_validator.validate_key(key2, "read") is False


# ============== Integration Tests ==============

class TestAuthIntegration:
    """Integration tests for authentication system."""
    
    def test_complete_auth_flow(self):
        """Test complete authentication flow."""
        # 1. Create user with password
        password = "SecureP@ss123!"
        password_hash = PasswordHasher.hash_password(password)
        
        # 2. Verify login
        assert PasswordHasher.verify_password(password, password_hash)
        
        # 3. Generate JWT
        jwt_handler = JWTHandler(secret="app_secret")
        token = jwt_handler.generate_token("user123")
        
        # 4. Verify JWT
        payload = jwt_handler.verify_token(token)
        assert payload["sub"] == "user123"
        
        # 5. Check permissions
        rbac = RBACManager()
        rbac.assign_role("user123", "operator")
        assert rbac.check_permission("user123", "scan:read")
        
        # 6. Generate API key
        api_validator = APIKeyValidator()
        api_key = api_validator.generate_key("my-app", ["scan:read"])
        assert api_validator.validate_key(api_key, "scan:read")
    
    def test_token_refresh_flow(self):
        """Test token refresh flow."""
        jwt_handler = JWTHandler(secret="app_secret")
        
        # Generate tokens
        access_token = jwt_handler.generate_token(
            "user123", 
            expires_delta=timedelta(minutes=15)
        )
        refresh_token = jwt_handler.generate_token(
            "user123",
            expires_delta=timedelta(days=7)
        )
        
        # Both tokens work initially
        assert jwt_handler.verify_token(access_token)["sub"] == "user123"
        assert jwt_handler.verify_token(refresh_token)["sub"] == "user123"
    
    def test_permission_denial_scenarios(self):
        """Test various permission denial scenarios."""
        rbac = RBACManager()
        rbac.assign_role("viewer", "viewer")
        
        # Viewer cannot execute scans
        assert not rbac.check_permission("viewer", "scan:execute")
        
        # Viewer cannot delete anything
        assert not rbac.check_permission("viewer", "scan:delete")
        
        # Unknown user has no access
        assert not rbac.check_permission("unknown", "scan:read")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
