"""
Agent Management Router
Handles agent registration, monitoring, and task assignment
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.routers.auth import get_current_active_user, require_admin
from app.schemas.agents import (
    AgentCreate,
    AgentListResponse,
    AgentMetrics,
    AgentResponse,
    AgentStatusUpdate,
    AgentTaskAssign,
)

router = APIRouter()

# In-memory agent registry (in production, use Redis)
registered_agents: dict = {}
agent_tasks: dict = {}


@router.get("", response_model=AgentListResponse)
async def list_agents(
    status: Optional[str] = None,
    capability: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all registered agents with filtering."""
    agents_list = []

    for agent_id, agent_data in registered_agents.items():
        # Apply filters
        if status and agent_data.get("status") != status:
            continue
        if capability and capability not in agent_data.get("capabilities", []):
            continue

        agents_list.append(agent_data)

    # Sort by last heartbeat (most recent first)
    agents_list.sort(key=lambda x: x.get("lastHeartbeat", ""), reverse=True)

    # Pagination
    total = len(agents_list)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_agents = agents_list[start_idx:end_idx]

    return AgentListResponse(
        success=True,
        data=paginated_agents,
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit,
            "hasNext": end_idx < total,
            "hasPrev": page > 1,
        },
    )


@router.get("/stats")
async def get_agent_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get agent statistics."""
    total = len(registered_agents)
    online = sum(1 for a in registered_agents.values() if a.get("status") == "online")
    busy = sum(1 for a in registered_agents.values() if a.get("status") == "busy")
    offline = sum(1 for a in registered_agents.values() if a.get("status") == "offline")

    total_tasks_completed = sum(a.get("tasksCompleted", 0) for a in registered_agents.values())
    total_tasks_failed = sum(a.get("tasksFailed", 0) for a in registered_agents.values())

    return {
        "success": True,
        "data": {
            "total": total,
            "online": online,
            "busy": busy,
            "offline": offline,
            "totalTasksCompleted": total_tasks_completed,
            "totalTasksFailed": total_tasks_failed,
        },
    }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed information about a specific agent."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent_data = registered_agents[agent_id]

    # Add current task if any
    if agent_id in agent_tasks:
        agent_data["currentTask"] = agent_tasks[agent_id]

    return AgentResponse(success=True, data=agent_data)


@router.post(
    "/register",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Register a new agent (admin only)."""
    import uuid

    agent_id = str(uuid.uuid4())

    new_agent = {
        "id": agent_id,
        "name": agent_data.name,
        "hostname": agent_data.hostname,
        "ipAddress": agent_data.ip_address,
        "version": agent_data.version,
        "status": "online",
        "capabilities": agent_data.capabilities,
        "currentTask": None,
        "lastHeartbeat": datetime.now(timezone.utc).isoformat(),
        "tasksCompleted": 0,
        "tasksFailed": 0,
        "cpuUsage": 0.0,
        "memoryUsage": 0.0,
        "diskUsage": 0.0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }

    registered_agents[agent_id] = new_agent

    return AgentResponse(success=True, data=new_agent)


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
    metrics: AgentMetrics,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Receive agent heartbeat with metrics."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent = registered_agents[agent_id]

    # Update metrics
    agent["lastHeartbeat"] = datetime.now(timezone.utc).isoformat()
    agent["cpuUsage"] = metrics.cpu_usage
    agent["memoryUsage"] = metrics.memory_usage
    agent["diskUsage"] = metrics.disk_usage
    agent["updatedAt"] = datetime.now(timezone.utc).isoformat()

    # Check if agent was offline, mark as online
    if agent["status"] == "offline":
        agent["status"] = "online"

    return {
        "success": True,
        "message": "Heartbeat received",
        "data": {"agentId": agent_id, "status": agent["status"]},
    }


@router.patch("/{agent_id}/status")
async def update_agent_status(
    agent_id: str,
    status_update: AgentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update agent status (admin only)."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent = registered_agents[agent_id]
    agent["status"] = status_update.status
    agent["updatedAt"] = datetime.now(timezone.utc).isoformat()

    return AgentResponse(success=True, data=agent)


@router.post("/{agent_id}/assign")
async def assign_task_to_agent(
    agent_id: str,
    task: AgentTaskAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Assign a task to an agent (admin only)."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent = registered_agents[agent_id]

    if agent["status"] != "online":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent is not available for task assignment",
        )

    # Store task
    task_data = {
        "taskId": task.task_id,
        "taskType": task.task_type,
        "payload": task.payload,
        "assignedAt": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }

    agent_tasks[agent_id] = task_data
    agent["status"] = "busy"
    agent["currentTask"] = task.task_id
    agent["updatedAt"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Task assigned successfully",
        "data": {"agentId": agent_id, "task": task_data},
    }


@router.post("/{agent_id}/task-complete")
async def complete_agent_task(
    agent_id: str,
    result: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark agent task as completed."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent = registered_agents[agent_id]

    # Update task
    if agent_id in agent_tasks:
        task = agent_tasks[agent_id]
        task["status"] = "completed"
        task["completedAt"] = datetime.now(timezone.utc).isoformat()
        task["result"] = result

    # Update agent
    agent["status"] = "online"
    agent["currentTask"] = None
    agent["tasksCompleted"] += 1
    agent["updatedAt"] = datetime.now(timezone.utc).isoformat()

    # Remove task
    if agent_id in agent_tasks:
        del agent_tasks[agent_id]

    return {
        "success": True,
        "message": "Task completed successfully",
        "data": {
            "agentId": agent_id,
            "tasksCompleted": agent["tasksCompleted"],
        },
    }


@router.post("/{agent_id}/task-fail")
async def fail_agent_task(
    agent_id: str,
    error: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark agent task as failed."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent = registered_agents[agent_id]

    # Update task
    if agent_id in agent_tasks:
        task = agent_tasks[agent_id]
        task["status"] = "failed"
        task["failedAt"] = datetime.now(timezone.utc).isoformat()
        task["error"] = error

    # Update agent
    agent["status"] = "online"
    agent["currentTask"] = None
    agent["tasksFailed"] += 1
    agent["updatedAt"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Task failure recorded",
        "data": {"agentId": agent_id, "tasksFailed": agent["tasksFailed"]},
    }


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Unregister an agent (admin only)."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Remove agent
    del registered_agents[agent_id]

    # Remove any pending tasks
    if agent_id in agent_tasks:
        del agent_tasks[agent_id]

    return None


@router.get("/{agent_id}/tasks")
async def get_agent_tasks(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get task history for an agent."""
    if agent_id not in registered_agents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Get current task
    current_task = agent_tasks.get(agent_id)

    return {
        "success": True,
        "data": {
            "currentTask": current_task,
            "tasksCompleted": registered_agents[agent_id].get("tasksCompleted", 0),
            "tasksFailed": registered_agents[agent_id].get("tasksFailed", 0),
        },
    }
