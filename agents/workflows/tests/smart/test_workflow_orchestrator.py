"""
SMART Tests for WorkflowOrchestrator Module

Test Strategy:
1. test_module_importable - Verify module imports correctly
2. test_module_uses_tool_executor - Verify ToolExecutor pattern
3. test_module_not_found_error - Handle missing dependencies
4. test_module_timeout_error - Handle timeout scenarios
5. test_module_parser_extracts_findings - Verify data extraction
6. test_module_end_to_end_mocked - Full workflow with mocks
7. test_module_empty_input - Handle empty/null inputs
8. test_module_invalid_output - Handle invalid outputs
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.workflows.orchestrator import (
    WORKFLOW_DEFINITIONS,
    Task,
    Workflow,
    WorkflowOrchestrator,
    WorkflowState,
    WorkflowStep,
    get_workflow_orchestrator,
)

# =============================================================================
# Test 1: Module Import
# =============================================================================


class TestModuleImportable:
    """Test that the module can be imported correctly."""

    def test_workflow_orchestrator_importable(self):
        """Test that WorkflowOrchestrator can be imported."""
        from agents.workflows.orchestrator import WorkflowOrchestrator

        assert WorkflowOrchestrator is not None

    def test_workflow_state_importable(self):
        """Test that WorkflowState enum can be imported."""
        from agents.workflows.orchestrator import WorkflowState

        assert WorkflowState is not None
        assert hasattr(WorkflowState, "PENDING")
        assert hasattr(WorkflowState, "RUNNING")
        assert hasattr(WorkflowState, "COMPLETED")
        assert hasattr(WorkflowState, "FAILED")

    def test_workflow_step_importable(self):
        """Test that WorkflowStep enum can be imported."""
        from agents.workflows.orchestrator import WorkflowStep

        assert WorkflowStep is not None
        assert hasattr(WorkflowStep, "RECONNAISSANCE")
        assert hasattr(WorkflowStep, "SCANNING")
        assert hasattr(WorkflowStep, "EXPLOITATION")

    def test_workflow_definitions_importable(self):
        """Test that workflow definitions can be imported."""
        from agents.workflows.orchestrator import WORKFLOW_DEFINITIONS

        assert WORKFLOW_DEFINITIONS is not None
        assert "network_recon" in WORKFLOW_DEFINITIONS
        assert "web_scan" in WORKFLOW_DEFINITIONS
        assert "full_pentest" in WORKFLOW_DEFINITIONS

    def test_get_workflow_orchestrator_singleton(self):
        """Test global orchestrator singleton."""
        orch1 = get_workflow_orchestrator()
        orch2 = get_workflow_orchestrator()
        assert orch1 is orch2


# =============================================================================
# Test 2: ToolExecutor Pattern (Architecture Compliance)
# =============================================================================


class TestModuleUsesToolExecutor:
    """Verify ToolExecutor pattern compliance."""

    def test_orchestrator_has_async_execute(self, workflow_orchestrator):
        """Verify orchestrator uses async execution."""
        import inspect

        assert inspect.iscoroutinefunction(workflow_orchestrator.start_workflow)
        assert inspect.iscoroutinefunction(workflow_orchestrator._execute_workflow)
        assert inspect.iscoroutinefunction(workflow_orchestrator._execute_step)
        assert inspect.iscoroutinefunction(workflow_orchestrator.submit_task_result)

    def test_orchestrator_has_task_management(self, workflow_orchestrator):
        """Verify task management methods exist."""
        assert hasattr(workflow_orchestrator, "submit_task_result")
        assert hasattr(workflow_orchestrator, "_distribute_tasks")
        assert hasattr(workflow_orchestrator, "_wait_for_tasks")

    def test_orchestrator_uses_timeout(self, workflow_orchestrator):
        """Verify timeout configuration."""
        assert hasattr(workflow_orchestrator, "step_timeout")
        assert workflow_orchestrator.step_timeout == 5


# =============================================================================
# Test 3: Not Found Error Handling
# =============================================================================


class TestModuleNotFoundError:
    """Test handling of missing workflows/resources."""

    def test_get_workflow_status_not_found(self, workflow_orchestrator):
        """Test getting status of non-existent workflow."""
        result = workflow_orchestrator.get_workflow_status("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_workflow(self, workflow_orchestrator):
        """Test cancelling non-existent workflow."""
        result = await workflow_orchestrator.cancel_workflow("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_submit_task_result_not_found(self, workflow_orchestrator, sample_task_result):
        """Test submitting result for non-existent task."""
        # Should not raise, just log warning
        await workflow_orchestrator.submit_task_result("nonexistent_task", sample_task_result)

    def test_start_workflow_unknown_type(self, workflow_orchestrator):
        """Test starting workflow with unknown type."""
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(workflow_orchestrator.start_workflow("unknown_type", "example.com", ["agent_001"]))
        assert "Unknown workflow type" in str(exc_info.value)


# =============================================================================
# Test 4: Timeout Error Handling
# =============================================================================


class TestModuleTimeoutError:
    """Test timeout handling in workflow orchestrator."""

    @pytest.mark.asyncio
    async def test_step_timeout_handling(self, workflow_orchestrator, sample_workflow):
        """Test step timeout handling."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow
        workflow_orchestrator.active_workflows.add(sample_workflow.id)

        # Create a task that will timeout
        task = Task(
            id="task_timeout_test",
            workflow_id=sample_workflow.id,
            step="reconnaissance",
            agent_id="agent_001",
            target="example.com",
            parameters={},
            status="running",
        )
        sample_workflow.tasks[task.id] = task

        # Wait with short timeout
        result = await workflow_orchestrator._wait_for_tasks(sample_workflow.id, [task], timeout=0.1)

        assert result is False  # Timeout should cause failure
        assert task.status == "failed"
        assert task.result == {"error": "Timeout"}


