"""
Agent Registry for gRPC Agent Communication v2.

Manages agent registration, status tracking, and session management.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""
    UNKNOWN = "unknown"
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentIdentity:
    """Agent identity information."""
    agent_id: str
    session_id: str
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)


@dataclass
class AgentSession:
    """Agent session information."""
    agent_id: str
    session_token: str
    status: AgentStatus = AgentStatus.ONLINE
    last_heartbeat: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0


class AgentRegistry:
    """Thread-safe agent registry.
    
    Manages agent registrations, sessions, and status tracking.
    Supports 100+ concurrent agents with efficient lookups.
    """
    
    def __init__(self, heartbeat_timeout: float = 60.0):
        """Initialize the agent registry.
        
        Args:
            heartbeat_timeout: Seconds after which an agent is considered offline
        """
        self._agents: Dict[str, AgentIdentity] = {}
        self._sessions: Dict[str, AgentSession] = {}
        self._lock = threading.RLock()
        self._heartbeat_timeout = heartbeat_timeout
        
    def register(
        self,
        identity: AgentIdentity,
        session_token: str
    ) -> bool:
        """Register a new agent.
        
        Args:
            identity: Agent identity information
            session_token: Session token for authentication
            
        Returns:
            True if registration successful, False otherwise
        """
        with self._lock:
            if identity.agent_id in self._agents:
                logger.warning(f"Agent {identity.agent_id} already registered")
                return False
            
            self._agents[identity.agent_id] = identity
            self._sessions[identity.agent_id] = AgentSession(
                agent_id=identity.agent_id,
                session_token=session_token,
                status=AgentStatus.ONLINE,
                last_heartbeat=time.time()
            )
            logger.info(f"Agent {identity.agent_id} registered")
            return True
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if unregistration successful, False if agent not found
        """
        with self._lock:
            if agent_id not in self._agents:
                logger.warning(f"Agent {agent_id} not found for unregistration")
                return False
            
            del self._agents[agent_id]
            del self._sessions[agent_id]
            logger.info(f"Agent {agent_id} unregistered")
            return True
    
    def get(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent identity by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentIdentity if found, None otherwise
        """
        with self._lock:
            return self._agents.get(agent_id)
    
    def get_session(self, agent_id: str) -> Optional[AgentSession]:
        """Get agent session by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentSession if found, None otherwise
        """
        with self._lock:
            return self._sessions.get(agent_id)
    
    def list_all(self) -> List[AgentIdentity]:
        """List all registered agents.
        
        Returns:
            List of all agent identities
        """
        with self._lock:
            return list(self._agents.values())
    
    def list_online(self) -> List[AgentIdentity]:
        """List all online agents.
        
        Returns:
            List of online agent identities
        """
        with self._lock:
            return [
                self._agents[agent_id]
                for agent_id, session in self._sessions.items()
                if session.status == AgentStatus.ONLINE
                and agent_id in self._agents
            ]
    
    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status.
        
        Args:
            agent_id: Agent ID
            status: New status
            
        Returns:
            True if update successful, False if agent not found
        """
        with self._lock:
            if agent_id not in self._sessions:
                return False
            
            self._sessions[agent_id].status = status
            self._sessions[agent_id].last_heartbeat = time.time()
            logger.debug(f"Agent {agent_id} status updated to {status.value}")
            return True
    
    def update_heartbeat(
        self,
        agent_id: str,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
        active_tasks: int = 0
    ) -> bool:
        """Update agent heartbeat.
        
        Args:
            agent_id: Agent ID
            cpu_usage: Current CPU usage (0-100)
            memory_usage: Current memory usage (0-100)
            active_tasks: Number of active tasks
            
        Returns:
            True if update successful, False if agent not found
        """
        with self._lock:
            if agent_id not in self._sessions:
                return False
            
            session = self._sessions[agent_id]
            session.last_heartbeat = time.time()
            session.cpu_usage = cpu_usage
            session.memory_usage = memory_usage
            session.active_tasks = active_tasks
            
            # Auto-update status to ONLINE if it was OFFLINE
            if session.status == AgentStatus.OFFLINE:
                session.status = AgentStatus.ONLINE
                
            return True
    
    def get_status(self, agent_id: str) -> AgentStatus:
        """Get agent status.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent status (UNKNOWN if agent not found)
        """
        with self._lock:
            session = self._sessions.get(agent_id)
            if session is None:
                return AgentStatus.UNKNOWN
            return session.status
    
    def verify_session(self, agent_id: str, session_token: str) -> bool:
        """Verify agent session token.
        
        Args:
            agent_id: Agent ID
            session_token: Session token to verify
            
        Returns:
            True if session is valid, False otherwise
        """
        with self._lock:
            session = self._sessions.get(agent_id)
            if session is None:
                return False
            return session.session_token == session_token
    
    def cleanup_stale_agents(self) -> int:
        """Remove agents that haven't sent heartbeat within timeout.
        
        Returns:
            Number of agents removed
        """
        with self._lock:
            current_time = time.time()
            stale_agents = [
                agent_id
                for agent_id, session in self._sessions.items()
                if current_time - session.last_heartbeat > self._heartbeat_timeout
            ]
            
            for agent_id in stale_agents:
                self._sessions[agent_id].status = AgentStatus.OFFLINE
                logger.info(f"Agent {agent_id} marked as offline (stale heartbeat)")
            
            return len(stale_agents)
    
    def get_agent_count(self) -> int:
        """Get total number of registered agents.
        
        Returns:
            Number of agents
        """
        with self._lock:
            return len(self._agents)
    
    def get_online_count(self) -> int:
        """Get number of online agents.
        
        Returns:
            Number of online agents
        """
        with self._lock:
            return sum(
                1 for session in self._sessions.values()
                if session.status == AgentStatus.ONLINE
            )
    
    def get_capabilities(self, agent_id: str) -> Set[str]:
        """Get agent capabilities.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Set of capabilities (empty if agent not found)
        """
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent is None:
                return set()
            return set(agent.capabilities)
    
    def find_by_capability(self, capability: str) -> List[AgentIdentity]:
        """Find agents with specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agents with the capability
        """
        with self._lock:
            return [
                agent for agent in self._agents.values()
                if capability in agent.capabilities
            ]
