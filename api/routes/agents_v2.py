"""
Agent Communication v2 API Routes
=================================

REST API endpoints for agent management and communication.

Routes:
- POST /api/v2/agents/register - Register new agent
- POST /api/v2/agents/{id}/revoke - Revoke agent credentials
- POST /api/v2/agents/{id}/rotate - Rotate API keys
- GET  /api/v2/agents - List active agents
- GET  /api/v2/agents/{id} - Get agent details
- WS   /agents/stream - WebSocket for real-time messaging
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from agents.v2.auth_manager import AgentAuthenticator, AgentRole
from auth import Permission, require_permission
from database.auth_models import get_auth_db

logger = logging.getLogger("api.agents.v2")
router = APIRouter(prefix="/api/v2/agents", tags=["Agent Communication v2"])
security = HTTPBearer()


# ============================================================================
# Dependencies
# ============================================================================


def get_authenticator(db: Session = Depends(get_auth_db)):
    """Get agent authenticator"""
    return AgentAuthenticator(db)


# ============================================================================
# REST Endpoints
# ============================================================================


@router.post("/register", response_model=dict)
async def register_agent(
    request: dict,
    authenticator: AgentAuthenticator = Depends(get_authenticator),
    user: dict = Depends(require_permission(Permission.AGENT_REGISTER)),
):
    """
    Register a new agent

    Requires: agent:register permission

    Request:
    {
        "name": "research-agent-1",
        "role": "researcher",
        "description": "Optional description",
        "expires_days": 90,
        "rate_limit": 1000
    }

    Response:
    {
        "agent_id": "agt_xxx",
        "api_key": "zen_xxx",
        "api_secret": "sec_yyy",  # ONLY SHOWN ONCE
        "role": "researcher",
        "permissions": [...],
        "created_at": "...",
        "expires_at": "..."
    }
    """
    name = request.get("name")
    role_str = request.get("role", "scanner")
    description = request.get("description")
    expires_days = request.get("expires_days", 90)
    rate_limit = request.get("rate_limit", 1000)

    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent name is required")

    # Validate role
    try:
        role = AgentRole(role_str)
    except ValueError:
        valid_roles = [r.value for r in AgentRole]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Valid roles: {valid_roles}")

    # Generate credentials
    try:
        creds = authenticator.generate_api_key(
            role=role, name=name, description=description, expires_days=expires_days, rate_limit=rate_limit
        )
    except Exception as e:
        logger.error(f"Failed to generate credentials: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate agent credentials")

    logger.info(f"Registered agent {creds.agent_id} with role {role.value}")

    return {
        "agent_id": creds.agent_id,
        "api_key": creds.api_key,
        "api_secret": creds.api_secret,  # IMPORTANT: Only shown once!
        "role": creds.role.value,
        "permissions": [p.value for p in creds.permissions],
        "created_at": creds.created_at.isoformat(),
        "expires_at": creds.expires_at.isoformat() if creds.expires_at else None,
        "warning": "Store the api_secret securely - it will not be shown again!",
    }


@router.post("/{agent_id}/revoke")
async def revoke_agent(
    agent_id: str,
    request: Optional[dict] = None,
    authenticator: AgentAuthenticator = Depends(get_authenticator),
    user: dict = Depends(require_permission(Permission.AGENT_UNREGISTER)),
):
    """
    Revoke agent credentials

    Requires: agent:unregister permission
    """
    reason = request.get("reason", "admin_action") if request else "admin_action"

    success = authenticator.revoke_key(agent_id, reason)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")

    logger.info(f"Revoked agent {agent_id}: {reason}")

    return {"message": f"Agent {agent_id} revoked successfully", "reason": reason}


@router.post("/{agent_id}/rotate")
async def rotate_agent_key(
    agent_id: str,
    authenticator: AgentAuthenticator = Depends(get_authenticator),
    user: dict = Depends(require_permission(Permission.AGENT_REGISTER)),
):
    """
    Rotate agent API key

    Generates new credentials and invalidates old ones.

    Requires: agent:register permission
    """
    new_creds = authenticator.rotate_key(agent_id)

    if not new_creds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found or already revoked")

    logger.info(f"Rotated key for agent {agent_id}")

    return {
        "agent_id": new_creds.agent_id,
        "api_key": new_creds.api_key,
        "api_secret": new_creds.api_secret,  # ONLY SHOWN ONCE
        "role": new_creds.role.value,
        "expires_at": new_creds.expires_at.isoformat() if new_creds.expires_at else None,
        "warning": "Store the api_secret securely - it will not be shown again!",
    }


@router.get("/")
async def list_agents(
    authenticator: AgentAuthenticator = Depends(get_authenticator),
    user: dict = Depends(require_permission(Permission.AGENT_LIST)),
):
    """
    List active agents

    Requires: agent:list permission
    """
    agents = authenticator.list_active_agents()

    return {
        "agents": [
            {
                "agent_id": a.agent_id,
                "role": a.role.value,
                "permissions": [p.value for p in a.permissions],
                "is_active": a.is_active,
                "last_seen": a.last_seen.isoformat() if a.last_seen else None,
            }
            for a in agents
        ],
        "count": len(agents),
    }


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    authenticator: AgentAuthenticator = Depends(get_authenticator),
    user: dict = Depends(require_permission(Permission.AGENT_LIST)),
):
    """
    Get agent details

    Requires: agent:list permission
    """
    # Find agent in list
    agents = authenticator.list_active_agents()
    agent = next((a for a in agents if a.agent_id == agent_id), None)

    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found")

    return {
        "agent_id": agent.agent_id,
        "role": agent.role.value,
        "permissions": [p.value for p in agent.permissions],
        "is_active": agent.is_active,
        "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================


class AgentConnectionManager:
    """Manage WebSocket connections from agents"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.authenticator: Optional[AgentAuthenticator] = None

    async def connect(self, websocket: WebSocket, authenticator: AgentAuthenticator):
        """Accept connection and wait for authentication"""
        self.authenticator = authenticator
        await websocket.accept()

        try:
            # Wait for authentication message
            auth_data = await websocket.receive_json()

            if auth_data.get("type") != "auth":
                await websocket.send_json({"type": "auth_failed", "error": "Expected auth message"})
                await websocket.close()
                return None

            # Authenticate
            identity = authenticator.authenticate(auth_data.get("api_key"), auth_data.get("api_secret"))

            if not identity:
                await websocket.send_json({"type": "auth_failed", "error": "Invalid credentials"})
                await websocket.close()
                return None

            # Store connection
            self.active_connections[identity.agent_id] = websocket

            # Send success
            await websocket.send_json(
                {
                    "type": "auth_success",
                    "agent_id": identity.agent_id,
                    "role": identity.role.value,
                    "permissions": [p.value for p in identity.permissions],
                }
            )

            logger.info(f"Agent {identity.agent_id} connected via WebSocket")
            return identity

        except Exception as e:
            logger.error(f"WebSocket auth error: {e}")
            await websocket.close()
            return None

    async def disconnect(self, agent_id: str):
        """Remove connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            logger.info(f"Agent {agent_id} disconnected")

    async def send_message(self, agent_id: str, message: dict):
        """Send message to specific agent"""
        if agent_id in self.active_connections:
            await self.active_connections[agent_id].send_json(message)

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        """Broadcast to all agents"""
        for agent_id, ws in self.active_connections.items():
            if agent_id != exclude:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to {agent_id}: {e}")


# Global connection manager
agent_manager = AgentConnectionManager()


@router.websocket("/stream")
async def agent_websocket(websocket: WebSocket, authenticator: AgentAuthenticator = Depends(get_authenticator)):
    """
    WebSocket endpoint for agent communication

    Protocol:
    1. Connect
    2. Send auth message: {"type": "auth", "api_key": "...", "api_secret": "..."}
    3. Wait for auth_success
    4. Send/receive messages

    Message format:
    {
        "type": "message",
        "recipient": "agent_id" or "broadcast",
        "payload": {...}
    }

    Server responses:
    {
        "type": "ack",
        "message_id": "...",
        "status": "delivered"
    }
    """
    identity = await agent_manager.connect(websocket, authenticator)

    if not identity:
        return

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            msg_type = data.get("type")

            if msg_type == "message":
                # Handle agent-to-agent message
                recipient = data.get("recipient")
                payload = data.get("payload", {})

                # Send acknowledgment
                await websocket.send_json(
                    {
                        "type": "ack",
                        "message_id": data.get("message_id", "unknown"),
                        "status": "received",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                # Route message
                if recipient == "broadcast":
                    await agent_manager.broadcast(
                        {"type": "message", "sender": identity.agent_id, "payload": payload}, exclude=identity.agent_id
                    )
                elif recipient in agent_manager.active_connections:
                    await agent_manager.send_message(
                        recipient, {"type": "message", "sender": identity.agent_id, "payload": payload}
                    )

            elif msg_type == "heartbeat":
                # Respond to heartbeat
                await websocket.send_json({"type": "heartbeat_ack", "timestamp": datetime.utcnow().isoformat()})

            elif msg_type == "disconnect":
                break

    except WebSocketDisconnect:
        logger.info(f"Agent {identity.agent_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {identity.agent_id}: {e}")
    finally:
        await agent_manager.disconnect(identity.agent_id)


# ============================================================================
# Legacy Compatibility
# ============================================================================


@router.post("/legacy-auth")
async def legacy_agent_auth(request: dict, authenticator: AgentAuthenticator = Depends(get_authenticator)):
    """
    Legacy authentication endpoint for backward compatibility

    Creates agent credentials from legacy auth tokens.
    """
    # This would handle migration from old auth system
    # For now, just return error directing to new endpoint
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Legacy auth deprecated. Use /register endpoint instead.")