# =============================================================================
# Test 5: Parser/Data Extraction Tests
# =============================================================================


class TestModuleParserExtractsFindings:
    """Test data extraction and parsing capabilities."""

    def test_workflow_to_dict(self, sample_workflow):
        """Test workflow serialization."""
        workflow_dict = sample_workflow.to_dict()

        assert workflow_dict["id"] == sample_workflow.id
        assert workflow_dict["type"] == "network_recon"
        assert workflow_dict["target"] == "example.com"
        assert workflow_dict["state"] == "pending"
        assert "task_count" in workflow_dict
        assert "finding_count" in workflow_dict

    def test_task_to_dict(self, sample_task):
        """Test task serialization."""
        task_dict = sample_task.to_dict()

        assert task_dict["id"] == sample_task.id
        assert task_dict["workflow_id"] == sample_task.workflow_id
        assert task_dict["step"] == "reconnaissance"
        assert task_dict["status"] == "pending"

    @pytest.mark.asyncio
    async def test_submit_task_result_with_findings(self, workflow_orchestrator, sample_workflow, sample_task_result):
        """Test extracting findings from task result."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow
        sample_workflow.tasks["task_001"] = Task(
            id="task_001",
            workflow_id=sample_workflow.id,
            step="scanning",
            agent_id="agent_001",
            target="example.com",
            parameters={},
            status="running",
        )

        await workflow_orchestrator.submit_task_result("task_001", sample_task_result)

        assert len(sample_workflow.findings) == 1
        assert sample_workflow.findings[0]["id"] == "CVE-2021-44228"

    def test_list_workflows_filtering(self, workflow_orchestrator, sample_workflow):
        """Test workflow list filtering."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow

        # Test no filter
        all_workflows = workflow_orchestrator.list_workflows()
        assert len(all_workflows) == 1

        # Test with state filter
        pending = workflow_orchestrator.list_workflows(state="pending")
        assert len(pending) == 1

        running = workflow_orchestrator.list_workflows(state="running")
        assert len(running) == 0


# =============================================================================
# Test 6: End-to-End Workflow Tests
# =============================================================================


