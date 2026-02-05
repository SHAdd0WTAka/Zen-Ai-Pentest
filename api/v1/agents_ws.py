"""
Agent Monitoring WebSocket API - Issue #24

Real-time agent activity monitoring and thought process streaming.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.auth import verify_token
from database.models import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents-ws"])

# ============================================================================
# Agent State Management
# ============================================================================

class AgentState(str, Enum):
    """Agent operational states"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class AgentRole(str, Enum):
    """Agent roles"""
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    EXPLOIT = "exploit"
    COORDINATOR = "coordinator"
    REPORTER = "reporter"
    POST_EXPLOITATION = "post_exploitation"


# In-memory agent registry (in production, use Redis)
agent_registry: Dict[str, Dict[str, Any]] = {}
agent_thoughts: Dict[str, List[Dict]] = {}
agent_connections: Dict[str, Set[WebSocket]] = {}


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentInfo(BaseModel):
    """Agent information"""
    id: str
    name: str
    role: str
    state: str
    current_task: Optional[str]
    task_progress: int = Field(0, ge=0, le=100)
    memory_entries: int
    queue_size: int
    connected_since: str
    last_activity: str
    current_tool: Optional[str]
    scan_id: Optional[int]


class AgentThought(BaseModel):
    """Agent thought process entry"""
    id: str
    agent_id: str
    timestamp: str
    thought_type: str  # reasoning, observation, action, reflection, conclusion
    content: str
    confidence: Optional[float] = Field(None, ge=0, le=1)
    related_tool: Optional[str]
    metadata: Dict[str, Any]


class AgentAction(BaseModel):
    """Agent action record"""
    id: str
    agent_id: str
    timestamp: str
    action_type: str  # tool_call, observation, message, decision
    target: Optional[str]
    parameters: Dict[str, Any]
    result: Optional[str]
    duration_ms: Optional[int]
    success: Optional[bool]


class AgentMessage(BaseModel):
    """Inter-agent message"""
    id: str
    sender_id: str
    sender_name: str
    recipient_id: str
    msg_type: str
    content: str
    timestamp: str
    priority: int
    requires_response: bool


# ============================================================================
# Helper Functions
# ============================================================================

def register_agent(agent_id: str, name: str, role: str, scan_id: Optional[int] = None):
    """Register a new agent in the system"""
    agent_registry[agent_id] = {
        "id": agent_id,
        "name": name,
        "role": role,
        "state": AgentState.IDLE,
        "current_task": None,
        "task_progress": 0,
        "memory_entries": 0,
        "queue_size": 0,
        "connected_since": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
        "current_tool": None,
        "scan_id": scan_id
    }
    agent_thoughts[agent_id] = []
    agent_connections[agent_id] = set()
    logger.info(f"Agent registered: {name} ({agent_id})")
    return agent_registry[agent_id]


def unregister_agent(agent_id: str):
    """Unregister an agent"""
    if agent_id in agent_registry:
        del agent_registry[agent_id]
    if agent_id in agent_thoughts:
        del agent_thoughts[agent_id]
    if agent_id in agent_connections:
        del agent_connections[agent_id]
    logger.info(f"Agent unregistered: {agent_id}")


def update_agent_state(agent_id: str, state: AgentState, **kwargs):
    """Update agent state and metadata"""
    if agent_id in agent_registry:
        agent_registry[agent_id]["state"] = state
        agent_registry[agent_id]["last_activity"] = datetime.utcnow().isoformat()
        for key, value in kwargs.items():
            if key in agent_registry[agent_id]:
                agent_registry[agent_id][key] = value


def add_agent_thought(agent_id: str, thought_type: str, content: str, 
                      confidence: float = None, related_tool: str = None,
                      metadata: Dict = None) -> Dict:
    """Add a thought process entry for an agent"""
    if agent_id not in agent_thoughts:
        agent_thoughts[agent_id] = []
    
    thought = {
        "id": f"{agent_id}-{len(agent_thoughts[agent_id])}",
        "agent_id": agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "thought_type": thought_type,
        "content": content,
        "confidence": confidence,
        "related_tool": related_tool,
        "metadata": metadata or {}
    }
    
    agent_thoughts[agent_id].append(thought)
    
    # Keep only last 1000 thoughts
    if len(agent_thoughts[agent_id]) > 1000:
        agent_thoughts[agent_id] = agent_thoughts[agent_id][-1000:]
    
    return thought


