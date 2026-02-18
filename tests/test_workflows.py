"""
Workflow Tests
==============

Critical tests for multi-agent workflow functionality.

Tests:
1. Workflow Lifecycle - Start to completion
2. Task Distribution - Tasks sent to agents
3. End-to-End - Full workflow with mock agent
"""

import asyncio
from datetime import datetime

import pytest

from agents.v2.agent_task_processor import TaskProcessor, TaskResult
from agents.workflows.orchestrator import WORKFLOW_DEFINITIONS, WorkflowOrchestrator, WorkflowState, WorkflowStep


class TestWorkflowLifecycle:
    """Test 1: Workflow lifecycle from start to completion"""

    @pytest.fixture
    def orchestrator(self):
        """Create fresh orchestrator with short timeout for testing"""
        orch = WorkflowOrchestrator(step_timeout=2)
        # Disable guardrails for workflow tests (we test guardrails separately)
        orch.guardrails_enabled = False
        return orch

    @pytest.mark.asyncio
    async def test_workflow_creation(self, orchestrator):
        """Test workflow creation"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.0/24", agents=["agent-1"]
        )

        assert workflow_id is not None
        assert workflow_id.startswith("wf_")

        # Check workflow exists
        status = orchestrator.get_workflow_status(workflow_id)
        assert status is not None
        assert status["type"] == "network_recon"
        assert status["target"] == "192.168.1.0/24"

    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self, orchestrator):
        """Test workflow state transitions"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.1", agents=["agent-1"]
        )

        # Check workflow was created in valid state
        status = orchestrator.get_workflow_status(workflow_id)
        assert status["state"] in ["pending", "running", "completed", "failed"]

        # Wait for workflow to complete (or fail due to no connected agents)
        for _ in range(20):  # Max 10 seconds
            status = orchestrator.get_workflow_status(workflow_id)
            if status["state"] in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(0.5)

        # Should reach terminal state
        assert status["state"] in ["completed", "failed", "cancelled"]

    @pytest.mark.asyncio
    async def test_workflow_steps_execution(self, orchestrator):
        """Test that workflow steps are executed"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.1", agents=["agent-1"]
        )

        # Wait longer for completion (tasks need time to timeout/fail)
        for _ in range(30):  # Max 15 seconds
            status = orchestrator.get_workflow_status(workflow_id)
            if status["state"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)

        status = orchestrator.get_workflow_status(workflow_id)

        # Should have task definitions for steps
        workflow = orchestrator.workflows[workflow_id]
        assert len(workflow.tasks) > 0  # Tasks were created

        # Steps should have been attempted (may fail due to no agents)
        total_steps = len(status["steps"])
        assert total_steps > 0

    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, orchestrator):
        """Test workflow cancellation"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="full_pentest", target="192.168.1.0/24", agents=["agent-1"]  # Longer workflow
        )

        # Wait for it to start
        await asyncio.sleep(0.2)

        # Cancel it
        success = await orchestrator.cancel_workflow(workflow_id)
        assert success is True

        # Check state
        status = orchestrator.get_workflow_status(workflow_id)
        assert status["state"] == "cancelled"

    def test_workflow_types_available(self):
        """Test that workflow types are defined"""
        types = WORKFLOW_DEFINITIONS

        assert "network_recon" in types
        assert "web_scan" in types
        assert "full_pentest" in types
        assert "targeted_attack" in types

        # Check structure
        for key, definition in types.items():
            assert "name" in definition
            assert "description" in definition
            assert "steps" in definition
            assert len(definition["steps"]) > 0


class TestTaskDistribution:
    """Test 2: Task creation and distribution"""

    @pytest.fixture
    def orchestrator(self):
        orch = WorkflowOrchestrator()
        orch.guardrails_enabled = False
        return orch

    @pytest.mark.asyncio
    async def test_task_creation(self, orchestrator):
        """Test that tasks are created for workflow steps"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.1", agents=["agent-1"]
        )

        # Wait for task creation
        await asyncio.sleep(0.3)

        # Check workflow has tasks
        workflow = orchestrator.workflows.get(workflow_id)
        assert workflow is not None
        assert len(workflow.tasks) > 0

        # Check task structure
        for task_id, task in workflow.tasks.items():
            assert task.workflow_id == workflow_id
            assert task.target == "192.168.1.1"
            assert task.step in ["reconnaissance", "scanning", "reporting"]

    @pytest.mark.asyncio
    async def test_task_assignment(self, orchestrator):
        """Test that tasks are assigned to agents"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.1", agents=["agent-1", "agent-2"]
        )

        await asyncio.sleep(0.3)

        workflow = orchestrator.workflows.get(workflow_id)

        # Tasks should be assigned to agents
        for task in workflow.tasks.values():
            assert task.agent_id in ["agent-1", "agent-2"]
            assert task.status in ["assigned", "sent", "queued", "pending"]

    @pytest.mark.asyncio
    async def test_task_result_submission(self, orchestrator):
        """Test task result submission"""
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.1", agents=["agent-1"]
        )

        await asyncio.sleep(0.3)

        workflow = orchestrator.workflows.get(workflow_id)

        # Get a task
        task_id = list(workflow.tasks.keys())[0]

        # Submit result
        result = {
            "task_id": task_id,
            "status": "success",
            "findings": [{"type": "open_port", "severity": "info", "title": "Port 80 open"}],
            "output": "Nmap scan results...",
            "timestamp": datetime.utcnow().isoformat(),
        }

        await orchestrator.submit_task_result(task_id, result)

        # Check task was updated
        task = workflow.tasks[task_id]
        assert task.status == "completed"
        assert task.result is not None
        assert len(task.result.get("findings", [])) == 1

        # Check finding was added to workflow
        assert len(workflow.findings) == 1


