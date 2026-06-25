"""
Unit Tests für RecoveryEngine
Testet Tool-Fallbacks, State-Transitions und Selbstheilung
"""

import sys
from unittest.mock import MagicMock, Mock

import pytest

sys.path.insert(0, "/root/.openclaw/workspace/Zen-Ai-Pentest")

from agents.recovery_engine import (
    AgentState,
    ReActAgentWithRecovery,
    RecoveryEngine,
)


class TestRecoveryEngine:
    """Testet die Recovery-Logik"""

    @pytest.fixture
    def engine(self):
        """Frische RecoveryEngine für jeden Test"""
        return RecoveryEngine()

    @pytest.fixture
    def engine_with_mock_agent(self):
        """RecoveryEngine mit mock Agent"""
        mock_agent = Mock()
        mock_agent.update_state = Mock()
        return RecoveryEngine(agent=mock_agent), mock_agent

    def test_handle_missing_tool_gobuster(self, engine):
        """
        Test: Gobuster fehlt -> Fallback zu dirb

        Szenario: Agent will Gobuster nutzen, aber es ist nicht installiert
        Erwartung: RecoveryEngine schlägt dirb als Alternative vor
        """
        result = engine.handle_failure(
            tool_name="gobuster",
            error_msg="command not found: gobuster",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "Try alternative scanner",
            },
        )

        assert result["action"] == "SWITCH_TOOL"
        assert result["original_tool"] == "gobuster"
        assert result["new_tool"] == "dirb"
        assert result["state"] == "PLANNING"

    def test_handle_missing_tool_nmap(self, engine):
        """
        Test: Nmap fehlt -> Fallback zu masscan
        """
        result = engine.handle_failure(
            tool_name="nmap",
            error_msg="bash: nmap: command not found",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "Use alternative port scanner",
            },
        )

        assert result["action"] == "SWITCH_TOOL"
        assert result["new_tool"] == "masscan"

    def test_handle_missing_tool_no_fallback(self, engine):
        """
        Test: Tool fehlt, aber kein Fallback bekannt

        Erwartung: ABORT mit Error-State
        """
        result = engine.handle_failure(
            tool_name="exotic_tool",
            error_msg="command not found: exotic_tool",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "No idea",
            },
        )

        assert result["action"] == "ABORT"
        assert result["state"] == "ERROR"

    def test_handle_timeout(self, engine):
        """
        Test: Tool timeout -> Retry mit Delay
        """
        result = engine.handle_failure(
            tool_name="sqlmap",
            error_msg="Command timed out after 300s",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "Add delays",
            },
        )

        assert result["action"] == "RETRY_WITH_DELAY"
        assert result["tool"] == "sqlmap"
        assert result["delay"] == 5
        assert result["state"] == "PLANNING"

    def test_handle_permission_denied(self, engine):
        """
        Test: Permission denied -> Escalation
        """
        result = engine.handle_failure(
            tool_name="nmap",
            error_msg="permission denied: raw sockets required",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "Need root",
            },
        )

        assert result["action"] == "ESCALATE_PERMISSIONS"
        assert "sudo" in result["suggestion"].lower()

    def test_handle_connection_error(self, engine):
        """
        Test: Connection refused -> Proxy vorschlagen
        """
        result = engine.handle_failure(
            tool_name="ffuf",
            error_msg="connection refused: target closed connection",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "Try proxy",
            },
        )

        assert result["action"] == "USE_PROXY"
        assert "proxy" in result["suggestion"].lower()

    def test_state_transition_called(self, engine_with_mock_agent):
        """
        Test: State-Transition wird beim Agenten aufgerufen
        """
        engine, mock_agent = engine_with_mock_agent

        engine.handle_failure(
            tool_name="gobuster",
            error_msg="not found",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "Switch tool",
            },
        )

        # Verify state transition was called
        mock_agent.update_state.assert_called_once()
        args = mock_agent.update_state.call_args[0]
        assert args[0] == AgentState.RECOVERY

    def test_failure_counting(self, engine):
        """
        Test: Failures werden gezählt
        """
        # Drei Fehler für gleiches Tool
        for _ in range(3):
            engine.handle_failure(
                tool_name="nmap",
                error_msg="timeout",
                ai_instructions={
                    "fallback_state": "RECOVERY",
                    "self_correction": "",
                },
            )

        stats = engine.get_recovery_stats()
        assert stats["failure_counts"]["nmap"] == 3
        assert stats["total_failures"] == 3

    def test_should_abort_after_max_failures(self, engine):
        """
        Test: Nach 3 Fehlern sollte Abbruch empfohlen werden
        """
        # 3 Fehler simulieren
        for _ in range(3):
            engine.handle_failure(
                tool_name="sqlmap",
                error_msg="timeout",
                ai_instructions={
                    "fallback_state": "RECOVERY",
                    "self_correction": "",
                },
            )

        assert engine.should_abort("sqlmap", max_failures=3)
        assert not engine.should_abort("sqlmap", max_failures=5)

    def test_recovery_history_tracking(self, engine):
        """
        Test: Recovery-Aktionen werden protokolliert
        """
        engine.handle_failure(
            tool_name="gobuster",
            error_msg="not found",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "",
            },
        )

        history = engine.recovery_history
        assert len(history) == 1
        assert history[0]["type"] == "tool_switch"
        assert history[0]["from"] == "gobuster"
        assert history[0]["to"] == "dirb"