async def broadcast_to_agent(agent_id: str, message: Dict):
    """Broadcast message to all connections for a specific agent"""
    if agent_id not in agent_connections:
        return
    
    disconnected = set()
    for ws in agent_connections[agent_id]:
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            disconnected.add(ws)
    
    # Cleanup disconnected
    for ws in disconnected:
        agent_connections[agent_id].discard(ws)


async def broadcast_agent_update(agent_id: str, update_type: str, data: Dict):
    """Broadcast agent update to all connected clients"""
    message = {
        "type": update_type,
        "agent_id": agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }
    
    # Broadcast to agent-specific connections
    await broadcast_to_agent(agent_id, message)
    
    # Also broadcast to global connections
    await broadcast_to_agent("global", message)


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/active", response_model=List[AgentInfo])
async def get_active_agents(
    scan_id: Optional[int] = None,
    role: Optional[str] = None,
    state: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """
    Get list of active agents.
    
    - **scan_id**: Filter by associated scan
    - **role**: Filter by agent role
    - **state**: Filter by agent state
    """
    agents = []
    
    for agent_id, info in agent_registry.items():
        # Apply filters
        if scan_id and info.get("scan_id") != scan_id:
            continue
        if role and info.get("role") != role:
            continue
        if state and info.get("state") != state:
            continue
        
        agents.append(AgentInfo(**info))
    
    return agents


@router.get("/{agent_id}/info", response_model=AgentInfo)
async def get_agent_info(
    agent_id: str,
    user: dict = Depends(verify_token)
):
    """Get detailed information about a specific agent"""
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentInfo(**agent_registry[agent_id])


@router.get("/{agent_id}/thoughts")
async def get_agent_thoughts(
    agent_id: str,
    limit: int = 50,
    thought_type: Optional[str] = None,
    since: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """
    Get agent thought process history.
    
    - **limit**: Number of thoughts to return (default: 50, max: 200)
    - **thought_type**: Filter by thought type (reasoning, observation, action, reflection, conclusion)
    - **since**: Get thoughts after this ISO timestamp
    
    Returns thoughts in reverse chronological order.
    """
    if agent_id not in agent_thoughts:
        raise HTTPException(status_code=404, detail="Agent not found or no thoughts recorded")
    
    thoughts = agent_thoughts[agent_id]
    
    # Filter by type
    if thought_type:
        thoughts = [t for t in thoughts if t.get("thought_type") == thought_type]
    
    # Filter by timestamp
    if since:
        thoughts = [t for t in thoughts if t.get("timestamp", "") > since]
    
    # Sort by timestamp descending
    thoughts = sorted(thoughts, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Limit
    limit = min(limit, 200)
    
    return {
        "agent_id": agent_id,
        "total": len(thoughts),
        "thoughts": thoughts[:limit]
    }


@router.get("/{agent_id}/timeline")
async def get_agent_timeline(
    agent_id: str,
    user: dict = Depends(verify_token)
):
    """
    Get agent activity timeline.
    
    Returns a chronological list of state changes and activities.
    """
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    thoughts = agent_thoughts.get(agent_id, [])
    
    # Build timeline from thoughts
    timeline = []
    for thought in sorted(thoughts, key=lambda x: x.get("timestamp", "")):
        timeline.append({
            "timestamp": thought["timestamp"],
            "type": thought["thought_type"],
            "content": thought["content"][:200],  # Truncate for timeline
            "confidence": thought.get("confidence"),
            "tool": thought.get("related_tool")
        })
    
    return {
        "agent_id": agent_id,
        "agent_info": agent_registry[agent_id],
        "timeline": timeline
    }


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """
    WebSocket for monitoring a specific agent.
    
    Clients will receive:
    - state_change: When agent state changes
    - thought: New thought process entries
    - action: Agent actions being executed
    - progress: Task progress updates
    - message: Inter-agent messages
    - heartbeat: Periodic keepalive
    
    Client messages:
    - { "action": "ping" }
    - { "action": "get_status" }
    - { "action": "get_thoughts", "limit": 10 }
    - { "action": "subscribe", "events": ["thoughts", "actions"] }
    """
    # Accept connection
    await websocket.accept()
    
    # Register connection
    if agent_id not in agent_connections:
        agent_connections[agent_id] = set()
    agent_connections[agent_id].add(websocket)
    
    # Also connect to global channel
    if "global" not in agent_connections:
        agent_connections["global"] = set()
    agent_connections["global"].add(websocket)
    
    try:
        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connected",
            "agent_id": agent_id,
            "message": f"Connected to agent {agent_id} monitoring",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send initial agent info if available
        if agent_id in agent_registry:
            await websocket.send_json({
                "type": "agent_info",
                "data": agent_registry[agent_id]
            })
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                action = message.get("action")
                
                if action == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif action == "get_status":
                    if agent_id in agent_registry:
                        await websocket.send_json({
                            "type": "agent_info",
                            "data": agent_registry[agent_id]
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Agent not found"
                        })
                
                elif action == "get_thoughts":
                    limit = message.get("limit", 10)
                    thoughts = agent_thoughts.get(agent_id, [])[-limit:]
                    await websocket.send_json({
                        "type": "thoughts",
                        "data": thoughts
                    })
                
                elif action == "subscribe":
                    events = message.get("events", ["all"])
                    await websocket.send_json({
                        "type": "subscribed",
                        "events": events
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
                
    except WebSocketDisconnect:
        # Cleanup connections
        agent_connections[agent_id].discard(websocket)
        agent_connections["global"].discard(websocket)
        logger.info(f"Agent WebSocket disconnected: {agent_id}")
        
    except Exception as e:
        logger.error(f"Agent WebSocket error for {agent_id}: {e}")
        agent_connections[agent_id].discard(websocket)
        agent_connections["global"].discard(websocket)


@router.websocket("/ws/global")
async def global_agents_websocket(websocket: WebSocket):
    """
    WebSocket for monitoring all agents globally.
    
    Receives updates for all agents including:
    - agent_registered: New agent joined
    - agent_unregistered: Agent left
    - state_change: Any agent state change
    - thought: Aggregated thought stream (rate limited)
    - heartbeat: System health
    """
    await websocket.accept()
    
    if "global" not in agent_connections:
        agent_connections["global"] = set()
    agent_connections["global"].add(websocket)
    
    try:
        # Send current active agents
        active_agents = [info for info in agent_registry.values()]
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to global agent monitoring",
            "active_agents": active_agents,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "active_agent_count": len(agent_registry),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif action == "get_agents":
                await websocket.send_json({
                    "type": "agents_list",
                    "agents": list(agent_registry.values())
                })
                
    except WebSocketDisconnect:
        agent_connections["global"].discard(websocket)
    except Exception as e:
        logger.error(f"Global agents WebSocket error: {e}")
        agent_connections["global"].discard(websocket)


# ============================================================================
# Agent Control Endpoints
# ============================================================================

@router.post("/{agent_id}/control")
async def control_agent(
    agent_id: str,
    action: str,  # pause, resume, stop
    reason: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """
    Send control command to an agent.
    
    - **action**: pause, resume, stop
    - **reason**: Reason for the control action
    """
    if agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    valid_actions = ["pause", "resume", "stop"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Broadcast control command
    await broadcast_to_agent(agent_id, {
        "type": "control_command",
        "action": action,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Update agent state
    if action == "pause":
        update_agent_state(agent_id, AgentState.WAITING)
    elif action == "resume":
        update_agent_state(agent_id, AgentState.THINKING)
    elif action == "stop":
        update_agent_state(agent_id, AgentState.STOPPED)
    
    return {
        "message": f"Control command '{action}' sent to agent {agent_id}",
        "agent_id": agent_id,
        "action": action
    }


# ============================================================================
# Integration helpers (to be called from agent code)
# ============================================================================

async def publish_agent_thought(agent_id: str, thought_type: str, content: str, **kwargs):
    """
    Publish a thought from an agent.
    To be called from agent implementations.
    """
    thought = add_agent_thought(agent_id, thought_type, content, **kwargs)
    await broadcast_agent_update(agent_id, "thought", {"thought": thought})
    return thought


async def publish_agent_action(agent_id: str, action_type: str, target: str = None, 
                                parameters: Dict = None, result: str = None, 
                                duration_ms: int = None, success: bool = None):
    """
    Publish an action from an agent.
    To be called from agent implementations.
    """
    action = {
        "id": f"{agent_id}-{datetime.utcnow().timestamp()}",
        "agent_id": agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "action_type": action_type,
        "target": target,
        "parameters": parameters or {},
        "result": result,
        "duration_ms": duration_ms,
        "success": success
    }
    
    await broadcast_agent_update(agent_id, "action", {"action": action})
    return action


async def publish_agent_state_change(agent_id: str, new_state: AgentState, **kwargs):
    """
    Publish a state change from an agent.
    To be called from agent implementations.
    """
    update_agent_state(agent_id, new_state, **kwargs)
    
    await broadcast_agent_update(agent_id, "state_change", {
        "new_state": new_state.value,
        **kwargs
    })