class TestModuleEndToEndMocked:
    """Test complete workflows with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle(self, workflow_orchestrator):
        """Test complete workflow from start to completion."""
        with patch("agents.workflows.orchestrator.GUARDRAILS_AVAILABLE", False):
            with patch.object(workflow_orchestrator, "_execute_step", return_value=True):
                workflow_id = await workflow_orchestrator.start_workflow(
                    workflow_type="network_recon",
                    target="example.com",
                    agents=["agent_001"],
                )

                assert workflow_id.startswith("wf_")
                assert workflow_id in workflow_orchestrator.workflows

                workflow = workflow_orchestrator.workflows[workflow_id]
                assert workflow.type == "network_recon"
                assert workflow.target == "example.com"

    @pytest.mark.asyncio
    async def test_workflow_event_handling(self, workflow_orchestrator, sample_event_handler):
        """Test workflow event emission and handling."""
        workflow_orchestrator.on_event(sample_event_handler)

        # Create a workflow and emit event
        workflow = Workflow(
            id="wf_event_test",
            type="network_recon",
            target="example.com",
            state=WorkflowState.RUNNING,
        )
        workflow_orchestrator.workflows[workflow.id] = workflow

        await workflow_orchestrator._emit_event("test_event", {"data": "test"})

        sample_event_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_distribution(
        self,
        workflow_orchestrator,
        sample_workflow,
        mock_agent_connection_manager,
    ):
        """Test task distribution to agents."""
        with patch(
            "agents.workflows.orchestrator.agent_connection_manager",
            mock_agent_connection_manager,
        ):
            workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow

            tasks = [
                Task(
                    id="task_001",
                    workflow_id=sample_workflow.id,
                    step="reconnaissance",
                    agent_id=None,
                    target="example.com",
                    parameters={"tool": "whois"},
                )
            ]

            await workflow_orchestrator._distribute_tasks(sample_workflow.id, tasks)

            assert tasks[0].agent_id in sample_workflow.agents
            assert tasks[0].status in ["assigned", "sent", "queued"]


# =============================================================================
# Test 7: Empty Input Handling
# =============================================================================


class TestModuleEmptyInput:
    """Test handling of empty/null inputs."""

    def test_empty_workflow_list(self, workflow_orchestrator):
        """Test listing workflows when none exist."""
        workflows = workflow_orchestrator.list_workflows()
        assert workflows == []

    def test_empty_parameters(self, workflow_orchestrator):
        """Test workflow with empty parameters."""
        with patch("agents.workflows.orchestrator.GUARDRAILS_AVAILABLE", False):
            with patch.object(workflow_orchestrator, "_execute_step", return_value=True):
                workflow_id = asyncio.run(
                    workflow_orchestrator.start_workflow(
                        workflow_type="network_recon",
                        target="example.com",
                        agents=["agent_001"],
                        parameters={},  # Empty parameters
                    )
                )

                assert workflow_id in workflow_orchestrator.workflows

    def test_empty_agents_list(self, workflow_orchestrator):
        """Test workflow with empty agents list."""
        with patch("agents.workflows.orchestrator.GUARDRAILS_AVAILABLE", False):
            with patch.object(workflow_orchestrator, "_execute_step", return_value=True):
                workflow_id = asyncio.run(
                    workflow_orchestrator.start_workflow(
                        workflow_type="network_recon",
                        target="example.com",
                        agents=[],  # Empty agents
                    )
                )

                assert workflow_id in workflow_orchestrator.workflows

    @pytest.mark.asyncio
    async def test_wait_for_tasks_empty_list(self, workflow_orchestrator, sample_workflow):
        """Test waiting for empty task list."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow

        result = await workflow_orchestrator._wait_for_tasks(sample_workflow.id, [], timeout=5)

        assert result is True  # Empty list should return success


# =============================================================================
# Test 8: Invalid Output Handling
# =============================================================================


class TestModuleInvalidOutput:
    """Test handling of invalid outputs."""

    @pytest.mark.asyncio
    async def test_submit_task_result_invalid_format(self, workflow_orchestrator, sample_workflow):
        """Test submitting result with invalid format."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow
        sample_workflow.tasks["task_001"] = Task(
            id="task_001",
            workflow_id=sample_workflow.id,
            step="scanning",
            agent_id="agent_001",
            target="example.com",
            parameters={},
        )

        # Submit result with error
        await workflow_orchestrator.submit_task_result("task_001", {"error": "Failed"})

        task = sample_workflow.tasks["task_001"]
        assert task.status == "failed"

    def test_validate_target_invalid(self, workflow_orchestrator_with_guardrails):
        """Test target validation with invalid target."""
        orch = workflow_orchestrator_with_guardrails

        with patch("agents.workflows.orchestrator.validate_domain") as mock_validate:

            class InvalidResult:
                is_valid = False
                reason = "Invalid domain"

            mock_validate.return_value = InvalidResult()

            is_valid, error = orch._validate_target("invalid..domain")

            assert is_valid is False
            assert error is not None

    @pytest.mark.asyncio
    async def test_cancel_completed_workflow(self, workflow_orchestrator, sample_workflow):
        """Test cancelling already completed workflow."""
        sample_workflow.state = WorkflowState.COMPLETED
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow

        result = await workflow_orchestrator.cancel_workflow(sample_workflow.id)

        assert result is False  # Cannot cancel completed workflow


# =============================================================================
# Additional Core Functionality Tests
# =============================================================================


class TestWorkflowInitialization:
    """Test workflow orchestrator initialization."""

    def test_default_initialization(self):
        """Test default orchestrator initialization."""
        orch = WorkflowOrchestrator()

        assert orch.step_timeout == 300  # Default timeout
        assert orch.guardrails_enabled is False
        assert orch.risk_manager is None
        assert len(orch.workflows) == 0
        assert len(orch.active_workflows) == 0

    def test_custom_timeout_initialization(self):
        """Test orchestrator with custom timeout."""
        orch = WorkflowOrchestrator(step_timeout=60)

        assert orch.step_timeout == 60


class TestTargetValidation:
    """Test target validation functionality."""

    def test_validate_target_without_guardrails(self, workflow_orchestrator):
        """Test target validation when guardrails disabled."""
        is_valid, error = workflow_orchestrator._validate_target("example.com")

        assert is_valid is True
        assert error is None

    def test_validate_target_url(self, workflow_orchestrator_with_guardrails):
        """Test URL target validation."""
        orch = workflow_orchestrator_with_guardrails

        with patch("agents.workflows.orchestrator.validate_url") as mock_validate:

            class ValidResult:
                is_valid = True
                reason = None

            mock_validate.return_value = ValidResult()

            is_valid, error = orch._validate_target("https://example.com")

            assert is_valid is True
            assert error is None


class TestToolPermissionValidation:
    """Test tool permission validation."""

    def test_validate_tool_allowed(self, workflow_orchestrator_with_guardrails):
        """Test allowed tool validation."""
        orch = workflow_orchestrator_with_guardrails

        is_allowed, error = orch._validate_tool_permission("nmap")

        assert is_allowed is True
        assert error is None

    def test_validate_tool_blocked(self, workflow_orchestrator_with_guardrails):
        """Test blocked tool validation."""
        orch = workflow_orchestrator_with_guardrails
        orch.risk_manager.can_run_tool.return_value = False
        orch.risk_manager.get_blocked_tools.return_value = ["exploit"]

        is_allowed, error = orch._validate_tool_permission("exploit")

        assert is_allowed is False
        assert "not allowed" in error.lower()


class TestWorkflowStepExecution:
    """Test workflow step execution."""

    def test_create_step_tasks(self, workflow_orchestrator, sample_workflow):
        """Test task creation for workflow steps."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow

        tasks = workflow_orchestrator._create_step_tasks(sample_workflow.id, WorkflowStep.RECONNAISSANCE.value)

        assert len(tasks) > 0
        assert all(isinstance(t, Task) for t in tasks)
        assert all(t.workflow_id == sample_workflow.id for t in tasks)

    def test_create_step_tasks_unknown_step(self, workflow_orchestrator, sample_workflow):
        """Test task creation for unknown step."""
        workflow_orchestrator.workflows[sample_workflow.id] = sample_workflow

        tasks = workflow_orchestrator._create_step_tasks(sample_workflow.id, "unknown_step")

        assert tasks == []


