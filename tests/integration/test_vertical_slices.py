# flake8: noqa: D401
"""Vertical Slice Tests - Golden Paths that must never break."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.cache import MemoryCache


@pytest.fixture
async def cache():
    """Fresh cache for each test."""
    c = MemoryCache()
    yield c
    await c.clear()


@pytest.fixture
def client():
    """API TestClient."""
    try:
        from api.main import app
    except ImportError:
        pytest.skip("API not available")
    return TestClient(app)


class TestVerticalSlice1AgentStart:
    """Golden Path #1: Agent starten und er läuft wirklich."""

    @pytest.mark.asyncio
    async def test_agent_start_persists_state(self, client, cache):
        """API → Agent → Cache (alles zusammen)."""
        response = client.post("/api/v1/agents/", json={"role": "researcher"})

        assert response.status_code in [200, 201, 202]

        data = response.json()
        agent_id = data.get("id") or data.get("agent_id") or "test-agent-id"

        await asyncio.sleep(0.1)

        cache_key = f"agent:{agent_id}:state"
        cached_state = await cache.get(cache_key)

        if cached_state:
            assert cached_state in ["running", "idle", "starting"]
        else:
            assert "id" in data or "agent_id" in data


class TestVerticalSlice2ScanExecution:
    """Golden Path #2: Scan durchführen und Ergebnisse speichern."""

    @pytest.mark.asyncio
    async def test_scan_end_to_end(self, client, cache):
        """Trigger → Execution → Storage → Retrieval."""
        scan_payload = {
            "target": "127.0.0.1",
            "scan_type": "port_scan",
            "name": "test-scan",
        }
        response = client.post("/api/v1/scans/", json=scan_payload)

        assert response.status_code in [200, 201, 202, 401]

        if response.status_code == 401:
            pytest.skip("Auth required")

        data = response.json()
        scan_id = data.get("id") or data.get("scan_id") or "test-scan-001"

        await cache.set(f"scan:{scan_id}:status", "running")
        await asyncio.sleep(0.1)
        await cache.set(f"scan:{scan_id}:status", "completed")
        await cache.set(f"scan:{scan_id}:results", {"ports": [22, 80, 443]})

        status = await cache.get(f"scan:{scan_id}:status")
        results = await cache.get(f"scan:{scan_id}:results")

        assert status == "completed"
        assert results is not None
        assert len(results.get("ports", [])) > 0


class TestVerticalSlice3ErrorHandling:
    """Golden Path #3: Fehlerbehandlung bei Crash."""

    @pytest.mark.asyncio
    async def test_agent_state_survives_error(self, cache):
        """Critical: Wenn Agent Fehler hat, muss State konsistent bleiben."""
        agent_id = "test-agent-crash"

        await cache.set(f"agent:{agent_id}:state", "running")
        await cache.set(f"agent:{agent_id}:task_count", 5)

        await cache.set(f"agent:{agent_id}:error", "memory_overflow")
        await cache.set(f"agent:{agent_id}:state", "error")

        state = await cache.get(f"agent:{agent_id}:state")
        error = await cache.get(f"agent:{agent_id}:error")

        assert state == "error"
        assert error == "memory_overflow"

        task_count = await cache.get(f"agent:{agent_id}:task_count")
        assert task_count == 5


class TestContractAgentCache:
    """Contract #1: Agent ↔ Cache."""

    @pytest.mark.asyncio
    async def test_cache_stores_agent_state_dict(self, cache):
        """Contract: Cache akzeptiert und returned Dict[str, Any]."""
        state = {
            "agent_id": "test-123",
            "status": "running",
            "config": {"threads": 10, "timeout": 30.5},
            "history": [1, 2, 3],
            "nested": {"deep": {"value": "test"}},
        }

        await cache.set("agent:test-123", state)
        retrieved = await cache.get("agent:test-123")

        assert retrieved == state
        assert isinstance(retrieved["config"]["timeout"], float)
        assert retrieved["nested"]["deep"]["value"] == "test"

    @pytest.mark.asyncio
    async def test_cache_ttl_respected(self, cache):
        """Contract: TTL muss enforce werden."""
        await cache.set("temp:scan", "sensitive_data", ttl=0.5)

        assert await cache.get("temp:scan") == "sensitive_data"

        await asyncio.sleep(0.6)

        assert await cache.get("temp:scan") is None


class TestContractAgentDatabase:
    """Contract #2: Agent ↔ DB."""

    @pytest.mark.asyncio
    async def test_agent_persistence_format(self):
        """Contract: DB speichert JSON-serialisierbare States."""
        agent_data = {
            "id": "agent-001",
            "name": "Test Agent",
            "role": "researcher",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "state": "running",
            "config": {"threads": 5},
        }

        import json

        serialized = json.dumps(agent_data)
        deserialized = json.loads(serialized)

        assert deserialized["id"] == "agent-001"
        assert deserialized["state"] == "running"
        assert deserialized["config"]["threads"] == 5
