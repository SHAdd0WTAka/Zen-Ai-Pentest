"""
Comprehensive tests for the job scheduler.

Tests cover:
- Scheduler class (TaskScheduler)
- Job creation and management
- Recurring jobs
- Cron expression parsing
- Job execution
- Persistence
"""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from scheduler.core import ScheduleConfig, TaskScheduler
from scheduler.cron import CRON_PATTERNS, CronExpression, CronParser
from scheduler.job import (
    JobBuilder,
    JobExecution,
    JobStatus,
    ScheduledJob,
    ScheduleType,
)
from scheduler.recurring import (
    RecurringSchedule,
    SchedulePresets,
    calculate_next_occurrence,
)

# =============================================================================
# ScheduleConfig Tests
# =============================================================================


class TestScheduleConfig:
    """Tests for ScheduleConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ScheduleConfig()

        assert config.check_interval == 60
        assert config.max_concurrent_jobs == 5
        assert config.default_timeout == 3600
        assert config.persistence_enabled is True
        assert config.persistence_path == "scheduler_state.json"
        assert config.auto_recover is True
        assert config.catch_up_missed is True
        assert config.max_catch_up_hours == 24
        assert config.enable_notifications is True
        assert config.webhook_url is None

    def test_custom_config(self):
        """Test custom configuration."""
        config = ScheduleConfig(
            check_interval=30,
            max_concurrent_jobs=10,
            default_timeout=7200,
            persistence_enabled=False,
            catch_up_missed=False,
        )

        assert config.check_interval == 30
        assert config.max_concurrent_jobs == 10
        assert config.default_timeout == 7200
        assert config.persistence_enabled is False
        assert config.catch_up_missed is False


# =============================================================================
# TaskScheduler Tests
# =============================================================================


class TestTaskScheduler:
    """Tests for TaskScheduler class."""

    @pytest.fixture
    async def scheduler(self):
        """Create a test scheduler."""
        config = ScheduleConfig(
            check_interval=1,
            persistence_enabled=False,
            enable_notifications=False,
        )
        scheduler = TaskScheduler(config)
        yield scheduler
        if scheduler._running:
            await scheduler.stop()

    @pytest.mark.asyncio
    async def test_initialization(self, scheduler):
        """Test scheduler initialization."""
        assert scheduler.config is not None
        assert scheduler._jobs == {}
        assert scheduler._executions == {}
        assert scheduler._running is False
        assert scheduler._scheduler_task is None

    @pytest.mark.asyncio
    async def test_start_stop(self, scheduler):
        """Test starting and stopping the scheduler."""
        await scheduler.start()
        assert scheduler._running is True
        assert scheduler._scheduler_task is not None

        await scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_start_idempotent(self, scheduler):
        """Test that start is idempotent."""
        await scheduler.start()
        task = scheduler._scheduler_task

        await scheduler.start()  # Second start should not create new task
        assert scheduler._scheduler_task is task

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_schedule_cron_job(self, scheduler):
        """Test scheduling a cron job."""
        job_id = await scheduler.schedule(
            name="Daily Scan",
            task_type="vulnerability_scan",
            task_data={"target": "example.com"},
            cron="0 2 * * *",
        )

        assert job_id is not None
        assert job_id in scheduler._jobs

        job = scheduler._jobs[job_id]
        assert job.name == "Daily Scan"
        assert job.task_type == "vulnerability_scan"
        assert job.schedule_type == ScheduleType.CRON
        assert job.schedule_expr == "0 2 * * *"
        assert job.enabled is True
        assert job.next_run is not None

    @pytest.mark.asyncio
    async def test_schedule_interval_job(self, scheduler):
        """Test scheduling an interval job."""
        job_id = await scheduler.schedule(
            name="Frequent Check",
            task_type="health_check",
            task_data={},
            interval=30,
        )

        job = scheduler._jobs[job_id]
        assert job.schedule_type == ScheduleType.INTERVAL
        assert job.schedule_expr == "30"
        assert job.next_run is not None

    @pytest.mark.asyncio
    async def test_schedule_one_time_job(self, scheduler):
        """Test scheduling a one-time job."""
        run_at = datetime.utcnow() + timedelta(hours=1)

        job_id = await scheduler.schedule(
            name="One Time Task",
            task_type="cleanup",
            task_data={},
            once=run_at,
        )

        job = scheduler._jobs[job_id]
        assert job.schedule_type == ScheduleType.ONCE
        assert job.next_run == run_at

    @pytest.mark.asyncio
    async def test_schedule_no_schedule_type(self, scheduler):
        """Test that scheduling without schedule type raises error."""
        with pytest.raises(
            ValueError, match="Must specify cron, interval, or once"
        ):
            await scheduler.schedule(
                name="Invalid Job", task_type="test", task_data={}
            )

    @pytest.mark.asyncio
    async def test_schedule_with_options(self, scheduler):
        """Test scheduling with additional options."""
        job_id = await scheduler.schedule(
            name="Test Job",
            task_type="test",
            task_data={"param": "value"},
            cron="0 * * * *",
            description="Test description",
            timezone="America/New_York",
            retries=5,
            timeout=1800,
        )

        job = scheduler._jobs[job_id]
        assert job.description == "Test description"
        assert job.timezone == "America/New_York"
        assert job.max_retries == 5
        assert job.timeout == 1800

    @pytest.mark.asyncio
    async def test_unschedule(self, scheduler):
        """Test removing a scheduled job."""
        job_id = await scheduler.schedule(
            name="Temporary Job",
            task_type="test",
            task_data={},
            cron="0 * * * *",
        )

        result = await scheduler.unschedule(job_id)
        assert result is True
        assert job_id not in scheduler._jobs

    @pytest.mark.asyncio
    async def test_unschedule_nonexistent(self, scheduler):
        """Test unscheduling non-existent job."""
        result = await scheduler.unschedule("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_pause_resume_job(self, scheduler):
        """Test pausing and resuming a job."""
        job_id = await scheduler.schedule(
            name="Pausable Job",
            task_type="test",
            task_data={},
            cron="0 * * * *",
        )

        # Pause
        result = await scheduler.pause_job(job_id)
        assert result is True
        assert scheduler._jobs[job_id].status == JobStatus.PAUSED
        assert scheduler._jobs[job_id].enabled is False

        # Resume
        result = await scheduler.resume_job(job_id)
        assert result is True
        assert scheduler._jobs[job_id].status == JobStatus.SCHEDULED
        assert scheduler._jobs[job_id].enabled is True

    @pytest.mark.asyncio
    async def test_pause_nonexistent_job(self, scheduler):
        """Test pausing non-existent job."""
        result = await scheduler.pause_job("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_run_job_now(self, scheduler):
        """Test manually triggering a job."""
        executed = []

        async def test_callback(data):
            executed.append("executed")
            return {"result": "success"}

        scheduler.register_callback("test_task", test_callback)

        job_id = await scheduler.schedule(
            name="Manual Job",
            task_type="test_task",
            task_data={},
            cron="0 0 * * *",  # Would normally not run soon
        )

        execution_id = await scheduler.run_job_now(job_id)
        assert execution_id is not None
        assert execution_id.startswith("exec-")

        # Wait for execution
        await asyncio.sleep(0.1)

        assert "executed" in executed

    @pytest.mark.asyncio
    async def test_update_job(self, scheduler):
        """Test updating job properties."""
        job_id = await scheduler.schedule(
            name="Original Name",
            task_type="test",
            task_data={"old": "data"},
            cron="0 * * * *",
        )

        result = await scheduler.update_job(
            job_id,
            name="New Name",
            description="New description",
            task_data={"new": "data"},
        )

        assert result is True
        job = scheduler._jobs[job_id]
        assert job.name == "New Name"
        assert job.description == "New description"
        assert job.task_data == {"new": "data"}

    @pytest.mark.asyncio
    async def test_update_job_schedule(self, scheduler):
        """Test updating job schedule."""
        job_id = await scheduler.schedule(
            name="Test Job", task_type="test", task_data={}, cron="0 * * * *"
        )

        original_next_run = scheduler._jobs[job_id].next_run

        result = await scheduler.update_job(job_id, cron="30 * * * *")

        assert result is True
        assert scheduler._jobs[job_id].schedule_expr == "30 * * * *"
        # Next run should be recalculated
        assert scheduler._jobs[job_id].next_run != original_next_run

    @pytest.mark.asyncio
    async def test_update_nonexistent_job(self, scheduler):
        """Test updating non-existent job."""
        result = await scheduler.update_job("non-existent", name="New Name")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_job(self, scheduler):
        """Test getting a job by ID."""
        job_id = await scheduler.schedule(
            name="Test Job", task_type="test", task_data={}, cron="0 * * * *"
        )

        job = await scheduler.get_job(job_id)
        assert job is not None
        assert job.id == job_id
        assert job.name == "Test Job"

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, scheduler):
        """Test getting non-existent job."""
        job = await scheduler.get_job("non-existent")
        assert job is None

    @pytest.mark.asyncio
    async def test_list_jobs(self, scheduler):
        """Test listing jobs with filters."""
        # Create jobs
        id1 = await scheduler.schedule(
            name="Job 1", task_type="scan", task_data={}, cron="0 * * * *"
        )
        id2 = await scheduler.schedule(
            name="Job 2", task_type="report", task_data={}, interval=60
        )
        await scheduler.schedule(
            name="Job 3", task_type="scan", task_data={}, cron="0 0 * * *"
        )

        scheduler._jobs[id1].status = JobStatus.SCHEDULED
        scheduler._jobs[id2].status = JobStatus.PAUSED

        # List all
        all_jobs = await scheduler.list_jobs()
        assert len(all_jobs) == 3

        # Filter by status
        paused = await scheduler.list_jobs(status="paused")
        assert len(paused) == 1
        assert paused[0].id == id2

        # Filter by task type
        scans = await scheduler.list_jobs(task_type="scan")
        assert len(scans) == 2

        # Filter by enabled
        await scheduler.pause_job(id2)
        enabled = await scheduler.list_jobs(enabled_only=True)
        assert len(enabled) == 2

    @pytest.mark.asyncio
    async def test_register_callback(self, scheduler):
        """Test registering job callbacks."""
        callback = AsyncMock()

        scheduler.register_callback("test_task", callback)
        assert "test_task" in scheduler._job_callbacks

    @pytest.mark.asyncio
    async def test_on_execution_complete(self, scheduler):
        """Test setting execution completion callback."""
        callback = AsyncMock()

        scheduler.on_execution_complete(callback)
        assert scheduler._on_execution_complete is callback

    @pytest.mark.asyncio
    async def test_job_execution(self, scheduler):
        """Test actual job execution."""
        executed_jobs = []

        async def test_callback(data):
            executed_jobs.append(data)
            return {"status": "completed"}

        scheduler.register_callback("test_task", test_callback)

        # Start scheduler
        await scheduler.start()

        # Schedule a job that should run soon
        run_at = datetime.utcnow() + timedelta(seconds=1)
        job_id = await scheduler.schedule(
            name="Immediate Job",
            task_type="test_task",
            task_data={"param": "value"},
            once=run_at,
        )

        # Wait for execution
        await asyncio.sleep(2)

        assert len(executed_jobs) == 1
        assert executed_jobs[0]["param"] == "value"

        # Check job was updated
        job = scheduler._jobs[job_id]
        assert job.run_count == 1
        assert job.last_run is not None
        assert job.status == JobStatus.COMPLETED

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_job_execution_failure(self, scheduler):
        """Test job execution failure handling."""

        async def failing_callback(data):
            raise ValueError("Test error")

        scheduler.register_callback("failing_task", failing_callback)

        await scheduler.start()

        run_at = datetime.utcnow() + timedelta(seconds=0.5)
        job_id = await scheduler.schedule(
            name="Failing Job",
            task_type="failing_task",
            task_data={},
            once=run_at,
        )

        await asyncio.sleep(1.5)

        job = scheduler._jobs[job_id]
        assert job.fail_count == 1
        assert job.status == JobStatus.FAILED

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_job_execution_timeout(self, scheduler):
        """Test job execution timeout."""

        async def slow_callback(data):
            await asyncio.sleep(10)  # Longer than timeout
            return {}

        scheduler.register_callback("slow_task", slow_callback)

        await scheduler.start()

        run_at = datetime.utcnow() + timedelta(seconds=0.5)
        job_id = await scheduler.schedule(
            name="Slow Job",
            task_type="slow_task",
            task_data={},
            once=run_at,
            timeout=1,  # 1 second timeout
        )

        await asyncio.sleep(2.5)

        job = scheduler._jobs[job_id]
        assert job.fail_count == 1
        assert job.status == JobStatus.FAILED

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_persistence(self):
        """Test saving and loading scheduler state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "state.json")

            # Create and populate scheduler
            config = ScheduleConfig(
                persistence_enabled=True, persistence_path=state_file
            )
            scheduler1 = TaskScheduler(config)

            job_id = await scheduler1.schedule(
                name="Persistent Job",
                task_type="test",
                task_data={"key": "value"},
                cron="0 * * * *",
            )

            await scheduler1.start()
            await asyncio.sleep(0.1)
            await scheduler1.stop()

            # Verify state file exists
            assert os.path.exists(state_file)

            # Create new scheduler and load state
            scheduler2 = TaskScheduler(config)
            await scheduler2.start()

            assert job_id in scheduler2._jobs
            assert scheduler2._jobs[job_id].name == "Persistent Job"
            assert scheduler2._jobs[job_id].task_data == {"key": "value"}

            await scheduler2.stop()

    @pytest.mark.asyncio
    async def test_catch_up_missed_jobs(self, scheduler):
        """Test catching up missed jobs."""
        callback = AsyncMock(return_value={"status": "completed"})
        scheduler.register_callback("test_task", callback)

        # Add a job that should have run recently
        job = ScheduledJob.create(
            name="Missed Job",
            task_type="test_task",
            task_data={},
            schedule_type=ScheduleType.CRON,
            schedule_expr="* * * * *",
        )
        job.next_run = datetime.utcnow() - timedelta(minutes=5)
        job.enabled = True
        scheduler._jobs["missed-job"] = job

        await scheduler.start()

        # Should execute the missed job
        await asyncio.sleep(0.5)

        assert callback.called

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_statistics(self, scheduler):
        """Test getting scheduler statistics."""
        # Create some jobs
        await scheduler.schedule(
            name="Job 1", task_type="test", task_data={}, cron="0 * * * *"
        )
        await scheduler.schedule(
            name="Job 2", task_type="test", task_data={}, interval=60
        )
        await scheduler.pause_job((await scheduler.list_jobs())[1].id)

        # Set some statistics
        scheduler._total_executions = 10
        scheduler._successful_executions = 8
        scheduler._failed_executions = 2

        stats = await scheduler.get_statistics()

        assert stats["total_jobs"] == 2
        assert stats["enabled_jobs"] == 1
        assert stats["total_executions"] == 10
        assert stats["successful_executions"] == 8
        assert stats["failed_executions"] == 2
        assert stats["success_rate"] == 80.0


