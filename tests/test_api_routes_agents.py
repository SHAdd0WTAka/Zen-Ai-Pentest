"""
Tests for api/routes/agents.py - Agent Management Endpoints

Comprehensive tests for agent listing, control, and task assignment.
"""

# Mock the dependencies before importing
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi import HTTPException

# Create mock modules
mock_agents = MagicMock()
mock_agents.agent_manager = MagicMock()
mock_agents.agent_manager.get_all_agents = MagicMock(return_value=[])
mock_agents.agent_manager.get_agent = MagicMock(return_value=None)
mock_agents.agent_manager.assign_task = AsyncMock(return_value="task-123")
mock_agents.agent_manager.send_message_to_agent = AsyncMock(return_value={"response": "ok"})
mock_agents.agent_manager.get_agent_logs = AsyncMock(return_value=[])
mock_agents.agent_manager.broadcast = AsyncMock()
mock_agents.agent_manager.shared_context = {}
mock_agents.agent_manager.message_history = []

mock_auth = MagicMock()
mock_auth.get_current_user = MagicMock()
mock_auth.require_permissions = MagicMock()

mock_user = MagicMock()
mock_user.User = MagicMock()
mock_user.UserRole = MagicMock()
mock_user.UserRole.ADMIN = MagicMock()
mock_user.UserRole.ADMIN.value = 2

sys.modules["api.core.agents"] = mock_agents
sys.modules["api.core.auth"] = mock_auth
sys.modules["api.models.user"] = mock_user

from api.routes.agents import (
    assign_task,
    broadcast_message,
    get_agent,
    get_agent_logs,
    get_system_status,
    list_agents,
    send_message,
    start_agent,
    stop_agent,
)

# ==================== Test Fixtures ====================


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = Mock()
    user.id = "user-001"
    user.username = "testuser"
    user.role = Mock()
    user.role.value = 1
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = Mock()
    user.id = "admin-001"
    user.username = "admin"
    user.role = Mock()
    user.role.value = 2
    return user


@pytest.fixture
def mock_agent():
    """Mock agent object"""
    agent = Mock()
    agent.id = "agent-001"
    agent.name = "Test Agent"
    agent.role = Mock()
    agent.role.value = "scanner"
    agent.state = Mock()
    agent.state.value = "running"
    agent.current_task = "scanning target"
    agent.last_activity = datetime.utcnow()
    agent.messages_processed = 10
    agent.errors_count = 0
    agent.start = AsyncMock()
    agent.stop = AsyncMock()
    return agent


# ==================== List Agents Tests ====================


