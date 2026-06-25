"""Tests for Heartbeat Service"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.heartbeat import HeartbeatService, heartbeat_service


@pytest.fixture
def service():
    return HeartbeatService()


@pytest.mark.asyncio
async def test_heartbeat_start_stop(service):
    """Test that start and stop work correctly"""
    # Mock _run_heartbeat_cycle to avoid actual DB calls
    service._run_heartbeat_cycle = AsyncMock()

    # Start should run one cycle then stop
    service.running = True

    async def stop_after_one():
        await service._run_heartbeat_cycle()
        service.running = False

    await stop_after_one()
    service._run_heartbeat_cycle.assert_awaited_once()


@pytest.mark.asyncio
async def test_heartbeat_stop_cancels_tasks(service):
    """Test that stop cancels running tasks"""
    task = MagicMock()
    service._tasks[uuid4()] = task
    await service.stop()
    task.cancel.assert_called_once()
    assert service.running is False


def test_should_run_heartbeat_no_last_heartbeat(service):
    """Agent without heartbeat should run"""
    agent = MagicMock()
    agent.last_heartbeat = None
    assert service._should_run_heartbeat(agent) is True


def test_should_run_heartbeat_recent(service):
    """Agent with recent heartbeat should not run"""
    agent = MagicMock()
    agent.last_heartbeat = datetime.utcnow()
    assert service._should_run_heartbeat(agent) is False


def test_should_run_heartbeat_old(service):
    """Agent with old heartbeat should run"""
    agent = MagicMock()
    agent.last_heartbeat = datetime.utcnow() - timedelta(minutes=10)
    assert service._should_run_heartbeat(agent) is True


@pytest.mark.asyncio
async def test_agent_heartbeat_inactive_agent(service):
    """Inactive agent should be skipped"""
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.heartbeat.async_session_maker") as mock_session:
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
        await service._agent_heartbeat(uuid4())


@pytest.mark.asyncio
async def test_process_ticket_generic(service):
    """Test processing a generic ticket marks it done"""
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()
    ticket = MagicMock()
    ticket.ticket_type = "generic"
    ticket.status = "open"
    ticket.id = uuid4()
    agent = MagicMock()
    agent.id = uuid4()
    agent.budget_used = 0.0

    with patch("app.services.heartbeat.generate_with_agent", new_callable=AsyncMock, return_value="Done!"):
        with patch(
            "app.services.heartbeat.get_persona",
            return_value=MagicMock(name="Tester", description="Test", expertise=["Testing"]),
        ):
            await service._process_ticket(mock_db, agent, ticket)
            assert ticket.status == "done"
            assert ticket.completed_at is not None
            mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_ticket_complex(service):
    """Test processing a complex ticket marks it in_review"""
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()
    ticket = MagicMock()
    ticket.ticket_type = "web_scan"
    ticket.status = "open"
    ticket.id = uuid4()
    agent = MagicMock()
    agent.id = uuid4()
    agent.budget_used = 0.0

    with patch("app.services.heartbeat.generate_with_agent", new_callable=AsyncMock, return_value="Findings..."):
        with patch(
            "app.services.heartbeat.get_persona",
            return_value=MagicMock(name="Tester", description="Test", expertise=["Testing"]),
        ):
            await service._process_ticket(mock_db, agent, ticket)
            assert ticket.status == "in_review"
            mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_process_ticket_llm_error(service):
    """Test LLM error marks ticket blocked"""
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()
    ticket = MagicMock()
    ticket.ticket_type = "generic"
    ticket.status = "open"
    ticket.id = uuid4()
    agent = MagicMock()
    agent.id = uuid4()

    with patch("app.services.heartbeat.generate_with_agent", new_callable=AsyncMock, side_effect=Exception("LLM Error")):
        with patch(
            "app.services.heartbeat.get_persona",
            return_value=MagicMock(name="Tester", description="Test", expertise=["Testing"]),
        ):
            await service._process_ticket(mock_db, agent, ticket)
            assert ticket.status == "blocked"
            mock_db.commit.assert_called()


def test_build_ticket_prompt(service):
    """Test prompt building"""
    ticket = MagicMock()
    ticket.title = "Test Ticket"
    ticket.description = "Desc"
    ticket.ticket_type = "web_scan"
    ticket.target = "example.com"
    ticket.priority = "high"

    persona = MagicMock()
    persona.name = "WebApp Expert"
    persona.description = "Security expert"
    persona.expertise = ["XSS", "SQLi"]

    prompt = service._build_ticket_prompt(ticket, persona)
    assert "WebApp Expert" in prompt
    assert "Test Ticket" in prompt
    assert "example.com" in prompt
    assert "XSS" in prompt


def test_global_heartbeat_service():
    """Test global heartbeat service instance exists"""
    assert heartbeat_service is not None
    assert isinstance(heartbeat_service, HeartbeatService)
