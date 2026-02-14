"""
Pytest Fixtures für Zen-AI Pentest Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import Base, get_db
from api.main import app

# Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override für Test-Datenbank"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Erstellt frische Test-Datenbank pro Test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """FastAPI Test Client mit Test-DB"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_token():
    """Test JWT Token"""
    from api.auth_simple import create_access_token
    token = create_access_token({"sub": "testuser", "role": "admin"})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Auth Headers für API Requests"""
    return {"Authorization": f"Bearer {auth_token}"}
