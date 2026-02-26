"""
Comprehensive Core Module Tests - Target: 80%+ Coverage

Tests für:
- core/orchestrator.py
- core/state_machine.py  
- core/cache.py
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Test State Machine
from core.state_machine import (
    StateType,
    HistoryType,
    StateEvent,
    State,
    Transition,
    AdvancedStateMachine,
    PentestStateMachine,
)


class TestStateMachine:
    """Tests for StateMachine classes."""

    @pytest.fixture
    def sm(self):
        """Create a test state machine."""
        return AdvancedStateMachine()

    def test_state_type_enum(self):
        """Test StateType enum."""
        assert StateType.INITIAL.value == "initial"
        assert StateType.FINAL.value == "final"

    def test_history_type_enum(self):
        """Test HistoryType enum."""
        assert HistoryType.NONE.value == "none"
        assert HistoryType.SHALLOW.value == "shallow"

    def test_state_event_creation(self):
        """Test StateEvent creation."""
        event = StateEvent(name="test_event", payload={"key": "value"})
        assert event.name == "test_event"
        assert event.payload == {"key": "value"}

    def test_state_creation(self):
        """Test State creation."""
        state = State(name="test_state")
        assert state.name == "test_state"
        assert state.state_type == StateType.NORMAL

    def test_state_with_type(self):
        """Test State with specific type."""
        state = State(name="initial", state_type=StateType.INITIAL)
        assert state.state_type == StateType.INITIAL

    def test_transition_creation(self):
        """Test Transition creation."""
        transition = Transition(source="state1", target="state2", event="go")
        assert transition.source == "state1"
        assert transition.target == "state2"
        assert transition.event == "go"

    def test_advanced_state_machine_init(self, sm):
        """Test AdvancedStateMachine initialization."""
        assert sm is not None

    def test_pentest_state_machine_init(self):
        """Test PentestStateMachine initialization."""
        psm = PentestStateMachine()
        assert psm is not None


# Test Cache
from core.cache import (
    CacheStats,
    CacheBackend,
    MemoryCache,
    generate_cache_key,
    get_cached_cve,
    cache_cve,
)


class TestCacheStats:
    """Tests for CacheStats."""

    def test_cache_stats_init(self):
        """Test CacheStats initialization."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_gets == 0

    def test_cache_stats_hit_rate(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        stats.hits = 80
        stats.misses = 20
        stats.total_gets = 100
        assert stats.hit_rate == 80.0

    def test_cache_stats_hit_rate_zero(self):
        """Test hit rate with zero gets."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0


class TestMemoryCache:
    """Tests for MemoryCache."""

    @pytest.fixture
    async def cache(self):
        """Create a test cache."""
        cache = MemoryCache(max_size=100)
        yield cache
        await cache.clear()

    @pytest.mark.asyncio
    async def test_memory_cache_get_set(self, cache):
        """Test get and set operations."""
        await cache.set("key", "value")
        result = await cache.get("key")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_memory_cache_get_missing(self, cache):
        """Test getting missing key."""
        result = await cache.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_delete(self, cache):
        """Test delete operation."""
        await cache.set("key", "value")
        await cache.delete("key")
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_clear(self, cache):
        """Test clear operation."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_memory_cache_exists(self, cache):
        """Test exists operation."""
        await cache.set("key", "value")
        assert await cache.exists("key") is True
        assert await cache.exists("missing") is False

    @pytest.mark.asyncio
    async def test_memory_cache_ttl_expired(self, cache):
        """Test TTL expiration."""
        await cache.set("key", "value", ttl=0.001)
        await asyncio.sleep(0.01)
        result = await cache.get("key")
        assert result is None


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_generate_cache_key_simple(self):
        """Test simple key generation."""
        key = generate_cache_key("func", (1, 2), {"a": 3})
        assert key is not None
        assert isinstance(key, str)

    def test_generate_cache_key_consistency(self):
        """Test key generation consistency."""
        key1 = generate_cache_key("func", (1, 2), {"a": 3})
        key2 = generate_cache_key("func", (1, 2), {"a": 3})
        assert key1 == key2

    def test_generate_cache_key_different(self):
        """Test different keys for different inputs."""
        key1 = generate_cache_key("func", (1,), {})
        key2 = generate_cache_key("func", (2,), {})
        assert key1 != key2


class TestCVEFunctions:
    """Tests for CVE cache functions."""

    @pytest.mark.asyncio
    async def test_cache_and_get_cve(self):
        """Test caching and retrieving CVE."""
        cve_data = {"id": "CVE-2021-1234", "severity": "high"}
        await cache_cve("CVE-2021-1234", cve_data)
        result = await get_cached_cve("CVE-2021-1234")
        assert result == cve_data

    @pytest.mark.asyncio
    async def test_get_cached_cve_missing(self):
        """Test getting non-existent CVE."""
        result = await get_cached_cve("CVE-NOT-EXIST")
        assert result is None