class TestWorkflowDefinitions:
    """Test workflow definitions."""

    def test_network_recon_definition(self):
        """Test network reconnaissance workflow definition."""
        definition = WORKFLOW_DEFINITIONS["network_recon"]

        assert "name" in definition
        assert "description" in definition
        assert "steps" in definition
        assert WorkflowStep.RECONNAISSANCE.value in definition["steps"]

    def test_full_pentest_definition(self):
        """Test full pentest workflow definition."""
        definition = WORKFLOW_DEFINITIONS["full_pentest"]

        assert len(definition["steps"]) == 7  # All steps
        assert WorkflowStep.RECONNAISSANCE.value in definition["steps"]
        assert WorkflowStep.EXPLOITATION.value in definition["steps"]
        assert WorkflowStep.POST_EXPLOITATION.value in definition["steps"]

    def test_get_available_workflow_types(self, workflow_orchestrator):
        """Test getting available workflow types."""
        types = workflow_orchestrator.get_available_workflow_types()

        assert "network_recon" in types
        assert "web_scan" in types
        assert "full_pentest" in types
        assert "targeted_attack" in types


class TestWorkflowStateTransitions:
    """Test workflow state transitions."""

    @pytest.mark.asyncio
    async def test_workflow_state_running(self, workflow_orchestrator):
        """Test workflow transitions to running state."""
        with patch("agents.workflows.orchestrator.GUARDRAILS_AVAILABLE", False):
            with patch.object(workflow_orchestrator, "_execute_step", return_value=True):
                workflow_id = await workflow_orchestrator.start_workflow(
                    workflow_type="network_recon",
                    target="example.com",
                    agents=["agent_001"],
                )

                workflow = workflow_orchestrator.workflows[workflow_id]
                # After start, state should be running (async execution)
                assert workflow.state in [
                    WorkflowState.PENDING,
                    WorkflowState.RUNNING,
                ]

    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, workflow_orchestrator):
        """Test workflow cancellation."""
        with patch("agents.workflows.orchestrator.GUARDRAILS_AVAILABLE", False):
            workflow_id = await workflow_orchestrator.start_workflow(
                workflow_type="network_recon",
                target="example.com",
                agents=["agent_001"],
            )

            # Cancel the workflow
            result = await workflow_orchestrator.cancel_workflow(workflow_id)

            assert result is True
            workflow = workflow_orchestrator.workflows[workflow_id]
            assert workflow.state == WorkflowState.CANCELLED
