"""
Multi-Agent Demonstration

Shows 2+ agents communicating and cooperating:
- Researcher Agent: Gathers information
- Analyst Agent: Analyzes findings

This demonstrates the agent_base.py capabilities in action.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_base import AgentMessage, AgentRole, BaseAgent


class ResearcherAgent(BaseAgent):
    """
    Researcher Agent - Gathers information about targets.
    Role: Reconnaissance and data collection
    """

    def __init__(self, orchestrator=None):
        super().__init__("Researcher-1", AgentRole.RESEARCHER, orchestrator)
        self.discovered_hosts = []
        self.open_ports = []

    async def execute_task(self, task: dict) -> dict:
        """Execute reconnaissance task."""
        target = task.get("target")
        task_type = task.get("type", "recon")

        self.logger.info(f"[{self.name}] Starting reconnaissance on {target} (type: {task_type})")

        # Simulate reconnaissance (in production, this would run real tools)
        await asyncio.sleep(2)  # Simulate work

        findings = {
            "target": target,
            "hosts": [target, f"www.{target}", f"api.{target}"],
            "open_ports": [80, 443, 8080],
            "technologies": ["Apache", "PHP", "MySQL"],
            "findings_count": 3,
        }

        self.discovered_hosts = findings["hosts"]
        self.open_ports = findings["open_ports"]

        # Share findings with other agents
        await self.share_findings({"type": "recon_complete", "target": target, "data": findings})

        self.logger.info(f"[{self.name}] Reconnaissance complete. Found {findings['findings_count']} hosts")

        return findings


class AnalystAgent(BaseAgent):
    """
    Analyst Agent - Analyzes data and identifies patterns.
    Role: Data analysis and vulnerability identification
    """

    def __init__(self, orchestrator=None):
        super().__init__("Analyst-1", AgentRole.ANALYST, orchestrator)
        self.vulnerabilities = []

    async def execute_task(self, task: dict) -> dict:
        """Execute analysis task."""
        data = task.get("data")

        self.logger.info(f"[{self.name}] Starting analysis of {len(data.get('hosts', []))} hosts")

        # Simulate analysis
        await asyncio.sleep(1.5)

        analysis = {
            "risk_level": "medium",
            "identified_vulnerabilities": [
                {"type": "information_disclosure", "severity": "low", "description": "Server version exposed"},
                {
                    "type": "potential_sqli",
                    "severity": "medium",
                    "description": "PHP app with MySQL backend - SQL injection possible",
                },
            ],
            "recommendations": ["Implement WAF", "Update Apache version", "Review input validation"],
        }

        self.vulnerabilities = analysis["identified_vulnerabilities"]

        # Share analysis
        await self.share_findings(
            {
                "type": "analysis_complete",
                "risk_level": analysis["risk_level"],
                "vulnerabilities": len(analysis["identified_vulnerabilities"]),
            }
        )

        self.logger.info(f"[{self.name}] Analysis complete. Risk: {analysis['risk_level']}")

        return analysis

    async def handle_message(self, msg: AgentMessage):
        """Handle incoming messages."""
        await super().handle_message(msg)

        if msg.msg_type == "findings":
            findings = msg.context.get("findings", {})
            if findings.get("type") == "recon_complete":
                self.logger.info(f"[{self.name}] Received recon data from {msg.sender}")
                # Trigger analysis
                await self.execute_task({"data": findings.get("data", {})})


class SimpleOrchestrator:
    """
    Simple orchestrator for multi-agent coordination.
    Routes messages between agents.
    """

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.message_log = []

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.id] = agent
        agent.orchestrator = self
        print(f"[Orchestrator] Registered {agent.name} ({agent.role.value})")

    async def route_message(self, msg: AgentMessage):
        """Route message to recipient(s)."""
        self.message_log.append(msg.to_dict())

        if msg.recipient == "all":
            # Broadcast to all agents
            for agent in self.agents.values():
                if agent.name != msg.sender:  # Don't send to self
                    await agent.receive_message(msg)
        else:
            # Direct message
            for agent in self.agents.values():
                if agent.name == msg.recipient or agent.id == msg.recipient:
                    await agent.receive_message(msg)
                    break

    async def run_demo(self, target: str):
        """Run the multi-agent demonstration."""
        print("\n" + "=" * 70)
        print("MULTI-AGENT PENETRATION TESTING DEMO")
        print("=" * 70)
        print(f"Target: {target}")
        print(f"Agents: {len(self.agents)}")
        print("=" * 70 + "\n")

        # Start all agents
        for agent in self.agents.values():
            await agent.start()

        # Assign task to Researcher
        researcher = next(a for a in self.agents.values() if a.role == AgentRole.RESEARCHER)

        print(f"[Demo] Assigning reconnaissance task to {researcher.name}...")
        recon_task = {"type": "recon", "target": target, "scope": "full"}

        # Execute reconnaissance
        recon_result = await researcher.execute_task(recon_task)

        # Wait a moment for messages to be processed
        await asyncio.sleep(1)

        # Analyst automatically processes findings via message handler
        analyst = next(a for a in self.agents.values() if a.role == AgentRole.ANALYST)

        # Wait for analysis
        await asyncio.sleep(2)

        # Summary
        print("\n" + "=" * 70)
        print("DEMO COMPLETE - SUMMARY")
        print("=" * 70)
        print("\nReconnaissance:")
        print(f"  - Hosts discovered: {len(recon_result.get('hosts', []))}")
        print(f"  - Open ports: {recon_result.get('open_ports', [])}")
        print("\nAnalysis:")
        print(f"  - Vulnerabilities: {len(analyst.vulnerabilities)}")
        print(f"  - Risk level: {analyst.vulnerabilities[0]['severity'] if analyst.vulnerabilities else 'unknown'}")
        print(f"\nMessages exchanged: {len(self.message_log)}")
        print("=" * 70)

        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()


async def main():
    """Main demo function."""
    # Create orchestrator
    orchestrator = SimpleOrchestrator()

    # Create agents
    researcher = ResearcherAgent(orchestrator)
    analyst = AnalystAgent(orchestrator)

    # Register with orchestrator
    orchestrator.register_agent(researcher)
    orchestrator.register_agent(analyst)

    # Run demo
    await orchestrator.run_demo("example.com")


if __name__ == "__main__":
    print("Starting Multi-Agent Demonstration...")
    print("This shows how multiple agents cooperate in a pentest workflow.")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[Demo] Interrupted by user")
    except Exception as e:
        print(f"\n[Demo] Error: {e}")
        import traceback

        traceback.print_exc()

    print("\n[Demo] Finished")
