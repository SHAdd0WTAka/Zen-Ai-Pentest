"""Multi-Agent Coordinator with Deadlock Prevention

Prevents deadlocks in multi-agent systems using resource ordering and timeouts.
Addresses Issue #13
"""
import asyncio
import time
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import logging


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class ResourceType(Enum):
    SCANNER = "scanner"
    DATABASE = "database"
    API_RATE_LIMIT = "api_rate_limit"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"


@dataclass
class Agent:
    """Agent representation"""
    id: str
    name: str
    status: AgentStatus = AgentStatus.IDLE
    acquired_resources: Set[ResourceType] = field(default_factory=set)
    waiting_for: Optional[ResourceType] = None
    start_time: float = field(default_factory=time.time)
    timeout: float = 300.0  # 5 minutes default


@dataclass
class Resource:
    """Resource representation"""
    type: ResourceType
    max_concurrent: int = 1
    current_users: Set[str] = field(default_factory=set)
    wait_queue: List[str] = field(default_factory=list)


class AgentCoordinator:
    """Coordinates multiple agents with deadlock prevention"""

    name = "agent_coordinator"
    version = "1.0.0"

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.resources: Dict[ResourceType, Resource] = {}
        self._lock = asyncio.Lock()
        self._init_resources()
        self.deadlock_check_interval = 10.0

    def _init_resources(self):
        """Initialize system resources"""
        self.resources = {
            ResourceType.SCANNER: Resource(ResourceType.SCANNER, max_concurrent=3),
            ResourceType.DATABASE: Resource(ResourceType.DATABASE, max_concurrent=5),
            ResourceType.API_RATE_LIMIT: Resource(ResourceType.API_RATE_LIMIT, max_concurrent=2),
            ResourceType.FILE_SYSTEM: Resource(ResourceType.FILE_SYSTEM, max_concurrent=10),
            ResourceType.NETWORK: Resource(ResourceType.NETWORK, max_concurrent=5),
        }

    async def register_agent(self, agent_id: str, name: str, timeout: float = 300.0) -> Agent:
        """Register a new agent"""
        async with self._lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already registered")
            
            agent = Agent(id=agent_id, name=name, timeout=timeout)
            self.agents[agent_id] = agent
            return agent

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent and release its resources"""
        async with self._lock:
            if agent_id not in self.agents:
                return
            
            agent = self.agents[agent_id]
            
            # Release all acquired resources
            for resource_type in list(agent.acquired_resources):
                await self._release_resource(agent_id, resource_type)
            
            del self.agents[agent_id]

    async def _acquire_resource(
        self,
        agent_id: str,
        resource_type: ResourceType,
        timeout: float = 30.0
    ) -> bool:
        """Acquire a resource with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with self._lock:
                if agent_id not in self.agents:
                    return False
                
                resource = self.resources[resource_type]
                agent = self.agents[agent_id]
                
                # Check if resource available
                if len(resource.current_users) < resource.max_concurrent:
                    resource.current_users.add(agent_id)
                    agent.acquired_resources.add(resource_type)
                    agent.waiting_for = None
                    return True
                
                # Add to wait queue
                if agent_id not in resource.wait_queue:
                    resource.wait_queue.append(agent_id)
                    agent.waiting_for = resource_type
                    agent.status = AgentStatus.WAITING
            
            # Wait and retry
            await asyncio.sleep(0.5)
        
        return False

    async def _release_resource(self, agent_id: str, resource_type: ResourceType):
        """Release an acquired resource"""
        resource = self.resources[resource_type]
        
        if agent_id in resource.current_users:
            resource.current_users.remove(agent_id)
        
        if agent_id in resource.wait_queue:
            resource.wait_queue.remove(agent_id)
        
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.acquired_resources.discard(resource_type)

    @asynccontextmanager
    async def acquire_resources(
        self,
        agent_id: str,
        resources: List[ResourceType],
        timeout: float = 30.0
    ):
        """
        Context manager for acquiring multiple resources
        Uses resource ordering to prevent deadlocks
        """
        # Sort resources to ensure consistent ordering (prevents circular wait)
        sorted_resources = sorted(resources, key=lambda r: r.value)
        
        acquired = []
        try:
            # Acquire all resources in order
            for resource_type in sorted_resources:
                success = await self._acquire_resource(agent_id, resource_type, timeout)
                if not success:
                    raise TimeoutError(f"Could not acquire {resource_type.value}")
                acquired.append(resource_type)
            
            yield acquired
        finally:
            # Release in reverse order
            for resource_type in reversed(acquired):
                await self._release_resource(agent_id, resource_type)

    async def check_deadlocks(self) -> List[Dict]:
        """Detect potential deadlocks in the system"""
        async with self._lock:
            deadlocks = []
            
            for agent_id, agent in self.agents.items():
                # Check for timeout
                if agent.status == AgentStatus.WAITING:
                    wait_time = time.time() - agent.start_time
                    if wait_time > agent.timeout:
                        deadlocks.append({
                            'agent_id': agent_id,
                            'type': 'timeout',
                            'wait_time': wait_time,
                            'waiting_for': agent.waiting_for.value if agent.waiting_for else None
                        })
                
                # Check for circular wait (simplified)
                if agent.waiting_for:
                    resource = self.resources[agent.waiting_for]
                    for other_id in resource.current_users:
                        if other_id in self.agents:
                            other = self.agents[other_id]
                            if other.waiting_for in agent.acquired_resources:
                                deadlocks.append({
                                    'agent_id': agent_id,
                                    'type': 'circular_wait',
                                    'involved': [agent_id, other_id],
                                    'resources': [agent.waiting_for.value, other.waiting_for.value if other.waiting_for else None]
                                })
            
            return deadlocks

    async def resolve_deadlock(self, agent_id: str):
        """Forcefully resolve a deadlock by killing an agent"""
        async with self._lock:
            if agent_id not in self.agents:
                return
            
            agent = self.agents[agent_id]
            
            # Release all resources
            for resource_type in list(agent.acquired_resources):
                await self._release_resource(agent_id, resource_type)
            
            agent.status = AgentStatus.ERROR
            logging.warning(f"Deadlock resolved: Agent {agent_id} terminated")

    def get_status(self) -> Dict:
        """Get coordinator status"""
        return {
            'agents': {
                aid: {
                    'name': a.name,
                    'status': a.status.value,
                    'resources': [r.value for r in a.acquired_resources],
                    'waiting_for': a.waiting_for.value if a.waiting_for else None
                }
                for aid, a in self.agents.items()
            },
            'resources': {
                rt.value: {
                    'max': r.max_concurrent,
                    'current': len(r.current_users),
                    'queue': len(r.wait_queue)
                }
                for rt, r in self.resources.items()
            }
        }

    def get_info(self) -> Dict:
        """Get module info"""
        return {
            'name': self.name,
            'version': self.version,
            'description': 'Multi-agent coordinator with deadlock prevention',
            'resources': [r.value for r in ResourceType],
            'deadlock_prevention': ['resource_ordering', 'timeout_detection', 'circular_wait_detection']
        }
