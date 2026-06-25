"""
End-to-End API Tests

Tests all API endpoints with actual HTTP requests.
Requires running server: python -m uvicorn api.main:app --reload
"""

import asyncio

import pytest

# Mark as e2e tests
pytestmark = pytest.mark.e2e


class TestHealthEndpoints:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, client):
        """Test /ready endpoint"""
        response = await client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert "ready" in data

    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, client):
        """Test /live endpoint"""
        response = await client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True


class TestOrchestratorEndpoints:
    """Test orchestrator API endpoints"""

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """Test orchestrator status endpoint"""
        response = await client.get("/api/v1/orchestrator/status")

        assert response.status_code == 200
        data = response.json()
        assert "instance_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_submit_task(self, client):
        """Test task submission"""
        task_data = {
            "type": "vulnerability_scan",
            "target": "test.example.com",
            "options": {"ports": "80,443"},
            "priority": "normal",
        }

        response = await client.post(
            "/api/v1/orchestrator/tasks", json=task_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "submitted"

        return data["task_id"]

    @pytest.mark.asyncio
    async def test_get_task_status(self, client):
        """Test getting task status"""
        # First submit a task
        task_id = await self.test_submit_task(client)

        # Get status
        response = await client.get(f"/api/v1/orchestrator/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert "state" in data

    @pytest.mark.asyncio
    async def test_list_tasks(self, client):
        """Test listing tasks"""
        response = await client.get("/api/v1/orchestrator/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data


class TestSchedulerEndpoints:
    """Test scheduler API endpoints"""

    @pytest.mark.asyncio
    async def test_get_scheduler_status(self, client):
        """Test scheduler status"""
        response = await client.get("/api/v1/scheduler/status")

        assert response.status_code == 200
        data = response.json()
        assert "running" in data

    @pytest.mark.asyncio
    async def test_schedule_job(self, client):
        """Test scheduling a job"""
        job_data = {
            "name": "E2E Test Job",
            "description": "Test job from E2E tests",
            "task_type": "vulnerability_scan",
            "task_data": {"target": "test.com"},
            "cron": "0 2 * * *",
            "timezone": "UTC",
        }

        response = await client.post("/api/v1/scheduler/jobs", json=job_data)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "scheduled"

        return data["job_id"]

    @pytest.mark.asyncio
    async def test_list_jobs(self, client):
        """Test listing scheduled jobs"""
        response = await client.get("/api/v1/scheduler/jobs")

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_presets(self, client):
        """Test getting schedule presets"""
        response = await client.get("/api/v1/scheduler/presets")

        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "pentest_schedules" in data


class TestDashboardEndpoints:
    """Test dashboard API endpoints"""

    @pytest.mark.asyncio
    async def test_get_dashboard_status(self, client):
        """Test dashboard status"""
        response = await client.get("/api/v1/dashboard/status")

        assert response.status_code == 200
        data = response.json()
        assert "running" in data

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, client):
        """Test getting dashboard data"""
        response = await client.get("/api/v1/dashboard/data")

        assert response.status_code == 200
        data = response.json()
        assert "system_status" in data
        assert "current_metrics" in data

    @pytest.mark.asyncio
    async def test_get_recent_events(self, client):
        """Test getting recent events"""
        response = await client.get("/api/v1/dashboard/events/recent")

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data


class TestAuditEndpoints:
    """Test audit logging endpoints"""

    @pytest.mark.asyncio
    async def test_get_audit_stats(self, client):
        """Test audit statistics"""
        response = await client.get("/api/v1/audit/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_events" in data

    @pytest.mark.asyncio
    async def test_list_compliance_standards(self, client):
        """Test listing compliance standards"""
        response = await client.get("/api/v1/audit/compliance/standards")

        assert response.status_code == 200
        data = response.json()
        assert "standards" in data
        assert len(data["standards"]) > 0


class TestAnalysisEndpoints:
    """Test analysis endpoints"""

    @pytest.mark.asyncio
    async def test_analysis_status(self, client):
        """Test analysis status endpoint"""
        # This might be 200 or 404 depending on implementation
        response = await client.get("/api/v1/analysis/status/test-id")

        assert response.status_code in [200, 404]


class TestPerformanceEndpoints:
    """Test performance endpoints"""

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, client):
        """Test cache statistics endpoint"""
        response = await client.get("/api/v1/performance/cache/stats")

        # May be 200 or 503 depending on config
        assert response.status_code in [200, 503]


class TestCompleteWorkflow:
    """Test complete workflows end-to-end"""

    @pytest.mark.asyncio
    async def test_full_scan_workflow(self, client):
        """Test complete scan and analysis workflow"""
        # 1. Submit scan task
        task_data = {
            "type": "vulnerability_scan",
            "target": "integration-test.example.com",
            "options": {"deep_scan": False},
            "priority": "high",
        }

        response = await client.post(
            "/api/v1/orchestrator/tasks", json=task_data
        )
        assert response.status_code == 200
        task_result = response.json()
        task_id = task_result["task_id"]

        # 2. Check task status (may be pending/running)
        response = await client.get(f"/api/v1/orchestrator/tasks/{task_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["id"] == task_id

        # 3. Check dashboard has events
        await asyncio.sleep(0.5)  # Give time for events
        response = await client.get("/api/v1/dashboard/events/recent")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_schedule_and_monitor_workflow(self, client):
        """Test scheduling and monitoring workflow"""
        # 1. Schedule a job
        job_data = {
            "name": "Integration Test Schedule",
            "task_type": "subdomain_enum",
            "task_data": {"domain": "test.com"},
            "interval": 60,  # Every 60 minutes
            "timezone": "UTC",
        }

        response = await client.post("/api/v1/scheduler/jobs", json=job_data)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # 2. Get job details
        response = await client.get(f"/api/v1/scheduler/jobs/{job_id}")
        assert response.status_code == 200
        job_data = response.json()
        assert job_data["id"] == job_id

        # 3. Pause job
        response = await client.post(f"/api/v1/scheduler/jobs/{job_id}/pause")
        assert response.status_code == 200

        # 4. Resume job
        response = await client.post(f"/api/v1/scheduler/jobs/{job_id}/resume")
        assert response.status_code == 200

        # 5. Clean up - delete job
        response = await client.delete(f"/api/v1/scheduler/jobs/{job_id}")
        assert response.status_code == 200


# Fixtures
try:
    import pytest_asyncio
    from httpx import AsyncClient

    @pytest_asyncio.fixture
    async def client():
        """Create HTTP client for testing"""
        base_url = "http://localhost:8000"
        async with AsyncClient(base_url=base_url) as client:
            yield client

except ImportError:
    # Fallback if httpx not available
    @pytest.fixture
    def client():
        pytest.skip("httpx not installed, skipping E2E tests")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
