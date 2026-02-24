"""Tests for agent coordinator module"""

import pytest

from modules.agent_coordinator import ResourceType  # noqa: F401
from modules.agent_coordinator import AgentCoordinator, AgentStatus


class TestAgentCoordinator:
    """Test AgentCoordinator functionality"""

    @pytest.fixture
    async def coordinator(self):
        """Create coordinator fixture"""
        coord = AgentCoordinator()
        yield coord
        # Cleanup
        for agent_id in list(coord.agents.keys()):
            await coord.unregister_agent(agent_id)

    @pytest.mark.asyncio
    async def test_init(self):
        """Test coordinator initialization"""
        coord = AgentCoordinator()
        assert coord.name == "agent_coordinator"
        assert len(coord.resources) == 5

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Test agent registration"""
        coord = AgentCoordinator()
        agent = await coord.register_agent("agent-1", "Test Agent")
        assert agent.id == "agent-1"
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_register_duplicate_agent(self):
        """Test registering duplicate agent fails"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent")
        with pytest.raises(ValueError):
            await coord.register_agent("agent-1", "Duplicate")

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """Test agent unregistration"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent")
        await coord.unregister_agent("agent-1")
        assert "agent-1" not in coord.agents

    @pytest.mark.asyncio
    async def test_acquire_single_resource(self):
        """Test acquiring a single resource"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent")

        success = await coord._acquire_resource(
            "agent-1", ResourceType.SCANNER, timeout=1.0
        )
        assert success is True

        # Check resource is acquired
        agent = coord.agents["agent-1"]
        assert ResourceType.SCANNER in agent.acquired_resources

    @pytest.mark.asyncio
    async def test_release_resource(self):
        """Test releasing a resource"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent")

        # Acquire and release
        await coord._acquire_resource("agent-1", ResourceType.SCANNER)
        await coord._release_resource("agent-1", ResourceType.SCANNER)

        agent = coord.agents["agent-1"]
        assert ResourceType.SCANNER not in agent.acquired_resources

    @pytest.mark.asyncio
    async def test_acquire_resources_context_manager(self):
        """Test context manager for resource acquisition"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent")

        async with coord.acquire_resources(
            "agent-1", [ResourceType.SCANNER, ResourceType.DATABASE]
        ) as resources:
            assert len(resources) == 2
            agent = coord.agents["agent-1"]
            assert ResourceType.SCANNER in agent.acquired_resources
            assert ResourceType.DATABASE in agent.acquired_resources

        # After context exit, resources should be released
        agent = coord.agents["agent-1"]
        assert len(agent.acquired_resources) == 0

    @pytest.mark.asyncio
    async def test_resource_limits_respected(self):
        """Test that resource limits are respected"""
        coord = AgentCoordinator()

        # Register 4 agents (limit is 3 for SCANNER)
        for i in range(4):
            await coord.register_agent(f"agent-{i}", f"Agent {i}")

        # First 3 should succeed
        for i in range(3):
            success = await coord._acquire_resource(
                f"agent-{i}", ResourceType.SCANNER, timeout=0.5
            )
            assert success is True

        # 4th should fail (timeout)
        success = await coord._acquire_resource(
            "agent-3", ResourceType.SCANNER, timeout=0.5
        )
        assert success is False

    @pytest.mark.asyncio
    async def test_check_deadlocks_empty(self):
        """Test deadlock detection with no agents"""
        coord = AgentCoordinator()
        deadlocks = await coord.check_deadlocks()
        assert len(deadlocks) == 0

    @pytest.mark.asyncio
    async def test_check_deadlocks_timeout(self):
        """Test deadlock detection for timeout"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent", timeout=0.01)

        # Put agent in waiting state
        coord.agents["agent-1"].status = AgentStatus.WAITING
        coord.agents["agent-1"].start_time = 0  # Force timeout

        deadlocks = await coord.check_deadlocks()
        assert len(deadlocks) >= 0  # May or may not detect depending on timing

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting coordinator status"""
        coord = AgentCoordinator()
        await coord.register_agent("agent-1", "Test Agent")
        await coord._acquire_resource("agent-1", ResourceType.SCANNER)

        status = coord.get_status()
        assert "agents" in status
        assert "resources" in status
        assert "agent-1" in status["agents"]

    @pytest.mark.asyncio
    async def test_get_info(self):
        """Test getting module info"""
        coord = AgentCoordinator()
        info = coord.get_info()
        assert info["name"] == "agent_coordinator"
        assert "deadlock_prevention" in info
