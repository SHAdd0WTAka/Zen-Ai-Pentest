"""
Einfache JWT Authentication für Zen-AI Pentest API
"""
import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from typing import Optional, Dict

# Konfiguration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Stunden

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer(auto_error=False)

# In-memory user store (Production: Datenbank nutzen!)
# Format: {username: {"password": hashed_password, "role": "admin|user"}}
USERS_DB = {
    "admin": {
        "password": pwd_context.hash("admin123"),  # Ändern in Production!
        "role": "admin"
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifiziert Passwort gegen Hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Erstellt Passwort-Hash"""
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authentifiziert User und gibt User-Daten zurück"""
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    return {"username": username, "role": user["role"]}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Erstellt JWT Access Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Verifiziert JWT Token aus Authorization Header
    Verwendet als Dependency in Protected Routes
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "user")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {"username": username, "role": role}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(user: Dict = Depends(verify_token)) -> Dict:
    """Prüft ob User Admin-Rechte hat"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user


# Optional: User Management Funktionen
def create_user(username: str, password: str, role: str = "user") -> bool:
    """Erstellt neuen User"""
    if username in USERS_DB:
        return False
    
    USERS_DB[username] = {
        "password": get_password_hash(password),
        "role": role
    }
    return True


def list_users() -> Dict:
    """Listet alle Users (ohne Passwörter)"""
    return {k: {"role": v["role"]} for k, v in USERS_DB.items()}
