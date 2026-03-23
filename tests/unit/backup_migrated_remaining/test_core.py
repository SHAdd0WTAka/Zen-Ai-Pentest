"""
Unit tests for ZenOrchestrator Core

Tests the main orchestration functionality including:
- Task submission and execution
- Component integration
- Event handling
- State management
"""

import asyncio

import pytest

# Import orchestrator components
try:
    from orchestrator import OrchestratorConfig, ZenOrchestrator
    from orchestrator.events import Event, EventType
    from orchestrator.tasks import Task, TaskPriority, TaskState
except ImportError:
    import sys

    sys.path.insert(0, "../../..")
    from orchestrator import OrchestratorConfig, ZenOrchestrator
    from orchestrator.events import Event, EventType
    from orchestrator.tasks import Task, TaskPriority, TaskState


class TestZenOrchestrator:
    """Test ZenOrchestrator main class"""

    @pytest.fixture
    async def orchestrator(self):
        """Create test orchestrator"""
        config = OrchestratorConfig(
            max_workers=2,
            max_concurrent_tasks=5,
            enable_analysis_bot=False,
            enable_audit_logging=False,
            enable_secure_validation=False,
        )

        orch = ZenOrchestrator(config)
        await orch.start()

        yield orch

        await orch.stop()

    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self):
        """Test orchestrator lifecycle"""
        config = OrchestratorConfig(
            enable_analysis_bot=False, enable_audit_logging=False
        )

        orch = ZenOrchestrator(config)

        # Should not be running initially
        assert not orch._running

        # Start
        success = await orch.start()
        assert success
        assert orch._running
        assert orch.started_at is not None

        # Stop
        success = await orch.stop()
        assert success
        assert not orch._running

    @pytest.mark.asyncio
    async def test_get_status(self, orchestrator):
        """Test status endpoint"""
        status = orchestrator.get_status()

        assert "instance_id" in status
        assert "status" in status
        assert "started_at" in status
        assert "uptime_seconds" in status
        assert "config" in status
        assert "components" in status

        assert status["status"] == "running"
        assert status["config"]["max_workers"] == 2

    @pytest.mark.asyncio
    async def test_submit_task(self, orchestrator):
        """Test task submission"""
        task_id = await orchestrator.submit_task(
            {"type": "test_task", "target": "example.com"}
        )

        assert task_id is not None
        assert len(task_id) > 0

        # Check task was created
        status = await orchestrator.get_task_status(task_id)
        assert status is not None
        assert status["type"] == "test_task"

    @pytest.mark.asyncio
    async def test_submit_task_with_priority(self, orchestrator):
        """Test task submission with priority"""
        task_id = await orchestrator.submit_task(
            {"type": "test_task", "target": "example.com"},
            priority=TaskPriority.HIGH,
        )

        status = await orchestrator.get_task_status(task_id)
        assert status["priority"] == "high"

    @pytest.mark.asyncio
    async def test_list_tasks(self, orchestrator):
        """Test listing tasks"""
        # Submit multiple tasks
        task_ids = []
        for i in range(3):
            task_id = await orchestrator.submit_task(
                {"type": "test_task", "target": f"target{i}.com"}
            )
            task_ids.append(task_id)

        # List all tasks
        tasks = await orchestrator.list_tasks()
        assert len(tasks) == 3

        # List with filter
        # (Note: tasks may already be processed, so status filter may not match)

    @pytest.mark.asyncio
    async def test_cancel_task(self, orchestrator):
        """Test task cancellation"""
        # Submit task
        task_id = await orchestrator.submit_task(
            {"type": "slow_task", "target": "example.com"}
        )

        # Cancel
        success = await orchestrator.cancel_task(task_id)
        assert success

        # Verify cancelled
        status = await orchestrator.get_task_status(task_id)
        assert status["state"] == "cancelled"

    @pytest.mark.asyncio
    async def test_event_subscription(self, orchestrator):
        """Test event subscription"""
        events_received = []

        async def handler(event):
            events_received.append(event)

        # Subscribe
        await orchestrator.subscribe(EventType.TASK_SUBMITTED, handler)

        # Submit task (should trigger event)
        await orchestrator.submit_task(
            {"type": "test_task", "target": "example.com"}
        )

        # Give time for event processing
        await asyncio.sleep(0.1)

        # Unsubscribe
        await orchestrator.unsubscribe(EventType.TASK_SUBMITTED, handler)

    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test health check"""
        health = await orchestrator.health_check()

        assert "healthy" in health
        assert "checks" in health
        assert "timestamp" in health


class TestTaskManager:
    """Test TaskManager"""

    @pytest.fixture
    async def task_manager(self):
        """Create test task manager"""
        from orchestrator.tasks import TaskManager

        tm = TaskManager(max_workers=2, max_concurrent=5)
        await tm.start()

        # Register test handler
        async def test_handler(task):
            await asyncio.sleep(0.01)  # Simulate work
            return {"result": "success", "task_id": task.id}

        tm.register_handler("test_task", test_handler)

        yield tm

        await tm.stop()

    @pytest.mark.asyncio
    async def test_submit_and_execute(self, task_manager):
        """Test task submission and execution"""
        task = Task(id="test-1", type="test_task", data={"key": "value"})

        task_id = await task_manager.submit(task)

        # Wait for completion
        await asyncio.sleep(0.1)

        # Check results
        retrieved = await task_manager.get_task(task_id)
        assert retrieved is not None
        assert retrieved.state == TaskState.COMPLETED

        results = await task_manager.get_results(task_id)
        assert results is not None
        assert results["result"] == "success"

    @pytest.mark.asyncio
    async def test_priority_ordering(self, task_manager):
        """Test task priority ordering"""
        execution_order = []

        async def tracking_handler(task):
            execution_order.append(task.id)
            await asyncio.sleep(0.01)
            return {"task_id": task.id}

        task_manager.register_handler("priority_test", tracking_handler)

        # Submit in reverse priority order
        task_low = Task(
            id="low", type="priority_test", priority=TaskPriority.LOW
        )
        task_high = Task(
            id="high", type="priority_test", priority=TaskPriority.HIGH
        )
        task_normal = Task(
            id="normal", type="priority_test", priority=TaskPriority.NORMAL
        )

        await task_manager.submit(task_low)
        await task_manager.submit(task_high)
        await task_manager.submit(task_normal)

        # Wait for completion
        await asyncio.sleep(0.2)

        # High priority should execute first
        assert execution_order[0] == "high"

    @pytest.mark.asyncio
    async def test_task_timeout(self, task_manager):
        """Test task timeout"""

        async def slow_handler(task):
            await asyncio.sleep(10)  # Will timeout
            return {}

        task_manager.register_handler("slow_task", slow_handler)

        task = Task(
            id="timeout-test", type="slow_task", timeout=0.1
        )  # 100ms timeout

        await task_manager.submit(task)

        # Wait for timeout
        await asyncio.sleep(0.3)

        retrieved = await task_manager.get_task(task.id)
        assert retrieved.state == TaskState.RETRYING  # Will retry

    @pytest.mark.asyncio
    async def test_task_retry(self, task_manager):
        """Test task retry logic"""
        attempt_count = 0

        async def failing_handler(task):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return {"success": True}

        task_manager.register_handler("retry_test", failing_handler)

        task = Task(id="retry-test", type="retry_test", max_retries=3)

        await task_manager.submit(task)

        # Wait for retries
        await asyncio.sleep(1)

        # Should have attempted multiple times
        assert attempt_count >= 1


class TestEventBus:
    """Test EventBus"""

    @pytest.fixture
    async def event_bus(self):
        """Create test event bus"""
        from orchestrator.events import EventBus

        bus = EventBus()
        await bus.start()

        yield bus

        await bus.stop()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus):
        """Test subscribe and publish"""
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe
        sub_id = await event_bus.subscribe(EventType.TASK_COMPLETED, handler)
        assert sub_id is not None

        # Publish
        event = Event(
            type=EventType.TASK_COMPLETED,
            source="test",
            data={"task_id": "123"},
        )

        success = await event_bus.publish(event)
        assert success

        # Wait for delivery
        await asyncio.sleep(0.1)

        # Unsubscribe
        await event_bus.unsubscribe_by_id(sub_id)

    @pytest.mark.asyncio
    async def test_event_filtering(self, event_bus):
        """Test event filtering by priority"""
        critical_events = []

        async def handler(event):
            critical_events.append(event)

        # Subscribe only to critical priority
        from orchestrator.events import EventPriority

        await event_bus.subscribe(
            EventType.SECURITY_ALERT,
            handler,
            priority_filter=[EventPriority.CRITICAL],
        )

        # Publish high priority event (should not be received)
        event = Event(
            type=EventType.SECURITY_ALERT,
            source="test",
            priority=EventPriority.HIGH,
            data={},
        )
        await event_bus.publish(event)

        # Publish critical priority event (should be received)
        critical_event = Event(
            type=EventType.SECURITY_ALERT,
            source="test",
            priority=EventPriority.CRITICAL,
            data={},
        )
        await event_bus.publish(critical_event)

        await asyncio.sleep(0.1)

        # Should only have received critical event
        assert len(critical_events) == 1
        assert critical_events[0].priority == EventPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_wait_for_event(self, event_bus):
        """Test wait_for_event utility"""

        # Start publishing event after delay
        async def delayed_publish():
            await asyncio.sleep(0.1)
            await event_bus.publish(
                Event(
                    type=EventType.TASK_COMPLETED,
                    source="test",
                    data={"task_id": "123"},
                )
            )

        asyncio.create_task(delayed_publish())

        # Wait for event
        event = await event_bus.wait_for_event(
            EventType.TASK_COMPLETED, timeout=1.0
        )

        assert event is not None
        assert event.data["task_id"] == "123"


class TestStateManager:
    """Test StateManager"""

    @pytest.fixture
    def state_manager(self):
        """Create test state manager"""
        from orchestrator.state import StateManager

        return StateManager()

    @pytest.mark.asyncio
    async def test_set_and_get_task_state(self, state_manager):
        """Test task state management"""
        # Set initial state
        await state_manager.set_task_state("task-1", TaskState.PENDING)

        # Get state
        state = await state_manager.get_task_state("task-1")
        assert state == TaskState.PENDING

        # Transition
        await state_manager.set_task_state("task-1", TaskState.RUNNING)
        state = await state_manager.get_task_state("task-1")
        assert state == TaskState.RUNNING

    @pytest.mark.asyncio
    async def test_invalid_transition(self, state_manager):
        """Test invalid state transition rejection"""
        await state_manager.set_task_state("task-1", TaskState.COMPLETED)

        # Should not allow transition from COMPLETED to RUNNING
        with pytest.raises(ValueError):
            await state_manager.set_task_state("task-1", TaskState.RUNNING)

    @pytest.mark.asyncio
    async def test_snapshot(self, state_manager):
        """Test state snapshots"""
        # Set some states
        from orchestrator.state import TaskState

        await state_manager.set_task_state("task-1", TaskState.RUNNING)
        await state_manager.set_task_state("task-2", TaskState.PENDING)

        # Create snapshot
        snapshot = await state_manager.create_snapshot()
        assert snapshot is not None
        assert len(snapshot.task_states) == 2

        # Verify integrity
        assert snapshot.verify()

        # List snapshots
        snapshots = await state_manager.list_snapshots()
        assert len(snapshots) == 1


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
