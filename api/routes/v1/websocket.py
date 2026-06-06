"""
WebSocket Routes

Diese Endpoints wurden aus api/main.py migriert.
"""

import json
import logging
import os
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.security_logging import sanitize_for_log

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)

# Import WebSocket managers from api module
try:
    from api.websocket import ConnectionManager as ScanConnectionManager

    ws_manager = ScanConnectionManager()
except ImportError:
    ws_manager = None
    logger.warning("Scan WebSocket manager not available")

try:
    from api.websocket_manager import manager
except ImportError:
    manager = None
    logger.warning("WebSocket manager not available")


# ============================================================================
# AGENT CONNECTION MANAGER
# ============================================================================


class SimpleAgentConnection:
    """
    Simple agent connection manager with task support

    **Migriert von:** `api/main.py`
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_info: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, agent_id: str, api_key: str = None):
        """Accept and register agent connection"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.agent_info[agent_id] = {
            "api_key": api_key,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"✅ Agent {sanitize_for_log(agent_id)} connected via WebSocket")

    def disconnect(self, agent_id: str):
        """Remove agent connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in self.agent_info:
            del self.agent_info[agent_id]
        logger.info(f"🔌 Agent {sanitize_for_log(agent_id)} disconnected")

    async def send_to_agent(self, agent_id: str, message: dict) -> bool:
        """Send message to specific agent. Returns True if sent."""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
                self.agent_info[agent_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
                return True
            except Exception as e:
                logger.error(f"❌ Failed to send to {sanitize_for_log(agent_id)}: {e}")
                return False
        return False

    async def send_task(self, agent_id: str, task: dict) -> bool:
        """Send task to agent"""
        return await self.send_to_agent(
            agent_id,
            {
                "type": "task",
                "task": task,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        """Broadcast message to all agents"""
        for agent_id, ws in self.active_connections.items():
            if agent_id != exclude:
                try:
                    await ws.send_json(message)
                    self.agent_info[agent_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
                except Exception as e:
                    logger.error(f"❌ Failed to send to {sanitize_for_log(agent_id)}: {e}")

    def get_connected_agents(self) -> list:
        """Get list of connected agent IDs"""
        return list(self.active_connections.keys())

    def is_agent_connected(self, agent_id: str) -> bool:
        """Check if agent is connected"""
        return agent_id in self.active_connections


# Global agent connection manager instance
agent_connection_manager = SimpleAgentConnection()


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================


@router.websocket("/ws/scans/{scan_id}")
async def scan_websocket(websocket: WebSocket, scan_id: int):
    """
    WebSocket for real-time scan updates

    Connect to receive live updates during a scan:
    - Progress updates
    - New findings
    - Status changes
    - Log messages

    **Migriert von:** `api/main.py` (ursprünglich @app.websocket("/ws/scans/{scan_id}"))
    """
    if ws_manager is None:
        await websocket.close(code=1011, reason="WebSocket manager not available")
        return

    await ws_manager.connect(websocket, scan_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, scan_id)
    except Exception as e:
        logger.error(f"Scan WebSocket error: {e}")
        ws_manager.disconnect(websocket, scan_id)


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """
    WebSocket for global notifications

    Connect to receive:
    - Scan completion notifications
    - New findings alerts
    - System notifications

    **Migriert von:** `api/main.py` (ursprünglich @app.websocket("/ws/notifications"))
    """
    if ws_manager is None:
        await websocket.close(code=1011, reason="WebSocket manager not available")
        return

    await ws_manager.connect(websocket, None)  # None for global
    try:
        while True:
            _ = await websocket.receive_text()
            # Handle incoming messages
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, None)
    except Exception as e:
        logger.error(f"Notifications WebSocket error: {e}")
        ws_manager.disconnect(websocket, None)


@router.websocket("/ws/{client_id}")
async def client_websocket(websocket: WebSocket, client_id: str):
    """
    Generic WebSocket Endpoint für Echtzeit-Updates

    Nutzung:
    - Verbinden: wscat -c ws://localhost:8000/api/v1/ws/client123
    - Ping: {"type": "ping"}
    - Subscribe: {"type": "subscribe", "channel": "scans"}

    **Migriert von:** `api/main.py` (ursprünglich @app.websocket("/ws/{client_id}"))
    """
    from datetime import datetime, timezone

    if manager is None:
        await websocket.close(code=1011, reason="WebSocket manager not available")
        return

    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )

            elif message.get("type") == "subscribe":
                channel = message.get("channel", "general")
                await manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "channel": channel,
                        "client_id": client_id,
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)


@router.websocket("/agents/ws")
async def agent_websocket_endpoint(websocket: WebSocket):
    """
    Agent Communication WebSocket Endpoint with API Key Auth

    Protocol:
    1. Auth: {"type": "auth", "agent_id": "...", "api_key": "...", "api_secret": "..."}
    2. Receive: {"type": "auth_success", "agent_id": "..."}
    3. Receive tasks: {"type": "task", "task": {...}}
    4. Send results: {"type": "task_result", "task_id": "...", "result": {...}}
    5. Heartbeat: {"type": "heartbeat"} every 30s

    **Migriert von:** `api/main.py` (ursprünglich @app.websocket("/agents/ws"))
    """
    from datetime import datetime, timezone

    agent_id: Optional[str] = None
    api_key: Optional[str] = None

    try:
        await websocket.accept()

        # Receive auth message
        auth_data = await websocket.receive_json()

        if auth_data.get("type") != "auth":
            await websocket.send_json(
                {
                    "type": "auth_failed",
                    "error": "Expected auth message with type 'auth'",
                }
            )
            await websocket.close()
            return

        agent_id = auth_data.get("agent_id")
        api_key = auth_data.get("api_key")

        if not agent_id:
            await websocket.send_json({"type": "auth_failed", "error": "agent_id required"})
            await websocket.close()
            return

        # Validate API Key (simple check for now)
        if not api_key or not api_key.startswith("zen_"):
            await websocket.send_json({"type": "auth_failed", "error": "Invalid API key format"})
            await websocket.close()
            return

        # Connect agent
        await agent_connection_manager.connect(websocket, agent_id, api_key)

        await websocket.send_json(
            {
                "type": "auth_success",
                "agent_id": agent_id,
                "message": "Connected to Zen-AI-Pentest Agent Network",
            }
        )

        logger.info(f"🔌 Agent {sanitize_for_log(agent_id)} authenticated")

        # Main message loop
        while True:
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "task_result":
                    # Receive task result from agent
                    task_id = data.get("task_id")
                    result = data.get("result", {})

                    logger.info(f"✅ Task result received from {agent_id}: {task_id}")

                    # Forward to workflow orchestrator
                    try:
                        from agents.workflows.orchestrator import (
                            get_workflow_orchestrator,
                        )

                        orchestrator = get_workflow_orchestrator()
                        await orchestrator.submit_task_result(task_id, result)

                        await websocket.send_json(
                            {
                                "type": "ack",
                                "message_id": task_id,
                                "status": "result_received",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to process task result: {e}")

                elif msg_type == "task_ack":
                    # Agent acknowledged task receipt
                    task_id = data.get("task_id")
                    logger.debug(f"📋 Task {task_id} acknowledged by {agent_id}")

                elif msg_type == "message":
                    # Agent-to-agent messaging
                    recipient = data.get("recipient", "broadcast")
                    payload = data.get("payload", {})

                    await websocket.send_json(
                        {
                            "type": "ack",
                            "message_id": data.get("message_id", "unknown"),
                            "status": "received",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                    if recipient == "broadcast":
                        await agent_connection_manager.broadcast(
                            {
                                "type": "message",
                                "sender": agent_id,
                                "payload": payload,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                            exclude=agent_id,
                        )
                    else:
                        # Direct message
                        await agent_connection_manager.send_to_agent(
                            recipient,
                            {
                                "type": "message",
                                "sender": agent_id,
                                "payload": payload,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )

                elif msg_type == "heartbeat":
                    await websocket.send_json(
                        {
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                elif msg_type == "disconnect":
                    break

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "Invalid JSON"})
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket.send_json({"type": "error", "error": str(e)})

    except WebSocketDisconnect:
        logger.info("Agent WebSocket disconnected")
    except Exception as e:
        logger.error(f"Agent WebSocket error: {e}")
    finally:
        if agent_id:
            agent_connection_manager.disconnect(agent_id)


# Import datetime for agent connection
try:
    from datetime import datetime, timezone
except ImportError:
    pass

# ============================================================================
# NEW AGENT WEBSOCKET MANAGER (v2)
# ============================================================================

try:
    from core.agent_websocket_manager import AgentWebSocketManager

    # Initialize with Redis if available
    redis_url = os.getenv("REDIS_URL")
    agent_ws_manager = AgentWebSocketManager(redis_url=redis_url)
    AGENT_WS_V2_AVAILABLE = True
except ImportError:
    agent_ws_manager = None
    AGENT_WS_V2_AVAILABLE = False
    logger.warning("New AgentWebSocketManager not available, using legacy implementation")


@router.websocket("/agents/ws/v2")
async def agent_websocket_v2(websocket: WebSocket):
    """
    NEW Agent WebSocket Endpoint v2 with Redis Support

    Features:
    - Room-based agent groups (recon, exploit, analysis)
    - Redis Pub/Sub for horizontal scaling
    - Automatic heartbeat monitoring
    - Concurrent message broadcasting

    Protocol:
    1. Connect: Automatic assignment of client_id
    2. Join room: {"type": "join_room", "room": "recon"}
    3. Broadcast to room: {"type": "room_message", "room": "recon", "content": {...}}
    4. Heartbeat: {"type": "pong"} (response to server ping)

    **NEW:** This endpoint uses the scalable AgentWebSocketManager
    """
    if not AGENT_WS_V2_AVAILABLE or agent_ws_manager is None:
        await websocket.close(code=1011, reason="Agent WebSocket v2 not available")
        return

    # Initialize Redis connection if not done
    if not agent_ws_manager.redis and not agent_ws_manager.local_mode:
        await agent_ws_manager.initialize()

    # Connect with agent type from query param or default
    agent_type = websocket.query_params.get("type", "generic")
    metadata = {"agent_version": "2.0"}

    client_id = await agent_ws_manager.connect(websocket=websocket, agent_type=agent_type, metadata=metadata)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "pong":
                agent_ws_manager.record_pong(client_id)

            elif msg_type == "join_room":
                room = data.get("room")
                await agent_ws_manager.join_room(client_id, room)
                await agent_ws_manager.send_to_agent(
                    client_id,
                    {
                        "type": "joined_room",
                        "room": room,
                        "client_id": client_id,
                    },
                )

            elif msg_type == "leave_room":
                room = data.get("room")
                await agent_ws_manager.leave_room(client_id, room)

            elif msg_type == "room_message":
                room = data.get("room")
                content = data.get("content")
                await agent_ws_manager.broadcast_to_room(
                    room,
                    {
                        "type": "room_message",
                        "room": room,
                        "from": client_id,
                        "content": content,
                    },
                )

            elif msg_type == "broadcast":
                content = data.get("content")
                await agent_ws_manager.global_broadcast(
                    {
                        "type": "broadcast",
                        "from": client_id,
                        "content": content,
                    }
                )

            elif msg_type == "stats":
                stats = agent_ws_manager.get_stats()
                await agent_ws_manager.send_to_agent(client_id, {"type": "stats", "data": stats})

    except WebSocketDisconnect:
        logger.info(f"Agent v2 {client_id} disconnected")
    except Exception as e:
        logger.error(f"Agent v2 WebSocket error: {e}")
    finally:
        await agent_ws_manager.disconnect(client_id)
