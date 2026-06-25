"""
Conftest for tests/unit/api/ — provides API-specific fixtures that override
the broken auth_headers/test_client from the root conftest.
"""

import os
from unittest.mock import MagicMock  # noqa: E402

import pytest  # noqa: E402

# Set env vars at module level so they're present when api modules are imported.
os.environ.setdefault("ADMIN_PASSWORD", "testpass")
os.environ.setdefault("SECRET_KEY", "your-secret-key-change-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("RATE_LIMIT_ANONYMOUS_RPM", "10000")
os.environ.setdefault("RATE_LIMIT_AUTHENTICATED_RPM", "10000")
os.environ.setdefault("RATE_LIMIT_AUTH_ENDPOINT_RPM", "10000")
os.environ.setdefault("RATE_LIMIT_BURST", "10000")


@pytest.fixture
def mock_db_session():
    """Function-scoped mock database session, shared with test_client via override."""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.all.return_value = []
    return session


_MOCK_USER = {"sub": "admin", "role": "admin", "username": "admin"}


@pytest.fixture(autouse=True)
def _reset_rate_limit_buckets():
    """Reset in-memory rate-limit buckets before every API test."""
    try:
        from api.rate_limiter import rate_limit_storage

        rate_limit_storage.buckets.clear()
    except Exception:
        pass
    yield


@pytest.fixture
def test_client(mock_db_session):
    """Test client with mock DB and v1 auth overrides."""
    from fastapi.testclient import TestClient

    from api.main import app
    from database.models import get_db

    # Collect all verify_token / optional_auth variants from each router module
    # (they may be the same object or local fallbacks depending on import success).
    override_keys = set()

    def _collect(module_path, names):
        try:
            import importlib

            mod = importlib.import_module(module_path)
            for name in names:
                fn = getattr(mod, name, None)
                if fn is not None:
                    override_keys.add(fn)
        except Exception:
            pass

    _collect("api.routes.v1.auth", ["verify_token", "optional_auth"])
    _collect("api.routes.v1.scans", ["verify_token", "optional_auth"])
    _collect("api.routes.v1.tools", ["verify_token", "optional_auth"])
    _collect("api.routes.v1.findings", ["verify_token"])
    _collect("api.auth_deps", ["verify_token", "optional_auth"])

    # Bypass CSRF protection
    try:
        from api.csrf_protection import require_csrf

        app.dependency_overrides[require_csrf] = lambda: True
    except Exception:
        pass

    app.dependency_overrides[get_db] = lambda: mock_db_session
    for fn in override_keys:
        app.dependency_overrides[fn] = lambda: _MOCK_USER

    # Reset in-memory rate-limit buckets so tests don't exhaust each other's quota
    try:
        from api.rate_limiter import rate_limit_storage

        rate_limit_storage.buckets.clear()
    except Exception:
        pass

    client = TestClient(app)
    yield client

    app.dependency_overrides.pop(get_db, None)
    for fn in override_keys:
        app.dependency_overrides.pop(fn, None)


@pytest.fixture
def client(test_client):
    """Alias for test_client used by some test modules."""
    return test_client


@pytest.fixture
def auth_headers():
    """Auth headers — value doesn't matter since verify_token is overridden."""
    return {"Authorization": "Bearer test-token"}
