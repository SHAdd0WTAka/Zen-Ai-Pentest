"""
Agent Management Endpoints

Control and monitor multi-agent collaboration system.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from api.core.agents import agent_manager
from api.core.auth import get_current_user, require_permissions
from api.models.user import User, UserRole

router = APIRouter()


class AgentResponse(BaseModel):
    """Agent status response"""

    id: str
    name: str
    role: str
    status: str
    current_task: Optional[str]
    last_activity: Optional[datetime]
    messages_processed: int
    errors_count: int


class AgentTaskRequest(BaseModel):
    """Assign task to agent"""

    agent_id: str
    task_type: str
    parameters: dict = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


class AgentMessageRequest(BaseModel):
    """Send message to agent"""

    agent_id: str
    message: str
    context: dict = Field(default_factory=dict)


@router.get("/", response_model=List[AgentResponse])
async def list_agents(current_user: User = Depends(get_current_user)):
    """List all registered agents and their status"""
    agents = agent_manager.get_all_agents()
    return [
        {
            "id": a.id,
            "name": a.name,
            "role": a.role.value,
            "status": a.state.value,
            "current_task": a.current_task,
            "last_activity": a.last_activity,
            "messages_processed": a.messages_processed,
            "errors_count": a.errors_count,
        }
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed information about a specific agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role.value,
        "status": agent.state.value,
        "current_task": agent.current_task,
        "last_activity": agent.last_activity,
        "messages_processed": agent.messages_processed,
        "errors_count": agent.errors_count,
    }


@router.post("/{agent_id}/start")
async def start_agent(agent_id: str, current_user: User = Depends(require_permissions(UserRole.ADMIN))):
    """Start an agent (admin only)"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await agent.start()
    return {"message": f"Agent {agent.name} started"}


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str, current_user: User = Depends(require_permissions(UserRole.ADMIN))):
    """Stop an agent (admin only)"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await agent.stop()
    return {"message": f"Agent {agent.name} stopped"}


@router.post("/{agent_id}/task")
async def assign_task(
    agent_id: str,
    task: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Assign a task to an agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.state.value != "running":
        raise HTTPException(status_code=400, detail="Agent is not running")

    task_id = await agent_manager.assign_task(agent_id, task.dict())

    return {"message": "Task assigned", "task_id": task_id, "agent_id": agent_id}


@router.post("/{agent_id}/message")
async def send_message(
    agent_id: str,
    message: AgentMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a message to an agent"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    response = await agent_manager.send_message_to_agent(agent_id, message.dict())

    return {"message": "Message sent", "agent_id": agent_id, "response": response}


@router.get("/{agent_id}/logs")
async def get_agent_logs(
    agent_id: str,
    limit: int = 100,
    current_user: User = Depends(require_permissions(UserRole.ADMIN)),
):
    """Get agent activity logs (admin only)"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    logs = await agent_manager.get_agent_logs(agent_id, limit)
    return {"agent_id": agent_id, "logs": logs}


@router.post("/broadcast")
async def broadcast_message(message: str, current_user: User = Depends(require_permissions(UserRole.ADMIN))):
    """Broadcast message to all agents (admin only)"""
    await agent_manager.broadcast(message)
    return {"message": "Broadcast sent to all agents"}


@router.get("/system/status")
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Get overall agent system status"""
    return {
        "total_agents": len(agent_manager.get_all_agents()),
        "active_agents": len([a for a in agent_manager.get_all_agents() if a.state.value == "running"]),
        "idle_agents": len([a for a in agent_manager.get_all_agents() if a.state.value == "idle"]),
        "error_agents": len([a for a in agent_manager.get_all_agents() if a.state.value == "error"]),
        "shared_context_keys": list(agent_manager.shared_context.keys()),
        "message_queue_size": len(agent_manager.message_history),
    }
