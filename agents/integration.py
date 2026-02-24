#!/usr/bin/env python3
"""
Integration Module - Connect Multi-Agent System to Zen AI Pentest
Provides easy interface for pentesters to use agent collaboration
Author: SHAdd0WTAka
"""

import asyncio
import logging
from typing import Any, Dict, List

from .agent_orchestrator import AgentOrchestrator
from .analysis_agent import AnalysisAgent
from .exploit_agent import ExploitAgent
from .research_agent import ResearchAgent

logger = logging.getLogger("ZenAI.Agents")


class AgentSystemIntegration:
    """
    High-level interface for using the multi-agent system
    Pentesters can use this to coordinate agent research and analysis
    """

    def __init__(self, zen_orchestrator=None):
        self.agent_orchestrator = AgentOrchestrator(zen_orchestrator)
        self.zen_orchestrator = zen_orchestrator
        self.initialized = False

    async def initialize(self):
        """Initialize the agent system with default agents"""
        if self.initialized:
            return

        logger.info("[AgentIntegration] Initializing multi-agent system...")

        # Create default agents
        research_agent = ResearchAgent(
            name="ResearchBot-Alpha",
            orchestrator=self.agent_orchestrator,
            zen_orchestrator=self.zen_orchestrator,
        )

        analysis_agent = AnalysisAgent(
            name="AnalysisBot-Beta",
            orchestrator=self.agent_orchestrator,
            zen_orchestrator=self.zen_orchestrator,
        )

        exploit_agent = ExploitAgent(
            name="ExploitBot-Gamma",
            orchestrator=self.agent_orchestrator,
            zen_orchestrator=self.zen_orchestrator,
        )

        # Register agents
        self.agent_orchestrator.register_agent(research_agent)
        self.agent_orchestrator.register_agent(analysis_agent)
        self.agent_orchestrator.register_agent(exploit_agent)

        # Start all agents
        await self.agent_orchestrator.start_all()

        self.initialized = True
        logger.info(
            "[AgentIntegration] Multi-agent system initialized with 3 agents"
        )

    async def conduct_research(self, topic: str, pentest_context: Dict) -> str:
        """
        Start coordinated research on a topic
        Agents will work together and share findings
        """
        if not self.initialized:
            await self.initialize()

        thread_id = await self.agent_orchestrator.start_research_coordination(
            topic=topic, pentest_context=pentest_context
        )

        logger.info(f"[AgentIntegration] Research started: {thread_id}")

        # Wait a bit for agents to work
        await asyncio.sleep(2)

        return thread_id

    async def analyze_target(self, target: str, findings: List[Dict]) -> Dict:
        """
        Have agents analyze a target collaboratively
        """
        if not self.initialized:
            await self.initialize()

        logger.info(
            f"[AgentIntegration] Starting collaborative analysis of {target}"
        )

        # Coordinate agents for vulnerability analysis
        results = await self.agent_orchestrator.coordinate_agents(
            task_type="vulnerability_analysis",
            context={"target": target, "findings": findings},
        )

        return results

    async def develop_exploits(
        self, vulnerabilities: List[Dict]
    ) -> List[Dict]:
        """
        Have ExploitAgent develop exploits for vulnerabilities
        """
        if not self.initialized:
            await self.initialize()

        exploits = []

        for vuln in vulnerabilities:
            # Send exploit request to ExploitAgent
            await self.agent_orchestrator.agents[
                list(self.agent_orchestrator.agents.keys())[2]  # ExploitAgent
            ].receive_message(
                type(
                    "Msg",
                    (),
                    {
                        "sender": "user",
                        "recipient": "ExploitBot-Gamma",
                        "msg_type": "exploit_request",
                        "context": {
                            "vulnerability_type": vuln.get("name"),
                            "target_info": vuln.get("target_info", {}),
                        },
                    },
                )()
            )

        return exploits

    async def facilitate_discussion(
        self, topic: str, rounds: int = 3
    ) -> List[str]:
        """
        Have agents discuss a topic and share insights
        Similar to Clawed/Moltbot conversations
        """
        if not self.initialized:
            await self.initialize()

        agent_ids = list(self.agent_orchestrator.agents.keys())

        conversation = await self.agent_orchestrator.facilitate_conversation(
            topic=topic, participants=agent_ids, rounds=rounds
        )

        # Extract conversation content
        messages = [msg.content for msg in conversation]

        return messages

    def get_system_status(self) -> Dict:
        """Get status of the multi-agent system"""
        if not self.initialized:
            return {"status": "not_initialized"}

        return self.agent_orchestrator.get_system_status()

    async def share_context(self, key: str, value: Any):
        """Share context with all agents"""
        if self.initialized:
            await self.agent_orchestrator.update_shared_context(
                key=key, value=value, source_agent_id="user"
            )

    async def shutdown(self):
        """Shutdown the agent system gracefully"""
        if self.initialized:
            await self.agent_orchestrator.stop_all()
            self.initialized = False
            logger.info("[AgentIntegration] Agent system shutdown complete")


# Convenience functions for direct use


async def start_collaborative_research(
    topic: str, zen_orchestrator=None
) -> AgentSystemIntegration:
    """
    Quick-start function to begin collaborative research

    Usage:
        integration = await start_collaborative_research("WordPress vulnerabilities")
        # Let agents work...
        status = integration.get_system_status()
    """
    integration = AgentSystemIntegration(zen_orchestrator)
    await integration.initialize()
    await integration.conduct_research(
        topic=topic, pentest_context={"target_type": "web", "scope": "full"}
    )
    return integration


async def multi_agent_analysis(
    target: str, findings: List[Dict], zen_orchestrator=None
) -> Dict:
    """
    One-shot function for multi-agent analysis

    Usage:
        results = await multi_agent_analysis("example.com", nmap_findings)
        print(results["shared_findings"])
    """
    integration = AgentSystemIntegration(zen_orchestrator)
    results = await integration.analyze_target(target, findings)
    await integration.shutdown()
    return results
