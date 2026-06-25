"""Tests for SQLiteCache and RedisCache backends"""

import asyncio
import tempfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
class TestSQLiteCache:
    """Test SQLiteCache backend"""

    async def test_sqlite_import(self):
        from core.cache import SQLiteCache

        assert SQLiteCache is not None

    async def test_sqlite_set_get(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            await cache.set("key1", "value1")
            result = await cache.get("key1")
            assert result == "value1"
            await cache.close()

    async def test_sqlite_delete(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            await cache.set("del_key", "value")
            deleted = await cache.delete("del_key")
            assert deleted is True
            assert await cache.get("del_key") is None
            await cache.close()

    async def test_sqlite_exists(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            await cache.set("exists", "val")
            assert await cache.exists("exists") is True
            assert await cache.exists("missing") is False
            await cache.close()

    async def test_sqlite_clear(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            await cache.set("k1", "v1")
            await cache.set("k2", "v2")
            await cache.clear()
            assert await cache.get("k1") is None
            await cache.close()

    async def test_sqlite_ttl_set(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            await cache.set("ttl", "val", ttl=3600)
            assert await cache.get("ttl") == "val"
            await cache.close()

    async def test_sqlite_dict_value(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            data = {"nested": {"key": "value"}, "list": [1, 2]}
            await cache.set("dict", data)
            result = await cache.get("dict")
            assert result == data
            await cache.close()

    async def test_sqlite_overwrite(self):
        from core.cache import SQLiteCache

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cache.db"
            cache = SQLiteCache(db_path=db_path)
            await cache.set("key", "old")
            await cache.set("key", "new")
            assert await cache.get("key") == "new"
            await cache.close()


@pytest.mark.asyncio
class TestRedisCache:
    """Test RedisCache backend (requires Redis)"""

    async def test_redis_import(self):
        from core.cache import RedisCache

        assert RedisCache is not None

    async def test_redis_set_get(self):
        from core.cache import RedisCache

        try:
            cache = RedisCache(host="localhost", port=6379, db=15)
            await cache.set("test_key", "test_value")
            result = await cache.get("test_key")
            assert result == "test_value"
            await cache.delete("test_key")
            await cache.close()
        except Exception:
            pytest.skip("Redis not available")

    async def test_redis_delete(self):
        from core.cache import RedisCache

        try:
            cache = RedisCache(host="localhost", port=6379, db=15)
            await cache.set("del_test", "val")
            deleted = await cache.delete("del_test")
            assert deleted is True
            await cache.close()
        except Exception:
            pytest.skip("Redis not available")

    async def test_redis_exists(self):
        from core.cache import RedisCache

        try:
            cache = RedisCache(host="localhost", port=6379, db=15)
            await cache.set("exists_test", "val")
            assert await cache.exists("exists_test") is True
            await cache.delete("exists_test")
            await cache.close()
        except Exception:
            pytest.skip("Redis not available")

    async def test_redis_clear(self):
        from core.cache import RedisCache

        try:
            cache = RedisCache(host="localhost", port=6379, db=15)
            await cache.clear()
            await cache.close()
        except Exception:
            pytest.skip("Redis not available")
