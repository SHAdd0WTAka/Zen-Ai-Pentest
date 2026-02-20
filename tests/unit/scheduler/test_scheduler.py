"""
Unit tests for Task Scheduler

Tests the scheduling system including:
- Cron expression parsing
- Job scheduling and execution
- Recurring schedules
"""

import asyncio
from datetime import datetime, timedelta

import pytest

# Import scheduler components
try:
    from scheduler import ScheduleConfig, TaskScheduler
    from scheduler.cron import CronExpression, CronParser
    from scheduler.job import JobBuilder, JobStatus, ScheduledJob, ScheduleType
    from scheduler.recurring import RecurringSchedule
except ImportError:
    import sys

    sys.path.insert(0, "../../..")
    from scheduler import ScheduleConfig, TaskScheduler
    from scheduler.cron import CronExpression, CronParser
    from scheduler.job import JobBuilder, JobStatus, ScheduledJob, ScheduleType
    from scheduler.recurring import RecurringSchedule


class TestCronExpression:
    """Test CronExpression parser"""

    def test_parse_simple(self):
        """Test parsing simple cron expression"""
        cron = CronExpression("0 2 * * *")

        assert 0 in cron.minutes
        assert 2 in cron.hours
        assert len(cron.minutes) == 1
        assert len(cron.hours) == 1

    def test_parse_wildcard(self):
        """Test parsing wildcard"""
        cron = CronExpression("* * * * *")

        assert len(cron.minutes) == 60
        assert len(cron.hours) == 24
        assert len(cron.days_of_month) == 31
        assert len(cron.months) == 12
        assert len(cron.days_of_week) == 7

    def test_parse_range(self):
        """Test parsing range"""
        cron = CronExpression("0 9-17 * * *")

        assert cron.hours == set(range(9, 18))

    def test_parse_step(self):
        """Test parsing step values"""
        cron = CronExpression("*/5 * * * *")

        assert cron.minutes == set(range(0, 60, 5))

    def test_parse_list(self):
        """Test parsing list of values"""
        cron = CronExpression("0 9,12,18 * * *")

        assert cron.hours == {9, 12, 18}

    def test_matches(self):
        """Test matching datetime"""
        cron = CronExpression("0 2 * * *")

        dt_match = datetime(2024, 1, 1, 2, 0)
        dt_no_match = datetime(2024, 1, 1, 3, 0)

        assert cron.matches(dt_match) is True
        assert cron.matches(dt_no_match) is False

    def test_next_occurrence(self):
        """Test calculating next occurrence"""
        cron = CronExpression("0 2 * * *")

        from_time = datetime(2024, 1, 1, 0, 0)
        next_run = cron.next_occurrence(from_time)

        assert next_run == datetime(2024, 1, 1, 2, 0)

    def test_invalid_expression(self):
        """Test invalid cron expression"""
        with pytest.raises(ValueError):
            CronExpression("invalid")


class TestCronParser:
    """Test CronParser utilities"""

    def test_parse_preset(self):
        """Test parsing preset expressions"""
        cron = CronParser.parse("@daily")

        assert "0" in cron.parts[0]  # minute
        assert "0" in cron.parts[1]  # hour

    def test_is_valid(self):
        """Test validation"""
        assert CronParser.is_valid("0 2 * * *") is True
        assert CronParser.is_valid("invalid") is False

    def test_describe(self):
        """Test human-readable description"""
        desc = CronParser.describe("0 2 * * *")

        assert "Daily" in desc or "2" in desc

    def test_get_next_run(self):
        """Test getting next run time"""
        next_run = CronParser.get_next_run("0 0 * * *")

        assert next_run > datetime.utcnow()
        assert next_run.hour == 0
        assert next_run.minute == 0


class TestScheduledJob:
    """Test ScheduledJob model"""

    def test_create_job(self):
        """Test job creation"""
        job = ScheduledJob.create(
            name="Test Job",
            task_type="test_task",
            task_data={"key": "value"},
            schedule_type=ScheduleType.CRON,
            schedule_expr="0 2 * * *",
        )

        assert job.name == "Test Job"
        assert job.task_type == "test_task"
        assert job.schedule_type == ScheduleType.CRON
        assert job.status == JobStatus.SCHEDULED

    def test_job_to_dict(self):
        """Test serialization"""
        job = ScheduledJob.create(
            name="Test", task_type="test", task_data={}, schedule_type=ScheduleType.CRON, schedule_expr="0 0 * * *"
        )

        data = job.to_dict()

        assert data["name"] == "Test"
        assert data["task_type"] == "test"
        assert "created_at" in data

    def test_job_builder(self):
        """Test JobBuilder"""
        job = (
            JobBuilder()
            .name("Builder Test")
            .task("test_task", target="example.com")
            .cron("0 2 * * *")
            .description("Test description")
            .build()
        )

        assert job.name == "Builder Test"
        assert job.task_type == "test_task"
        assert job.description == "Test description"

    def test_job_pause_resume(self):
        """Test pause and resume"""
        job = ScheduledJob.create(
            name="Test", task_type="test", task_data={}, schedule_type=ScheduleType.CRON, schedule_expr="0 0 * * *"
        )

        job.pause()
        assert job.status == JobStatus.PAUSED
        assert job.enabled is False

        job.resume()
        assert job.status == JobStatus.SCHEDULED
        assert job.enabled is True

    def test_record_execution(self):
        """Test recording execution"""
        job = ScheduledJob.create(
            name="Test", task_type="test", task_data={}, schedule_type=ScheduleType.CRON, schedule_expr="0 0 * * *"
        )

        job.record_execution(success=True)

        assert job.run_count == 1
        assert job.status == JobStatus.SCHEDULED
        assert job.last_run is not None


