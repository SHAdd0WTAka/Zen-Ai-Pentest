"""
Workflow API Routes
===================

REST API endpoints for managing multi-agent pentest workflows.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from agents.workflows import WorkflowOrchestrator

logger = logging.getLogger("api.workflows")
router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])


def get_orchestrator():
    """Get workflow orchestrator instance"""
    from agents.workflows.orchestrator import get_workflow_orchestrator

    return get_workflow_orchestrator()


# Simple auth dependency
def get_current_user():
    return {"sub": "admin", "role": "admin"}


@router.get("/types")
async def list_workflow_types(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator), user: dict = Depends(get_current_user)
):
    """
    List available workflow types.

    Returns all predefined workflow templates.
    """
    types = orchestrator.get_available_workflow_types()

    return {
        "types": [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "steps": value["steps"],
            }
            for key, value in types.items()
        ]
    }


@router.post("/")
async def create_workflow(
    request: dict, orchestrator: WorkflowOrchestrator = Depends(get_orchestrator), user: dict = Depends(get_current_user)
):
    """
    Start a new workflow.

    Request:
    {
        "type": "network_recon",
        "target": "192.168.1.0/24",
        "agents": ["agent-1", "agent-2"],
        "parameters": {"ports": "top1000"}
    }
    """
    workflow_type = request.get("type")
    target = request.get("target")
    agents = request.get("agents", [])
    parameters = request.get("parameters", {})

    if not workflow_type or not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow type and target are required")

    if not agents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one agent is required")

    try:
        workflow_id = await orchestrator.start_workflow(
            workflow_type=workflow_type, target=target, agents=agents, parameters=parameters
        )

        return {"workflow_id": workflow_id, "status": "pending", "message": "Workflow started successfully"}

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start workflow")


@router.get("/")
async def list_workflows(
    status: Optional[str] = None,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
    user: dict = Depends(get_current_user),
):
    """List workflows."""
    workflows = orchestrator.list_workflows(state=status)

    return {"workflows": workflows, "count": len(workflows)}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str, orchestrator: WorkflowOrchestrator = Depends(get_orchestrator), user: dict = Depends(get_current_user)
):
    """Get workflow status and details."""
    workflow_status = orchestrator.get_workflow_status(workflow_id)

    if not workflow_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found")

    return workflow_status


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str, orchestrator: WorkflowOrchestrator = Depends(get_orchestrator), user: dict = Depends(get_current_user)
):
    """Cancel a running workflow."""
    success = await orchestrator.cancel_workflow(workflow_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Workflow {workflow_id} not found or not running")

    return {"workflow_id": workflow_id, "status": "cancelled", "message": "Workflow cancelled successfully"}


@router.get("/{workflow_id}/findings")
async def get_workflow_findings(
    workflow_id: str, orchestrator: WorkflowOrchestrator = Depends(get_orchestrator), user: dict = Depends(get_current_user)
):
    """Get findings from a workflow."""
    workflow_status = orchestrator.get_workflow_status(workflow_id)

    if not workflow_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found")

    # Get full workflow object to access findings
    orch = get_orchestrator()

    if workflow_id in orch.workflows:
        workflow = orch.workflows[workflow_id]
        return {"workflow_id": workflow_id, "findings": workflow.findings, "count": len(workflow.findings)}

    return {"workflow_id": workflow_id, "findings": [], "count": 0}


@router.post("/{workflow_id}/tasks/{task_id}/result")
async def submit_task_result(
    workflow_id: str,
    task_id: str,
    result: dict,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
    user: dict = Depends(get_current_user),
):
    """Submit task result (for agent use)."""
    await orchestrator.submit_task_result(task_id, result)

    return {"task_id": task_id, "status": "received", "message": "Task result submitted"}
