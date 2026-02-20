#!/usr/bin/env python3
"""
KI Autonomous Agent Demo - Visual Interface

Zeigt den vollständigen ReAct Loop mit:
- Live State Machine Visualisierung
- KI-Analyse Integration
- Memory System Übersicht
- Tool Orchestration
- Human-in-the-Loop Demo

Usage:
    python ki_agent_demo.py <target> [--human-in-loop]

Example:
    python ki_agent_demo.py 192.168.1.1
    python ki_agent_demo.py example.com --human-in-loop
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from autonomous.ki_analysis_agent import AgentState, KIAutonomousAgent, ReActStep, run_ki_agent


class Colors:
    """ANSI Farbcodes für Terminal-Output."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def print_banner():
    """Zeigt den Banner."""
    banner = rf"""
{Colors.CYAN}{Colors.BOLD}
    ______      _   ___        _      ___ ____                        _
   |__  /     / \ |_ _|      / \    |_ _|  _ \ ___  ___ __ _ _ __ __| |
     / /     / _ \ | |      / _ \    | || |_) / _ \/ __/ _` | '__/ _` |
    / /_    / ___ \| |     / ___ \   | ||  __/ (_) | (_| (_| | | | (_| |
   /____|  /_/   \_\___|   /_/   \_\ |___|_|   \___/ \___\__,_|_|  \__,_|
{Colors.ENDC}
{Colors.GREEN}{Colors.BOLD}
    +========================================================================+
    |     KI AUTONOMOUS AGENT v2.1 - ReAct Pattern Enabled                  |
    |     State Machine | Memory System | Tool Orchestration                |
    +========================================================================+
{Colors.ENDC}
"""
    print(banner)


def print_state_machine(current_state: AgentState, previous_state: AgentState = None):
    """Visualisiert die State Machine."""
    states = [
        (AgentState.IDLE, "IDLE"),
        (AgentState.PLANNING, "PLANNING"),
        (AgentState.EXECUTING, "EXECUTING"),
        (AgentState.OBSERVING, "OBSERVING"),
        (AgentState.REFLECTING, "REFLECTING"),
        (AgentState.COMPLETED, "COMPLETED"),
    ]

    state_line = []
    for state, name in states:
        if state == current_state:
            state_line.append(f"{Colors.GREEN}{Colors.BOLD}[{name}]{Colors.ENDC}")
        elif previous_state == state:
            state_line.append(f"{Colors.DIM}{name}{Colors.ENDC}")
        else:
            state_line.append(f"{Colors.DIM}{name}{Colors.ENDC}")

    print(f"\n  {' → '.join(state_line)}")


