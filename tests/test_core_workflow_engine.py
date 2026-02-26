"""Tests für core/workflow_engine.py - Target: 80%+ Coverage."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from core.workflow_engine import (
    TaskStatus,
    WorkflowStatus,
    TaskResult,
    TaskState,
    WorkflowState,
    Task,
    FunctionTask,
    WorkflowEngine,
)


class TestTaskStatus:
    """Tests für TaskStatus Enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestWorkflowStatus:
    """Tests für WorkflowStatus Enum."""

    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"


class TestTaskResult:
    """Tests für TaskResult."""

    def test_task_result_init(self):
        """Test TaskResult initialization."""
        result = TaskResult(
            success=True,
            data={"key": "value"},
        )
        assert result.success is True
        assert result.data == {"key": "value"}

    def test_task_result_defaults(self):
        """Test TaskResult default values."""
        result = TaskResult(success=False)
        assert result.success is False
        assert result.data is None
        assert result.error is None


class TestTaskState:
    """Tests für TaskState."""

    def test_task_state_init(self):
        """Test TaskState initialization."""
        state = TaskState(
            task_id="task-1",
            name="Test Task",
        )
        assert state.task_id == "task-1"
        assert state.name == "Test Task"
        assert state.status == TaskStatus.PENDING


class TestWorkflowState:
    """Tests für WorkflowState."""

    def test_workflow_state_init(self):
        """Test WorkflowState initialization."""
        state = WorkflowState(
            workflow_id="wf-1",
            name="Test Workflow",
        )
        assert state.workflow_id == "wf-1"
        assert state.name == "Test Workflow"
        assert state.status == WorkflowStatus.PENDING


class TestFunctionTask:
    """Tests für FunctionTask."""

    def test_function_task_init(self):
        """Test FunctionTask initialization."""
        def test_func():
            return "result"
        
        task = FunctionTask(
            task_id="task-1",
            name="Test Task",
            func=test_func,
        )
        assert task.task_id == "task-1"
        assert task.name == "Test Task"


class TestWorkflowEngine:
    """Tests für WorkflowEngine."""

    @pytest.fixture
    def engine(self):
        """Create a test workflow engine."""
        return WorkflowEngine()

    def test_engine_init(self, engine):
        """Test engine initialization."""
        assert engine is not None

    def test_create_workflow(self, engine):
        """Test creating a workflow."""
        workflow = engine.create_workflow(
            name="Test Workflow",
            description="Test description",
        )
        assert workflow is not None
        assert workflow.name == "Test Workflow"

    def test_get_workflow(self, engine):
        """Test getting a workflow."""
        workflow = engine.create_workflow(name="Test Workflow")
        workflow_id = workflow.workflow_id
        retrieved = engine.get_workflow(workflow_id)
        assert retrieved is not None
        assert retrieved.name == "Test Workflow"

    def test_list_workflows_empty(self, engine):
        """Test listing workflows when empty."""
        workflows = engine.list_workflows()
        assert workflows == []
