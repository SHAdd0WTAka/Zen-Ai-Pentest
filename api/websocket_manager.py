"""
WebSocket Connection Manager für Echtzeit-Updates
"""

import json
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    """Verwaltet WebSocket Verbindungen"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Neue Verbindung akzeptieren"""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        """Verbindung schließen"""
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Nachricht an einzelnen Client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            pass

    async def broadcast(self, message: dict, client_id: str = None):
        """Nachricht an alle oder spezifische Clients"""
        if client_id and client_id in self.active_connections:
            connections = self.active_connections[client_id]
        else:
            connections = [
                ws
                for conns in self.active_connections.values()
                for ws in conns
            ]

        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)

        # Cleanup disconnected
        for conn in disconnected:
            for cid, conns in self.active_connections.items():
                if conn in conns:
                    conns.remove(conn)


# Globale Instanz
manager = ConnectionManager()
