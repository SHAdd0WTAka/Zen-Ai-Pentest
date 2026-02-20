"""
Worker Agent
============

Production agent that connects to orchestrator and processes tasks.

Usage:
    python -m agents.v2.worker_agent --agent-id agt_xxx --api-key zen_xxx --api-secret sec_xxx
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

try:
    import websockets
    from websockets.exceptions import ConnectionClosed

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from .agent_task_processor import get_task_processor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("zen.agents.worker")


class WorkerAgent:
    """
    Agent that connects to orchestrator and executes tasks.

    Features:
    - WebSocket connection with auto-reconnect
    - API Key authentication
    - Task processing
    - Heartbeat/keepalive
    - Result reporting
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        api_secret: str,
        server_url: str = "ws://localhost:8000/agents/ws",
        auto_reconnect: bool = True,
        reconnect_delay: float = 10.0,
    ):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets required. Install with: pip install websockets")

        self.agent_id = agent_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.server_url = server_url
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.authenticated = False
        self.processor = get_task_processor()
        self._shutdown = False
        self._tasks_processing = 0

    async def run(self):
        """Main agent loop"""
        logger.info(f"🚀 Starting Worker Agent: {self.agent_id}")

        while not self._shutdown:
            try:
                if await self._connect():
                    await self._main_loop()

                if not self.auto_reconnect or self._shutdown:
                    break

                logger.info(f"⏱️  Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)

            except Exception as e:
                logger.error(f"💥 Agent error: {e}")
                if not self.auto_reconnect:
                    break
                await asyncio.sleep(self.reconnect_delay)

        logger.info("👋 Agent stopped")

    async def _connect(self) -> bool:
        """Connect and authenticate"""
        try:
            logger.info(f"🔌 Connecting to {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)

            # Authenticate with API Key
            auth_msg = {"type": "auth", "agent_id": self.agent_id, "api_key": self.api_key, "api_secret": self.api_secret}

            await self.websocket.send(json.dumps(auth_msg))

            # Wait for auth response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)

            data = json.loads(response)

            if data.get("type") == "auth_success":
                self.connected = True
                self.authenticated = True
                logger.info(f"✅ Authenticated as {self.agent_id}")
                return True
            else:
                logger.error(f"❌ Authentication failed: {data}")
                await self.websocket.close()
                return False

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def _main_loop(self):
        """Main message loop"""
        try:
            while self.connected and not self._shutdown:
                try:
                    # Receive message
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)

                    await self._handle_message(message)

                except asyncio.TimeoutError:
                    # Send heartbeat
                    await self._send_heartbeat()

        except ConnectionClosed:
            logger.warning("🔌 Connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Main loop error: {e}")
            self.connected = False

    async def _handle_message(self, message: str):
        """Handle incoming message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "task":
                # Execute task
                await self._handle_task(data)

            elif msg_type == "heartbeat_ack":
                logger.debug("💓 Heartbeat acknowledged")

            elif msg_type == "message":
                # General message from other agent
                sender = data.get("sender", "unknown")
                payload = data.get("payload", {})
                logger.info(f"📨 Message from {sender}: {payload}")

            else:
                logger.debug(f"📨 Received: {data}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message[:100]}")
        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def _handle_task(self, data: dict):
        """Handle task execution"""
        task = data.get("task", {})
        task_id = task.get("id", "unknown")

        logger.info(f"📝 Received task {task_id}")
        self._tasks_processing += 1

        try:
            # Send acknowledgment
            await self.websocket.send(
                json.dumps(
                    {"type": "task_ack", "task_id": task_id, "status": "accepted", "timestamp": datetime.utcnow().isoformat()}
                )
            )

            # Execute task
            result = await self.processor.process_task(task)

            # Send result
            await self.websocket.send(json.dumps({"type": "task_result", "task_id": task_id, "result": result.to_dict()}))

            logger.info(f"✅ Task {task_id} completed: {result.status}")

        except Exception as e:
            logger.exception(f"❌ Task {task_id} failed: {e}")

            # Send failure result
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "task_result",
                        "task_id": task_id,
                        "result": {
                            "task_id": task_id,
                            "status": "failed",
                            "findings": [],
                            "output": "",
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }
                )
            )

        finally:
            self._tasks_processing -= 1

    async def _send_heartbeat(self):
        """Send heartbeat"""
        if self.connected:
            try:
                await self.websocket.send(
                    json.dumps(
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                            "tasks_processing": self._tasks_processing,
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to send heartbeat: {e}")

    async def stop(self):
        """Stop agent gracefully"""
        logger.info("🛑 Stopping agent...")
        self._shutdown = True

        if self.websocket:
            try:
                await self.websocket.send(json.dumps({"type": "disconnect"}))
                await self.websocket.close()
            except:
                pass

        # Wait for tasks to complete
        if self._tasks_processing > 0:
            logger.info(f"⏳ Waiting for {self._tasks_processing} tasks to complete...")
            while self._tasks_processing > 0:
                await asyncio.sleep(0.5)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Zen Worker Agent")
    parser.add_argument("--agent-id", required=True, help="Agent ID")
    parser.add_argument("--api-key", required=True, help="API Key")
    parser.add_argument("--api-secret", required=True, help="API Secret")
    parser.add_argument("--server", default="ws://localhost:8000/agents/ws", help="Server URL")
    parser.add_argument("--reconnect-delay", type=float, default=10.0, help="Reconnect delay (seconds)")

    args = parser.parse_args()

    agent = WorkerAgent(
        agent_id=args.agent_id,
        api_key=args.api_key,
        api_secret=args.api_secret,
        server_url=args.server,
        reconnect_delay=args.reconnect_delay,
    )

    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        asyncio.run(agent.stop())


if __name__ == "__main__":
    main()
