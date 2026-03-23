"""
Comprehensive tests for the Workflow Engine.

Tests cover:
- WorkflowEngine class
- Workflow definitions and execution
- Task classes (FunctionTask, SubWorkflowTask)
- State transitions
- EventBus integration
- Error handling and retry logic
- Parallel execution
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from core.workflow_engine import (
    EventBus,
    FunctionTask,
    SubWorkflowTask,
    Task,
    TaskResult,
    TaskState,
    TaskStatus,
    Workflow,
    WorkflowEngine,
    WorkflowState,
    WorkflowStatus,
    task,
)

# =============================================================================
# Workflow Tests
# =============================================================================


class TestWorkflow:
    """Tests for Workflow class."""

    def test_workflow_creation(self):
        """Test workflow initialization."""
        workflow = Workflow(
            name="Test Workflow",
            workflow_id="test-123",
            description="A test workflow",
            version="1.0.0",
        )

        assert workflow.name == "Test Workflow"
        assert workflow.workflow_id == "test-123"
        assert workflow.description == "A test workflow"
        assert workflow.version == "1.0.0"
        assert workflow.tasks == {}
        assert workflow.task_order == []

    def test_workflow_auto_id(self):
        """Test workflow auto-generates ID."""
        workflow = Workflow(name="Test Workflow")
        assert workflow.workflow_id.startswith("workflow_")
        assert len(workflow.workflow_id) > 10

    def test_add_task(self):
        """Test adding tasks to workflow."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        task2 = FunctionTask(name="task2", func=lambda: None, task_id="t2")

        workflow.add_task(task1)
        assert "t1" in workflow.tasks
        assert workflow.task_order == ["t1"]

        workflow.add_task(task2)
        assert "t2" in workflow.tasks
        assert workflow.task_order == ["t1", "t2"]

    def test_add_tasks_chain(self):
        """Test adding multiple tasks in chain."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        task2 = FunctionTask(name="task2", func=lambda: None, task_id="t2")

        result = workflow.add_tasks(task1, task2)
        assert result is workflow  # Returns self for chaining
        assert len(workflow.tasks) == 2

    def test_get_task(self):
        """Test getting tasks by ID."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        workflow.add_task(task1)

        found = workflow.get_task("t1")
        assert found is task1

        not_found = workflow.get_task("nonexistent")
        assert not_found is None

    def test_get_dependencies(self):
        """Test getting task dependencies."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        task2 = FunctionTask(
            name="task2", func=lambda: None, task_id="t2", dependencies=["t1"]
        )

        workflow.add_task(task1)
        workflow.add_task(task2)

        deps = workflow.get_dependencies("t2")
        assert deps == ["t1"]

        no_deps = workflow.get_dependencies("t1")
        assert no_deps == []

    def test_get_execution_order_linear(self):
        """Test execution order for linear workflow."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        task2 = FunctionTask(
            name="task2", func=lambda: None, task_id="t2", dependencies=["t1"]
        )
        task3 = FunctionTask(
            name="task3", func=lambda: None, task_id="t3", dependencies=["t2"]
        )

        workflow.add_tasks(task1, task2, task3)

        order = workflow.get_execution_order()
        assert len(order) == 3
        assert order[0] == ["t1"]
        assert order[1] == ["t2"]
        assert order[2] == ["t3"]

    def test_get_execution_order_parallel(self):
        """Test execution order with parallel tasks."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        task2 = FunctionTask(
            name="task2", func=lambda: None, task_id="t2", dependencies=["t1"]
        )
        task3 = FunctionTask(
            name="task3", func=lambda: None, task_id="t3", dependencies=["t1"]
        )
        task4 = FunctionTask(
            name="task4",
            func=lambda: None,
            task_id="t4",
            dependencies=["t2", "t3"],
        )

        workflow.add_tasks(task1, task2, task3, task4)

        order = workflow.get_execution_order()
        assert len(order) == 3
        assert order[0] == ["t1"]
        assert set(order[1]) == {"t2", "t3"}  # Parallel
        assert order[2] == ["t4"]

    def test_get_execution_order_circular_dependency(self):
        """Test error on circular dependency."""
        workflow = Workflow(name="Test")

        task1 = FunctionTask(
            name="task1", func=lambda: None, task_id="t1", dependencies=["t2"]
        )
        task2 = FunctionTask(
            name="task2", func=lambda: None, task_id="t2", dependencies=["t1"]
        )

        workflow.add_tasks(task1, task2)

        with pytest.raises(ValueError, match="Cannot resolve dependencies"):
            workflow.get_execution_order()

    def test_workflow_to_dict(self):
        """Test workflow serialization."""
        workflow = Workflow(
            name="Test",
            workflow_id="test-123",
            description="Test workflow",
            version="1.0",
        )

        task1 = FunctionTask(name="task1", func=lambda: None, task_id="t1")
        workflow.add_task(task1)

        d = workflow.to_dict()
        assert d["name"] == "Test"
        assert d["workflow_id"] == "test-123"
        assert d["description"] == "Test workflow"
        assert d["version"] == "1.0"
        assert "tasks" in d
        assert "task_order" in d

    def test_workflow_from_dict(self):
        """Test workflow deserialization."""
        data = {
            "name": "Test",
            "workflow_id": "test-123",
            "description": "Test workflow",
            "version": "1.0",
            "tasks": {},
            "task_order": [],
        }

        workflow = Workflow.from_dict(data)
        assert workflow.name == "Test"
        assert workflow.workflow_id == "test-123"
        assert workflow.description == "Test workflow"
        assert workflow.version == "1.0"


# =============================================================================
# Task Tests
# =============================================================================


class TestTask:
    """Tests for Task base class."""

    def test_task_creation(self):
        """Test task initialization."""
        task = Task(
            name="Test Task",
            task_id="test-1",
            dependencies=["dep1", "dep2"],
            max_retries=5,
            retry_delay=2.0,
            timeout=300.0,
            parallel=True,
            metadata={"key": "value"},
        )

        assert task.name == "Test Task"
        assert task.task_id == "test-1"
        assert task.dependencies == ["dep1", "dep2"]
        assert task.max_retries == 5
        assert task.retry_delay == 2.0
        assert task.timeout == 300.0
        assert task.parallel is True
        assert task.metadata == {"key": "value"}

    def test_task_auto_id(self):
        """Test task auto-generates ID."""
        task = Task(name="Test")
        assert task.task_id.startswith("Test_")

    def test_should_execute_no_condition(self):
        """Test task executes when no condition."""
        task = Task(name="Test")
        assert task.should_execute({}) is True

    def test_should_execute_with_condition(self):
        """Test conditional execution."""

        def condition(ctx):
            return ctx.get("should_run", False)

        task = Task(name="Test", condition=condition)

        assert task.should_execute({"should_run": True}) is True
        assert task.should_execute({"should_run": False}) is False

    def test_should_execute_condition_error(self):
        """Test task skips when condition raises error."""

        def bad_condition(ctx):
            raise ValueError("Test error")

        task = Task(name="Test", condition=bad_condition)

        assert task.should_execute({}) is False

    def test_task_to_dict(self):
        """Test task serialization."""
        task = Task(
            name="Test",
            task_id="test-1",
            dependencies=["dep1"],
            max_retries=3,
            retry_delay=1.0,
            timeout=100.0,
            parallel=False,
            metadata={"key": "value"},
        )

        d = task.to_dict()
        assert d["name"] == "Test"
        assert d["task_id"] == "test-1"
        assert d["dependencies"] == ["dep1"]
        assert d["max_retries"] == 3
        assert d["retry_delay"] == 1.0
        assert d["timeout"] == 100.0
        assert d["parallel"] is False
        assert d["metadata"] == {"key": "value"}


class TestFunctionTask:
    """Tests for FunctionTask class."""

    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """Test executing async function."""

        async def async_func(arg1, arg2, context):
            return {"sum": arg1 + arg2, "context_keys": list(context.keys())}

        task = FunctionTask(
            name="Async Task",
            func=async_func,
            args=[1, 2],
            kwargs={"extra": "value"},
        )

        context = {"workflow_id": "wf-1"}
        result = await task.execute(context)

        assert result.success is True
        assert result.data["sum"] == 3
        assert "context" in result.data["context_keys"]

    @pytest.mark.asyncio
    async def test_sync_function_execution(self):
        """Test executing sync function in thread pool."""

        def sync_func(arg1, context):
            return {"result": arg1 * 2}

        task = FunctionTask(name="Sync Task", func=sync_func, args=[5])

        context = {}
        result = await task.execute(context)

        assert result.success is True
        assert result.data["result"] == 10

    @pytest.mark.asyncio
    async def test_function_execution_error(self):
        """Test error handling in function execution."""

        async def failing_func(context):
            raise ValueError("Test error")

        task = FunctionTask(name="Failing Task", func=failing_func)

        result = await task.execute({})

        assert result.success is False
        assert "Test error" in result.error
        assert result.execution_time > 0
        assert "traceback" in result.metadata

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self):
        """Test that execution time is tracked."""

        async def slow_func(context):
            await asyncio.sleep(0.1)
            return {}

        task = FunctionTask(name="Slow Task", func=slow_func)

        start = time.time()
        result = await task.execute({})
        elapsed = time.time() - start

        assert result.execution_time >= 0.1
        assert result.execution_time <= elapsed + 0.05  # Reasonable tolerance


class TestSubWorkflowTask:
    """Tests for SubWorkflowTask class."""

    @pytest.mark.asyncio
    async def test_subworkflow_execution(self):
        """Test executing a sub-workflow."""
        sub_workflow = Workflow(name="Sub Workflow")

        async def task_func(context):
            return {"sub_result": "success"}

        sub_task = FunctionTask(name="sub_task", func=task_func, task_id="st1")
        sub_workflow.add_task(sub_task)

        parent_task = SubWorkflowTask(name="Parent", workflow=sub_workflow)

        with patch("core.workflow_engine.WorkflowEngine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_state = MagicMock()
            mock_state.status = WorkflowStatus.COMPLETED
            mock_state.to_dict.return_value = {"status": "completed"}
            mock_state.workflow_id = "sub-wf-123"
            mock_engine.execute_workflow = AsyncMock(return_value=mock_state)
            mock_engine_class.return_value = mock_engine

            result = await parent_task.execute({"parent_key": "value"})

            assert result.success is True
            assert "sub_workflow_id" in result.metadata
            mock_engine_class.assert_called_once()
            mock_engine.execute_workflow.assert_called_once()


# =============================================================================
# WorkflowEngine Tests
# =============================================================================


class TestWorkflowEngine:
    """Tests for WorkflowEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a test workflow engine."""
        return WorkflowEngine(max_parallel_tasks=5)

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.max_parallel_tasks == 5
        assert engine.state_manager is None
        assert engine.event_bus is not None
        assert isinstance(engine._semaphore, asyncio.Semaphore)

    def test_event_registration(self, engine):
        """Test event listener registration."""
        handler = Mock()

        result = engine.on("workflow.started", handler)
        assert result is engine  # Returns self for chaining

        # Verify registration
        assert handler in engine.event_bus._listeners.get(
            "workflow.started", []
        )

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self, engine):
        """Test executing a simple workflow."""
        workflow = Workflow(name="Simple Workflow")

        execution_log = []

        async def task1_func(context):
            execution_log.append("task1")
            return {"step": 1}

        async def task2_func(context):
            execution_log.append("task2")
            return {"step": 2}

        task1 = FunctionTask(
            name="task1",
            func=task1_func,
            task_id="t1",
            metadata={"save_to_context": True, "context_key": "result1"},
        )
        task2 = FunctionTask(
            name="task2", func=task2_func, task_id="t2", dependencies=["t1"]
        )

        workflow.add_tasks(task1, task2)

        state = await engine.execute_workflow(workflow, {"initial": "data"})

        assert state.status == WorkflowStatus.COMPLETED
        assert len(execution_log) == 2
        assert execution_log == ["task1", "task2"]
        assert state.context.get("result1") == {"step": 1}

    @pytest.mark.asyncio
    async def test_execute_parallel_workflow(self, engine):
        """Test executing parallel tasks."""
        workflow = Workflow(name="Parallel Workflow")

        execution_times = []

        async def parallel_task(name):
            async def task_func(context):
                execution_times.append((name, time.time()))
                await asyncio.sleep(0.1)
                return {"name": name}

            return task_func

        task1 = FunctionTask(
            name="task1", func=await parallel_task("A"), task_id="t1"
        )
        task2 = FunctionTask(
            name="task2", func=await parallel_task("B"), task_id="t2"
        )
        task3 = FunctionTask(
            name="task3", func=await parallel_task("C"), task_id="t3"
        )

        # All three can run in parallel (no dependencies)
        workflow.add_tasks(task1, task2, task3)

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.COMPLETED
        assert len(execution_times) == 3

        # All should start within a small window (parallel execution)
        times = [t[1] for t in execution_times]
        max_diff = max(times) - min(times)
        assert max_diff < 0.05  # Should start almost simultaneously

    @pytest.mark.asyncio
    async def test_task_retry_on_failure(self, engine):
        """Test task retry logic."""
        workflow = Workflow(name="Retry Workflow")

        attempt_count = 0

        async def failing_task(context):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError(f"Attempt {attempt_count} failed")
            return {"success": True}

        task1 = FunctionTask(
            name="retry_task",
            func=failing_task,
            task_id="t1",
            max_retries=3,
            retry_delay=0.01,  # Fast retry for tests
        )
        workflow.add_task(task1)

        events_received = []
        engine.on(
            "task.retrying", lambda e: events_received.append("retrying")
        )
        engine.on(
            "task.completed", lambda e: events_received.append("completed")
        )

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.COMPLETED
        assert attempt_count == 3
        assert "retrying" in events_received
        assert "completed" in events_received

    @pytest.mark.asyncio
    async def test_task_failure_after_max_retries(self, engine):
        """Test task failure after exhausting retries."""
        workflow = Workflow(name="Failure Workflow")

        async def always_failing(context):
            raise ValueError("Always fails")

        task1 = FunctionTask(
            name="failing_task",
            func=always_failing,
            task_id="t1",
            max_retries=2,
            retry_delay=0.01,
        )
        workflow.add_task(task1)

        events_received = []
        engine.on("task.failed", lambda e: events_received.append("failed"))

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.FAILED
        assert "failed" in events_received
        assert "1 task(s) failed" in state.error_message

    @pytest.mark.asyncio
    async def test_task_timeout(self, engine):
        """Test task timeout handling."""
        workflow = Workflow(name="Timeout Workflow")

        async def slow_task(context):
            await asyncio.sleep(10)  # Much longer than timeout
            return {}

        task1 = FunctionTask(
            name="slow_task", func=slow_task, task_id="t1", timeout=0.1
        )  # 100ms timeout
        workflow.add_task(task1)

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.FAILED
        task_state = state.tasks["t1"]
        assert task_state.status == TaskStatus.FAILED
        assert "timeout" in task_state.result.error.lower()

    @pytest.mark.asyncio
    async def test_conditional_task_skip(self, engine):
        """Test conditional task execution."""
        workflow = Workflow(name="Conditional Workflow")

        execution_log = []

        async def always_run(context):
            execution_log.append("always")
            return {}

        async def conditional_run(context):
            execution_log.append("conditional")
            return {}

        def should_run(ctx):
            return ctx.get("run_condition", False)

        task1 = FunctionTask(name="task1", func=always_run, task_id="t1")
        task2 = FunctionTask(
            name="task2",
            func=conditional_run,
            task_id="t2",
            condition=should_run,
        )

        workflow.add_tasks(task1, task2)

        # First run - condition is False
        state = await engine.execute_workflow(
            workflow, {"run_condition": False}
        )

        assert state.status == WorkflowStatus.COMPLETED
        assert execution_log == ["always"]
        assert state.tasks["t2"].status == TaskStatus.SKIPPED

        # Second run - condition is True
        execution_log.clear()
        state = await engine.execute_workflow(
            workflow, {"run_condition": True}
        )

        assert execution_log == ["always", "conditional"]

    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, engine):
        """Test workflow cancellation."""
        workflow = Workflow(name="Cancellable Workflow")

        async def long_task(context):
            await asyncio.sleep(10)
            return {}

        task1 = FunctionTask(name="task1", func=long_task, task_id="t1")
        workflow.add_task(task1)

        # Start workflow in background
        workflow_task = asyncio.create_task(
            engine.execute_workflow(workflow, workflow_id="wf-cancel")
        )

        # Give it time to start
        await asyncio.sleep(0.05)

        # Cancel it
        await engine.cancel_workflow("wf-cancel")

        # Wait for completion
        state = await workflow_task

        # The workflow should have been cancelled or failed
        assert state.status in [
            WorkflowStatus.CANCELLED,
            WorkflowStatus.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_workflow_with_state_manager(self):
        """Test workflow with state persistence."""
        mock_state_manager = AsyncMock()
        mock_state_manager.exists = AsyncMock(return_value=False)
        mock_state_manager.save = AsyncMock(return_value=True)

        engine = WorkflowEngine(
            max_parallel_tasks=5, state_manager=mock_state_manager
        )

        workflow = Workflow(name="Persisted Workflow")

        async def simple_task(context):
            return {"result": "ok"}

        task1 = FunctionTask(name="task1", func=simple_task, task_id="t1")
        workflow.add_task(task1)

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.COMPLETED
        # State should be saved multiple times
        assert mock_state_manager.save.call_count >= 1

    @pytest.mark.asyncio
    async def test_workflow_resumption(self):
        """Test resuming a workflow from saved state."""
        # Create a state that looks like it was saved mid-workflow
        saved_state = WorkflowState(
            workflow_id="wf-resume",
            name="Resumable Workflow",
            status=WorkflowStatus.RUNNING,
            tasks={
                "t1": TaskState(
                    task_id="t1", name="task1", status=TaskStatus.COMPLETED
                ),
                "t2": TaskState(
                    task_id="t2", name="task2", status=TaskStatus.PENDING
                ),
            },
            context={"step1_result": "done"},
        )

        mock_state_manager = AsyncMock()
        mock_state_manager.exists = AsyncMock(return_value=True)
        mock_state_manager.load = AsyncMock(return_value=saved_state)

        engine = WorkflowEngine(
            max_parallel_tasks=5, state_manager=mock_state_manager
        )

        workflow = Workflow(name="Resumable Workflow")

        execution_log = []

        async def task1_func(context):
            execution_log.append("task1")
            return {"step": 1}

        async def task2_func(context):
            execution_log.append("task2")
            return {"step": 2}

        task1 = FunctionTask(name="task1", func=task1_func, task_id="t1")
        task2 = FunctionTask(
            name="task2", func=task2_func, task_id="t2", dependencies=["t1"]
        )

        workflow.add_tasks(task1, task2)

        state = await engine.execute_workflow(
            workflow, workflow_id="wf-resume"
        )

        # Should resume from saved state - task1 already done
        assert "task1" not in execution_log  # Should not re-run
        assert "task2" in execution_log
        assert state.context.get("step1_result") == "done"

    @pytest.mark.asyncio
    async def test_create_workflow_from_config(self, engine):
        """Test creating workflow from configuration."""
        config = {
            "name": "Config Workflow",
            "description": "Created from config",
            "version": "1.0",
            "tasks": [
                {
                    "name": "task1",
                    "type": "function",
                    "function": "test_func",
                    "task_id": "t1",
                    "max_retries": 2,
                }
            ],
        }

        # Should raise because function isn't registered
        with pytest.raises(NotImplementedError):
            engine.create_workflow_from_config(config)


# =============================================================================
# TaskResult and TaskState Tests
# =============================================================================


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_success_result(self):
        """Test successful result."""
        result = TaskResult(
            success=True,
            data={"key": "value"},
            execution_time=1.5,
            retry_count=0,
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["data"] == {"key": "value"}
        assert d["execution_time"] == 1.5
        assert d["retry_count"] == 0
        assert d["error"] is None

    def test_failure_result(self):
        """Test failed result."""
        result = TaskResult(
            success=False,
            error="Something went wrong",
            execution_time=0.5,
            retry_count=2,
            metadata={"traceback": "line 1\nline 2"},
        )

        d = result.to_dict()
        assert d["success"] is False
        assert d["error"] == "Something went wrong"
        assert d["metadata"]["traceback"] == "line 1\nline 2"


class TestTaskState:
    """Tests for TaskState dataclass."""

    def test_task_state_creation(self):
        """Test task state initialization."""
        state = TaskState(
            task_id="task-1",
            name="Test Task",
            status=TaskStatus.RUNNING,
            dependencies=["dep1"],
            retry_count=1,
            max_retries=3,
        )

        assert state.task_id == "task-1"
        assert state.name == "Test Task"
        assert state.status == TaskStatus.RUNNING
        assert state.dependencies == ["dep1"]
        assert state.retry_count == 1

    def test_task_state_to_dict(self):
        """Test task state serialization."""
        result = TaskResult(success=True, data={"key": "value"})

        state = TaskState(
            task_id="task-1",
            name="Test Task",
            status=TaskStatus.COMPLETED,
            result=result,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 1, 0),
            dependencies=["dep1"],
        )

        d = state.to_dict()
        assert d["task_id"] == "task-1"
        assert d["status"] == "COMPLETED"
        assert d["result"]["success"] is True
        assert d["started_at"] == "2024-01-01T12:00:00"
        assert d["completed_at"] == "2024-01-01T12:01:00"


# =============================================================================
# WorkflowState Tests
# =============================================================================


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_workflow_state_creation(self):
        """Test workflow state initialization."""
        state = WorkflowState(
            workflow_id="wf-1",
            name="Test Workflow",
            status=WorkflowStatus.RUNNING,
            context={"key": "value"},
        )

        assert state.workflow_id == "wf-1"
        assert state.name == "Test Workflow"
        assert state.status == WorkflowStatus.RUNNING
        assert state.context == {"key": "value"}
        assert isinstance(state.created_at, datetime)

    def test_workflow_state_to_dict(self):
        """Test workflow state serialization."""
        task_state = TaskState(
            task_id="t1", name="task1", status=TaskStatus.COMPLETED
        )

        state = WorkflowState(
            workflow_id="wf-1",
            name="Test",
            status=WorkflowStatus.COMPLETED,
            tasks={"t1": task_state},
            context={"result": "ok"},
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 5, 0),
            error_message=None,
        )

        d = state.to_dict()
        assert d["workflow_id"] == "wf-1"
        assert d["status"] == "COMPLETED"
        assert "t1" in d["tasks"]
        assert d["context"] == {"result": "ok"}
        assert d["started_at"] == "2024-01-01T12:00:00"
        assert d["completed_at"] == "2024-01-01T12:05:00"


# =============================================================================
# EventBus Tests (Workflow Engine specific)
# =============================================================================


class TestEventBus:
    """Tests for EventBus in workflow engine."""

    @pytest.fixture
    def event_bus(self):
        """Create a test event bus."""
        return EventBus()

    def test_event_bus_initialization(self, event_bus):
        """Test event bus initialization."""
        assert event_bus._listeners == {}

    def test_on_and_off(self, event_bus):
        """Test registering and unregistering listeners."""
        handler1 = Mock()
        handler2 = Mock()

        event_bus.on("event1", handler1)
        event_bus.on("event1", handler2)
        event_bus.on("event2", handler1)

        assert len(event_bus._listeners["event1"]) == 2
        assert len(event_bus._listeners["event2"]) == 1

        event_bus.off("event1", handler1)
        assert len(event_bus._listeners["event1"]) == 1
        assert handler2 in event_bus._listeners["event1"]

    @pytest.mark.asyncio
    async def test_emit_async_handler(self, event_bus):
        """Test emitting to async handlers."""
        handler = AsyncMock()

        event_bus.on("test_event", handler)
        await event_bus.emit("test_event", {"key": "value"})

        handler.assert_called_once_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_emit_sync_handler(self, event_bus):
        """Test emitting to sync handlers."""
        handler = Mock()

        event_bus.on("test_event", handler)
        await event_bus.emit("test_event", {"key": "value"})

        handler.assert_called_once_with({"key": "value"})

    @pytest.mark.asyncio
    async def test_emit_multiple_handlers(self, event_bus):
        """Test emitting to multiple handlers."""
        handler1 = Mock()
        handler2 = AsyncMock()
        handler3 = Mock()

        event_bus.on("test_event", handler1)
        event_bus.on("test_event", handler2)
        event_bus.on("test_event", handler3)

        await event_bus.emit("test_event", "data")

        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_handler_error(self, event_bus):
        """Test that handler errors don't break other handlers."""
        bad_handler = Mock(side_effect=Exception("Handler error"))
        good_handler = Mock()

        event_bus.on("test_event", bad_handler)
        event_bus.on("test_event", good_handler)

        # Should not raise
        await event_bus.emit("test_event", "data")

        bad_handler.assert_called_once()
        good_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_no_listeners(self, event_bus):
        """Test emitting when no listeners registered."""
        # Should not raise
        await event_bus.emit("nonexistent_event", "data")


