"""Test async database"""

import pytest


class TestAsyncDatabase:
    """Test async database"""

    def test_import(self):
        from core.async_database import AsyncDatabaseManager

        assert AsyncDatabaseManager is not None

    def test_creation(self):
        from core.async_database import AsyncDatabaseManager

        db = AsyncDatabaseManager()
        assert db is not None

    def test_has_connect(self):
        from core.async_database import AsyncDatabaseManager

        db = AsyncDatabaseManager()
        assert hasattr(db, "connect") or hasattr(db, "initialize")
