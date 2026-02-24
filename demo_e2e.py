#!/usr/bin/env python3
"""
End-to-End Demo for Zen-AI-Pentest
==================================

This demo shows the complete workflow:
1. Start a workflow targeting scanme.nmap.org
2. Simulate agent connection and task execution
3. Execute real security tools (nmap, whois)
4. Generate a penetration test report

Usage:
    python demo_e2e.py [--target TARGET] [--risk-level {0,1,2,3}]

Examples:
    python demo_e2e.py                              # Default demo
    python demo_e2e.py --target scanme.nmap.org     # Specific target
    python demo_e2e.py --risk-level 0               # Safe mode only
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zen.demo")

# Import our modules
from agents.workflows.orchestrator import WorkflowOrchestrator
from guardrails.risk_levels import RiskLevel


class MockAgent:
    """
    Simulates a pentest agent that connects to the orchestrator
    and executes tasks.
    """

    def __init__(self, agent_id: str, orchestrator: WorkflowOrchestrator):
        self.agent_id = agent_id
        self.orchestrator = orchestrator
        self.tasks_completed = 0
        self.findings = []

    async def connect(self):
        """Register agent with orchestrator"""
        logger.info(f"🤖 Agent {self.agent_id} connecting...")
        # In real scenario, this would be a WebSocket connection
        self.orchestrator.agent_assignments[self.agent_id] = None
        logger.info(f"✅ Agent {self.agent_id} connected")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a security tool task.

        For demo purposes, executes real tools when available,
        otherwise simulates results.
        """
        tool = task.get("parameters", {}).get("tool", "unknown")
        target = task.get("target", "")
        task_id = task.get("id", "unknown")

        logger.info(f"🔧 Agent {self.agent_id} executing: {tool} on {target}")

        # Execute based on tool type
        if tool == "whois":
            result = await self._execute_whois(target)
        elif tool == "dns":
            result = await self._execute_dns(target)
        elif tool == "nmap":
            result = await self._execute_nmap(target)
        elif tool == "subdomain":
            result = await self._execute_subdomain(target)
        else:
            result = self._simulate_result(tool, target)

        self.tasks_completed += 1
        if result.get("findings"):
            self.findings.extend(result["findings"])

        logger.info(f"✅ Task {task_id} completed: {result.get('status')}")
        return result

    async def _execute_whois(self, target: str) -> Dict:
        """Execute WHOIS lookup"""
        try:
            import subprocess

            result = subprocess.run(
                ["whois", target], capture_output=True, text=True, timeout=10
            )

            # Parse basic info
            output = result.stdout
            registrar = None
            for line in output.split("\n"):
                if "Registrar:" in line and not registrar:
                    registrar = line.split(":", 1)[1].strip()

            return {
                "status": "success",
                "output": (
                    output[:500] + "..." if len(output) > 500 else output
                ),
                "findings": (
                    [
                        {
                            "type": "whois_info",
                            "severity": "info",
                            "title": f"WHOIS lookup for {target}",
                            "details": f"Registrar: {registrar or 'Unknown'}",
                        }
                    ]
                    if registrar
                    else []
                ),
            }
        except Exception as e:
            logger.warning(f"WHOIS failed: {e}, using simulation")
            return self._simulate_result("whois", target)

    async def _execute_dns(self, target: str) -> Dict:
        """Execute DNS enumeration"""
        try:
            import subprocess

            result = subprocess.run(
                ["dig", "+short", target],
                capture_output=True,
                text=True,
                timeout=10,
            )

            ips = [
                ip.strip() for ip in result.stdout.split("\n") if ip.strip()
            ]

            return {
                "status": "success",
                "output": result.stdout,
                "findings": [
                    {
                        "type": "dns_record",
                        "severity": "info",
                        "title": f"DNS resolution for {target}",
                        "details": f"Resolved to: {', '.join(ips) if ips else 'No records found'}",
                    }
                ],
            }
        except Exception as e:
            logger.warning(f"DNS lookup failed: {e}, using simulation")
            return self._simulate_result("dns", target)

    async def _execute_nmap(self, target: str) -> Dict:
        """Execute Nmap scan (quick scan)"""
        try:
            import subprocess

            logger.info(
                f"🔍 Running nmap on {target} (this may take a moment)..."
            )

            result = subprocess.run(
                ["nmap", "-Pn", "-F", "--open", target],
                capture_output=True,
                text=True,
                timeout=120,
            )

            output = result.stdout

            # Parse open ports
            open_ports = []
            for line in output.split("\n"):
                if "/tcp" in line and "open" in line:
                    parts = line.split()
                    port = parts[0]
                    service = parts[2] if len(parts) > 2 else "unknown"
                    open_ports.append(f"{port} ({service})")

            findings = []
            if open_ports:
                findings.append(
                    {
                        "type": "open_ports",
                        "severity": "medium",
                        "title": f"Open ports on {target}",
                        "details": f"Found {len(open_ports)} open ports: {', '.join(open_ports[:5])}",
                    }
                )

            return {
                "status": "success",
                "output": (
                    output[:1000] + "..." if len(output) > 1000 else output
                ),
                "findings": findings,
            }
        except FileNotFoundError:
            logger.warning("nmap not installed, using simulation")
            return self._simulate_result("nmap", target)
        except subprocess.TimeoutExpired:
            logger.warning("nmap timeout, using simulation")
            return self._simulate_result("nmap", target)
        except Exception as e:
            logger.warning(f"nmap failed: {e}, using simulation")
            return self._simulate_result("nmap", target)

    async def _execute_subdomain(self, target: str) -> Dict:
        """Execute subdomain enumeration (simulated)"""
        # Subdomain enumeration requires additional tools
        return self._simulate_result("subdomain", target)

    def _simulate_result(self, tool: str, target: str) -> Dict:
        """Simulate tool results for demo purposes"""
        simulations = {
            "whois": {
                "status": "success",
                "output": f"Simulated WHOIS for {target}",
                "findings": [
                    {
                        "type": "whois_info",
                        "severity": "info",
                        "title": f"WHOIS: {target}",
                        "details": "Registrar: Example Registrar LLC",
                    }
                ],
            },
            "dns": {
                "status": "success",
                "output": "45.33.32.156",
                "findings": [
                    {
                        "type": "dns_record",
                        "severity": "info",
                        "title": f"DNS: {target}",
                        "details": "Resolved to: 45.33.32.156",
                    }
                ],
            },
            "nmap": {
                "status": "success",
                "output": f"Simulated nmap scan for {target}\n22/tcp open ssh\n80/tcp open http",
                "findings": [
                    {
                        "type": "open_ports",
                        "severity": "medium",
                        "title": f"Open ports on {target}",
                        "details": "Ports: 22 (ssh), 80 (http)",
                    }
                ],
            },
            "subdomain": {
                "status": "success",
                "output": "Found 3 subdomains",
                "findings": [
                    {
                        "type": "subdomain",
                        "severity": "low",
                        "title": f"Subdomains of {target}",
                        "details": "www, mail, ftp",
                    }
                ],
            },
            "web_enum": {
                "status": "success",
                "output": "Found endpoints: /api, /admin, /login",
                "findings": [
                    {
                        "type": "endpoint",
                        "severity": "medium",
                        "title": "Web endpoints discovered",
                        "details": "/admin may be sensitive",
                    }
                ],
            },
            "nuclei": {
                "status": "success",
                "output": "Scan completed",
                "findings": [
                    {
                        "type": "vulnerability",
                        "severity": "high",
                        "title": "Potential security issue",
                        "details": "CVE-2023-XXXX: Example vulnerability",
                    }
                ],
            },
        }

        return simulations.get(
            tool,
            {
                "status": "success",
                "output": f"Simulated {tool} execution",
                "findings": [],
            },
        )


