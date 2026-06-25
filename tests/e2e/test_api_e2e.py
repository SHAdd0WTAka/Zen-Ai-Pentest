"""
E2E Tests for API Endpoints
"""

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


@pytest.mark.e2e
class TestAPIAuthE2E:
    """E2E Tests for Auth Endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint"""
        from api.routes.v1.health import health_check

        result = await health_check()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_info(self):
        """Test API info endpoint"""
        from api.routes.v1.health import api_info

        result = await api_info()
        assert "name" in result
        assert "version" in result


@pytest.mark.e2e
class TestAPIToolsE2E:
    """E2E Tests for Tools Endpoints"""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list tools endpoint"""
        from api.routes.v1.tools import list_tools

        result = await list_tools(user=None)
        assert "tools" in result
        assert len(result["tools"]) > 0


@pytest.mark.e2e
class TestAPIStatsE2E:
    """E2E Tests for Stats Endpoints"""

    @pytest.mark.asyncio
    async def test_stats_overview(self):
        """Test stats overview endpoint"""
        from api.routes.v1.stats import get_stats_overview

        result = await get_stats_overview(user={"sub": "test"})
        assert "total_scans" in result
        assert "total_findings" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
