#!/usr/bin/env python3
"""
Test Agent Worker
=================

Simple agent that connects with API Key and processes tasks.

Usage:
    # Terminal 1: Start server
    JWT_SECRET_KEY="test" ADMIN_PASSWORD="admin123" python -m api.main

    # Terminal 2: Run test agent
    python test_agent_worker.py --agent-id agent-1 --api-key zen_test123 --api-secret sec_test456
"""

import argparse
import asyncio
import logging

from agents.v2.worker_agent import WorkerAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Test Agent Worker")
    parser.add_argument("--agent-id", default="test-agent-1", help="Agent ID")
    parser.add_argument("--api-key", default="zen_test123", help="API Key")
    parser.add_argument("--api-secret", default="sec_test456", help="API Secret")
    parser.add_argument("--server", default="ws://localhost:8000/agents/ws", help="Server URL")

    args = parser.parse_args()

    print("=" * 60)
    print("Zen-AI-Pentest Test Agent Worker")
    print("=" * 60)
    print(f"Agent ID: {args.agent_id}")
    print(f"API Key: {args.api_key[:10]}...")
    print(f"Server: {args.server}")
    print("=" * 60)
    print()

    # Create agent
    agent = WorkerAgent(
        agent_id=args.agent_id,
        api_key=args.api_key,
        api_secret=args.api_secret,
        server_url=args.server,
        auto_reconnect=True,
        reconnect_delay=5.0,
    )

    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
