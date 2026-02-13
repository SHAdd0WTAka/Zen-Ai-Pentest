"""
WebSocket Endpoint for Agent Communication Protocol (ACP)
Handles real-time messaging between agents
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter
from pydantic import ValidationError
from typing import Dict, List
from datetime import datetime
import json
import asyncio

# Import ACP models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agent_comm.models import AgentMessage, MessageContent, MessageContext, MessageType

router = APIRouter(prefix="/ws/agent-comm", tags=["agent-communication"])


class ConnectionManager:
    """
    Manages WebSocket connections for multi-agent sessions
    
    Structure: {session_id: [{"websocket": ws, "agent_id": agent_id}, ...]}
    """
    def __init__(self):
        self.active_connections: Dict[str, List[Dict]] = {}
        self.agent_sessions: Dict[str, str] = {}  # agent_id -> session_id
    
    async def connect(self, websocket: WebSocket, session_id: str, agent_id: str):
        """Accept connection and register agent"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append({
            "websocket": websocket,
            "agent_id": agent_id
        })
        self.agent_sessions[agent_id] = session_id
        
        print(f"Agent {agent_id} connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket, session_id: str, agent_id: str):
        """Remove connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id] = [
                conn for conn in self.active_connections[session_id] 
                if conn["websocket"] != websocket
            ]
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        if agent_id in self.agent_sessions:
            del self.agent_sessions[agent_id]
        
        print(f"Agent {agent_id} disconnected from session {session_id}")
    
    async def broadcast(self, message: AgentMessage, session_id: str):
        """Broadcast message to all agents in session"""
        if session_id not in self.active_connections:
            return
        
        message_dict = message.model_dump()
        disconnected = []
        
        for conn in self.active_connections[session_id]:
            try:
                await conn["websocket"].send_json(message_dict)
            except Exception as e:
                print(f"Failed to send to {conn['agent_id']}: {e}")
                disconnected.append(conn)
        
        # Clean up failed connections
        for conn in disconnected:
            self.active_connections[session_id].remove(conn)
    
    async def send_to_agent(self, message: AgentMessage, target_agent: str):
        """Send message to specific agent"""
        if target_agent not in self.agent_sessions:
            return False
        
        session_id = self.agent_sessions[target_agent]
        
        for conn in self.active_connections.get(session_id, []):
            if conn["agent_id"] == target_agent:
                try:
                    await conn["websocket"].send_json(message.model_dump())
                    return True
                except Exception as e:
                    print(f"Failed to send to {target_agent}: {e}")
                    return False
        return False
    
    def get_session_agents(self, session_id: str) -> List[str]:
        """Get list of connected agents in session"""
        return [conn["agent_id"] for conn in self.active_connections.get(session_id, [])]


manager = ConnectionManager()


@router.websocket("/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for ACP v1.1
    
    Query Parameters:
        agent_id: ID of the connecting agent (required)
    
    Example JavaScript client:
        const ws = new WebSocket(
            "ws://localhost:8000/ws/agent-comm/scan_xyz789?agent_id=analysis-bot-1"
        );
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            console.log("Received:", msg);
        };
        ws.send(JSON.stringify({
            message_id: "msg_001",
            agent_id: "analysis-bot-1",
            type: "observe",
            content: {observation: "Port 80 open"},
            targets: ["orchestrator"],
            context: {target: "example.com", session_id: "scan_xyz789"}
        }));
    """
    # Get agent_id from query params
    agent_id = websocket.query_params.get("agent_id")
    if not agent_id:
        await websocket.close(code=4000, reason="agent_id required")
        return
    
    await manager.connect(websocket, session_id, agent_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            try:
                # Validate with Pydantic
                msg = AgentMessage.model_validate(data)
                
                # Ensure message matches session
                if msg.session_id != session_id:
                    error_msg = {
                        "type": "error",
                        "error_message": f"Session mismatch: {msg.session_id} != {session_id}"
                    }
                    await websocket.send_json(error_msg)
                    continue
                
                # Broadcast to targets
                await manager.broadcast(msg, session_id)
                
                # TODO: Persist to database
                # db.add(AgentCommLog.from_message(msg))
                # db.commit()
                
                print(f"[{session_id}] {msg.agent_id} -> {msg.type}: {msg.message_id}")
                
            except ValidationError as e:
                # Send validation error back to sender
                error_msg = {
                    "type": "error",
                    "error_message": f"Validation error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_json(error_msg)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id, agent_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id, agent_id)


@router.get("/sessions/{session_id}/agents")
async def get_connected_agents(session_id: str):
    """Get list of connected agents in a session"""
    agents = manager.get_session_agents(session_id)
    return {
        "session_id": session_id,
        "connected_agents": agents,
        "count": len(agents)
    }
