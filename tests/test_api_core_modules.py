"""Tests for api/core/agents.py and api/core/scans.py stubs."""

import pytest
from api.core.agents import AgentManager, agent_manager
from api.core.scans import ScanManager, scan_manager


class TestAgentManager:
    """Test AgentManager stub."""

    def test_init(self):
        """Test initialization."""
        manager = AgentManager()
        assert manager.agents == {}

    def test_create_agent(self):
        """Test creating agent."""
        manager = AgentManager()
        agent_id = manager.create_agent({"name": "test_agent", "type": "recon"})

        assert agent_id == "agent_0"
        assert agent_id in manager.agents
        assert manager.agents[agent_id]["name"] == "test_agent"
        assert manager.agents[agent_id]["type"] == "recon"

    def test_create_multiple_agents(self):
        """Test creating multiple agents."""
        manager = AgentManager()
        id1 = manager.create_agent({"name": "agent1"})
        id2 = manager.create_agent({"name": "agent2"})

        assert id1 == "agent_0"
        assert id2 == "agent_1"

    def test_get_agent_existing(self):
        """Test getting existing agent."""
        manager = AgentManager()
        agent_id = manager.create_agent({"name": "test"})
        agent = manager.get_agent(agent_id)

        assert agent is not None
        assert agent["name"] == "test"

    def test_get_agent_nonexistent(self):
        """Test getting non-existent agent."""
        manager = AgentManager()
        agent = manager.get_agent("nonexistent")

        assert agent is None

    def test_list_agents_empty(self):
        """Test listing agents when empty."""
        manager = AgentManager()
        agents = manager.list_agents()

        assert agents == []

    def test_list_agents(self):
        """Test listing agents."""
        manager = AgentManager()
        manager.create_agent({"name": "agent1"})
        manager.create_agent({"name": "agent2"})
        agents = manager.list_agents()

        assert len(agents) == 2

    def test_global_instance(self):
        """Test global agent_manager instance."""
        assert isinstance(agent_manager, AgentManager)


class TestScanManager:
    """Test ScanManager stub."""

    def test_init(self):
        """Test initialization."""
        manager = ScanManager()
        assert manager.scans == {}

    def test_create_scan(self):
        """Test creating scan."""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")

        assert scan_id == "scan_0"
        assert scan_id in manager.scans
        assert manager.scans[scan_id]["target"] == "example.com"
        assert manager.scans[scan_id]["type"] == "nmap"
        assert manager.scans[scan_id]["status"] == "pending"
        assert "created_at" in manager.scans[scan_id]

    def test_create_multiple_scans(self):
        """Test creating multiple scans."""
        manager = ScanManager()
        id1 = manager.create_scan("target1.com", "nmap")
        id2 = manager.create_scan("target2.com", "zap")

        assert id1 == "scan_0"
        assert id2 == "scan_1"

    def test_get_scan_existing(self):
        """Test getting existing scan."""
        manager = ScanManager()
        scan_id = manager.create_scan("example.com", "nmap")
        scan = manager.get_scan(scan_id)

        assert scan is not None
        assert scan["target"] == "example.com"

    def test_get_scan_nonexistent(self):
        """Test getting non-existent scan."""
        manager = ScanManager()
        scan = manager.get_scan("nonexistent")

        assert scan is None

    def test_list_scans_empty(self):
        """Test listing scans when empty."""
        manager = ScanManager()
        scans = manager.list_scans()

        assert scans == []

    def test_list_scans(self):
        """Test listing scans."""
        manager = ScanManager()
        manager.create_scan("target1.com", "nmap")
        manager.create_scan("target2.com", "zap")
        scans = manager.list_scans()

        assert len(scans) == 2

    def test_global_instance(self):
        """Test global scan_manager instance."""
        assert isinstance(scan_manager, ScanManager)
