#!/usr/bin/env python3
"""
Research Agent - Specializes in reconnaissance and information gathering
Part of the Multi-Agent Collaboration System
Author: SHAdd0WTAka
"""

import logging
from typing import Dict, List

from modules.cve_database import CVEDatabase
from modules.sql_injection_db import SQLInjectionDatabase

from .agent_base import AgentMessage, AgentRole, BaseAgent

logger = logging.getLogger("ZenAI.Agents")


class ResearchAgent(BaseAgent):
    """
    Research Agent - Gathers information, performs reconnaissance
    Can research CVEs, exploits, techniques, and targets
    """

    def __init__(self, name: str, orchestrator=None, zen_orchestrator=None):
        super().__init__(name, AgentRole.RESEARCHER, orchestrator)
        self.zen_orchestrator = zen_orchestrator  # LLM orchestrator
        self.cve_db = CVEDatabase()
        self.sqli_db = SQLInjectionDatabase()
        self.current_research = {}

        # Register message handlers
        self.register_handler("research_task", self._handle_research_task)
        self.register_handler("request_info", self._handle_info_request)
        self.register_handler("findings", self._handle_findings)

    async def _handle_research_task(self, msg: AgentMessage):
        """Handle incoming research tasks"""
        logger.info(f"[ResearchAgent:{self.name}] Received research task")

        task_context = msg.context.get("pentest_context", {})
        thread_id = msg.context.get("thread_id", "unknown")

        # Acknowledge receipt
        await self.send_message(
            content=f"Starting research on {task_context.get('target', 'unknown target')}",
            recipient=msg.sender,
            msg_type="research_status",
            context={"thread_id": thread_id, "status": "started"},
        )

        # Perform research
        findings = await self._perform_research(task_context)

        # Share findings with all agents
        await self.send_message(
            content=f"Research complete. Found {len(findings)} relevant items.",
            recipient="all",
            msg_type="findings",
            priority=2,
            context={
                "thread_id": thread_id,
                "findings": findings,
                "researcher": self.name,
            },
        )

        # Update shared context
        self.update_context(f"research_{thread_id}", findings, share=True)

    async def _handle_info_request(self, msg: AgentMessage):
        """Handle requests for specific information"""
        request_type = msg.context.get("info_type")
        query = msg.content

        logger.info(f"[ResearchAgent:{self.name}] Info request: {request_type}")

        result = None

        if request_type == "cve":
            result = self.cve_db.search_cve(query)
        elif request_type == "ransomware":
            result = self.cve_db.search_ransomware(query)
        elif request_type == "sqli_payload":
            db_type = msg.context.get("db_type")
            result = self.sqli_db.get_payloads(db_type=db_type)

        if result:
            await self.send_message(
                content=f"Found information about {query}",
                recipient=msg.sender,
                msg_type="response",
                context={"result": result, "query": query},
            )

    async def _handle_findings(self, msg: AgentMessage):
        """Handle findings from other agents - cross-reference with research"""
        findings = msg.context.get("findings", {})

        # If findings contain CVEs, enrich them with database info
        if "cves" in findings:
            enriched = []
            for cve_id in findings["cves"]:
                cve_info = self.cve_db.search_cve(cve_id)
                if cve_info:
                    enriched.append(cve_info)

            if enriched:
                await self.send_message(
                    content=f"Enriched {len(enriched)} CVEs with database information",
                    recipient=msg.sender,
                    msg_type="enrichment",
                    context={"enriched_cves": enriched},
                )

    async def _perform_research(self, context: Dict) -> List[Dict]:
        """Perform actual research based on context"""
        findings = []
        target = context.get("target", "")
        _ = target  # TODO: Use target for research

        # Research 1: Check for known CVEs related to target tech
        technologies = context.get("technologies", [])
        for tech in technologies:
            # Use LLM to find relevant CVEs
            if self.zen_orchestrator:
                prompt = f"""
                List known CVEs for {tech} that are commonly exploited by ransomware.
                Return CVE IDs only, one per line.
                """
                response = await self.zen_orchestrator.process(prompt)

                # Parse CVEs from response
                import re

                cves = re.findall(r"CVE-\d{4}-\d{4,}", response.content)

                for cve_id in cves[:5]:  # Limit to top 5
                    cve_data = self.cve_db.search_cve(cve_id)
                    if cve_data:
                        findings.append(
                            {"type": "cve", "data": cve_data, "source": "llm_research"}
                        )

        # Research 2: Check for ransomware using these technologies
        ransomware = self.cve_db.list_all_ransomware()
        for rw in ransomware[:3]:  # Check top 3
            findings.append({"type": "ransomware", "data": rw, "source": "database"})

        return findings

    async def execute_task(self, task: Dict) -> Dict:
        """Execute a research task"""
        task_type = task.get("type", "")
        context = task.get("context", {})

        logger.info(f"[ResearchAgent:{self.name}] Executing task: {task_type}")

        if task_type == "reconnaissance":
            findings = await self._perform_research(context)

            # Share with other agents
            await self.send_message(
                content="Reconnaissance findings ready",
                recipient="role:analyst",
                msg_type="findings",
                context={"findings": findings},
            )

            return {
                "status": "complete",
                "findings_count": len(findings),
                "agent": self.name,
            }

        return {"status": "unknown_task"}