# =============================================================================
# ScheduledJob Tests
# =============================================================================


class TestScheduledJob:
    """Tests for ScheduledJob class."""

    def test_job_creation(self):
        """Test job creation."""
        job = ScheduledJob.create(
            name="Test Job",
            task_type="vulnerability_scan",
            task_data={"target": "example.com"},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 2 * * *",
            description="Test description",
        )

        assert job.name == "Test Job"
        assert job.task_type == "vulnerability_scan"
        assert job.schedule_type == ScheduleType.CRON
        assert job.schedule_expr == "0 2 * * *"
        assert job.description == "Test description"
        assert job.id.startswith("job-")
        assert job.enabled is True
        assert job.status == JobStatus.SCHEDULED

    def test_record_execution_success(self):
        """Test recording successful execution."""
        job = ScheduledJob.create(
            name="Test",
            task_type="test",
            task_data={},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 * * * *",
        )

        job.record_execution(success=True, result={"data": "value"})

        assert job.run_count == 1
        assert job.fail_count == 0
        assert job.status == JobStatus.SCHEDULED
        assert job.last_run is not None

    def test_record_execution_failure(self):
        """Test recording failed execution."""
        job = ScheduledJob.create(
            name="Test",
            task_type="test",
            task_data={},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 * * * *",
        )

        job.record_execution(success=False, error="Test error")

        assert job.run_count == 1
        assert job.fail_count == 1
        assert job.status == JobStatus.FAILED

    def test_record_execution_one_time(self):
        """Test recording execution for one-time job."""
        job = ScheduledJob.create(
            name="One Time",
            task_type="test",
            task_data={},
            schedule_type=ScheduleType.ONCE,
            schedule_expr="2024-01-01T00:00:00",
        )

        job.record_execution(success=True)

        assert job.status == JobStatus.COMPLETED

    def test_pause_resume(self):
        """Test pause and resume."""
        job = ScheduledJob.create(
            name="Test",
            task_type="test",
            task_data={},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 * * * *",
        )

        job.pause()
        assert job.enabled is False
        assert job.status == JobStatus.PAUSED

        job.resume()
        assert job.enabled is True
        assert job.status == JobStatus.SCHEDULED

    def test_disable(self):
        """Test disabling a job."""
        job = ScheduledJob.create(
            name="Test",
            task_type="test",
            task_data={},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 * * * *",
        )

        job.disable()
        assert job.enabled is False
        assert job.status == JobStatus.DISABLED

    def test_to_dict(self):
        """Test job serialization."""
        job = ScheduledJob.create(
            name="Test",
            task_type="test",
            task_data={"key": "value"},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 * * * *",
        )
        job.run_count = 5
        job.fail_count = 1

        d = job.to_dict()

        assert d["name"] == "Test"
        assert d["task_type"] == "test"
        assert d["schedule_type"] == "cron"
        assert d["run_count"] == 5
        assert d["fail_count"] == 1

    def test_from_dict(self):
        """Test job deserialization."""
        data = {
            "id": "job-123",
            "name": "Test Job",
            "description": "Test",
            "task_type": "scan",
            "task_data": {},
            "schedule_type": "cron",
            "schedule_expr": "0 * * * *",
            "status": "scheduled",
            "timezone": "UTC",
            "max_retries": 3,
            "timeout": 3600,
            "enabled": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "last_run": None,
            "next_run": "2024-01-02T00:00:00",
            "run_count": 0,
            "fail_count": 0,
            "metadata": {},
        }

        job = ScheduledJob.from_dict(data)

        assert job.id == "job-123"
        assert job.name == "Test Job"
        assert job.schedule_type == ScheduleType.CRON
        assert job.status == JobStatus.SCHEDULED
        assert isinstance(job.next_run, datetime)


