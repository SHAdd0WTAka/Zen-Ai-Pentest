"""
WebSocket Endpoints

Real-time communication for live scan updates and agent messages.
"""

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()

# Store active connections
active_connections: Dict[str, Set[WebSocket]] = {
    "scans": set(),
    "agents": set(),
    "system": set(),
}


async def broadcast_to_channel(channel: str, message: dict):
    """Broadcast message to all connections in a channel"""
    if channel not in active_connections:
        return

    disconnected = set()
    for connection in active_connections[channel]:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)

    # Remove disconnected clients
    active_connections[channel] -= disconnected


@router.websocket("/scans/{scan_id}")
async def scan_websocket(websocket: WebSocket, scan_id: str):
    """
    WebSocket for real-time scan updates.

    Connect to receive live updates during a scan:
    - Progress updates
    - New findings
    - Status changes
    - Log messages
    """
    await websocket.accept()

    # Add to scan channel
    if scan_id not in active_connections:
        active_connections[scan_id] = set()
    active_connections[scan_id].add(websocket)

    try:
        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connected",
                "channel": f"scan:{scan_id}",
                "message": "Connected to scan updates",
            }
        )

        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle client commands
                if message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message.get("action") == "subscribe":
                    await websocket.send_json({"type": "subscribed", "channel": f"scan:{scan_id}"})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        active_connections[scan_id].discard(websocket)
    except Exception as e:
        active_connections[scan_id].discard(websocket)
        await websocket.close(code=1011, reason=str(e))


@router.websocket("/agents")
async def agents_websocket(websocket: WebSocket):
    """
    WebSocket for real-time agent updates.

    Receive live updates from all agents:
    - Agent status changes
    - Task assignments
    - Message broadcasts
    - System events
    """
    await websocket.accept()
    active_connections["agents"].add(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "channel": "agents",
                "message": "Connected to agent updates",
            }
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle agent commands
            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

            elif message.get("action") == "get_status":
                from api.core.agents import agent_manager

                status = {
                    "type": "agent_status",
                    "data": {
                        "total": len(agent_manager.get_all_agents()),
                        "active": len([a for a in agent_manager.get_all_agents() if a.state.value == "running"]),
                    },
                }
                await websocket.send_json(status)

    except WebSocketDisconnect:
        active_connections["agents"].discard(websocket)
    except Exception as e:
        active_connections["agents"].discard(websocket)
        await websocket.close(code=1011, reason=str(e))


@router.websocket("/system")
async def system_websocket(websocket: WebSocket):
    """
    WebSocket for system-wide notifications.

    Receive system events:
    - Maintenance notifications
    - Error alerts
    - Performance warnings
    - Updates available
    """
    await websocket.accept()
    active_connections["system"].add(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "channel": "system",
                "message": "Connected to system notifications",
            }
        )

        # Send initial system status
        import psutil

        await websocket.send_json(
            {
                "type": "system_status",
                "data": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "status": "healthy",
                },
            }
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        active_connections["system"].discard(websocket)
    except Exception as e:
        active_connections["system"].discard(websocket)
        await websocket.close(code=1011, reason=str(e))


# Helper functions for broadcasting


async def notify_scan_update(scan_id: str, data: dict):
    """Send update to all clients watching a scan"""
    channel = f"scan:{scan_id}"
    if channel in active_connections:
        await broadcast_to_channel(channel, {"type": "scan_update", "scan_id": scan_id, "data": data})


async def notify_agent_update(agent_id: str, data: dict):
    """Send agent update to all connected clients"""
    await broadcast_to_channel("agents", {"type": "agent_update", "agent_id": agent_id, "data": data})


async def notify_system_event(event_type: str, message: str, severity: str = "info"):
    """Send system-wide notification"""
    await broadcast_to_channel(
        "system",
        {
            "type": "system_event",
            "event_type": event_type,
            "message": message,
            "severity": severity,
            "timestamp": asyncio.get_event_loop().time(),
        },
    )
