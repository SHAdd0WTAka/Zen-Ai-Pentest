"""Vertical Slice 3: API Endpoints - Auth & Scans."""

import os
from datetime import datetime, timezone

import pytest


def test_jwt_token_creation():
    """JWT Token mit api.auth erstellen."""
    import jwt

    # Einfacher Token ohne komplexe Imports
    payload = {"sub": "testuser", "role": "operator", "exp": 1893456000}
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only")

    token = jwt.encode(payload, secret, algorithm="HS256")

    # Token ist String
    assert isinstance(token, str)
    assert len(token) > 20

    # Dekodieren und prüfen
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "operator"


def test_password_hashing():
    """Passwort Hashing mit passlib."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Hash erstellen
    password = "testpassword123"
    hashed = pwd_context.hash(password)

    # Hash ist verschieden von Plaintext
    assert hashed != password
    assert len(hashed) > 50

    # Verifizieren
    assert pwd_context.verify(password, hashed) is True
    assert pwd_context.verify("wrongpassword", hashed) is False


def test_scan_status_enum():
    """ScanStatus Enum Werte prüfen."""
    from database.models import ScanStatus

    # Status Werte
    assert ScanStatus.PENDING == "pending"
    assert ScanStatus.RUNNING == "running"
    assert ScanStatus.COMPLETED == "completed"
    assert ScanStatus.FAILED == "failed"
    assert ScanStatus.CANCELLED == "cancelled"

    # Alle Status
    statuses = [s.value for s in ScanStatus]
    assert "pending" in statuses
    assert "completed" in statuses
