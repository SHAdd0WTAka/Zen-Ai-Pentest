"""
WebSocket Connection Manager für Real-Time Updates
"""

import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # scan_id -> Set of WebSocket connections
        self.scan_connections: Dict[int, Set[WebSocket]] = {}
        # Global connections (for notifications)
        self.global_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, scan_id: int = None):
        """Accept and register new connection"""
        await websocket.accept()

        if scan_id:
            if scan_id not in self.scan_connections:
                self.scan_connections[scan_id] = set()
            self.scan_connections[scan_id].add(websocket)
            logger.info(f"WebSocket connected for scan {scan_id}")
        else:
            self.global_connections.add(websocket)
            logger.info("Global WebSocket connected")

    def disconnect(self, websocket: WebSocket, scan_id: int = None):
        """Remove connection"""
        if scan_id and scan_id in self.scan_connections:
            self.scan_connections[scan_id].discard(websocket)
            if not self.scan_connections[scan_id]:
                del self.scan_connections[scan_id]
        else:
            self.global_connections.discard(websocket)

        logger.info(f"WebSocket disconnected (scan: {scan_id})")

    async def broadcast_to_scan(self, scan_id: int, message: dict):
        """Send message to all connections for a scan"""
        if scan_id not in self.scan_connections:
            return

        disconnected = set()
        for connection in self.scan_connections[scan_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.add(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, scan_id)

    async def broadcast_global(self, message: dict):
        """Send message to all global connections"""
        disconnected = set()
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.add(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")

    def get_scan_connections_count(self, scan_id: int) -> int:
        """Get number of active connections for a scan"""
        return len(self.scan_connections.get(scan_id, set()))

    def get_global_connections_count(self) -> int:
        """Get number of global connections"""
        return len(self.global_connections)

    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "global_connections": len(self.global_connections),
            "active_scans": len(self.scan_connections),
            "total_scan_connections": sum(len(conns) for conns in self.scan_connections.values()),
        }
