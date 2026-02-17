"""
Dashboard WebSocket Handler

Manages WebSocket connections for real-time dashboard updates.
"""

import asyncio
import json
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime
import logging

from .events import DashboardEvent, EventType


logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a single WebSocket connection"""
    
    def __init__(self, connection_id: str, websocket):
        self.id = connection_id
        self.websocket = websocket
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.subscriptions: Set[EventType] = set()
        self.min_priority = 1
        self.user_id: Optional[str] = None
        self.is_alive = True
    
    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message to client"""
        try:
            await self.websocket.send_json(message)
            return True
        except Exception as e:
            logger.debug(f"Failed to send to {self.id}: {e}")
            self.is_alive = False
            return False
    
    async def close(self) -> None:
        """Close connection"""
        try:
            await self.websocket.close()
        except:
            pass
        self.is_alive = False


class DashboardWebSocket:
    """
    WebSocket manager for dashboard
    
    Handles multiple client connections, subscriptions,
    and message broadcasting.
    
    Example:
        ws_manager = DashboardWebSocket()
        
        # In FastAPI route:
        @app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            await ws_manager.connect(websocket)
    """
    
    def __init__(
        self,
        ping_interval: int = 30,
        max_connections: int = 100
    ):
        self.ping_interval = ping_interval
        self.max_connections = max_connections
        
        # Connections
        self._connections: Dict[str, WebSocketConnection] = {}
        self._connection_counter = 0
        
        # Runtime
        self._running = False
        self._ping_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_connections = 0
        self._messages_sent = 0
    
    async def start(self) -> None:
        """Start WebSocket manager"""
        if self._running:
            return
        
        self._running = True
        self._ping_task = asyncio.create_task(self._ping_loop())
        logger.info("Dashboard WebSocket started")
    
    async def stop(self) -> None:
        """Stop WebSocket manager"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel ping task
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        async with self._lock:
            for conn in list(self._connections.values()):
                await conn.close()
            self._connections.clear()
        
        logger.info("Dashboard WebSocket stopped")
    
    async def connect(self, websocket, user_id: Optional[str] = None) -> str:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: WebSocket object
            user_id: Optional user ID
        
        Returns:
            Connection ID
        """
        async with self._lock:
            if len(self._connections) >= self.max_connections:
                await websocket.close(code=1008, reason="Too many connections")
                raise RuntimeError("Maximum connections reached")
            
            self._connection_counter += 1
            conn_id = f"conn-{self._connection_counter}"
            
            conn = WebSocketConnection(conn_id, websocket)
            conn.user_id = user_id
            
            self._connections[conn_id] = conn
            self._total_connections += 1
        
        logger.info(f"WebSocket connected: {conn_id} (total: {len(self._connections)})")
        
        # Send welcome message
        await conn.send({
            "type": "connected",
            "connection_id": conn_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return conn_id
    
    async def disconnect(self, connection_id: str) -> None:
        """Disconnect a client"""
        async with self._lock:
            conn = self._connections.pop(connection_id, None)
        
        if conn:
            await conn.close()
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> None:
        """
        Handle incoming message from client
        
        Supported actions:
        - subscribe: Subscribe to event types
        - unsubscribe: Unsubscribe from event types
        - ping: Ping/pong
        - get_stats: Get connection statistics
        """
        conn = self._connections.get(connection_id)
        if not conn:
            return
        
        action = message.get("action")
        
        if action == "subscribe":
            event_types = message.get("event_types", [])
            for et in event_types:
                try:
                    conn.subscriptions.add(EventType(et))
                except ValueError:
                    pass
            
            await conn.send({
                "type": "subscribed",
                "subscriptions": [et.value for et in conn.subscriptions]
            })
        
        elif action == "unsubscribe":
            event_types = message.get("event_types", [])
            for et in event_types:
                try:
                    conn.subscriptions.discard(EventType(et))
                except ValueError:
                    pass
        
        elif action == "ping":
            conn.last_ping = datetime.utcnow()
            await conn.send({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
        
        elif action == "set_priority":
            conn.min_priority = message.get("min_priority", 1)
        
        elif action == "get_stats":
            await conn.send({
                "type": "stats",
                "data": {
                    "connection_id": conn_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscriptions": len(conn.subscriptions)
                }
            })
    
    async def broadcast(
        self,
        event: DashboardEvent,
        exclude: Optional[Set[str]] = None
    ) -> int:
        """
        Broadcast event to all connected clients
        
        Args:
            event: Event to broadcast
            exclude: Connection IDs to exclude
        
        Returns:
            Number of clients notified
        """
        exclude = exclude or set()
        message = event.to_dict()
        sent_count = 0
        dead_connections = []
        
        async with self._lock:
            connections = list(self._connections.items())
        
        for conn_id, conn in connections:
            if conn_id in exclude:
                continue
            
            if not conn.is_alive:
                dead_connections.append(conn_id)
                continue
            
            # Check subscription
            if conn.subscriptions and event.type not in conn.subscriptions:
                continue
            
            # Check priority
            if event.priority < conn.min_priority:
                continue
            
            if await conn.send(message):
                sent_count += 1
        
        # Cleanup dead connections
        for conn_id in dead_connections:
            await self.disconnect(conn_id)
        
        self._messages_sent += sent_count
        return sent_count
    
    async def send_to_user(
        self,
        user_id: str,
        event: DashboardEvent
    ) -> int:
        """
        Send event to specific user
        
        Args:
            user_id: User ID
            event: Event to send
        
        Returns:
            Number of clients notified
        """
        message = event.to_dict()
        sent_count = 0
        
        async with self._lock:
            connections = [
                conn for conn in self._connections.values()
                if conn.user_id == user_id
            ]
        
        for conn in connections:
            if await conn.send(message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """Send message to specific connection"""
        conn = self._connections.get(connection_id)
        if conn and conn.is_alive:
            return await conn.send(message)
        return False
    
    async def _ping_loop(self) -> None:
        """Keep-alive ping loop"""
        while self._running:
            try:
                await asyncio.sleep(self.ping_interval)
                
                now = datetime.utcnow()
                dead_connections = []
                
                async with self._lock:
                    connections = list(self._connections.items())
                
                for conn_id, conn in connections:
                    # Check if connection is stale
                    if (now - conn.last_ping).seconds > self.ping_interval * 3:
                        dead_connections.append(conn_id)
                        continue
                    
                    # Send ping
                    try:
                        await conn.send({"type": "ping"})
                    except:
                        dead_connections.append(conn_id)
                
                # Cleanup dead connections
                for conn_id in dead_connections:
                    await self.disconnect(conn_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ping loop error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            "active_connections": len(self._connections),
            "total_connections": self._total_connections,
            "messages_sent": self._messages_sent,
            "max_connections": self.max_connections
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information"""
        conn = self._connections.get(connection_id)
        if not conn:
            return None
        
        return {
            "id": conn.id,
            "user_id": conn.user_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_ping": conn.last_ping.isoformat(),
            "subscriptions": [et.value for et in conn.subscriptions],
            "is_alive": conn.is_alive
        }