# =============================================================================
# JobExecution Tests
# =============================================================================


class TestJobExecution:
    """Tests for JobExecution class."""

    def test_execution_creation(self):
        """Test execution record creation."""
        execution = JobExecution(
            id="exec-123",
            job_id="job-456",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        assert execution.id == "exec-123"
        assert execution.job_id == "job-456"
        assert execution.status == "running"
        assert execution.completed_at is None

    def test_duration_calculation(self):
        """Test execution duration calculation."""
        execution = JobExecution(
            id="exec-123",
            job_id="job-456",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 5, 30),
        )

        duration = execution.duration_seconds()
        assert duration == 330.0  # 5 minutes 30 seconds

    def test_duration_running(self):
        """Test duration for running job."""
        execution = JobExecution(
            id="exec-123", job_id="job-456", started_at=datetime.utcnow()
        )

        duration = execution.duration_seconds()
        assert duration is None


# =============================================================================
# JobBuilder Tests
# =============================================================================


class TestJobBuilder:
    """Tests for JobBuilder class."""

    def test_builder_pattern(self):
        """Test builder pattern methods."""
        builder = JobBuilder()

        result = builder.name("Test Job").description("A test job")
        assert result is builder  # Returns self for chaining

    def test_build_complete_job(self):
        """Test building a complete job."""
        job = (
            JobBuilder()
            .name("Complete Job")
            .description("Test")
            .task("vulnerability_scan", target="example.com")
            .cron("0 2 * * *")
            .timezone("America/New_York")
            .retries(5)
            .timeout(1800)
            .with_metadata(created_by="test")
            .build()
        )

        assert job.name == "Complete Job"
        assert job.task_type == "vulnerability_scan"
        assert job.task_data == {"target": "example.com"}
        assert job.schedule_type == ScheduleType.CRON
        assert job.timezone == "America/New_York"
        assert job.max_retries == 5
        assert job.timeout == 1800
        assert job.metadata == {"created_by": "test"}

    def test_build_interval_job(self):
        """Test building interval job."""
        job = (
            JobBuilder()
            .name("Interval Job")
            .task("health_check")
            .interval(30)
            .build()
        )

        assert job.schedule_type == ScheduleType.INTERVAL
        assert job.schedule_expr == "30"

    def test_build_one_time_job(self):
        """Test building one-time job."""
        run_at = datetime(2024, 12, 25, 0, 0, 0)

        job = (
            JobBuilder()
            .name("One Time Job")
            .task("cleanup")
            .once(run_at)
            .build()
        )

        assert job.schedule_type == ScheduleType.ONCE
        assert job.schedule_expr == "2024-12-25T00:00:00"

    def test_build_missing_name(self):
        """Test error when name is missing."""
        with pytest.raises(ValueError, match="Job name is required"):
            JobBuilder().task("test").cron("0 * * * *").build()

    def test_build_missing_task_type(self):
        """Test error when task type is missing."""
        with pytest.raises(ValueError, match="Task type is required"):
            JobBuilder().name("Test").cron("0 * * * *").build()

    def test_build_missing_schedule(self):
        """Test error when schedule is missing."""
        with pytest.raises(
            ValueError, match="Schedule expression is required"
        ):
            JobBuilder().name("Test").task("test").build()


