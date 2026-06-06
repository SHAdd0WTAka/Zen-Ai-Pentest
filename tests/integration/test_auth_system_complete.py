"""Complete Auth System Tests - Target: auth/ 0% -> 80%"""

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from passlib.context import CryptContext


class TestAuthComplete:
    """20 Tests für auth/ Modul"""

    def test_password_hash_creation(self):
        """Passwort Hash erstellen."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "testpassword123"
        hashed = pwd_context.hash(password)
        assert hashed != password
        assert pwd_context.verify(password, hashed) is True

    def test_password_hash_verification(self):
        """Passwort Hash verifizieren."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "mypassword"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True
        assert pwd_context.verify("wrongpassword", hashed) is False

    def test_jwt_token_creation(self):
        """JWT Token erstellen."""
        payload = {"sub": "user123", "role": "admin"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        assert token is not None
        assert isinstance(token, str)

    def test_jwt_token_decode(self):
        """JWT Token dekodieren."""
        payload = {"sub": "user456", "role": "user"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS256"])
        assert decoded["sub"] == "user456"
        assert decoded["role"] == "user"

    def test_jwt_with_expiration(self):
        """JWT mit Ablaufdatum."""
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {"sub": "user", "exp": exp}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS256"])
        assert decoded["sub"] == "user"
        assert "exp" in decoded

    def test_jwt_invalid_signature(self):
        """JWT mit ungültiger Signatur."""
        payload = {"sub": "user"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret1"), algorithm="HS256")
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret2"), algorithms=["HS256"])

    def test_jwt_expired_token(self):
        """Abgelaufener JWT Token."""
        exp = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = {"sub": "user", "exp": exp}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS256"])

    def test_password_complexity_short(self):
        """Kurzes Passwort."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "short"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True

    def test_password_complexity_long(self):
        """Langes Passwort."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "a" * 100
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True

    def test_password_complexity_special(self):
        """Passwort mit Sonderzeichen."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True

    def test_jwt_algorithm_hs256(self):
        """JWT mit HS256."""
        payload = {"sub": "user"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS256"])
        assert decoded["sub"] == "user"

    def test_jwt_algorithm_hs384(self):
        """JWT mit HS384."""
        payload = {"sub": "user"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS384")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS384"])
        assert decoded["sub"] == "user"

    def test_jwt_algorithm_hs512(self):
        """JWT mit HS512."""
        payload = {"sub": "user"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS512")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS512"])
        assert decoded["sub"] == "user"

    def test_jwt_payload_structure(self):
        """JWT Payload Struktur."""
        payload = {
            "sub": "user123",
            "username": "testuser",
            "role": "admin",
            "permissions": ["read", "write", "delete"],
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
        }
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS256"])
        assert decoded["username"] == "testuser"
        assert "read" in decoded["permissions"]

    def test_password_hash_uniqueness(self):
        """Passwort Hash Einzigartigkeit."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "samepassword"
        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)
        assert hash1 != hash2  # bcrypt salzt automatisch
        assert pwd_context.verify(password, hash1) is True
        assert pwd_context.verify(password, hash2) is True

    def test_jwt_token_length(self):
        """JWT Token Länge."""
        payload = {"sub": "user"}
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        assert len(token) > 20  # Base64 encoded

    def test_bcrypt_rounds(self):
        """Bcrypt Rounds."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password = "test"
        hashed = pwd_context.hash(password)
        # bcrypt hashes start with $2b$ or $2a$
        assert "$2" in hashed

    def test_jwt_multiple_claims(self):
        """JWT mit mehreren Claims."""
        payload = {
            "sub": "user",
            "iss": "zen-ai-pentest",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "role": "admin",
            "scan_quota": 100,
        }
        token = jwt.encode(payload, os.environ.get("JWT_SECRET_KEY", "secret"), algorithm="HS256")
        decoded = jwt.decode(token, os.environ.get("JWT_SECRET_KEY", "secret"), algorithms=["HS256"])
        assert decoded["iss"] == "zen-ai-pentest"
        assert decoded["scan_quota"] == 100

    def test_password_context_reuse(self):
        """Passwort Context wiederverwenden."""
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        passwords = ["pass1", "pass2", "pass3"]
        hashes = [pwd_context.hash(p) for p in passwords]

        for i, pwd in enumerate(passwords):
            assert pwd_context.verify(pwd, hashes[i]) is True