# =============================================================================
# Task Decorator Tests
# =============================================================================


class TestTaskDecorator:
    """Tests for the @task decorator."""

    def test_decorator_basic(self):
        """Test basic decorator usage."""

        @task()
        def my_task(context):
            return {"result": "ok"}

        assert isinstance(my_task, FunctionTask)
        assert my_task.name == "my_task"
        assert my_task.func.__name__ == "my_task"

    def test_decorator_with_options(self):
        """Test decorator with options."""

        @task(
            name="custom_name",
            dependencies=["dep1"],
            max_retries=5,
            timeout=300,
            save_to_context=True,
            context_key="my_result",
        )
        def my_task(context):
            return {"result": "ok"}

        assert my_task.name == "custom_name"
        assert my_task.dependencies == ["dep1"]
        assert my_task.max_retries == 5
        assert my_task.timeout == 300
        assert my_task.metadata["save_to_context"] is True
        assert my_task.metadata["context_key"] == "my_result"

    def test_decorator_preserves_functionality(self):
        """Test that decorated function still works."""

        @task()
        def add_task(context, x, y):
            return {"sum": x + y}

        # The task is a FunctionTask, but we can still access the original func
        result = add_task.func(None, 2, 3)
        assert result == {"sum": 5}


# =============================================================================
# Integration Tests
# =============================================================================


