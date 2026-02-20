"""
Comprehensive tests for the ZenOrchestrator system.

Tests cover:
- ZenOrchestrator class (orchestrator/core.py)
- StateManager (orchestrator/state.py)
- EventBus (orchestrator/events.py)
- TaskManager (orchestrator/tasks.py)
"""

import asyncio
import json
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import orchestrator components
from orchestrator.core import OrchestratorConfig, OrchestratorStatus, ZenOrchestrator
from orchestrator.events import Event, EventBus, EventPriority, EventStream, EventType, Subscription
from orchestrator.state import StateManager, StateSnapshot, SystemState, TaskState
from orchestrator.tasks import Task, TaskManager, TaskPriority, TaskState as TaskManagerState


# =============================================================================
# ZenOrchestrator Tests
# =============================================================================


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OrchestratorConfig.default()
        assert config.max_concurrent_tasks == 10
        assert config.max_workers == 4
        assert config.task_timeout == 3600
        assert config.enable_analysis_bot is True
        assert config.enable_audit_logging is True
        assert config.auto_recover is True

    def test_production_config(self):
        """Test production configuration preset."""
        config = OrchestratorConfig.production()
        assert config.max_concurrent_tasks == 50
        assert config.max_workers == 8
        assert config.enable_audit_logging is True
        assert config.health_check_interval == 10

    def test_development_config(self):
        """Test development configuration preset."""
        config = OrchestratorConfig.development()
        assert config.max_concurrent_tasks == 5
        assert config.max_workers == 2
        assert config.task_timeout == 600


