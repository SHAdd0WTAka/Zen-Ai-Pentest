#!/usr/bin/env python3
"""
CLI Interface for Multi-Agent System
Interactive commands for managing agents
Author: SHAdd0WTAka
"""

import asyncio
import sys


from backends.duckduckgo import DuckDuckGoBackend
from core.orchestrator import ZenOrchestrator
from utils.helpers import colorize

from .integration import AgentSystemIntegration


class AgentCLI:
    """Command-line interface for the agent system"""

    def __init__(self):
        self.integration = None
        self.zen_orchestrator = None

    async def initialize(self):
        """Initialize the system"""
        print(colorize("[*] Initializing Zen AI Agent System...", "cyan"))

        # Setup LLM orchestrator
        self.zen_orchestrator = ZenOrchestrator()
        async with DuckDuckGoBackend() as ddg:
            self.zen_orchestrator.add_backend(ddg)

        # Setup agent integration
        self.integration = AgentSystemIntegration(self.zen_orchestrator)
        await self.integration.initialize()

        print(colorize("[+] Agent system ready!", "green"))
        print()

    def print_banner(self):
        """Print agent system banner"""
        print(
            colorize(
                """
╔══════════════════════════════════════════════════════════════╗
║           🤖 Zen AI Multi-Agent System 🤖                     ║
║              (Inspired by Clawed/Moltbot)                    ║
╠══════════════════════════════════════════════════════════════╣
║  Agents: Research • Analysis • Exploit                       ║
║  Features: Collaborative Research • Context Sharing          ║
╚══════════════════════════════════════════════════════════════╝
        """,
                "bold",
            )
        )

    def print_help(self):
        """Print help message"""
        help_text = """
Available Commands:
  research <topic>       - Start collaborative research on topic
  analyze <target>       - Have agents analyze a target
  discuss <topic>        - Facilitate agent discussion
  status                 - Show agent system status
  agents                 - List all active agents
  context <key> <value>  - Share context with agents
  chat <message>         - Send message to all agents
  stop                   - Shutdown agent system
  help                   - Show this help
  quit/exit              - Exit

Examples:
  research WordPress CVEs
  analyze example.com
  discuss Attack vectors for CVE-2017-0144
  context target example.com
        """
        print(help_text)

    async def run(self):
        """Main CLI loop"""
        self.print_banner()
        await self.initialize()
        self.print_help()

        while True:
            try:
                cmd = input(colorize("agents> ", "bold")).strip()

                if not cmd:
                    continue

                parts = cmd.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if command in ("quit", "exit"):
                    print(colorize("[*] Shutting down agent system...", "yellow"))
                    await self.integration.shutdown()
                    print(colorize("[+] Goodbye!", "green"))
                    break

                elif command == "help":
                    self.print_help()

                elif command == "research":
                    if not args:
                        print(colorize("[!] Usage: research <topic>", "red"))
                        continue
                    print(colorize(f"[*] Starting research on: {args}", "cyan"))
                    thread_id = await self.integration.conduct_research(
                        topic=args,
                        pentest_context={
                            "target_type": "unknown",
                            "initiated_by": "user",
                        },
                    )
                    print(
                        colorize(f"[+] Research thread started: {thread_id}", "green")
                    )
                    print(
                        colorize(
                            "[*] Agents are working... Check status for updates",
                            "yellow",
                        )
                    )

                elif command == "analyze":
                    if not args:
                        print(colorize("[!] Usage: analyze <target>", "red"))
                        continue
                    print(colorize(f"[*] Analyzing target: {args}", "cyan"))
                    results = await self.integration.analyze_target(
                        target=args, findings=[]
                    )
                    print(colorize("[+] Analysis complete!", "green"))
                    print(
                        colorize(
                            f"[*] Agent responses: {len(results.get('agent_responses', {}))}",
                            "cyan",
                        )
                    )

                elif command == "discuss":
                    if not args:
                        print(colorize("[!] Usage: discuss <topic>", "red"))
                        continue
                    print(
                        colorize(
                            f"[*] Facilitating agent discussion on: {args}", "cyan"
                        )
                    )
                    messages = await self.integration.facilitate_discussion(
                        topic=args, rounds=2
                    )
                    print(colorize("[+] Discussion complete:", "green"))
                    for i, msg in enumerate(messages, 1):
                        print(f"  {i}. {msg[:100]}...")

                elif command == "status":
                    status = self.integration.get_system_status()
                    print(colorize("[*] Agent System Status:", "cyan"))
                    print(f"  Active agents: {len(status.get('agents', {}))}")
                    print(f"  Message count: {status.get('message_count', 0)}")
                    print(
                        f"  Shared context keys: {len(status.get('shared_context_keys', []))}"
                    )
                    print(f"  Role distribution: {status.get('role_distribution', {})}")

                elif command == "agents":
                    status = self.integration.get_system_status()
                    print(colorize("[*] Active Agents:", "cyan"))
                    for agent_id, agent_status in status.get("agents", {}).items():
                        role = agent_status.get("role", "unknown")
                        running = "✓" if agent_status.get("running") else "✗"
                        print(
                            f"  {running} {agent_status['name']} ({role}) [{agent_id}]"
                        )
                        print(
                            f"     Queue: {agent_status.get('queue_size', 0)} | Inbox: {agent_status.get('inbox_count', 0)}"
                        )

                elif command == "context":
                    if not args or len(args.split()) < 2:
                        print(colorize("[!] Usage: context <key> <value>", "red"))
                        continue
                    key_val = args.split(maxsplit=1)
                    key, value = key_val[0], key_val[1]
                    await self.integration.share_context(key, value)
                    print(colorize(f"[+] Shared context: {key} = {value}", "green"))

                elif command == "chat":
                    if not args:
                        print(colorize("[!] Usage: chat <message>", "red"))
                        continue
                    # Send to all agents
                    from .agent_base import AgentMessage

                    for (
                        agent_id,
                        agent,
                    ) in self.integration.agent_orchestrator.agents.items():
                        await agent.receive_message(
                            AgentMessage(
                                sender="user",
                                recipient=f"{agent.name}[{agent.id}]",
                                msg_type="chat",
                                content=args,
                            )
                        )
                    print(colorize(f"[+] Message sent to all agents", "green"))

                elif command == "stop":
                    await self.integration.shutdown()
                    print(colorize("[+] Agent system stopped", "green"))

                else:
                    print(colorize(f"[!] Unknown command: {command}", "red"))

            except KeyboardInterrupt:
                print(colorize("\n[*] Use 'quit' to exit", "yellow"))
            except Exception as e:
                print(colorize(f"[!] Error: {e}", "red"))


async def main():
    """Entry point for agent CLI"""
    cli = AgentCLI()
    try:
        await cli.run()
    except Exception as e:
        print(colorize(f"[!] Fatal error: {e}", "red"))
        sys.exit(1)


if __name__ == "__main__":
    # Handle Windows Python 3.13+ compatibility
    import sys

    if sys.platform == "win32" and sys.version_info >= (3, 13):
        from utils.async_fixes import apply_windows_async_fixes

        apply_windows_async_fixes()

        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        finally:
            try:
                loop.run_until_complete(asyncio.sleep(0.25))
            except:
                pass
            loop.close()
    else:
        asyncio.run(main())
