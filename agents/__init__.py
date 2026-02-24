"""
Multi-Agent Collaboration System for Zen AI Pentest
Inspired by Clawed/Moltbot architecture
Agents can communicate, share context, and coordinate research
Author: SHAdd0WTAka
"""

from .agent_base import AgentMessage, AgentRole, BaseAgent
from .agent_orchestrator import AgentOrchestrator
from .analysis_agent import AnalysisAgent
from .exploit_agent import ExploitAgent
from .post_scan_agent import (
    PentestLoot,
    PostScanAgent,
    VerifiedFinding,
    run_post_scan_workflow,
)
from .research_agent import ResearchAgent

__all__ = [
    "BaseAgent",
    "AgentRole",
    "AgentMessage",
    "AgentOrchestrator",
    "ResearchAgent",
    "ExploitAgent",
    "AnalysisAgent",
    "PostScanAgent",
    "run_post_scan_workflow",
    "VerifiedFinding",
    "PentestLoot",
]
