"""
Load Testing Script for Zen-AI-Pentest WebSocket Layer
Validates 100+ concurrent agent capacity
"""

import argparse
import asyncio
import os
import random
import statistics

# Add parent directory to path for imports
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from websocket.agent_client import AgentClient, AgentClientConfig


@dataclass
class LoadTestResult:
    """Results from load test"""

    total_agents: int
    successful_connections: int
    failed_connections: int
    avg_connection_time: float
    min_connection_time: float
    max_connection_time: float
    messages_sent: int
    messages_received: int
    avg_latency: float
    p95_latency: float
    p99_latency: float
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0


class LoadTestAgent:
    """Agent for load testing"""

    def __init__(self, agent_id: str, server_url: str):
        self.agent_id = agent_id
        self.config = AgentClientConfig(
            websocket_url=f"ws://{server_url}/ws/scans/{{scan_id}}",
            agent_id=agent_id,
            agent_type="load-test-agent",
            reconnect_config=None,  # Disable reconnection for load testing
        )
        self.client = AgentClient(self.config)
        self.connection_time: float = 0.0
        self.latencies: List[float] = []
        self.messages_received: int = 0
        self.errors: List[str] = []
        self.connected: bool = False

    async def connect(self, scan_id: str) -> bool:
        """Connect and measure time"""
        start = time.time()
        try:
            self.connected = await self.client.connect(scan_id)
            self.connection_time = time.time() - start
            return self.connected
        except Exception as e:
            self.connection_time = time.time() - start
            self.errors.append(str(e))
            return False

    async def send_message(self, message: dict) -> bool:
        """Send message and measure latency"""
        start = time.time()

        # Add timestamp for round-trip measurement
        message["_sent_at"] = start

        success = await self.client.send_message(message)

        if success:
            latency = time.time() - start
            self.latencies.append(latency)

        return success

    async def disconnect(self):
        """Disconnect client"""
        await self.client.disconnect()


