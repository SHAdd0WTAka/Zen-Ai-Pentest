#!/usr/bin/env python3
"""
Base Agent Class for Multi-Agent System
Provides messaging, context sharing, and role-based capabilities
Author: SHAdd0WTAka
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("ZenAI.Agents")


class AgentRole(Enum):
    """Agent roles for specialization"""

    RESEARCHER = "researcher"  # Gathers information, reconnaissance
    ANALYST = "analyst"  # Analyzes data, finds patterns
    EXPLOIT = "exploit"  # Develops exploits, payloads
    COORDINATOR = "coordinator"  # Manages workflow between agents
    REPORTER = "reporter"  # Generates reports, summaries
    POST_EXPLOITATION = (
        "post_exploit"  # Post-scan workflow: verification, evidence, cleanup
    )


class AgentState(Enum):
    """Operational states for agents"""

    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"



@dataclass
class AgentMessage:
    """Message format for inter-agent communication"""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str = ""
    recipient: str = ""  # "all" for broadcast, specific ID for direct
    msg_type: str = "chat"  # chat, task, result, request, response
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    requires_response: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.msg_type,
            "content": self.content,
            "context": self.context,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "requires_response": self.requires_response,
        }


class BaseAgent(ABC):
    """
    Base class for all agents in the system
    Provides messaging, context management, and coordination capabilities
    """

    def __init__(self, name: str, role: AgentRole, orchestrator=None):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.role = role
        self.orchestrator = orchestrator
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.inbox: List[AgentMessage] = []
        self.context: Dict[str, Any] = {}  # Shared workspace
        self.memory: List[Dict] = []  # Agent's memory of interactions
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.task: Optional[asyncio.Task] = None

        logger.info(f"[Agent] Initialized {self.name} ({self.role.value}) [{self.id}]")

    def register_handler(self, msg_type: str, handler: Callable):
        """Register a handler for specific message types"""
        self.handlers[msg_type] = handler

    async def send_message(
        self,
        content: str,
        recipient: str = "all",
        msg_type: str = "chat",
        priority: int = 1,
        requires_response: bool = False,
        context: Dict = None,
    ) -> str:
        """
        Send a message to another agent or broadcast
        Returns message ID for tracking
        """
        msg = AgentMessage(
            sender=f"{self.name}[{self.id}]",
            recipient=recipient,
            msg_type=msg_type,
            content=content,
            priority=priority,
            requires_response=requires_response,
            context=context or {},
        )

        if self.orchestrator:
            await self.orchestrator.route_message(msg)
            logger.debug(f"[Agent:{self.name}] Sent {msg_type} to {recipient}")
        else:
            # Direct send if no orchestrator
            await self.message_queue.put(msg)

        return msg.id

    async def receive_message(self, msg: AgentMessage):
        """Receive a message into the queue"""
        await self.message_queue.put(msg)
        self.inbox.append(msg)

        # Store in memory
        self.memory.append(
            {"type": "received", "message": msg.to_dict(), "processed": False}
        )

        logger.debug(f"[Agent:{self.name}] Received message from {msg.sender}")

    async def process_messages(self):
        """Main message processing loop"""
        self.running = True

        while self.running:
            try:
                # Get message with timeout to allow checking running flag
                msg = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)

                # Process based on type
                if msg.msg_type in self.handlers:
                    await self.handlers[msg.msg_type](msg)
                else:
                    await self.handle_message(msg)

                # Mark as processed in memory
                for mem in self.memory:
                    if mem["type"] == "received" and mem["message"]["id"] == msg.id:
                        mem["processed"] = True

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[Agent:{self.name}] Error processing message: {e}")

    async def handle_message(self, msg: AgentMessage):
        """Default message handler - override in subclasses"""
        logger.info(f"[Agent:{self.name}] Handling {msg.msg_type} from {msg.sender}")

        # Default chat response
        if msg.msg_type == "chat":
            response = f"Acknowledged: {msg.content[:50]}..."
            if msg.requires_response:
                await self.send_message(
                    content=response, recipient=msg.sender, msg_type="response"
                )

    def update_context(self, key: str, value: Any, share: bool = False):
        """
        Update agent's local context
        If share=True, broadcast to all agents via orchestrator
        """
        self.context[key] = value

        if share and self.orchestrator:
            asyncio.create_task(
                self.orchestrator.update_shared_context(key, value, self.id)
            )

    def get_context(self, key: str) -> Any:
        """Get value from context"""
        return self.context.get(key)

    def share_findings(self, findings: Dict):
        """Share findings with all agents"""
        if self.orchestrator:
            asyncio.create_task(
                self.send_message(
                    content=f"Sharing {len(findings)} findings",
                    msg_type="findings",
                    context={"findings": findings},
                    priority=2,
                )
            )

    @abstractmethod
    async def execute_task(self, task: Dict) -> Dict:
        """Execute a specific task - must be implemented by subclasses"""
        pass

    async def start(self):
        """Start the agent's message processing loop"""
        self.task = asyncio.create_task(self.process_messages())
        logger.info(f"[Agent:{self.name}] Started")

    async def stop(self):
        """Stop the agent gracefully"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(f"[Agent:{self.name}] Stopped")

    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "running": self.running,
            "queue_size": self.message_queue.qsize(),
            "inbox_count": len(self.inbox),
            "memory_entries": len(self.memory),
            "context_keys": list(self.context.keys()),
        }
