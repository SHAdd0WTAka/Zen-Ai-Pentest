"""
Unit Tests for Async Database Module
Week 1 Goal: Core Infrastructure coverage
"""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestAsyncDatabaseManager:
    """Test AsyncDatabaseManager class"""

    def test_singleton_pattern(self):
        from core.async_database import AsyncDatabaseManager

        # First instance
        db1 = AsyncDatabaseManager()
        # Second instance should be same object
        db2 = AsyncDatabaseManager()

        assert db1 is db2

    def test_database_url_from_env(self):
        from core.async_database import AsyncDatabaseManager

        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://test:test@localhost/test"},
        ):
            db = AsyncDatabaseManager()
            assert db.database_url == "postgresql://test:test@localhost/test"

    def test_default_sqlite_url(self):
        from core.async_database import AsyncDatabaseManager

        with patch.dict(os.environ, {}, clear=True):
            db = AsyncDatabaseManager()
            assert "sqlite" in db.database_url.lower()

    @pytest.mark.asyncio
    async def test_health_check(self):
        from core.async_database import AsyncDatabaseManager

        db = AsyncDatabaseManager()
        db._engine = Mock()

        # Mock successful health check
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        db._engine.connect = AsyncMock(return_value=mock_conn)

        result = await db.health_check()

        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        from core.async_database import AsyncDatabaseManager

        db = AsyncDatabaseManager()
        db._engine = Mock()

        # Mock failed health check
        db._engine.connect = AsyncMock(side_effect=Exception("Connection failed"))

        result = await db.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result

    def test_methods_exist(self):
        from core.async_database import AsyncDatabaseManager

        db = AsyncDatabaseManager()

        # Check all CRUD methods exist
        assert hasattr(db, "create_scan")
        assert hasattr(db, "get_scan")
        assert hasattr(db, "get_scans")
        assert hasattr(db, "update_scan_status")
        assert hasattr(db, "create_finding")
        assert hasattr(db, "get_finding")
        assert hasattr(db, "get_findings")
        assert hasattr(db, "bulk_create_findings")
        assert hasattr(db, "get_user")
        assert hasattr(db, "get_user_by_username")
        assert hasattr(db, "create_report")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
