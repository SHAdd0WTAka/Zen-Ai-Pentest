"""
Agent Communication Protocol (ACP) v1.1
Pydantic Models for structured inter-agent messaging
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageType:
    """Message types for ACP v1.1"""

    REASON = "reason"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"
    DELEGATE = "delegate"
    DELEGATE_TASK = "delegate_task"  # v1.1
    ERROR = "error"
    COMPLETE = "complete"
    STATUS_UPDATE = "status_update"  # v1.1
    CANCEL = "cancel"  # v1.1


class PriorityLevel:
    """Priority levels (0=CRITICAL, 4=BACKGROUND)"""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class MessageContent(BaseModel):
    """Flexible content block - fields vary by message type"""

    model_config = ConfigDict(extra="allow")

    reasoning: Optional[str] = None
    action: Optional[str] = None  # Tool name for 'act'
    parameters: Optional[Dict[str, Any]] = None  # Tool parameters
    observation: Optional[str] = None
    result: Optional[Dict[str, Any]] = None  # Structured result
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    evidence: Optional[List[str]] = None
    error_message: Optional[str] = None
    task_description: Optional[str] = None  # For delegate_task
    assignee: Optional[Union[str, List[str]]] = None
    due_in_seconds: Optional[int] = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class MessageContext(BaseModel):
    """Context information for the message"""

    target: str
    session_id: str
    scan_id: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    safety_level: Literal["non_destructive", "low_risk", "medium_risk", "high_risk", "manual"] = "non_destructive"
    environment: Optional[Dict[str, Any]] = None  # e.g., {"vm_id": "vm-kali-01"}


class AgentMessage(BaseModel):
    """
    Main message model - Agent Communication Protocol v1.1

    Example:
        {
            "message_id": "msg_k7p9m4x2",
            "version": "1.1",
            "timestamp": "2026-02-13T14:42:19.337Z",
            "agent_id": "analysis-bot-4",
            "session_id": "scan_xyz789",
            "type": "delegate_task",
            "priority": 1,
            "content": {
                "task_description": "Perform deep enumeration...",
                "assignee": "recon-bot-2",
                "due_in_seconds": 1800
            },
            "targets": ["orchestrator"],
            "context": {
                "target": "api.target.com",
                "session_id": "scan_xyz789",
                "safety_level": "medium_risk"
            }
        }
    """

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(..., pattern=r"^msg_[a-z0-9_]{8,30}$")
    version: Literal["1.1"] = "1.1"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str
    session_id: str
    type: str = Field(
        ...,
        description="Message type: reason, act, observe, reflect, delegate, delegate_task, error, complete, status_update, cancel",
    )
    priority: int = Field(default=PriorityLevel.NORMAL, ge=0, le=4)
    content: MessageContent
    targets: List[str] = Field(..., min_length=1)
    context: MessageContext
    correlation_id: Optional[str] = None  # For request-response pairs
    ttl_seconds: Optional[int] = Field(default=3600, ge=0)  # Time-to-live

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: List[str]):
        if not v:
            raise ValueError("At least one target required")
        return v

    @field_validator("content")
    @classmethod
    def validate_content_by_type(cls, v: MessageContent, info):
        values = info.data
        msg_type = values.get("type")

        if msg_type == MessageType.ACT and not v.action:
            raise ValueError("'act' messages must have 'action' field")

        if msg_type in (MessageType.OBSERVE, MessageType.REFLECT) and not v.observation:
            raise ValueError(f"'{msg_type}' messages should contain 'observation'")

        if msg_type == MessageType.DELEGATE_TASK and not v.task_description:
            raise ValueError("'delegate_task' requires 'task_description'")

        if msg_type == MessageType.ERROR and not v.error_message:
            raise ValueError("'error' messages should contain 'error_message'")

        return v

    def is_high_priority(self) -> bool:
        """Check if message is high priority (0 or 1)"""
        return self.priority <= PriorityLevel.HIGH

    def is_expired(self) -> bool:
        """Check if message TTL has expired"""
        if not self.ttl_seconds:
            return False
        from datetime import timedelta

        expiry = self.timestamp + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry


class MessageResponse(BaseModel):
    """Standard response wrapper for message operations"""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Pre-defined message templates for common operations
class MessageTemplates:
    """Templates for common message types"""

    @staticmethod
    def create_delegate_task(
        agent_id: str,
        session_id: str,
        task_description: str,
        assignee: Union[str, List[str]],
        target: str,
        priority: int = PriorityLevel.NORMAL,
        due_in_seconds: int = 1800,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AgentMessage:
        """Create a delegate_task message"""
        return AgentMessage(
            message_id=f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{agent_id[:4]}",
            agent_id=agent_id,
            session_id=session_id,
            type=MessageType.DELEGATE_TASK,
            priority=priority,
            content=MessageContent(
                task_description=task_description,
                assignee=assignee,
                due_in_seconds=due_in_seconds,
                parameters=parameters or {},
            ),
            targets=[assignee] if isinstance(assignee, str) else assignee,
            context=MessageContext(target=target, session_id=session_id, safety_level="medium_risk"),
        )

    @staticmethod
    def create_status_update(agent_id: str, session_id: str, status: str, progress_percent: int, target: str) -> AgentMessage:
        """Create a status_update message"""
        return AgentMessage(
            message_id=f"msg_status_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            agent_id=agent_id,
            session_id=session_id,
            type=MessageType.STATUS_UPDATE,
            priority=PriorityLevel.NORMAL,
            content=MessageContent(observation=status, result={"progress": progress_percent}),
            targets=["orchestrator"],
            context=MessageContext(target=target, session_id=session_id, safety_level="non_destructive"),
        )
