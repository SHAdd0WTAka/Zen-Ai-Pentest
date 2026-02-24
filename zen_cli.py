#!/usr/bin/env python3
"""
Zen AI Pentest CLI - Main Entry Point
Provides 'zen' command with auth support
"""

import os
import sys

# Windows Asyncio Fix (must be first)
if sys.platform == "win32":
    import warnings

    warnings.filterwarnings("ignore", message="unclosed transport", category=ResourceWarning)

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth.cli import AuthCLI
from core.auth.token_store import get_stored_token, is_logged_in


class ZenCLI:
    """Main Zen AI CLI"""

    def __init__(self):
        self.auth_cli = AuthCLI()

    def print_banner(self):
        """Print CLI banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 Zen AI Pentest 🤖                       ║
║              Advanced AI-Powered Security Testing             ║
╠══════════════════════════════════════════════════════════════╣
║  Version: 3.0.0                                              ║
║  Website: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest     ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def print_main_help(self):
        """Print main help"""
        auth_status = "✅ logged in" if is_logged_in() else "❌ not logged in"

        help_text = f"""
Usage: zen <command> [options]

Commands:
  auth              Authentication commands
    auth login      Login to Kimi AI (opens browser)
    auth logout     Remove credentials
    auth status     Check login status

  agent             Multi-agent system commands
    agent start     Start interactive agent session
    agent status    Show agent status

  scan              Scanning commands
    scan start      Start a new scan
    scan list       List scans
    scan status     Check scan status

  config            Configuration
    config set      Set configuration value
    config get      Get configuration value

Quick Start:
  1. Authenticate:  zen auth login
  2. Start agents:  zen agent start
  3. Or scan:       zen scan start <target>

Authentication Status: {auth_status}

Run 'zen <command> --help' for more information.
        """
        print(help_text)

    def run(self, args=None):
        """Main entry point"""
        if args is None:
            args = sys.argv[1:]

        if not args or args[0] in ("-h", "--help", "help"):
            self.print_banner()
            self.print_main_help()
            return 0

        command = args[0].lower()

        if command == "auth":
            return self._handle_auth(args[1:])
        elif command == "agent":
            return self._handle_agent(args[1:])
        elif command == "scan":
            return self._handle_scan(args[1:])
        elif command == "config":
            return self._handle_config(args[1:])
        elif command in ("-v", "--version", "version"):
            print("Zen AI Pentest v3.0.0")
            return 0
        else:
            print(f"Unknown command: {command}")
            print()
            self.print_main_help()
            return 1

    def _handle_auth(self, args):
        """Handle auth subcommands"""
        if not args or args[0] in ("-h", "--help", "help"):
            self.auth_cli.print_help()
            return 0

        subcommand = args[0].lower()

        if subcommand == "login":
            return self.auth_cli.login()
        elif subcommand == "logout":
            return self.auth_cli.logout()
        elif subcommand == "status":
            return self.auth_cli.status()
        else:
            print(f"Unknown auth command: {subcommand}")
            self.auth_cli.print_help()
            return 1

    def _handle_agent(self, args):
        """Handle agent subcommands"""
        if not is_logged_in():
            print("❌ Not authenticated. Please run: zen auth login")
            return 1

        if not args or args[0] in ("-h", "--help", "help"):
            print(
                """
Agent Commands:
  zen agent start   - Start interactive agent session
  zen agent status  - Show agent status
            """
            )
            return 0

        subcommand = args[0].lower()

        if subcommand == "start":
            from agents.cli import AgentCLI

            agent_cli = AgentCLI()
            return asyncio.run(agent_cli.run())
        elif subcommand == "status":
            print("Agent status: Ready")
            print(f"Token available: {'Yes' if get_stored_token() else 'No'}")
            return 0
        else:
            print(f"Unknown agent command: {subcommand}")
            return 1

    def _handle_scan(self, args):
        """Handle scan subcommands"""
        if not is_logged_in():
            print("❌ Not authenticated. Please run: zen auth login")
            return 1

        print("Scan functionality coming soon...")
        return 0

    def _handle_config(self, args):
        """Handle config subcommands"""
        print("Config functionality coming soon...")
        return 0


def main():
    """Entry point"""
    try:
        cli = ZenCLI()
        return cli.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        return 130


if __name__ == "__main__":
    import asyncio

    sys.exit(main())
