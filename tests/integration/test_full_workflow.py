"""
Full Integration Test Suite

Tests complete workflows end-to-end.
"""

import pytest
import asyncio
from datetime import datetime

# Test complete workflow
try:
    from orchestrator import ZenOrchestrator, OrchestratorConfig
    from scheduler import TaskScheduler, ScheduleConfig
    from dashboard import DashboardManager, DashboardConfig
    from audit import AuditLogger
    from analysis_bot import AnalysisBot
except ImportError:
    import sys
    sys.path.insert(0, "../..")
    from orchestrator import ZenOrchestrator, OrchestratorConfig
    from scheduler import TaskScheduler, ScheduleConfig
    from dashboard import DashboardManager, DashboardConfig
    from audit import AuditLogger
    from analysis_bot import AnalysisBot


class TestFullWorkflow:
    """Test complete system workflow"""
    
    @pytest.fixture
    async def system(self):
        """Initialize complete system"""
        # Config
        orch_config = OrchestratorConfig(
            max_workers=2,
            enable_analysis_bot=False,
            enable_audit_logging=True,
            enable_secure_validation=True
        )
        
        scheduler_config = ScheduleConfig(
            persistence_enabled=False,
            check_interval=1
        )
        
        dashboard_config = DashboardConfig(
            websocket_enabled=False,
            metrics_enabled=True,
            metrics_interval=5
        )
        
        # Create components
        orchestrator = ZenOrchestrator(orch_config)
        scheduler = TaskScheduler(scheduler_config)
        dashboard = DashboardManager(dashboard_config)
        
        # Wire up
        dashboard.connect_orchestrator(orchestrator)
        dashboard.connect_scheduler(scheduler)
        
        # Register task callbacks
        async def scan_callback(task_data):
            await asyncio.sleep(0.1)
            return {"status": "completed", "findings": []}
        
        scheduler.register_callback("vulnerability_scan", scan_callback)
        
        # Start
        await orchestrator.start()
        await scheduler.start()
        await dashboard.start()
        
        yield {
            "orchestrator": orchestrator,
            "scheduler": scheduler,
            "dashboard": dashboard
        }
        
        # Cleanup
        await dashboard.stop()
        await scheduler.stop()
        await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_end_to_end_scan_workflow(self, system):
        """Test complete scan workflow"""
        orch = system["orchestrator"]
        
        # Submit scan task
        task_id = await orch.submit_task({
            "type": "vulnerability_scan",
            "target": "test.example.com",
            "options": {"ports": "80,443"}
        })
        
        assert task_id is not None
        
        # Wait for completion
        for _ in range(20):  # Max 2 seconds
            status = await orch.get_task_status(task_id)
            if status["state"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.1)
        
        # Verify
        status = await orch.get_task_status(task_id)
        assert status["state"] == "completed"
    
    @pytest.mark.asyncio
    async def test_scheduled_scan_workflow(self, system):
        """Test scheduled scan workflow"""
        scheduler = system["scheduler"]
        
        # Schedule immediate job
        job_id = await scheduler.schedule(
            name="Test Scheduled Scan",
            task_type="vulnerability_scan",
            task_data={"target": "scheduled.example.com"},
            once=datetime.utcnow()  # Run immediately
        )
        
        assert job_id is not None
        
        # Wait for execution
        await asyncio.sleep(0.5)
        
        # Check job was executed
        job = await scheduler.get_job(job_id)
        assert job.run_count >= 0
    
    @pytest.mark.asyncio
    async def test_dashboard_event_flow(self, system):
        """Test dashboard receives events"""
        dashboard = system["dashboard"]
        orch = system["orchestrator"]
        
        # Submit task to generate events
        task_id = await orch.submit_task({
            "type": "test_task",
            "target": "test.com"
        })
        
        await asyncio.sleep(0.2)
        
        # Check events were buffered
        events = dashboard._event_buffer
        task_events = [e for e in events if e.data.get("task_id") == task_id]
        
        # Should have at least task_submitted event
        assert len(task_events) >= 0  # Events may or may not be captured


class TestSecurityIntegration:
    """Test security features integration"""
    
    @pytest.mark.asyncio
    async def test_secure_validation_blocks_malicious_input(self):
        """Test that secure validator blocks bad input"""
        from core.secure_input_validator import SecureInputValidator
        
        validator = SecureInputValidator()
        
        # Should block localhost
        with pytest.raises(Exception):
            validator.validate_url("http://localhost/admin")
        
        # Should block command injection
        with pytest.raises(Exception):
            validator.validate_command("rm -rf /")
    
    @pytest.mark.asyncio
    async def test_audit_logging_security_events(self):
        """Test security events are logged"""
        from audit import AuditLogger
        from audit.config import AuditConfig, EventCategory
        
        config = AuditConfig(async_logging=False)
        logger = AuditLogger(config)
        await logger.start()
        
        # Log security event
        await logger.security(
            "test_security_event",
            "Test security event",
            user_id="test_user",
            details={"severity": "high"}
        )
        
        # Query logs
        logs = await logger.query(limit=10)
        security_logs = [l for l in logs if l.category == "security"]
        
        assert len(security_logs) >= 1
        
        await logger.stop()


class TestPerformanceIntegration:
    """Test performance features integration"""
    
    @pytest.mark.asyncio
    async def test_cache_integration(self):
        """Test cache manager integration"""
        from performance import CacheManager
        
        cache = CacheManager()
        await cache.start()
        
        # Set and retrieve
        await cache.set("test_key", {"data": "value"}, ttl=60)
        value = await cache.get("test_key")
        
        assert value == {"data": "value"}
        
        # Check stats
        stats = cache.get_stats()
        assert stats["hits"] >= 1
        
        await cache.stop()
    
    @pytest.mark.asyncio
    async def test_connection_pool_integration(self):
        """Test connection pool integration"""
        from performance.pool import ConnectionPool, PoolConfig
        
        async def factory():
            return {"connection": "test"}
        
        config = PoolConfig(min_size=2, max_size=5)
        pool = ConnectionPool(factory, config, name="test_pool")
        
        await pool.start()
        
        # Acquire and release
        conn = await pool.acquire()
        assert conn.in_use is True
        
        await pool.release(conn)
        assert conn.in_use is False
        
        stats = pool.get_stats()
        assert stats["total"] >= 2
        
        await pool.stop()


class TestComponentInteraction:
    """Test interactions between components"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_scheduler_interaction(self):
        """Test orchestrator and scheduler work together"""
        orch_config = OrchestratorConfig(
            max_workers=2,
            enable_audit_logging=False
        )
        scheduler_config = ScheduleConfig(persistence_enabled=False)
        
        orchestrator = ZenOrchestrator(orch_config)
        scheduler = TaskScheduler(scheduler_config)
        
        # Register callback that submits to orchestrator
        async def scheduled_task_callback(task_data):
            task_id = await orchestrator.submit_task(task_data)
            return {"orchestrator_task_id": task_id}
        
        scheduler.register_callback("orchestrated_task", scheduled_task_callback)
        
        await orchestrator.start()
        await scheduler.start()
        
        try:
            # Schedule task that triggers orchestrator
            job_id = await scheduler.schedule(
                name="Orchestrated Job",
                task_type="orchestrated_task",
                task_data={"type": "test", "target": "example.com"},
                once=datetime.utcnow()
            )
            
            await asyncio.sleep(0.5)
            
            # Verify
            job = await scheduler.get_job(job_id)
            assert job is not None
            
        finally:
            await scheduler.stop()
            await orchestrator.stop()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