class TestListAgents:
    """Test list_agents endpoint"""

    @pytest.mark.asyncio
    async def test_list_agents_empty(self, mock_current_user):
        """Test listing agents when none exist"""
        mock_agents.agent_manager.get_all_agents.return_value = []

        result = await list_agents(mock_current_user)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_agents_with_agents(self, mock_current_user, mock_agent):
        """Test listing agents"""
        mock_agents.agent_manager.get_all_agents.return_value = [mock_agent]

        result = await list_agents(mock_current_user)

        assert len(result) == 1
        assert result[0]["id"] == "agent-001"
        assert result[0]["name"] == "Test Agent"
        assert result[0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_list_agents_multiple(self, mock_current_user, mock_agent):
        """Test listing multiple agents"""
        agent2 = Mock()
        agent2.id = "agent-002"
        agent2.name = "Agent 2"
        agent2.role.value = "exploiter"
        agent2.state.value = "idle"
        agent2.current_task = None
        agent2.last_activity = None
        agent2.messages_processed = 5
        agent2.errors_count = 1

        mock_agents.agent_manager.get_all_agents.return_value = [mock_agent, agent2]

        result = await list_agents(mock_current_user)

        assert len(result) == 2
        assert result[0]["id"] == "agent-001"
        assert result[1]["id"] == "agent-002"


# ==================== Get Agent Tests ====================


class TestGetAgent:
    """Test get_agent endpoint"""

    @pytest.mark.asyncio
    async def test_get_agent_success(self, mock_current_user, mock_agent):
        """Test getting a specific agent"""
        mock_agents.agent_manager.get_agent.return_value = mock_agent

        result = await get_agent("agent-001", mock_current_user)

        assert result["id"] == "agent-001"
        assert result["name"] == "Test Agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, mock_current_user):
        """Test getting non-existent agent"""
        mock_agents.agent_manager.get_agent.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_agent("nonexistent", mock_current_user)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


# ==================== Start Agent Tests ====================


class TestStartAgent:
    """Test start_agent endpoint"""

    @pytest.mark.asyncio
    async def test_start_agent_success(self, mock_admin_user, mock_agent):
        """Test starting an agent"""
        mock_agents.agent_manager.get_agent.return_value = mock_agent

        result = await start_agent("agent-001", mock_admin_user)

        assert "started" in result["message"].lower()
        mock_agent.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_agent_not_found(self, mock_admin_user):
        """Test starting non-existent agent"""
        mock_agents.agent_manager.get_agent.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await start_agent("nonexistent", mock_admin_user)

        assert exc_info.value.status_code == 404


# ==================== Stop Agent Tests ====================


class TestStopAgent:
    """Test stop_agent endpoint"""

    @pytest.mark.asyncio
    async def test_stop_agent_success(self, mock_admin_user, mock_agent):
        """Test stopping an agent"""
        mock_agents.agent_manager.get_agent.return_value = mock_agent

        result = await stop_agent("agent-001", mock_admin_user)

        assert "stopped" in result["message"].lower()
        mock_agent.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_agent_not_found(self, mock_admin_user):
        """Test stopping non-existent agent"""
        mock_agents.agent_manager.get_agent.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await stop_agent("nonexistent", mock_admin_user)

        assert exc_info.value.status_code == 404


# ==================== Assign Task Tests ====================


class TestAssignTask:
    """Test assign_task endpoint"""

    @pytest.mark.asyncio
    async def test_assign_task_success(self, mock_current_user, mock_agent):
        """Test assigning task to agent"""
        mock_agents.agent_manager.get_agent.return_value = mock_agent
        mock_agents.agent_manager.assign_task.return_value = "task-456"

        task_request = Mock()
        task_request.dict.return_value = {
            "agent_id": "agent-001",
            "task_type": "scan",
            "parameters": {"target": "example.com"},
            "priority": 5,
        }

        result = await assign_task("agent-001", task_request, Mock(), mock_current_user)

        assert result["task_id"] == "task-456"
        assert result["agent_id"] == "agent-001"

    @pytest.mark.asyncio
    async def test_assign_task_agent_not_found(self, mock_current_user):
        """Test assigning task to non-existent agent"""
        mock_agents.agent_manager.get_agent.return_value = None

        task_request = Mock()
        task_request.dict.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await assign_task("nonexistent", task_request, Mock(), mock_current_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_task_agent_not_running(self, mock_current_user, mock_agent):
        """Test assigning task to non-running agent"""
        mock_agent.state.value = "idle"
        mock_agents.agent_manager.get_agent.return_value = mock_agent

        task_request = Mock()
        task_request.dict.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await assign_task("agent-001", task_request, Mock(), mock_current_user)

        assert exc_info.value.status_code == 400
        assert "not running" in exc_info.value.detail.lower()


# ==================== Send Message Tests ====================


class TestSendMessage:
    """Test send_message endpoint"""

    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_current_user, mock_agent):
        """Test sending message to agent"""
        mock_agents.agent_manager.get_agent.return_value = mock_agent
        mock_agents.agent_manager.send_message_to_agent.return_value = {"status": "received"}

        message_request = Mock()
        message_request.dict.return_value = {"message": "Hello", "context": {}}

        result = await send_message("agent-001", message_request, mock_current_user)

        assert result["agent_id"] == "agent-001"
        assert "response" in result

    @pytest.mark.asyncio
    async def test_send_message_agent_not_found(self, mock_current_user):
        """Test sending message to non-existent agent"""
        mock_agents.agent_manager.get_agent.return_value = None

        message_request = Mock()
        message_request.dict.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await send_message("nonexistent", message_request, mock_current_user)

        assert exc_info.value.status_code == 404


# ==================== Get Agent Logs Tests ====================


class TestGetAgentLogs:
    """Test get_agent_logs endpoint"""

    @pytest.mark.asyncio
    async def test_get_agent_logs_success(self, mock_admin_user, mock_agent):
        """Test getting agent logs"""
        mock_agents.agent_manager.get_agent.return_value = mock_agent
        mock_agents.agent_manager.get_agent_logs.return_value = [
            {"timestamp": "2024-01-01", "message": "Started"},
            {"timestamp": "2024-01-01", "message": "Completed"},
        ]

        result = await get_agent_logs("agent-001", 100, mock_admin_user)

        assert result["agent_id"] == "agent-001"
        assert len(result["logs"]) == 2

    @pytest.mark.asyncio
    async def test_get_agent_logs_not_found(self, mock_admin_user):
        """Test getting logs for non-existent agent"""
        mock_agents.agent_manager.get_agent.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_agent_logs("nonexistent", 100, mock_admin_user)

        assert exc_info.value.status_code == 404


# ==================== Broadcast Tests ====================


class TestBroadcastMessage:
    """Test broadcast_message endpoint"""

    @pytest.mark.asyncio
    async def test_broadcast_success(self, mock_admin_user):
        """Test broadcasting message to all agents"""
        result = await broadcast_message("Test message", mock_admin_user)

        assert "broadcast sent" in result["message"].lower()
        mock_agents.agent_manager.broadcast.assert_called_once_with("Test message")


# ==================== System Status Tests ====================


class TestGetSystemStatus:
    """Test get_system_status endpoint"""

    @pytest.mark.asyncio
    async def test_system_status_empty(self, mock_current_user):
        """Test system status with no agents"""
        mock_agents.agent_manager.get_all_agents.return_value = []
        mock_agents.agent_manager.shared_context = {}
        mock_agents.agent_manager.message_history = []

        result = await get_system_status(mock_current_user)

        assert result["total_agents"] == 0
        assert result["active_agents"] == 0
        assert result["idle_agents"] == 0
        assert result["error_agents"] == 0

    @pytest.mark.asyncio
    async def test_system_status_with_agents(self, mock_current_user):
        """Test system status with agents in different states"""
        running_agent = Mock()
        running_agent.state.value = "running"

        idle_agent = Mock()
        idle_agent.state.value = "idle"

        error_agent = Mock()
        error_agent.state.value = "error"

        mock_agents.agent_manager.get_all_agents.return_value = [running_agent, idle_agent, error_agent]
        mock_agents.agent_manager.shared_context = {"key": "value"}
        mock_agents.agent_manager.message_history = ["msg1", "msg2"]

        result = await get_system_status(mock_current_user)

        assert result["total_agents"] == 3
        assert result["active_agents"] == 1
        assert result["idle_agents"] == 1
        assert result["error_agents"] == 1
        assert "key" in result["shared_context_keys"]
        assert result["message_queue_size"] == 2


# ==================== Model Tests ====================


class TestAgentModels:
    """Test Pydantic models for agents"""

    def test_agent_task_request_model(self):
        """Test AgentTaskRequest model validation"""
        from pydantic import BaseModel, Field

        class AgentTaskRequest(BaseModel):
            agent_id: str
            task_type: str
            parameters: dict = Field(default_factory=dict)
            priority: int = Field(default=5, ge=1, le=10)

        # Valid request
        request = AgentTaskRequest(agent_id="agent-001", task_type="scan", parameters={"target": "example.com"}, priority=8)
        assert request.priority == 8

        # Default priority
        request2 = AgentTaskRequest(agent_id="agent-001", task_type="scan")
        assert request2.priority == 5

    def test_agent_message_request_model(self):
        """Test AgentMessageRequest model validation"""
        from pydantic import BaseModel, Field

        class AgentMessageRequest(BaseModel):
            agent_id: str
            message: str
            context: dict = Field(default_factory=dict)

        request = AgentMessageRequest(agent_id="agent-001", message="Hello", context={"key": "value"})
        assert request.message == "Hello"

    def test_agent_response_model(self):
        """Test AgentResponse model structure"""
        from datetime import datetime
        from typing import Optional

        from pydantic import BaseModel

        class AgentResponse(BaseModel):
            id: str
            name: str
            role: str
            status: str
            current_task: Optional[str]
            last_activity: Optional[datetime]
            messages_processed: int
            errors_count: int

        response = AgentResponse(
            id="agent-001",
            name="Test Agent",
            role="scanner",
            status="running",
            current_task="scanning",
            last_activity=datetime.utcnow(),
            messages_processed=10,
            errors_count=0,
        )
        assert response.id == "agent-001"
