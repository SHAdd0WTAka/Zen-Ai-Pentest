"""
JWT Handler Module
==================

Secure JWT token handling with:
- Access tokens (short-lived)
- Refresh tokens (long-lived)
- Token blacklisting
- JTI (JWT ID) for token tracking
- Secure claims validation

Compliance: OWASP ASVS 2026 V3.5, V3.6
"""

import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional, Any, List, Set
from dataclasses import dataclass
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from .config import get_config, JWTConfig


class TokenType(Enum):
    """Token types for JWT"""
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenPayload:
    """Structured token payload"""
    sub: str                    # Subject (user ID)
    jti: str                    # JWT ID (unique token identifier)
    type: TokenType             # Token type
    iat: datetime               # Issued at
    exp: datetime               # Expiration
    nbf: datetime               # Not before
    iss: str                    # Issuer
    aud: str                    # Audience
    roles: List[str]            # User roles
    permissions: List[str]      # User permissions
    session_id: Optional[str]   # Session ID
    mfa_verified: bool          # MFA verification status
    ip_address: Optional[str]   # Client IP
    user_agent: Optional[str]   # Client user agent
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT encoding"""
        return {
            "sub": self.sub,
            "jti": self.jti,
            "type": self.type.value,
            "iat": self.iat,
            "exp": self.exp,
            "nbf": self.nbf,
            "iss": self.iss,
            "aud": self.aud,
            "roles": self.roles,
            "permissions": self.permissions,
            "session_id": self.session_id,
            "mfa_verified": self.mfa_verified,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """Create from decoded JWT dictionary"""
        return cls(
            sub=data.get("sub", ""),
            jti=data.get("jti", ""),
            type=TokenType(data.get("type", "access")),
            iat=datetime.fromtimestamp(data.get("iat", 0), tz=timezone.utc),
            exp=datetime.fromtimestamp(data.get("exp", 0), tz=timezone.utc),
            nbf=datetime.fromtimestamp(data.get("nbf", 0), tz=timezone.utc),
            iss=data.get("iss", ""),
            aud=data.get("aud", ""),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            session_id=data.get("session_id"),
            mfa_verified=data.get("mfa_verified", False),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
        )


class JWTError(Exception):
    """Base JWT error"""
    pass


class TokenExpiredError(JWTError):
    """Token has expired"""
    pass


class TokenInvalidError(JWTError):
    """Token is invalid"""
    pass


class TokenBlacklistedError(JWTError):
    """Token has been blacklisted"""
    pass


class JWTHandler:
    """
    JWT Handler for secure token management
    
    Features:
    - Dual token system (access + refresh)
    - Token blacklisting
    - JTI tracking
    - Secure claims validation
    """
    
    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or get_config().jwt
        self._blacklisted_tokens: Set[str] = set()  # In production: use Redis
        self._token_metadata: Dict[str, Dict] = {}   # Token metadata storage
        
        if not self.config.secret_key:
            raise JWTError("JWT secret key is required")
    
    def _generate_jti(self) -> str:
        """Generate unique JWT ID"""
        return str(uuid.uuid4())
    
    def _hash_token(self, token: str) -> str:
        """Hash token for storage/comparison"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def create_access_token(
        self,
        user_id: str,
        roles: List[str],
        permissions: List[str],
        session_id: Optional[str] = None,
        mfa_verified: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new access token
        
        Args:
            user_id: User identifier
            roles: User roles
            permissions: User permissions
            session_id: Optional session ID
            mfa_verified: Whether MFA has been verified
            ip_address: Client IP address
            user_agent: Client user agent
            additional_claims: Additional custom claims
            
        Returns:
            Encoded JWT access token
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)
        jti = self._generate_jti()
        
        payload = TokenPayload(
            sub=user_id,
            jti=jti,
            type=TokenType.ACCESS,
            iat=now,
            exp=expires,
            nbf=now,
            iss=self.config.issuer,
            aud=self.config.audience,
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            mfa_verified=mfa_verified,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        claims = payload.to_dict()
        if additional_claims:
            claims.update(additional_claims)
        
        # Store token metadata
        self._token_metadata[jti] = {
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "user_id": user_id,
            "type": "access",
            "session_id": session_id,
        }
        
        return jwt.encode(
            claims,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
    
    def create_refresh_token(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create a new refresh token
        
        Args:
            user_id: User identifier
            session_id: Optional session ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Encoded JWT refresh token
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self.config.refresh_token_expire_days)
        jti = self._generate_jti()
        
        payload = TokenPayload(
            sub=user_id,
            jti=jti,
            type=TokenType.REFRESH,
            iat=now,
            exp=expires,
            nbf=now,
            iss=self.config.issuer,
            aud=self.config.audience,
            roles=[],
            permissions=[],
            session_id=session_id,
            mfa_verified=True,  # Refresh tokens imply MFA verified
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Store token metadata
        self._token_metadata[jti] = {
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "user_id": user_id,
            "type": "refresh",
            "session_id": session_id,
        }
        
        return jwt.encode(
            payload.to_dict(),
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
    
    def decode_token(
        self,
        token: str,
        verify_type: Optional[TokenType] = None
    ) -> TokenPayload:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
            verify_type: Expected token type (optional)
            
        Returns:
            Decoded token payload
            
        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
            TokenBlacklistedError: If token is blacklisted
        """
        try:
            # Decode without verification first to get JTI
            unverified = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            jti = unverified.get("jti")
            
            # Check if blacklisted
            if jti and self.is_blacklisted(jti):
                raise TokenBlacklistedError("Token has been revoked")
            
            # Now decode with full verification
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience,
            )
            
            token_payload = TokenPayload.from_dict(payload)
            
            # Verify token type if specified
            if verify_type and token_payload.type != verify_type:
                raise TokenInvalidError(
                    f"Invalid token type. Expected {verify_type.value}, "
                    f"got {token_payload.type.value}"
                )
            
            return token_payload
            
        except ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")
    
    def verify_access_token(self, token: str) -> TokenPayload:
        """Verify an access token"""
        return self.decode_token(token, verify_type=TokenType.ACCESS)
    
    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify a refresh token"""
        return self.decode_token(token, verify_type=TokenType.REFRESH)
    
    def blacklist_token(self, jti: str, reason: str = "logout") -> None:
        """
        Blacklist a token by its JTI
        
        Args:
            jti: JWT ID to blacklist
            reason: Reason for blacklisting
        """
        self._blacklisted_tokens.add(jti)
        if jti in self._token_metadata:
            self._token_metadata[jti]["blacklisted"] = True
            self._token_metadata[jti]["blacklist_reason"] = reason
            self._token_metadata[jti]["blacklisted_at"] = datetime.now(timezone.utc).isoformat()
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted"""
        return jti in self._blacklisted_tokens
    
    def blacklist_user_tokens(self, user_id: str, reason: str = "security") -> int:
        """
        Blacklist all tokens for a user
        
        Args:
            user_id: User ID
            reason: Reason for blacklisting
            
        Returns:
            Number of tokens blacklisted
        """
        count = 0
        for jti, metadata in self._token_metadata.items():
            if metadata.get("user_id") == user_id and jti not in self._blacklisted_tokens:
                self.blacklist_token(jti, reason)
                count += 1
        return count
    
    def rotate_refresh_token(
        self,
        refresh_token: str,
        roles: List[str],
        permissions: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Rotate refresh token - creates new access and refresh tokens
        
        Args:
            refresh_token: Current refresh token
            roles: User roles
            permissions: User permissions
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with new access_token and refresh_token
        """
        # Verify and decode the refresh token
        payload = self.verify_refresh_token(refresh_token)
        
        # Blacklist the old refresh token (one-time use)
        self.blacklist_token(payload.jti, "token_rotation")
        
        # Create new tokens
        new_access = self.create_access_token(
            user_id=payload.sub,
            roles=roles,
            permissions=permissions,
            session_id=payload.session_id,
            mfa_verified=True,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        new_refresh = self.create_refresh_token(
            user_id=payload.sub,
            session_id=payload.session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiration time"""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        except Exception:
            pass
        return None
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired token metadata
        
        Returns:
            Number of tokens cleaned up
        """
        now = datetime.now(timezone.utc)
        to_remove = []
        
        for jti, metadata in self._token_metadata.items():
            expires_at = metadata.get("expires_at")
            if expires_at:
                expiry = datetime.fromisoformat(expires_at)
                if expiry < now:
                    to_remove.append(jti)
        
        for jti in to_remove:
            del self._token_metadata[jti]
            self._blacklisted_tokens.discard(jti)
        
        return len(to_remove)
    
    def get_token_info(self, jti: str) -> Optional[Dict]:
        """Get metadata for a token"""
        return self._token_metadata.get(jti)
    
    def create_token_pair(
        self,
        user_id: str,
        roles: List[str],
        permissions: List[str],
        session_id: Optional[str] = None,
        mfa_verified: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create both access and refresh tokens
        
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        """
        access_token = self.create_access_token(
            user_id=user_id,
            roles=roles,
            permissions=permissions,
            session_id=session_id,
            mfa_verified=mfa_verified,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.config.access_token_expire_minutes * 60,
        }
