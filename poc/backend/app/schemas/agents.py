"""
Pydantic schemas for agent management
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Agent creation schema"""

    name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., min_length=1, max_length=45)
    version: str = Field(..., min_length=1, max_length=50)
    capabilities: List[str] = Field(default_factory=list)


class AgentMetrics(BaseModel):
    """Agent metrics schema"""

    cpu_usage: float = Field(..., ge=0, le=100)
    memory_usage: float = Field(..., ge=0, le=100)
    disk_usage: float = Field(..., ge=0, le=100)


class AgentStatusUpdate(BaseModel):
    """Agent status update schema"""

    status: str = Field(..., regex="^(online|offline|busy|error)$")


class AgentTaskAssign(BaseModel):
    """Agent task assignment schema"""

    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: str = "normal"


class AgentData(BaseModel):
    """Agent data schema"""

    id: str
    name: str
    hostname: str
    ipAddress: str
    version: str
    status: str
    capabilities: List[str]
    currentTask: Optional[str]
    lastHeartbeat: str
    tasksCompleted: int
    tasksFailed: int
    cpuUsage: float
    memoryUsage: float
    diskUsage: float
    createdAt: str
    updatedAt: str


class AgentResponse(BaseModel):
    """Agent response schema"""

    success: bool
    data: AgentData


class AgentListResponse(BaseModel):
    """Agent list response schema"""

    success: bool
    data: List[AgentData]
    meta: Dict


class AgentTaskData(BaseModel):
    """Agent task data schema"""

    taskId: str
    taskType: str
    payload: Dict[str, Any]
    assignedAt: str
    status: str
    completedAt: Optional[str]
    result: Optional[Dict]
    error: Optional[Dict]