# =============================================================================
# CronExpression Tests
# =============================================================================


class TestCronExpression:
    """Tests for CronExpression class."""

    def test_parse_simple(self):
        """Test parsing simple cron expression."""
        cron = CronExpression("0 2 * * *")

        assert cron.minutes == {0}
        assert cron.hours == {2}
        assert len(cron.days_of_month) == 31
        assert len(cron.months) == 12
        assert len(cron.days_of_week) == 7

    def test_parse_wildcard(self):
        """Test parsing wildcard."""
        cron = CronExpression("* * * * *")

        assert len(cron.minutes) == 60
        assert len(cron.hours) == 24

    def test_parse_step(self):
        """Test parsing step values."""
        cron = CronExpression("*/5 * * * *")

        assert cron.minutes == {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}

    def test_parse_range(self):
        """Test parsing range values."""
        cron = CronExpression("0 9-17 * * 1-5")

        assert cron.hours == set(range(9, 18))
        assert cron.days_of_week == {1, 2, 3, 4, 5}

    def test_parse_list(self):
        """Test parsing list values."""
        cron = CronExpression("0 0,12 * * 0,6")

        assert cron.hours == {0, 12}
        assert cron.days_of_week == {0, 6}

    def test_parse_invalid(self):
        """Test parsing invalid expression."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            CronExpression("invalid")

        with pytest.raises(ValueError, match="Expected 5 fields"):
            CronExpression("* * * *")  # Only 4 fields

    def test_matches(self):
        """Test matching datetime against expression."""
        cron = CronExpression("30 14 * * *")  # 2:30 PM daily

        dt = datetime(2024, 1, 15, 14, 30, 0)
        assert cron.matches(dt) is True

        dt = datetime(2024, 1, 15, 14, 31, 0)
        assert cron.matches(dt) is False

    def test_next_occurrence(self):
        """Test calculating next occurrence."""
        cron = CronExpression("0 2 * * *")  # 2 AM daily

        from_time = datetime(2024, 1, 15, 10, 0, 0)
        next_time = cron.next_occurrence(from_time)

        assert next_time == datetime(2024, 1, 16, 2, 0, 0)

    def test_previous_occurrence(self):
        """Test calculating previous occurrence."""
        cron = CronExpression("0 2 * * *")  # 2 AM daily

        from_time = datetime(2024, 1, 15, 10, 0, 0)
        prev_time = cron.previous_occurrence(from_time)

        assert prev_time == datetime(2024, 1, 15, 2, 0, 0)


# =============================================================================
# CronParser Tests
# =============================================================================


class TestCronParser:
    """Tests for CronParser class."""

    def test_parse_presets(self):
        """Test parsing preset expressions."""
        presets = {
            "@yearly": "0 0 1 1 *",
            "@annually": "0 0 1 1 *",
            "@monthly": "0 0 1 * *",
            "@weekly": "0 0 * * 0",
            "@daily": "0 0 * * *",
            "@midnight": "0 0 * * *",
            "@hourly": "0 * * * *",
            "@minutely": "* * * * *",
        }

        for preset, expected in presets.items():
            cron = CronParser.parse(preset)
            assert cron.expression == expected

    def test_parse_regular(self):
        """Test parsing regular expressions."""
        cron = CronParser.parse("0 2 * * *")
        assert isinstance(cron, CronExpression)

    def test_is_valid(self):
        """Test expression validation."""
        assert CronParser.is_valid("0 2 * * *") is True
        assert CronParser.is_valid("*/5 * * * *") is True
        assert CronParser.is_valid("@daily") is True
        assert CronParser.is_valid("invalid") is False
        assert CronParser.is_valid("* * * *") is False  # Only 4 fields

    def test_get_next_run(self):
        """Test get_next_run convenience method."""
        from_time = datetime(2024, 1, 15, 10, 0, 0)
        next_run = CronParser.get_next_run("0 2 * * *", from_time)

        assert next_run == datetime(2024, 1, 16, 2, 0, 0)

    def test_describe(self):
        """Test expression description."""
        assert CronParser.describe("0 0 * * *") == "Daily at midnight"
        assert CronParser.describe("0 2 * * *") == "Daily at 2:00 AM"
        assert CronParser.describe("0 * * * *") == "Every hour"
        assert CronParser.describe("*/5 * * * *") == "Every 5 minutes"
        assert (
            CronParser.describe("0 0 * * 0") == "Weekly on Sunday at midnight"
        )
        assert (
            CronParser.describe("0 0 1 * *")
            == "Monthly on the 1st at midnight"
        )

    def test_describe_invalid(self):
        """Test describing invalid expression."""
        result = CronParser.describe("invalid")
        assert "Invalid" in result

    def test_describe_generic(self):
        """Test generic description."""
        result = CronParser.describe("15,30 9,17 * * 1-5")
        # Should describe specific minutes and hours
        assert "minute" in result.lower() or "at minutes" in result


class TestCronPatterns:
    """Tests for common cron patterns."""

    def test_patterns_exist(self):
        """Test that common patterns are defined."""
        patterns = [
            "every_minute",
            "every_5_minutes",
            "every_15_minutes",
            "every_30_minutes",
            "hourly",
            "every_2_hours",
            "daily",
            "daily_morning",
            "daily_evening",
            "weekly",
            "weekly_monday",
            "monthly",
            "yearly",
        ]

        for pattern in patterns:
            assert pattern in CRON_PATTERNS
            assert CronParser.is_valid(CRON_PATTERNS[pattern])


# =============================================================================
# RecurringSchedule Tests
# =============================================================================


class TestRecurringSchedule:
    """Tests for RecurringSchedule class."""

    def test_every_minute(self):
        """Test every minute pattern."""
        assert RecurringSchedule.every_minute() == "* * * * *"

    def test_every_n_minutes(self):
        """Test every N minutes pattern."""
        assert RecurringSchedule.every_n_minutes(5) == "*/5 * * * *"
        assert RecurringSchedule.every_n_minutes(15) == "*/15 * * * *"

    def test_every_hour(self):
        """Test every hour pattern."""
        assert RecurringSchedule.every_hour() == "0 * * * *"

    def test_every_n_hours(self):
        """Test every N hours pattern."""
        assert RecurringSchedule.every_n_hours(2) == "0 */2 * * *"

    def test_daily(self):
        """Test daily pattern."""
        assert RecurringSchedule.daily(14, 30) == "30 14 * * *"
        assert RecurringSchedule.daily() == "0 0 * * *"

    def test_twice_daily(self):
        """Test twice daily pattern."""
        assert RecurringSchedule.twice_daily() == "0 9,21 * * *"
        assert RecurringSchedule.twice_daily((8, 20)) == "0 8,20 * * *"

    def test_weekly(self):
        """Test weekly pattern."""
        assert (
            RecurringSchedule.weekly(0, 2, 30) == "30 2 * * 0"
        )  # Sunday 2:30 AM
        assert (
            RecurringSchedule.weekly(1, 9, 0) == "0 9 * * 1"
        )  # Monday 9:00 AM

    def test_weekly_monday(self):
        """Test weekly Monday pattern."""
        assert RecurringSchedule.weekly_monday(9, 0) == "0 9 * * 1"

    def test_weekly_friday(self):
        """Test weekly Friday pattern."""
        assert RecurringSchedule.weekly_friday(17, 0) == "0 17 * * 5"

    def test_monthly(self):
        """Test monthly pattern."""
        assert RecurringSchedule.monthly(15, 10, 30) == "30 10 15 * *"
        assert RecurringSchedule.monthly() == "0 0 1 * *"

    def test_weekdays(self):
        """Test weekdays pattern."""
        assert RecurringSchedule.weekdays(9, 0) == "0 9 * * 1-5"

    def test_weekends(self):
        """Test weekends pattern."""
        assert RecurringSchedule.weekends(10, 0) == "0 10 * * 0,6"

    def test_business_hours(self):
        """Test business hours pattern."""
        assert RecurringSchedule.business_hours() == "0 9-17 * * 1-5"

    def test_startup_delay(self):
        """Test startup delay."""
        future = RecurringSchedule.startup_delay(5)
        assert isinstance(future, datetime)
        assert future > datetime.utcnow()
        assert future < datetime.utcnow() + timedelta(minutes=6)

    def test_next_weekday(self):
        """Test next weekday calculation."""
        # This just tests the method exists and returns a datetime
        next_day = RecurringSchedule.next_weekday(9, 0)
        assert isinstance(next_day, datetime)
        assert next_day.weekday() < 5  # Monday-Friday

    def test_end_of_month(self):
        """Test end of month pattern."""
        assert RecurringSchedule.end_of_month(23, 0) == "0 23 28-31 * *"

    def test_quarter_end(self):
        """Test quarter end pattern."""
        assert RecurringSchedule.quarter_end() == "0 0 31 3,6,9,12 *"

    def test_year_end(self):
        """Test year end pattern."""
        assert RecurringSchedule.year_end() == "0 0 31 12 *"


# =============================================================================
# SchedulePresets Tests
# =============================================================================


class TestSchedulePresets:
    """Tests for SchedulePresets class."""

    def test_daily_vulnerability_scan(self):
        """Test daily vulnerability scan preset."""
        assert SchedulePresets.daily_vulnerability_scan() == "0 2 * * *"
        assert SchedulePresets.daily_vulnerability_scan(3) == "0 3 * * *"

    def test_weekly_deep_scan(self):
        """Test weekly deep scan preset."""
        assert SchedulePresets.weekly_deep_scan() == "0 3 * * 0"
        assert SchedulePresets.weekly_deep_scan(1, 4) == "0 4 * * 1"

    def test_subdomain_monitoring(self):
        """Test subdomain monitoring preset."""
        assert SchedulePresets.subdomain_monitoring() == "0 */4 * * *"

    def test_certificate_expiry_check(self):
        """Test certificate expiry check preset."""
        assert SchedulePresets.certificate_expiry_check() == "0 6 * * *"

    def test_threat_intelligence_update(self):
        """Test threat intelligence update preset."""
        assert SchedulePresets.threat_intelligence_update() == "0 */6 * * *"

    def test_weekly_report(self):
        """Test weekly report preset."""
        assert SchedulePresets.weekly_report() == "0 9 * * 1"

    def test_monthly_compliance_audit(self):
        """Test monthly compliance audit preset."""
        assert SchedulePresets.monthly_compliance_audit() == "0 2 1 * *"


# =============================================================================
# calculate_next_occurrence Tests
# =============================================================================


class TestCalculateNextOccurrence:
    """Tests for calculate_next_occurrence function."""

    def test_next_occurrence(self):
        """Test calculating next occurrence."""
        # Use a relative time to ensure test is stable
        now = datetime.utcnow()
        base = now.replace(minute=0, second=0, microsecond=0)

        # Next 30-minute interval from base should be base + 30 min
        next_time = calculate_next_occurrence(base, 30)

        # Should be at a 30-minute boundary after now
        assert next_time > now
        assert next_time.minute % 30 == 0

    def test_next_occurrence_future(self):
        """Test that next occurrence is in the future."""
        now = datetime.utcnow()
        base = now.replace(second=0, microsecond=0)

        # Test with 15-minute interval
        next_time = calculate_next_occurrence(base, 15)
        assert next_time > now
        # Verify it's at the expected interval offset from base
        delta = next_time - base
        assert delta.total_seconds() % (15 * 60) == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestSchedulerIntegration:
    """Integration tests for the scheduler."""

    @pytest.mark.asyncio
    async def test_full_job_lifecycle(self):
        """Test complete job lifecycle."""
        config = ScheduleConfig(check_interval=1, persistence_enabled=False)
        scheduler = TaskScheduler(config)

        execution_log = []

        async def test_callback(data):
            execution_log.append(
                {"timestamp": datetime.utcnow(), "data": data}
            )
            return {"status": "completed"}

        scheduler.register_callback("integration_test", test_callback)

        await scheduler.start()

        # Schedule a one-time job
        run_at = datetime.utcnow() + timedelta(seconds=2)
        job_id = await scheduler.schedule(
            name="Integration Test Job",
            task_type="integration_test",
            task_data={"test": "value"},
            once=run_at,
        )

        # Wait for execution
        await asyncio.sleep(3)

        assert len(execution_log) == 1
        assert execution_log[0]["data"]["test"] == "value"

        job = scheduler._jobs[job_id]
        assert job.run_count == 1
        assert job.status == JobStatus.COMPLETED

        # Get executions
        executions = await scheduler.get_executions(job_id)
        assert len(executions) == 1
        assert executions[0].status == "completed"

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_multiple_scheduled_jobs(self):
        """Test multiple jobs scheduled at different intervals."""
        config = ScheduleConfig(check_interval=1, persistence_enabled=False)
        scheduler = TaskScheduler(config)

        execution_count = {"job1": 0, "job2": 0}
        execution_events = []

        async def callback1(data):
            execution_count["job1"] += 1
            execution_events.append("job1")
            return {}

        async def callback2(data):
            execution_count["job2"] += 1
            execution_events.append("job2")
            return {}

        scheduler.register_callback("job1", callback1)
        scheduler.register_callback("job2", callback2)

        await scheduler.start()

        # Schedule jobs to run soon
        now = datetime.utcnow()
        await scheduler.schedule(
            name="Job 1",
            task_type="job1",
            task_data={},
            once=now + timedelta(seconds=0.5),
        )

        await scheduler.schedule(
            name="Job 2",
            task_type="job2",
            task_data={},
            once=now + timedelta(seconds=1),
        )

        # Wait for both to complete with some buffer
        await asyncio.sleep(2.5)

        # Both should have executed at least once
        assert (
            execution_count["job1"] >= 1
        ), f"job1 executed {execution_count['job1']} times"
        assert (
            execution_count["job2"] >= 1
        ), f"job2 executed {execution_count['job2']} times"

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_execution_callback(self):
        """Test on_execution_complete callback."""
        config = ScheduleConfig(check_interval=1, persistence_enabled=False)
        scheduler = TaskScheduler(config)

        completed_jobs = []

        async def test_callback(data):
            return {"result": "ok"}

        async def on_complete(job, execution):
            completed_jobs.append(
                {
                    "job_name": job.name,
                    "execution_id": execution.id,
                    "status": execution.status,
                }
            )

        scheduler.register_callback("test", test_callback)
        scheduler.on_execution_complete(on_complete)

        await scheduler.start()

        run_at = datetime.utcnow() + timedelta(seconds=1)
        await scheduler.schedule(
            name="Callback Test", task_type="test", task_data={}, once=run_at
        )

        await asyncio.sleep(2)

        assert len(completed_jobs) == 1
        assert completed_jobs[0]["job_name"] == "Callback Test"
        assert completed_jobs[0]["status"] == "completed"

        await scheduler.stop()