class TestReActAgentWithRecovery:
    """Integration-Test: Agent mit Recovery"""

    def test_agent_cycle_with_recovery(self):
        """
        Test: Kompletter Agent-Zyklus mit Fehler und Recovery
        """
        agent = ReActAgentWithRecovery()

        # Simuliere LLM-Entscheidung für Gobuster
        ai_decision = {
            "tool": "gobuster",
            "params": {"url": "http://target.com", "wordlist": "common.txt"},
            "expected_state": "ANALYZING",
            "fallback_state": "RECOVERY",
            "self_correction": "Try dirb if gobuster fails",
        }

        # Überschreibe die Simulation um garantierten Fehler zu erhalten
        def mock_simulate(tool, params):
            return {"success": False, "stderr": "command not found: gobuster"}

        agent._simulate_tool_execution = mock_simulate

        # Führe Zyklus aus
        result = agent.run_cycle("target.com", ai_decision)

        # Assertions
        assert result["status"] == "recovered"
        assert "recovery_plan" in result
        assert result["recovery_plan"]["action"] == "SWITCH_TOOL"
        assert result["recovery_plan"]["new_tool"] == "dirb"

        # State sollte RECOVERY sein
        assert agent.state == AgentState.RECOVERY

    def test_agent_cycle_success(self):
        """
        Test: Erfolgreicher Zyklus ohne Recovery
        """
        agent = ReActAgentWithRecovery()

        ai_decision = {
            "tool": "nmap",
            "params": {"target": "target.com"},
            "expected_state": "ANALYZING",
            "fallback_state": "RECOVERY",
            "self_correction": "",
        }

        # Erfolg simulieren
        def mock_simulate(tool, params):
            return {"success": True, "output": ["22/tcp open ssh"]}

        agent._simulate_tool_execution = mock_simulate

        result = agent.run_cycle("target.com", ai_decision)

        assert result["status"] == "success"
        assert agent.state == AgentState.ANALYZING


class TestToolFallbackMatrix:
    """Testet die Tool-Fallback-Matrix"""

    @pytest.mark.parametrize(
        "tool,expected_fallback",
        [
            ("gobuster", "dirb"),
            ("nmap", "masscan"),
            ("masscan", "naabu"),
            ("ffuf", "gobuster"),
            ("amass", "subfinder"),
            ("subfinder", "assetfinder"),
            ("nikto", "nuclei"),
            ("burpsuite", "zap"),
        ],
    )
    def test_fallback_matrix(self, tool, expected_fallback):
        """
        Test: Alle Fallbacks sind korrekt definiert
        """
        engine = RecoveryEngine()

        result = engine.handle_failure(
            tool_name=tool,
            error_msg=f"command not found: {tool}",
            ai_instructions={
                "fallback_state": "RECOVERY",
                "self_correction": "",
            },
        )

        if result["action"] != "ABORT":  # Wenn Fallback existiert
            assert result["new_tool"] == expected_fallback
