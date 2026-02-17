"""
Workflow Orchestrator
=====================

Manages multi-agent pentest workflows with state machine.

State Machine:
    PENDING → RUNNING → [STEP_1 → STEP_2 → ...] → COMPLETED
                ↓
            PAUSED/FAILED

Usage:
    orchestrator = WorkflowOrchestrator()
    workflow_id = await orchestrator.start_workflow(
        workflow_type="network_recon",
        target="192.168.1.0/24",
        agents=["agent-1", "agent-2"]
    )
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set


logger = logging.getLogger("zen.agents.workflow")


class WorkflowState(Enum):
    """Workflow execution states"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(Enum):
    """Standard pentest workflow steps"""
    RECONNAISSANCE = "reconnaissance"
    SCANNING = "scanning"
    ENUMERATION = "enumeration"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"


@dataclass
class Task:
    """Task assigned to an agent"""
    id: str
    workflow_id: str
    step: str
    agent_id: Optional[str]
    target: str
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Optional[Dict] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Workflow:
    """Workflow instance"""
    id: str
    type: str
    target: str
    state: WorkflowState
    current_step: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    tasks: Dict[str, Task] = field(default_factory=dict)
    findings: List[Dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "target": self.target,
            "state": self.state.value,
            "current_step": self.current_step,
            "steps": self.steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "agents": self.agents,
            "task_count": len(self.tasks),
            "finding_count": len(self.findings),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


# Workflow Definitions
WORKFLOW_DEFINITIONS = {
    "network_recon": {
        "name": "Network Reconnaissance",
        "description": "Network discovery and mapping",
        "steps": [
            WorkflowStep.RECONNAISSANCE.value,
            WorkflowStep.SCANNING.value,
            WorkflowStep.REPORTING.value,
        ],
    },
    "web_scan": {
        "name": "Web Application Scan",
        "description": "Web application security testing",
        "steps": [
            WorkflowStep.RECONNAISSANCE.value,
            WorkflowStep.ENUMERATION.value,
            WorkflowStep.VULNERABILITY_ANALYSIS.value,
            WorkflowStep.REPORTING.value,
        ],
    },
    "full_pentest": {
        "name": "Full Penetration Test",
        "description": "Complete penetration test workflow",
        "steps": [
            WorkflowStep.RECONNAISSANCE.value,
            WorkflowStep.SCANNING.value,
            WorkflowStep.ENUMERATION.value,
            WorkflowStep.VULNERABILITY_ANALYSIS.value,
            WorkflowStep.EXPLOITATION.value,
            WorkflowStep.POST_EXPLOITATION.value,
            WorkflowStep.REPORTING.value,
        ],
    },
    "targeted_attack": {
        "name": "Targeted Attack",
        "description": "Focused attack on specific target",
        "steps": [
            WorkflowStep.RECONNAISSANCE.value,
            WorkflowStep.VULNERABILITY_ANALYSIS.value,
            WorkflowStep.EXPLOITATION.value,
            WorkflowStep.REPORTING.value,
        ],
    },
}


class WorkflowOrchestrator:
    """
    Orchestrates multi-agent pentest workflows.
    
    Features:
    - State machine for workflow progression
    - Task distribution to agents
    - Result aggregation
    - Error handling and retry logic
    - Progress tracking
    """
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Set[str] = set()
        self.task_callbacks: Dict[str, Callable] = {}
        self.agent_assignments: Dict[str, str] = {}  # agent_id -> workflow_id
        self._running = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._event_handlers: List[Callable] = []
        
        logger.info("✅ WorkflowOrchestrator initialized")
    
    async def start_workflow(
        self,
        workflow_type: str,
        target: str,
        agents: List[str],
        parameters: Optional[Dict] = None
    ) -> str:
        """
        Start a new workflow.
        
        Args:
            workflow_type: Type of workflow (network_recon, web_scan, etc.)
            target: Target to test (IP, URL, range)
            agents: List of agent IDs to use
            parameters: Optional workflow parameters
            
        Returns:
            workflow_id: Unique workflow identifier
        """
        if workflow_type not in WORKFLOW_DEFINITIONS:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        definition = WORKFLOW_DEFINITIONS[workflow_type]
        
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        workflow = Workflow(
            id=workflow_id,
            type=workflow_type,
            target=target,
            state=WorkflowState.PENDING,
            steps=definition["steps"].copy(),
            agents=agents,
            metadata={
                "name": definition["name"],
                "description": definition["description"],
                "parameters": parameters or {},
            }
        )
        
        self.workflows[workflow_id] = workflow
        
        logger.info(f"🚀 Workflow {workflow_id} created ({workflow_type} on {target})")
        
        # Start workflow execution
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        return workflow_id
    
    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow steps"""
        workflow = self.workflows[workflow_id]
        
        try:
            workflow.state = WorkflowState.RUNNING
            workflow.started_at = datetime.utcnow().isoformat()
            self.active_workflows.add(workflow_id)
            
            await self._emit_event("workflow_started", workflow.to_dict())
            
            # Execute each step
            for step in workflow.steps:
                if workflow.state == WorkflowState.CANCELLED:
                    logger.info(f"🛑 Workflow {workflow_id} cancelled")
                    break
                
                workflow.current_step = step
                logger.info(f"▶️  Workflow {workflow_id}: Starting step '{step}'")
                
                success = await self._execute_step(workflow_id, step)
                
                if success:
                    workflow.completed_steps.append(step)
                    await self._emit_event("step_completed", {
                        "workflow_id": workflow_id,
                        "step": step,
                    })
                else:
                    workflow.failed_steps.append(step)
                    logger.error(f"❌ Workflow {workflow_id}: Step '{step}' failed")
                    
                    # Continue or fail based on step criticality
                    if step in [WorkflowStep.REPORTING.value]:
                        break
            
            # Determine final state
            if workflow.state == WorkflowState.CANCELLED:
                pass  # Already set
            elif len(workflow.failed_steps) == 0:
                workflow.state = WorkflowState.COMPLETED
                logger.info(f"✅ Workflow {workflow_id} completed successfully")
            elif len(workflow.completed_steps) > 0:
                workflow.state = WorkflowState.COMPLETED  # Partial completion
                logger.info(f"⚠️  Workflow {workflow_id} completed with {len(workflow.failed_steps)} failed steps")
            else:
                workflow.state = WorkflowState.FAILED
                logger.error(f"❌ Workflow {workflow_id} failed")
            
            workflow.completed_at = datetime.utcnow().isoformat()
            self.active_workflows.discard(workflow_id)
            
            await self._emit_event("workflow_completed", workflow.to_dict())
            
        except Exception as e:
            logger.exception(f"💥 Workflow {workflow_id} crashed: {e}")
            workflow.state = WorkflowState.FAILED
            workflow.completed_at = datetime.utcnow().isoformat()
            self.active_workflows.discard(workflow_id)
            
            await self._emit_event("workflow_failed", {
                "workflow_id": workflow_id,
                "error": str(e),
            })
    
    async def _execute_step(self, workflow_id: str, step: str) -> bool:
        """Execute a single workflow step"""
        workflow = self.workflows[workflow_id]
        
        try:
            # Create tasks for this step
            tasks = self._create_step_tasks(workflow_id, step)
            
            if not tasks:
                logger.warning(f"⚠️  No tasks created for step '{step}'")
                return True
            
            # Distribute tasks to agents
            await self._distribute_tasks(workflow_id, tasks)
            
            # Wait for all tasks to complete
            timeout = 300  # 5 minutes per step
            completed = await self._wait_for_tasks(workflow_id, tasks, timeout)
            
            return completed
            
        except Exception as e:
            logger.exception(f"❌ Step '{step}' execution failed: {e}")
            return False
    
    def _create_step_tasks(self, workflow_id: str, step: str) -> List[Task]:
        """Create tasks for a workflow step"""
        workflow = self.workflows[workflow_id]
        tasks = []
        
        # Task definitions per step
        task_definitions = {
            WorkflowStep.RECONNAISSANCE.value: [
                {"tool": "whois", "description": "WHOIS lookup"},
                {"tool": "dns", "description": "DNS enumeration"},
                {"tool": "subdomain", "description": "Subdomain discovery"},
            ],
            WorkflowStep.SCANNING.value: [
                {"tool": "nmap", "description": "Port scanning"},
                {"tool": "service", "description": "Service detection"},
            ],
            WorkflowStep.ENUMERATION.value: [
                {"tool": "web_enum", "description": "Web enumeration"},
                {"tool": "directory", "description": "Directory brute force"},
            ],
            WorkflowStep.VULNERABILITY_ANALYSIS.value: [
                {"tool": "nuclei", "description": "Vulnerability scanning"},
            ],
            WorkflowStep.EXPLOITATION.value: [
                {"tool": "exploit", "description": "Exploit attempt"},
            ],
            WorkflowStep.POST_EXPLOITATION.value: [
                {"tool": "pivot", "description": "Network pivoting"},
            ],
            WorkflowStep.REPORTING.value: [
                {"tool": "report", "description": "Generate report"},
            ],
        }
        
        definitions = task_definitions.get(step, [])
        
        for i, definition in enumerate(definitions):
            task_id = f"task_{workflow_id}_{step}_{i}"
            task = Task(
                id=task_id,
                workflow_id=workflow_id,
                step=step,
                agent_id=None,  # Not assigned yet
                target=workflow.target,
                parameters={
                    **definition,
                    "workflow_type": workflow.type,
                }
            )
            tasks.append(task)
            workflow.tasks[task_id] = task
        
        return tasks
    
    async def _distribute_tasks(self, workflow_id: str, tasks: List[Task]):
        """Distribute tasks to available agents via WebSocket"""
        workflow = self.workflows[workflow_id]
        agents = workflow.agents.copy()
        
        # Import agent connection manager
        try:
            # Import from main API module
            import sys
            sys.path.insert(0, '/mnt/c/Users/Ataka/zen-ai-pentest')
            from api.main import agent_connection_manager
            
            # Round-robin assignment
            for i, task in enumerate(tasks):
                agent_id = agents[i % len(agents)]
                task.agent_id = agent_id
                task.status = "assigned"
                
                # Check if agent is connected
                if agent_connection_manager.is_agent_connected(agent_id):
                    # Send task via WebSocket
                    success = await agent_connection_manager.send_task(
                        agent_id, 
                        task.to_dict()
                    )
                    
                    if success:
                        logger.info(f"📤 Task {task.id} sent to agent {agent_id}")
                        task.status = "sent"
                    else:
                        logger.error(f"❌ Failed to send task {task.id} to agent {agent_id}")
                        task.status = "failed"
                else:
                    logger.warning(f"⚠️  Agent {agent_id} not connected, task {task.id} queued")
                    task.status = "queued"
                
                # Also put in queue for tracking
                await self._task_queue.put(task)
                
        except Exception as e:
            logger.error(f"Failed to distribute tasks: {e}")
            # Fallback: just queue tasks
            for task in tasks:
                task.status = "pending"
                await self._task_queue.put(task)
    
    async def _wait_for_tasks(self, workflow_id: str, tasks: List[Task], timeout: int) -> bool:
        """Wait for all tasks to complete"""
        task_ids = {t.id for t in tasks}
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if all tasks completed
            completed = sum(1 for t in tasks if t.status in ["completed", "failed"])
            
            if completed == len(tasks):
                # All done
                failed = sum(1 for t in tasks if t.status == "failed")
                return failed == 0  # Success if none failed
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning(f"⏱️  Step timeout after {timeout}s")
                # Mark pending tasks as failed
                for t in tasks:
                    if t.status not in ["completed", "failed"]:
                        t.status = "failed"
                        t.result = {"error": "Timeout"}
                return False
            
            await asyncio.sleep(1)
    
    async def submit_task_result(self, task_id: str, result: Dict):
        """Submit result from agent"""
        # Find task
        for workflow in self.workflows.values():
            if task_id in workflow.tasks:
                task = workflow.tasks[task_id]
                task.result = result
                task.status = "completed" if not result.get("error") else "failed"
                task.completed_at = datetime.utcnow().isoformat()
                
                # Add findings
                if "findings" in result:
                    workflow.findings.extend(result["findings"])
                
                logger.info(f"✅ Task {task_id} completed")
                
                await self._emit_event("task_completed", {
                    "workflow_id": workflow.id,
                    "task_id": task_id,
                    "status": task.status,
                })
                return
        
        logger.warning(f"⚠️  Task {task_id} not found")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            return None
        
        return self.workflows[workflow_id].to_dict()
    
    def list_workflows(self, state: Optional[str] = None) -> List[Dict]:
        """List workflows, optionally filtered by state"""
        workflows = self.workflows.values()
        
        if state:
            workflows = [w for w in workflows if w.state.value == state]
        
        return [w.to_dict() for w in workflows]
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        if workflow.state not in [WorkflowState.RUNNING, WorkflowState.PENDING]:
            return False
        
        workflow.state = WorkflowState.CANCELLED
        logger.info(f"🛑 Workflow {workflow_id} cancelled")
        
        await self._emit_event("workflow_cancelled", workflow.to_dict())
        return True
    
    def on_event(self, handler: Callable):
        """Register event handler"""
        self._event_handlers.append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict):
        """Emit event to all handlers"""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        
        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_available_workflow_types(self) -> Dict[str, Dict]:
        """Get available workflow types"""
        return WORKFLOW_DEFINITIONS.copy()


# Global instance
_orchestrator: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
    return _orchestrator
