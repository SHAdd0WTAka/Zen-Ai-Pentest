"""
Comprehensive tests for agent_comm/v2/src/registry.py
Target: 80%+ Coverage
"""

import time
import threading
import pytest
from agent_comm.v2.src.registry import (
    AgentRegistry,
    AgentIdentity,
    AgentSession,
    AgentStatus,
)


class TestAgentIdentity:
    """Tests for AgentIdentity dataclass."""
    
    def test_default_values(self):
        """Test default identity values."""
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        assert identity.agent_id == "agent-1"
        assert identity.session_id == "session-1"
        assert identity.version == "1.0.0"
        assert identity.capabilities == []
        assert identity.metadata == {}
        assert identity.registered_at <= time.time()
    
    def test_custom_values(self):
        """Test custom identity values."""
        identity = AgentIdentity(
            agent_id="agent-1",
            session_id="session-1",
            version="2.0.0",
            capabilities=["scan", "exploit"],
            metadata={"region": "eu-west-1"}
        )
        
        assert identity.version == "2.0.0"
        assert identity.capabilities == ["scan", "exploit"]
        assert identity.metadata == {"region": "eu-west-1"}


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def test_init(self):
        """Test registry initialization."""
        registry = AgentRegistry()
        
        assert registry.get_agent_count() == 0
        assert registry.get_online_count() == 0
    
    def test_register_single_agent(self):
        """Test registering a single agent."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        result = registry.register(identity, "token-1")
        
        assert result is True
        assert registry.get_agent_count() == 1
        assert registry.get_online_count() == 1
    
    def test_register_duplicate_agent(self):
        """Test registering duplicate agent fails."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.register(identity, "token-2")
        
        assert result is False
        assert registry.get_agent_count() == 1
    
    def test_unregister_existing(self):
        """Test unregistering existing agent."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.unregister("agent-1")
        
        assert result is True
        assert registry.get_agent_count() == 0
    
    def test_unregister_nonexistent(self):
        """Test unregistering non-existent agent."""
        registry = AgentRegistry()
        
        result = registry.unregister("nonexistent")
        
        assert result is False
    
    def test_get_existing(self):
        """Test getting existing agent."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.get("agent-1")
        
        assert result is not None
        assert result.agent_id == "agent-1"
    
    def test_get_nonexistent(self):
        """Test getting non-existent agent."""
        registry = AgentRegistry()
        
        result = registry.get("nonexistent")
        
        assert result is None
    
    def test_get_session_existing(self):
        """Test getting session for existing agent."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        session = registry.get_session("agent-1")
        
        assert session is not None
        assert session.agent_id == "agent-1"
        assert session.session_token == "token-1"
        assert session.status == AgentStatus.ONLINE
    
    def test_get_session_nonexistent(self):
        """Test getting session for non-existent agent."""
        registry = AgentRegistry()
        
        session = registry.get_session("nonexistent")
        
        assert session is None
    
    def test_list_all_empty(self):
        """Test listing all agents when empty."""
        registry = AgentRegistry()
        
        result = registry.list_all()
        
        assert result == []
    
    def test_list_all_multiple(self):
        """Test listing multiple agents."""
        registry = AgentRegistry()
        
        registry.register(AgentIdentity(agent_id="agent-1", session_id="s1"), "t1")
        registry.register(AgentIdentity(agent_id="agent-2", session_id="s2"), "t2")
        
        result = registry.list_all()
        
        assert len(result) == 2
        assert {a.agent_id for a in result} == {"agent-1", "agent-2"}
    
    def test_list_online(self):
        """Test listing online agents."""
        registry = AgentRegistry()
        
        registry.register(AgentIdentity(agent_id="agent-1", session_id="s1"), "t1")
        registry.register(AgentIdentity(agent_id="agent-2", session_id="s2"), "t2")
        registry.update_status("agent-2", AgentStatus.OFFLINE)
        
        result = registry.list_online()
        
        assert len(result) == 1
        assert result[0].agent_id == "agent-1"
    
    def test_update_status_existing(self):
        """Test updating status for existing agent."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.update_status("agent-1", AgentStatus.BUSY)
        
        assert result is True
        assert registry.get_status("agent-1") == AgentStatus.BUSY
    
    def test_update_status_nonexistent(self):
        """Test updating status for non-existent agent."""
        registry = AgentRegistry()
        
        result = registry.update_status("nonexistent", AgentStatus.BUSY)
        
        assert result is False
    
    def test_update_heartbeat_existing(self):
        """Test updating heartbeat for existing agent."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.update_heartbeat("agent-1", cpu_usage=50.0, memory_usage=60.0, active_tasks=3)
        
        assert result is True
        session = registry.get_session("agent-1")
        assert session.cpu_usage == 50.0
        assert session.memory_usage == 60.0
        assert session.active_tasks == 3
    
    def test_update_heartbeat_nonexistent(self):
        """Test updating heartbeat for non-existent agent."""
        registry = AgentRegistry()
        
        result = registry.update_heartbeat("nonexistent")
        
        assert result is False
    
    def test_update_heartbeat_sets_online(self):
        """Test that heartbeat sets offline agent to online."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        registry.update_status("agent-1", AgentStatus.OFFLINE)
        
        registry.update_heartbeat("agent-1")
        
        assert registry.get_status("agent-1") == AgentStatus.ONLINE
    
    def test_get_status_unknown(self):
        """Test getting status for unknown agent."""
        registry = AgentRegistry()
        
        result = registry.get_status("nonexistent")
        
        assert result == AgentStatus.UNKNOWN
    
    def test_verify_session_valid(self):
        """Test verifying valid session."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.verify_session("agent-1", "token-1")
        
        assert result is True
    
    def test_verify_session_invalid(self):
        """Test verifying invalid session."""
        registry = AgentRegistry()
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        result = registry.verify_session("agent-1", "wrong-token")
        
        assert result is False
    
    def test_verify_session_nonexistent(self):
        """Test verifying session for non-existent agent."""
        registry = AgentRegistry()
        
        result = registry.verify_session("nonexistent", "token")
        
        assert result is False
    
    def test_cleanup_stale_agents(self):
        """Test cleaning up stale agents."""
        registry = AgentRegistry(heartbeat_timeout=0.1)
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        time.sleep(0.15)  # Wait for timeout
        
        count = registry.cleanup_stale_agents()
        
        assert count == 1
        assert registry.get_status("agent-1") == AgentStatus.OFFLINE
    
    def test_cleanup_no_stale(self):
        """Test cleanup when no stale agents."""
        registry = AgentRegistry(heartbeat_timeout=60.0)
        identity = AgentIdentity(agent_id="agent-1", session_id="session-1")
        
        registry.register(identity, "token-1")
        
        count = registry.cleanup_stale_agents()
        
        assert count == 0
        assert registry.get_status("agent-1") == AgentStatus.ONLINE
    
    def test_get_capabilities(self):
        """Test getting agent capabilities."""
        registry = AgentRegistry()
        identity = AgentIdentity(
            agent_id="agent-1",
            session_id="session-1",
            capabilities=["scan", "exploit", "report"]
        )
        
        registry.register(identity, "token-1")
        caps = registry.get_capabilities("agent-1")
        
        assert caps == {"scan", "exploit", "report"}
    
    def test_get_capabilities_nonexistent(self):
        """Test getting capabilities for non-existent agent."""
        registry = AgentRegistry()
        
        caps = registry.get_capabilities("nonexistent")
        
        assert caps == set()
    
    def test_find_by_capability(self):
        """Test finding agents by capability."""
        registry = AgentRegistry()
        
        registry.register(
            AgentIdentity(agent_id="agent-1", session_id="s1", capabilities=["scan"]),
            "t1"
        )
        registry.register(
            AgentIdentity(agent_id="agent-2", session_id="s2", capabilities=["scan", "exploit"]),
            "t2"
        )
        registry.register(
            AgentIdentity(agent_id="agent-3", session_id="s3", capabilities=["report"]),
            "t3"
        )
        
        result = registry.find_by_capability("scan")
        
        assert len(result) == 2
        assert {a.agent_id for a in result} == {"agent-1", "agent-2"}
    
    def test_find_by_capability_none(self):
        """Test finding agents by non-existent capability."""
        registry = AgentRegistry()
        
        registry.register(AgentIdentity(agent_id="agent-1", session_id="s1"), "t1")
        
        result = registry.find_by_capability("nonexistent")
        
        assert result == []


class TestAgentRegistryConcurrency:
    """Concurrency tests for AgentRegistry."""
    
    def test_concurrent_registration(self):
        """Test concurrent agent registration."""
        registry = AgentRegistry()
        errors = []
        
        def register_agent(agent_id):
            try:
                identity = AgentIdentity(agent_id=agent_id, session_id=f"s-{agent_id}")
                registry.register(identity, f"t-{agent_id}")
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=register_agent, args=(f"agent-{i}",))
            for i in range(100)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert registry.get_agent_count() == 100
    
    def test_concurrent_status_updates(self):
        """Test concurrent status updates."""
        registry = AgentRegistry()
        
        # Register agents first
        for i in range(50):
            identity = AgentIdentity(agent_id=f"agent-{i}", session_id=f"s-{i}")
            registry.register(identity, f"t-{i}")
        
        errors = []
        
        def update_status(agent_id):
            try:
                registry.update_status(agent_id, AgentStatus.BUSY)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=update_status, args=(f"agent-{i}",))
            for i in range(50)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        # All should be BUSY
        for i in range(50):
            assert registry.get_status(f"agent-{i}") == AgentStatus.BUSY