class TestZenOrchestrator:
    """Tests for ZenOrchestrator main class."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator instance."""
        config = OrchestratorConfig.default()
        config.enable_analysis_bot = False
        config.enable_audit_logging = False
        config.enable_secure_validation = False
        return ZenOrchestrator(config)

    @pytest.fixture
    def running_orchestrator(self):
        """Create and start a test orchestrator."""
        config = OrchestratorConfig.default()
        config.enable_analysis_bot = False
        config.enable_audit_logging = False
        config.enable_secure_validation = False
        config.health_check_interval = 0  # Disable health checks for tests
        config.metrics_enabled = False
        orch = ZenOrchestrator(config)
        return orch

    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator.status == OrchestratorStatus.INITIALIZING
        assert orchestrator.instance_id is not None
        assert orchestrator.config is not None
        assert orchestrator.state_manager is not None
        assert orchestrator.event_bus is not None
        assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_start_stop(self, running_orchestrator):
        """Test starting and stopping the orchestrator."""
        orchestrator = running_orchestrator

        # Mock task manager to avoid actual task execution
        with patch.object(orchestrator, '_initialize_components'):
            with patch.object(orchestrator, '_register_event_handlers'):
                with patch('orchestrator.core.TaskManager') as mock_tm_class:
                    mock_tm = AsyncMock()
                    mock_tm_class.return_value = mock_tm

                    # Start
                    result = await orchestrator.start()
                    assert result is True
                    assert orchestrator._running is True
                    assert orchestrator.status == OrchestratorStatus.RUNNING
                    assert orchestrator.started_at is not None
                    mock_tm.start.assert_called_once()

                    # Stop
                    stop_result = await orchestrator.stop()
                    assert stop_result is True
                    assert orchestrator._running is False

    @pytest.mark.asyncio
    async def test_submit_task(self, running_orchestrator):
        """Test submitting a task to the orchestrator."""
        orchestrator = running_orchestrator

        with patch.object(orchestrator, '_log_event', new_callable=AsyncMock):
            with patch.object(orchestrator.event_bus, 'publish', new_callable=AsyncMock):
                with patch('orchestrator.core.TaskManager') as mock_tm_class:
                    mock_tm = AsyncMock()
                    mock_tm.submit = AsyncMock(return_value="task-123")
                    mock_tm_class.return_value = mock_tm

                    # Start first
                    await orchestrator.start()

                    # Submit task
                    task_data = {"type": "vulnerability_scan", "target": "example.com"}
                    task_id = await orchestrator.submit_task(task_data, priority=TaskPriority.HIGH)

                    assert task_id == "task-123"
                    mock_tm.submit.assert_called_once()

                    await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_submit_task_with_validation(self):
        """Test task submission with input validation."""
        config = OrchestratorConfig.default()
        config.enable_secure_validation = True
        orchestrator = ZenOrchestrator(config)

        # Create a mock validator
        mock_validator = MagicMock()
        mock_validator.validate_url = Mock(return_value=True)
        orchestrator.validator = mock_validator

        with patch.object(orchestrator, '_log_event', new_callable=AsyncMock):
            with patch.object(orchestrator.event_bus, 'publish', new_callable=AsyncMock):
                with patch('orchestrator.core.TaskManager') as mock_tm_class:
                    mock_tm = AsyncMock()
                    mock_tm.submit = AsyncMock(return_value="task-456")
                    mock_tm_class.return_value = mock_tm

                    await orchestrator.start()

                    task_data = {"type": "scan", "target": "https://example.com"}
                    task_id = await orchestrator.submit_task(task_data)

                    assert task_id == "task-456"
                    mock_validator.validate_url.assert_called_once_with("https://example.com")

                    await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_cancel_task(self, running_orchestrator):
        """Test cancelling a task."""
        orchestrator = running_orchestrator

        with patch('orchestrator.core.TaskManager') as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.cancel = AsyncMock(return_value=True)
            mock_tm_class.return_value = mock_tm

            await orchestrator.start()

            result = await orchestrator.cancel_task("task-123")
            assert result is True
            mock_tm.cancel.assert_called_once_with("task-123")

            await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_get_task_status(self, running_orchestrator):
        """Test getting task status."""
        orchestrator = running_orchestrator

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.type = "scan"
        mock_task.state = TaskManagerState.RUNNING
        mock_task.priority = TaskPriority.NORMAL
        mock_task.created_at = datetime.utcnow()
        mock_task.started_at = None
        mock_task.completed_at = None
        mock_task.progress = 50.0
        mock_task.error = None

        with patch('orchestrator.core.TaskManager') as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.get_task = AsyncMock(return_value=mock_task)
            mock_tm_class.return_value = mock_tm

            await orchestrator.start()

            status = await orchestrator.get_task_status("task-123")

            assert status is not None
            assert status["id"] == "task-123"
            assert status["type"] == "scan"
            assert status["state"] == "running"
            assert status["progress"] == 50.0

            await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_list_tasks(self, running_orchestrator):
        """Test listing tasks with filtering."""
        orchestrator = running_orchestrator

        mock_tasks = [
            MagicMock(
                id="task-1",
                type="scan",
                state=TaskManagerState.COMPLETED,
                priority=TaskPriority.HIGH,
                created_at=datetime.utcnow(),
            ),
            MagicMock(
                id="task-2",
                type="scan",
                state=TaskManagerState.RUNNING,
                priority=TaskPriority.NORMAL,
                created_at=datetime.utcnow(),
            ),
        ]

        with patch('orchestrator.core.TaskManager') as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.list_tasks = AsyncMock(return_value=mock_tasks)
            mock_tm_class.return_value = mock_tm

            await orchestrator.start()

            # List all tasks
            tasks = await orchestrator.list_tasks()
            assert len(tasks) == 2

            # List with filter
            tasks = await orchestrator.list_tasks(status="running")
            mock_tm.list_tasks.assert_called_with(status="running", task_type=None, limit=100)

            await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_event_subscription(self, running_orchestrator):
        """Test event subscription and unsubscription."""
        orchestrator = running_orchestrator

        mock_handler = AsyncMock()

        await orchestrator.subscribe(EventType.TASK_COMPLETED, mock_handler)
        orchestrator.event_bus.subscribe.assert_called_once_with(EventType.TASK_COMPLETED, mock_handler)

        await orchestrator.unsubscribe(EventType.TASK_COMPLETED, mock_handler)
        orchestrator.event_bus.unsubscribe.assert_called_once_with(EventType.TASK_COMPLETED, mock_handler)

    @pytest.mark.asyncio
    async def test_emit_custom_event(self, running_orchestrator):
        """Test emitting custom events."""
        orchestrator = running_orchestrator

        with patch.object(orchestrator.event_bus, 'publish', new_callable=AsyncMock) as mock_publish:
            await orchestrator.emit_event("custom_event", {"key": "value"})

            mock_publish.assert_called_once()
            event_arg = mock_publish.call_args[0][0]
            assert event_arg.type == EventType.CUSTOM
            assert event_arg.data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_analyze_results(self, running_orchestrator):
        """Test analysis bot integration."""
        orchestrator = running_orchestrator

        # No analysis bot configured
        result = await orchestrator.analyze_results({"findings": []}, "vulnerability")
        assert "error" in result

        # With analysis bot
        mock_bot = MagicMock()
        mock_bot.analyze = Mock(return_value={"summary": "test analysis"})
        orchestrator.analysis_bot = mock_bot

        result = await orchestrator.analyze_results({"findings": [1, 2, 3]}, "vulnerability")
        assert result["summary"] == "test analysis"

    @pytest.mark.asyncio
    async def test_get_status(self, running_orchestrator):
        """Test getting orchestrator status."""
        orchestrator = running_orchestrator

        status = orchestrator.get_status()

        assert "instance_id" in status
        assert "status" in status
        assert "config" in status
        assert "components" in status
        assert status["instance_id"] == orchestrator.instance_id

    @pytest.mark.asyncio
    async def test_health_check(self, running_orchestrator):
        """Test health check functionality."""
        orchestrator = running_orchestrator

        with patch('orchestrator.core.TaskManager') as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.health_check = AsyncMock(return_value=True)
            mock_tm_class.return_value = mock_tm

            await orchestrator.start()

            health = await orchestrator.health_check()

            assert "healthy" in health
            assert "checks" in health
            assert "timestamp" in health

            await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_internal_event_handlers(self, running_orchestrator):
        """Test internal event handlers."""
        orchestrator = running_orchestrator

        with patch.object(orchestrator, '_log_event', new_callable=AsyncMock) as mock_log:
            # Test task completed handler
            event = Event(
                type=EventType.TASK_COMPLETED,
                source="test",
                data={"task_id": "task-123", "auto_analyze": False}
            )
            await orchestrator._on_task_completed(event)
            mock_log.assert_called()

            # Test task failed handler
            event = Event(
                type=EventType.TASK_FAILED,
                source="test",
                data={"task_id": "task-456", "error": "Test error"}
            )
            await orchestrator._on_task_failed(event)

            # Test security alert handler
            event = Event(
                type=EventType.SECURITY_ALERT,
                source="test",
                data={"alert_type": "test_alert", "details": {}}
            )
            await orchestrator._on_security_alert(event)


