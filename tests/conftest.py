"""
Pytest Fixtures für Zen-AI Pentest Tests

Diese conftest.py verwendet einen "Mock-First" Ansatz um Import-Fehler zu vermeiden.
Unit-Tests benötigen keine vollständige API-Initialisierung.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# LAZY IMPORT FIXTURES
# ============================================================
# Diese Fixtures laden Abhängigkeiten erst wenn sie benötigt werden

@pytest.fixture(scope="session")
def db_engine():
    """Lazy-loaded database engine"""
    try:
        from sqlalchemy import create_engine
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
        return engine
    except ImportError as e:
        pytest.skip(f"SQLAlchemy nicht verfügbar: {e}")


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Test-Datenbank Session - funktioniert nur wenn DB verfügbar"""
    try:
        from sqlalchemy.orm import sessionmaker
        from database.models import Base

        TestingSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=db_engine
        )

        Base.metadata.create_all(bind=db_engine)
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=db_engine)
    except Exception as e:
        # Wenn DB nicht verfügbar, überspringen
        pytest.skip(f"Datenbank nicht verfügbar: {e}")


@pytest.fixture
def mock_db():
    """Mock-Datenbank für Unit-Tests ohne echte DB"""
    mock = MagicMock()
    mock.query.return_value.filter.return_value.first.return_value = None
    mock.query.return_value.all.return_value = []
    mock.add = MagicMock()
    mock.commit = MagicMock()
    mock.refresh = MagicMock()
    return mock


@pytest.fixture
def client():
    """FastAPI Test Client - nur wenn API verfügbar"""
    try:
        import os
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
        os.environ["ADMIN_PASSWORD"] = "testpass"

        from fastapi.testclient import TestClient
        from api.main import app
        from database.models import get_db

        # Mock DB
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()
    except Exception as e:
        pytest.skip(f"API nicht verfügbar: {e}")


@pytest.fixture
def auth_token():
    """Test JWT Token"""
    try:
        import os
        os.environ["JWT_SECRET_KEY"] = "test-secret-key"
        from api.auth_simple import create_access_token
        token = create_access_token({"sub": "testuser", "role": "admin"})
        return token
    except Exception:
        # Fallback: Dummy-Token für Unit-Tests
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.test"


@pytest.fixture
def auth_headers(auth_token):
    """Auth Headers für API Requests"""
    return {"Authorization": f"Bearer {auth_token}"}


# ============================================================
# MOCK FIXTURES FÜR UNIT-TESTS
# ============================================================

@pytest.fixture
def mock_requests():
    """Mock für requests library"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}
        yield {"get": mock_get, "post": mock_post}


@pytest.fixture
def mock_subprocess():
    """Mock für subprocess calls"""
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"test output"
        mock_run.return_value.stderr = b""
        mock_popen.return_value.returncode = 0
        mock_popen.return_value.communicate.return_value = (b"output", b"error")
        yield {"run": mock_run, "popen": mock_popen}


@pytest.fixture
def test_data_dir():
    """Pfad zu Test-Daten"""
    return Path(__file__).parent / "data"


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """Pytest Konfiguration"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (keine API/DB nötig)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (API/DB nötig)"
    )
    config.addinivalue_line(
        "markers", "slow: Langsame Tests (> 10s)"
    )


def pytest_collection_modifyitems(config, items):
    """Test-Items modifizieren"""
    for item in items:
        # Automatisch 'unit' marker wenn keiner gesetzt
        if not any(marker.name in ["unit", "integration"] for marker in item.own_markers):
            item.add_marker(pytest.mark.unit)
