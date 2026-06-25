"""Smoke tests for core/workflow_engine.py"""

import pytest

from core.workflow_engine import (
    EventBus,
    FunctionTask,
    TaskResult,
    TaskStatus,
    Workflow,
    WorkflowEngine,
    WorkflowState,
    WorkflowStatus,
)


class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.PENDING.name == "PENDING"
        assert TaskStatus.COMPLETED.name == "COMPLETED"


class TestWorkflowStatus:
    def test_values(self):
        assert WorkflowStatus.CREATED.name == "CREATED"
        assert WorkflowStatus.RUNNING.name == "RUNNING"


class TestTaskResult:
    def test_success(self):
        result = TaskResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.execution_time == 0.0

    def test_failure(self):
        result = TaskResult(success=False, error="something went wrong")
        assert result.success is False
        assert result.error == "something went wrong"


class TestWorkflowState:
    def test_creation(self):
        state = WorkflowState(workflow_id="wf-1", name="test")
        assert state.status == WorkflowStatus.CREATED
        assert state.name == "test"


class TestEventBus:
    def test_init(self):
        bus = EventBus()
        assert bus._listeners == {}

    def test_on_off(self):
        bus = EventBus()

        def cb(x):
            return None

        bus.on("test_event", cb)
        assert "test_event" in bus._listeners
        assert cb in bus._listeners["test_event"]
        bus.off("test_event", cb)
        assert cb not in bus._listeners["test_event"]


class TestWorkflow:
    def test_creation(self):
        wf = Workflow(name="test-workflow")
        assert wf.name == "test-workflow"
        assert wf.tasks == {}

    def test_add_task(self):
        wf = Workflow(name="test")
        task = FunctionTask(name="my-task", func=lambda: None)
        wf.add_task(task)
        assert task.task_id in wf.tasks


class TestWorkflowEngine:
    def test_init(self):
        engine = WorkflowEngine(max_parallel_tasks=5)
        assert engine.max_parallel_tasks == 5
        assert engine.event_bus is not None
