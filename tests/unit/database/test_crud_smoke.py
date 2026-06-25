"""Smoke tests for database/crud.py"""

import pytest

from database.crud import (
    AsyncDatabaseSession,
    get_async_db_session,
    get_dashboard_stats,
    get_finding_stats,
    get_scans_with_counts,
)


class TestAsyncDatabaseSession:
    def test_singleton(self):
        s1 = AsyncDatabaseSession()
        s2 = AsyncDatabaseSession()
        assert s1 is s2

    def test_initialized_flag(self):
        s = AsyncDatabaseSession()
        assert s._initialized is True


class TestGetAsyncDbSession:
    def test_returns_session(self):
        session = get_async_db_session()
        assert isinstance(session, AsyncDatabaseSession)

    def test_singleton(self):
        s1 = get_async_db_session()
        s2 = get_async_db_session()
        assert s1 is s2


class TestModuleFunctions:
    def test_get_dashboard_stats_requires_db(self):
        with pytest.raises(Exception):
            get_dashboard_stats(None)

    def test_get_finding_stats_requires_db(self):
        with pytest.raises(Exception):
            get_finding_stats(None, scan_id=1)

    def test_get_scans_with_counts_requires_db(self):
        with pytest.raises(Exception):
            get_scans_with_counts(None)


class TestModuleAttributes:
    def test___all___defined(self):
        from database import crud

        assert hasattr(crud, "__all__")
        assert "create_scan" in crud.__all__
        assert "async_create_scan" in crud.__all__
        assert "AsyncDatabaseSession" in crud.__all__