class TestTaskScheduler:
    """Test TaskScheduler"""

    @pytest.fixture
    async def scheduler(self):
        """Create test scheduler"""
        config = ScheduleConfig(check_interval=1, persistence_enabled=False)  # Fast for testing

        sched = TaskScheduler(config)

        # Register test callback
        async def test_callback(data):
            await asyncio.sleep(0.01)
            return {"result": "success", "data": data}

        sched.register_callback("test_task", test_callback)

        await sched.start()

        yield sched

        await sched.stop()

    @pytest.mark.asyncio
    async def test_schedule_cron_job(self, scheduler):
        """Test scheduling cron job"""
        job_id = await scheduler.schedule(
            name="Daily Test", task_type="test_task", task_data={"test": "data"}, cron="0 2 * * *"
        )

        assert job_id is not None
        assert job_id in scheduler._jobs

        job = scheduler._jobs[job_id]
        assert job.name == "Daily Test"
        assert job.next_run is not None

    @pytest.mark.asyncio
    async def test_schedule_interval_job(self, scheduler):
        """Test scheduling interval job"""
        job_id = await scheduler.schedule(name="Interval Test", task_type="test_task", task_data={}, interval=5)

        job = scheduler._jobs[job_id]
        assert job.schedule_type == ScheduleType.INTERVAL
        assert job.schedule_expr == "5"

    @pytest.mark.asyncio
    async def test_schedule_once_job(self, scheduler):
        """Test scheduling one-time job"""
        run_at = datetime.utcnow() + timedelta(minutes=5)

        job_id = await scheduler.schedule(name="Once Test", task_type="test_task", task_data={}, once=run_at)

        job = scheduler._jobs[job_id]
        assert job.schedule_type == ScheduleType.ONCE

    @pytest.mark.asyncio
    async def test_pause_resume_job(self, scheduler):
        """Test pausing and resuming"""
        job_id = await scheduler.schedule(name="Pausable", task_type="test_task", task_data={}, cron="0 0 * * *")

        # Pause
        success = await scheduler.pause_job(job_id)
        assert success
        assert scheduler._jobs[job_id].status == JobStatus.PAUSED

        # Resume
        success = await scheduler.resume_job(job_id)
        assert success
        assert scheduler._jobs[job_id].status == JobStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_unschedule_job(self, scheduler):
        """Test removing job"""
        job_id = await scheduler.schedule(name="Removable", task_type="test_task", task_data={}, cron="0 0 * * *")

        success = await scheduler.unschedule(job_id)
        assert success
        assert job_id not in scheduler._jobs

    @pytest.mark.asyncio
    async def test_get_job(self, scheduler):
        """Test getting job"""
        job_id = await scheduler.schedule(name="Gettable", task_type="test_task", task_data={}, cron="0 0 * * *")

        job = await scheduler.get_job(job_id)
        assert job is not None
        assert job.name == "Gettable"

        # Non-existent job
        assert await scheduler.get_job("nonexistent") is None

    @pytest.mark.asyncio
    async def test_list_jobs(self, scheduler):
        """Test listing jobs"""
        # Create multiple jobs
        for i in range(3):
            await scheduler.schedule(name=f"Job {i}", task_type="test_task", task_data={}, cron="0 0 * * *")

        jobs = await scheduler.list_jobs()
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_statistics(self, scheduler):
        """Test statistics"""
        stats = await scheduler.get_statistics()

        assert "total_jobs" in stats
        assert "total_executions" in stats
        assert "success_rate" in stats


class TestRecurringSchedule:
    """Test RecurringSchedule helpers"""

    def test_every_minute(self):
        """Test every minute"""
        cron = RecurringSchedule.every_minute()
        assert cron == "* * * * *"

    def test_every_hour(self):
        """Test every hour"""
        cron = RecurringSchedule.every_hour()
        assert cron == "0 * * * *"

    def test_daily(self):
        """Test daily"""
        cron = RecurringSchedule.daily(hour=2, minute=30)
        assert cron == "30 2 * * *"

    def test_weekly(self):
        """Test weekly"""
        cron = RecurringSchedule.weekly(day=1, hour=9)  # Monday 9 AM
        assert cron == "0 9 * * 1"

    def test_monthly(self):
        """Test monthly"""
        cron = RecurringSchedule.monthly(day=15, hour=2)
        assert cron == "0 2 15 * *"

    def test_weekdays(self):
        """Test weekdays"""
        cron = RecurringSchedule.weekdays(hour=9)
        assert cron == "0 9 * * 1-5"

    def test_business_hours(self):
        """Test business hours"""
        cron = RecurringSchedule.business_hours()
        assert "9-17" in cron
        assert "1-5" in cron


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