class TestTaskProcessor:
    """Test task execution"""

    @pytest.fixture
    def processor(self):
        return TaskProcessor()

    @pytest.mark.asyncio
    async def test_whois_task(self, processor):
        """Test whois task execution"""
        task = {"id": "test-whois-1", "target": "example.com", "parameters": {"tool": "whois"}}

        result = await processor.process_task(task)

        assert isinstance(result, TaskResult)
        assert result.task_id == "test-whois-1"
        assert result.status in ["success", "failed"]  # May fail if whois not installed
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_dns_task(self, processor):
        """Test DNS task execution"""
        task = {"id": "test-dns-1", "target": "example.com", "parameters": {"tool": "dns"}}

        result = await processor.process_task(task)

        assert isinstance(result, TaskResult)
        assert result.task_id == "test-dns-1"
        assert result.status in ["success", "failed"]

    @pytest.mark.asyncio
    async def test_unknown_tool(self, processor):
        """Test handling of unknown tool"""
        task = {"id": "test-unknown-1", "target": "example.com", "parameters": {"tool": "unknown_tool_xyz"}}

        result = await processor.process_task(task)

        assert result.status == "failed"
        assert "Unknown tool" in result.error


class TestWorkflowListAndStatus:
    """Test workflow listing and status"""

    @pytest.fixture
    def orchestrator(self):
        orch = WorkflowOrchestrator()
        orch.guardrails_enabled = False
        return orch

    @pytest.mark.asyncio
    async def test_list_workflows(self, orchestrator):
        """Test listing workflows"""
        # Create a few workflows
        wf1 = await orchestrator.start_workflow("network_recon", "192.168.1.1", ["agent-1"])
        wf2 = await orchestrator.start_workflow("web_scan", "example.com", ["agent-1"])

        # List all
        workflows = orchestrator.list_workflows()
        assert len(workflows) == 2

        # List by state
        pending = orchestrator.list_workflows(state="pending")
        running = orchestrator.list_workflows(state="running")

        assert len(pending) + len(running) == 2

    @pytest.mark.asyncio
    async def test_get_workflow_status(self, orchestrator):
        """Test getting workflow status"""
        workflow_id = await orchestrator.start_workflow("network_recon", "192.168.1.1", ["agent-1"])

        status = orchestrator.get_workflow_status(workflow_id)

        assert status is not None
        assert status["id"] == workflow_id
        assert "state" in status
        assert "steps" in status
        assert "agents" in status

    def test_get_nonexistent_workflow(self, orchestrator):
        """Test getting status of non-existent workflow"""
        status = orchestrator.get_workflow_status("wf_nonexistent123")
        assert status is None


class TestEndToEnd:
    """Test 3: End-to-end workflow with mock components"""

    @pytest.mark.asyncio
    async def test_full_workflow_mock_execution(self):
        """
        End-to-end test with simulated agent responses.

        This tests the full flow:
        1. Create workflow
        2. Tasks distributed
        3. Simulate agent responses
        4. Workflow completes
        """
        orchestrator = WorkflowOrchestrator()
        orchestrator.guardrails_enabled = False

        # Track events
        events = []

        async def event_handler(event):
            events.append(event)

        orchestrator.on_event(event_handler)

        # Start workflow
        workflow_id = await orchestrator.start_workflow(
            workflow_type="network_recon", target="192.168.1.1", agents=["mock-agent"]
        )

        # Wait for tasks to be created
        await asyncio.sleep(0.5)

        # Simulate agent processing
        workflow = orchestrator.workflows[workflow_id]

        # Submit results for all tasks
        for task_id, task in list(workflow.tasks.items())[:3]:  # First 3 tasks
            result = {
                "task_id": task_id,
                "status": "success",
                "findings": [{"type": "test_finding", "severity": "info", "title": f"Finding from {task.step}"}],
                "output": f"Executed {task.parameters.get('tool', 'unknown')}",
                "timestamp": datetime.utcnow().isoformat(),
            }

            await orchestrator.submit_task_result(task_id, result)

        # Wait for workflow to process results
        await asyncio.sleep(0.5)

        # Check workflow has findings
        workflow = orchestrator.workflows[workflow_id]
        assert len(workflow.findings) > 0

        # Check events were emitted
        event_types = [e.get("type") for e in events]
        assert "workflow_started" in event_types


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