class ReportGenerator:
    """Generates penetration test reports from workflow results"""

    def generate(self, workflow, agent: MockAgent) -> str:
        """Generate a markdown report"""

        report = f"""# Penetration Test Report

## Executive Summary

**Target:** {workflow.target}
**Workflow Type:** {workflow.type}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {workflow.state.value}

## Test Scope

- **Reconnaissance:** {'✅' if 'reconnaissance' in workflow.completed_steps else '❌'}
- **Scanning:** {'✅' if 'scanning' in workflow.completed_steps else '❌'}
- **Enumeration:** {'✅' if 'enumeration' in workflow.completed_steps else '❌'}
- **Vulnerability Analysis:** {'✅' if 'vulnerability_analysis' in workflow.completed_steps else '❌'}
- **Reporting:** ✅

## Agent Statistics

- **Agent ID:** {agent.agent_id}
- **Tasks Completed:** {agent.tasks_completed}
- **Total Findings:** {len(agent.findings)}

## Findings Summary

| Severity | Count |
|----------|-------|
| 🔴 High | {len([f for f in agent.findings if f.get('severity') == 'high'])} |
| 🟠 Medium | {len([f for f in agent.findings if f.get('severity') == 'medium'])} |
| 🟡 Low | {len([f for f in agent.findings if f.get('severity') == 'low'])} |
| 🔵 Info | {len([f for f in agent.findings if f.get('severity') == 'info'])} |

## Detailed Findings

"""

        # Add findings
        if agent.findings:
            for i, finding in enumerate(agent.findings, 1):
                severity = finding.get("severity", "info").upper()
                icon = {
                    "HIGH": "🔴",
                    "MEDIUM": "🟠",
                    "LOW": "🟡",
                    "INFO": "🔵",
                }.get(severity, "🔵")

                report += f"""### {i}. {finding.get('title', 'Finding')}

**Severity:** {icon} {severity}
**Type:** {finding.get('type', 'unknown')}
**Details:** {finding.get('details', 'No details available')}

---

"""
        else:
            report += "No findings were discovered during this assessment.\n\n"

        report += f"""## Conclusion

This automated penetration test was conducted using the Zen-AI-Pentest framework.
For detailed technical information, please refer to the raw scan outputs.

**Report Generated:** {datetime.now().isoformat()}
**Framework Version:** 2.3.9
"""

        return report


