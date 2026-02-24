"""
JWT Authentication für Zen-AI-Pentest API

SECURITY NOTES:
- All secrets are loaded from environment variables
- Never commit actual secrets to version control
- Use .env file locally, proper secret management in production
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

# =============================================================================
# Configuration - Load from environment variables
# =============================================================================

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if (
    not SECRET_KEY
    or SECRET_KEY == "your-super-secret-jwt-key-change-this-in-production"
):
    # Generate a random key for development (not for production!)
    import warnings

    warnings.warn(
        "JWT_SECRET_KEY not set or using default! Using random key for development. "
        "Set JWT_SECRET_KEY environment variable for production!",
        RuntimeWarning,
    )
    SECRET_KEY = secrets.token_hex(32)

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# =============================================================================
# Password Functions
# =============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifiziert Passwort"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashed Passwort"""
    return pwd_context.hash(password)


# =============================================================================
# JWT Token Functions
# =============================================================================


def create_access_token(
    data: Dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Erstellt JWT Token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict]:
    """Decodiert JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        return None


# =============================================================================
# FastAPI Dependencies
# =============================================================================


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """FastAPI Dependency für Token-Verifizierung"""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiration
    exp = payload.get("exp")
    if exp and datetime.now(timezone.utc).timestamp() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def check_permissions(user: Dict, required_role: str) -> bool:
    """Prüft ob User die benötigte Rolle hat"""
    user_role = user.get("role", "viewer")

    roles_hierarchy = {"viewer": 1, "operator": 2, "admin": 3}

    user_level = roles_hierarchy.get(user_role, 0)
    required_level = roles_hierarchy.get(required_role, 0)

    return user_level >= required_level


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """Erfordert Admin-Rolle"""
    user = await verify_token(credentials)

    if not check_permissions(user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user


async def require_operator(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """Erfordert Operator oder höhere Rolle"""
    user = await verify_token(credentials)

    if not check_permissions(user, "operator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator privileges required",
        )

    return user


# =============================================================================
# API Key Authentication
# =============================================================================

# In-memory store for API keys (use database in production!)
API_KEYS: Dict[str, Dict] = {}


def verify_api_key(api_key: str) -> Optional[Dict]:
    """Verifiziert API Key"""
    return API_KEYS.get(api_key)


def create_api_key(user_id: int, name: str) -> str:
    """Erstellt neuen API Key"""
    key = secrets.token_urlsafe(32)
    API_KEYS[key] = {
        "user_id": user_id,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return key


def revoke_api_key(api_key: str) -> bool:
    """Widerruft API Key"""
    if api_key in API_KEYS:
        del API_KEYS[api_key]
        return True
    return False
