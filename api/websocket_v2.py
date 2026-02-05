"""
WebSocket v2.0 - Real-time Updates
Q2 2026 Feature
"""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManagerV2:
    """Advanced WebSocket connection manager with rooms"""
    
    def __init__(self):
        # Active connections by room
        self.rooms: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "scans": set(),
            "findings": set(),
            "notifications": set()
        }
        # User connections
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, room: str = "dashboard", user_id: str = None):
        """Connect client to room"""
        await websocket.accept()
        
        if room in self.rooms:
            self.rooms[room].add(websocket)
        
        if user_id:
            self.user_connections[user_id] = websocket
        
        logger.info(f"Client connected to room: {room}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "room": room,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, room: str = None):
        """Disconnect client"""
        if room and room in self.rooms:
            self.rooms[room].discard(websocket)
        else:
            # Remove from all rooms
            for room_set in self.rooms.values():
                room_set.discard(websocket)
        
        # Remove from user connections
        for user_id, conn in list(self.user_connections.items()):
            if conn == websocket:
                del self.user_connections[user_id]
        
        logger.info("Client disconnected")
    
    async def broadcast_to_room(self, room: str, message: dict):
        """Broadcast message to all clients in room"""
        if room not in self.rooms:
            return
        
        disconnected = set()
        for connection in self.rooms[room]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.rooms[room].discard(conn)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception:
                del self.user_connections[user_id]
    
    async def broadcast_scan_update(self, scan_id: str, status: str, progress: int = None):
        """Broadcast scan progress update"""
        await self.broadcast_to_room("scans", {
            "type": "scan_update",
            "scan_id": scan_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_finding(self, finding: dict):
        """Broadcast new finding discovery"""
        await self.broadcast_to_room("findings", {
            "type": "new_finding",
            "finding": finding,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_notification(self, title: str, message: str, severity: str = "info"):
        """Broadcast system notification"""
        await self.broadcast_to_room("notifications", {
            "type": "notification",
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_room_stats(self) -> dict:
        """Get connection statistics"""
        return {
            room: len(connections)
            for room, connections in self.rooms.items()
        }


# Global manager instance
manager_v2 = ConnectionManagerV2()


async def websocket_dashboard_endpoint(websocket: WebSocket):
    """Dashboard real-time updates"""
    await manager_v2.connect(websocket, room="dashboard")
    try:
        while True:
            # Receive ping from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
    except WebSocketDisconnect:
        manager_v2.disconnect(websocket, room="dashboard")


async def websocket_scans_endpoint(websocket: WebSocket):
    """Scan progress real-time updates"""
    await manager_v2.connect(websocket, room="scans")
    try:
        while True:
            data = await websocket.receive_text()
            # Handle scan subscription requests
            message = json.loads(data)
            
            if message.get("action") == "subscribe_scan":
                scan_id = message.get("scan_id")
                await websocket.send_json({
                    "type": "subscribed",
                    "scan_id": scan_id,
                    "message": f"Subscribed to scan {scan_id} updates"
                })
                
    except WebSocketDisconnect:
        manager_v2.disconnect(websocket, room="scans")


async def websocket_notifications_endpoint(websocket: WebSocket, user_id: str = None):
    """User-specific notifications"""
    await manager_v2.connect(websocket, room="notifications", user_id=user_id)
    try:
        while True:
            _ = await websocket.receive_text()
            # Acknowledge receipt
            await websocket.send_json({
                "type": "ack",
                "received": True
            })
    except WebSocketDisconnect:
        manager_v2.disconnect(websocket, room="notifications")
