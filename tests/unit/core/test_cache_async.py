"""
Async tests for core/cache module
Properly handles async/await patterns
"""

import asyncio
import json
import os
import tempfile
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest


@pytest.mark.asyncio
class TestMemoryCacheAsync:
    """Test MemoryCache with async support"""

    @pytest.fixture
    async def memory_cache(self):
        """Create a MemoryCache instance"""
        from core.cache import MemoryCache

        cache = MemoryCache()
        yield cache
        await cache.clear()

    @pytest.mark.timeout(10)
    async def test_memory_cache_set_get(self, memory_cache):
        """Test async set and get"""
        await memory_cache.set("key1", "value1")
        result = await memory_cache.get("key1")
        assert result == "value1"

    @pytest.mark.timeout(10)
    async def test_memory_cache_get_nonexistent(self, memory_cache):
        """Test getting non-existent key"""
        result = await memory_cache.get("nonexistent")
        assert result is None

    @pytest.mark.timeout(10)
    async def test_memory_cache_delete(self, memory_cache):
        """Test async delete"""
        await memory_cache.set("key1", "value1")
        await memory_cache.delete("key1")
        result = await memory_cache.get("key1")
        assert result is None

    @pytest.mark.timeout(10)
    async def test_memory_cache_exists(self, memory_cache):
        """Test async exists"""
        await memory_cache.set("key1", "value1")
        assert await memory_cache.exists("key1") is True
        assert await memory_cache.exists("nonexistent") is False

    @pytest.mark.timeout(10)
    async def test_memory_cache_clear(self, memory_cache):
        """Test async clear"""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.clear()
        assert await memory_cache.get("key1") is None
        assert await memory_cache.get("key2") is None

    @pytest.mark.timeout(10)
    async def test_memory_cache_ttl_expired(self, memory_cache):
        """Test TTL expiration"""
        await memory_cache.set("key1", "value1", ttl=0.001)
        await asyncio.sleep(0.01)
        result = await memory_cache.get("key1")
        assert result is None

    @pytest.mark.timeout(10)
    async def test_memory_cache_ttl_not_expired(self, memory_cache):
        """Test TTL not expired"""
        await memory_cache.set("key1", "value1", ttl=3600)
        result = await memory_cache.get("key1")
        assert result == "value1"


@pytest.mark.asyncio
class TestLongTermMemoryAsync:
    """Test LongTermMemory async operations"""

    @pytest.fixture
    async def ltm(self, tmp_path):
        """Create a LongTermMemory instance"""
        from autonomous.memory import LongTermMemory

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(exist_ok=True)
        ltm = LongTermMemory(storage_path=str(cache_dir / "test.json"))
        yield ltm

    @pytest.mark.timeout(10)
    async def test_ltm_add_with_embedding(self, ltm):
        """Test adding entry with auto-generated embedding"""
        from autonomous.memory import MemoryEntry

        entry = MemoryEntry(id="test-1", content="This is a test entry", memory_type="thought")

        await ltm.add(entry)

        assert entry.id in ltm.entries
        assert entry.embedding is not None
        assert len(entry.embedding) == 128

    @pytest.mark.timeout(10)
    async def test_ltm_semantic_search(self, ltm):
        """Test semantic search"""
        from autonomous.memory import MemoryEntry

        await ltm.add(MemoryEntry(id="1", content="Port scanning with nmap tool", memory_type="action"))
        await ltm.add(MemoryEntry(id="2", content="SQL injection found in login form", memory_type="finding"))

        results = await ltm.search("vulnerability security", limit=3)

        assert len(results) > 0

    @pytest.mark.timeout(10)
    async def test_ltm_get_recent(self, ltm):
        """Test getting recent entries"""
        from autonomous.memory import MemoryEntry

        for i in range(5):
            await ltm.add(MemoryEntry(id=f"{i}", content=f"Entry {i}", memory_type="action"))

        recent = await ltm.get_recent(3)
        assert len(recent) == 3

    @pytest.mark.timeout(10)
    async def test_ltm_persist_and_load(self, ltm):
        """Test persistence and loading"""
        from autonomous.memory import MemoryEntry

        await ltm.add(MemoryEntry(id="1", content="Test entry", memory_type="action"))

        # Persist
        await ltm._persist()

        # Verify file was created
        from pathlib import Path

        assert Path(ltm.storage_path).exists()


@pytest.mark.asyncio
class TestCacheManagerAsync:
    """Test CacheManager async operations"""

    @pytest.fixture
    async def cache_manager(self):
        """Create a CacheManager instance"""
        from core.cache import CacheManager, MemoryCache

        cm = CacheManager()
        backend = MemoryCache()
        cm.register_backend("default", backend)
        yield cm

    @pytest.mark.timeout(10)
    async def test_cm_set_get(self, cache_manager):
        """Test set/get through manager"""
        await cache_manager.set("key1", "value1", backend="default")
        result = await cache_manager.get("key1", backend="default")
        assert result == "value1"

    @pytest.mark.timeout(10)
    async def test_cm_delete(self, cache_manager):
        """Test delete through manager"""
        await cache_manager.set("key1", "value1")
        await cache_manager.delete("key1")
        assert await cache_manager.get("key1") is None

    @pytest.mark.timeout(10)
    async def test_cm_clear(self, cache_manager):
        """Test clear through manager"""
        await cache_manager.set("key1", "value1")
        await cache_manager.clear()
        assert await cache_manager.get("key1") is None

    @pytest.mark.timeout(10)
    async def test_cm_exists(self, cache_manager):
        """Test exists through manager"""
        await cache_manager.set("key1", "value1")
        assert await cache_manager.exists("key1") is True
        assert await cache_manager.exists("nonexistent") is False


@pytest.mark.asyncio
class TestCacheDecoratorAsync:
    """Test async cache decorator"""

    @pytest.mark.timeout(10)
    async def test_cache_decorator_basic(self):
        """Test basic cache decorator functionality"""
        from core.cache import MemoryCache, cache_result

        cache = MemoryCache()
        call_count = 0

        @cache_result(cache=cache, ttl=3600)
        async def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await expensive_function(5)
        result2 = await expensive_function(5)

        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    @pytest.mark.timeout(10)
    async def test_cache_decorator_different_args(self):
        """Test cache with different arguments"""
        from core.cache import MemoryCache, cache_result

        cache = MemoryCache()
        call_count = 0

        @cache_result(cache=cache, ttl=3600)
        async def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        result1 = await expensive_function(1, 2)
        result2 = await expensive_function(3, 4)

        assert result1 == 3
        assert result2 == 7
        assert call_count == 2


class TestCacheHelpers:
    """Test cache helper functions (sync)"""

    def test_generate_cache_key_string(self):
        """Test cache key generation from string"""
        from core.cache import generate_cache_key

        key = generate_cache_key("test_data")
        assert isinstance(key, str)
        assert len(key) == 64

    def test_generate_cache_key_dict(self):
        """Test cache key generation from dict"""
        from core.cache import generate_cache_key

        data = {"key": "value", "num": 123}
        key = generate_cache_key(data)
        assert isinstance(key, str)
        assert len(key) == 64

    def test_generate_cache_key_consistency(self):
        """Test that same input generates same key"""
        from core.cache import generate_cache_key

        key1 = generate_cache_key({"a": 1, "b": 2})
        key2 = generate_cache_key({"a": 1, "b": 2})
        assert key1 == key2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