async def run_demo(
    target: str = "scanme.nmap.org", risk_level: RiskLevel = RiskLevel.NORMAL
):
    """
    Run the complete end-to-end demo.

    Args:
        target: Target to scan (default: scanme.nmap.org - Nmap's test server)
        risk_level: Risk level for the scan (0-3)
    """

    print("=" * 70)
    print("🎯 ZEN-AI-PENTEST END-TO-END DEMO")
    print("=" * 70)
    print()

    # Step 1: Initialize Orchestrator
    print("📋 Step 1: Initializing Workflow Orchestrator")
    print("-" * 70)

    orchestrator = WorkflowOrchestrator(
        step_timeout=30, risk_level=risk_level
    )  # Short timeout for demo
    print(f"✅ Orchestrator initialized (Risk Level: {risk_level.name})")
    print()

    # Step 2: Create Mock Agent
    print("🤖 Step 2: Creating Mock Agent")
    print("-" * 70)

    agent = MockAgent("demo-agent-1", orchestrator)
    await agent.connect()
    print()

    # Step 3: Start Workflow
    print(f"🚀 Step 3: Starting Workflow (Target: {target})")
    print("-" * 70)

    try:
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon",
            target=target,
            agents=[agent.agent_id],
            parameters={"ports": "top1000", "timing": "T3"},
        )
        print(f"✅ Workflow started: {workflow_id}")
    except ValueError as e:
        print(f"❌ Workflow failed to start: {e}")
        print("   (This is expected if target is blocked by guardrails)")
        return

    print()

    # Step 4: Wait for tasks and execute them
    print("⚙️  Step 4: Executing Tasks")
    print("-" * 70)

    # Monitor workflow and execute tasks
    max_wait = 60  # Maximum wait time
    start_time = asyncio.get_event_loop().time()

    while True:
        # Get workflow status
        status = orchestrator.get_workflow_status(workflow_id)
        workflow = orchestrator.workflows[workflow_id]

        # Check for pending tasks
        pending_tasks = [
            task
            for task in workflow.tasks.values()
            if task.status in ["assigned", "queued", "pending"]
        ]

        if pending_tasks:
            # Execute first pending task
            task = pending_tasks[0]
            task.status = "running"

            result = await agent.execute_task(task.to_dict())

            # Submit result back to orchestrator
            await orchestrator.submit_task_result(
                task.id,
                {
                    "task_id": task.id,
                    "status": result["status"],
                    "findings": result["findings"],
                    "output": result["output"],
                    "timestamp": datetime.now().isoformat(),
                },
            )
            task.status = "completed"

        # Check if workflow is complete
        if status["state"] in ["completed", "failed", "cancelled"]:
            print(f"✅ Workflow completed with state: {status['state']}")
            break

        # Timeout check
        if asyncio.get_event_loop().time() - start_time > max_wait:
            print("⏱️  Demo timeout reached")
            break

        await asyncio.sleep(0.5)

    print()

    # Step 5: Generate Report
    print("📊 Step 5: Generating Report")
    print("-" * 70)

    report_gen = ReportGenerator()
    report = report_gen.generate(workflow, agent)

    # Save report
    report_file = f"pentest_report_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"✅ Report saved to: {report_file}")
    print()

    # Step 6: Summary
    print("=" * 70)
    print("📈 DEMO SUMMARY")
    print("=" * 70)
    print(f"Workflow ID:        {workflow_id}")
    print(f"Target:             {target}")
    print(f"Final State:        {workflow.state.value}")
    print(f"Completed Steps:    {len(workflow.completed_steps)}")
    print(f"Failed Steps:       {len(workflow.failed_steps)}")
    print(f"Tasks Completed:    {agent.tasks_completed}")
    print(f"Total Findings:     {len(agent.findings)}")
    print(f"Report File:        {report_file}")
    print()

    # Show sample findings
    if agent.findings:
        print("🎯 Sample Findings:")
        for finding in agent.findings[:3]:
            severity = finding.get("severity", "info").upper()
            print(f"   [{severity}] {finding.get('title')}")

    print()
    print("=" * 70)
    print("✨ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)

    return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Zen-AI-Pentest End-to-End Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_e2e.py                              # Default demo
  python demo_e2e.py --target scanme.nmap.org     # Scan specific target
  python demo_e2e.py --risk-level 0               # Safe mode (recon only)
        """,
    )

    parser.add_argument(
        "--target",
        default="scanme.nmap.org",
        help="Target to scan (default: scanme.nmap.org)",
    )

    parser.add_argument(
        "--risk-level",
        type=int,
        choices=[0, 1, 2, 3],
        default=1,
        help="Risk level: 0=SAFE, 1=NORMAL, 2=ELEVATED, 3=AGGRESSIVE (default: 1)",
    )

    args = parser.parse_args()

    # Map risk level
    risk_levels = {
        0: RiskLevel.SAFE,
        1: RiskLevel.NORMAL,
        2: RiskLevel.ELEVATED,
        3: RiskLevel.AGGRESSIVE,
    }
    risk_level = risk_levels[args.risk_level]

    # Warning for non-demo targets
    if args.target != "scanme.nmap.org":
        print()
        print("⚠️  WARNING: You are targeting a non-demo host!")
        print(f"   Target: {args.target}")
        print("   Make sure you have authorization to scan this target.")
        print()
        response = input("Continue? [y/N]: ")
        if response.lower() != "y":
            print("Demo cancelled.")
            sys.exit(0)

    # Run demo
    try:
        report = asyncio.run(run_demo(args.target, risk_level))

        # Print report preview
        print()
        print("📄 REPORT PREVIEW (first 50 lines):")
        print("-" * 70)
        lines = report.split("\n")[:50]
        for line in lines:
            print(line)
        print("-" * 70)
        print("   (Full report saved to file)")

    except KeyboardInterrupt:
        print()
        print("\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
