"""Tests for Delegation Engine"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.delegation import DelegationEngine, delegation_engine


@pytest.fixture
def engine():
    return DelegationEngine()


class FakePersona:
    def __init__(self, expertise=None, tags=None, default_skills=None):
        self.expertise = expertise or []
        self.tags = tags or []
        self.default_skills = default_skills or []


class FakeAgent:
    def __init__(self, id, name, persona, company_id, status="active", budget_used=0, budget_limit=100, last_heartbeat=None):
        self.id = id
        self.name = name
        self.persona = persona
        self.company_id = company_id
        self.status = status
        self.budget_used = budget_used
        self.budget_limit = budget_limit
        self.last_heartbeat = last_heartbeat


class FakeTicket:
    def __init__(self, id, title, ticket_type, company_id, priority="medium"):
        self.id = id
        self.title = title
        self.ticket_type = ticket_type
        self.company_id = company_id
        self.priority = priority
        self.assigned_agent_id = None


def test_is_relevant_for_ticket_direct_skill(engine):
    persona = FakePersona(default_skills=["web_scanning", "xss_detection"])
    ticket = FakeTicket(str(uuid4()), "T", "web_scan", str(uuid4()))
    assert engine._is_relevant_for_ticket(persona, ticket) is True


def test_is_relevant_for_ticket_tag_match(engine):
    persona = FakePersona(tags=["web", "owasp"])
    ticket = FakeTicket(str(uuid4()), "T", "web_scan", str(uuid4()))
    assert engine._is_relevant_for_ticket(persona, ticket) is True


def test_is_relevant_for_ticket_no_match(engine):
    persona = FakePersona(tags=["crypto"], default_skills=["tls_analysis"])
    ticket = FakeTicket(str(uuid4()), "T", "web_scan", str(uuid4()))
    assert engine._is_relevant_for_ticket(persona, ticket) is False


@pytest.mark.asyncio
async def test_delegate_ticket_preferred_agent(engine):
    """Test delegating to a preferred agent"""
    mock_db = MagicMock()
    agent = FakeAgent(uuid4(), "A", "webapp_expert", uuid4())
    ticket = FakeTicket(uuid4(), "T", "web_scan", uuid4())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = agent
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await engine.delegate_ticket(mock_db, ticket, preferred_agent_id=agent.id)
    assert result == agent


@pytest.mark.asyncio
async def test_delegate_ticket_preferred_not_found(engine):
    """Test fallback when preferred agent not found"""
    mock_db = MagicMock()
    ticket = FakeTicket(uuid4(), "T", "web_scan", uuid4())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch.object(engine, "_find_candidates", new_callable=AsyncMock, return_value=[]):
        result = await engine.delegate_ticket(mock_db, ticket, preferred_agent_id=uuid4())
        assert result is None


@pytest.mark.asyncio
async def test_delegate_ticket_no_candidates(engine):
    """Test no candidates found"""
    mock_db = MagicMock()
    ticket = FakeTicket(uuid4(), "T", "web_scan", uuid4())

    with patch.object(engine, "_find_candidates", new_callable=AsyncMock, return_value=[]):
        result = await engine.delegate_ticket(mock_db, ticket)
        assert result is None


@pytest.mark.asyncio
async def test_find_candidates(engine):
    """Test finding candidates"""
    mock_db = MagicMock()
    company_id = uuid4()
    agent = FakeAgent(uuid4(), "A", "webapp_expert", company_id)
    ticket = FakeTicket(uuid4(), "T", "web_scan", company_id)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [agent]
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.delegation.get_persona", return_value=FakePersona(tags=["web"], default_skills=["web_scan"])):
        candidates = await engine._find_candidates(mock_db, ticket)
        assert len(candidates) == 1
        assert candidates[0].name == "A"


@pytest.mark.asyncio
async def test_score_candidates(engine):
    """Test scoring candidates"""
    mock_db = MagicMock()
    agent1 = FakeAgent(uuid4(), "A1", "webapp_expert", uuid4(), budget_used=10)
    agent2 = FakeAgent(uuid4(), "A2", "webapp_expert", uuid4(), budget_used=90)
    ticket = FakeTicket(uuid4(), "T", "web_scan", uuid4())

    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch(
        "app.services.delegation.get_persona", return_value=FakePersona(expertise=["XSS", "SQLi"], default_skills=["web_scan"])
    ):
        best = await engine._score_candidates(mock_db, [agent1, agent2], ticket)
        assert best is not None


@pytest.mark.asyncio
async def test_calculate_score(engine):
    """Test score calculation"""
    mock_db = MagicMock()
    agent = FakeAgent(uuid4(), "A", "webapp_expert", uuid4(), last_heartbeat=datetime.utcnow())
    ticket = FakeTicket(uuid4(), "T", "web_scan", uuid4())

    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch(
        "app.services.delegation.get_persona", return_value=FakePersona(expertise=["XSS"], default_skills=["web_scan"])
    ):
        score = await engine._calculate_score(mock_db, agent, ticket)
        assert score > 0


def test_global_delegation_engine():
    assert delegation_engine is not None
    assert isinstance(delegation_engine, DelegationEngine)
