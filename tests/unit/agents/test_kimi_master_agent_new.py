from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import agents.kimi_master_agent as kimi_module
from agents.kimi_master_agent import (
    KimiMasterAgent,
    KimiSwarmController,
    SwarmConfig,
    analyze_with_kimi,
    quick_scan,
)


@pytest.mark.asyncio
async def test_initialize_success_with_kimi_bridge(monkeypatch):
    bridge = AsyncMock()
    bridge.is_authenticated = AsyncMock(return_value=True)
    bridge.get_access_token = AsyncMock(return_value="token123")
    bridge.get_token_preview = Mock(return_value="tok***")

    monkeypatch.setattr(kimi_module, "KIMI_BRIDGE_AVAILABLE", True)
    monkeypatch.setattr(
        kimi_module,
        "AsyncKimiAuthBridge",
        Mock(return_value=bridge),
        raising=False,
    )
    monkeypatch.setattr(
        kimi_module.AgentChainOrchestrator,
        "create_scan_chain",
        Mock(return_value=Mock(start_workflow=Mock(return_value="wf-1"))),
    )

    master = KimiMasterAgent()
    ok = await master.initialize()

    assert ok is True
    assert master.auth_token == "token123"
    assert master.agent_chain is not None


@pytest.mark.asyncio
async def test_initialize_fails_when_not_authenticated(monkeypatch):
    bridge = AsyncMock()
    bridge.is_authenticated = AsyncMock(return_value=False)

    monkeypatch.setattr(kimi_module, "KIMI_BRIDGE_AVAILABLE", True)
    monkeypatch.setattr(
        kimi_module,
        "AsyncKimiAuthBridge",
        Mock(return_value=bridge),
        raising=False,
    )

    master = KimiMasterAgent()
    ok = await master.initialize()

    assert ok is False
    assert master.auth_token is None


@pytest.mark.asyncio
async def test_run_swarm_scan_requires_auth():
    master = KimiMasterAgent()
    result = await master.run_swarm_scan("example.com")
    assert result == {"error": "Not authenticated"}


@pytest.mark.asyncio
async def test_run_swarm_scan_with_chain_calls_simulation(monkeypatch):
    master = KimiMasterAgent()
    master.auth_token = "token"
    master.agent_chain = Mock(start_workflow=Mock(return_value="wf-99"))
    master._simulate_agent_flow = AsyncMock(return_value={"ok": True})

    result = await master.run_swarm_scan("example.com", "quick")

    assert result == {"ok": True}
    master.agent_chain.start_workflow.assert_called_once()
    master._simulate_agent_flow.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_swarm_scan_without_chain_uses_direct_scan():
    master = KimiMasterAgent()
    master.auth_token = "token"
    master.agent_chain = None
    master._direct_scan = AsyncMock(return_value={"direct": True})

    result = await master.run_swarm_scan("example.com")

    assert result == {"direct": True}
    master._direct_scan.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_analyzer_without_ai_returns_raw_findings():
    master = KimiMasterAgent(SwarmConfig(use_kimi_for_analysis=False))
    scan_results = {"findings": [{"severity": "critical", "cvss": 9.8}]}

    result = await master._run_analyzer(scan_results)

    assert result["ai_analysis"] is False
    assert result["findings"] == scan_results["findings"]


@pytest.mark.asyncio
async def test_run_analyzer_with_ai_adds_priorities(monkeypatch):
    master = KimiMasterAgent()
    master.auth_token = "token"

    async def _no_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(kimi_module.asyncio, "sleep", _no_sleep)

    scan_results = {
        "findings": [
            {"severity": "critical", "cvss": 9.8},
            {"severity": "high", "cvss": 7.5},
            {"severity": "medium", "cvss": 5.0},
        ]
    }

    result = await master._run_analyzer(scan_results)

    assert result["ai_analysis"] is True
    assert result["risk_score"] == pytest.approx((9.8 + 7.5 + 5.0) / 3)
    assert result["findings"][0]["ai_priority"].startswith("P0")


@pytest.mark.asyncio
async def test_run_reporter_counts_severity(monkeypatch):
    master = KimiMasterAgent()

    async def _no_sleep(*_args, **_kwargs):
        return None

    monkeypatch.setattr(kimi_module.asyncio, "sleep", _no_sleep)

    analysis = {
        "findings": [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
        ]
    }
    report = await master._run_reporter(analysis)

    assert report["total_findings"] == 3
    assert report["critical_count"] == 1
    assert report["high_count"] == 1


@pytest.mark.asyncio
async def test_query_kimi_requires_auth_and_then_returns_text():
    master = KimiMasterAgent()
    assert await master.query_kimi("hello") == "Error: Not authenticated"

    master.auth_token = "token"
    response = await master.query_kimi("hello")
    assert "Kimi analysis complete" in response


def test_get_auth_status_fields():
    master = KimiMasterAgent()
    status = master.get_auth_status()
    assert status["authenticated"] is False
    assert "kimi_bridge_available" in status


@pytest.mark.asyncio
async def test_coordinate_agents_returns_per_agent_results(monkeypatch):
    master = KimiMasterAgent()

    monkeypatch.setattr(
        kimi_module.AgentMessage,
        "create",
        Mock(return_value=SimpleNamespace(id="msg1")),
    )

    agents = [
        SimpleNamespace(role="scanner", email="s@x"),
        SimpleNamespace(role="analyzer", email="a@x"),
    ]
    task = {"target": "example.com"}

    results = await master.coordinate_agents(agents, task)

    assert len(results) == 2
    assert results[0]["agent"] == "scanner"


@pytest.mark.asyncio
async def test_swarm_controller_scan_status_and_ask(monkeypatch):
    controller = KimiSwarmController()
    controller.master.initialize = AsyncMock(return_value=True)
    controller.master.run_swarm_scan = AsyncMock(return_value={"r": 1})
    controller.master.query_kimi = AsyncMock(return_value="ans")

    assert await controller.start() is True

    scan_id = await controller.scan_target("example.com", "quick")
    status = controller.get_scan_status(scan_id)
    assert status["results"] == {"r": 1}
    assert await controller.ask_kimi("q") == "ans"


@pytest.mark.asyncio
async def test_quick_scan_and_analyze_with_kimi(monkeypatch):
    fake_controller = Mock()
    fake_controller.start = AsyncMock()
    fake_controller.scan_target = AsyncMock(return_value="scan-1")
    fake_controller.get_scan_status = Mock(return_value={"status": "completed"})

    monkeypatch.setattr(kimi_module, "KimiSwarmController", Mock(return_value=fake_controller))

    result = await quick_scan("example.com")
    assert result == {"status": "completed"}

    fake_master = Mock()
    fake_master.initialize = AsyncMock()
    fake_master.query_kimi = AsyncMock(return_value="analysis")
    monkeypatch.setattr(kimi_module, "KimiMasterAgent", Mock(return_value=fake_master))

    out = await analyze_with_kimi([{"id": "VULN-1"}])
    assert out == "analysis"