def print_react_step(step: ReActStep):
    """Zeigt einen ReAct Step an."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}+==============================================================+")
    print(f"|  STEP {step.step_number:3d} - ReAct Pattern                              |")
    print(f"+==============================================================+{Colors.ENDC}")

    # REASON
    print(f"\n{Colors.YELLOW}[REASON] Thought:{Colors.ENDC}")
    print(f"  {step.thought}")

    # ACT
    print(f"\n{Colors.BLUE}[ACT] Action:{Colors.ENDC}")
    print(f"  → {step.action}")
    if step.action_params:
        print(f"  Parameters: {step.action_params}")

    # OBSERVE
    print(f"\n{Colors.CYAN}[OBSERVE] Results:{Colors.ENDC}")
    obs = step.observation[:200] + "..." if len(step.observation) > 200 else step.observation
    print(f"  {obs}")

    # REFLECT
    print(f"\n{Colors.GREEN}[REFLECT] Analysis:{Colors.ENDC}")
    print(f"  {step.reflection[:200]}...")

    # Status
    status = f"{Colors.GREEN}[OK]" if step.success else f"{Colors.RED}[FAIL]"
    print(f"\n  {status} Success: {step.success}{Colors.ENDC}")


def print_memory_status(agent: KIAutonomousAgent):
    """Zeigt Memory-Status."""
    mem = agent.memory

    print(f"\n{Colors.DIM}+-- Memory System ---------------------------------------------+{Colors.ENDC}")
    print(f"  Session ID: {mem.session_id[:8]}...")
    print(f"  Short-term: {len(mem.short_term)}/{mem.max_short_term} entries")
    print(f"  Context Window: {len(mem.context_window)}/{mem.max_context_window} steps")
    print(f"  Findings: {len(mem.findings)}")
    print(f"  Phase: {agent.current_phase.value}")
    print(f"{Colors.DIM}+-------------------------------------------------------------+{Colors.ENDC}")


def print_finding(finding: dict):
    """Zeigt einen Finding."""
    severity_colors = {
        "critical": Colors.RED + Colors.BOLD,
        "high": Colors.RED,
        "medium": Colors.YELLOW,
        "low": Colors.BLUE,
        "info": Colors.DIM,
    }

    sev = finding.get("severity", "info").lower()
    name = finding.get("name", "Unknown")
    color = severity_colors.get(sev, Colors.ENDC)

    print(f"\n  {color}[{sev.upper()}] {name}{Colors.ENDC}")
    if "description" in finding:
        print(f"  → {finding['description'][:80]}...")


def print_human_prompt(message: str):
    """Zeigt Human-in-the-Loop Prompt."""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}{message}{Colors.ENDC}")


def print_report(report: dict):
    """Zeigt finalen Report."""
    print(f"\n{Colors.GREEN}{Colors.BOLD}")
    print("+==================================================================+")
    print("|                    ASSESSMENT COMPLETE                           |")
    print("+==================================================================+")
    print(f"{Colors.ENDC}")

    print(f"\n{Colors.CYAN}Session:{Colors.ENDC} {report['session_id']}")
    print(f"{Colors.CYAN}Target:{Colors.ENDC} {report['target']}")
    duration = datetime.now() - datetime.fromisoformat(report["completed_at"])
    print(f"{Colors.CYAN}Duration:{Colors.ENDC} {duration.total_seconds():.1f}s")

    print(f"\n{Colors.BOLD}Statistics:{Colors.ENDC}")
    print(f"  Total Steps: {report['total_steps']}")
    print(f"  Total Findings: {report['findings_count']}")
    print(f"  Success Rate: {report['execution_summary']['success_rate']:.1f}%")
    print(f"  Final State: {report['final_state']}")

    print(f"\n{Colors.BOLD}Findings by Severity:{Colors.ENDC}")
    for sev, count in report["findings_by_severity"].items():
        if count > 0:
            color = Colors.RED if sev in ["critical", "high"] else Colors.YELLOW if sev == "medium" else Colors.BLUE
            print(f"  {color}[{sev.upper():8}] {count:3d}{Colors.ENDC}")

    print(f"\n{Colors.DIM}Report saved: logs/ki_agent_reports/report_{report['session_id']}.json{Colors.ENDC}")


async def demo_with_visualization(target: str, human_in_loop: bool = False):
    """Führt Demo mit Visualisierung aus."""
    print_banner()

    print(f"{Colors.CYAN}Configuration:{Colors.ENDC}")
    print(f"  Target: {Colors.BOLD}{target}{Colors.ENDC}")
    status_color = Colors.GREEN if human_in_loop else Colors.DIM
    status_text = "Enabled" if human_in_loop else "Disabled"
    print(f"  Human-in-the-Loop: {status_color}{status_text}{Colors.ENDC}")
    print("  KI Backend: kimi-cli (with fallback)")

    # Erstelle Agent
    agent = KIAutonomousAgent(
        goal="Comprehensive security assessment with KI analysis",
        target=target,
        human_in_loop=human_in_loop,
        pause_on_critical=True,
        max_iterations=15,
    )

    previous_state = AgentState.IDLE

    def on_state_change(old: AgentState, new: AgentState):
        nonlocal previous_state
        print_state_machine(new, old)
        previous_state = old

    def on_step_complete(step: ReActStep):
        print_react_step(step)
        print_memory_status(agent)

    def on_finding(finding: dict):
        print_finding(finding)

    def on_human_prompt(msg: str):
        print_human_prompt(msg)

    # Setze Callbacks
    agent.set_callbacks(
        state_change=on_state_change, step_complete=on_step_complete, finding=on_finding, human_prompt=on_human_prompt
    )

    print(f"\n{Colors.GREEN}Starting KI Autonomous Agent...{Colors.ENDC}")
    print("=" * 70)

    try:
        start_time = datetime.now()
        report = await agent.run()
        duration = (datetime.now() - start_time).total_seconds()

        print_report(report)

        print(f"\n{Colors.GREEN}Demo completed successfully!{Colors.ENDC}")
        print(f"Total time: {duration:.1f} seconds")

        return report

    except Exception as e:
        print(f"\n{Colors.RED}[ERROR] {e}{Colors.ENDC}")
        raise


async def quick_demo(target: str = "192.168.1.1"):
    """Schnelle Demo ohne viel Output."""
    print_banner()
    print(f"\nRunning quick demo on target: {target}\n")

    result = await run_ki_agent(target=target, goal="Security assessment", human_in_loop=False, verbose=False)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="KI Autonomous Agent Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ki_agent_demo.py 192.168.1.1
  python ki_agent_demo.py example.com --human-in-loop
  python ki_agent_demo.py --quick
        """,
    )

    parser.add_argument("target", nargs="?", default="192.168.1.1", help="Target IP or domain (default: 192.168.1.1)")
    parser.add_argument("--human-in-loop", action="store_true", help="Enable human approval for critical actions")
    parser.add_argument("--quick", action="store_true", help="Quick mode with minimal output")

    args = parser.parse_args()

    try:
        if args.quick:
            asyncio.run(quick_demo(args.target))
        else:
            asyncio.run(demo_with_visualization(args.target, args.human_in_loop))

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}[!] Interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}[!] Error: {e}{Colors.ENDC}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