class TestWorkflowEngineIntegration:
    """Integration tests for the workflow engine."""

    @pytest.mark.asyncio
    async def test_complex_workflow(self):
        """Test a complex workflow with multiple patterns."""
        engine = WorkflowEngine(max_parallel_tasks=10)

        workflow = Workflow(name="Complex Workflow")

        execution_order = []
        context_values = {}

        # Task 1: Initial data loading
        async def load_data(context):
            await asyncio.sleep(0.01)
            execution_order.append("load")
            return {"data": [1, 2, 3, 4, 5]}

        # Task 2A: Process data (parallel with 2B)
        async def process_a(context):
            await asyncio.sleep(0.01)
            execution_order.append("process_a")
            return {"processed": "a"}

        # Task 2B: Process data (parallel with 2A)
        async def process_b(context):
            await asyncio.sleep(0.01)
            execution_order.append("process_b")
            return {"processed": "b"}

        # Task 3: Aggregate (depends on 2A and 2B)
        async def aggregate(context):
            execution_order.append("aggregate")
            context_values.update(context)
            return {"aggregated": True}

        # Task 4: Conditional finalize
        async def finalize(context):
            execution_order.append("finalize")
            return {"final": True}

        def should_finalize(context):
            return context.get("aggregated", False)

        task1 = FunctionTask(
            name="load",
            func=load_data,
            task_id="t1",
            metadata={"save_to_context": True, "context_key": "loaded_data"},
        )
        task2a = FunctionTask(
            name="process_a",
            func=process_a,
            task_id="t2a",
            dependencies=["t1"],
            parallel=True,
        )
        task2b = FunctionTask(
            name="process_b",
            func=process_b,
            task_id="t2b",
            dependencies=["t1"],
            parallel=True,
        )
        task3 = FunctionTask(
            name="aggregate",
            func=aggregate,
            task_id="t3",
            dependencies=["t2a", "t2b"],
            metadata={"save_to_context": True, "context_key": "aggregated"},
        )
        task4 = FunctionTask(
            name="finalize",
            func=finalize,
            task_id="t4",
            dependencies=["t3"],
            condition=should_finalize,
        )

        workflow.add_tasks(task1, task2a, task2b, task3, task4)

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.COMPLETED
        assert execution_order[0] == "load"
        # process_a and process_b can be in any order (parallel)
        assert set(execution_order[1:3]) == {"process_a", "process_b"}
        assert execution_order[3] == "aggregate"
        assert execution_order[4] == "finalize"

    @pytest.mark.asyncio
    async def test_workflow_event_lifecycle(self):
        """Test that all workflow events are fired correctly."""
        engine = WorkflowEngine()

        events = []

        engine.on("workflow.started", lambda e: events.append("started"))
        engine.on("workflow.completed", lambda e: events.append("completed"))
        engine.on(
            "task.started", lambda e: events.append(f"task_started:{e.name}")
        )
        engine.on(
            "task.completed",
            lambda e: events.append(f"task_completed:{e.name}"),
        )

        workflow = Workflow(name="Event Test")

        async def simple_task(context):
            return {}

        task1 = FunctionTask(name="task1", func=simple_task, task_id="t1")
        workflow.add_task(task1)

        await engine.execute_workflow(workflow)

        assert "started" in events
        assert "completed" in events
        assert "task_started:task1" in events
        assert "task_completed:task1" in events

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test workflow with error recovery patterns."""
        engine = WorkflowEngine()

        workflow = Workflow(name="Recovery Workflow")

        attempt_count = 0

        async def flaky_task(context):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise ValueError("First attempt fails")
            if attempt_count == 2:
                raise ValueError("Second attempt fails")
            return {"success": True}

        task1 = FunctionTask(
            name="flaky",
            func=flaky_task,
            task_id="t1",
            max_retries=3,
            retry_delay=0.01,
        )
        workflow.add_task(task1)

        state = await engine.execute_workflow(workflow)

        assert state.status == WorkflowStatus.COMPLETED
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_nested_workflow(self):
        """Test workflow with sub-workflow."""
        engine = WorkflowEngine()

        # Create sub-workflow
        sub_workflow = Workflow(name="Sub Workflow")

        async def sub_task_func(context):
            return {"sub": "result"}

        sub_task = FunctionTask(
            name="sub_task", func=sub_task_func, task_id="st1"
        )
        sub_workflow.add_task(sub_task)

        # Create parent workflow
        parent_workflow = Workflow(name="Parent Workflow")

        with patch("core.workflow_engine.WorkflowEngine") as mock_engine_class:
            mock_sub_engine = MagicMock()
            mock_state = MagicMock()
            mock_state.status = WorkflowStatus.COMPLETED
            mock_state.to_dict.return_value = {
                "status": "completed",
                "sub_result": "ok",
            }
            mock_state.workflow_id = "sub-wf"
            mock_sub_engine.execute_workflow = AsyncMock(
                return_value=mock_state
            )
            mock_engine_class.return_value = mock_sub_engine

            sub_task_wrapper = SubWorkflowTask(
                name="sub", workflow=sub_workflow, task_id="t1"
            )
            parent_workflow.add_task(sub_task_wrapper)

            state = await engine.execute_workflow(parent_workflow)

            assert state.status == WorkflowStatus.COMPLETED