# =============================================================================
# StateManager Tests
# =============================================================================


class TestStateManager:
    """Tests for StateManager class."""

    @pytest.fixture
    def state_manager(self):
        """Create a test state manager."""
        return StateManager(persistence_enabled=False)

    @pytest.mark.asyncio
    async def test_set_and_get_task_state(self, state_manager):
        """Test setting and getting task state."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        state = await state_manager.get_task_state("task-1")
        assert state == TaskState.PENDING

        await state_manager.set_task_state("task-1", TaskState.RUNNING)
        state = await state_manager.get_task_state("task-1")
        assert state == TaskState.RUNNING

    @pytest.mark.asyncio
    async def test_invalid_state_transition(self, state_manager):
        """Test that invalid state transitions raise errors."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)

        # Valid: PENDING -> QUEUED
        await state_manager.set_task_state("task-1", TaskState.QUEUED)

        # Invalid: QUEUED -> COMPLETED (must go through RUNNING)
        with pytest.raises(ValueError, match="Invalid state transition"):
            await state_manager.set_task_state("task-1", TaskState.COMPLETED)

    @pytest.mark.asyncio
    async def test_force_state_transition(self, state_manager):
        """Test forced state transitions."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_task_state("task-1", TaskState.QUEUED)

        # Force invalid transition
        result = await state_manager.set_task_state("task-1", TaskState.COMPLETED, force=True)
        assert result is True

        state = await state_manager.get_task_state("task-1")
        assert state == TaskState.COMPLETED

    @pytest.mark.asyncio
    async def test_task_data_management(self, state_manager):
        """Test task data storage and retrieval."""
        await state_manager.update_task_data("task-1", {"target": "example.com", "scan_type": "full"})

        data = await state_manager.get_task_data("task-1")
        assert data["target"] == "example.com"
        assert data["scan_type"] == "full"
        assert "last_updated" in data

        # Test merge
        await state_manager.update_task_data("task-1", {"progress": 50})
        data = await state_manager.get_task_data("task-1")
        assert data["target"] == "example.com"  # Still there
        assert data["progress"] == 50

        # Test non-merge (replace)
        await state_manager.update_task_data("task-1", {"new_key": "value"}, merge=False)
        data = await state_manager.get_task_data("task-1")
        assert "target" not in data  # Replaced
        assert data["new_key"] == "value"

    @pytest.mark.asyncio
    async def test_get_all_task_states(self, state_manager):
        """Test getting all task states."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_task_state("task-2", TaskState.RUNNING)
        await state_manager.set_task_state("task-3", TaskState.COMPLETED)

        all_states = await state_manager.get_all_task_states()
        assert len(all_states) == 3
        assert all_states["task-1"] == TaskState.PENDING
        assert all_states["task-2"] == TaskState.RUNNING
        assert all_states["task-3"] == TaskState.COMPLETED

    @pytest.mark.asyncio
    async def test_get_tasks_by_state(self, state_manager):
        """Test filtering tasks by state."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_task_state("task-2", TaskState.PENDING)
        await state_manager.set_task_state("task-3", TaskState.RUNNING)

        pending = await state_manager.get_tasks_by_state(TaskState.PENDING)
        assert len(pending) == 2
        assert "task-1" in pending
        assert "task-2" in pending

        running = await state_manager.get_tasks_by_state(TaskState.RUNNING)
        assert len(running) == 1
        assert "task-3" in running

    @pytest.mark.asyncio
    async def test_remove_task(self, state_manager):
        """Test removing a task."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.update_task_data("task-1", {"target": "test.com"})

        result = await state_manager.remove_task("task-1")
        assert result is True

        state = await state_manager.get_task_state("task-1")
        assert state is None

        data = await state_manager.get_task_data("task-1")
        assert data is None

        # Removing non-existent task
        result = await state_manager.remove_task("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_system_state(self, state_manager):
        """Test system state management."""
        await state_manager.set_system_state(SystemState.ACTIVE, {"version": "1.0"})

        state = await state_manager.get_system_state()
        assert state == SystemState.ACTIVE

        metadata = await state_manager.get_system_metadata()
        assert metadata["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_state_history(self, state_manager):
        """Test state change history."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_task_state("task-1", TaskState.QUEUED)
        await state_manager.set_task_state("task-1", TaskState.RUNNING)

        history = await state_manager.get_state_history("task-1")
        assert len(history) == 3

        # All history
        all_history = await state_manager.get_state_history()
        assert len(all_history) == 3

    @pytest.mark.asyncio
    async def test_snapshot_creation_and_restore(self, state_manager):
        """Test snapshot creation and restoration."""
        await state_manager.set_task_state("task-1", TaskState.RUNNING)
        await state_manager.set_task_state("task-2", TaskState.PENDING)
        await state_manager.set_system_state(SystemState.ACTIVE)

        # Create snapshot
        snapshot = await state_manager.create_snapshot()
        assert snapshot.id.startswith("snap-")
        assert "task-1" in snapshot.task_states
        assert snapshot.system_state == "active"
        assert snapshot.verify() is True

        # Modify state
        await state_manager.set_task_state("task-1", TaskState.COMPLETED)
        await state_manager.set_system_state(SystemState.DEGRADED)

        # Restore snapshot
        result = await state_manager.restore_snapshot(snapshot.id)
        assert result is True

        state = await state_manager.get_task_state("task-1")
        assert state == TaskState.RUNNING

        system_state = await state_manager.get_system_state()
        assert system_state == SystemState.ACTIVE

    @pytest.mark.asyncio
    async def test_list_snapshots(self, state_manager):
        """Test listing snapshots."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.create_snapshot()
        await state_manager.create_snapshot()

        snapshots = await state_manager.list_snapshots()
        assert len(snapshots) == 2

    @pytest.mark.asyncio
    async def test_statistics(self, state_manager):
        """Test statistics collection."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_task_state("task-2", TaskState.RUNNING)
        await state_manager.set_task_state("task-3", TaskState.COMPLETED)

        stats = await state_manager.get_statistics()
        assert stats["total_tasks"] == 3
        assert stats["state_counts"]["pending"] == 1
        assert stats["state_counts"]["running"] == 1
        assert stats["state_counts"]["completed"] == 1
        assert stats["state_changes"] == 3

    @pytest.mark.asyncio
    async def test_persistence(self, state_manager):
        """Test save/load to file."""
        await state_manager.set_task_state("task-1", TaskState.RUNNING)
        await state_manager.update_task_data("task-1", {"target": "test.com"})
        await state_manager.set_system_state(SystemState.ACTIVE, {"version": "1.0"})

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            # Save
            result = await state_manager.save_to_file(filepath)
            assert result is True

            # Clear state
            await state_manager.clear()

            # Load
            result = await state_manager.load_from_file(filepath)
            assert result is True

            # Verify
            state = await state_manager.get_task_state("task-1")
            assert state == TaskState.RUNNING

            system_state = await state_manager.get_system_state()
            assert system_state == SystemState.ACTIVE
        finally:
            import os
            os.unlink(filepath)

    @pytest.mark.asyncio
    async def test_clear(self, state_manager):
        """Test clearing all state."""
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_system_state(SystemState.ACTIVE)

        await state_manager.clear()

        all_states = await state_manager.get_all_task_states()
        assert len(all_states) == 0

        system_state = await state_manager.get_system_state()
        assert system_state == SystemState.INITIALIZING


class TestStateSnapshot:
    """Tests for StateSnapshot class."""

    def test_snapshot_creation(self):
        """Test snapshot creation and checksum."""
        snapshot = StateSnapshot(
            id="snap-1",
            timestamp=datetime.utcnow(),
            task_states={"task-1": "pending", "task-2": "running"},
            system_state="active",
            metadata={"version": "1.0"},
        )

        assert snapshot.checksum != ""
        assert snapshot.verify() is True

    def test_snapshot_tampering_detection(self):
        """Test that tampered snapshots fail verification."""
        snapshot = StateSnapshot(
            id="snap-1",
            timestamp=datetime.utcnow(),
            task_states={"task-1": "pending"},
            system_state="active",
            metadata={},
        )

        # Tamper with data
        snapshot.task_states["task-1"] = "completed"

        assert snapshot.verify() is False


# =============================================================================
# EventBus Tests
# =============================================================================


class TestEventBus:
    """Tests for EventBus class."""

    @pytest.fixture
    async def event_bus(self):
        """Create and start a test event bus."""
        bus = EventBus(max_queue_size=100, history_size=50)
        await bus.start()
        yield bus
        await bus.stop()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test event bus lifecycle."""
        bus = EventBus()
        assert bus.is_running is False

        await bus.start()
        assert bus.is_running is True

        await bus.stop()
        assert bus.is_running is False

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus):
        """Test event subscription and publishing."""
        handler = AsyncMock()

        sub_id = await event_bus.subscribe(EventType.TASK_COMPLETED, handler)
        assert sub_id.startswith("sub-")

        event = Event(type=EventType.TASK_COMPLETED, source="test", data={"task_id": "123"})
        await event_bus.publish(event)

        # Wait for processing
        await asyncio.sleep(0.1)

        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.TASK_COMPLETED
        assert call_args.data["task_id"] == "123"

    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus):
        """Test unsubscribing from events."""
        handler = AsyncMock()

        await event_bus.subscribe(EventType.TASK_COMPLETED, handler)
        result = await event_bus.unsubscribe(EventType.TASK_COMPLETED, handler)
        assert result is True

        # Publish after unsubscribe
        event = Event(type=EventType.TASK_COMPLETED, source="test", data={})
        await event_bus.publish(event)
        await asyncio.sleep(0.1)

        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_unsubscribe_by_id(self, event_bus):
        """Test unsubscribing by subscription ID."""
        handler = AsyncMock()

        sub_id = await event_bus.subscribe(EventType.TASK_COMPLETED, handler)
        result = await event_bus.unsubscribe_by_id(sub_id)
        assert result is True

        # Non-existent subscription
        result = await event_bus.unsubscribe_by_id("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_filtering(self, event_bus):
        """Test event filtering by priority and source."""
        high_priority_handler = AsyncMock()
        source_filtered_handler = AsyncMock()

        await event_bus.subscribe(
            EventType.TASK_COMPLETED,
            high_priority_handler,
            priority_filter=[EventPriority.HIGH, EventPriority.CRITICAL]
        )

        await event_bus.subscribe(
            EventType.TASK_COMPLETED,
            source_filtered_handler,
            source_filter=["worker-1"]
        )

        # High priority event
        event1 = Event(
            type=EventType.TASK_COMPLETED,
            source="test",
            data={},
            priority=EventPriority.HIGH
        )
        await event_bus.publish(event1)

        # Normal priority event
        event2 = Event(
            type=EventType.TASK_COMPLETED,
            source="test",
            data={},
            priority=EventPriority.NORMAL
        )
        await event_bus.publish(event2)

        # From worker-1
        event3 = Event(
            type=EventType.TASK_COMPLETED,
            source="worker-1",
            data={}
        )
        await event_bus.publish(event3)

        await asyncio.sleep(0.1)

        high_priority_handler.assert_called_once()
        source_filtered_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_immediate(self, event_bus):
        """Test immediate publishing (bypasses queue)."""
        handler = AsyncMock()

        await event_bus.subscribe(EventType.TASK_COMPLETED, handler)

        event = Event(type=EventType.TASK_COMPLETED, source="test", data={})
        await event_bus.publish_immediate(event)

        # Should be immediate, no sleep needed
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history(self, event_bus):
        """Test event history."""
        # Publish some events
        for i in range(5):
            event = Event(
                type=EventType.TASK_COMPLETED,
                source=f"source-{i}",
                data={"index": i}
            )
            await event_bus.publish(event)

        await asyncio.sleep(0.1)

        # Get all history
        history = await event_bus.get_history()
        assert len(history) == 5

        # Filter by type
        filtered = await event_bus.get_history(event_type=EventType.TASK_COMPLETED)
        assert len(filtered) == 5

        # Filter by source
        filtered = await event_bus.get_history(source="source-1")
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_clear_history(self, event_bus):
        """Test clearing event history."""
        event = Event(type=EventType.TASK_COMPLETED, source="test", data={})
        await event_bus.publish(event)
        await asyncio.sleep(0.1)

        await event_bus.clear_history()

        history = await event_bus.get_history()
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_statistics(self, event_bus):
        """Test event bus statistics."""
        stats = await event_bus.get_statistics()
        assert "published" in stats
        assert "delivered" in stats
        assert "dropped" in stats
        assert "queue_size" in stats
        assert "history_size" in stats
        assert "subscriptions" in stats

    @pytest.mark.asyncio
    async def test_wait_for_event(self, event_bus):
        """Test waiting for specific events."""
        async def publish_delayed():
            await asyncio.sleep(0.05)
            event = Event(
                type=EventType.TASK_COMPLETED,
                source="test",
                data={"task_id": "123"}
            )
            await event_bus.publish(event)

        asyncio.create_task(publish_delayed())

        event = await event_bus.wait_for_event(EventType.TASK_COMPLETED, timeout=1.0)
        assert event is not None
        assert event.data["task_id"] == "123"

    @pytest.mark.asyncio
    async def test_wait_for_event_with_predicate(self, event_bus):
        """Test waiting for event with predicate filter."""
        async def publish_events():
            await asyncio.sleep(0.01)
            await event_bus.publish(Event(
                type=EventType.TASK_COMPLETED,
                source="test",
                data={"task_id": "111"}
            ))
            await asyncio.sleep(0.01)
            await event_bus.publish(Event(
                type=EventType.TASK_COMPLETED,
                source="test",
                data={"task_id": "222"}
            ))

        asyncio.create_task(publish_events())

        event = await event_bus.wait_for_event(
            EventType.TASK_COMPLETED,
            timeout=1.0,
            predicate=lambda e: e.data.get("task_id") == "222"
        )

        assert event is not None
        assert event.data["task_id"] == "222"

    @pytest.mark.asyncio
    async def test_wait_for_event_timeout(self, event_bus):
        """Test wait_for_event timeout."""
        event = await event_bus.wait_for_event(EventType.TASK_COMPLETED, timeout=0.01)
        assert event is None

    @pytest.mark.asyncio
    async def test_sync_handler(self, event_bus):
        """Test that sync handlers work too."""
        sync_handler = Mock()

        await event_bus.subscribe(EventType.TASK_COMPLETED, sync_handler)

        event = Event(type=EventType.TASK_COMPLETED, source="test", data={})
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        sync_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_to_dict(self):
        """Test Event serialization."""
        event = Event(
            type=EventType.TASK_COMPLETED,
            source="test",
            data={"key": "value"},
            priority=EventPriority.HIGH,
            correlation_id="corr-123"
        )

        d = event.to_dict()
        assert d["type"] == "task.completed"
        assert d["source"] == "test"
        assert d["data"] == {"key": "value"}
        assert d["priority"] == 1
        assert d["correlation_id"] == "corr-123"


class TestEventStream:
    """Tests for EventStream class."""

    @pytest.mark.asyncio
    async def test_event_stream_iteration(self):
        """Test async iteration over events."""
        bus = EventBus()
        await bus.start()

        stream = EventStream(bus, [EventType.TASK_COMPLETED])
        await stream.start()

        # Publish some events
        async def publish_events():
            for i in range(3):
                await bus.publish(Event(
                    type=EventType.TASK_COMPLETED,
                    source="test",
                    data={"index": i}
                ))
            await stream.stop()

        asyncio.create_task(publish_events())

        events = []
        async for event in stream:
            events.append(event)

        assert len(events) == 3

        await bus.stop()

    @pytest.mark.asyncio
    async def test_event_stream_stop(self):
        """Test stopping event stream."""
        bus = EventBus()
        await bus.start()

        stream = EventStream(bus, [EventType.TASK_COMPLETED])
        await stream.start()

        # Stop immediately
        await stream.stop()

        # Iterator should stop
        with pytest.raises(StopAsyncIteration):
            await stream.__anext__()

        await bus.stop()


# =============================================================================
# TaskManager Tests
# =============================================================================


class TestTaskManager:
    """Tests for TaskManager class."""

    @pytest.fixture
    async def task_manager(self):
        """Create and start a test task manager."""
        tm = TaskManager(max_workers=2, max_concurrent=5)
        await tm.start()
        yield tm
        await tm.stop()

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test task manager lifecycle."""
        tm = TaskManager(max_workers=2)

        await tm.start()
        assert tm._running is True
        assert len(tm._workers) == 2

        await tm.stop()
        assert tm._running is False
        assert len(tm._workers) == 0

    @pytest.mark.asyncio
    async def test_submit_task(self, task_manager):
        """Test submitting a task."""
        task = Task(
            id="task-1",
            type="test_task",
            data={"key": "value"},
            priority=TaskPriority.NORMAL
        )

        # Register handler
        async def handler(t):
            return {"result": "success"}

        task_manager.register_handler("test_task", handler)

        task_id = await task_manager.submit(task)
        assert task_id == "task-1"

        # Wait for completion
        await asyncio.sleep(0.1)

        # Check task state
        completed_task = await task_manager.get_task("task-1")
        assert completed_task.state == TaskManagerState.COMPLETED

    @pytest.mark.asyncio
    async def test_task_execution_result(self, task_manager):
        """Test that task results are stored."""
        task = Task(
            id="task-1",
            type="test_task",
            data={"input": "test"}
        )

        async def handler(t):
            return {"output": f"processed_{t.data['input']}"}

        task_manager.register_handler("test_task", handler)
        await task_manager.submit(task)

        await asyncio.sleep(0.1)

        result = await task_manager.get_results("task-1")
        assert result["output"] == "processed_test"

    @pytest.mark.asyncio
    async def test_task_priority_ordering(self, task_manager):
        """Test that high priority tasks execute first."""
        execution_order = []

        async def handler(t):
            execution_order.append(t.id)
            return {}

        task_manager.register_handler("test_task", handler)

        # Submit low priority first
        await task_manager.submit(Task(
            id="low",
            type="test_task",
            priority=TaskPriority.LOW
        ))

        # Then high priority
        await task_manager.submit(Task(
            id="high",
            type="test_task",
            priority=TaskPriority.HIGH
        ))

        # And critical
        await task_manager.submit(Task(
            id="critical",
            type="test_task",
            priority=TaskPriority.CRITICAL
        ))

        await asyncio.sleep(0.2)

        # Should execute in priority order
        assert execution_order[0] == "critical"
        assert execution_order[1] == "high"
        assert execution_order[2] == "low"

    @pytest.mark.asyncio
    async def test_task_timeout(self, task_manager):
        """Test task timeout handling."""
        task = Task(
            id="task-1",
            type="slow_task",
            timeout=0.1  # 100ms timeout
        )

        async def slow_handler(t):
            await asyncio.sleep(1.0)  # Too slow
            return {}

        task_manager.register_handler("slow_task", slow_handler)
        await task_manager.submit(task)

        await asyncio.sleep(0.2)

        completed_task = await task_manager.get_task("task-1")
        assert completed_task.state == TaskManagerState.TIMEOUT
        assert "timed out" in completed_task.error.lower()

    @pytest.mark.asyncio
    async def test_task_retry(self, task_manager):
        """Test task retry logic."""
        attempts = 0

        async def failing_handler(t):
            nonlocal attempts
            attempts += 1
            raise Exception("Simulated failure")

        task = Task(
            id="task-1",
            type="failing_task",
            max_retries=2
        )

        task_manager.register_handler("failing_task", failing_handler)
        await task_manager.submit(task)

        await asyncio.sleep(0.5)  # Wait for retries

        assert attempts == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_cancel_task(self, task_manager):
        """Test task cancellation."""
        task = Task(
            id="task-1",
            type="slow_task"
        )

        async def slow_handler(t):
            await asyncio.sleep(10.0)
            return {}

        task_manager.register_handler("slow_task", slow_handler)
        await task_manager.submit(task)

        await asyncio.sleep(0.05)

        result = await task_manager.cancel("task-1")
        assert result is True

        cancelled_task = await task_manager.get_task("task-1")
        assert cancelled_task.state == TaskManagerState.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, task_manager):
        """Test cancelling non-existent task."""
        result = await task_manager.cancel("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_no_handler_error(self, task_manager):
        """Test error when no handler registered."""
        task = Task(
            id="task-1",
            type="unknown_task"
        )

        await task_manager.submit(task)
        await asyncio.sleep(0.1)

        completed_task = await task_manager.get_task("task-1")
        assert completed_task.state == TaskManagerState.FAILED
        assert "No handler" in completed_task.error

    @pytest.mark.asyncio
    async def test_register_unregister_handler(self, task_manager):
        """Test handler registration and unregistration."""
        async def handler(t):
            return {}

        task_manager.register_handler("test_type", handler)
        assert "test_type" in task_manager._handlers

        result = task_manager.unregister_handler("test_type")
        assert result is True
        assert "test_type" not in task_manager._handlers

        # Unregister non-existent
        result = task_manager.unregister_handler("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_tasks(self, task_manager):
        """Test listing tasks with filtering."""
        # Create tasks in different states
        task1 = Task(id="task-1", type="scan", state=TaskManagerState.COMPLETED)
        task2 = Task(id="task-2", type="scan", state=TaskManagerState.RUNNING)
        task3 = Task(id="task-3", type="report", state=TaskManagerState.PENDING)

        task_manager._tasks["task-1"] = task1
        task_manager._tasks["task-2"] = task2
        task_manager._tasks["task-3"] = task3

        # List all
        all_tasks = await task_manager.list_tasks()
        assert len(all_tasks) == 3

        # Filter by status
        running = await task_manager.list_tasks(status="running")
        assert len(running) == 1
        assert running[0].id == "task-2"

        # Filter by type
        scans = await task_manager.list_tasks(task_type="scan")
        assert len(scans) == 2

    @pytest.mark.asyncio
    async def test_cleanup_old_tasks(self, task_manager):
        """Test cleaning up old completed tasks."""
        from datetime import timedelta

        old_task = Task(
            id="old-task",
            type="scan",
            state=TaskManagerState.COMPLETED,
            completed_at=datetime.utcnow() - timedelta(hours=48)
        )

        recent_task = Task(
            id="recent-task",
            type="scan",
            state=TaskManagerState.COMPLETED,
            completed_at=datetime.utcnow() - timedelta(hours=1)
        )

        task_manager._tasks["old-task"] = old_task
        task_manager._tasks["recent-task"] = recent_task
        task_manager._results["old-task"] = {"data": "old"}

        cleaned = await task_manager.cleanup_old_tasks(max_age_hours=24)
        assert cleaned == 1
        assert "old-task" not in task_manager._tasks
        assert "old-task" not in task_manager._results
        assert "recent-task" in task_manager._tasks

    @pytest.mark.asyncio
    async def test_update_progress(self, task_manager):
        """Test progress updates."""
        task = Task(id="task-1", type="scan")
        task_manager._tasks["task-1"] = task

        task_manager.update_progress("task-1", 50.0, "Halfway done")

        assert task.progress == 50.0
        assert task.metadata["progress_message"] == "Halfway done"

        # Test clamping
        task_manager.update_progress("task-1", 150.0)
        assert task.progress == 100.0

        task_manager.update_progress("task-1", -10.0)
        assert task.progress == 0.0

    @pytest.mark.asyncio
    async def test_task_duration(self):
        """Test task duration calculation."""
        from datetime import timedelta

        now = datetime.utcnow()
        task = Task(
            id="task-1",
            type="scan",
            started_at=now - timedelta(minutes=5),
            completed_at=now
        )

        assert task.duration_seconds() == 300.0

        # Running task
        running_task = Task(
            id="task-2",
            type="scan",
            started_at=now - timedelta(minutes=2)
        )

        duration = running_task.duration_seconds()
        assert duration is not None
        assert duration >= 120.0

        # Pending task
        pending_task = Task(id="task-3", type="scan")
        assert pending_task.duration_seconds() is None

    @pytest.mark.asyncio
    async def test_task_to_dict(self):
        """Test Task serialization."""
        task = Task(
            id="task-1",
            type="scan",
            data={"target": "example.com"},
            priority=TaskPriority.HIGH,
            state=TaskManagerState.COMPLETED,
            progress=100.0,
            result={"findings": []},
            retry_count=1
        )

        d = task.to_dict()
        assert d["id"] == "task-1"
        assert d["type"] == "scan"
        assert d["priority"] == 1
        assert d["state"] == "completed"
        assert d["progress"] == 100.0
        assert "duration_seconds" in d

    @pytest.mark.asyncio
    async def test_health_check(self, task_manager):
        """Test health check."""
        # Should be healthy when running
        assert await task_manager.health_check() is True

        # Should be unhealthy when not running
        await task_manager.stop()
        assert await task_manager.health_check() is False

    @pytest.mark.asyncio
    async def test_statistics(self, task_manager):
        """Test statistics collection."""
        # Add some tasks
        task_manager._tasks["task-1"] = Task(id="task-1", type="scan", state=TaskManagerState.PENDING)
        task_manager._tasks["task-2"] = Task(id="task-2", type="scan", state=TaskManagerState.RUNNING)
        task_manager._tasks["task-3"] = Task(id="task-3", type="scan", state=TaskManagerState.COMPLETED)

        task_manager.submitted_count = 10
        task_manager.completed_count = 5
        task_manager.failed_count = 2
        task_manager.cancelled_count = 1

        stats = await task_manager.get_statistics()

        assert stats["total_tasks"] == 3
        assert stats["submitted"] == 10
        assert stats["completed"] == 5
        assert stats["failed"] == 2
        assert stats["cancelled"] == 1
        assert stats["state_counts"]["pending"] == 1
        assert stats["state_counts"]["running"] == 1
        assert stats["state_counts"]["completed"] == 1

    @pytest.mark.asyncio
    async def test_queue_full(self):
        """Test behavior when queue is full."""
        tm = TaskManager(max_workers=1, queue_size=1)
        await tm.start()

        # Fill the queue
        task1 = Task(id="task-1", type="slow_task")
        task2 = Task(id="task-2", type="slow_task")

        async def slow_handler(t):
            await asyncio.sleep(10)
            return {}

        tm.register_handler("slow_task", slow_handler)

        await tm.submit(task1)
        await tm.submit(task2)

        # Third task should fail
        task3 = Task(id="task-3", type="slow_task")
        with pytest.raises(RuntimeError, match="Task queue is full"):
            await tm.submit(task3)

        await tm.stop()


# =============================================================================
# Subscription Tests
# =============================================================================


class TestSubscription:
    """Tests for Subscription class."""

    def test_subscription_matches(self):
        """Test subscription matching logic."""
        handler = Mock()

        sub = Subscription(
            id="sub-1",
            event_type=EventType.TASK_COMPLETED,
            handler=handler,
            priority_filter={EventPriority.HIGH},
            source_filter={"worker-1"}
        )

        # Should match
        event1 = Event(
            type=EventType.TASK_COMPLETED,
            source="worker-1",
            priority=EventPriority.HIGH
        )
        assert sub.matches(event1) is True

        # Wrong priority
        event2 = Event(
            type=EventType.TASK_COMPLETED,
            source="worker-1",
            priority=EventPriority.NORMAL
        )
        assert sub.matches(event2) is False

        # Wrong source
        event3 = Event(
            type=EventType.TASK_COMPLETED,
            source="worker-2",
            priority=EventPriority.HIGH
        )
        assert sub.matches(event3) is False

    def test_subscription_no_filters(self):
        """Test subscription without filters matches all."""
        handler = Mock()

        sub = Subscription(
            id="sub-1",
            event_type=EventType.TASK_COMPLETED,
            handler=handler
        )

        event = Event(
            type=EventType.TASK_COMPLETED,
            source="any-source",
            priority=EventPriority.NORMAL
        )
        assert sub.matches(event) is True


# =============================================================================
# Integration Tests
# =============================================================================


class TestOrchestratorIntegration:
    """Integration tests for the orchestrator system."""

    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self):
        """Test complete task lifecycle through orchestrator."""
        config = OrchestratorConfig.default()
        config.enable_analysis_bot = False
        config.enable_audit_logging = False
        config.enable_secure_validation = False
        config.health_check_interval = 0
        config.metrics_enabled = False

        orchestrator = ZenOrchestrator(config)

        # Track events
        events_received = []

        async def event_handler(event):
            events_received.append(event.type.value)

        orchestrator.event_bus.subscribe = AsyncMock()
        orchestrator.event_bus.publish = AsyncMock()

        with patch('orchestrator.core.TaskManager') as mock_tm_class:
            mock_tm = AsyncMock()
            mock_tm.submit = AsyncMock(return_value="task-123")
            mock_tm.get_task = AsyncMock(return_value=MagicMock(
                id="task-123",
                type="vulnerability_scan",
                state=TaskManagerState.COMPLETED,
                priority=TaskPriority.NORMAL,
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                progress=100.0,
                error=None
            ))
            mock_tm_class.return_value = mock_tm

            await orchestrator.start()

            # Submit task
            task_id = await orchestrator.submit_task({
                "type": "vulnerability_scan",
                "target": "example.com"
            })

            assert task_id == "task-123"

            # Check status
            status = await orchestrator.get_task_status(task_id)
            assert status["id"] == "task-123"

            await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_state_and_events_integration(self):
        """Test StateManager and EventBus working together."""
        state_manager = StateManager()
        event_bus = EventBus()
        await event_bus.start()

        state_changes = []

        async def on_state_change(event):
            state_changes.append(event.data)

        await event_bus.subscribe(EventType.TASK_COMPLETED, on_state_change)

        # Simulate state change triggering event
        await state_manager.set_task_state("task-1", TaskState.PENDING)
        await state_manager.set_task_state("task-1", TaskState.QUEUED)
        await state_manager.set_task_state("task-1", TaskState.RUNNING)
        await state_manager.set_task_state("task-1", TaskState.COMPLETED)

        # Publish completion event
        await event_bus.publish(Event(
            type=EventType.TASK_COMPLETED,
            source="state_manager",
            data={"task_id": "task-1", "final_state": "completed"}
        ))

        await asyncio.sleep(0.1)

        assert len(state_changes) == 1
        assert state_changes[0]["task_id"] == "task-1"

        await event_bus.stop()
