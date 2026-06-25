"""SQLite cache tests"""

import pytest


class TestSQLiteCache:
    """Test SQLite cache"""

    def test_sqlite_cache_import(self):
        from core.cache import SQLiteCache

        assert SQLiteCache is not None

    def test_sqlite_cache_has_set(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "set")

    def test_sqlite_cache_has_get(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "get")

    def test_sqlite_cache_has_delete(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "delete")

    def test_sqlite_cache_has_exists(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "exists")

    def test_sqlite_cache_has_clear(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "clear")

    def test_sqlite_cache_has_get_stats(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "get_stats")

    def test_sqlite_cache_has_close(self):
        from core.cache import SQLiteCache

        assert hasattr(SQLiteCache, "close")
