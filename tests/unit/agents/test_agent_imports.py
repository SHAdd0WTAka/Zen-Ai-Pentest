"""Test agent imports"""

import pytest


class TestAgentImports:
    """Test all agents can be imported"""

    def test_agent_base_import(self):
        from agents.agent_base import BaseAgent

        assert BaseAgent is not None

    def test_analysis_agent_import(self):
        from agents.analysis_agent import AnalysisAgent

        assert AnalysisAgent is not None

    def test_exploit_agent_import(self):
        from agents.exploit_agent import ExploitAgent

        assert ExploitAgent is not None

    def test_research_agent_import(self):
        from agents.research_agent import ResearchAgent

        assert ResearchAgent is not None

    def test_agent_orchestrator_import(self):
        from agents.agent_orchestrator import AgentOrchestrator

        assert AgentOrchestrator is not None

    def test_kimi_master_import(self):
        from agents.kimi_master_agent import KimiMasterAgent

        assert KimiMasterAgent is not None
