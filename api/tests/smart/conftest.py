"""
Pytest fixtures for API tests.
"""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_jwt_secret():
    """Mock JWT secret for testing."""
    return os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only")


@pytest.fixture
def sample_user_data():
    """Create sample user data."""
    return {
        "username": "testuser",
        "role": "admin",
        "sub": "testuser",
        "exp": datetime.now(timezone.utc).timestamp() + 3600,
    }


@pytest.fixture
def sample_token(sample_user_data, mock_jwt_secret):
    """Create a sample JWT token."""
    import jwt

    return jwt.encode(sample_user_data, mock_jwt_secret, algorithm="HS256")


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock(return_value={"action": "ping"})
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.query = MagicMock(return_value=session)
    session.filter = MagicMock(return_value=session)
    session.first = MagicMock(return_value=None)
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.close = MagicMock()
    return session