class WebSocketLoadTest:
    """
    Load test for WebSocket server
    Tests concurrent connections, message throughput, and latency
    """

    def __init__(self, server_url: str, num_agents: int = 100):
        self.server_url = server_url
        self.num_agents = num_agents
        self.agents: List[LoadTestAgent] = []
        self.results: Dict[str, any] = {}

    async def run_test(self, duration_seconds: int = 60) -> LoadTestResult:
        """Run complete load test"""
        print(f"\n{'=' * 60}")
        print(f"WebSocket Load Test - {self.num_agents} Agents")
        print(f"Server: {self.server_url}")
        print(f"Duration: {duration_seconds}s")
        print(f"{'=' * 60}\n")

        start_time = time.time()

        # Phase 1: Create agents
        print("Phase 1: Creating agents...")
        self.agents = [LoadTestAgent(f"load_agent_{i:03d}", self.server_url) for i in range(self.num_agents)]
        print(f"Created {len(self.agents)} agents\n")

        # Phase 2: Connect all agents
        print("Phase 2: Connecting agents...")
        await self._connect_all()

        # Phase 3: Send messages
        print("\nPhase 3: Sending messages...")
        await self._send_messages(duration_seconds)

        # Phase 4: Cleanup
        print("\nPhase 4: Cleaning up...")
        await self._disconnect_all()

        total_duration = time.time() - start_time

        # Compile results
        return self._compile_results(total_duration)

    async def _connect_all(self):
        """Connect all agents concurrently"""
        scan_id = f"load_test_{int(time.time())}"

        # Connect in batches to avoid overwhelming the server
        batch_size = 20
        for i in range(0, len(self.agents), batch_size):
            batch = self.agents[i : i + batch_size]
            tasks = [agent.connect(scan_id) for agent in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = sum(1 for r in results if r is True)
            print(f"  Batch {i // batch_size + 1}: {successful}/{len(batch)} connected")

            # Small delay between batches
            await asyncio.sleep(0.5)

        # Print connection summary
        successful = sum(1 for a in self.agents if a.connected)
        print(f"\nConnection Summary: {successful}/{len(self.agents)} successful")

    async def _send_messages(self, duration_seconds: int):
        """Send messages from all agents"""
        connected_agents = [a for a in self.agents if a.connected]

        if not connected_agents:
            print("No connected agents, skipping message phase")
            return

        print(f"Sending messages from {len(connected_agents)} agents...")

        start_time = time.time()
        message_count = 0

        while time.time() - start_time < duration_seconds:
            # Send messages from random agents
            num_messages = min(len(connected_agents), 10)
            selected = random.sample(connected_agents, num_messages)

            tasks = []
            for agent in selected:
                message = {
                    "type": "load_test_message",
                    "timestamp": time.time(),
                    "data": "x" * 100,  # 100 byte payload
                }
                tasks.append(agent.send_message(message))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            message_count += sum(1 for r in results if r is True)

            # Print progress every 10 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0:
                print(f"  {int(elapsed)}s: {message_count} messages sent")

            # Small delay between bursts
            await asyncio.sleep(0.1)

        print(f"\nTotal messages sent: {message_count}")

    async def _disconnect_all(self):
        """Disconnect all agents"""
        tasks = [agent.disconnect() for agent in self.agents]
        await asyncio.gather(*tasks, return_exceptions=True)
        print("All agents disconnected")

    def _compile_results(self, duration: float) -> LoadTestResult:
        """Compile test results"""
        successful = [a for a in self.agents if a.connected]
        failed = [a for a in self.agents if not a.connected]

        # Connection times
        connection_times = [a.connection_time for a in successful]

        # Latencies
        all_latencies = []
        for agent in successful:
            all_latencies.extend(agent.latencies)

        # Errors
        all_errors = []
        for agent in self.agents:
            all_errors.extend(agent.errors)

        result = LoadTestResult(
            total_agents=self.num_agents,
            successful_connections=len(successful),
            failed_connections=len(failed),
            avg_connection_time=(statistics.mean(connection_times) if connection_times else 0),
            min_connection_time=(min(connection_times) if connection_times else 0),
            max_connection_time=(max(connection_times) if connection_times else 0),
            messages_sent=sum(len(a.latencies) for a in successful),
            messages_received=sum(a.messages_received for a in successful),
            avg_latency=(statistics.mean(all_latencies) * 1000 if all_latencies else 0),
            p95_latency=(statistics.quantiles(all_latencies, n=20)[18] * 1000 if len(all_latencies) >= 20 else 0),
            p99_latency=(statistics.quantiles(all_latencies, n=100)[98] * 1000 if len(all_latencies) >= 100 else 0),
            errors=list(set(all_errors))[:10],  # Unique errors, limit to 10
            duration=duration,
        )

        return result


def print_results(result: LoadTestResult):
    """Print formatted test results"""
    print(f"\n{'=' * 60}")
    print("LOAD TEST RESULTS")
    print(f"{'=' * 60}\n")

    print("Connection Statistics:")
    print(f"  Total Agents:        {result.total_agents}")
    print(
        f"  Successful:          {result.successful_connections} ({result.successful_connections / result.total_agents * 100:.1f}%)"
    )
    print(f"  Failed:              {result.failed_connections} ({result.failed_connections / result.total_agents * 100:.1f}%)")
    print(f"  Avg Connection Time: {result.avg_connection_time * 1000:.2f}ms")
    print(f"  Min Connection Time: {result.min_connection_time * 1000:.2f}ms")
    print(f"  Max Connection Time: {result.max_connection_time * 1000:.2f}ms")

    print("\nMessage Statistics:")
    print(f"  Messages Sent:       {result.messages_sent}")
    print(f"  Messages Received:   {result.messages_received}")
    print(f"  Avg Latency:         {result.avg_latency:.2f}ms")
    print(f"  P95 Latency:         {result.p95_latency:.2f}ms")
    print(f"  P99 Latency:         {result.p99_latency:.2f}ms")

    print(f"\nTest Duration: {result.duration:.2f}s")

    if result.errors:
        print(f"\nErrors ({len(result.errors)} unique):")
        for error in result.errors:
            print(f"  - {error}")

    # Pass/Fail criteria
    print(f"\n{'=' * 60}")
    print("PASS/FAIL CRITERIA:")

    success_rate = result.successful_connections / result.total_agents
    passed = True

    if success_rate < 0.95:
        print(f"  [FAIL] Connection success rate {success_rate * 100:.1f}% < 95%")
        passed = False
    else:
        print(f"  [PASS] Connection success rate {success_rate * 100:.1f}% >= 95%")

    if result.avg_latency > 100:
        print(f"  [FAIL] Average latency {result.avg_latency:.2f}ms > 100ms")
        passed = False
    else:
        print(f"  [PASS] Average latency {result.avg_latency:.2f}ms <= 100ms")

    if result.p95_latency > 500:
        print(f"  [FAIL] P95 latency {result.p95_latency:.2f}ms > 500ms")
        passed = False
    else:
        print(f"  [PASS] P95 latency {result.p95_latency:.2f}ms <= 500ms")

    print(f"\nOverall: {'PASS' if passed else 'FAIL'}")
    print(f"{'=' * 60}\n")

    return passed


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="WebSocket Load Test for Zen-AI-Pentest")
    parser.add_argument("--server", default="localhost:8000", help="WebSocket server URL")
    parser.add_argument("--agents", type=int, default=100, help="Number of agents to simulate")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--output", help="Output file for JSON results")

    args = parser.parse_args()

    # Run test
    test = WebSocketLoadTest(args.server, args.agents)
    result = await test.run_test(args.duration)

    # Print results
    passed = print_results(result)

    # Save to file if requested
    if args.output:
        import json as json_module

        with open(args.output, "w") as f:
            json_module.dump(
                {
                    "total_agents": result.total_agents,
                    "successful_connections": result.successful_connections,
                    "failed_connections": result.failed_connections,
                    "avg_connection_time_ms": result.avg_connection_time * 1000,
                    "avg_latency_ms": result.avg_latency,
                    "p95_latency_ms": result.p95_latency,
                    "p99_latency_ms": result.p99_latency,
                    "messages_sent": result.messages_sent,
                    "duration_seconds": result.duration,
                    "passed": passed,
                },
                f,
                indent=2,
            )
        print(f"Results saved to {args.output}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
