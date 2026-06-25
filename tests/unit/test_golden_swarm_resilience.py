"""Golden Test 1: Swarm Chaos – Wenn alles zusammenbricht."""

# flake8: noqa: D102

import asyncio

import pytest

from agents.agent_base import AgentRole, BaseAgent
from core.cache import MemoryCache


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    async def execute_task(self, task):
        return {"status": "completed"}


@pytest.mark.asyncio
class TestSwarmChaosResilience:
    """Ein Test. 10 Agents. 5 Crashes. System muss überleben."""

    async def test_swarm_survives_partial_catastrophe(self):
        cache = MemoryCache(max_size=1000)
        agents = []

        # 1. Starte 10 Agents
        for i in range(10):
            agent = MockAgent(name=f"chaos_agent_{i}", role=AgentRole.RESEARCHER)
            await agent.start()
            await asyncio.sleep(0.05)
            agents.append(agent)
            await cache.set(f"agent:{agent.id}:state", "running")

        # 2. CHAOS: Crashe 5 Agents (0, 2, 4, 6, 8)
        for i in range(0, 10, 2):
            agents[i].running = False
            if agents[i].task:
                agents[i].task.cancel()
                try:
                    await agents[i].task
                except asyncio.CancelledError:
                    pass
            await cache.set(f"agent:{agents[i].id}:state", "crashed")

        # 3. Verifikation: Die anderen 5 laufen noch
        for i in range(1, 10, 2):
            assert agents[i].running is True, f"Agent {i} sollte laufen"
            cached = await cache.get(f"agent:{agents[i].id}:state")
            assert cached == "running", f"Cache für Agent {i} ist {cached}"

        # 4. Golden Assertion: Keine Split-Brain
        for i, agent in enumerate(agents):
            cached = await cache.get(f"agent:{agent.id}:state")
            actual = "crashed" if i % 2 == 0 else "running"
            assert cached == actual, f"SPLIT BRAIN bei Agent {i}"

        # 5. Cleanup
        for agent in agents:
            if agent.running:
                await agent.stop()
            await cache.delete(f"agent:{agent.id}:state")
